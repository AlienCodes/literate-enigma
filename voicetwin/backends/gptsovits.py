"""GPT-SoVITS 引擎（推荐）：用你的素材微调，复刻程度最高。

训练流程与官方 WebUI 完全一致（1A 文本 → 1B 特征/声纹 → 1C 语义 → SoVITS 训练 → GPT 训练），
只是全部自动完成；推理通过官方 api_v2.py 服务进行。
训练出来的模型和官方 WebUI 通用，也可以在 GPT-SoVITS 的界面里直接选择使用。

自动训练设置（plan_training）只采用有根据的做法（GPT-SoVITS 官方代码里的默认值和公式、官方说明，
以及多个来源一致的经验；没有测量依据的猜测一律不用）：
- 每批数量（batch）= 官方公式 floor((显存 + 0.4) / 2)，最多 12；小显存（< 8 GB 档）最多 2；
  不超过素材条数 / 4；不用半精度时减半；显卡正被别的程序占用时按空闲显存算。
- 轮数看素材多少和干不干净，不看显存：SoVITS 素材 < 30 分钟 8 轮、≥ 30 分钟 12 轮（有底噪/背景音时最多 8 轮），
  GPT 15 轮（官方默认；轮数太多反而容易漏字、复读）。
- 多存几个模型（每 2~3 轮存一次，最后一轮一定会存下来），训练完自动挑最像你的那个（不是越多轮越好）。
- DPO 是官方的实验功能：自动时一律不开（没有可靠的测量说明它能让声音更像，而且显存翻倍、语气训练慢 2~4 倍），
  只在高级设置 / config.yaml / 命令行里手动打开时才用。
- 训练时显存不够（CUDA out of memory）：自动把每批数量减半，再试一次。
高级设置 / config.yaml / 命令行里明确填写的数值优先。
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

from voicetwin.backends.base import (
    Backend,
    ProgressFn,
    Stage,
    SynthRequest,
    TaskCancelled,
    TrainStepError,
    cancel_requested,
    check_cancel,
    gpu_memory_gb,
    kill_process_tree,
    resolve_python,
)
from voicetwin.backends.worker import subprocess_env
from voicetwin.utils.winsys import kill_with_parent
from voicetwin.utils.log import get_logger
from voicetwin.utils.logtail import RUN_MARKER, condense, diagnose_gsv_api, last_run, read_text
from voicetwin.utils.textutil import short_hash

log = get_logger("gptsovits")

PRETRAINED_SOVITS = {
    "v2": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth",
    "v2Pro": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth",
    "v2ProPlus": "GPT_SoVITS/pretrained_models/v2Pro/s2Gv2ProPlus.pth",
}
PRETRAINED_GPT = {
    "v2": "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
    "v2Pro": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
    "v2ProPlus": "GPT_SoVITS/pretrained_models/s1v3.ckpt",
}
BERT_DIR = "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"
HUBERT_DIR = "GPT_SoVITS/pretrained_models/chinese-hubert-base"
SV_PATH = "GPT_SoVITS/pretrained_models/sv/pretrained_eres2netv2w24s4ep4.ckpt"
SUPPORTED_VERSIONS = tuple(PRETRAINED_SOVITS)
#: 目前公开的最新、最强版本。官方 wiki《GPT‐SoVITS‐features(Latest‐Including‐v5)》：
#: 时间顺序 V1<V2<V3<V4<V2Pro(Plus)<V5；v2ProPlus "超 v4 的性能"，Zero Shot 相似度比 v2Pro 略高；
#: V5 截至 2026-10-01 还没有公开的代码和模型（GitHub 最新发布 20250606v2pro）。V5 公开后再实测比较。
LATEST_VERSION = "v2ProPlus"


def version_status(version: str) -> Tuple[bool, str]:
    """GPT-SoVITS 模型版本是不是目前公开的最新版本：(是否最新, 说明)。"""
    if version == LATEST_VERSION:
        return True, (f"{version}：目前公开的最新、最强版本（官方版本顺序 V1<V2<V3<V4<V2Pro(Plus)<V5，"
                      "V5 还没有公开；v2ProPlus 比 v2Pro 更像）")
    return False, (f"设置里用的是 {version}，不是最新的 {LATEST_VERSION}。怎么办：用记事本打开 config.yaml，把 "
                   f"backends → gptsovits 下面的 version 改成 {LATEST_VERSION}，保存后在 ② 训练模型 重新训练一次")

# ---------------------------------------------------------------- 从模型文件本身读出版本
# 和 GPT-SoVITS 自己判断的方法完全一样（GPT_SoVITS/process_ckpt.py 的 get_sovits_version_from_path_fast）：
#   1. 官方底模：文件开头 8192 字节的 MD5 对照表；
#   2. 训练出来的新格式模型：文件开头 2 个字节是版本标记（00=v1 01=v2 02=v3 03=v3 LoRA 04=v4 LoRA 05=v2Pro 06=v2ProPlus）；
#   3. 旧格式（开头是 PK 的 zip）：按文件大小分 v1 / v2 / v3。
# 对照表会再从整合包里的 process_ckpt.py 读一遍（以后官方出了新版本，例如 v5，标记会自动认出来）；
# 两边都不认识的标记就如实显示"未知版本"，不猜。
SOVITS_HEAD_VERSION: Dict[bytes, Tuple[str, bool]] = {
    b"00": ("v1", False), b"01": ("v2", False), b"02": ("v3", False), b"03": ("v3", True),
    b"04": ("v4", True), b"05": ("v2Pro", False), b"06": ("v2ProPlus", False),
}
SOVITS_HASH_VERSION: Dict[str, str] = {
    "dc3c97e17592963677a4a1681f30c653": "v2",         # s2G488k.pth（v1 底模，官方按 v2 处理）
    "43797be674a37c1c83ee81081941ed0f": "v3",         # s2Gv3.pth
    "6642b37f3dbb1f76882b69937c95a5f3": "v2",         # s2G2333k.pth
    "4f26b9476d0c5033e04162c486074374": "v4",         # s2Gv4.pth
    "c7e9fce2223f3db685cdfa1e6368728a": "v2Pro",      # s2Gv2Pro.pth
    "66b313e39455b57ab1b0bc0b239c9d0a": "v2ProPlus",  # s2Gv2ProPlus.pth
}
_GSV_MAPS_CACHE: Dict[str, Tuple[float, Dict[bytes, Tuple[str, bool]], Dict[str, str]]] = {}


def gsv_version_maps(root: Optional[Path]) -> Tuple[Dict[bytes, Tuple[str, bool]], Dict[str, str]]:
    """版本对照表：内置的 + 整合包 process_ckpt.py 里的（整合包的优先，新版本的标记也能认出来）。"""
    heads, hashes = dict(SOVITS_HEAD_VERSION), dict(SOVITS_HASH_VERSION)
    src = Path(root) / "GPT_SoVITS" / "process_ckpt.py" if root else None
    try:
        if src is None or not src.exists():
            return heads, hashes
        key, mtime = str(src), src.stat().st_mtime
        cached = _GSV_MAPS_CACHE.get(key)
        if cached is None or cached[0] != mtime:
            import ast

            text = src.read_text(encoding="utf-8", errors="replace")
            h2v: Dict[bytes, Tuple[str, bool]] = {}
            hsh: Dict[str, str] = {}
            m = re.search(r"^head2version\s*=\s*(\{.*?\n\})", text, re.S | re.M)
            if m:
                for k, v in ast.literal_eval(m.group(1)).items():
                    if isinstance(k, bytes) and isinstance(v, (list, tuple)) and len(v) >= 2:
                        h2v[k] = (str(v[1]), bool(v[2]) if len(v) > 2 else False)
            m = re.search(r"^hash_pretrained_dict\s*=\s*(\{.*?\n\})", text, re.S | re.M)
            if m:
                for k, v in ast.literal_eval(m.group(1)).items():
                    if isinstance(v, (list, tuple)) and len(v) >= 2:
                        hsh[str(k)] = str(v[1])
            cached = (mtime, h2v, hsh)
            _GSV_MAPS_CACHE[key] = cached
        heads.update(cached[1])
        hashes.update(cached[2])
    except Exception as exc:  # 读不懂整合包的文件：用内置的对照表
        log.debug(f"读取 process_ckpt.py 的版本对照表失败：{exc}")
    return heads, hashes


def detect_sovits_version(path: Any, root: Optional[Path] = None) -> Dict[str, Any]:
    """读 SoVITS 模型文件，判断它是哪个 GPT-SoVITS 版本。只读文件开头几 KB，很快。

    返回 {"version": "v2ProPlus" / None, "lora": bool, "how": 判断依据（中文）, "file": 路径}。"""
    p = Path(str(path or ""))
    out: Dict[str, Any] = {"version": None, "lora": False, "how": "", "file": str(p)}
    if not str(path or "") or not p.is_file():
        out["how"] = "找不到模型文件"
        return out
    heads, hashes = gsv_version_maps(root)
    with open(p, "rb") as f:
        head = f.read(8192)
    digest = hashlib.md5(head).hexdigest()
    if digest in hashes:
        out.update(version=hashes[digest], how="官方底模（按文件内容核对）")
    elif head[:2] in heads:
        ver, lora = heads[head[:2]]
        out.update(version=ver, lora=lora, how="模型文件里的版本标记")
    elif head[:2] == b"PK":
        size = p.stat().st_size
        out.update(version="v1" if size < 82978 * 1024 else ("v2" if size < 700 * 1024 * 1024 else "v3"),
                   how="旧格式模型（按文件大小判断）")
    else:
        out["how"] = f"不认识的版本标记 {head[:2]!r}（可能是更新的 GPT-SoVITS 版本）"
    return out


#: 模型文件夹里必须有的文件：每一组里至少要有一个（下载到一半的 *.part 不算）
DIR_REQUIREMENTS: Dict[str, Tuple[Tuple[str, ...], ...]] = {
    BERT_DIR: (("config.json",), ("pytorch_model.bin", "model.safetensors"), ("tokenizer.json", "vocab.txt")),
    HUBERT_DIR: (("config.json",), ("preprocessor_config.json",), ("pytorch_model.bin", "model.safetensors")),
}
WEIGHT_SUFFIXES = (".bin", ".safetensors", ".pth", ".ckpt", ".pt")
MIN_WEIGHT_BYTES = 1024           # 模型权重小于 1 KB 肯定是坏的 / 没下载完
DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_BACKOFF = (2.0, 5.0)

# ---------------------------------------------------------------- 自动训练设置（research_quality.md §3、§4）
REPORTED_FUDGE_GB = 0.4           # 官方 config.py：显存读数 + 0.4 再用（H）
TIER_MID_GB = 7.5                 # 加 0.4 之后：< 7.5 算 6 GB 以下的小显存（low）
TIER_HIGH_GB = 15.5               # ≥ 15.5 算 16 GB 以上（high）
FREE_SLACK_GB = 1.5               # 按空闲显存算时加的余量：桌面、浏览器平时占的 1 GB 左右不影响每批数量
BATCH_CAP = 12                    # 再大只是更快，不会更好（每轮更新次数反而变少）
LOW_TIER_BATCH = 2
TINY_GPU_GB = 5.0                 # 4 GB 级别的卡：每批 1 条
CPU_BATCH = 2
DPO_RISKY_GB = 12.0               # 低于它手动开 DPO 基本会显存不够
SOVITS_EPOCHS_SMALL = 8           # 官方默认（素材 < 30 分钟）
SOVITS_EPOCHS_LARGE = 12          # 素材 ≥ 30 分钟
SOVITS_LARGE_MINUTES = 30.0
GPT_EPOCHS_AUTO = 15              # 官方默认；更多轮容易漏字、复读（#2508）
SOVITS_MAX_EPOCHS = 25            # 官方界面上限
GPT_MAX_EPOCHS = 50               # 官方界面上限
SAVE_TARGET_COUNT = 5             # 自动保存间隔：每个模型尽量存 5 个左右
SAVE_MAX_COUNT = 8
#: 旧版 config.yaml 里抄来的默认保存间隔（不是用户自己填的）：当作「自动」
LEGACY_SAVE_EVERY = {"sovits_save_every": 4, "gpt_save_every": 5}
NOISY_FRACTION = 0.5              # 一半以上的素材有底噪 / 去过背景音乐：算「有底噪」
SUSPECT_MAX_RATIO = 0.05          # 超过 5% 的文字可能有错：不自动开 DPO
#: 训练完自动挑选时，SoVITS / GPT 各试几个（从早到晚均匀挑，最后一个一定在内）
SELECT_SOVITS = 4
SELECT_GPT = 3
RUN_STAMP = "voicetwin_run_started"
KEEP_OLD_RUNS = 2
USER_KEYS = ("batch_size", "sovits_epochs", "gpt_epochs", "sovits_save_every", "gpt_save_every", "if_dpo")


def _api_reason(r: Any) -> str:
    """api_v2 出错时回答里的真正原因（JSON 的 Exception / message），不是 JSON 就用原文。"""
    try:
        j = r.json()
        if isinstance(j, dict):
            return str(j.get("Exception") or j.get("message") or r.text)
    except Exception:
        pass
    return str(r.text or f"HTTP {getattr(r, 'status_code', '?')}")


def _silent_answer(data: bytes) -> str:
    """引擎回的 WAV 是不是一点声音都没有；是的话返回一句描述（例如「1.0 秒的静音」），否则返回空字符串。"""
    try:
        import io

        import soundfile as sf

        wav, sr = sf.read(io.BytesIO(data), dtype="int16", always_2d=False)
    except Exception:
        return ""
    if getattr(wav, "size", 0) and not wav.any():
        return f"{len(wav) / sr:.1f} 秒的静音"
    return ""


def _last_exception(text: str) -> str:
    """一段记录里最后一个 Traceback 的报错那一行（例如 torch.OutOfMemoryError: CUDA out of memory. …）。"""
    from voicetwin.utils.logtail import exception_counts

    found = exception_counts(text)
    return found[-1][0] if found else ""


def _json_has(r: Any, key: str) -> bool:
    """HTTP 回答是不是 JSON、里面有没有 key。"""
    try:
        j = r.json()
    except Exception:
        return False
    return isinstance(j, dict) and key in j


def _free_port(preferred: int) -> int:
    for port in [preferred] + list(range(preferred + 1, preferred + 50)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def _exp_name(voice: str) -> str:
    ascii_part = re.sub(r"[^A-Za-z0-9_-]+", "", voice)[:20]
    return f"vt_{ascii_part + '_' if ascii_part else ''}{short_hash(voice, n=6)}"


# ================================================================ 自动训练设置
def _is_auto(value: Any) -> bool:
    """None / '' / 'auto' / '自动' / 0 都表示「自动」。"""
    if value is None or isinstance(value, bool):
        return value is None
    if isinstance(value, str):
        return value.strip().lower() in ("", "auto", "自动", "0", "none")
    try:
        return float(value) == 0
    except (TypeError, ValueError):
        return True


def _to_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _pos_float(value: Any) -> Optional[float]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def _dpo_choice(value: Any) -> Optional[bool]:
    """DPO 开关：None 表示自动。"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in ("true", "on", "yes", "y", "1", "开", "开启", "打开", "是"):
        return True
    if s in ("false", "off", "no", "n", "0", "关", "关闭", "不开", "否"):
        return False
    return None


