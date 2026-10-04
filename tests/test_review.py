"""校对表的数据逻辑（voicetwin/data/review.py）：草稿、蓝色 / 红色位置、修改建议、保存、删除 / 撤销删除。"""

import shutil

import pytest

from voicetwin import workflows as wf
from voicetwin.data import proofcheck as P
from voicetwin.data import review as R
from voicetwin.project import apply_text_edit
from voicetwin.webui import app as A

T = "大多数情况下，艾子所代替的一般是整个句子。在定语从句中，艾子主要被翻译为正如。"
S1, S2 = T.index("艾子"), T.rindex("艾子")


def _rec(**kw):
    rec = {"id": "c1", "text": T, "keep": True, "lang": "zh",
           "suspect": {"spans": [[S1, S1 + 2], [S2, S2 + 2]], "alt": T.replace("艾子", "as"), "reasons": ["r"]}}
    rec.update(kw)
    return rec


@pytest.fixture
def voice(prepared, tmp_path):
    from conftest import make_cfg

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    cfg2 = make_cfg(ws)
    proj = wf.Project(cfg2, project.voice)
    recs = proj.load_manifest()
    for r in recs:
        r.pop("suspect", None)
    proj.save_manifest(recs)
    return cfg2, proj


# ---------------------------------------------------------------------------- 红 / 蓝 / 建议
def test_analyze_untouched_text():
    info = R.analyze(_rec())
    assert info["red"] == [(S1, S1 + 2), (S2, S2 + 2)] and info["blue"] == [] and info["active"]
    assert info["edits"] == [(S1, S1 + 2, "as"), (S2, S2 + 2, "as")] and not info["adopted"]
    assert R.describe_edits(T, info["edits"]) == "艾子 → as（2 处）"  # 一样的改动合在一起说


def test_fixing_one_spot_turns_it_blue_and_keeps_the_other_red():
    cur = T[:S2] + "as" + T[S2 + 2:]
    info = R.analyze(_rec(), cur)
    assert info["red"] == [(S1, S1 + 2)] and info["blue"] == [(S2, S2 + 2)]
    assert info["edits"] == [(S1, S1 + 2, "as")]
    new = R.apply_edits(cur, info["edits"])
    assert new == T.replace("艾子", "as")
    done = R.analyze(_rec(), new)
    assert done["red"] == [] and done["edits"] == [] and done["adopted"] and not done["active"]
    assert done["blue"] == [(S1, S1 + 2), (S2, S2 + 2)]


def test_red_marks_follow_text_moved_by_an_edit_before_them():
    cur = "其实" + T  # 前面加了两个字：红字的位置跟着往后挪
    info = R.analyze(_rec(), cur)
    assert info["red"] == [(S1 + 2, S1 + 4), (S2 + 2, S2 + 4)] and info["blue"] == [(0, 2)]
    assert cur[info["red"][0][0]:info["red"][0][1]] == "艾子"


def test_deleted_words_are_reported_for_blue_strikethrough():
    rec = {"id": "x", "text": "我们我们来看一下", "keep": True, "lang": "zh"}
    info = R.analyze(rec, "我们来看一下")
    assert info["blue"] == [] and [g for _, g in info["deleted"]] == ["我们"] and info["deleted"][0][0] in (0, 2)
    html = A._colored_html(info)
    assert 'class="vt-blue-del"' in html and "我们" in html


def test_insert_suggestion_clears_neighbour_mark_once_adopted():
    # 查错字时"这里漏了字"：标的是缺字位置两边的字；按建议补上以后不再标红
    rec = {"id": "x", "text": "我们来看一下吧", "keep": True, "lang": "zh",
           "suspect": {"spans": [[5, 7]], "alt": "我们来看一下了吧", "reasons": ["这里可能漏了「了」"]}}
    info = R.analyze(rec)
    assert info["edits"] == [(6, 6, "了")]
    new = R.apply_edits(rec["text"], info["edits"])
    after = R.analyze(rec, new)
    assert new == "我们来看一下了吧" and after["red"] == [] and after["edits"] == [] and after["adopted"]
    # 老师自己已经补上了：建议不会再补一次
    assert R.analyze(rec, "我们来看一下了吧")["edits"] == []


