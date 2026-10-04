"""R6 查找可能的错字（voicetwin/data/proofcheck.py）。不需要任何识别模型：识别引擎一律用假的代替。"""

import re
import sys
import types

import numpy as np
import pytest
import soundfile as sf

from voicetwin.data import proofcheck as pc
from voicetwin.project import Project

from conftest import make_cfg

RED = '<span style="color:#dc2626;font-weight:700;background:#fee2e2">'


# ---------------------------------------------------------------------------- 切字（位置要对得回原文）
def test_tokenize_offsets_point_into_original_text():
    text = "我們今天講ＶＦＩＸＥＤ的用法，2024年有50%的人用GPT4、don’t worry！"
    toks = pc.tokenize(text)
    assert toks
    for t in toks:
        assert 0 <= t.start < t.end <= len(text)
        assert text[t.start:t.end].strip()
    keys = [t.key for t in toks]
    assert keys[:5] == ["我", "们", "今", "天", "讲"]  # 繁体 → 简体（没装 zhconv 也行）
    assert "vfixed" in keys  # 全角字母 → 半角小写
    assert text[toks[keys.index("vfixed")].start:toks[keys.index("vfixed")].end] == "ＶＦＩＸＥＤ"
    assert "dont" in keys and "worry" in keys  # 撇号不影响
    i = keys.index("gpt")
    assert keys[i + 1] == "#"  # GPT4 = GPT 4
    assert "，" not in keys and "！" not in keys


def test_tokenize_drops_punctuation_and_spacing():
    assert [t.key for t in pc.tokenize("你好，世界！ Hello,  World.")] == [t.key for t in pc.tokenize("你好世界hello world")]


@pytest.mark.parametrize("a,b", [
    ("2024年", "二零二四年"),
    ("2024年", "两千零二十四年"),
    ("50%的人", "百分之五十的人"),
    ("3.5倍", "三点五倍"),
    ("1/3的", "三分之一的"),
    ("1,000元", "一千元"),
    ("350元", "三百五元"),
    ("15000元", "一万五元"),
    ("第15章", "第十五章"),
    ("105个", "一百零五个"),
    ("3万人", "三万人"),
    ("1+1=2", "一加一等于二"),
])
def test_number_and_symbol_spellings_compare_equal(a, b):
    ta, tb = pc.tokenize(a), pc.tokenize(b)
    assert [t.key for t in ta] == [t.key for t in tb]
    for x, y in zip(ta, tb):
        assert pc._num_equal(x.val, y.val), (x, y)


def test_number_values_that_differ_are_seen():
    assert not pc._num_equal(pc.tokenize("30个")[0].val, pc.tokenize("四十个")[0].val)
    assert not pc._num_equal(pc.tokenize("50%")[0].val, pc.tokenize("五十")[0].val)  # 少了"百分之"
    assert pc._num_equal(None, "3")  # 看不懂的不乱报


def test_merge_spans():
    assert pc.merge_spans([[5, 7], [1, 3], [2, 4], [9, 9], "x", None, [8, "a"]]) == [[1, 4], [5, 7]]
    text = "AB CD，EF"
    assert pc.merge_spans([[0, 2], [3, 5], [6, 8]], text) == [[0, 5], [6, 8]]  # 只隔空格的合并，隔标点的不合并
    assert pc.merge_spans([[-3, 2], [7, 100]], text) == [[0, 2], [7, 8]]  # 限制在文字范围内


# ---------------------------------------------------------------------------- 规则（不需要模型）
def _hits(text, **kw):
    return [(text[e.start:e.end], e.kind, e.weight) for e in pc.heuristics(text, **kw)]


@pytest.mark.parametrize("word", ["VFIXED", "WHOOZ", "WINDOW"])
def test_heuristics_flag_all_caps_gibberish(word):
    text = f"我们今天讲{word}的用法，这个很常用。"
    hits = _hits(text)
    assert (word, "caps", pc.W_CAPS) in hits


@pytest.mark.parametrize("text", [
    "我们今天讲VLOOKUP和SUMIF两个函数。",
    "把模型放到GPU上，再打开PPT。",
    "第III部分我们讲第IV章。",
    "这台电脑用的是RTX4090和GPT4。",
    "我们用iPhone和YouTube看视频。",
    "看看这个，试试那个，慢慢来。",
    "对对对，就是这样，好好好。",
    "哈哈哈，大家别紧张。",
    "嗯嗯嗯，我们继续。",
    "这个这个问题很简单。",
])
def test_heuristics_leave_normal_text_alone(text):
    assert _hits(text) == []


def test_heuristics_lexicon_terms_and_frequent_caps():
    text = "今天我们用ZOTERO管理文献。"
    assert _hits(text) and _hits(text)[0][1] == "caps"
    assert _hits(text, known_terms=["Zotero"]) == []
    freq = _hits(text, frequent=["ZOTERO"])
    assert freq == [("ZOTERO", "caps", pc.W_CAPS_FREQ)]  # 常见词：只算弱证据
    assert pc.build_suspect(text, frequent=["ZOTERO"]) is None


