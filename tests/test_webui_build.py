"""在 gradio 4.24（GPT-SoVITS 整合包自带的版本）下建出整个网页，并检查每个流式处理函数的每一次输出个数都对。

默认的测试环境装的是新版 gradio，这个文件会自动跳过。用整合包同款环境运行：
    GRADIO_ANALYTICS_ENABLED=False PYTHONPATH=$PWD <scratchpad>/gsv39/bin/python -m pytest -q tests/test_webui_build.py
"""

import inspect
import shutil

import pytest

gr = pytest.importorskip("gradio")
if not str(getattr(gr, "__version__", "")).startswith("4."):
    pytest.skip("这个测试只针对 gradio 4.x（整合包自带 4.24）", allow_module_level=True)

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402
from voicetwin.webui.app import build_app  # noqa: E402


def _cfg(tmp_path, **extra):
    from conftest import make_cfg

    return make_cfg(tmp_path / "ws", **extra)


def _blank(component):
    if isinstance(component, (gr.Number, gr.Slider)):
        return None
    if isinstance(component, gr.Checkbox):
        return False
    if isinstance(component, gr.State):
        return {}
    if isinstance(component, (gr.File, gr.Audio, gr.Dataframe)):
        return None
    return ""


def _streaming(app):
    return [f for f in app.fns if f.fn is not None and inspect.isgeneratorfunction(f.fn)]


def test_build_app_local_and_remote(tmp_path):
    cfg = _cfg(tmp_path)
    app = build_app(cfg)
    assert app.title == "声音分身 VoiceTwin v18"  # 浏览器标签页上也是 v18（老师的永久要求）
    vers = [c for c in app.get_config_file()["components"] if (c.get("props") or {}).get("elem_id") == "vt-version"]
    assert vers and A.APP_VERSION in vers[0]["props"]["value"]  # launcher 用它分辨开着的是不是旧版本
    conf = app.get_config_file()
    assert ".vt-prog" in (conf.get("css") or "") and ".vt-gpu" in (conf.get("css") or "")
    assert build_app(cfg, local=False) is not None


def test_every_streaming_yield_matches_outputs(tmp_path):
    """每个流式处理函数：声音名称留空、其它输入都是空值时，每次 yield 的个数都等于 outputs 的个数。"""
    app = build_app(_cfg(tmp_path))
    fns = _streaming(app)
    assert len(fns) >= 8
    for f in fns:
        args = [_blank(c) for c in f.inputs]
        for out in f.fn(*args):
            assert isinstance(out, tuple), f.name
            assert len(out) == len(f.outputs), f"{f.name}: {len(out)} != {len(f.outputs)}"


def test_heavy_events_hide_overlay_and_have_no_queue_limit(tmp_path):
    app = build_app(_cfg(tmp_path))
    conf = app.get_config_file()
    deps = conf["dependencies"]
    streaming_ids = {id(f.fn) for f in _streaming(app)}
    heavy = [(d, f) for d, f in zip(deps, app.fns) if id(f.fn) in streaming_ids]
    assert heavy
    for d, f in heavy:
        assert d.get("show_progress") == "hidden", f.name
        assert f.concurrency_limit is None, f.name


def test_dummy_engine_only_offered_in_test_config(tmp_path):
    ui = A.WebUI(_cfg(tmp_path, backend="gptsovits"))
    ui.build()
    choices = [v for _, v in ui.c["s_backend"].choices]
    assert "dummy" not in choices and ui.c["s_backend"].value == "gptsovits"
    ui2 = A.WebUI(_cfg(tmp_path / "b"))  # 测试配置里 backend = dummy
    ui2.build()
    assert "dummy" in [v for _, v in ui2.c["s_backend"].choices]
    assert [v for _, v in ui2.c["quality"].choices] == ["fast", "balanced", "best", "max", "perfect", "identical"]
    assert ui2.c["quality"].value == "identical"  # 网页每次打开都先选好「一模一样」
    assert ui2.c["speed"].minimum == -30 and ui2.c["speed"].maximum == 30 and ui2.c["speed"].value == 0


def test_prepare_through_the_page(tmp_path, lecture_dir):
    """在 4.24 下点「开始准备素材」：按钮变灰、进度条走到绿色、片段表和状态卡刷新。"""
    app_ui = A.WebUI(_cfg(tmp_path))
    app = app_ui.build()
    f = next(f for f in app.fns if getattr(f.fn, "__name__", "") == "do_prepare")
    outs = list(f.fn("网页声音", None, str(lecture_dir), "none", "auto", "off", False))
    assert all(len(o) == len(f.outputs) for o in outs)
    names = app_ui.PREP_OUT
    first, last = dict(zip(names, outs[0])), dict(zip(names, outs[-1]))
    if len(outs) > 1:
        assert first["prep_btn"]["interactive"] is False and first["prep_stop"]["visible"] is True
    assert "vt-done" in last["prep_bar"], last["prep_md"]
    assert last["prep_btn"]["interactive"] is True and last["prep_stop"]["visible"] is False
    assert last["prep_md"].startswith("### ✅ 素材准备好了") and "{" not in last["prep_md"]
    # 表格由接在后面的 after_prepare_clips 刷新
    after = next(f for f in app.fns if getattr(getattr(f.fn, "__wrapped__", f.fn), "__name__", "") == "after_prepare_clips")
    count, clips, _ = after.fn("网页声音", False, None, last["clips_base"])
    assert clips and clips[0][0] == 1 and "用来训练的句子" in count
    assert "还没训练" in last["voice_status"]
    # 第一次准备完还没确认训练素材（点开始训练会被拦下）：「去「② 训练模型」 →」先不显示，
    # 确认好了再准备时才显示（test_bug_hunt4.py::test_prepare_done_points_to_confirm_before_training）
    assert last["prep_next"]["visible"] is False
    # 页面再点一次：已经处理过的文件不会重做（同一个文件夹）
    assert wf.Project(app_ui.cfg, "网页声音").exists
    shutil.rmtree(wf.Project(app_ui.cfg, "网页声音").root, ignore_errors=True)


