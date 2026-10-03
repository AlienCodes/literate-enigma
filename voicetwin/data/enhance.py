"""录音清理：去低频嗡嗡声、（可选）去背景音乐、（按需）轻度降噪、统一响度。

原则：宁可少处理，不可过度处理——降噪过猛会把你的音色一起"削掉"，克隆出来就不像了。
"""

from __future__ import annotations

import collections
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from voicetwin.utils.audio import (clip_counts, estimate_snr, frame_rms_db, highpass, load_audio, measure_lufs,
                                   normalize_lufs, save_audio)
from voicetwin.utils.log import get_logger

log = get_logger("enhance")

#: 降噪用的噪声样本（停顿里最安静的部分）最多取这么长；不到 NOISE_SAMPLE_MIN_S 秒时不降噪
NOISE_SAMPLE_MAX_S = 10.0
NOISE_SAMPLE_MIN_S = 1.0
#: Demucs 运行时每隔这么多秒看一次「停止」按钮
DEMUCS_POLL_SECONDS = 0.5


def _run_demucs(cmd: List[str]) -> Tuple[int, str]:
    """运行 Demucs（一两个小时的视频要二三十分钟），返回 (退出码, 最后一段输出)。

    隔半秒看一次「停止」按钮：点了就结束 Demucs（连同它开的子进程），抛出 TaskCancelled（以前要等 Demucs 做完才停）。
    输出边读边丢、只留最后一段（报错时给帮忙的人看），不会因为进度条把管道写满而卡住。"""
    from voicetwin.backends.base import kill_process_tree
    from voicetwin.utils.progress import CANCEL, TaskCancelled
    from voicetwin.utils.winsys import kill_with_parent

    extra: Dict[str, Any] = {} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), **extra)
    kill_with_parent(proc)  # 关掉声音分身（黑色窗口）时 Demucs 一起结束
    tail: "collections.deque[bytes]" = collections.deque(maxlen=64)

    def read() -> None:
        try:
            for chunk in iter(lambda: proc.stdout.read(4096), b""):  # type: ignore[union-attr]
                tail.append(chunk)
        except Exception:  # noqa: BLE001 - 读输出出错不影响 Demucs 本身
            pass

    reader = threading.Thread(target=read, name="vt-demucs-output", daemon=True)
    reader.start()
    finished = False
    try:
        while True:
            try:
                code = proc.wait(timeout=DEMUCS_POLL_SECONDS)
                break
            except subprocess.TimeoutExpired:
                if CANCEL.is_set():
                    log.info("正在停止去背景音乐（Demucs）……")
                    raise TaskCancelled("已按你的要求停止")
        finished = True
    finally:
        if not finished:
            kill_process_tree(proc)
            try:
                proc.wait(timeout=10)
            except Exception:  # noqa: BLE001
                pass
        reader.join(timeout=5)
        try:
            proc.stdout.close()  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            pass
    return int(code), b"".join(tail).decode("utf-8", errors="replace")


def separate_vocals(wav_path: Path, work_dir: Path) -> Path:
    """用 Demucs 去掉背景音乐，只保留人声。需要 pip install demucs。

    临时文件夹（demucs_*）不管成功、出错还是点了停止都删掉（以前出错时留在 raw/ 里）。"""
    try:
        import demucs  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("去背景音乐需要安装 demucs：pip install \"voicetwin[separate]\"") from exc
    out_root = Path(tempfile.mkdtemp(prefix="demucs_", dir=str(work_dir)))
    try:
        cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", str(out_root),
               str(wav_path)]
        log.info("正在分离人声与背景音乐（Demucs）……")
        code, output = _run_demucs(cmd)
        if code != 0:
            raise RuntimeError("Demucs 执行失败：\n" + output[-2000:])
        vocals = next(out_root.rglob("vocals.wav"), None)
        if vocals is None:
            raise RuntimeError("Demucs 没有输出 vocals.wav")
        final = work_dir / (wav_path.stem + ".vocals.wav")
        shutil.move(str(vocals), final)
        return final
    finally:
        shutil.rmtree(out_root, ignore_errors=True)


