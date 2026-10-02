"""v18.5 文字校正：母本标准库（老师修缮过的母本 + 语法术语 + 对照表）、上传母本、直接改 / 建议、下载改好的文字。

读音相近要用 pypinyin、判断完整的词要用 jieba（GPT-SoVITS 整合包里都有）；没装时相关的测试跳过，
另有测试检查没有 jieba 时更保守（只给建议、不乱改）。"""

import csv
import importlib.util
from pathlib import Path

import pytest

from conftest import confirm_material, make_cfg
from voicetwin import workflows as wf
from voicetwin.data import lexicon_fix as lf
from voicetwin.data import review
from voicetwin.data import transcript_fix as tf

HAS_PINYIN = importlib.util.find_spec("pypinyin") is not None
HAS_JIEBA = importlib.util.find_spec("jieba") is not None or importlib.util.find_spec("jieba_fast") is not None
need_pinyin = pytest.mark.skipif(not HAS_PINYIN, reason="没有装 pypinyin（整合包里有）")
need_both = pytest.mark.skipif(not (HAS_PINYIN and HAS_JIEBA), reason="没有装 pypinyin / jieba（整合包里有）")
ROOT = Path(__file__).resolve().parents[1]
MOTHER_DIR = ROOT / "research" / "文字校正" / "老师的母本"

REF = """同学们好，今天我们来讲定语从句。定语从句是用来修饰名词的句子。被修饰的名词叫做先行词。
我们先来看 as 引导的定语从句。as 引导的定语从句可以放在句首，也可以放在句末。
比如 As we all know, the earth is round. 这里的 as 指代的是后面整个句子。
好，我们来做一下练习。请大家翻到第三十五页。
关系代词 that 和 which 的区别是什么呢？我们来总结一下。"""


# ---------------------------------------------------------------------------- 读文件、母本格式
def test_read_text_file_encodings(tmp_path):
    s = "定语从句 which 引导"
    for name, data in (("a.txt", s.encode("utf-8")), ("b.txt", b"\xef\xbb\xbf" + s.encode("utf-8")),
                       ("c.txt", s.encode("utf-16")), ("d.txt", s.encode("gbk")),
                       ("e.txt", s.encode("utf-16-le"))):
        (tmp_path / name).write_bytes(data)
        assert tf.read_text_file(tmp_path / name) == s, name


def test_parse_mother_csv_skips_deleted_rows_and_keeps_ids():
    text = ("﻿id,keep,split,lang,duration,text,drop_reason,audio\n"
            "a1,1,train,zh,5,第一句  定语从句,,x.wav\n"
            "a2,0,train,zh,5,删掉的那句,老师删除,x.wav\n"
            "a3,0,train,zh,1,太短的,太短,x.wav\n")
    assert tf.parse_mother("transcripts.csv", text) == [("a1", "第一句 定语从句"), ("a3", "太短的")]
    assert tf.parse_mother("x.tsv", "# 说明\nb1\t文字一\n\n文字二\n") == [("b1", "文字一"), ("", "文字二")]
    assert tf.parse_mother("x.txt", "第一行\n\n 第二行 \n") == [("", "第一行"), ("", "第二行")]


def test_save_and_load_transcripts(tmp_path):
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "母本声音").ensure()
    a = tmp_path / "讲稿.txt"
    a.write_text("这是一份讲稿，讲定语从句和先行词。", encoding="utf-8")
    b = tmp_path / "transcripts.csv"
    b.write_text("id,text,drop_reason\nx1,第二份的文字很多很多字,\n", encoding="utf-8")
    info = tf.save_transcripts(project, [str(a), str(b)])
    assert info["files"] == ["transcripts.csv", "讲稿.txt"] and info["chars"] > 10
    lines, names = tf.load_transcripts(project)
    assert ("x1", "第二份的文字很多很多字") in lines and names == info["files"]
    bad = tmp_path / "a.docx"
    bad.write_bytes(b"PK")
    with pytest.raises(ValueError, match="不是 txt 或 csv"):
        tf.save_transcripts(project, [str(bad)])
    assert tf.load_transcripts(project)[1] == info["files"]  # 出错时一个都不存，原来的还在


