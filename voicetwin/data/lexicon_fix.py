"""母本标准库纠错（v18.5）：按老师的「标准库」改正识别引擎写错的字。

老师 10-03 的要求：修缮过的母本就是老师全部的说话习惯，再加上所有的中文语法术语，作为标准库；
识别出来的文字里被写错的字，以这个库为标准去改（「借词」不可能出现，正确的是「介词」；「艾子」是 as）。

标准库：
- 程序自带（voicetwin/data/lexicon/）：grammar_terms.txt（英语语法术语和老师常用说法的标准写法）、
  corrections.txt（错的写法 => 正确写法）。
- 老师上传的母本（修缮过的 transcripts.csv 或 txt，存在声音文件夹「逐字稿」里，不放进公开的仓库）：
  用来统计老师的习惯写法（每个词说了多少次）。
- 老师以前在校对表里自己改过的（最初识别的文字 → 改好的文字）：别的句子里同样的错也改。

找错的办法（每一处都要「刚好是一个完整的词」：用 jieba 分词判断，「凭借词汇」里的「借词」、「介词一起」里的
「词一」都不算）：
1. 对照表里左边的写法 → 直接改成右边的。
2. 读音和标准库里的某个词（术语、母本里常说的词）一样、写法不一样、至少一半的字相同，而且这种写法在母本里
   几乎没出现过（老师自己的写法是另一种）→ 读音完全一样的直接改；声调不同的只给建议。
3. 老师以前自己改过的错（读音相同或相近的词、英文被写成汉字）→ 直接改。
直接改的存成没保存的修改（红灯），老师看一眼再点「保存修改」；「修改建议」的红色按钮可以撤销。

对外接口：Lexicon.build(...)、Lexicon.find(text) -> List[Fix]、learn_from_edits(records)、builtin_info()
"""

from __future__ import annotations

import difflib
import importlib
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from voicetwin.data import proofcheck as pc
from voicetwin.data import transcript_fix as tf
from voicetwin.utils.log import get_logger

log = get_logger("lexicon_fix")

LEXICON_DIR = Path(__file__).resolve().parent / "lexicon"
TERMS_FILE = "grammar_terms.txt"
CORRECTIONS_FILE = "corrections.txt"
_HAN = re.compile(r"^[㐀-䶿一-鿿豈-﫿]+$")
MAX_TERM = 10
HABIT_MIN = 3  # 母本里至少说过这么多次的词，算老师的习惯说法
COMMON_FREQ = 2000  # jieba 词典里这么常见的词（「一声」「以下」）不当成写错的


# ============================================================================ 自带的词库
def _read_lines(name: str) -> List[str]:
    try:
        text = (LEXICON_DIR / name).read_text(encoding="utf-8")
    except OSError:
        return []
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]


@lru_cache(maxsize=1)
def builtin_terms() -> Tuple[str, ...]:
    """grammar_terms.txt 里的词（空格分开，一行可以好几个）。"""
    out: List[str] = []
    for ln in _read_lines(TERMS_FILE):
        for w in ln.split():
            if w and w not in out:
                out.append(w)
    return tuple(out)


def parse_corrections(lines: Iterable[str]) -> Dict[str, str]:
    """「错 => 对」（也认 -> 和 →）；左右一样、或者有一边是空的跳过。"""
    out: Dict[str, str] = {}
    for ln in lines:
        ln = str(ln).strip()
        if not ln or ln.startswith("#"):
            continue
        m = re.match(r"^(.+?)\s*(?:=>|->|→)\s*(.+)$", ln)
        if not m:
            continue
        a, b = m.group(1).strip(), m.group(2).strip()
        if a and b and a != b:
            out[a] = b
    return out


@lru_cache(maxsize=1)
def builtin_corrections() -> Dict[str, str]:
    return parse_corrections(_read_lines(CORRECTIONS_FILE))


