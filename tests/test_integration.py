"""各部分合在一起之后的接口检查：网页 ↔ 工作流 ↔ 生成引擎 ↔ 训练引擎 ↔ 命令行用的是同一套约定。

（每个部分自己的细节在各自的测试文件里；这里只测它们之间“对不对得上”。不需要 gradio 4.24。）
"""

import shutil
import sys
from pathlib import Path

import pytest
from conftest import make_cfg

import voicetwin
from voicetwin import workflows as wf
from voicetwin.synth import engine as eng
from voicetwin.webui import app as A


def _copy_voice(prepared, tmp_path):
    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    for name in ("models.json",):
        p = ws / project.voice / name
        if p.exists():
            p.unlink()
    shutil.rmtree(ws / project.voice / "outputs", ignore_errors=True)
    return make_cfg(ws), project.voice


def test_version_is_shown_in_page_header():
    """老师的永久要求：网页标题永远显示「v18」，版本号（18.2……）只在黑色窗口、发布页、下载的文件名里。"""
    assert voicetwin.__version__ == "18.2"
    assert A.APP_TITLE_VERSION == "18" and "# 🎙️ 声音分身 VoiceTwin v18 " in A.INTRO and "18.2" not in A.INTRO
    text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "18.2"' in text
    src = (Path(__file__).resolve().parents[1] / "voicetwin" / "webui" / "app.py").read_text(encoding="utf-8")
    assert '\nAPP_TITLE_VERSION = "18"\n' in src  # 写死的，不跟着版本号变


def test_quality_names_are_one_source():
    """网页的单选框、命令行和报告用同一套档位名字（生成引擎里写一份）。"""
    assert A.QUALITY_CHOICES == eng.quality_choices()
    assert A.QUALITY_SHORT == eng.QUALITY_SHORT
    assert A.QUALITY_SHORT["balanced"] == "均衡"
    labels = dict((v, k) for k, v in A.QUALITY_CHOICES)
    assert labels["perfect"].startswith("完美：每句最多试 20 次") and "句子之间完全静音" in labels["perfect"]
    assert "最慢" not in labels["max"]  # 「完美」比「极致」更慢
    for _, value in A.QUALITY_CHOICES:  # 每个标签都能被认回来（命令行、配置里写中文也行）
        assert eng.resolve_quality(labels[value]) == value
    # 没有显卡时的说明也用同一个名字（浏览器里实测发现过旧名字「标准」）
    q, note = A._recommended_quality({"ok": False, "level": "error", "total_gb": None})
    assert q == "balanced" and "「均衡」" in note and "标准" not in note


def test_stages_follow_selected_quality(prepared):
    cfg, _, _ = prepared
    assert A._stages(cfg, "narrate", quality="perfect") == wf.STAGES_NARRATE_VARIANTS
    assert A._stages(cfg, "narrate", quality="fast") == wf.STAGES_NARRATE
    assert A._stages(cfg, "proofcheck") == wf.STAGES_PROOFCHECK
    assert A._stages(cfg, "verify") == wf.STAGES_VERIFY
    assert A._stages(cfg, "blind") == wf.STAGES_BLIND_TEST
    assert A._stages(cfg, "prepare", overrides={"proofcheck": "off"}) == wf.STAGES_PREPARE
    assert A._stages(cfg, "没有这种任务") == []


def _record_stream(monkeypatch):
    seen = {}

    def fake_stream(kind, label, voice, fn, *args, stages=None, hint="", note="", **kwargs):
        seen.update(kind=kind, fn=fn, args=args, stages=stages, kwargs=kwargs)
        yield "", {"done": True, "bar": "", "error": RuntimeError("测试"), "friendly": None}

    monkeypatch.setattr(A, "stream_task", fake_stream)
    return seen


