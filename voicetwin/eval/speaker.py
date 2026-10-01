"""声纹（音色）向量：用来衡量"像不像你"。

单个声纹模型（素材准备时剔除"不是你本人"的片段用），依次尝试：
1. resemblyzer —— 模型权重随 pip 包附带，离线可用，轻量；
2. speechbrain ECAPA —— 精度更高，首次使用需下载（国内可设 HF_ENDPOINT=https://hf-mirror.com）；
3. MFCC 统计量 —— 最后的兜底，只能粗略比较，不用于自动剔除片段。

给合成结果打"像你本人（%）"时用多个声纹模型一起打分（SimilarityJudge）：
- GPT-SoVITS v2Pro 整合包自带的 ERes2NetV2 说话人识别模型
  （GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt，3D-Speaker 训练的 20 万人模型）；
- resemblyzer；
- 两个都没有时才用 MFCC（仅供参考）。

百分比是"校准"过的：100% = 和你自己的真实录音一样像。
做法：先用你的训练片段算出"平均声纹"，再看你留出来没参与训练的真实片段（验证集）和它有多像，
取中位数 p50_real；一段合成音频和平均声纹的余弦相似度为 s 时，像你本人 = 100 × min(1, s / p50_real)。
每个模型分别校准，再取平均。相似度是声纹模型自动打分，越高越像，但不是绝对精确，最终以耳朵为准。
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.utils.audio import load_audio, resample, trim_silence
from voicetwin.utils.log import get_logger

log = get_logger("speaker")

SV_CKPT_REL = "GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt"
ERES_DIR_REL = "GPT_SoVITS/eres2net"
CALIBRATION_FILE = "speaker_calibration.json"
#: ERes2NetV2 一次只看这么长：整篇讲课一次送进去，显存/内存按长度涨（每秒约 30 MB，10 分钟要十几 GB）
SV_WINDOW_SECONDS = 10.0
PCT_HELP = "100% = 和你自己的真实录音一样像"
HONEST_NOTE = "相似度是声纹模型自动打分，越高越像，但不是绝对精确，最终以耳朵为准"
MIN_PCT_DEFAULT = 85.0
MODEL_LABELS = {
    "eres2netv2": "ERes2NetV2（GPT-SoVITS 自带）",
    "resemblyzer": "Resemblyzer",
    "speechbrain-ecapa": "SpeechBrain ECAPA",
    "mfcc-stats": "简易 MFCC（仅供参考）",
}
ProgressFn = Callable[[float, str], None]


def _l2(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(_l2(a), _l2(b)))


def centroid(embs: Sequence[np.ndarray]) -> np.ndarray:
    return _l2(np.mean(np.stack([_l2(e) for e in embs]), axis=0))


def _torch_device(device: str = "auto") -> str:
    if device and device not in ("auto", ""):
        return device
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
        self._lock = threading.Lock()

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        from resemblyzer import preprocess_wav

        w16 = resample(wav, sr, 16000)
        try:
            proc = preprocess_wav(w16, source_sr=16000)
        except Exception:
            proc = w16
        if len(proc) < 16000 * 0.6:
            proc = w16
        with self._lock:
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
        self._lock = threading.Lock()

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        import torch

        w16, _, _ = trim_silence(resample(wav, sr, 16000), 16000)
        if len(w16) < 8000:
            w16 = resample(wav, sr, 16000)
        with self._lock, torch.no_grad():
            emb = self._model.encode_batch(torch.from_numpy(w16).float().unsqueeze(0))
        return _l2(emb.squeeze().cpu().numpy())


_IMPORT_LOCK = threading.Lock()


def _load_module_from(path: Path, name: str, extra_path: Path) -> Any:
    """从 GPT-SoVITS 目录里按文件路径加载模块（它们互相用顶层 import，所以临时把目录放进 sys.path）。"""
    with _IMPORT_LOCK:
        cached = sys.modules.get(name)
        if cached is not None:
            return cached
        added = str(extra_path) not in sys.path
        if added:
            sys.path.insert(0, str(extra_path))
        try:
            spec = importlib.util.spec_from_file_location(name, str(path))
            if spec is None or spec.loader is None:
                raise ImportError(f"无法加载 {path}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[name] = mod
            return mod
        finally:
            if added:
                try:
                    sys.path.remove(str(extra_path))
                except ValueError:
                    pass


class ERes2NetV2Encoder(SpeakerEncoder):
    """GPT-SoVITS v2Pro 自带的说话人识别模型（3D-Speaker ERes2NetV2 w24s4ep4）。

    GPT-SoVITS 训练时用它的中间特征（forward3）给音色做条件；这里用的是它本来的用途——说话人识别：
    80 维 Kaldi fbank（16 kHz、dither=0、减去均值，和 3D-Speaker 推理一致）→ forward() 输出 192 维声纹。
    """

    name = "eres2netv2"

    def __init__(self, gsv_root: Path, device: str = "auto") -> None:
        root = Path(gsv_root)
        ckpt = root / SV_CKPT_REL
        eres_dir = root / ERES_DIR_REL
        if not ckpt.exists():
            raise FileNotFoundError(f"没有找到 {ckpt}")
        if not (eres_dir / "ERes2NetV2.py").exists():
            raise FileNotFoundError(f"没有找到 {eres_dir / 'ERes2NetV2.py'}")
        import torch

        mod = _load_module_from(eres_dir / "ERes2NetV2.py", "voicetwin_gsv_ERes2NetV2", eres_dir)
        try:
            from torchaudio.compliance import kaldi as kaldi_mod  # type: ignore
        except Exception:
            kaldi_mod = _load_module_from(eres_dir / "kaldi.py", "voicetwin_gsv_kaldi", eres_dir)
        try:
            state = torch.load(str(ckpt), map_location="cpu", weights_only=False)
        except TypeError:  # 旧版 torch 没有 weights_only 参数
            state = torch.load(str(ckpt), map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state and isinstance(state["state_dict"], dict):
            state = state["state_dict"]
        model = mod.ERes2NetV2(baseWidth=24, scale=4, expansion=4)
        model.load_state_dict(state)
        model.eval()
        self._device = _torch_device(device)
        self._model = model.to(self._device)
        self._kaldi = kaldi_mod
        self._torch = torch
        self._lock = threading.Lock()

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        """一段音频的声纹。长音频（整篇讲课）切成约 10 秒一段分别算，再取平均：
        一次整段送进模型的话，显存/内存跟着长度涨，几分钟的文件就会显存不够（而且出错时不会报出来）。"""
        torch = self._torch
        w16 = resample(np.asarray(wav, dtype=np.float32), sr, 16000)
        trimmed, _, _ = trim_silence(w16, 16000, pad_ms=60)
        if len(trimmed) >= 16000 * 0.5:
            w16 = trimmed
        if len(w16) < 8000:  # 太短的片段重复一下，fbank 至少要几十帧
            w16 = np.tile(w16, int(np.ceil(8000 / max(len(w16), 1)))) if len(w16) else np.zeros(8000, np.float32)
        win = int(16000 * SV_WINDOW_SECONDS)
        chunks = [w16] if len(w16) <= win * 1.2 else list(np.array_split(w16, int(np.ceil(len(w16) / win))))
        if len(chunks) > 1:  # 整段都是静音的窗口（长停顿）不算
            loud = [c for c in chunks if float(np.sqrt(np.mean(np.square(c, dtype=np.float64)))) >= 0.003]
            chunks = loud or chunks
        embs, weights = [], []
        with self._lock, torch.no_grad():
            for ch in chunks:
                x = torch.from_numpy(np.ascontiguousarray(ch, dtype=np.float32)).unsqueeze(0)
                feat = self._kaldi.fbank(x, num_mel_bins=80, sample_frequency=16000, dither=0.0)
                feat = feat - feat.mean(dim=0, keepdim=True)
                emb = self._model(feat.unsqueeze(0).to(self._device))
                embs.append(_l2(emb.reshape(-1).float().cpu().numpy()))
                weights.append(float(len(ch)))
            if len(chunks) > 1 and str(self._device).startswith("cuda"):
                try:  # 把这次多占的显存还回去，别影响接下来的生成
                    torch.cuda.empty_cache()
                except Exception:
                    pass
        if len(embs) == 1:
            return embs[0]
        return _l2(np.average(np.stack(embs), axis=0, weights=np.asarray(weights)))


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


def _choose_centroid_clips(project, max_clips: int = 80) -> List[Dict[str, Any]]:
    records = [r for r in project.load_manifest(only_kept=True) if r.get("split", "train") == "train"]
    records.sort(key=lambda r: (-(r.get("speaker_sim") or 0.0), r["id"]))
    return spread_sample(sorted(records[: max_clips * 2], key=lambda r: r["id"]), max_clips)


def voice_centroid(project, encoder: SpeakerEncoder, max_clips: int = 80, refresh: bool = False) -> Optional[np.ndarray]:
    """你本人声音的"平均声纹"，按声纹模型分别缓存。"""
    path = Path(project.root) / f"speaker_centroid.{encoder.name}.npy"
    if path.exists() and not refresh:
        return np.load(path)
    chosen = _choose_centroid_clips(project, max_clips)
    if not chosen:
        return None
    embs = [encoder.embed_file(project.abspath(r["path"])) for r in chosen]
    cen = centroid(embs)
    np.save(path, cen)
    return cen


# ============================================================================ 多模型一起打分
def gsv_root_from_cfg(cfg: Any) -> Optional[Path]:
    """配置里的 GPT-SoVITS 目录（整合包），没有配置或不存在时返回 None。"""
    try:
        from voicetwin.config import resolve_path

        raw = (cfg.get("backends", {}) or {}).get("gptsovits", {}) or {}
        root = resolve_path(cfg, raw.get("root")) if raw.get("root") else None
        return root if root is not None and root.exists() else None
    except Exception:
        return None


_ENSEMBLE_CACHE: Dict[Tuple[str, str, str], SpeakerEncoder] = {}
_ENSEMBLE_LOCK = threading.Lock()


def _make_encoder(name: str, cfg: Any, device: str) -> SpeakerEncoder:
    if name == "eres2netv2":
        root = gsv_root_from_cfg(cfg)
        if root is None:
            raise FileNotFoundError("没有找到 GPT-SoVITS 目录")
        key = (name, str(root), device)
        with _ENSEMBLE_LOCK:  # 同一时间只加载一次（模型有几十 MB）
            enc = _ENSEMBLE_CACHE.get(key)
            if enc is None:
                enc = ERes2NetV2Encoder(root, device=device)
                _ENSEMBLE_CACHE[key] = enc
            return enc
    if name == "resemblyzer":
        return get_speaker_encoder("resemblyzer") if _has_module("resemblyzer") else _raise(name)
    if name in ("speechbrain", "speechbrain-ecapa"):
        return get_speaker_encoder("speechbrain")
    if name in ("mfcc", "mfcc-stats"):
        return MFCCEncoder()
    raise ValueError(f"未知的声纹模型：{name}")


def _raise(name: str) -> SpeakerEncoder:
    raise ImportError(f"没有安装 {name}")


def _has_module(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def ensemble_names(cfg: Any) -> List[str]:
    """打分要用哪些声纹模型（按配置；auto = ERes2NetV2 + resemblyzer）。"""
    sim_cfg = (cfg.get("similarity") or {}) if hasattr(cfg, "get") else {}
    models = sim_cfg.get("models", "auto")
    if isinstance(models, str) and models not in ("", "auto"):
        models = [m.strip() for m in models.replace("，", ",").split(",") if m.strip()]
    if models in (None, "", "auto"):
        single = str(cfg.get("speaker_encoder", "auto") or "auto").lower() if hasattr(cfg, "get") else "auto"
        if single != "auto":  # 用户（或测试）指定了某一个声纹模型：就只用它
            return [single]
        return ["eres2netv2", "resemblyzer"]
    return [str(m).lower() for m in models]


def get_speaker_ensemble(cfg: Any) -> List[SpeakerEncoder]:
    """能用上的声纹模型列表（至少有一个：实在没有时退回简易 MFCC）。"""
    sim_cfg = (cfg.get("similarity") or {}) if hasattr(cfg, "get") else {}
    device = str(sim_cfg.get("device", "auto") or "auto")
    out: List[SpeakerEncoder] = []
    problems: List[str] = []
    for name in ensemble_names(cfg):
        try:
            enc = _make_encoder(name, cfg, device)
            if all(e.name != enc.name for e in out):
                out.append(enc)
        except Exception as exc:
            problems.append(f"{name}：{exc}")
    reliable = [e for e in out if e.reliable]
    if reliable:
        out = reliable  # 有正经的声纹模型时，不再把简易 MFCC 混进平均值
    if not out:
        out = [MFCCEncoder()]
        if problems:
            log.warning("声纹打分模型都用不了，改用简易 MFCC（仅供参考）：" + "；".join(problems))
    elif problems:
        log.info("部分声纹模型没有用上：" + "；".join(problems))
    return out


def pct_from_sim(sim: Optional[float], p50: Optional[float]) -> Optional[float]:
    """把余弦相似度换算成"像你本人"百分比：100 × min(1, s / p50_real)，保留一位小数。"""
    if sim is None or p50 is None or not np.isfinite(sim) or p50 <= 0:
        return None
    return round(100.0 * float(min(1.0, max(0.0, sim) / p50)), 1)


def status_for_pct(pct: Optional[float], min_pct: float = MIN_PCT_DEFAULT) -> str:
    """✅ ≥95 / 🟢 85~95 / 🔴 <85（没有分数时返回空字符串）。"""
    if pct is None:
        return ""
    if pct >= 95.0:
        return "✅"
    if pct >= min_pct:
        return "🟢"
    return "🔴"


def _manifest_sig(project) -> str:
    from voicetwin.utils.textutil import short_hash

    recs = project.load_manifest(only_kept=True)
    return short_hash(sorted((r["id"], r.get("split", "train")) for r in recs), n=12)


def judge_centroid(project, encoder: SpeakerEncoder, refresh: bool = False,
                   max_clips: int = 80) -> Tuple[Optional[np.ndarray], List[str]]:
    """打分用的"平均声纹"：只用训练片段（验证集留给校准，保证校准是公平的）。素材变了会自动重算。"""
    root = Path(project.root)
    path = root / f"speaker_centroid.{encoder.name}.judge.npy"
    meta_path = root / f"speaker_centroid.{encoder.name}.judge.json"
    sig = _manifest_sig(project)
    if path.exists() and meta_path.exists() and not refresh:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("sig") == sig:
                return np.load(path), list(meta.get("ids") or [])
        except Exception:
            pass
    chosen = _choose_centroid_clips(project, max_clips)
    if not chosen:
        return None, []
    embs = [encoder.embed_file(project.abspath(r["path"])) for r in chosen]
    cen = centroid(embs)
    np.save(path, cen)
    ids = [r["id"] for r in chosen]
    meta_path.write_text(json.dumps({"sig": sig, "ids": ids}, ensure_ascii=False), encoding="utf-8")
    return cen, ids


def _calibration_records(project, used_ids: Sequence[str] = ()) -> Tuple[List[Dict[str, Any]], str]:
    """校准用的真实录音：优先验证集；不够 3 条时用没参与平均声纹的训练片段；再不够就用全部。"""
    recs = project.load_manifest(only_kept=True)
    used = set(used_ids)
    val = [r for r in recs if r.get("split") == "val"]
    if len(val) >= 3:
        return val, "val"
    val = [r for r in recs if r["id"] not in used]
    if len(val) >= 3:
        return val, "train_unused"
    return list(recs), "train"


def calibrate(project, encoder: SpeakerEncoder, cen: np.ndarray, used_ids: Sequence[str] = (),
              refresh: bool = False, max_clips: int = 40) -> Dict[str, Any]:
    """你自己的真实录音和"平均声纹"有多像：p10 / p50 / p90（每个声纹模型分别算，结果缓存）。

    优先用验证集（没参与训练、也没参与平均声纹的片段）；不够 3 条时，用没参与平均声纹的训练片段代替。
    """
    from voicetwin.utils.textutil import short_hash

    root = Path(project.root)
    cache_path = root / CALIBRATION_FILE
    val, source = _calibration_records(project, used_ids)
    val = spread_sample(sorted(val, key=lambda r: r["id"]), max_clips)
    sig = short_hash(encoder.name, np.round(np.asarray(cen, dtype=np.float64), 5).tolist(),
                     sorted(r["id"] for r in val), n=12)
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    except Exception:
        cache = {}
    entry = cache.get(encoder.name)
    if entry and entry.get("sig") == sig and not refresh:
        return entry
    sims = []
    for r in val:
        try:
            sims.append(cosine(encoder.embed_file(project.abspath(r["path"])), cen))
        except Exception as exc:  # 个别片段读不了不影响
            log.debug(f"校准时跳过 {r.get('id')}：{exc}")
    if not sims:
        return {"p10": None, "p50": None, "p90": None, "n": 0, "source": source, "sig": sig}
    arr = np.asarray(sims, dtype=np.float64)
    entry = {"p10": round(float(np.percentile(arr, 10)), 4), "p50": round(float(np.median(arr)), 4),
             "p90": round(float(np.percentile(arr, 90)), 4), "n": int(arr.size), "source": source, "sig": sig}
    if entry["p50"] is not None and entry["p50"] <= 0.05:
        entry["p50"] = None  # 模型完全分不出来（几乎不可能）：不换算百分比
    cache[encoder.name] = entry
    try:
        tmp = cache_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(cache_path)
    except OSError:
        pass
    return entry


@dataclass
class JudgeMember:
    encoder: SpeakerEncoder
    centroid: np.ndarray
    calib: Dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.encoder.name

    @property
    def p50(self) -> Optional[float]:
        val = self.calib.get("p50")
        return float(val) if isinstance(val, (int, float)) and val > 0 else None


class SimilarityJudge:
    """几个声纹模型一起给一段音频打"像你本人（%）"。没有任何模型可用时 available=False，judge() 返回空结果。"""

    def __init__(self, members: Sequence[JudgeMember]):
        self.members: List[JudgeMember] = list(members)

    # ------------------------------------------------------------------ 构造
    @classmethod
    def for_project(cls, cfg: Any, project, encoders: Optional[Sequence[SpeakerEncoder]] = None,
                    progress: Optional[ProgressFn] = None) -> "SimilarityJudge":
        members: List[JudgeMember] = []
        for enc in (encoders if encoders is not None else get_speaker_ensemble(cfg)):
            try:
                if progress is not None:
                    try:
                        progress(0.0, f"准备声纹打分模型 {MODEL_LABELS.get(enc.name, enc.name)}……")
                    except Exception:
                        pass
                cen, ids = judge_centroid(project, enc)
                if cen is None:
                    continue
                members.append(JudgeMember(enc, cen, calibrate(project, enc, cen, ids)))
            except Exception as exc:
                log.warning(f"声纹模型 {enc.name} 打分不可用：{exc}")
        return cls(members)

    @classmethod
    def from_files(cls, cfg: Any, files: Sequence[Path], fallback: Optional["SimilarityJudge"] = None,
                   encoders: Optional[Sequence[SpeakerEncoder]] = None, project: Any = None,
                   max_clips: int = 20) -> "SimilarityJudge":
        """用你挑的几段原声当"标准"。

        - ≥3 段：留一法校准（每段和其它几段的平均声纹比）。
        - 1~2 段：给了 project 时，用这个声音素材里留出来的真实录音和这 1~2 段的平均声纹比，得到「100%」的标准
          （打分和校准用同一个标准）。不能借用这个声音原来的校准：那是和几十段的平均声纹比出来的，
          和 1~2 段比天然偏低，百分比会系统性地偏小。
        - 上面都做不到：直接用这个声音原来的标准（fallback：它自己的平均声纹 + 校准，source = voice_calibration），
          这时上传的原声只当参考、不参与打分；连 fallback 也没有时只给原始相似度、不换算百分比。"""
        members: List[JudgeMember] = []
        uploaded = set()
        for f in files:
            try:
                uploaded.add(str(Path(f).resolve()))
            except OSError:
                uploaded.add(str(f))
        for enc in (encoders if encoders is not None else get_speaker_ensemble(cfg)):
            try:
                embs = [enc.embed_file(Path(f)) for f in files]
            except Exception as exc:
                log.warning(f"声纹模型 {enc.name} 读不了原声：{exc}")
                continue
            if not embs:
                continue
            cen = centroid(embs)
            calib: Dict[str, Any] = {"p50": None, "n": len(embs), "source": "uploaded"}
            if len(embs) >= 3:
                loo = [cosine(e, centroid([x for j, x in enumerate(embs) if j != i])) for i, e in enumerate(embs)]
                arr = np.asarray(loo, dtype=np.float64)
                calib.update({"p10": round(float(np.percentile(arr, 10)), 4), "p50": round(float(np.median(arr)), 4),
                              "p90": round(float(np.percentile(arr, 90)), 4), "source": "uploaded_loo"})
                members.append(JudgeMember(enc, cen, calib))
                continue
            if project is not None:
                sims: List[float] = []
                try:
                    # 这里的平均声纹只来自上传的原声，所以素材里别的片段（验证集优先，不够再加训练片段）都能拿来校准
                    recs = [r for r in project.load_manifest(only_kept=True)
                            if str(Path(project.abspath(r["path"])).resolve()) not in uploaded]
                    val = sorted((r for r in recs if r.get("split") == "val"), key=lambda r: r["id"])
                    rest = sorted((r for r in recs if r.get("split") != "val"), key=lambda r: r["id"])
                    pick = spread_sample(val, max_clips)
                    pick += spread_sample(rest, max_clips - len(pick)) if len(pick) < max_clips else []
                    for r in pick:
                        try:
                            sims.append(cosine(enc.embed_file(project.abspath(r["path"])), cen))
                        except Exception as exc:
                            log.debug(f"校准时跳过 {r.get('id')}：{exc}")
                except Exception as exc:
                    log.debug(f"用素材里的录音校准失败：{exc}")
                if len(sims) >= 3 and float(np.median(sims)) > 0.05:
                    arr = np.asarray(sims, dtype=np.float64)
                    calib.update({"p10": round(float(np.percentile(arr, 10)), 4),
                                  "p50": round(float(np.median(arr)), 4),
                                  "p90": round(float(np.percentile(arr, 90)), 4), "n_clips": int(arr.size),
                                  "source": "voice_clips_vs_uploaded"})
                    members.append(JudgeMember(enc, cen, calib))
                    continue
            other = next((m for m in fallback.members if m.name == enc.name), None) if fallback is not None else None
            if other is not None and other.p50 is not None:
                members.append(JudgeMember(enc, other.centroid, dict(other.calib, source="voice_calibration")))
                continue
            members.append(JudgeMember(enc, cen, calib))
        return cls(members)

    # ------------------------------------------------------------------ 信息
    @property
    def available(self) -> bool:
        return bool(self.members)

    @property
    def models(self) -> List[str]:
        return [m.name for m in self.members]

    @property
    def reliable(self) -> bool:
        return any(m.encoder.reliable for m in self.members)

    @property
    def calibrated(self) -> bool:
        return any(m.p50 is not None for m in self.members)

    def info(self) -> Dict[str, Any]:
        return {
            "models": self.models,
            "labels": [MODEL_LABELS.get(n, n) for n in self.models],
            "reliable": self.reliable,
            "calibration": {m.name: {k: m.calib.get(k) for k in ("p10", "p50", "p90", "n", "n_clips", "source")}
                            for m in self.members},
            "definition": PCT_HELP,
            "note": HONEST_NOTE,
        }

    # ------------------------------------------------------------------ 打分
    def judge_embeddings(self, embs: Dict[str, np.ndarray]) -> Dict[str, Any]:
        sims: Dict[str, float] = {}
        pcts: Dict[str, float] = {}
        for m in self.members:
            emb = embs.get(m.name)
            if emb is None:
                continue
            s = cosine(emb, m.centroid)
            sims[m.name] = round(s, 4)
            p = pct_from_sim(s, m.p50)
            if p is not None:
                pcts[m.name] = p
        pct = round(float(np.mean(list(pcts.values()))), 1) if pcts else None
        first = next(iter(sims.values()), None)
        return {"pct": pct, "pcts": pcts, "sims": sims, "sim": first}

    def embed(self, wav: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        out: Dict[str, np.ndarray] = {}
        for m in self.members:
            try:
                out[m.name] = m.encoder.embed(wav, sr)
            except Exception as exc:
                log.debug(f"{m.name} 打分失败：{exc}")
        return out

    def judge(self, wav: np.ndarray, sr: int) -> Dict[str, Any]:
        if not self.members or wav is None or len(wav) < sr * 0.3:
            return {"pct": None, "pcts": {}, "sims": {}, "sim": None}
        return self.judge_embeddings(self.embed(wav, sr))

    def judge_file(self, path: Path) -> Dict[str, Any]:
        wav, sr = load_audio(path, sr=16000)
        return self.judge(wav, sr)
