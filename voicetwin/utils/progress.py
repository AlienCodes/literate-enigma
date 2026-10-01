"""进度核心：进度状态（ProgressTracker）、取消（停止按钮）、进度条 HTML / CSS / JS、命令行进度行、下载进度。

这个文件不能 import gradio：命令行和测试也要用它（测试环境的 gradio 版本和整合包里的 4.24 不一样）。
只用 typing.Optional / List / Tuple / Dict，保持 Python 3.9 可用。

颜色约定（老师明确要求的）：
- 正常进行：绿色进度条（#16a34a），带会动的斜条纹，看得出程序“活着”；
- 很久没有新进度（≥ 180 秒）：黄色/琥珀色（#d97706），并提示“可能比较慢，也可能卡住了”；
- 出错了：红色（#dc2626），写清楚停在哪一步、原因和怎么办；
- 全部完成：不动的绿色，“✅ 全部完成！用时 …”；
- 用户点了停止：灰色（#6b7280），“⏹ 已停止”。
"""

import datetime
import html
import math
import re
import threading
import time
from contextlib import contextmanager
from itertools import count
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

Stage = Tuple[float, str]
ProgressFn = Callable[[float, str], None]

#: 多久没有新进度就算“很久”（进度条变成黄色）
STALL_SECONDS = 180.0
#: 多久没有新进度就先轻轻提示一句“仍在工作中”
HEARTBEAT_SECONDS = 60.0
#: 总剩余时间至少要满足这两个条件才显示（太早估出来的数字不可信）
TOTAL_ETA_MIN_FRAC = 0.03
TOTAL_ETA_MIN_ELAPSED = 30.0
#: 总剩余时间的平滑程度：每秒保留 90% 的旧估计（比单步的 0.7 更稳，数字不会忽大忽小）
TOTAL_ETA_KEEP = 0.9
#: 当前这一步的剩余时间的显示条件
STAGE_ETA_MIN_P = 0.05
STAGE_ETA_MIN_ELAPSED = 20.0
#: 估计超过这么久就当作“还估不准”（例如刚开始时进度几乎不动）
ETA_MAX_SECONDS = 3 * 24 * 3600.0

ESTIMATING = "正在估算……"

# ---------------------------------------------------------------------------
# 取消（停止按钮）
# ---------------------------------------------------------------------------


class TaskCancelled(BaseException):
    """用户点了“停止”。

    故意继承 BaseException：后端里有很多 ``except Exception`` 用来吞掉进度回调的小错误，
    取消信号必须能穿过它们一路传到最外层。"""


CANCEL = threading.Event()


def request_cancel() -> None:
    """请求停止当前任务（下一次报进度或 check_cancel() 时生效）。"""
    CANCEL.set()


def clear_cancel() -> None:
    CANCEL.clear()


def check_cancel() -> None:
    """如果用户已经点了停止，就抛出 TaskCancelled。"""
    if CANCEL.is_set():
        raise TaskCancelled("已按你的要求停止")


# ---------------------------------------------------------------------------
# 时间格式
# ---------------------------------------------------------------------------


def _num(s: Any) -> float:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v) or math.isinf(v) or v < 0:
        return 0.0
    return v


def _duration_core(s: Any) -> str:
    """'不到 1 分钟' / '12 分钟' / '1 小时 5 分'（不带“约”字，方便拼句子）。"""
    s = _num(s)
    if s < 60:
        return "不到 1 分钟"
    minutes = int(s / 60.0 + 0.5)
    if minutes < 60:
        return f"{minutes} 分钟"
    h, m = divmod(minutes, 60)
    return f"{h} 小时 {m} 分" if m else f"{h} 小时"


def format_duration(s: Any) -> str:
    """估计的剩余时间：'不到 1 分钟' / '约 12 分钟' / '约 1 小时 5 分'。"""
    core = _duration_core(s)
    return core if core.startswith("不到") else "约 " + core


def format_elapsed(s: Any) -> str:
    """已经用了多久：'45 秒' / '3 分 20 秒' / '1 小时 05 分'。"""
    s = int(_num(s))
    if s < 60:
        return f"{s} 秒"
    if s < 3600:
        return f"{s // 60} 分 {s % 60} 秒"
    return f"{s // 3600} 小时 {(s % 3600) // 60:02d} 分"