def test_heuristics_confusable_english_inside_chinese():
    assert ("whose", "confusable", pc.W_CONFUSABLE) in _hits("这个户字的意思是whose，大家记一下。")
    assert ("the", "confusable", pc.W_CONFUSABLE) in _hits("大家好，今天天气不错 the 我们开始上课。")
    assert _hits("我们说 so far so good 的意思。") == []  # 在英文短语里：不管
    assert _hits("so我们开始吧。") == [("so", "confusable", pc.W_CONFUSABLE_SOFT)]  # 顺口说的 so：弱证据


def test_heuristics_garbage_foreign_and_english_clips():
    assert ("wHoOz", "garbage", pc.W_GARBAGE) in _hits("我们用wHoOz来做。")
    assert ("xkcdq", "garbage", pc.W_GARBAGE) in _hits("这个是xkcdq的问题。")
    assert ("カタカナ", "script", pc.W_SCRIPT) in _hits("这里有カタカナ。")
    assert any(k == "script" for _w, k, _ in _hits("这里有乱码" + chr(0xFFFD) + "了。"))
    assert _hits("We will use VFIXED and WHOOZ here.", lang="en") == []  # 英文片段不查大写


def test_heuristics_repeated_phrases_mark_the_repeat_not_the_first():
    text = "我们来看一下我们来看一下这个公式。"
    hits = _hits(text)
    assert hits == [("我们来看一下", "repeat", pc.W_REPEAT_LONG)]
    ev = pc.heuristics(text)[0]
    assert (ev.start, ev.end) == (6, 12)
    assert _hits("我们我们我们开始上课。") == [("我们我们", "repeat", pc.W_REPEAT)]
    # 中间隔着标点、只说两遍：可能是故意强调，只算弱证据
    assert _hits("大家注意一下，大家注意一下。") == [("大家注意一下", "repeat", pc.W_REPEAT_PUNCT)]
    assert pc.build_suspect("大家注意一下，大家注意一下。") is None


def test_phrases_that_differ_only_in_a_number_are_not_repeats():
    """第四轮找 bug：「第一种情况第二种情况」「三月三号三月四号」以前标红，说「「第一种情况」连着重复了 2 遍」。"""
    for t in ("那么第一种情况第二种情况我们分别来看", "三月三号三月四号我们考试", "第一个例句第二个例句都是定语从句",
              "第一个空第二个空第三个空都填介词", "第三种用法，第四种用法"):
        assert _hits(t) == [], t
        assert pc.build_suspect(t) is None, t
    # 真的重复照样标（数字一样，写法不一样也算）
    assert _hits("第一种情况第一种情况我们分别来看") == [("第一种情况", "repeat", pc.W_REPEAT_LONG)]
    assert _hits("第1种情况第一种情况我们分别来看") == [("第一种情况", "repeat", pc.W_REPEAT_LONG)]


def test_reason_positions_are_only_used_while_checking():
    """查错字时带上每条原因的位置（去掉标红 / 建议时说明也跟着去掉），存进校对表的和以前一样（原因太多照样截短）。
    母本优先第二轮：另外按原因记下位置（REASON_AT，「……还有 N 处」那一条是剩下的合在一起），和母本对照时
    原因说的地方都在母本对上的部分里就去掉（另一个引擎的字在这一句里找不到，以前看引用的字去不掉）。"""
    t = "我们看第三页、第五页、第七页、第九页、第十一页、第十三页、第十五页和第十七页的练习"
    o = "我们看第四页、第六页、第八页、第十页、第十二页、第十四页、第十六页和第十八页的练习"
    plain = pc.build_suspect(t, o, engine=pc.ENGINE_FUNASR)
    assert plain["reasons"][-1].startswith("……还有")
    done = pc._finish_reasons(pc.build_suspect(t, o, engine=pc.ENGINE_FUNASR, with_pos=True))
    at = done.pop(pc.REASON_AT)
    assert done == plain and pc.REASON_POS not in done
    assert set(at) == set(plain["reasons"]) and len(at[plain["reasons"][-1]]) > 1


# ---------------------------------------------------------------------------- 两个引擎对比
def test_spacing_only_difference_is_ignored_but_heuristic_still_flags():
    text = "我们今天讲VFIXED的用法，这个函数很常用。"
    sus = pc.build_suspect(text, "我们今天讲 v fixed 的用法这个函数很常用", engine=pc.ENGINE_FUNASR)
    assert sus["spans"] == [[5, 11]] and text[5:11] == "VFIXED"
    assert sus["alt"] == ""  # 另一个引擎听到的一样：没有建议


