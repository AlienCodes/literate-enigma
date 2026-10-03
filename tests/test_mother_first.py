"""母本优先（10-04 老师的要求）：识别出来的句子先和母本对照，母本里有差不多（或者一模一样）的句子，
和母本不一样的地方就是错误，按母本改；按内容找，不按片段 id。

老师的原话：「识别出来的这些句子，先去跟母本对照。一般母本都会有差不多或者原模原样的句子。跟母本不一样的地方，
那很明显就是错误的地方。」「这个自动检查错字功能，它的底层逻辑也是要以母本为主……母本是最优先级。」

数据：research/文字校正/老师的母本/母本_原文.csv（老师修缮以前、识别引擎写的句子）和母本_修缮后.csv（正确答案），
程序自带的母本（core_corpus.tsv）就是修缮好的这些句子。这些测试在修改以前的代码上都会失败
（片段 id 变了、切的位置不一样时很多句子改不对；自动查错字的建议不看母本；和母本矛盾的建议留着）。"""

import csv
import difflib
import importlib.util
import unittest.mock as um
from pathlib import Path

import pytest

from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.data import transcript_fix as tf
from voicetwin.utils.textutil import clean_transcript

HAS_PINYIN = importlib.util.find_spec("pypinyin") is not None
HAS_JIEBA = importlib.util.find_spec("jieba") is not None or importlib.util.find_spec("jieba_fast") is not None
need_both = pytest.mark.skipif(not (HAS_PINYIN and HAS_JIEBA), reason="没有装 pypinyin / jieba（整合包里有）")
MOTHER_DIR = Path(__file__).resolve().parents[1] / "research" / "文字校正" / "老师的母本"
VOICE = "母本优先"


def _teacher_rows():
    orig = list(csv.DictReader(open(MOTHER_DIR / "母本_原文.csv", encoding="utf-8-sig")))
    clean = {r["id"]: r["text"] for r in csv.DictReader(open(MOTHER_DIR / "母本_修缮后.csv", encoding="utf-8-sig"))}
    return [(r["id"], r["text"], clean[r["id"]]) for r in orig if r["keep"] == "1" and r["drop_reason"] != "老师删除"]


def _voice(tmp_path, texts, ids):
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, VOICE).ensure()
    project.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for i, t in zip(ids, texts)])
    return cfg, project