def test_suggestion_edits_cover_whole_english_words():
    edits = R.suggestion_edits("我们今天讲 VFIXED 的用法", "我们今天讲 V fixed 的用法")
    assert edits == [(6, 12, "V fixed")]
    edits = R.suggestion_edits("the number of smoker has dropped", "the number of smokers have dropped")
    assert R.describe_edits("the number of smoker has dropped", edits) == "smoker → smokers；has → have"


def test_colored_html_escapes_markup():
    rec = {"id": "x", "text": "1. *设置* <b>x</b>", "keep": True, "lang": "zh",
           "suspect": {"spans": [[3, 7]], "alt": "", "reasons": ["r"]}}
    html = A._colored_html(R.analyze(rec))
    assert "<b>" not in html and "*" not in html and html.count('class="vt-red"') == 1
    assert A._colored_html(R.analyze({"id": "y", "text": "没有问题", "keep": True})) == ""


def test_apply_text_edit_keeps_untouched_marks_and_original_text():
    rec = _rec()
    apply_text_edit(rec, T[:S2] + "as" + T[S2 + 2:])
    assert rec["orig_text"] == T and rec["suspect"]["text"] == T and rec["text_edited"]
    assert R.analyze(rec)["red"] == [(S1, S1 + 2)]
    apply_text_edit(rec, T.replace("艾子", "as"))
    info = R.analyze(rec)
    assert rec["orig_text"] == T and not info["active"] and info["adopted"]  # 不再算可能有错；建议生效（按钮红）
    assert info["blue"] == [(S1, S1 + 2), (S2, S2 + 2)]
    apply_text_edit(rec, T.replace("艾子", "as") + "再加一句。")
    assert "suspect" in rec  # 采用过的建议一直记着（按钮一直是红的，也能撤销）
    rec2 = {"id": "z", "text": "一二三四", "suspect": {"spans": [[0, 1]], "alt": "", "reasons": ["r"]}}
    apply_text_edit(rec2, "改一二三四")  # 红字被改掉、又没有建议：整个标记去掉
    assert "suspect" not in rec2


def test_unadopt_reverts_only_suggestion_spots():
    rec = _rec()
    adopted = T.replace("艾子", "as")
    info = R.analyze(rec, "其实" + adopted)  # 采用以后老师又在前面加了两个字
    assert info["adopted"] and R.describe_adopted("其实" + adopted, info["undo"]) == "艾子 → as（2 处）"
    assert R.apply_edits("其实" + adopted, info["undo"]) == "其实" + T  # 只改回建议的地方


# ---------------------------------------------------------------------------- 草稿、保存、删除
def test_draft_round_trip(voice):
    cfg, proj = voice
    rec = proj.load_manifest()[0]
    out = R.set_draft(proj, rec["id"], text=rec["text"] + "改")
    assert out["dirty"] and R.load_draft(proj)[rec["id"]]["text"].endswith("改")
    out = R.set_draft(proj, rec["id"], text=rec["text"])  # 改回原样：草稿自动去掉
    assert not out["dirty"] and R.load_draft(proj) == {} and not R.draft_path(proj).exists()
    with pytest.raises(ValueError, match="空的"):
        R.set_draft(proj, rec["id"], text="  ")
    with pytest.raises(KeyError):
        R.set_draft(proj, "没有这个", keep=False)
    R.draft_path(proj).write_text("坏掉的文件", encoding="utf-8")
    assert R.load_draft(proj) == {}  # 草稿文件坏了：当作没有，不报错