def format_clock(ts: Any, now: Optional[float] = None) -> str:
    """把时间戳变成 '21:40'；不是今天就写 '明天 01:20' 或 '10月3日 09:00'。"""
    try:
        t = time.localtime(float(ts))
        if now is None:
            now = time.time()
        n = time.localtime(float(now))
    except (TypeError, ValueError, OverflowError, OSError):
        return ""
    hm = time.strftime("%H:%M", t)
    days = (_date_ord(t) - _date_ord(n))
    if days == 0:
        return hm
    if days == 1:
        return "明天 " + hm
    return f"{t.tm_mon}月{t.tm_mday}日 {hm}"


def _date_ord(t: time.struct_time) -> int:
    return datetime.date(t.tm_year, t.tm_mon, t.tm_mday).toordinal()


# ---------------------------------------------------------------------------
# 从进度说明里认出“120/800”这样的计数
# ---------------------------------------------------------------------------

_COUNT_RE = re.compile(r"(\d+)\s*/\s*(\d+)")
_UNIT_RE = re.compile(r"\s*(个文件|个视频|个版本|个模型|个片段|个句子|个|轮|段|句|条|次|项|篇|MB|GB|KB)")
_UNIT_KEYWORDS = (
    (("识别", "声纹", "处理文字", "特征", "语义", "片段"), "段"),
    (("试听", "评估"), "条"),
    (("逐句", "句"), "句"),
)


def _parse_counter(msg: str, stage_name: str = "") -> Tuple[Optional[int], Optional[int], str, bool]:
    """返回 (step, total, 单位, 是不是“第 N 个”这种正在做的序号)。认不出来时 step/total 为 None。"""
    m = _COUNT_RE.search(msg or "")
    if not m:
        return None, None, "", False
    try:
        step, total = int(m.group(1)), int(m.group(2))
    except ValueError:  # pragma: no cover - 正则保证是数字
        return None, None, "", False
    if total <= 0 or step < 0 or step > total:
        return None, None, "", False
    before = msg[: m.start()].rstrip()
    ordinal = before.endswith("第") or before.endswith("[") or before.endswith("【")
    um = _UNIT_RE.match(msg[m.end():])
    unit = um.group(1) if um else ""
    if not unit:
        hay = msg + " " + (stage_name or "")
        for words, u in _UNIT_KEYWORDS:
            if any(w in hay for w in words):
                unit = u
                break
    return step, total, unit, ordinal


def counter_text(snap: Dict[str, Any]) -> str:
    """'已完成 120 / 800 段'、'第 3 / 12 轮'、'已下载 120 / 3100 MB'；没有计数时返回 ''。"""
    step, total = snap.get("step"), snap.get("total")
    if step is None or not total:
        return ""
    unit = str(snap.get("unit") or "")
    tail = f" {unit}" if unit else ""
    if unit in ("MB", "GB", "KB"):
        return f"已下载 {step} / {total}{tail}"
    if snap.get("ordinal"):
        return f"第 {step} / {total}{tail}"
    return f"已完成 {step} / {total}{tail}"


# ---------------------------------------------------------------------------
# ProgressTracker
# ---------------------------------------------------------------------------

_RUN_COUNTER = count(1)


def _clean_stages(stages: Optional[Sequence[Any]]) -> List[Stage]:
    out: List[Stage] = []
    for item in stages or []:
        try:
            start, name = item[0], item[1]
            start = float(start)
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        if math.isnan(start):
            continue
        out.append((min(1.0, max(0.0, start)), str(name)))
    out.sort(key=lambda s: s[0])
    return out