def test_vfixed_whooz_window_merged_and_replaced_by_second_engine():
    text = "我们打开VFIXED WHOOZ WINDOW这个菜单。"
    only_rules = pc.build_suspect(text)
    assert only_rules["spans"] == [[4, 23]] and text[4:23] == "VFIXED WHOOZ WINDOW"
    assert len(only_rules["reasons"]) == 3 and only_rules["alt"] == ""
    sus = pc.build_suspect(text, "我们打开微费克斯户字温度这个菜单", engine=pc.ENGINE_FUNASR)
    assert sus["spans"] == [[4, 23]]
    assert sus["alt"] == "我们打开微费克斯户字温度这个菜单。"


def test_whose_becomes_hu_zi_suggestion():
    text = "这个户字的意思是whose，大家记一下。"
    sus = pc.build_suspect(text, "这 个 户 字 的 意 思 是 户 字 大 家 记 一 下", engine=pc.ENGINE_FUNASR)
    assert sus["spans"] == [[8, 13]] and text[8:13] == "whose"
    assert sus["alt"] == "这个户字的意思是户字，大家记一下。"  # 保留原来的标点
    assert sus["score"] >= pc.FLAG_THRESHOLD
    assert set(sus) == {"spans", "alt", "reasons", "score"}


def test_the_becomes_de():
    sus = pc.build_suspect("大家好，今天天气不错 the 我们开始上课。", "大家好今天天气不错的我们开始上课")
    assert sus["alt"] == "大家好，今天天气不错的我们开始上课。"


@pytest.mark.parametrize("a,b", [
    ("2024年我们讲了50%的内容。", "二零二四年我们讲了百分之五十的内容"),
    ("那个，我们打开Python的设置页面。", "嗯那个我们打开派森的设置页面"),  # 语气词 + FunASR 的英文音译
    ("他说的在理，我们再看一下。", "她说得在理我们在看一下"),  # 同音字
    ("我们今天讲 VLOOKUP 和 SUMIF 两个函数，在 Excel 里很常用。", "我们今天讲vlookup和sumif两个函数在excel里很常用"),
    ("我們用ＰＰＴ做課件，好嗎？", "我们用ppt做课件好吗"),  # 繁简体 + 全角 + 标点
    ("一加一等于二，对吧。", "1+1=2，对吧。"),
    ("第3章讲3.5和1,000还有1/3。", "第三章讲三点五和一千还有三分之一"),
    ("所以，我们要注意：这个地方很重要！", "所以我们要注意这个地方很重要"),
    ("嗯，那我们现在开始。", "那我们现在开始"),
    ("我们吃了饭再说。", "我们吃饭再说"),  # 只差一个"了"：太弱，不标
])
def test_formatting_differences_are_not_flagged(a, b):
    assert pc.build_suspect(a, b, engine=pc.ENGINE_FUNASR) is None


def test_real_differences_are_flagged_with_suggestion():
    sus = pc.build_suspect("我们今天讲十个函数。", "我们今天讲是个函数")
    assert sus["spans"] == [[5, 6]] and sus["alt"] == "我们今天讲是个函数。"
    sus = pc.build_suspect("我们讲了30个例子。", "我们讲了四十个例子")
    assert sus["spans"] == [[4, 6]] and sus["alt"] == "我们讲了四十个例子。"
    assert any("数字" in r for r in sus["reasons"])
    sus = pc.build_suspect("我们今天讲列表式。", "我们今天讲列表推导式")  # 漏了字：标出缺字位置两边
    assert sus["spans"] == [[6, 8]] and sus["alt"] == "我们今天讲列表推导式。"
    assert "推导" in sus["reasons"][0]
    sus = pc.build_suspect("我们今天讲列表推导式和。", "我们今天讲列表推导式")
    assert sus["spans"] == [[10, 11]] and sus["alt"] == "我们今天讲列表推导式。"


def test_repeated_phrase_with_second_engine():
    text = "我们来看一下我们来看一下这个公式。"
    sus = pc.build_suspect(text, "我们来看一下这个公式")
    assert sus["spans"] == [[6, 12]]
    assert sus["alt"] == "我们来看一下这个公式。"


def test_total_mismatch_and_silence():
    sus = pc.build_suspect("完全不相关的一句话。", "今天天气很好我们出去玩")
    assert sus["spans"] == [[0, 9]] and sus["alt"] == "今天天气很好我们出去玩。"
    assert "差别很大" in sus["reasons"][0]
    short = pc.build_suspect("我们今天讲的是列表推导式的用法。", "好的")
    assert short["alt"] == ""  # 只听清一小部分：不给整句建议
    silent = pc.build_suspect("我们今天讲列表推导式。", "")
    assert silent["spans"] == [[0, 10]] and silent["alt"] == ""


