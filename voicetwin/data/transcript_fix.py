"""文字校正（v18.5）：用老师自己的逐字稿（txt）检查校对表里识别出来的文字，结果写进「可能有错」列。

老师 10-02 的要求：在查错字的地方上传逐字稿，点「文字校正」，和识别出来的文字一句一句比对，结果覆盖「可能有错」
那一列；没上传就照旧显示自动查错字的结果。老师补充：逐字稿「只是我平时讲课和说话的习惯……不一定是一模一样的」，
所以不能逐字硬对，要智能比对。

怎么比（全部在本机算，不用模型、不联网）：
1. 按读音对齐。每个汉字换成拼音（不带声调；zh/z、ch/c、sh/s、n/l、ang/an、eng/en、ing/in 当成一样），
   英文词换成读音代码（there 和 their 一样）。识别引擎听错的字，读音和原来的字一样或很像（定语 → 定于），
   按读音还是对得上；老师当时换了个说法，读音也不一样，就不算错（录音为准）。
2. 只在前后文对得上的地方下结论：
   - 整句对齐：这一句的大部分（≥ 60%）按读音能和逐字稿里的某一段对上（逐字稿就是这节课的讲稿时）；
   - 局部对齐：前后一共至少 3 个字和逐字稿里某处一模一样（逐字稿只是平时的说法时：常说的术语、口头禅）。
3. 能认出来的错：读音一样或很像的别字（定于 → 定语）；英文被写成了汉字（艾子 → as）、汉字被写成了英文（the → 的）；
   英文拼错或写成读音一样的词（clouse → clause，there → their）；读音很像的中文数字。
   读音完全一样的别字（最高集 → 最高级）只在整句对齐时标，并且写明「不影响训练，改不改都行」。
4. 不标：两种写法都常见的同音字（他/她/它、的/地/得、做/作）；多说 / 少说的字；读音不一样的不同说法；
   局部对齐时读音完全一样的单个字（证据不够），以及识别出来的写法在逐字稿里本来就出现过的（那也是老师的说法）。
5. 逐字稿对得上、证明没错的地方，原来自动查错字标的红去掉；逐字稿里没有对应内容的地方，保留原来自动查错字的结果
   （原因前面写「自动检查：」）。老师点过「这句没错」（文字没再改过）的句子不动。

结果写进 record["suspect"]，和自动查错字同样的格式（校对表的标红、「修改建议」的采用按钮都照常能用），另外有：
  src="transcript"、text=比对时的文字（含没保存的修改）、ref=逐字稿里对应的那段话（点这一行时显示）。
原来自动查错字的结果另存在 record["suspect_auto"]，再点一次「文字校正」时用它（不会把上次逐字稿的结果当成自动检查的）。

对外接口：
- read_text_file(path) -> str：读 txt（UTF-8 / UTF-16 / GBK 都行）
- save_transcripts(project, paths) / load_transcripts(project) / transcript_info(project)
- check_with_transcript(project, text=None, progress=None) -> dict
"""

from __future__ import annotations

import difflib
import re
import shutil
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple

from voicetwin.data import proofcheck as pc
from voicetwin.utils.log import get_logger

try:  # 停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    def _check_cancel() -> None:
        return None

log = get_logger("transcript_fix")

ProgressFn = Callable[[float, str], None]

TRANSCRIPT_DIR = "逐字稿"  # 声音文件夹里存老师上传的逐字稿（再点「文字校正」不用重新上传）
TEXT_SUFFIXES = (".txt",)
MAX_TOKENS = 400_000  # 逐字稿太长时只用前面这么多字（大约 25 节课），免得占太多内存
MIN_CHARS = 10

# ---------------------------------------------------------------------------- 对齐的参数
S_COVERAGE = 0.6  # 一句里至少这么多字按读音对得上：算「整句对齐」
S_MIN_MATCH = 4
L_MIN_CTX = 3  # 局部对齐：不一样的地方前后一共至少这么多个一模一样的字
BUCKET = 4
MARGIN = 8
TOP_K = 6
MAX_HITS = 400  # 逐字稿里出现太多次的三个音（"我们的"）不拿来找位置
CONFIRM_RUN_L = 4  # 局部对齐时，连续这么多个字一模一样，才算「逐字稿证明这几个字没错」

W = {  # 每种证据的分量（和自动查错字一样合起来打分，≥ 0.45 标红；每条单独都够标红）
    ("near", "S"): 0.85, ("near", "L"): 0.6,
    ("same", "S"): 0.6, ("same", "L"): 0.5,
    ("cjk_en", "S"): 0.75, ("cjk_en", "L"): 0.6,
    ("en_cjk", "S"): 0.7, ("en_cjk", "L"): 0.55,
    ("en", "S"): 0.7, ("en", "L"): 0.55,
    ("num", "S"): 0.6, ("num", "L"): 0.5,
}
MULTI_BONUS = 0.15  # 局部对齐时逐字稿里好几处都这么写
AGREE_BONUS = 0.15  # 另一个识别引擎（自动查错字）也听成这样
AUTO_PREFIX = "自动检查："


