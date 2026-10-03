"""第四轮全面找 bug（10-03，每个模块一个一个查 + 独立复核）确认的问题，每个一个测试（在修复以前的代码上都失败）。

g1：网页（voicetwin/webui/app.py 的网页脚本和处理函数、launcher）。记录在 research/全面找bug/第四轮/g1.md。"""

import html
import json
import os
import re
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui import app as A


def _voice(tmp_path, texts, name="g1"):
    """一个只有校对表的声音（不用真的切录音）。"""
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, name).ensure()
    project.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for i, t in enumerate(texts)])
    return cfg, project


def _act(ui, name, action, cid, no="1", **extra):
    """和网页一样：经过 _safe（出错时变成说明），把操作放进隐藏的输入框，再按隐藏的按钮。"""
    payload = json.dumps(dict(action=action, id=cid, no=no, seq="t", **extra), ensure_ascii=False)
    return A._safe("校对表", 3, 0)(ui.do_clip_action)(name, payload, False)


def _is_update(v):
    return isinstance(v, dict) and v.get("__type__") == "update"


def _inner_text(cell):
    """浏览器里「文字」那一格显示出来的字（innerText 的近似：去掉标签、实体还原、连续空白合成一个、去掉头尾空白）。"""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", str(cell)))).strip()


def _gradio4():
    gr = pytest.importorskip("gradio")
    if not str(getattr(gr, "__version__", "")).startswith("4."):
        pytest.skip("只针对 gradio 4.x（整合包自带 4.24）")
    return gr


# ---------------------------------------------------------------------------- appA#1 编辑框里的旧句子把刚采用的建议改回去
def test_stale_edit_box_does_not_undo_a_just_applied_suggestion(tmp_path):
    """老师点了「采用」（或者一键校正正在改），马上双击同一行改别的字：编辑框里是采用以前的旧句子。以前按回车就把整句旧的
    存回去（刚采用的建议没了），还当成「老师自己打字改回去」记进撤销记录（以后 🔍 和一键校正都不再建议）。
    现在网页把打开编辑框时的句子（orig）一起送来：这期间这一句被改过就不存，说明原因，也不记撤销。"""
    T = "我们今天学习定语从句"
    cfg, project = _voice(tmp_path, [T, "第二句话。"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[6, 7]], "alt": "我们今天学习状语从句", "reasons": ["测试"], "score": 0.7}
    project.save_manifest(recs)
    ui = A.WebUI(cfg)
    _act(ui, "g1", "adopt", "c000")
    assert review.load_draft(project)["c000"]["text"] == "我们今天学习状语从句"
    msg, count, rows = _act(ui, "g1", "edit", "c000", text=T + "吧", orig=T)  # 编辑框是采用以前打开的
    assert review.load_draft(project)["c000"]["text"] == "我们今天学习状语从句"  # 刚采用的建议还在
    assert not review.load_rejected(project).get("c000")  # 没有当成老师撤销
    assert "没有存上" in msg and "再双击" in msg and T + "吧" in msg and "❌" not in msg
    assert isinstance(rows, list) and not _is_update(count)  # 表格重画成现在的样子
    # 在新的句子上改（orig 是现在的样子）：照常存
    msg2, _, _ = _act(ui, "g1", "edit", "c000", text="我们今天学习状语从句吧", orig="我们今天学习状语从句")
    assert "改好了" in msg2 and review.load_draft(project)["c000"]["text"] == "我们今天学习状语从句吧"
    # 打的正好就是现在的样子：不算被改过
    msg3, _, _ = _act(ui, "g1", "edit", "c000", text="我们今天学习状语从句吧", orig=T)
    assert "没有存上" not in msg3
    # 升级前打开的旧网页（送来的没有 orig）：照旧直接存
    _act(ui, "g1", "edit", "c001", text="第二句话改过了。")
    assert review.load_draft(project)["c001"]["text"] == "第二句话改过了。"