def test_builtin_standard_library_is_shipped():
    assert len(tf.builtin_mother()) > 900  # 老师修缮过的母本
    assert sum(len(v) for v in tf.builtin_fixes().values()) == 138
    info = lf.builtin_info()
    assert info["terms"] > 300 and info["corrections"] > 30
    terms = set(lf.builtin_terms())
    for w in ("及物动词", "不及物动词", "谓语", "宾语", "表语", "名词性从句", "状语从句", "形容词", "形容词词性",
              "虚拟从句", "定语从句", "先行词", "关系代词", "介词"):
        assert w in terms, w
    corr = lf.builtin_corrections()
    assert corr["借词"] == "介词" and corr["艾子"] == "as" and corr["关系带词"] == "关系代词"


def test_english_sound_codes():
    assert tf.en_code("there") == tf.en_code("their")
    assert tf.en_code("know") == tf.en_code("no")
    assert tf.en_code("write") == tf.en_code("right")
    assert tf.en_code("clause") == tf.en_code("clouse")
    assert tf.en_code("as") != tf.en_code("is")


@need_pinyin
def test_sounds_like_english():
    assert tf.sounds_like_english(["ai4", "zi3"], ["as"])
    assert tf.sounds_like_english(["pai4", "sen1"], ["python"])
    assert tf.sounds_like_english(["de5"], ["the"])
    assert not tf.sounds_like_english(["ju4", "zi5"], ["sentence"])


# ---------------------------------------------------------------------------- 和母本对齐
@need_pinyin
@pytest.mark.parametrize("text,wrong,right", [
    ("今天我们来讲定于从句", "于", "语"),
    ("我们先来看艾子引导的定语从句", "艾子", "as"),
    ("被修饰的名词叫做先行次", "次", "词"),
    ("好我们来做一下联系", "联系", "练习"),
    ("关系代词 that 和 witch 的区别是什么呢", "witch", "which"),
    ("比如 as we all no the earth is round", "no", "know"),
])
def test_check_text_finds_misrecognized_words(text, wrong, right):
    res = tf.check_text(text, tf.Reference(REF))
    toks = tf.tokens(text)
    got = [(text[toks[p.i1].start:toks[p.i2 - 1].end], p.rep) for p in res.props]
    assert (wrong, right) in got, got


@need_pinyin
@pytest.mark.parametrize("text", [
    "请大家翻到第四十五页",  # 页码不一样：老师当时就是这么说的
    "他们都可以引导非限制性定语从句",
    "下课以后记得复习今天的内容",
    "我们来联系一下家长",
    "她们都可以引导非限制性定语从句",  # 他/她：写法习惯，不算错
])
def test_check_text_leaves_different_wording_alone(text):
    assert tf.check_text(text, tf.Reference(REF)).props == []


@need_pinyin
def test_check_text_skips_its_own_line():
    lines = [("r1", "被修饰的名词叫做先行次"), ("r2", "今天我们讲状语从句")]
    ref = tf.Reference(lines)
    assert ref.id_range["r1"][0] == 0
    res = tf.check_text("被修饰的名词叫做先行次", ref, exclude_id="r1")
    assert res.props == [] and not res.aligned  # 只有它自己能对上：不拿自己证明自己没错


# ---------------------------------------------------------------------------- 标准库
@need_both
@pytest.mark.parametrize("text,wrong,right,direct", [
    ("关系代词that不能和借词一起提前到定语从句的句首。", "借词", "介词", True),
    ("我们先来学习一下关系带词that的使用方法。", "关系带词", "关系代词", True),
    ("一起被提前到定语从剧最前端的时候，", "定语从剧", "定语从句", True),
    ("做主语和位语的都是同一个对象", "位语", "谓语", True),
    ("这是一个不纠动词。", "不纠动词", "不及物动词", True),
    ("无法进行同类向的合并。", "同类向", "同类项", True),
])
def test_lexicon_fixes(text, wrong, right, direct):
    lex = lf.Lexicon.build([x for _, x in tf.builtin_mother()])
    fixes = lex.find(text)
    fixed = tf._apply(text, [(f.start, f.end, f.rep) for f in fixes if f.direct == direct])
    assert right in fixed and wrong not in fixed, [(text[f.start:f.end], f.rep, f.direct) for f in fixes]