# ============================================================================ 读 txt、存逐字稿
def read_text_file(path: Any) -> str:
    """读老师的 txt：记事本存的 UTF-8（带不带 BOM）、「Unicode」（UTF-16）、ANSI（GBK）都能读。"""
    raw = Path(path).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    head = raw[:4000]
    if head and head.count(b"\x00") > len(head) // 4:  # 没有 BOM 的 UTF-16
        for enc in ("utf-16-le", "utf-16-be"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def transcript_dir(project: Any) -> Path:
    return Path(project.root) / TRANSCRIPT_DIR


def _useful_chars(text: str) -> int:
    return sum(1 for t in pc.tokenize(text))


def _file_name(p: Any) -> str:
    """gradio 传来的可能是路径字符串，也可能是带 .name 的临时文件对象。"""
    return str(getattr(p, "name", p) or "")


def save_transcripts(project: Any, paths: Iterable[Any]) -> Dict[str, Any]:
    """把这次上传的逐字稿存进声音文件夹（替换上次的），统一存成 UTF-8。返回 transcript_info。

    不是 txt、读出来没有文字的文件：说明原因（ValueError），一个都不存。"""
    items: List[Tuple[str, str]] = []
    bad: List[str] = []
    for p in paths or []:
        src = Path(_file_name(p))
        if not src.name:
            continue
        if src.suffix.lower() not in TEXT_SUFFIXES:
            bad.append(f"「{src.name}」不是 txt 文件")
            continue
        try:
            text = read_text_file(src)
        except OSError as exc:
            bad.append(f"「{src.name}」读不出来（{exc}）")
            continue
        if _useful_chars(text) < MIN_CHARS:
            bad.append(f"「{src.name}」里几乎没有文字")
            continue
        items.append((src.name, text))
    if bad:
        raise ValueError("逐字稿没有存上：" + "；".join(bad) + "。请上传记事本保存的 .txt 文件（Word 文档可以先「另存为」纯文本 .txt）。")
    if not items:
        raise ValueError("没有收到逐字稿文件，请先选好 txt 文件再点「文字校正」。")
    folder = transcript_dir(project)
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    used: Set[str] = set()
    for name, text in items:
        stem = re.sub(r'[\\/:*?"<>|]+', "_", Path(name).stem).strip() or "逐字稿"
        out, k = f"{stem}.txt", 2
        while out.lower() in used:
            out, k = f"{stem}_{k}.txt", k + 1
        used.add(out.lower())
        (folder / out).write_text(text.replace("\r\n", "\n"), encoding="utf-8")
    info = transcript_info(project)
    log.info(f"已保存逐字稿：{'、'.join(info['files'])}（共 {info['chars']} 字）")
    return info


def load_transcripts(project: Any) -> Tuple[str, List[str]]:
    """存好的逐字稿（几个文件接在一起，中间空一行）和文件名。没有时返回 ("", [])。"""
    folder = transcript_dir(project)
    if not folder.is_dir():
        return "", []
    files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES)
    texts, names = [], []
    for p in files:
        try:
            texts.append(read_text_file(p))
            names.append(p.name)
        except OSError:
            continue
    return "\n\n".join(texts), names


def transcript_info(project: Any) -> Dict[str, Any]:
    text, names = load_transcripts(project)
    return {"files": names, "chars": _useful_chars(text) if text else 0}


# ============================================================================ 读音
class Tk(NamedTuple):
    """一个可以比较的单位（汉字一个字一个、英文一个词一个、数字一整段）。start/end 是在原文里的位置。"""

    key: str  # 写法（简体字 / 小写英文 / "#数值"）
    snd: str  # 读音（不带声调的拼音 / 英文读音代码 / "#数值"）
    fz: str  # 模糊读音（zh=z、ang=an……）
    tone: str  # 带声调的拼音（判断「读音完全一样」）
    kind: str  # han / lat / num / other
    start: int
    end: int


@lru_cache(maxsize=1)
def _pinyin_fn() -> Optional[Callable[[str], List[str]]]:
    """pypinyin（GPT-SoVITS 整合包里有，训练处理中文就靠它）。没有时返回 None。"""
    try:
        from pypinyin import Style, lazy_pinyin  # type: ignore
    except Exception:
        return None

    def fn(s: str) -> List[str]:
        try:
            return list(lazy_pinyin(s, style=Style.TONE3, neutral_tone_with_five=True, errors=lambda x: list(x)))
        except TypeError:  # 很旧的 pypinyin
            return list(lazy_pinyin(s, style=Style.TONE3, errors=lambda x: list(x)))

    try:
        fn("测试")
    except Exception:
        return None
    return fn


def has_pinyin() -> bool:
    return _pinyin_fn() is not None


_INI = ("zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x", "r", "z", "c", "s",
        "y", "w")
_INI_FZ = {"zh": "z", "ch": "c", "sh": "s", "l": "n"}


def _split_py(py: str) -> Tuple[str, str]:
    ini = next((i for i in _INI if py.startswith(i) and len(py) > len(i)), "")
    return ini, py[len(ini):]


@lru_cache(maxsize=8192)
def fuzzy(py: str) -> str:
    """模糊读音：zh/z、ch/c、sh/s、n/l 不分，ang/an、eng/en、ing/in、ong/on 不分（南方口音、识别引擎常混）。"""
    if not py or not py.isascii() or not py.isalpha():
        return py
    ini, fin = _split_py(py)
    if fin.endswith("ng") and len(fin) > 2:
        fin = fin[:-1]
    return _INI_FZ.get(ini, ini) + fin


@lru_cache(maxsize=8192)
def en_code(word: str) -> str:
    """英文词的读音代码（简化的 Metaphone）：there = their，clause = clouse，know = no，write = right。"""
    w = "".join(ch for ch in str(word).lower() if "a" <= ch <= "z")
    if not w:
        return ""
    for a, b in (("kn", "n"), ("gn", "n"), ("pn", "n"), ("wr", "r"), ("ps", "s"), ("wh", "w"), ("x", "s"),
                 ("gh", "g")):
        if w.startswith(a):
            w = b + w[len(a):]
            break
    w = w[0] + w[1:].replace("gh", "")
    for a, b in (("tch", "x"), ("sch", "sk"), ("ch", "x"), ("sh", "x"), ("th", "0"), ("ph", "f"), ("ck", "k"),
                 ("dge", "j"), ("qu", "kw"), ("q", "k"), ("x", "ks"), ("z", "s")):
        w = w.replace(a, b)
    w = "".join(("s" if nxt in "eiy" else "k") if ch == "c" else ch for ch, nxt in zip(w, w[1:] + " "))
    if w.endswith("mb"):
        w = w[:-1]
    if len(w) > 2 and w.endswith("e") and w[-2] not in "aeiou":
        w = w[:-1]
    out = [w[0]]
    for i in range(1, len(w)):
        ch = w[i]
        nxt = w[i + 1] if i + 1 < len(w) else ""
        if ch in "aeiouy":
            continue
        if ch in "wh" and (not nxt or nxt not in "aeiou"):
            continue
        if out[-1] != ch:
            out.append(ch)
    return "".join(out).upper()