@pytest.mark.parametrize("text", [
    "我们  来看  *设置*  和 _下划线_ 还有 `代码` [括号] <b>粗</b> 1. 开头",
    "  前后有空格  ",
    "Let's look at it, as you see.",
    "全角，标点：和（括号）还有 ABC１２３",
    "a|b # c > d ~ e $ f",
])
def test_stale_check_accepts_what_the_page_shows(tmp_path, text):
    """网页上显示出来的字（innerText）和存的字会差在空格、markdown 符号、全角半角上：不能因为这些就说「被改过了」、
    一直存不上。编辑框打开时的字就是网页上那一格显示的字，按两边同样的整理方法比。"""
    cfg, project = _voice(tmp_path, [text])
    ui = A.WebUI(cfg)
    rows = A._clips_table(cfg, "g1")
    shown = _inner_text(rows[0][A.CLIP_HEADERS.index(A.COL_TEXT)])
    msg, _, _ = _act(ui, "g1", "edit", "c000", text=shown + "吧", orig=shown)
    assert "没有存上" not in msg, (text, shown)
    assert review.load_draft(project)["c000"]["text"].endswith("吧")


def test_stale_check_with_empty_text_row(tmp_path):
    """还没有文字的行：编辑框里是空的（「还没有识别出文字」只是提示），打上字照常存。"""
    cfg, project = _voice(tmp_path, ["", "第二句。"])
    ui = A.WebUI(cfg)
    msg, _, _ = _act(ui, "g1", "edit", "c000", text="老师自己打的。", orig="")
    assert "改好了" in msg and review.load_draft(project)["c000"]["text"] == "老师自己打的。"


def test_review_js_sends_the_text_the_edit_box_started_from():
    js = A.review_js()
    assert "orig: e.orig" in js and "orig: flat(ta.value)" in js


# ---------------------------------------------------------------------------- appA#2 / appB#2 / appC#1 被拒绝的「采用」
def test_refused_adopt_is_a_plain_note_and_the_table_is_redrawn(tmp_path):
    """老师先自己改了一处（看看 → 看），再点「采用」：程序有意不改（拿不准就不改）。以前显示成「❌ 校对表没有完成」+ 英文的
    ValueError 技术细节，表格也不重画（按钮一直是 ⏳）。现在是一句 ⚠️ 说明，表格照样重画。"""
    T = "我们我们来看看第二个第二个例子。"
    cfg, project = _voice(tmp_path, [T])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[0, 2], [9, 12]], "alt": "我们来看看第二个例子。", "reasons": ["测试"], "score": 0.7}
    project.save_manifest(recs)
    ui = A.WebUI(cfg)
    _act(ui, "g1", "edit", "c000", text="我们我们来看第二个第二个例子。", orig=T)
    sug = A._clips_table(cfg, "g1")[0][A.CLIP_HEADERS.index(A.COL_SUGGEST)]
    assert "vt-sug-blue" in sug  # 按钮还在（点了才知道不行）
    msg, count, rows = _act(ui, "g1", "adopt", "c000", no="5")
    assert msg.startswith("⚠️ 第 5 条没有改：") and "自己改" in msg
    assert "❌" not in msg and "ValueError" not in msg and "技术细节" not in msg
    assert isinstance(rows, list) and not _is_update(count)
    assert review.load_draft(project)["c000"]["text"] == "我们我们来看第二个第二个例子。"  # 没有乱改
    # 撤销一条没采用过的建议：一样是说明
    msg2, _, rows2 = _act(ui, "g1", "unadopt", "c000")
    assert msg2.startswith("⚠️") and "没有采用过的建议" in msg2 and "ValueError" not in msg2 and isinstance(rows2, list)