def test_generate_passes_quality_speed_and_stages(prepared, tmp_path, monkeypatch):
    """③ 生成：「完美」档的阶段表多一步；语速滑块 −20 → 语速倍数 1.2（和 wf.slider_to_speed 一样）；重做编号原样传。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    seen = _record_stream(monkeypatch)
    ui = A.WebUI(cfg)
    outs = list(ui.do_generate(name, "第一句。第二句。第三句。", None, "dummy", "perfect", -20, "", "2, 3", "", "wav"))
    assert all(len(o) == len(ui.GEN_OUT) for o in outs)
    assert seen["fn"] is wf.run_narrate and seen["stages"] == wf.STAGES_NARRATE_VARIANTS
    kw = seen["kwargs"]
    assert kw["quality"] == "perfect" and kw["speed"] == pytest.approx(wf.slider_to_speed(-20)) == pytest.approx(1.2)
    assert kw["redo"] == [2, 3]  # 和表格的 # 一样从 1 开始，engine 自己减 1


def test_speed_preview_is_single_version(prepared, tmp_path, monkeypatch):
    cfg, name = _copy_voice(prepared, tmp_path)
    seen = _record_stream(monkeypatch)
    ui = A.WebUI(cfg)
    list(ui.do_speed_preview(name, "", 15, "dummy"))
    kw = seen["kwargs"]
    assert kw["quality"] == "fast" and kw["variants"] is False and kw["subtitles"] is False
    assert kw["speed"] == pytest.approx(0.85) and seen["stages"] == wf.STAGES_NARRATE


def test_train_passes_dpo_choice(prepared, tmp_path, monkeypatch):
    cfg, name = _copy_voice(prepared, tmp_path)
    seen = _record_stream(monkeypatch)
    ui = A.WebUI(cfg)
    list(ui.do_train(name, "gptsovits", 0, 20, 0, 4, "off"))
    kw = seen["kwargs"]
    assert seen["fn"] is wf.run_train
    assert kw["if_dpo"] is False and kw["gpt_epochs"] == 20 and kw["batch_size"] == 4 and kw["sovits_epochs"] is None
    list(ui.do_train(name, "gptsovits", 0, 0, 0, 0, "auto"))
    assert seen["kwargs"]["if_dpo"] is None and seen["kwargs"]["batch_size"] is None


def test_training_plan_preview_is_quick(prepared, tmp_path, monkeypatch):
    """② 训练页的预览：用显卡检查的结果说「显存 12 GB → 每批 …」；读不到显卡时不去跑十几秒的 PyTorch。"""
    from fake_gptsovits import build_fake_root

    from voicetwin.backends import base as B
    from voicetwin.utils import gpu

    cfg0, name = _copy_voice(prepared, tmp_path)
    root = build_fake_root(tmp_path / "GSV")
    cfg = make_cfg(Path(cfg0["workspace"]), backend="gptsovits",
                   backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    ui = A.WebUI(cfg)

    def slow(*a, **k):
        raise AssertionError("预览不能跑 GPT-SoVITS 的 Python")

    monkeypatch.setattr(B, "gpu_memory_gb", slow)
    import voicetwin.backends.gptsovits as G

    monkeypatch.setattr(G, "gpu_memory_gb", slow)
    monkeypatch.setattr(gpu, "gpu_status", lambda refresh=False: {"ok": True, "level": "ok", "total_gb": 11.99,
                                                                  "free_gb": 11.2, "source": "test"})
    md = ui.train_plan_preview(name, "gptsovits")
    assert md.startswith("🧠 **电脑会自动这样训练**：显存 12 GB → 每批") and "训练计划：" not in md
    assert "不开 DPO" in md and "高级设置" in md
    md2 = ui.train_plan_preview(name, "gptsovits", 0, 0, 2, "on")
    assert "每批 2 条（你指定的）" in md2 and "开启 DPO（你指定的" in md2
    monkeypatch.setattr(gpu, "gpu_status", lambda refresh=False: {"ok": False, "level": "error", "total_gb": None})
    md3 = ui.train_plan_preview(name, "gptsovits")
    assert "没有检测到能用的 N 卡" in md3
    # 新声音（还没准备素材）、或者引擎不需要训练：显示默认说明
    assert ui.train_plan_preview("还没有的声音", "gptsovits") == A.PLAN_DEFAULT
    assert wf.training_plan(cfg, name, "indextts") == ""


def test_plan_line_from_training_log():
    log_text = ("21:00:01 | 检查显卡、整理训练素材（大约半分钟）……\n"
                "21:00:03 | 训练计划：没有检测到能用的 N 卡 → 每批 2 条（用 CPU 训练会非常慢）；素材 3 分钟（30 条）→ 音色 SoVITS 8 轮。\n"
                "21:00:04 | 处理文字 3/30")
    assert A._plan_line(log_text).startswith("没有检测到能用的 N 卡")
    info = {"params": {"summary": "训练计划：显存 12 GB → 每批 6 条。"}}
    assert A._plan_text(info) == "显存 12 GB → 每批 6 条。"
    md = A._train_done_md(dict(info, train_minutes=3.5))
    assert "用时 3.5 分钟" in md and "显存 12 GB → 每批 6 条" in md and "训练计划：" not in md


def test_verify_rows_use_workflow_result_shape():
    """⑤ 机器鉴别：wf.verify_files 的结果（pcts / sims / pass / rank / models.labels）画成编号、排名的表。"""
    result = {
        "rows": [
            {"file": "b.wav", "path": "/x/b.wav", "pct": 80.0, "pcts": {"eres2netv2": 79.0, "resemblyzer": 81.0},
             "sims": {"eres2netv2": 0.61, "resemblyzer": 0.7}, "pass": False, "rank": 2},
            {"file": "a.wav", "path": "/x/a.wav", "pct": 97.5, "pcts": {"eres2netv2": 98.0, "resemblyzer": 97.0},
             "sims": {"eres2netv2": 0.74, "resemblyzer": 0.83}, "pass": True, "rank": 1},
        ],
        "models": {"models": ["eres2netv2", "resemblyzer"], "labels": ["ERes2NetV2（GPT-SoVITS 自带）", "Resemblyzer"]},
        "min_pct": 85.0, "calibrated": True, "originals": [],
    }
    table, md = A._verify_rows(result)
    assert [r[0] for r in table] == [1, 2] and [r[1] for r in table] == ["a.wav", "b.wav"]
    assert table[0][3] == "97.5%" and table[0][4] == 1 and table[0][5] == "✅ 是" and table[1][5] == "🔴 否"
    assert "ERes2NetV2（GPT-SoVITS 自带） 98.0%（原始 0.740）" in table[0][2] and "Resemblyzer 97.0%" in table[0][2]
    assert "共 2 个文件，其中 1 个 ≥ 85%" in md and "Resemblyzer" in md and "平均" in md
    _, md2 = A._verify_rows(dict(result, calibrated=False, originals=["1.wav", "2.wav", "3.wav"]))
    assert "你选的 3 段原始录音" in md2 and "只能粗略参考" in md2


def test_verify_uses_chosen_originals(prepared, tmp_path):
    """⑤ 机器鉴别：网页把「你的原始录音」和「要鉴别的音频」按名字传给 wf.verify_files（它的参数顺序是生成的在前）。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    recs = project.load_manifest(only_kept=True)
    originals = [str(project.abspath(r["path"])) for r in recs[:3]]
    gen = tmp_path / "要鉴别的.wav"
    shutil.copyfile(project.abspath(recs[5]["path"]), gen)
    ui = A.WebUI(cfg)
    outs = list(ui.do_verify(name, originals, [str(gen)], {}))
    last = dict(zip(ui.VERIFY_OUT, outs[-1]))
    assert "鉴别完成：共 1 个文件" in last["vf_md"], last["vf_md"]
    assert "你选的 3 段原始录音" in last["vf_md"]
    assert last["vf_table"][0][1] == "要鉴别的.wav" and last["vf_table"][0][3].endswith("%")