def test_select_handlers_accept_gradio_event_data(prepared):
    cfg, project, _ = prepared
    ui = A.WebUI(cfg)
    app = ui.build()
    clip_fn = next(f for f in app.fns if getattr(f.fn, "__name__", "") == "clip_pick")
    rows = A._clips_table(cfg, project.voice)
    tc, idc = A.CLIP_HEADERS.index(A.COL_TEXT), A.CLIP_HEADERS.index(A.COL_ID)
    evt = gr.SelectData(None, {"index": [1, tc], "value": rows[1][tc], "selected": True})
    audio, panel, cid = clip_fn.fn(project.voice, rows, evt)
    assert cid == rows[1][idc] and audio["value"].endswith(".wav")


def _dep(app, ui, comp, event):
    conf = app.get_config_file()
    cid = ui.c[comp]._id
    return [d for d in conf["dependencies"] if any(t[0] == cid and t[1] == event for t in d["targets"])]


def test_wiring_review_fixes(tmp_path):
    """几处容易漏接的事件：换版本更新下载列表；准备素材带上「只看可能有错的」和表格；数字框 always_last；
    ③ 的提醒在打开这一页、做完训练后会刷新；停止按钮 5 秒后变回来。"""
    ui = A.WebUI(_cfg(tmp_path))
    app = ui.build()
    ids = {k: getattr(v, "_id", None) for k, v in ui.c.items()}
    (var,) = _dep(app, ui, "var_choice", "input")
    assert ids["out_files"] in var["outputs"] and ids["out_audio"] in var["outputs"]
    (prep,) = _dep(app, ui, "prep_btn", "click")
    assert ids["only_sus"] in prep["inputs"] and ids["clips"] in prep["inputs"]
    for name in ("s_ep", "g_ep", "bs"):
        (d,) = _dep(app, ui, name, "input")
        assert d["trigger_mode"] == "always_last"
    (act,) = _dep(app, ui, "clip_action_btn", "click")  # 校对表里的操作（网页脚本按的隐藏按钮）
    assert act["inputs"] == [ids["voice"], ids["clip_action"], ids["only_sus"]]
    assert act["outputs"] == [ids["clip_msg"], ids["clips_count"], ids["clips"]]
    (filt,) = _dep(app, ui, "only_sus", "change")
    assert ids["clips"] in filt["inputs"]
    conf = app.get_config_file()
    warn_deps = [d for d in conf["dependencies"] if d["outputs"] == [ids["gen_warn"]]]
    events = {tuple(t) for d in warn_deps for t in d["targets"]}
    assert any(e[1] == "select" for e in events)  # 打开 ③ 这一页
    assert any(e[1] == "then" for e in events)  # 准备素材 / 训练做完后
    (voice,) = [d for d in _dep(app, ui, "voice", "change") if ids["gen_warn"] in d["outputs"]]
    assert ids["s_backend"] in voice["inputs"]


def test_result_tables_have_no_phantom_zero_row(tmp_path):
    """还没有结果的表格不能显示一行「0」（gradio 4.24 默认用 0 填数字列）。"""
    ui = A.WebUI(_cfg(tmp_path))
    ui.build()
    for name in ("gen_table", "vf_table", "doc_out", "doc_opt"):
        comp = ui.c[name]
        data = comp.postprocess(comp.value).model_dump()["data"] if hasattr(comp.postprocess(comp.value), "model_dump") \
            else comp.value["data"]
        assert all(cell in ("", None) for row in data for cell in row), (name, data)
        assert comp.value["headers"][0] == "#"


def test_clip_player_and_diff_are_below_the_table(tmp_path):
    """点一行时会出现/消失的播放器、对比放在校对表下面：放在上面会把表格顶上顶下。"""
    ui = A.WebUI(_cfg(tmp_path))
    ui.build()
    table = ui.c["clips"]._id
    for name in ("clip_audio", "clip_diff"):
        assert ui.c[name]._id > table, name