@need_both
@pytest.mark.parametrize("text", [
    "凭借词汇量取胜",  # 「借词」只是两个词挨着
    "因为which也可以和介词一起提前到定语从句的句首。",  # 「介词一起」里没有「词义」
    "名词性从句能做主语、宾语、表语和同位语。",  # 同位语里的「位语」
    "那这个定语从句的原型就是that person's son is a famous writer。",  # 老师一直说「原型」
    "时间比较急，我们先讲到这里。",  # 「比较急」不是「比较级」
    "我们会发现，定语从句的引导词，whose",
    "从具体的例子来看",
])
def test_lexicon_leaves_correct_text_alone(text):
    lex = lf.Lexicon.build([x for _, x in tf.builtin_mother()])
    assert [f for f in lex.find(text) if f.direct] == [], [(text[f.start:f.end], f.rep) for f in lex.find(text)]


def test_lexicon_without_jieba_is_conservative(monkeypatch):
    monkeypatch.setattr(lf, "_tokenizer", lambda: None)
    lex = lf.Lexicon.build(["关系代词和介词", "定语从句"])
    fixes = lex.find("不能和借词一起提前；表语和同位语")
    assert [(f.rep, f.direct) for f in fixes if f.direct] == [("介词", True)]  # 对照表照样改；同位语里的「位语」不动
    assert all(not f.direct for f in fixes if f.kind in ("term", "habit"))  # 读音找到的只给建议


@need_pinyin
def test_learn_from_teacher_edits():
    recs = [{"orig_text": "我们来看艾子引导的从句", "text": "我们来看as引导的从句"},
            {"orig_text": "这个关系带词很重要", "text": "这个关系代词很重要"},
            {"orig_text": "他说的话", "text": "她说的话"},  # 写法习惯，不学
            {"orig_text": "我们再看", "text": "我们在看"},  # 单个字，不学
            {"orig_text": "整句改掉了", "text": "完全不一样的说法", "deleted": True}]
    learned = lf.learn_from_edits(recs)
    assert learned == {"艾子": "as", "带词": "代词"}


# ---------------------------------------------------------------------------- 整个声音
def _voice(tmp_path, texts, ids=None):
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "校正声音").ensure()
    ids = ids or [f"c{i:03d}" for i in range(len(texts))]
    project.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for i, t in zip(ids, texts)])
    return cfg, project


@need_both
def test_check_with_transcript_fixes_directly_as_unsaved_edits(tmp_path):
    texts = ["关系代词that不能和借词一起提前到定语从句的句首。", "这个句子完全没有错。",
             "我们先来看艾子引导的定语从句。", "凭借词汇量取胜"]
    cfg, project = _voice(tmp_path, texts)
    recs = project.load_manifest()
    recs[1]["suspect"] = {"spans": [[0, 2]], "alt": "", "reasons": ["测试用的自动检查结果"], "score": 0.6}
    project.save_manifest(recs)
    res = tf.check_with_transcript(project)
    assert res["fixes"] >= 2 and res["fixed_rows"] == 2
    draft = review.load_draft(project)
    assert draft["c000"]["text"] == "关系代词that不能和介词一起提前到定语从句的句首。"
    assert draft["c002"]["text"].startswith("我们先来看as")
    assert "c003" not in draft and "c001" not in draft
    recs = {r["id"]: r for r in project.load_manifest()}
    sus = recs["c000"]["suspect"]
    assert sus["src"] == "transcript" and sus["text"] == texts[0]
    assert any(x.startswith("已按标准库改好：「借词」应该是「介词」") for x in sus["reasons"])
    info = review.analyze(recs["c000"], draft["c000"]["text"])
    assert info["adopted"] and not info["edits"]  # 「修改建议」是红色的「已采用」，可以撤销
    assert recs["c000"]["text"] == texts[0]  # 只是草稿：老师点「保存修改」才写进校对表
    assert recs["c001"]["suspect"]["reasons"] == ["测试用的自动检查结果"]  # 母本里对不上：保留自动检查的
    assert review.unsaved_count(project) == 2  # 没保存不能训练
    review.unadopt_suggestion(project, "c000")
    assert review.load_draft(project).get("c000") is None  # 撤销以后和保存的一样，草稿去掉


