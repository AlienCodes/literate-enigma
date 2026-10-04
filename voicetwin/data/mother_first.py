"""母本优先（10-04 老师的要求）：每一句识别出来的文字，先按**内容**去母本里找「差不多或者原模原样」的那一段；
找到了，母本就是标准答案——和母本不一样的地方都是识别错，按母本的写法改。

老师的原话：「识别出来的这些句子，先去跟母本对照。一般母本都会有差不多或者原模原样的句子。跟母本不一样的地方，
那很明显就是错误的地方。逻辑就这么简单。」「这个自动检查错字功能，它的底层逻辑也是要以母本为主……母本是最优先级。」

为什么按内容找、不按片段 id 找：片段 id 里有视频的完整路径和大小算出来的编号（data/prepare.py 的 source_id），
重新准备素材、视频挪了地方、上传视频而不是选文件夹、升级以后新建了声音，id 就全变了；切的位置也可能不一样
（两句合成一句、一句切成两句）。所以把母本当成一整串话（所有句子连起来，标点不算），按读音找这一句对应的那一段；
id 只当提示（同一个 id 的那一句文字也对得上时优先用它）。

怎么找（全部在本机算）：
1. 每个字换成模糊读音（transcript_fix.tokens：zh/z、n/l、ang/an 不分；英文用读音代码），三个音一组在母本里找位置
   （和以前的对齐用同一套：transcript_fix._windows），每个候选位置前后多看几个字；
2. 这一句和候选的那一段按读音对齐（difflib），找出连着对上的几段（至少 2 个字），挑「对上的多、中间空的少」的
   一串当这一句在母本里的范围；句子开头 / 结尾没对上的 1~3 个字，读音像（同声母 / 同韵母、汉字读音像英文）
   才算母本里挨着的那几个字被听错了；
3. 像不像（相似度）= 读音对上的字数 ÷ max(这一句的字数, 母本那一段的字数)。到 MATCH_MIN 才算「找到了」；
   只对上一部分（比如两句合成一句、其中一句是新的话）时，那一部分至少 PART_MIN 个字、也到 MATCH_MIN 才算，
   剩下的部分再找一次，还找不到就交给标准库（对照表、术语）、另一个识别引擎和规则。只对上一句中间的一小段不算
   （「我们来看一下」这种常说的话到处都有，证明不了录音里怎么说）。
   MATCH_MIN 是在老师 1005 句母本上量出来的（research/文字校正/母本优先/分布.py）：把每一句当成「新的话」、
   从母本里拿掉它自己再找，看会不会被别的句子硬改；同一批句子（修缮前 → 修缮后）都要找得到。
4. 找到的那一段里，读音一样写法不一样的字（定于 → 定语）、读音不一样的字（let → that、电影 → 定语）、多出来的字、
   少了的字，都按母本改——前提是有证据说明这是同一批录音（transcript_fix._mother_first 和 _SameBatch：
   同一个 id 的那一句、或者前后挨着的片段也对上母本里前后挨着的句子）；没有这种证据时（新讲的课用了母本里的说法），
   只有读音像识别错的地方直接按母本改，读音不像的（定语从句 / 状语从句、可以 / 不可以、两个 / 三个、多的少的字）
   只给「没把握」的建议（第二轮检查的人发现的，见 research/文字校正/母本优先/README.md 第 7 节）。
5. 母本是一整串话，但录音里挨着的句子在母本里不一定挨着（不同的课连在一起、删掉的句子不在母本里）：
   对上的范围不能靠两三个常说的字（「我们」「的时候」）跨进母本的上一句 / 下一句（_trim_lines），句子开头 / 结尾
   没对上的字也不能算成母本上一句 / 下一句的字（_edge_anchor / _extend 只在同一句里找）。
6. 母本里好几处字一模一样、只有标点不一样时，标点只改这几处都一样的（Segment.alts，按它们的交集改）。

对外接口：find_segments(text, ref, hint_id, skips) -> (tokens, [Segment])、segment_edits(text, toks, ref, seg)、
segment_pieces（带上每一小处属于哪一处整的改动，写说明用）、covered_ranges(toks, segs)、line_no(ref, m)
"""

from __future__ import annotations

import bisect
import difflib
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import List, Optional, Sequence, Tuple

from voicetwin.data import proofcheck as pc
from voicetwin.data import transcript_fix as tf

