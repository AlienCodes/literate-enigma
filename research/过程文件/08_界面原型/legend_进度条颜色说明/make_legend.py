"""用真实的 render_progress_html 画出进度条的 5 种状态（手册用的图例）。"""
import sys
import time

sys.path.insert(0, "<仓库>")
from voicetwin.utils import progress as P  # noqa: E402

STAGES = [(0.0, "启动合成引擎"), (0.05, "逐句生成"), (0.9, "拼接、导出音频和字幕")]


def tracker():
    t = P.ProgressTracker(stages=STAGES, title="生成讲课音频")
    t.started = time.time() - 185 if hasattr(t, "started") else None
    return t


def snap_running():
    t = P.ProgressTracker(stages=STAGES, title="生成讲课音频")
    for i, f in enumerate([0.1, 0.2, 0.3, 0.4, 0.46]):
        t(f, f"逐句生成 第 {i + 3}/12 句")
        time.sleep(0.05)
    s = t.snapshot()
    return s


runs = snap_running()
stall = dict(runs); stall["level"] = "stall"; stall["idle"] = 420
t = P.ProgressTracker(stages=STAGES, title="生成讲课音频"); t(0.3, "逐句生成 第 4/12 句"); t.finish(False, "讲稿里有一句太长，模型读不了", advice="在这句话中间加一个逗号或句号，再点「生成」。")
err = t.snapshot()
t = P.ProgressTracker(stages=STAGES, title="生成讲课音频"); t(0.55, "逐句生成 第 7/12 句"); t.finish(False, "", stopped=True)
stopped = t.snapshot()
t = P.ProgressTracker(stages=STAGES, title="生成讲课音频"); t(0.9, ""); t.finish(True, "")
done = t.snapshot()
runs.update(elapsed=372, idle=3, eta=360, eta_text="这一步大约还要 6 分钟", eta_total=420,
            eta_total_text="全部大约还要 7 分钟，预计 15:42 左右完成", msg="逐句生成 第 7/12 句（第 2 次尝试）")
stall.update(elapsed=980, idle=420, msg="逐句生成 第 7/12 句（第 2 次尝试）")
err.update(elapsed=145)
stopped.update(elapsed=260)
done.update(elapsed=1120, ended_clock="15:42")
for name, s in [("running", runs), ("stall", stall), ("error", err), ("stopped", stopped), ("done", done)]:
    print(name, {k: s.get(k) for k in ("status", "level", "pct", "elapsed", "eta")})
html = ["<!doctype html><meta charset=utf-8><style>body{font-family:'Noto Sans CJK SC',sans-serif;margin:0;padding:12px;width:1100px;background:#fff;"
        "--body-text-color:#1f2937;--body-text-color-subdued:#6b7280;--background-fill-secondary:#f9fafb;--border-color-primary:#e5e7eb;color:#1f2937}"
        ".cap{font-weight:700;margin:14px 0 4px;font-size:15px}</style><style>" + P.PROGRESS_CSS + "</style>"]
caps = {"running": "① 绿色：正在正常工作", "stall": "② 黄色：好几分钟没有新进度", "error": "③ 红色：出问题停下了",
        "stopped": "④ 灰色：你点了停止", "done": "⑤ 实心绿色 100%：全部完成"}
for name, s in [("running", runs), ("stall", stall), ("error", err), ("stopped", stopped), ("done", done)]:
    html.append(f'<div class="cap">{caps[name]}</div>' + P.render_progress_html(s))
open("legend.html", "w", encoding="utf-8").write("".join(html))