def test_draft_file_unreadable_does_not_escape_and_page_can_retry(tmp_path):
    """草稿文件一时读不了（Windows 上被杀毒软件 / OneDrive 占着）：说明里写「请等几秒再点一次」，不能让错误冲出去；
    文件好了以后再点一次就采用上了。"""
    T = "我们今天学习定语从句"
    cfg, project = _voice(tmp_path, [T])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[6, 7]], "alt": "我们今天学习状语从句", "reasons": ["测试"], "score": 0.7}
    project.save_manifest(recs)
    ui = A.WebUI(cfg)
    d = review.draft_path(project)
    d.mkdir()  # 读的时候报 OSError（和被占着一样）
    try:
        msg, count, rows = ui.do_clip_action("g1", json.dumps({"action": "adopt", "id": "c000", "no": "1"}), False)
    finally:
        d.rmdir()
    assert "等几秒再点一次" in msg and msg.startswith("⚠️") and "技术细节" not in msg and _is_update(rows)
    msg, _, _ = _act(ui, "g1", "adopt", "c000")
    assert "已按建议改好" in msg and review.load_draft(project)["c000"]["text"] == "我们今天学习状语从句"


def test_review_js_releases_the_busy_button_when_the_request_finishes():
    """表格没重画（程序没改）时，网页脚本自己把 ⏳ 的按钮放回原样：每个操作记一笔，做完一个放回一个（按顺序）。"""
    js = A.review_js()
    assert "window.__vtSugDone" in js and "pending.shift()" in js and "pending.push(busy || null)" in js
    assert "{el: sug, label: label}" in js and "isConnected" in js
    assert "return []" in A.SUG_DONE_JS and "__vtSugDone" in A.SUG_DONE_JS  # gradio 4.24：网页脚本要返回列表


def test_clip_action_event_runs_the_release_script(tmp_path):
    _gradio4()
    from conftest import make_cfg

    ui = A.WebUI(make_cfg(tmp_path / "ws"))
    app = ui.build()
    deps = app.get_config_file()["dependencies"]
    btn = ui.c["clip_action_btn"]._id
    (click,) = [i for i, d in enumerate(deps) if [btn, "click"] in [list(t) for t in d["targets"]]]
    after = [d for d in deps if d.get("trigger_after") == click]
    assert any(d.get("js") == A.SUG_DONE_JS and not d["outputs"] for d in after)
    # 每次点击按顺序取自己的那一个操作（gradio 正在刷新时，两次挨得很近的点击以前都读到后一个，前一个丢了）
    assert deps[click]["js"] == A.CLIP_TAKE_JS and deps[click]["trigger_mode"] == "multiple"


def test_review_js_queues_every_action_in_order():
    """浏览器里实测（第四轮 g1）：改完字马上点另一行的「采用」这种挨得很近的两个操作，gradio 4.24 刷新网页时会把点击
    推迟到刷新完，两次都读到隐藏输入框里后一个操作，前一个（改的字）丢了。现在每个操作排进 outbox，点击时按顺序取。"""
    js = A.review_js()
    assert "outbox.push(box.value)" in js and "outbox.shift()" in js and "window.__vtTake" in js
    assert "window.__vtTake(payload)" in A.CLIP_TAKE_JS and "return [voice, p, only]" in A.CLIP_TAKE_JS


# ---------------------------------------------------------------------------- appA#3 下载失败时又下载了上次的旧文件
def test_failed_text_download_hides_the_previous_file(tmp_path):
    cfg, project = _voice(tmp_path, ["第一句旧的文字。"])
    ui = A.WebUI(cfg)
    md, f = A._safe("下载改好的文字", 2, 0)(ui.do_download_text)("g1")
    assert f["visible"] is True and Path(f["value"]).exists()
    review.save_draft(project, {"c000": {"text": "第一句老师刚改好的。", "keep": True, "lang": "zh"}})
    d = review.draft_path(project)
    saved = d.read_bytes()
    d.unlink()
    d.mkdir()  # 草稿一时读不了（OSError，不是 ValueError / RuntimeError）
    try:
        md2, f2 = A._safe("下载改好的文字", 2, 0)(ui.do_download_text)("g1")
    finally:
        d.rmdir()
        d.write_bytes(saved)
    assert "没有完成" in md2
    assert f2.get("value") is None and f2.get("visible") is False  # 旧的文件藏起来：浏览器不会再自动下载那份旧的


