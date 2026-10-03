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
- 训练时显存不够（CUDA out of memory）：每批数量一次减 1 条接着练（最多减 3 次，已经练好的部分会接着用）。
高级设置 / config.yaml / 命令行里明确填写的数值优先。

两种训练方式（backends.gptsovits.train.mode，网页「训练方式」，命令行 --mode）：
- standard（标准）：上面这些，和以前一样的训练量；
- identical（「一模一样」，默认）：练得更久、多存几个版本（每批 4 条时音色 24 轮每 2 轮存一个、语气 20 轮每轮存一个），
  训练前先用官方的训练程序实测显卡一次最多能练几条（_probe_batch：练够 40 步或 90 秒就停，比每秒练几条、看显存有没有满），
  每批多练几条时轮数按比例加多（模型更新的次数和每批 4 条时一样）。训练完把每个存下的版本都拿来比较。
两种方式都用 VoiceTwin 自己的「处理文字」（gsv_scripts/get_text_mixed.py：中文句子里夹着的英文也参加训练，
不成功自动退回官方的 1-get-text.py）和「末尾没有标点补「，」」：这两条是修正素材，不是加大训练量。
素材、处理文字的方法、录音文件变了 → 从头训练（旧模型备份起来，下次挑选时也参加比较）；
没变而计划练得更多 → 接着上次往下练；没变而且已经练够了 → 不重新训练，直接挑选。
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import re
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import yaml

from voicetwin.backends.base import (
    OOM_PATTERN,
    SEED_STEP,
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
    many_prefix,
    resolve_python,
)
from voicetwin.backends.worker import subprocess_env
from voicetwin.utils.winsys import kill_with_parent
from voicetwin.utils.log import get_logger
from voicetwin.utils.logtail import RUN_MARKER, condense, diagnose_gsv_api, last_run, read_text
from voicetwin.utils.textutil import send_lang, short_hash

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

# ---------------------------------------------------------------- 「一模一样」训练（设计方案 §1.2、§2 P7）
TRAIN_MODES = ("identical", "standard")
#: 每批 4 条时的训练量：音色 24 轮每 2 轮存一个，语气 20 轮每轮存一个（官方 s1longer-v2.yaml 的默认 20 轮 / 每轮存）
SOVITS_EPOCHS_DEEP = 24
GPT_EPOCHS_DEEP = 20
SOVITS_SAVE_DEEP = 2
GPT_SAVE_DEEP = 1
DEEP_BASE_BATCH = 4
#: 每批多练几条时轮数按比例加多，但不超过这些（练太多会变差；每个存下的版本都会拿来比较）
DEEP_MAX_SOVITS = 48
#: 实测显卡一次能练几条：用最长的 128 条素材，每个数量练够 40 步（日志里记的步数）或 90 秒就停，第 10 步以后才算速度
PROBE_CLIPS = 128
PROBE_SOVITS = (4, 5, 6, 8)
PROBE_GPT = (4, 6, 8, 12)
PROBE_STEPS = 40
PROBE_SECONDS = 90.0
PROBE_WARMUP_STEPS = 10
#: 大一点的数量至少要快这么多才用它（Windows 显存满了不报错，而是借用内存、变慢）
PROBE_MIN_GAIN = 1.05
#: 显存最高用到「总显存 − 0.3 GB」以上算满了（再大就会借用内存）
PROBE_SPILL_GB = 0.3
#: 训练时显存不够：每批减 1 条再练，最多减几次
OOM_MAX_RETRIES = 3
#: 实际参加训练的不到这么多就提醒；VoiceTwin 自己的「处理文字」写出来的不到这么多句就退回官方的方法
MIN_TRAINED_SHARE = 0.98
MIXED_MIN_SHARE = 0.98
#: 硬盘至少留这么多（GB）
DISK_RESERVE_GB = 2.0
#: 显卡平均使用率低于它（%）时说明「主要卡在处理器或读文件上」
LOW_GPU_UTIL = 70.0
#: 处理文字用的方法：mixed（VoiceTwin 自己的，中英文一起）/ official（官方 1-get-text.py）
FRONTEND_FILE = "voicetwin_frontend.txt"
FEATURES_FILE = "voicetwin_features.json"
PROBE_FILE = "voicetwin_probe.json"
MIXED_SCRIPT = Path(__file__).resolve().parent / "gsv_scripts" / "get_text_mixed.py"
TEXT_FEATURES = ("2-name2text.txt", "3-bert")
ALL_FEATURES = ("2-name2text.txt", "6-name2semantic.tsv", "3-bert", "4-cnhubert", "5-wav32k", "7-sv_cn")


#: 训练进度（引擎自己的 0~1）里每一步从哪开始。standard 和以前完全一样；identical 多一步「实测显卡一次能练几条」，
#: 两步训练占得更多（练得更久）
TRAIN_POS: Dict[str, Dict[str, float]] = {
    "standard": {"plan": 0.03, "text": 0.05, "hubert": 0.12, "sv": 0.18, "semantic": 0.20, "probe": 0.25,
                 "sovits": 0.25, "gpt": 0.60, "save": 0.95},
    "identical": {"plan": 0.02, "text": 0.03, "hubert": 0.10, "sv": 0.16, "semantic": 0.19, "probe": 0.22,
                  "sovits": 0.29, "gpt": 0.72, "save": 0.95},
}
TRAIN_STAGES_IDENTICAL: List[Tuple[float, str]] = [
    (0.00, "检查显卡、整理训练素材"), (0.03, "处理文字"), (0.10, "提取声音特征"), (0.19, "提取语义"),
    (0.22, "实测显卡一次能练几条"), (0.29, "训练音色（SoVITS）"), (0.72, "训练语气和节奏（GPT）"),
    (0.95, "保存模型、核对实际参加训练的条数"),
]


def resolve_train_mode(value: Any) -> str:
    """训练方式：auto / 空 / 「一模一样」/ identical → identical；standard / 标准 → standard；不认识的写法用默认的 identical。"""
    s = str(value if value is not None else "").strip().lower()
    if s in ("standard", "标准", "std") or s.startswith("标准"):
        return "standard"
    if s not in ("", "auto", "自动", "none", "identical") and not s.startswith("一模一样"):
        log.warning(f"不认识的训练方式「{value}」，改用默认的「一模一样」")
    return "identical"


def _half_up(x: float) -> int:
    """四舍五入（Python 的 round 是「银行家舍入」，2.5 会变成 2）。"""
    return int(math.floor(float(x) + 0.5))

# ---------------------------------------------------------------- 一次请求同时生成同一句话的好几个版本（「一模一样」档）
# 做法：同一句话复制 n 份、用换行隔开，text_split_method=cut0、batch_size=n。官方 TTS.py（@ abe9843）按换行切成 n 段，
# 一批一起生成（每一行各自抽样，所以是 n 个不同的版本），每段后面补 fragment_interval 秒的数字静音
# （audio_postprocess），程序再按这些静音把 n 个版本切开。
#: 每个版本后面补的数字静音（秒）
BATCH_INTERVAL = 0.5
#: 语速正好是 1.0 时改成发这个数。TTS.py 在 speed_factor == 1.0 时把整批的语义拼在一起、一次解码，再按估算的位置切开
#: （版本之间互相影响，和单独生成的不一样）；不是 1.0 时每段单独解码，和单独生成时完全一样。
#: 1.0001 时长度不变：models.py 里新长度是 int(L / 1.0001) + 1，L 在 1~9999 帧时都正好等于 L（算过，见
#: research/一模一样/scripts/sim_batch_copies_结果.txt）。同样长度的线性插值应该就是原样，但开发机没有 torch、没有实测，
#: 所以每次启动引擎先自检（_speed_trick_ok），没通过就不用这个办法。
BATCH_SPEED = 1.0001
#: 文字超过这么多个字就不同时生成（单独生成）
BATCH_MAX_CHARS = 400
#: 能同时生成的模型版本（V3 / V4 用另一套声码器的做法，一个一个生成）
BATCH_VERSIONS = ("v2", "v2Pro", "v2ProPlus")
#: 切开后每个版本至少多长（秒）；切开后每个版本后面补多长的数字静音（秒，和单独生成时引擎补的 0.3 秒一样）
BATCH_MIN_PIECE = 0.3
BATCH_PAD = 0.3
#: 「语速 1.0001」自检：长度最多差多少、波形相关系数至少多少、最多换几个随机种子试
SPEED_TRICK_MAX_LEN_DIFF = 0.01
SPEED_TRICK_MIN_R = 0.99
SPEED_TRICK_SEEDS = 2

# 下面照抄官方切分文字的规则（GPT_SoVITS/TTS_infer_pack/TextPreprocessor.py 的 replace_consecutive_punctuation、
# pre_seg_text、merge_short_text_in_array、get_first，text_segmentation_method.py 的 splits、punctuation、cut0），
# 用来提前算出一次请求会被切成几段。老师的 1004 句素材复制 4 份，全部正好切成 4 段（sim_batch_copies_结果.txt）。
_GSV_SPLITS = frozenset({"，", "。", "？", "！", ",", ".", "?", "!", "~", ":", "：", "—", "…"})
_GSV_SEG_PUNCT = frozenset({"!", "?", "…", ",", ".", "-", " "})       # text_segmentation_method.punctuation（cut0 用）
_GSV_TP_PUNCT = "".join(re.escape(x) for x in ("!", "?", "…", ",", ".", "-"))   # TextPreprocessor.punctuation
_GSV_CONSECUTIVE = re.compile(f"([{_GSV_TP_PUNCT}])([{_GSV_TP_PUNCT}])+")
_GSV_FIRST = re.compile("[" + "".join(re.escape(x) for x in sorted(_GSV_SPLITS)) + "]")
_GSV_MERGE_SHORT = 5    # pre_seg_text 里 merge_short_text_in_array(_texts, 5)


def _gsv_first(text: str) -> str:
    """get_first：第一个标点之前的部分。"""
    return _GSV_FIRST.split(text)[0].strip()


def _gsv_merge_short(texts: List[str], threshold: int) -> List[str]:
    """merge_short_text_in_array：太短（不到 threshold 个字）的段和后面的合在一起。"""
    if len(texts) < 2:
        return texts
    result: List[str] = []
    text = ""
    for ele in texts:
        text += ele
        if len(text) >= threshold:
            result.append(text)
            text = ""
    if text:
        if not result:
            result.append(text)
        else:
            result[-1] += text
    return result


def _gsv_pre_seg(text: str, lang: str) -> List[str]:
    """官方 TextPreprocessor.preprocess 用 cut0 时实际会合成的那几段文字（split_big_text 只管超过 510 个字的段，这里用不到）。"""
    text = _GSV_CONSECUTIVE.sub(r"\1", text)          # replace_consecutive_punctuation
    text = text.strip("\n")
    if not text:
        return []
    if text[0] not in _GSV_SPLITS and len(_gsv_first(text)) < 4:
        text = ("。" if lang != "en" else ".") + text
    if set(text).issubset(_GSV_SEG_PUNCT):            # cut0：只有标点时变成 "/n"
        text = "/n"
    while "\n\n" in text:
        text = text.replace("\n\n", "\n")
    parts = [t for t in text.split("\n") if t not in (" ", "")]    # filter_text
    out: List[str] = []
    for t in _gsv_merge_short(parts, _GSV_MERGE_SHORT):
        if not t.strip() or not re.sub(r"\W+", "", t):
            continue
        if t[-1] not in _GSV_SPLITS:
            t += "。" if lang != "en" else "."
        out.append(t)
    return out


def _batch_text(text: str, lang: str, n: int) -> Optional[str]:
    """同时生成 n 个版本时发给引擎的文字：同一句话复制 n 份、用换行隔开；每份开头先加上单独生成时引擎自己会加的
    「。」/「.」（pre_seg_text：第一个标点前不到 4 个字时加），这样每一段都和单独生成时一模一样。

    按官方规则算出来不是正好 n 段、每段都和单独生成的那一段一样（例如「好的。」这种很短的句子会被合并），
    或者文字里有换行、超过 BATCH_MAX_CHARS 个字时，返回 None（只能一个一个生成）。lang 是发给引擎的 text_lang。"""
    n = int(n)
    if n < 2 or not text or "\n" in text or len(text) > BATCH_MAX_CHARS:
        return None
    one = text
    if one[0] not in _GSV_SPLITS and len(_gsv_first(_GSV_CONSECUTIVE.sub(r"\1", one))) < 4:
        one = ("。" if lang != "en" else ".") + one
    single = _gsv_pre_seg(text, lang)
    batched = "\n".join([one] * n)
    if len(single) != 1 or _gsv_pre_seg(batched, lang) != single * n:
        return None
    return batched


def _api_reason(r: Any) -> str:
    """api_v2 出错时回答里的真正原因（JSON 的 Exception / message），不是 JSON 就用原文。"""
    try:
        j = r.json()
        if isinstance(j, dict):
            return str(j.get("Exception") or j.get("message") or r.text)
    except Exception:
        pass
    return str(r.text or f"HTTP {getattr(r, 'status_code', '?')}")


def _fix_int16_wrap(data: bytes) -> bytes:
    """修好真实 GPT-SoVITS 输出里的「咔哒」声。

    半精度（is_half）时声码器最后的 tanh 会正好等于 1.0，TTS.py 的 audio_postprocess 只在 >1 时才缩放，
    然后 (audio * 32768).astype(np.int16) 把 32768 溢出成 -32768：一个满幅度的跳变，听起来就是「咔哒」。
    （GPT_SoVITS/TTS_infer_pack/TTS.py @ abe9843 第 1559、1590 行。）真正的 -1.0 两边是负的，溢出的两边是正的，
    所以把两边有正数的 -32768 改回 32767。没有这种情况就原样返回。"""
    try:
        import io

        import numpy as np
        import soundfile as sf

        info = sf.info(io.BytesIO(data))
        if info.subtype != "PCM_16" or info.channels != 1:
            return data
        x, sr = sf.read(io.BytesIO(data), dtype="int16", always_2d=False)
        idx = np.flatnonzero(x == -32768)
        if idx.size == 0:
            return data
        brk = np.r_[True, np.diff(idx) > 1]
        starts, ends = idx[brk], idx[np.r_[brk[1:], True]]
        fixed = 0
        for a, b in zip(starts, ends):
            before = int(x[a - 1]) if a > 0 else 0
            after = int(x[b + 1]) if b + 1 < len(x) else 0
            if before > 0 or after > 0:
                x[a:b + 1] = 32767
                fixed += int(b - a + 1)
        if not fixed:
            return data
        buf = io.BytesIO()
        sf.write(buf, x, sr, format="WAV", subtype="PCM_16")
        log.debug(f"修好了 {fixed} 个溢出的采样点（半精度时 1.0 变成了 -32768）")
        return buf.getvalue()
    except Exception:
        return data


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


def _read_int16(data: bytes) -> Tuple["Any", int]:
    """WAV 内容 → (int16 数组, 采样率)，先修好半精度溢出的「咔哒」声。读不了时抛异常。"""
    import io

    import soundfile as sf

    x, sr = sf.read(io.BytesIO(_fix_int16_wrap(data)), dtype="int16", always_2d=False)
    return x, int(sr)


