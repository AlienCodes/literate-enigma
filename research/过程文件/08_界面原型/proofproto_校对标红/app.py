# Prototype: gradio 4.24 Dataframe with markdown / html display columns + Styler.
import html as _html
import sys
import warnings

import gradio as gr
import pandas as pd

RED = '<span style="color:#dc2626;font-weight:700;background:#fee2e2">'


def render_marked(text, spans):
    out, pos = [], 0
    for s, e in sorted(spans):
        out.append(_html.escape(text[pos:s]))
        out.append(RED + _html.escape(text[s:e]) + "</span>")
        pos = e
    out.append(_html.escape(text[pos:]))
    return "".join(out)


MD_ESC = {c: "&#%d;" % ord(c) for c in "\\`*_{}[]()#+-.!|~>$"}


def md_safe(s):
    # escape markdown-significant characters inside an already-HTML-escaped string
    return "".join(MD_ESC.get(c, c) for c in s)


def render_marked_md(text, spans):
    out, pos = [], 0
    for s, e in sorted(spans):
        out.append(md_safe(_html.escape(text[pos:s])))
        out.append(RED + md_safe(_html.escape(text[s:e])) + "</span>")
        pos = e
    out.append(md_safe(_html.escape(text[pos:])))
    return "".join(out)


ROWS = [
    ("c_0001", "我们今天讲 VFIXED 的用法，这个函数很常用。", [(6, 12)]),
    ("c_0002", "1. 首先打开 *设置* 页面_然后点保存", [(9, 11)]),
    ("c_0003", "这个户字的意思是 whose，大家记一下。", [(2, 4)]),
    ("c_0004", "<b>不是粗体</b> & 没有错的句子。", []),
    ("c_0005", "XSS测试 <img src=x onerror=\"window.__xss=(window.__xss||0)+1\">", []),
]


def table(kind):
    rows = []
    for i, (cid, text, spans) in enumerate(ROWS, 1):
        if kind == "md":
            disp = render_marked_md(text, spans) if spans else md_safe(_html.escape(text))
        elif kind == "html":
            disp = render_marked(text, spans) if spans else _html.escape(text)
        elif kind == "raw_html":   # unescaped user text -> shows XSS behaviour of datatype=html
            disp = text
        else:  # plain fallback with 【】
            disp = text
            for s, e in sorted(spans, reverse=True):
                disp = disp[:s] + "【" + disp[s:e] + "】" + disp[e:]
        rows.append([i, cid, text, disp])
    return pd.DataFrame(rows, columns=["#", "id", "文字", "可能有错（红色）"])


def styled():
    df = table("plain")
    flagged = {cid for cid, _t, sp in ROWS if sp}

    def row_style(r):
        bad = r["id"] in flagged
        return ["", "", "background-color:#fee2e2;color:#991b1b" if bad else "", ""]

    return df.style.apply(row_style, axis=1)


with gr.Blocks() as demo:
    gr.Markdown("gradio " + gr.__version__ + " / pandas " + pd.__version__)
    with gr.Row():
        out = gr.Textbox(label="select → id", elem_id="selout")
    df_md = gr.Dataframe(value=table("md"), datatype=["number", "str", "str", "markdown"],
                         interactive=True, wrap=True, label="A: markdown column (interactive)", elem_id="df_md")
    df_html = gr.Dataframe(value=table("html"), datatype=["number", "str", "str", "html"],
                           interactive=True, wrap=True, label="B: html column (interactive)", elem_id="df_html")
    df_raw = gr.Dataframe(value=table("raw_html"), datatype=["number", "str", "str", "html"],
                          interactive=False, wrap=True, label="C: html column with UNESCAPED text (XSS check)", elem_id="df_raw")
    df_mdraw = gr.Dataframe(value=table("raw_html"), datatype=["number", "str", "str", "markdown"],
                            interactive=False, wrap=True, label="G: markdown column with UNESCAPED text (sanitize check)", elem_id="df_mdraw")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        df_sty_i = gr.Dataframe(value=styled(), interactive=True, wrap=True,
                                label="D: pandas Styler, interactive=True", elem_id="df_sty_i")
        df_sty_n = gr.Dataframe(value=styled(), interactive=False, wrap=True,
                                label="E: pandas Styler, interactive=False", elem_id="df_sty_n")
        print("WARNINGS:", [str(x.message) for x in w], flush=True)
    df_plain = gr.Dataframe(value=table("plain"), interactive=True, wrap=True,
                            label="F: plain text fallback with 【】", elem_id="df_plain")
    echo = gr.Textbox(label="change → backend value of col 3 row 1 (A)", elem_id="echo")

    def on_select(tbl, evt: gr.SelectData):
        row = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
        return f"index={evt.index} value={evt.value!r} id_from_table={tbl.iloc[int(row)]['id']}"

    df_md.select(on_select, df_md, out)
    df_md.change(lambda t: repr(t.iloc[0, 3]) if len(t) else "", df_md, echo)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7880
    demo.launch(server_name="127.0.0.1", server_port=port, show_api=False)