def builtin_info() -> Dict[str, int]:
    return {"terms": len(builtin_terms()), "corrections": len(builtin_corrections())}


# ============================================================================ 分词（判断「是不是一个完整的词」）
@lru_cache(maxsize=1)
def _tokenizer() -> Any:
    """jieba（GPT-SoVITS 整合包里有 jieba 和 jieba_fast）的一个单独的分词器，加上语法术语。没有时返回 None。"""
    for name in ("jieba_fast", "jieba"):
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        try:
            try:
                mod.setLogLevel(logging.ERROR)
            except Exception:
                pass
            tk = mod.Tokenizer()
            tk.initialize()
            for w in builtin_terms():
                if _HAN.match(w):
                    tk.add_word(w, freq=max(tk.FREQ.get(w, 0) or 0, 5000))
            return tk
        except Exception as exc:  # noqa: BLE001
            log.debug(f"{name} 用不了：{exc}")
    return None


def has_jieba() -> bool:
    return _tokenizer() is not None


def word_bounds(text: str) -> Optional[Set[int]]:
    """分词以后每个词开头和结尾的位置；没有 jieba 时返回 None。"""
    tk = _tokenizer()
    if tk is None:
        return None
    out = {0, len(text)}
    try:
        for _w, s, e in tk.tokenize(text):
            out.add(int(s))
            out.add(int(e))
    except Exception as exc:  # noqa: BLE001
        log.debug(f"分词出错：{exc}")
        return None
    return out


def word_freq(w: str) -> int:
    tk = _tokenizer()
    if tk is None:
        return 0
    try:
        return int(tk.FREQ.get(w, 0) or 0)
    except Exception:
        return 0


def _nonword(w: str) -> bool:
    """不是一个常见的词（「定语从剧」「关系带词」）：词典里没有，也不是几个常见的词拼起来的（「比较急」）。"""
    tk = _tokenizer()
    if tk is None:
        return False
    if word_freq(w) > 0:
        return False
    try:
        parts = [p for p in tk.lcut(w, HMM=False) if p.strip()]
    except Exception:
        return False
    return not (len(parts) >= 2 and all(word_freq(p) >= COMMON_FREQ for p in parts))


# ============================================================================ 一处改法
@dataclass
class Fix:
    start: int
    end: int
    rep: str
    kind: str  # list / learned / term / habit / same_row / align
    direct: bool
    weight: float
    reason: str


PRIORITY = {"same_row": 6, "list": 5, "learned": 4, "align": 3, "term": 2, "habit": 1}


def resolve(fixes: Sequence[Fix]) -> List[Fix]:
    """同一个地方好几种改法：直接改的优先，再按来源（同一句的母本 > 对照表 > 以前改过的 > 对齐 > 术语）、长的优先。"""
    order = sorted(fixes, key=lambda f: (-int(f.direct), -PRIORITY.get(f.kind, 0), -(f.end - f.start), f.start))
    kept: List[Fix] = []
    for f in order:
        if all(not (f.start < g.end and g.start < f.end) and f.start != g.start for g in kept):
            kept.append(f)
    return sorted(kept, key=lambda f: (f.start, f.end))


# ============================================================================ 标准库
def _han_runs(text: str) -> List[str]:
    return re.findall(r"[㐀-䶿一-鿿豈-﫿]+", str(text or ""))


def _count_ngrams(texts: Iterable[str], max_n: int = MAX_TERM) -> Counter:
    c: Counter = Counter()
    for t in texts:
        for run in _han_runs(t):
            for n in range(2, min(max_n, len(run)) + 1):
                for i in range(len(run) - n + 1):
                    c[run[i:i + n]] += 1
    return c


def _sound(word: str) -> Optional[Tuple[Tuple[str, ...], Tuple[str, ...]]]:
    """一个词的（不带声调的读音, 带声调的读音）；不全是汉字时返回 None。"""
    toks = tf.tokens(word)
    if not toks or any(t.kind != "han" for t in toks) or len(toks) != len(word):
        return None
    return tuple(t.snd for t in toks), tuple(t.tone for t in toks)