def test_save_rows_only_saves_requested_rows(voice):
    cfg, proj = voice
    a, b = proj.load_manifest()[:2]
    R.set_draft(proj, a["id"], text="第一条改了。")
    R.set_draft(proj, b["id"], keep=not b.get("keep", True))
    res = R.save_rows(proj, [a["id"]])
    assert res["saved"] == [a["id"]] and res["changed"]["text"] == 1 and not res["csv_locked"]
    recs = {r["id"]: r for r in proj.load_manifest()}
    assert recs[a["id"]]["text"] == "第一条改了。" and recs[a["id"]]["edited"] is True
    assert recs[a["id"]]["orig_text"] == a["text"] and b["id"] in R.load_draft(proj)
    assert R.has_saved_edit(recs[a["id"]]) and "第一条改了。" in proj.csv_path.read_text(encoding="utf-8-sig")
    res = R.save_rows(proj)
    assert res["saved"] == [b["id"]] and R.load_draft(proj) == {}
    assert {r["id"]: r for r in proj.load_manifest()}[b["id"]]["manual_keep"] is (not b.get("keep", True))


def test_delete_and_undo_restore_previous_state(voice):
    cfg, proj = voice
    rec = proj.load_manifest()[0]
    before = {k: rec.get(k) for k in ("keep", "manual_keep", "drop_reason")}
    R.delete_clip(proj, rec["id"])
    d = {r["id"]: r for r in proj.load_manifest()}[rec["id"]]
    assert d["deleted"] and d["keep"] is False and d["drop_reason"] == R.DELETED_REASON
    assert [r["id"] for r in R.deleted_records(proj)] == [rec["id"]]
    # 重新统计（过滤、挑参考音频）时，删除的一直不用
    wf.apply_review(cfg, proj.voice, read_csv=False)
    d = {r["id"]: r for r in proj.load_manifest()}[rec["id"]]
    assert d["keep"] is False and d["deleted"]
    R.restore_clip(proj, rec["id"])
    back = {r["id"]: r for r in proj.load_manifest()}[rec["id"]]
    assert "deleted" not in back and {k: back.get(k) for k in before} == before


def test_review_save_rereads_summary_without_csv(voice, monkeypatch):
    cfg, proj = voice
    rec = proj.load_manifest()[0]
    R.set_draft(proj, rec["id"], text="保存时表格被锁住。")

    def locked(self, records=None):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(wf.Project, "export_csv", locked)
    res = wf.review_save(cfg, proj.voice)
    assert res["csv_locked"] and res["summary"]
    # 没有读回旧的 CSV（否则会把刚保存的修改改回去）
    assert {r["id"]: r for r in proj.load_manifest()}[rec["id"]]["text"] == "保存时表格被锁住。"


def test_prune_draft_drops_missing_clips(voice):
    cfg, proj = voice
    R.save_draft(proj, {"不存在": {"text": "x", "keep": True, "lang": "zh"}})
    assert R.prune_draft(proj) == 1 and R.load_draft(proj) == {}


# ---------------------------------------------------------------------------- 查错字：素材里本来就有的英文词
def test_known_english_word_becomes_a_suggestion():
    other = "大多数情况下as所代替的一般是整个句子在定语从句中as主要被翻译为正如"
    plain = P.build_suspect(T, other, engine=P.ENGINE_FUNASR)
    assert plain and plain["alt"] == ""  # 以前：只标红，没有建议（FunASR 的英文一般不可靠）
    sus = P.build_suspect(T, other, engine=P.ENGINE_FUNASR, vocab=frozenset({"as"}))
    assert sus["alt"] == T.replace("艾子", "as")


def test_known_english_rule_stays_conservative():
    vocab = frozenset({"as", "so", "the"})
    assert P._known_english(["艾", "子"], ["as"], vocab)
    assert not P._known_english(["艾", "子"], ["as"], frozenset())  # 素材里没有这个词
    assert not P._known_english(["搜"], ["so"], vocab)  # so / yeah / oh 这类口头语不算
    assert not P._known_english(list("这是一个很长的中文句子"), ["the"], vocab)  # 汉字太多：不像英文的读音
    recs = [{"text": "也就是说 as所代替的"}, {"text": "As it is reported"}, {"text": "it"},
            {"text": "as", "deleted": True}]
    assert P.voice_vocab(recs) == frozenset({"as", "it"})  # 删除的那一条不算（as 只算了两段）


