"""Prototype for the character-level diff + heuristics recommended in research_proofcheck.md (py3.9-compatible)."""
from __future__ import annotations

import difflib
import html
import re
import unicodedata
from typing import Dict, List, Optional, Sequence, Tuple

CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
CN_NUM = set("零〇一二两三四五六七八九十百千万亿")
WORDCH = re.compile(r"[a-z0-9']")

try:  # optional: traditional -> simplified per char (zhconv is installed by VoiceTwin; opencc in GSV)
    import zhconv  # type: ignore

    def _simp(ch: str) -> str:
        return zhconv.convert(ch, "zh-cn")
except Exception:  # pragma: no cover
    def _simp(ch: str) -> str:
        return ch

Tok = Tuple[str, int, int]  # (normalized token, start, end) offsets into the ORIGINAL string


def _nk(ch: str) -> str:
    return unicodedata.normalize("NFKC", ch).lower()


def tokenize(text: str) -> List[Tok]:
    """CJK -> one token per char; Latin/digit words -> one token; number runs (digits or Chinese numerals) -> '#';
    punctuation and whitespace -> dropped. Offsets always refer to `text`."""
    out: List[Tok] = []
    i, n = 0, len(text)
    while i < n:
        c = _nk(text[i])
        if c and ("a" <= c[0] <= "z"):
            j = i
            while j < n and _nk(text[j]) and WORDCH.match(_nk(text[j])[0]):
                j += 1
            out.append(("".join(_nk(x) for x in text[i:j]), i, j))
            i = j
            continue
        if text.startswith("百分之", i) and i + 3 < n and (text[i + 3] in CN_NUM or text[i + 3].isdigit()):
            j = i + 3
            while j < n and (text[j] in CN_NUM or _nk(text[j])[:1].isdigit() or text[j] == "点"):
                j += 1
            out.append(("#", i, j))
            i = j
            continue
        if c and (c[0].isdigit() or text[i] in CN_NUM):
            j = i
            while j < n:
                cj = _nk(text[j])
                if cj and (cj[0].isdigit() or text[j] in CN_NUM or cj in "%.") or (
                        text[j] == "点" and j + 1 < n and (text[j + 1] in CN_NUM or text[j + 1].isdigit())):
                    j += 1
                elif cj and "a" <= cj[0] <= "z":   # "4k", "5g": glue letters to a digit word
                    while j < n and _nk(text[j]) and WORDCH.match(_nk(text[j])[0]):
                        j += 1
                    break
                else:
                    break
            seg = text[i:j].rstrip(".")
            j = i + len(seg) if seg else j
            word = "".join(_nk(x) for x in text[i:j])
            out.append(("#" if not re.search(r"[a-z]", word) else word, i, j))
            i = max(j, i + 1)
            continue
        if CJK.match(c or ""):
            out.append((_simp(c), i, i + 1))
        i += 1
    return out


FILLERS = set("嗯呃额啊哦噢唉诶欸哎呀吧呢嘛啦哈") | {"那个", "这个", "就是", "然后"}
PARTICLES = set("的地得了着过")


HOMO_GROUPS = ["他她它祂", "的地得", "在再", "做作", "象像", "须需", "账帐", "分份", "即既", "副付", "截节"]
_HOMO = {ch: g for g in HOMO_GROUPS for ch in g}


def _pinyin(chars: str) -> Optional[List[str]]:
    try:
        from pypinyin import Style, lazy_pinyin  # type: ignore
        return lazy_pinyin(chars, style=Style.TONE3, neutral_tone_with_five=True)
    except Exception:
        return [_HOMO.get(ch, ch) for ch in chars]   # tiny fallback when pypinyin is missing


