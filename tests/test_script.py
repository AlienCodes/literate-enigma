from voicetwin.synth.script import apply_lexicon, chunk_sentence, parse_script, split_sentences
from voicetwin.utils.textutil import syllable_count


def test_markdown_pauses_and_lexicon():
    md = """# 第一课

大家好。今天我们学习 **SQL** 的基础知识。[停顿=1.5]
```python
print("不应该被朗读")
```
那么，大家明白了吗？

Next, let's look at Dr. Smith's example. The value is 3.14.
"""
    segs = parse_script(md, lexicon=[("SQL", "sequel")])
    texts = [s.text for s in segs]
    assert texts[0] == "第一课。"
    assert segs[0].pause_after == "paragraph"
    assert any("sequel" in t for t in texts)
    assert any("SQL" in s.display for s in segs)
    assert not any("不应该被朗读" in t for t in texts)
    assert any(s.pause_after == 1.5 for s in segs)
    assert any(s.kind == "question" for s in segs)
    assert "Next, let's look at Dr. Smith's example." in texts
    assert segs[-1].pause_after == 0.0


def test_split_sentences_keeps_decimals_and_abbreviations():
    assert split_sentences("Pi is 3.14. Mr. Li said hi. 好的！走吧。") == ["Pi is 3.14.", "Mr. Li said hi.", "好的！", "走吧。"]


def test_long_sentence_is_chunked_at_clauses():
    s = "，".join(["这是一个比较长的分句用来测试"] * 8) + "。"
    chunks = chunk_sentence(s, 50)
    assert len(chunks) > 1
    assert all(syllable_count(c) <= 50 for c in chunks)


def test_short_sentences_are_merged():
    segs = parse_script("好。今天我们要学习一个非常重要的概念。")
    assert len(segs) == 1


def test_lexicon_word_boundary():
    assert apply_lexicon("MySQL and SQL", [("SQL", "sequel")]) == "MySQL and sequel"


def test_srt_script(tmp_path):
    p = tmp_path / "a.srt"
    p.write_text("1\n00:00:01,000 --> 00:00:03,000\n第一句话。\n\n2\n00:00:04,500 --> 00:00:06,000\nSecond line.\n", encoding="utf-8")
    segs = parse_script(p)
    assert [s.cue_start for s in segs] == [1.0, 4.5]
