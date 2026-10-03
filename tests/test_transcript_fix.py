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
    # 整理成和校对表一样的写法（clean_transcript：中文中间的空格去掉）
    assert tf.parse_mother("transcripts.csv", text) == [("a1", "第一句定语从句"), ("a3", "太短的")]
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
    assert ref.id_ranges["r1"] == [(0, 11)]
    res = tf.check_text("被修饰的名词叫做先行次", ref, exclude_id="r1")
    assert res.props == [] and not res.aligned  # 只有它自己能对上：不拿自己证明自己没错


@need_pinyin
def test_same_id_twice_skips_both_copies_but_not_the_lines_between():
    """程序自带的母本和老师上传的 transcripts.csv 里有同一个 id：两处都跳过，中间别的句子照常拿来比
    （以前只记一个从第一处到最后一处的范围，把中间所有的句子都跳过了）。"""
    lines = [("r1", "被修饰的名词叫做先行次"), ("r2", "我们先来看艾子引导的定语从句"), ("r3", "今天我们讲状语从句"),
             ("r1", "被修饰的名词叫做先行次")]
    ref = tf.Reference(lines)
    assert len(ref.id_ranges["r1"]) == 2 and ref.id_ranges["r2"] == [(11, 25)]
    res = tf.check_text("被修饰的名词叫做先行次", ref, exclude_id="r1")
    assert res.props == [] and not res.aligned
    ref2 = tf.Reference([("r1", "我们先来看as引导的定语从句"), ("r2", "今天我们讲状语从句"), ("r1", "这一句完全不一样了")])
    res2 = tf.check_text("我们先来看艾子引导的定语从句", ref2, exclude_id="x")
    assert [p.rep for p in res2.props] == ["as"]


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
    # 判断不了是不是一个完整的词（「凭借词汇」）：对照表也只给没把握的建议（一键校正不自动采用）；同位语里的「位语」不动
    assert [(f.rep, f.direct, f.weight < tf.SURE_WEIGHT) for f in fixes] == [("介词", False, True)]
    assert lex.find("凭借词汇量取胜") and all(not f.direct for f in lex.find("凭借词汇量取胜"))


@need_pinyin
def test_learn_from_teacher_edits():
    recs = [{"orig_text": "我们来看艾子引导的从句", "text": "我们来看as引导的从句"},
            {"orig_text": "这个关系带词很重要", "text": "这个关系代词很重要"},
            {"orig_text": "他说的话", "text": "她说的话"},  # 写法习惯，不学
            {"orig_text": "我们再看", "text": "我们在看"},  # 单个字，不学
            {"orig_text": "整句改掉了", "text": "完全不一样的说法", "deleted": True}]
    learned = lf.learn_from_edits(recs)
    assert learned == {"艾子": "as", "带词": "代词"}
    # 用的时候再筛：母本里出现过的、常用词不学
    lex = lf.Lexicon.build(["我们来看这个位置"], learned={"艾子": "as", "位置": "which", "按照": "and"})
    assert "艾子" in lex.learned and "位置" not in lex.learned
    if HAS_JIEBA:
        assert "按照" not in lex.learned


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
    # 老师看过、点了「保存修改」以后再点一次：什么都不应该再改（以前出过错：从保存的修改里学到「位置 → which」「按照 → and」，
    # 别的句子里正常的「位置」「按照」也被改掉了）
    review.save_rows(project)
    res2 = tf.check_with_transcript(project)
    assert review.load_draft(project) == {} and res2["fixes"] == 0, list(review.load_draft(project).items())[:3]


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
    pinned = dict(auto, text="不能和借词一起提前到句首")  # 记下是按哪段文字算的（保存修改以后位置才换算得对）
    assert r["suspect_auto"] == pinned and r["suspect"]["src"] == "transcript"
    review.discard_draft(project)
    tf.check_with_transcript(project)
    r = project.load_manifest()[0]
    assert r["suspect_auto"] == pinned  # 不会把上次文字校正的结果当成自动检查的


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
    texts = ["我们先来看艾子引导的从句", "这里可能有错但是没有建议", "没有标红的句子", "周末我们一起去公园散步",
             "小明昨天说接词后面接名词", "不当训练素材的艾子"]
    cfg, project = _voice(tmp_path, texts)
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[5, 7]], "alt": "我们先来看as引导的从句", "reasons": ["文字校正的"], "score": 0.7,
                          "text": texts[0], "src": "transcript"}
    recs[1]["suspect"] = {"spans": [[2, 4]], "alt": "", "reasons": ["自动的"], "score": 0.6}
    # 自动查错字原来的建议（没经过文字校正）：不知道对不对，一键不自动采用
    recs[3]["suspect"] = {"spans": [[0, 2]], "alt": "周日我们一起去公园散步", "reasons": ["自动的"], "score": 0.6}
    # 文字校正标了「没把握」的建议：也不自动采用
    recs[4]["suspect"] = {"spans": [[5, 7]], "alt": "小明昨天说介词后面接名词", "reasons": ["没把握"], "score": 0.6,
                          "text": texts[4], "src": "transcript", "sure_alt": texts[4]}
    recs[5]["keep"] = False  # 不当训练素材的行不动
    recs[5]["suspect"] = {"spans": [[7, 9]], "alt": "不当训练素材的as", "reasons": ["文字校正的"], "score": 0.7,
                          "text": texts[5], "src": "transcript"}
    project.save_manifest(recs)
    res = review.adopt_all_suggestions(project)
    assert (res["rows"], res["changes"], res["no_suggestion"], res["unsure"]) == (1, 1, 1, 2), res
    draft = review.load_draft(project)
    assert draft["c000"]["text"] == "我们先来看as引导的从句" and set(draft) == {"c000"}
    rec = project.load_manifest()[0]
    info = review.analyze(rec, draft["c000"]["text"])
    assert info["adopted"] and info["blue"]  # 改过的地方是蓝色，「修改建议」按钮变红（可以撤销）
    assert review.adopt_all_suggestions(project)["rows"] == 0  # 再点一次：没有可以采用的了
    # 没把握的照样可以一行一行采用
    review.adopt_suggestion(project, "c004")
    assert review.load_draft(project)["c004"]["text"] == "小明昨天说介词后面接名词"


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


# ---------------------------------------------------------------------------- 发布前检查发现的问题（每个都有一个测试）
def _cur(project, rid):
    rec = {r["id"]: r for r in project.load_manifest()}[rid]
    return rec, review.current_values(rec, review.load_draft(project).get(rid))["text"]


@need_both
@pytest.mark.parametrize("text,span,alt,fixed", [
    ("小明昨天说借词后面接名词", [5, 7], "小明昨天说接词后面接名词", "小明昨天说介词后面接名词"),
    ("周末我们看艾子去公园散步", [5, 7], "周末我们看爱子去公园散步", "周末我们看as去公园散步"),
])
def test_save_then_click_again_never_reverts_the_fix(tmp_path, text, span, alt, fixed):
    """问题 1：自动查错字的结果没记下是按哪段文字算的 → 保存修改以后再点一次，把改好的字又改成了自动检查的错建议。"""
    cfg, project = _voice(tmp_path, [text])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [span], "alt": alt, "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project)["c000"]["text"] == fixed
    review.save_rows(project)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project) == {} and res["fixes"] == 0 and res["adopted"]["changes"] == 0
    rec, cur = _cur(project, "c000")
    assert cur == fixed and review.analyze(rec, cur)["edits"] == []


@need_both
def test_red_marks_stay_on_the_right_words_after_save(tmp_path):
    """问题 1（续）：保存以后再点，没改的红字还标在原来的词上（以前标到了「接冰」上）。"""
    text = "小明说这是一个不纠动词，后面不能接冰鱼"
    i = text.index("冰鱼")
    cfg, project = _voice(tmp_path, [text])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[i, i + 2]], "alt": "", "reasons": ["冰鱼可能有错"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    review.save_rows(project)
    wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, "c000")
    assert "不及物动词" in cur and [cur[s:e] for s, e in review.analyze(rec, cur)["red"]] == ["冰鱼"]


@need_both
def test_uploaded_csv_never_overrides_the_teachers_later_edits(tmp_path):
    """问题 2：老师上传的 transcripts.csv 里同一个 id 的句子，把老师后来自己改过的（保存的、没保存的）改回去了。"""
    texts = ["今天我们学习一下定语从句的用法", "下面我们来看第二个例子"]
    cfg, project = _voice(tmp_path, texts)
    up = tmp_path / "transcripts.csv"
    up.write_text("id,text,drop_reason\nc000,今天我们学习一下定语从句的用法,\nc001,下面我们来看第二个例子,\n",
                  encoding="utf-8")
    wf.run_transcript_fix(cfg, "校正声音", files=[str(up)])
    review.set_draft(project, "c000", text="今天我们复习一下定语从句的用法")  # 老师听了录音自己改的
    review.save_rows(project)
    wf.run_transcript_fix(cfg, "校正声音")  # 保存过的：不改回去
    assert review.load_draft(project) == {}
    review.set_draft(project, "c001", text="下面我们来看第三个例子")  # 没保存的：也不改回去、不给改回去的建议
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project)["c001"]["text"] == "下面我们来看第三个例子"
    assert res["adopted"]["changes"] == 0
    rec, cur = _cur(project, "c001")
    assert review.analyze(rec, cur)["edits"] == []


@need_both
def test_uploaded_csv_same_id_insert_and_delete_positions(tmp_path):
    """问题 9：按上传的同一句补字时补在句号后面了；删词以后留下两个空格。"""
    cfg, project = _voice(tmp_path, ["我们来看一下这个句子。", "我们 really 来看一下这个例子", "完全不一样的一句话"],
                          ids=["a1", "a2", "a3"])
    lines = [("a1", "我们来看一下这个句子吧。"), ("a2", "我们来看一下这个例子"), ("a3", "今天讲定语从句的先行词")]
    tf.check_with_transcript(project, lines=lines, use_builtin=False)
    draft = review.load_draft(project)
    assert draft["a1"]["text"] == "我们来看一下这个句子吧。"
    assert draft["a2"]["text"] == "我们来看一下这个例子"
    assert "a3" not in draft  # 同一个 id 但完全不像：不是同一句，不用