_CLS = {"p": "P", "b": "P", "t": "T", "d": "T", "0": "T", "k": "K", "g": "K", "f": "F", "v": "F", "s": "S", "x": "S",
        "j": "S", "z": "S", "c": "S", "m": "M", "n": "N", "l": "L", "r": "L", "h": "H"}
_PY_CLS = {"b": "P", "p": "P", "d": "T", "t": "T", "g": "K", "k": "K", "f": "F", "m": "M", "n": "N", "l": "L", "r": "L",
           "h": "H", "z": "S", "c": "S", "s": "S", "zh": "S", "ch": "S", "sh": "S", "j": "S", "q": "S", "x": "S"}


def _collapse(s: str) -> str:
    out: List[str] = []
    for ch in s:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(out)


def _en_skeleton(words: Sequence[str]) -> str:
    out = ""
    for w in words:
        code = en_code(w).lower()
        if code[:1] in "aeiou":
            code = code[1:]
        out += "".join(_CLS.get(ch, "") for ch in code)
    return _collapse(out)


def _py_skeleton(pys: Sequence[str]) -> str:
    out = ""
    for py in pys:
        ini, fin = _split_py(_toneless(str(py)))
        out += _PY_CLS.get(ini, "")
        if fin.endswith("n") or fin.endswith("ng"):
            out += "N"
    return _collapse(out)


def _en_syllables(words: Sequence[str]) -> int:
    return sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in words)


def sounds_like_english(pys: Sequence[str], words: Sequence[str]) -> bool:
    """几个汉字的读音像不像这几个英文词（艾子 ≈ as，派森 ≈ python，哈喽 ≈ hello；句子 ≠ sentence）。"""
    if not pys or not words:
        return False
    if len(pys) > 2 * _en_syllables(words) + 1:
        return False
    a, b = _py_skeleton(pys), _en_skeleton(words)
    if not a and not b:
        return True
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio() >= 0.5


def _han_snd(keys: Sequence[str]) -> List[str]:
    """一串汉字的带声调拼音（按上下文定多音字）；没有 pypinyin 时用同音字小表。"""
    fn = _pinyin_fn()
    if fn is None:
        return [pc._HOMO.get(k, k) for k in keys]
    s = "".join(keys)
    try:
        out = fn(s)
    except Exception:
        out = []
    if len(out) != len(keys):
        out = []
        for k in keys:
            try:
                r = fn(k)
                out.append(r[0] if r else k)
            except Exception:
                out.append(k)
    return out


def _toneless(py: str) -> str:
    return py[:-1] if py[-1:].isdigit() else py


def tokens(text: str) -> List[Tk]:
    """切成可以比较的单位，并标上读音。"""
    text = str(text or "")
    # 单独一个中文数字（一下、一定、十分、零活里的「一、十、零」）当普通汉字比读音：容易 → 容一 才认得出来
    raw = [pc.Tok(text[x.start:x.end], x.start, x.end) if x.key == "#" and x.end - x.start == 1
           and text[x.start] in pc._CN_NUM else x for x in pc.tokenize(text)]
    out: List[Optional[Tk]] = [None] * len(raw)
    i = 0
    while i < len(raw):
        t = raw[i]
        if pc._CJK_RE.match(t.key or ""):
            j = i + 1
            while j < len(raw) and pc._CJK_RE.match(raw[j].key or "") and raw[j].start in (raw[j - 1].end, raw[j - 1].start):
                j += 1
            run = raw[i:j]
            tones = _han_snd([x.key for x in run])
            for x, tn in zip(run, tones):
                if _pinyin_fn() is None:
                    snd = tn
                else:
                    snd = _toneless(tn)
                out[i + run.index(x)] = Tk(x.key, snd, fuzzy(snd), tn, "han", x.start, x.end)
            i = j
            continue
        if t.key == "#":
            k = "#" + str(t.val if t.val is not None else text[t.start:t.end])
            out[i] = Tk(k, k, k, text[t.start:t.end], "num", t.start, t.end)
        elif pc._latin_key(t.key):
            code = "en:" + en_code(t.key)
            out[i] = Tk(t.key, code, code, t.key, "lat", t.start, t.end)
        else:
            out[i] = Tk(t.key, t.key, t.key, t.key, "other", t.start, t.end)
        i += 1
    return [x for x in out if x is not None]


def _num_pinyin(surface: str) -> Optional[List[str]]:
    """中文数字的读音（"四十" → si shi）；不是纯中文数字时返回 None。"""
    if not surface or not all(ch in pc._CN_NUM for ch in surface):
        return None
    return [_toneless(p) for p in _han_snd(list(surface))]


