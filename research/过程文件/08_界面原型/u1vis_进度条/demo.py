import sys
sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-3")
import gradio as gr
from voicetwin.utils.progress import (ProgressTracker, render_progress_html, render_notice_html,
                                      PROGRESS_CSS, PROGRESS_JS)

STAGES = [(0.00, "整理要处理的文件"), (0.02, "提取声音、降噪、切成小段"), (0.40, "识别每段话的文字"),
          (0.74, "分析语速和停顿"), (0.80, "检查是不是你本人的声音"), (0.90, "挑选参考音频、保存结果"),
          (0.95, "分析你的说话风格")]


class C:
    t = 1_790_000_000.0

    def __call__(self):
        return self.t


def mk(status, idle=0):
    c = C()
    t = ProgressTracker(STAGES, title="准备素材", clock=c)
    c.t += 40
    t(0.30, "[第 2/3 个文件] 降噪、统一音量")
    c.t += 200
    t(0.45, "识别 120/800：大家好，今天我们来学习 Python 里面的列表推导式，这是一个很长的句子会被截断")
    if status == "done":
        t.finish(True)
    if status == "error":
        t.finish(False, "显卡内存（显存）不够",
                 advice="关掉游戏、剪映、在线视频等占用显卡的程序，再点一次；训练时可以打开「高级设置」，把「每批数量」改成 2。")
    if status == "stopped":
        t.finish(False, "已按你的要求停止", stopped=True)
    c.t += idle
    return t.snapshot()


running = render_progress_html(mk("running"), note="运行期间电脑不会自动睡眠；可以去做别的事，但不要关闭黑色窗口。")
fresh = render_progress_html(ProgressTracker(STAGES, title="训练模型", hint="训练通常要 30~90 分钟").snapshot())
beat = render_progress_html(mk("running", idle=90))
stall = render_progress_html(mk("running", idle=400))
done = render_progress_html(mk("done"))
err = render_progress_html(mk("error"))
stopped = render_progress_html(mk("stopped"))
notice = render_notice_html("现在正在「训练模型」（声音：我的声音），已经进行 12 分 3 秒（35%）。同一时间只能做一件事，请等它完成后再点。\n进度可以在「② 训练模型」页看到。", "warn")

with gr.Blocks(css=PROGRESS_CSS, js=PROGRESS_JS, title="声音分身 VoiceTwin") as demo:
    gr.Markdown("# demo")
    for h in (fresh, running, beat, stall, done, err, stopped, notice):
        gr.HTML(h)
    gr.Textbox("log", label="运行记录")

demo.launch(server_name="127.0.0.1", server_port=int(sys.argv[1]))