# ---------------------------------------------------------------------------- appA#4 灰色的行里看不见查找的颜色
def _css_rule(selector_part, prop):
    for block in re.findall(r"([^{}]+)\{([^{}]*)\}", A.APP_CSS):
        sel, body = block
        if selector_part in sel and prop in body:
            return sel, body
    return None


def test_find_highlight_and_suggestion_colors_survive_grey_rows():
    """灰色的行（程序判断不能用）把格子里所有东西都改成灰字、透明背景（!important）：查找的黄色 / 橙色、采用按钮的
    蓝色 / 红色都看不见了，「替换这一处」却照样换那里。比那条多一个 class 的规则把颜色放回来。"""
    cur = _css_rule("tr:has(.vt-mark-unused) td .vt-find-cur", "#f97316!important")
    found = _css_rule("tr:has(.vt-mark-unused) td .vt-find,", "#fde047!important")
    blue = _css_rule("tr:has(.vt-mark-unused) td .vt-sug-blue:not(.vt-sug-busy)", "#2563eb!important")
    red = _css_rule("tr:has(.vt-mark-unused) td .vt-sug-red:not(.vt-sug-busy)", "#dc2626!important")
    assert cur and found and blue and red
    assert "tr.vt-row-unused td .vt-find-cur" in cur[0]  # 旧浏览器（没有 :has）也一样
    # 灰色那条本身不能加 :not()（会盖过「确认以后不用的行号不显示」那条）
    grey = _css_rule("tr:has(.vt-mark-unused) td *", "background:transparent!important")
    assert grey and ":not(" not in grey[0]


# ---------------------------------------------------------------------------- appA#5 只用字幕时一直叫老师再点一次
def test_subtitle_only_setting_is_explained_not_called_interrupted(tmp_path, monkeypatch):
    """「识别文字用哪个引擎」选了「不识别（只用字幕）」、视频又没有同名字幕：以前上方说「识别这一步没做完，再点一次开始准备素材
    就好」，点多少次都一样。现在说清楚是这个设置的原因、怎么改；改成真的识别以后照常识别、说明也没了。"""
    from conftest import make_cfg, make_lecture

    from voicetwin.data import asr as asr_mod
    from voicetwin.data import prepare as prep

    src = tmp_path / "src"
    make_lecture(src / "第2课.wav", repeats=1, with_srt=False)
    cfg = make_cfg(tmp_path / "ws")  # 识别引擎 none
    wf.run_prepare(cfg, "g1", [str(src)])
    project = wf.Project(cfg, "g1")
    recs = project.load_manifest()
    assert recs and all(r.get("no_asr") and not r.get("text") for r in recs)
    count = A._clips_count_md(cfg, "g1")
    assert "不识别（只用字幕）" in count and "通用（中英文都行，推荐）" in count
    assert "中途点了停止" not in count and "请再点一次上面的「开始准备素材」**" not in count
    ui = A.WebUI(cfg)
    assert A.TEXTFIX_NO_ENGINE_INFO in ui.textfix_info("g1")
    md, _, _ = ui.do_confirm("g1")
    assert "不识别（只用字幕）" in md

    class FakeTranscriber:
        progress = None
        progress_range = (0, 1)

        def __init__(self, c):
            pass

        def _load(self):
            pass

        def transcribe(self, wav):
            return SimpleNamespace(text="这是识别出来的一句话。", lang="zh", engine="fake", avg_logprob=-0.2,
                                   no_speech_prob=0.01)

    monkeypatch.setattr(prep, "Transcriber", FakeTranscriber)
    monkeypatch.setattr(asr_mod, "engine_importable", lambda engine: True)
    wf.run_prepare(make_cfg(tmp_path / "ws", prepare={"asr": {"engine": "faster-whisper"}}), "g1", [str(src)])
    after = project.load_manifest()
    assert all(r.get("asr_done") and r.get("text") and "no_asr" not in r for r in after)
    assert "不识别（只用字幕）" not in A._clips_count_md(cfg, "g1")