# ============================================================================ 逐字稿
class Reference:
    """处理好的逐字稿：每个字的读音、按读音找位置的索引、哪些写法出现过。"""

    def __init__(self, text: str, progress: Optional[ProgressFn] = None):
        self.text = str(text or "")
        toks = tokens(self.text)
        self.truncated = len(toks) > MAX_TOKENS
        self.toks = toks[:MAX_TOKENS]
        self.keys = [t.key for t in self.toks]
        self.ids: Dict[str, int] = {}
        self.fid = [self.ids.setdefault(t.fz, len(self.ids)) for t in self.toks]
        self.idx2: Dict[int, List[int]] = defaultdict(list)
        self.idx3: Dict[int, List[int]] = defaultdict(list)
        f = self.fid
        for i in range(len(f) - 1):
            self.idx2[(f[i] << 21) | f[i + 1]].append(i)
            if i + 2 < len(f):
                self.idx3[(f[i] << 42) | (f[i + 1] << 21) | f[i + 2]].append(i)
        self.joined = "\x1f" + "\x1f".join(self.keys) + "\x1f"
        self.latin = Counter(t.key for t in self.toks if t.kind == "lat")

    def __len__(self) -> int:
        return len(self.toks)

    def has(self, keys: Sequence[str]) -> bool:
        """这几个字（按写法）在逐字稿里连着出现过没有。"""
        return bool(keys) and ("\x1f" + "\x1f".join(keys) + "\x1f") in self.joined

    def count(self, keys: Sequence[str]) -> int:
        return self.joined.count("\x1f" + "\x1f".join(keys) + "\x1f") if keys else 0

    def ids_of(self, toks: Sequence[Tk]) -> List[int]:
        """识别文字的模糊读音换成逐字稿用的编号；逐字稿里没有的读音给一个不会对上的编号。"""
        out, extra = [], -1
        for t in toks:
            v = self.ids.get(t.fz)
            if v is None:
                v, extra = extra, extra - 1
            out.append(v)
        return out

    def surface(self, j1: int, j2: int) -> str:
        if j2 <= j1:
            return ""
        return self.text[self.toks[j1].start:self.toks[j2 - 1].end]

    def snippet(self, j1: int, j2: int, pad: int = 12, limit: int = 80) -> str:
        """逐字稿里对应的那段话（前后多带几个字），给老师看「逐字稿里是怎么写的」。"""
        if not self.toks:
            return ""
        j1, j2 = max(0, j1), min(len(self.toks), max(j2, j1 + 1))
        s = self.toks[max(0, j1 - pad)].start
        e = self.toks[min(len(self.toks), j2 + pad) - 1].end
        out = re.sub(r"\s+", " ", self.text[s:e]).strip()
        if len(out) > limit:
            out = out[:limit] + "……"
        return out


# ============================================================================ 一句话和逐字稿比
@dataclass
class Prop:
    """一处「可能有错」：识别文字的第 i1~i2 个单位，按逐字稿应该是 rep。"""

    i1: int
    i2: int
    rep: str
    kind: str
    mode: str  # S = 整句对齐，L = 局部对齐
    weight: float
    reason: str
    need: int = 1  # 逐字稿里至少几处这么写才算
    locs: Set[int] = field(default_factory=set)
    ref: Tuple[int, int] = (0, 0)


def _rep_text(ref: Reference, j1: int, j2: int, kind: str) -> str:
    """逐字稿里的写法（汉字转简体；英文用逐字稿的原样，几个词之间一个空格）。"""
    parts = [ref.text[t.start:t.end] for t in ref.toks[j1:j2]]
    if kind in ("cjk_en", "en"):
        return " ".join(parts)
    return pc._simp_text("".join(parts))


class _Clip:
    def __init__(self, text: str, ref: Reference):
        self.text = text
        self.toks = tokens(text)
        self.keys = [t.key for t in self.toks]
        self.fid = ref.ids_of(self.toks)


def _windows(clip: _Clip, ref: Reference) -> List[Tuple[int, int]]:
    """按读音找逐字稿里可能对应的几段（三个音一组找位置，按「对角线」投票）。"""
    n, f = len(clip.fid), clip.fid
    votes: Counter = Counter()

    def vote(k: int) -> None:
        idx = ref.idx3 if k == 3 else ref.idx2
        for i in range(n - k + 1):
            if any(x < 0 for x in f[i:i + k]):
                continue
            key = (f[i] << 42) | (f[i + 1] << 21) | f[i + 2] if k == 3 else (f[i] << 21) | f[i + 1]
            hits = idx.get(key)
            if not hits or len(hits) > MAX_HITS:
                continue
            for p in hits:
                votes[(p - i) // BUCKET] += 1

    if n >= 3:
        vote(3)
    if n < 3 or (not votes and n <= 6):
        vote(2)
    out: List[List[int]] = []
    for b, _v in sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_K]:
        d = b * BUCKET
        w0, w1 = max(0, d - MARGIN), min(len(ref), d + BUCKET + n + MARGIN)
        for w in out:  # 同一段（相邻的对角线）合在一起
            if w0 < w[1] and w[0] < w1:
                w[0], w[1] = min(w[0], w0), max(w[1], w1)
                break
        else:
            out.append([w0, w1])
    return [(a, b) for a, b in out]


class _Align:
    """识别文字和逐字稿的一段按读音对齐的结果。"""

    def __init__(self, clip: _Clip, ref: Reference, w0: int, w1: int):
        self.clip, self.ref, self.w0 = clip, ref, w0
        sm = difflib.SequenceMatcher(None, clip.fid, ref.fid[w0:w1], autojunk=False)
        self.ops = [(tag, i1, i2, j1 + w0, j2 + w0) for tag, i1, i2, j1, j2 in sm.get_opcodes()]
        n = len(clip.fid)
        # 只算连着 ≥ 2 个的（单独一个字对上多半是碰巧）
        self.matched = sum(i2 - i1 for tag, i1, i2, _, _ in self.ops if tag == "equal" and (i2 - i1 >= 2 or n <= 3))
        self.longest = max([i2 - i1 for tag, i1, i2, _, _ in self.ops if tag == "equal"] or [0])
        self.mode = "S" if n and self.matched >= min(S_MIN_MATCH, n) and self.matched / n >= S_COVERAGE else "L"
        self.exact = [False] * n
        self.partner = [-1] * n
        for tag, i1, i2, j1, _ in self.ops:
            if tag != "equal":
                continue
            for k in range(i2 - i1):
                self.partner[i1 + k] = j1 + k
                self.exact[i1 + k] = clip.keys[i1 + k] == ref.keys[j1 + k]
        spans = [(j1, j2) for tag, _, _, j1, j2 in self.ops if tag == "equal"]
        self.region = (min(s for s, _ in spans), max(e for _, e in spans)) if spans else (w0, w0)

    def useful(self) -> bool:
        return self.mode == "S" or self.longest >= 3

    def ctx(self, i1: int, i2: int, j1: int, j2: int) -> Tuple[int, int, bool, bool]:
        """不一样的地方（识别文字 i1~i2，逐字稿 j1~j2）左边、右边连着几个一模一样的字（两边都得是挨着的）；
        是不是在句子开头 / 结尾。"""
        left = 0
        k = i1 - 1
        while k >= 0 and self.exact[k] and self.partner[k] == j1 - (i1 - k) and left < 6:
            left, k = left + 1, k - 1
        right = 0
        k = i2
        while k < len(self.exact) and self.exact[k] and self.partner[k] == j2 + (k - i2) and right < 6:
            right, k = right + 1, k + 1
        return left, right, i1 == 0, i2 == len(self.exact)

    def confirmed(self) -> Set[int]:
        """逐字稿证明没错的字（识别文字里的位置）：整句对齐时连着 ≥ 2 个一模一样，局部对齐时连着 ≥ 4 个。"""
        need = 2 if self.mode == "S" else CONFIRM_RUN_L
        out: Set[int] = set()
        k, n = 0, len(self.exact)
        while k < n:
            if not self.exact[k]:
                k += 1
                continue
            j = k
            while j < n and self.exact[j] and (j == k or self.partner[j] == self.partner[j - 1] + 1):
                j += 1
            if j - k >= need:
                out.update(range(k, j))
            k = j
        return out