#: 相似度到这么多才算「母本里有这一句」（读音对上的字数 ÷ 两边长的那个）。在老师的母本上量出来的（分布.py）：
#: 同一批句子（修缮前 → 修缮后，123 句）最低 0.867；母本里每一句拿掉它自己再找，别的句子最像的（不算母本自己前后
#: 不一致的那一处「想得 / 显得」）最高 0.842。取中间的 0.85
MATCH_MIN = 0.85
#: 这一句至少这么多个字 / 词才按母本改（太短的话母本里到处都有，比如「一下 / 以下」，说明不了录音里是哪个）
MIN_TOKENS = 4
#: 只对上一部分时，那一部分至少这么多个字 / 词（两句合成一句、一句里一半是新的话），而且必须正好是母本里完整的一句。
#: 量出来的：8 的时候母本里 8 个字的一句「会想得非常不自然。」（母本里漏改的识别错，应该是「显得」）被当成别的句子的
#: 一部分，把别的句子里对的「显得」改成了「想得」；10 以后这种很短的句子不会被拿来改别的长句子
PART_MIN = 10
#: 句子开头 / 结尾没对上的字，最多这么多个才看是不是母本里挨着的字被听错了
EDGE_MAX = 3
#: 两个候选差不多一样像（相差不到这么多）时：同一个 id 的那一句优先；写法不一样、分不出是哪一个时不改
TIE_EPS = 0.02
#: 找连着对上的几段时，中间每空一个字扣的分（对上一个字加 1 分）
GAP_COST = 0.4
#: 对上的范围跨过母本的句子边界时，边界外面那一小段至少要有这么多个字读音一模一样（两个字的「我们」「所以」到处都有，
#: 不能靠它跨进母本的上一句 / 下一句；第二轮检查的人发现的）
MIN_CROSS = 3


@dataclass
class Segment:
    """这一句的第 r1 ~ r2 个单位（不含 r2）对上母本的第 m1 ~ m2 个单位。ops：读音对齐的结果（位置都是绝对的）。"""

    r1: int
    r2: int
    m1: int
    m2: int
    sim: float
    ops: List[Tuple[str, int, int, int, int]] = field(default_factory=list)
    hint: bool = False  # 是同一个 id 的那一句
    ambiguous: bool = False  # 母本里有好几处一样像、写法不一样：分不出是哪一处，不按它改
    keys_equal: int = 0  # 写法也一模一样的字数（一样像时挑写法更像的）
    eq: int = 0  # 读音对上的字数
    q: float = 0.0  # 对整句（这一次要找的范围）来说有多像：读音对上的字数 ÷ max(整句的字数, 母本那一段的字数)
    #: 母本里别的地方字也一模一样、差不多一样像（只有标点可能不一样）：标点只改这几处都一样的（segment_pieces）
    alts: List["Segment"] = field(default_factory=list)

    @property
    def length(self) -> int:
        return self.r2 - self.r1


# ============================================================================ 读音像不像（句子开头 / 结尾）
def _near_han(x: tf.Tk, y: tf.Tk) -> bool:
    """两个汉字读音像：模糊读音一样，或者声母一样，或者韵母一样（电影 / 定语、零 / 连）。"""
    if x.fz == y.fz:
        return True
    xi, xf = tf._split_py(x.fz)
    yi, yf = tf._split_py(y.fz)
    return bool((xi and xi == yi) or (xf and xf == yf))


def _close_lat(x: tf.Tk, y: tf.Tk) -> bool:
    """两个英文词拼法很像，或者读音代码一样（clouse / clause）。"""
    return x.snd == y.snd or difflib.SequenceMatcher(None, x.key, y.key, autojunk=False).ratio() >= 0.75


def _near_lat(x: tf.Tk, y: tf.Tk) -> bool:
    a, b = x.snd[3:], y.snd[3:]
    if not a or not b:
        return False
    return a[0] == b[0] or difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.5


def _plausible(xs: Sequence[tf.Tk], ys: Sequence[tf.Tk], strict: bool = False) -> bool:
    """句子开头 / 结尾这几个字（xs）是不是母本里挨着的那几个字（ys）被听错了：读音得像。
    strict=True（跨过母本句子边界的那一小段用）：汉字要模糊读音一样（不是只有声母或者韵母一样：
    「今天 / 具体」声母一样，但不是听错），英文要拼法很像。"""
    if not xs or not ys:
        return False
    kx, ky = {t.kind for t in xs}, {t.kind for t in ys}
    if kx == {"han"} and ky == {"lat"}:
        return tf.sounds_like_english([t.tone for t in xs], [t.key for t in ys])
    if kx == {"lat"} and ky == {"han"}:
        return tf.sounds_like_english([t.tone for t in ys], [t.key for t in xs])
    if len(xs) != len(ys):
        return False
    for x, y in zip(xs, ys):
        if x.kind != y.kind:
            return False
        if x.kind == "han" and not (x.fz == y.fz if strict else _near_han(x, y)):
            return False
        if x.kind == "lat" and not (_close_lat(x, y) if strict else _near_lat(x, y)):
            return False
        if x.kind == "other" and x.key != y.key:
            return False
    return True