def _auto_save_every(epochs: int, max_epochs: Optional[int] = None) -> Tuple[int, int]:
    """自动的保存间隔：返回 (轮数, 每几轮存一次)。

    GPT-SoVITS 只在「轮数是保存间隔的整数倍」时导出模型，所以最后一轮必须是倍数，否则最后一轮的模型存不下来。
    尽量让每个模型存 5 个左右（3~8 个，同样接近时多存）。按原来的轮数只能存 2 个时（例如 22 轮只能每 11 轮存一次），
    多练 1~2 轮（不超过上限 max_epochs）凑一个能多存几个的轮数：22 → 24 轮每 4 轮存一次，存 6 个。"""
    epochs = max(1, int(epochs))
    if epochs <= 2:
        return epochs, 1

    def best_for(e: int) -> Optional[Tuple[Tuple[int, int], int]]:
        best: Optional[Tuple[Tuple[int, int], int]] = None
        for d in range(1, e + 1):
            if e % d:
                continue
            count = e // d
            if count < 2 or count > SAVE_MAX_COUNT:
                continue
            score = (abs(count - SAVE_TARGET_COUNT), -count)
            if best is None or score < best[0]:
                best = (score, d)
        return best

    options = []
    for e in (epochs, epochs + 1, epochs + 2):  # 尽量少改轮数：第一个能存 ≥ 3 个的就用它
        if e != epochs and max_epochs is not None and e > max_epochs:
            continue
        b = best_for(e)
        if b is None:
            continue
        if e // b[1] >= 3:
            return e, b[1]
        options.append((b[0], e - epochs, e, b[1]))
    if options:  # 到了上限也凑不出 3 个：至少存 2 个（最后一轮一定存）
        _, _, e, d = min(options)
        return e, d
    return epochs, 1  # 走不到这里（epochs+1、epochs+2 里总有偶数）