def test_engine_specific_trust_in_english():
    # FunASR 的英文不可靠：英文拼法不同不单独标红，也不拿它的英文当建议
    assert pc.build_suspect("我们打开Excel表格。", "我们打开excell表格", engine=pc.ENGINE_FUNASR) is None
    # faster-whisper 能拼英文：FunASR 写成音译时，建议用 Whisper 的英文
    sus = pc.build_suspect("我们打开一克赛欧表格。", "我们打开Excel表格。", engine=pc.ENGINE_WHISPER)
    assert sus["alt"] == "我们打开Excel表格。"
    # 但 Whisper 把中文听成 whose / the：多半是它自己听错，不标
    assert pc.build_suspect("这个户字很难写。", "这个whose很难写", engine=pc.ENGINE_WHISPER) is None


def test_stutter_and_erhua_are_only_weak_evidence():
    # Whisper 常把口误重复、儿化音省掉：不单独标红
    assert pc.build_suspect("我们来看这个例子。", "我们我们来看这个例子") is None
    assert pc.build_suspect("我们休息一会。", "我们休息一会儿") is None
    assert pc.build_suspect("选A选项，然后看X轴。", "选a选项然后看x轴") is None
    # 但真漏了词还是要标
    assert pc.build_suspect("我们来看这个例子。", "我们来看一下这个例子") is not None


def test_works_without_the_progress_module(monkeypatch):
    import importlib.util

    monkeypatch.setitem(sys.modules, "voicetwin.utils.progress", None)  # 单独合并本单元时的样子
    spec = importlib.util.spec_from_file_location("proofcheck_without_u1", pc.__file__)
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "proofcheck_without_u1", mod)
    spec.loader.exec_module(mod)
    assert mod._check_cancel() is None
    assert mod.build_suspect("我们今天讲VFIXED的用法。")["spans"] == [[5, 11]]


def test_srt_text_and_low_logprob_weights():
    s1 = pc.build_suspect("我们今天讲十个函数。", "我们今天讲是个函数", srt=True)
    assert s1["score"] == pc.W_DIFF_SRT
    s2 = pc.build_suspect("我们今天讲十个函数。", "我们今天讲是个函数", avg_logprob=-0.8)
    assert s2["score"] > 0.6


# ---------------------------------------------------------------------------- faster-whisper 逐词把握程度
class _Word:
    def __init__(self, w, p):
        self.word, self.probability, self.start, self.end = w, p, 0.0, 0.0


def _words():
    return [_Word("我們", .98), _Word("今天", .97), _Word("講", .9), _Word(" V", .2), _Word("FIX", .25), _Word("ED", .3),
            _Word("的", .9), _Word("用法", .95), _Word("，", .9), _Word("這個", .96), _Word("函數", .4), _Word("很", .99),
            _Word("常用。", .97)]


def test_low_prob_words_map_onto_text_through_traditional_and_split_latin():
    text = "我们今天讲VFIXED的用法，这个函数很常用。"
    spans = pc.low_prob_spans(text, _words())
    assert [(text[s:e], round(p, 2)) for s, e, p in spans] == [("VFIXED", 0.2), ("函数", 0.4)]
    # dict 和 (词, 概率) 两种写法也认
    as_dicts = [{"word": w.word, "probability": w.probability} for w in _words()]
    assert pc.low_prob_spans(text, as_dicts) == spans
    assert pc.low_prob_spans(text, [(w.word, w.probability) for w in _words()]) == spans


def test_low_prob_words_alone_decide_by_strength():
    text = "我们今天讲列表推导式。"
    weak = [("我们今天讲列表", 0.9), ("推导", 0.4), ("式。", 0.9)]
    assert pc.build_suspect(text, None, weak, engine=pc.ENGINE_WHISPER_WORDS) is None  # 一个 0.4：不标
    strong = [("我们今天讲列表", 0.9), ("推导", 0.2), ("式。", 0.9)]
    sus = pc.build_suspect(text, None, strong, engine=pc.ENGINE_WHISPER_WORDS)
    assert sus["spans"] == [[7, 9]] and sus["alt"] == ""
    # 同一个引擎重新听一遍（words 模式）时，不拿它的文字做对比
    assert pc.build_suspect(text, "完全不同的话", weak, engine=pc.ENGINE_WHISPER_WORDS) is None


# ---------------------------------------------------------------------------- 显示
def test_render_marked_escapes_and_wraps():
    text = "1. 首先 *打开* <b>x</b> $$y$$ it's & co_1"
    out = pc.render_marked(text, [[6, 8], [7, 9]])
    assert out.count(RED) == 1 and out.count("</span>") == 1
    bare = out.replace(RED, "").replace("</span>", "")
    for ch in "<>*_$":
        assert ch not in bare, ch
    assert "1&#46;" in bare and "&amp;" in bare
    assert pc.render_marked(text, []) == pc._esc(text) == pc.render_marked(text, None)
    assert pc.render_marked(text, [["a", 1], [99, 120], [3, 2]]) == pc._esc(text)  # 无效的位置忽略
    assert pc.render_marked("<img src=x onerror=alert(1)>", [[0, 4]]).count("<img") == 0
    assert pc.render_marked("我们今天讲VFIXED的用法", [[5, 11]]) == "我们今天讲" + RED + "VFIXED</span>的用法"
    assert pc.render_plain("我们今天讲VFIXED的用法", [[5, 11]]) == "我们今天讲【VFIXED】的用法"


