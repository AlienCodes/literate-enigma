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
