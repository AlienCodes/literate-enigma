"""voicetwin.utils.progress：进度状态、颜色状态、剩余时间、HTML、命令行进度行、下载进度。"""

import re
import threading
import time

import pytest

from voicetwin.utils import progress as P
from voicetwin.utils.progress import (
    PROGRESS_CSS,
    PROGRESS_JS,
    ProgressTracker,
    TaskCancelled,
    check_cancel,
    clear_cancel,
    console_line,
    console_reporter,
    format_clock,
    format_duration,
    format_elapsed,
    render_notice_html,
    render_progress_html,
    request_cancel,
    watch_download,
)

STAGES7 = [(0.00, "整理要处理的文件"), (0.02, "提取声音、降噪、切成小段"), (0.40, "识别每段话的文字"),
           (0.74, "分析语速和停顿"), (0.80, "检查是不是你本人的声音"), (0.90, "挑选参考音频、保存结果"),
           (0.95, "分析你的说话风格")]


class FakeClock:
    def __init__(self, t: float = 1_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, s: float) -> None:
        self.t += s


@pytest.fixture(autouse=True)
def _no_cancel():
    clear_cancel()
    yield
    clear_cancel()


def make(stages=None, **kw):
    clock = FakeClock()
    return ProgressTracker(stages, clock=clock, **kw), clock


# ---------------------------------------------------------------- 基本状态

def test_monotonic_and_clamped():
    t, _ = make()
    t(0.5)
    t(0.3)
    assert t.snapshot()["frac"] == 0.5
    t(7)
    assert t.snapshot()["frac"] == 1.0
    assert t.snapshot()["pct"] == 99  # 还没 finish，不显示 100%


def test_nan_and_garbage_ignored():
    t, _ = make()
    t(0.2)
    t(float("nan"), "")
    t("abc", "")  # type: ignore[arg-type]
    t(None, "")  # type: ignore[arg-type]
    snap = t.snapshot()
    assert snap["frac"] == 0.2
    assert snap["status"] == "running"


def test_counter_parsing():
    t, _ = make()
    t(0.1, "识别 120/800：大家好")
    s = t.snapshot()
    assert (s["step"], s["total"]) == (120, 800)
    assert s["unit"] == "段"
    assert P.counter_text(s) == "已完成 120 / 800 段"
    t(0.2, "训练音色：第 3/12 轮（45%）")
    s = t.snapshot()
    assert (s["step"], s["total"], s["unit"], s["ordinal"]) == (3, 12, "轮", True)
    assert P.counter_text(s) == "第 3 / 12 轮"
    t(0.3, "s2G.pth 120/3100 MB")
    assert P.counter_text(t.snapshot()) == "已下载 120 / 3100 MB"
    t(0.4, "没有数字")
    assert t.snapshot()["step"] is None
    t(0.5, "坏的 9/3")  # step > total：不要
    assert t.snapshot()["total"] is None


def test_msg_is_trimmed():
    t, _ = make()
    t(0.1, "第一行\n第二行   " + "长" * 500)
    msg = t.snapshot()["msg"]
    assert "\n" not in msg and len(msg) == 300


def test_stage_change_resets_stage_elapsed_and_counter():
    t, clock = make(STAGES7)
    t(0.0, "找到 3 个视频")
    s = t.snapshot()
    assert (s["stage_index"], s["stage_count"], s["stage_name"]) == (1, 7, "整理要处理的文件")
    t(0.1, "[第 1/3 个文件] 从视频里提取声音")
    clock.advance(50)
    t(0.3)
    assert t.snapshot()["stage_elapsed"] == pytest.approx(50)
    assert t.snapshot()["step"] == 1
    t(0.45)  # 换到第 3 步，且没有新说明：计数清空
    s = t.snapshot()
    assert s["stage_index"] == 3 and s["stage_name"] == "识别每段话的文字"
    assert s["stage_elapsed"] == pytest.approx(0)
    assert s["step"] is None
    assert s["elapsed"] == pytest.approx(50)


def test_no_stages_snapshot_keys():
    t, _ = make(title="下载模型")
    s = t.snapshot()
    for key in ("status", "frac", "pct", "title", "stage_index", "stage_count", "stage_name", "msg", "step",
                "total", "elapsed", "stage_elapsed", "eta", "eta_text", "idle", "hint", "run_id", "error",
                "eta_total", "eta_total_text", "finish_clock", "level"):
        assert key in s, key
    assert s["stage_index"] == 0 and s["stage_count"] == 0
    assert isinstance(s["run_id"], str) and s["run_id"]