class ProgressTracker:
    """线程安全的进度状态。

    用法和以前的进度回调完全一样：``tracker(0.45, '识别 120/800：大家好')``。
    进度只会往前走（报一个更小的数会被忽略），每次报进度前先检查有没有点“停止”。"""

    def __init__(self, stages: Optional[Sequence[Stage]] = None, title: str = "", hint: str = "",
                 clock: Callable[[], float] = time.time,
                 on_update: Optional[Callable[[Dict[str, Any]], None]] = None):
        self._lock = threading.Lock()
        self.stages: List[Stage] = _clean_stages(stages)
        self.title = str(title or "")
        self.hint = str(hint or "")
        self._clock = clock
        self.on_update = on_update
        now = self._now()
        self._t0 = now
        self._run_id = f"{now:.3f}-{next(_RUN_COUNTER)}"
        self._frac = 0.0
        self._msg = ""
        self._step: Optional[int] = None
        self._total: Optional[int] = None
        self._unit = ""
        self._ordinal = False
        self._stage_idx = self._stage_for(0.0)
        self._stage_t0 = now
        self._last_change = now
        self._status = "running"
        self._error = ""
        self._advice = ""
        self._finished_at: Optional[float] = None
        # 平滑（EMA）后的“这一步一共要多久”和“整个任务一共要多久”
        self._stage_T: Optional[float] = None
        self._stage_T_at: Optional[float] = None
        self._total_T: Optional[float] = None
        self._total_T_at: Optional[float] = None

    # -- 内部工具 ---------------------------------------------------------
    def _now(self) -> float:
        try:
            return float(self._clock())
        except Exception:
            return time.time()

    def _stage_for(self, frac: float) -> int:
        idx = -1
        for i, (start, _name) in enumerate(self.stages):
            if start <= frac + 1e-9:
                idx = i
        if idx < 0 and self.stages:
            idx = 0
        return idx

    def _stage_bounds(self) -> Tuple[float, float]:
        if self._stage_idx < 0 or not self.stages:
            return 0.0, 1.0
        lo = self.stages[self._stage_idx][0]
        hi = self.stages[self._stage_idx + 1][0] if self._stage_idx + 1 < len(self.stages) else 1.0
        return lo, hi

    def _stage_name(self) -> str:
        if 0 <= self._stage_idx < len(self.stages):
            return self.stages[self._stage_idx][1]
        return ""

    @staticmethod
    def _ema(old: Optional[float], old_at: Optional[float], raw: float, now: float,
             keep: float = 0.7) -> Tuple[float, float]:
        """平滑：每过 1 秒保留 keep 的旧值（keep=0.7 即“0.7 旧 + 0.3 新”）。

        最多每秒更新一次（网页 0.6 秒刷新一次，不能因此算得更快）；隔了很久才更新时（例如网页关掉一阵
        又接上），按经过的秒数折算，旧值几乎不再起作用，不会被很久以前的估计拖住。"""
        if old is None or old_at is None:
            return raw, now
        dt = now - old_at
        if dt < 1.0:
            return old, old_at
        w = keep ** min(dt, 120.0)
        return w * old + (1.0 - w) * raw, now

    def _update_eta_locked(self, now: float) -> None:
        """更新平滑后的“一共要多久”。只用已经可信的数据（太早的估计会把平均值带偏很久）。"""
        if self._status != "running":
            return
        elapsed = now - self._t0
        if self._frac >= TOTAL_ETA_MIN_FRAC and elapsed >= TOTAL_ETA_MIN_ELAPSED:
            self._total_T, self._total_T_at = self._ema(self._total_T, self._total_T_at,
                                                        elapsed / self._frac, now, keep=TOTAL_ETA_KEEP)
        lo, hi = self._stage_bounds()
        p = (self._frac - lo) / (hi - lo) if hi > lo else 1.0
        stage_elapsed = now - self._stage_t0
        if p >= STAGE_ETA_MIN_P and stage_elapsed >= STAGE_ETA_MIN_ELAPSED:
            self._stage_T, self._stage_T_at = self._ema(self._stage_T, self._stage_T_at,
                                                        stage_elapsed / p, now)

    # -- 对外接口 ---------------------------------------------------------
    def __call__(self, frac: float, msg: str = "") -> None:
        check_cancel()  # 唯一允许抛出去的异常
        try:
            self._update(frac, msg)
        except Exception:
            return
        cb = self.on_update
        if cb is not None:
            try:
                cb(self.snapshot())
            except Exception:
                pass

    def _update(self, frac: Any, msg: Any) -> None:
        try:
            f = float(frac)
        except (TypeError, ValueError):
            f = None
        if f is not None and math.isnan(f):
            f = None
        now = self._now()
        with self._lock:
            if self._status != "running":
                return
            changed = False
            if f is not None:
                f = min(1.0, max(0.0, f))
                if f > self._frac:
                    self._frac = f
                    changed = True
            new_msg = None
            if msg:
                new_msg = " ".join(str(msg).split())[:300]
                if new_msg != self._msg:
                    changed = True
                self._msg = new_msg
            idx = self._stage_for(self._frac)
            if idx != self._stage_idx:
                self._stage_idx = idx
                self._stage_t0 = now
                self._stage_T = self._stage_T_at = None
                self._step = self._total = None
                self._unit, self._ordinal = "", False
                changed = True
            if new_msg is not None:
                self._step, self._total, self._unit, self._ordinal = _parse_counter(new_msg, self._stage_name())
            if changed:
                self._last_change = now
            self._update_eta_locked(now)

    def finish(self, ok: bool, msg: str = "", stopped: bool = False, advice: str = "") -> None:
        """任务结束：ok=True 完成；stopped=True 用户停止；否则出错（msg 是出错原因，advice 是怎么办）。"""
        now = self._now()
        with self._lock:
            if self._status != "running":  # 只算第一次
                return
            if stopped:
                self._status = "stopped"
                self._error = str(msg or "")[:500]
            elif ok:
                self._status = "done"
                self._frac = 1.0
                if msg:
                    self._msg = " ".join(str(msg).split())[:300]
            else:
                self._status = "error"
                self._error = str(msg or "")[:500] or "出现了意外错误"
                self._advice = str(advice or "")[:800]
            self._finished_at = now
        cb = self.on_update
        if cb is not None:
            try:
                cb(self.snapshot())
            except Exception:
                pass

    @property
    def status(self) -> str:
        return self._status

    def snapshot(self) -> Dict[str, Any]:
        now = self._now()
        with self._lock:
            self._update_eta_locked(now)
            end = self._finished_at if self._finished_at is not None else now
            running = self._status == "running"
            elapsed = max(0.0, end - self._t0)
            stage_elapsed = max(0.0, end - self._stage_t0)
            idle = max(0.0, now - self._last_change) if running else 0.0
            frac = self._frac
            pct = int(frac * 100 + 1e-9)
            pct = 100 if self._status == "done" else min(99 if running else 100, max(0, pct))

            # 当前这一步还要多久
            lo, hi = self._stage_bounds()
            p = (frac - lo) / (hi - lo) if hi > lo else 1.0
            eta: Optional[float] = None
            if running and p >= 0.98 and stage_elapsed >= STAGE_ETA_MIN_ELAPSED:
                eta = 0.0
                eta_text = "这一步快好了"
            elif (running and p >= STAGE_ETA_MIN_P and stage_elapsed >= STAGE_ETA_MIN_ELAPSED
                  and self._stage_T is not None):
                eta = max(0.0, self._stage_T - stage_elapsed)
                if eta > ETA_MAX_SECONDS:
                    eta = None
                    eta_text = self.hint or "正在估算剩余时间……"
                elif eta < 60:
                    eta_text = "这一步不到 1 分钟就好"
                else:
                    eta_text = "这一步大约还要 " + _duration_core(eta)
            else:
                eta_text = (self.hint or "正在估算剩余时间……") if running else ""

            # 整个任务还要多久（R1：frac ≥ 3% 且已经过了 30 秒才显示）
            eta_total: Optional[float] = None
            finish_clock = ""
            if running and frac >= TOTAL_ETA_MIN_FRAC and elapsed >= TOTAL_ETA_MIN_ELAPSED and self._total_T:
                left = max(0.0, self._total_T - elapsed)
                if left <= ETA_MAX_SECONDS:
                    eta_total = left
            if not running:
                eta_total_text = ""
            elif eta_total is None:
                eta_total_text = "全部还要多久：" + ESTIMATING
            elif eta_total < 60:
                eta_total_text = "全部快完成了，不到 1 分钟"
                finish_clock = format_clock(now + eta_total, now)
            else:
                finish_clock = format_clock(now + eta_total, now)
                eta_total_text = f"全部大约还要 {_duration_core(eta_total)}，预计 {finish_clock} 左右完成"

            if self._status == "running":
                level = "stall" if idle >= STALL_SECONDS else "ok"
            else:
                level = self._status
            stage_idx = self._stage_idx
            return {
                "status": self._status,
                "level": level,
                "frac": frac,
                "pct": pct,
                "title": self.title,
                "stage_index": stage_idx + 1 if stage_idx >= 0 else 0,
                "stage_count": len(self.stages),
                "stage_name": self._stage_name(),
                "msg": self._msg,
                "step": self._step,
                "total": self._total,
                "unit": self._unit,
                "ordinal": self._ordinal,
                "elapsed": elapsed,
                "stage_elapsed": stage_elapsed,
                "eta": eta,
                "eta_text": eta_text,
                "eta_total": eta_total,
                "eta_total_text": eta_total_text,
                "finish_clock": finish_clock,
                "idle": idle,
                "hint": self.hint,
                "run_id": self._run_id,
                "error": self._error,
                "advice": self._advice,
                "started_clock": format_clock(self._t0, now),
                "ended_clock": format_clock(self._finished_at, now) if self._finished_at is not None else "",
                "stopping": bool(running and CANCEL.is_set()),
            }