@need_both
def test_english_is_not_replaced_by_a_chinese_word_that_does_not_sound_like_it(tmp_path):
    """问题 3：「who在定语从句中」被对到母本里「词在……」上，一键校正把 who 改成了「词」。"""
    texts = ["那接下来我们看一下最后一个关系副词why的用法。", "我们需要把这个定语从句中的which换成 that。",
             "who在定语从句中，能够做的句子成分主要有两个。", "那这个特殊的先行词就是way。",
             "好，那接下来我们看一下关系副词why。", "那我们需要把这个句子中的 as换成 that。", "这个先行词就是way，当way做先行词的时候"]
    cfg, project = _voice(tmp_path, texts)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project) == {} and res["adopted"]["changes"] == 0


@need_both
def test_one_click_does_not_adopt_unvetted_auto_guesses_and_never_learns_them(tmp_path):
    """问题 3 / 4：另一个识别引擎的猜测（李华 → 理化）不自动采用；老师自己采用、保存以后，也不会学去改别的句子。"""
    texts = ["今天李华同学回答得很好", "李华同学请你来读一下这个句子", "我们请李华来回答"]
    cfg, project = _voice(tmp_path, texts)
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[2, 4]], "alt": "今天理化同学回答得很好", "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project) == {} and res["adopted"]["unsure"] == 1
    rec, cur = _cur(project, "c000")
    info = review.analyze(rec, cur)
    assert [cur[s:e] for s, e in info["red"]] == ["李华"] and info["edits"] and not info["sure"]  # 还是红色、有建议
    review.adopt_suggestion(project, "c000")  # 老师听了录音，自己点「采用」
    review.save_rows(project)
    wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project) == {}  # 别的句子里的「李华」不会被改成「理化」


@need_both
def test_one_click_adopts_vetted_auto_suggestion_english_written_as_chinese(tmp_path):
    """标准库能证明的自动查错字建议（不是常用词的汉字、读音像英文：艾子 → as）照样一起采用。"""
    cfg, project = _voice(tmp_path, ["周末我们去看威驰引导的句子"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[6, 8]], "alt": "周末我们去看which引导的句子", "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")  # 「威驰」不在对照表里：是靠核对自动查错字的建议改的
    assert review.load_draft(project)["c000"]["text"] == "周末我们去看which引导的句子"
    assert res["fixes"] == 0 and res["adopted"]["changes"] == 1
    assert tf._auto_edit_sure("看艾子的", 1, 3, "as", lf.Lexicon.build([]))
    assert not tf._auto_edit_sure("我爱你", 1, 2, "I", lf.Lexicon.build([]))  # 「爱」是常用字：不知道是不是英文


@need_both
def test_whole_sentence_auto_suggestion_is_not_adopted(tmp_path):
    cfg, project = _voice(tmp_path, ["今天天气很好我们去公园"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[0, 11]], "alt": "金田天奇恨好喔们取攻原", "score": 0.7,
                          "reasons": ["两次识别的结果差别很大，整句可能都不对"]}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project) == {} and res["adopted"]["unsure"] == 1


@need_both
def test_adopted_suggestions_can_still_be_undone_after_clicking_again(tmp_path):
    """问题 5：以前采用过的建议（红色按钮，可以撤销）再点一次一键校正以后撤销不了了，还被算成「母本证明没错」。"""
    texts = ["周末我们一起去公园散步", "周末我们一起去公园散步", "小明昨天说借词后面接名词"]
    cfg, project = _voice(tmp_path, texts)
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[0, 2]], "alt": "周日我们一起去公园散步", "reasons": ["自动"], "score": 0.6}
    recs[1]["suspect"] = {"spans": [[0, 2]], "alt": "周日我们一起去公园散步", "reasons": ["自动"], "score": 0.6}
    recs[2]["suspect"] = {"spans": [[0, 2]], "alt": "小名昨天说借词后面接名词", "reasons": ["自动"], "score": 0.6}
    project.save_manifest(recs)
    for cid in ("c000", "c001", "c002"):
        review.adopt_suggestion(project, cid)
    review.save_rows(project, ["c001"])
    res = tf.check_with_transcript(project)
    assert res["cleared"] == 0 and res["kept_undo"] == 2
    for cid in ("c000", "c001"):
        rec, cur = _cur(project, cid)
        assert cur.startswith("周日") and review.analyze(rec, cur)["adopted"]
    rec, cur = _cur(project, "c002")
    info = review.analyze(rec, cur)
    assert cur == "小名昨天说介词后面接名词" and info["adopted"] and len(info["undo"]) == 2  # 两处都能撤销
    review.unadopt_suggestion(project, "c002")
    assert review.load_draft(project).get("c002") is None  # 全部撤销：回到保存的样子
    review.unadopt_suggestion(project, "c000")
    assert review.load_draft(project).get("c000") is None


@need_both
def test_second_click_keeps_undo_for_unsaved_direct_fixes(tmp_path):
    cfg, project = _voice(tmp_path, ["小明昨天说借词后面接名词", "我们先来看艾子引导的定语从句。"])
    wf.run_transcript_fix(cfg, "校正声音")
    wf.run_transcript_fix(cfg, "校正声音")
    for cid in ("c000", "c001"):
        rec, cur = _cur(project, cid)
        assert review.analyze(rec, cur)["adopted"], cid
    review.unadopt_suggestion(project, "c001")
    assert "艾子" in _cur(project, "c001")[1]


@need_pinyin
@pytest.mark.parametrize("text", ["他是一位语文老师。", "凭借词汇量取胜。", "这里用陷阱词汇考你。", "叙述词语要准确。",
                                  "这个主剧情很精彩。", "关于代词的用法我们下次讲", "每一位语言学家都知道"])
def test_without_jieba_nothing_is_changed_directly(tmp_path, monkeypatch, text):
    """问题 6：没有 jieba（判断不了完整的词）时，对照表直接改出了「凭介词汇」「一谓语文」。"""
    monkeypatch.setattr(lf, "_tokenizer", lambda: None)
    cfg, project = _voice(tmp_path, [text])
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert review.load_draft(project) == {} and res["fixes"] == 0 and res["adopted"]["changes"] == 0


@need_both
@pytest.mark.parametrize("text", ["他会说壮语，也会说普通话", "他的原籍是山东", "关于代词的用法我们下次讲",
                                  "这个词兼名词和动词两种词性", "这是两个陷阱词，考试要小心", "如果我们把关系代词位置还原"])
def test_real_words_are_never_changed_directly(tmp_path, text):
    """问题 7：本身是词的（壮语 → 状语）和正常的说法（关于代词、兼名词、陷阱词）不直接改。"""
    cfg, project = _voice(tmp_path, [text])
    res = wf.run_transcript_fix(cfg, "校正声音", adopt_all=False)
    assert res["fixes"] == 0 and review.load_draft(project) == {}
    review.adopt_all_suggestions(project)
    assert review.load_draft(project) == {}  # 一键也不自动采用（没把握的建议还在，可以一行一行采用）


@need_both
def test_dismissed_row_with_unsaved_edit_is_left_alone(tmp_path):
    """问题 8：表格里显示没保存的修改时点「这句没错」，一键校正还是改了这一句。"""
    from voicetwin.data.proofcheck import dismiss_suspect

    cfg, project = _voice(tmp_path, ["关于带词的用法下节课讲"])
    review.set_draft(project, "c000", text="关于代词的用法下节课讲")
    dismiss_suspect(project, "c000")
    res = tf.check_with_transcript(project)
    assert res["dismissed"] == 1 and review.load_draft(project)["c000"]["text"] == "关于代词的用法下节课讲"


@need_both
def test_row_fixes_only_for_the_same_sentence(tmp_path):
    """逐句修缮记录按 id 改：新的录音碰巧是同一个 id、但句子不一样时不改。"""
    rid, (wrong, right, _why) = next(iter(tf.builtin_fixes().items()))[0], next(iter(tf.builtin_fixes().values()))[0]
    cfg, project = _voice(tmp_path, [f"这是另外一句新的话，里面也有{wrong}这几个字，但不是同一句"], ids=[rid])
    tf.check_with_transcript(project)
    assert rid not in review.load_draft(project)


def test_teacher_uploads_her_raw_transcripts_csv_again(tmp_path):
    """老师又上传了修缮以前的 transcripts.csv（同样的 id，里面还有「借词」）：结果和不上传一样，
    需要改的 123 句全对、多改 0 句；保存以后再点一次什么都不改。"""
    orig = list(csv.DictReader(open(MOTHER_DIR / "母本_原文.csv", encoding="utf-8-sig")))
    clean = {r["id"]: r["text"] for r in csv.DictReader(open(MOTHER_DIR / "母本_修缮后.csv", encoding="utf-8-sig"))}
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "老师").ensure()
    project.save_manifest([{"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh",
                            "duration": 3.0, "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
                            "split": "train"} for r in orig])
    res = wf.run_transcript_fix(cfg, "老师", files=[str(MOTHER_DIR / "母本_原文.csv")])
    draft = review.load_draft(project)
    need = {r["id"] for r in orig if r["text"] != clean[r["id"]] and r["drop_reason"] != "老师删除"}
    assert set(draft) == need and all(draft[i]["text"] == clean[i] for i in need)
    assert res["adopted"]["changes"] == 0
    review.save_rows(project)
    res2 = wf.run_transcript_fix(cfg, "老师")
    assert review.load_draft(project) == {} and res2["fixes"] == 0 and res2["adopted"]["changes"] == 0


