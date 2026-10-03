from voicetwin.utils.textutil import (cer, clean_transcript, detect_lang, en_syllables, ends_sentence, sentence_kind,
                                      syllable_count)


def test_detect_lang_mixed_is_zh():
    assert detect_lang("今天我们学习 machine learning 和 deep learning") == "zh"
    assert detect_lang("Today we learn Python.") == "en"


def test_syllables():
    assert syllable_count("你好世界") == 4
    assert en_syllables("API") == 3
    assert en_syllables("comprehension") >= 4
    assert syllable_count("我有3个苹果") == 6


def test_cer_ignores_punct_numbers_and_traditional():
    assert cer("今天，我们学习2024年的内容。", "今天我们学习二零二四年的内容") == 0.0
    assert cer("abc", "abd") > 0
    assert cer("Hello, World!", "hello world") == 0.0


def test_sentence_kind():
    assert sentence_kind("这是什么？") == "question"
    assert sentence_kind("太好了！") == "exclaim"
    assert sentence_kind("好的。") == "statement"
    assert ends_sentence("Done.")


def test_clean_transcript_restores_chinese_punct():
    assert clean_transcript("今天 我们 学习,好吗?") == "今天我们学习，好吗？"


def test_clean_transcript_parentheses():
    assert clean_transcript("今天学习列表推导式（已校对）。") == "今天学习列表推导式（已校对）。"
    assert clean_transcript("这是函数(function)的定义") == "这是函数（function）的定义"
    assert clean_transcript("We call f(x) here.") == "We call f(x) here."


def test_clean_transcript_keeps_chinese_punctuation_the_teacher_types():
    """第四轮找 bug：「……」以前变成「。.....」，「！！」变成「！!」，「（定语从句），」变成「（定语从句）,」。"""
    for t in ("那么这个句子……我们先放一放。", "等一下…", "我们先放一放！！然后看下一个？！", "你知道吗？？",
              "这个句子（定语从句），我们先放一放。", "他说“先放一放”，然后看下一个。", "《语法》，很好。"):
        assert clean_transcript(t) == t, t
    assert clean_transcript("好的...然后呢") == "好的……然后呢"  # 识别 / 字幕里的英文点跟在中文后面：中文省略号
    assert clean_transcript("啊!!!真的吗?!") == "啊！！！真的吗？！"
    assert clean_transcript("（定语从句）.") == "（定语从句）。"
    # 原来的写法照旧：英文后面的逗号半角、英文里的点和括号、数字里的点
    for t, want in (("which, 我们", "which,我们"), ("f(x), 然后", "f(x),然后"), ("Hello...world", "Hello...world"),
                    ("温度是3.5度。", "温度是3.5度。"), ("版本1.2.3里", "版本1.2.3里"), ("We call f(x) here.", "We call f(x) here.")):
        assert clean_transcript(t) == want, t
    for t in ("那么这个句子……我们先放一放。", "好的...然后呢", "啊!!!真的吗?!"):
        assert clean_transcript(clean_transcript(t)) == clean_transcript(t)  # 再整理一次不变