def test_finish_states():
    t, clock = make(title="准备素材")
    t(0.4)
    clock.advance(30)
    t.finish(True)
    s = t.snapshot()
    assert (s["status"], s["level"], s["pct"], s["frac"]) == ("done", "done", 100, 1.0)
    clock.advance(100)
    assert t.snapshot()["elapsed"] == pytest.approx(30)  # 结束后用时不再增加
    t(0.1, "结束后再报不算数")
    assert t.snapshot()["status"] == "done"
    t.finish(False, "第二次 finish 不算数")
    assert t.snapshot()["status"] == "done"

    t2, _ = make()
    t2(0.3)
    t2.finish(False, "显卡内存不够", advice="关掉游戏再试")
    s = t2.snapshot()
    assert (s["status"], s["level"], s["error"], s["advice"]) == ("error", "error", "显卡内存不够", "关掉游戏再试")
    assert s["pct"] == 30

    t3, _ = make()
    t3.finish(False, "已按你的要求停止", stopped=True)
    assert t3.snapshot()["status"] == "stopped"
    assert t3.snapshot()["level"] == "stopped"


def test_on_update_called_and_errors_swallowed():
    seen = []
    t = ProgressTracker(on_update=lambda s: seen.append(s["frac"]))
    t(0.25, "x")
    t.finish(True)
    assert seen == [0.25, 1.0]

    def bad(_snap):
        raise RuntimeError("回调坏了")

    t2 = ProgressTracker(on_update=bad)
    t2(0.5, "仍然不能抛出")  # 不抛异常
    assert t2.snapshot()["frac"] == 0.5


def test_cancel():
    t, _ = make()
    request_cancel()
    assert t.snapshot()["stopping"] is True
    with pytest.raises(TaskCancelled):
        t(0.1, "x")
    with pytest.raises(TaskCancelled):
        check_cancel()
    assert issubclass(TaskCancelled, BaseException) and not issubclass(TaskCancelled, Exception)
    clear_cancel()
    t(0.2, "y")
    assert t.snapshot()["frac"] == 0.2
    check_cancel()