def test_render_diff_html_highlights_only_real_differences():
    out = pc.render_diff_html("我们今天讲十个函数。", "我们今天讲是个函数。")
    assert "识别 A" in out and "识别 B" in out
    assert RED + "十</span>" in out and pc.GREEN_SPAN + "是</span>" in out
    same = pc.render_diff_html("我們用ＰＰＴ，好嗎？", "我们用PPT好吗")
    assert RED not in same and pc.GREEN_SPAN not in same  # 繁简体、全角、标点不同不标
    none = pc.render_diff_html("我们今天讲VFIXED的用法。", "", [[5, 11]])
    assert RED + "VFIXED</span>" in none and "没有建议" in none
    evil = pc.render_diff_html("<script>x</script>", "<b>y</b>")
    assert "<script>" not in evil and "<b>" not in evil


# ---------------------------------------------------------------------------- 选哪个引擎
@pytest.fixture
def installed(monkeypatch):
    mods = set()
    monkeypatch.setattr(pc, "_has", lambda m: m in mods)
    return mods


def test_available_checker_prefers_a_second_engine(installed):
    installed.update({"funasr", "modelscope", "torch", "faster_whisper"})
    assert pc.available_checker({"prepare": {"asr": {"engine": "faster-whisper"}}})[0] == "funasr"
    assert pc.available_checker({"prepare": {"asr": {"engine": "funasr"}}})[0] == "faster-whisper"
    assert pc.available_checker({"prepare": {"asr": {"engine": "none"}}})[0] == "funasr"
    assert pc.available_checker(make_cfg(".", prepare={"asr": {"engine": "faster-whisper"}}))[0] == "funasr"
    installed.clear()
    installed.add("faster_whisper")
    name, reason = pc.available_checker({"prepare": {"asr": {"engine": "faster-whisper"}}})
    assert name == "faster-whisper-words" and "没把握" in reason
    assert pc.available_checker({"prepare": {"asr": {"engine": "none"}}})[0] == "faster-whisper"
    installed.clear()
    installed.update({"funasr", "modelscope", "torch"})
    assert pc.available_checker({"prepare": {"asr": {"engine": "funasr"}}})[0] == ""  # 同一个引擎再听一遍没有意义
    installed.clear()
    name, reason = pc.available_checker({"prepare": {"asr": {"engine": "faster-whisper"}}})
    assert name == "" and "规则" in reason
    assert pc.available_checker(None)[0] == ""


def test_available_checker_respects_override(installed):
    installed.update({"funasr", "modelscope", "torch", "faster_whisper"})
    assert pc.available_checker({"prepare": {"proofcheck_engine": "rules"}})[0] == ""
    assert pc.available_checker({"prepare": {"proofcheck_engine": "faster-whisper"}})[0] == "faster-whisper-words"


def test_paraformer_path_prefers_local_copy(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELSCOPE_CACHE", str(tmp_path / "ms"))
    cfg = {"backends": {"gptsovits": {"root": str(tmp_path / "gsv")}}}
    assert pc.paraformer_path(cfg) == "paraformer-zh"
    local = tmp_path / "gsv" / pc.PARAFORMER_LOCAL
    local.mkdir(parents=True)
    (local / "configuration.json").write_text("{}", encoding="utf-8")
    assert pc.paraformer_path(cfg) == str(local)


def test_funasr_checker_loads_lazily_with_offline_friendly_options(tmp_path, monkeypatch):
    calls = {}

    class AutoModel:
        def __init__(self, **kw):
            calls["kw"] = kw

        def generate(self, input):
            calls["input"] = input
            return [{"key": "x", "text": "我 们 今 天"}]

    monkeypatch.setitem(sys.modules, "funasr", types.SimpleNamespace(AutoModel=AutoModel))
    local = tmp_path / "gsv" / pc.PARAFORMER_LOCAL
    local.mkdir(parents=True)
    (local / "configuration.json").write_text("{}", encoding="utf-8")
    ck = pc._make_checker("funasr", {"backends": {"gptsovits": {"root": str(tmp_path / "gsv")}},
                                     "prepare": {"asr": {"device": "cpu"}}})
    assert ck.diff and calls == {}  # 创建时不加载
    assert ck.applies({"lang": "zh", "text": "你好"}) and not ck.applies({"lang": "en", "text": "hello"})
    ck.load()
    kw = calls["kw"]
    assert kw["model"] == str(local) and kw["device"] == "cpu" and kw["check_latest"] is False
    assert kw["disable_update"] is True and kw["disable_pbar"] is True and kw["log_level"] == "ERROR"
    assert "vad_model" not in kw and "punc_model" not in kw and "model_revision" not in kw
    text, words = ck.recognize(np.zeros(16000, dtype=np.float32), "zh")
    assert text == "我 们 今 天" and words is None
    ck.close()


def test_whisper_checker_requests_word_probabilities(monkeypatch):
    seen = {}

    class Seg:
        text = "我們今天"
        words = [_Word("我們", 0.9), _Word("今天", 0.2)]

    class WhisperModel:
        def __init__(self, name, device="cpu", compute_type="int8"):
            seen["model"] = name

        def transcribe(self, wav, **kw):
            seen["kw"] = kw
            return iter([Seg()]), None

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=WhisperModel))
    ck = pc._make_checker("faster-whisper", {"prepare": {"asr": {"engine": "funasr", "model": "paraformer-zh",
                                                                  "device": "cpu"}}})
    ck.load()
    assert seen["model"] == "large-v3"  # 主识别是 FunASR 时，模型名换成 Whisper 的
    text, words = ck.recognize(np.zeros(16000, dtype=np.float32), "zh")
    assert seen["kw"]["word_timestamps"] is True and seen["kw"]["language"] == "zh"
    assert text == "我們今天" and words == [("我們", 0.9), ("今天", 0.2)]