def _ctx_ok(al: _Align, i1: int, i2: int, j1: int, j2: int) -> bool:
    left, right, at_start, at_end = al.ctx(i1, i2, j1, j2)
    if al.mode == "S":
        return left + right >= 2 or (left + right >= 1 and (at_start or at_end))
    if (left >= 1 or at_start) and (right >= 1 or at_end) and left + right >= L_MIN_CTX:
        return True
    return False


#: 读音一样、两种写法都常见的字（写法习惯，不算错）
_STYLE_GROUPS = ("的地得", "他她它祂牠", "做作", "哪那", "账帐", "象像", "须需", "唯惟", "噢哦喔")


def _style_pair(a: str, b: str) -> bool:
    return any(a in g and b in g for g in _STYLE_GROUPS)


def _absent_around(clip: _Clip, ref: Reference, i1: int, i2: int) -> bool:
    """识别出来的写法在逐字稿里没出现过（单个字时看它和左右邻字组成的词）。"""
    if i2 - i1 >= 2:
        return not ref.has(clip.keys[i1:i2])
    pairs = []
    if i1 > 0 and clip.toks[i1 - 1].kind == "han":
        pairs.append(clip.keys[i1 - 1:i2])
    if i2 < len(clip.keys) and clip.toks[i2].kind == "han":
        pairs.append(clip.keys[i1:i2 + 1])
    return not any(ref.has(p) for p in pairs) if pairs else not ref.has(clip.keys[i1:i2])


def _q(s: str, n: int = 12) -> str:
    return pc._short(s, n)


def _props_equal_block(al: _Align, i1: int, i2: int, j1: int) -> List[Prop]:
    """读音对得上、但写法不一样的地方（定于 / 定语、there / their）。"""
    clip, ref = al.clip, al.ref
    out: List[Prop] = []
    k = i1
    while k < i2:
        if clip.keys[k] == ref.keys[j1 + (k - i1)]:
            k += 1
            continue
        s = k
        while k < i2 and clip.keys[k] != ref.keys[j1 + (k - i1)]:
            k += 1
        a1, a2 = s, k
        b1, b2 = j1 + (a1 - i1), j1 + (a2 - i1)
        ct, rt = clip.toks[a1:a2], ref.toks[b1:b2]
        kinds = {t.kind for t in ct} | {t.kind for t in rt}
        if not _ctx_ok(al, a1, a2, b1, b2):
            continue
        cs = clip.text[ct[0].start:ct[-1].end]
        if kinds == {"han"}:
            same = all(a.tone == b.tone for a, b in zip(ct, rt))
            all_diff = all(a.tone != b.tone for a, b in zip(ct, rt))
            if same and a2 - a1 == 1 and (al.mode == "L" or _style_pair(ct[0].key, rt[0].key)):
                continue  # 读音完全一样的单个字：局部对齐时证据不够；他/她、的/得 是写法习惯，训练也不受影响
            rep = _rep_text(ref, b1, b2, "near")
            if same:
                need = 2 if al.mode == "L" else 1
                reason = f"「{_q(cs)}」和逐字稿里的「{_q(rep)}」读音一样（不影响训练，改不改都行）"
                kind = "same"
            else:
                if al.mode == "L" and not _absent_around(clip, ref, a1, a2):
                    continue  # 识别出来的写法逐字稿里也有：那也是老师的说法
                need = 2 if (al.mode == "L" and a2 - a1 >= 2 and all_diff) else 1
                if need == 2 and sum(al.ctx(a1, a2, b1, b2)[:2]) < 4:
                    continue
                reason = f"「{_q(cs)}」读音和逐字稿里的「{_q(rep)}」很像，可能是识别错了"
                kind = "near"
        elif kinds == {"lat"}:
            if al.mode == "L" and (ref.latin.get(ct[0].key) or a2 - a1 > 2):
                continue
            rep = _rep_text(ref, b1, b2, "en")
            reason = f"英文「{_q(cs)}」逐字稿里写的是「{_q(rep)}」（读音一样，可能是识别错了）"
            kind = "en"
            need = 1
        else:
            continue
        out.append(Prop(a1, a2, rep, kind, al.mode, W[(kind, al.mode)], reason, need, {b1}, (b1, b2)))
    return out


def _runs(toks: Sequence[Tk]) -> Tuple[int, int]:
    """开头连着几个英文词、结尾连着几个英文词。"""
    head = 0
    while head < len(toks) and toks[head].kind == "lat":
        head += 1
    tail = 0
    while tail < len(toks) and toks[len(toks) - 1 - tail].kind == "lat":
        tail += 1
    return head, tail


