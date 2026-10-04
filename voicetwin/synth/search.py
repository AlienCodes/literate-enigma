"""「一模一样」档每句话怎么找（设计方案 research/一模一样/设计方案原文.md §1.5、§1.7、§1.8）。

1. 挑参考录音（shortlist_refs）：从参考录音库（refs_bank.json）里按句型、长短、英文比例、是不是一段话的开头、
   试听 / 原来的分数打分，挑 R 条（第二条尽量来自别的视频）；和这句话文字一样的录音不用。每条主参考再配几条
   辅助参考（aux_set：同语言、陈述句、别的视频、4~9.8 秒）。
2. 组合（Arm）= 参考录音 × 生成设置（P0 / P1，读错时加更稳的 P2）× 辅助参考几条（3 / 0）[× 语速]。
3. 第 1 轮每种组合发一次请求（同一条参考的排在一起，引擎可以接着用算好的参考特征）；读错太多就加更稳的设置，
   语速整体偏了就加一个改了语速的组合；第 2 轮最好的两种组合各一次；之后最好的组合一次一次地试。
   每次请求一次同时生成好几个版本（引擎自检通过时；见 backends/gptsovits.py synthesize_many）。
4. 打分分两步（eval/identical_judge.py）：每个版本都快速打分，快速分前 12 名、每种组合最好的那个再完整打分（每句最多 24 个）。
5. 停下：试满至少的个数、挑出来的那个达到继续找的目标（错字检查通过、像你本人不低于你自己录音的中位水平），
   并且最近 8 个版本没让最好的综合分再高 0.02；或者试满最多的个数。连着 2 次请求什么都没拿到、又一个版本都没有时放弃。
6. 语速微调：挑出来的那个（和差不到 0.02 的第二名）语速和你平时差得多时，同一个请求只改语速再发一次，拿同一行。
7. 每句留下最好的 6 个版本（store_candidates）：重新生成时它们一起比（最好的不会变差）；打分标准、说话习惯、
   排序权重变了时，不用显卡、按新标准重新排一遍。

只有生成线程（_Producer）跟合成引擎说话（用 requests）；主线程一边打分。没有 N 卡时不开生成线程（pipeline: auto）。
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
import queue
import random
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.backends.base import SEED_STEP, SynthRequest
from voicetwin.eval.metrics import Score
from voicetwin.utils.audio import load_audio
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import normalize_for_cer, send_lang, short_hash, syllable_count

try:  # 停止按钮
    from voicetwin.utils.progress import TaskCancelled
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    class TaskCancelled(BaseException):  # type: ignore[no-redef]
        pass

    def _check_cancel() -> None:
        return None

log = get_logger("search")

#: Arm.preset_idx：更稳的生成设置（P2，有字读错时才加）
RESCUE = -1
#: 每句话之间种子差这么多（和以前的档位一样）
SENT_SEED_STEP = 7919
#: 综合分差不到这么多算「差不多一样高」：这时按时长、音调、读得准不准挑
TIE_EPS = 0.02
#: 比「再试也不更好」时，达标的档次（读对了、达到全部标准）每高一级算多这么多分
CLASS_GAP = 100.0
#: 语速微调：差多少才重发、语速最多改多少、重发出来的时长和原来按语速换算差 4% 以内才算「同一个版本只改了语速」
REFINE_MIN_DEV = 0.03
REFINE_CLIP = (0.88, 1.12)
REFINE_SAME = 0.04
#: 加语速组合：整体语速偏了 8% 以上，语速最多改 10%
SPEED_ARM_DEV = 0.08
SPEED_ARM_CLIP = (0.9, 1.1)
#: 第 1 轮以后最多再加几种组合（更稳的设置 2 种 + 改语速 1 种）：完整打分的名额先给它们留着
EXTRA_ARMS_MAX = 3
#: 已经有版本了、后面却连着这么多次请求什么都没拿到（出错）：不再试，用已经有的里面最好的
EMPTY_STREAK_STOP = 4
STORE_FILE = "cands.json"
STORE_EMB = "cands.npz"
STORE_VERSION = 1

#: 第 1 轮的组合（设计方案 §1.7）：(第几条参考, 第几种生成设置, 第几种辅助参考个数)
#: A1 (r1,P0,辅助3) A2 (r1,P1,辅助3) A3 (r1,P0,辅助0) A4 (r2,P0,辅助3) A5 (r2,P1,辅助3) A6 (r3,P0,辅助3)
ARM_TEMPLATES: Tuple[Tuple[int, int, int], ...] = ((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), (1, 1, 0), (2, 0, 0))
PHASE1_ARMS: Dict[str, Tuple[int, ...]] = {"high": (0, 1, 2, 3, 4, 5), "mid": (0, 1, 2, 3, 4, 5),
                                           "low": (0, 1, 2, 3, 4), "none": (0, 1, 3)}


# ============================================================================ 参考录音
def pool_from_bank(bank: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """参考录音库里的录音（「一模一样」挑参考用）。"""
    out = []
    for e in (bank or {}).get("entries") or []:
        if isinstance(e, dict) and e.get("id") and e.get("text") and e.get("path"):
            out.append(dict(e, _bank=True))
    return out


def pool_from_refs(refs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """还没有参考录音库时（或库是空的）：用 references.json 里挑好的那几条，补上挑参考要用的特征。"""
    from voicetwin.style.twin_profile import en_share

    out = []
    for r in refs:
        if not r.get("id") or not r.get("path"):
            continue
        text = str(r.get("text") or "")
        out.append({"id": str(r["id"]), "path": r["path"], "text": text, "lang": r.get("lang", "zh"),
                    "kind": r.get("kind", "statement"), "syllables": syllable_count(text),
                    "en_ratio": round(en_share(text), 4), "source": str(r.get("source") or ""),
                    "dur": r.get("duration"), "para_initial": False, "max_pause": 0.0,
                    "base": float(r.get("score") or 0.0), "_bank": False})
    return out


def pool_signature(pool: Sequence[Dict[str, Any]], bank: Optional[Dict[str, Any]] = None) -> str:
    """参考录音的指纹（缓存键用）：参考录音库的 bank_sig；用 references.json 时按 id + 文字算。"""
    if bank and bank.get("bank_sig") and any(e.get("_bank") for e in pool):
        return str(bank["bank_sig"])
    return "refs:" + short_hash(sorted(f"{e['id']}|{e.get('text', '')}" for e in pool), n=12)


def _z(values: Dict[str, float]) -> Dict[str, float]:
    if not values:
        return {}
    arr = np.asarray(list(values.values()), dtype=np.float64)
    sd = float(arr.std())
    mu = float(arr.mean())
    return {k: ((float(v) - mu) / sd if sd > 1e-12 else 0.0) for k, v in values.items()}


def prior_scores(pool: Sequence[Dict[str, Any]], audition: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """每条参考录音的「先验」z 分数：有试听结果（P8：用没参加训练的录音试听过）时 = 试听的 z 分数往原来挑参考的分数的
    z 分数收缩一半；没有试听时就是原来分数的 z 分数。"""
    base = _z({e["id"]: float(e.get("base") or 0.0) for e in pool})
    aud = {k: float(v) for k, v in (audition or {}).items()
           if isinstance(v, (int, float)) and math.isfinite(float(v)) and k in base}
    az = _z(aud)
    return {k: (0.5 * az[k] + 0.5 * b if k in az else b) for k, b in base.items()}


def _kind_eff(seg: Any) -> str:
    """一句长话拆成几段时，只有最后一段用这句话的句型（问句的语气在最后），前面几段按陈述句。"""
    return "statement" if getattr(seg, "pause_after", "") == "clause" else (getattr(seg, "kind", "") or "statement")


def _seg_features(seg: Any, para_initial: bool = False) -> Tuple[int, float, str, bool]:
    from voicetwin.style.twin_profile import en_share

    return syllable_count(seg.text), en_share(seg.text), _kind_eff(seg), bool(para_initial)


def match_score(entry: Dict[str, Any], seg: Any, prior: Dict[str, float], para_initial: bool = False,
                feats: Optional[Tuple[int, float, str, bool]] = None) -> float:
    """这条录音当这句话的参考合不合适（设计方案 §1.5 第 2 条）。feats：这句话的特征（挑很多条时先算好）。"""
    syl_seg, en_seg, kind_eff, para = feats if feats is not None else _seg_features(seg, para_initial)
    syl_ref = int(entry.get("syllables") or syllable_count(entry.get("text", "")))
    en_ref = float(entry.get("en_ratio") or 0.0)
    m = 1.2 * float(entry.get("kind", "statement") == kind_eff)
    m -= 1.0 * abs(math.log((syl_ref + 1.0) / (syl_seg + 1.0)))
    m -= 1.5 * abs(en_ref - en_seg)
    m += 0.3 * float(bool(entry.get("para_initial")) == para)
    m += 1.0 * float(prior.get(entry["id"], 0.0))
    m -= 0.3 * float(float(entry.get("max_pause") or 0.0) > 0.9)
    return m


def _norm_text(entry: Dict[str, Any]) -> str:
    """录音文字去标点、转简体以后的样子（比较「是不是同一句话」用；算一次记在这条录音上）。"""
    got = entry.get("_norm")
    if got is None or entry.get("_norm_of") != entry.get("text"):
        got = normalize_for_cer(entry.get("text", ""))
        entry["_norm"], entry["_norm_of"] = got, entry.get("text")
    return got


def shortlist_refs(seg: Any, bank: Sequence[Dict[str, Any]], prior: Dict[str, float], R: int,
                   forced: Optional[Dict[str, Any]] = None, para_initial: bool = False) -> List[Dict[str, Any]]:
    """给这句话挑 R 条参考录音：最合适的；再挑一条别的视频里的（不比第一名差 1.0 以上）；再按顺序往下挑。
    这句话里英文占 15% 以上时，至少有一条参考里英文也占 15% 以上（有的话）。老师自己指定的参考优先（只用它）。"""
    if forced is not None:
        return [forced]
    norm = normalize_for_cer(seg.text)
    feats = _seg_features(seg, para_initial)
    scored = sorted(((match_score(e, seg, prior, feats=feats), e) for e in bank if _norm_text(e) != norm),
                    key=lambda p: (-p[0], str(p[1]["id"])))
    if not scored:
        return []
    R = max(1, int(R))
    top_m, top = scored[0]
    picks = [top]
    if R >= 2:
        other = next((e for m, e in scored[1:] if e.get("source") and e.get("source") != top.get("source")
                      and m >= top_m - 1.0), None)
        if other is not None:
            picks.append(other)
    for _, e in scored[1:]:
        if len(picks) >= R:
            break
        if e not in picks:
            picks.append(e)
    if feats[1] >= 0.15 and not any(float(e.get("en_ratio") or 0.0) >= 0.15 for e in picks):
        en = next((e for _, e in scored if float(e.get("en_ratio") or 0.0) >= 0.15), None)
        if en is not None:
            picks[-1] = en
    return picks


def aux_set(main: Dict[str, Any], bank: Sequence[Dict[str, Any]], prior: Dict[str, float], n: int
            ) -> List[Dict[str, Any]]:
    """主参考的辅助参考（融合音色）：先验分数最高的 n 条，同语言、陈述句、别的视频、4.0~9.8 秒、不是主参考本身。"""
    if n <= 0:
        return []
    out = []
    for e in bank:
        if e["id"] == main["id"] or e.get("lang") != main.get("lang") or e.get("kind", "statement") != "statement":
            continue
        if main.get("source") and e.get("source") == main.get("source"):
            continue
        dur = e.get("dur")
        if isinstance(dur, (int, float)) and not 4.0 <= float(dur) <= 9.8:
            continue
        out.append(e)
    out.sort(key=lambda e: (-float(prior.get(e["id"], 0.0)), str(e["id"])))
    return out[:n]


def find_forced(reference: str, pool: Sequence[Dict[str, Any]], refs: Sequence[Dict[str, Any]]
                ) -> Optional[Dict[str, Any]]:
    """老师指定的参考（id 或路径）：先在参考录音库里找，再在 references.json 里找；找不到返回 None。"""
    if not reference:
        return None
    for e in pool:
        if e["id"] == reference or e.get("path") == reference:
            return e
    got = pool_from_refs([r for r in refs if r.get("id") == reference or r.get("path") == reference])
    return got[0] if got else None


# ============================================================================ 组合
@dataclass(frozen=True)
class Arm:
    """一种组合：参考录音 × 生成设置 × 辅助参考几条 × 语速倍数（× 模型，以后两个模型都留着时用）。"""
    ref_id: str
    preset_idx: int
    aux_n: int
    speed_mult: float = 1.0
    ckpt: Optional[str] = None

    def label(self, refs: Sequence[Dict[str, Any]] = ()) -> str:
        ids = [r["id"] for r in refs]
        no = f"参考{ids.index(self.ref_id) + 1}" if self.ref_id in ids else f"参考{self.ref_id}"
        preset = "更稳的设置" if self.preset_idx == RESCUE else f"设置{self.preset_idx + 1}"
        text = f"{no}·{preset}·辅助{self.aux_n}"
        if abs(self.speed_mult - 1.0) > 1e-9:
            text += f"·语速×{self.speed_mult:.3f}"
        return text

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


def plan_arms(tier: str, refs: Sequence[Dict[str, Any]], aux_by_ref: Dict[str, List[Dict[str, Any]]],
              n_presets: int = 2, aux_options: Sequence[Any] = (3, 0)) -> List[Arm]:
    """第 1 轮要试的组合（按显卡：high/mid A1~A6、low A1~A5、没有 N 卡 A1、A2、A4）。辅助参考实际只有几条就按几条算：
    引擎不支持辅助参考（例如测试引擎）时 A1 和 A3 一模一样，只留一个。同一条参考的排在一起。"""
    arms: List[Arm] = []
    for t in PHASE1_ARMS.get(tier, PHASE1_ARMS["mid"]):
        r_i, p_i, a_i = ARM_TEMPLATES[t]
        if r_i >= len(refs):
            continue
        ref_id = str(refs[r_i]["id"])
        try:
            want = int(list(aux_options)[a_i]) if a_i < len(list(aux_options)) else 0
        except (TypeError, ValueError):
            want = 0
        arm = Arm(ref_id, p_i if p_i < max(1, n_presets) else 0, max(0, min(want, len(aux_by_ref.get(ref_id) or []))))
        if arm not in arms:
            arms.append(arm)
    return arms


# ============================================================================ 候选
@dataclass(eq=False)
class SearchCand:
    """一个版本。wav 是引擎原样给的声音（还没去首尾：打分要用首尾的静音估计底噪）。"""
    wav: np.ndarray
    sr: int
    arm: Arm
    seed: int                 # 这个版本的种子（一个一个生成时 = 请求的种子 + 第几个 × SEED_STEP）
    req_seed: int             # 那次请求的种子
    row: int                  # 那次请求里的第几个（从 0 数起）
    req_no: int               # 第几次请求（从 0 数起）
    req_n: int                # 那次请求要了几个
    speed: float              # 发给引擎的语速
    mode: str = "single"      # batch（一次同时生成好几个）| single（一个一个生成）
    quick: Any = None
    score: Optional[Score] = None
    stored: bool = False      # 以前存下来的（重新生成时一起比）
    refined: bool = False     # 「同一个版本只改了语速」
    refine_of: Optional["SearchCand"] = None
    model: str = ""
    embs: Dict[str, np.ndarray] = field(default_factory=dict)
    speech_sec: Optional[float] = None  # 人声几秒（没舍入；和声纹一起存，重新打分时短句子的标准不变）
    #: 打分用的声音：最后放进音频里的那一段（去首尾）两边补 0.3 秒数字静音（Narrator._analysis）；wav 还是引擎原样的（存下来用）
    awav: Optional[np.ndarray] = field(default=None, repr=False)
    empty: bool = False                 # 去首尾以后是空的（整段只有底噪）：不能拿来用

    @property
    def scored_wav(self) -> np.ndarray:
        return self.awav if self.awav is not None else self.wav

    @property
    def round(self) -> int:
        return self.req_no

    @property
    def total(self) -> float:
        return float(self.score.total) if self.score is not None else float("-inf")


@dataclass
class Outcome:
    best: SearchCand
    cands: List[SearchCand]          # 完整打过分的版本（这次的 + 以前存下的），按档次和综合分排
    tries: int                       # 这次新试了几个版本（不算语速微调）
    met: bool
    arms: List[Dict[str, Any]]
    stats: Dict[str, Any]
    keep: List[SearchCand] = field(default_factory=list)  # 要留下来的顺序（挑出来的那个第一，见 keep_order）


@dataclass
class _Job:
    arm: Arm
    n: int
    seed: int
    speed: float
    no: int
    ref: Dict[str, Any]
    ref_audio: Path
    aux_paths: List[Path]
    sampling: Dict[str, Any]
    refine_of: Optional[SearchCand] = None
    row: int = 0


# ============================================================================ 每次同时生成几个
class BatchTuner:
    """每次同时生成几个（设计方案 §1.6）：开头 6 次请求轮流用 B0/2 和 B0，按实测「每秒几个版本」选——
    大的至少快 5% 才用大的（Windows 显存溢出到内存时只会变慢、不报错，这样能发现）。整个生成过程只选一次。"""

    def __init__(self, b0: int, enabled: bool = True, trials: int = 6):
        self.b0 = max(1, int(b0))
        self.small = max(1, self.b0 // 2)
        self.enabled = bool(enabled) and self.small < self.b0
        self.trials = int(trials)
        self.assigned = 0
        self.records: List[Tuple[int, int, float]] = []
        self.choice: Optional[int] = None if self.enabled else self.b0
        self.result: Dict[str, Any] = {}

    def next_b(self) -> int:
        if self.choice is not None:
            return self.choice
        if self.assigned >= self.trials:
            return self.b0
        b = self.small if self.assigned % 2 == 0 else self.b0
        self.assigned += 1
        return b

    def record(self, asked: int, pieces: int, seconds: float) -> None:
        if self.choice is not None or pieces <= 0 or not seconds or seconds <= 0:
            return
        self.records.append((int(asked), int(pieces), float(seconds)))
        if len(self.records) < self.trials:
            return
        groups: Dict[str, List[Tuple[int, float]]] = {"small": [], "large": []}
        for asked_b, got, secs in self.records:
            groups["small" if asked_b <= self.small else "large"].append((got, secs))
        cps = {k: (sum(g for g, _ in v) / sum(s for _, s in v)) if v and sum(s for _, s in v) > 0 else None
               for k, v in groups.items()}
        if cps["small"] is None or cps["large"] is None:
            self.choice = self.b0
        else:
            self.choice = self.b0 if cps["large"] >= 1.05 * cps["small"] else self.small
        self.result = {"small": self.small, "large": self.b0, "cps_small": cps["small"], "cps_large": cps["large"],
                       "chosen": self.choice}
        if cps["small"] is not None and cps["large"] is not None:
            log.info(f"实测：每次同时生成 {self.small} 个，每秒 {cps['small']:.2f} 个版本；{self.b0} 个，每秒 "
                     f"{cps['large']:.2f} 个——以后每次同时生成 {self.choice} 个")


# ============================================================================ 生成线程
class _Producer(threading.Thread):
    """生成线程：一个一个地发请求（只有它跟合成引擎说话），结果放进最多 2 个的队列，主线程同时给上一批打分。
    出错（包括停止按钮）都交给主线程，在主线程里原样再抛出来（同一个异常、同样的话）。"""

    def __init__(self, work: Callable[[Any], Any]):
        super().__init__(name="vt-identical-gen", daemon=True)
        self._work = work
        self.jobs: "queue.Queue[Any]" = queue.Queue()
        self.results: "queue.Queue[Any]" = queue.Queue(maxsize=2)
        self._halt = threading.Event()

    def submit(self, job: Any) -> None:
        self.jobs.put(job)

    def run(self) -> None:
        while not self._halt.is_set():
            try:
                job = self.jobs.get(timeout=0.05)
            except queue.Empty:
                continue
            if job is None:
                return
            try:
                _check_cancel()
                item = (job, self._work(job), None)
            except BaseException as exc:  # noqa: B036 - 停止按钮（TaskCancelled）也交给主线程
                item = (job, None, exc)
            while not self._halt.is_set():
                try:
                    self.results.put(item, timeout=0.05)
                    break
                except queue.Full:
                    continue
            if item[2] is not None and not isinstance(item[2], Exception):
                return  # 点了停止：后面的请求不再发

    def get(self, check: Optional[Callable[[], None]] = None) -> Tuple[Any, Any]:
        """等下一个结果。生成线程里出的错在这里原样抛出来；check：等的时候顺便检查停止按钮。"""
        while True:
            if check is not None:
                check()
            try:
                job, out, exc = self.results.get(timeout=0.05)
            except queue.Empty:
                if not self.is_alive() and self.results.empty():
                    raise RuntimeError("生成线程意外停止了")
                continue
            if exc is not None:
                raise exc
            return job, out

    def close(self) -> None:
        """停下：正在发的那个请求做完（引擎那边停不下来），后面的不再发；等线程结束。"""
        self._halt.set()
        self.jobs.put(None)
        self.join()
        while True:
            try:
                self.results.get_nowait()
            except queue.Empty:
                break


# ============================================================================ 留下来的版本
def store_dir(cache_dir: Path, pool_key: str) -> Path:
    return Path(cache_dir) / "segments" / pool_key[:2] / f"{pool_key}.cands"


def store_candidates(folder: Path, cands: Sequence[SearchCand], k: int = 6, judge_sig: str = "",
                     extra: Optional[Dict[str, Any]] = None) -> int:
    """把排在最前面的 k 个版本存下来：c{i}.flac（引擎原样的声音，无损）+ cands.json（分数、组合、种子、第几行、模型、
    人声几秒）+ cands.npz（每个声纹模型的声纹）。cands 的顺序就是存的顺序（挑出来的那个排第一，见 IdenticalSearch.keep_order）。
    先写到临时文件夹再换上去；存不了不影响生成（返回存了几个）。"""
    from voicetwin.utils.audio import save_audio

    folder = Path(folder)
    keep = [c for c in cands if c.score is not None][: max(0, int(k))]
    if not keep:
        return 0
    tmp = folder.with_name(folder.name + f".tmp{uuid.uuid4().hex[:6]}")
    try:
        tmp.mkdir(parents=True, exist_ok=True)
        items = []
        embs: Dict[str, np.ndarray] = {}
        for i, c in enumerate(keep):
            name = f"c{i}.flac"
            save_audio(tmp / name, c.wav, c.sr, subtype="PCM_16")
            for m, v in (c.embs or {}).items():
                embs[f"c{i}|{m}"] = np.asarray(v, dtype=np.float32)
            items.append({"file": name, "sr": int(c.sr), "seed": int(c.seed), "req_seed": int(c.req_seed),
                          "row": int(c.row), "req_no": int(c.req_no), "req_n": int(c.req_n), "speed": float(c.speed),
                          "mode": c.mode, "arm": c.arm.to_dict(), "score": c.score.to_dict(), "model": c.model,
                          "refined": bool(c.refined), "judge_sig": judge_sig, "embs": sorted(c.embs or {}),
                          "speech_sec": c.speech_sec, "f0_med": _f0_of(c), "empty": bool(c.empty)})
        if embs:
            np.savez(tmp / STORE_EMB, **embs)
        (tmp / STORE_FILE).write_text(json.dumps({"version": STORE_VERSION, "items": items, **(extra or {})},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        os.replace(tmp, folder)
        return len(keep)
    except Exception as exc:  # noqa: BLE001 - 存不了（硬盘满了等）：这句照样用，只是以后不能拿它们比
        log.debug(f"留下的版本存不了：{exc}")
        shutil.rmtree(tmp, ignore_errors=True)
        return 0


def _f0_of(c: SearchCand) -> Optional[float]:
    """这个版本（最后放进音频的那一段）的音高中位数（Hz）：整篇再挑一遍时比前后两句的音调变化用。
    和量你本人录音的 f0_med_hz 是同一个算法；量不出来是 None（这一项不比）。"""
    try:
        from voicetwin.style.twin_profile import f0_median_hz

        val = f0_median_hz(c.scored_wav, c.sr)
    except Exception:  # noqa: BLE001
        return None
    return round(float(val), 3) if val else None


def store_items(folder: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, np.ndarray]]]:
    """只读存下来的版本的记录和声纹（不读声音，整篇再挑一遍时每句都要读、要快）：(items, {文件名: {模型: 声纹}})。"""
    folder = Path(folder)
    try:
        data = json.loads((folder / STORE_FILE).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return [], {}
    if not isinstance(data, dict) or data.get("version") != STORE_VERSION:
        return [], {}
    items = [it for it in (data.get("items") or []) if isinstance(it, dict) and it.get("file")]
    embs: Dict[str, Dict[str, np.ndarray]] = {}
    if (folder / STORE_EMB).exists():
        try:
            with np.load(folder / STORE_EMB) as z:
                for k in z.files:
                    key, _, member = k.partition("|")
                    embs.setdefault(key, {})[member] = np.asarray(z[k], dtype=np.float32)
        except Exception:  # noqa: BLE001
            embs = {}
    out = {}
    for it in items:
        own = embs.get(Path(str(it["file"])).stem) or {}  # c3.flac 的声纹存成 c3|模型名
        out[it["file"]] = {m: v for m, v in own.items() if m in (it.get("embs") or [])}
    return items, out


def has_stored(folder: Path) -> bool:
    """这句话有没有留下来的版本（只看 cands.json，不读声音：整篇开始前每句都要查，要快）。
    声音读不了的，到时候重新排不成，再启动合成引擎重新生成。"""
    try:
        data = json.loads((Path(folder) / STORE_FILE).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return False
    return isinstance(data, dict) and data.get("version") == STORE_VERSION and bool(data.get("items"))


def store_info(folder: Path) -> Dict[str, Any]:
    """存下来的版本的其它记录（这句话一共试了几个等），读不了是空的。"""
    try:
        data = json.loads((Path(folder) / STORE_FILE).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return {k: v for k, v in data.items() if k != "items"} if isinstance(data, dict) else {}


def load_candidates(folder: Path) -> List[Dict[str, Any]]:
    """读存下来的版本：[{"wav", "sr", "seed", "row", "arm", "score", "embs", ...}]；读不了的跳过。"""
    folder = Path(folder)
    path = folder / STORE_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    if not isinstance(data, dict) or data.get("version") != STORE_VERSION:
        return []
    embs: Dict[str, np.ndarray] = {}
    if (folder / STORE_EMB).exists():
        try:
            with np.load(folder / STORE_EMB) as z:
                embs = {k: z[k] for k in z.files}
        except Exception:  # noqa: BLE001
            embs = {}
    out = []
    for i, it in enumerate(data.get("items") or []):
        try:
            wav, sr = load_audio(folder / it["file"])
        except Exception:  # noqa: BLE001
            continue
        own = {m: embs[f"c{i}|{m}"] for m in it.get("embs") or [] if f"c{i}|{m}" in embs}
        out.append(dict(it, wav=wav, sr=int(sr), emb=own))
    return out


# ============================================================================ 搜索
def _stat_seconds(stats: Any) -> Optional[float]:
    """引擎记的每种数量一共用了几秒（不算自检的请求）；没有这个记录时 None。"""
    if not isinstance(stats, dict) or not isinstance(stats.get("by_batch"), dict):
        return None
    return float(sum(float((v or {}).get("seconds") or 0.0) for v in stats["by_batch"].values()))


class IdenticalSearch:
    """一句话的搜索。用 Narrator 的打分器、门槛、进度；引擎由生成线程（或没有 N 卡时主线程）调用。"""

    def __init__(self, narrator: Any):
        self.n = narrator

    # ------------------------------------------------------------------ 设置
    @property
    def preset(self) -> Dict[str, Any]:
        return self.n.preset

    def _int(self, key: str, default: int) -> int:
        try:
            return int(self.preset.get(key, default))
        except (TypeError, ValueError):
            return default

    def pipeline_on(self) -> bool:
        opt = self.preset.get("pipeline", "auto")
        if isinstance(opt, str) and opt.strip().lower() in ("auto", ""):
            return self.n.tier != "none"
        if isinstance(opt, str):
            return opt.strip().lower() in ("true", "on", "yes", "1")
        return bool(opt)

    def samplings(self) -> List[Dict[str, Any]]:
        presets = [p for p in (self.preset.get("presets") or []) if isinstance(p, dict)]
        return presets or [{"temperature": 1.0, "top_k": 15, "top_p": 1.0}]

    def _sampling(self, idx: int) -> Dict[str, Any]:
        if idx == RESCUE:
            r = self.preset.get("rescue_preset")
            return dict(r) if isinstance(r, dict) else {"temperature": 0.6, "top_k": 15, "top_p": 0.8}
        s = self.samplings()
        return dict(s[idx] if 0 <= idx < len(s) else s[0])

    # ------------------------------------------------------------------ 挑最好的
    def _key(self, c: SearchCand) -> Tuple[bool, bool, float]:
        return (bool(self.n._cer_ok(c, self.lang)), bool(self.n._meets_targets(c, self.seg)), c.total)

    def _non_timbre(self, c: SearchCand) -> float:
        fn = getattr(self.scorer, "non_timbre", None)
        return float(fn(c.score)) if callable(fn) else c.total

    def _pick_pool(self, cands: Sequence[SearchCand]) -> Tuple[List[SearchCand], Dict[int, Tuple[bool, bool, float]]]:
        """pick() 从哪些里挑：几乎没声音的不要；不够像（< 85%，有可靠声纹打分时）的不要（都不够像时照样比）。"""
        full = [c for c in cands if c.score is not None]
        alive = [c for c in full if "几乎没有声音" not in c.score.issues] or full
        pool = [c for c in alive if self.n._pct_ok(c)] or alive
        return pool, {id(c): self._key(c) for c in pool}

    def _top(self, cands: Sequence[SearchCand]) -> Optional[SearchCand]:
        """pick() 里定标准的那个：档次最高（读对了、达到全部标准）、综合分最高的；「差不多一样高」从它往下算。"""
        pool, keys = self._pick_pool(cands)
        return max(pool, key=lambda c: keys[id(c)]) if pool else None

    def pick(self, cands: Sequence[SearchCand]) -> Optional[SearchCand]:
        """和最后真正用的一样挑：几乎没声音的不要；不够像（< 85%，有可靠声纹打分时）的排后面；
        读对的 > 达到全部标准的 > 综合分高的；综合分差不到 0.02 时按时长、音调、读得准不准挑。"""
        pool, keys = self._pick_pool(cands)
        if not pool:
            return None
        top = max(pool, key=lambda c: keys[id(c)])
        cls = keys[id(top)][:2]
        group = [c for c in pool if keys[id(c)][:2] == cls and c.total >= top.total - TIE_EPS]
        return max(group, key=lambda c: (round(self._non_timbre(c), 9), c.total))

    def keep_order(self, best: SearchCand, cands: Sequence[SearchCand],
                   left: Optional[Sequence[SearchCand]] = None) -> List[SearchCand]:
        """要留下来的版本的顺序：挑出来的那个排第一，定「差不多一样高」标准的那个（档次最高、综合分最高的）第二，
        其余按档次和综合分。只留前 6 个时挑出来的那个也一定在里面：分数不变时从留下来的里重新挑还是它，
        重新生成时它也一起比。left：挑的时候实际是从哪些里挑的（去掉了去首尾以后是空的那些）。"""
        full = [c for c in cands if c.score is not None]
        top = self._top(left if left is not None else full)
        head = [best] + ([top] if top is not None and top is not best else [])
        return head + sorted((c for c in full if all(c is not h for h in head)), key=self._value, reverse=True)

    def _value(self, c: Optional[SearchCand]) -> float:
        if c is None:
            return float("-inf")
        cer_ok, met, total = self._key(c)
        return (int(cer_ok) + int(met)) * CLASS_GAP + total

    # ------------------------------------------------------------------ 一句
    def _setup(self, seg: Any, plan: Any) -> None:
        n = self.n
        self.seg, self.plan = seg, plan
        self.lang = send_lang(seg.text, seg.lang)
        self.mult = n._speed_multiplier()
        self.scorer = n.scorer
        self.B0 = max(1, int(n.n_candidates))
        self.min_c, self.max_c = int(n.min_candidates), int(n.max_candidates)
        self.full_top = max(1, self._int("full_score_top", 12))
        self.full_max = max(1, self._int("full_score_max", 24))
        self.cands: List[SearchCand] = []        # 这次新试的（不算语速微调）
        self.pool: List[SearchCand] = []         # 拿来挑的：这次的 + 以前存下的 + 语速微调的
        self.req_no = 0
        self.requests = 0
        self.empty = 0
        self.n_full = 0
        self.last_exc: Optional[BaseException] = None
        self.last_mode, self.last_batch = "", 0
        self.batches: List[int] = []
        self.refined: List[SearchCand] = []
        self.extra_done = False                  # 第 1 轮以后要不要加组合已经定了
        self.pending: List[Arm] = []             # 这一轮还没回来的请求的组合（完整打分给还没出场的留名额）
        self.left: List[SearchCand] = []         # 挑出来的那个是从哪些里挑的（_best_nonempty）
        self.model = str(getattr(n.backend, "model_id", lambda: "")())

    def run(self, seg: Any, plan: Any, force: bool = False) -> Outcome:
        n = self.n
        self._setup(seg, plan)
        t0 = time.monotonic()
        self.seed0 = n.base_seed + seg.index * SENT_SEED_STEP + (random.randint(1, 10_000_000) if force else 0)
        self.tmp = n.project.cache_dir / "tmp" / f"id_{plan.key}_{uuid.uuid4().hex[:6]}"
        self.tmp.mkdir(parents=True, exist_ok=True)
        stored = self.load_stored(seg, plan) if force else []
        self.pool += stored
        self.producer: Optional[_Producer] = None
        stop = ""
        try:
            if self.pipeline_on():
                self.producer = _Producer(self._work)
                self.producer.start()
            stop = self._search()
            if stop != "gave_up":
                self._refine()
        finally:
            if self.producer is not None:
                self.producer.close()
            shutil.rmtree(self.tmp, ignore_errors=True)
        best = self._best_nonempty()
        if best is None:
            exc = self.last_exc
            why = self._reason(exc) if exc is not None else "生成的音频是空的"
            raise RuntimeError(f"第 {seg.index + 1} 句没能生成（原因：{why}）：{seg.text[:30]}") from exc
        met = bool(n._meets_targets(best, seg))
        full = sorted([c for c in self.pool if c.score is not None], key=self._value, reverse=True)
        stats = {"requests": self.requests, "candidates": len(self.cands), "full_scored": self.n_full,
                 "stored_competed": len(stored), "refine_requests": len(self.refined),
                 "refined": sum(1 for c in self.refined if c.refined), "batches": self.batches,
                 "pipeline": self.producer is not None, "stop": stop or "max",
                 "seconds": round(time.monotonic() - t0, 2), "chosen_arm": best.arm.label(plan.refs),
                 "chosen_stored": best.stored, "chosen_refined": best.refined}
        return Outcome(best, full, len(self.cands), met, self._arm_rows(), stats,
                       keep=self.keep_order(best, full, self.left))

    def _best_nonempty(self) -> Optional[SearchCand]:
        """挑出来的那个去掉首尾以后不能是空的（整段都是底噪）；是空的就换下一个。去首尾和最后放进音频时一样（Narrator._trim）。"""
        left = [c for c in self.pool if c.score is not None]
        while left:
            best = self.pick(left)
            if best is None:
                return None
            if self.n._trim(best.wav, best.sr).size > 0:
                self.left = left
                return best
            left = [c for c in left if c is not best]
        return None

    def _arm_rows(self) -> List[Dict[str, Any]]:
        rows: Dict[Arm, Dict[str, Any]] = {}
        for c in self.cands + self.refined:
            r = rows.setdefault(c.arm, {"arm": c.arm.label(self.plan.refs), **c.arm.to_dict(), "n": 0, "full": 0,
                                        "best_total": None})
            r["n"] += 1
            if c.score is not None:
                r["full"] += 1
                r["best_total"] = round(max(r["best_total"] if r["best_total"] is not None else -1e9, c.total), 4)
        return list(rows.values())

    # ------------------------------------------------------------------ 几轮
    def _search(self) -> str:
        arms1 = list(self.plan.arms)
        self._run(self._jobs(arms1, phase1=True))
        if self._gave_up():
            return "gave_up"
        stop = self._stop()
        if stop:
            return stop
        extra = self._extra_arms(arms1)
        self.extra_done = True
        if extra:
            self._run(self._jobs(extra))
            if self._gave_up():
                return "gave_up"
            stop = self._stop()
            if stop:
                return stop
        self._continue_note()
        self._run(self._jobs(self._top_arms(2) or arms1[:1]))
        while True:
            if self._gave_up():
                return "gave_up"
            stop = self._stop()
            if stop:
                return stop
            self._continue_note()
            jobs = self._jobs((self._top_arms(1) or arms1)[:1])
            if not jobs:
                return "max"
            self._run(jobs)

    def _gave_up(self) -> bool:
        return self.empty >= 2 and not self.cands

    def _stuck(self) -> bool:
        """已经有版本了，后面的请求却一直什么都没拿到：不再试（不然会一直试下去），用已经有的里面最好的。"""
        if self.cands and self.empty >= EMPTY_STREAK_STOP:
            log.warning(f"  第 {self.seg.index + 1} 句：连着 {self.empty} 次请求都没生成出来，"
                        f"先用已经试过的 {len(self.cands)} 个版本里最好的")
            return True
        return False

    def _stop(self) -> str:
        """停下的原因（还要接着试时是空字符串）。"""
        if len(self.cands) >= self.max_c:
            return "max"
        if self._stuck():
            return "errors"
        full = [c for c in self.pool if c.score is not None]
        best = self.pick(full)
        if best is None or len(self.cands) < self.min_c:
            return ""
        if not self.n._meets_targets(best, self.seg, "search"):
            return ""
        return "target" if self._flat(full) else ""

    def _flat(self, full: List[SearchCand]) -> bool:
        """最近 plateau（8）个新版本没让最好的综合分再高 plateau_eps（0.02）。试过的还不到 8 个时看已经试过的这几个。"""
        plateau, eps = int(self.n.plateau), float(self.n.plateau_eps)
        w = min(plateau, len(self.cands) - 1)
        if plateau <= 0 or w <= 0:
            return True
        recent = {id(c) for c in self.cands[-w:]}
        before = [c for c in full if id(c) not in recent]
        return self._value(self.pick(full)) - self._value(self.pick(before)) < eps

    def _top_arms(self, k: int) -> List[Arm]:
        """综合分最好的 k 种组合（每种组合按它最好的两个版本的平均）。"""
        by: Dict[Arm, List[float]] = {}
        for c in self.cands:
            if c.score is not None:
                by.setdefault(c.arm, []).append(c.total)
        rank = sorted(by.items(), key=lambda kv: -float(np.mean(sorted(kv[1], reverse=True)[:2])))
        return [a for a, _ in rank[:k]]

    def _extra_arms(self, arms1: List[Arm]) -> List[Arm]:
        n = self.n
        full = [c for c in self.cands if c.score is not None]
        extra: List[Arm] = []
        if n.use_asr and full and not any(n._cer_ok(c, self.lang) for c in full):
            for r in self.plan.refs[:2]:
                aux = len(self.plan.aux_by_ref.get(r["id"]) or [])
                top_aux = max((a.aux_n for a in arms1 if a.ref_id == r["id"]), default=0)
                arm = Arm(str(r["id"]), RESCUE, min(aux, top_aux))
                if arm not in extra:
                    extra.append(arm)
            i, total_n = n._pos
            n._progress(self._frac(), f"[{i + 1}/{total_n}] 有字读错了，换更稳的生成设置再试")
        ratios = [c.score.voiced / c.score.expected for c in full if c.score.expected and c.score.voiced]
        if ratios:
            med = float(np.median(ratios))
            if abs(med - 1.0) > SPEED_ARM_DEV:
                base = (self._top_arms(1) or arms1)[0]
                mult = float(np.clip(med, *SPEED_ARM_CLIP))
                extra.append(dataclasses.replace(base, speed_mult=round(base.speed_mult * mult, 4)))
        return extra

    # ------------------------------------------------------------------ 请求
    def _job(self, arm: Arm, size: int, *, seed: Optional[int] = None, speed: Optional[float] = None,
             refine_of: Optional[SearchCand] = None, row: int = 0) -> _Job:
        from voicetwin.data.references import bank_wav

        n = self.n
        ref = next((r for r in self.plan.refs if str(r["id"]) == arm.ref_id), None) or \
            next((e for e in getattr(self.plan, "pool", []) if str(e["id"]) == arm.ref_id), self.plan.refs[0])
        aux = (self.plan.aux_by_ref.get(arm.ref_id) or [])[:arm.aux_n]

        def audio(e: Dict[str, Any]) -> Path:
            return bank_wav(n.project, e) if e.get("_bank") else n.project.abspath(e["path"])

        if seed is None:
            # 第 j 次请求的种子：每次请求占 B0 个种子位置（一个一个生成时第 k 个用 +k × SEED_STEP），
            # 和别的请求的版本不会撞上同一个种子（P4 记录里留下的问题）
            seed = self.seed0 + self.req_no * self.B0 * SEED_STEP
            no = self.req_no
            self.req_no += 1
        else:
            no = refine_of.req_no if refine_of is not None else self.req_no
        if speed is None:
            speed = float(min(2.0, max(0.5, self.plan.speed * arm.speed_mult)))
        return _Job(arm=arm, n=max(1, int(size)), seed=int(seed), speed=float(speed), no=no, ref=ref,
                    ref_audio=audio(ref), aux_paths=[audio(a) for a in aux], sampling=self._sampling(arm.preset_idx),
                    refine_of=refine_of, row=row)

    def _jobs(self, arms: Sequence[Arm], phase1: bool = False) -> List[_Job]:
        """这几种组合各发一次请求；一共不超过每句最多试几个。第 1 轮给后面每种组合至少留 1 个。"""
        tuner = self.n._batch_tuner()
        order = {str(r["id"]): k for k, r in enumerate(self.plan.refs)}
        arms = sorted(arms, key=lambda a: (order.get(a.ref_id, 99), -a.aux_n)) if not phase1 else list(arms)
        jobs: List[_Job] = []
        planned = len(self.cands)
        for k, arm in enumerate(arms):
            left = self.max_c - planned
            if left <= 0:
                break
            size = min(int(tuner.next_b()), left)
            if phase1:
                size = max(1, min(size, left - (len(arms) - k - 1)))
            jobs.append(self._job(arm, size))
            planned += size
        return jobs

    def _work(self, job: _Job) -> Dict[str, Any]:
        """真正发请求（生成线程里，或者没有 N 卡时在主线程里）。"""
        backend = self.n.backend
        req = SynthRequest(text=self.seg.text, lang=self.seg.lang, ref_audio=job.ref_audio,
                           ref_text=job.ref.get("text", ""), ref_lang=job.ref.get("lang", "zh"),
                           aux_refs=list(job.aux_paths), seed=job.seed, speed=job.speed,
                           temperature=job.sampling.get("temperature"), top_k=job.sampling.get("top_k"),
                           top_p=job.sampling.get("top_p"))
        stats = getattr(backend, "batch_stats", None)
        before = _stat_seconds(stats)
        t0 = time.monotonic()
        files = backend.synthesize_many(req, job.n, self.tmp)
        wall = time.monotonic() - t0
        after = _stat_seconds(stats)
        secs = (after - before) if (before is not None and after is not None and after > before) else wall
        last = getattr(backend, "last_many", None)
        mode = "batch" if (getattr(backend, "supports_batch", False) and isinstance(last, dict)
                           and last.get("mode") == "batch") else "single"
        return {"files": list(files or []), "seconds": float(secs), "mode": mode}

    def _run(self, jobs: List[_Job]) -> List[SearchCand]:
        """发这几个请求，结果一到就快速打分、挑出来的完整打分。返回拿到的版本。"""
        got: List[SearchCand] = []
        if not jobs:
            return got
        if self.producer is not None:
            for j in jobs:
                self.producer.submit(j)
        # 这一轮还没回来的请求：完整打分的名额给它们的组合留着（包括第 1 轮以后加的组合，见 _reserve）
        self.pending = [j.arm for j in jobs]
        try:
            for j in jobs:
                if self._gave_up():  # 连着 2 次什么都没拿到、又一个版本都没有：后面的不再等（生成线程里排着的作废）
                    break
                try:
                    if self.producer is not None:
                        job, out = self.producer.get(_check_cancel)
                    else:
                        _check_cancel()
                        job, out = j, self._work(j)
                except Exception as exc:  # noqa: BLE001 - 停止按钮不是 Exception，照常传出去
                    self.requests += 1
                    self.pending.remove(j.arm)  # 生成线程按顺序发：出错的就是这一个
                    self._failed(exc)
                    continue
                self.requests += 1
                self.pending.remove(j.arm)
                got += self._absorb(job, out)
        finally:
            self.pending = []
        return got

    def _failed(self, exc: BaseException) -> None:
        self.last_exc = exc
        log.warning(f"  第 {self.seg.index + 1} 句第 {self.requests} 次请求生成失败：{exc}")
        if self._fatal(exc):  # 显存不够（同时生成的数量已经减到 1 也不够）、服务起不来……换个种子也没用
            raise RuntimeError(f"第 {self.seg.index + 1} 句没能生成（原因：{self._reason(exc)}）："
                               f"{self.seg.text[:30]}") from exc
        self.empty += 1

    @staticmethod
    def _fatal(exc: BaseException) -> bool:
        from voicetwin.synth.engine import _is_fatal

        return _is_fatal(exc)

    @staticmethod
    def _reason(exc: Optional[BaseException]) -> str:
        from voicetwin.synth.engine import _reason

        return _reason(exc)

    def _absorb(self, job: _Job, out: Dict[str, Any]) -> List[SearchCand]:
        files = sorted(out.get("files") or [], key=lambda f: f[1])
        if job.refine_of is None:  # 按实测速度选每次同时生成几个（语速微调的请求不算）
            self.n._batch_tuner().record(job.n, len(files), float(out.get("seconds") or 0.0))
        got: List[SearchCand] = []
        for path, row in files:
            try:
                wav, sr = load_audio(path)
            except Exception as exc:  # noqa: BLE001
                log.debug(f"读不了生成的声音：{exc}")
                continue
            finally:
                try:
                    Path(path).unlink()
                except OSError:
                    pass
            if job.refine_of is not None and int(row) != job.row:
                continue
            if wav.size == 0:
                continue
            seed = job.seed if out.get("mode") == "batch" else job.seed + int(row) * SEED_STEP
            c = SearchCand(wav=wav, sr=int(sr), arm=job.arm, seed=int(seed), req_seed=job.seed, row=int(row),
                           req_no=job.no, req_n=job.n, speed=job.speed, mode=str(out.get("mode") or "single"),
                           model=self.model)
            # 打分用最后真正放进音频的那一段（去首尾、两边补 0.3 秒静音），不是引擎原样的声音（设计方案 §1.9 第 1 条）
            c.awav, c.empty = self.n._analysis_pair(wav, int(sr))
            c.quick = self.scorer.quick(c.awav, sr, self.seg.text, self.lang, self.mult)
            got.append(c)
        if job.refine_of is not None:
            return got
        if not got:
            self.empty += 1
            return got
        self.empty = 0
        self.cands += got
        self.pool += got
        self.last_mode, self.last_batch = str(out.get("mode") or "single"), len(files)
        self.batches.append(len(files))
        self._cascade()
        self._note()
        return got

    def _reserve(self) -> int:
        """完整打分的名额要给还没出场的组合留几个（每种组合最好的那个一定要完整打分）：这一轮还没回来的请求的组合
        （第 1 轮的、第 1 轮以后加的），再加上还没决定要不要加的组合（最多 3 种）。"""
        seen = {c.arm for c in self.cands}
        return len({a for a in self.pending if a not in seen}) + (0 if self.extra_done else EXTRA_ARMS_MAX)

    def _cascade(self) -> None:
        """完整打分：每种组合最好的那个、快速分排在前 full_score_top（12）名的；每句最多 full_score_max（24）个，
        而且给还没出场的组合留着名额（保证每种组合至少一个完整打分）。"""
        quick = [c for c in self.cands if c.quick is not None]
        by_arm: Dict[Arm, List[SearchCand]] = {}
        for c in quick:
            by_arm.setdefault(c.arm, []).append(c)
        for group in by_arm.values():
            if not any(c.score is not None for c in group) and self.n_full < self.full_max:
                self._full(max(group, key=lambda c: c.quick.total))
        limit = self.full_max - self._reserve()
        for c in sorted(quick, key=lambda c: -c.quick.total)[:self.full_top]:
            if self.n_full >= limit:
                break
            if c.score is None:
                self._full(c)

    def _full(self, c: SearchCand, count: bool = True) -> None:
        n = self.n
        prepared = getattr(c.quick, "prepared", None)
        wav = c.scored_wav
        try:
            c.score = self.scorer.full(wav, c.sr, self.seg.text, self.lang, self.mult, prepared=prepared,
                                       use_asr=n.use_asr)
        except Exception as exc:
            if not n.use_asr:
                raise
            # 识别校验（查错字）只是帮着挑的：它出错（比如识别模型显存不够）时关掉它接着生成，不能让整篇停下
            log.warning(f"⚠️ 识别校验出错了（{str(exc).splitlines()[0] if str(exc) else type(exc).__name__}），"
                        "后面只按声纹、语速和停顿挑选")
            n.use_asr = False
            c.score = self.scorer.full(wav, c.sr, self.seg.text, self.lang, self.mult, prepared=prepared,
                                       use_asr=False)
        c.score.arm = c.arm.label(self.plan.refs)
        c.score.model = c.model
        if isinstance(prepared, dict):
            c.embs = {k: np.asarray(v, dtype=np.float32) for k, v in (prepared.get("embs") or {}).items()}
            c.speech_sec = prepared.get("seconds")
            prepared["speech"] = {}  # 声纹已经算好了：人声检测的结果不用再留着（人声几秒记在 prepared["seconds"]）
        if count:
            self.n_full += 1

    # ------------------------------------------------------------------ 进度
    def _frac(self) -> float:
        """这一句在整篇进度里走到哪了：按每句最多试几个算（设计方案 §2 P6：进度的分母是 max_candidates）。"""
        lo, hi = self.n._gen_range
        i, total_n = self.n._pos
        k = len(self.cands)
        return lo + (hi - lo) * (i + min(0.95, k / max(self.max_c, 1))) / max(total_n, 1)

    def _note(self) -> None:
        i, total_n = self.n._pos
        best = self.pick(self.pool)
        batch = f"（显卡一次同时生成 {self.last_batch} 个）" if self.last_mode == "batch" else ""
        pct = f"，目前最像你的 {best.score.pct:.1f}%" if best is not None and best.score.pct is not None else ""
        self.n._progress(self._frac(), f"[{i + 1}/{total_n}] 已试 {len(self.cands)} 个版本{batch}{pct}")

    def _continue_note(self) -> None:
        """还要接着试：挑出来的那个已经达到继续找的目标时说一声（只是确认没有更好的）。"""
        best = self.pick(self.pool)
        if best is not None and self.n._meets_targets(best, self.seg, "search"):
            i, total_n = self.n._pos
            self.n._progress(self._frac(), f"[{i + 1}/{total_n}] 已经达到标准，再多试几个，确认没有更好的"
                                           f"（第 {len(self.cands) + 1} 个）")

    # ------------------------------------------------------------------ 语速微调
    def _refine(self) -> None:
        """挑出来的那个（和综合分差不到 0.02 的第二名）语速和你平时差得多时，同一个请求（同样的几份、种子、参考、
        辅助参考、生成设置）只改语速再发一次，拿同一行；也和别的版本一起比。"""
        if not self.preset.get("refine_tempo", True):
            return
        full = [c for c in self.pool if c.score is not None]
        best = self.pick(full)
        if best is None:
            return
        targets = [best]
        others = [c for c in full if c is not best and not c.stored]
        runner = self.pick(others)
        if runner is not None and abs(runner.total - best.total) <= TIE_EPS:
            targets.append(runner)
        rs = getattr(self.scorer, "resid_sd", None)
        sd = rs() if callable(rs) else None
        thr = max(REFINE_MIN_DEV, 0.5 * sd) if sd else REFINE_MIN_DEV
        jobs: List[_Job] = []
        for c in targets:
            s = c.score
            if c.stored or c.refine_of is not None or not s.expected or not s.voiced:
                continue
            ratio = float(s.voiced) / float(s.expected)
            if abs(math.log(ratio)) <= thr:
                continue
            speed = float(min(2.0, max(0.5, c.speed * float(np.clip(ratio, *REFINE_CLIP)))))
            if c.mode == "batch":  # 同一个请求：同样的几份、同一个种子，拿同一行
                jobs.append(self._job(c.arm, c.req_n, seed=c.req_seed, speed=speed, refine_of=c, row=c.row))
            else:  # 一个一个生成的：这个版本自己就是一个请求（种子 = 请求的种子 + 第几个 × SEED_STEP）
                jobs.append(self._job(c.arm, 1, seed=c.seed, speed=speed, refine_of=c, row=0))
        if not jobs:
            return
        got: List[Tuple[_Job, List[SearchCand]]] = []
        if self.producer is not None:
            for j in jobs:
                self.producer.submit(j)
        for j in jobs:
            try:
                if self.producer is not None:
                    job, out = self.producer.get(_check_cancel)
                else:
                    _check_cancel()
                    job, out = j, self._work(j)
            except Exception as exc:  # noqa: BLE001 - 微调失败不影响已经挑好的
                self.requests += 1
                if self._fatal(exc):
                    raise RuntimeError(f"第 {self.seg.index + 1} 句没能生成（原因：{self._reason(exc)}）："
                                       f"{self.seg.text[:30]}") from exc
                log.warning(f"  第 {self.seg.index + 1} 句语速微调没成功：{exc}")
                continue
            self.requests += 1
            got.append((job, self._absorb(job, out)))
        for job, cs in got:
            old = job.refine_of
            for r in cs:
                self._full(r, count=False)  # 语速微调的版本一定完整打分（不占每句 24 个的名额）
                r.refine_of = old
                ov = float(old.score.voiced or 0.0)
                if ov > 0 and r.score.voiced is not None:
                    r.refined = abs(float(r.score.voiced) * job.speed / old.speed - ov) / ov <= REFINE_SAME
                self.refined.append(r)
                self.pool.append(r)

    # ------------------------------------------------------------------ 存下来的版本
    def load_stored(self, seg: Any, plan: Any) -> List[SearchCand]:
        """读这句话以前留下的版本，用现在的打分标准在处理器上重新打分（不用显卡、不再识别一遍）。"""
        if not getattr(self, "seg", None) or self.seg is not seg:
            self._setup(seg, plan)
        sig_now = self.n._judge_sig()
        folder = store_dir(self.n.project.cache_dir, plan.pool_key)
        # 当时打分用的声音和现在一样（同样的去首尾设置）才沿用存下来的声纹；不一样（这一版以前存的、你本人的收音长度变了）
        # 就按现在的去首尾重新算
        same_audio = store_info(folder).get("scored_on") == self.n._scored_on()
        out: List[SearchCand] = []
        for it in load_candidates(folder):
            try:
                arm = Arm(**{k: v for k, v in (it.get("arm") or {}).items() if k in Arm.__dataclass_fields__})
            except TypeError:
                continue
            wav, sr = it["wav"], int(it["sr"])
            c = SearchCand(wav=wav, sr=sr, arm=arm, seed=int(it.get("seed", 0)), req_seed=int(it.get("req_seed", 0)),
                           row=int(it.get("row", 0)), req_no=int(it.get("req_no", -1)), req_n=int(it.get("req_n", 1)),
                           speed=float(it.get("speed", plan.speed)), mode=str(it.get("mode") or "single"), stored=True,
                           refined=bool(it.get("refined")), model=str(it.get("model") or ""))
            c.awav, c.empty = self.n._analysis_pair(wav, sr)
            prepare = getattr(self.scorer, "prepare", None)
            prepared = prepare(c.awav, sr) if callable(prepare) else None
            if (isinstance(prepared, dict) and same_audio and it.get("judge_sig") == sig_now and it.get("emb")
                    and "speech_sec" in it):
                # 打分标准没变：声纹沿用存下来的（不再做人声检测），人声几秒也沿用当时量的（短句子的标准按它定）；
                # 没记人声几秒的（这一版以前存的）重新做一遍人声检测
                prepared["embs"].update(it["emb"])
                prepared["seconds"] = it["speech_sec"]
            s = it.get("score") or {}
            cer = None
            if s.get("cer") is not None:
                cer = {"cer": s.get("cer"), "hyp": s.get("hyp"), "errors": s.get("errors"), "engine": s.get("checker")}
            c.score = self.scorer.full(c.awav, sr, seg.text, self.lang, self.mult, prepared=prepared, use_asr=False,
                                       cer=cer)
            c.score.arm = arm.label(plan.refs)
            c.score.model = c.model
            if isinstance(prepared, dict):
                c.embs = {k: np.asarray(v, dtype=np.float32) for k, v in (prepared.get("embs") or {}).items()}
                c.speech_sec = prepared.get("seconds")
                prepared["speech"] = {}
            out.append(c)
        return out

    def rerank(self, seg: Any, plan: Any, tries: int = 0) -> Optional[Outcome]:
        """只用存下来的版本、按现在的标准重新挑（打分标准 / 说话习惯 / 排序权重变了时；不用显卡）。没有存下的返回 None。"""
        self._setup(seg, plan)
        stored = self.load_stored(seg, plan)
        if not stored:
            return None
        self.pool = list(stored)
        best = self._best_nonempty()
        if best is None:
            return None
        full = sorted(stored, key=self._value, reverse=True)
        stats = {"reranked": True, "stored_competed": len(stored), "requests": 0, "candidates": 0,
                 "chosen_arm": best.arm.label(plan.refs), "chosen_stored": True}
        return Outcome(best, full, int(tries), bool(self.n._meets_targets(best, seg)), [], stats,
                       keep=self.keep_order(best, full, self.left))