def _fit_explicit_save(epochs: int, save: int, max_epochs: int) -> Tuple[int, int]:
    """用户自己填了保存间隔：轮数凑成它的整数倍（先往上凑，超过上限就往下凑）。"""
    epochs, save = max(1, int(epochs)), max(1, int(save))
    if save > max_epochs:
        return epochs, epochs
    if epochs % save == 0:
        return epochs, save
    up = int(math.ceil(epochs / float(save))) * save
    if up <= max_epochs:
        return up, save
    return max(save, (epochs // save) * save), save


def _dpo_gpt_batch(g: float) -> int:
    """开 DPO 时 GPT 每批数量（官方代码内部还会再减半）。"""
    if g >= 32:
        return 8
    if g >= 24:
        return 6
    if g >= 22:
        return 4
    if g >= 16:
        return 2
    return 1


def _tier(g: float) -> str:
    if g <= 0:
        return "none"
    if g < TIER_MID_GB:
        return "low"
    if g < TIER_HIGH_GB:
        return "mid"
    return "high"


def _nominal_gb(total_gb: float) -> str:
    """显存按包装盒上的大小显示：11.76 → 12，7.6 → 8。"""
    try:
        from voicetwin.utils.gpu import nominal_gb

        v = nominal_gb(total_gb)
        if v:
            return f"{v:g}" if float(v).is_integer() else f"{v:.1f}"
    except Exception:
        pass
    return f"{int(round(total_gb + 0.2))}"


def plan_training(n_clips: int, minutes: float, total_gb: Optional[float] = None, free_gb: Optional[float] = None,
                  *, is_half: bool = True, noisy: bool = False, suspects: int = 0,
                  user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """根据显存和素材，算出这次的训练设置，并写一行中文说明（summary）。纯计算，不碰显卡和文件。

    user 里不是「自动」的值优先（来自高级设置 / config.yaml / 命令行）。"""
    user = dict(user or {})
    n_clips = max(0, int(n_clips or 0))
    minutes = float(minutes or 0.0)
    notes: List[str] = []
    total = _pos_float(total_gb)
    free = _pos_float(free_gb)
    g_total = total + REPORTED_FUDGE_GB if total else 0.0

    def vram_batch(gb: float) -> int:
        if gb <= 0:
            return CPU_BATCH
        b = int(gb // 2)
        if gb < TIER_MID_GB:
            b = min(b, LOW_TIER_BATCH)
        if gb < TINY_GPU_GB:
            b = 1
        return max(1, min(b, BATCH_CAP))

    # 显卡正被别的程序占着、按空闲显存算会更小时，才按空闲的算（Windows 显存满了不报错，而是慢好几倍）
    g = g_total
    by_free = False
    if g_total and free is not None and vram_batch(free + FREE_SLACK_GB) < vram_batch(g_total):
        g = free + FREE_SLACK_GB
        by_free = True

    def mine(key: str) -> str:
        return "" if auto[key] else "（你指定的）"

    auto = {k: _is_auto(user.get(k)) for k in USER_KEYS if k != "if_dpo"}
    dpo_user = _dpo_choice(user.get("if_dpo"))
    auto["if_dpo"] = dpo_user is None

    # ---- 每批数量
    clip_cap = max(1, n_clips // 4)
    if auto["batch_size"]:
        bs = vram_batch(g)
        if by_free:
            notes.append(f"显卡现在有 {max(0.0, total - free):.1f} GB 被别的程序占着（只空闲 {free:.1f} GB），"
                         "每批数量按空闲的显存算；想练得快一点，可以先关掉游戏、剪映、在线视频等占用显卡的程序")
    else:
        bs = max(1, _to_int(user.get("batch_size"), CPU_BATCH))
    if n_clips and bs > clip_cap:  # 和官方 GPT 数据加载一样：每批不超过素材条数的 1/4
        notes.append(f"素材只有 {n_clips} 条，每批最多 {clip_cap} 条")
        bs = clip_cap
    if not is_half:
        bs = max(1, bs // 2)
        notes.append("显卡用全精度训练（is_half: false），每批数量减半")

    # ---- 轮数（看素材，不看显存）
    if auto["sovits_epochs"]:
        s_ep = SOVITS_EPOCHS_LARGE if minutes >= SOVITS_LARGE_MINUTES else SOVITS_EPOCHS_SMALL
        if noisy and s_ep > SOVITS_EPOCHS_SMALL:
            s_ep = SOVITS_EPOCHS_SMALL
            notes.append(f"素材里一大半有底噪或背景音乐，音色训练最多 {SOVITS_EPOCHS_SMALL} 轮（练太多会把杂音也学进去）")
    else:
        s_ep = max(1, min(_to_int(user.get("sovits_epochs"), SOVITS_EPOCHS_SMALL), SOVITS_MAX_EPOCHS))
    if auto["gpt_epochs"]:
        g_ep = GPT_EPOCHS_AUTO
    else:
        g_ep = max(1, min(_to_int(user.get("gpt_epochs"), GPT_EPOCHS_AUTO), GPT_MAX_EPOCHS))

    # ---- 多久存一次（最后一轮一定要存下来）
    def fit_save(key: str, epochs: int, max_epochs: int, name: str) -> Tuple[int, int]:
        if auto[key]:
            new_ep, save = _auto_save_every(epochs, max_epochs)
        else:
            new_ep, save = _fit_explicit_save(epochs, _to_int(user.get(key), 1), max_epochs)
        if new_ep != epochs:
            notes.append(f"为了让最后一轮的模型能保存下来，{name}轮数从 {epochs} 调整为 {new_ep}")
        return new_ep, save

    s_ep, s_save = fit_save("sovits_save_every", s_ep, SOVITS_MAX_EPOCHS, "音色（SoVITS）")
    g_ep, g_save = fit_save("gpt_save_every", g_ep, GPT_MAX_EPOCHS, "语气（GPT）")

    # ---- DPO（官方实验功能）
    why_not = ""
    if dpo_user is None:
        # 自动时一律不开（research_quality.md §1.4、§8.5：没有可靠的测量说明它能提升效果；它是实验功能，
        # 显存翻倍、语气训练慢 2~4 倍，整合包里的版本还有已知问题）。想试的话在高级设置里手动打开。
        dpo = False
        if g < DPO_RISKY_GB:
            why_not = "官方实验功能，显存也不够；需要的话可以在高级设置里手动打开"
        elif noisy:
            why_not = "官方实验功能；素材有底噪或背景音乐，开了反而可能变差"
        elif n_clips and suspects / float(n_clips) > SUSPECT_MAX_RATIO:
            why_not = f"官方实验功能；还有 {suspects} 条文字可能有错，先校对好"
        else:
            why_not = "官方实验功能，没有可靠的证据说明能让声音更像，开了语气训练会慢 2～4 倍；想试可以在高级设置里手动打开"
    else:
        dpo = dpo_user
        if not dpo:
            why_not = "你在高级设置里关掉了"
    gpt_bs = bs
    if dpo:
        if auto["batch_size"]:
            gpt_bs = min(_dpo_gpt_batch(g), clip_cap) if n_clips else _dpo_gpt_batch(g)
            if not is_half:
                gpt_bs = max(1, gpt_bs // 2)
        if g < DPO_RISKY_GB:
            notes.append("显存不到 12 GB 还开 DPO，很可能显存不够（会自动把每批数量减半再试一次）")

    # ---- 一行中文说明
    parts: List[str] = []
    if g_total > 0:
        gpu = f"显存 {_nominal_gb(total)} GB" + (f"（现在空闲 {free:.1f} GB）" if by_free else "")
        parts.append(f"{gpu} → 每批 {bs} 条{mine('batch_size')}")
    else:
        parts.append(f"没有检测到能用的 N 卡 → 每批 {bs} 条{mine('batch_size')}（用 CPU 训练会非常慢）")
    mat = f"素材 {minutes:g} 分钟（{n_clips} 条{'，有底噪或背景音乐' if noisy else ''}）"
    parts.append(f"{mat} → 音色 SoVITS {s_ep} 轮{mine('sovits_epochs')}、语气 GPT {g_ep} 轮{mine('gpt_epochs')}")
    def every(n: int) -> str:
        return "每轮" if n == 1 else f"每 {n} 轮"

    if s_save == g_save:
        parts.append(f"{every(s_save)}存一次模型，训练完自动挑最像你的那个")
    else:
        parts.append(f"音色{every(s_save)}、语气{every(g_save)}存一次模型，训练完自动挑最像你的那个")
    if dpo:
        who = "" if auto["if_dpo"] else "你指定的；"
        parts.append(f"开启 DPO（{who}官方实验功能，用来减少重复、漏字；语气训练每批 {gpt_bs} 条，会慢 2～4 倍）")
    else:
        parts.append(f"不开 DPO（{why_not}）")
    summary = "训练计划：" + "；".join(parts) + "。"

    return {
        "batch_size": bs, "gpt_batch_size": gpt_bs,
        "sovits_epochs": s_ep, "gpt_epochs": g_ep,
        "sovits_save_every": s_save, "gpt_save_every": g_save,
        "if_dpo": bool(dpo),
        "gpu_mem_gb": round(total, 1) if total else 0.0,
        "gpu_free_gb": round(free, 1) if free is not None else None,
        "vram_gb": round(g, 1), "tier": _tier(g_total),
        "minutes": minutes, "n_clips": n_clips, "noisy": bool(noisy), "suspects": int(suspects),
        "auto": auto, "notes": notes, "summary": summary,
    }


# ================================================================ 训练日志 → 进度
def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


_SOVITS_STEP = re.compile(r"Train Epoch:\s*(\d+)\s*\[(\d+(?:\.\d+)?)%\]")
_SOVITS_DONE = re.compile(r"====> Epoch:\s*(\d+)")
_GPT_STEP = re.compile(r"Epoch\s+(\d+):\s*(\d+)%")
# 只认「接着上次练」那一行里的 checkpoint 文件名（v2 底模的文件名里也有 epoch=12，不能当成进度）
_GPT_CKPT = re.compile(r"(?:ckpt_path:|checkpoint path at).*?epoch=(\d+)-step=")


def _sovits_parser(total: int) -> Callable[[str], Optional[Tuple[float, str]]]:
    """s2_train.py：「Train Epoch: 3 [45%]」（第 3 轮进行中，从 1 开始数）和「====> Epoch: 3」（第 3 轮完成）。

    开头的「start training from epoch 1」不算进度（否则一开始就跳到 1/8）。"""
    total = max(1, int(total))

    def parse(line: str) -> Optional[Tuple[float, str]]:
        m = _SOVITS_STEP.search(line)
        if m:
            e, p = int(m.group(1)), float(m.group(2))
            return _clamp01(((e - 1) + p / 100.0) / total), f"训练音色：第 {min(e, total)}/{total} 轮（{int(p)}%）"
        m = _SOVITS_DONE.search(line)
        if m:
            e = int(m.group(1))
            return _clamp01(e / float(total)), f"训练音色：第 {min(e, total)}/{total} 轮完成"
        return None

    return parse


def _gpt_parser(total: int) -> Callable[[str], Optional[Tuple[float, str]]]:
    """s1_train.py（Lightning 进度条）：「Epoch 0:  45%|…」（从 0 开始数）；
    接着上次训练时打印「ckpt_path: …/ckpt/epoch=9-step=…」（第 10 轮已经练完）。"""
    total = max(1, int(total))

    def parse(line: str) -> Optional[Tuple[float, str]]:
        m = _GPT_STEP.search(line)
        if m:
            e, p = int(m.group(1)), int(m.group(2))
            return _clamp01((e + p / 100.0) / total), f"训练语气和节奏：第 {min(e + 1, total)}/{total} 轮（{p}%）"
        m = _GPT_CKPT.search(line)
        if m:
            e = int(m.group(1)) + 1  # Lightning 的 checkpoint 文件名里 epoch 从 0 开始
            return _clamp01(e / float(total)), f"训练语气和节奏：第 {min(e, total)}/{total} 轮完成"
        return None

    return parse


def _line_counter(n: int, label: str) -> Callable[[str], Optional[Tuple[float, str]]]:
    """1-get-text.py 每处理一条素材打印一行文件名（xxx.wav）。"""
    n = max(1, int(n))
    count = [0]

    def parse(line: str) -> Optional[Tuple[float, str]]:
        if line.strip().lower().endswith(".wav"):
            count[0] += 1
            c = count[0]
            return min(1.0, c / float(n)), f"{label} {min(c, n)}/{n}"
        return None

    return parse


def _count_files(folder: Path, pattern: str, total: int) -> Callable[[], Optional[Tuple[int, int]]]:
    """1B / 声纹这两步每处理一条素材写一个 .pt 文件：数文件就知道做到哪了。"""
    total = max(1, int(total))

    def poll() -> Optional[Tuple[int, int]]:
        try:
            if not folder.is_dir():
                return (0, total)
            return (sum(1 for _ in folder.glob(pattern)), total)
        except OSError:
            return None

    return poll


def _spread(items: List[Path], k: int) -> List[Path]:
    """从早到晚均匀挑 k 个（最早的一个通常还没练好，多的时候先去掉；最后一个一定在内）。"""
    items = list(items)
    k = max(1, int(k))
    if len(items) <= k:
        return items
    pool = items[1:]
    if len(pool) <= k:
        return pool
    if k == 1:
        return [pool[-1]]
    idx = sorted({int(math.floor(i * (len(pool) - 1) / float(k - 1) + 0.5)) for i in range(k)})
    return [pool[i] for i in idx]


def _pick_run(files: List[Path], since: float) -> List[Path]:
    """只要这一轮训练（since 之后）存下的模型；同一轮数有好几个文件时用最新的。按轮数排序。"""
    stats: List[Tuple[Path, float]] = []
    for f in files:
        try:
            stats.append((f, f.stat().st_mtime))
        except OSError:
            continue
    if since > 0:
        recent = [(f, m) for f, m in stats if m >= since - 2.0]  # FAT32 / 网络盘的时间只精确到 2 秒
        if recent:
            stats = recent
    best: Dict[int, Tuple[Path, float]] = {}
    for f, m in stats:
        e = _epoch(f)
        if e not in best or m > best[e][1]:
            best[e] = (f, m)
    return [best[e][0] for e in sorted(best)]


def _file_ok(path: Path) -> bool:
    try:
        if not path.is_file():
            return False
        size = path.stat().st_size
    except OSError:
        return False
    if path.suffix.lower() in WEIGHT_SUFFIXES:
        return size >= MIN_WEIGHT_BYTES
    return size > 0


class GPTSoVITSBackend(Backend):
    name = "gptsovits"
    display_name = "GPT-SoVITS"
    supports_training = True
    supports_speed = True
    supports_aux_refs = True
    train_stages: List[Stage] = [
        (0.00, "检查显卡、整理训练素材"),
        (0.05, "处理文字"),
        (0.12, "提取声音特征"),
        (0.20, "提取语义"),
        (0.25, "训练音色（SoVITS）"),
        (0.60, "训练语气和节奏（GPT）"),
        (0.95, "保存模型"),
    ]
    #: 1B / 声纹这两步多久数一次文件（秒）
    POLL_SECONDS = 2.0
    #: 推理服务启动时多久报一次「还在启动」（秒）
    STARTUP_NOTE_SECONDS = 15.0
    #: 端口已经打开、但回答和 api_v2 对不上时，最多再等多久就报错（秒）。
    #: api_v2 是加载完全部模型之后才打开端口的（api_v2.py 先 TTS(tts_config) 再 uvicorn.run），
    #: 端口一开就应该马上能用；这么久还对不上，说明是别的程序或者版本对不上，不用白等到超时。
    MISMATCH_GRACE_SECONDS = 60.0
    #: gptsovits_api.log 超过这么大（字节）时，启动前先改名成 gptsovits_api.old.log，重新记
    API_LOG_MAX_BYTES = 5_000_000

    def __init__(self, cfg, project):
        super().__init__(cfg, project)
        self.root = self.resolve("root", "./third_party/GPT-SoVITS")
        self.version = str(self.bcfg.get("version", "v2ProPlus"))
        if self.version not in SUPPORTED_VERSIONS:
            log.warning(f"暂只自动化支持 {SUPPORTED_VERSIONS}，当前配置 {self.version}，改用 v2ProPlus")
            self.version = "v2ProPlus"
        self.python = resolve_python(self.bcfg.get("python", "auto"), self.root, cfg)
        self.exp_name = _exp_name(project.voice)
        self.external_url = (self.bcfg.get("api_url") or "").rstrip("/")
        self.port = int(self.bcfg.get("port", 9880))
        self.api_url = self.external_url or f"http://127.0.0.1:{self.port}"
        self.proc: Optional[subprocess.Popen] = None
        self._loaded: Dict[str, str] = {}
        self._http = None
        self._log_fh = None
        self._warned_pretrained = False

    # ================================================================ 路径与检查
    def p(self, rel: str) -> Path:
        assert self.root is not None
        return (self.root / rel).resolve()

    @property
    def is_half(self) -> bool:
        v = self.bcfg.get("is_half", True)
        if isinstance(v, str):  # config.yaml 里写成字符串 "false" 时 bool("false") 是 True
            return v.strip().lower() not in ("false", "0", "no", "off", "")
        return bool(v)

    def check(self) -> List[str]:
        problems = []
        if self.external_url:
            return problems
        if not self.root or not self.root.exists():
            return [f"找不到 GPT-SoVITS 目录：{self.root}（请运行安装脚本，或在 config.yaml 里设置 backends.gptsovits.root）"]
        if not (self.root / "api_v2.py").exists():
            problems.append(f"{self.root} 不是完整的 GPT-SoVITS 目录（缺少 api_v2.py）")
        missing = self.missing_pretrained()
        for rel in missing:
            problems.append(f"缺少预训练模型：{rel}")
        if missing:
            problems.append("可运行 voicetwin download-models 自动下载（国内加 --source hf-mirror）")
        return problems

    def _required_pretrained(self) -> List[str]:
        needed = [BERT_DIR, HUBERT_DIR, PRETRAINED_SOVITS[self.version], PRETRAINED_SOVITS[self.version].replace("s2G", "s2D"),
                  PRETRAINED_GPT[self.version]]
        if "Pro" in self.version:
            needed.append(SV_PATH)
        return needed

    def _pretrained_ok(self, rel: str) -> bool:
        path = self.p(rel)
        groups = DIR_REQUIREMENTS.get(rel)
        if groups is None:
            return _file_ok(path)
        if not path.is_dir():
            return False
        return all(any(_file_ok(path / name) for name in group) for group in groups)

    def missing_pretrained(self) -> List[str]:
        """缺少（或没下载完整）的预训练模型。文件夹里少了必需的文件、模型文件小于 1 KB，都算缺少。"""
        return [rel for rel in self._required_pretrained() if not self._pretrained_ok(rel)]

    def download_pretrained(self, source: str = "auto", progress: Optional[ProgressFn] = None) -> List[str]:
        """从 Hugging Face（lj1995/GPT-SoVITS）下载缺失的预训练模型；国内可用 source="hf-mirror"。

        每个文件最多试 3 次；先下载到 *.part，下载完整才改成正式文件名。"""
        import requests

        if not self.root or not self.root.exists():
            raise RuntimeError(f"找不到 GPT-SoVITS 目录：{self.root}")
        endpoints = {"hf": ["https://huggingface.co"], "hf-mirror": ["https://hf-mirror.com"]}.get(
            source, [os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/"), "https://hf-mirror.com"])
        repo = "lj1995/GPT-SoVITS"
        prefix = "GPT_SoVITS/pretrained_models/"
        missing = self.missing_pretrained()
        if not missing:
            log.info("GPT-SoVITS 预训练模型齐全，无需下载")
            return []
        session = requests.Session()
        last_error: Optional[Exception] = None
        for ep in endpoints:
            try:
                files: List[Tuple[str, Optional[int]]] = []
                for rel in missing:
                    remote = rel[len(prefix):]
                    if rel in DIR_REQUIREMENTS:
                        r = session.get(f"{ep}/api/models/{repo}/tree/main/{remote}", timeout=30)
                        r.raise_for_status()
                        for item in r.json():
                            if item.get("type") == "file":
                                size = (item.get("lfs") or {}).get("size") or item.get("size")
                                files.append((item["path"], int(size) if size else None))
                    else:
                        files.append((remote, None))
                for i, (remote, expected) in enumerate(files):
                    dst = self.p(prefix + remote)
                    if _file_ok(dst) and (expected is None or dst.stat().st_size == expected):
                        continue
                    self._download_file(session, f"{ep}/{repo}/resolve/main/{remote}", dst, remote, ep,
                                        progress, i, len(files))
                return [remote for remote, _ in files]
            except TaskCancelled:
                raise
            except Exception as exc:
                last_error = exc
                log.warning(f"从 {ep} 下载失败：{exc}")
        raise RuntimeError(f"预训练模型下载失败：{last_error}。也可以手动从 https://huggingface.co/{repo} 下载后放入 "
                           f"{self.p(prefix)}")

    @staticmethod
    def _download_file(session: Any, url: str, dst: Path, remote: str, ep: str, progress: Optional[ProgressFn],
                       index: int, count: int) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_suffix(dst.suffix + ".part")
        name = remote.rsplit("/", 1)[-1]
        for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
            try:
                log.info(f"下载 {remote}（{ep}）……" + (f"（第 {attempt} 次尝试）" if attempt > 1 else ""))
                with session.get(url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    total = int(r.headers.get("Content-Length", 0) or 0)
                    done = 0
                    last_decile = -1
                    with open(tmp, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 20):
                            check_cancel()
                            f.write(chunk)
                            done += len(chunk)
                            if total:
                                decile = int(done * 10 / total)
                                msg = f"下载 {name}：{done >> 20}/{total >> 20} MB"
                                if decile != last_decile:
                                    last_decile = decile
                                    log.info(f"  {msg}")
                                if progress:
                                    try:
                                        progress((index + done / float(total)) / max(count, 1), msg)
                                    except Exception:
                                        pass
                    if total and done < total:
                        raise IOError(f"{name} 只下载了 {done >> 20}/{total >> 20} MB，连接断了")
                tmp.replace(dst)
                return
            except TaskCancelled:
                raise
            except Exception as exc:
                if attempt >= DOWNLOAD_ATTEMPTS:
                    raise
                wait = DOWNLOAD_BACKOFF[min(attempt - 1, len(DOWNLOAD_BACKOFF) - 1)]
                log.warning(f"下载 {name} 出错（{exc}），{wait:g} 秒后重试……")
                time.sleep(wait)

    def env(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        assert self.root is not None
        root = str(self.root)
        paths = [root, os.path.join(root, "GPT_SoVITS"), os.path.join(root, "GPT_SoVITS", "BigVGAN"),
                 os.path.join(root, "tools"), os.path.join(root, "tools", "asr"), os.path.join(root, "tools", "uvr5")]
        existing = os.environ.get("PYTHONPATH", "")
        # 整合包的 ffmpeg.exe 在根目录，Python 在 runtime/，与官方 go-webui.bat 一样加入 PATH
        bin_paths = [root, os.path.join(root, "runtime")]
        env = subprocess_env({
            "PATH": os.pathsep.join(bin_paths + [os.environ.get("PATH", "")]),
            "PYTHONPATH": os.pathsep.join(paths + ([existing] if existing else [])),
            "version": self.version,
            "is_half": str(self.is_half),
            "no_proxy": "localhost, 127.0.0.1, ::1",
            "KMP_DUPLICATE_LIB_OK": "TRUE",
        })
        env.pop("all_proxy", None)
        env.pop("ALL_PROXY", None)
        if extra:
            env.update({k: str(v) for k, v in extra.items()})
        return env

    def ensure_users_pth(self) -> None:
        """和官方 webui.py 启动时一样，在 GPT-SoVITS 的 site-packages 写入 users.pth（整合包的训练脚本依赖它）。"""
        assert self.root is not None
        root = str(self.root).replace("\\", "/")
        code = (
            "import site, os\n"
            f"root = {root!r}\n"
            "content = '\\n'.join([root, root + '/GPT_SoVITS/BigVGAN', root + '/tools', root + '/tools/asr', "
            "root + '/GPT_SoVITS', root + '/tools/uvr5'])\n"
            "cands = [p for p in site.getsitepackages() if 'packages' in p] or [root + '/runtime/Lib/site-packages']\n"
            "for sp in cands:\n"
            "    if os.path.isdir(sp):\n"
            "        f = os.path.join(sp, 'users.pth')\n"
            "        try:\n"
            "            if not os.path.exists(f) or open(f, encoding='utf-8', errors='ignore').read() != content:\n"
            "                open(f, 'w', encoding='utf-8').write(content)\n"
            "            break\n"
            "        except OSError:\n"
            "            pass\n"
        )
        try:
            subprocess.run([self.python, "-c", code], env=self.env(), cwd=str(self.root), timeout=120,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception as exc:  # pragma: no cover
            log.warning(f"写入 users.pth 失败（通常不影响）：{exc}")

    # ================================================================ 自动训练设置
    def _gpu(self) -> str:
        return str((self.bcfg.get("train", {}) or {}).get("gpu", "0"))

    def _gpu_memory(self, quick: bool = False) -> Tuple[float, Optional[float], str]:
        """（显存 GiB 原始读数, 空闲 GiB 或 None, 来源）。先用网页顶部那个显卡检查（快，还知道空闲多少），
        读不到时再用 GPT-SoVITS 自己的 PyTorch 读（慢一点，可能要十几秒）。quick=True（网页上的预览）时不用慢的办法。"""
        try:
            from voicetwin.utils.gpu import gpu_status

            st = gpu_status(refresh=not quick)
            total = _pos_float(st.get("total_gb"))
            if st.get("level") != "error" and total:
                free = st.get("free_gb")
                return total, (_pos_float(free) if free is not None else None), str(st.get("source") or "gpu")
        except Exception:
            pass
        if quick:
            return 0.0, None, "none"
        return gpu_memory_gb(self.python, self.env()) if self.root else 0.0, None, "torch"

    def _material_quality(self) -> Tuple[bool, float, int]:
        """（有没有底噪, 有底噪的素材占比, 可能有错字的条数）。看准备素材时记下的信噪比、是否去过背景音乐。"""
        try:
            from voicetwin.data.exporters import train_records

            recs = train_records(self.project)
            sources = self.project.read_json(self.project.sources_path, {}) or {}
            thr = float(((self.cfg.get("prepare") or {}).get("snr_threshold_db")) or 25)
            total = noisy_s = 0.0
            for r in recs:
                d = float(r.get("duration") or 0.0)
                total += d
                src = sources.get(str(r.get("source", ""))) or {}
                snr = src.get("snr_before")
                if src.get("separated") or (isinstance(snr, (int, float)) and snr < thr):
                    noisy_s += d
            share = noisy_s / total if total > 0 else 0.0
            suspects = sum(1 for r in recs if r.get("suspect"))
            return share >= NOISY_FRACTION, share, suspects
        except Exception:
            return False, 0.0, 0

    def _user_settings(self, opts: Dict[str, Any]) -> Dict[str, Any]:
        """config.yaml 的 train 段 + 本次的选项（高级设置 / 命令行）。旧版 config.yaml 抄来的保存间隔当作自动。"""
        tcfg = dict(self.bcfg.get("train", {}) or {})
        for key, legacy in LEGACY_SAVE_EVERY.items():
            if not _is_auto(tcfg.get(key)) and _to_int(tcfg.get(key), -1) == legacy:
                tcfg[key] = "auto"
        user = {k: tcfg.get(k) for k in USER_KEYS}
        for k, v in (opts or {}).items():
            if k in user and v is not None and not (isinstance(v, str) and v.strip().lower() in ("", "auto")):
                user[k] = v
        return user

    def _make_plan(self, n_clips: int, minutes: float, opts: Dict[str, Any], quick: bool = False) -> Dict[str, Any]:
        total, free, source = self._gpu_memory(quick)
        if total <= 0 and not quick:
            log.warning("没有检测到可用的 NVIDIA 显卡，训练会非常慢（CPU 训练可能需要数天）")
        noisy, share, suspects = self._material_quality()
        plan = plan_training(n_clips, minutes, total, free, is_half=self.is_half, noisy=noisy, suspects=suspects,
                             user=self._user_settings(opts))
        plan["gpu_source"] = source
        plan["noisy_share"] = round(share, 2)
        return plan

    def training_plan(self, quick: bool = False, **opts: Any) -> Dict[str, Any]:
        """训练前预览这次的自动训练设置（不训练、不导出文件）。

        quick=True：只用 nvidia-smi 读显卡（网页上每次换声音都会预览，不能等十几秒）。"""
        from voicetwin.data.exporters import train_records

        recs = train_records(self.project)
        minutes = round(sum(float(r.get("duration") or 0.0) for r in recs) / 60.0, 1)
        return self._make_plan(len(recs), minutes, opts, quick=quick)

    # ================================================================ 训练
    def _opt_dir(self) -> Path:
        return self.p(f"logs/{self.exp_name}")

    def _run_started(self) -> float:
        """这一轮训练（素材第一次训练或素材有变化后）从什么时候开始；不知道时返回 0。"""
        if self.root is None:
            return 0.0
        try:
            return float((self._opt_dir() / RUN_STAMP).read_text(encoding="utf-8").strip() or 0)
        except (OSError, ValueError):
            return 0.0

    def _weight_files(self) -> List[Tuple[str, Path]]:
        """这个声音导出过的模型文件：[(所在的文件夹名, 文件)]。"""
        out: List[Tuple[str, Path]] = []
        for sub, pattern in ((f"SoVITS_weights_{self.version}", f"{self.exp_name}_e*_s*.pth"),
                             (f"GPT_weights_{self.version}", f"{self.exp_name}-e*.ckpt")):
            d = self.p(sub)
            if d.is_dir():
                out += [(sub, f) for f in sorted(d.glob(pattern)) if f.is_file()]
        return out

    def _repoint_models(self, moved: Dict[str, str]) -> None:
        """旧模型文件挪进 old_runs 以后，models.json 里记的路径跟着改：重新训练中途停下时，原来选中的模型照样能用。"""
        if not moved:
            return
        models = self.project.load_models()
        entry = models.get(self.name)
        if not entry:
            return

        def fix(path: Any) -> Any:
            name = str(path or "").replace("\\", "/").rsplit("/", 1)[-1]
            return moved.get(name, path)

        for key in ("sovits", "gpt"):
            if isinstance(entry.get(key), list):
                entry[key] = [fix(x) for x in entry[key]]
        sel = entry.get("selected")
        if isinstance(sel, dict):
            for key in ("sovits", "gpt"):
                if sel.get(key):
                    sel[key] = fix(sel[key])
        self.project.write_json(self.project.models_path, models)

    def _archive_old_run(self, opt_dir: Path) -> Optional[Path]:
        """素材变了：把旧的训练进度（GPT-SoVITS 会从这里接着练）和旧的模型文件移到 old_runs/<时间>/，这次从头训练。

        模型文件也要挪走：素材条数不变时（例如只改了错字），新模型的文件名和旧的一模一样，不挪的话会直接覆盖掉
        原来选中的模型，而且新旧模型分不出来（生成时会一直用到旧模型的缓存）。models.json 里的路径跟着改到新位置。"""
        names = [f"logs_s2_{self.version}", f"logs_s1_{self.version}", "logs_s1"]
        existing = []
        for n in names:
            d = opt_dir / n
            try:
                if d.is_dir() and any(d.iterdir()):
                    existing.append(d)
            except OSError:
                continue
        weights = self._weight_files() if self.root is not None else []
        if not existing and not weights:
            return None
        base = opt_dir / "old_runs" / time.strftime("%Y%m%d_%H%M%S")
        dest, i = base, 1
        while dest.exists():
            dest, i = base.with_name(f"{base.name}_{i}"), i + 1
        moved = False
        for src in existing:
            try:
                dest.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest / src.name))  # 跨盘时 shutil.move 自己会复制再删除
                moved = True
            except Exception as exc:
                log.warning(f"备份旧的训练进度 {src.name} 没成功（{exc}），直接删掉它，免得接着旧模型练")
                shutil.rmtree(src, ignore_errors=True)
                if src.exists():
                    log.warning(f"{src} 删不掉（可能被别的程序占用），这次训练可能会接着旧的进度")
        moved_weights: Dict[str, str] = {}
        for sub, f in weights:
            target = dest / sub / f.name
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(f), str(target))
                moved_weights[f.name] = str(target)
                moved = True
            except Exception as exc:
                log.warning(f"备份旧的模型文件 {f.name} 没成功（{exc}），这次训练可能会覆盖它")
        try:
            self._repoint_models(moved_weights)
        except Exception as exc:
            log.warning(f"更新 models.json 里的模型位置没成功：{exc}")
        if not moved:
            try:
                dest.rmdir()
            except OSError:
                pass
        old_root = opt_dir / "old_runs"
        try:  # 只留最近几次备份（每次大约 1 GB），免得占满硬盘；正在用的模型所在的那次不删
            sel = (self.project.load_models().get(self.name) or {}).get("selected") or {}
            in_use = [str(sel.get(k) or "") for k in ("sovits", "gpt") if sel.get(k)]
            runs = sorted((p for p in old_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)
            for p in runs[:-KEEP_OLD_RUNS]:
                if any(u.startswith(str(p)) for u in in_use):
                    continue
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass
        return dest if moved else None

    def _prepare_features(self, list_path: Path, wav_dir: Path, progress: Optional[ProgressFn],
                          n_clips: int = 0) -> Path:
        opt_dir = self._opt_dir()
        opt_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha1(list_path.read_bytes() + self.version.encode()).hexdigest()
        stamp = opt_dir / "voicetwin_list.sha1"
        old = stamp.read_text().strip() if stamp.exists() else None
        fresh = old is None
        if old is not None and old != digest:
            log.info("训练素材有变化，清理旧的特征文件后重新提取")
            for name in ("2-name2text.txt", "6-name2semantic.tsv", "3-bert", "4-cnhubert", "5-wav32k", "7-sv_cn"):
                target = opt_dir / name
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
            archived = self._archive_old_run(opt_dir)
            if archived is not None:
                log.info(f"检测到素材有变化：这次会从头训练新模型（旧的训练进度已备份到 {archived}）")
            else:
                log.info("检测到素材有变化：这次会从头训练新模型")
            fresh = True
        if fresh:
            (opt_dir / RUN_STAMP).write_text(f"{time.time():.3f}", encoding="utf-8")
        stamp.write_text(digest)
        n = max(1, int(n_clips or 0) or len(list_path.read_text(encoding="utf-8").strip().splitlines()))
        base = {"inp_text": str(list_path), "inp_wav_dir": str(wav_dir), "exp_name": self.exp_name,
                "opt_dir": str(opt_dir), "i_part": "0", "all_parts": "1", "_CUDA_VISIBLE_DEVICES": self._gpu(),
                "is_half": str(self.is_half), "version": self.version}

        # 1A：文本 → 音素 + BERT 特征
        path_text = opt_dir / "2-name2text.txt"
        if not path_text.exists() or len(path_text.read_text(encoding="utf-8").strip().splitlines()) < 2:
            self.step(progress, 0.05, "处理文字（把讲稿转成拼音和特征）")
            self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/1-get-text.py"], self.root,
                            self.env({**base, "bert_pretrained_dir": str(self.p(BERT_DIR))}), "gsv_1a_text",
                            progress, (0.05, 0.12), _line_counter(n, "处理文字"), label="处理文字")
            part = opt_dir / "2-name2text-0.txt"
            lines = part.read_text(encoding="utf-8").strip("\n").split("\n") if part.exists() else []
            if not "".join(lines).strip():
                raise RuntimeError("1A 文本处理没有产出，请查看日志 logs/gsv_1a_text.log")
            path_text.write_text("\n".join(lines) + "\n", encoding="utf-8")
            part.unlink(missing_ok=True)

        # 1B：HuBERT 特征 + 32k 音频（+ v2Pro 声纹）。脚本不打印进度，数它写出的文件。
        self.step(progress, 0.12, "提取声音特征（比较慢，素材多时要十几分钟）")
        env_1b = {**base, "cnhubert_base_dir": str(self.p(HUBERT_DIR)), "sv_path": str(self.p(SV_PATH))}
        self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"], self.root,
                        self.env(env_1b), "gsv_1b_hubert", progress, (0.12, 0.18), label="提取声音特征",
                        poll_progress=_count_files(opt_dir / "4-cnhubert", "*.pt", n), poll_interval=self.POLL_SECONDS)
        if "Pro" in self.version:
            self.step(progress, 0.18, "提取声纹")
            self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/2-get-sv.py"], self.root,
                            self.env(env_1b), "gsv_1b_sv", progress, (0.18, 0.20), label="提取声纹",
                            poll_progress=_count_files(opt_dir / "7-sv_cn", "*.pt", n), poll_interval=self.POLL_SECONDS)

        # 1C：语义 token
        path_sem = opt_dir / "6-name2semantic.tsv"
        if not path_sem.exists() or path_sem.stat().st_size < 31:
            self.step(progress, 0.20, "提取语义（大约 1~3 分钟）")
            env_1c = {**base, "pretrained_s2G": str(self.p(PRETRAINED_SOVITS[self.version])),
                      "s2config_path": self._s2_config_template()}
            self.run_logged([self.python, "-s", "GPT_SoVITS/prepare_datasets/3-get-semantic.py"], self.root,
                            self.env(env_1c), "gsv_1c_semantic", progress, (0.20, 0.25), label="提取语义")
            part = opt_dir / "6-name2semantic-0.tsv"
            lines = ["item_name\tsemantic_audio"]
            if part.exists():
                lines += part.read_text(encoding="utf-8").strip("\n").split("\n")
                part.unlink()
            path_sem.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return opt_dir

    def _s2_config_template(self) -> str:
        return "GPT_SoVITS/configs/s2.json" if "Pro" not in self.version else f"GPT_SoVITS/configs/s2{self.version}.json"

    def _with_oom_retry(self, what: str, bs: int, run: Callable[[int], None], progress: Optional[ProgressFn],
                        frac: float) -> int:
        """跑一步训练；显存不够（CUDA out of memory）时把每批数量减半，自动再试一次。返回实际用的每批数量。"""
        try:
            run(bs)
            return bs
        except TrainStepError as exc:
            if not exc.oom or bs <= 1:
                raise
            new_bs = max(1, bs // 2)
            msg = (f"{what}时显存不够：自动把每批数量从 {bs} 减到 {new_bs}，再试一次"
                   "（只自动重试一次；已经练好的部分会接着用）……")
            log.warning(msg)
            if progress:
                try:
                    progress(frac, msg)
                except Exception:
                    pass
            run(new_bs)
            return new_bs

    def _train_sovits(self, opt_dir: Path, params: Dict[str, Any], progress: Optional[ProgressFn]) -> int:
        tcfg = self.bcfg.get("train", {}) or {}
        total = int(params["sovits_epochs"])
        pre_g = str(self.p(PRETRAINED_SOVITS[self.version]))
        s2_path = self.work_dir / "tmp_s2.json"

        def run(bs: int) -> None:
            with open(self.p(self._s2_config_template()), "r", encoding="utf-8") as f:
                s2 = json.load(f)
            if not self.is_half:
                s2["train"]["fp16_run"] = False
            s2["train"].update({
                "batch_size": int(bs), "epochs": total,
                "text_low_lr_rate": float(tcfg.get("text_low_lr_rate", 0.4)),
                "pretrained_s2G": pre_g, "pretrained_s2D": pre_g.replace("s2G", "s2D"),
                "if_save_latest": True, "if_save_every_weights": True,
                "save_every_epoch": int(params["sovits_save_every"]), "gpu_numbers": self._gpu(),
                "grad_ckpt": False, "lora_rank": 32,
            })
            s2["model"]["version"] = self.version
            s2["data"]["exp_dir"] = s2["s2_ckpt_dir"] = str(opt_dir)
            s2["save_weight_dir"] = f"SoVITS_weights_{self.version}"
            s2["name"] = self.exp_name
            s2["version"] = self.version
            (opt_dir / f"logs_s2_{self.version}").mkdir(parents=True, exist_ok=True)
            # 真实的 s2_train.py 不会自己建这个文件夹（只有官方 webui.py 启动时会建），没有的话练完也存不下模型
            self.p(f"SoVITS_weights_{self.version}").mkdir(parents=True, exist_ok=True)
            s2_path.write_text(json.dumps(s2, ensure_ascii=False), encoding="utf-8")
            self.run_logged([self.python, "-s", "GPT_SoVITS/s2_train.py", "--config", str(s2_path)], self.root,
                            self.env(), "gsv_s2_train", progress, (0.25, 0.60), _sovits_parser(total), label="训练音色")

        self.step(progress, 0.25, f"训练音色（SoVITS），共 {total} 轮……")
        return self._with_oom_retry("训练音色（SoVITS）", int(params["batch_size"]), run, progress, 0.25)

    def _train_gpt(self, opt_dir: Path, params: Dict[str, Any], progress: Optional[ProgressFn]) -> int:
        total = int(params["gpt_epochs"])
        dpo = bool(params.get("if_dpo"))
        s1_path = self.work_dir / "tmp_s1.yaml"

        def run(bs: int) -> None:
            with open(self.p("GPT_SoVITS/configs/s1longer-v2.yaml"), "r", encoding="utf-8") as f:
                s1 = yaml.safe_load(f)
            if not self.is_half:
                s1["train"]["precision"] = "32"
            s1["train"].update({
                "batch_size": int(bs), "epochs": total,
                "save_every_n_epoch": int(params["gpt_save_every"]), "if_save_every_weights": True,
                "if_save_latest": True, "if_dpo": dpo, "half_weights_save_dir": f"GPT_weights_{self.version}",
                "exp_name": self.exp_name,
            })
            s1["pretrained_s1"] = str(self.p(PRETRAINED_GPT[self.version]))
            s1["train_semantic_path"] = str(opt_dir / "6-name2semantic.tsv")
            s1["train_phoneme_path"] = str(opt_dir / "2-name2text.txt")
            s1["output_dir"] = str(opt_dir / f"logs_s1_{self.version}")
            (opt_dir / "logs_s1").mkdir(parents=True, exist_ok=True)
            self.p(f"GPT_weights_{self.version}").mkdir(parents=True, exist_ok=True)  # 同上，s1_train.py 也不建
            s1_path.write_text(yaml.dump(s1, default_flow_style=False, allow_unicode=True), encoding="utf-8")
            self.run_logged([self.python, "-s", "GPT_SoVITS/s1_train.py", "--config_file", str(s1_path)], self.root,
                            self.env({"_CUDA_VISIBLE_DEVICES": self._gpu(), "hz": "25hz"}), "gsv_s1_train",
                            progress, (0.60, 0.95), _gpt_parser(total), label="训练语气和节奏")

        self.step(progress, 0.60, f"训练语气和节奏（GPT），共 {total} 轮" + ("，已开启 DPO（会比较慢）" if dpo else "") + "……")
        return self._with_oom_retry("训练语气和节奏（GPT）", int(params["gpt_batch_size"]), run, progress, 0.60)

    def train(self, progress: Optional[ProgressFn] = None, **opts: Any) -> Dict[str, Any]:
        """训练。opts（高级设置 / 命令行，None 或 "auto" 表示自动）：batch_size、sovits_epochs、gpt_epochs、
        sovits_save_every、gpt_save_every、if_dpo（True / False / None）。

        返回值（也写进 models.json）的 params 里有这次实际用的设置，params["summary"] 是一行中文说明。"""
        from voicetwin.data.exporters import export_gptsovits

        self.step(progress, 0.0, "检查显卡、整理训练素材（大约半分钟）……")
        problems = self.check()
        if self.external_url:
            problems.append("配置了外部 api_url 时无法自动训练，请清空 backends.gptsovits.api_url 并设置 root")
        if problems:
            raise RuntimeError("GPT-SoVITS 环境有问题：\n- " + "\n- ".join(problems))
        if self.proc is not None:  # 推理服务占着显存，先关掉
            self.stop()
        exp = export_gptsovits(self.project, speaker=self.exp_name)
        latest, note = version_status(self.version)
        log.info(f"实验名 {self.exp_name}；GPT-SoVITS 版本 {self.version}"
                 + ("（目前公开的最新、最强版本）" if latest else f"（⚠️ {note}）"))
        self.step(progress, 0.02, f"训练素材 {exp['count']} 条，共 {exp['minutes']} 分钟")
        params = self._make_plan(int(exp["count"]), float(exp["minutes"]), opts)
        self.step(progress, 0.03, params["summary"])
        for note in params["notes"]:
            log.info(f"  · {note}")
        self.ensure_users_pth()
        opt_dir = self._prepare_features(Path(exp["list"]), Path(exp["wav_dir"]), progress, n_clips=int(exp["count"]))

        used_s = self._train_sovits(opt_dir, params, progress)
        used_g = self._train_gpt(opt_dir, params, progress)
        if used_s != params["batch_size"] or used_g != params["gpt_batch_size"]:
            params["oom_retry"] = True
            params["batch_size_used"] = used_s
            params["gpt_batch_size_used"] = used_g

        self.step(progress, 0.95, "保存模型……")
        sovits, gpt = self._list_weights()
        if not sovits or not gpt:
            raise RuntimeError("训练结束但没有找到权重文件，请查看 logs/gsv_s2_train.log 与 logs/gsv_s1_train.log")
        info = {
            "version": self.version, "exp_name": self.exp_name, "trained_at": time.strftime("%Y-%m-%d %H:%M"),
            "params": params, "sovits": [str(p) for p in sovits], "gpt": [str(p) for p in gpt],
            "selected": {"id": f"s{_epoch(sovits[-1])}-g{_epoch(gpt[-1])}", "sovits": str(sovits[-1]), "gpt": str(gpt[-1])},
        }
        # 旧模型的挑选结果和语速校准不能留给新模型用（自动挑选没做成功、或者不挑选时，会一直用着旧的数字）
        self.project.update_models(self.name, info, drop=("selection", "speed", "selection_error"))
        self.step(progress, 1.0, "GPT-SoVITS 训练完成")
        return info

    def _list_weights(self) -> Tuple[List[Path], List[Path]]:
        """这一轮训练存下的模型（素材变过以后，旧素材练出来的不算），按轮数排序。"""
        sov_dir = self.p(f"SoVITS_weights_{self.version}")
        gpt_dir = self.p(f"GPT_weights_{self.version}")
        sovits = list(sov_dir.glob(f"{self.exp_name}_e*_s*.pth")) if sov_dir.exists() else []
        gpt = list(gpt_dir.glob(f"{self.exp_name}-e*.ckpt")) if gpt_dir.exists() else []
        since = self._run_started()
        return _pick_run(sovits, since), _pick_run(gpt, since)

    def _locate_weight(self, path: str) -> Optional[Path]:
        """models.json 里记的是绝对路径；整合包被移动 / 换了电脑后，按文件名到当前 root 里重新找。"""
        if not path:
            return None
        p = Path(path)
        if p.exists():
            return p
        if self.root is None:
            return None
        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        for d in (f"SoVITS_weights_{self.version}", f"GPT_weights_{self.version}"):
            cand = self.p(d) / name
            if cand.exists():
                return cand
        return None

    def model_version_info(self) -> Dict[str, Any]:
        """生成时实际会用的 SoVITS 模型是哪个版本：从模型文件本身读出来（不是照抄设置）。

        返回 detect_sovits_version 的结果，再加 source（"trained" 训练好的 / "pretrained" 还没训练、用底模 /
        "external" 用的是别处的 GPT-SoVITS 服务，读不到文件）和 configured（设置里的版本）。"""
        info: Dict[str, Any] = {"version": None, "lora": False, "how": "", "file": "", "configured": self.version}
        sel = self.selected_checkpoint()
        path = self._locate_weight(str(sel.get("sovits") or "")) if sel else None
        if path is not None:
            info.update(detect_sovits_version(path, self.root), source="trained")
        elif self.external_url or self.root is None:
            info.update(source="external", how="用的是别处的 GPT-SoVITS 服务，读不到模型文件")
        else:
            info.update(detect_sovits_version(self.p(PRETRAINED_SOVITS[self.version]), self.root), source="pretrained")
            info["trained_missing"] = bool(sel)  # 训练过，但模型文件找不到了（生成时也会退回底模）
        info["configured"] = self.version
        return info

    def checkpoints(self, max_sovits: Optional[int] = None, max_gpt: Optional[int] = None) -> List[Dict[str, Any]]:
        """自动挑选要试的模型组合：SoVITS 默认 4 个 × GPT 3 个，从早到晚均匀挑（最后一轮一定在内）。

        config.yaml 的 backends.gptsovits.train.select_sovits / select_gpt 可以改这两个数。"""
        info = self.project.load_models().get(self.name) or {}
        sovits = [w for w in (self._locate_weight(p) for p in info.get("sovits", [])) if w]
        gpt = [w for w in (self._locate_weight(p) for p in info.get("gpt", [])) if w]
        if not sovits or not gpt:
            sovits, gpt = self._list_weights()
        sovits = sorted(dict.fromkeys(sovits), key=_epoch)
        gpt = sorted(dict.fromkeys(gpt), key=_epoch)
        tcfg = self.bcfg.get("train", {}) or {}
        ks = max_sovits or max(1, _to_int(tcfg.get("select_sovits"), SELECT_SOVITS))
        kg = max_gpt or max(1, _to_int(tcfg.get("select_gpt"), SELECT_GPT))
        out = []
        for s in _spread(sovits, ks):
            for g in _spread(gpt, kg):
                out.append({"id": f"s{_epoch(s)}-g{_epoch(g)}", "sovits": str(s), "gpt": str(g),
                            "sovits_epoch": _epoch(s), "gpt_epoch": _epoch(g)})
        return out

    # ================================================================ 推理服务
    def _current_weights(self) -> Dict[str, str]:
        sel = self.selected_checkpoint()
        if sel:
            sovits, gpt = self._locate_weight(sel.get("sovits", "")), self._locate_weight(sel.get("gpt", ""))
            if sovits and gpt:
                return {"sovits": str(sovits), "gpt": str(gpt), "id": sel.get("id", "custom")}
        if self.root is None:
            return {"sovits": "", "gpt": "", "id": "external"}
        if not self._warned_pretrained:  # 每句话都会问一次模型，警告只说一次
            self._warned_pretrained = True
            log.warning("还没有训练好的 GPT-SoVITS 模型，暂时使用官方底模做零样本克隆（像度会明显低于训练后）")
        return {"sovits": str(self.p(PRETRAINED_SOVITS[self.version])), "gpt": str(self.p(PRETRAINED_GPT[self.version])),
                "id": "pretrained"}

    def model_id(self) -> str:
        """当前用的模型的标识（生成的缓存按它区分）。除了路径，还算上文件的大小和修改时间：
        重新训练后文件名可能一模一样，内容却换了，不能还用旧模型生成的缓存。"""
        w = self._current_weights()

        def sig(path: str) -> str:
            try:
                st = Path(path).stat()
                return f"{st.st_size}-{st.st_mtime_ns}"
            except (OSError, ValueError):
                return ""

        return f"gsv-{self.version}-{w['id']}-{short_hash(w['sovits'], w['gpt'], sig(w['sovits']), sig(w['gpt']), n=6)}"

    def _session(self):
        if self._http is None:
            import requests

            self._http = requests.Session()
            self._http.trust_env = False  # 访问本机服务不走代理
        return self._http

    def _probe(self) -> Tuple[bool, str]:
        """推理服务现在能不能用。返回 (能不能用, 不能用的原因)；原因是空字符串表示端口还没打开（还在加载模型）。

        问法：GET /control，不带 command。官方 api_v2.py 从 2024-08 的第一版（52c50c6）到现在（abe9843）
        都回答 400 + {"message": "command is required"}，而且什么也不做。
        千万不能用不带参数的 GET /tts：所有官方版本都在检查参数之前先执行 text_lang.lower()，报错回 500。
        v18.2 及以前就是用它判断的，结果引擎明明一分钟内就开好了，程序却一直等到 10 分钟超时
        （老师的 gptsovits_api.log 里同一个报错重复了 867 次，见 research/合成引擎启动/）。"""
        import requests

        port_open = False
        try:
            # 先很快地看端口有没有打开：Windows 上连一个还没打开的端口要等 2 秒左右才失败，
            # 直接发请求的话每次检查都要卡这么久（启动时的「已等待 N 秒」提示也会出不来）
            from urllib.parse import urlsplit

            u = urlsplit(str(self.api_url))
            host, port = u.hostname or "127.0.0.1", u.port or (443 if u.scheme == "https" else 80)
            if host in ("127.0.0.1", "localhost", "::1"):  # 只查本机的服务（别的电脑上的服务网络可能比较慢）
                with socket.create_connection((host, port), timeout=0.5):
                    port_open = True
        except OSError:
            return False, ""
        except Exception:  # 网址解析不了等意外情况：直接发请求试
            pass
        # Connection: close —— 每次检查用一个新连接，不受上一次请求的影响
        headers = {"Connection": "close"}
        try:
            r = self._session().get(f"{self.api_url}/control", timeout=5, headers=headers)
        except requests.exceptions.ConnectionError as exc:
            if port_open:  # 端口明明连得上，请求却被断开：不是「还没打开」（比如被安全软件拦了）
                return False, f"端口已经打开，但请求被断开了（{type(exc).__name__}）"
            return False, ""
        except Exception as exc:
            return False, f"端口已经打开，但是 5 秒内没有回答（{type(exc).__name__}）"
        if r.status_code == 400 and _json_has(r, "message"):
            return True, ""
        # 兜底：FastAPI 自带的接口清单里有 /tts 和 /set_gpt_weights，也认作 api_v2（以后的版本万一改了 /control 的回答）
        try:
            r2 = self._session().get(f"{self.api_url}/openapi.json", timeout=5, headers=headers)
            paths = r2.json().get("paths", {}) if r2.status_code == 200 else {}
            if isinstance(paths, dict) and "/tts" in paths and "/set_gpt_weights" in paths:
                return True, ""
        except Exception:
            pass
        body = re.sub(r"\s+", " ", r.text or "").strip()[:150]
        return False, f"端口已经打开，但回答和 GPT-SoVITS 的 api_v2 对不上（HTTP {r.status_code}：{body or '没有内容'}）"

    def start_hint(self) -> str:
        """上次启动推理服务实际用了多久（start() 就绪时记下的）；没有记录时只说要先加载模型。"""
        try:
            sec = float((self.work_dir / "api_start_seconds.txt").read_text(encoding="utf-8").strip())
            return f"上次用了 {int(round(sec))} 秒"
        except (OSError, ValueError):
            return "要先加载模型"

    def _alive(self) -> bool:
        if self._probe()[0]:
            return True
        # 自己开的服务进程还活着：多试两次（偶尔一次没回答就重启引擎，要重新加载模型，白白多等）
        if self.proc is not None and self.proc.poll() is None and self._loaded:
            for _ in range(2):
                time.sleep(1.0)
                if self._probe()[0]:
                    return True
        return False

    def _api_log_path(self) -> Path:
        return self.project.logs_dir / "gptsovits_api.log"

    def _api_tail(self, n: int) -> str:
        """引擎记录最后一次启动之后的部分，整理过（重复的报错只留一份），最多 n 行。"""
        try:
            if self._log_fh is not None:
                self._log_fh.flush()
        except Exception:
            pass
        return condense(last_run(read_text(self._api_log_path())), max_lines=max(10, n))

    def _api_report(self, n: int = 40) -> str:
        """出错时附在报错后面的说明：自动诊断的结论 + 整理过的引擎记录。"""
        text = last_run(read_text(self._api_log_path()))
        notes = diagnose_gsv_api(text)
        out = ""
        if notes:
            out += "自动诊断：\n" + "\n".join("- " + x for x in notes) + "\n"
        tail = condense(text, max_lines=n)
        if tail:
            out += f"引擎记录（{self._api_log_path().name} 最后一次启动的部分，重复的已合并）：\n" + tail
        return out

    def _rotate_api_log(self, path: Path) -> None:
        try:
            if path.exists() and path.stat().st_size > self.API_LOG_MAX_BYTES:
                os.replace(path, path.with_name(path.stem + ".old" + path.suffix))
        except OSError:
            pass  # 改不了名（比如被别的程序打开着）：接着往后写，不影响使用

    def start(self) -> None:
        # 只接着用「自己开的、还活着的」服务，或者 config.yaml 里指定的外部服务（api_url）。
        # 端口上别的程序开的 api_v2（例如以前没关掉的）不接手：它的显卡设置不一定对，结束时也关不掉它。
        # 这时 _free_port 会换一个空闲端口，自己开一个。（v18.2 及以前因为检查方式不对，这条路从来没走到过。）
        own = self.proc is not None and self.proc.poll() is None
        if (own or self.external_url) and self._alive():
            self._ensure_weights()
            return
        if self.external_url:
            raise RuntimeError(f"连接不上 GPT-SoVITS 服务 {self.external_url}，请先启动 api_v2.py")
        problems = self.check()
        if problems:
            raise RuntimeError("GPT-SoVITS 环境有问题：\n- " + "\n- ".join(problems))
        check_cancel()
        if self.proc is not None:  # 上次启动的服务已经不响应了：先收拾掉
            self.stop()
        self.port = _free_port(self.port)
        self.api_url = f"http://127.0.0.1:{self.port}"
        weights = self._current_weights()
        missing = [w for w in (weights.get("gpt"), weights.get("sovits")) if not w or not Path(w).exists()]
        if missing:
            # 真实的 TTS_Config 找不到文件时会悄悄改用官方底模（TTS.py @ main），声音就不像了，所以先说清楚
            raise RuntimeError("找不到要用的模型文件：" + "、".join(str(m) for m in missing)
                               + "。可能被移动或删除了；到「② 训练模型」点「重新挑选最佳模型」，还不行就重新训练一次。")
        cfg_path = self.work_dir / "tts_infer.yaml"
        cfg_path.write_text(yaml.dump({"custom": {
            "bert_base_path": str(self.p(BERT_DIR)), "cnhuhbert_base_path": str(self.p(HUBERT_DIR)),
            "device": str(self.bcfg.get("device", "cuda")), "is_half": self.is_half, "version": self.version,
            "t2s_weights_path": weights["gpt"], "vits_weights_path": weights["sovits"],
        }}, allow_unicode=True), encoding="utf-8")
        log_path = self._api_log_path()
        log.info(f"启动 GPT-SoVITS 推理服务（端口 {self.port}，模型 {weights['id']}）……")
        try:
            total, free, _src = self._gpu_memory(quick=True)
            if total:
                log.info(f"显卡内存：共 {total:.1f} GB，现在可用 {free:.1f} GB" if free is not None
                         else f"显卡内存：共 {total:.1f} GB")
        except Exception:
            pass
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._rotate_api_log(log_path)
        self._log_fh = open(log_path, "a", encoding="utf-8")
        try:  # 分隔线：出错时只看这一次启动的记录
            from voicetwin import __version__

            self._log_fh.write(f"\n{RUN_MARKER} {__version__} 启动推理服务 {time.strftime('%Y-%m-%d %H:%M:%S')}"
                               f"（端口 {self.port}，模型 {weights['id']}）=====\n")
            self._log_fh.flush()
        except Exception:
            pass
        self.proc = subprocess.Popen(
            [self.python, "-s", "api_v2.py", "-a", "127.0.0.1", "-p", str(self.port), "-c", str(cfg_path)],
            cwd=str(self.root), env=self.env(), stdout=self._log_fh, stderr=subprocess.STDOUT, creationflags=creationflags,
        )
        kill_with_parent(self.proc)
        t0 = time.time()
        timeout = float(self.bcfg.get("startup_timeout", 600))
        deadline = t0 + timeout
        next_note = float(self.STARTUP_NOTE_SECONDS)
        open_since: Optional[float] = None  # 端口打开了、但还对不上的开始时间
        last_why = ""
        while time.time() < deadline:
            if cancel_requested():
                self.stop()
                raise TaskCancelled("已按你的要求停止")
            if self.proc.poll() is not None:
                code = self.proc.returncode
                report = self._api_report()
                self.stop()
                raise RuntimeError(f"GPT-SoVITS 推理服务启动失败（退出码 {code}）：\n" + report)
            ok, why = self._probe()
            if ok:
                self._loaded = {"sovits": weights["sovits"], "gpt": weights["gpt"]}
                used = time.time() - t0
                log.info(f"GPT-SoVITS 推理服务已就绪（启动用了 {int(used)} 秒）")
                try:  # 记下实际用了多久，下次进度条上写「上次用了 N 秒」
                    (self.work_dir / "api_start_seconds.txt").write_text(f"{used:.0f}\n", encoding="utf-8")
                except OSError:
                    pass
                return
            if why:
                last_why = why
                if open_since is None:
                    open_since = time.time()
                    log.info("合成引擎已经打开了，正在确认能不能用……")
                elif time.time() - open_since >= float(self.MISMATCH_GRACE_SECONDS):
                    report = self._api_report()
                    self.stop()
                    raise RuntimeError(f"GPT-SoVITS 推理服务打开了，但是程序没法和它对上话：{why}\n" + report)
            else:
                open_since = None
            time.sleep(min(2.0, max(0.1, float(self.STARTUP_NOTE_SECONDS) / 4)))
            waited = time.time() - t0
            if waited >= next_note:
                log.info(f"推理服务启动中（正在加载模型）……已等待 {int(waited)} 秒")
                while next_note <= waited:
                    next_note += float(self.STARTUP_NOTE_SECONDS)
        report = self._api_report()
        self.stop()
        state = last_why or "合成引擎一直没有加载完模型（端口没有打开）"
        raise RuntimeError(f"GPT-SoVITS 推理服务启动超时（等了 {int(timeout)} 秒，{state}）。"
                           f"引擎的完整记录在 {log_path}\n" + report)

    def stop(self) -> None:
        if self.proc is not None:
            if self.proc.poll() is None:
                asked = False
                try:  # 官方 api_v2 收到 exit 会直接结束自己，通常来不及回复
                    self._session().get(f"{self.api_url}/control", params={"command": "exit"}, timeout=3)
                    asked = True
                except Exception:
                    pass
                try:
                    self.proc.wait(timeout=10 if asked else 2)
                except Exception:
                    kill_process_tree(self.proc)
                    try:
                        self.proc.wait(timeout=10)
                    except Exception:
                        pass
            self.proc = None
            try:
                if self._log_fh is not None:
                    self._log_fh.close()
            except Exception:
                pass
            self._log_fh = None
        self._loaded = {}

    def _set_weights(self, gpt: str, sovits: str) -> None:
        s = self._session()
        for kind, path, route in (("GPT", gpt, "set_gpt_weights"), ("SoVITS", sovits, "set_sovits_weights")):
            key = kind.lower()
            if not path or self._loaded.get(key) == path:
                continue
            r = s.get(f"{self.api_url}/{route}", params={"weights_path": path}, timeout=600)
            if r.status_code != 200:
                # 真实的 api_v2 失败时回 400 {"message": "change gpt weight failed", "Exception": "真正的原因"}
                raise RuntimeError(f"切换 {kind} 模型失败：{_api_reason(r)}（{path}）\n" + self._api_report(20))
            self._loaded[key] = path

    def _ensure_weights(self) -> None:
        w = self._current_weights()
        if w["sovits"] and w["gpt"]:
            self._set_weights(w["gpt"], w["sovits"])

    def use_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        if not self._alive():
            self.start()
        self._set_weights(ckpt["gpt"], ckpt["sovits"])

    def _server_died(self) -> bool:
        return self.proc is not None and self.proc.poll() is not None

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        if not self._alive():
            self.start()
        icfg = self.bcfg.get("infer", {}) or {}
        # 语速：speed_factor 在模型内部控制时长（SoVITS 解码前把内容特征序列按 1/speed 插值拉长或缩短，
        # 再由声码器生成波形，见 GPT_SoVITS/module/models.py 的 TextEncoder.forward），音高和音色不变；
        # 官方代码里对整段音频做 atempo 变速的写法已经注释掉了（TTS.py）。所以这里不对生成的音频做任何重采样或变速。
        speed = float(req.speed or 1.0)
        if not math.isfinite(speed) or speed <= 0:
            speed = 1.0
        payload = {
            "text": req.text,
            "text_lang": "en" if req.lang == "en" else "zh",
            "ref_audio_path": str(Path(req.ref_audio).resolve()),
            "aux_ref_audio_paths": [str(Path(p).resolve()) for p in req.aux_refs],
            "prompt_text": req.ref_text,
            "prompt_lang": "en" if req.ref_lang == "en" else "zh",
            "top_k": int(req.top_k if req.top_k is not None else icfg.get("top_k", 15)),
            "top_p": float(req.top_p if req.top_p is not None else icfg.get("top_p", 1.0)),
            "temperature": float(req.temperature if req.temperature is not None else icfg.get("temperature", 1.0)),
            "text_split_method": "cut0",   # 已按句切好，不再二次切分，保留模型自己的句内停顿
            "batch_size": 1,
            "speed_factor": max(0.25, min(4.0, speed)),
            "fragment_interval": 0.3,
            "seed": int(req.seed),
            "media_type": "wav",
            "streaming_mode": False,
            "parallel_infer": True,
            "repetition_penalty": float(icfg.get("repetition_penalty", 1.35)),
            "sample_steps": int(icfg.get("sample_steps", 32)),
            "super_sampling": False,
        }
        import requests

        try:
            log_pos = self._api_log_path().stat().st_size
        except OSError:
            log_pos = 0
        r = None
        for attempt in (1, 2):
            try:
                r = self._session().post(f"{self.api_url}/tts", json=payload, timeout=600)
                break
            except Exception as exc:
                if self._server_died():
                    raise RuntimeError("GPT-SoVITS 推理服务意外退出了。\n" + self._api_report(20)) from exc
                # 连接被断开（比如空闲太久后服务端刚好关掉了旧连接）：服务还活着就重试一次，不算这句失败
                if attempt == 1 and isinstance(exc, requests.exceptions.ConnectionError) and self._alive():
                    log.debug(f"连接合成引擎时断开了一下（{type(exc).__name__}），重试一次")
                    continue
                raise
        assert r is not None
        if r.status_code != 200:
            # api_v2 合成出错时返回 {"message": "tts failed", "Exception": "真正的原因"}
            text = f"GPT-SoVITS 合成失败：{_api_reason(r)}"
            if self._server_died():
                text += "\n推理服务已经退出了。\n" + self._api_report(20)
            raise RuntimeError(text)
        silent = _silent_answer(r.content)
        if silent:
            # 真实的 TTS.run 出错时（比如显存不够）不报错：打印 Traceback，然后回 200 + 1 秒 16 kHz 的静音
            # （GPT_SoVITS/TTS_infer_pack/TTS.py @ abe9843 第 1516~1518 行）。模拟版回的是 400，所以以前没发现。
            reason = _last_exception(self._api_new_text(log_pos))
            raise RuntimeError("GPT-SoVITS 合成失败：" + (reason or f"引擎回了一段{silent}，记录里没有报错"
                                                         "（可能是这句话里没有它能读出来的字）")
                               + "\n" + self._api_report(20))
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        return out_path

    def _api_new_text(self, pos: int) -> str:
        """引擎记录从 pos（字节）之后新写的内容。"""
        try:
            if self._log_fh is not None:
                self._log_fh.flush()
        except Exception:
            pass
        try:
            with open(self._api_log_path(), "rb") as fh:
                fh.seek(max(0, pos))
                return fh.read(2_000_000).decode("utf-8", errors="replace")
        except OSError:
            return ""


def _epoch(path: Path) -> int:
    m = re.search(r"_e(\d+)_s\d+\.pth$", str(path)) or re.search(r"-e(\d+)\.ckpt$", str(path))
    return int(m.group(1)) if m else 0
