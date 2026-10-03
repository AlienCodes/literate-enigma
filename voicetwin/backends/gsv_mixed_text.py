"""「一模一样」训练：中文句子里夹着的英文也参加训练（VoiceTwin 自己的 1A 里不用 torch 的那部分计算）。

为什么要有它：官方的 1-get-text.py 对整句话做 clean_text(text, "zh")，chinese2.replace_punctuation 只留汉字和标点，
句子里的英文字母整个被删掉（老师的 1004 句素材里 559 句夹着英文，一共 2080 个英文单词，以前从来没有参加过训练）。
可是生成的时候（api_v2 的 text_lang = zh）走的是 TextPreprocessor.get_phones_and_bert：先用 LangSegmenter 把英文切出来，
英文按英文的音素（ARPAbet）读、BERT 特征是 0，中文照常。训练和生成用的是两套不一样的处理方法。

这里照抄生成时的做法（GPT_SoVITS/TTS_infer_pack/TextPreprocessor.py @ abe9843，也就是老师电脑上的版本）：
- 连着的英文段合成一段；连着的不是英文的段合成一段，按 zh 处理（官方注释：「因无法区别中日韩文汉字,以用户输入为准」）；
- 每段各自 clean_text，音素按顺序接起来；
- BERT 特征：中文段和官方 1A 一样算，英文段是 0（get_bert_inf），每段的长度 = 这一段的音素个数，
  加起来正好等于整句的音素个数（s1 训练的数据集会检查 bert.shape[-1] == len(phones)）。

这个文件只用 Python 标准库：整合包的 Python 直接按文件路径加载它（gsv_scripts/get_text_mixed.py），
不需要整合包里装了 voicetwin。"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

#: 英文音素（ARPAbet）：1~2 个大写字母，后面可能跟着重音数字 0~2（例如 HH、AH0、OW1）
ARPABET_RE = re.compile(r"^[A-Z]{1,2}[0-2]?$")
#: 符合上面的写法、但不是英文音素的符号（静音、停顿、不认识的音）
NOT_ARPABET = frozenset({"SP", "AP", "SP2", "SP3", "UNK"})
#: 英文字母（判断一句话里有没有英文）
LATIN_RE = re.compile(r"[A-Za-z]")
#: 汉字（和 voicetwin.utils.textutil.CJK_RE 一样；这里不 import voicetwin）
CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")


def is_arpabet(phone: Any) -> bool:
    """是不是一个英文音素（ARPAbet）。"""
    p = str(phone)
    return bool(ARPABET_RE.match(p)) and p not in NOT_ARPABET


def merge_segments(raw: Iterable[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """LangSegmenter.getTexts 的结果 → [(文字, 语言)]，语言只有 "en" 和 "zh"。

    和 abe9843 的 TextPreprocessor.get_phones_and_bert（text_lang = zh 的那个分支）一模一样：
    这一段和上一段都是英文、或者都不是英文，就接到上一段后面；不是英文的一律记成 zh。空的段也照样参加（和官方一样）。"""
    texts: List[str] = []
    langs: List[str] = []
    for seg in raw:
        text = str((seg or {}).get("text") or "")
        is_en = (seg or {}).get("lang") == "en"
        if langs and (is_en == (langs[-1] == "en")):
            texts[-1] += text
            continue
        langs.append("en" if is_en else "zh")
        texts.append(text)
    return list(zip(texts, langs))


def assemble(results: Sequence[Tuple[str, Sequence[str], Optional[Sequence[int]], str]]
             ) -> Tuple[List[str], List[int], str, List[Tuple[str, int]]]:
    """每段 clean_text 的结果 [(语言, 音素, word2ph, 规范化的文字)] → 整句的 (音素, word2ph, 文字, BERT 分段)。

    - 音素：按顺序接起来；
    - BERT 分段：[(语言, 这一段的音素个数)]，加起来 == 整句的音素个数（中文段算 BERT，英文段是 0）；
    - word2ph：中文段照抄每个字的音素个数；英文段官方本来就没有（None），这里记成一个数 = 这一段的音素个数，
      所以 sum(word2ph) 也 == 音素个数（训练程序只读音素那一列，word2ph 只是记下来）；
    - 文字：每段规范化后的文字接起来（制表符换成空格，免得训练列表多出一列）。"""
    phones: List[str] = []
    word2ph: List[int] = []
    norm: List[str] = []
    spans: List[Tuple[str, int]] = []
    for lang, ph, w2p, text in results:
        ph = [str(p) for p in ph]
        phones += ph
        if lang == "zh" and w2p is not None:
            word2ph += [int(x) for x in w2p]
        elif ph:
            word2ph.append(len(ph))
        norm.append(str(text or ""))
        spans.append(("zh" if lang == "zh" else "en", len(ph)))
    return phones, word2ph, "".join(norm).replace("\t", " ").replace("\n", " "), spans


def count_en_phones(results: Sequence[Tuple[str, Sequence[str], Any, Any]]) -> int:
    """英文段里的英文音素一共几个（只数英文段：中文的零声母 AA / EE / OO 写法和英文音素长得一样，不能算进来）。"""
    return sum(1 for lang, ph, _w, _t in results if lang == "en" for p in ph if is_arpabet(p))


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def has_latin(text: str) -> bool:
    return bool(LATIN_RE.search(text or ""))
