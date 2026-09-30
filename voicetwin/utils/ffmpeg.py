"""ffmpeg 封装：优先使用系统 ffmpeg，找不到时使用 imageio-ffmpeg 自带的二进制（免手动安装）。"""

from __future__ import annotations

import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np


class FFmpegError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - 取决于环境
        raise FFmpegError(
            "找不到 ffmpeg。请执行 `pip install imageio-ffmpeg`，或安装系统 ffmpeg 并加入 PATH。"
        ) from exc


def _run(args: Sequence[str], capture_stdout: bool = False) -> bytes:
    cmd = [find_ffmpeg(), "-hide_banner", "-nostdin", "-loglevel", "error", *args]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        msg = proc.stderr.decode("utf-8", errors="replace").strip()
        raise FFmpegError(f"ffmpeg 执行失败：{' '.join(map(str, args))}\n{msg}")
    return proc.stdout if capture_stdout else b""


def extract_audio(src: Path, dst: Path, sample_rate: int = 44100, mono: bool = True) -> Path:
    """从视频或任意音频文件中提取音轨，保存为 16-bit PCM wav。"""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    args: List[str] = ["-y", "-i", str(src), "-vn", "-sn", "-dn"]
    if mono:
        args += ["-ac", "1"]
    args += ["-ar", str(sample_rate), "-c:a", "pcm_s16le", str(dst)]
    _run(args)
    return dst


def decode_to_array(src: Path, sample_rate: Optional[int] = None, mono: bool = True) -> "tuple[np.ndarray, int]":
    """用 ffmpeg 解码为 float32 数组（soundfile 读不了 mp3/m4a/视频时使用）。"""
    sr = int(sample_rate or 44100)
    args = ["-i", str(src), "-vn", "-f", "f32le", "-acodec", "pcm_f32le", "-ar", str(sr)]
    if mono:
        args += ["-ac", "1"]
    args += ["pipe:1"]
    raw = _run(args, capture_stdout=True)
    wav = np.frombuffer(raw, dtype=np.float32).copy()
    if not mono:
        wav = wav.reshape(-1, 2)
    return wav, sr


def encode(src_wav: Path, dst: Path, bitrate: str = "192k") -> Path:
    """wav 转 mp3/m4a 等（按目标扩展名决定编码器）。"""
    dst = Path(dst)
    ext = dst.suffix.lower()
    args = ["-y", "-i", str(src_wav)]
    if ext == ".mp3":
        args += ["-c:a", "libmp3lame", "-b:a", bitrate]
    elif ext in (".m4a", ".aac"):
        args += ["-c:a", "aac", "-b:a", bitrate]
    elif ext == ".flac":
        args += ["-c:a", "flac"]
    args.append(str(dst))
    _run(args)
    return dst


def atempo(src_wav: Path, dst_wav: Path, tempo: float) -> Path:
    """变速不变调（ffmpeg atempo，适合 0.8~1.25 的小幅调整，音质好于相位声码器）。"""
    tempo = float(tempo)
    filters = []
    remaining = tempo
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.5f}")
    _run(["-y", "-i", str(src_wav), "-filter:a", ",".join(filters), str(dst_wav)])
    return Path(dst_wav)


def mux_audio_into_video(video: Path, audio: Path, dst: Path, keep_original_audio: bool = False) -> Path:
    """把合成好的讲解音频放进视频（默认替换原音轨，视频流直接复制不重新编码）。"""
    args = ["-y", "-i", str(video), "-i", str(audio)]
    if keep_original_audio:
        args += [
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=longest[a]",
            "-map",
            "0:v",
            "-map",
            "[a]",
        ]
    else:
        args += ["-map", "0:v:0", "-map", "1:a:0"]
    args += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(dst)]
    _run(args)
    return Path(dst)