@need_both
def test_clip_count_after_one_click_only_counts_rows_still_wrong(tmp_path):
    """表格上方「N 条可能有错」：一键校正改好、还没保存的不算（以前按保存的文字算，改好的 123 条也算进去了）。"""
    pytest.importorskip("gradio")
    from voicetwin.webui.app import _clips_count_md

    cfg, project = _voice(tmp_path, ["小明昨天说借词后面接名词", "今天李华同学回答得很好"])
    recs = project.load_manifest()
    recs[1]["suspect"] = {"spans": [[2, 4]], "alt": "今天理化同学回答得很好", "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    assert "**1** 条可能有错" in _clips_count_md(cfg, "校正声音")  # 只剩没把握的那一条


# ---------------------------------------------------------------------------- 第二次独立检查发现的问题（每个都有一个测试）
@need_both
def test_mother_txt_without_ids_never_reverts_saved_fixes(tmp_path):
    """问题 1（重要）：上传没有 id 的 txt 母本（老师修缮以前的文字）：保存以后再点，把改好的「介词」「as」对齐改回了
    「借词」「艾子」，再点又改过来，来回跳。"""
    texts = ["第二种情况就是关系代词that不能和借词一起提前到定语从句的句首", "我们先来看艾子引导的这个定语从句的例子"]
    cfg, project = _voice(tmp_path, texts)
    up = tmp_path / "旧讲稿.txt"
    up.write_text("\n".join(texts), encoding="utf-8")
    wf.run_transcript_fix(cfg, "校正声音", files=[str(up)])
    fixed = {k: v["text"] for k, v in review.load_draft(project).items()}
    assert "介词" in fixed["c000"] and "as" in fixed["c001"]
    review.save_rows(project)
    for _ in range(3):
        res = wf.run_transcript_fix(cfg, "校正声音")
        assert review.load_draft(project) == {} and res["fixes"] == 0 and res["adopted"]["changes"] == 0
    assert {r["id"]: r["text"] for r in project.load_manifest()} == fixed


@need_both
def test_mother_txt_never_overrides_the_teachers_own_edit(tmp_path):
    """问题 1（续）：下载的「改好的文字」txt 当母本上传；老师后来自己改了一句（小明 → 晓明）并保存，一键又改回去了。"""
    texts = ["小明今天下午去公园里面散步了", "我们今天来学习一下定语从句的基本用法", "这个句子里面的先行词就是这个人"]
    cfg, project = _voice(tmp_path, texts)
    out = review.export_text(project)
    review.set_draft(project, "c000", text="晓明今天下午去公园里面散步了")
    review.save_rows(project)
    res = wf.run_transcript_fix(cfg, "校正声音", files=[out["path"]])
    assert review.load_draft(project) == {} and res["fixes"] == 0
    rec, cur = _cur(project, "c000")
    assert cur == "晓明今天下午去公园里面散步了" and review.analyze(rec, cur)["edits"] == []


@need_both
def test_unsure_insertion_next_to_the_same_character_is_not_adopted(tmp_path):
    """问题 2：没把握的「补上一个字」挨着一样的字（看 → 看看），两次比对的位置差一个字，一键校正把它采用了。"""
    cfg, project = _voice(tmp_path, ["我们一起来看这个从剧的结构", "我们一起来看这个句子的结构"])
    recs = project.load_manifest()
    for k, t in enumerate(["我们一起来看看这个从剧的结构", "我们一起来看看这个句子的结构"]):
        recs[k]["suspect"] = {"spans": [[5, 7]], "alt": t, "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")
    draft = review.load_draft(project)
    assert draft["c000"]["text"] == "我们一起来看这个从句的结构" and "c001" not in draft
    assert res["adopted"]["changes"] == 0 and res["adopted"]["unsure"] == 2


@need_both
def test_partly_similar_same_id_row_is_only_an_unsure_suggestion(tmp_path):
    """问题 3：上传的 csv 里同一个 id 的句子只有点像（切的位置不一样），一键校正把录音里没有的话补了进去。"""
    cfg, project = _voice(tmp_path, ["那么到底什么是定语从句呢"], ids=["x_0031"])
    up = tmp_path / "transcripts.csv"
    up.write_text("id,text\nx_0031,我们今天来学习定语从句那么到底什么是定语从句呢\n", encoding="utf-8")
    res = wf.run_transcript_fix(cfg, "校正声音", files=[str(up)])
    assert review.load_draft(project) == {} and res["adopted"]["unsure"] == 1
    rec, cur = _cur(project, "x_0031")
    assert review.analyze(rec, cur)["edits"]  # 建议还在，老师听了录音可以自己采用


@need_both
def test_row_with_fix_and_unsure_suggestion_keeps_an_undo_button(tmp_path):
    """问题 4：一行里有直接改好的（介词）和没把握的建议（理化）：只显示蓝色「采用」，改好的撤销不了。"""
    pytest.importorskip("gradio")
    from voicetwin.webui.app import _suggest_cell

    cfg, project = _voice(tmp_path, ["小明昨天说借词后面接名词，今天李华同学回答得很好"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[15, 17]], "alt": "小明昨天说借词后面接名词，今天理化同学回答得很好",
                          "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    for saved in (False, True):
        rec, cur = _cur(project, "c000")
        info = review.analyze(rec, cur)
        html = _suggest_cell(info)
        assert "vt-sug-blue" in html and "vt-sug-red" in html, html  # 两个按钮都有
        review.unadopt_suggestion(project, "c000")
        assert "借词" in _cur(project, "c000")[1] and "李华" in _cur(project, "c000")[1]
        review.adopt_suggestion(project, "c000")
        assert "理化" in _cur(project, "c000")[1]  # 蓝色的「采用」照样能用
        review.discard_draft(project)
        if not saved:
            wf.run_transcript_fix(cfg, "校正声音")
            review.save_rows(project)


@need_both
def test_teachers_undo_is_remembered(tmp_path):
    """问题 5：老师点红色按钮撤销了（主句 → 主剧），再点一键校正又改回去；保存以后也一样。"""
    cfg, project = _voice(tmp_path, ["他说这个主剧的结构很完整", "这个主剧的结构也很完整"])
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "c000")[1] == "他说这个主句的结构很完整"
    review.unadopt_suggestion(project, "c000")
    for _ in range(2):
        wf.run_transcript_fix(cfg, "校正声音")
        assert _cur(project, "c000")[1] == "他说这个主剧的结构很完整"  # 不再改回来
        assert _cur(project, "c001")[1] == "这个主句的结构也很完整"  # 别的句子照常改
        review.save_rows(project)
    rec, cur = _cur(project, "c000")
    assert review.analyze(rec, cur)["edits"] == []  # 也不再建议


@pytest.mark.parametrize("kind", ["zip", "nul"])
def test_binary_or_broken_csv_upload_says_why(tmp_path, kind):
    """问题 6：Excel 表格改名成 .csv、里面有 0 字节的文件：以前直接报英文错误，现在说明原因。"""
    import zipfile

    cfg, project = _voice(tmp_path, ["我们先来看这个定语从句的例子"])
    f = tmp_path / "transcripts.csv"
    if kind == "zip":
        with zipfile.ZipFile(f, "w") as zf:
            zf.writestr("xl/sharedStrings.xml", "<sst>" + "我们先来看这个定语从句的例子" * 50 + "</sst>")
        with pytest.raises(ValueError, match="不是文字文件"):
            tf.save_transcripts(project, [str(f)])
    else:
        f.write_text("id,text\nc000,我们先来看这个定语从句的例子吧\n", encoding="utf-32")
        assert tf.save_transcripts(project, [str(f)])["files"] == ["transcripts.csv"]
        g = tmp_path / "t2.csv"
        g.write_bytes("id,text\nc000,我们先来看这个\x00定语从句的例子吧\n".encode("utf-8"))
        assert tf.parse_mother("t2.csv", g.read_text(encoding="utf-8")) == [("c000", "我们先来看这个定语从句的例子吧")]


def test_dismiss_with_unsaved_edit_then_auto_check_does_not_flag_again(tmp_path, monkeypatch):
    """问题 7：表格里显示没保存的修改时点「这句没错」，再点「自动查找可能的错字」，这一句又被标红。"""
    from voicetwin.data import proofcheck as pc

    cfg, project = _voice(tmp_path, ["今天我们讲一下定语从句的基本用法", "下面我们来看第二个例子"])
    monkeypatch.setattr(pc, "build_suspect", lambda text, *a, **k: {"spans": [[0, 2]], "alt": "", "reasons": ["自动"],
                                                                     "score": 0.6})
    pc.find_suspects(project, cfg)
    review.set_draft(project, "c000", text="今天我们讲一下定语从句的用法")
    pc.dismiss_suspect(project, "c000")
    pc.find_suspects(project, cfg)
    assert not {r["id"]: r for r in project.load_manifest()}["c000"].get("suspect")


@need_both
def test_undo_covers_earlier_adoption_when_teacher_also_edited_elsewhere(tmp_path):
    """问题 8：以前采用过建议（周末 → 周日）、老师又在别处自己加了字：再点一键校正以后，以前采用的撤销不了。"""
    cfg, project = _voice(tmp_path, ["周末我们一起去公园散步，小明昨天说借词后面接名词"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[0, 2]], "alt": "周日我们一起去公园散步，小明昨天说借词后面接名词",
                          "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    review.adopt_suggestion(project, "c000")
    review.set_draft(project, "c000", text="周日我们一起去公园散步，小明昨天说借词后面接名词好的")  # 老师自己加的
    wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, "c000")
    assert cur == "周日我们一起去公园散步，小明昨天说介词后面接名词好的"
    assert len(review.analyze(rec, cur)["undo"]) == 2
    review.unadopt_suggestion(project, "c000")
    assert _cur(project, "c000")[1] == "周末我们一起去公园散步，小明昨天说借词后面接名词好的"  # 老师加的字还在


@need_both
def test_auto_check_between_one_click_and_save_keeps_undo(tmp_path, monkeypatch):
    """问题 9：一键校正以后、保存以前点「自动查找可能的错字」：改好的行撤销不了了，再点一键校正也回不来。"""
    from voicetwin.data import proofcheck as pc

    cfg, project = _voice(tmp_path, ["小明昨天说借词后面接名词", "我们先来看艾子引导的定语从句。"])
    wf.run_transcript_fix(cfg, "校正声音")
    monkeypatch.setattr(pc, "build_suspect", lambda text, *a, **k: (
        {"spans": [[0, 2]], "alt": "", "reasons": ["自动"], "score": 0.6} if "小明" in text else None))
    pc.find_suspects(project, cfg)
    for _ in range(2):
        for cid in ("c000", "c001"):
            rec, cur = _cur(project, cid)
            assert review.analyze(rec, cur)["undo"], cid
        wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, "c000")
    assert [cur[s:e] for s, e in review.analyze(rec, cur)["red"]] == ["小明"]  # 这次查到的标红也在