def diff_spans(text: str, alt: str) -> Dict:
    """Return {'spans': [[s,e],...], 'merged': str, 'ratio': float, 'ops': [...]} comparing text (A) with alt (B)."""
    a, b = tokenize(text), tokenize(alt)
    sm = difflib.SequenceMatcher(None, [t[0] for t in a], [t[0] for t in b], autojunk=False)
    spans: List[List[int]] = []
    edits: List[Tuple[int, int, str]] = []   # (start, end, replacement) in A coordinates
    ops = []
    weak: List[list] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        a_txt = "".join(t[0] for t in a[i1:i2])
        b_txt = "".join(t[0] for t in b[j1:j2])
        b_orig = alt[b[j1][1]:b[j2 - 1][2]] if j2 > j1 else ""
        # ignore filler-only / particle-only insertions and deletions
        if (tag in ("insert", "delete")) and all(t in FILLERS or t in PARTICLES for t in (a_txt, b_txt) if t) and \
                len(a_txt + b_txt) <= 2:
            continue
        if a_txt == b_txt:          # "VFIXED" vs "v fixed": only spacing differs
            continue
        kind = "diff"
        if tag == "replace" and re.fullmatch(r"[a-z']+", a_txt) and CJK.search(b_txt) and not re.search(r"[a-z]", b_txt):
            kind = "en_vs_cjk"      # paraformer cannot spell English: weak evidence, never auto-suggested
        elif tag == "replace" and CJK.search(a_txt) and CJK.search(b_txt) and len(a_txt) == len(b_txt):
            pa, pb = _pinyin(a_txt), _pinyin(b_txt)
            if pa is not None and pa == pb:
                kind = "homophone"   # same pinyin incl. tone: TTS phonemes identical -> not flagged
        ops.append((tag, a_txt, b_txt, kind))
        if kind == "homophone":
            continue
        if kind == "en_vs_cjk":
            weak.append([a[i1][1], a[i2 - 1][2], b_orig])
            continue
        if tag == "insert":   # A lacks something: mark the neighbouring token so the user sees where
            k = i1 - 1 if i1 > 0 else (i1 if i1 < len(a) else None)
            if k is not None:
                spans.append([a[k][1], a[k][2]])
            pos = a[i1 - 1][2] if i1 > 0 else (a[0][1] if a else 0)
            sep = " " if (b_orig[:1].isascii() and b_orig[:1].isalpha() and pos > 0 and text[pos - 1].isalnum()) else ""
            edits.append((pos, pos, sep + b_orig))
        else:
            s, e = a[i1][1], a[i2 - 1][2]
            spans.append([s, e])
            edits.append((s, e, b_orig))
    merged = text
    for s, e, rep in sorted(edits, reverse=True):
        merged = merged[:s] + rep + merged[e:]
    return {"spans": merge_spans(spans), "weak": weak, "merged": merged, "ratio": sm.ratio(), "ops": ops}


def merge_spans(spans: Sequence[Sequence[int]], gap: int = 0) -> List[List[int]]:
    out: List[List[int]] = []
    for s, e in sorted((int(s), int(e)) for s, e in spans if e > s):
        if out and s <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