@need_both
def test_check_with_transcript_respects_dismissed_and_deleted_rows(tmp_path):
    texts = ["不能和借词一起提前", "也不能和借词一起提前", "还是不能和借词一起提前"]
    cfg, project = _voice(tmp_path, texts)
    recs = project.load_manifest()
    recs[0]["suspect_ok"] = texts[0]  # 老师点过「这句没错」
    recs[1]["deleted"] = True
    recs[1]["keep"] = False
    project.save_manifest(recs)
    res = tf.check_with_transcript(project)
    assert res["dismissed"] == 1 and res["checked"] == 1
    assert set(review.load_draft(project)) == {"c002"}


def test_teacher_rows_are_fixed_exactly_like_the_manual_review(tmp_path):
    """老师现在这个声音的句子（母本原文）点一次「文字校正」：需要改的句子改得和逐句修缮的一模一样，别的句子不动。"""
    orig = list(csv.DictReader(open(MOTHER_DIR / "母本_原文.csv", encoding="utf-8-sig")))
    clean = list(csv.DictReader(open(MOTHER_DIR / "母本_修缮后.csv", encoding="utf-8-sig")))
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "老师").ensure()
    project.save_manifest([{"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh",
                            "duration": 3.0, "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
                            "split": "train"} for r in orig])
    res = tf.check_with_transcript(project)
    draft = review.load_draft(project)
    need = {o["id"] for o, c in zip(orig, clean) if o["text"] != c["text"] and o["drop_reason"] != "老师删除"}
    assert set(draft) == need and len(need) == 123
    for o, c in zip(orig, clean):
        if o["id"] in draft:
            assert draft[o["id"]]["text"] == c["text"], o["id"]
    assert res["fixes"] >= 138


@need_both
def test_uploaded_transcripts_csv_with_same_ids(tmp_path):
    cfg, project = _voice(tmp_path, ["这个是识别错的句子，关系代词dead", "另一句"], ids=["u1", "u2"])
    res = tf.check_with_transcript(project, lines=[("u1", "这个是识别错的句子，关系代词that")], use_builtin=False)
    assert review.load_draft(project)["u1"]["text"].endswith("关系代词that") and res["fixed_rows"] == 1


@need_both
def test_second_run_uses_the_original_auto_result(tmp_path):
    cfg, project = _voice(tmp_path, ["不能和借词一起提前到句首"])
    recs = project.load_manifest()
    auto = {"spans": [[0, 2]], "alt": "", "reasons": ["自动的"], "score": 0.6}
    recs[0]["suspect"] = auto
    project.save_manifest(recs)
    tf.check_with_transcript(project)
    r = project.load_manifest()[0]
    assert r["suspect_auto"] == auto and r["suspect"]["src"] == "transcript"
    review.discard_draft(project)
    tf.check_with_transcript(project)
    r = project.load_manifest()[0]
    assert r["suspect_auto"] == auto  # 不会把上次文字校正的结果当成自动检查的