def test_prepare_again_finishes_missing_text(tmp_path, lecture_dir, monkeypatch):
    """识别文字中途停了（片段切好了、没有文字）：再点一次「开始准备素材」会接着识别，片段不会重新切、删除的还是删除。"""
    from types import SimpleNamespace

    from conftest import make_cfg
    from voicetwin.data import asr as asr_mod
    from voicetwin.data import prepare as prep

    cfg = make_cfg(tmp_path / "ws")
    wf.run_prepare(cfg, "v", [str(lecture_dir)])
    proj = wf.Project(cfg, "v")
    recs = proj.load_manifest()
    before = [(r["id"], r["duration"]) for r in recs]
    for r in recs:
        r.update(text="", lang="", keep=True)
        r.pop("asr_done", None)
    proj.save_manifest(recs)
    R.delete_clip(proj, recs[0]["id"])

    class FakeTranscriber:
        progress = None
        progress_range = (0, 1)

        def __init__(self, cfg):
            pass

        def _load(self):
            pass

        def transcribe(self, wav):
            return SimpleNamespace(text="这是识别出来的一句话。", lang="zh", engine="fake", avg_logprob=-0.2,
                                   no_speech_prob=0.01)

    monkeypatch.setattr(prep, "Transcriber", FakeTranscriber)
    monkeypatch.setattr(asr_mod, "engine_importable", lambda engine: True)
    cfg2 = make_cfg(tmp_path / "ws", prepare={"asr": {"engine": "faster-whisper"}})
    wf.run_prepare(cfg2, "v", [str(lecture_dir)])
    after = proj.load_manifest()
    assert [(r["id"], r["duration"]) for r in after] == before  # 没有重新切
    assert all(r["text"] == "这是识别出来的一句话。" and r["asr_done"] for r in after)
    by_id = {r["id"]: r for r in after}
    assert by_id[recs[0]["id"]]["deleted"] and by_id[recs[0]["id"]]["keep"] is False  # 删除的还是删除
    c = R.material_counts(after)
    assert c["deleted"] == 1 and c["no_text"] == 0 and c["material"] >= 1


def test_describe_merges_same_change_and_shows_the_word():
    """10-03 截图发现：一句里两处「借词」的建议写成「借 → 介；借 → 介」（只差一个字时只写那个字、同样的改法重复写）
    → 带上所在的词、一样的合在一起：「借词 → 介词（2 处）」。有没有 jieba 都一样（没有时带上后面一个汉字）。"""
    t = "在这个句子中，which前面的借词是in，借词加上关系代词就可以引导一个定语从句。"
    alt = t.replace("借词", "介词")
    s1, s2 = t.index("借词"), t.rindex("借词")
    rec = {"id": "a", "text": t, "lang": "zh", "keep": True,
           "suspect": {"spans": [[s1, s1 + 2], [s2, s2 + 2]], "alt": alt, "reasons": ["r"], "score": 0.75}}
    assert R.describe_change(t, alt) == "借词 → 介词（2 处）"
    assert R.describe_states(rec, t, alt) == "借词 → 介词（2 处）"
    info = R.analyze(rec, t)
    assert R.describe_edits(t, info["edits"]) == "借词 → 介词（2 处）"
    done = R.analyze(rec, alt)  # 采用以后：「已采用」那里也一样
    assert done["adopted"] and R.describe_adopted(alt, done["undo"]) == "借词 → 介词（2 处）"
    # 不同的改法照样分开写（带上所在的词：「了 → 过」说成「去了 → 去过」）；超过 limit 种写「还有」
    two = R.describe_change("他去了学校", "她去过学校").split("；")
    assert len(two) == 2 and "她" in two[0] and "过" in two[1] and "处）" not in "".join(two)
    assert R.describe_change("cat x dog x pig x cow", "bat x log x big x how", limit=2) == "cat → bat；dog → log；还有 2 处"


