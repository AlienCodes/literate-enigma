"""声纹（音色）向量：用来衡量"像不像你"。

给合成结果打"像你本人（%）"（SimilarityJudge）——v0.1.7 起的精准打分（实测见 docs/声纹打分准确度.md）：
1. 只看人声：原声和生成的声音都先用同一个人声检测模型（silero-vad）去掉停顿，
   停顿是绝对静音还是有环境声都不影响分数（sv_frontend.py）；
2. 几个公开测试里最准的声纹模型一起打分（ReDimNet2-B6、3D-Speaker CAM++ / ERes2NetV2，sv_models.py）；
3. 分数归一化（AS-norm）：每个分数都和一大批"陌生人"的声音比过，去掉"这段声音和谁都有点像"的偏差；
4. 百分比两头校准：0% = 陌生人的水平，100% = 你自己没参与平均声纹的真实录音（验证集）的中位数，
   每个模型分别校准再取平均。
这几个模型没下载时，退回旧的打分方式：
- GPT-SoVITS v2Pro 整合包自带的 ERes2NetV2（GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt）
  + resemblyzer，像你本人 = 100 × min(1, s / p50_real)；都没有时用 MFCC（仅供参考）。

单个声纹模型（素材准备时剔除"不是你本人"的片段用），依次尝试：
1. resemblyzer —— 模型权重随 pip 包附带，离线可用，轻量；
2. speechbrain ECAPA —— 精度更高，首次使用需下载（国内可设 HF_ENDPOINT=https://hf-mirror.com）；
3. MFCC 统计量 —— 最后的兜底，只能粗略比较，不用于自动剔除片段。

相似度是声纹模型自动打分，越高越像，但不是绝对精确，最终以耳朵为准。
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
PCT_HELP = "100% = 和你自己的真实录音一样像，0% = 陌生人的水平"
HONEST_NOTE = "相似度是几个声纹模型一起自动打分，越高越像；机器打分不可能百分之百准确，最终以耳朵为准"
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


class OnnxSVEncoder(SpeakerEncoder):
    """v0.1.7 起的精准声纹模型（ONNX，CPU）：先用人声检测去掉停顿，再算声纹。

    几个模型共用同一个人声检测（vad），SimilarityJudge 对同一段音频只做一次人声检测（prepare），
    再交给每个模型（embed_prepared）。"""

    reliable = True

    def __init__(self, spec: Any, path: Path, vad: Any) -> None:
        from voicetwin.eval.sv_models import OnnxEmbedder

        self.spec = spec
        self.name = spec.key
        self._model = OnnxEmbedder(spec, path)
        self._vad = vad

    @property
    def prep_key(self) -> Tuple[str, int]:
        return ("speech16k", id(self._vad))

    def prepare(self, wav: np.ndarray, sr: int) -> np.ndarray:
        return self._vad.speech_only(resample(np.asarray(wav, dtype=np.float32), sr, 16000))

    def embed_prepared(self, speech: np.ndarray) -> np.ndarray:
        return _l2(self._model.embed16k(speech))

    def embed(self, wav: np.ndarray, sr: int) -> np.ndarray:
        return self.embed_prepared(self.prepare(wav, sr))


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
        try:
            return np.load(path)
        except Exception as exc:  # noqa: BLE001 - 半个文件（断电、硬盘满了）：重新算
            log.warning(f"平均声纹缓存读不了（{exc}），重新计算")
    chosen = _choose_centroid_clips(project, max_clips)
    if not chosen:
        return None
    embs = [encoder.embed_file(project.abspath(r["path"])) for r in chosen]
    cen = centroid(embs)
    _save_npy_atomic(path, cen)
    return cen


def _save_npy_atomic(path: Path, arr: np.ndarray) -> None:
    """先写临时文件再换上去：不会留下半个文件。"""
    from voicetwin.utils import atomic

    tmp = atomic.tmp_for(path).with_suffix(".npy")
    try:
        np.save(tmp, arr)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    atomic.finish(tmp, path)


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


#: similarity.models = auto 时排在第一位：先用精准声纹模型（sv_models.DEFAULT_ENSEMBLE），一个都用不了才用后面的旧模型
SV_AUTO = "sv-auto"


def _vad_for(cfg: Any) -> Any:
    from voicetwin.eval import sv_models
    from voicetwin.eval.sv_frontend import SileroVAD

    path = sv_models.model_dir(cfg) / sv_models.VAD_MODEL.file
    if not sv_models.file_ok(sv_models.VAD_MODEL, path, deep=True):
        raise FileNotFoundError(f"人声检测模型还没下载或文件不完整（{path}）")
    key = ("silero-vad", str(path), "cpu")
    with _ENSEMBLE_LOCK:
        vad = _ENSEMBLE_CACHE.get(key)
        if vad is None:
            vad = SileroVAD(path)
            _ENSEMBLE_CACHE[key] = vad
        return vad


def _onnx_encoder(name: str, cfg: Any) -> SpeakerEncoder:
    from voicetwin.eval import sv_models

    spec = sv_models.MODELS[name]
    path = sv_models.model_dir(cfg) / spec.file
    if not sv_models.file_ok(spec, path):
        raise FileNotFoundError(f"声纹模型 {spec.label} 还没下载（{path}）")
    if not sv_models.file_ok(spec, path, deep=True):  # 每个文件每次运行核对一次（sha256 / 自检）
        raise FileNotFoundError(f"声纹模型 {spec.label} 的文件核对不通过（下载坏了？），请重新下载（{path}）")
    vad = _vad_for(cfg)
    key = (name, str(path), "cpu")
    with _ENSEMBLE_LOCK:
        enc = _ENSEMBLE_CACHE.get(key)
        if enc is None:
            enc = OnnxSVEncoder(spec, path, vad)
            _ENSEMBLE_CACHE[key] = enc
        return enc


def _make_encoder(name: str, cfg: Any, device: str) -> SpeakerEncoder:
    from voicetwin.eval.sv_models import MODELS

    if name in MODELS:
        return _onnx_encoder(name, cfg)
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
    """打分要用哪些声纹模型（按配置）。auto = 先用精准声纹模型（sv-auto），没下载时用 ERes2NetV2 + resemblyzer。"""
    sim_cfg = (cfg.get("similarity") or {}) if hasattr(cfg, "get") else {}
    models = sim_cfg.get("models", "auto")
    if isinstance(models, str) and models not in ("", "auto"):
        models = [m.strip() for m in models.replace("，", ",").split(",") if m.strip()]
    if models in (None, "", "auto"):
        single = str(cfg.get("speaker_encoder", "auto") or "auto").lower() if hasattr(cfg, "get") else "auto"
        if single != "auto":  # 用户（或测试）指定了某一个声纹模型：就只用它
            return [single]
        return [SV_AUTO, "eres2netv2", "resemblyzer"]
    return [str(m).lower() for m in models]


def get_speaker_ensemble(cfg: Any) -> List[SpeakerEncoder]:
    """能用上的声纹模型列表（至少有一个：实在没有时退回简易 MFCC）。"""
    sim_cfg = (cfg.get("similarity") or {}) if hasattr(cfg, "get") else {}
    device = str(sim_cfg.get("device", "auto") or "auto")
    out: List[SpeakerEncoder] = []
    problems: List[str] = []
    names = ensemble_names(cfg)
    if names and names[0] == SV_AUTO:
        from voicetwin.eval.sv_models import ensemble_keys

        for key in ensemble_keys(cfg):
            try:
                out.append(_onnx_encoder(key, cfg))
            except Exception as exc:
                problems.append(f"{key}：{exc}")
        if out:  # 精准声纹模型能用：只用它们（旧模型准确度差很多，混进平均值反而拉低准确度）
            if problems:
                log.warning("部分精准声纹模型没有用上（可以点「⬇️ 下载缺少的模型」补上）：" + "；".join(problems))
            return out
        log.info("精准声纹模型还没下载，先用旧的打分方式（" + "；".join(problems) + "）")
        problems = []
        names = names[1:]
    for name in names:
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


# ============================================================================ 陌生人声纹库（AS-norm 和 0% 的标准）
#: 程序附带的"陌生人声纹库"：每个精准声纹模型一份（几百个不同的人，中文 + 英文），只有声纹向量，没有声音
COHORT_FILE = Path(__file__).with_name("sv_cohort.npz")
#: AS-norm 取和这段声音最像的多少个陌生人
AS_NORM_TOPK = 100
#: 短句子单独校准的长度（秒，只算人声）：你自己的真实录音截成这么长，作为同样长的句子的「100%」
SHORT_SECONDS = (1.5, 3.0)
#: 人声不到这么多秒时，分数只能粗略参考
SHORT_WARN_SECONDS = 2.0
#: 校准方法改了就加 1（缓存的校准结果作废，重新算）
CALIB_VERSION = 2
#: 0% 的标准：陌生人里第几百分位的分数（95 = 比 95% 的陌生人都像才开始算分；见 docs/声纹打分准确度.md）
IMPOSTOR_PERCENTILE = 95.0
_COHORT_CACHE: Dict[str, Optional[Dict[str, np.ndarray]]] = {}


def load_cohort(name: str, path: Optional[Path] = None) -> Optional[Dict[str, np.ndarray]]:
    """某个声纹模型的陌生人声纹库：{"emb": (N, d) 单位向量, "mu"/"sd": 每个陌生人自己的 AS-norm 统计量}。
    没有这个模型的库（或库和模型对不上）时返回 None，这个模型就只用余弦相似度。"""
    key = f"{path or COHORT_FILE}|{name}"
    if key in _COHORT_CACHE:
        return _COHORT_CACHE[key]
    out: Optional[Dict[str, np.ndarray]] = None
    try:
        with np.load(str(path or COHORT_FILE), allow_pickle=False) as data:
            if f"{name}__emb" in data.files:
                emb = np.asarray(data[f"{name}__emb"], dtype=np.float32)
                emb = emb / np.maximum(np.linalg.norm(emb, axis=1, keepdims=True), 1e-9)
                out = {"emb": emb}
                for extra in ("mu", "sd", "zh"):
                    if f"{name}__{extra}" in data.files:
                        out[extra] = np.asarray(data[f"{name}__{extra}"])
                if "mu" not in out or "sd" not in out:
                    out["mu"], out["sd"] = cohort_self_stats(emb)
    except (OSError, ValueError, KeyError) as exc:
        log.debug(f"陌生人声纹库读不了：{exc}")
        out = None
    _COHORT_CACHE[key] = out
    return out


def topk_stats(emb: np.ndarray, cohort: np.ndarray, topk: int = AS_NORM_TOPK) -> Tuple[float, float]:
    """一段声音和陌生人声纹库里最像的 topk 个人的平均分、标准差（AS-norm 用）。"""
    s = cohort @ _l2(emb)
    k = int(min(topk, s.size))
    top = np.partition(s, s.size - k)[s.size - k:]
    return float(top.mean()), float(top.std() + 1e-6)


def cohort_self_stats(cohort: np.ndarray, topk: int = AS_NORM_TOPK) -> Tuple[np.ndarray, np.ndarray]:
    """库里每个陌生人自己的 AS-norm 统计量（不和自己比）。"""
    s = cohort @ cohort.T
    np.fill_diagonal(s, -np.inf)
    k = int(min(topk, s.shape[1] - 1))
    top = np.sort(s, axis=1)[:, -k:]
    return top.mean(axis=1).astype(np.float32), (top.std(axis=1) + 1e-6).astype(np.float32)


def as_norm(score: float, enroll: Tuple[float, float], test: Tuple[float, float]) -> float:
    return 0.5 * ((score - enroll[0]) / enroll[1] + (score - test[0]) / test[1])


def impostor_scores(cohort: Dict[str, np.ndarray], cen: np.ndarray) -> np.ndarray:
    """库里每个陌生人和你的平均声纹比的分数（AS-norm 后）：用来定 0% 的标准。"""
    c = _l2(cen)
    enroll = topk_stats(c, cohort["emb"])
    s = cohort["emb"] @ c
    return 0.5 * ((s - enroll[0]) / enroll[1] + (s - cohort["mu"]) / cohort["sd"])


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
    _save_npy_atomic(path, cen)
    ids = [r["id"] for r in chosen]
    from voicetwin.utils import atomic

    atomic.write_text(meta_path, json.dumps({"sig": sig, "ids": ids}, ensure_ascii=False))
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


def _cohort_sig(cohort: Optional[Dict[str, np.ndarray]]) -> str:
    if cohort is None:
        return ""
    emb = cohort["emb"]
    return f"{emb.shape[0]}x{emb.shape[1]}:{float(np.round(emb[:3].sum(), 5))}:{AS_NORM_TOPK}:{IMPOSTOR_PERCENTILE}"


def calibration_stats(cos_scores: Sequence[float], norm_scores: Optional[Sequence[float]] = None,
                      impostors: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """校准数字：你自己的真实录音（cos_scores / norm_scores）和陌生人（impostors）的分数分布。

    p10/p50/p90：余弦相似度（旧的打分方式、挑选模型时用）；
    g10/g50/g90：AS-norm 后的分数，g50 就是「100%」；i0：陌生人第 95 百分位的分数，就是「0%」。"""
    arr = np.asarray(list(cos_scores), dtype=np.float64)
    out: Dict[str, Any] = {"p10": None, "p50": None, "p90": None, "n": int(arr.size)}
    if arr.size:
        out.update({"p10": round(float(np.percentile(arr, 10)), 4), "p50": round(float(np.median(arr)), 4),
                    "p90": round(float(np.percentile(arr, 90)), 4)})
        if out["p50"] is not None and out["p50"] <= 0.05:
            out["p50"] = None  # 模型完全分不出来（几乎不可能）：不换算百分比
    if norm_scores is not None and impostors is not None and len(norm_scores) and np.size(impostors):
        g = np.asarray(list(norm_scores), dtype=np.float64)
        imp = np.asarray(impostors, dtype=np.float64)
        g50, i0 = float(np.median(g)), float(np.percentile(imp, IMPOSTOR_PERCENTILE))
        if g50 - i0 > 0.5:  # 你自己的录音明显比陌生人像：才按两头校准换算
            out.update({"norm": "asnorm", "g10": round(float(np.percentile(g, 10)), 4),
                        "g25": round(float(np.percentile(g, 25)), 4), "g50": round(g50, 4),
                        "g90": round(float(np.percentile(g, 90)), 4), "i0": round(i0, 4),
                        "i50": round(float(np.median(imp)), 4), "n_impostors": int(imp.size)})
    return out


def calibrate(project, encoder: SpeakerEncoder, cen: np.ndarray, used_ids: Sequence[str] = (),
              refresh: bool = False, max_clips: int = 40,
              cohort: Optional[Dict[str, np.ndarray]] = None) -> Dict[str, Any]:
    """你自己的真实录音和"平均声纹"有多像（每个声纹模型分别算，结果缓存）。

    优先用验证集（没参与训练、也没参与平均声纹的片段）；不够 3 条时，用没参与平均声纹的训练片段代替。
    有陌生人声纹库（cohort）时同时算 AS-norm 后的分数和陌生人的分数，百分比按两头校准。
    """
    from voicetwin.utils.textutil import short_hash

    root = Path(project.root)
    cache_path = root / CALIBRATION_FILE
    val, source = _calibration_records(project, used_ids)
    val = spread_sample(sorted(val, key=lambda r: r["id"]), max_clips)
    sig = short_hash(encoder.name, np.round(np.asarray(cen, dtype=np.float64), 5).tolist(),
                     sorted(r["id"] for r in val), _cohort_sig(cohort), CALIB_VERSION if cohort is not None else 1, n=12)
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    except Exception:
        cache = {}
    entry = cache.get(encoder.name)
    if entry and entry.get("sig") == sig and not refresh:
        return entry
    member = JudgeMember(encoder, cen, {}, cohort)
    sims: List[float] = []
    norms: List[float] = []
    lengths: List[float] = []
    short: Dict[float, List[float]] = {b: [] for b in SHORT_SECONDS}
    can_crop = cohort is not None and hasattr(encoder, "prepare") and hasattr(encoder, "embed_prepared")
    for r in val:
        try:
            if can_crop:  # 同时算截短的版本：短句子要和"同样长的你自己的录音"比
                wav, sr = load_audio(project.abspath(r["path"]), sr=16000)
                speech = encoder.prepare(wav, sr)
                emb = encoder.embed_prepared(speech)
                lengths.append(speech.size / 16000.0)
                for b in SHORT_SECONDS:
                    if speech.size >= int(b * 16000) * 1.3:
                        mid = (speech.size - int(b * 16000)) // 2
                        short[b].append(member.norm_score(encoder.embed_prepared(speech[mid:mid + int(b * 16000)])))
            else:
                emb = encoder.embed_file(project.abspath(r["path"]))
        except Exception as exc:  # 个别片段读不了不影响
            log.debug(f"校准时跳过 {r.get('id')}：{exc}")
            continue
        sims.append(cosine(emb, cen))
        if cohort is not None:
            norms.append(member.norm_score(emb))
    if not sims:
        return {"p10": None, "p50": None, "p90": None, "n": 0, "source": source, "sig": sig}
    entry = calibration_stats(sims, norms if cohort is not None else None,
                              impostor_scores(cohort, cen) if cohort is not None else None)
    if entry.get("norm") == "asnorm" and lengths:
        table = {f"{b:g}": round(float(np.median(v)), 4) for b, v in short.items() if len(v) >= 3}
        if table:
            entry["g50_short"] = table
            entry["full_seconds"] = round(float(np.median(lengths)), 2)
    entry.update({"source": source, "sig": sig})
    cache[encoder.name] = entry
    try:
        from voicetwin.utils import atomic

        atomic.write_text(cache_path, json.dumps(cache, ensure_ascii=False, indent=1))
    except OSError:
        pass
    return entry


def _clamp_pct(value: float) -> float:
    return round(float(min(100.0, max(0.0, value))), 1)


@dataclass
class JudgeMember:
    encoder: SpeakerEncoder
    centroid: np.ndarray
    calib: Dict[str, Any] = field(default_factory=dict)
    cohort: Optional[Dict[str, np.ndarray]] = None
    _enroll: Optional[Tuple[float, float]] = field(default=None, repr=False, compare=False)

    @property
    def name(self) -> str:
        return self.encoder.name

    @property
    def p50(self) -> Optional[float]:
        val = self.calib.get("p50")
        return float(val) if isinstance(val, (int, float)) and val > 0 else None

    @property
    def two_sided(self) -> bool:
        """百分比按两头校准（0% = 陌生人，100% = 你自己的真实录音）？"""
        g50, i0 = self.calib.get("g50"), self.calib.get("i0")
        return (self.cohort is not None and self.calib.get("norm") == "asnorm"
                and isinstance(g50, (int, float)) and isinstance(i0, (int, float)) and g50 > i0)

    def norm_score(self, emb: np.ndarray, ref: Optional[np.ndarray] = None) -> float:
        """和平均声纹（或 ref）的分数：有陌生人声纹库时是 AS-norm 后的分数，否则是余弦相似度。"""
        target = self.centroid if ref is None else ref
        s = cosine(emb, target)
        if self.cohort is None:
            return s
        if ref is None:
            if self._enroll is None:
                self._enroll = topk_stats(self.centroid, self.cohort["emb"])
            enroll = self._enroll
        else:
            enroll = topk_stats(ref, self.cohort["emb"])
        return as_norm(s, enroll, topk_stats(emb, self.cohort["emb"]))

    def g50_for(self, seconds: Optional[float] = None) -> float:
        """「100%」的标准：一般是你自己真实录音的中位数；句子很短时，用你自己的录音截成同样长度的中位数
        （短句子的声纹天然没那么稳，不这样的话短句子会系统性地偏低十几个百分点）。"""
        g50 = float(self.calib["g50"])
        table = self.calib.get("g50_short") or {}
        full = self.calib.get("full_seconds")
        if seconds is None or not table or not isinstance(full, (int, float)):
            return g50
        pts = sorted([(float(k), float(v)) for k, v in table.items() if float(k) < float(full)] + [(float(full), g50)])
        xs = np.array([p[0] for p in pts])
        ys = np.maximum.accumulate(np.array([p[1] for p in pts]))  # 越长越稳：标准只会随长度变高
        return float(np.interp(float(seconds), xs, ys))

    def pct_raw(self, emb: np.ndarray, seconds: Optional[float] = None) -> Optional[float]:
        """没有封顶的"像你本人"（可以超过 100，也可以是负数）；没校准时返回 None。seconds：这段声音里人声有几秒。"""
        if self.two_sided:
            g50, i0 = self.g50_for(seconds), float(self.calib["i0"])
            if g50 <= i0:
                g50 = float(self.calib["g50"])
            return 100.0 * (self.norm_score(emb) - i0) / (g50 - i0)
        p50 = self.p50
        if p50 is None:
            return None
        return 100.0 * max(0.0, cosine(emb, self.centroid)) / p50


def cohort_for(enc: SpeakerEncoder) -> Optional[Dict[str, np.ndarray]]:
    """精准声纹模型的陌生人声纹库（旧模型没有）。"""
    return load_cohort(enc.name) if isinstance(enc, OnnxSVEncoder) else None


def model_label(name: str) -> str:
    if name in MODEL_LABELS:
        return MODEL_LABELS[name]
    try:
        from voicetwin.eval.sv_models import MODELS

        return MODELS[name].label if name in MODELS else name
    except Exception:
        return name


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
                        progress(0.0, f"准备声纹打分模型 {model_label(enc.name)}……")
                    except Exception:
                        pass
                cen, ids = judge_centroid(project, enc)
                if cen is None:
                    continue
                cohort = cohort_for(enc)
                members.append(JudgeMember(enc, cen, calibrate(project, enc, cen, ids, cohort=cohort), cohort))
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
            cohort = cohort_for(enc)
            impostors = impostor_scores(cohort, cen) if cohort is not None else None
            calib: Dict[str, Any] = {"p50": None, "n": len(embs), "source": "uploaded"}
            if len(embs) >= 3:
                loo_cos: List[float] = []
                loo_norm: List[float] = []
                for i, e in enumerate(embs):
                    other_cen = centroid([x for j, x in enumerate(embs) if j != i])
                    loo_cos.append(cosine(e, other_cen))
                    if cohort is not None:
                        loo_norm.append(JudgeMember(enc, other_cen, {}, cohort).norm_score(e))
                calib.update(calibration_stats(loo_cos, loo_norm if cohort is not None else None, impostors))
                calib.update({"n": len(embs), "source": "uploaded_loo"})
                members.append(JudgeMember(enc, cen, calib, cohort))
                continue
            if project is not None:
                sims: List[float] = []
                norms: List[float] = []
                probe = JudgeMember(enc, cen, {}, cohort)
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
                            emb = enc.embed_file(project.abspath(r["path"]))
                        except Exception as exc:
                            log.debug(f"校准时跳过 {r.get('id')}：{exc}")
                            continue
                        sims.append(cosine(emb, cen))
                        if cohort is not None:
                            norms.append(probe.norm_score(emb))
                except Exception as exc:
                    log.debug(f"用素材里的录音校准失败：{exc}")
                if len(sims) >= 3 and float(np.median(sims)) > 0.05:
                    calib.update(calibration_stats(sims, norms if cohort is not None else None, impostors))
                    calib.update({"n": len(embs), "n_clips": len(sims), "source": "voice_clips_vs_uploaded"})
                    members.append(JudgeMember(enc, cen, calib, cohort))
                    continue
            other = next((m for m in fallback.members if m.name == enc.name), None) if fallback is not None else None
            if other is not None and (other.p50 is not None or other.two_sided):
                members.append(JudgeMember(enc, other.centroid, dict(other.calib, source="voice_calibration"),
                                           other.cohort))
                continue
            members.append(JudgeMember(enc, cen, calib, cohort))
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
        return any(m.p50 is not None or m.two_sided for m in self.members)

    @property
    def precise(self) -> bool:
        """用的是 v0.1.7 的精准打分（精准声纹模型 + 陌生人声纹库 + 两头校准）？"""
        return bool(self.members) and all(m.two_sided for m in self.members)

    def info(self) -> Dict[str, Any]:
        keys = ("p10", "p50", "p90", "g10", "g25", "g50", "g90", "i0", "i50", "norm", "n", "n_clips", "n_impostors",
                "source")
        return {
            "models": self.models,
            "labels": [model_label(n) for n in self.models],
            "reliable": self.reliable,
            "precise": self.precise,
            "calibration": {m.name: {k: m.calib.get(k) for k in keys if k in m.calib} for m in self.members},
            "natural_range": self.natural_range(),
            "definition": PCT_HELP,
            "note": HONEST_NOTE,
        }

    def signature(self) -> str:
        """打分标准的"指纹"：模型、平均声纹、校准有任何变化都会变（以前生成好的句子据此决定要不要重新打分）。"""
        from voicetwin.utils.textutil import short_hash

        return short_hash([(m.name, m.calib.get("sig"), m.calib.get("norm"), m.calib.get("g50"), m.calib.get("i0"),
                            m.calib.get("p50")) for m in self.members], n=12)

    def natural_range(self) -> Optional[Dict[str, float]]:
        """你自己的真实录音（验证集）换算成"像你本人"是多少：{"p10", "p25", "p50"=100, "p90"}（几个模型的平均）。
        真人录音本身就有波动——生成的句子落在这个范围里，声纹模型就分不出它和你的真实录音。"""
        rows = []
        for m in self.members:
            if not m.two_sided:
                continue
            g50, i0 = float(m.calib["g50"]), float(m.calib["i0"])
            vals = {}
            for k in ("g10", "g25", "g90"):
                v = m.calib.get(k)
                if isinstance(v, (int, float)):
                    vals["p" + k[1:]] = 100.0 * (float(v) - i0) / (g50 - i0)
            if vals:
                rows.append(vals)
        if not rows:
            return None
        out = {k: round(float(np.mean([r[k] for r in rows if k in r])), 1)
               for k in ("p10", "p25", "p90") if any(k in r for r in rows)}
        out["p50"] = 100.0
        return out

    # ------------------------------------------------------------------ 打分
    def judge_embeddings(self, embs: Dict[str, np.ndarray], seconds: Optional[float] = None) -> Dict[str, Any]:
        """pct：像你本人（0~100，每个模型分别校准再取平均）；pct_raw：没封顶的平均值（排序用，能分出 100% 以上的高低）；
        pcts：每个模型各自的百分比；spread：几个模型之间差多少（越小越一致）；sims：原始余弦相似度。"""
        sims: Dict[str, float] = {}
        raws: Dict[str, float] = {}
        for m in self.members:
            emb = embs.get(m.name)
            if emb is None:
                continue
            sims[m.name] = round(cosine(emb, m.centroid), 4)
            raw = m.pct_raw(emb, seconds)
            if raw is not None and np.isfinite(raw):
                raws[m.name] = float(raw)
        pcts = {k: _clamp_pct(v) for k, v in raws.items()}
        pct_raw = float(np.mean(list(raws.values()))) if raws else None
        first = next(iter(sims.values()), None)
        return {"pct": _clamp_pct(pct_raw) if pct_raw is not None else None,
                "pct_raw": round(pct_raw, 2) if pct_raw is not None else None,
                "pcts": pcts, "sims": sims, "sim": first,
                "spread": round(float(np.std(list(raws.values()))), 1) if len(raws) > 1 else None,
                "seconds": round(float(seconds), 2) if seconds is not None else None,
                "short": bool(seconds is not None and seconds < SHORT_WARN_SECONDS)}

    def embed(self, wav: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """每个模型的声纹。精准声纹模型共用一次人声检测（同一段音频只去一次停顿）。"""
        return self.embed_with_seconds(wav, sr)[0]

    def embed_with_seconds(self, wav: np.ndarray, sr: int) -> Tuple[Dict[str, np.ndarray], Optional[float]]:
        """每个模型的声纹 + 人声一共几秒（没有人声检测的旧模型时为 None）。"""
        out: Dict[str, np.ndarray] = {}
        prepared: Dict[Any, np.ndarray] = {}
        for m in self.members:
            enc = m.encoder
            try:
                key = getattr(enc, "prep_key", None)
                if key is None:
                    out[m.name] = enc.embed(wav, sr)
                    continue
                if key not in prepared:
                    prepared[key] = enc.prepare(wav, sr)
                out[m.name] = enc.embed_prepared(prepared[key])
            except Exception as exc:
                log.debug(f"{m.name} 打分失败：{exc}")
        seconds = next((float(v.size) / 16000.0 for v in prepared.values()), None)
        return out, seconds

    def judge(self, wav: np.ndarray, sr: int) -> Dict[str, Any]:
        if not self.members or wav is None or len(wav) < sr * 0.3:
            return {"pct": None, "pct_raw": None, "pcts": {}, "sims": {}, "sim": None, "spread": None,
                    "seconds": None, "short": False}
        embs, seconds = self.embed_with_seconds(wav, sr)
        return self.judge_embeddings(embs, seconds)

    def judge_file(self, path: Path) -> Dict[str, Any]:
        wav, sr = load_audio(path, sr=16000)
        return self.judge(wav, sr)
