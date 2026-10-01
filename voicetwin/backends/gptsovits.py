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
- DPO 是官方的实验功能：只在显存 ≥ 22 GB、素材干净时自动开启，其余情况不开。
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
from voicetwin.utils.log import get_logger
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
DPO_AUTO_MIN_GB = 22.0            # DPO 显存翻倍、语气训练慢 2~4 倍：只在 22 GB 以上自动开
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


def _auto_save_every(epochs: int) -> Tuple[int, int]:
    """自动的保存间隔：返回 (轮数, 每几轮存一次)。

    GPT-SoVITS 只在「轮数是保存间隔的整数倍」时导出模型，所以最后一轮必须是倍数，否则最后一轮的模型存不下来。
    尽量让每个模型存 5 个左右（3~8 个，同样接近时多存）；轮数是大于 8 的质数时多练 1 轮凑成偶数。"""
    epochs = max(1, int(epochs))
    if epochs <= 2:
        return epochs, 1
    for e in (epochs, epochs + 1):
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
        if best is not None:
            return e, best[1]
    return epochs, 1  # 走不到这里（epochs+1 是偶数，总能找到）


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
            new_ep, save = _auto_save_every(epochs)
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
        if g < DPO_AUTO_MIN_GB:
            dpo, why_not = False, f"它是实验功能，要显存 ≥ {DPO_AUTO_MIN_GB:.0f} GB，开了语气训练会慢 2～4 倍"
        elif noisy:
            dpo, why_not = False, "素材有底噪或背景音乐，开了反而可能变差"
        elif n_clips and suspects / float(n_clips) > SUSPECT_MAX_RATIO:
            dpo, why_not = False, f"还有 {suspects} 条文字可能有错，先校对好再开"
        else:
            dpo = True
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
        return bool(self.bcfg.get("is_half", True))

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

    def _gpu_memory(self) -> Tuple[float, Optional[float], str]:
        """（显存 GiB 原始读数, 空闲 GiB 或 None, 来源）。先用网页顶部那个显卡检查（快，还知道空闲多少），
        读不到时再用 GPT-SoVITS 自己的 PyTorch 读（慢一点）。"""
        try:
            from voicetwin.utils.gpu import gpu_status

            st = gpu_status(refresh=True)
            total = _pos_float(st.get("total_gb"))
            if st.get("level") != "error" and total:
                free = st.get("free_gb")
                return total, (_pos_float(free) if free is not None else None), str(st.get("source") or "gpu")
        except Exception:
            pass
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

    def _make_plan(self, n_clips: int, minutes: float, opts: Dict[str, Any]) -> Dict[str, Any]:
        total, free, source = self._gpu_memory()
        if total <= 0:
            log.warning("没有检测到可用的 NVIDIA 显卡，训练会非常慢（CPU 训练可能需要数天）")
        noisy, share, suspects = self._material_quality()
        plan = plan_training(n_clips, minutes, total, free, is_half=self.is_half, noisy=noisy, suspects=suspects,
                             user=self._user_settings(opts))
        plan["gpu_source"] = source
        plan["noisy_share"] = round(share, 2)
        return plan

    def training_plan(self, **opts: Any) -> Dict[str, Any]:
        """训练前预览这次的自动训练设置（不训练、不导出文件）。"""
        from voicetwin.data.exporters import train_records

        recs = train_records(self.project)
        minutes = round(sum(float(r.get("duration") or 0.0) for r in recs) / 60.0, 1)
        return self._make_plan(len(recs), minutes, opts)

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

    def _archive_old_run(self, opt_dir: Path) -> Optional[Path]:
        """素材变了：把旧的训练进度（GPT-SoVITS 会从这里接着练）移到 old_runs/<时间>/，这次从头训练。"""
        names = [f"logs_s2_{self.version}", f"logs_s1_{self.version}", "logs_s1"]
        existing = []
        for n in names:
            d = opt_dir / n
            try:
                if d.is_dir() and any(d.iterdir()):
                    existing.append(d)
            except OSError:
                continue
        if not existing:
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
        if not moved:
            try:
                dest.rmdir()
            except OSError:
                pass
        old_root = opt_dir / "old_runs"
        try:  # 只留最近几次备份（每次大约 1 GB），免得占满硬盘
            runs = sorted((p for p in old_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)
            for p in runs[:-KEEP_OLD_RUNS]:
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
        log.info(f"实验名 {self.exp_name}；版本 {self.version}")
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
        self.project.update_models(self.name, info)
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
        w = self._current_weights()
        return f"gsv-{self.version}-{w['id']}-{short_hash(w['sovits'], w['gpt'], n=6)}"

    def _session(self):
        if self._http is None:
            import requests

            self._http = requests.Session()
            self._http.trust_env = False  # 访问本机服务不走代理
        return self._http

    def _alive(self) -> bool:
        """api_v2 对不带参数的 /tts 请求会返回 400 + {"message": ...}，以此判断服务已就绪。"""
        try:
            r = self._session().get(f"{self.api_url}/tts", timeout=3)
            return r.status_code == 400 and "message" in r.json()
        except Exception:
            return False

    def _api_log_path(self) -> Path:
        return self.project.logs_dir / "gptsovits_api.log"

    def _api_tail(self, n: int) -> str:
        try:
            if self._log_fh is not None:
                self._log_fh.flush()
        except Exception:
            pass
        try:
            lines = self._api_log_path().read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        return "\n".join(lines[-n:])

    def start(self) -> None:
        if self._alive():
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
        cfg_path = self.work_dir / "tts_infer.yaml"
        cfg_path.write_text(yaml.dump({"custom": {
            "bert_base_path": str(self.p(BERT_DIR)), "cnhuhbert_base_path": str(self.p(HUBERT_DIR)),
            "device": str(self.bcfg.get("device", "cuda")), "is_half": self.is_half, "version": self.version,
            "t2s_weights_path": weights["gpt"], "vits_weights_path": weights["sovits"],
        }}, allow_unicode=True), encoding="utf-8")
        log_path = self._api_log_path()
        log.info(f"启动 GPT-SoVITS 推理服务（端口 {self.port}，模型 {weights['id']}）……")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._log_fh = open(log_path, "a", encoding="utf-8")
        self.proc = subprocess.Popen(
            [self.python, "api_v2.py", "-a", "127.0.0.1", "-p", str(self.port), "-c", str(cfg_path)],
            cwd=str(self.root), env=self.env(), stdout=self._log_fh, stderr=subprocess.STDOUT, creationflags=creationflags,
        )
        t0 = time.time()
        deadline = t0 + float(self.bcfg.get("startup_timeout", 600))
        next_note = float(self.STARTUP_NOTE_SECONDS)
        while time.time() < deadline:
            if cancel_requested():
                self.stop()
                raise TaskCancelled("已按你的要求停止")
            if self.proc.poll() is not None:
                tail = self._api_tail(30)
                self.stop()
                raise RuntimeError("GPT-SoVITS 推理服务启动失败：\n" + tail)
            if self._alive():
                self._loaded = {"sovits": weights["sovits"], "gpt": weights["gpt"]}
                log.info("GPT-SoVITS 推理服务已就绪")
                return
            time.sleep(min(2.0, max(0.1, float(self.STARTUP_NOTE_SECONDS) / 4)))
            waited = time.time() - t0
            if waited >= next_note:
                log.info(f"推理服务启动中……已等待 {int(waited)} 秒（第一次比较慢，请稍等）")
                while next_note <= waited:
                    next_note += float(self.STARTUP_NOTE_SECONDS)
        self.stop()
        raise RuntimeError(f"GPT-SoVITS 推理服务启动超时，请查看 {log_path}")

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
        if gpt and self._loaded.get("gpt") != gpt:
            r = s.get(f"{self.api_url}/set_gpt_weights", params={"weights_path": gpt}, timeout=600)
            if r.status_code != 200:
                raise RuntimeError(f"切换 GPT 模型失败：{r.text}")
            self._loaded["gpt"] = gpt
        if sovits and self._loaded.get("sovits") != sovits:
            r = s.get(f"{self.api_url}/set_sovits_weights", params={"weights_path": sovits}, timeout=600)
            if r.status_code != 200:
                raise RuntimeError(f"切换 SoVITS 模型失败：{r.text}")
            self._loaded["sovits"] = sovits

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
        try:
            r = self._session().post(f"{self.api_url}/tts", json=payload, timeout=600)
        except Exception as exc:
            if self._server_died():
                raise RuntimeError("GPT-SoVITS 推理服务意外退出了。最后的日志：\n" + self._api_tail(5)) from exc
            raise
        if r.status_code != 200:
            try:
                j = r.json()
                # api_v2 合成出错时返回 {"message": "tts failed", "Exception": "真正的原因"}
                msg = (j.get("Exception") or j.get("message") or r.text) if isinstance(j, dict) else r.text
            except Exception:
                msg = r.text
            text = f"GPT-SoVITS 合成失败：{msg}"
            if self._server_died():
                text += "\n推理服务已经退出了，最后的日志：\n" + self._api_tail(5)
            raise RuntimeError(text)
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        return out_path


def _epoch(path: Path) -> int:
    m = re.search(r"_e(\d+)_s\d+\.pth$", str(path)) or re.search(r"-e(\d+)\.ckpt$", str(path))
    return int(m.group(1)) if m else 0