def _style_only(a: str, b: str) -> bool:
    return all(x == y or tf._style_pair(x, y) for x, y in zip(a, b))


class Lexicon:
    """标准库：术语、对照表、老师的习惯说法（母本里每个词说了多少次）、老师以前改过的错。"""

    def __init__(self, terms: Iterable[str], corrections: Dict[str, str], mother_texts: Sequence[str] = (),
                 learned: Optional[Dict[str, str]] = None):
        self.corrections = dict(corrections)
        self.learned = dict(learned or {})
        self.counts = _count_ngrams(mother_texts)
        self.has_mother = bool(mother_texts)
        self.builtin = set(t for t in terms if _HAN.match(t) and len(t) >= 2)
        habits: Set[str] = set()
        tk = _tokenizer()
        if tk is not None and mother_texts:  # 母本里说过好几次的词（分词得到的完整的词）
            wc: Counter = Counter()
            for t in mother_texts:
                for run in _han_runs(t):
                    try:
                        wc.update(w for w in tk.lcut(run, HMM=False) if len(w) >= 2)
                    except Exception:
                        break
            habits = {w for w, c in wc.items() if c >= HABIT_MIN and _HAN.match(w)}
        self.habits = habits - self.builtin
        self.vocab = self.builtin | self.habits  # 标准写法（这些写法本身永远不改）
        self.by_sound: Dict[Tuple[str, ...], List[str]] = {}
        for w in sorted(self.vocab, key=len, reverse=True):
            s = _sound(w)
            if s is not None:
                self.by_sound.setdefault(s[0], []).append(w)
        self.tones = {w: (_sound(w) or ((), ()))[1] for w in self.vocab}
        self.longest = max([len(w) for w in self.vocab] or [2])

    @classmethod
    def build(cls, mother_texts: Sequence[str] = (), learned: Optional[Dict[str, str]] = None,
              extra_corrections: Optional[Dict[str, str]] = None) -> "Lexicon":
        corr = dict(builtin_corrections())
        corr.update(extra_corrections or {})
        return cls(builtin_terms(), corr, mother_texts, learned)

    # -------------------------------------------------------------- 判断
    def _aligned(self, bounds: Optional[Set[int]], s: int, e: int) -> bool:
        return bounds is None or (s in bounds and e in bounds)

    def _inside_term(self, text: str, s: int, e: int) -> bool:
        """这几个字是不是某个标准写法的一部分（「同位语」里的「位语」）。"""
        for w in self.vocab:
            if len(w) <= e - s or w.find(text[s:e]) < 0:
                continue
            k = text.find(w, max(0, e - len(w)))
            while 0 <= k <= s:
                if k + len(w) >= e:
                    return True
                k = text.find(w, k + 1)
        return False

    def _partial_overlap_term(self, text: str, s: int, e: int) -> bool:
        """没有 jieba 时的边界保护：有一个标准写法跨在这几个字的边上（「介词一起」的「词一」）。"""
        for w in self.vocab:
            k = text.find(w)
            while k >= 0:
                if (k < s < k + len(w) < e) or (s < k < e < k + len(w)) or (k < s and e < k + len(w)):
                    return True
                k = text.find(w, k + 1)
        return False

    def inside_vocab(self, text: str, s: int, e: int) -> bool:
        """这几个字在一个标准写法（术语、母本里常说的词）里面，而且那个词就是这么写的（「及物动词」里的「及」）。"""
        for w in self.vocab:
            if len(w) < e - s:
                continue
            k = text.find(w, max(0, e - len(w)))
            while 0 <= k <= s:
                if k + len(w) >= e:
                    return True
                k = text.find(w, k + 1)
        return False

    def has_common_word(self, piece: str) -> bool:
        """这几个字里有常用的词（或者本身就是常用的单字，比如「它」）。"""
        tk = _tokenizer()
        if tk is None:
            return True
        try:
            words = [w for w in tk.lcut(piece, HMM=False) if w.strip()]
        except Exception:
            return True
        return any(word_freq(w) >= COMMON_FREQ or w in self.vocab for w in words)

    def mother_count(self, w: str) -> int:
        return int(self.counts.get(w, 0))

    # -------------------------------------------------------------- 找错
    def find(self, text: str) -> List[Fix]:
        text = str(text or "")
        if not text.strip():
            return []
        bounds = word_bounds(text)
        fixes: List[Fix] = []
        for table, kind, w0 in ((self.corrections, "list", 0.9), (self.learned, "learned", 0.85)):
            for wrong, right in table.items():
                k = text.find(wrong)
                while k >= 0:
                    e = k + len(wrong)
                    if self._ok_place(text, k, e, bounds, wrong):
                        what = "对照表" if kind == "list" else "你以前改过"
                        fixes.append(Fix(k, e, pc._pad(text, k, e, right), kind, True, w0,
                                         f"「{wrong}」应该是「{right}」（{what}）"))
                    k = text.find(wrong, k + 1)
        fixes += self._sound_fixes(text, bounds)
        return resolve(fixes)

    def _ok_place(self, text: str, s: int, e: int, bounds: Optional[Set[int]], wrong: str) -> bool:
        if not self._aligned(bounds, s, e):
            return False
        if self._inside_term(text, s, e):
            return False
        if bounds is None and self._partial_overlap_term(text, s, e):
            return False
        return True

    def _sound_fixes(self, text: str, bounds: Optional[Set[int]]) -> List[Fix]:
        if not tf.has_pinyin() or not self.by_sound:
            return []
        toks = tf.tokens(text)
        out: List[Fix] = []
        n_tok = len(toks)
        for i in range(n_tok):
            if toks[i].kind != "han":
                continue
            for n in range(2, min(self.longest, n_tok - i) + 1):
                run = toks[i:i + n]
                if any(t.kind != "han" for t in run) or any(run[k].start != run[k - 1].end for k in range(1, n)):
                    break
                s, e = run[0].start, run[-1].end
                win = text[s:e]
                if len(win) != n or win in self.vocab:
                    continue
                cands = self.by_sound.get(tuple(t.snd for t in run))
                if not cands:
                    continue
                fix = self._best_term(text, win, run, cands, s, e, bounds)
                if fix is not None:
                    out.append(fix)
        return out

    def _best_term(self, text: str, win: str, run: Sequence[Any], cands: Sequence[str], s: int, e: int,
                   bounds: Optional[Set[int]]) -> Optional[Fix]:
        n = len(win)
        best: Optional[Fix] = None
        for term in cands:
            if term == win or len(term) != n:
                continue
            shared = sum(a == b for a, b in zip(win, term))
            if shared < math.ceil(n / 2) or _style_only(win, term):
                continue
            habit = term in self.habits
            cw, ct = self.mother_count(win), self.mother_count(term)
            if self.has_mother and cw and cw * 3 > ct:
                continue  # 老师的母本里这种写法也常见：那也是老师的说法
            if word_freq(win) >= COMMON_FREQ:
                continue  # 「一声」「以下」这种常见的词不当成写错的
            if not self._ok_place(text, s, e, bounds, win):
                continue
            same_tone = tuple(t.tone for t in run) == self.tones.get(term)
            nonword = _nonword(win)
            if habit and not nonword:
                continue  # 母本里常说的词（不是术语）：只有写成「不是词」的样子才算写错
            if same_tone:
                direct = (term in self.builtin and (ct >= HABIT_MIN or nonword or not self.has_mother)) or \
                         (habit and nonword)
                if bounds is None:
                    direct = False  # 没有分词：只给建议
            else:
                if not nonword or cw:
                    continue
                direct = False
            src = "语法术语" if term in self.builtin else f"你的母本里说过 {ct} 次"
            how = "读音一样" if same_tone else "读音很像"
            fix = Fix(s, e, term, "term" if term in self.builtin else "habit", direct,
                      0.85 if direct else 0.6, f"「{win}」应该是「{term}」（{how}，{src}）")
            if best is None or (fix.direct and not best.direct) or (ct > self.mother_count(best.rep)):
                best = fix
        return best