# ---------------------------------------------------------------------------- 整个流程（假的识别引擎）
def _project(tmp_path, rows, engine="none"):
    cfg = make_cfg(tmp_path / "ws", prepare={"asr": {"engine": engine}})
    project = Project(cfg, "查错字").ensure()
    recs = []
    for i, row in enumerate(rows):
        rel = f"clips/c_{i:04d}.wav"
        sf.write(str(project.root / rel), np.zeros(1600 + i, dtype=np.float32), 16000)
        rec = {"id": f"c_{i:04d}", "path": rel, "lang": "zh", "keep": True, "duration": 0.1, "split": "train"}
        rec.update(row)
        recs.append(rec)
    project.save_manifest(recs)
    return cfg, project


class FakeChecker:
    def __init__(self, name, answers=None, words=None, fail=(), load_error=None, log=None):
        self.name = name
        self.label = f"假的{name}"
        self.diff = name != pc.ENGINE_WHISPER_WORDS
        self.model_id = "fake-1"
        self.answers, self.words, self.fail, self.load_error = answers or {}, words or {}, set(fail), load_error
        self.log = log if log is not None else []

    def applies(self, rec):
        return self.name != pc.ENGINE_FUNASR or rec.get("lang") == "zh"

    def load(self):
        self.log.append(("load", self.name))
        if self.load_error:
            raise self.load_error

    def recognize(self, wav, lang):
        cid = wav  # 测试里 _load_wav16 直接返回片段 id
        self.log.append(("recognize", self.name, cid))
        if cid in self.fail or "*" in self.fail:
            raise RuntimeError("识别出错了")
        return self.answers.get(cid, ""), self.words.get(cid)

    def close(self):
        self.log.append(("close", self.name))


@pytest.fixture
def fake_engines(monkeypatch, installed):
    made = {}
    log = []

    def factory(name, cfg):
        spec = made.get(name, {})
        return FakeChecker(name, log=log, **spec)

    monkeypatch.setattr(pc, "_make_checker", factory)
    monkeypatch.setattr(pc, "_load_wav16", lambda project, rec: rec["id"])
    return types.SimpleNamespace(specs=made, log=log, installed=installed)


class Progress:
    def __init__(self):
        self.calls = []

    def __call__(self, frac, msg):
        self.calls.append((frac, msg))


ROWS = [
    {"text": "我们今天讲VFIXED的用法。"},
    {"text": "这本书的意思是shoe，大家记一下。"},  # shoe：老师的母本里没有这个词（whose 有，见下面的测试）
    {"text": "我们今天讲十个函数。", "suspect": {"spans": [[0, 1]], "alt": "旧的", "reasons": ["旧"], "score": 0.9}},
    {"text": "这一段完全没有问题。", "suspect": {"spans": [[0, 1]], "alt": "", "reasons": ["旧"], "score": 0.9}},
    {"text": "We will use VFIXED here.", "lang": "en"},
    {"text": "不保留的片段VFIXED。", "keep": False},
    {"text": ""},
]
ANSWERS = {"c_0000": "我们今天讲v fixed的用法", "c_0001": "这本书的意思是书大家记一下", "c_0002": "我们今天讲是个函数",
           "c_0003": "这一段完全没有问题"}


