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
    assert app.title == "声音分身 VoiceTwin"
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
    assert [v for _, v in ui2.c["quality"].choices] == ["fast", "balanced", "best", "max", "perfect"]
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
    assert last["clips"] and last["clips"][0][0] == 1
    assert "还没训练" in last["voice_status"]
    assert last["prep_next"]["visible"] is True
    # 页面再点一次：已经处理过的文件不会重做（同一个文件夹）
    assert wf.Project(app_ui.cfg, "网页声音").exists
    shutil.rmtree(wf.Project(app_ui.cfg, "网页声音").root, ignore_errors=True)


def test_select_handlers_accept_gradio_event_data(prepared):
    cfg, project, _ = prepared
    ui = A.WebUI(cfg)
    app = ui.build()
    clip_fn = next(f for f in app.fns if getattr(f.fn, "__name__", "") == "clip_pick")
    rows = A._clips_table(cfg, project.voice)
    evt = gr.SelectData(None, {"index": [1, 5], "value": rows[1][5], "selected": True})
    audio, panel, adopt, cid = clip_fn.fn(project.voice, rows, evt)
    assert cid == rows[1][1] and audio["value"].endswith(".wav")