def _split_wav(data: bytes, n: int, interval: float = BATCH_INTERVAL) -> Tuple[Optional[List["Any"]], int, str]:
    """把一次请求同时生成的 n 个版本按它们后面的数字静音切开：返回 (n 段 int16 数组, 采样率, 切不开的原因)。

    规则很严：至少 round(0.6 × interval × 采样率) 个连着的 0 才算版本之间的静音（V3 / V4 的 48 kHz 输出里，
    引擎按 32 kHz 算的静音也够长）；必须正好 n 段，最后一段静音到文件结尾（差 1 个采样点以内）；每个版本至少
    BATCH_MIN_PIECE 秒、而且有声音。每段后面补 BATCH_PAD 秒的 0（和单独生成时一样）。不符合就返回 (None, 采样率, 原因)，
    调用的地方改成一个一个生成。"""
    import numpy as np

    try:
        x, sr = _read_int16(data)
    except Exception as exc:
        return None, 0, f"读不了引擎回的声音（{type(exc).__name__}）"
    if getattr(x, "ndim", 0) != 1 or not sr:
        return None, sr, "引擎回的不是单声道的声音"
    need = max(1, int(round(0.6 * float(interval) * sr)))
    z = np.concatenate([[False], x == 0, [False]]).astype(np.int8)
    d = np.diff(z)
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    long_ = (ends - starts) >= need
    runs = list(zip(starts[long_].tolist(), ends[long_].tolist()))
    if len(runs) != int(n):
        return None, sr, f"找到 {len(runs)} 段长的静音，应该是 {int(n)} 段"
    if len(x) - runs[-1][1] > 1:
        return None, sr, "最后一段静音没有到结尾"
    pad = np.zeros(int(round(BATCH_PAD * sr)), dtype=np.int16)
    out: List[Any] = []
    prev = 0
    for i, (a, b) in enumerate(runs):
        piece = x[prev:a]
        if len(piece) < BATCH_MIN_PIECE * sr:
            return None, sr, f"第 {i + 1} 个版本太短（{len(piece) / sr:.2f} 秒）"
        if not piece.any():
            return None, sr, f"第 {i + 1} 个版本没有声音"
        out.append(np.concatenate([piece.astype(np.int16), pad]))
        prev = b
    return out, sr, ""


def _split_fragments(data: bytes, n: int, interval: float = BATCH_INTERVAL) -> Optional[List["Any"]]:
    """_split_wav 只要切好的 n 段（切不开时是 None）。"""
    return _split_wav(data, n, interval)[0]


def _speed_of(req: SynthRequest) -> float:
    """请求里的语速（不合理的数当 1.0），限制在 api_v2 能用的 0.25~4.0 之间。"""
    speed = float(req.speed or 1.0)
    if not math.isfinite(speed) or speed <= 0:
        speed = 1.0
    return max(0.25, min(4.0, speed))


def _answer_error(text: str, reason: str) -> RuntimeError:
    """合成失败的报错（和以前一样是 RuntimeError）；oom=True 表示引擎说的原因是显存不够（只看这一次的原因，
    不看记录里以前的报错）。"""
    err = RuntimeError(text)
    err.oom = bool(reason and OOM_PATTERN.search(reason))  # type: ignore[attr-defined]
    return err


def _new_batch_stats() -> Dict[str, Any]:
    """同时生成好几个版本的实测记录（写进报告用）。"""
    return {"requests": 0, "pieces": 0, "by_batch": {}, "oom_backoffs": 0, "split_fallbacks": 0, "split_reason": "",
            "gpu_releases": 0, "single_reasons": {}, "speed_trick": None, "speed_trick_reason": "", "max_batch": None}


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


def _clip_signature(names: List[str], wav_dir: Path) -> str:
    """训练用的录音文件的指纹：每个文件的「名字|大小|修改时间（纳秒）」排好序算 sha1。

    录音文件换过（例如重新准备素材、手动替换了片段）时，旧的声音特征就不能再用了。"""
    rows = []
    for name in sorted(set(str(n) for n in names if n)):
        try:
            st = (Path(wav_dir) / name).stat()
            rows.append(f"{name}|{st.st_size}|{st.st_mtime_ns}")
        except OSError:
            rows.append(f"{name}|missing")
    return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest()


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
                  user: Optional[Dict[str, Any]] = None, mode: str = "standard", probe_batch: Any = None,
                  deep: Optional[Dict[str, Any]] = None, will_probe: bool = False, n_val: Optional[int] = None,
                  en_lines: Optional[int] = None, mixed_text: bool = False,
                  batch_source: str = "probe") -> Dict[str, Any]:
    """根据显存和素材，算出这次的训练设置，并写一行中文说明（summary）。纯计算，不碰显卡和文件。

    user 里不是「自动」的值优先（来自高级设置 / config.yaml / 命令行）。
    mode="identical"（「一模一样」）：每批 b 条（probe_batch = 实测出来的；可以是一个数，也可以是
    {"sovits": b1, "gpt": b2}；没有实测时按显存的公式）时，音色 min(48, ⌈24·b/4⌉) 轮、每 max(1, round(2·b/4)) 轮存一个，
    语气 min(50, ⌈20·b/4⌉) 轮、每 max(1, round(b/4)) 轮存一个——模型更新的次数和每批 4 条时一样；最后一轮一定存下来。
    deep 可以改每批 4 条时的轮数和保存间隔（config.yaml 的 deep_sovits_epochs 等）。standard 的结果和以前完全一样。
    will_probe / n_val / en_lines / mixed_text / batch_source 只影响说明里的话（会不会先实测、挑选用几句录音、
    几句夹着英文、probe_batch 是实测的 "probe" 还是接着练时沿用上次的 "previous"）。"""
    user = dict(user or {})
    mode = mode if mode in TRAIN_MODES else "standard"
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
            notes.append("显存不到 12 GB 还开 DPO，很可能显存不够（会自动减少每批数量再试）")

    if mode == "identical":
        return _plan_deep(locals())

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
        "mode": "standard",
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


def _probe_pair(probe_batch: Any) -> Tuple[Optional[int], Optional[int]]:
    """probe_batch（一个数，或 {"sovits": b1, "gpt": b2}）→ (音色的每批条数, 语气的每批条数)，没有的是 None。"""
    if isinstance(probe_batch, dict):
        vals = [probe_batch.get("sovits"), probe_batch.get("gpt")]
    else:
        vals = [probe_batch, probe_batch]
    out: List[Optional[int]] = []
    for v in vals:
        n = _to_int(v, 0) if v is not None and not isinstance(v, bool) else 0
        out.append(n if n > 0 else None)
    return out[0], out[1]


def _plan_deep(v: Dict[str, Any]) -> Dict[str, Any]:
    """plan_training 的「一模一样」部分（v 是 plan_training 里算到 DPO 为止的局部变量）。"""
    user, auto, notes = v["user"], v["auto"], v["notes"]
    deep = dict(v.get("deep") or {})
    base_s = max(1, _to_int(deep.get("sovits_epochs"), SOVITS_EPOCHS_DEEP))
    base_g = max(1, _to_int(deep.get("gpt_epochs"), GPT_EPOCHS_DEEP))
    base_ss = max(1, _to_int(deep.get("sovits_save"), SOVITS_SAVE_DEEP))
    base_gs = max(1, _to_int(deep.get("gpt_save"), GPT_SAVE_DEEP))
    p_s, p_g = _probe_pair(v.get("probe_batch"))
    clip_cap = v["clip_cap"]
    bs, gpt_bs = v["bs"], v["gpt_bs"]
    if auto["batch_size"]:  # 你自己填了每批数量：不实测，用你填的
        if p_s:
            bs = min(p_s, clip_cap) if v["n_clips"] else p_s
        if p_g and not v["dpo"]:
            gpt_bs = min(p_g, clip_cap) if v["n_clips"] else p_g
        elif not v["dpo"]:
            gpt_bs = bs if not p_g else gpt_bs

    def scaled(base_ep: int, base_save: int, b: int, cap: int) -> Tuple[int, int]:
        return min(cap, int(math.ceil(base_ep * b / float(DEEP_BASE_BATCH)))), max(1, _half_up(base_save * b / float(DEEP_BASE_BATCH)))

    s_ep, s_save = scaled(base_s, base_ss, bs, DEEP_MAX_SOVITS)
    g_ep, g_save = scaled(base_g, base_gs, gpt_bs, GPT_MAX_EPOCHS)
    if not auto["sovits_epochs"]:
        s_ep = max(1, min(_to_int(user.get("sovits_epochs"), s_ep), DEEP_MAX_SOVITS))
    if not auto["gpt_epochs"]:
        g_ep = max(1, min(_to_int(user.get("gpt_epochs"), g_ep), GPT_MAX_EPOCHS))
    if not auto["sovits_save_every"]:
        s_save = max(1, _to_int(user.get("sovits_save_every"), s_save))
    if not auto["gpt_save_every"]:
        g_save = max(1, _to_int(user.get("gpt_save_every"), g_save))

    def fit(epochs: int, save: int, max_epochs: int, name: str) -> Tuple[int, int]:
        new_ep, new_save = _fit_explicit_save(epochs, save, max_epochs)
        if new_ep != epochs:
            notes.append(f"为了让最后一轮的模型能保存下来，{name}轮数从 {epochs} 调整为 {new_ep}")
        return new_ep, new_save

    s_ep, s_save = fit(s_ep, s_save, DEEP_MAX_SOVITS, "音色（SoVITS）")
    g_ep, g_save = fit(g_ep, g_save, GPT_MAX_EPOCHS, "语气（GPT）")

    def mine(key: str) -> str:
        return "" if auto[key] else "（你指定的）"

    def every(n: int) -> str:
        return "每轮" if n == 1 else f"每 {n} 轮"

    total, free, g_total, by_free = v["total"], v["free"], v["g_total"], v["by_free"]
    measured = auto["batch_size"] and bool(p_s or p_g)
    probing = bool(v.get("will_probe")) and auto["batch_size"] and g_total > 0 and not measured
    parts: List[str] = []
    if g_total > 0:
        gpu = f"显存 {_nominal_gb(total)} GB" + (f"（现在空闲 {free:.1f} GB）" if by_free else "")
        if probing:
            parts.append(f"{gpu} → 先实测一次能练几条（按显存估计每批 {bs} 条）")
        elif measured:
            parts.append(f"{gpu} → 每批 {bs} 条" + (f"（语气 {gpt_bs} 条）" if gpt_bs != bs else "")
                         + ("（和上次一样）" if v.get("batch_source") == "previous" else "（实测）"))
        else:
            parts.append(f"{gpu} → 每批 {bs} 条{mine('batch_size')}")
    else:
        parts.append(f"没有检测到能用的 N 卡 → 每批 {bs} 条{mine('batch_size')}（仍然按「一模一样」训练，但用处理器会非常慢）")
    line = (f"音色 SoVITS {s_ep} 轮{mine('sovits_epochs')}、{every(s_save)}存一个；"
            f"语气 GPT {g_ep} 轮{mine('gpt_epochs')}、{every(g_save)}存一个")
    if probing and (auto["sovits_epochs"] or auto["gpt_epochs"]):
        line += "（实测的每批条数不一样时，轮数按比例调整，模型更新的次数不变）"
    parts.append(line)
    if v.get("mixed_text"):
        en = v.get("en_lines")
        parts.append("中文和英文都参加训练" + (f"（素材里有 {en} 句夹着英文）" if en else ""))
    n_val = v.get("n_val")
    if n_val:
        parts.append(f"训练完用你没参加训练的 {n_val} 句录音把每个存下的版本都试一遍，挑最像你的")
    else:
        parts.append("训练完把每个存下的版本都试一遍，挑最像你的")
    dpo = v["dpo"]
    if dpo:
        who = "" if auto["if_dpo"] else "你指定的；"
        parts.append(f"开启 DPO（{who}官方实验功能，用来减少重复、漏字；语气训练每批 {gpt_bs} 条，会慢 2～4 倍）")
    else:
        parts.append(f"不开 DPO（{v['why_not']}）")
    if max(bs, gpt_bs) > DEEP_BASE_BATCH and (auto["sovits_epochs"] or auto["gpt_epochs"]):
        notes.append("每批多练几条时轮数会跟着加多，每句话总共会被多练几遍；练得太多可能变差，所以每个存下的版本都会拿来比较")
    summary = "训练计划：「一模一样」训练——" + "；".join(parts) + "。"
    return {
        "mode": "identical",
        "batch_size": bs, "gpt_batch_size": gpt_bs,
        "sovits_epochs": s_ep, "gpt_epochs": g_ep,
        "sovits_save_every": s_save, "gpt_save_every": g_save,
        "if_dpo": bool(dpo),
        "gpu_mem_gb": round(total, 1) if total else 0.0,
        "gpu_free_gb": round(free, 1) if free is not None else None,
        "vram_gb": round(v["g"], 1), "tier": _tier(g_total),
        "minutes": v["minutes"], "n_clips": v["n_clips"], "noisy": bool(v["noisy"]), "suspects": int(v["suspects"]),
        "auto": auto, "notes": notes, "summary": summary,
        "probe_batch": {"sovits": p_s, "gpt": p_g} if (p_s or p_g) else None,
    }


# ================================================================ 训练日志 → 进度
def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


_SOVITS_STEP = re.compile(r"Train Epoch:\s*(\d+)\s*\[(\d+(?:\.\d+)?)%\]")
_SOVITS_DONE = re.compile(r"====> Epoch:\s*(\d+)")
_GPT_STEP = re.compile(r"Epoch\s+(\d+):\s*(\d+)%")
# 只认「接着上次练」那一行里的 checkpoint 文件名（v2 底模的文件名里也有 epoch=12，不能当成进度）
_GPT_CKPT = re.compile(r"(?:ckpt_path:|checkpoint path at).*?epoch=(\d+)-step=")
#: Lightning 进度条里这一轮第几步：「Epoch 3:  45%|████▌     | 20/44 [...]」
_GPT_BAR = re.compile(r"Epoch\s+(\d+):\s*\d+%\|[^|]*\|\s*(\d+)/(\d+)")
_S2_START = re.compile(r"start training from epoch\s+(\d+)")


# 训练程序开始时打印的「实际用了几条」（module/data_utils.py、AR/data/dataset.py @ 48b1a01 / 20250606v2pro）
_S2_PHONE_LEN = re.compile(r"phoneme_data_len:\s*(\d+)")
_S2_WAV_LEN = re.compile(r"wav_data_len:\s*(\d+)")
_S2_SKIPPED = re.compile(r"skipped_phone:\s*(\d+)\s*,\s*skipped_dur:\s*(\d+)")
_S2_LEFT = re.compile(r"total left:\s*(\d+)")
_S2_NOT_IN = re.compile(r"(\S+) not in self\.phoneme_data !")
_S2_ZERO = re.compile(r"Zero duration for (\S+), skipping")
_S2_SSL = re.compile(r"load audio or ssl error!*\s*(\S+)")
_S1_SEM_LEN = re.compile(r"semantic_data_len:\s*(\d+)")
_S1_DELETED = re.compile(r"deleted (\d+) audios who's (duration|phoneme/sec)")
_S1_NOT_IN = re.compile(r"there are (\d+) semantic datas not in phoneme datas")
_S1_LEN = re.compile(r"dataset\.__len__\(\):\s*(\d+)")


def _wav_stem(path: str) -> str:
    name = str(path).replace("\\", "/").rsplit("/", 1)[-1]
    return name[:-4] if name.lower().endswith(".wav") else name


def _capture_s2(line: str, counts: Dict[str, Any]) -> None:
    """s2 训练日志里「实际用了几条」的几行记进 counts（同一次训练重新开始时会再打印一遍，后面的覆盖前面的）；
    「start training from epoch N」→ resumed_from = N − 1（这次是接着第几轮往下练的）。"""
    m = _S2_START.search(line)
    if m:
        counts["resumed_from"] = max(0, int(m.group(1)) - 1)
        return
    for key, rx in (("phone_len", _S2_PHONE_LEN), ("wav_len", _S2_WAV_LEN), ("total_left", _S2_LEFT)):
        m = rx.search(line)
        if m:
            counts[key] = int(m.group(1))
            if key == "phone_len":  # 新的一次开始：前面记的名字清掉
                counts["missing"], counts["zero"], counts["ssl"] = [], [], []
            return
    m = _S2_SKIPPED.search(line)
    if m:
        counts["skipped_phone"], counts["skipped_dur"] = int(m.group(1)), int(m.group(2))
        return
    for key, rx in (("missing", _S2_NOT_IN), ("zero", _S2_ZERO), ("ssl", _S2_SSL)):
        m = rx.search(line)
        if m:
            names = counts.setdefault(key, [])
            stem = _wav_stem(m.group(1))
            if stem not in names:
                names.append(stem)
            return