def test_result_message_wording():
    """问题 10：没有自动改、但还有要听的句子时，标题不能写「没有需要改的地方」；按钮叫「采用」。"""
    pytest.importorskip("gradio")
    from voicetwin.webui.app import WebUI

    md = WebUI._textfix_md({"checked": 2, "adopted": {"unsure": 2}})
    assert "没有需要改的地方" not in md and "听一听" in md and "「采用」" in md and "✓ 采用" not in md
    assert "没有需要改的地方" in WebUI._textfix_md({"checked": 2, "adopted": {}})


# ---------------------------------------------------------------------------- 第三次独立检查发现的问题（每个都有一个测试）
@need_both
@pytest.mark.parametrize("text", ["这里借词主剧都要记一下", "它是关系带词艾子的用法", "看一下借词主剧的意思",
                                  "我们说借词是什么，" * 8, "这个从剧的借词要注意"])
def test_undo_is_remembered_for_neighbouring_and_bundled_changes(tmp_path, text):
    """问题 1（重要）：撤销记的是「前后 3 个字」，挨着的两处、一次改好几处、重复很多遍的句子都对不上，再点又改回来
    （老师真实数据上 123 句里有 12 句）。现在按「原来的字 → 程序想改成的字」记，不管位置。"""
    cfg, project = _voice(tmp_path, [text])
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "c000")[1] != text
    review.unadopt_suggestion(project, "c000")
    assert _cur(project, "c000")[1] == text
    for _ in range(2):
        res = wf.run_transcript_fix(cfg, "校正声音")
        assert _cur(project, "c000")[1] == text and res["fixes"] == 0 and res["adopted"]["changes"] == 0
        review.save_rows(project)


def test_teacher_undoing_every_fix_on_her_real_rows_is_remembered(tmp_path):
    """老师真实的 1004 句：一键校正以后 123 句全部点红色按钮撤销，再点一键校正：一句都不改回来（保存前后都一样）。"""
    if not (HAS_PINYIN and HAS_JIEBA):
        pytest.skip("没有装 pypinyin / jieba")
    orig = list(csv.DictReader(open(MOTHER_DIR / "母本_原文.csv", encoding="utf-8-sig")))
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "老师").ensure()
    project.save_manifest([{"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh",
                            "duration": 3.0, "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
                            "split": "train"} for r in orig])
    wf.run_transcript_fix(cfg, "老师")
    changed = list(review.load_draft(project))
    assert len(changed) == 123
    for cid in changed:
        review.unadopt_suggestion(project, cid)
    assert review.load_draft(project) == {}
    res = wf.run_transcript_fix(cfg, "老师")
    assert review.load_draft(project) == {} and res["fixes"] == 0 and res["adopted"]["changes"] == 0


@need_both
def test_teachers_own_typing_is_never_overridden(tmp_path):
    """问题 2：老师自己把改好的字打回去（主句 → 主剧）并保存、或者自己打了「借词」：一键校正又改掉了。"""
    cfg, project = _voice(tmp_path, ["他说这个主剧的结构很完整", "英语里有很多外来的词"])
    wf.run_transcript_fix(cfg, "校正声音")
    review.save_rows(project)
    review.set_draft(project, "c000", text="他说这个主剧的结构很完整")  # 双击自己改回去
    review.save_rows(project)
    review.set_draft(project, "c001", text="英语里有很多借词，也就是外来的词")  # 自己打的
    for _ in range(2):
        res = wf.run_transcript_fix(cfg, "校正声音")
        assert _cur(project, "c000")[1] == "他说这个主剧的结构很完整"
        assert _cur(project, "c001")[1] == "英语里有很多借词，也就是外来的词"
        assert res["fixes"] == 0 and res["adopted"]["changes"] == 0
        review.save_rows(project)


@need_both
def test_row_revert_counts_as_undo(tmp_path):
    """「撤销这一行的修改」把一键校正改好的撤销了：再点也不改回来。"""
    cfg, project = _voice(tmp_path, ["他说这个主剧的结构很完整"])
    wf.run_transcript_fix(cfg, "校正声音")
    review.discard_draft(project, "c000")
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "c000")[1] == "他说这个主剧的结构很完整" and review.load_draft(project) == {}


@need_both
def test_dismissed_row_is_never_changed_by_old_suggestions(tmp_path):
    """问题 3：点过「这句没错」的句子，以前留下的建议被一键校正采用了。"""
    from voicetwin.data.proofcheck import dismiss_suspect

    t0 = "这里的借词后面要接名词，大家记一下"
    cfg, project = _voice(tmp_path, [t0])
    dismiss_suspect(project, "c000")
    review.set_draft(project, "c000", text=t0.replace("大家", "同学们"))
    wf.run_transcript_fix(cfg, "校正声音")
    review.set_draft(project, "c000", text=t0)  # 改回老师确认过的那句
    res = wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, "c000")
    assert cur == t0 and res["dismissed"] == 1 and res["adopted"]["changes"] == 0
    assert not rec.get("suspect")  # 以前的标红、建议也去掉了


@need_both
def test_uploading_the_downloaded_text_does_not_hide_auto_flags(tmp_path):
    """问题 4：把下载的「改好的文字」当母本上传，每一句都和自己对上，自动查错字标红的地方被当成「母本证明没错」去掉了。"""
    texts = ["今天我们讲一下定语从句的用法和意义", "大家先把课本翻到第三十二页看一下", "这个句子里面有一个先行词需要注意"]
    cfg, project = _voice(tmp_path, texts)
    recs = project.load_manifest()
    recs[1]["suspect"] = {"spans": [[10, 12]], "alt": texts[1].replace("三十二", "三十三"), "reasons": ["另一个引擎"],
                          "score": 0.7}
    recs[2]["suspect"] = {"spans": [[0, 2]], "alt": "", "reasons": ["识别时没把握"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    out = review.export_text(project)
    res = wf.run_transcript_fix(cfg, "校正声音", files=[out["path"]])
    assert res["cleared"] == 0
    for cid, red in (("c001", ["十二"]), ("c002", ["这个"])):
        rec, cur = _cur(project, cid)
        assert [cur[s:e] for s, e in review.analyze(rec, cur)["red"]] == red


@need_both
def test_undo_clicked_while_auto_check_runs_is_kept(tmp_path, monkeypatch):
    """问题 5：自动查错字正在进行时点红色按钮撤销：查错字最后保存校对表时把撤销的记录冲掉了（现在记在单独的文件里）。"""
    from voicetwin.data import proofcheck as pc

    cfg, project = _voice(tmp_path, ["他说这个主剧的结构很完整"] + [f"这是第{i}句普通的话" for i in range(5)])
    wf.run_transcript_fix(cfg, "校正声音")
    state = {"done": False}

    def build(text, *a, **k):
        if not state["done"]:
            state["done"] = True
            review.unadopt_suggestion(project, "c000")
        return None

    monkeypatch.setattr(pc, "build_suspect", build)
    pc.find_suspects(project, cfg)
    assert review.load_rejected(project).get("c000")
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "c000")[1] == "他说这个主剧的结构很完整"


@need_both
def test_rows_still_red_after_adopting_are_counted(tmp_path):
    """问题 6：一行采用了有把握的建议以后还有标红（没有建议），结果说明里没算进「要你听」的句子。"""
    t = "我们先看威驰引导的从句，然后再看后面那个例子的用法"
    cfg, project = _voice(tmp_path, [t])
    recs = project.load_manifest()
    a, b = t.index("威驰"), t.index("那个")
    recs[0]["suspect"] = {"spans": [[a, a + 2], [b, b + 2]], "alt": t.replace("威驰", "which"),
                          "reasons": ["另一个引擎听到 which", "识别时没把握"], "score": 0.7}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert res["adopted"]["changes"] == 1 and res["adopted"]["no_suggestion"] == 1


# ---------------------------------------------------------------------------- 第四次独立检查发现的问题（每个都有一个测试）
@need_both
@pytest.mark.parametrize("how", ["type", "revert"])
def test_typed_or_row_revert_is_remembered_at_sentence_edges(tmp_path, how):
    """问题 1（重要）：在句子开头 / 结尾改好的字，老师自己打回去或者「撤销这一行的修改」，再点又改回来。"""
    texts = ["借词后面一般要接名词或者代词。", "我们今天要讲的这个就是借词"]
    cfg, project = _voice(tmp_path, texts, ids=["e_0001", "e_0002"])
    wf.run_transcript_fix(cfg, "校正声音")
    for rid in ("e_0001", "e_0002"):
        if how == "type":
            review.set_draft(project, rid, text=_cur(project, rid)[1].replace("介词", "借词"))
        else:
            review.discard_draft(project, rid)
    wf.run_transcript_fix(cfg, "校正声音")
    assert [_cur(project, r)[1] for r in ("e_0001", "e_0002")] == texts and review.load_draft(project) == {}


@need_both
@pytest.mark.parametrize("how", ["type", "revert", "unadopt"])
def test_undoing_a_deletion_is_remembered(tmp_path, how):
    """问题 1（续）：按上传的同一句删掉的字（那个），老师改回去以后再点又删掉。"""
    right, wrong = "我们今天来讲一下定语从句的用法。", "我们今天来讲一下那个定语从句的用法。"
    cfg, project = _voice(tmp_path, [wrong, "这是另外一句话，没有问题。"], ids=["x_0001", "x_0002"])
    up = tmp_path / "transcripts.csv"
    up.write_text(f"id,text\nx_0001,{right}\nx_0002,这是另外一句话，没有问题。\n", encoding="utf-8")
    wf.run_transcript_fix(cfg, "校正声音", files=[str(up)])
    assert _cur(project, "x_0001")[1] == right
    {"type": lambda: review.set_draft(project, "x_0001", text=wrong),
     "revert": lambda: review.discard_draft(project, "x_0001"),
     "unadopt": lambda: review.unadopt_suggestion(project, "x_0001")}[how]()
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "x_0001")[1] == wrong