# ------------------------------------------------------------------ heuristics
ACRONYMS = set("""
AI API APP CPU GPU NPU TPU RAM ROM SSD HDD USB HDMI WIFI PDF PPT PPTX DOC DOCX XLS XLSX CSV TXT JPG JPEG PNG GIF SVG
MP3 MP4 AVI MOV HTML CSS JSON XML SQL URL HTTP HTTPS FTP SSH IP TCP UDP DNS VPN LAN WAN NAS IT IOS OS PC CEO CFO CTO COO
HR KPI OKR ROI GDP CPI PPI PMI IPO ETF VIP DIY FAQ CAD BIM UI UX ID OK QQ VR AR MR XR IOT LLM GPT AIGC NLP CNN RNN LSTM
GAN TTS ASR OCR SDK IDE ATM NBA CBA CCTV BBC USA UK EU UN WHO WTO NASA MBA PHD GRE GMAT IELTS TOEFL SAT DNA RNA PCR
MRI ECG BMI LED LCD OLED PCB CNC PLC ERP CRM SAAS SEO SEM GPS SIM SMS APK EXE DLL BUG CMD CEO PPP GNU AWS GCP RGB CMYK
DPI FPS HDR PS PR AE AM PM ABC TV DVD CD NFC PIN QR OA OTA SOP PDCA SWOT PEST MECE STEM STEAM AP IB
SUM IF IFS AND OR NOT AVERAGE COUNT COUNTA COUNTIF COUNTIFS SUMIF SUMIFS VLOOKUP HLOOKUP XLOOKUP INDEX MATCH LEFT RIGHT
MID LEN TRIM ROUND MAX MIN IFERROR TEXT DATE TODAY NOW RANK
""".split())
ROMAN = re.compile(r"^(?=[IVXLCDM]+$)M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
CONFUSABLE_EN = set("""whose who how she so say the one way why hey yeah me my bye buy no know now show sure shoe see sea tea
door low law lay lie pie pay tie die hi yo ya ma na la ha he her here high hum oh ah wow cool shit fuck """.split())
LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z']*")
KANA_ETC = re.compile(r"[぀-ヿ가-힯Ѐ-ӿ�-]")
REDUP_OK = set("看看试试慢慢常常谢谢刚刚天天个个人人渐渐往往偏偏仅仅稍稍大大好好明明悄悄默默星星妈妈爸爸哥哥姐姐弟弟妹妹奶奶爷爷宝宝"
               "太太叔叔哈哈呵呵嘻嘻想想说说听听走走等等讲讲问问聊聊")


def heuristics(text: str, known_terms: Sequence[str] = ()) -> List[Tuple[int, int, str, float]]:
    """Return [(start, end, reason, weight)] for one transcript."""
    hits: List[Tuple[int, int, str, float]] = []
    n_cjk = len(CJK.findall(text))
    zh = n_cjk >= 4
    known = {k.upper() for k in known_terms}
    for m in LATIN_TOKEN.finditer(text):
        w = m.group(0)
        s, e = m.span()
        if not zh:
            continue
        up = w.upper()
        if up in ACRONYMS or up in known or ROMAN.match(up):
            continue
        if w.isupper() and len(w) >= 3:
            hits.append((s, e, f"「{w}」像是听错的英文", 0.7))
            continue
        before = text[:s].rstrip()[-1:]
        after = text[e:].lstrip()[:1]
        isolated = bool(CJK.match(before or "") or CJK.match(after or "") or before in "，。、" or after in "，。、")
        if w.lower() in CONFUSABLE_EN and isolated:
            hits.append((s, e, f"中文里夹着「{w}」，可能是把中文听成了英文", 0.6))
        elif re.search(r"[a-z][A-Z].*[a-z][A-Z]|^[^aeiouyAEIOUY]{4,}$", w) or len(w) > 15:
            hits.append((s, e, f"「{w}」像是乱码", 0.6))
    for m in KANA_ETC.finditer(text):
        hits.append((m.start(), m.end(), "出现了不该有的外文字符", 0.8))
    # repeats on the punctuation-free token stream, mapped back to offsets
    toks = tokenize(text)
    keys = [t[0] for t in toks]
    i = 0
    while i < len(keys):
        found = False
        for L in range(1, 7):
            if i + 2 * L > len(keys):
                break
            unit = keys[i:i + L]
            k = 1
            while keys[i + k * L:i + (k + 1) * L] == unit:
                k += 1
            unit_s = "".join(unit)
            if k >= 2 and unit_s != "#":
                strong = (L == 1 and k >= 3 and unit_s not in "哈呵嘻啦嗯") or (L in (2, 3) and k >= 3) or (L >= 4)
                if strong and (unit_s * 2) not in REDUP_OK:
                    s, e = toks[i + L][1], toks[i + k * L - 1][2]   # mark the repeated copies, not the first
                    hits.append((s, e, f"「{text[toks[i][1]:toks[i + L - 1][2]]}」连续重复了 {k} 次", 0.5 if L < 4 else 0.6))
                    i += k * L
                    found = True
                    break
        if not found:
            i += 1
    return hits


MD_ESC = {c: "&#%d;" % ord(c) for c in "\\`*_{}[]()#+-.!|~>$"}


def _esc(s: str) -> str:
    # HTML-escape, then neutralise Markdown syntax with numeric entities -> safe for datatype "markdown" AND "html"
    return "".join(MD_ESC.get(c, c) for c in html.escape(s, quote=True))


RED = '<span style="color:#dc2626;font-weight:700;background:#fee2e2">'


def render_marked(text: str, spans: Sequence[Sequence[int]]) -> str:
    out, pos = [], 0
    for s, e in merge_spans([[max(0, s), min(len(text), e)] for s, e in spans]):
        out.append(_esc(text[pos:s]))
        out.append(RED + _esc(text[s:e]) + "</span>")
        pos = e
    out.append(_esc(text[pos:]))
    return "".join(out)


def render_plain(text: str, spans: Sequence[Sequence[int]]) -> str:
    out, pos = [], 0
    for s, e in merge_spans(spans):
        out += [text[pos:s], "【", text[s:e], "】"]
        pos = e
    out.append(text[pos:])
    return "".join(out)


if __name__ == "__main__":
    cases = [
        ("我们今天讲VFIXED的用法，这个函数很常用。", "我们今天讲 v fixed 的用法这个函数很常用"),
        ("这个户字的意思是whose，大家记一下。", "这 个 胡 子 的 意 思 是 户 字 大 家 记 一 下"),
        ("2024年我们讲了50%的内容。", "二零二四年我们讲了百分之五十的内容"),
        ("那个，我们打开Python的设置页面。", "嗯那个我们打开派森的设置页面"),
        ("他说的在理，我们再看一下。", "她说得在理我们在看一下"),
        ("我们来看一下我们来看一下这个公式。", "我们来看一下这个公式"),
        ("我们今天讲 VLOOKUP 和 SUMIF 两个函数，在 Excel 里很常用。", "我们今天讲vlookup和sumif两个函数在excel里很常用"),
        ("大家好，今天天气不错 the 我们开始上课。", "大家好今天天气不错的我们开始上课"),
    ]
    def clean_b(t):
        return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", t)
    for a, b in cases:
        b = clean_b(b)
        d = diff_spans(a, b)
        h = heuristics(a)
        print("A:", a)
        print("B:", b)
        print("  diff spans:", d["spans"], [a[s:e] for s, e in d["spans"]], "weak:", d["weak"], "ratio=%.2f" % d["ratio"])
        print("  ops:", d["ops"])
        print("  merged alt:", d["merged"])
        print("  heuristics:", [(a[s:e], r, w) for s, e, r, w in h])
        print("  plain:", render_plain(a, merge_spans(d["spans"] + [[s, e] for s, e, _r, _w in h])))
    print(render_marked("1. 首先 *打开* <b>x</b> $$y$$", [[6, 8]]))


# ------------------------------------------------------------------ word probabilities -> spans in record text
def low_prob_spans(text: str, words: Sequence, thr: float = 0.45) -> List[Tuple[int, int, float, str]]:
    """words: faster-whisper Word objects (or dicts) with .word/.probability. Maps each low-probability word onto
    `text` (the stored, cleaned transcript) via token alignment, so traditional/simplified, spacing and punctuation
    differences do not break the offsets."""
    get = (lambda w, k: w[k]) if words and isinstance(words[0], dict) else getattr
    raw, ranges = [], []
    pos = 0
    for w in words:
        ws = get(w, "word")
        raw.append(ws)
        ranges.append((pos, pos + len(ws), float(get(w, "probability"))))
        pos += len(ws)
    W = "".join(raw)
    wt, tt = tokenize(W), tokenize(text)
    sm = difflib.SequenceMatcher(None, [t[0] for t in wt], [t[0] for t in tt], autojunk=False)
    w2t: Dict[int, int] = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w2t[blk.a + k] = blk.b + k
    out = []
    for s, e, p in ranges:
        if p >= thr:
            continue
        idx = [i for i, t in enumerate(wt) if t[1] < e and t[2] > s and i in w2t]
        if idx:
            ts, te = tt[w2t[idx[0]]][1], tt[w2t[idx[-1]]][2]
            out.append((ts, te, p, text[ts:te]))
    merged: List[list] = []          # zh-mode Whisper splits "VFIXED" into " V","FIX","ED": merge, keep min prob
    for ts, te, p, _ in sorted(out):
        if merged and ts <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], te)
            merged[-1][2] = min(merged[-1][2], p)
        else:
            merged.append([ts, te, p])
    return [(a, b, p, text[a:b]) for a, b, p in merged]


