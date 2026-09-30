"""讲稿解析：把 txt / md / srt / docx 讲稿切成适合合成的句子。

讲稿里可以用的标记：
    空一行                     → 段落停顿（按你本人的段落停顿习惯）
    [停顿] / [pause]           → 段落停顿
    [停顿=1.5] / [停顿 2秒]    → 指定停顿秒数（[pause=1.5s]、<break time="800ms"/> 也可以）
Markdown 的标题、列表、加粗、链接会被自动清理；``` 代码块默认不朗读。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from voicetwin.utils.textutil import (
    CLAUSE_CHARS,
    count_cjk,
    detect_lang,
    ensure_final_punct,
    sentence_kind,
    syllable_count,
)

PAUSE_RE = re.compile(
    r"\[(?:停顿|暂停|pause|break)(?:\s*[=:：]?\s*(\d+(?:\.\d+)?)\s*(ms|毫秒|s|秒)?)?\s*\]"
    r"|<break\s+time\s*=\s*[\"']?(\d+(?:\.\d+)?)\s*(ms|s)?[\"']?\s*/?>",
    re.IGNORECASE,
)
ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e", "no", "fig", "eq",
                 "approx", "dept", "inc", "ltd", "co", "u.s", "a.m", "p.m"}
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]+")


@dataclass
class ScriptSegment:
    text: str                           # 送去合成的文字（已应用读音词典）
    display: str                        # 字幕显示的原文
    lang: str
    kind: str = "statement"
    pause_after: Union[str, float] = "sentence"   # clause | sentence | paragraph | 秒数
    paragraph: int = 0
    cue_start: Optional[float] = None   # 按字幕时间轴合成时使用
    cue_end: Optional[float] = None
    index: int = 0
    extra: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- 读取
def read_script_file(path: Path) -> Tuple[str, Optional[list]]:
    """返回 (纯文本, 字幕 cue 列表或 None)。"""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in (".srt", ".vtt"):
        from voicetwin.data.subtitles import parse_subtitles

        return "", parse_subtitles(path)
    if ext == ".docx":
        try:
            import docx  # type: ignore
        except ImportError as exc:
            raise RuntimeError("读取 Word 讲稿需要：pip install python-docx（或另存为 txt）") from exc
        doc = docx.Document(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip()), None
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            return raw.decode(enc), None
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), None


# ----------------------------------------------------------------------------- 清理
def clean_markdown(text: str, skip_code_blocks: bool = True) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if skip_code_blocks:
        text = re.sub(r"```.*?```", "\n\n", text, flags=re.S)
    else:
        text = text.replace("```", "")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                    # 图片
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)               # 链接
    text = re.sub(r"<(?!break\b)[^>]+>", "", text)                      # HTML 标签（保留 <break>）
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if re.fullmatch(r"[-*_=|:\s]{3,}", s):                          # 分隔线 / 表格分隔
            lines.append("")
            continue
        heading = re.match(r"^#{1,6}\s+(.*)$", s)
        if heading:
            h = heading.group(1).strip()
            lines += ["", ensure_final_punct(h, detect_lang(h)), ""]
            continue
        s = re.sub(r"^>\s?", "", s)                                     # 引用
        s = re.sub(r"^(?:[-*+]|\d+[.)、])\s+", "", s)                   # 列表
        if s.startswith("|") and s.endswith("|"):                       # 表格行
            s = "，".join(c.strip() for c in s.strip("|").split("|") if c.strip())
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = EMOJI_RE.sub("", text)
    return text


def apply_lexicon(text: str, lexicon: Sequence[Tuple[str, str]]) -> str:
    for src, dst in sorted(lexicon, key=lambda p: -len(p[0])):
        if re.fullmatch(r"[A-Za-z0-9 .+#-]+", src):
            text = re.sub(rf"(?<![A-Za-z]){re.escape(src)}(?![A-Za-z])", dst, text)
        else:
            text = text.replace(src, dst)
    return text


def tts_normalize(text: str) -> str:
    text = text.replace("——", "，").replace("--", "，")
    text = re.sub(r"(?<=\d)\s*[~～]\s*(?=\d)", "到" if count_cjk(text) else " to ", text)
    text = text.replace("~", " ").replace("～", " ")
    text = re.sub(r"[\[\]{}【】<>《》]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+(?=[，。！？；：,.!?;:])", "", text)
    return ensure_final_punct(text, detect_lang(text)) if text else text


# ----------------------------------------------------------------------------- 切句
def split_sentences(paragraph: str) -> List[str]:
    """按句末标点切句；英文句点要排除小数、缩写。"""
    out: List[str] = []
    buf = ""
    i, n = 0, len(paragraph)
    closers = "”\"'’）)」』】"
    while i < n:
        ch = paragraph[i]
        buf += ch
        boundary = False
        if ch in "。！？!?；;…":
            while i + 1 < n and (paragraph[i + 1] in "。！？!?…" or paragraph[i + 1] in closers):
                i += 1
                buf += paragraph[i]
            boundary = True
        elif ch == ".":
            prev_word = re.search(r"([A-Za-z.]+)\.$", buf)
            nxt = paragraph[i + 1] if i + 1 < n else ""
            is_decimal = bool(re.search(r"\d\.$", buf)) and nxt.isdigit()
            is_abbr = bool(prev_word) and prev_word.group(1).lower().rstrip(".") in ABBREVIATIONS
            single_initial = bool(re.search(r"(?:^|\s)[A-Z]\.$", buf))
            if not is_decimal and not is_abbr and not single_initial and (nxt == "" or nxt.isspace() or count_cjk(nxt)
                                                                           or nxt in closers):
                while i + 1 < n and paragraph[i + 1] in closers:
                    i += 1
                    buf += paragraph[i]
                boundary = True
        if boundary:
            if buf.strip():
                out.append(buf.strip())
            buf = ""
        i += 1
    if buf.strip():
        out.append(buf.strip())
    return out


def _split_clauses(sentence: str) -> List[str]:
    parts = re.split(f"(?<=[{re.escape(CLAUSE_CHARS)}])", sentence)
    return [p.strip() for p in parts if p.strip()]


def _hard_split(text: str, max_units: int) -> List[str]:
    """一个分句仍然太长（很少见）：英文按单词、中文按字数硬切。"""
    if count_cjk(text) == 0:
        words, out, cur = text.split(), [], []
        for w in words:
            if cur and syllable_count(" ".join(cur + [w])) > max_units:
                out.append(" ".join(cur))
                cur = []
            cur.append(w)
        if cur:
            out.append(" ".join(cur))
        return out
    out, cur = [], ""
    for ch in text:
        if syllable_count(cur + ch) > max_units and cur:
            out.append(cur)
            cur = ""
        cur += ch
    if cur:
        out.append(cur)
    return out


def chunk_sentence(sentence: str, max_units: int) -> List[str]:
    if syllable_count(sentence) <= max_units:
        return [sentence]
    chunks: List[str] = []
    cur = ""
    for clause in _split_clauses(sentence):
        pieces = [clause] if syllable_count(clause) <= max_units else _hard_split(clause, max_units)
        for piece in pieces:
            joiner = "" if (count_cjk(cur[-1:]) or count_cjk(piece[:1]) or not cur) else " "
            if cur and syllable_count(cur + joiner + piece) > max_units:
                chunks.append(cur)
                cur = piece
            else:
                cur = cur + joiner + piece if cur else piece
    if cur:
        chunks.append(cur)
    return chunks


def _join(a: str, b: str) -> str:
    return a + ("" if count_cjk(a[-1:]) or count_cjk(b[:1]) else " ") + b


# ----------------------------------------------------------------------------- 主函数
def parse_script(source: Union[str, Path], lexicon: Sequence[Tuple[str, str]] = (), max_units_zh: int = 50,
                 max_units_en: int = 45, min_units: int = 6, skip_code_blocks: bool = True) -> List[ScriptSegment]:
    cues = None
    if isinstance(source, Path) or (isinstance(source, str) and len(source) < 1024 and "\n" not in source
                                    and Path(source).suffix.lower() in (".txt", ".md", ".srt", ".vtt", ".docx", ".markdown")
                                    and Path(source).exists()):
        text, cues = read_script_file(Path(source))
    else:
        text = str(source)
    if cues is not None:
        return _segments_from_cues(cues, lexicon, max_units_zh, max_units_en)

    text = clean_markdown(text, skip_code_blocks)
    # 把停顿标记替换成独立占位行
    tokens: List[Union[str, float]] = []
    pos = 0
    for m in PAUSE_RE.finditer(text):
        tokens.append(text[pos:m.start()])
        num, unit = (m.group(1), m.group(2)) if m.group(1) or m.group(0).startswith("[") else (m.group(3), m.group(4))
        if num:
            sec = float(num) / (1000.0 if unit and unit.lower() in ("ms", "毫秒") else 1.0)
            tokens.append(sec)
        else:
            tokens.append(-1.0)  # 段落停顿
        pos = m.end()
    tokens.append(text[pos:])

    segments: List[ScriptSegment] = []
    para_idx = 0
    for tok in tokens:
        if isinstance(tok, float):
            if segments:
                segments[-1].pause_after = "paragraph" if tok < 0 else tok
            continue
        paragraphs = re.split(r"\n\s*\n", tok)
        for p_i, para in enumerate(paragraphs):
            lines = [ln.strip() for ln in para.split("\n") if ln.strip()]
            if not lines:
                continue
            # 合并被硬换行打断的英文句子；其它换行视为句子结束
            merged = lines[0]
            for ln in lines[1:]:
                if re.search(r"[A-Za-z,]$", merged) and re.match(r"^[a-z]", ln):
                    merged += " " + ln
                else:
                    merged = ensure_final_punct(merged, detect_lang(merged)) + ("" if count_cjk(ln[:1]) else " ") + ln
            sentences = split_sentences(merged)
            # 太短的句子并入下一句（例如"好。"单独合成不自然）
            packed: List[str] = []
            for s in sentences:
                limit = max_units_zh if detect_lang(s) == "zh" else max_units_en
                if packed and syllable_count(packed[-1]) < min_units and syllable_count(_join(packed[-1], s)) <= limit:
                    packed[-1] = _join(packed[-1], s)
                else:
                    packed.append(s)
            if len(packed) > 1 and syllable_count(packed[-1]) < min_units:
                last = packed.pop()
                packed[-1] = _join(packed[-1], last)
            for s_i, sent in enumerate(packed):
                lang = detect_lang(sent)
                chunks = chunk_sentence(sent, max_units_zh if lang == "zh" else max_units_en)
                for c_i, chunk in enumerate(chunks):
                    last_chunk = c_i == len(chunks) - 1
                    pause: Union[str, float] = "clause" if not last_chunk else "sentence"
                    if last_chunk and s_i == len(packed) - 1:
                        pause = "paragraph"
                    display = chunk.strip()
                    tts_text = tts_normalize(apply_lexicon(display, lexicon))
                    if not syllable_count(tts_text):
                        continue
                    segments.append(ScriptSegment(text=tts_text, display=display, lang=detect_lang(tts_text),
                                                  kind=sentence_kind(sent), pause_after=pause, paragraph=para_idx))
            para_idx += 1
    if segments and segments[-1].pause_after == "paragraph":
        segments[-1].pause_after = 0.0
    for i, s in enumerate(segments):
        s.index = i
    return segments


def _segments_from_cues(cues: list, lexicon, max_units_zh: int, max_units_en: int) -> List[ScriptSegment]:
    segments: List[ScriptSegment] = []
    for c_i, cue in enumerate(cues):
        lang = detect_lang(cue.text)
        chunks = chunk_sentence(cue.text, max_units_zh if lang == "zh" else max_units_en)
        for k, chunk in enumerate(chunks):
            tts_text = tts_normalize(apply_lexicon(chunk, lexicon))
            if not syllable_count(tts_text):
                continue
            segments.append(ScriptSegment(
                text=tts_text, display=chunk, lang=detect_lang(tts_text), kind=sentence_kind(cue.text),
                pause_after="clause" if k < len(chunks) - 1 else 0.0, paragraph=c_i,
                cue_start=cue.start if k == 0 else None, cue_end=cue.end if k == len(chunks) - 1 else None,
            ))
    for i, s in enumerate(segments):
        s.index = i
    return segments
