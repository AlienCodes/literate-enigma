"""网页里的后台任务登记表：同一时间只做一件事；刷新或关掉网页后，任务继续在后台做，再点同一个按钮能接上进度。

这个文件不能 import gradio（测试环境的 gradio 版本和整合包里的 4.24 不一样）。

为什么日志收集器挂在“后台线程”上而不是挂在网页的生成器上：
gradio 4.24 在网页断开（刷新或关闭）时会直接停止迭代生成器（routes.py / queueing.py），
被丢下的生成器的 finally 不一定会执行。所以日志收集、结束标记都由后台线程自己负责。
"""

import collections
import html
import logging
import os
import threading
import time
from typing import Any, Callable, Deque, Dict, Generator, List, Optional, Sequence, Tuple

from voicetwin.utils.log import get_logger
from voicetwin.utils.progress import (
    ProgressTracker,
    Stage,
    TaskCancelled,
    clear_cancel,
    format_elapsed,
    render_notice_html,
    render_progress_html,
    request_cancel,
)

log = get_logger("tasks")

POLL_SECONDS = 0.6
#: 第二次产出至少在第一次之后 FIRST_GAP_FACTOR × POLL_SECONDS 秒（见 _follow 里的说明）
FIRST_GAP_FACTOR = 2.0
MAX_LINES = 2000
#: 网页上一次最多显示多少行运行记录
SHOW_LINES = 400
#: 上次的任务结束后，横幅还提示多久
BANNER_KEEP_SECONDS = 12 * 3600

KIND_LABELS = {
    "prepare": "准备素材",
    "train": "训练模型",
    "select": "重新挑选最佳模型",
    "generate": "生成讲课音频",
    "download": "下载模型",
    "proofcheck": "查找可能的错字",
    "speed": "试听语速",
    "verify": "机器鉴别",
    "blind": "生成盲听测试",
}
#: 每种任务的进度在哪个页面、点哪个按钮能看到（用在提示文字里）
KIND_TABS = {
    "prepare": "① 准备素材",
    "proofcheck": "① 准备素材",
    "train": "② 训练模型",
    "select": "② 训练模型",
    "generate": "③ 生成讲课音频",
    "narrate": "③ 生成讲课音频",
    "speed": "③ 生成讲课音频",
    "verify": "⑤ 鉴别",
    "blind": "⑤ 鉴别",
    "download": "🩺 环境检查",
}
KIND_BUTTONS = {
    "prepare": "开始准备素材",
    "proofcheck": "🔍 自动查找可能的错字",
    "train": "开始训练",
    "select": "重新挑选最佳模型",
    "generate": "生成",
    "narrate": "生成",
    "speed": "▶ 试听语速",
    "verify": "开始鉴别",
    "blind": "生成盲听测试",
    "download": "⬇️ 下载缺少的模型",
}

ATTACHED_NOTE = "（已接上正在进行的任务，不会重新开始；新选的内容要等它完成后再点一次）"
STOPPED_LOG = "⏹ 已停止。已经做好的部分不会丢。"


