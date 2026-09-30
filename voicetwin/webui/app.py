"""VoiceTwin 网页界面（Gradio）。启动：voicetwin webui，然后浏览器打开 http://127.0.0.1:7860"""


import logging
import queue
import tempfile
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from voicetwin import workflows as wf
from voicetwin.config import Config
from voicetwin.utils.log import get_logger

log = get_logger("webui")

INTRO = """
# 🎙️ 声音分身 VoiceTwin
用你自己的讲课视频/录音，复刻你的**音色、语气和节奏**（中文 + 英文）。按 ①→②→③ 的顺序操作即可。
"""


class _QueueHandler(logging.Handler):
    def __init__(self, q: "queue.Queue[str]"):
        super().__init__()
        self.q = q
        self.setFormatter(logging.Formatter("%(asctime)s | %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.q.put(self.format(record))
        except Exception:
            pass


def stream_task(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
    """在后台线程运行耗时任务，同时把日志实时推送到界面。"""
    q: "queue.Queue[str]" = queue.Queue()
    handler = _QueueHandler(q)
    root = logging.getLogger("voicetwin")
    root.addHandler(handler)
    state: Dict[str, Any] = {}

    def target() -> None:
        try:
            state["value"] = fn(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - 交互路径
            state["error"] = exc
            q.put("❌ " + str(exc))
            q.put(traceback.format_exc())

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    lines: List[str] = []
    try:
        while thread.is_alive() or not q.empty():
            while not q.empty():
                lines.append(q.get())
            yield "\n".join(lines[-400:]), state
            time.sleep(0.6)
        while not q.empty():
            lines.append(q.get())
        state["done"] = True
        yield "\n".join(lines[-400:]), state
    finally:
        root.removeHandler(handler)


def _voices(cfg: Config) -> List[str]:
    return [v["voice"] for v in wf.list_voices(cfg)]


def _clips_table(cfg: Config, voice: str) -> List[List[Any]]:
    if not voice:
        return []
    project = wf.Project(cfg, voice)
    rows = []
    for r in project.load_manifest():
        rows.append([r["id"], "✔" if r.get("keep", True) else "✘", r.get("lang", ""), round(r.get("duration", 0), 1),
                     r.get("text", ""), r.get("drop_reason", "")])
    return rows


def _summary_md(s: Dict[str, Any]) -> str:
    if not s:
        return ""
    md = [f"### ✅ 素材准备完成：保留 **{s['clips_kept']}** / {s['clips_total']} 条，共 **{s['minutes_kept']}** 分钟",
          f"各语言分钟数：{s.get('minutes_by_lang', {})}；验证集 {s.get('val_clips', 0)} 条"]
    if s.get("dropped"):
        md.append("丢弃原因：" + "，".join(f"{k} {v} 条" for k, v in s["dropped"].items()))
    for w in s.get("warnings", []):
        md.append(f"> ⚠️ {w}")
    prof = s.get("profile") or {}
    if prof.get("rate"):
        rates = "，".join(f"{'中文' if k == 'zh' else '英文'} {v['p50']:.2f} 音节/秒" for k, v in prof["rate"].items())
        md.append(f"**你的语速**：{rates}")
    if prof.get("pauses"):
        p = prof["pauses"]
        md.append(f"**你的停顿习惯**：逗号 {p['clause']:.2f}s / 句号 {p['sentence']:.2f}s / 段落 {p['paragraph']:.2f}s")
    if s.get("references"):
        md.append("**自动挑选的参考音频**：\n" + "\n".join(f"- [{r['lang']}/{r['kind']}] {r['text']}" for r in s["references"][:12]))
    return "\n\n".join(md)


def build_app(cfg: Config):
    import gradio as gr

    backends = ["gptsovits", "qwen3tts", "indextts", "dummy"]
    default_backend = cfg.get("backend", "gptsovits")

    with gr.Blocks(title="声音分身 VoiceTwin") as app:
        gr.Markdown(INTRO)
        with gr.Row():
            voice = gr.Dropdown(choices=_voices(cfg), value=(_voices(cfg) or [None])[0], label="声音名称（新建请直接输入名字）",
                                allow_custom_value=True, scale=4)
            refresh = gr.Button("🔄 刷新", scale=1)
        refresh.click(lambda: gr.update(choices=_voices(cfg)), outputs=voice)

        # ------------------------------------------------------------ ① 准备素材
        with gr.Tab("① 准备素材"):
            gr.Markdown("上传你的**讲课视频或录音**（越多越好，建议总时长 ≥30 分钟，1~3 小时最佳；"
                        "只要你本人说话的部分）。如果视频有同名 `.srt` 字幕，也一起上传，会直接用字幕的文字，更准确。")
            with gr.Row():
                files = gr.File(label="上传视频/音频/字幕（可多选）", file_count="multiple")
                folder = gr.Textbox(label="或者填写电脑上的文件夹路径", placeholder=r"例如 D:\讲课视频")
            with gr.Row():
                asr = gr.Dropdown(["faster-whisper", "funasr", "none"], value=cfg.get_path("prepare.asr.engine", "faster-whisper"),
                                  label="语音识别引擎（纯中文课可选 funasr）")
                lang = gr.Dropdown(["auto", "zh", "en"], value="auto", label="素材语言")
                denoise = gr.Dropdown(["auto", "on", "off"], value="auto", label="降噪")
                separate = gr.Checkbox(label="视频有背景音乐（去除背景音乐）", value=False)
            prep_btn = gr.Button("开始准备素材", variant="primary")
            prep_log = gr.Textbox(label="运行日志", lines=12, max_lines=20, autoscroll=True)
            prep_md = gr.Markdown()

            gr.Markdown("### 校对文字（可选，但能明显提升效果）\n识别错的字直接在表格里改；不想要的片段把「保留」改成 ✘。"
                        "点击某一行可以试听。改完点「保存修改」。")
            clips = gr.Dataframe(headers=["id", "保留", "语言", "秒", "文字", "丢弃原因"], datatype=["str"] * 6,
                                 interactive=True, wrap=True)
            with gr.Row():
                load_clips = gr.Button("载入片段列表")
                save_clips = gr.Button("保存修改", variant="primary")
            clip_audio = gr.Audio(label="试听选中的片段", type="filepath")
            review_md = gr.Markdown()

            def do_prepare(voice_name, up_files, folder_path, asr_engine, language, dn, sep):
                if not voice_name:
                    yield "请先在上方填写声音名称", "", gr.update()
                    return
                inputs = []
                if up_files:
                    tmp = Path(tempfile.mkdtemp(prefix="voicetwin_upload_"))
                    for f in up_files:
                        src = Path(f if isinstance(f, str) else getattr(f, "name", f))
                        dst = tmp / src.name
                        dst.write_bytes(src.read_bytes())
                    inputs.append(str(tmp))
                if folder_path and folder_path.strip():
                    inputs.append(folder_path.strip().strip('"'))
                if not inputs and not wf.Project(cfg, voice_name).exists:
                    yield "请上传文件或填写文件夹路径", "", gr.update()
                    return
                overrides = {"asr": {"engine": asr_engine, "language": language}, "denoise": dn, "separate_vocals": bool(sep)}
                for text, state in stream_task(wf.run_prepare, cfg, voice_name, inputs, overrides=overrides):
                    md = _summary_md(state.get("value")) if state.get("done") and "value" in state else ""
                    yield text, md, gr.update(choices=_voices(cfg))

            prep_btn.click(do_prepare, [voice, files, folder, asr, lang, denoise, separate], [prep_log, prep_md, voice])
            load_clips.click(lambda v: _clips_table(cfg, v), voice, clips)

            def on_select(voice_name, evt: gr.SelectData):
                try:
                    row = evt.index[0] if isinstance(evt.index, (list, tuple)) else evt.index
                    project = wf.Project(cfg, voice_name)
                    rec = project.load_manifest()[int(row)]
                    return str(project.abspath(rec["path"]))
                except Exception:
                    return None

            clips.select(on_select, voice, clip_audio)

            def do_save(voice_name, table):
                import csv

                project = wf.Project(cfg, voice_name)
                rows = table.values.tolist() if hasattr(table, "values") else table
                records = {r["id"]: r for r in project.load_manifest()}
                with open(project.csv_path, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=["id", "keep", "split", "lang", "duration", "text", "drop_reason", "audio"])
                    w.writeheader()
                    for row in rows:
                        rid = str(row[0])
                        if rid not in records:
                            continue
                        w.writerow({"id": rid, "keep": 0 if str(row[1]).strip() in ("✘", "0", "x", "X", "否") else 1,
                                    "split": records[rid].get("split", "train"), "lang": row[2], "duration": row[3],
                                    "text": row[4], "drop_reason": row[5], "audio": ""})
                summary = wf.apply_review(cfg, voice_name)
                return f"已保存：{summary['changed']}\n\n" + _summary_md(summary), _clips_table(cfg, voice_name)

            save_clips.click(do_save, [voice, clips], [review_md, clips])

        # ------------------------------------------------------------ ② 训练
        with gr.Tab("② 训练模型"):
            gr.Markdown("**GPT-SoVITS**（推荐）：用你的素材微调，最像你；需要 NVIDIA 显卡（6GB+），1 小时素材约 30~60 分钟。\n\n"
                        "**Qwen3-TTS**：也可微调（显存需求更大）。**IndexTTS** 不需要训练，可以直接去第③步。\n\n"
                        "训练结束后会自动用验证集挑选最像你的模型，并校准语速。")
            with gr.Row():
                t_backend = gr.Dropdown(["gptsovits", "qwen3tts"], value="gptsovits" if default_backend not in ("qwen3tts",) else default_backend,
                                        label="引擎")
                s_ep = gr.Number(label="SoVITS 轮数（0=自动）", value=0, precision=0)
                g_ep = gr.Number(label="GPT 轮数（0=自动）", value=0, precision=0)
                q_ep = gr.Number(label="Qwen3 轮数（0=默认）", value=0, precision=0)
                bs = gr.Number(label="batch（0=自动）", value=0, precision=0)
            with gr.Row():
                train_btn = gr.Button("开始训练", variant="primary")
                select_btn = gr.Button("重新挑选最佳模型")
            train_log = gr.Textbox(label="训练日志", lines=16, max_lines=24, autoscroll=True)
            train_md = gr.Markdown()

            def do_train(voice_name, backend, se, ge, qe, b):
                opts = {"sovits_epochs": int(se) or None, "gpt_epochs": int(ge) or None, "epochs": int(qe) or None,
                        "batch_size": int(b) or None}
                for text, state in stream_task(wf.run_train, cfg, voice_name, backend, **opts):
                    md = ""
                    if state.get("done") and "value" in state:
                        sel = (state["value"].get("selection") or {}).get("selection", {})
                        md = f"### ✅ 训练完成，最佳模型：{sel.get('best', '')}，语速校准：{(state['value'].get('selection') or {}).get('speed')}"
                    yield text, md

            def do_select(voice_name, backend):
                for text, state in stream_task(wf.run_select, cfg, voice_name, backend):
                    md = ""
                    if state.get("done") and "value" in state:
                        md = f"### ✅ 最佳模型：{state['value']['selection']['best']}，语速校准：{state['value']['speed']}"
                    yield text, md

            train_btn.click(do_train, [voice, t_backend, s_ep, g_ep, q_ep, bs], [train_log, train_md])
            select_btn.click(do_select, [voice, t_backend], [train_log, train_md])

        # ------------------------------------------------------------ ③ 合成
        with gr.Tab("③ 生成讲课音频"):
            gr.Markdown("粘贴讲稿或上传讲稿文件（txt / md / srt / docx）。空一行 = 段落停顿；"
                        "`[停顿=1.5]` 指定停顿秒数。多音字、术语读音可在 `workspace/声音名/lexicon.txt` 里纠正。")
            with gr.Row():
                with gr.Column(scale=3):
                    script = gr.Textbox(label="讲稿", lines=12, placeholder="大家好，今天我们来学习……")
                    script_file = gr.File(label="或上传讲稿文件", file_count="single")
                with gr.Column(scale=2):
                    s_backend = gr.Dropdown(backends, value=default_backend, label="引擎")
                    quality = gr.Radio(["fast", "balanced", "best"], value=cfg.get_path("synth.quality", "balanced"),
                                       label="质量（best = 每句 5 个候选 + 识别校验，最慢最好）")
                    speed = gr.Slider(0.7, 1.3, value=1.0, step=0.01, label="语速倍数（1.0 = 和你本人一样）")
                    ref = gr.Textbox(label="指定参考音频 id（留空自动）", value="")
                    redo = gr.Textbox(label="只重新生成第几句（例如 3,5,8-10）", value="")
                    gen_btn = gr.Button("生成", variant="primary")
            out_audio = gr.Audio(label="结果", type="filepath")
            out_files = gr.File(label="下载（音频 / 字幕 / 报告）", file_count="multiple")
            gen_log = gr.Textbox(label="日志", lines=8, max_lines=16, autoscroll=True)
            gen_md = gr.Markdown()

            def do_generate(voice_name, text, sfile, backend, q, spd, ref_id, redo_s):
                from voicetwin.cli import _parse_redo

                source = ""
                if sfile:
                    source = str(sfile if isinstance(sfile, str) else getattr(sfile, "name", sfile))
                elif text and text.strip():
                    source = text
                if not source:
                    yield None, None, "请输入讲稿", ""
                    return
                for logs, state in stream_task(wf.run_narrate, cfg, voice_name, source, backend_name=backend, quality=q,
                                               speed=float(spd), reference=ref_id.strip(), redo=_parse_redo(redo_s)):
                    if state.get("done") and "value" in state:
                        res = state["value"]
                        files_out = [str(res.audio_path), str(res.report_path)] + ([str(res.srt_path)] if res.srt_path else [])
                        rows = "\n".join(
                            f"| {s['index']} | {s['text'][:40]} | {s.get('speaker_sim') if s.get('speaker_sim') is None else round(s['speaker_sim'], 3)} "
                            f"| {'；'.join(s.get('issues') or [])} |" for s in res.segments)
                        md = (f"### ✅ 完成：{res.duration:.1f} 秒\n\n| # | 句子 | 声纹相似度 | 提示 |\n|---|---|---|---|\n{rows}")
                        yield str(res.audio_path), files_out, logs, md
                    else:
                        yield None, None, logs, ""

            gen_btn.click(do_generate, [voice, script, script_file, s_backend, quality, speed, ref, redo],
                          [out_audio, out_files, gen_log, gen_md])

        # ------------------------------------------------------------ ④ 评估
        with gr.Tab("④ 评估相似度"):
            gr.Markdown("上传任意一段音频，看看它和你的声音有多像（可用来对比不同引擎、不同参数）。")
            ev_audio = gr.Audio(label="音频", type="filepath")
            ev_text = gr.Textbox(label="对应文字（可选，填了会检查错字）")
            ev_btn = gr.Button("评估")
            ev_out = gr.JSON(label="结果")

            def do_eval(voice_name, audio, text):
                from voicetwin.synth.select import evaluate_file

                project = wf.open_project(cfg, voice_name, must_exist=True)
                return evaluate_file(cfg, project, Path(audio), text or "")

            ev_btn.click(do_eval, [voice, ev_audio, ev_text], ev_out)

        # ------------------------------------------------------------ 环境
        with gr.Tab("环境检查"):
            doc_btn = gr.Button("检查环境")
            doc_out = gr.Dataframe(headers=["状态", "项目", "说明"], wrap=True)
            doc_btn.click(lambda: [[r["status"], r["item"], r["detail"]] for r in wf.doctor(cfg)], outputs=doc_out)
    return app


def launch(cfg: Config, host: str = "127.0.0.1", port: int = 7860, share: bool = False) -> None:
    try:
        import gradio  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("网页界面需要 gradio：pip install \"voicetwin[webui]\"") from exc
    app = build_app(cfg)
    app.queue()
    log.info(f"网页界面：http://{host}:{port}")
    app.launch(server_name=host, server_port=port, share=share, inbrowser=host in ("127.0.0.1", "localhost"))