# ---------------------------------------------------------------------------- 下载改好的文字
def test_export_text(tmp_path):
    cfg, project = _voice(tmp_path, ["第一句改好了", "第二句删掉了", "", "第四句"])
    recs = project.load_manifest()
    recs[1]["deleted"] = True
    project.save_manifest(recs)
    review.set_draft(project, "c003", text="第四句改了还没保存")
    res = review.export_text(project)
    raw = Path(res["path"]).read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") and b"\r\n" in raw
    lines = raw.decode("utf-8-sig").splitlines()
    assert lines == ["第一句改好了", "第四句改了还没保存"]
    assert res["lines"] == 2 and res["unsaved"] == 1 and res["deleted"] == 1
    assert Path(res["path"]).parent.name == review.EXPORT_DIR and "校正声音" in Path(res["path"]).name
    # 下载的文件可以直接当母本上传
    assert tf.parse_mother(Path(res["path"]).name, tf.read_text_file(res["path"]))[0] == ("", "第一句改好了")


def test_export_text_without_text_says_why(tmp_path):
    cfg, project = _voice(tmp_path, ["", ""])
    with pytest.raises(ValueError, match="还没有文字"):
        review.export_text(project)


def test_workflow_helpers(tmp_path):
    cfg, project = _voice(tmp_path, ["第一句"])
    assert wf.transcript_info(cfg, "没有这个声音") == {"files": [], "chars": 0}
    assert wf.transcript_info(cfg, "校正声音")["files"] == []
    assert wf.export_review_text(cfg, "校正声音")["lines"] == 1
    assert [n for _, n in wf.task_stages("textfix")] == ["读母本和语法术语", "一句一句检查"]


# ---------------------------------------------------------------------------- 一键全部文字校正
def test_adopt_all_suggestions(tmp_path):
    cfg, project = _voice(tmp_path, ["我们先来看艾子引导的从句", "这里可能有错但是没有建议", "没有标红的句子"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[5, 7]], "alt": "我们先来看as引导的从句", "reasons": ["自动的"], "score": 0.7}
    recs[1]["suspect"] = {"spans": [[2, 4]], "alt": "", "reasons": ["自动的"], "score": 0.6}
    project.save_manifest(recs)
    res = review.adopt_all_suggestions(project)
    assert res["rows"] == 1 and res["changes"] == 1 and res["no_suggestion"] == 1
    draft = review.load_draft(project)
    assert draft["c000"]["text"] == "我们先来看as引导的从句" and set(draft) == {"c000"}
    rec = project.load_manifest()[0]
    info = review.analyze(rec, draft["c000"]["text"])
    assert info["adopted"] and info["blue"]  # 改过的地方是蓝色，「修改建议」按钮变红（可以撤销）
    assert review.adopt_all_suggestions(project)["rows"] == 0  # 再点一次：没有可以采用的了


@need_both
def test_one_click_full_correction_then_save_and_confirm(tmp_path):
    """老师的流程：一键全部文字校正 → 🔴 没保存（不能训练）→ 保存修改 → 确认训练素材 → 训练用的是改好的字。"""
    cfg, project = _voice(tmp_path, ["关系代词不能和借词一起提前", "我们先来看艾子引导的从句", "第三句"])
    recs = project.load_manifest()
    recs[2]["suspect"] = {"spans": [[0, 1]], "alt": "第3句", "reasons": ["自动的"], "score": 0.6}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert res["fixes"] >= 2 and "adopted" in res
    assert wf.training_blocker_for(cfg, "校正声音")  # 有没保存的修改：不能训练
    review.save_rows(project)
    texts = {r["id"]: r["text"] for r in project.load_manifest()}
    assert texts["c000"] == "关系代词不能和介词一起提前" and texts["c001"].startswith("我们先来看as")
    assert wf.training_blocker_for(cfg, "校正声音")  # 保存了，但还没确认训练素材
    confirm_material(cfg, "校正声音")
    assert not wf.training_blocker_for(cfg, "校正声音")
    from voicetwin.data.exporters import gptsovits_list_text

    listing = gptsovits_list_text(wf.Project(cfg, "校正声音"), "校正声音")
    assert "介词" in listing and "借词" not in listing and "艾子" not in listing