# ---------------------------------------------------------------------------- 第四轮找 bug（g3：校对表的数据）
def _rows(tmp_path, rows, name="v"):
    """不用录音的小声音：rows 里每条覆盖默认的 id / 文字 / 保留 / 语言。"""
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    proj = wf.Project(cfg, name).ensure()
    proj.save_manifest([dict({"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "duration": 3.0, "keep": True,
                              "split": "train", "lang": "zh"}, **r) for i, r in enumerate(rows)])
    return cfg, proj


def test_typed_text_on_grey_clip_is_not_pinned_unused_after_prepare(tmp_path, lecture_dir, monkeypatch):
    """还没识别出文字（灰色、不用）的一条，老师自己打了字（没保存），再点「开始准备素材」识别出文字、程序判断能用了：
    以前「保存修改」把草稿里抄的旧「不用」当成老师选的写回去（manual_keep=False），这条再也不用来训练，还说「改成了要用 / 不用」。"""
    from types import SimpleNamespace

    from conftest import make_cfg
    from voicetwin.data import asr as asr_mod
    from voicetwin.data import prepare as prep

    cfg = make_cfg(tmp_path / "ws")
    wf.run_prepare(cfg, "v", [str(lecture_dir)])
    proj = wf.Project(cfg, "v")
    recs = proj.load_manifest()
    for r in recs:
        r.update(text="", lang="", keep=False, drop_reason="没有文字")
        r.pop("asr_done", None)
    proj.save_manifest(recs)
    cid = recs[0]["id"]
    R.set_draft(proj, cid, text="这是老师自己打的一句话。")

    class FakeTranscriber:
        progress = None
        progress_range = (0, 1)

        def __init__(self, cfg):
            pass

        def _load(self):
            pass

        def transcribe(self, wav):
            return SimpleNamespace(text="这是识别出来的一句话。", lang="zh", engine="fake", avg_logprob=-0.2,
                                   no_speech_prob=0.01)

    monkeypatch.setattr(prep, "Transcriber", FakeTranscriber)
    monkeypatch.setattr(asr_mod, "engine_importable", lambda engine: True)
    cfg2 = make_cfg(tmp_path / "ws", prepare={"asr": {"engine": "faster-whisper"}})
    wf.run_prepare(cfg2, "v", [str(lecture_dir)])
    R.prune_draft(proj)  # 准备素材做完以后网页做的
    rec = {r["id"]: r for r in proj.load_manifest()}[cid]
    assert rec["keep"] is True  # 程序判断能用了
    vals = R.current_values(rec, R.load_draft(proj).get(cid))
    assert vals["keep"] is True and vals["text"] == "这是老师自己打的一句话。"  # 表格里不再显示成灰色
    res = R.save_rows(proj)
    rec = {r["id"]: r for r in proj.load_manifest()}[cid]
    assert res["changed"] == {"text": 1, "keep": 0, "lang": 0}  # 不说「改成了要用 / 不用」
    assert rec["keep"] is True and rec.get("manual_keep") is None and R.is_material(rec)


def test_unsaved_edit_does_not_force_a_clip_the_program_dropped(tmp_path):
    """反过来：草稿里抄的是「要用」，之后程序重新过滤把这句判成不能用（声音不像本人）：以前保存时把它硬塞进训练（manual_keep=True）。
    老师自己点的「✅ 这一条也要用」照样算数。"""
    cfg, proj = _rows(tmp_path, [{"text": "第一句话。"}, {"text": "第二句话。", "keep": False, "drop_reason": "声音不像本人"}])
    R.set_draft(proj, "c000", text="第一句话改了。")
    R.set_draft(proj, "c001", keep=True)  # 老师自己点的「要用」
    recs = proj.load_manifest()
    recs[0].update(keep=False, drop_reason="声音不像本人")  # 程序重新过滤
    recs[1].update(keep=True, drop_reason="")  # 程序自己也判成能用了：老师点的「要用」还在
    proj.save_manifest(recs)
    res = R.save_rows(proj)
    a, b = proj.load_manifest()
    assert a["text"] == "第一句话改了。" and a["keep"] is False and a.get("manual_keep") is None
    assert res["changed"]["keep"] == 0 and b["keep"] is True