@need_both
@pytest.mark.parametrize("how", ["type", "revert"])
def test_teacher_typing_every_fix_back_on_real_rows_is_remembered(tmp_path, how):
    """老师真实的 1004 句：123 句全部自己打回去（或撤销这一行的修改），再点一句都不改回来（以前有 2 句：开头的斌与、英文 home）。"""
    if not (HAS_PINYIN and HAS_JIEBA):
        pytest.skip("没有装 pypinyin / jieba")
    orig = list(csv.DictReader(open(MOTHER_DIR / "母本_原文.csv", encoding="utf-8-sig")))
    cfg = make_cfg(tmp_path / "ws")
    project = wf.Project(cfg, "老师").ensure()
    project.save_manifest([{"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh",
                            "duration": 3.0, "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
                            "split": "train"} for r in orig])
    wf.run_transcript_fix(cfg, "老师")
    texts = {r["id"]: r["text"] for r in orig}
    for cid in list(review.load_draft(project)):
        if how == "type":
            review.set_draft(project, cid, text=texts[cid])
        else:
            review.discard_draft(project, cid)
    assert review.load_draft(project) == {}
    res = wf.run_transcript_fix(cfg, "老师")
    assert review.load_draft(project) == {} and res["fixes"] == 0 and res["adopted"]["changes"] == 0


@need_both
@pytest.mark.parametrize("how", ["dismiss_revert", "dismiss_type", "autocheck_type"])
def test_typed_undo_is_remembered_after_dismiss_or_auto_check(tmp_path, monkeypatch, how):
    """问题 2：点过「这句没错」、或者保存以后又自动查过错字（「可能有错」列的记录没了），老师再改回去，一键又改回来。"""
    from voicetwin.data import proofcheck as pc

    t = "这是一个定语从剧，那个修饰名词。"
    cfg, project = _voice(tmp_path, [t], ids=["w_0001"])
    recs = project.load_manifest()
    k = t.index("那个")
    recs[0]["suspect"] = {"spans": [[k, k + 2]], "alt": t.replace("那个", "这个"), "reasons": ["两个引擎"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    if how.startswith("dismiss"):
        pc.dismiss_suspect(project, "w_0001")
    else:
        review.save_rows(project)
        monkeypatch.setattr(pc, "build_suspect", lambda text, *a, **kw: None)
        pc.find_suspects(project, cfg)
    if how.endswith("revert"):
        review.discard_draft(project, "w_0001")
    else:
        review.set_draft(project, "w_0001", text=_cur(project, "w_0001")[1].replace("从句", "从剧"))
        review.save_rows(project)
    wf.run_transcript_fix(cfg, "校正声音")
    assert "从剧" in _cur(project, "w_0001")[1]


@need_both
def test_auto_suggestion_never_overrides_teachers_typing(tmp_path, monkeypatch):
    """问题 3：老师自己打的「威驰」（识别的是「微池」）保存了，自动查错字的另一个引擎听成 which，一键把它改成了 which。"""
    from voicetwin.data import proofcheck as pc

    cfg, project = _voice(tmp_path, ["我昨天开的是一辆微池汽车。"], ids=["b_0001"])
    review.set_draft(project, "b_0001", text="我昨天开的是一辆威驰汽车。")
    review.save_rows(project)

    def fake(text, *a, **kw):
        k = text.index("威驰")
        return {"spans": [[k, k + 2]], "alt": text[:k] + "which" + text[k + 2:], "reasons": ["另一个引擎"], "score": 0.7}

    monkeypatch.setattr(pc, "build_suspect", fake)
    pc.find_suspects(project, cfg)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "b_0001")[1] == "我昨天开的是一辆威驰汽车。" and res["adopted"]["changes"] == 0


@need_both
def test_fix_right_next_to_a_teacher_deletion_still_works(tmp_path):
    """问题 4：老师删掉了「借词」后面的「嗯」，一键校正就不改「借词」了（删掉的地方旁边的字也被当成老师改过的）。"""
    orig = ["这个借词嗯用来连接名词。", "这个借词用来连接名词嗯。", "这个借词用来连接名词。"]
    cfg, project = _voice(tmp_path, orig, ids=["y_0001", "y_0002", "y_0003"])
    review.set_draft(project, "y_0001", text="这个借词用来连接名词。")
    review.set_draft(project, "y_0002", text="这个借词用来连接名词。")
    review.save_rows(project)
    wf.run_transcript_fix(cfg, "校正声音")
    for rid in ("y_0001", "y_0002", "y_0003"):
        assert _cur(project, rid)[1] == "这个介词用来连接名词。", rid


@need_both
def test_rejected_fix_is_not_shown_as_a_suggestion_again(tmp_path):
    """问题 5：一行两处改好的，老师把一处打回去：再点（保存以后也一样），那一处还显示成蓝色「采用」、说明写着「已按标准库改好」。"""
    cfg, project = _voice(tmp_path, ["这个借词引导一个定语从剧。"], ids=["k_0001"])
    wf.run_transcript_fix(cfg, "校正声音")
    review.set_draft(project, "k_0001", text=_cur(project, "k_0001")[1].replace("介词", "借词"))
    for _ in range(2):
        res = wf.run_transcript_fix(cfg, "校正声音")
        rec, cur = _cur(project, "k_0001")
        info = review.analyze(rec, cur)
        assert cur == "这个借词引导一个定语从句。" and info["edits"] == [] and info["red"] == []
        assert info["adopted"] and not any("借词" in x for x in rec["suspect"]["reasons"])  # 从剧 → 从句 还能撤销
        assert res["adopted"]["unsure"] == 0 and res["adopted"]["no_suggestion"] == 0
        review.save_rows(project)


@need_both
def test_undo_replace_is_not_recorded_as_rejecting_a_fix(tmp_path):
    """问题 6：查找替换「从剧 → 从句」再「撤销刚才的替换」，被记成老师不要这个改法，一键校正就不改了。"""
    texts = ["这是一个定语从剧，修饰名词。", "这是一个定语从剧，也修饰名词。"]
    cfg, project = _voice(tmp_path, texts, ids=["z_0001", "z_0002"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[6, 8]], "alt": texts[0].replace("从剧", "从句"), "reasons": ["两个引擎"], "score": 0.6}
    project.save_manifest(recs)
    review.replace_matches(project, "从剧", "从句")
    review.undo_replace(project)
    assert review.load_rejected(project) == {}
    wf.run_transcript_fix(cfg, "校正声音")
    assert all("从句" in _cur(project, r)[1] for r in ("z_0001", "z_0002"))


@need_both
def test_builtin_mother_still_confirms_the_same_sentence_with_another_id(tmp_path):
    """问题 7：和程序自带母本一模一样、但 id 不一样的句子（重新切的片段），母本不再能证明它没错（自动查错字的错标红留着）。"""
    lines = [x for rid, x in tf.builtin_mother() if rid and 15 <= len(x) <= 40][:12]
    cfg, project = _voice(tmp_path, lines)
    recs = project.load_manifest()
    for r in recs:
        t = r["text"]
        r["suspect"] = {"spans": [[3, 5]], "alt": t[:3] + "那个" + t[5:], "reasons": ["两个引擎"], "score": 0.6}
    project.save_manifest(recs)
    wf.run_transcript_fix(cfg, "校正声音")
    left = 0
    for r in project.load_manifest():
        rec, cur = _cur(project, r["id"])
        info = review.analyze(rec, cur)
        left += bool(info["red"] or info["edits"])
    assert left <= 1 and review.load_draft(project) == {}


@need_both
def test_undo_replace_keeps_an_undo_made_after_the_replace(tmp_path):
    """随机操作脚本发现：先查找替换（我们 → 咱们），再一键校正、点红色按钮撤销（从剧），最后「撤销刚才的替换」：
    以前把撤销记录整个恢复成替换以前的样子，老师后来的撤销丢了，再点一键又改回「从句」。"""
    t = "在这个句子里面定语从剧的关系代词，我们也使用了which。"
    cfg, project = _voice(tmp_path, [t], ids=["c000"])
    review.replace_matches(project, "我们", "咱们")
    wf.run_transcript_fix(cfg, "校正声音")
    assert "从句" in _cur(project, "c000")[1]
    review.unadopt_suggestion(project, "c000")
    review.undo_replace(project)
    assert _cur(project, "c000")[1] == t
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "c000")[1] == t  # 老师撤销的「从剧 → 从句」不再改回来