def build_suspect(text: str, alt_raw: str = "", words: Sequence = (), known_terms: Sequence[str] = ()) -> Optional[Dict]:
    """Combine evidence -> record['suspect'] dict, or None when clean. Noisy-OR score in [0,1]."""
    spans: List[List[int]] = []
    reasons: List[str] = []
    weights: List[float] = []
    alt = ""
    heur = heuristics(text, known_terms)
    for s, e, r, w in heur:
        spans.append([s, e]); reasons.append(r); weights.append(w)
    if alt_raw:
        alt_c = re.sub(r"(?<=[一-鿿])\s+(?=[一-鿿])", "", alt_raw).strip()
        d = diff_spans(text, alt_c)
        if d["ratio"] < 0.5:
            spans.append([0, len(text)]); reasons.append("两次识别结果差别很大，整句可能不对"); weights.append(0.7)
            alt = alt_c
        else:
            for s, e in d["spans"]:
                spans.append([s, e]); weights.append(0.6)
            if d["spans"]:
                reasons.append(f"另一个识别引擎听到的不一样（{len(d['spans'])} 处）")
            merged = d["merged"]
            # weak English-vs-Chinese diffs become real suggestions only when a heuristic also flagged that word
            for s, e, b_orig in sorted(d["weak"], reverse=True):
                if any(hs < e and he > s for hs, he, _r, _w in heur):
                    merged = merged[:s] + b_orig + merged[e:] if merged[s:e] == text[s:e] else merged
            alt = re.sub(r"(?<=[一-鿿，。！？；：])\s+|\s+(?=[一-鿿，。！？；：])", "", merged)
            if alt == text:
                alt = ""
    for s, e, p, _w in low_prob_spans(text, list(words)) if words else []:
        spans.append([s, e]); weights.append(0.5 if p < 0.3 else 0.3)
        reasons.append(f"「{text[s:e]}」识别把握不大（{p:.0%}）")
    if not spans:
        return None
    score = 1.0
    for w in weights:
        score *= (1.0 - w)
    score = round(1.0 - score, 3)
    if score < 0.45:          # e.g. a single weak low-probability word -> not shown
        return None
    return {"spans": merge_spans(spans), "alt": alt, "reasons": list(dict.fromkeys(reasons)), "score": score}


if __name__ == "__main__":
    print("---- build_suspect")
    for a, b in [("这个户字的意思是whose，大家记一下。", "这 个 户 字 的 意 思 是 户 字 大 家 记 一 下"),
                 ("大家好，今天天气不错 the 我们开始上课。", "大家好今天天气不错的我们开始上课"),
                 ("那个，我们打开Python的设置页面。", "嗯那个我们打开派森的设置页面"),
                 ("我们今天讲十个函数。", "我们今天讲是个函数"),
                 ("完全不相关的一句话。", "the quick brown fox")]:
        print(a, "=>", build_suspect(a, b))
    class Wd:
        def __init__(self, w, p): self.word, self.probability = w, p
    words = [Wd("我們", .98), Wd("今天", .97), Wd("講", .9), Wd(" V", .2), Wd("FIX", .25), Wd("ED", .3), Wd("的", .9),
             Wd("用法", .95), Wd("，", .9), Wd("這個", .96), Wd("函數", .4), Wd("很", .99), Wd("常用。", .97)]
    t = "我们今天讲VFIXED的用法，这个函数很常用。"
    print(low_prob_spans(t, words))
    print(build_suspect(t, "", words))