def test_unsaved_edit_does_not_put_back_an_old_language(tmp_path):
    """草稿里抄的语言：之后在 Excel 里把这句的语言改成了英文，「保存修改」以前把抄的「中文」当成老师选的写回去。"""
    cfg, proj = _rows(tmp_path, [{"text": "这个例子很简单。"}])
    R.set_draft(proj, "c000", text="这个例子非常简单。")
    recs = proj.load_manifest()
    recs[0]["lang"] = "en"  # 从 Excel 读回来的（老师手动选的）
    proj.save_manifest(recs)
    res = R.save_rows(proj)
    rec = proj.load_manifest()[0]
    assert rec["text"] == "这个例子非常简单。" and rec["lang"] == "en" and res["changed"]["lang"] == 0


def test_old_drafts_without_own_fields_still_work(tmp_path):
    """旧版本存的草稿（没记改过哪几样）：和以前一样按草稿算，只有抄下来的「不用」不算（表格里只能改成「要用」）；
    网页数没保存的条数时顺手记下改过哪几样。"""
    cfg, proj = _rows(tmp_path, [{"text": "第一句。"}, {"text": "第二句。", "keep": False}, {"text": "第三句。"}])
    R.save_draft(proj, {"c000": {"text": "第一句改了。", "keep": False, "lang": "zh"},  # 「不用」是抄的旧值
                        "c001": {"text": "第二句。", "keep": True, "lang": "zh"},  # 老师点的「要用」
                        "c002": {"text": "第三句。", "keep": True, "lang": "en"}})  # 老师改的语言
    recs = {r["id"]: r for r in proj.load_manifest()}
    draft = R.load_draft(proj)
    assert R.current_values(recs["c000"], draft["c000"]) == {"text": "第一句改了。", "keep": True, "lang": "zh"}
    assert R.current_values(recs["c001"], draft["c001"])["keep"] is True
    assert R.current_values(recs["c002"], draft["c002"])["lang"] == "en"
    assert R.unsaved_count(proj) == 3
    assert {k: v["own"] for k, v in R.load_draft(proj).items()} == {"c000": ["text"], "c001": ["keep"], "c002": ["lang"]}
    R.save_rows(proj)
    a, b, c = proj.load_manifest()
    assert a["keep"] is True and a.get("manual_keep") is None and b["manual_keep"] is True and c["lang"] == "en"


def test_one_click_adopt_keeps_following_the_saved_keep(tmp_path):
    """一键校正（全部采用）存的草稿也只记下改了文字：之后程序把这句判成不能用，保存时不会硬塞进训练。"""
    t = "大多数情况下，艾子所代替的一般是整个句子。"
    s1 = t.index("艾子")
    cfg, proj = _rows(tmp_path, [{"text": t, "suspect": {"spans": [[s1, s1 + 2]], "alt": t.replace("艾子", "as"),
                                                          "reasons": ["文字校正的"], "score": 0.7, "text": t,
                                                          "src": "transcript"}}])
    assert R.adopt_all_suggestions(proj)["rows"] == 1
    assert R.load_draft(proj)["c000"]["own"] == ["text"]
    recs = proj.load_manifest()
    recs[0].update(keep=False, drop_reason="声音不像本人")
    proj.save_manifest(recs)
    R.save_rows(proj)
    rec = proj.load_manifest()[0]
    assert "as" in rec["text"] and rec["keep"] is False and rec.get("manual_keep") is None