# ---------------------------------------------------------------------------- 第五次独立检查发现的问题（每个都有一个测试）
@need_both
@pytest.mark.parametrize("case", ["adopted_then_undone", "real_error"])
def test_uploading_the_downloaded_text_never_hides_real_errors(tmp_path, case):
    """问题 1：把下载的「改好的文字」当母本上传（网页上建议这么做）：没检查过的句子「自己证明自己没错」，
    自动查错字的标红、「线性 → 先行」这种建议被去掉了。"""
    from voicetwin.data import proofcheck as pc  # noqa: F401

    if case == "adopted_then_undone":
        t = "但是如果我们只是单独把关系带词which放在定语从句句首的话，那么这个which是可以直接被省略掉的。"
        cfg, project = _voice(tmp_path, [t, "这个句子完全没有错误，我们继续往下看。"], ids=["0007_d8ade5_0026", "s_0002"])
        recs = project.load_manifest()
        k = t.index("单独把")
        recs[0]["suspect"] = {"spans": [[k, k + 3]], "alt": t[:k] + "单单把" + t[k + 3:], "reasons": ["另一个引擎"],
                              "score": 0.7}
        project.save_manifest(recs)
        wf.run_transcript_fix(cfg, "校正声音")
        review.unadopt_suggestion(project, "0007_d8ade5_0026")
        rid, want = "0007_d8ade5_0026", "单独把"
    else:
        t = "两者最主要的区别，就是当线性词是物的情况下，"
        cfg, project = _voice(tmp_path, [t], ids=["0007_d8ade5_0004"])
        wf.run_transcript_fix(cfg, "校正声音")
        rid, want = "0007_d8ade5_0004", "线性"
    rec, cur = _cur(project, rid)
    assert want in [cur[s:e] for s, e in review.analyze(rec, cur)["red"]]
    out = review.export_text(project)
    res = wf.run_transcript_fix(cfg, "校正声音", files=[out["path"]])
    rec, cur = _cur(project, rid)
    info = review.analyze(rec, cur)
    assert res["cleared"] == 0 and want in [cur[s:e] for s, e in info["red"]] and info["edits"]


@need_both
def test_mixed_row_adopt_and_undo_never_garble_the_text(tmp_path):
    """问题 2 / 3：一行里有直接改好的（斌与 → 宾语）和挨着的没把握的建议（像主语 → 了）：点蓝色「采用」变成了
    「了、宾语、宾语」，红色撤销也撤不回去；再点一次一键校正，红色「已采用」没了。"""
    pytest.importorskip("gradio")
    from voicetwin.webui.app import _suggest_cell

    t = "如果因为缺少类似于像主语、斌与或者是表语而无法构成一个完整的句子，"
    cfg, project = _voice(tmp_path, [t], ids=["05_27d31c_0082"])  # 老师那一句的 id（自带母本里同一句不拿来比）
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[9, 12]], "alt": t[:9] + "了" + t[12:], "reasons": ["另一个引擎听到「了」"], "score": 0.6}
    project.save_manifest(recs)
    for _ in range(2):  # 连点两次一键校正：结果一样，两个按钮都在，说明不乱
        wf.run_transcript_fix(cfg, "校正声音")
        rec, cur = _cur(project, "05_27d31c_0082")
        assert cur == t.replace("斌与", "宾语")
        html = _suggest_cell(review.analyze(rec, cur))
        assert "像主语 → 了" in html and "斌与 → 宾语" in html and "vt-sug-red" in html
    out = review.adopt_suggestion(project, "05_27d31c_0082")
    assert out["text"] == "如果因为缺少类似于了、宾语或者是表语而无法构成一个完整的句子，" and out["changes"] == "像主语 → 了"
    out = review.unadopt_suggestion(project, "05_27d31c_0082")
    assert out["text"] == t and "斌与 → 宾语" in out["changes"]


@need_both
def test_two_clicks_in_a_row_give_the_same_result(tmp_path):
    """问题 4：直接改好的那几个字里没变的字（关键代词 → 关系代词 里的「词」）上自动查错字的标红，第一次被盖住、第二次又冒出来。"""
    t = "接下来我们学习一下关键代词that的使用方法。"
    cfg, project = _voice(tmp_path, [t], ids=["0007_d8ade5_0067"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[12, 13]], "alt": t[:12] + "那个" + t[12:], "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    seen = []
    for _ in range(2):
        res = wf.run_transcript_fix(cfg, "校正声音")
        rec, cur = _cur(project, "0007_d8ade5_0067")
        info = review.analyze(rec, cur)
        seen.append((cur, [cur[s:e] for s, e in info["red"]], len(info["edits"]), res["adopted"]["unsure"]))
    assert seen[0] == seen[1] and seen[0][1] == ["词"] and seen[0][3] == 1


@need_both
def test_auto_suggestion_on_half_a_common_word_is_not_sure(tmp_path):
    """问题 6：另一个引擎把「结构」里的「构」听成 which，一键校正把它改成了「结which」。"""
    t = "我们来看一下这个句子的结构，它有一个定语从句。"
    cfg, project = _voice(tmp_path, [t], ids=["q_0001"])
    recs = project.load_manifest()
    k = t.index("构")
    recs[0]["suspect"] = {"spans": [[k, k + 1]], "alt": t[:k] + "which" + t[k + 1:], "reasons": ["另一个引擎"], "score": 0.6}
    project.save_manifest(recs)
    res = wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "q_0001")[1] == t and res["adopted"]["changes"] == 0


@need_both
def test_undoing_one_of_two_same_fixes_keeps_the_other_undoable(tmp_path):
    """问题 7：一句里同样的改法有两处（原形 → 原型），老师把第一处打回去：再点以后，第二处（还改着）没有撤销按钮了。"""
    orig = {r["id"]: r["text"] for r in csv.DictReader(open(MOTHER_DIR / "母本_原文.csv", encoding="utf-8-sig"))}
    rid = "0006_9498bb_0104"
    cfg, project = _voice(tmp_path, [orig[rid]], ids=[rid])
    wf.run_transcript_fix(cfg, "校正声音")
    cur = _cur(project, rid)[1]
    assert cur.count("原型") == 2
    review.set_draft(project, rid, text=cur.replace("原型", "原形", 1))
    wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, rid)
    info = review.analyze(rec, cur)
    assert cur.count("原型") == 1 and info["undo"]  # 第二处还能撤销


@need_both
def test_adopting_next_to_a_teacher_change_still_gives_an_undo_button(tmp_path):
    """问题 8：查找替换「我们 → 咱们」以后采用「删掉『们就先』」：没有撤销按钮（挨着老师改过的字）。"""
    t = "那我们就先来分析一下这个定语从句原型的句子成分。"
    cfg, project = _voice(tmp_path, [t], ids=["q_0042"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[2, 5]], "alt": t[:2] + t[5:], "reasons": ["另一个引擎没听到"], "score": 0.6}
    project.save_manifest(recs)
    review.replace_matches(project, "我们", "咱们")
    review.adopt_suggestion(project, "q_0042")
    rec, cur = _cur(project, "q_0042")
    assert review.analyze(rec, cur)["undo"]


# ---------------------------------------------------------------------------- 第五次检查以后随机操作脚本找到的问题
def _mixed_row(tmp_path):
    """一行：有把握的改好了（从具 → 从句、关系带词 → 关系代词），还有一个挨着的没把握的建议（删掉「系」）；
    老师又在别处改过（查找替换 我们 → 咱们）。"""
    orig = "在这个句子里面定语从具的关系带词，我们也使用了which。"
    base = orig.replace("，", "曌")  # 老师先改过的标点
    sure = base.replace("从具", "从句").replace("关系带词", "关系代词")
    alt = sure.replace("关系代词", "关代词")
    cfg, project = _voice(tmp_path, [orig], ids=["0007_d8ade5_0015"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[10, 11], [13, 14], [14, 15]], "alt": alt, "sure_alt": sure, "direct_alt": sure,
                          "text": base, "src": "transcript", "reasons": ["已按标准库改好"], "score": 0.9}
    project.save_manifest(recs)
    review.set_draft(project, "0007_d8ade5_0015", text=sure.replace("我们", "咱们"))
    return project, base, sure, alt


def test_undo_next_to_an_unsure_suggestion_never_garbles_the_text(tmp_path):
    """随机操作找到的：上面那一行点红色「已采用」撤销，变成了「关系系带词」（把没采用的「删掉系」也当成采用过的去撤销）。"""
    project, base, sure, alt = _mixed_row(tmp_path)
    rec, cur = _cur(project, "0007_d8ade5_0015")
    info = review.analyze(rec, cur)
    assert [cur[s:e] + "→" + rep for s, e, rep in info["edits"]] == ["系→"]  # 没采用的那个建议还在（蓝色「采用」）
    assert review.apply_edits(cur, info["undo"]) == base.replace("我们", "咱们")
    out = review.unadopt_suggestion(project, "0007_d8ade5_0015")
    assert out["text"] == base.replace("我们", "咱们")  # 只撤销采用过的两处，老师的「咱们」还在
    out = review.adopt_suggestion(project, "0007_d8ade5_0015")
    assert out["text"] == alt.replace("我们", "咱们")


def test_adopting_the_unsure_part_of_a_mixed_row(tmp_path):
    project, base, sure, alt = _mixed_row(tmp_path)
    out = review.adopt_suggestion(project, "0007_d8ade5_0015")
    assert out["text"] == alt.replace("我们", "咱们")
    out = review.unadopt_suggestion(project, "0007_d8ade5_0015")
    assert out["text"] == base.replace("我们", "咱们")


def test_safe_apply_refuses_results_it_cannot_explain():
    """采用 / 撤销一处一处对位置时，结果必须「改回去又能改回来」：配错位置的结果（关系系带词）一律不用。"""
    base = "定语从具的关系带词我们也用"
    sure = "定语从句的关系代词我们也用"
    alt = "定语从句的关代词我们也用"
    cur = "定语从句的关系代词咱们也用"
    # 只给了错的那一句（alt）：可以不改、可以只撤销没碰到的那一处，但不能改乱
    got = review.safe_apply(cur, [(7, 8, "系带")], alt, base)
    assert got in ("", "定语从具的关系带词咱们也用", "定语从具的关系代词咱们也用") and "系系" not in got
    assert review.safe_apply(cur, [(7, 8, "系带")], [alt, sure], base) == "定语从具的关系带词咱们也用"