# ---------------------------------------------------------------------------
# 进度条 HTML
# ---------------------------------------------------------------------------


def _e(s: Any) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def _stage_label(snap: Dict[str, Any]) -> str:
    n = int(snap.get("stage_count") or 0)
    i = int(snap.get("stage_index") or 0)
    name = str(snap.get("stage_name") or "")
    if n > 1 and i > 0:
        return f"第 {i} 步（共 {n} 步）：{name}"
    return name or str(snap.get("title") or "") or "正在处理"


def _where_stopped(snap: Dict[str, Any]) -> str:
    """出错 / 停止时说清楚停在哪里。"""
    n = int(snap.get("stage_count") or 0)
    i = int(snap.get("stage_index") or 0)
    name = str(snap.get("stage_name") or "")
    if n > 1 and i > 0:
        return f"停在第 {i} 步「{name}」"
    if name or snap.get("title"):
        return f"停在「{name or snap.get('title')}」这一步"
    return ""


def _task_words(title: str) -> str:
    """'准备素材' → '准备素材'；'正在训练' → '训练'；空 → '工作'（用来拼“正在…… / 还在……”）。"""
    t = title.strip()
    if t.startswith("正在"):
        t = t[2:].strip()
    return t or "工作"


def render_progress_html(snap: Optional[Dict[str, Any]], note: str = "") -> str:
    """把 ProgressTracker.snapshot() 画成进度条（交给 gr.HTML 显示）。所有文字都会转义。"""
    if not snap:
        return ""
    status = str(snap.get("status") or "running")
    if status not in ("running", "done", "error", "stopped"):
        status = "running"
    level = str(snap.get("level") or ("ok" if status == "running" else status))
    pct = max(0, min(100, int(_num(snap.get("pct")))))
    title = str(snap.get("title") or "")
    stage_name = str(snap.get("stage_name") or "")
    elapsed = format_elapsed(snap.get("elapsed"))
    stall = status == "running" and level == "stall"

    classes = f"vt-prog vt-{status}" + (" vt-stall" if stall else "")
    attrs = (f' data-status="{_e(status)}" data-level="{_e(level)}" data-pct="{pct}"'
             f' data-title="{_e(f"{pct}% {stage_name or title}".strip())}" data-run="{_e(snap.get("run_id", ""))}"')
    track = (f'<div class="vt-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct}">'
             f'<div class="vt-fill" style="width:{pct}%"></div></div>')

    def head(left: str) -> str:
        return (f'<div class="vt-head"><div class="vt-stage">{_e(left)}</div>'
                f'<div class="vt-pct">{pct}%</div></div>')

    parts: List[str] = [f'<div class="{classes}"{attrs}>']

    if status == "running":
        idle = _num(snap.get("idle"))
        if stall:
            top = f"🟡 还在{_task_words(title)}，但已经好一会儿没有新进度"
        else:
            top = f"🟢 正在{_task_words(title)}……"
        parts.append(f'<div class="vt-top">{_e(top)}'
                     + ('' if stall else '<span class="vt-tip">（绿色条纹在动，说明程序在正常工作）</span>')
                     + '</div>')
        parts.append(head(_stage_label(snap)))
        parts.append(track)
        meta = []
        c = counter_text(snap)
        if c:
            meta.append(c)
        meta.append(f"已用 {elapsed}")
        if int(snap.get("stage_count") or 0) > 1 and snap.get("eta") is not None and snap.get("eta_text"):
            meta.append(str(snap.get("eta_text")))
        parts.append(f'<div class="vt-meta">{_e(" · ".join(meta))}</div>')
        total_text = str(snap.get("eta_total_text") or ("全部还要多久：" + ESTIMATING))
        if stall:  # 好一会儿没有新进度时，按过去的速度算出来的时间不可信：不显示假数字
            total_text = "全部还要多久：暂时算不出来（这一步一直没有新进度）"
        elif snap.get("eta_total") is None and snap.get("hint"):
            total_text += f"（{snap.get('hint')}）"
        parts.append(f'<div class="vt-eta">⏱ {_e(total_text)}</div>')
        if snap.get("msg"):
            parts.append(f'<div class="vt-msg" title="{_e(snap.get("msg"))}">现在：{_e(snap.get("msg"))}</div>')
        if snap.get("stopping"):
            parts.append('<div class="vt-warn">⏹ 正在停止……（等手上这一小步做完就停，请稍等）</div>')
        elif stall:
            minutes = max(1, int(idle // 60))
            parts.append(f'<div class="vt-warn">⚠️ 已经 {minutes} 分钟没有新进度：这一步可能比较慢，也可能卡住了。'
                         '请先等一等，不要关闭黑色窗口。</div>')
        elif idle >= HEARTBEAT_SECONDS:
            parts.append(f'<div class="vt-beat">仍在工作中：已经 {_e(format_elapsed(idle))}没有新进度'
                         '（有的步骤本来就比较慢），请不要关闭黑色窗口。</div>')
        if note:
            parts.append(f'<div class="vt-small">{_e(note)}</div>')

    elif status == "done":
        parts.append(head(f"✅ 全部完成！用时 {elapsed}"))
        parts.append(track)
        meta = []
        if title:
            meta.append(f"「{title}」已经做好了")
        if snap.get("ended_clock"):
            meta.append(f"完成时间 {snap.get('ended_clock')}")
        if meta:
            parts.append(f'<div class="vt-meta">{_e(" · ".join(meta))}</div>')

    elif status == "error":
        where = _where_stopped(snap)
        parts.append(head("❌ 没有完成" + (f"：{where}" if where else "")))
        parts.append(track)
        reason = str(snap.get("error") or "出现了意外错误")
        advice = str(snap.get("advice") or "") or "可以再点一次试试；如果还是不行，把下方「详细过程」里的内容复制发给帮你的人。"
        parts.append(f'<div class="vt-errbox"><div><b>原因：</b>{_e(reason)}</div>'
                     f'<div><b>怎么办：</b>{_e(advice)}</div></div>')
        parts.append(f'<div class="vt-meta">{_e(f"已用 {elapsed} · 详细的出错信息在下方「详细过程」里，需要时可以复制给帮你的人。")}</div>')

    else:  # stopped
        where = _where_stopped(snap)
        parts.append(head("⏹ 已停止"))
        parts.append(track)
        meta = [m for m in (where, f"已用 {elapsed}") if m]
        parts.append(f'<div class="vt-meta">{_e(" · ".join(meta))}</div>')
        parts.append('<div class="vt-small">已经做好的部分不会丢。需要时再点一次开始就行。</div>')

    parts.append("</div>")
    return "".join(parts)


_TONES = ("info", "warn", "error", "ok")


def render_notice_html(text: Any, tone: str = "info") -> str:
    """一段带彩色左边框的提示（例如“现在正在训练，请等它完成”）。tone: info / warn / error / ok。"""
    tone = tone if tone in _TONES else "info"
    body = "<br>".join(_e(line) for line in str(text if text is not None else "").splitlines())
    return f'<div class="vt-note vt-note-{tone}" data-tone="{tone}">{body}</div>'


PROGRESS_CSS = """
.vt-prog{margin:4px 0;padding:10px 12px;border:1px solid var(--border-color-primary);border-radius:8px;
  background:var(--background-fill-primary);line-height:1.5;box-sizing:border-box;max-width:100%;overflow-wrap:anywhere}
.vt-top{font-size:var(--text-sm);color:var(--body-text-color-subdued);margin-bottom:2px}
.vt-tip{margin-left:4px}
.vt-head{display:flex;justify-content:space-between;align-items:flex-end;gap:8px;font-weight:700}
.vt-stage{flex:1 1 auto;min-width:0}
.vt-pct{flex:0 0 auto;font-size:1.9em;line-height:1.1;font-weight:800;font-variant-numeric:tabular-nums}
.vt-track{height:16px;border-radius:8px;background:var(--background-fill-secondary);
  border:1px solid var(--border-color-primary);overflow:hidden;margin:6px 0;box-sizing:border-box}
.vt-fill{height:100%;width:0;background-color:#16a34a;transition:width .5s}
.vt-running .vt-fill{background-image:linear-gradient(45deg,rgba(255,255,255,.3) 25%,transparent 25%,transparent 50%,
  rgba(255,255,255,.3) 50%,rgba(255,255,255,.3) 75%,transparent 75%,transparent);
  background-size:28px 28px;animation:vt-move 1s linear infinite}
.vt-running.vt-stall .vt-fill{background-color:#d97706;animation-duration:2.5s}
.vt-done .vt-fill{background-color:#16a34a;background-image:none}
.vt-error .vt-fill{background-color:#dc2626;background-image:none}
.vt-stopped .vt-fill{background-color:#6b7280;background-image:none}
.vt-running .vt-pct,.vt-done .vt-pct{color:#16a34a}
.vt-running.vt-stall .vt-pct{color:#d97706}
.vt-error .vt-pct{color:#dc2626}
.vt-stopped .vt-pct{color:#6b7280}
.vt-prog.vt-done{border-color:#16a34a}
.vt-prog.vt-stall{border-color:#d97706}
.vt-prog.vt-error{border-color:#dc2626}
.vt-done .vt-track{border-color:#16a34a}
.vt-stall .vt-track{border-color:#d97706;background:rgba(217,119,6,.12)}
.vt-error .vt-track{border-color:#dc2626;background:rgba(220,38,38,.12)}
.vt-meta,.vt-msg,.vt-small,.vt-beat{color:var(--body-text-color-subdued);font-size:var(--text-sm)}
.vt-eta{font-weight:600;margin-top:2px}
.vt-msg{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.vt-warn{margin-top:6px;padding:6px 10px;border-left:4px solid #d97706;background:rgba(217,119,6,.12);border-radius:4px}
.vt-errbox{margin:6px 0 4px;padding:6px 10px;border-left:4px solid #dc2626;background:rgba(220,38,38,.10);border-radius:4px}
.vt-small{margin-top:4px}
@keyframes vt-move{from{background-position:0 0}to{background-position:28px 0}}
.vt-note{margin:4px 0;padding:8px 12px;border-left:4px solid var(--color-accent);background:var(--background-fill-secondary);
  border-radius:4px;line-height:1.5;overflow-wrap:anywhere}
.vt-note-warn{border-left-color:#d97706;background:rgba(217,119,6,.12)}
.vt-note-error{border-left-color:#dc2626;background:rgba(220,38,38,.10)}
.vt-note-ok{border-left-color:#16a34a;background:rgba(22,163,74,.10)}
.vt-bar-box .generating{border:none!important;animation:none!important}
@media (max-width:480px){.vt-prog{padding:8px}.vt-pct{font-size:1.5em}.vt-tip{display:none}}
"""

#: 交给 gr.Blocks(js=...)：浏览器标签页标题显示进度（例如“45% 识别每段话的文字 - 声音分身”），
#: 完成时标题变成“✅ 完成了”并轻轻响一声。出任何问题都静默忽略。
PROGRESS_JS = r"""
() => {
  try {
    const base = document.title;
    const seen = new Set();
    let pending = false;
    let flagged = false;
    const beep = () => {
      try {
        const AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        const ctx = new AC();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.value = 880;
        gain.gain.value = 0.15;
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.3);
        setTimeout(() => { try { ctx.close(); } catch (e) {} }, 800);
      } catch (e) {}
    };
    const update = () => {
      pending = false;
      try {
        const run = document.querySelector('.vt-prog.vt-running');
        if (run) {
          const warn = run.classList.contains('vt-stall') ? '⚠️ ' : '';
          document.title = warn + (run.dataset.title || '') + ' - 声音分身';
          flagged = false;
          return;
        }
        const fresh = Array.from(document.querySelectorAll('.vt-prog.vt-done, .vt-prog.vt-error'))
          .find((el) => el.dataset.run && !seen.has(el.dataset.run));
        if (fresh) {
          seen.add(fresh.dataset.run);
          if (fresh.classList.contains('vt-done')) {
            document.title = '✅ 完成了 - 声音分身';
            beep();
          } else {
            document.title = '❌ 出错了 - 声音分身';
          }
          flagged = true;
          return;
        }
        if (!flagged) document.title = base;
      } catch (e) {}
    };
    new MutationObserver(() => {
      if (!pending) { pending = true; setTimeout(update, 200); }
    }).observe(document.body, { subtree: true, childList: true, attributes: true });
    document.addEventListener('visibilitychange', () => {
      try {
        if (document.visibilityState === 'visible' && flagged) {
          setTimeout(() => {
            flagged = false;
            if (!document.querySelector('.vt-prog.vt-running')) document.title = base;
          }, 3000);
        }
      } catch (e) {}
    });
  } catch (e) {}
}
"""


# ---------------------------------------------------------------------------
# 命令行：每隔一会儿打印一整行进度
# ---------------------------------------------------------------------------


def console_line(snap: Dict[str, Any]) -> str:
    """'⏳ 45% ｜第 3/7 步 识别每段话的文字｜已完成 120 / 800 段｜已用 3 分 20 秒｜这一步大约还要 5 分钟'。"""
    status = snap.get("status", "running")
    elapsed = format_elapsed(snap.get("elapsed"))
    if status == "done":
        return f"✅ 完成，用时 {elapsed}"
    if status == "error":
        where = _where_stopped(snap)
        return "❌ 没有完成" + (f"（{where}）" if where else "") + f"：{snap.get('error') or '出现了意外错误'}"
    if status == "stopped":
        return f"⏹ 已停止，用时 {elapsed}"
    parts = [f"⏳ {int(_num(snap.get('pct')))}% "]
    n = int(snap.get("stage_count") or 0)
    i = int(snap.get("stage_index") or 0)
    if n > 1 and i > 0:
        parts.append(f"第 {i}/{n} 步 {snap.get('stage_name', '')}")
    elif snap.get("stage_name") or snap.get("title"):
        parts.append(str(snap.get("stage_name") or snap.get("title")))
    c = counter_text(snap)
    if c:
        parts.append(c)
    parts.append(f"已用 {elapsed}")
    if n > 1 and snap.get("eta") is not None and snap.get("eta_text"):
        parts.append(str(snap.get("eta_text")))
    if snap.get("eta_total") is not None and snap.get("eta_total_text"):
        parts.append(str(snap.get("eta_total_text")))
    if snap.get("level") == "stall":
        parts.append(f"已经 {max(1, int(_num(snap.get('idle')) // 60))} 分钟没有新进度，请先等一等")
    return "｜".join(parts)


def console_reporter(print_fn: Callable[[str], Any], min_interval: float = 30.0,
                     pct_step: int = 5) -> Callable[[Dict[str, Any]], None]:
    """返回一个 on_update 回调：换步骤、百分比跨过 pct_step 的倍数、过了 min_interval 秒、或者结束时，打印一整行。

    只打印整行（不用 '\\r'）：Windows 的黑色窗口里 '\\r' 会和其他日志行搅在一起。"""
    lock = threading.Lock()
    st: Dict[str, Any] = {"stage": None, "bucket": None, "t": None, "final": None}
    step = max(1, int(pct_step or 1))

    def on_update(snap: Dict[str, Any]) -> None:
        try:
            status = snap.get("status", "running")
            t = _num(snap.get("elapsed"))
            bucket = int(_num(snap.get("pct"))) // step
            stage = snap.get("stage_index")
            with lock:
                if status != "running":
                    key = (status, snap.get("run_id"))
                    if st["final"] == key:
                        return
                    st["final"] = key
                    do_print = True
                else:
                    do_print = (st["t"] is None or stage != st["stage"] or bucket > (st["bucket"] or 0)
                                or t - st["t"] >= min_interval)
                if do_print:
                    st["stage"], st["bucket"], st["t"] = stage, bucket, t
            if do_print:
                print_fn(console_line(snap))
        except Exception:
            pass

    return on_update


# ---------------------------------------------------------------------------
# 第一次下载大模型时，显示已经下载了多少 MB
# ---------------------------------------------------------------------------


def _dir_mb(path: Path) -> int:
    total = 0
    try:
        if path.is_file():
            return int(path.stat().st_size / (1024 * 1024))
        for f in path.rglob("*"):
            try:
                if f.is_file():
                    total += f.stat().st_size
            except OSError:
                continue
    except OSError:
        pass
    return int(total / (1024 * 1024))


@contextmanager
def watch_download(path: Path, expected_mb: int, progress: Optional[ProgressFn], lo: float, hi: float,
                   label: str, interval: float = 2.0, stall_seconds: float = 120.0) -> Iterator[None]:
    """下载期间每 2 秒数一次 path 下文件的总大小（包括 huggingface 的 blobs/*.incomplete），报给进度条。

    进度不会超过 hi；所有异常（包括取消）都在后台线程里吞掉，取消由调用方自己处理。"""
    stop = threading.Event()
    thread: Optional[threading.Thread] = None
    if progress is not None:
        expected = max(1, int(_num(expected_mb)) or 1)
        lo_f, hi_f = float(lo), float(hi)

        def run() -> None:
            last_mb = -1
            last_grow = time.time()
            stalled = False
            while not stop.is_set():
                try:
                    mb = _dir_mb(Path(path))
                    now = time.time()
                    grew = mb > last_mb
                    if grew:
                        last_grow = now
                        last_mb = mb
                    was_stalled = stalled
                    stalled = (not grew) and (now - last_grow >= stall_seconds)
                    if grew or stalled != was_stalled:
                        frac = lo_f + (hi_f - lo_f) * min(0.99, mb / float(expected))
                        if stalled:
                            msg = (f"下载好像停住了（已下载 {mb} / {expected} MB）：请检查网络；"
                                   "也可以关掉程序重新打开再试（已下载的部分会保留）")
                        else:
                            msg = f"第一次使用，正在下载{label}：{mb} / {expected} MB（下载一次以后就不用再下了）"
                        progress(frac, msg)
                except BaseException:  # noqa: B036 - 包括 TaskCancelled：取消由调用方处理
                    pass
                stop.wait(interval)

        thread = threading.Thread(target=run, name="vt-watch-download", daemon=True)
        try:
            thread.start()
        except Exception:
            thread = None
    try:
        yield
    finally:
        stop.set()
        if thread is not None:
            thread.join(timeout=max(1.0, float(interval) + 1.0))