def _shown(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return rec, str(review.current_values(rec, review.load_draft(project).get(rid))["text"] or "")


def _auto_check(project, cfg, heard=None):
    """🔍 自动查找：第二个识别引擎（假的 FunASR）听到的是 heard[id]（没给的听到的和现在的文字一样）。"""
    from voicetwin.data import proofcheck as pc

    heard = heard or {}

    class FakeRunner(pc._EngineRunner):
        def recognize(self, rec, lang):
            return heard.get(rec["id"], rec["text"]), None, pc.ENGINE_FUNASR

    with um.patch.object(pc, "_EngineRunner", FakeRunner):
        return pc.find_suspects(project, cfg)


def _same(a, b):
    return clean_transcript(a) == clean_transcript(b)


def _comma_cut(t, c):
    """在识别文字和修缮好的文字都没改过的逗号处一起切开（两边都至少 6 个字）。"""
    for tag, i1, i2, j1, _j2 in difflib.SequenceMatcher(None, t, c, autojunk=False).get_opcodes():
        if tag != "equal":
            continue
        for p in range(i1, i2):
            if t[p] in "，," and p >= 6 and len(t) - p - 1 >= 6:
                q = j1 + (p - i1)
                return (t[:p + 1], t[p + 1:]), (c[:q + 1], c[q + 1:])
    return None


# ---------------------------------------------------------------------------- 一键校正：按内容找，不按 id
@need_both
def test_changed_ids_still_follow_the_master(tmp_path):
    """片段 id 全变了（重新准备素材、视频挪了地方、升级以后新建了声音）：以前按 id 的逐句修缮记录全都用不上，
    123 句里 33 句没改、7 句改成别的样子。现在和母本不一样的句子全部改得和母本一模一样，对的句子一个字都不动。"""
    rows = _teacher_rows()
    diff = [(i, t, c) for i, t, c in rows if t != c]
    same = [(i, t, c) for i, t, c in rows if t == c][::9]
    data = diff + same
    ids = [f"0099_b0b0b0_{k:04d}" for k in range(len(data))]
    cfg, project = _voice(tmp_path, [t for _i, t, _c in data], ids)
    res = wf.run_transcript_fix(cfg, VOICE, once=True)
    wrong = []
    for nid, (_i, t, c) in zip(ids, data):
        cur = _shown(project, nid)[1]
        if not _same(cur, c):
            wrong.append((t, cur, c))
    assert not wrong, wrong[:5]
    assert len(diff) == 123 and res["mother_rows"] == len(data)


@need_both
def test_different_clip_boundaries_still_follow_the_master(tmp_path):
    """切的位置也不一样（两句合成一句、长句子在逗号处切成两句）：按内容在母本这一整串话里找，合成的、切开的都改对。"""
    rows = _teacher_rows()
    texts, truth = [], []
    k = 0
    while k < len(rows) - 1 and len(texts) < 120:
        (i1, t1, c1), (i2, t2, c2) = rows[k], rows[k + 1]
        if (t1 != c1 or t2 != c2) and i1.split("_")[1] == i2.split("_")[1] and len(t1) + len(t2) <= 120:
            texts.append(t1 + t2)  # 同一个视频里相邻的两句合成一句
            truth.append(c1 + c2)
            k += 2
            continue
        cut = _comma_cut(t1, c1) if t1 != c1 else None
        if cut:
            (ta, tb), (ca, cb) = cut
            texts += [ta, tb]
            truth += [ca, cb]
        k += 1
    ids = [f"0100_c0ffee_{n:04d}" for n in range(len(texts))]
    cfg, project = _voice(tmp_path, texts, ids)
    wf.run_transcript_fix(cfg, VOICE, once=True)
    wrong = [(t, _shown(project, nid)[1], c) for nid, t, c in zip(ids, texts, truth)
             if not _same(_shown(project, nid)[1], c)]
    assert len(texts) >= 60 and not wrong, wrong[:5]


@need_both
def test_split_piece_is_not_padded_with_the_rest_of_the_master_sentence():
    """一句被切成了两句：前半句只按母本里对应的那一段改，不把母本后半句的话补进来（录音里没有）。"""
    ref = tf.Reference(list(tf.builtin_mother()))
    t = "首先，as这个关系代词，它最经常出现在非限定性定于从句中，"  # 母本里这一句后面还有半句
    fixes, covered, _snip, full = tf._mother_first(t, "新的编号", ref, (t,))
    assert full and [(t[f.start:f.end], f.rep) for f in fixes] == [("于", "语")]


# ---------------------------------------------------------------------------- 自动查错字：每一句先和母本对照
@need_both
def test_auto_suggestion_that_contradicts_the_master_is_dropped(tmp_path):
    """另一个识别引擎把对的「定语」听成「定于」：以前「修改建议」里一直有「定语 → 定于」（老师点的是同一批讲课，
    母本里就是「定语」）。现在母本里有这一句，和母本矛盾的建议不要，也不标红。"""
    rows = _teacher_rows()
    rid, t, _c = next((i, t, c) for i, t, c in rows if t == c and "定语从句" in t and len(t) > 20)
    cfg, project = _voice(tmp_path, [t], ["0099_x_0001"])
    _auto_check(project, cfg, {"0099_x_0001": t.replace("定语", "定于", 1)})
    rec, cur = _shown(project, "0099_x_0001")
    info = review.analyze(rec, cur)
    assert not info["edits"] and not info["red"]
    wf.run_transcript_fix(cfg, VOICE, once=True)
    rec, cur = _shown(project, "0099_x_0001")
    info = review.analyze(rec, cur)
    assert cur == t and not info["edits"] and not info["red"]


@need_both
def test_auto_check_before_one_click_already_suggests_the_master_wording(tmp_path):
    """准备素材以后的自动查错字（还没点一键校正）：以前建议只来自另一个识别引擎，不看母本——两个引擎都听成「定于」时
    什么都不提示。现在每一句都先和母本对照：和母本不一样的句子，「修改建议」就是母本的写法，写着「按母本」，
    点一下「采用」就和母本一模一样；自动查错字一个字都不直接改。"""
    rows = _teacher_rows()
    diff = [(i, t, c) for i, t, c in rows if t != c][:40]
    ids = [f"0099_y_{k:04d}" for k in range(len(diff))]
    cfg, project = _voice(tmp_path, [t for _i, t, _c in diff], ids)
    _auto_check(project, cfg)
    assert review.load_draft(project) == {}  # 自动查错字不直接改字
    for nid, (_i, t, c) in zip(ids, diff):
        rec, cur = _shown(project, nid)
        info = review.analyze(rec, cur)
        assert cur == t and info["edits"], t
        assert _same(review.apply_edits(cur, info["edits"]), c), (t, c)
        assert any(str(x).startswith("按母本：") for x in info["reasons"]), info["reasons"]
    review.adopt_suggestion(project, ids[0])
    assert _same(_shown(project, ids[0])[1], diff[0][2])


@need_both
def test_suggestion_cell_says_by_the_master(tmp_path):
    """「修改建议」那一列：按母本的建议写成「按母本：……」。"""
    pytest.importorskip("gradio")
    from voicetwin.webui.app import _suggest_cell

    t = "接下来我们就学习一下另外一个关系代词，as,这个关系代词相对来说比较特殊。".replace("关系代词", "关系带词", 1)
    cfg, project = _voice(tmp_path, [t], ["0099_z_0001"])
    _auto_check(project, cfg)
    rec, cur = _shown(project, "0099_z_0001")
    html = _suggest_cell(review.analyze(rec, cur))
    assert "按母本：" in html and "关系带词 → 关系代词" in html


# ---------------------------------------------------------------------------- 不该改的不改
@need_both
def test_new_content_is_never_forced_to_the_master(tmp_path):
    """母本里没有的新内容：一个字都不按母本改（不硬对）。"""
    texts = ["今天我们来学习一下名词性从句里面的主语从句。", "宾语从句一定要用陈述句的语序，不能用疑问句的语序。",
             "第二题考的是 whether 和 if 的区别，大家注意一下。", "与现在事实相反的虚拟语气，从句要用一般过去时。",
             "拿到长难句以后，第一步是先找到句子的谓语动词。", "好，今天的课就上到这里，同学们再见。"]
    ids = [f"new_{k}" for k in range(len(texts))]
    cfg, project = _voice(tmp_path, texts, ids)
    _auto_check(project, cfg)
    res = wf.run_transcript_fix(cfg, VOICE, once=True)
    assert res["mother_rows"] == 0 and review.load_draft(project) == {}
    for nid in ids:
        rec, cur = _shown(project, nid)
        assert not any("按母本" in str(x) for x in review.analyze(rec, cur)["reasons"])


@need_both
def test_teacher_edits_are_never_overwritten_and_get_a_note(tmp_path):
    """老师自己改过的字和母本不一样：不动（老师的修改为准），点那一行时看到一句说明；同一句里别的错照样按母本改。"""
    rows = _teacher_rows()
    rid, t, c = next((i, t, c) for i, t, c in rows if t.count("借词") == 1 and t != c and c.count("介词") == 1
                     and len(review._change_items(t, c)) == 1)
    typed = t.replace("借词", "介绍词")  # 老师自己打的（录音里也许是别的说法）
    extra = typed.replace("的", "得", 1) if "的" in typed else typed  # 再放一个识别错：按母本改回「的」
    cfg, project = _voice(tmp_path, [extra], ["0099_t_0001"])
    review.set_draft(project, "0099_t_0001", text=extra)
    recs = project.load_manifest()
    recs[0]["orig_text"] = t.replace("的", "得", 1) if "的" in typed else t  # 最初识别的文字（老师改以前）
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, VOICE, once=True)
    rec, cur = _shown(project, "0099_t_0001")
    assert "介绍词" in cur  # 老师打的字没动
    if extra != typed:
        assert cur == clean_transcript(typed)  # 别的识别错照样按母本改
    note = rec.get("mother_note") or {}
    assert note.get("text") == extra and any("介绍词" in x and "介词" in x for x in note.get("notes", []))
    pytest.importorskip("gradio")
    from voicetwin.webui.app import _mother_note_html

    assert "介绍词" in _mother_note_html(rec, extra) and _mother_note_html(rec, cur + "改过") == ""