@need_both
def test_fixed_text_is_stored_in_the_same_form_as_typed_text(tmp_path):
    """随机操作找到的：一键校正把「艾子，」改成「as，」（全角逗号），老师点「采用」存进去的却是「as,」（表格里的文字都这样整理）：
    整句对不上，采用 / 撤销只能一处一处对位置。现在改出来的、记下的整句都和老师自己改、点「采用」存的一模一样。"""
    t = "接下来我们就学习一下另外一个关键代词，艾子，这个关系代词相对来说比较特殊。"
    cfg, project = _voice(tmp_path, [t], ids=["q_0006"])
    wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, "q_0006")
    assert "as," in cur and "关系代词" in cur and cur == review.clean_transcript(cur)
    assert rec["suspect"]["direct_alt"] == cur
    for _ in range(2):  # 撤销、采用来回点：每次都是整句换，文字只有两种
        out = review.unadopt_suggestion(project, "q_0006")
        assert out["text"] == t == _cur(project, "q_0006")[1]
        out = review.adopt_suggestion(project, "q_0006")
        assert out["text"] == _cur(project, "q_0006")[1] == rec["suspect"]["alt"]
    review.unadopt_suggestion(project, "q_0006")
    wf.run_transcript_fix(cfg, "校正声音")  # 撤销过的不再改回来
    assert _cur(project, "q_0006")[1] == t


def test_parse_mother_lines_are_tidied_like_the_table():
    assert tf.parse_mother("a.txt", "使用which，比如说\n关系代词that，不要省略") == [
        ("", "使用which,比如说"), ("", "关系代词that,不要省略")]


def test_adopt_after_teacher_typed_one_of_the_fixes_gives_the_whole_suggestion():
    """随机操作找到的（修第一版时）：老师自己已经打了建议里的一处（问 → when），再点「采用」只改了一部分。
    三方合并：两边同一处改得一样算一处，别的照样采用。"""
    base = "那我们就需要使用跟时间有关的关系副词问。"
    sure = "那我单单就需要使用跟时间有关的关系副词when。"
    alt = "那我单单就as需要使用跟时间有关的关系副词when。"
    cur = base.replace("问", "when")
    assert review.merge3(base, alt, cur) == alt
    assert review.safe_apply(cur, [], [base, sure], alt) == alt
    assert review.safe_apply(cur, [], [sure, alt], base) == base  # 撤销：回到查错字时的样子


def test_three_way_merge_refuses_when_both_sides_touch_the_same_place():
    src, a, b = "关代词我们", "关系带词我们", "关系代词咱们"  # 两边都在「关」后面加了字：不知道先后
    assert review.merge3(src, a, b) == ""
    assert review.merge3("那我们就先来", "那我来", "那咱们就先来") == "那咱来"  # 只是挨着：照样合


def test_adopt_skips_only_the_suggestion_that_overlaps_the_teachers_change(tmp_path):
    """随机操作找到的：两个建议里有一个和老师改的字（查找替换 我们 → 咱们）碰在一起（表格上不显示它），点「采用」整行都不改。
    现在只跳过碰到的那一个，按钮上写的那一处照样改；再点「已采用」原样撤销。"""
    base = "接下来我们学习一下关系带词that的使用方法。"
    sure = base.replace("带词", "代词")
    alt = sure.replace("下来我", "as")
    cfg, project = _voice(tmp_path, [base], ids=["q_0067"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[1, 4], [11, 12]], "alt": alt, "sure_alt": sure, "text": base, "src": "transcript",
                          "reasons": ["r"], "score": 0.9}
    project.save_manifest(recs)
    review.replace_matches(project, "我们", "咱们")
    rec, cur = _cur(project, "q_0067")
    assert [cur[s:e] + "→" + rep for s, e, rep in review.analyze(rec, cur)["edits"]] == ["带→代"]
    out = review.adopt_suggestion(project, "q_0067")
    assert out["text"] == "接下来咱们学习一下关系代词that的使用方法。"
    out = review.unadopt_suggestion(project, "q_0067")
    assert out["text"] == cur


def test_red_mark_of_an_adopted_insertion_stays_gone_next_to_a_fix():
    """随机操作找到的：自动查错字建议「补上『的』」（标红后面的「它」），老师采用了；字旁边又改过（从具 → 从句）以后，
    「它」又标红了——同一个改动 difflib 有时分成「换 + 插入」、有时合成一个「换」，结果就不一样。"""
    t = "所以说这个从具它没有办法独立存在"
    k = t.index("它")
    rec = {"id": "q", "text": t, "suspect": {"spans": [[k, k + 1]], "alt": t[:k] + "的" + t[k:], "reasons": ["r"], "score": 0.6}}
    for cur in (t[:k] + "的" + t[k:], (t[:k] + "的" + t[k:]).replace("从具", "从句")):
        info = review.analyze(rec, cur)
        assert info["red"] == [] and info["edits"] == [] and info["undo"], cur


@need_both
def test_two_clicks_after_adopting_an_insertion_give_the_same_table(tmp_path):
    t = "必然是要存在于句子里面才可以，所以说这个从具它没有办法独立存在，只能在句子里面才有意义。"
    k = t.index("它")
    cfg, project = _voice(tmp_path, [t], ids=["22222222222_56d51b_0070"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[k, k + 1]], "alt": t[:k] + "的" + t[k:], "reasons": ["自动"], "score": 0.6}
    project.save_manifest(recs)
    review.adopt_suggestion(project, "22222222222_56d51b_0070")
    seen = []
    for _ in range(2):
        wf.run_transcript_fix(cfg, "校正声音")
        rec, cur = _cur(project, "22222222222_56d51b_0070")
        info = review.analyze(rec, cur)
        seen.append((cur, info["red"], info["edits"], bool(info["undo"])))
    assert seen[0] == seen[1] and "从句的它" in seen[0][0] and seen[0][1] == [] and seen[0][3]


@need_both
def test_second_click_with_nothing_changed_keeps_the_same_suggestions(tmp_path):
    """随机操作找到的：自动查错字建议在「从据」后面补上 which，第一次点一键校正（从据 → 从句）建议还在，
    第二次点（什么都没变）建议没了——第二次是从改好的文字算的，挨着改好的字的建议算得不一样。
    现在：上次点完以后什么都没变（母本、自动查错字的结果、撤销记录、文字），结果原样留着。"""
    t = "而且很明显，这个定于从据是属于这个宾语从句里面的一部分。"
    k = t.index("是")
    cfg, project = _voice(tmp_path, [t], ids=["22222222222_56d51b_0058"])
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[k, k + 1]], "alt": t[:k] + "which" + t[k:], "reasons": ["自动"], "score": 0.6}
    project.save_manifest(recs)
    seen = []
    for _ in range(3):
        wf.run_transcript_fix(cfg, "校正声音")
        rec, cur = _cur(project, "22222222222_56d51b_0058")
        info = review.analyze(rec, cur)
        seen.append((cur, info["red"], info["edits"], info["undo"], rec["suspect"]))
    assert seen[0] == seen[1] == seen[2]
    assert "从句是" in seen[0][0] and [rep for _s, _e, rep in seen[0][2]] == ["which"]
    review.save_rows(project)  # 保存以后再点也一样
    wf.run_transcript_fix(cfg, "校正声音")
    rec, cur = _cur(project, "22222222222_56d51b_0058")
    assert review.analyze(rec, cur)["edits"] == seen[0][2]
    review.unadopt_suggestion(project, "22222222222_56d51b_0058")  # 撤销记录变了：重新算，撤销的不再改回来
    wf.run_transcript_fix(cfg, "校正声音")
    assert "从据" in _cur(project, "22222222222_56d51b_0058")[1]


# ---------------------------------------------------------------------------- 第六次独立检查发现的问题（每个都有一个测试）
def _set_suspect(project, rid, sus):
    recs = project.load_manifest()
    for r in recs:
        if r["id"] == rid:
            r["suspect"] = sus
    project.save_manifest(recs)


def test_no_false_undo_button_in_a_run_of_the_same_character(tmp_path):
    """问题 1：另一个引擎听成「看看」（建议补上「看」），老师没有采用，只改了后面的「这 → 那」：表格上多出一个红色的
    「已采用：补上『看』」，点了把老师原来的「看」删掉了。"""
    base = "我们来看这个句子。"
    cfg, project = _voice(tmp_path, [base], ids=["c000"])
    _set_suspect(project, "c000", {"spans": [[3, 4]], "alt": "我们来看看这个句子。", "reasons": ["另一个引擎"], "score": 0.6})
    review.set_draft(project, "c000", text="我们来看那个句子。")
    rec, cur = _cur(project, "c000")
    info = review.analyze(rec, cur)
    assert info["undo"] == [] and [rep for _s, _e, rep in info["edits"]] == ["看"]
    with pytest.raises(ValueError):
        review.unadopt_suggestion(project, "c000")
    assert review.adopt_suggestion(project, "c000")["text"] == "我们来看看那个句子。"


def test_adopted_double_character_is_not_offered_again(tmp_path):
    """问题 1（采用的一面）：采用了「看 → 看看」，又改了旁边的字：又出来「补上『看』」，点了变成「看看看」。"""
    base = "我们来看这个句子。"
    cfg, project = _voice(tmp_path, [base], ids=["c000"])
    _set_suspect(project, "c000", {"spans": [[3, 4]], "alt": "我们来看看这个句子。", "reasons": ["另一个引擎"], "score": 0.6})
    review.adopt_suggestion(project, "c000")
    review.set_draft(project, "c000", text="我们来看看那个句子。")
    rec, cur = _cur(project, "c000")
    info = review.analyze(rec, cur)
    assert info["edits"] == [] and info["undo"]
    assert review.unadopt_suggestion(project, "c000")["text"] == "我们来看那个句子。"


def test_undo_takes_back_everything_the_program_changed(tmp_path):
    """问题 2：老师采用以后自己又改了一处一样的改法（带替 → 代替）：红色撤销只撤了一半（程序改的「带 → 代」留着）。"""
    base = "定语从具的关系带词可以带替先行词。"
    direct = base.replace("从具", "从句")
    alt = direct.replace("关系带词", "关系代词")
    cfg, project = _voice(tmp_path, [base], ids=["c000"])
    _set_suspect(project, "c000", {"spans": [[3, 4], [7, 8]], "alt": alt, "direct_alt": direct, "text": base,
                                   "src": "transcript", "reasons": ["x"], "score": 0.9})
    review.set_draft(project, "c000", text=direct)
    out = review.adopt_suggestion(project, "c000")
    review.set_draft(project, "c000", text=out["text"].replace("带替", "代替"))
    assert review.unadopt_suggestion(project, "c000")["text"] == base.replace("带替", "代替")