def noise_sample(wav: np.ndarray, sr: int, db: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
    """降噪用的噪声样本：停顿里最安静的部分（连续 80 毫秒以上、两头各让出 20 毫秒，不带进说话的开头结尾），
    最多 NOISE_SAMPLE_MAX_S 秒。数字静音（剪辑时插进去的全 0）不算。找不到足够的停顿时返回 None。
    db：已经算好的逐帧电平（frame_rms_db，10 毫秒一帧），不给就现算。"""
    hop = max(1, int(round(sr * 0.01)))
    if db is None:
        db = frame_rms_db(wav, sr)
    db = np.asarray(db)
    valid = db > -90.0
    if not np.any(valid):
        return None
    floor = float(np.percentile(db[valid], 10))
    top = float(np.percentile(db[valid], 95))
    if top - floor < 6.0:  # 没有比说话声明显安静的地方：分不出哪里是底噪
        return None
    quiet = (valid & (db <= floor + 3.0)).astype(np.int8)
    edges = np.diff(np.concatenate([[0], quiet, [0]]))
    max_n = int(NOISE_SAMPLE_MAX_S * sr)
    pieces: List[np.ndarray] = []
    total = 0
    for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        if b - a < 8:
            continue
        s, e = (int(a) + 2) * hop, min(len(wav), (int(b) - 2) * hop)
        if e <= s:
            continue
        pieces.append(wav[s:e])
        total += e - s
        if total >= max_n:
            break
    if total < NOISE_SAMPLE_MIN_S * sr:
        return None
    noise = np.concatenate(pieces)[:max_n].astype(np.float32)
    if float(np.max(np.abs(noise))) <= 0.0:
        return None
    return noise


def denoise(wav: np.ndarray, sr: int, strength: float = 0.6, db: Optional[np.ndarray] = None) -> np.ndarray:
    """轻度降噪（noisereduce 平稳噪声模式）。没有降噪时原样返回同一个数组。

    噪声样本取停顿里最安静的部分（noise_sample）。以前不给噪声样本，noisereduce 拿录音开头 13.6 秒当「噪声」——
    讲课录音开头多半就是老师在说话，结果把老师的声音削掉 6~7 dB，比不降噪还差。找不到足够的停顿时不降噪
    （宁可不降，也不伤音色）。"""
    try:
        import noisereduce as nr
    except ImportError:
        log.warning("未安装 noisereduce，跳过降噪（重新双击 install_windows.bat 安装一次就会装上；"
                    "命令行：pip install noisereduce）")
        return wav
    noise = noise_sample(wav, sr, db)
    if noise is None:
        log.info("  没有找到足够长的停顿来估计底噪，这次不降噪（宁可不降，也不伤你的音色）")
        return wav
    out = nr.reduce_noise(y=wav, sr=sr, y_noise=noise, stationary=True, prop_decrease=float(strength),
                          n_std_thresh_stationary=1.5)
    return np.asarray(out, dtype=np.float32)


def _snr_from_db(db: np.ndarray) -> float:
    """和 estimate_snr 一样（语音电平 95% 分位 - 底噪 10% 分位），用已经算好的逐帧电平。"""
    db = np.asarray(db)
    db = db[db > -100]
    if db.size == 0:
        return 0.0
    return float(np.percentile(db, 95) - np.percentile(db, 10))


def enhance_file(src: Path, dst: Path, cfg: Dict[str, Any], work_dir: Path,
                 clip_info: Optional[Dict[str, Any]] = None) -> Tuple[Path, Dict[str, Any]]:
    """处理一整条录音，返回 (输出路径, 统计信息)。

    clip_info（给了的话）：填进原始录音每 1 毫秒里满格样本的个数（clip_counts / clip_hop）。「有爆音」要在统一音量
    以前查：统一音量以后最响只有 -1 dB，永远查不出来（以前就是这样，破音的句子都拿去训练了）。"""
    sr = int(cfg.get("sample_rate", 44100))
    input_path = Path(src)
    info: Dict[str, Any] = {}
    if cfg.get("separate_vocals"):
        if clip_info is not None:  # 爆音按原来的录音查（去背景音乐以后不再是满格）
            raw_wav, _ = load_audio(input_path, sr=sr)
            clip_info["clip_counts"], clip_info["clip_hop"] = clip_counts(raw_wav, sr)
            del raw_wav
        vocals = separate_vocals(input_path, work_dir)
        try:
            wav, sr = load_audio(vocals, sr=sr)
        finally:
            vocals.unlink(missing_ok=True)  # 和整个视频一样长的人声文件：读进来就不要了（以前每个视频都留一个）
        info["separated"] = True
    else:
        wav, sr = load_audio(input_path, sr=sr)
        if clip_info is not None:
            clip_info["clip_counts"], clip_info["clip_hop"] = clip_counts(wav, sr)
    info["orig_lufs"] = measure_lufs(wav, sr)
    wav = highpass(wav, sr, float(cfg.get("highpass_hz", 60) or 0))
    db = frame_rms_db(wav, sr)
    snr = _snr_from_db(db)
    info["snr_before"] = snr
    mode = str(cfg.get("denoise", "auto")).lower()
    do_denoise = mode == "on" or (mode == "auto" and snr < float(cfg.get("snr_threshold_db", 25)))
    if do_denoise:
        log.info(f"  估计信噪比 {snr:.1f} dB，进行轻度降噪（强度 {cfg.get('denoise_strength', 0.6)}）")
        out = denoise(wav, sr, float(cfg.get("denoise_strength", 0.6)), db=db)
        if out is not wav:
            wav = out
            info["denoised"] = True
            info["snr_after"] = estimate_snr(wav, sr)
    del db
    wav = normalize_lufs(wav, sr, float(cfg.get("target_lufs", -20)))
    save_audio(dst, wav, sr)
    return Path(dst), info
