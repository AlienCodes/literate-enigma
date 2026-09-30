"""中英文文本工具：语言判断、音节计数（统一衡量中英文语速）、错字率、简繁转换。"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import List

CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
EN_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
DIGIT_RE = re.compile(r"\d")
# 数字串（阿拉伯数字或中文数字）在计算错字率时统一成一个占位符，避免 "2024" 与 "二零二四" 被判为错字
NUM_RUN_RE = re.compile(r"[0-9零〇一二两三四五六七八九十百千万亿点.%％]+")

SENT_END_CHARS = "。！？!?；;…"
CLAUSE_CHARS = "，,、：:—"
ALL_PUNCT_RE = re.compile(r"[\s　-〿＀-￯!-/:-@\[-`{-~“”‘’…—·]+")


def count_cjk(text: str) -> int:
    return len(CJK_RE.findall(text))


def en_words(text: str) -> List[str]:
    return EN_WORD_RE.findall(text)


def detect_lang(text: str) -> str:
    """只区分 zh / en。中文句子里夹英文单词仍算 zh（GPT-SoVITS 的 zh 模式支持中英混读）。"""
    cjk = count_cjk(text)
    words = len(en_words(text))
    if cjk == 0:
        return "en"
    return "zh" if cjk >= max(1, 0.2 * words) else "en"


_VOWEL_GROUP = re.compile(r"[aeiouy]+")


def en_syllables(word: str) -> int:
    """英文单词音节数的启发式估计（误差 ±1，足够用于语速统计）。"""
    if not word:
        return 0
    if word.isupper() and len(word) <= 5:  # 缩写 API / GPU / SQL 逐字母读
        return sum(3 if ch == "W" else 1 for ch in word)
    w = word.lower().replace("'", "")
    groups = _VOWEL_GROUP.findall(w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and n > 1:
        n -= 1
    if w.endswith(("ed",)) and not w.endswith(("ted", "ded")) and n > 1:
        n -= 1
    return max(1, n)


def syllable_count(text: str) -> int:
    """统一的"音节"计数：每个汉字 1 个，英文按音节估计，每个数字 1 个。"""
    total = count_cjk(text)
    total += sum(en_syllables(w) for w in en_words(text))
    total += len(DIGIT_RE.findall(text))
    return total


def to_simplified(text: str) -> str:
    try:
        import zhconv  # type: ignore

        return zhconv.convert(text, "zh-cn")
    except Exception:
        pass
    try:
        import opencc  # type: ignore

        return opencc.OpenCC("t2s").convert(text)
    except Exception:
        return text


def normalize_for_cer(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = to_simplified(text).lower()
    text = NUM_RUN_RE.sub("#", text)
    text = ALL_PUNCT_RE.sub("", text)
    return text


def edit_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float:
    """字符错误率（中英文统一按字符计算，已去掉标点和空格）。"""
    ref = normalize_for_cer(reference)
    hyp = normalize_for_cer(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return edit_distance(ref, hyp) / len(ref)


def sentence_kind(text: str) -> str:
    t = text.strip().rstrip("”\"'’）)」』")
    if not t:
        return "statement"
    if t[-1] in "？?":
        return "question"
    if t[-1] in "！!":
        return "exclaim"
    return "statement"


def ends_sentence(text: str) -> bool:
    t = text.strip().rstrip("”\"'’）)」』")
    return bool(t) and (t[-1] in SENT_END_CHARS or t[-1] == ".")


def ends_clause(text: str) -> bool:
    t = text.strip()
    return bool(t) and t[-1] in CLAUSE_CHARS


def ensure_final_punct(text: str, lang: str) -> str:
    t = text.strip()
    if not t:
        return t
    if t[-1] in SENT_END_CHARS + CLAUSE_CHARS + ".":
        return t
    return t + ("。" if lang == "zh" else ".")


def clean_transcript(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\n", " ").replace("|", " ")
    text = re.sub(r"\s+", " ", text).strip()
    # NFKC 会把中文全角标点转成半角，这里把中文语境下的常用标点转回来
    if count_cjk(text):
        text = re.sub(r"(?<=[一-鿿]),", "，", text)
        text = re.sub(r"(?<=[一-鿿])\?", "？", text)
        text = re.sub(r"(?<=[一-鿿])!", "！", text)
        text = re.sub(r"(?<=[一-鿿]);", "；", text)
        text = re.sub(r"(?<=[一-鿿]):", "：", text)
        text = re.sub(r"(?<=[一-鿿])\.(?!\d)", "。", text)
        text = re.sub(r"\s+(?=[一-鿿，。！？；：])", "", text)
        text = re.sub(r"(?<=[一-鿿，。！？；：])\s+(?=[一-鿿])", "", text)
        # 括号里有中文、或紧跟在中文后面时，还原为全角括号（字幕更美观）
        text = re.sub(r"\(([^()]*)\)", lambda m: f"（{m.group(1)}）"
                      if count_cjk(m.group(1)) or count_cjk(m.string[max(0, m.start() - 1):m.start()])
                      else m.group(0), text)
    return text


def safe_name(text: str, max_len: int = 40) -> str:
    base = re.sub(r"[^\w一-鿿-]+", "_", text).strip("_")[:max_len] or "item"
    return base


def short_hash(*parts: object, n: int = 10) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(repr(p).encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:n]