def _capture_s1(line: str, counts: Dict[str, Any]) -> None:
    """s1 训练日志：读到几条、删掉几条、最后用几条；「ckpt_path: …epoch=9-step=…」→ resumed_from = 10。"""
    m = _GPT_CKPT.search(line)
    if m:
        counts["resumed_from"] = int(m.group(1)) + 1
        return
    m = _S1_SEM_LEN.search(line)
    if m:
        keep = counts.get("resumed_from")
        counts.clear()
        if keep is not None:
            counts["resumed_from"] = keep
        counts["semantic_len"] = int(m.group(1))
        return
    m = _S1_DELETED.search(line)
    if m:
        key = "deleted_long" if m.group(2) == "duration" else "deleted_ps"
        counts[key] = int(m.group(1))
        return
    m = _S1_NOT_IN.search(line)
    if m:
        counts["not_in"] = int(m.group(1))
        return
    m = _S1_LEN.search(line)
    if m:
        counts["dataset_len"] = int(m.group(1))


def _sovits_parser(total: int, counts: Optional[Dict[str, Any]] = None) -> Callable[[str], Optional[Tuple[float, str]]]:
    """s2_train.py：「Train Epoch: 3 [45%]」（第 3 轮进行中，从 1 开始数）和「====> Epoch: 3」（第 3 轮完成）。

    开头的「start training from epoch 1」不算进度（否则一开始就跳到 1/8）。
    counts（可选）：顺便记下训练程序打印的「实际用了几条」（total left、skipped_dur、读不了的录音……）。"""
    total = max(1, int(total))

    def parse(line: str) -> Optional[Tuple[float, str]]:
        if counts is not None:
            _capture_s2(line, counts)
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


def _gpt_parser(total: int, counts: Optional[Dict[str, Any]] = None) -> Callable[[str], Optional[Tuple[float, str]]]:
    """s1_train.py（Lightning 进度条）：「Epoch 0:  45%|…」（从 0 开始数）；
    接着上次训练时打印「ckpt_path: …/ckpt/epoch=9-step=…」（第 10 轮已经练完）。
    counts（可选）：顺便记下「deleted K audios …」「dataset.__len__(): N」。"""
    total = max(1, int(total))

    def parse(line: str) -> Optional[Tuple[float, str]]:
        if counts is not None:
            _capture_s1(line, counts)
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


def _link_or_copy(src: Path, dst: Path) -> None:
    """硬链接（不占硬盘），不行（例如不同的盘、FAT32）就复制。"""
    try:
        os.link(str(src), str(dst))
    except OSError:
        shutil.copy2(str(src), str(dst))


def _gpu_sampler(index: Any) -> Any:
    """每 5 秒用 nvidia-smi 量一次显卡（没有 nvidia-smi 时什么都不做）。"""
    from voicetwin.utils.gpu import GpuSampler

    return GpuSampler(5.0, index).start()


def _disk_save_every(size: int, total: int, done_epoch: int, save: int, free: int) -> Optional[int]:
    """硬盘够不够存剩下的模型文件（每个 size 字节，第 done_epoch 轮以后每 save 轮存一个，最后留 DISK_RESERVE_GB）：
    够 → None；不够 → 加大的保存间隔（至少加倍、而且最后一轮一定能存下来；实在不够就只存最后一轮）。"""
    total, save = max(1, int(total)), max(1, int(save))
    room = float(free) - DISK_RESERVE_GB * 1024 ** 3

    def need(k: int) -> float:
        return float(size) * sum(1 for e in range(int(done_epoch) + 1, total + 1) if e % k == 0)

    if need(save) <= room:
        return None
    k = save
    while k < total:
        k = next((d for d in range(2 * k, total + 1) if total % d == 0), total)
        if need(k) <= room:
            return k
    return k if k != save else None


class _DiskWatch:
    """训练时盯着硬盘：这一步第一个模型文件存好（两次量的大小一样）以后，量它多大，算剩下的还存得下存不下；
    存不下就定一个更大的保存间隔（new_save），poll() 返回 True 让这一步停下，调用的地方按新的间隔接着练
    （GPT-SoVITS 会从刚存的进度接着练，已经练好的不会白练）。只查一次。"""

    def __init__(self, backend: "GPTSoVITSBackend", kind: str, total: int, save: int) -> None:
        self.b, self.kind, self.total, self.save = backend, kind, int(total), int(save)
        self.t0 = time.time()
        self.seen: Dict[str, int] = {}
        self.done = False
        self.new_save: Optional[int] = None
        self.size_mb: Optional[float] = None

    def _dir_and_pattern(self) -> Tuple[Path, str]:
        if self.kind == "sovits":
            return self.b.p(f"SoVITS_weights_{self.b.version}"), f"{self.b.exp_name}_e*_s*.pth"
        return self.b.p(f"GPT_weights_{self.b.version}"), f"{self.b.exp_name}-e*.ckpt"

    def poll(self) -> Optional[bool]:
        if self.done:
            return None
        d, pattern = self._dir_and_pattern()
        files: List[Tuple[Path, int]] = []
        if d.is_dir():
            for f in d.glob(pattern):
                try:
                    stt = f.stat()
                except OSError:
                    continue
                if stt.st_mtime >= self.t0 - 2.0:
                    files.append((f, stt.st_size))
        if not files:
            return None
        f, size = max(files, key=lambda x: (_epoch(x[0]), str(x[0])))
        if size <= 0 or self.seen.get(str(f)) != size:  # 可能还在写：下次再量
            self.seen[str(f)] = size
            return None
        self.done = True
        try:
            free = shutil.disk_usage(str(d)).free
        except OSError:
            return None
        new = _disk_save_every(size, self.total, _epoch(f), self.save, free)
        if new is None:
            return None
        self.new_save = new
        self.size_mb = round(size / 1048576.0, 1)
        log.warning(f"硬盘空间不够存这么多版本：每个模型实测 {self.size_mb:g} MB，已改成每 {new} 轮存一个。")
        return True


def _repeat_factor(listed: Optional[int], expected: int) -> int:
    """训练程序在素材少于 100 条时把整份重复 max(2, int(100 / 条数)) 遍：从它打印的条数反推重复了几遍（推不出来就是 1）。"""
    if not listed or listed <= expected:
        return 1
    for u in range(min(int(expected), 99), 0, -1):  # 从多到少试：同一个总数可能有几种拆法，条数最接近素材条数的最可能
        r = max(2, int(100 / u))
        if u * r == listed:
            return r
    return 1


def _trained_counts(s2: Dict[str, Any], s1: Dict[str, Any], expected: int) -> Dict[str, Any]:
    """从训练日志（_capture_s2 / _capture_s1 记下的）算出实际参加训练的条数：
    {"sovits": 音色用了几条, "gpt": 语气用了几条, "expected": 训练素材条数, "reasons": {原因: 条数}, "ids": [没参加的片段]}。
    日志里没有这些行（版本不一样）时对应的是 None（没测出来，不猜）。"""
    out: Dict[str, Any] = {"sovits": None, "gpt": None, "expected": int(expected), "reasons": {}, "ids": []}
    reasons: Dict[str, int] = {}
    left = s2.get("total_left")
    if left is not None:
        r = _repeat_factor(s2.get("wav_len"), expected)
        out["sovits"] = int(round(left / float(r)))
        if s2.get("phone_len") is not None and s2.get("wav_len") is not None:
            missing = int(s2["phone_len"]) - int(round(s2["wav_len"] / float(r)))
            if missing > 0:
                reasons["声音特征没提取出来"] = missing
        if s2.get("skipped_phone"):
            reasons["文字处理的结果里没有这条"] = int(round(s2["skipped_phone"] / float(r)))
        if s2.get("skipped_dur"):
            reasons["声音太短（不到 0.6 秒）或太长（54 秒以上）"] = int(round(s2["skipped_dur"] / float(r)))
    if s2.get("ssl"):
        reasons["训练时读不了这条录音或它的特征"] = len(s2["ssl"])
    sem = s1.get("semantic_len")
    if sem is not None:
        gone = int(s1.get("not_in") or 0) + int(s1.get("deleted_long") or 0) + int(s1.get("deleted_ps") or 0)
        out["gpt"] = max(0, int(sem) - gone)
        if s1.get("deleted_ps"):
            reasons["每秒的音素数不在 3～25 之间（多半是文字和声音对不上）"] = int(s1["deleted_ps"])
        if s1.get("deleted_long"):
            reasons["太长（超过 54 秒）"] = int(s1["deleted_long"])
        if s1.get("not_in"):
            reasons.setdefault("文字处理的结果里没有这条", int(s1["not_in"]))
    out["reasons"] = reasons
    out["ids"] = list(dict.fromkeys(list(s2.get("missing") or []) + list(s2.get("zero") or []) + list(s2.get("ssl") or [])))
    return out


def _report_lines(params: Dict[str, Any]) -> List[str]:
    """训练完给老师看的几句话，每个数字都是这次实测（数出来 / nvidia-smi 量出来 / 计时）的；没测出来的写「没测出来」或不写。"""
    lines: List[str] = []
    tc = params.get("trained_counts") or {}
    n = tc.get("expected")

    def num(v: Any) -> str:
        return "（没测出来）" if v is None else f"{v}"

    if n:
        lines.append(f"实际参加训练：音色 {num(tc.get('sovits'))} 条、语气 {num(tc.get('gpt'))} 条（一共 {n} 条）。")
        got = [v for v in (tc.get("sovits"), tc.get("gpt")) if v is not None]
        if got and min(got) < MIN_TRAINED_SHARE * n:
            k = n - min(got)
            why = "、".join(f"{r} {c} 条" for r, c in (tc.get("reasons") or {}).items()) or "训练程序没有说明"
            ids = tc.get("ids") or []
            tail = (f"可以在校对表里看看这几条：{'、'.join(ids[:20])}" + ("……" if len(ids) > 20 else "")
                    if ids else "训练程序没有记下是哪几条")
            lines.append(f"有 {k} 条没参加训练（原因：{why}），一般是文字和声音对不上或者太短；不影响使用，{tail}。")
    if params.get("text_frontend") == "mixed" and params.get("en_lines"):
        lines.append(f"英文：{params['en_lines']} 句里的英文这次也参加了训练（一共 {params.get('en_phones') or 0} 个英文音素）。")
    gpu = params.get("gpu") or {}
    parts = []
    low = False
    for kind, name, bkey in (("sovits", "音色", "batch_size"), ("gpt", "语气", "gpt_batch_size")):
        g = gpu.get(kind) or {}
        if g.get("util_avg") is None and g.get("peak_gb") is None:
            continue
        b = params.get(f"{bkey}_used") or params.get(bkey)
        bits = [f"每批 {b} 条"]
        if g.get("peak_gb") is not None:
            bits.append(f"显存最高 {g['peak_gb']:.1f} GB")
        if g.get("util_avg") is not None:
            bits.append(f"平均使用率 {g['util_avg']:.0f}%")
            low = low or float(g["util_avg"]) < LOW_GPU_UTIL
        parts.append(f"{name}训练" + "，".join(bits))
    if parts:
        lines.append("显卡（实测）：" + "；".join(parts) + "。" + ("这一步主要卡在处理器或读文件上，显卡没法再更忙。" if low else ""))
    t = params.get("timing") or {}
    bits = []
    if t.get("features_s") is not None:
        bits.append(f"处理文字和提取特征 {t['features_s'] / 60.0:.1f} 分钟")
    if t.get("probe_s"):
        bits.append(f"实测显卡 {t['probe_s'] / 60.0:.1f} 分钟")
    if t.get("sovits_s_per_epoch") is not None:
        bits.append(f"音色每轮 {t['sovits_s_per_epoch']:.0f} 秒")
    if t.get("gpt_s_per_epoch") is not None:
        bits.append(f"语气每轮 {t['gpt_s_per_epoch']:.0f} 秒")
    if bits:
        lines.append("用时（实测）：" + "、".join(bits) + "。")
    return lines