class _Task:
    def __init__(self, kind: str, label: str, voice: str, tracker: ProgressTracker):
        self.kind = kind
        self.label = label
        self.voice = voice
        self.tracker = tracker
        self.lines: Deque[str] = collections.deque(maxlen=MAX_LINES)
        self.lines_lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.state: Dict[str, Any] = {}
        self.started = time.time()
        self.finished: Optional[float] = None

    def alive(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def add_line(self, line: str) -> None:
        with self.lines_lock:
            self.lines.append(line)

    def text(self, limit: int = SHOW_LINES) -> str:
        with self.lines_lock:
            lines = list(self.lines)
        return "\n".join(lines[-limit:])


_CURRENT: Optional[_Task] = None
_LOCK = threading.Lock()


class _LineHandler(logging.Handler):
    """把日志一行一行收进任务的缓冲区。

    故意不带 exc_info（出错时的英文 Traceback）：那些只写到黑色窗口和这个声音的 voicetwin.log 里，
    不显示在网页上，免得吓到人。"""

    def __init__(self, task: _Task):
        super().__init__()
        self.task = task

    def emit(self, record: logging.LogRecord) -> None:
        try:
            stamp = time.strftime("%H:%M:%S", time.localtime(record.created))
            self.task.add_line(f"{stamp} | {record.getMessage()}")
        except Exception:
            pass


class _FallbackFriendly:
    """voicetwin.errors 还不存在时（各部分分开合并）用的简单版出错说明。"""

    def __init__(self, title: str, advice: str = "", detail: str = ""):
        self.title = title
        self.advice = advice
        self.detail = detail

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"Friendly(title={self.title!r}, advice={self.advice!r})"


def _explain(exc: BaseException) -> Any:
    """优先用 voicetwin.errors.explain 把报错翻成大白话；没有这个模块或它出错时退回 str(exc)。"""
    try:
        from voicetwin.errors import explain  # type: ignore
    except ImportError:
        explain = None
    if explain is not None:
        try:
            f = explain(exc)
            if getattr(f, "title", ""):
                return f
        except Exception:
            pass
    title = str(exc).strip()[:200] or type(exc).__name__
    return _FallbackFriendly(title=title, advice="", detail=repr(exc)[:2000])


def _log_file_hint(voice: str) -> str:
    """告诉用户详细的出错信息存在哪里。"""
    files: List[str] = []
    for h in logging.getLogger("voicetwin").handlers:
        name = getattr(h, "baseFilename", "")
        if isinstance(h, logging.FileHandler) and name:
            files.append(str(name))
    if voice:
        marker = os.sep + voice + os.sep
        for name in reversed(files):
            if marker in name:
                return f"（详细的出错信息已保存在：{name}）"
    return "（详细的英文出错信息显示在黑色窗口里，需要时可以截图发给帮你的人）"


def _tab(kind: str) -> str:
    return KIND_TABS.get(kind, "")


def _voice_part(voice: str) -> str:
    return f"（声音：{voice}）" if voice else ""


def _tee(tracker: ProgressTracker, other: Callable[[float, str], Any]) -> Callable[[float, str], None]:
    """调用方自己也传了 progress 时，两边都报。"""

    def progress(frac: float, msg: str = "") -> None:
        tracker(frac, msg)  # 可能抛出 TaskCancelled，必须传出去
        try:
            other(frac, msg)
        except Exception:
            pass

    return progress


def _run(task: _Task, fn: Callable[..., Any], args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> None:
    """后台线程：真正执行任务。日志收集器跟着线程走，网页断开也不影响。"""
    handler = _LineHandler(task)
    vlog = logging.getLogger("voicetwin")
    vlog.addHandler(handler)
    try:
        task.state["value"] = fn(*args, **kwargs)
        task.tracker.finish(True)
    except TaskCancelled:
        task.state["stopped"] = True
        task.tracker.finish(False, "已按你的要求停止", stopped=True)
        log.info(STOPPED_LOG)
    except Exception as exc:
        f = _explain(exc)
        task.state.update(error=exc, friendly=f)
        task.tracker.finish(False, f.title, advice=getattr(f, "advice", "") or "")
        log.error("❌ 出错了：" + f.title + ("。怎么办：" + f.advice if getattr(f, "advice", "") else ""),
                  exc_info=True)
        log.info(_log_file_hint(task.voice))
    except BaseException as exc:  # SystemExit / KeyboardInterrupt 等：不让线程悄悄死掉
        f = _explain(exc)
        task.state.update(error=exc, friendly=f)
        task.tracker.finish(False, "任务意外中断：" + f.title)
        log.error("❌ 任务意外中断：" + f.title, exc_info=True)
    finally:
        task.finished = time.time()
        vlog.removeHandler(handler)
        clear_cancel()  # 不让这次的“停止”影响下一次


def _busy_message(cur: _Task) -> str:
    snap = cur.tracker.snapshot()
    tab = _tab(cur.kind)
    return (f"现在正在「{cur.label}」{_voice_part(cur.voice)}，已经进行 {format_elapsed(snap.get('elapsed'))}"
            f"（{snap.get('pct', 0)}%）。同一时间只能做一件事，请等它完成后再点。"
            + (f"进度可以在「{tab}」页看到。" if tab else ""))


def stream_task(kind: str, label: str, voice: str, fn: Callable[..., Any], *args: Any,
                stages: Optional[Sequence[Stage]] = None, hint: str = "", note: str = "",
                **kwargs: Any) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """在后台线程运行耗时任务，并不断产出 (运行记录文字, state)。

    state 里一定有 bar（进度条 HTML）；最后一次产出一定有 done=True，另外：
    - 成功：value；出错：error、friendly；停止：stopped=True；
    - 另一件事正在做：只产出一次，busy=True（文字是中文的说明，bar 是黄色提示）；
    - 同一种任务、同一个声音正在做：不重新开始，attached=True，跟着看它的进度。"""
    global _CURRENT
    voice = str(voice or "")
    label = str(label or KIND_LABELS.get(kind, kind))
    attached = False
    task: Optional[_Task] = None
    busy_msg = ""
    busy_state: Dict[str, Any] = {}
    with _LOCK:
        cur = _CURRENT
        if cur is not None and cur.alive():
            if cur.kind == kind and cur.voice == voice:
                task = cur
                attached = True
            else:
                busy_msg = _busy_message(cur)
                busy_state = {"busy": True, "done": True, "bar": render_notice_html(busy_msg, "warn")}
        else:
            tracker = ProgressTracker(stages, title=label, hint=hint)
            given = kwargs.get("progress")
            kwargs["progress"] = tracker if given is None else _tee(tracker, given)
            clear_cancel()
            task = _Task(kind, label, voice, tracker)
            task.thread = threading.Thread(target=_run, args=(task, fn, args, kwargs),
                                           name=f"voicetwin-{kind}", daemon=True)
            _CURRENT = task
            task.thread.start()
    if task is None:
        yield busy_msg, busy_state
        return
    yield from _follow(task, note, attached)


def _follow(task: _Task, note: str, attached: bool) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """跟着一个任务看进度：马上产出一次，之后每 POLL_SECONDS 秒一次，结束时最后产出一次（done=True）。"""
    view: Dict[str, Any] = {}
    if attached:
        view["attached"] = True
    prefix = (ATTACHED_NOTE + "\n") if attached else ""
    first_at: Optional[float] = None
    while True:
        alive = task.alive()
        snap = task.tracker.snapshot()
        if not alive and snap.get("status") == "running":
            # 线程已经结束但没有写结果（几乎不会发生）：当作意外中断
            task.tracker.finish(False, "任务意外中断了")
            snap = task.tracker.snapshot()
        view["snap"] = snap
        view["bar"] = render_progress_html(snap, note=note if alive else "")
        text = prefix + task.text()
        if not alive:
            for key in ("value", "error", "friendly", "stopped"):
                if key in task.state:
                    view[key] = task.state[key]
            view["done"] = True
            yield text, dict(view)
            return
        yield text, dict(view)  # 每次一个新的 dict，前面产出的不会被后面的改掉
        if first_at is None:
            first_at = time.time()
        if task.thread is not None:
            task.thread.join(POLL_SECONDS)  # 任务一结束马上返回，不用等满
        else:  # pragma: no cover - 不会发生
            time.sleep(POLL_SECONDS)
        # 第一次和第二次产出至少隔 FIRST_GAP_FACTOR × POLL_SECONDS（默认 1.2 秒）。浏览器里实测（gradio 4.24）：
        # 任务很快就做完时，头两次产出前后脚到达网页，偶尔第二次的「差异」会被原样当成新的值（Markdown 收到一个列表，
        # 报 x.trim is not a function），之后整个页面不再刷新、也换不了页。隔开一点，就不会挤在一起。
        wait = FIRST_GAP_FACTOR * POLL_SECONDS - (time.time() - first_at)
        if wait > 0:
            time.sleep(wait)


def current_task() -> Optional[Dict[str, Any]]:
    """正在做的任务，或者最近一次做完的任务；都没有时返回 None。"""
    with _LOCK:
        cur = _CURRENT
    if cur is None:
        return None
    running = cur.alive()
    snap = cur.tracker.snapshot()
    ok: Optional[bool] = None
    if not running:
        ok = snap.get("status") == "done"
    return {
        "kind": cur.kind,
        "label": cur.label,
        "voice": cur.voice,
        "running": running,
        "started": cur.started,
        "finished": cur.finished,
        "ok": ok,
        "snap": snap,
    }


def _md(s: Any) -> str:
    """给 Markdown 用：转义 HTML，避免出错信息里的 < > 被当成标签。"""
    return html.escape(str(s if s is not None else ""), quote=False)


def task_banner_md() -> str:
    """页面顶部的一行提示：后台正在做什么 / 上次做完了没有。没什么可说时返回 ''。"""
    info = current_task()
    if not info:
        return ""
    snap = info["snap"] or {}
    label = _md(info["label"])
    voice = _md(_voice_part(info["voice"]))
    if info["running"]:
        tab = _tab(info["kind"])
        button = KIND_BUTTONS.get(info["kind"], "")
        where = f"到「{tab}」页点「{button}」可以接着看进度，不会重新开始。" if tab and button else ""
        return (f"🔄 后台正在「{label}」{voice}，已经进行 {format_elapsed(snap.get('elapsed'))}，"
                f"完成 {snap.get('pct', 0)}%。{where}")
    finished = info.get("finished") or 0
    if not finished or time.time() - finished > BANNER_KEEP_SECONDS:
        return ""
    status = snap.get("status")
    if status == "done":
        hm = time.strftime("%H:%M", time.localtime(finished))
        return f"✅ 上次的「{label}」{voice}已经在 {hm} 完成。"
    if status == "stopped":
        return f"⏹ 上次的「{label}」{voice}已经按你的要求停止。"
    return f"❌ 上次的「{label}」{voice}没有完成：{_md(snap.get('error') or '出现了意外错误')}"


def request_stop() -> bool:
    """“停止”按钮：只有正在做事时才发出停止信号。返回是否真的发出了。"""
    with _LOCK:
        cur = _CURRENT
        if cur is None or not cur.alive():
            return False
        request_cancel()
    log.info(f"收到停止请求：等「{cur.label}」手上这一小步做完就停……")
    return True


def is_busy() -> bool:
    """现在有没有后台任务在做。"""
    with _LOCK:
        cur = _CURRENT
    return cur is not None and cur.alive()