def test_find_suspects_rules_only_without_any_engine(tmp_path, fake_engines):
    cfg, project = _project(tmp_path, ROWS)
    prog = Progress()
    res = pc.find_suspects(project, cfg, progress=prog)
    assert res["engine"] == "" and res["checked"] == 5 and res["errors"] == 0
    assert set(res) >= {"checked", "flagged", "engine", "note"} and "规则" in res["note"]
    recs = {r["id"]: r for r in project.load_manifest()}  # 已经存进 manifest
    assert recs["c_0000"]["suspect"]["spans"] == [[5, 11]]
    assert recs["c_0001"]["suspect"]["alt"] == ""  # 没有第二个引擎：只标红、没有建议
    assert "suspect" not in recs["c_0002"]  # 规则看不出"十/是"：旧的标记去掉
    assert "suspect" not in recs["c_0003"]
    assert "suspect" not in recs["c_0005"] and "suspect" not in recs["c_0006"]  # 不保留的 / 没文字的不查
    assert res["flagged"] == 2
    fracs = [f for f, _m in prog.calls]
    assert fracs == sorted(fracs) and fracs[-1] == 1.0
    assert sum(1 for _f, m in prog.calls if m.startswith("已检查")) == 5  # 每段都报告
    assert any("已检查 5 / 5 条" in m for _f, m in prog.calls)
    assert not any(e[0] == "load" for e in fake_engines.log)


def test_find_suspects_with_second_engine_and_cache(tmp_path, fake_engines):
    fake_engines.installed.update({"funasr", "modelscope", "torch"})
    fake_engines.specs["funasr"] = {"answers": ANSWERS}
    cfg, project = _project(tmp_path, ROWS)
    res = pc.find_suspects(project, cfg)
    assert res["engine"] == "funasr" and res["checked"] == 5 and res["flagged"] == 3
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs["c_0001"]["suspect"]["alt"] == "这本书的意思是书，大家记一下。"
    assert recs["c_0002"]["suspect"]["alt"] == "我们今天讲是个函数。"
    assert recs["c_0002"]["suspect"]["spans"] == [[5, 6]]
    assert "suspect" not in recs["c_0003"]
    assert "suspect" not in recs["c_0004"]  # 英文片段 FunASR 不听，规则也不查大写
    assert "英文" in res["note"] or "规则" in res["note"]
    recognized = [e for e in fake_engines.log if e[0] == "recognize"]
    assert len(recognized) == 4 and ("load", "funasr") in fake_engines.log and ("close", "funasr") in fake_engines.log
    # 改了一句的文字再查：识别结果用缓存，不再加载模型
    recs["c_0002"]["text"] = "我们今天讲是个函数。"
    recs["c_0002"].pop("suspect")
    project.save_manifest(list(recs.values()))
    fake_engines.log.clear()
    res2 = pc.find_suspects(project, cfg)
    assert res2["engine"] == "funasr" and res2["flagged"] == 2
    assert not any(e[0] in ("load", "recognize") for e in fake_engines.log)
    assert "suspect" not in {r["id"]: r for r in project.load_manifest()}["c_0002"]


def test_find_suspects_only_kept_and_limit(tmp_path, fake_engines):
    cfg, project = _project(tmp_path, ROWS)
    res = pc.find_suspects(project, cfg, only_kept=False)
    assert res["checked"] == 6
    assert {r["id"]: r for r in project.load_manifest()}["c_0005"]["suspect"]["spans"]
    res = pc.find_suspects(project, cfg, limit=1)
    assert res["checked"] == 1 and res["total"] == 1


def test_find_suspects_survives_a_failing_clip(tmp_path, fake_engines):
    fake_engines.installed.update({"funasr", "modelscope", "torch"})
    fake_engines.specs["funasr"] = {"answers": ANSWERS, "fail": {"c_0000"}}
    cfg, project = _project(tmp_path, ROWS)
    res = pc.find_suspects(project, cfg)
    assert res["errors"] == 1 and res["checked"] == 5 and res["engine"] == "funasr"
    assert "出错" in res["note"]
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs["c_0000"]["suspect"]["spans"] == [[5, 11]]  # 出错的那段改用规则检查
    assert recs["c_0002"]["suspect"]["alt"] == "我们今天讲是个函数。"  # 后面的照常检查


def test_find_suspects_falls_back_when_engine_cannot_load(tmp_path, fake_engines):
    fake_engines.installed.update({"funasr", "modelscope", "torch", "faster_whisper"})
    fake_engines.specs["funasr"] = {"answers": ANSWERS, "load_error": RuntimeError("Download failed")}
    fake_engines.specs["faster-whisper-words"] = {
        "answers": {}, "words": {"c_0003": [("这一段完全", 0.9), ("没有", 0.1), ("问题。", 0.9)]}}
    cfg, project = _project(tmp_path, ROWS, engine="faster-whisper")
    res = pc.find_suspects(project, cfg)
    assert res["engine"] == "faster-whisper-words"
    assert "没能用上" in res["note"]
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs["c_0003"]["suspect"]["spans"] == [[5, 7]]  # "没有" 把握很低
    assert recs["c_0003"]["suspect"]["alt"] == ""