def test_interrupted_recognition_keeps_the_old_advice(tmp_path):
    """真的是识别中途停下（没有 no_asr 记号）：照旧请老师再点一次「开始准备素材」。两种都有时两句都说、个数分开算。"""
    cfg, project = _voice(tmp_path, ["", "", "有字的一句。"])
    recs = project.load_manifest()
    recs[1]["no_asr"] = True
    project.save_manifest(recs)
    count = A._clips_count_md(cfg, "g1")
    assert "有 1 条还没有识别出文字" in count and "中途点了停止" in count
    assert "有 1 条没有文字" in count and "不识别（只用字幕）" in count


# ---------------------------------------------------------------------------- appB#1 上传的临时文件没了，uploads 里的那一份被删
def test_reprepare_after_upload_expired_keeps_the_saved_copy(tmp_path):
    """网页服务重启过、gradio 的临时文件没了，上传框还显示着那个文件，老师再点「开始准备素材」：以前先把 uploads 里
    好好的那一份删掉、再复制（失败），素材准备整个停下，说「找不到文件，检查路径」。现在照样用 uploads 里那一份。"""
    from conftest import make_cfg, make_lecture

    cfg = make_cfg(tmp_path / "ws")
    up = tmp_path / "gradio_tmp"
    make_lecture(up / "第2课.wav", repeats=1)
    A._prepare_job(cfg, "g1", [str(up / "第2课.wav")], "", {})
    dst = wf.Project(cfg, "g1").root / "uploads" / "第2课.wav"
    size = dst.stat().st_size
    (up / "第2课.wav").unlink()
    A._prepare_job(cfg, "g1", [str(up / "第2课.wav")], "", {})  # 不报错
    assert dst.is_file() and dst.stat().st_size == size
    # 两边都没有了：说清楚是上传的临时文件过期了、怎么办
    with pytest.raises(RuntimeError, match="重新上传"):
        A._prepare_job(cfg, "g1", [str(up / "第3课.wav")], "", {})


def test_failed_upload_copy_keeps_the_previous_copy(tmp_path, monkeypatch):
    """换了一个同名、大小不同的文件，复制到一半失败（硬盘满了）：uploads 里原来的那一份还在，没有留下半个文件。"""
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    updir = wf.Project(cfg, "g1").root / "uploads"
    updir.mkdir(parents=True)
    (updir / "a.wav").write_bytes(b"old" * 10)
    src = tmp_path / "a.wav"
    src.write_bytes(b"new" * 20)

    def no_link(a, b):
        raise OSError("不能硬链接")

    def disk_full(a, b):
        Path(b).write_bytes(b"ne")
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(A.os, "link", no_link)
    monkeypatch.setattr(A.shutil, "copyfile", disk_full)
    with pytest.raises(OSError):
        A._prepare_job(cfg, "g1", [str(src)], "", {})
    assert (updir / "a.wav").read_bytes() == b"old" * 10
    assert sorted(p.name for p in updir.iterdir()) == ["a.wav"]
    monkeypatch.undo()
    monkeypatch.setattr(wf, "run_prepare", lambda *a, **k: {})
    A._prepare_job(cfg, "g1", [str(src)], "", {})  # 换成新的文件
    assert (updir / "a.wav").read_bytes() == b"new" * 20