def test_undo_with_a_teacher_change_equal_to_an_unsure_one(tmp_path):
    """问题 2：老师自己补了一个「的」，没把握的建议也补了一个「的」：撤销时那个「的」留着。"""
    base = "在这个句子里面定语从具的关系带词也使用了which。"
    direct = base.replace("从具", "从句")
    sure = direct.replace("关系带词", "关系代词")
    alt = sure.replace("也使用", "也的使用")
    cfg, project = _voice(tmp_path, [base], ids=["c000"])
    _set_suspect(project, "c000", {"spans": [[9, 10], [13, 14], [16, 17]], "alt": alt, "sure_alt": sure,
                                   "direct_alt": direct, "text": base, "src": "transcript", "reasons": ["x"], "score": 0.9})
    out = review.adopt_suggestion(project, "c000")
    review.set_draft(project, "c000", text=out["text"].replace("在这个", "在这个的"))
    assert review.unadopt_suggestion(project, "c000")["text"] == base.replace("在这个", "在这个的")


@need_both
@pytest.mark.parametrize("how", ["button", "row", "type_half"])
def test_undo_of_two_touching_fixes_is_remembered(tmp_path, how):
    """问题 3：挨着的两处改法（艾子借词 → as介词）撤销时记成了一处，下次分开改就认不出来，又改回去了。"""
    t = "我们来看一下艾子借词的用法和例句。"
    cfg, project = _voice(tmp_path, [t], ids=["c000"])
    wf.run_transcript_fix(cfg, "校正声音")
    cur = _cur(project, "c000")[1]
    assert "as介词" in cur
    if how == "button":
        review.unadopt_suggestion(project, "c000")
    elif how == "row":
        review.discard_draft(project, "c000")
    else:
        review.set_draft(project, "c000", text=cur.replace("as介词", "艾子介词"))  # 只改回一处
    before = _cur(project, "c000")[1]
    wf.run_transcript_fix(cfg, "校正声音")
    assert _cur(project, "c000")[1] == before


def test_red_mark_next_to_a_teacher_change_stays(tmp_path):
    """问题 4：老师把「威驰」后面的「的」改成「这个」：威驰 → which 的标红和建议都没了（修第一版时把挨着的改动算成碰到了）。"""
    base = "这里的关系代词威驰的用法和that不一样。"
    cfg, project = _voice(tmp_path, [base], ids=["c000"])
    _set_suspect(project, "c000", {"spans": [[7, 9]], "alt": base.replace("威驰", "which"), "reasons": ["另一个引擎"],
                                   "score": 0.6})
    review.set_draft(project, "c000", text=base.replace("威驰的", "威驰这个"))
    rec, cur = _cur(project, "c000")
    info = review.analyze(rec, cur)
    assert [cur[s:e] for s, e in info["red"]] == ["威驰"] and [rep for _s, _e, rep in info["edits"]] == ["which"]


def test_safe_apply_result_is_always_on_the_shortest_path():
    """采用 / 撤销的结果必须在「现在的文字 → 目标」的最短路上：多改、改错地方都不行。"""
    assert review.safe_apply("我们来看那个句子。", [(3, 4, "")], ["我们来看看这个句子。"], "我们来看这个句子。") == ""
    assert review.safe_apply("我们来看看那个句子。", [(3, 3, "看")], ["我们来看这个句子。"], "我们来看看这个句子。") == ""


# ---------------------------------------------------------------------------- 一键全部文字校正每批素材只能用一次（老师 10-03 的要求）
def _add_rows(project, rows):
    """像加了新素材（准备素材识别出新的句子）一样，往校对表里加几句。"""
    recs = project.load_manifest()
    recs += [{"id": i, "path": f"clips/{i}.wav", "text": t, "lang": "zh", "duration": 3.0, "keep": True, "split": "train"}
             for i, t in rows]
    project.save_manifest(recs)


@need_both
def test_one_click_once_per_batch_of_material(tmp_path):
    """网页上的按钮（once=True）：每批素材只能用一次；加了新素材以后又能用一次，只改新加的句子，以前的句子一点不动；
    测试 / 命令行（once=False）不受影响。"""
    cfg, project = _voice(tmp_path, ["我们先来看艾子引导的定语从句。", "关系代词that不能和借词一起提前。"],
                          ids=["a1", "a2"])
    assert not wf.textfix_used(cfg, "校正声音")
    res = wf.run_transcript_fix(cfg, "校正声音", once=True)
    assert wf.textfix_used(cfg, "校正声音") and res["only"] == 2
    assert "as" in _cur(project, "a1")[1] and "介词" in _cur(project, "a2")[1]
    with pytest.raises(ValueError, match="每批素材只能用一次"):
        wf.run_transcript_fix(cfg, "校正声音", once=True)
    # 老师把第一句改回去（不保存）、第二句保存了：再加新素材
    review.set_draft(project, "a1", text="我们先来看艾子引导的定语从句。")
    review.save_rows(project, ["a2"])
    before = {k: _cur(project, k) for k in ("a1", "a2")}
    _add_rows(project, [("b1", "这里的借词后面要接宾语。")])
    assert not wf.textfix_used(cfg, "校正声音")  # 有新的句子：按钮又亮了
    res = wf.run_transcript_fix(cfg, "校正声音", once=True)
    assert res["only"] == 1 and res["checked"] == 1
    assert "介词" in _cur(project, "b1")[1]  # 新加的句子改好了
    for k in ("a1", "a2"):  # 以前的句子一点没动（文字、标记都一样）
        assert _cur(project, k) == before[k]
    assert wf.textfix_used(cfg, "校正声音")
    wf.run_transcript_fix(cfg, "校正声音")  # 不是按钮（once=False）：照样能做
    assert not wf.textfix_used(cfg, "还没有的声音")


def test_failed_one_click_does_not_count_as_used(tmp_path, monkeypatch):
    cfg, project = _voice(tmp_path, ["我们先来看艾子引导的定语从句。"])

    def boom(*a, **kw):
        raise RuntimeError("中途出错")

    monkeypatch.setattr(tf, "check_with_transcript", boom)
    with pytest.raises(RuntimeError):
        wf.run_transcript_fix(cfg, "校正声音", once=True)
    assert not wf.textfix_used(cfg, "校正声音")  # 出错的不算用过，可以再点


def test_deleted_new_rows_do_not_light_the_button_again(tmp_path):
    cfg, project = _voice(tmp_path, ["我们先来看艾子引导的定语从句。"])
    wf.run_transcript_fix(cfg, "校正声音", once=True)
    _add_rows(project, [("x1", "删掉的一句")])
    recs = project.load_manifest()
    recs[-1]["deleted"] = True
    project.save_manifest(recs)
    assert wf.textfix_used(cfg, "校正声音")  # 只多了删除（紫色）的句子：不算新素材


def test_broken_used_file_counts_as_used_but_new_material_still_works(tmp_path):
    cfg, project = _voice(tmp_path, ["我们先来看艾子引导的定语从句。"])
    (project.root / tf.USED_FILE).write_text("{坏了", encoding="utf-8")
    assert wf.textfix_used(cfg, "校正声音")  # 宁可不改，也不重复改
    _add_rows(project, [("n1", "这里的借词后面要接宾语。")])
    assert tf.textfix_new_ids(project) == ["n1"]  # 记录重新记了一份：新加的素材照样认得出来


def test_one_click_never_touches_what_the_teacher_already_changed(tmp_path):
    """用一键全部文字校正以前，老师自己改过的字不动；同一句里别的错字照样改。"""
    if not (HAS_PINYIN and HAS_JIEBA):
        pytest.skip("没有装 pypinyin / jieba（整合包里有）")
    t = "我们先来看艾子引导的定语从剧和借词。"
    cfg, project = _voice(tmp_path, [t], ids=["q1"])
    review.set_draft(project, "q1", text=t.replace("借词", "接词"))  # 老师自己把「借词」改成了「接词」（不管对不对）
    wf.run_transcript_fix(cfg, "校正声音", once=True)
    cur = _cur(project, "q1")[1]
    assert "接词" in cur and "as" in cur and "定语从句" in cur


def test_webui_button_turns_gray_after_use_and_lights_again_for_new_material(tmp_path):
    pytest.importorskip("gradio")
    from voicetwin.webui import app as A

    cfg, project = _voice(tmp_path, ["我们先来看艾子引导的定语从句。"])
    ui = A.WebUI(cfg)
    O = ui.TEXTFIX_OUT
    assert ui.textfix_btn("校正声音")["interactive"] is True
    outs = list(ui.do_textfix("校正声音"))
    last = dict(zip(O, outs[-1]))
    assert last["tr_btn"]["interactive"] is False  # 用完变灰
    assert "每批素材只能用一次" in last["tr_info"] and "新的素材" in last["tr_info"]
    assert ui.textfix_btn("校正声音")["interactive"] is False  # 刷新网页 / 换声音回来也是灰的
    draft_before = review.load_draft(project)
    outs = list(ui.do_textfix("校正声音"))  # 灰的时候（旧网页上还能点）也不会再做一次
    again = dict(zip(O, outs[-1]))
    assert "每批素材只能用一次" in again["proof_bar"] and again["tr_btn"]["interactive"] is False
    assert review.load_draft(project) == draft_before
    _add_rows(project, [("n1", "这里的借词后面要接宾语。")])
    assert ui.textfix_btn("校正声音")["interactive"] is True  # 加了新素材：又能用一次
    assert "只能用一次" not in ui.textfix_info("校正声音")