class GPTSoVITSBackend(Backend):
    name = "gptsovits"
    display_name = "GPT-SoVITS"
    supports_training = True
    supports_speed = True
    supports_aux_refs = True
    supports_batch = True
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
        #: use_checkpoint 指定的模型（自动挑选时一个一个试）；引擎中途重启或重新确认时也用它，不要换回默认的模型
        self._wanted: Optional[Dict[str, Any]] = None
        self._http = None
        self._log_fh = None
        self._warned_pretrained = False
        #: 「语速 1.0001」自检的结果（None = 这次启动引擎以后还没查过；每次启动新的引擎都重新查）
        self._speed_trick: Optional[bool] = None
        #: 显存不够时实测出来的、最多同时生成几个（None = 还没遇到过显存不够）
        self._max_batch: Optional[int] = None
        #: 同时生成好几个版本的实测记录（请求数、拿到几个版本、每种数量用了几秒、显存不够减半几次、切不开几次……）
        self.batch_stats: Dict[str, Any] = _new_batch_stats()
        #: 最近一次 synthesize_many 实际怎么生成的：{"mode": "batch", "batch", "seed", "speed"} 或
        #: {"mode": "single", "seeds", "speed"}（以后按同一个请求只改语速再生成一次时要用）
        self.last_many: Dict[str, Any] = {}

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

    # ---------------------------------------------------------------- 训练方式和相关设置
    def _tcfg(self) -> Dict[str, Any]:
        return dict(self.bcfg.get("train", {}) or {})

    def _train_mode(self, value: Any = None) -> str:
        """这次用哪种训练方式：本次指定的（网页 / 命令行）优先，没指定看 config.yaml 的 train.mode（auto = identical）。"""
        return resolve_train_mode(value if value not in (None, "") else self._tcfg().get("mode"))

    def _text_frontend(self) -> str:
        """处理文字的方法：mixed（VoiceTwin 自己的，中英文一起；默认）/ official（官方 1-get-text.py）。"""
        v = str(self._tcfg().get("text_frontend", "auto") or "auto").strip().lower()
        return "official" if v in ("official", "官方", "false", "off", "no") else "mixed"

    def _feature_parts(self, tier: str) -> int:
        """提取特征分几路同时做：auto = 8 GB 档以上 2 路，否则 1 路；也可以在 config.yaml 里写 1~4。"""
        v = self._tcfg().get("feature_parts", "auto")
        if _is_auto(v):
            return 2 if tier in ("mid", "high") else 1
        return max(1, min(4, _to_int(v, 1)))

    def _probe_enabled(self) -> bool:
        v = self._tcfg().get("batch_probe", "auto")
        return _is_auto(v) or _dpo_choice(v) is not False

    def _deep_cfg(self) -> Dict[str, Any]:
        t = self._tcfg()
        return {"sovits_epochs": t.get("deep_sovits_epochs"), "gpt_epochs": t.get("deep_gpt_epochs"),
                "sovits_save": t.get("deep_sovits_save"), "gpt_save": t.get("deep_gpt_save")}

    def _plan_context(self) -> Dict[str, Any]:
        """说明里要用的实测数字：挑选用几句没参加训练的录音、几句夹着英文。读不了就不说。"""
        out: Dict[str, Any] = {"n_val": None, "en_lines": None}
        try:
            from voicetwin.data.audit import material_audit
            from voicetwin.data.exporters import validation_items
            from voicetwin.synth.select import DEFAULT_ITEMS

            out["n_val"] = len(validation_items(self.project, limit=DEFAULT_ITEMS)) or None
            out["en_lines"] = material_audit(self.project).get("en_lines")
        except Exception as exc:
            log.debug(f"读训练说明要用的数字没成功：{exc}")
        return out

    def _make_plan(self, n_clips: int, minutes: float, opts: Dict[str, Any], quick: bool = False,
                   gpu: Optional[Tuple[float, Optional[float], str]] = None, mode: str = "standard",
                   **plan_kw: Any) -> Dict[str, Any]:
        total, free, source = gpu if gpu is not None else self._gpu_memory(quick)
        if total <= 0 and not quick and gpu is None:
            log.warning("没有检测到可用的 NVIDIA 显卡，训练会非常慢（CPU 训练可能需要数天）")
        noisy, share, suspects = self._material_quality()
        if mode == "identical":
            plan_kw.setdefault("deep", self._deep_cfg())
            plan_kw.setdefault("mixed_text", self._text_frontend() == "mixed")
            for k, v in self._plan_context().items():
                plan_kw.setdefault(k, v)
        plan = plan_training(n_clips, minutes, total, free, is_half=self.is_half, noisy=noisy, suspects=suspects,
                             user=self._user_settings(opts), mode=mode, **plan_kw)
        plan["gpu_source"] = source
        plan["noisy_share"] = round(share, 2)
        return plan

    def training_plan(self, quick: bool = False, **opts: Any) -> Dict[str, Any]:
        """训练前预览这次的自动训练设置（不训练、不导出文件）。

        quick=True：只用 nvidia-smi 读显卡（网页上每次换声音都会预览，不能等十几秒）。
        返回的 summary 是训练计划；state_note 说这次会从头练 / 接着练 / 不重新练（按现在的素材算出来的）；
        audit_lines 是素材检查里实际有的情况（data/audit.py）。opts 里的 mode 是训练方式。"""
        from voicetwin.data.exporters import gptsovits_list_text, train_records

        mode = self._train_mode(opts.pop("mode", None))
        opts.pop("train_v4", None)
        recs = train_records(self.project)
        minutes = round(sum(float(r.get("duration") or 0.0) for r in recs) / 60.0, 1)
        gpu = self._gpu_memory(quick)
        state: Dict[str, Any] = {}
        try:  # 和训练时一样算素材的指纹（不写文件）：判断这次会怎么练
            if recs and self.root is not None:
                text = gptsovits_list_text(self.project, self.exp_name, recs).replace("\n", os.linesep)
                feat = self._feature_digest_bytes(text.encode("utf-8"), self.project.clips_dir)
                state = self._run_state(feat, mode, opts, len(recs), minutes, gpu)
        except Exception as exc:
            log.debug(f"预览训练状态没成功：{exc}")
        if state.get("plan"):
            plan = state["plan"]
        else:
            will = mode == "identical" and self._probe_enabled() and gpu[0] > 0
            plan = self._make_plan(len(recs), minutes, opts, quick=quick, gpu=gpu, mode=mode, will_probe=will)
        plan["state"] = state.get("state", "")
        plan["state_note"] = state.get("note", "")
        try:
            from voicetwin.data.audit import material_audit

            plan["audit_lines"] = list(material_audit(self.project).get("lines") or [])
        except Exception:
            plan["audit_lines"] = []
        return plan

    # ---------------------------------------------------------------- 素材有没有变（决定从头练 / 接着练 / 不重新练）
    def _feature_digest(self, list_path: Path, wav_dir: Path) -> Dict[str, str]:
        return self._feature_digest_bytes(Path(list_path).read_bytes(), wav_dir)

    def _feature_digest_bytes(self, data: bytes, wav_dir: Path) -> Dict[str, str]:
        """训练素材的指纹：训练列表 + 版本 + 处理文字的方法 + 录音文件（名字、大小、修改时间）。

        digest 变了就要重新提取特征、从头训练；list_sha1（只有训练列表 + 版本，和以前的算法一样）用来提醒
        「校对表在上次训练以后改过」。"""
        names = [line.split("|", 1)[0] for line in data.decode("utf-8", errors="replace").splitlines() if line.strip()]
        frontend = self._text_frontend()
        clip_sig = _clip_signature(names, wav_dir)
        digest = hashlib.sha1(data + self.version.encode() + b"|text=" + frontend.encode()
                              + b"|clips=" + clip_sig.encode()).hexdigest()
        return {"digest": digest, "list_sha1": hashlib.sha1(data + self.version.encode()).hexdigest(),
                "frontend": frontend, "clip_sig": clip_sig, "names_sig": short_hash(*sorted(names), n=16),
                "version": self.version}

    def _material_changes(self, feat: Dict[str, str], opt_dir: Path) -> Tuple[bool, List[str], List[str]]:
        """和上次提取特征时比：(变了没有, 变了哪些 [list / frontend / clips / names / version / legacy / first], 中文原因)。"""
        stamp = opt_dir / "voicetwin_list.sha1"
        old = stamp.read_text().strip() if stamp.exists() else None
        if old is None:
            return True, ["first"], []
        if old == feat["digest"]:
            return False, [], []
        kinds: List[str] = []
        try:
            info = json.loads((opt_dir / FEATURES_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            info = None
        if isinstance(info, dict):
            for key, kind in (("list_sha1", "list"), ("frontend", "frontend"), ("clip_sig", "clips"),
                              ("names_sig", "names"), ("version", "version")):
                if info.get(key) != feat[key]:
                    kinds.append(kind)
            if "names" in kinds and "clips" in kinds:  # 句子增减了，录音的指纹当然也变了：原因是素材改过
                kinds.remove("clips")
            old_list = str(info.get("list_sha1") or "")
        else:  # 以前的版本训练的：指纹只有训练列表 + 版本，处理文字用的是官方的方法
            kinds.append("legacy")
            old_list = old
            if old != feat["list_sha1"]:
                kinds.append("list")
            if feat["frontend"] == "mixed":
                kinds.append("frontend")
        reasons: List[str] = []
        if "frontend" in kinds:
            reasons.append("中英文一起训练的新方法" if feat["frontend"] == "mixed" else "处理文字改用官方的方法")
        if "list" in kinds or "names" in kinds:
            reasons.append("句末没有标点的句子改成补「，」" if old_list and old_list == self._legacy_list_sha1() else "素材改过")
        if "clips" in kinds:
            reasons.append("录音文件改过")
        if "version" in kinds:
            reasons.append("模型版本换了")
        if not reasons:
            reasons.append("素材改过")
        return True, kinds or ["unknown"], list(dict.fromkeys(reasons))

    def _legacy_list_sha1(self) -> str:
        """按以前的规则（末尾补「。」）导出的训练列表的指纹：认出「素材其实没改，只是导出规则改进了」。"""
        try:
            from voicetwin.data.exporters import gptsovits_list_text, train_records

            data = gptsovits_list_text(self.project, self.exp_name, train_records(self.project), legacy_punct=True)
            return hashlib.sha1(data.replace("\n", os.linesep).encode("utf-8") + self.version.encode()).hexdigest()
        except Exception:
            return ""

    def _frontend_used(self, opt_dir: Path) -> str:
        try:
            return (opt_dir / FRONTEND_FILE).read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def _previous_run(self, feat: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """上次做完的训练用的就是这份素材、模型文件也都在：返回 models.json 里的记录，否则 None。"""
        entry = self.project.load_models().get(self.name) or {}
        params = entry.get("params")
        if entry.get("features_sha1") != feat["digest"] or not isinstance(params, dict):
            return None
        files = [self._locate_weight(str(x)) for x in list(entry.get("sovits") or []) + list(entry.get("gpt") or [])]
        if not entry.get("sovits") or not entry.get("gpt") or not all(files):
            return None
        return entry

    def _run_state(self, feat: Dict[str, str], mode: str, opts: Dict[str, Any], n_clips: int, minutes: float,
                   gpu: Tuple[float, Optional[float], str]) -> Dict[str, Any]:
        """这次怎么练：{"state": fresh / extend / skip / continue, "note": 给老师看的一句话, "reasons": [...],
        "kinds": [...], "plan": 训练计划（接着练 / 不重新练时按上次的每批条数算）, "previous": 上次的记录}。"""
        opt_dir = self._opt_dir()
        changed, kinds, reasons = self._material_changes(feat, opt_dir)
        prev = None if changed else self._previous_run(feat)
        out: Dict[str, Any] = {"kinds": kinds, "reasons": reasons, "previous": prev}
        if prev is not None:
            pp = prev["params"]
            prev_b = {"sovits": pp.get("batch_size_used") or pp.get("batch_size"),
                      "gpt": pp.get("gpt_batch_size_used") or pp.get("gpt_batch_size")}
            kw: Dict[str, Any] = {"probe_batch": prev_b, "batch_source": "previous"} if mode == "identical" else {}
            plan = self._make_plan(n_clips, minutes, opts, gpu=gpu, mode=mode, **kw)
            more = (int(plan["sovits_epochs"]) > _to_int(pp.get("sovits_epochs"), 0)
                    or int(plan["gpt_epochs"]) > _to_int(pp.get("gpt_epochs"), 0))
            out["plan"] = plan
            if more:
                out["state"] = "extend"
                out["note"] = "素材没变：接着上次的训练往下练（上次存下的版本也一起参加比较）。"
            else:
                out["state"] = "skip"
                out["note"] = ("素材没变，已经按「一模一样」练过了：这次不重新训练，直接重新挑选。"
                               if pp.get("mode") == "identical" else
                               "素材没变，上次已经练够了这么多轮：这次不重新训练，直接重新挑选。")
        elif changed:
            out["state"] = "fresh"
            entry = self.project.load_models().get(self.name) or {}
            if "first" in kinds or not entry.get("selected"):
                out["note"] = f"这次会从头训练（原因：{'、'.join(reasons)}）。" if "first" not in kinds else ""
            else:
                out["note"] = (f"这次会从头训练（原因：{'、'.join(reasons)}）。你原来的模型会备份起来，一起参加比较；"
                               "新模型实测不比它好，就继续用它。")
        else:
            out["state"] = "continue"
            out["note"] = "素材没变：接着上次没做完的训练往下练。"
        return out

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
        try:  # 原来用的模型记下来：下次挑选时也参加比较（新模型实测不比它好，就继续用它）
            self._record_previous_selected()
        except Exception as exc:
            log.warning(f"记下原来用的模型没成功（这次挑选时它不参加比较）：{exc}")
        if not moved:
            try:
                dest.rmdir()
            except OSError:
                pass
        old_root = opt_dir / "old_runs"
        try:  # 只留最近几次备份（每次大约 1 GB），免得占满硬盘；正在用的模型所在的那次不删，
            # 下次挑选时要一起比较的原来的模型（previous_selected，挑选做完以前）也不删
            entry = self.project.load_models().get(self.name) or {}
            sel = entry.get("selected") or {}
            in_use = [str(sel.get(k) or "") for k in ("sovits", "gpt") if sel.get(k)]
            prev = entry.get("previous_selected") or {}
            if isinstance(prev, dict) and prev.get("pending"):
                in_use += [str(prev.get(k) or "") for k in ("sovits", "gpt") if prev.get(k)]
            runs = sorted((p for p in old_root.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)
            for p in runs[:-KEEP_OLD_RUNS]:
                if any(u.startswith(str(p)) for u in in_use):
                    continue
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass
        return dest if moved else None

    def _record_previous_selected(self) -> None:
        """把现在用的模型（models.json 的 selected，已经改到备份后的位置）记成 previous_selected：
        新模型训练好以后它也参加挑选；挑选做完以前它所在的备份不会被删掉（pending）。
        上次的挑选没做完（没有 selection）而以前记下的原来的模型还在时，留着以前那个（它才是实测挑出来的）。"""
        entry = self.project.load_models().get(self.name) or {}
        sel = entry.get("selected") or {}
        if not isinstance(sel, dict) or not sel.get("sovits") or not sel.get("gpt"):
            return
        old = entry.get("previous_selected") or {}
        if (isinstance(old, dict) and old.get("pending") and not entry.get("selection")
                and self._locate_weight(str(old.get("sovits") or "")) and self._locate_weight(str(old.get("gpt") or ""))):
            return
        info = entry.get("selection") or {}
        best = next((r for r in (info.get("results") or []) if isinstance(r, dict) and r.get("id") == info.get("best")), {})
        prev = {"id": str(sel.get("id") or ""), "sovits": str(sel["sovits"]), "gpt": str(sel["gpt"]), "pending": True,
                "pct": best.get("pct"), "cer": best.get("cer"), "evaluated_at": info.get("evaluated_at"),
                "mode": (entry.get("params") or {}).get("mode"), "recorded_at": time.strftime("%Y-%m-%d %H:%M")}
        self.project.update_models(self.name, {"previous_selected": prev})

    def _feature_base(self, list_path: Path, wav_dir: Path, opt_dir: Path) -> Dict[str, Any]:
        """官方特征提取脚本都要的环境变量（i_part / all_parts 由 _run_parts 填）。"""
        return {"inp_text": str(list_path), "inp_wav_dir": str(wav_dir), "exp_name": self.exp_name,
                "opt_dir": str(opt_dir), "i_part": "0", "all_parts": "1", "_CUDA_VISIBLE_DEVICES": self._gpu(),
                "is_half": str(self.is_half), "version": self.version}

    def _prepare_features(self, list_path: Path, wav_dir: Path, progress: Optional[ProgressFn],
                          n_clips: int = 0, *, feat: Optional[Dict[str, str]] = None, changed: Optional[bool] = None,
                          kinds: Optional[List[str]] = None, pos: Optional[Dict[str, float]] = None, parts: int = 1,
                          mixed_ready: Optional[Tuple[Path, Dict[str, int]]] = None) -> Dict[str, Any]:
        """1A 处理文字 → 1B 声音特征（+ v2Pro 声纹）→ 1C 语义，和官方 WebUI 一样的脚本和文件。

        素材的指纹（_feature_digest：训练列表 + 版本 + 处理文字的方法 + 录音文件）变了：删掉旧的特征文件、把旧的训练进度和
        模型挪进 old_runs（_archive_old_run），这次从头训练。只是文字或处理文字的方法变了（录音、句子都没变）时只重新处理文字，
        声音特征接着用。1B / 声纹 / 1C 分 parts 路同时做（_run_parts）。
        mixed_ready：上次退回了官方的方法、这次先在临时文件夹里试成功的「中英文一起」的结果，直接拿来用。
        返回 {"opt_dir", "frontend": 这次文字实际是哪种方法处理的, "en_phones", "en_lines"}。"""
        pos = pos or TRAIN_POS["standard"]
        opt_dir = self._opt_dir()
        opt_dir.mkdir(parents=True, exist_ok=True)
        feat = feat or self._feature_digest(list_path, wav_dir)
        if changed is None:
            changed, kinds, _ = self._material_changes(feat, opt_dir)
        kinds = list(kinds or [])
        stamp = opt_dir / "voicetwin_list.sha1"
        old = stamp.read_text().strip() if stamp.exists() else None
        if old:  # 旧版本训练的模型：models.json 里没记它用的素材，先把上次的指纹记过去（这次训练失败 / 停止时还能提醒）
            try:
                entry = self.project.load_models().get(self.name) or {}
                if entry.get("sovits") and not entry.get("list_sha1"):
                    try:
                        prev_list = json.loads((opt_dir / FEATURES_FILE).read_text(encoding="utf-8"))["list_sha1"]
                    except (OSError, ValueError, KeyError, TypeError):
                        prev_list = old  # 以前的版本：指纹本来就只有训练列表 + 版本
                    self.project.update_models(self.name, {"list_sha1": prev_list})
            except Exception as exc:  # noqa: BLE001
                log.debug(f"记下旧模型用的素材指纹没成功：{exc}")
        if changed and old is not None:
            text_only = (("legacy" not in kinds and set(kinds) <= {"frontend", "list"})
                         or set(kinds) == {"legacy", "frontend"})
            if text_only:
                log.info("处理文字的方法或训练文字变了：重新处理文字（声音特征没变，接着用）")
            else:
                log.info("训练素材有变化，清理旧的特征文件后重新提取")
            for name in (TEXT_FEATURES if text_only else ALL_FEATURES):
                target = opt_dir / name
                if target.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                elif target.exists():
                    target.unlink()
            for f in list(opt_dir.glob("2-name2text-*.txt")) + list(opt_dir.glob("6-name2semantic-*.tsv")):
                f.unlink(missing_ok=True)
            archived = self._archive_old_run(opt_dir)
            if archived is not None:
                log.info(f"检测到素材有变化：这次会从头训练新模型（旧的训练进度已备份到 {archived}）")
            else:
                log.info("检测到素材有变化：这次会从头训练新模型")
        if changed:
            (opt_dir / RUN_STAMP).write_text(f"{time.time():.3f}", encoding="utf-8")
            (opt_dir / PROBE_FILE).unlink(missing_ok=True)
        stamp.write_text(feat["digest"])
        (opt_dir / FEATURES_FILE).write_text(json.dumps(feat, ensure_ascii=False), encoding="utf-8")
        n = max(1, int(n_clips or 0) or len(list_path.read_text(encoding="utf-8").strip().splitlines()))
        base = self._feature_base(list_path, wav_dir, opt_dir)

        # 1A：文本 → 音素 + BERT 特征
        path_text = opt_dir / "2-name2text.txt"
        text_file = opt_dir / "voicetwin_text.json"
        frontend = self._frontend_used(opt_dir) or "official"
        en: Dict[str, int] = {}
        if not path_text.exists() or len(path_text.read_text(encoding="utf-8").strip().splitlines()) < 2:
            self._clear_text_outputs(opt_dir)
            if mixed_ready is not None:
                frontend, en = "mixed", self._adopt_mixed(mixed_ready[0], opt_dir, mixed_ready[1])
            else:
                frontend, en = self._run_text(opt_dir, base, n, progress, pos, parts)
            (opt_dir / FRONTEND_FILE).write_text(frontend, encoding="utf-8")
            text_file.write_text(json.dumps(en), encoding="utf-8")
        else:
            try:
                en = json.loads(text_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                en = {}

        # 1B：HuBERT 特征 + 32k 音频（+ v2Pro 声纹）。脚本不打印进度，数它写出的文件。
        two = "，两路同时做" if parts > 1 else ""
        self.step(progress, pos["hubert"], f"提取声音特征（比较慢，素材多时要十几分钟{two}）")
        env_1b = self.env({**base, "cnhubert_base_dir": str(self.p(HUBERT_DIR)), "sv_path": str(self.p(SV_PATH))})
        self._run_parts([self.python, "-s", "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"], env_1b, parts,
                        "gsv_1b_hubert", progress, (pos["hubert"], pos["sv"]), label="提取声音特征",
                        poll=_count_files(opt_dir / "4-cnhubert", "*.pt", n))
        if "Pro" in self.version:
            self.step(progress, pos["sv"], "提取声纹")
            self._run_parts([self.python, "-s", "GPT_SoVITS/prepare_datasets/2-get-sv.py"], env_1b, parts,
                            "gsv_1b_sv", progress, (pos["sv"], pos["semantic"]), label="提取声纹",
                            poll=_count_files(opt_dir / "7-sv_cn", "*.pt", n))

        # 1C：语义 token
        path_sem = opt_dir / "6-name2semantic.tsv"
        if not path_sem.exists() or path_sem.stat().st_size < 31:
            self.step(progress, pos["semantic"], "提取语义（大约 1~3 分钟）")
            for f in opt_dir.glob("6-name2semantic-*.tsv"):
                f.unlink(missing_ok=True)
            env_1c = self.env({**base, "pretrained_s2G": str(self.p(PRETRAINED_SOVITS[self.version])),
                               "s2config_path": self._s2_config_template()})
            self._run_parts([self.python, "-s", "GPT_SoVITS/prepare_datasets/3-get-semantic.py"], env_1c, parts,
                            "gsv_1c_semantic", progress, (pos["semantic"], pos["probe"]), label="提取语义")
            self._merge_parts(opt_dir, "6-name2semantic-{}.tsv", parts, "6-name2semantic.tsv",
                              header="item_name\tsemantic_audio")
        return {"opt_dir": opt_dir, "frontend": frontend, "en_phones": int(en.get("en_phones") or 0),
                "en_lines": int(en.get("en_lines") or 0)}

    # ---------------------------------------------------------------- 几路同时做、合并结果
    def _run_parts(self, cmd: List[Any], env: Dict[str, str], parts: int, log_name: str,
                   progress: Optional[ProgressFn], progress_range: Tuple[float, float], *, label: str,
                   parse: Optional[Callable[[str], Any]] = None,
                   poll: Optional[Callable[[], Optional[Tuple[int, int]]]] = None, retry: bool = True) -> None:
        """同一个官方脚本分 parts 路同时跑（和官方 WebUI 一样：每路 i_part = 0..parts-1、all_parts = parts，
        都用同一块显卡），等每一路都做完。进度只由第 1 路报（parse 会看到每一路的输出，poll 数的是所有路一起写的文件）。
        某一路出错：单独把这一路再做一次（retry=False 时直接报错），还不行就报错。点了停止照常停下。"""
        parts = max(1, int(parts))
        lock = threading.Lock()

        def wrapped(i: int) -> Optional[Callable[[str], Any]]:
            if parse is None:
                return None

            def f(line: str) -> Any:
                with lock:
                    res = parse(line)
                return res if i == 0 else None

            return f

        def run_one(i: int) -> None:
            self.run_logged(cmd, self.root, {**env, "i_part": str(i), "all_parts": str(parts)},
                            log_name if i == 0 else f"{log_name}_{i + 1}", progress if i == 0 else None,
                            progress_range, wrapped(i), label=label, poll_progress=poll if i == 0 else None,
                            poll_interval=self.POLL_SECONDS)

        if parts == 1:
            run_one(0)
            return
        errors: Dict[int, BaseException] = {}

        def target(i: int) -> None:
            try:
                run_one(i)
            except BaseException as exc:  # noqa: B036 - 在主线程里再处理（包括停止按钮）
                errors[i] = exc

        threads = [threading.Thread(target=target, args=(i,), name=f"vt-part-{i}", daemon=True) for i in range(parts)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        if any(isinstance(e, TaskCancelled) for e in errors.values()):
            raise TaskCancelled("已按你的要求停止")
        for i in sorted(errors):
            if not retry:
                raise errors[i]
            first = (str(errors[i]).splitlines() or [type(errors[i]).__name__])[0][:200]
            log.warning(f"「{label}」第 {i + 1} 路出错了（{first}），单独把这一路再做一次……")
            check_cancel()
            run_one(i)

    @staticmethod
    def _merge_parts(opt_dir: Path, pattern: str, parts: int, out_name: str, header: Optional[str] = None) -> List[str]:
        """把每一路写的结果（pattern.format(i)）按顺序合成 out_name，删掉每一路的文件；返回合并后的行（不含表头）。
        一行都没有、又没有表头时不写 out_name（下次会重新做）。"""
        lines: List[str] = []
        for i in range(max(1, int(parts))):
            part = opt_dir / pattern.format(i)
            if part.exists():
                lines += [ln for ln in part.read_text(encoding="utf-8").strip("\n").split("\n") if ln.strip()]
                part.unlink()
        if lines or header:
            (opt_dir / out_name).write_text("\n".join(([header] if header else []) + lines) + "\n", encoding="utf-8")
        return lines

    @staticmethod
    def _clear_text_outputs(opt_dir: Path) -> None:
        """处理文字之前：删掉上次（或者没做完的）处理文字的结果，免得官方脚本看到旧文件就跳过、或者 BERT 特征和音素对不上。"""
        for f in opt_dir.glob("2-name2text*.txt"):
            f.unlink(missing_ok=True)
        shutil.rmtree(opt_dir / "3-bert", ignore_errors=True)

    # ---------------------------------------------------------------- 处理文字：中英文一起（失败退回官方的方法）
    def _run_text(self, opt_dir: Path, base: Dict[str, Any], n: int, progress: Optional[ProgressFn],
                  pos: Dict[str, float], parts: int) -> Tuple[str, Dict[str, int]]:
        lo, hi = pos["text"], pos["hubert"]
        if self._text_frontend() == "mixed":
            self.step(progress, lo, "处理文字：中文和英文都参加训练（以前英文部分会被丢掉）")
            ok, why, en = self._run_mixed_text(opt_dir, base, n, progress, (lo, hi), parts)
            if ok:
                return "mixed", en
            self._clear_text_outputs(opt_dir)
            msg = f"中英文一起训练的新方法这次没成功（原因：{why}），已改用官方的方法（英文部分不参加训练），训练照常进行。"
            log.warning(msg)
            if progress:
                try:
                    progress(lo, msg)
                except Exception:
                    pass
        else:
            self.step(progress, lo, "处理文字（把讲稿转成拼音和特征）")
        env = self.env({**base, "bert_pretrained_dir": str(self.p(BERT_DIR))})
        self._run_parts([self.python, "-s", "GPT_SoVITS/prepare_datasets/1-get-text.py"], env, parts, "gsv_1a_text",
                        progress, (lo, hi), label="处理文字", parse=_line_counter(n, "处理文字"))
        lines = self._merge_parts(opt_dir, "2-name2text-{}.txt", parts, "2-name2text.txt")
        if not "".join(lines).strip():
            raise RuntimeError("1A 文本处理没有产出，请查看日志 logs/gsv_1a_text.log")
        return "official", {}

    def _run_mixed_text(self, out_dir: Path, base: Dict[str, Any], n: int, progress: Optional[ProgressFn],
                        prange: Tuple[float, float], parts: int) -> Tuple[bool, str, Dict[str, int]]:
        """用 VoiceTwin 自己的 1A（gsv_scripts/get_text_mixed.py）处理文字，结果写进 out_dir。
        返回 (成功没有, 没成功的中文原因, {"en_phones": 英文音素个数, "en_lines": 夹着英文的句子数})。
        整合包里缺模块、出错、退出码不是 0、写出来的不到 98% 的句子，都算没成功（调用的地方退回官方的方法）。"""
        if not MIXED_SCRIPT.exists():
            return False, "程序里缺少 get_text_mixed.py", {}
        env = self.env({**base, "opt_dir": str(out_dir), "bert_pretrained_dir": str(self.p(BERT_DIR)),
                        "VOICETWIN_MIXED_TEXT": str(MIXED_SCRIPT.parent.parent / "gsv_mixed_text.py")})
        vt = {"en_phones": 0, "en_lines": 0}
        counter = _line_counter(n, "处理文字")

        def parse(line: str) -> Any:
            m = re.match(r"VT_EN_(PHONES|LINES)\s+(\d+)", line.strip())
            if m:
                vt["en_phones" if m.group(1) == "PHONES" else "en_lines"] += int(m.group(2))
                return None
            return counter(line)

        for f in out_dir.glob("2-name2text-*.txt"):
            f.unlink(missing_ok=True)
        try:
            self._run_parts([self.python, "-s", str(MIXED_SCRIPT)], env, parts, "gsv_1a_text", progress, prange,
                            label="处理文字", parse=parse, retry=False)
        except TaskCancelled:
            raise
        except TrainStepError as exc:
            reason = next((ln.split("VT_FAIL", 1)[1].strip() for ln in reversed(exc.tail) if "VT_FAIL" in ln), "")
            return False, reason or (str(exc).splitlines() or ["出错了"])[0][:200], {}
        except Exception as exc:
            return False, f"{type(exc).__name__}: {str(exc)[:200]}", {}
        lines = self._merge_parts(out_dir, "2-name2text-{}.txt", parts, "2-name2text.txt")
        done = len(lines)
        if done < MIXED_MIN_SHARE * n:
            return False, f"只处理好 {done}/{n} 句（不到 98%）", {}
        return True, "", vt

    def _try_mixed(self, list_path: Path, wav_dir: Path, opt_dir: Path, n: int, progress: Optional[ProgressFn],
                   pos: Dict[str, float], parts: int) -> Optional[Tuple[Path, Dict[str, int]]]:
        """上次「中英文一起」的方法没成功、退回了官方的方法：这次先在临时文件夹里再试一次（不动现在的特征）。
        成功了返回 (临时文件夹, 英文的数字)，调用的地方当成素材变了（从头训练）；没成功就接着用现在的特征，说明原因。"""
        tmp = opt_dir / "_vt_mixed_try"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True, exist_ok=True)
        self.step(progress, pos["text"], "上次「中英文一起训练」的新方法没成功，这次先再试一次……")
        ok, why, en = self._run_mixed_text(tmp, self._feature_base(list_path, wav_dir, tmp), n, progress,
                                           (pos["text"], pos["hubert"]), parts)
        if ok:
            log.info("中英文一起训练的新方法这次成功了：重新训练（英文部分也参加训练）")
            return tmp, en
        shutil.rmtree(tmp, ignore_errors=True)
        log.warning(f"中英文一起训练的新方法这次还是没成功（原因：{why}），接着用现在的特征（英文部分不参加训练），训练照常进行。")
        return None

    @staticmethod
    def _adopt_mixed(tmp: Path, opt_dir: Path, en: Dict[str, int]) -> Dict[str, int]:
        """把临时文件夹里试成功的「中英文一起」的结果搬进正式的特征文件夹。"""
        shutil.move(str(tmp / "2-name2text.txt"), str(opt_dir / "2-name2text.txt"))
        if (tmp / "3-bert").is_dir():
            shutil.rmtree(opt_dir / "3-bert", ignore_errors=True)
            shutil.move(str(tmp / "3-bert"), str(opt_dir / "3-bert"))
        shutil.rmtree(tmp, ignore_errors=True)
        return dict(en)

    def _count_features(self, opt_dir: Path, n: int) -> Dict[str, Any]:
        """数一下特征文件和行数（和训练素材条数 n 比）：{"expected", "text", "semantic", "hubert", "wav32k", "sv", "bert"}。"""
        def rows(name: str, header: bool = False) -> Optional[int]:
            try:
                lines = [ln for ln in (opt_dir / name).read_text(encoding="utf-8").splitlines() if ln.strip()]
            except OSError:
                return None
            return max(0, len(lines) - (1 if header else 0))

        def files(sub: str, pattern: str) -> Optional[int]:
            d = opt_dir / sub
            return sum(1 for _ in d.glob(pattern)) if d.is_dir() else None

        return {"expected": int(n), "text": rows("2-name2text.txt"), "semantic": rows("6-name2semantic.tsv", True),
                "hubert": files("4-cnhubert", "*.pt"), "wav32k": files("5-wav32k", "*"),
                "sv": files("7-sv_cn", "*.pt") if "Pro" in self.version else None, "bert": files("3-bert", "*.pt")}

    def _s2_config_template(self) -> str:
        return "GPT_SoVITS/configs/s2.json" if "Pro" not in self.version else f"GPT_SoVITS/configs/s2{self.version}.json"

    # ---------------------------------------------------------------- 写训练设置
    def _write_s2_config(self, path: Path, bs: int, epochs: int, save_every: int, exp_dir: Path, *,
                         probe: bool = False) -> None:
        tcfg = self._tcfg()
        pre_g = str(self.p(PRETRAINED_SOVITS[self.version]))
        with open(self.p(self._s2_config_template()), "r", encoding="utf-8") as f:
            s2 = json.load(f)
        if not self.is_half:
            s2["train"]["fp16_run"] = False
        s2["train"].update({
            "batch_size": int(bs), "epochs": int(epochs),
            "text_low_lr_rate": float(tcfg.get("text_low_lr_rate", 0.4)),
            "pretrained_s2G": pre_g, "pretrained_s2D": pre_g.replace("s2G", "s2D"),
            "if_save_latest": not probe, "if_save_every_weights": not probe,
            "save_every_epoch": 9999 if probe else int(save_every), "gpu_numbers": self._gpu(),
            "grad_ckpt": False, "lora_rank": 32,
            # 日志里多久记一次进度（官方模板是 100 步）：训练时 20 步，看得到进度；实测时 2 步，几十步就能算出速度
            "log_interval": 2 if probe else 20,
        })
        s2["model"]["version"] = self.version
        s2["data"]["exp_dir"] = s2["s2_ckpt_dir"] = str(exp_dir)
        weight_dir = f"SoVITS_weights_{self.version}" if not probe else str(Path(exp_dir) / "weights")
        s2["save_weight_dir"] = weight_dir
        s2["name"] = self.exp_name + ("_probe" if probe else "")
        s2["version"] = self.version
        (Path(exp_dir) / f"logs_s2_{self.version}").mkdir(parents=True, exist_ok=True)
        # 真实的 s2_train.py 不会自己建这个文件夹（只有官方 webui.py 启动时会建），没有的话练完也存不下模型
        (self.p(weight_dir) if not probe else Path(weight_dir)).mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(s2, ensure_ascii=False), encoding="utf-8")

    def _write_s1_config(self, path: Path, bs: int, epochs: int, save_every: int, exp_dir: Path, dpo: bool, *,
                         probe: bool = False) -> None:
        with open(self.p("GPT_SoVITS/configs/s1longer-v2.yaml"), "r", encoding="utf-8") as f:
            s1 = yaml.safe_load(f)
        if not self.is_half:
            s1["train"]["precision"] = "32"
        weight_dir = f"GPT_weights_{self.version}" if not probe else str(Path(exp_dir) / "weights")
        s1["train"].update({
            "batch_size": int(bs), "epochs": int(epochs),
            "save_every_n_epoch": 9999 if probe else int(save_every), "if_save_every_weights": not probe,
            "if_save_latest": not probe, "if_dpo": bool(dpo), "half_weights_save_dir": weight_dir,
            "exp_name": self.exp_name + ("_probe" if probe else ""),
        })
        # 读数据的子进程个数：处理器核数 − 2，至少 2 个、最多 8 个（官方模板是 4 个）
        if not isinstance(s1.get("data"), dict):
            s1["data"] = {}
        s1["data"]["num_workers"] = max(2, min(8, (os.cpu_count() or 4) - 2))
        s1["pretrained_s1"] = str(self.p(PRETRAINED_GPT[self.version]))
        s1["train_semantic_path"] = str(Path(exp_dir) / "6-name2semantic.tsv")
        s1["train_phoneme_path"] = str(Path(exp_dir) / "2-name2text.txt")
        s1["output_dir"] = str(Path(exp_dir) / (f"logs_s1_{self.version}" if not probe else "logs_s1_probe"))
        (Path(exp_dir) / "logs_s1").mkdir(parents=True, exist_ok=True)
        (self.p(weight_dir) if not probe else Path(weight_dir)).mkdir(parents=True, exist_ok=True)  # 同上，s1_train.py 也不建
        path.write_text(yaml.dump(s1, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    # ---------------------------------------------------------------- 实测显卡一次能练几条
    #: 实测时多久量一次显存（秒）
    PROBE_POLL_SECONDS = 1.0

    def _build_probe_dir(self, opt_dir: Path) -> Optional[Path]:
        """用最长的 PROBE_CLIPS 条素材建一个实测用的文件夹 logs/<实验名>_probe（特征文件用硬链接，不行就复制）。
        素材太少（不到 4 条）时返回 None。"""
        try:
            names = [ln.split("\t")[0] for ln in (opt_dir / "2-name2text.txt").read_text(encoding="utf-8").splitlines()
                     if len(ln.split("\t")) == 4]
        except OSError:
            return None
        sizes: Dict[str, int] = {}
        for nm in names:
            try:
                if (opt_dir / "4-cnhubert" / f"{nm}.pt").exists():
                    sizes[nm] = (opt_dir / "5-wav32k" / nm).stat().st_size
            except OSError:
                continue
        pick = sorted(sizes, key=lambda x: (-sizes[x], x))[:PROBE_CLIPS]
        if len(pick) < 4:
            return None
        probe = self.p(f"logs/{self.exp_name}_probe")
        shutil.rmtree(probe, ignore_errors=True)
        probe.mkdir(parents=True, exist_ok=True)
        for sub, suffix in (("4-cnhubert", ".pt"), ("5-wav32k", ""), ("7-sv_cn", ".pt"), ("3-bert", ".pt")):
            src_dir = opt_dir / sub
            if not src_dir.is_dir():
                continue
            (probe / sub).mkdir(exist_ok=True)
            for nm in pick:
                src = src_dir / f"{nm}{suffix}"
                if src.exists():
                    _link_or_copy(src, probe / sub / src.name)
        keep = set(pick)
        text = [ln for ln in (opt_dir / "2-name2text.txt").read_text(encoding="utf-8").splitlines()
                if ln.split("\t")[0] in keep]
        (probe / "2-name2text.txt").write_text("\n".join(text) + "\n", encoding="utf-8")
        sem = (opt_dir / "6-name2semantic.tsv").read_text(encoding="utf-8").splitlines()
        sem = sem[:1] + [ln for ln in sem[1:] if ln.split("\t")[0] in keep]
        (probe / "6-name2semantic.tsv").write_text("\n".join(sem) + "\n", encoding="utf-8")
        return probe

    def _probe_run(self, kind: str, bs: int, probe_dir: Path) -> Dict[str, Any]:
        """用官方的训练程序练每批 bs 条，练够 PROBE_STEPS 步（日志里记的）或 PROBE_SECONDS 秒就停（不存模型）。
        返回 {"bs", "samples_per_s"（第 10 步以后每秒练几条）, "peak_gb"（nvidia-smi 量到的最高显存）, "ok", "why"}。"""
        from voicetwin.utils import gpu as gpu_mod

        row: Dict[str, Any] = {"bs": int(bs), "samples_per_s": None, "peak_gb": None, "ok": False, "why": ""}
        meas: Dict[str, Any] = {"peak": None, "total": None, "count": 0, "last": None}
        events: List[Tuple[float, int]] = []
        if kind == "sovits":
            cfg = self.work_dir / "tmp_probe_s2.json"
            self._write_s2_config(cfg, bs, 100, 9999, probe_dir, probe=True)
            cmd = [self.python, "-s", "GPT_SoVITS/s2_train.py", "--config", str(cfg)]
            env = self.env()
            label = "实测显卡（音色）"
        else:
            cfg = self.work_dir / "tmp_probe_s1.yaml"
            self._write_s1_config(cfg, bs, 100, 9999, probe_dir, False, probe=True)
            cmd = [self.python, "-s", "GPT_SoVITS/s1_train.py", "--config_file", str(cfg)]
            env = self.env({"_CUDA_VISIBLE_DEVICES": self._gpu(), "hz": "25hz"})
            label = "实测显卡（语气）"
        lock = threading.Lock()
        t0 = time.monotonic()

        def sample() -> None:
            s = gpu_mod.smi_sample(self._gpu())
            if s:
                with lock:
                    meas["total"] = s.get("total_gb")
                    used = s.get("used_gb")
                    if used is not None and (meas["peak"] is None or used > meas["peak"]):
                        meas["peak"] = used

        def step_of(line: str) -> Optional[int]:
            if kind == "sovits":
                if _SOVITS_STEP.search(line):
                    meas["count"] += 1
                    return meas["count"] * 2  # log_interval = 2：每一行是 2 步
                return None
            m = _GPT_BAR.search(line)
            if m:
                return int(m.group(1)) * int(m.group(3)) + int(m.group(2))
            return None

        def stop_when(line: str) -> bool:
            st = step_of(line)
            if st is None or (meas["last"] is not None and st <= meas["last"]):
                return False
            meas["last"] = st
            events.append((time.monotonic(), st))
            if len(events) >= PROBE_STEPS:
                sample()
                return True
            return False

        def on_poll() -> bool:
            sample()
            return time.monotonic() - t0 >= PROBE_SECONDS

        try:
            res = self.run_logged(cmd, self.root, env, f"gsv_probe_{kind}", None, (0.0, 1.0), None, label=label,
                                  stop_when=stop_when, on_poll=on_poll, poll_interval=self.PROBE_POLL_SECONDS)
        except TrainStepError as exc:
            row["peak_gb"] = round(meas["peak"], 2) if meas["peak"] is not None else None
            row["why"] = "显存不够" if exc.oom else "出错了：" + (str(exc).splitlines() or ["?"])[0][:120]
            return row
        row["peak_gb"] = round(meas["peak"], 2) if meas["peak"] is not None else None
        if res.get("oom"):
            row["why"] = "显存不够"
            return row
        pts = events[PROBE_WARMUP_STEPS - 1:]
        if len(pts) < 2 or pts[-1][0] <= pts[0][0]:
            row["why"] = f"{time.monotonic() - t0:.0f} 秒里只练了 {len(events)} 步，没测出速度"
            return row
        row["samples_per_s"] = round((pts[-1][1] - pts[0][1]) * int(bs) / (pts[-1][0] - pts[0][0]), 2)
        total = meas["total"]
        if row["peak_gb"] is not None and total and row["peak_gb"] >= total - PROBE_SPILL_GB:
            row["why"] = f"显存满了（最高 {row['peak_gb']:.1f} GB，一共 {total:.1f} GB），再多会借用内存、变慢"
            return row
        row["ok"] = True
        return row

    def _probe_batch(self, kind: str, candidates: List[int], probe_dir: Path, progress: Optional[ProgressFn] = None,
                     prange: Tuple[float, float] = (0.0, 1.0)) -> Tuple[Optional[int], List[Dict[str, Any]]]:
        """从小到大试 candidates：选实测每秒练得最多、显存没满的那个（比小一点的至少快 5% 才用大的）；
        显存不够、显存满了、出错时不再试更大的。返回 (选定的每批条数或 None, 每个数量的实测表)。"""
        name = "音色" if kind == "sovits" else "语气"
        table: List[Dict[str, Any]] = []
        best: Optional[int] = None
        best_rate = 0.0
        cands = sorted(set(int(c) for c in candidates if int(c) >= 1))
        lo, hi = prange
        for i, b in enumerate(cands):
            check_cancel()
            self.step(progress, lo + (hi - lo) * i / max(1, len(cands)), f"实测显卡一次能练几条（{name}）：正在试每批 {b} 条……")
            row = self._probe_run(kind, b, probe_dir)
            table.append(row)
            if row["samples_per_s"] is not None:
                log.info(f"  每批 {b} 条：每秒 {row['samples_per_s']:g} 条，"
                         + (f"显存最高 {row['peak_gb']:.1f} GB" if row["peak_gb"] is not None else "显存用了多少量不出来"))
            if not row["ok"]:
                log.info(f"  每批 {b} 条：{row['why']}，不再试更大的")
                break
            if best is None or row["samples_per_s"] >= best_rate * PROBE_MIN_GAIN:
                best, best_rate = b, float(row["samples_per_s"])
        if best is not None:
            chosen = next(r for r in table if r["bs"] == best)
            tail = "（实测最快，显存没有溢出）" if chosen.get("peak_gb") is not None else "（实测最快；这台电脑量不出显存用了多少）"
            self.step(progress, hi, f"{name}：选定每批 {best} 条{tail}")
        else:
            log.info(f"{name}：没测出来能练几条，按显存的公式算每批数量")
        return best, table

    # ---------------------------------------------------------------- 显存不够：每批减 1 条接着练
    def _oom_ladder(self, what: str, bs: int, run: Callable[[int], None], progress: Optional[ProgressFn], frac: float,
                    floor_bs: int = 1, last_resort: Optional[Callable[[], None]] = None) -> int:
        """跑一步训练；显存不够（CUDA out of memory）时每批数量减 1 条接着练（GPT-SoVITS 会从上次存的进度接着练），
        最多减 OOM_MAX_RETRIES 次；减到 floor_bs 还不够时，有 last_resort 就先用它再试一次。返回实际用的每批数量。"""
        tries = 0
        resorted = False
        while True:
            try:
                run(bs)
                return bs
            except TrainStepError as exc:
                if not exc.oom:
                    raise
                if bs <= floor_bs or tries >= OOM_MAX_RETRIES:
                    if last_resort is not None and not resorted:
                        resorted = True
                        last_resort()
                        continue
                    raise
                new_bs = bs - 1
                msg = f"{what}：显存不够：每批从 {bs} 条减到 {new_bs} 条，接着练（已经练好的部分会接着用）"
                log.warning(msg)
                if progress:
                    try:
                        progress(frac, msg)
                    except Exception:
                        pass
                bs, tries = new_bs, tries + 1

    # ---------------------------------------------------------------- 训练音色 / 语气
    def _run_stage(self, kind: str, opt_dir: Path, params: Dict[str, Any], progress: Optional[ProgressFn],
                   prange: Tuple[float, float], counts: Dict[str, Any], bs: int) -> None:
        """练一步（kind：sovits / gpt）。练的时候盯着硬盘：第一个模型文件存下来以后量它多大，剩下的存不下时
        把保存间隔加倍、接着上次存的进度重新开始这一步（_DiskWatch）。"""
        save_key = f"{kind}_save_every"
        total = int(params[f"{kind}_epochs"])
        restarts = 0
        while True:
            save = int(params[save_key])
            if kind == "sovits":
                cfg = self.work_dir / "tmp_s2.json"
                self._write_s2_config(cfg, bs, total, save, opt_dir)
                cmd = [self.python, "-s", "GPT_SoVITS/s2_train.py", "--config", str(cfg)]
                env = self.env()
                parser = self._sovits_progress(total, counts, params)
                log_name, label = "gsv_s2_train", "训练音色"
            else:
                cfg = self.work_dir / "tmp_s1.yaml"
                self._write_s1_config(cfg, bs, total, save, opt_dir, bool(params.get("if_dpo")))
                cmd = [self.python, "-s", "GPT_SoVITS/s1_train.py", "--config_file", str(cfg)]
                env = self.env({"_CUDA_VISIBLE_DEVICES": self._gpu(), "hz": "25hz"})
                parser = _gpt_parser(total, counts)
                log_name, label = "gsv_s1_train", "训练语气和节奏"
            watch = _DiskWatch(self, kind, total, save)
            res = self.run_logged(cmd, self.root, env, log_name, progress, prange, parser, label=label,
                                  on_poll=watch.poll, poll_interval=self.POLL_SECONDS)
            if res.get("stopped") and watch.new_save and restarts < 3:
                params[save_key] = watch.new_save
                params.setdefault("disk_guard", {})[kind] = {"weight_mb": watch.size_mb, "save_every": watch.new_save}
                restarts += 1
                continue
            return

    def _sovits_progress(self, total: int, counts: Dict[str, Any],
                         params: Dict[str, Any]) -> Callable[[str], Optional[Tuple[float, str]]]:
        """训练音色的进度；没有 N 卡时练完第一轮按实际速度估计一下还要多久（只说一次，标明是估计）。"""
        base = _sovits_parser(total, counts)
        t0 = time.time()
        said = [params.get("tier") != "none" or params.get("mode") != "identical"]

        def parse(line: str) -> Optional[Tuple[float, str]]:
            res = base(line)
            if not said[0]:
                m = _SOVITS_DONE.search(line)
                if m:
                    said[0] = True
                    e = int(m.group(1))
                    done = e - int(counts.get("resumed_from") or 0)
                    if done > 0 and total > e:
                        hours = (time.time() - t0) / done * (total - e) / 3600.0
                        log.warning(f"没有检测到能用的 N 卡：仍然按「一模一样」训练，但用处理器会非常慢。按第一轮的实际速度估算，"
                                    f"音色训练练完大约还要 {hours:.1f} 小时；着急的话可以改选「标准」。")
            return res

        return parse

    def _train_sovits(self, opt_dir: Path, params: Dict[str, Any], progress: Optional[ProgressFn],
                      pos: Optional[Dict[str, float]] = None, counts: Optional[Dict[str, Any]] = None) -> int:
        pos = pos or TRAIN_POS["standard"]
        counts = {} if counts is None else counts
        total = int(params["sovits_epochs"])
        self.step(progress, pos["sovits"], f"训练音色（SoVITS），共 {total} 轮……")
        return self._oom_ladder("训练音色（SoVITS）", int(params["batch_size"]),
                                lambda bs: self._run_stage("sovits", opt_dir, params, progress, (pos["sovits"], pos["gpt"]),
                                                           counts, bs), progress, pos["sovits"])

    def _train_gpt(self, opt_dir: Path, params: Dict[str, Any], progress: Optional[ProgressFn],
                   pos: Optional[Dict[str, float]] = None, counts: Optional[Dict[str, Any]] = None) -> int:
        pos = pos or TRAIN_POS["standard"]
        counts = {} if counts is None else counts
        total = int(params["gpt_epochs"])
        dpo = bool(params.get("if_dpo"))
        self.step(progress, pos["gpt"], f"训练语气和节奏（GPT），共 {total} 轮" + ("，已开启 DPO（会比较慢）" if dpo else "") + "……")
        return self._oom_ladder("训练语气和节奏（GPT）", int(params["gpt_batch_size"]),
                                lambda bs: self._run_stage("gpt", opt_dir, params, progress, (pos["gpt"], pos["save"]),
                                                           counts, bs), progress, pos["gpt"])

    @classmethod
    def train_stages_for(cls, mode: Any = None) -> List[Stage]:
        """训练分哪几步（引擎自己的 0~1 进度）：standard 和以前一样；identical 多一步「实测显卡一次能练几条」。"""
        return list(TRAIN_STAGES_IDENTICAL if resolve_train_mode(mode) == "identical" else cls.train_stages)

    # ---------------------------------------------------------------- 训练
    def train(self, progress: Optional[ProgressFn] = None, **opts: Any) -> Dict[str, Any]:
        """训练。opts（高级设置 / 命令行，None 或 "auto" 表示自动）：mode（identical / standard，见 resolve_train_mode）、
        batch_size、sovits_epochs、gpt_epochs、sovits_save_every、gpt_save_every、if_dpo（True / False / None）。

        先看素材有没有变（_run_state）：变了从头练（旧模型备份、下次挑选时也参加比较）；没变而计划练得更多就接着练；
        没变而且已经练够了就不重新训练（直接返回上次的结果，接着挑选）。
        返回值（也写进 models.json）的 params 里有这次实际用的设置，params["summary"] 是一行中文说明，
        params["report"] 是训练完实测的几句话（实际参加训练的条数、英文、显卡、用时）。"""
        from voicetwin.data.exporters import export_gptsovits

        mode = self._train_mode(opts.pop("mode", None))
        opts.pop("train_v4", None)
        pos = TRAIN_POS[mode]
        t_start = time.time()
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
        n = int(exp["count"])
        minutes = float(exp["minutes"])
        self.step(progress, pos["plan"] - 0.01, f"训练素材 {n} 条，共 {minutes} 分钟")
        list_path, wav_dir = Path(exp["list"]), Path(exp["wav_dir"])
        gpu = self._gpu_memory()
        if gpu[0] <= 0:
            log.warning("没有检测到可用的 NVIDIA 显卡，训练会非常慢（CPU 训练可能需要数天）")
        tier = _tier(gpu[0] + REPORTED_FUDGE_GB if gpu[0] > 0 else 0.0)
        parts = self._feature_parts(tier)
        opt_dir = self._opt_dir()
        opt_dir.mkdir(parents=True, exist_ok=True)
        feat = self._feature_digest(list_path, wav_dir)
        st = self._run_state(feat, mode, dict(opts), n, minutes, gpu)
        mixed_ready = None
        if (st["state"] in ("extend", "skip", "continue") and feat["frontend"] == "mixed"
                and self._frontend_used(opt_dir) == "official" and (opt_dir / "2-name2text.txt").exists()):
            mixed_ready = self._try_mixed(list_path, wav_dir, opt_dir, n, progress, pos, parts)
            if mixed_ready is not None:
                st.update(state="fresh", kinds=["frontend"], reasons=["中英文一起训练的新方法"], plan=None,
                          note=("这次会从头训练（原因：中英文一起训练的新方法）。你原来的模型会备份起来，一起参加比较；"
                                "新模型实测不比它好，就继续用它。"))
        state = st["state"]
        user_batch = not _is_auto(self._user_settings(opts).get("batch_size"))
        will_probe = (mode == "identical" and state in ("fresh", "continue") and not user_batch and gpu[0] > 0
                      and self._probe_enabled())
        params = st.get("plan") or self._make_plan(n, minutes, opts, gpu=gpu, mode=mode, will_probe=will_probe)
        self.step(progress, pos["plan"], params["summary"])
        for line in params["notes"]:
            log.info(f"  · {line}")
        if st.get("note"):
            self.step(progress, pos["plan"], st["note"])

        prev = st.get("previous")
        if state == "skip":
            assert prev is not None
            info = {k: v for k, v in prev.items() if k not in ("selection", "speed", "selection_error")}
            info["params"] = dict(prev["params"], run_state="skip")
            self.project.update_models(self.name, {"params": info["params"]})
            self.step(progress, 1.0, "GPT-SoVITS 训练完成（素材没变，这次不用重新训练）")
            return info

        self.ensure_users_pth()
        t_feat = time.time()
        feats = self._prepare_features(list_path, wav_dir, progress, n_clips=n, feat=feat, changed=state == "fresh",
                                       kinds=st.get("kinds"), pos=pos, parts=parts, mixed_ready=mixed_ready)
        features_s = time.time() - t_feat
        features = self._count_features(opt_dir, n)

        probe_s = None
        probe: Optional[Dict[str, Any]] = None
        if will_probe:
            probe, probe_s = self._probe_or_cached(opt_dir, feat["digest"], n, bool(params.get("if_dpo")), progress, pos)
            if probe and (probe.get("sovits") or probe.get("gpt")):
                params = self._make_plan(n, minutes, opts, gpu=gpu, mode=mode,
                                         probe_batch={"sovits": probe.get("sovits"), "gpt": probe.get("gpt")})
                self.step(progress, pos["sovits"], params["summary"])
                for line in params["notes"]:
                    log.info(f"  · {line}")
        params["tier"] = tier

        pp = (prev or {}).get("params") or {}
        s_done = _to_int(pp.get("sovits_epochs"), 0) if state == "extend" else 0
        g_done = _to_int(pp.get("gpt_epochs"), 0) if state == "extend" else 0
        counts_s: Dict[str, Any] = {}
        counts_g: Dict[str, Any] = {}
        gpu_used: Dict[str, Any] = {}
        timing: Dict[str, Any] = {"features_s": round(features_s, 1), "probe_s": probe_s}
        used_s, used_g = int(params["batch_size"]), int(params["gpt_batch_size"])
        for kind in ("sovits", "gpt"):
            total = int(params[f"{kind}_epochs"])
            done = s_done if kind == "sovits" else g_done
            if state == "extend" and total <= done:
                log.info(f"{'音色（SoVITS）' if kind == 'sovits' else '语气（GPT）'}上次已经练到第 {done} 轮，这次不用再练")
                continue
            sampler = _gpu_sampler(self._gpu())
            t0 = time.time()
            try:
                if kind == "sovits":
                    used_s = self._train_sovits(opt_dir, params, progress, pos, counts_s)
                else:
                    used_g = self._train_gpt(opt_dir, params, progress, pos, counts_g)
            finally:
                gpu_used[kind] = sampler.stop()
            secs = time.time() - t0
            counts = counts_s if kind == "sovits" else counts_g
            start = int(counts.get("resumed_from") or done)
            timing[f"{kind}_s"] = round(secs, 1)
            if total > start:
                timing[f"{kind}_s_per_epoch"] = round(secs / (total - start), 1)
        if used_s != params["batch_size"] or used_g != params["gpt_batch_size"]:
            params["oom_retry"] = True
            params["batch_size_used"] = used_s
            params["gpt_batch_size_used"] = used_g

        self.step(progress, pos["save"], "保存模型……" if mode == "standard" else "保存模型、核对实际参加训练的条数……")
        sovits, gpt = self._list_weights()
        if not sovits or not gpt:
            raise RuntimeError("训练结束但没有找到权重文件，请查看 logs/gsv_s2_train.log 与 logs/gsv_s1_train.log")
        trained = _trained_counts(counts_s, counts_g, n)
        if state == "extend":  # 这次没练的那一步：沿用上次实测的条数
            old_tc = pp.get("trained_counts") or {}
            for kind in ("sovits", "gpt"):
                if trained.get(kind) is None and old_tc.get(kind) is not None:
                    trained[kind] = old_tc[kind]
        timing["total_s"] = round(time.time() - t_start, 1)
        params.update(mode=mode, run_state=state, timing=timing, gpu=gpu_used, features=features,
                      trained_counts=trained, text_frontend=feats["frontend"], en_phones=feats["en_phones"],
                      en_lines=feats["en_lines"], feature_parts=parts)
        if probe:
            params["probe"] = {"sovits": probe.get("sovits"), "gpt": probe.get("gpt"), "table": probe.get("table")}
        params["report"] = _report_lines(params)
        for line in params["report"]:
            self.step(progress, pos["save"], line)
        info = {
            "version": self.version, "exp_name": self.exp_name, "trained_at": time.strftime("%Y-%m-%d %H:%M"),
            "params": params, "sovits": [str(p) for p in sovits], "gpt": [str(p) for p in gpt],
            "selected": {"id": f"s{_epoch(sovits[-1])}-g{_epoch(gpt[-1])}", "sovits": str(sovits[-1]), "gpt": str(gpt[-1])},
            # 这个模型是用哪份素材训练好的（训练做完才记：训练失败 / 停止了，还是旧模型的指纹，提醒不会消失）
            "list_sha1": feat["list_sha1"], "features_sha1": feat["digest"],
        }
        # 旧模型的挑选结果和语速校准不能留给新模型用（自动挑选没做成功、或者不挑选时，会一直用着旧的数字）
        self.project.update_models(self.name, info, drop=("selection", "speed", "selection_error"))
        self.step(progress, 1.0, "GPT-SoVITS 训练完成")
        return info

    def _probe_or_cached(self, opt_dir: Path, digest: str, n: int, dpo: bool, progress: Optional[ProgressFn],
                         pos: Dict[str, float]) -> Tuple[Optional[Dict[str, Any]], Optional[float]]:
        """实测显卡一次能练几条（同一份素材实测过就用上次的结果，例如上次训练中途停下了）。返回 (结果, 用了几秒)。"""
        try:
            cached = json.loads((opt_dir / PROBE_FILE).read_text(encoding="utf-8"))
            if isinstance(cached, dict) and cached.get("digest") == digest:
                log.info("这份素材上次已经实测过显卡一次能练几条，直接用上次的结果")
                return cached, None
        except (OSError, ValueError):
            pass
        self.step(progress, pos["probe"], f"实测显卡一次能练几条（用最长的 {PROBE_CLIPS} 条素材，每个数量练几十步就停，不存模型）……")
        t0 = time.time()
        probe_dir = self._build_probe_dir(opt_dir)
        if probe_dir is None:
            log.info("素材太少，不实测，按显存的公式算每批数量")
            return None, None
        cap = max(1, n // 4)
        mid = pos["probe"] + (pos["sovits"] - pos["probe"]) / 2
        try:
            b_s, tab_s = self._probe_batch("sovits", [b for b in PROBE_SOVITS if b <= cap], probe_dir, progress,
                                           (pos["probe"], mid))
            if dpo:  # 开了 DPO：语气训练每批的条数官方代码里还会再减半，不实测
                b_g, tab_g = None, []
            else:
                b_g, tab_g = self._probe_batch("gpt", [b for b in PROBE_GPT if b <= cap], probe_dir, progress,
                                               (mid, pos["sovits"]))
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)
        secs = round(time.time() - t0, 1)
        probe = {"digest": digest, "sovits": b_s, "gpt": b_g, "table": {"sovits": tab_s, "gpt": tab_g}, "seconds": secs}
        try:
            (opt_dir / PROBE_FILE).write_text(json.dumps(probe, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        return probe, secs

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

    def checkpoints(self, max_sovits: Optional[int] = None, max_gpt: Optional[int] = None,
                    all: bool = False) -> List[Dict[str, Any]]:  # noqa: A002 - 设计方案里就叫 all
        """自动挑选要试的模型组合：SoVITS 默认 4 个 × GPT 3 个，从早到晚均匀挑（最后一轮一定在内）。
        all=True（「一模一样」）：每个存下的版本都试（练到第 4 轮以后的；不到 4 轮的只有最后一个）。

        两种都把原来用的模型（previous_selected，文件还在时）加在最后一起比较。
        config.yaml 的 backends.gptsovits.train.select_sovits / select_gpt 可以改前两个数。"""
        out = self._checkpoint_grid(max_sovits, max_gpt, every=all)
        prev = (self.project.load_models().get(self.name) or {}).get("previous_selected") or {}
        if isinstance(prev, dict) and prev.get("sovits") and prev.get("gpt"):
            sov, gpt = self._locate_weight(str(prev["sovits"])), self._locate_weight(str(prev["gpt"]))
            known = {(c["sovits"], c["gpt"]) for c in out}
            if sov and gpt and (str(sov), str(gpt)) not in known:
                out.append({"id": f"prev-s{_epoch(sov)}-g{_epoch(gpt)}", "sovits": str(sov), "gpt": str(gpt),
                            "sovits_epoch": _epoch(sov), "gpt_epoch": _epoch(gpt), "previous": True})
        return out

    def _checkpoint_grid(self, max_sovits: Optional[int], max_gpt: Optional[int], every: bool) -> List[Dict[str, Any]]:
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
        if every:
            pick_s = [w for w in sovits if _epoch(w) >= 4] or sovits[-1:]
            pick_g = [w for w in gpt if _epoch(w) >= 4] or gpt[-1:]
        else:
            pick_s, pick_g = _spread(sovits, ks), _spread(gpt, kg)
        out = []
        for s in pick_s:
            for g in pick_g:
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

    def trained_material_note(self) -> str:
        """校对表在上次训练以后又改过（改了文字、删除或恢复了句子）时返回一句提醒，否则返回空字符串。

        怎么判断：训练开始时 _prepare_features 记下了当时训练列表的指纹（GPT-SoVITS 的 logs/<实验名>/voicetwin_list.sha1）；
        用现在校对表里保存好的文字按同样的方法算一遍（旧版本训练的模型也能判断）。"""
        try:
            entry = self.project.load_models().get(self.name) or {}
            stamp = self._opt_dir() / "voicetwin_list.sha1"
            # 训练做完时记下的指纹（训练失败 / 中途停止不会改它）；旧版本训练的模型只有训练开始时写的那份
            want = str(entry.get("list_sha1") or "") or (stamp.read_text().strip() if stamp.exists() else "")
            if not want or not entry.get("sovits"):
                return ""
            from voicetwin.data.exporters import gptsovits_list_text, train_records

            recs = train_records(self.project)
            if not recs:
                return ""
            # 和 export_gptsovits 写文件时一样：文本方式写入，Windows 上换行是 \r\n。
            # 也按以前的句末标点规则（末尾补「。」）算一遍：以前训练的模型用的就是那样的列表，
            # 只是导出规则改进了、老师什么都没改时，不能说「校对表改过」
            for legacy in (False, True):
                data = gptsovits_list_text(self.project, self.exp_name, recs, legacy_punct=legacy)
                data = data.replace("\n", os.linesep).encode("utf-8")
                if hashlib.sha1(data + self.version.encode()).hexdigest() == want:
                    return ""
        except Exception:
            return ""
        return ("⚠️ 校对表在上次训练以后改过（改了文字、删除或恢复了句子），现在的模型还是用改之前的素材训练的。"
                "想让改好的文字生效，请到「② 训练模型」重新点「开始训练」（只用保存好的文字、不用删除的句子）。")

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
        weights = self._weights_to_use()
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
        self._speed_trick = None  # 新启动的引擎：「语速 1.0001」重新自检
        self.batch_stats["speed_trick"] = None
        self.batch_stats["speed_trick_reason"] = ""
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

    def _weights_to_use(self) -> Dict[str, Any]:
        return self._wanted or self._current_weights()

    def _ensure_weights(self) -> None:
        w = self._weights_to_use()
        if w["sovits"] and w["gpt"]:
            self._set_weights(w["gpt"], w["sovits"])

    def use_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        self._wanted = {"id": ckpt.get("id", "?"), "gpt": ckpt["gpt"], "sovits": ckpt["sovits"]}
        if not self._alive():
            self.start()
        self._set_weights(ckpt["gpt"], ckpt["sovits"])

    def _server_died(self) -> bool:
        return self.proc is not None and self.proc.poll() is not None

    def _payload(self, req: SynthRequest, *, batch: int = 1, interval: float = 0.3,
                 speed: Optional[float] = None) -> Dict[str, Any]:
        """发给 api_v2 POST /tts 的请求。用默认值（batch=1、interval=0.3、speed=None 按 req 的语速）就是 synthesize
        一直发的那一份，一个字段、一个数都不变；同时生成好几个版本时只有 batch_size、fragment_interval
        （版本之间的数字静音）和 speed_factor 不一样（文字由调用的地方换成复制好的几份）。"""
        icfg = self.bcfg.get("infer", {}) or {}
        # 语速：speed_factor 在模型内部控制时长（SoVITS 解码前把内容特征序列按 1/speed 插值拉长或缩短，
        # 再由声码器生成波形，见 GPT_SoVITS/module/models.py 的 TextEncoder.forward），音高和音色不变；
        # 官方代码里对整段音频做 atempo 变速的写法已经注释掉了（TTS.py）。所以这里不对生成的音频做任何重采样或变速。
        speed_factor = _speed_of(req) if speed is None else max(0.25, min(4.0, float(speed)))
        # 语言：句子里只要有汉字就按 zh 发（zh 模式中英混读；以前英文单词多的句子被判成 en，
        # GPT-SoVITS 的 en 模式会把里面的汉字整个丢掉）。参考音频的文字也一样
        return {
            "text": req.text,
            "text_lang": send_lang(req.text, req.lang),
            "ref_audio_path": str(Path(req.ref_audio).resolve()),
            "aux_ref_audio_paths": [str(Path(p).resolve()) for p in req.aux_refs],
            "prompt_text": req.ref_text,
            "prompt_lang": send_lang(req.ref_text, req.ref_lang),
            "top_k": int(req.top_k if req.top_k is not None else icfg.get("top_k", 15)),
            "top_p": float(req.top_p if req.top_p is not None else icfg.get("top_p", 1.0)),
            "temperature": float(req.temperature if req.temperature is not None else icfg.get("temperature", 1.0)),
            "text_split_method": "cut0",   # 已按句切好，不再二次切分，保留模型自己的句内停顿
            "batch_size": int(batch),
            "speed_factor": speed_factor,
            "fragment_interval": float(interval),
            "seed": int(req.seed),
            "media_type": "wav",
            "streaming_mode": False,
            "parallel_infer": True,
            "repetition_penalty": float(icfg.get("repetition_penalty", 1.35)),
            "sample_steps": int(icfg.get("sample_steps", 32)),
            "super_sampling": False,
        }

    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        if not self._alive():
            self.start()
        data = self._tts_answer(self._payload(req))
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        return out_path

    def _tts_answer(self, payload: Dict[str, Any]) -> bytes:
        """发一次 POST /tts，返回引擎回的 WAV（已经修好半精度溢出的「咔哒」声）。

        失败时抛出 RuntimeError，第一行是「GPT-SoVITS 合成失败：原因」；属性 oom=True 表示这次的原因是显存不够。"""
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
            reason = _api_reason(r)
            text = f"GPT-SoVITS 合成失败：{reason}"
            if self._server_died():
                text += "\n推理服务已经退出了。\n" + self._api_report(20)
            raise _answer_error(text, reason)
        silent = _silent_answer(r.content)
        if silent:
            # 真实的 TTS.run 出错时（比如显存不够）不报错：打印 Traceback，然后回 200 + 1 秒 16 kHz 的静音
            # （GPT_SoVITS/TTS_infer_pack/TTS.py @ abe9843 第 1516~1518 行）。模拟版回的是 400，所以以前没发现。
            reason = _last_exception(self._api_new_text(log_pos))
            raise _answer_error("GPT-SoVITS 合成失败：" + (reason or f"引擎回了一段{silent}，记录里没有报错"
                                                          "（可能是这句话里没有它能读出来的字）")
                                + "\n" + self._api_report(20), reason)
        return _fix_int16_wrap(r.content)

    # ================================================================ 一次请求同时生成好几个版本
    def _batch_version(self) -> str:
        """现在用的 SoVITS 模型是哪个版本：从正在用的模型文件读（自动挑选时是正在试的那个）；
        读不出来（别处的服务、不认识的文件）时按设置里的版本。"""
        w = self._weights_to_use()
        ver = detect_sovits_version(w["sovits"], self.root).get("version") if w.get("sovits") else None
        return str(ver or self.version)

    def _single_reason(self, req: SynthRequest, n: int) -> str:
        """要 n 个版本时，为什么只能一个一个生成（中文原因）；能同时生成时返回空字符串。"""
        if n <= 1:
            return "只要一个版本"
        if self._max_batch is not None and self._max_batch <= 1:
            return "显存不够，已经改成一次生成一个"
        if _batch_text(req.text, self._payload(req)["text_lang"], 2) is None:
            return "这句话不能同时生成（很短的句子会被引擎合在一起读、有换行或者太长）"
        ver = self._batch_version()
        if ver not in BATCH_VERSIONS:
            return f"{ver} 模型只能一个一个生成"
        if _speed_of(req) == 1.0 and not self._speed_trick_ok(req):
            # 按自检之后的情况说真正的原因：自检里显存不够（已经改成一次一个）、自检出错没做完、自检做完了没通过
            if self._max_batch is not None and self._max_batch <= 1:
                return "显存不够，已经改成一次生成一个"
            if self._speed_trick is None:
                return f"「语速 1.0001」自检没做成（{self.batch_stats['speed_trick_reason']}）"
            return "「语速 1.0001」自检没通过（语速正好 1.0 的句子）"
        return ""

    def _count(self, batch: int, seconds: float, pieces: int) -> None:
        st = self.batch_stats
        st["requests"] += 1
        st["pieces"] += int(pieces)
        row = st["by_batch"].setdefault(str(int(batch)), {"requests": 0, "pieces": 0, "seconds": 0.0})
        row["requests"] += 1
        row["pieces"] += int(pieces)
        row["seconds"] = round(row["seconds"] + float(seconds), 3)

    def _speed_trick_once(self, req: SynthRequest, seed: int) -> Tuple[bool, str, Dict[str, float]]:
        """用一个随机种子自检一次：返回 (通过没有, 没通过的原因, 量出来的数 {"len_diff": 长度差, "r": 波形相关系数})。"""
        import numpy as np

        base = dataclasses.replace(req, seed=int(seed))
        xa, sra = _read_int16(self._tts_answer(self._payload(base, speed=1.0)))
        xb, srb = _read_int16(self._tts_answer(self._payload(base, speed=BATCH_SPEED)))
        if sra != srb:
            return False, f"采样率不一样（{sra} / {srb}）", {}
        la, lb = len(xa), len(xb)
        diff = abs(la - lb) / float(max(la, lb, 1))
        if diff > SPEED_TRICK_MAX_LEN_DIFF:
            return False, f"长度差了 {diff:.1%}", {"len_diff": diff}
        m = min(la, lb)
        a, b = xa[:m].astype(np.float64), xb[:m].astype(np.float64)
        r = float(np.corrcoef(a, b)[0, 1]) if m > 1 and a.std() > 0 and b.std() > 0 else float("nan")
        measured = {"len_diff": diff, "r": r}
        if not (r >= SPEED_TRICK_MIN_R):  # nan 也算没通过
            return False, f"波形的相关系数只有 {r:.3f}", measured
        text2 = _batch_text(req.text, self._payload(req)["text_lang"], 2)
        if text2 is None:
            return False, "这句话不能同时生成，没法检查能不能切开", measured
        payload = self._payload(base, batch=2, interval=BATCH_INTERVAL, speed=BATCH_SPEED)
        payload["text"] = text2
        try:
            data = self._tts_answer(payload)
        except RuntimeError as exc:
            if getattr(exc, "oom", False):  # 同时生成 2 个显存都不够：以后一个一个生成，不用每句都再查
                self._max_batch = self.batch_stats["max_batch"] = 1
                log.info("显存不够：同时生成 2 个也不够，改成一次生成一个（不会停下）")
            raise
        pieces, _sr, why = _split_wav(data, 2, BATCH_INTERVAL)
        if pieces is None:
            return False, f"同时生成的 2 个版本分不开（{why}）", measured
        return True, "", measured

    def _speed_trick_ok(self, req: SynthRequest) -> bool:
        """语速正好 1.0 的句子能不能同时生成：自检「语速写成 1.0001」在这次启动的引擎上是不是和 1.0 几乎一样。

        同一个随机种子、同一条参考录音各生成一次（1.0 和 1.0001），长度差不超过 1%、波形相关系数至少 0.99，
        再同时生成 2 个版本、要能切开，才算通过；最多换 2 个随机种子（显卡计算有一点点随机的出入），有一个通过就算通过。
        每次启动引擎只查一次（start() 时清掉）；自检时出错（比如显存不够）不换种子再试，这次先按没通过算、下次再查。
        没通过只影响语速正好 1.0 的句子（改成一个一个生成，结果的标准一样，只是更慢）。"""
        if self._speed_trick is not None:
            return self._speed_trick
        reasons: List[str] = []
        errored = False
        ok = False
        measured: Dict[str, float] = {}
        for j in range(SPEED_TRICK_SEEDS):
            try:
                ok, why, measured = self._speed_trick_once(req, int(req.seed) + j * SEED_STEP)
            except Exception as exc:  # 停止按钮（TaskCancelled）不是 Exception，照常传出去
                reasons.append("自检时出错：" + str(exc).split("\n", 1)[0][:200])
                errored = True
                break
            if ok:
                break
            reasons.append(why)
        reason = "；".join(dict.fromkeys(reasons))
        self.batch_stats["speed_trick"] = ok if not errored else None
        self.batch_stats["speed_trick_reason"] = "" if ok else reason
        if ok:
            self._speed_trick = True
            # 只写量出来的：相关系数往下舍（0.9996 写 0.999，不会写成 1.000 让人以为完全一样）
            r_shown = math.floor(measured["r"] * 1000) / 1000
            log.info(f"自检通过：语速写成 1.0001 和 1.0 生成的声音几乎一样（长度差 {measured['len_diff']:.2%}、"
                     f"波形相关系数 {r_shown:.3f}），同时生成的 2 个版本也能按数字静音分开——可以同时生成好几个版本")
        elif errored:
            log.info(f"「语速 1.0001」自检没做成（{reason}）：这次语速正好 1.0 的句子先一个一个生成，下次再查")
        else:
            self._speed_trick = False
            log.info(f"自检没通过（{reason}）：语速正好 1.0 的句子改成一个一个生成（结果的标准一样，只是更慢）")
        return ok

    def synthesize_many(self, req: SynthRequest, n: int, out_dir: Path) -> List[Tuple[Path, int]]:
        """同一句话要 n 个版本，写进 out_dir，返回 [(文件, 第几个)]。

        能同时生成时只发一次请求：同一句话复制 n 份、用换行隔开，batch_size = n、fragment_interval = 0.5、
        语速 1.0 时发 1.0001（见 BATCH_SPEED），再按每个版本后面的数字静音切开，每个后面补 0.3 秒的 0。
        这些情况一个一个生成（第 k 个用随机种子 seed + k × SEED_STEP，请求和 synthesize 的完全一样）：
        只要 1 个；按官方规则算，文字不能正好切成 n 段、每段和单独生成时一样；模型不是 v2 / v2Pro / v2ProPlus；
        语速正好 1.0 而这次启动的引擎没通过「1.0001」自检。
        显存不够：同时生成的数量减半再试（记下来，以后都不超过它），所以拿到的个数可能比 n 少；减到 1 个还不够，
        先调用 release_gpu_callback 让出显存、再试一次，还不行就和 synthesize 一样报错。
        切不开（段数不对等）：说明原因，改成一个一个生成。"""
        n = max(1, int(n))
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        if not self._alive():
            self.start()
        why = self._single_reason(req, n)
        if why:
            if n > 1:
                d = self.batch_stats["single_reasons"]
                d[why] = d.get(why, 0) + 1
            return self._many_singles(req, n, out_dir)
        import soundfile as sf

        b = min(n, self._max_batch or n)
        speed = _speed_of(req)
        send = BATCH_SPEED if speed == 1.0 else speed
        lang = self._payload(req)["text_lang"]
        while b > 1:
            check_cancel()
            text = _batch_text(req.text, lang, b)
            if text is None:  # 上面已经按 2 份检查过；段数不受份数影响，这里只是保险
                return self._many_singles(req, b, out_dir)
            payload = self._payload(req, batch=b, interval=BATCH_INTERVAL, speed=send)
            payload["text"] = text
            t0 = time.monotonic()
            try:
                data = self._tts_answer(payload)
            except RuntimeError as exc:
                if not getattr(exc, "oom", False):
                    raise
                half = b // 2
                log.info(f"显存不够：每次同时生成的数量从 {b} 减到 {half}，接着试（不会停下）")
                self.batch_stats["oom_backoffs"] += 1
                self._max_batch = self.batch_stats["max_batch"] = half
                b = half
                continue
            pieces, sr, why = _split_wav(data, b, BATCH_INTERVAL)
            self._count(b, time.monotonic() - t0, len(pieces) if pieces else 0)
            if pieces is None:
                log.info(f"这次没能把同时生成的几个版本分开（原因：{why}），改成一个一个生成")
                self.batch_stats["split_fallbacks"] += 1
                self.batch_stats["split_reason"] = why
                return self._many_singles(req, b, out_dir)
            prefix = many_prefix(out_dir)
            out: List[Tuple[Path, int]] = []
            for k, piece in enumerate(pieces):
                path = out_dir / f"{prefix}_b{b}_r{k}.wav"
                sf.write(str(path), piece, sr, subtype="PCM_16")
                out.append((path, k))
            self.last_many = {"mode": "batch", "batch": b, "seed": int(req.seed), "speed": send}
            return out
        return self._many_singles(req, 1, out_dir)

    def _many_singles(self, req: SynthRequest, n: int, out_dir: Path) -> List[Tuple[Path, int]]:
        """一个一个生成 n 个版本（第 k 个用随机种子 seed + k × SEED_STEP）。"""
        prefix = many_prefix(out_dir)
        out: List[Tuple[Path, int]] = []
        seeds: List[int] = []
        for k in range(max(1, int(n))):
            check_cancel()
            one = dataclasses.replace(req, seed=int(req.seed) + k * SEED_STEP)
            t0 = time.monotonic()
            path = self._synthesize_freeing_gpu(one, out_dir / f"{prefix}_r{k}.wav")
            self._count(1, time.monotonic() - t0, 1)
            out.append((path, k))
            seeds.append(one.seed)
        self.last_many = {"mode": "single", "seeds": seeds, "speed": _speed_of(req)}
        return out

    def _synthesize_freeing_gpu(self, req: SynthRequest, out_path: Path) -> Path:
        """单独生成一个；显存不够时先调用 release_gpu_callback 让出显存，再试一次，还不行就照常报错。

        回调返回真值（比如 CERChecker.release_gpu 卸掉了模型）才算让出了显存、记进 gpu_releases；
        日志按实际发生的写（让出了 / 没有能让出的 / 出错了）。不管让没让出都再试一次，还不行才报错。"""
        try:
            return self.synthesize(req, out_path)
        except RuntimeError as exc:
            if not getattr(exc, "oom", False):
                raise
            cb = self.release_gpu_callback
            note = ""
            if cb is not None:
                try:
                    released = bool(cb())
                except Exception as e2:  # 让不出来也接着试
                    released = False
                    note = f"没能让出显存（{(str(e2).splitlines() or [type(e2).__name__])[0][:200]}），"
                else:
                    note = "已经让出了一部分显存，" if released else "没有能让出的显存，"
                if released:
                    self.batch_stats["gpu_releases"] += 1
            log.info("显存不够：一次只生成一个也不够。" + note + "再试一次……")
        return self.synthesize(req, out_path)

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
