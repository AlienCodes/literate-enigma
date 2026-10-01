"""精准声纹打分用的模型：清单、下载（带校验）、加载。

所有模型都是 ONNX 格式，用 onnxruntime 在 CPU 上运行（GPT-SoVITS 整合包自带 onnxruntime-gpu；
不占显卡，生成声音时不会和 GPT-SoVITS 抢显存）。模型文件放在 similarity.model_dir（默认 ./models/sv），
用 `voicetwin download-models` 或网页「⬇️ 下载缺少的模型」下载，安装程序也会自动下载。

下载来源按顺序尝试：本项目发布页（sv-models-1）→ 模型原作者的发布页 / 国内镜像。
每个文件下载完都要核对：有 sha256 的核对 sha256；我们自己从原作者权重导出的 ONNX 文件再跑一遍
"自检"（固定的测试音频算出来的声纹必须和预先算好的一致），不一致就删掉重下，绝不会用坏文件打分。
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.utils.log import get_logger

log = get_logger("sv")

ProgressFn = Callable[[float, str], None]

RELEASE_TAG = "sv-models-1"
RELEASE_BASE = f"https://github.com/AlienCodes/literate-enigma/releases/download/{RELEASE_TAG}/"
SHERPA_BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/"
SHERPA_HF = "https://hf-mirror.com/csukuangfj/speaker-embedding-models/resolve/main/"
SILERO_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx"
#: 国内访问 GitHub 慢时的加速镜像（下载完照样核对，镜像改了文件也会被发现）
GH_MIRRORS = ("https://ghfast.top/", "https://gh-proxy.com/")
DOWNLOAD_ATTEMPTS = 3


@dataclass(frozen=True)
class SVModel:
    key: str                    # 配置里、缓存文件名里用的名字
    label: str                  # 界面上显示的名字
    file: str                   # 本地文件名
    kind: str                   # "fbank"：输入 80 维 Kaldi fbank；"wave"：输入 16 kHz 波形
    size: int                   # 字节数
    sha256: Optional[str]       # None = 我们自己导出的文件，用自检向量核对
    sources: Tuple[str, ...]    # 下载地址（按顺序试）
    origin: str = ""            # 出处（论文 / 训练数据），写在环境检查和说明里
    scale: float = 1.0          # fbank 模型输入的幅度（WeSpeaker 按 16 位整数训练 = 32768）
    dim: int = 192


def _gh(url: str) -> Tuple[str, ...]:
    """GitHub 地址 + 加速镜像。"""
    return (url,) + tuple(m + url for m in GH_MIRRORS)


VAD_MODEL = SVModel(
    key="silero-vad", label="silero-vad v4（人声检测）", file="silero_vad.onnx", kind="vad", size=643854,
    sha256="9e2449e1087496d8d4caba907f23e0bd3f78d91fa552479bb9c23ac09cbb1fd6",
    sources=_gh(RELEASE_BASE + "silero_vad.onnx") + _gh(SILERO_URL),
    origin="Silero Team（MIT 许可），k2-fsa 导出的 16 kHz 版本", dim=0)


def _sherpa(key: str, label: str, file: str, size: int, sha256: str, origin: str, dim: int = 192,
            scale: float = 1.0) -> SVModel:
    return SVModel(key=key, label=label, file=file, kind="fbank", size=size, sha256=sha256,
                   sources=_gh(RELEASE_BASE + file) + _gh(SHERPA_BASE + file) + (SHERPA_HF + file,),
                   origin=origin, scale=scale, dim=dim)


#: 候选模型（实测准确度见 docs/声纹打分准确度.md）。DEFAULT_ENSEMBLE 是默认一起打分的几个。
MODELS: Dict[str, SVModel] = {
    m.key: m for m in (
        SVModel(key="redimnet2-b6", label="ReDimNet2-B6（2026 年最新，中英文 10 万人训练）",
                file="redimnet2_b6_vb2_vox2_cnc2_lm.onnx", kind="wave", size=0, sha256=None,
                sources=_gh(RELEASE_BASE + "redimnet2_b6_vb2_vox2_cnc2_lm.onnx"),
                origin="ReDimNet2（Interspeech 2026，Palabra.ai，MIT 许可），VoxBlink2 + VoxCeleb2 + CN-Celeb2 训练"),
        SVModel(key="redimnet2-b3", label="ReDimNet2-B3（2026，中英文训练，轻量）",
                file="redimnet2_b3_vb2_vox2_cnc2_lm.onnx", kind="wave", size=0, sha256=None,
                sources=_gh(RELEASE_BASE + "redimnet2_b3_vb2_vox2_cnc2_lm.onnx"),
                origin="ReDimNet2（Interspeech 2026，Palabra.ai，MIT 许可），VoxBlink2 + VoxCeleb2 + CN-Celeb2 训练"),
        _sherpa("campplus-zh-en", "CAM++（3D-Speaker，中英文 20 万人训练）",
                "3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx", 28281164,
                "aa3cfc16963a10586a9393f5035d6d6b57e98d358b347f80c2a30bf4f00ceba2",
                "3D-Speaker（阿里通义实验室，Apache-2.0 许可）"),
        _sherpa("eres2netv2-zh", "ERes2NetV2（3D-Speaker，中文 20 万人训练）",
                "3dspeaker_speech_eres2netv2_sv_zh-cn_16k-common.onnx", 71441526,
                "bf1a75b9930474cf3389ef415e6e5d38ca96fea4a3a00f7e301d080a58ee2239",
                "3D-Speaker（阿里通义实验室，Apache-2.0 许可）"),
        _sherpa("eres2net-base-zh", "ERes2Net-base（3D-Speaker，中文 20 万人训练）",
                "3dspeaker_speech_eres2net_base_200k_sv_zh-cn_16k-common.onnx", 39593765,
                "e2d2048292e055f7b61cdec3db010503f35369b245bf0b3bbad021c9a91e4053",
                "3D-Speaker（阿里通义实验室，Apache-2.0 许可）", dim=512),
        _sherpa("campplus-zh", "CAM++（3D-Speaker，中文 20 万人训练）",
                "3dspeaker_speech_campplus_sv_zh-cn_16k-common.onnx", 28281138,
                "f682b514c05d947ee3fa91cd6ec6c5c7543479a128373fa29b1faedccd21fd11",
                "3D-Speaker（阿里通义实验室，Apache-2.0 许可）"),
        _sherpa("resnet34-cnceleb", "ResNet34-LM（WeSpeaker，CN-Celeb 训练）",
                "wespeaker_zh_cnceleb_resnet34_LM.onnx", 26530548,
                "87d1d5068397f3792c730570b53d66cd8be1da7ea22dd04f5b6706d96a3cd168",
                "WeSpeaker（Apache-2.0 许可）", dim=256, scale=32768.0),
    )
}
DEFAULT_ENSEMBLE: Tuple[str, ...] = ("redimnet2-b6", "campplus-zh-en", "eres2netv2-zh")

#: 自检用的固定测试音频（确定的伪随机"类语音"信号，不依赖任何文件）和每个模型应该得到的声纹（前 16 维 + 范数）
SELFTEST: Dict[str, Dict[str, Any]] = {}


def selftest_signal(seconds: float = 3.0) -> np.ndarray:
    """确定的测试信号：带共振峰和音高变化的合成元音串（只用来核对模型文件没坏，不是真人声音）。"""
    from scipy.signal import lfilter

    sr = 16000
    t = np.arange(int(sr * seconds)) / sr
    f0 = 140.0 + 30.0 * np.sin(2 * np.pi * 0.7 * t)
    phase = 2 * np.pi * np.cumsum(f0) / sr
    src = sum(np.sin(k * phase) / k for k in range(1, 30))
    rng = np.random.default_rng(20261001)
    out = np.zeros_like(t)
    for i, (f1, f2) in enumerate([(700, 1200), (300, 2300), (500, 900), (400, 2000)]):
        seg = slice(int(i * len(t) / 4), int((i + 1) * len(t) / 4))
        x = src[seg] + 0.05 * rng.standard_normal(seg.stop - seg.start)
        for f in (f1, f2):  # 两个共振峰（二阶谐振器）
            w = 2 * np.pi * f / sr
            x = lfilter([1.0], [1.0, -2 * 0.97 * np.cos(w), 0.97 ** 2], x)
        out[seg] = x
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.5
    return out.astype(np.float32)


# ============================================================================ 文件
def model_dir(cfg: Any) -> Path:
    from voicetwin.config import resolve_path

    raw = ((cfg.get("similarity") or {}) if hasattr(cfg, "get") else {}).get("model_dir") or "./models/sv"
    path = resolve_path(cfg, raw) if hasattr(cfg, "get") else Path(raw)
    return Path(path)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_VERIFIED: Dict[Tuple[str, int, float], bool] = {}
_VERIFY_LOCK = threading.Lock()


def file_ok(spec: SVModel, path: Path, deep: bool = False) -> bool:
    """文件在不在、大小对不对；deep=True 时再核对 sha256（或跑自检）。结果按（路径, 大小, 修改时间）缓存。"""
    try:
        st = path.stat()
    except OSError:
        return False
    if st.st_size < 1024 or (spec.size and st.st_size != spec.size):
        return False
    if not deep:
        return True
    key = (str(path), int(st.st_size), float(st.st_mtime))
    with _VERIFY_LOCK:
        if key in _VERIFIED:
            return _VERIFIED[key]
    if spec.sha256:
        ok = _sha256(path) == spec.sha256
    else:
        ok = _selftest_ok(spec, path)
    with _VERIFY_LOCK:
        _VERIFIED[key] = ok
    return ok


def _selftest_ok(spec: SVModel, path: Path) -> bool:
    ref = SELFTEST.get(spec.key)
    if not ref:
        return True  # 没有自检数据（开发中的模型）：只核对大小
    try:
        emb = OnnxEmbedder(spec, path).embed16k(selftest_signal())
    except Exception as exc:
        log.warning(f"{spec.label} 自检失败：{exc}")
        return False
    head = np.asarray(ref["head"], dtype=np.float32)
    got = emb[: head.size]
    cos = float(np.dot(got, head) / (np.linalg.norm(got) * np.linalg.norm(head) + 1e-12))
    norm_ok = abs(float(np.linalg.norm(emb)) - float(ref["norm"])) <= 0.01 * float(ref["norm"]) + 1e-3
    if cos < 0.999 or not norm_ok:
        log.warning(f"{spec.label} 自检结果不对（{cos:.4f}），文件可能下载坏了")
        return False
    return True


def required(cfg: Any, keys: Optional[Sequence[str]] = None) -> List[SVModel]:
    names = list(keys) if keys is not None else ensemble_keys(cfg)
    return [VAD_MODEL] + [MODELS[k] for k in names if k in MODELS]


def missing(cfg: Any, keys: Optional[Sequence[str]] = None) -> List[SVModel]:
    root = model_dir(cfg)
    return [m for m in required(cfg, keys) if not file_ok(m, root / m.file)]


def ensemble_keys(cfg: Any) -> List[str]:
    """配置 similarity.sv_models：auto = 默认的几个模型；也可以写成逗号分隔的名字。"""
    sim = (cfg.get("similarity") or {}) if hasattr(cfg, "get") else {}
    raw = sim.get("sv_models", "auto")
    if raw in (None, "", "auto"):
        return list(DEFAULT_ENSEMBLE)
    if isinstance(raw, str):
        raw = [x.strip() for x in raw.replace("，", ",").split(",")]
    return [str(x).strip().lower() for x in raw if str(x).strip().lower() in MODELS]


def download(cfg: Any, progress: Optional[ProgressFn] = None, keys: Optional[Sequence[str]] = None) -> List[str]:
    """下载缺少的声纹模型（带校验），返回下载了哪些文件。"""
    import requests

    from voicetwin.utils.progress import TaskCancelled, check_cancel

    root = model_dir(cfg)
    root.mkdir(parents=True, exist_ok=True)
    todo = [m for m in required(cfg, keys) if not file_ok(m, root / m.file, deep=True)]
    if not todo:
        return []
    total = sum(max(m.size, 30 << 20) for m in todo)
    done_bytes = 0
    session = requests.Session()
    got: List[str] = []
    for m in todo:
        dst = root / m.file
        if dst.exists():  # 核对不通过的旧文件（下载坏了或被改过）：先删掉，免得下载失败时还被当成好的
            dst.unlink()
        errors: List[str] = []
        for url in m.sources:
            for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
                try:
                    check_cancel()
                    _fetch(session, url, dst, m, progress, done_bytes, total)
                    if not file_ok(m, dst, deep=True):
                        dst.unlink()
                        raise IOError("下载的文件核对不通过（不完整或被改过），已删除")
                    break
                except TaskCancelled:
                    raise
                except Exception as exc:
                    errors.append(f"{url}：{exc}")
                    if attempt < DOWNLOAD_ATTEMPTS:
                        time.sleep(2.0 * attempt)
            if file_ok(m, dst, deep=True):
                break
        if not file_ok(m, dst, deep=True):
            raise RuntimeError(f"{m.label} 下载失败：" + "；".join(errors[-3:]) +
                               f"。也可以手动下载 {m.sources[0]} 放到 {root}")
        done_bytes += max(m.size, 30 << 20)
        got.append(m.file)
        log.info(f"✅ 已下载 {m.label}")
    return got


def _fetch(session: Any, url: str, dst: Path, m: SVModel, progress: Optional[ProgressFn], base: int,
           total: int) -> None:
    from voicetwin.utils.progress import check_cancel

    tmp = dst.with_suffix(dst.suffix + ".part")
    log.info(f"下载 {m.file}（{url.split('/')[2]}）……")
    with session.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        size = int(r.headers.get("Content-Length", 0) or 0)
        n = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                check_cancel()
                f.write(chunk)
                n += len(chunk)
                if progress is not None and total:
                    try:
                        progress(min(0.999, (base + n) / float(total)),
                                 f"下载声纹模型 {m.file}：{n >> 20}/{(size or m.size) >> 20} MB")
                    except Exception:
                        pass
        if size and n < size:
            raise IOError(f"只下载了 {n >> 20}/{size >> 20} MB，连接断了")
    os.replace(tmp, dst)


# ============================================================================ 推理
class OnnxEmbedder:
    """一个 ONNX 声纹模型：输入 16 kHz 人声，输出 L2 归一化的声纹向量。"""

    #: 一次最多送这么长（更长的切段分别算再按长度加权平均，内存不随音频长度无限涨）
    WINDOW_SECONDS = 20.0

    def __init__(self, spec: SVModel, path: Path, threads: int = 0, device: str = "cpu"):
        from voicetwin.eval.sv_frontend import ort_session

        self.spec = spec
        self.sess = ort_session(Path(path), threads=threads, device=device)
        self.input = self.sess.get_inputs()[0].name
        self._lock = threading.Lock()

    def _run(self, chunk: np.ndarray) -> np.ndarray:
        from voicetwin.eval.sv_frontend import kaldi_fbank

        if self.spec.kind == "wave":
            x = np.ascontiguousarray(chunk, dtype=np.float32)[None, :]
        else:
            feat = kaldi_fbank(chunk, scale=self.spec.scale)
            feat = feat - feat.mean(axis=0, keepdims=True)
            x = feat[None, :, :]
        with self._lock:
            out = self.sess.run(None, {self.input: x})[0]
        v = np.asarray(out, dtype=np.float32).reshape(-1)
        return v

    def embed16k(self, speech: np.ndarray) -> np.ndarray:
        """speech：已经只剩人声的 16 kHz 音频。返回没有归一化的声纹（自检用）；打分用 embed()。"""
        speech = np.asarray(speech, dtype=np.float32).reshape(-1)
        if speech.size < 8000:  # 不到半秒：重复一下，fbank 至少要几十帧
            reps = int(np.ceil(8000 / max(speech.size, 1)))
            speech = np.tile(speech, reps) if speech.size else np.zeros(8000, dtype=np.float32)
        win = int(16000 * self.WINDOW_SECONDS)
        if speech.size <= win * 1.25:
            return self._run(speech)
        n = int(np.ceil(speech.size / win))
        parts = np.array_split(speech, n)
        embs = [self._run(p) for p in parts]
        unit = [e / (np.linalg.norm(e) + 1e-12) for e in embs]
        return np.average(np.stack(unit), axis=0, weights=[len(p) for p in parts]).astype(np.float32)