def test_thread_safety_many_writers():
    t = ProgressTracker([(0.0, "a"), (0.5, "b")])

    def worker(k):
        for i in range(200):
            t((k * 200 + i) / 1000.0, f"{i}/200")
            t.snapshot()

    threads = [threading.Thread(target=worker, args=(k,)) for k in range(5)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert t.snapshot()["frac"] == pytest.approx(0.999)


# ---------------------------------------------------------------- 剩余时间

def test_stage_eta_estimating_then_minutes():
    t, clock = make([(0.0, "第一步"), (0.5, "第二步")])
    t(0.0)
    clock.advance(10)
    t(0.1)  # p = 0.2，但才 10 秒
    assert "正在估算" in t.snapshot()["eta_text"]
    assert t.snapshot()["eta"] is None
    clock.advance(50)  # 60 秒做了 p=0.2 → 这一步一共 300 秒，还要 240 秒
    t(0.1)
    s = t.snapshot()
    assert s["eta"] == pytest.approx(240, abs=1)
    assert s["eta_text"] == "这一步大约还要 4 分钟"


def test_stage_eta_uses_hint_while_estimating():
    t, _ = make([(0.0, "a"), (0.5, "b")], hint="训练通常要 30~90 分钟")
    assert t.snapshot()["eta_text"] == "训练通常要 30~90 分钟"


def test_stage_eta_nearly_done():
    t, clock = make([(0.0, "a"), (0.5, "b")])
    clock.advance(30)
    t(0.495)
    assert t.snapshot()["eta_text"] == "这一步快好了"


def test_total_eta_needs_3_percent_and_30_seconds():
    t, clock = make(title="生成讲课音频")
    clock.advance(20)
    t(0.2)
    s = t.snapshot()
    assert s["eta_total"] is None and s["finish_clock"] == ""
    assert s["eta_total_text"] == "全部还要多久：正在估算……"
    t2, clock2 = make()
    clock2.advance(300)
    t2(0.02)  # 只有 2%
    assert t2.snapshot()["eta_total"] is None


def test_total_eta_and_finish_clock():
    t, clock = make(title="训练模型")
    clock.advance(60)
    t(0.1)  # 60 秒 10% → 一共 600 秒，还要 540 秒
    s = t.snapshot()
    assert s["eta_total"] == pytest.approx(540, abs=1)
    expected_clock = format_clock(clock.t + s["eta_total"], clock.t)
    assert s["finish_clock"] == expected_clock
    assert re.search(r"\d{2}:\d{2}$", s["finish_clock"])
    assert s["eta_total_text"] == f"全部大约还要 9 分钟，预计 {expected_clock} 左右完成"


def test_total_eta_is_smoothed():
    t, clock = make()
    clock.advance(60)
    t(0.1)  # 一共 600
    first = t.snapshot()["eta_total"]
    clock.advance(1)
    t(0.3)  # 原始估计突然变成 61/0.3 ≈ 203 秒一共
    smoothed = t.snapshot()["eta_total"]
    raw_left = 61 / 0.3 - 61
    assert raw_left < smoothed < first  # 平滑：在新旧之间，不会一下子跳过去
    # 0.6 秒刷一次不应该让平滑变快
    before = t.snapshot()["eta_total"]
    clock.advance(0.5)
    t.snapshot()
    clock.advance(0.1)
    after = t.snapshot()["eta_total"]
    assert after == pytest.approx(before - 0.6, abs=0.01)


def test_total_eta_not_stuck_after_long_gap():
    """很久没人看（网页关掉一阵又接上）时，不能被很久以前的估计拖住，说成“快完成了”。"""
    t, clock = make()
    clock.advance(40)
    t(0.3)  # 一共约 133 秒
    clock.advance(200)
    t(0.45)  # 240 秒才 45%：一共约 533 秒，还要约 293 秒
    left = t.snapshot()["eta_total"]
    assert left == pytest.approx(240 / 0.45 - 240, rel=0.02)
    assert "快完成" not in t.snapshot()["eta_total_text"]


def test_total_eta_grows_while_idle_and_hidden_when_done():
    t, clock = make()
    clock.advance(60)
    t(0.5)
    a = t.snapshot()["eta_total"]
    clock.advance(120)  # 卡住两分钟：估计不应该越来越少
    for _ in range(20):
        clock.advance(1)
        t.snapshot()
    b = t.snapshot()["eta_total"]
    assert b > a
    t.finish(True)
    s = t.snapshot()
    assert s["eta_total"] is None and s["eta_total_text"] == "" and s["finish_clock"] == ""


def test_level_stall_after_180s_and_only_changes_count():
    t, clock = make()
    t(0.1, "识别 1/10")
    clock.advance(100)
    t(0.1, "识别 1/10")  # 一模一样的重复报告不算新进度
    assert t.snapshot()["level"] == "ok"
    clock.advance(90)
    s = t.snapshot()
    assert s["idle"] == pytest.approx(190)
    assert s["level"] == "stall"
    t(0.11, "识别 2/10")
    assert t.snapshot()["level"] == "ok"
    assert t.snapshot()["idle"] == 0


# ---------------------------------------------------------------- 格式

@pytest.mark.parametrize("s,expected", [
    (0, "不到 1 分钟"), (59, "不到 1 分钟"), (60, "约 1 分钟"), (89, "约 1 分钟"), (90, "约 2 分钟"),
    (12 * 60, "约 12 分钟"), (3599, "约 1 小时"), (3600, "约 1 小时"), (3900, "约 1 小时 5 分"),
    (2 * 3600 + 30 * 60, "约 2 小时 30 分"), (float("nan"), "不到 1 分钟"), (None, "不到 1 分钟"),
])
def test_format_duration(s, expected):
    assert format_duration(s) == expected


@pytest.mark.parametrize("s,expected", [
    (0, "0 秒"), (45, "45 秒"), (45.9, "45 秒"), (60, "1 分 0 秒"), (200, "3 分 20 秒"),
    (3600 + 5 * 60, "1 小时 05 分"), (10 * 3600 + 59 * 60 + 59, "10 小时 59 分"), (-5, "0 秒"),
])
def test_format_elapsed(s, expected):
    assert format_elapsed(s) == expected


def test_format_clock_days():
    base = time.mktime((2026, 10, 1, 21, 0, 0, 0, 0, -1))
    assert format_clock(base + 40 * 60, base) == "21:40"
    assert format_clock(base + 4 * 3600, base) == "明天 01:00"
    assert format_clock(base + 3 * 86400, base) == "10月4日 21:00"
    assert format_clock("bad", base) == ""


# ---------------------------------------------------------------- HTML

def snap_for(status="running", **over):
    t, clock = make(STAGES7, title="准备素材", hint="")
    t(0.45, "识别 120/800：大家好")
    if status == "done":
        t.finish(True)
    elif status == "error":
        t.finish(False, "显卡内存（显存）不够", advice="关掉游戏再点一次")
    elif status == "stopped":
        t.finish(False, "已按你的要求停止", stopped=True)
    s = t.snapshot()
    s.update(over)
    return s


def test_html_escapes_everything():
    s = snap_for(msg="<script>alert(1)</script>", title='"><img src=x>')
    out = render_progress_html(s, note="<b>注意</b>")
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "<img" not in out and "<b>注意" not in out
    err = snap_for("error", error="<b>坏</b>", advice="<i>x</i>")
    out = render_progress_html(err)
    assert "<b>坏" not in out and "&lt;b&gt;坏" in out and "<i>x" not in out


@pytest.mark.parametrize("status", ["running", "done", "error", "stopped"])
def test_html_status_classes(status):
    out = render_progress_html(snap_for(status))
    assert f'class="vt-prog vt-{status}' in out
    assert f'data-status="{status}"' in out
    assert 'class="vt-track"' in out and 'class="vt-fill"' in out


def test_html_running_layout():
    out = render_progress_html(snap_for(), note="可以去做别的事")
    assert 'data-pct="45"' in out and "width:45%" in out
    assert 'data-title="45% 识别每段话的文字"' in out
    assert "第 3 步（共 7 步）：识别每段话的文字" in out
    assert "已完成 120 / 800 段" in out
    assert "已用 0 秒" in out
    assert "正在估算……" in out  # 还估不出来时不编数字
    assert "现在：识别 120/800：大家好" in out
    assert "可以去做别的事" in out
    assert "绿色条纹在动" in out
    assert "vt-stall" not in out


def test_html_shows_total_eta_when_known():
    t, clock = make(STAGES7, title="准备素材")
    clock.advance(120)
    t(0.4)
    out = render_progress_html(t.snapshot())
    assert "全部大约还要 3 分钟，预计" in out and "左右完成" in out
    assert "正在估算" not in out.split("vt-eta")[1].split("</div>")[0]


def test_html_heartbeat_and_stall():
    beat = render_progress_html(snap_for(idle=90, level="ok"))
    assert "仍在工作中：已经 1 分 30 秒没有新进度" in beat
    assert "vt-stall" not in beat
    stall = render_progress_html(snap_for(idle=200, level="stall"))
    assert "vt-running vt-stall" in stall and 'data-level="stall"' in stall
    assert "已经 3 分钟没有新进度：这一步可能比较慢，也可能卡住了。请先等一等，不要关闭黑色窗口。" in stall
    assert "🟡" in stall


def test_html_done_error_stopped_texts():
    done = render_progress_html(snap_for("done"))
    assert "✅ 全部完成！用时" in done and "width:100%" in done and 'data-pct="100"' in done
    err = render_progress_html(snap_for("error"))
    assert "❌ 没有完成：停在第 3 步「识别每段话的文字」" in err
    assert "原因：</b>显卡内存（显存）不够" in err and "怎么办：</b>关掉游戏再点一次" in err
    no_advice = render_progress_html(snap_for("error", advice=""))
    assert "怎么办：</b>" in no_advice  # 没有具体建议时也给一句通用的
    stopped = render_progress_html(snap_for("stopped"))
    assert "⏹ 已停止" in stopped and "停在第 3 步「识别每段话的文字」" in stopped


def test_html_stopping_line():
    out = render_progress_html(snap_for(stopping=True))
    assert "正在停止" in out


def test_html_empty_and_partial_snaps():
    assert render_progress_html({}) == ""
    assert render_progress_html(None) == ""  # type: ignore[arg-type]
    out = render_progress_html({"status": "running", "pct": 12})
    assert 'data-pct="12"' in out and "正在处理" in out


def test_notice_html():
    out = render_notice_html("第一行\n<第二行>", "warn")
    assert 'class="vt-note vt-note-warn"' in out
    assert "第一行<br>&lt;第二行&gt;" in out
    assert "vt-note-info" in render_notice_html("x", "nonsense")
    for tone in ("info", "warn", "error", "ok"):
        assert f"vt-note-{tone}" in render_notice_html("x", tone)


def test_css_has_all_states_and_colors():
    css = PROGRESS_CSS
    for needle in (".vt-prog", ".vt-head", ".vt-track", ".vt-fill", ".vt-running .vt-fill", ".vt-stall",
                   ".vt-done", ".vt-error", ".vt-stopped", ".vt-note-warn", "@keyframes vt-move",
                   "#16a34a", "#d97706", "#dc2626", "#6b7280", "animation:vt-move", "var(--body-text-color-subdued)"):
        assert needle in css, needle
    assert ".dark" not in css  # gradio 4.24 会特殊处理含 .dark 的规则；这里只用主题变量
    assert css.count("{") == css.count("}")


def test_js_is_an_arrow_function():
    js = PROGRESS_JS.strip()
    assert js.startswith("() =>") and js.endswith("}")
    assert "MutationObserver" in js and "vt-running" in js and "880" in js
    assert js.count("{") == js.count("}") and js.count("(") == js.count(")")


# ---------------------------------------------------------------- 命令行

def test_console_line():
    s = snap_for()
    line = console_line(s)
    assert line.startswith("⏳ 45% ｜第 3/7 步 识别每段话的文字｜已完成 120 / 800 段｜已用 0 秒")
    assert "\r" not in line
    assert console_line(snap_for("done")).startswith("✅ 完成，用时")
    assert console_line(snap_for("error")).startswith("❌ 没有完成（停在第 3 步「识别每段话的文字」）：显卡内存")
    assert console_line(snap_for("stopped")).startswith("⏹ 已停止")
    t, clock = make(title="训练模型")
    clock.advance(60)
    t(0.1, "训练音色：第 1/12 轮（20%）")
    line = console_line(t.snapshot())
    assert "第 1 / 12 轮" in line and "全部大约还要 9 分钟，预计" in line
    assert "没有新进度" in console_line(dict(t.snapshot(), level="stall", idle=240))


def test_console_reporter_throttles():
    lines = []
    clock = FakeClock()
    t = ProgressTracker([(0.0, "a"), (0.5, "b")], clock=clock,
                        on_update=console_reporter(lines.append, min_interval=30.0, pct_step=5))
    t(0.0, "开始")
    assert len(lines) == 1  # 第一次一定打印
    for i in range(1, 40):  # 0.1% 一点点地涨、时间也不到 30 秒
        clock.advance(0.5)
        t(i / 1000.0)
    assert len(lines) == 1
    t(0.05)  # 跨过 5%
    assert len(lines) == 2
    t(0.06)
    assert len(lines) == 2
    clock.advance(31)  # 超过 30 秒：打印一次心跳
    t(0.061)
    assert len(lines) == 3
    t(0.062)
    assert len(lines) == 3
    t(0.5)  # 换步骤
    assert len(lines) == 4
    t.finish(True)
    assert len(lines) == 5 and lines[-1].startswith("✅ 完成")
    rep = t.on_update
    rep(t.snapshot())  # 同一个结束状态不重复打印
    assert len(lines) == 5


# ---------------------------------------------------------------- 下载进度

def test_watch_download_reports_growing_size(tmp_path):
    calls = []
    lock = threading.Lock()

    def progress(frac, msg):
        with lock:
            calls.append((frac, msg))

    target = tmp_path / "models--Systran--faster-whisper-small" / "blobs"
    target.mkdir(parents=True)
    with watch_download(tmp_path, 4, progress, 0.40, 0.44, "识别模型", interval=0.05, stall_seconds=60):
        for k in range(3):
            (target / f"part{k}.incomplete").write_bytes(b"\0" * (1024 * 1024))
            time.sleep(0.2)
    n = len(calls)
    time.sleep(0.2)
    assert len(calls) == n  # 退出后线程停了
    fracs = [f for f, _ in calls]
    assert fracs == sorted(fracs) and len(set(fracs)) >= 2
    assert all(0.40 <= f < 0.44 for f in fracs)
    assert any("3 / 4 MB" in m for _, m in calls)
    assert "第一次使用，正在下载识别模型" in calls[-1][1]


def test_watch_download_stall_message_and_swallows_errors(tmp_path):
    calls = []

    def progress(frac, msg):
        calls.append(msg)
        raise TaskCancelled("在线程里被吞掉")

    with watch_download(tmp_path / "missing", 100, progress, 0.0, 1.0, "模型", interval=0.02, stall_seconds=0.1):
        time.sleep(0.4)
    assert calls and any("下载好像停住了" in m for m in calls)


def test_watch_download_without_progress_is_noop(tmp_path):
    with watch_download(tmp_path, 10, None, 0.0, 1.0, "模型"):
        pass


def test_no_gradio_import():
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(P))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert "gradio" not in names