# ============================================================================ 老师以前改过的
def _word_around(a: Sequence[Any], b: Sequence[Any], i: int, j: int, new: str) -> Optional[Tuple[int, int, int, int]]:
    """改了一个字：右边（或左边）连着一个没改的汉字、改好以后这两个字是一个词（标准库里的词或者 jieba 词典里的词），
    返回扩大以后的范围；凑不成词返回 None。"""
    vocab = set(builtin_terms())
    for di, dj, si, sj in ((0, 0, 2, 2), (-1, -1, 2, 2)):
        i1, j1 = i + di, j + dj
        i2, j2 = i1 + si, j1 + sj
        if i1 < 0 or j1 < 0 or i2 > len(a) or j2 > len(b):
            continue
        if any(t.kind != "han" for t in list(a[i1:i2]) + list(b[j1:j2])):
            continue
        k = i1 if di == 0 else i1  # 没改的那个字两边要一样
        other_a = a[i1 + 1] if di == 0 else a[i1]
        other_b = b[j1 + 1] if dj == 0 else b[j1]
        if other_a.key != other_b.key:
            continue
        word = new[b[j1].start:b[j2 - 1].end]
        if word in vocab or word_freq(word) > 0:
            return i1, i2, j1, j2
    return None


def learn_from_edits(records: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    """校对表里老师改过的地方（最初识别的文字 orig_text → 改好的 text）：读音相同或相近的词、英文被写成汉字。

    只学 ≥ 2 个字的词（单个字的同音字太容易用错地方）。同一个错改成了不同的写法时，不学。"""
    pairs: Dict[str, Counter] = {}
    for r in records:
        if r.get("deleted"):
            continue
        old, new = str(r.get("orig_text") or ""), str(r.get("text") or "")
        if not old or not new or old == new:
            continue
        a, b = tf.tokens(old), tf.tokens(new)
        sm = difflib.SequenceMatcher(None, [t.key for t in a], [t.key for t in b], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "replace" or not (1 <= i2 - i1 <= 4 and 1 <= j2 - j1 <= 4):
                continue
            if i2 - i1 == 1 and j2 - j1 == 1 and a[i1].kind == "han" and b[j1].kind == "han":
                # 只改了一个字（关系带词 → 关系代词）：连上旁边没改的字，凑成一个词（带词 → 代词）再学
                ext = _word_around(a, b, i1, j1, new)
                if ext is None:
                    continue
                i1, i2, j1, j2 = ext
            at, bt = a[i1:i2], b[j1:j2]
            wrong = old[at[0].start:at[-1].end]
            right = new[bt[0].start:bt[-1].end]
            ak, bk = {t.kind for t in at}, {t.kind for t in bt}
            ok = False
            if ak == {"han"} and bk == {"han"} and len(wrong) >= 2 and len(wrong) == len(right):
                ok = [t.fz for t in at] == [t.fz for t in bt] and not _style_only(wrong, right)
            elif ak == {"han"} and bk == {"lat"}:
                ok = len(wrong) >= 2 and tf.sounds_like_english([t.tone for t in at], [t.key for t in bt])
            if ok:
                pairs.setdefault(wrong, Counter())[right] += 1
    out: Dict[str, str] = {}
    for wrong, c in pairs.items():
        if len(c) == 1:
            out[wrong] = next(iter(c))
    return out


__all__ = ["Lexicon", "Fix", "resolve", "learn_from_edits", "builtin_terms", "builtin_corrections", "builtin_info",
           "parse_corrections", "has_jieba", "word_bounds"]