def test_revert_survives_a_briefly_locked_draft_file(tmp_path, monkeypatch):
    """Windows 上「撤销这一行的修改」的同时别的按钮正读着草稿文件：删不掉。以前悄悄当成删掉了（页面说已撤销），
    下次「保存修改」把撤销了的字存了进去。现在等一会儿再删；一直删不掉就写成空的。"""
    from pathlib import Path

    from voicetwin.utils import atomic

    cfg, proj = _rows(tmp_path, [{"text": "首先我们看一个最简单的例子。"}])
    monkeypatch.setattr(atomic, "RETRY_WAITS", [0.0] * 3)
    real = Path.unlink
    fails = {"n": 2}

    def locked(self, *a, **kw):
        if self.name in (R.DRAFT_FILE, R.REJECTED_FILE) and fails["n"] > 0:
            fails["n"] -= 1
            raise PermissionError(32, "另一个程序正在使用此文件，进程无法访问。")
        return real(self, *a, **kw)

    monkeypatch.setattr(Path, "unlink", locked)
    R.set_draft(proj, "c000", text="首先我们看一个最难的例子。")
    assert R.discard_draft(proj, "c000") == 1
    assert R.load_draft(proj) == {} and not R.draft_path(proj).exists()  # 等了一下就删掉了
    R.save_rows(proj)
    assert proj.load_manifest()[0]["text"] == "首先我们看一个最简单的例子。"
    # 一直删不掉：写成空的（读出来也是没有草稿）
    R.set_draft(proj, "c000", text="首先我们看一个最难的例子。")
    fails["n"] = 99
    assert R.discard_draft(proj, "c000") == 1 and R.load_draft(proj) == {}
    fails["n"] = 99
    R._save_rejected(proj, {})
    assert R.load_rejected(proj) == {}


def test_replace_that_cleanup_turns_back_is_not_counted(tmp_path):
    """查找「,」替换成「，」：表格的统一写法（英文后面的逗号一律半角）马上又改回去。以前说「已经把 5 处换成…（🔴 没保存）」，
    其实什么都没变，还冲掉了上一次替换的撤销记录；「替换这一处」一直停在同一处。"""
    cfg, proj = _rows(tmp_path, [{"text": "这里的 as,意思是正如。"}, {"text": "Next, let's look at it, as you see."},
                                 {"text": "我们先来看艾子的用法。"}])
    ui = A.WebUI(cfg)
    R.replace_matches(proj, "艾子", "as")
    res = R.replace_matches(proj, ",", "，")
    assert (res["count"], res["rows"], res["same"]) == (0, 0, 2)
    assert R.undo_replace(proj)["rows"] == 1  # 上一次替换的撤销记录还在
    R.replace_matches(proj, "艾子", "as")
    status = ui.do_replace_all("v", ",", "，", True)[0]
    assert "已经把" not in status and "没有换" in status and "半角" in status
    assert R.has_undo(proj)
    ui.do_find("v", ",", True)
    first = R.load_find(proj)["i"]
    status = ui.do_replace_one("v", ",", "，", True)[0]
    assert "换好了" not in status and "跳到下一处" in status and R.load_find(proj)["i"] == first + 1


def test_undo_replace_keeps_the_language_chosen_afterwards(tmp_path):
    """替换以后老师又把这一句的语言改成了中文，再点「撤销刚才的替换」：以前把语言也改回替换以前的英文（还算「改回去了」）。
    替换本身让语言跟着变了的，撤销时照样变回来。"""
    cfg, proj = _rows(tmp_path, [{"text": "Next, let's look at a slightly more complex example.", "lang": "en"},
                                 {"text": "我们来看 the example。"}])
    R.replace_matches(proj, "slightly", "much")
    R.set_draft(proj, "c000", lang="zh")
    assert R.undo_replace(proj) == {"rows": 1, "kept": 0}
    rec = proj.load_manifest()[0]
    vals = R.current_values(rec, R.load_draft(proj).get("c000"))
    assert vals == {"text": rec["text"], "keep": True, "lang": "zh"}  # 文字改回去了，语言照老师后来选的
    # 替换让语言自动变了（中文 → 英文）：撤销时语言也变回来，而且不算老师选的
    R.discard_draft(proj)
    R.replace_matches(proj, "我们来看", "Let's see")
    rec1 = proj.load_manifest()[1]
    assert R.current_values(rec1, R.load_draft(proj)["c001"])["lang"] == "en"
    assert R.undo_replace(proj)["rows"] == 1 and "c001" not in R.load_draft(proj)
