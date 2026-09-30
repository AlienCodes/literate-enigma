"""声纹（音色）向量：用来衡量"像不像你"。

依次尝试：
1. resemblyzer —— 模型权重随 pip 包附带，离线可用，轻量；
2. speechbrain ECAPA —— 精度更高，首次使用需下载（国内可设 HF_ENDPOINT=https://hf-mirror.com）；
3. MFCC 统计量 —— 最后的兜底，只能粗略比较，不用于自动剔除片段。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

from voicetwin.utils.audio import load_audio, resample, trim_silence
from voicetwin.utils.log import get_logger

log = get_logger("speaker")


def _l2(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(_l2(a), _l2(b)))


def centroid(embs: Sequence[np.ndarray]) -> np.ndarray:
    return _l2(np.mean(np.stack([_l2(e) for e in embs]), axis=0))


def _torch_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


class SpeakerEncoder:
    name = "base"
    reliable = True  # 是否足够可靠，可以用来自动剔除"不是你"的片段

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        raise NotImplementedError

    def embed_file(self, path: Path) -> np.ndarray:
        wav, sr = load_audio(path, sr=16000)
        return self.embed(wav, sr)

    def embed_many(self, paths: Sequence[Path]) -> List[np.ndarray]:
        return [self.embed_file(p) for p in paths]


class ResemblyzerEncoder(SpeakerEncoder):
    name = "resemblyzer"

    def __init__(self) -> None:
        from resemblyzer import VoiceEncoder  # noqa: F401

        self._enc = VoiceEncoder(device=_torch_device(), verbose=False)

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        from resemblyzer import preprocess_wav

        w16 = resample(wav, sr, 16000)
        try:
            proc = preprocess_wav(w16, source_sr=16000)
        except Exception:
            proc = w16
        if len(proc) < 16000 * 0.6:
            proc = w16
        return _l2(self._enc.embed_utterance(proc))


class SpeechBrainEncoder(SpeakerEncoder):
    name = "speechbrain-ecapa"

    def __init__(self) -> None:
        import torch  # noqa: F401

        try:
            from speechbrain.inference.speaker import EncoderClassifier
        except ImportError:
            from speechbrain.pretrained import EncoderClassifier  # type: ignore
        save = Path.home() / ".cache" / "voicetwin" / "spkrec-ecapa-voxceleb"
        self._model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb", savedir=str(save), run_opts={"device": _torch_device()}
        )

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        import torch

        w16, _, _ = trim_silence(resample(wav, sr, 16000), 16000)
        if len(w16) < 8000:
            w16 = resample(wav, sr, 16000)
        with torch.no_grad():
            emb = self._model.encode_batch(torch.from_numpy(w16).float().unsqueeze(0))
        return _l2(emb.squeeze().cpu().numpy())


class MFCCEncoder(SpeakerEncoder):
    name = "mfcc-stats"
    reliable = False

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        import librosa

        w16, _, _ = trim_silence(resample(wav, sr, 16000), 16000)
        if len(w16) < 1600:
            w16 = resample(wav, sr, 16000)
        mfcc = librosa.feature.mfcc(y=w16, sr=16000, n_mfcc=24, n_fft=512, hop_length=160)[1:]
        feat = np.concatenate([mfcc.mean(axis=1) / 20.0, mfcc.std(axis=1) / 10.0])
        return _l2(feat)


@lru_cache(maxsize=4)
def get_speaker_encoder(kind: str = "auto") -> SpeakerEncoder:
    kind = (kind or "auto").lower()
    order = {"auto": ["resemblyzer", "speechbrain", "mfcc"], "resemblyzer": ["resemblyzer", "mfcc"],
             "speechbrain": ["speechbrain", "mfcc"], "mfcc": ["mfcc"]}.get(kind, ["resemblyzer", "speechbrain", "mfcc"])
    errors = []
    for name in order:
        try:
            if name == "resemblyzer":
                enc: SpeakerEncoder = ResemblyzerEncoder()
            elif name == "speechbrain":
                enc = SpeechBrainEncoder()
            else:
                enc = MFCCEncoder()
            if name == "mfcc" and errors:
                log.warning("声纹模型不可用，使用简易 MFCC 相似度（仅供参考）。"
                            "建议安装：pip install webrtcvad-wheels && pip install resemblyzer --no-deps")
            return enc
        except Exception as exc:  # pragma: no cover - 取决于环境
            errors.append(f"{name}: {exc}")
    raise RuntimeError("没有可用的声纹模型：" + "; ".join(errors))


def load_centroid(path: Path) -> Optional[np.ndarray]:
    if Path(path).exists():
        return np.load(path)
    return None


def spread_sample(items: Sequence, k: int) -> list:
    """均匀抽样 k 个（保持来源分布），k<=0 或数量不足时全部返回。"""
    items = list(items)
    if k <= 0 or len(items) <= k:
        return items
    idx = np.linspace(0, len(items) - 1, k).round().astype(int)
    return [items[i] for i in sorted(set(idx.tolist()))]


def voice_centroid(project, encoder: SpeakerEncoder, max_clips: int = 80, refresh: bool = False) -> Optional[np.ndarray]:
    """你本人声音的"平均声纹"，按声纹模型分别缓存。"""
    path = Path(project.root) / f"speaker_centroid.{encoder.name}.npy"
    if path.exists() and not refresh:
        return np.load(path)
    records = [r for r in project.load_manifest(only_kept=True) if r.get("split", "train") == "train"]
    if not records:
        return None
    records.sort(key=lambda r: (-(r.get("speaker_sim") or 0.0), r["id"]))
    chosen = spread_sample(sorted(records[: max_clips * 2], key=lambda r: r["id"]), max_clips)
    embs = [encoder.embed_file(project.abspath(r["path"])) for r in chosen]
    cen = centroid(embs)
    np.save(path, cen)
    return cen