def test_find_suspects_drops_an_engine_that_never_works(tmp_path, fake_engines):
    fake_engines.installed.update({"funasr", "modelscope", "torch"})
    fake_engines.specs["funasr"] = {"answers": ANSWERS, "fail": {"*"}}
    cfg, project = _project(tmp_path, ROWS)
    res = pc.find_suspects(project, cfg)
    assert res["engine"] == "" and res["errors"] == pc.MAX_LOAD_FAILS_BEFORE_OK - 1
    assert res["checked"] == 5 and "没能用上" in res["note"]
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs["c_0000"]["suspect"]["spans"] == [[5, 11]]


def test_find_suspects_stop_button_saves_what_was_done(tmp_path, fake_engines):
    from voicetwin.utils.progress import TaskCancelled, clear_cancel, request_cancel

    assert pc._check_cancel.__module__ == "voicetwin.utils.progress"
    cfg, project = _project(tmp_path, ROWS)

    def prog(frac, msg):
        if msg.startswith("已检查 2 /"):
            request_cancel()

    try:
        with pytest.raises(TaskCancelled):
            pc.find_suspects(project, cfg, progress=prog)
    finally:
        clear_cancel()
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs["c_0000"]["suspect"]["spans"] == [[5, 11]]  # 停止前查完的已经存好
    assert "suspect" in recs["c_0003"]  # 还没查到的保持原样


def test_find_suspects_progress_callback_errors_are_ignored(tmp_path, fake_engines):
    cfg, project = _project(tmp_path, ROWS[:2])

    def bad(frac, msg):
        raise ValueError("界面出错")

    assert pc.find_suspects(project, cfg, progress=bad)["checked"] == 2


def test_find_suspects_empty_project(tmp_path, fake_engines):
    cfg, project = _project(tmp_path, [{"text": ""}])
    res = pc.find_suspects(project, cfg)
    assert res["checked"] == 0 and res["flagged"] == 0 and res["note"]


def test_dismiss_suspect_until_text_changes(tmp_path, fake_engines):
    cfg, project = _project(tmp_path, ROWS[:1])
    pc.find_suspects(project, cfg)
    assert project.load_manifest()[0].get("suspect")
    assert pc.dismiss_suspect(project, "c_0000") is True
    assert pc.dismiss_suspect(project, "不存在") is False
    pc.find_suspects(project, cfg)
    assert "suspect" not in project.load_manifest()[0]  # 确认过没错：不再标红
    recs = project.load_manifest()
    recs[0]["text"] = "我们今天讲VFIXED和WHOOZ的用法。"
    project.save_manifest(recs)
    pc.find_suspects(project, cfg)
    assert project.load_manifest()[0].get("suspect")  # 文字改了：重新检查


def test_cache_is_refreshed_when_the_recording_changes(tmp_path, fake_engines):
    fake_engines.installed.update({"funasr", "modelscope", "torch"})
    fake_engines.specs["funasr"] = {"answers": ANSWERS}
    cfg, project = _project(tmp_path, ROWS[:3])
    pc.find_suspects(project, cfg)
    sf.write(str(project.root / "clips/c_0002.wav"), np.zeros(4000, dtype=np.float32), 16000)  # 录音换了
    fake_engines.log.clear()
    pc.find_suspects(project, cfg)
    assert [e for e in fake_engines.log if e[0] == "recognize"] == [("recognize", "funasr", "c_0002")]


def test_edge_cases_never_raise():
    assert pc.build_suspect("", "随便") is None
    assert pc.build_suspect("。。。", "") is None
    assert pc.build_suspect("好。", "好的") is None
    sus = pc.build_suspect("列表推导式很好用。", "嗯这个列表推导式很好用")  # 开头多出来的是语气词
    assert sus is None
    sus = pc.build_suspect("推导式很好用。", "列表推导式很好用")  # 开头漏了词
    assert sus["alt"] == "列表推导式很好用。"
    assert pc.render_diff_html("一样的句子。", "一样的句子").count(RED) == 0
    assert pc._apply_edits("abcdef", [(1, 3, "X"), (2, 4, "Y"), (0, 0, "Z")]) == "ZabYef"  # 重叠的只取后面那个
    assert pc.low_prob_spans("", [("x", 0.1)]) == [] and pc.low_prob_spans("文字", None) == []
    assert pc.merge_spans(None) == [] and pc.render_plain("", [[0, 3]]) == ""


def test_no_heavy_imports_at_module_level():
    src = open(pc.__file__, encoding="utf-8").read()
    head = src.split("# ============================================================================ 小工具")[0]
    assert not re.search(r"^\s*(import|from)\s+(funasr|faster_whisper|torch|gradio|modelscope)", head, re.M)
