import gradio as gr, time
CSS = ".vt-track{height:14px;border-radius:7px;background:var(--background-fill-secondary)} .vt-fill{height:100%;background:var(--color-accent);transition:width .5s}"
JS = "() => { window.vtBase = document.title; }"
with gr.Blocks(title="声音分身 VoiceTwin", css=CSS, js=JS, head="<script>window.vtDirty=false;</script>", delete_cache=(86400,86400)) as app:
    banner = gr.Markdown(visible=False)
    with gr.Tabs() as tabs:
        with gr.Tab("① 准备素材", id="prep") as t1:
            btn = gr.Button("开始", variant="primary")
            stop = gr.Button("⏹ 停止", variant="stop", visible=False)
            bar = gr.HTML("", elem_classes="vt-bar-box")
            with gr.Accordion("详细过程", open=False):
                logbox = gr.Textbox(lines=8, autoscroll=True, show_copy_button=True)
            md = gr.Markdown()
            q = gr.Radio([("快速试听","fast"),("标准（推荐）","balanced")], value="balanced")
            f = gr.File(file_types=[".txt",".md",".docx",".srt",".vtt"])
            df = gr.Dataframe(headers=["状态","项目","说明"], interactive=False, wrap=True, column_widths=["120px","200px","auto"])
        with gr.Tab("② 训练模型", id="train") as t2:
            go = gr.Button("去训练 →")
    def run(qv):
        yield gr.update(interactive=False), gr.update(visible=True), "<div class='vt-prog vt-running'>0%</div>", "", ""
        gr.Info("✅ 完成")
        yield gr.update(interactive=True), gr.update(visible=False), "<div class='vt-prog vt-done'>100%</div>", "log", "done"
    btn.click(run, q, [btn, stop, bar, logbox, md], show_progress="hidden", concurrency_id="gpu", concurrency_limit=1)
    go.click(lambda: gr.Tabs(selected="train"), None, tabs)
    t2.select(lambda: "selected", None, md)
    df.input(None, None, None, js="() => { window.vtDirty = true; }")
    app.load(lambda: gr.update(visible=True, value="x"), None, banner)
cfg = app.get_config_file()
print("ok", len(cfg["dependencies"]), [d.get("show_progress") for d in cfg["dependencies"]][:2], [d.get("concurrency_id") for d in cfg["dependencies"]][:2])
