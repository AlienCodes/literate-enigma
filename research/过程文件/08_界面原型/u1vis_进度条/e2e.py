import sys
import time

sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-3")
import gradio as gr

from voicetwin.utils.log import get_logger
from voicetwin.utils.progress import PROGRESS_CSS, PROGRESS_JS
from voicetwin.webui.tasks import stream_task, task_banner_md

log = get_logger("e2e")
STAGES = [(0.0, "整理要处理的文件"), (0.2, "识别每段话的文字"), (0.9, "保存结果")]


def job(n, progress=None):
    for i in range(n):
        progress(0.2 + 0.7 * (i + 1) / n, f"识别 {i + 1}/{n}：第 {i + 1} 段")
        log.info(f"识别了第 {i + 1} 段")
        time.sleep(0.5)
    return f"做完了 {n} 段"


def do_run():
    for text, state in stream_task("prepare", "准备素材", "我的声音", job, 16, stages=STAGES,
                                   note="可以去做别的事，但不要关闭运行程序的窗口。"):
        if state.get("done"):
            res = state.get("value") or ("busy" if state.get("busy") else "")
            yield state["bar"], text, str(res), gr.update(interactive=True, value="开始准备素材")
        else:
            yield state["bar"], text, gr.update(), gr.update(interactive=False, value="⏳ 正在准备素材……")


with gr.Blocks(css=PROGRESS_CSS, js=PROGRESS_JS, title="声音分身 VoiceTwin") as demo:
    banner = gr.Markdown()
    btn = gr.Button("开始准备素材", variant="primary")
    bar = gr.HTML("", elem_classes="vt-bar-box")
    with gr.Accordion("详细过程", open=False):
        logbox = gr.Textbox(label="运行记录", lines=5)
    res = gr.Markdown()
    btn.click(do_run, None, [bar, logbox, res, btn], show_progress="hidden", concurrency_limit=None)
    demo.load(task_banner_md, None, banner)

demo.queue().launch(server_name="127.0.0.1", server_port=int(sys.argv[1]))