# ---------------------------------------------------------------------------- appB#4 顶部的「当前声音状态」不跟着变
def test_voice_status_follows_confirm_and_delete(prepared, tmp_path):
    from conftest import make_cfg

    cfg0, project0, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project0.root, ws / "g1")
    for f in ("models.json", "review_confirmed.json"):
        if (ws / "g1" / f).exists():
            (ws / "g1" / f).unlink()
    cfg = make_cfg(ws)
    ui = A.WebUI(cfg)
    assert "确认训练素材" in ui.voice_status("g1")
    ui.do_confirm("g1")
    st = ui.voice_status("g1")
    assert "去「② 训练模型」点「开始训练」" in st and "确认训练素材" not in st
    rid = next(r["id"] for r in wf.Project(cfg, "g1").load_manifest() if review.is_material(r))
    _act(ui, "g1", "delete", rid)
    assert "确认训练素材" in ui.voice_status("g1")


def test_review_events_refresh_the_voice_status(tmp_path):
    """确认训练素材、保存修改、表格里的操作、替换以后，都接着刷新页面顶部的「当前声音状态」。"""
    _gradio4()
    from conftest import make_cfg

    ui = A.WebUI(make_cfg(tmp_path / "ws"))
    app = ui.build()
    deps = app.get_config_file()["dependencies"]
    status = ui.c["voice_status"]._id

    def chain(start):
        out, todo = [], [start]
        while todo:
            k = todo.pop()
            out.append(k)
            todo += [i for i, d in enumerate(deps) if d.get("trigger_after") == k]
        return out

    for name in ("confirm_btn", "save_clips", "clip_action_btn", "find_rep1", "find_repall", "find_undo"):
        comp = ui.c[name]._id if name in ui.c else None
        starts = [i for i, d in enumerate(deps) if comp is not None and [comp, "click"] in [list(t) for t in d["targets"]]]
        if name == "save_clips":  # 「保存修改」不在 self.c 里：按处理函数找
            starts = [i for i, f in enumerate(app.fns) if getattr(getattr(f.fn, "__wrapped__", f.fn), "__name__", "") == "do_save"]
        assert starts, name
        assert any(status in deps[k]["outputs"] for k in chain(starts[0])), name


# ---------------------------------------------------------------------------- appB#5 准备完说「可以去训练了」
def test_prepare_done_points_to_confirm_before_training(tmp_path, lecture_dir, monkeypatch):
    """准备素材做完：还没确认训练素材时不能说「可以去「② 训练模型」了」（点了开始训练会被拦下），要说先确认；
    确认以后又加了新素材，拦下的原因里要说「加了新素材」（以前只说改了文字、删除……老师没做过这些）。"""
    from conftest import make_cfg, make_lecture

    from voicetwin.errors import explain

    toasts = []
    monkeypatch.setattr(A, "_info", lambda m: toasts.append(m))
    cfg = make_cfg(tmp_path / "ws")
    ui = A.WebUI(cfg)
    last = dict(zip(ui.PREP_OUT, list(ui.do_prepare("g1", None, str(lecture_dir), "none", "auto", "off", False))[-1]))
    assert last["prep_md"].startswith("### ✅ 素材准备好了") and "确认训练素材" in last["prep_md"]
    assert toasts and not any("可以去「② 训练模型」了" in t for t in toasts) and "确认训练素材" in toasts[-1]
    wf.review_confirm(cfg, "g1")
    more = tmp_path / "more"
    make_lecture(more / "第2课.wav", repeats=1, seed=5)
    toasts.clear()
    list(ui.do_prepare("g1", None, str(more), "none", "auto", "off", False))
    assert "确认训练素材" in toasts[-1]
    why = wf.training_blocker_for(cfg, "g1")
    assert "加了新素材" in why and explain(RuntimeError(why)).key == "confirm_stale"  # 中文说明照样认得出
    assert "加了新素材" in A._clips_count_md(cfg, "g1")
    # 确认好了再准备（什么都没加）：照旧说可以去训练
    wf.review_confirm(cfg, "g1")
    toasts.clear()
    list(ui.do_prepare("g1", None, str(more), "none", "auto", "off", False))
    assert "可以去「② 训练模型」了" in toasts[-1]


