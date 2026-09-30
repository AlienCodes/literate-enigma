"""录音清理：去低频嗡嗡声、（可选）去背景音乐、（按需）轻度降噪、统一响度。

原则：宁可少处理，不可过度处理——降噪过猛会把你的音色一起"削掉"，克隆出来就不像了。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from voicetwin.utils.audio import estimate_snr, highpass, load_audio, measure_lufs, normalize_lufs, save_audio
from voicetwin.utils.log import get_logger

log = get_logger("enhance")


def separate_vocals(wav_path: Path, work_dir: Path) -> Path:
    """用 Demucs 去掉背景音乐，只保留人声。需要 pip install demucs。"""
    try:
        import demucs  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("去背景音乐需要安装 demucs：pip install \"voicetwin[separate]\"") from exc
    out_root = Path(tempfile.mkdtemp(prefix="demucs_", dir=str(work_dir)))
    cmd = [sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", str(out_root), str(wav_path)]
    log.info("正在分离人声与背景音乐（Demucs）……")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise RuntimeError("Demucs 执行失败：\n" + proc.stdout.decode("utf-8", errors="replace")[-2000:])
    vocals = next(out_root.rglob("vocals.wav"), None)
    if vocals is None:
        raise RuntimeError("Demucs 没有输出 vocals.wav")
    final = work_dir / (wav_path.stem + ".vocals.wav")
    shutil.move(str(vocals), final)
    shutil.rmtree(out_root, ignore_errors=True)
    return final


def denoise(wav: np.ndarray, sr: int, strength: float = 0.6) -> np.ndarray:
    try:
        import noisereduce as nr
    except ImportError:
        log.warning("未安装 noisereduce，跳过降噪（pip install \"voicetwin[denoise]\"）")
        return wav
    out = nr.reduce_noise(y=wav, sr=sr, stationary=True, prop_decrease=float(strength), n_std_thresh_stationary=1.5)
    return np.asarray(out, dtype=np.float32)


def enhance_file(src: Path, dst: Path, cfg: Dict[str, Any], work_dir: Path) -> Tuple[Path, Dict[str, Any]]:
    """处理一整条录音，返回 (输出路径, 统计信息)。"""
    sr = int(cfg.get("sample_rate", 44100))
    input_path = Path(src)
    info: Dict[str, Any] = {}
    if cfg.get("separate_vocals"):
        input_path = separate_vocals(input_path, work_dir)
        info["separated"] = True
    wav, sr = load_audio(input_path, sr=sr)
    info["orig_lufs"] = measure_lufs(wav, sr)
    wav = highpass(wav, sr, float(cfg.get("highpass_hz", 60) or 0))
    snr = estimate_snr(wav, sr)
    info["snr_before"] = snr
    mode = str(cfg.get("denoise", "auto")).lower()
    do_denoise = mode == "on" or (mode == "auto" and snr < float(cfg.get("snr_threshold_db", 25)))
    if do_denoise:
        log.info(f"  估计信噪比 {snr:.1f} dB，进行轻度降噪（强度 {cfg.get('denoise_strength', 0.6)}）")
        wav = denoise(wav, sr, float(cfg.get("denoise_strength", 0.6)))
        info["denoised"] = True
        info["snr_after"] = estimate_snr(wav, sr)
    wav = normalize_lufs(wav, sr, float(cfg.get("target_lufs", -20)))
    save_audio(dst, wav, sr)
    return Path(dst), info