# ============================================================================ 母本里的一句一句
def _line_table(ref: tf.Reference) -> Tuple[List[int], List[int]]:
    """母本每一句第一个字的位置、最后一个字后面的位置（排好序）。母本的字是连着编号的，所以上一句的结尾就是下一句的开头。"""
    got = getattr(ref, "_mf_lines", None)
    if got is None:
        got = (sorted(ref.line_firsts), sorted(ref.line_ends))
        try:
            ref._mf_lines = got
        except AttributeError:
            pass
    return got


def _line_start(ref: tf.Reference, m: int) -> int:
    """母本第 m 个字 / 词所在的那一句从哪里开始。"""
    firsts = _line_table(ref)[0]
    k = bisect.bisect_right(firsts, m) - 1
    return firsts[k] if k >= 0 else 0


def _line_end(ref: tf.Reference, m: int) -> int:
    """母本第 m 个字 / 词所在的那一句在哪里结束（最后一个字后面）。"""
    ends = _line_table(ref)[1]
    k = bisect.bisect_right(ends, m)
    return ends[k] if k < len(ends) else len(ref)


def line_no(ref: tf.Reference, m: int) -> int:
    """母本第 m 个字 / 词在第几句（只算有字的句子，从 0 开始）：前后挨着的片段是不是对上母本里前后挨着的句子。"""
    return max(0, bisect.bisect_right(_line_table(ref)[0], m) - 1)


# ============================================================================ 在母本里找这一句
def _chain(blocks: Sequence[Tuple[int, int, int]], n: int) -> Optional[Tuple[int, int, int, int]]:
    """连着对上的几段（a, b, 长度）里，挑「对上的多、中间空的少」的一串：(这一句开始, 结束, 母本开始, 结束)。
    只有 1 个字的对上不能当一串的开头 / 结尾（多半是碰巧），很短的句子（≤ 3 个字）除外。"""
    anchors = [blk for blk in blocks if blk[2] >= 2 or (n <= 3 and blk[2] >= 1)]
    best: Optional[Tuple[float, int, int, int, int, int]] = None
    for p in range(len(anchors)):
        for q in range(p, len(anchors)):
            a1, b1 = anchors[p][0], anchors[p][1]
            a2, b2 = anchors[q][0] + anchors[q][2], anchors[q][1] + anchors[q][2]
            matched = sum(s for a, b, s in blocks if a >= a1 and a + s <= a2 and b >= b1 and b + s <= b2)
            val = matched - GAP_COST * ((a2 - a1 - matched) + (b2 - b1 - matched))
            if best is None or (val, matched) > (best[0], best[1]):
                best = (val, matched, a1, a2, b1, b2)
    return best[2:] if best else None