@need_both
def test_master_fix_the_teacher_undid_is_not_redone(tmp_path):
    """老师点红色按钮撤销了按母本的改法：再点一键校正、再自动查错字都不改回来（老师的决定为准），说明里写着撤销过。"""
    rows = _teacher_rows()
    rid, t, c = next((i, t, c) for i, t, c in rows if "关系带词" in t)
    cfg, project = _voice(tmp_path, [t], ["0099_u_0001"])
    wf.run_transcript_fix(cfg, VOICE)
    assert _same(_shown(project, "0099_u_0001")[1], c)
    review.unadopt_suggestion(project, "0099_u_0001")
    assert _shown(project, "0099_u_0001")[1] == t
    wf.run_transcript_fix(cfg, VOICE)
    _auto_check(project, cfg)
    rec, cur = _shown(project, "0099_u_0001")
    assert cur == t and not review.analyze(rec, cur)["edits"]
    assert any("撤销过" in x for x in (rec.get("mother_note") or {}).get("notes", []))


@need_both
def test_deleted_rows_are_skipped(tmp_path):
    rows = _teacher_rows()
    rid, t, c = next((i, t, c) for i, t, c in rows if t != c)
    cfg, project = _voice(tmp_path, [t, t], ["0099_d_0001", "0099_d_0002"])
    review.delete_clip(project, "0099_d_0001")
    wf.run_transcript_fix(cfg, VOICE, once=True)
    assert _shown(project, "0099_d_0001")[1] == t and _same(_shown(project, "0099_d_0002")[1], c)


