import gradio as gr, time
def gen(x, progress=None):
    for i in range(3):
        yield gr.update(value="⏳ 正在生成…", interactive=False), f"<div>{i}</div>", gr.update()
    yield gr.update(value="生成", interactive=True), "<div>done</div>", [[1,"00:03","你好","✅ 很像",""]]
with gr.Blocks() as app:
    with gr.Tab("③") as t3:
        q = gr.Radio([("快速试听（每句 1 遍）","fast"),("平衡（推荐）","balanced")], value="balanced")
        ref = gr.Dropdown([("自动挑选（推荐）","auto"),("中文·陈述·6.2秒：大家好","clip_001")], value="auto")
        fmt = gr.Radio([("WAV（剪映用）","wav"),("MP3（文件小）","mp3")], value="wav")
        b = gr.Button("生成", variant="primary")
        bar = gr.HTML()
        tbl = gr.Dataframe(headers=["第几句","开始","句子","像不像","提示"], datatype=["number","str","str","str","str"], interactive=False, wrap=True, column_widths=["8%","10%","52%","12%","18%"], height=400)
        a = gr.Audio(type="filepath", interactive=False, autoplay=True)
        redo1 = gr.Button("🔁 重新生成这一句", visible=False)
        lex = gr.Textbox(lines=8, label="读音纠正")
    ev = b.click(gen, [q], [b, bar, tbl], concurrency_id="synth")
    stop = gr.Button("停止", variant="stop")
    stop.click(None, None, None, cancels=[ev])
    def sel(table, evt: gr.SelectData):
        return gr.update(visible=True)
    tbl.select(sel, tbl, redo1)
    t3.select(lambda: "x", None, lex)
cfg = app.get_config_file()
print("ok", len(cfg["components"]), gr.__version__)