def _edge_anchor(fid: Sequence[int], ref: tf.Reference, lo: int, hi: int, r1: int, r2: int, m1: int, m2: int,
                 limit: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """句子第一个 / 最后一个字和母本里挨着的字一模一样（读音），中间只隔着几个对不上的字（被按的连接 / 被and连接、
    vichy sleeping / which is sleeping）：从这个字算起（中间的就是听错的）。只隔着 1~EDGE_MAX 个字才算。"""
    if 0 < r1 - lo <= EDGE_MAX + 1:
        gap = r1 - lo - 1
        for x in sorted(range(max(limit[0], m1 - EDGE_MAX - 1), m1), key=lambda x: abs((m1 - x - 1) - gap)):
            if ref.fid[x] == fid[lo]:
                r1, m1 = lo, x
                break
    if 0 < hi - r2 <= EDGE_MAX + 1:
        gap = hi - r2 - 1
        for y in sorted(range(m2, min(limit[1], m2 + EDGE_MAX + 1)), key=lambda y: abs((y - m2) - gap)):
            if ref.fid[y] == fid[hi - 1]:
                r2, m2 = hi, y + 1
                break
    return r1, r2, m1, m2


def _extend(toks: Sequence[tf.Tk], ref: tf.Reference, lo: int, hi: int, r1: int, r2: int, m1: int, m2: int,
            limit: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """句子开头 / 结尾没对上的 1~EDGE_MAX 个字：读音像母本里挨着的那几个字，就算对上了（是那几个字被听错了）。
    limit：母本里能用的范围（拿掉的句子不能用）。"""
    head = r1 - lo
    if 0 < head <= EDGE_MAX:
        for take in _edge_lengths(toks[lo:r1]):
            if m1 - take >= limit[0] and _plausible(toks[lo:r1], ref.toks[m1 - take:m1]):
                r1, m1 = lo, m1 - take
                break
    tail = hi - r2
    if 0 < tail <= EDGE_MAX:
        for take in _edge_lengths(toks[r2:hi]):
            if m2 + take <= limit[1] and _plausible(toks[r2:hi], ref.toks[m2:m2 + take]):
                r2, m2 = hi, m2 + take
                break
    return r1, r2, m1, m2


def _edge_lengths(xs: Sequence[tf.Tk]) -> List[int]:
    """开头 / 结尾这几个字在母本里可能对应几个字：一样多；汉字听成英文（艾子 → as）时 1~2 个英文词，反过来 1~3 个汉字。"""
    kinds = {t.kind for t in xs}
    out = [len(xs)]
    if kinds == {"han"}:
        out += [1, 2]
    elif kinds == {"lat"}:
        out += [1, 2, 3]
    return [k for i, k in enumerate(out) if k > 0 and k not in out[:i]]


def _final_ops(fid: Sequence[int], ref: tf.Reference, r1: int, r2: int, m1: int, m2: int
               ) -> List[Tuple[str, int, int, int, int]]:
    sm = difflib.SequenceMatcher(None, list(fid[r1:r2]), ref.fid[m1:m2], autojunk=False)
    return [(tag, i1 + r1, i2 + r1, j1 + m1, j2 + m1) for tag, i1, i2, j1, j2 in sm.get_opcodes()]


def _piece_weak(toks: Sequence[tf.Tk], ref: tf.Reference, ops: Sequence[Tuple[str, int, int, int, int]],
                j_lo: int, j_hi: int, inner: int) -> bool:
    """对上的范围跨过了母本的句子边界时，边界外面那一小段（母本的 [j_lo, j_hi)）是不是碰巧对上的：
    读音对上的不到 MATCH_MIN，而且有读音不像听错的地方（多的 / 少的字、读音不像的字）。
    inner：靠里的那个边界（正好在边界上、这一句多出来的字算在外面这一段：宁可不跨过去）。
    例子：「……跟as完全不一样。今天我们」对上母本「……不一样。当我们使用……」——「今天」和「当」读音不像，
    只是「我们」碰巧一样，不能把「今天」改成「当」（第二轮检查的人发现的）。"""
    eq = row_n = 0
    bad = False
    for tag, i1, i2, j1, j2 in ops:
        if tag == "delete":  # 这一句多出来的字（母本里没有；「呢、啊」也算：跨过去的那一小段要一模一样或者读音一样）
            if j_lo < j1 < j_hi or j1 == inner:
                row_n += i2 - i1
                bad = True
            continue
        lo_, hi_ = max(j1, j_lo), min(j2, j_hi)
        if hi_ <= lo_:
            continue
        if tag == "equal":
            eq += hi_ - lo_
            row_n += hi_ - lo_
        elif tag == "replace":
            row_n += i2 - i1
            bad = bad or not _plausible(toks[i1:i2], ref.toks[j1:j2], strict=True)
        else:  # insert：母本多出来的字
            bad = True
    if eq < MIN_CROSS:
        return True  # 只有一两个字一样（「所以」「我们」）：碰巧的
    return bad and eq < MATCH_MIN * max(row_n, j_hi - j_lo) - 1e-9


def _row_at(ops: Sequence[Tuple[str, int, int, int, int]], cut: int, tail: bool) -> Optional[int]:
    """母本的位置 cut（一句的边界）对应这一句的哪个位置。跨过边界的一处改动（replace）整个算在被切掉的那一头；
    正好在边界上、这一句多出来的字也算在被切掉的那一头。tail=True：切掉后面（返回留下的结尾），否则切掉前面（返回留下的开头）。"""
    if tail:
        for tag, i1, i2, j1, j2 in ops:
            if tag == "delete" and j1 == cut:
                return i1
            if j2 > cut:
                return i1 + (cut - j1 if tag == "equal" and j1 < cut else 0)
        return None
    for tag, i1, i2, j1, j2 in reversed(ops):
        if tag == "delete" and j1 == cut:
            return i2
        if j1 < cut:
            return i2 - (j2 - cut if tag == "equal" and j2 > cut else 0)
    return None


def _trim_lines(toks: Sequence[tf.Tk], fid: Sequence[int], ref: tf.Reference, r1: int, r2: int, m1: int, m2: int
                ) -> Optional[Tuple[int, int, int, int]]:
    """对上的范围跨过母本的句子边界时，边界外面那一头是碰巧对上的（_piece_weak）就切掉：母本是一整串话，
    但母本里的下一句不一定是录音里的下一句（不同的课连在一起、老师删掉的句子不在母本里）。
    两句合成一个片段的（每一句都对得上）照样跨过去。"""
    for _ in range(8):
        if r2 - r1 < 2 or m2 - m1 < 2:
            return None
        ops = _final_ops(fid, ref, r1, r2, m1, m2)
        cut = _line_start(ref, m2 - 1)
        if m1 < cut and _piece_weak(toks, ref, ops, cut, m2, cut):
            at = _row_at(ops, cut, tail=True)
            if at is None:
                return None
            r2, m2 = at, cut
            continue
        cut = _line_end(ref, m1)
        if cut < m2 and _piece_weak(toks, ref, ops, m1, cut, cut):
            at = _row_at(ops, cut, tail=False)
            if at is None:
                return None
            r1, m1 = at, cut
            continue
        break
    if r2 - r1 < 2 or m2 - m1 < 2:
        return None
    return r1, r2, m1, m2


def _snap(toks: Sequence[tf.Tk], ref: tf.Reference, lo: int, hi: int, r1: int, r2: int, m1: int, m2: int,
          limit: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """这一句后面 / 前面还有别的话（母本里的一句和一句新的话在同一个片段里），母本那一句只差最后 / 最前面
    1~EDGE_MAX 个字没对上：那几个字读音像，就算对上了（是那几个字被听错了），这样对上的正好是母本完整的一句。"""
    end = min(limit[1], _line_end(ref, m2 - 1))
    if r2 < hi and 0 < end - m2 <= EDGE_MAX + 1:
        want = ref.toks[m2:end]
        for take in (_edge_lengths(want) if end - m2 <= EDGE_MAX else []):
            if r2 + take <= hi and _plausible(toks[r2:r2 + take], want):
                r2, m2 = r2 + take, end
                break
        else:  # 母本那一句的最后一个字在这一句后面不远处（中间隔着听错 / 漏掉的几个字：vichy sleeping / which is sleeping）
            for x in range(r2, min(hi, r2 + EDGE_MAX + 1)):
                if fid_of(toks, ref, x) == ref.fid[end - 1] and abs((x - r2) - (end - 1 - m2)) <= 1:
                    r2, m2 = x + 1, end
                    break
    start = max(limit[0], _line_start(ref, m1))
    if r1 > lo and 0 < m1 - start <= EDGE_MAX + 1:
        want = ref.toks[start:m1]
        for take in (_edge_lengths(want) if m1 - start <= EDGE_MAX else []):
            if r1 - take >= lo and _plausible(toks[r1 - take:r1], want):
                r1, m1 = r1 - take, start
                break
        else:  # 「关系代which」/ 母本「关系代词which」：母本那一句的第一个字在前面不远处
            for x in range(r1 - 1, max(lo - 1, r1 - EDGE_MAX - 2), -1):
                if fid_of(toks, ref, x) == ref.fid[start] and abs((r1 - x - 1) - (m1 - start - 1)) <= 1:
                    r1, m1 = x, start
                    break
    return r1, r2, m1, m2


def fid_of(toks: Sequence[tf.Tk], ref: tf.Reference, k: int) -> int:
    """这一句第 k 个字 / 词的读音编号（母本里没有的读音给 -1，不会和母本对上）。"""
    return ref.ids.get(toks[k].fz, -1)


def _in_window(toks: Sequence[tf.Tk], fid: Sequence[int], ref: tf.Reference, lo: int, hi: int,
               w0: int, w1: int) -> Optional[Segment]:
    """这一句的 lo ~ hi 和母本的 w0 ~ w1 这一段比：找出对上的范围，算相似度。"""
    sm = difflib.SequenceMatcher(None, list(fid[lo:hi]), ref.fid[w0:w1], autojunk=False)
    blocks = [(a + lo, b + w0, s) for a, b, s in sm.get_matching_blocks() if s]
    got = _chain(blocks, hi - lo)
    if got is None:
        return None
    got = _trim_lines(toks, fid, ref, *got)
    if got is None:
        return None
    r1, r2, m1, m2 = got
    # 句子开头 / 结尾没对上的字只在母本的同一句里找（不能算成母本上一句 / 下一句的字：「今天的」→「which we know,」）
    lim = (max(w0, _line_start(ref, m1)), min(w1, _line_end(ref, m2 - 1)))
    r1, r2, m1, m2 = _edge_anchor(fid, ref, lo, hi, r1, r2, m1, m2, limit=lim)
    r1, r2, m1, m2 = _extend(toks, ref, lo, hi, r1, r2, m1, m2, limit=lim)
    r1, r2, m1, m2 = _snap(toks, ref, lo, hi, r1, r2, m1, m2, limit=lim)
    got = _trim_lines(toks, fid, ref, r1, r2, m1, m2)  # 补上开头 / 结尾以后再看一次（跨过去的那一头可能变弱了）
    if got is None:
        return None
    r1, r2, m1, m2 = got
    ops = _final_ops(fid, ref, r1, r2, m1, m2)
    eq = sum(i2 - i1 for tag, i1, i2, _j1, _j2 in ops if tag == "equal")
    sim = eq / max(r2 - r1, m2 - m1, 1)
    same = sum(1 for tag, i1, i2, j1, _j2 in ops if tag == "equal"
               for k in range(i2 - i1) if toks[i1 + k].key == ref.toks[j1 + k].key)
    return Segment(r1, r2, m1, m2, sim, ops, keys_equal=same, eq=eq, q=eq / max(hi - lo, m2 - m1, 1))


def _cut(w0: int, w1: int, skips: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """候选位置去掉不能用的句子（老师上传的、就是这一句自己的那几行），剩下的几段。"""
    parts = [(w0, w1)]
    for a, b in skips:
        nxt = []
        for x0, x1 in parts:
            if b <= x0 or x1 <= a:
                nxt.append((x0, x1))
                continue
            if x0 < a:
                nxt.append((x0, a))
            if b < x1:
                nxt.append((b, x1))
        parts = nxt
    return [(x0, x1) for x0, x1 in parts if x1 - x0 >= 2]


def _target(ref: tf.Reference, seg: Segment) -> Tuple[str, ...]:
    return tuple(ref.keys[seg.m1:seg.m2])


def _acceptable(seg: Segment, toks: Sequence[tf.Tk], lo: int, hi: int, ref: tf.Reference) -> bool:
    """这一段算不算「母本里有这一句」：相似度到 MATCH_MIN；整句都对上了（开头 / 结尾没对上的只能是「嗯、啊」这种
    语气词），或者对上的正好是母本里完整的一句（几句）、至少 PART_MIN 个字（两句合成一句、其中一句是新的话）。
    只对上一句中间的一小段不算：常说的话（「这个句子」「我们来看一下」）到处都有，证明不了录音里怎么说。"""
    if seg.sim < MATCH_MIN - 1e-9 or seg.length < MIN_TOKENS:
        return False
    if all(_filler(toks[k]) for k in list(range(lo, seg.r1)) + list(range(seg.r2, hi))):
        return True  # 整句都对上了（开头 / 结尾多出来的只有「嗯、啊」这种语气词）
    return seg.length >= PART_MIN and seg.m1 in ref.line_firsts and seg.m2 in ref.line_ends


def _filler(t: tf.Tk) -> bool:
    return t.kind == "han" and t.key in pc.FILLER_CHARS


def _best(toks: Sequence[tf.Tk], fid: Sequence[int], ref: tf.Reference, lo: int, hi: int, hint_id: str,
          skips: Sequence[Tuple[int, int]]) -> Optional[Segment]:
    """这一句的 lo ~ hi 在母本里最像的一段（够不上 _acceptable 的不要）。按「对整句来说有多像」排：
    整句都对上的排在只对上一小段的前面（不然一小段一模一样的常说的话会把整句对上的挤掉）。"""
    probe = SimpleNamespace(fid=list(fid[lo:hi]))
    wins = list(tf._windows(probe, ref))
    hints = [] if not hint_id else list(ref.id_ranges.get(hint_id, []))
    for a, b in hints:
        wins.append((max(0, a - tf.MARGIN), min(len(ref), b + tf.MARGIN)))
    cands: List[Segment] = []
    for w0, w1 in wins:
        for x0, x1 in _cut(w0, w1, skips):
            seg = _in_window(toks, fid, ref, lo, hi, x0, x1)
            if seg is None or not _acceptable(seg, toks, lo, hi, ref):
                continue
            seg.hint = any(seg.m1 < b and a < seg.m2 for a, b in hints)
            if all((c.r1, c.r2, c.m1, c.m2) != (seg.r1, seg.r2, seg.m1, seg.m2) for c in cands):
                cands.append(seg)
    if not cands:
        return None
    cands.sort(key=lambda s: (-s.q, -s.sim, -s.keys_equal, s.m1))
    best = cands[0]
    near = [s for s in cands if s.q >= best.q - TIE_EPS]
    vetted = [s for s in near if s.m2 <= ref.unvetted_from]
    if vetted and len(vetted) < len(near):
        # 差不多一样像时，老师修缮过的母本（程序自带的）比上传的、没修缮过的可信：只看修缮过的
        cands = vetted + [s for s in cands if s not in near]
        best = cands[0]
    hinted = [s for s in cands if s.hint and s.q >= best.q - TIE_EPS]
    if hinted:  # 同一个 id 的那一句文字也对得上：用它（id 只当提示）
        return _to_line_edges(toks, fid, ref, lo, hi, hinted[0], hints)
    rivals = [s for s in cands[1:] if s.q >= best.q - TIE_EPS and (s.r1, s.r2) == (best.r1, best.r2)
              and not (s.m1 < best.m2 and best.m1 < s.m2)]
    mine = tuple(toks[k].key for k in range(best.r1, best.r2))
    if any(_target(ref, s) != _target(ref, best) for s in rivals):
        same = [s for s in [best] + rivals if _target(ref, s) == mine]
        if same:  # 其中一处和这一句一模一样：就是它，不用改（字一样、标点不一样的几处一起看，见 segment_pieces）
            same[0].alts = [s for s in same[1:] if not (s.m1 < same[0].m2 and same[0].m1 < s.m2)]
            return same[0]
        best.ambiguous = True  # 好几处一样像、写法又不一样：分不出是哪一处，不按它改
        return best
    # 母本里好几处字一模一样（只有标点可能不一样，比如「那就是that person。」和「就是that person」）：
    # 分不出是哪一处，标点只改这几处都一样的（以前用最前面那一处的标点，把对的句子加上了句号）
    best.alts = rivals
    return best


def _to_line_edges(toks: Sequence[tf.Tk], fid: Sequence[int], ref: tf.Reference, lo: int, hi: int, seg: Segment,
                   hints: Sequence[Tuple[int, int]]) -> Segment:
    """同一个 id 的那一句（文字也对得上）：这一句到头了、母本那一句只多出开头 / 结尾 1~EDGE_MAX 个字时，
    就是识别时漏了这几个字（「我们来看一下这个句子。」/「……句子吧。」），补上。
    不是同一个 id 的时候不补：可能只是切的位置不一样（一句切成了两句，后半句在下一个片段里）。"""
    line = next(((a, b) for a, b in hints if a <= seg.m1 and seg.m2 <= b), None)
    if line is None:
        return seg
    m1, m2 = seg.m1, seg.m2
    if seg.r1 == lo and 0 < m1 - line[0] <= EDGE_MAX:
        m1 = line[0]
    if seg.r2 == hi and 0 < line[1] - m2 <= EDGE_MAX:
        m2 = line[1]
    if (m1, m2) == (seg.m1, seg.m2):
        return seg
    ops = _final_ops(fid, ref, seg.r1, seg.r2, m1, m2)
    eq = sum(i2 - i1 for tag, i1, i2, _j1, _j2 in ops if tag == "equal")
    sim = eq / max(seg.r2 - seg.r1, m2 - m1, 1)
    if sim < MATCH_MIN - 1e-9:
        return seg
    return Segment(seg.r1, seg.r2, m1, m2, sim, ops, hint=True, keys_equal=seg.keys_equal, eq=eq,
                   q=eq / max(hi - lo, m2 - m1, 1))


def find_segments(text: str, ref: Optional[tf.Reference], hint_id: str = "",
                  skips: Sequence[Tuple[int, int]] = ()) -> Tuple[List[tf.Tk], List[Segment]]:
    """这一句在母本里对应的几段（按这一句里的位置排好）。先找整句最像的一段；只对上一部分时，剩下的部分
    （至少 PART_MIN 个字）再找。skips：母本里不能用的范围（老师上传的、就是这一句自己的那几行）。"""
    clip = tf._Clip(str(text or ""), ref) if ref is not None else None
    if clip is None or not clip.toks or not len(ref):
        return (list(clip.toks) if clip else []), []
    toks, fid = clip.toks, clip.fid
    segs: List[Segment] = []
    todo = [(0, len(toks))]
    while todo:
        lo, hi = todo.pop()
        if hi - lo < MIN_TOKENS:
            continue
        seg = _best(toks, fid, ref, lo, hi, hint_id, skips)
        if seg is None:
            continue
        segs.append(seg)
        if seg.r1 - lo >= PART_MIN:
            todo.append((lo, seg.r1))
        if hi - seg.r2 >= PART_MIN:
            todo.append((seg.r2, hi))
    segs.sort(key=lambda s: s.r1)
    return toks, segs


# ============================================================================ 按母本改
def segment_edits(text: str, toks: Sequence[tf.Tk], ref: tf.Reference, seg: Segment
                  ) -> List[Tuple[int, int, str]]:
    """对上的这一段里和母本不一样的地方 → [(开始, 结束, 改成母本的写法)]（位置按这一句的文字算）。见 segment_pieces。"""
    return [piece for piece, _whole in segment_pieces(text, toks, ref, seg)]


def segment_pieces(text: str, toks: Sequence[tf.Tk], ref: tf.Reference, seg: Segment
                   ) -> List[Tuple[Tuple[int, int, str], Tuple[int, int, str]]]:
    """[(一小处改动, 它属于的那一处整的改动)]：一处整的改动（「一声 → 医生」）按读音拆成一小处一小处（「一 → 医」
    「声 → 生」，老师自己改过的那个字不动、旁边的照样改）；写说明时按整的那一处写（不然会写出母本里没有的「医声」）。
    母本里好几处字一模一样、只有标点不一样（seg.alts）：只要这几处都一样的改动（标点不一样的不改）。"""
    out = _pieces(text, toks, ref, seg)
    for alt in seg.alts:
        theirs = {piece for piece, _whole in _pieces(text, toks, ref, alt)}
        out = [x for x in out if x[0] in theirs]
    return out


def _pieces(text: str, toks: Sequence[tf.Tk], ref: tf.Reference, seg: Segment
            ) -> List[Tuple[Tuple[int, int, str], Tuple[int, int, str]]]:
    """对上的这一段里和母本不一样的地方（一小处一小处，带上整的那一处）。
    整段按字比（英文按整个单词），所以读音一样写法不一样的、读音不一样的、多的、少的、英文大小写、中间的标点
    都按母本；对上的正好是母本一句的开头 / 结尾、这一句也到头了时，句首 / 句末的标点也按母本（Where is quiet? /
    where it's quiet.）。只是写法整理（全角 / 半角逗号）不一样的不算。"""
    from voicetwin.data import review as _review
    from voicetwin.utils.textutil import clean_transcript

    rs, re_ = toks[seg.r1].start, toks[seg.r2 - 1].end
    ms, me = ref.toks[seg.m1].start, ref.toks[seg.m2 - 1].end
    if seg.r1 == 0 and seg.m1 in ref.line_firsts:
        rs, ms = 0, ref.line_chars[ref.line_of[seg.m1]][0]
    if seg.r2 == len(toks) and seg.m2 in ref.line_ends:
        re_, me = len(text), ref.line_chars[ref.line_of_end[seg.m2]][1]
    elif seg.m2 in ref.line_ends and seg.r2 < len(toks):
        # 母本的一句到头了、这一句后面还有别的话（母本的一句和一句新的话在同一个片段里）：母本这一句末尾有标点时
        # 按母本（Where is quiet? → where it's quiet.）；母本末尾没有标点时不动（不把这一句里的逗号去掉）
        end = ref.line_chars[ref.line_of_end[seg.m2]][1]
        if ref.text[me:end].strip():
            re_, me = toks[seg.r2].start, end
    a, b = text[rs:re_], ref.text[ms:me].replace("\n", "")
    if a == b:
        return []
    out: List[Tuple[Tuple[int, int, str], Tuple[int, int, str]]] = []
    base = clean_transcript(text)
    for s, e, rep in _review.suggestion_edits(a, b):
        s, e = s + rs, e + rs
        for s2, e2, rep2 in _split(text, s, e, rep):
            rep2 = pc._pad(text, s2, e2, rep2)
            if clean_transcript(text[:s2] + rep2 + text[e2:]) == base:
                continue  # 只是写法整理不一样（英文后面的逗号全角 / 半角）：不算
            out.append(((s2, e2, rep2), (s, e, rep)))
    return out


def _split(text: str, s: int, e: int, rep: str) -> List[Tuple[int, int, str]]:
    """按字比出来的一处改动（「从具的」→「从句」）再按读音拆细：「具 → 句」和「删掉『的』」分开。
    这样老师自己改过的那个字（采用过的「的」）不动，旁边该按母本改的字照样改（_protect 是一处一处看的）。
    拆完和原来改出来的不一样（标点挨着等）就不拆。"""
    old = text[s:e]
    a, b = tf.tokens(old), tf.tokens(rep)
    if len(a) + len(b) < 3 or not a or not b:
        return [(s, e, rep)]
    sm = difflib.SequenceMatcher(None, [t.fz for t in a], [t.fz for t in b], autojunk=False)
    parts: List[Tuple[int, int, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                x, y = a[i1 + k], b[j1 + k]
                if old[x.start:x.end] != rep[y.start:y.end]:
                    parts.append((s + x.start, s + x.end, rep[y.start:y.end]))
            continue
        new = rep[b[j1].start:b[j2 - 1].end] if j2 > j1 else ""
        if i2 > i1:
            parts.append((s + a[i1].start, s + a[i2 - 1].end, new))
        else:
            at = s + (a[i1 - 1].end if i1 > 0 else a[0].start)
            parts.append((at, at, new))
    if not parts:
        return [(s, e, rep)]
    whole = text[:s] + rep + text[e:]
    out, left = text, len(text) + 1
    for s2, e2, r2 in sorted(parts, reverse=True):
        if e2 > left:
            return [(s, e, rep)]
        out, left = out[:s2] + r2 + out[e2:], s2
    return sorted(parts) if out == whole else [(s, e, rep)]


def covered_ranges(toks: Sequence[tf.Tk], segs: Sequence[Segment]) -> List[Tuple[int, int]]:
    """母本对上的部分在这一句里的位置（字符，[开始, 结束)）。"""
    return [(toks[s.r1].start, toks[s.r2 - 1].end) for s in segs if s.r2 > s.r1]


__all__ = ["MATCH_MIN", "MIN_TOKENS", "PART_MIN", "Segment", "find_segments", "segment_edits", "segment_pieces",
           "covered_ranges", "line_no"]