def _replace_candidates(al: _Align, i1: int, i2: int, j1: int, j2: int) -> List[Tuple[int, int, int, int]]:
    """一处读音对不上的地方，可能只有一部分是识别错（另一部分是老师换了说法），列出值得看的几种切法。"""
    clip, ref = al.clip, al.ref
    n = len(clip.toks)
    cands: List[Tuple[int, int, int, int]] = []
    lc, lr = i2 - i1, j2 - j1
    if lc and lr and lc <= 4 and lr <= 4:
        cands.append((i1, i2, j1, j2))
    if lc and lr > lc:  # 在句子开头 / 结尾：逐字稿那边会多出后面（前面）的话，只取挨着的一小段
        ck = clip.toks[i1].kind
        if i2 == n:
            take = _runs(ref.toks[j1:j2])[0] if ck == "han" else lc
            if 0 < take <= 4:
                cands.append((i1, i2, j1, j1 + take))
        if i1 == 0:
            take = _runs(ref.toks[j1:j2])[1] if ck == "han" else lc
            if 0 < take <= 4:
                cands.append((i1, i2, j2 - take, j2))
    for a, b, c, d, swap in ((i1, i2, j1, j2, False), (j1, j2, i1, i2, True)):
        # 一边全是汉字、另一边是「汉字 + 英文」：英文那段和汉字那边对应的一段比（看艾子 / 讲 as → 艾子 / as）
        xs = ref.toks[c:d] if not swap else clip.toks[c:d]
        ys = clip.toks[a:b] if not swap else ref.toks[a:b]
        if not xs or not ys or {t.kind for t in ys} != {"han"}:
            continue
        head, tail = _runs(xs)
        if tail and tail < len(xs) and all(t.kind == "han" for t in xs[:len(xs) - tail]):
            rest = len(xs) - tail
            if len(ys) > rest:
                sub = (a + rest, b, d - tail, d)
                cands.append(sub if not swap else (sub[2], sub[3], sub[0], sub[1]))
        if head and head < len(xs) and all(t.kind == "han" for t in xs[head:]):
            rest = len(xs) - head
            if len(ys) > rest:
                sub = (a, b - rest, c, c + head)
                cands.append(sub if not swap else (sub[2], sub[3], sub[0], sub[1]))
    out: List[Tuple[int, int, int, int]] = []
    for x in cands:
        if x not in out:
            out.append(x)
    return out


def _props_replace(al: _Align, i1: int, i2: int, j1: int, j2: int) -> List[Prop]:
    """读音对不上的地方：只认英文 ↔ 汉字、英文拼写、中文数字这几种，其它算老师换了说法。"""
    for c in _replace_candidates(al, i1, i2, j1, j2):
        props = _props_replace_one(al, *c)
        if props:
            return props
    return []


def _props_replace_one(al: _Align, i1: int, i2: int, j1: int, j2: int) -> List[Prop]:
    clip, ref = al.clip, al.ref
    ct, rt = clip.toks[i1:i2], ref.toks[j1:j2]
    if not ct or not rt or len(ct) > 4 or len(rt) > 4:
        return []
    ck, rk = {t.kind for t in ct}, {t.kind for t in rt}
    if not _ctx_ok(al, i1, i2, j1, j2):
        return []
    cs = clip.text[ct[0].start:ct[-1].end]
    if ck == {"han"} and rk == {"lat"} and len(rt) <= 2:
        words = [t.key for t in rt]
        ok = sounds_like_english([t.tone for t in ct], words)
        absent = not ref.has(clip.keys[i1:i2])
        if al.mode == "S":
            ok = ok or (absent and len(ct) <= 3 and all(ref.latin.get(w, 0) >= 2 for w in words))
        else:
            ok = ok and absent and all(ref.latin.get(w, 0) >= 2 for w in words)
        if not ok:
            return []
        rep = _rep_text(ref, j1, j2, "cjk_en")
        return [Prop(i1, i2, rep, "cjk_en", al.mode, W[("cjk_en", al.mode)],
                     f"「{_q(cs)}」可能是英文「{_q(rep)}」（逐字稿里是 {_q(rep)}）", 1, {j1}, (j1, j2))]
    if ck == {"lat"} and rk == {"han"} and len(ct) <= 2:
        words = [t.key for t in ct]
        conf = all(w in pc.CONFUSABLE_EN or w in pc.CONFUSABLE_SOFT for w in words)
        ok = sounds_like_english([t.tone for t in rt], words)
        if al.mode == "S":
            ok = ok or conf
        else:
            ok = ok and not any(ref.latin.get(w) for w in words)
        if not ok:
            return []
        rep = _rep_text(ref, j1, j2, "en_cjk")
        return [Prop(i1, i2, rep, "en_cjk", al.mode, W[("en_cjk", al.mode)],
                     f"「{_q(cs)}」可能是中文「{_q(rep)}」（逐字稿里是「{_q(rep)}」）", 1, {j1}, (j1, j2))]
    if ck == {"lat"} and rk == {"lat"} and len(ct) <= 2 and len(rt) <= 2:
        a, b = " ".join(t.key for t in ct), " ".join(t.key for t in rt)
        ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        need_ratio = 0.75 if al.mode == "S" else 0.8
        if ratio < need_ratio or min(len(a), len(b)) < 3:
            return []
        if al.mode == "L" and any(ref.latin.get(t.key) for t in ct):
            return []
        rep = _rep_text(ref, j1, j2, "en")
        return [Prop(i1, i2, rep, "en", al.mode, W[("en", al.mode)],
                     f"英文「{_q(cs)}」逐字稿里写的是「{_q(rep)}」（可能拼错了）", 1, {j1}, (j1, j2))]
    if ck == {"num"} and rk == {"num"} and len(ct) == 1 and len(rt) == 1:
        a = _num_pinyin(clip.text[ct[0].start:ct[0].end])
        b = _num_pinyin(ref.text[rt[0].start:rt[0].end])
        if not a or not b or len(a) != len(b) or [fuzzy(x) for x in a] != [fuzzy(x) for x in b]:
            return []
        rep = ref.text[rt[0].start:rt[0].end]
        return [Prop(i1, i2, rep, "num", al.mode, W[("num", al.mode)],
                     f"数字「{_q(cs)}」读音和逐字稿里的「{_q(rep)}」很像，可能是识别错了", 1, {j1}, (j1, j2))]
    return []


@dataclass
class ClipResult:
    props: List[Prop]
    confirmed_chars: Set[int]
    aligned: bool  # 整句对齐了
    ref_text: str


