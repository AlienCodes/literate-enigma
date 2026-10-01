"""voicetwin.webui.tasks：后台任务登记表、同一时间只做一件事、刷新后接上进度、停止。"""

import ast
import inspect
import logging
import threading
import time

import pytest

from voicetwin.utils.progress import TaskCancelled, check_cancel, clear_cancel
from voicetwin.utils.log import get_logger
from voicetwin.webui import tasks

log = get_logger("test_tasks")


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    monkeypatch.setattr(tasks, "POLL_SECONDS", 0.02)
    with tasks._LOCK:
        tasks._CURRENT = None
    clear_cancel()
    yield
    cur = tasks._CURRENT
    if cur is not None and cur.thread is not None:
        cur.thread.join(5)
    with tasks._LOCK:
        tasks._CURRENT = None
    clear_cancel()


def drain(gen):
    return list(gen)


def test_success_value_bar_and_lines():
    def job(a, b, progress=None):
        log.info("第一行")
        log.info("第二行")
        progress(0.5, "[1/2] x")
        log.info("第三行")
        return a + b

    out = drain(tasks.stream_task("prepare", "准备素材", "v", job, 40, 2,
                                  stages=[(0.0, "a"), (0.5, "b")], note="不要关闭窗口"))
    assert out  # 任务很快时，第一次产出可能就是最后一次
    assert all("done" not in s for _, s in out[:-1])
    text, state = out[-1]
    assert state["done"] is True and state["value"] == 42
    assert "error" not in state and "busy" not in state and "attached" not in state
    assert "vt-done" in state["bar"]
    assert state["snap"]["status"] == "done"
    for line in ("第一行", "第二行", "第三行"):
        assert line in text
    assert all("bar" in s for _, s in out)
    assert all(" | " in ln for ln in text.splitlines())  # 每行都带时间
    assert tasks.current_task()["ok"] is True


def test_first_yield_is_immediate():
    gate = threading.Event()

    def job(progress=None):
        gate.wait(5)
        return 1

    gen = tasks.stream_task("train", "训练模型", "v", job)
    t0 = time.time()
    text, state = next(gen)
    assert time.time() - t0 < 0.5
    assert "done" not in state
    assert "vt-running" in state["bar"]
    gate.set()
    rest = list(gen)
    assert rest[-1][1]["done"] is True and rest[-1][1]["value"] == 1


def test_error_is_friendly_and_has_no_traceback():
    def job(progress=None):
        progress(0.3, "识别 3/10")
        raise RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB")

    text, state = drain(tasks.stream_task("train", "训练模型", "v", job))[-1]
    assert state["done"] is True
    assert isinstance(state["error"], RuntimeError)
    friendly = state["friendly"]
    try:
        from voicetwin.errors import explain  # U5
    except ImportError:
        assert friendly.title.startswith("CUDA out of memory")
    else:
        assert friendly.title == explain(state["error"]).title
    assert "Traceback" not in text
    assert "❌ 出错了：" in text
    assert "vt-error" in state["bar"] and "原因：" in state["bar"] and "怎么办：" in state["bar"]
    assert state["snap"]["status"] == "error" and state["snap"]["pct"] == 30
    assert tasks.current_task()["ok"] is False