def test_review_table_is_display_only_with_bridge(tmp_path):
    """校对表不能直接在格子里打字（gradio 4.24 的格子编辑框只有一行）：改字由网页脚本的编辑框做，
    通过隐藏的输入框 + 按钮交给 do_clip_action。隐藏用 CSS（visible=False 的组件不会出现在网页里，脚本找不到）。"""
    ui = A.WebUI(_cfg(tmp_path))
    app = ui.build()
    clips = ui.c["clips"]
    assert clips.interactive is False and clips.elem_id == "vt-clips" and clips.headers == A.CLIP_HEADERS
    (conf,) = _dep(app, ui, "confirm_btn", "click")  # 「✅ 确认训练素材」在「保存修改」下面
    ids = {k: getattr(v, "_id", None) for k, v in ui.c.items()}
    assert conf["outputs"] == [ids["review_md"], ids["clips_count"], ids["clips"]]
    assert ui.c["confirm_btn"]._id > ids["clips"] and ui.c["confirm_btn"].value == A.CONFIRM_BTN
    for name, eid in (("clip_action", "vt-clip-action"), ("clip_action_btn", "vt-clip-action-btn")):
        comp = ui.c[name]
        assert comp.elem_id == eid and "vt-bridge" in (comp.elem_classes or []) and comp.visible is not False
    assert ".vt-bridge{display:none!important}" in A.APP_CSS
    js = A.page_js()
    assert "vt-clip-action-btn" in js and "isComposing" in js
    assert f'"text": {A.CLIP_HEADERS.index(A.COL_TEXT)}' in js and f'"menu": {A.CLIP_HEADERS.index(A.COL_MENU)}' in js


def test_find_bar_wiring(tmp_path):
    """查找栏在表格上面；每个按钮都更新（查找结果、片段总数、表格、查找框）；查找的按钮一个接一个处理，
    上一处 / 下一处连点几下走几处（trigger_mode=multiple），替换只算一次（防止连点换两次）；查找框按回车 = 查找。"""
    ui = A.WebUI(_cfg(tmp_path))
    app = ui.build()
    ids = {k: getattr(v, "_id", None) for k, v in ui.c.items()}
    want = [ids[k] for k in A.WebUI.FIND_OUT]
    assert ids["find_q"] < ids["clips"] and ids["find_status"] < ids["clips"]
    assert ui.c["find_q"].elem_id == "vt-find-q" and ui.c["find_repall"].elem_id == "vt-find-all"
    # 老师 10-03 要求的例子：借词（识别错的）→ 介词（正确的）
    assert ui.c["find_q"].label == "🔍 查找（例如：借词）" and ui.c["find_r"].label == "替换成（例如：介词）"
    for comp, event, mode in (("find_btn", "click", "once"), ("find_q", "submit", "once"),
                              ("find_prev", "click", "multiple"), ("find_next", "click", "multiple"),
                              ("find_rep1", "click", "once"), ("find_repall", "click", "once"),
                              ("find_undo", "click", "once"), ("find_close", "click", "once")):
        (d,) = _dep(app, ui, comp, event)
        fn = app.fns[app.get_config_file()["dependencies"].index(d)]
        assert d["outputs"] == want and d["trigger_mode"] == mode and fn.concurrency_id == "vt-find", comp
    js = A.page_js()
    assert "#vt-find-all" in js and "window.confirm" in js and "scrollToFind" in js


def test_review_table_actions_queue_and_refresh(tmp_path):
    """10-03 找 bug：表格里的操作、保存修改、确认训练素材同时改校对表会互相冲掉 → 一个接一个处理；表格里连着点的
    每一下都要排队（默认 once 会丢掉：删除一行的 3 秒里改的字不见了）；长任务做完刷新页面顶部的「当前声音状态」；
    准备素材 / 一键校正做完按现在选的声音刷新「一键全部文字校正」按钮（加了新素材又能用一次）。"""
    ui = A.WebUI(_cfg(tmp_path))
    app = ui.build()
    conf = app.get_config_file()
    deps = conf["dependencies"]

    def fn_of(d):
        return app.fns[deps.index(d)]

    for comp, mode in (("clip_action_btn", "multiple"), ("confirm_btn", "once")):
        (d,) = _dep(app, ui, comp, "click")
        assert d["trigger_mode"] == mode and fn_of(d).concurrency_id == "vt-review", comp
    saves = [d for d in deps if fn_of(d).concurrency_id == "vt-review"]
    assert len(saves) >= 3  # 表格操作 + 保存修改 + 确认训练素材
    status_id = ui.c["voice_status"]._id
    after = [d for d, f in zip(deps, app.fns) if getattr(f.fn, "__name__", "") == "after_task"]
    assert after and all(status_id in d["outputs"] for d in after)
    out = ui.after_task("")
    assert len(out) == len(after[0]["outputs"])
    want = [ui.c[k]._id for k in ("tr_btn", "tr_files", "tr_info")]
    refresh = [d for d, f in zip(deps, app.fns) if getattr(f.fn, "__name__", "") == "textfix_state"]
    # 打开网页、换声音、准备素材后、一键校正后、表格操作 / 保存 / 确认以后
    assert len(refresh) >= 7 and all(d["outputs"] == want for d in refresh)