def check_text(text: str, ref: Reference) -> ClipResult:
    """一句识别文字和逐字稿比：返回可能有错的地方、逐字稿证明没错的字（字符位置）、整句对齐了没有。"""
    clip = _Clip(text, ref)
    if not clip.toks or not len(ref):
        return ClipResult([], set(), False, "")
    found: Dict[Tuple[int, int, str], Prop] = {}
    confirmed_tok: Set[int] = set()
    aligned = False
    best_region: Optional[Tuple[int, int, int]] = None  # (对上的字数, 开始, 结束)
    for w0, w1 in _windows(clip, ref):
        al = _Align(clip, ref, w0, w1)
        if not al.useful():
            continue
        aligned = aligned or al.mode == "S"
        confirmed_tok |= al.confirmed()
        if best_region is None or al.matched > best_region[0]:
            best_region = (al.matched, al.region[0], al.region[1])
        for tag, i1, i2, j1, j2 in al.ops:
            if tag == "equal":
                props = _props_equal_block(al, i1, i2, j1)
            elif tag == "replace":
                props = _props_replace(al, i1, i2, j1, j2)
            else:
                props = []
            for p in props:
                key = (p.i1, p.i2, p.rep)
                old = found.get(key)
                if old is None:
                    found[key] = p
                else:
                    old.locs |= p.locs
                    if p.weight > old.weight:
                        old.weight, old.mode, old.reason, old.need, old.ref = p.weight, p.mode, p.reason, p.need, p.ref
                    old.need = min(old.need, p.need)
    props = []
    for p in found.values():
        if len(p.locs) < p.need:
            continue
        if p.mode == "L" and len(p.locs) >= 2:
            p.weight = min(0.95, p.weight + MULTI_BONUS)
        props.append(p)
    props.sort(key=lambda p: (-p.weight, -len(p.locs), p.i1))
    kept: List[Prop] = []
    for p in props:  # 同一个地方几种说法：留分量最大的
        if all(p.i2 <= q.i1 or q.i2 <= p.i1 for q in kept):
            kept.append(p)
    kept.sort(key=lambda p: p.i1)
    chars: Set[int] = set()
    for k in confirmed_tok:
        if not any(p.i1 <= k < p.i2 for p in kept):
            t = clip.toks[k]
            chars.update(range(t.start, t.end))
    snippet = ""
    if kept:
        snippet = ref.snippet(*kept[0].ref)
    elif best_region is not None and aligned:
        snippet = ref.snippet(best_region[1], best_region[2], pad=0)
    return ClipResult(kept, chars, aligned, snippet)


# ============================================================================ 和自动查错字的结果合在一起
def _apply(text: str, edits: Sequence[Tuple[int, int, str]]) -> str:
    """从后往前改（不像 review.apply_edits 那样整理整句的空格标点，免得多出别的改动）。"""
    out, left = text, len(text) + 1
    for s, e, rep in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        if not (0 <= s <= e <= len(text)) or e > left:
            continue
        out = out[:s] + rep + out[e:]
        left = s
    return out


def _token_chars(text: str) -> Set[int]:
    out: Set[int] = set()
    for t in pc.tokenize(text):
        out.update(range(t.start, t.end))
    return out


def _is_confirmed(s: int, e: int, confirmed: Set[int], tokchars: Set[int]) -> bool:
    """这一段里的字逐字稿都证明没错（标点、空格不算）。插入的位置（s == e）看两边的字。"""
    if e <= s:
        return (s - 1 in confirmed or s - 1 not in tokchars) and (s in confirmed or s not in tokchars) and (
            s - 1 in confirmed or s in confirmed)
    inside = [k for k in range(s, e) if k in tokchars]
    return bool(inside) and all(k in confirmed for k in inside)


def _noisy_or(ws: Iterable[float]) -> float:
    keep = 1.0
    for w in ws:
        keep *= 1.0 - max(0.0, min(1.0, w))
    return 1.0 - keep


def merge_with_auto(cur: str, res: ClipResult, auto: Optional[Dict[str, Any]], rec: Dict[str, Any]
                    ) -> Tuple[Optional[Dict[str, Any]], str]:
    """逐字稿的结果和原来自动查错字的结果（auto）合起来，返回 (新的 suspect 或 None, 发生了什么)。

    发生了什么：found = 逐字稿发现了错；cleared = 原来标红、逐字稿证明没错，去掉了；kept_auto = 只剩自动检查的标红；
    unchanged_auto = 原样保留自动检查的结果；none = 没有标红。"""
    from voicetwin.data import review as _review

    clip = tokens(cur)
    a_red: List[Tuple[int, int]] = []
    a_edits: List[Tuple[int, int, str]] = []
    a_reasons: List[str] = []
    a_score = 0.0
    if auto:
        info = _review.analyze(dict(rec, suspect=auto), cur)
        a_red, a_edits = list(info["red"]), list(info["edits"])
        a_reasons = [r for r in info["reasons"] if r]
        try:
            a_score = float(auto.get("score") or 0.6)
        except (TypeError, ValueError):
            a_score = 0.6
    tokchars = _token_chars(cur)
    red_keep = [sp for sp in a_red if not _is_confirmed(sp[0], sp[1], res.confirmed_chars, tokchars)]
    t_edits: List[Tuple[int, int, str]] = []
    spans: List[List[int]] = []
    reasons: List[str] = []
    weights: List[float] = []
    for p in res.props:
        s, e = clip[p.i1].start, clip[p.i2 - 1].end
        rep = pc._pad(cur, s, e, p.rep)
        w, reason = p.weight, p.reason
        if any(es == s and ee == e and pc.tokenize(er) and [t.key for t in pc.tokenize(er)] ==
               [t.key for t in pc.tokenize(rep)] for es, ee, er in a_edits):
            w = min(0.95, w + AGREE_BONUS)
            reason += "（另一个识别引擎也听成这样）"
        t_edits.append((s, e, rep))
        spans.append([s, e])
        reasons.append(reason)
        weights.append(w)
    edits_keep = [ed for ed in a_edits if not _is_confirmed(ed[0], ed[1], res.confirmed_chars, tokchars)
                  and all(ed[1] <= s or e <= ed[0] for s, e, _ in t_edits)
                  and any(not (ed[1] <= rs or re_ <= ed[0]) or ed[0] == ed[1] for rs, re_ in red_keep)]
    auto_left = bool(red_keep or edits_keep)
    if not res.props:
        if not auto:
            return None, "none"
        if not auto_left:
            return None, "cleared"
        if len(red_keep) == len(a_red) and len(edits_keep) == len(a_edits):
            return auto, "unchanged_auto"
    if auto_left:
        spans += [list(sp) for sp in red_keep]
        reasons += [AUTO_PREFIX + r for r in a_reasons]
        weights.append(a_score)
    edits = t_edits + edits_keep
    alt = _apply(cur, edits) if edits else ""
    sus: Dict[str, Any] = {"spans": pc.merge_spans(spans, cur), "alt": alt if alt != cur else "",
                           "reasons": _limit_reasons(reasons), "score": round(_noisy_or(weights), 3),
                           "text": cur, "src": "transcript"}
    if res.ref_text and res.props:
        sus["ref"] = res.ref_text
    return sus, ("found" if res.props else "kept_auto")