def test_verify_defaults_include_sentence_clips(prepared, tmp_path):
    """没选文件时，机器鉴别默认比最近一次生成的结果和每一句的音频（和 wf.verify_defaults 一样）。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    res = wf.run_narrate(cfg, name, "第一句话在这里。第二句话也在这里。", out=str(tmp_path / "ws" / name / "outputs" / "t.wav"),
                         backend_name="dummy", quality="fast")
    project = wf.Project(cfg, name)
    files = A._report_audio_files(A._latest_report(project), project)
    assert str(res.audio_path) in files and len(files) == 1 + len(res.segments)
    defaults = wf.verify_defaults(cfg, name)["generated"]
    assert sorted(files) == sorted(defaults)


def test_cli_progress_passes_stage_keywords(prepared, monkeypatch):
    from voicetwin import cli

    cfg, _, _ = prepared
    seen = []
    real = wf.task_stages

    def spy(kind, cfg=None, backend_name=None, select=True, **kw):
        seen.append((kind, kw))
        return real(kind, cfg, backend_name, select=select, **kw)

    monkeypatch.setattr(wf, "task_stages", spy)
    p = cli._cli_progress("narrate", cfg, "生成音频", None, quality="perfect")
    assert seen[-1] == ("narrate", {"quality": "perfect"})
    assert p.snapshot()["stage_count"] == len(wf.STAGES_NARRATE_VARIANTS)
    cli._cli_progress("prepare", cfg, "准备素材", overrides={"proofcheck": "off"})
    assert seen[-1] == ("prepare", {"overrides": {"proofcheck": "off"}})


def test_quick_check_is_one_friendly_line_per_problem(tmp_path):
    root = tmp_path / "GSV"
    root.mkdir()
    (root / "api_v2.py").write_text("", encoding="utf-8")
    cfg = make_cfg(tmp_path / "ws", backend="gptsovits", backends={"gptsovits": {"root": str(root)}})
    problems = [p for p in wf.quick_check(cfg) if "ffmpeg" not in p]
    assert len(problems) == 1 and problems[0].startswith("缺少 6 个 GPT-SoVITS 模型文件") and "等" in problems[0]
    assert "「🩺 环境检查」" in problems[0] and "「⬇️ 下载缺少的模型」" in problems[0]
    (root / "api_v2.py").unlink()
    problems = [p for p in wf.quick_check(cfg) if "ffmpeg" not in p]
    assert len(problems) == 1 and "缺少 api_v2.py" in problems[0] and "install_windows.bat" in problems[0]


def test_task_banner_names_tab_and_button_for_every_kind():
    from voicetwin.webui import tasks

    for kind in ("prepare", "proofcheck", "train", "select", "generate", "speed", "verify", "blind", "download"):
        assert tasks.KIND_TABS.get(kind) and tasks.KIND_BUTTONS.get(kind), kind
    # 网页上的按钮文字和横幅里说的一样
    assert tasks.KIND_BUTTONS["proofcheck"] == A.PROOF_BTN and tasks.KIND_BUTTONS["download"] == A.DL_BTN
    assert tasks.KIND_BUTTONS["speed"] == A.SPEED_BTN and tasks.KIND_BUTTONS["verify"] == A.VERIFY_BTN
    assert tasks.KIND_BUTTONS["blind"] == A.BLIND_BTN and tasks.KIND_BUTTONS["prepare"] == A.PREP_BTN


def test_error_advice_names_real_ui_labels():
    """报错里的「怎么办」提到的按钮、选项，网页上真的有。"""
    from voicetwin.errors import explain

    f = explain(RuntimeError("没有可用于训练的片段，请先运行素材准备并检查 transcripts.csv。"))
    assert "「保留」改成「是」" in f.advice  # 校对表的「保留」列填 是/否
    f = explain(RuntimeError("GPT-SoVITS 环境有问题：\n- 配置了外部 api_url 时无法自动训练"))
    assert f.key == "gsv_env" and "「检查环境」" not in f.advice and "🩺 环境检查" in f.advice
    f = explain(RuntimeError("CUDA out of memory. Tried to allocate 2.00 GiB"))
    assert "每批数量" in f.advice and "质量" in f.advice


def test_stop_button_is_not_reset_while_running(tmp_path, monkeypatch):
    """进度条每 0.6 秒刷新一次时，不能把「再点一次确认停止」改回「⏹ 停止」（浏览器里实测发现的问题）。"""
    import threading

    from voicetwin.webui import tasks

    monkeypatch.setattr(tasks, "POLL_SECONDS", 0.02)
    pause = threading.Event()

    def slow_download(cfg, progress=None):
        for k in range(5):
            progress(0.1 + 0.1 * k, f"已下载 {k} MB")
            pause.wait(0.08)
        return []

    monkeypatch.setattr(A, "_download_job", slow_download)
    ui = A.WebUI(make_cfg(tmp_path))
    outs = [dict(zip(ui.DL_OUT, o)) for o in ui.do_download()]
    running = [o for o in outs[:-1] if o["dl_btn"].get("interactive") is False]
    assert len(running) >= 2
    assert running[0]["dl_stop"]["visible"] is True and running[0]["dl_stop"]["value"] == A.STOP_LABEL
    assert all(o["dl_stop"] == {"__type__": "update"} for o in running[1:])
    assert outs[-1]["dl_stop"]["visible"] is False
    # 停止按钮自己的两步确认
    upd, armed = A.WebUI.on_stop(0)
    assert upd["value"] == A.STOP_CONFIRM and armed > 0


def test_variants_md_when_percentages_are_equal():
    """两个版本百分比一样时（浏览器里实测见过「高 0.0 个百分点」），改说综合得分或「几乎一样」。"""
    vs = [{"name": "未去杂音", "path": "/a.wav", "score": 0.712, "pct": 72.3, "recommended": True},
          {"name": "去杂音", "path": "/b.wav", "score": 0.709, "pct": 72.3, "recommended": False}]
    md = A._variants_md(vs)
    assert "高 0.0 个百分点" not in md and "综合得分高 0.003" in md
    same = [dict(vs[0], score=0.71), dict(vs[1], score=0.71)]
    assert "几乎一样像" in A._variants_md(same)


def test_page_js_has_guard_and_progress_script():
    """gradio 4.24 的保护脚本和进度条脚本都在 gr.Blocks(js=...) 里，而且各自出错不会影响另一个。"""
    js = A.page_js()
    assert js.startswith("() => {") and "Array.prototype.trim" in js
    if A.PROGRESS_JS:
        assert A.PROGRESS_JS.strip()[:40] in js
    assert js.count("try {") >= 2


def test_second_yield_is_not_glued_to_the_first(monkeypatch):
    """任务马上就做完时，第二次产出也要和第一次隔开一点（gradio 4.24 两条消息挤在一起会出错）。"""
    import time as _time

    from voicetwin.webui import tasks

    monkeypatch.setattr(tasks, "POLL_SECONDS", 0.05)

    def quick(progress=None):
        _time.sleep(0.02)  # 第一次产出时还在做，紧接着就做完
        return "ok"

    stamps = []
    for _text, st in tasks.stream_task("download", "下载模型", "", quick):
        stamps.append((_time.time(), st.get("done", False)))
    assert len(stamps) == 2 and stamps[0][1] is False and stamps[1][1] is True
    assert stamps[1][0] - stamps[0][0] >= 0.9 * tasks.FIRST_GAP_FACTOR * 0.05


def test_stall_bar_shows_no_fake_estimate():
    """好一会儿没有新进度（黄色）时，不显示按过去速度算出来的「预计几点完成」。"""
    from voicetwin.utils.progress import render_progress_html

    snap = {"status": "running", "level": "stall", "pct": 52, "title": "训练模型", "stage_index": 6, "stage_count": 8,
            "stage_name": "训练语气和节奏（GPT）", "elapsed": 400, "idle": 200, "eta_total": 360.0,
            "eta_total_text": "全部大约还要 6 分钟，预计 07:33 左右完成", "msg": "训练音色：第 8/8 轮（0%）"}
    text = render_progress_html(snap)
    assert "暂时算不出来" in text and "预计 07:33" not in text and "3 分钟没有新进度" in text