def test_explain_fallback_without_errors_module(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "voicetwin.errors":
            raise ImportError("not merged yet")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    f = tasks._explain(ValueError("x" * 500))
    assert f.title == "x" * 200 and f.advice == "" and "ValueError" in f.detail
    assert tasks._explain(MemoryError()).title == "MemoryError"


def test_busy_attach_banner():
    gate = threading.Event()
    started = threading.Event()

    def long_job(progress=None):
        started.set()
        progress(0.25, "训练音色：第 1/4 轮")
        gate.wait(5)
        return "ok"

    main = tasks.stream_task("train", "训练模型", "v", long_job)
    next(main)
    assert started.wait(2)

    # 另一件事：只产出一次，busy + done
    busy = drain(tasks.stream_task("generate", "生成讲课音频", "v", lambda progress=None: 1))
    assert len(busy) == 1
    text, state = busy[0]
    assert state["busy"] is True and state["done"] is True
    assert "vt-note-warn" in state["bar"]
    assert "现在正在「训练模型」（声音：v）" in text and "同一时间只能做一件事" in text
    assert "「② 训练模型」" in text

    # 同一种任务、换一个声音也不行
    other = drain(tasks.stream_task("train", "训练模型", "w", lambda progress=None: 1))
    assert len(other) == 1 and other[0][1]["busy"] is True

    # 横幅
    banner = tasks.task_banner_md()
    assert "后台正在「训练模型」" in banner and "「开始训练」" in banner
    info = tasks.current_task()
    assert info["running"] is True and info["ok"] is None and info["kind"] == "train"
    assert tasks.is_busy() is True

    # 同一种任务、同一个声音：接上，不重新开始
    att = tasks.stream_task("train", "训练模型", "v", lambda progress=None: "不应该运行")
    text, state = next(att)
    assert state["attached"] is True
    assert text.startswith(tasks.ATTACHED_NOTE)
    gate.set()
    rest = list(att)
    final = rest[-1][1] if rest else state
    assert final["done"] is True and final["value"] == "ok" and final["attached"] is True
    main_final = list(main)[-1][1]
    assert main_final["value"] == "ok"

    banner = tasks.task_banner_md()
    assert banner.startswith("✅ 上次的「训练模型」") and "完成" in banner
    assert tasks.is_busy() is False


def test_request_stop_marks_stopped_and_clears_flag():
    assert tasks.request_stop() is False  # 没有任务时什么都不做

    started = threading.Event()

    def job(progress=None):
        started.set()
        for i in range(500):
            progress(i / 500.0, f"{i}/500")
            time.sleep(0.01)
        return "不应该做完"

    gen = tasks.stream_task("generate", "生成讲课音频", "v", job)
    next(gen)
    assert started.wait(2)
    assert tasks.request_stop() is True
    text, state = list(gen)[-1]
    assert state["done"] is True and state["stopped"] is True
    assert "value" not in state and "error" not in state
    assert "vt-stopped" in state["bar"]
    assert "⏹ 已停止" in text
    check_cancel()  # 停止标记已经清掉，不影响下一次
    assert tasks.task_banner_md().startswith("⏹ 上次的「生成讲课音频」")

    # 停止之后可以马上开始新的任务
    out = drain(tasks.stream_task("generate", "生成讲课音频", "v", lambda progress=None: 7))
    assert out[-1][1]["value"] == 7


def test_task_survives_abandoned_generator():
    """网页刷新/关闭：gradio 不再迭代生成器。任务和日志收集都要继续。"""
    gate = threading.Event()

    def job(progress=None):
        gate.wait(5)
        log.info("网页断开以后写的日志")
        return 5

    gen = tasks.stream_task("prepare", "准备素材", "v", job)
    next(gen)
    gen.close()  # 模拟断开
    del gen
    gate.set()
    tasks._CURRENT.thread.join(5)
    info = tasks.current_task()
    assert info["running"] is False and info["ok"] is True
    assert "网页断开以后写的日志" in tasks._CURRENT.text()
    # 处理器已经从 logger 上拿掉
    assert not any(isinstance(h, tasks._LineHandler) for h in logging.getLogger("voicetwin").handlers)


def test_cancelled_base_exception_passes_except_exception():
    """后端里常见的 except Exception 不能吞掉停止信号。"""

    def job(progress=None):
        try:
            raise TaskCancelled("stop")
        except Exception:  # pragma: no cover - 不应该走到这里
            return "被吞掉了"

    state = drain(tasks.stream_task("prepare", "准备素材", "v", job))[-1][1]
    assert state["stopped"] is True


def test_explicit_progress_is_teed():
    seen = []

    def job(progress=None):
        progress(0.5, "一半")
        return 1

    state = drain(tasks.stream_task("prepare", "准备素材", "v", job,
                                    progress=lambda f, m: seen.append((f, m))))[-1][1]
    assert seen == [(0.5, "一半")]
    assert state["value"] == 1


def test_banner_empty_and_old_tasks(monkeypatch):
    assert tasks.task_banner_md() == ""
    assert tasks.current_task() is None
    drain(tasks.stream_task("download", "下载模型", "", lambda progress=None: []))
    assert "✅ 上次的「下载模型」" in tasks.task_banner_md()
    monkeypatch.setattr(tasks.time, "time", lambda: tasks._CURRENT.finished + 13 * 3600)
    assert tasks.task_banner_md() == ""


def test_banner_error_is_escaped():
    def job(progress=None):
        raise RuntimeError("坏了 <script>x</script>")

    drain(tasks.stream_task("prepare", "准备素材", "v", job))
    banner = tasks.task_banner_md()
    assert banner.startswith("❌ 上次的「准备素材」")
    assert "<script>" not in banner


def test_kind_labels_contract():
    assert tasks.KIND_LABELS == {"prepare": "准备素材", "train": "训练模型", "select": "重新挑选最佳模型",
                                 "generate": "生成讲课音频", "download": "下载模型"}
    assert tasks.POLL_SECONDS == 0.02  # 被测试改小了；默认值见下
    assert "POLL_SECONDS = 0.6" in inspect.getsource(tasks)


def test_no_gradio_import():
    tree = ast.parse(inspect.getsource(tasks))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert "gradio" not in names