def _limit_reasons(reasons: Sequence[str]) -> List[str]:
    out: List[str] = []
    for r in reasons:
        if r and r not in out:
            out.append(r)
    if len(out) > pc.MAX_REASONS:
        rest = len(out) - (pc.MAX_REASONS - 1)
        out = out[:pc.MAX_REASONS - 1] + [f"……还有 {rest} 处"]
    return out


# ============================================================================ 整个声音
_report = pc._report  # 进度回调自己出错不影响比对；停止按钮照常传出去


def auto_suspect(rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """这一条原来自动查错字的结果（上次逐字稿校正前存下的那份；没做过逐字稿校正就是现在的）。"""
    sus = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else None
    if sus and sus.get("src") == "transcript":
        old = rec.get("suspect_auto")
        return old if isinstance(old, dict) and old else None
    return sus or None


def check_with_transcript(project: Any, text: Optional[str] = None, progress: Optional[ProgressFn] = None,
                          names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """用逐字稿检查这个声音的校对表，结果写进 manifest。返回统计（见 _summary）。"""
    from voicetwin.data import review as _review

    t0 = time.time()
    if text is None:
        text, names = load_transcripts(project)
    if not text or _useful_chars(text) < MIN_CHARS:
        raise ValueError("还没有上传逐字稿：请先在「文字校正」左边选好逐字稿（txt 文件），再点「文字校正」。")
    _report(progress, 0.02, "正在读逐字稿……")
    ref = Reference(text)
    _report(progress, 0.15, f"逐字稿有 {len(ref)} 个字 / 词，开始一句一句比对……")
    records = project.load_manifest()
    draft = _review.load_draft(project)
    todo = []
    dismissed = 0
    for r in records:
        if r.get("deleted"):
            continue
        vals = _review.current_values(r, draft.get(r["id"]))
        cur = str(vals["text"] or "")
        if not cur.strip() or not vals["keep"]:
            continue
        if r.get("suspect_ok") and r.get("suspect_ok") == cur:
            dismissed += 1
            continue
        todo.append((r["id"], cur))
    results: Dict[str, Tuple[str, ClipResult]] = {}
    n = len(todo)
    for i, (rid, cur) in enumerate(todo, 1):
        _check_cancel()
        results[rid] = (cur, check_text(cur, ref))
        if i % 20 == 0 or i == n:
            _report(progress, 0.15 + 0.8 * i / max(n, 1), f"已比对 {i} / {n} 条")
    stats = Counter()
    examples: List[str] = []
    with _review._LOCK:
        records = project.load_manifest()
        draft = _review.load_draft(project)
        for r in records:
            item = results.get(r.get("id"))
            if item is None:
                continue
            cur, res = item
            vals = _review.current_values(r, draft.get(r["id"]))
            if str(vals["text"] or "") != cur:  # 比对期间改过（一般不会：比对时不能改表格）
                continue
            auto = auto_suspect(r)
            sus, what = merge_with_auto(cur, res, auto, r)
            stats[what] += 1
            stats["aligned"] += int(res.aligned)
            if auto:
                r["suspect_auto"] = auto
            else:
                r.pop("suspect_auto", None)
            if sus is None:
                r.pop("suspect", None)
            else:
                r["suspect"] = sus
                stats["flagged"] += 1
            if what == "found" and len(examples) < 5:
                clip = tokens(cur)
                for p in res.props[:2]:
                    examples.append(f"{cur[clip[p.i1].start:clip[p.i2 - 1].end]} → {p.rep}")
        project.save_manifest(records)
    secs = round(time.time() - t0, 1)
    out = {"checked": n, "flagged": stats["flagged"], "found": stats["found"], "aligned": stats["aligned"],
           "cleared": stats["cleared"], "kept_auto": stats["kept_auto"] + stats["unchanged_auto"],
           "dismissed": dismissed, "chars": len(ref), "files": list(names or []), "pinyin": has_pinyin(),
           "truncated": ref.truncated, "examples": examples[:5], "seconds": secs}
    log.info(f"文字校正完成：比对了 {n} 条，{out['found']} 条和逐字稿对比发现可能有错，{out['aligned']} 条整句对上，"
             f"{out['cleared']} 条原来的标红被逐字稿证明没错、已去掉，保留自动检查标红 {out['kept_auto']} 条；用时 {secs} 秒。")
    _report(progress, 1.0, f"比对完了：{out['found']} 条和逐字稿对比发现可能有错（已标红）")
    return out


__all__ = [
    "TRANSCRIPT_DIR", "read_text_file", "save_transcripts", "load_transcripts", "transcript_info", "Reference",
    "check_text", "check_with_transcript", "merge_with_auto", "auto_suspect", "tokens", "fuzzy", "en_code",
    "sounds_like_english", "has_pinyin",
]