# ---------------------------------------------------------------------------- appB#7 「像你本人 X%（每句的平均）」
def test_generation_summary_says_how_the_whole_percentage_is_counted():
    """整篇的百分比是按每句的长短算的（完美 / 一模一样是最终那个版本整篇打的分），不是各句的平均：说明要写对（规定 7）。"""
    segs = [{"pct": 80.0, "duration": 1.0}] * 10 + [{"pct": 97.0, "duration": 9.0}] * 10
    md = A._gen_summary_md(SimpleNamespace(overall_pct=94.3, segments=segs, duration=100))
    line = next(x for x in md.split("\n\n") if "像你本人 **94.3%**" in x)
    assert "每句的平均" not in line and "按每句的长短算" in line
    two = SimpleNamespace(overall_pct=95.0, segments=segs, duration=100,
                          variants=[{"path": "a.wav", "name": "未去杂音", "pct": 95.0, "final": True},
                                    {"path": "b.wav", "name": "去杂音", "pct": 93.0}])
    assert "最终用的那个版本整篇打的分" in A._gen_summary_md(two)
    plain = A._gen_summary_md(SimpleNamespace(segments=[{"pct": 80.0}, {"pct": 90.0}], duration=10))
    assert "像你本人 **85.0%**（每句的平均）" in plain  # 没有整篇分数时才是各句的平均


# ---------------------------------------------------------------------------- appC#2 gradio 的临时文件从来不删
def test_gradio_cache_cleanup_can_actually_delete():
    """gradio 4.24 判断「多久以前」用的是 timedelta.seconds（只有不满一天的部分，0~86399）：以前写的 (86400, 86400)
    永远不成立、什么都不删。清理「多久以前」一定要少于一天。"""
    from datetime import timedelta

    freq, age = A.GRADIO_DELETE_CACHE
    assert freq <= 3600 and age < 86400
    assert any(timedelta(hours=h).seconds > age for h in range(1, 24))  # 照 gradio 的写法，一天里有时候会删


def test_build_passes_the_working_cleanup_setting(tmp_path):
    _gradio4()
    from conftest import make_cfg

    app = A.WebUI(make_cfg(tmp_path / "ws")).build()
    assert tuple(app.delete_cache) == A.GRADIO_DELETE_CACHE


def test_launcher_puts_gradio_files_in_the_workspace_and_cleans_old_ones(tmp_path, monkeypatch):
    """关掉黑色窗口（点 ×）时 gradio 自己的清理不会运行：临时文件改放在工作文件夹里的 __gradio_cache（不放 C 盘的
    %TEMP%），每次启动时删掉一天以前的；声音库里不显示这个文件夹；已经设了 GRADIO_TEMP_DIR 的照旧。"""
    from conftest import make_cfg

    from voicetwin.webui import launcher

    monkeypatch.delenv("GRADIO_TEMP_DIR", raising=False)
    cfg = make_cfg(tmp_path / "ws")
    cache = Path(launcher._use_workspace_cache(cfg))
    assert cache == tmp_path / "ws" / launcher.GRADIO_CACHE_DIR and os.environ["GRADIO_TEMP_DIR"] == str(cache)
    assert launcher.GRADIO_CACHE_DIR not in [p.voice for p in wf._voice_dirs(cfg)]
    old = cache / "abc123" / "第1课.wav"
    old.parent.mkdir()
    old.write_bytes(b"x")
    assert launcher._clean_old_files(str(cache), 86400, now=time.time()) == 0 and old.exists()  # 刚放进来的不删
    assert launcher._clean_old_files(str(cache), 86400, now=time.time() + 2 * 86400) == 1
    assert not old.exists() and not old.parent.exists() and cache.exists()  # 空了的子文件夹也删，本身留着
    monkeypatch.setenv("GRADIO_TEMP_DIR", str(tmp_path / "mine"))
    assert launcher._use_workspace_cache(cfg) is None and os.environ["GRADIO_TEMP_DIR"] == str(tmp_path / "mine")