@need_both
def test_uploaded_master_with_a_typo_does_not_override_correct_text(tmp_path):
    """老师上传的讲稿也是母本，但没修缮过（拼音输入法打的「主雨」）：读音一样的一个字只给没把握的建议，
    不把表格里对的「主语」改成错字。"""
    t = "这个句子的主语是我们刚才讲过的那个名词短语。"
    cfg, project = _voice(tmp_path, [t], ["up_0001"])
    up = tmp_path / "讲稿.txt"
    up.write_text("这个句子的主雨是我们刚才讲过的那个名词短语。\n", encoding="utf-8")
    res = wf.run_transcript_fix(cfg, VOICE, files=[str(up)])
    assert _shown(project, "up_0001")[1] == t and res["adopted"]["changes"] == 0


@need_both
def test_uploaded_lecture_script_does_not_overwrite_what_was_said(tmp_path):
    """老师上传的讲稿（讲课以前写的）：讲的时候换的说法（多说的「我们」、不一样的页码）不按讲稿改——上传的文字不是
    「说了算」的母本，只有读音像识别错的地方（瑞森 → reason）才按它改。实测见 research/文字校正/母本优先/讲稿实测.py。"""
    said = ["请大家翻到课本第三十六页，看第二大题。", "那如果我们用一个句子来修饰名词，这个句子就叫做定语从句。",
            "第一小题，空格前面的先行词是 the 瑞森。"]
    ids = ["k1", "k2", "k3"]
    cfg, project = _voice(tmp_path, said, ids)
    up = tmp_path / "讲稿.txt"
    up.write_text("请大家翻到课本第三十五页，看第二大题。\n那如果用一个句子来修饰名词，这个句子就叫做定语从句。\n"
                  "第一小题，空格前面的先行词是 the reason。\n", encoding="utf-8")
    wf.run_transcript_fix(cfg, VOICE, files=[str(up)])
    assert _shown(project, "k1")[1] == said[0] and _shown(project, "k2")[1] == said[1]
    assert "the reason" in _shown(project, "k3")[1]


def test_mother_first_without_any_master_does_nothing():
    """没有母本（读不到）时一点都不出错。"""
    assert tf._mother_first("定于从句", "x", None, ("定于从句",)) == ([], [], "", False)
