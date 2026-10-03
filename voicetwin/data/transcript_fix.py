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
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple

from voicetwin.data import proofcheck as pc
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import clean_transcript

try:  # 停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    def _check_cancel() -> None:
        return None

log = get_logger("transcript_fix")

ProgressFn = Callable[[float, str], None]

TRANSCRIPT_DIR = "逐字稿"  # 声音文件夹里存老师上传的逐字稿（再点「文字校正」不用重新上传）
TEXT_SUFFIXES = (".txt", ".csv", ".tsv")  # txt：一行一句；transcripts.csv：用 text 列（删除的句子不要）
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
    if raw.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        return raw.decode("utf-32", errors="replace")
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


def _looks_binary(raw: bytes) -> bool:
    """不是文字文件：压缩包（Excel / WPS 的 .xlsx、Word 的 .docx 都是）、旧的 .xls / .doc、里面有很多 0 字节的。"""
    head = raw[:4000]
    if head.startswith((b"PK\x03\x04", b"\xd0\xcf\x11\xe0")):
        return True
    if head.startswith((b"\xff\xfe", b"\xfe\xff", b"\x00\x00\xfe\xff")):
        return False  # UTF-16 / UTF-32：本来就有很多 0 字节
    return bool(head) and head.count(b"\x00") > len(head) // 4 and not _utf16_like(head)


def _utf16_like(head: bytes) -> bool:
    """没有 BOM 的 UTF-16：每两个字节里有一个 0（英文、标点多的时候）。"""
    even, odd = head[0::2].count(0), head[1::2].count(0)
    return max(even, odd) > len(head) // 4 and min(even, odd) < len(head) // 20


def parse_mother(name: str, text: str) -> List[Tuple[str, str]]:
    """一个母本文件 → [(句子 id, 文字)]。txt 一行一句（没有 id）；transcripts.csv 用 id 和 text 两列，
    老师删除的句子不要；声音分身自己的 tsv（id<TAB>文字，# 开头是说明）。表格格式坏了的 csv 当 txt 一行一行读。
    每一句都整理成和校对表一样的写法（clean_transcript：英文后面的逗号是半角的「,」等），比较时才对得上。"""
    suffix = Path(str(name)).suffix.lower()
    text = str(text or "").replace("\x00", "")
    out: List[Tuple[str, str]] = []
    if suffix == ".csv":
        import csv
        import io

        try:
            reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
            fields = [str(f or "").strip().lower() for f in (reader.fieldnames or [])]
            if "text" in fields:
                for row in reader:
                    low = {str(k or "").strip().lower(): (v or "") for k, v in row.items()}
                    if str(low.get("drop_reason", "")).strip() == "老师删除":
                        continue
                    line = clean_transcript(str(low.get("text", "")))
                    if line:
                        out.append((str(low.get("id", "")).strip(), line))
                return out
        except csv.Error:
            out = []
    if suffix == ".tsv":
        for ln in text.splitlines():
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            rid, _, line = ln.partition("\t")
            if not _:
                rid, line = "", rid
            line = clean_transcript(line)
            if line:
                out.append((rid.strip(), line))
        return out
    for ln in text.splitlines():
        line = clean_transcript(ln)
        if line:
            out.append(("", line))
    return out


def save_transcripts(project: Any, paths: Iterable[Any], refuse_useless: bool = False) -> Dict[str, Any]:
    """把这次上传的母本 / 逐字稿存进声音文件夹（替换上次上传的），统一存成 UTF-8。返回 transcript_info。

    txt、transcripts.csv 都行。读出来没有文字的、不是这两种的：说明原因（ValueError），一个都不存。
    太长的（程序自带的母本加上去超过 MAX_TOKENS，后面的用不上）也不存，说明原因（以前悄悄只用前面的，页面上还说都用了）。
    refuse_useless=True（网页上的按钮）：上传的句子全都和校对表（或程序自带的母本）一模一样（这个声音自己下载的文字、
    自己的 transcripts.csv）时也不存——用不上，还会把上次上传的有用的母本换掉（这批素材的一键校正也还没用掉）。"""
    items: List[Tuple[str, str, List[Tuple[str, str]]]] = []
    bad: List[str] = []
    for p in paths or []:
        src = Path(_file_name(p))
        if not src.name:
            continue
        if src.suffix.lower() not in TEXT_SUFFIXES:
            bad.append(f"「{src.name}」不是 txt 或 csv 文件")
            continue
        try:
            if _looks_binary(src.read_bytes()[:4000]):
                bad.append(f"「{src.name}」不是文字文件（可能是 Excel / WPS 表格或 Word 文档改了名字；表格请用"
                           "「另存为」选「CSV UTF-8」，Word 请「另存为」纯文本 .txt）")
                continue
            text = read_text_file(src)
            parsed = parse_mother(src.name, text)
        except (OSError, ValueError) as exc:
            bad.append(f"「{src.name}」读不出来（{exc}）")
            continue
        if _useful_chars(" ".join(x for _, x in parsed)) < MIN_CHARS:
            bad.append(f"「{src.name}」里几乎没有文字")
            continue
        items.append((src.name, text, parsed))
    if bad:
        raise ValueError("母本没有存上：" + "；".join(bad) + "。请上传记事本保存的 .txt 文件，或者声音文件夹里的 "
                         "transcripts.csv（Word 文档可以先「另存为」纯文本 .txt）。")
    if not items:
        raise ValueError("没有收到母本文件，请先选好文件再点「📝 一键全部文字校正」。")
    selves = _row_texts(project)
    kept = [(name, [(rid, x) for rid, x in parsed if _norm_line(x) not in selves]) for name, _t, parsed in items]
    chars, room = sum(_useful_chars(x) for _, fl in kept for _rid, x in fl), upload_room()
    if chars > room:
        raise ValueError(f"母本没有存上：这次上传的文字一共 {chars} 个字 / 词（和校对表一模一样的句子不算），"
                         f"最多只能用 {room} 个——多出来的部分用不上。请只上传和这批录音有关的讲稿，少选几个文件再试。"
                         "这次什么都没改，上次上传的母本还在，这批素材的「📝 一键全部文字校正」也还能用。")
    if refuse_useless and not _any_usable([x for _, fl in kept for x in fl], selves):
        names = "、".join(f"「{name}」" for name, _t, _p in items)
        raise ValueError(f"母本没有存上：{names}里的句子和校对表（或者程序自带的母本）里的一模一样——这是这个声音自己的文字"
                         "（比如「⬇️ 下载改好的文字」存的 txt、这个声音的 transcripts.csv）。一句话不能拿来证明它自己没错，"
                         "所以用不上（它可以给别的声音当母本用）。这次什么都没改，上次上传的母本还在，"
                         "这批素材的「📝 一键全部文字校正」也还能用；要上传的话，请选这批录音的讲稿。")
    folder = transcript_dir(project)
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    _parse_file.cache_clear()
    used: Set[str] = set()
    for name, text, _parsed in items:
        stem = re.sub(r'[\\/:*?"<>|]+', "_", Path(name).stem).strip() or "母本"
        suffix = Path(name).suffix.lower()
        out, k = f"{stem}{suffix}", 2
        while out.lower() in used:
            out, k = f"{stem}_{k}{suffix}", k + 1
        used.add(out.lower())
        (folder / out).write_text(text.replace("\r\n", "\n"), encoding="utf-8")
    info = transcript_info(project)
    log.info(f"已保存母本：{'、'.join(info['files'])}（共 {info['chars']} 字）")
    return info


@lru_cache(maxsize=64)
def _parse_file(path: str, size: int, mtime_ns: int) -> Tuple[Tuple[str, str, int], ...]:
    """一个存好的母本文件：((句子 id, 文字, 字 / 词数), ...)。文件没变（名字、大小、修改时间都一样）就不再读一遍、
    不再数一遍（表格里每做一个操作，按钮下面的说明都要刷新；以前每次都把上传的文字整个重新读、重新数，大文件要好几秒）。"""
    p = Path(path)
    return tuple((rid, x, _useful_chars(x)) for rid, x in parse_mother(p.name, read_text_file(p)))


def load_transcript_files(project: Any) -> List[Tuple[str, List[Tuple[str, str, int]]]]:
    """老师上传的母本，按文件：[(文件名, [(句子 id, 文字, 字 / 词数), ...])]（按文件名排序）。读不了的文件跳过。"""
    folder = transcript_dir(project)
    if not folder.is_dir():
        return []
    out: List[Tuple[str, List[Tuple[str, str, int]]]] = []
    for p in sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES):
        try:
            st = p.stat()
            out.append((p.name, list(_parse_file(str(p), st.st_size, st.st_mtime_ns))))
        except (OSError, ValueError):  # 读不了的文件跳过，不影响别的
            continue
    return out


def load_transcripts(project: Any) -> Tuple[List[Tuple[str, str]], List[str]]:
    """老师上传的母本：[(句子 id, 文字)] 和文件名。没有时返回 ([], [])。"""
    files = load_transcript_files(project)
    return [(rid, x) for _name, fl in files for rid, x, _n in fl], [name for name, _fl in files]


#: 「📝 一键全部文字校正」每批素材只能用一次（老师 10-03 的要求）：用过以后在声音文件夹里记下这次处理过的句子（id），
#: 按钮变灰；以后加了新的素材、识别出新的句子，按钮再亮起来，只改新加的那些句子
USED_FILE = "textfix_used.json"


def _all_ids(project: Any) -> List[str]:
    return [str(r.get("id")) for r in project.load_manifest() if r.get("id")]


def textfix_eligible_ids(project: Any) -> List[str]:
    """「一键全部文字校正」能处理的句子：没删除、要用（不是「不用」）、已经有文字（按表格里显示的，含没保存的修改）。
    还没识别出文字、标了「不用」的句子不算——等识别完 / 改成要用以后才算新素材。"""
    from voicetwin.data import review as _review

    draft = _review.load_draft(project)
    out = []
    for r in project.load_manifest():
        if not r.get("id") or r.get("deleted"):
            continue
        vals = _review.current_values(r, draft.get(r["id"]))
        if vals["keep"] and str(vals["text"] or "").strip():
            out.append(str(r["id"]))
    return out


def textfix_ever_used(project: Any) -> bool:
    """这个声音用过「一键全部文字校正」没有（有记录）。"""
    return (Path(project.root) / USED_FILE).exists()


def textfix_done_ids(project: Any) -> Set[str]:
    """用过「一键全部文字校正」的句子（记录里的 id）；没有记录、读不了都返回空的（只用来合并结果，不改记录）。"""
    import json

    from voicetwin.utils import atomic

    try:
        data = json.loads(atomic.read_text(Path(project.root) / USED_FILE))
    except (OSError, ValueError):
        return set()
    if isinstance(data, dict) and isinstance(data.get("ids"), list):
        return {str(x) for x in data["ids"]}
    return set()


def textfix_new_ids(project: Any) -> List[str]:
    """还没用过「一键全部文字校正」、现在能处理的句子：空的 = 按钮是灰色的。
    记录坏了：当作现在的句子都用过了（宁可不改，也不重复改），并且重新记一份，以后加的新素材照样认得出来。"""
    import json

    from voicetwin.utils import atomic

    path = Path(project.root) / USED_FILE
    live = textfix_eligible_ids(project)
    try:
        text = atomic.read_text(path)
    except FileNotFoundError:
        return live
    except OSError as exc:  # 一直读不了：当作都用过（按钮灰的），不重写记录（不能把以前的记录冲掉）
        log.warning(f"「一键全部文字校正」的记录现在读不了（{exc}），这次当作都用过")
        return []
    try:
        data = json.loads(text)
        done = {str(x) for x in data["ids"]} if isinstance(data, dict) and isinstance(data.get("ids"), list) else None
    except (ValueError, TypeError):
        done = None
    if done is None:
        log.warning("「一键全部文字校正」的记录读不了，当作现在的句子都已经用过（以后加的新素材照样能用）")
        mark_textfix_used(project, _all_ids(project))
        return []
    return [x for x in live if x not in done]


def textfix_used(project: Any) -> bool:
    """这批素材（现在所有没删除的句子）是不是都已经用过「一键全部文字校正」了（按钮该是灰色的）。"""
    return not textfix_new_ids(project)


def mark_textfix_used(project: Any, ids: Iterable[str]) -> None:
    """记下这些句子用过「一键全部文字校正」了（和以前记下的合在一起）。"""
    import json

    from voicetwin.utils import atomic

    path = Path(project.root) / USED_FILE
    done: Set[str] = set()
    try:
        old = json.loads(atomic.read_text(path))  # 一时读不了等一会儿；一直读不了就报错，不能把以前的记录冲掉
        if isinstance(old, dict) and isinstance(old.get("ids"), list):
            done = {str(x) for x in old["ids"]}
    except FileNotFoundError:
        pass
    except (ValueError, TypeError):  # 坏了：留一份副本，从这次开始重新记
        atomic.keep_bad_copy(path)
    done |= {str(x) for x in ids}
    from voicetwin.utils import atomic

    atomic.write_text(path, json.dumps({"used": True, "at": time.strftime("%Y-%m-%d %H:%M:%S"), "ids": sorted(done)},
                                       ensure_ascii=False))


def transcript_info(project: Any) -> Dict[str, Any]:
    """存好的母本：files 文件名；chars 用得上的字 / 词数（和校对表里某一句一模一样的不算：那是这一句自己，证明不了什么）；
    lines / same_lines 一共几句、其中几句和校对表一模一样；files_same 全都一模一样的文件；
    room 最多能用多少个字 / 词（程序自带的母本占了一部分）；too_long 超过了（只用前面的）。"""
    files = load_transcript_files(project)
    selves = _row_texts(project) if files else set()
    chars = lines = same = 0
    files_same: List[str] = []
    for name, fl in files:
        usable = [n for _rid, x, n in fl if _norm_line(x) not in selves]
        lines += len(fl)
        same += len(fl) - len(usable)
        chars += sum(usable)
        if fl and not usable:
            files_same.append(name)
    room = upload_room()
    return {"files": [name for name, _fl in files], "chars": chars, "lines": lines, "same_lines": same,
            "files_same": files_same, "room": room, "too_long": chars > room, "builtin": len(builtin_mother())}


def upload_room() -> int:
    """老师上传的母本最多能用多少个字 / 词（MAX_TOKENS 减去程序自带的母本）。"""
    return max(0, MAX_TOKENS - _builtin_tokens())


@lru_cache(maxsize=1)
def _builtin_tokens() -> int:
    return _useful_chars("\n".join(x for _, x in builtin_mother()))


def _any_usable(lines: Sequence[Tuple[str, str]], selves: Set[str]) -> bool:
    """上传的句子里有没有一句真的用得上（见 _filter_upload）；找到一句就不再往下看（大文件也快）。"""
    from voicetwin.data.lexicon_fix import Lexicon

    todo = [(rid, x) for rid, x in (lines or []) if _norm_line(x) not in selves]
    if not todo:
        return False
    builtin = builtin_mother()
    row_table, by_id, cleaner = dict(builtin_fixes()), {rid: x for rid, x in builtin if rid}, Lexicon.build([])
    return any(_filter_upload([line], selves, row_table, by_id, cleaner) for line in todo)


def _filter_upload(lines: Sequence[Tuple[str, str]], selves: Set[str], row_table: Dict[str, Any],
                   builtin_by_id: Dict[str, str], cleaner: Any) -> List[Tuple[str, str]]:
    """老师上传的母本里真正拿来用的句子：和校对表某一句（现在的 / 保存的 / 最初识别的样子）一模一样的不用（就是那一句自己，
    比如下载的「改好的文字」，什么也证明不了，不然没检查过的句子会「自己证明自己没错」）；先按对照表、逐句修缮记录改掉里面的
    识别错，改完和程序自带的一模一样的、和校对表某一句一模一样的也不用。"""
    out = [(rid, x) for rid, x in (lines or []) if _norm_line(x) not in selves]
    out = _clean_uploaded(out, row_table, builtin_by_id, cleaner) if out else []
    return [(rid, x) for rid, x in out if _norm_line(x) not in selves]


BUILTIN_MOTHER = Path(__file__).resolve().parent / "lexicon" / "core_corpus.tsv"
BUILTIN_FIXES = Path(__file__).resolve().parent / "lexicon" / "core_fixes.tsv"


@lru_cache(maxsize=1)
def builtin_mother() -> Tuple[Tuple[str, str], ...]:
    """程序自带的母本：老师修缮过的讲课文字（老师同意公开）。"""
    try:
        return tuple(parse_mother(BUILTIN_MOTHER.name, BUILTIN_MOTHER.read_text(encoding="utf-8")))
    except OSError:
        return ()


@lru_cache(maxsize=1)
def builtin_fixes() -> Dict[str, Tuple[Tuple[str, str, str], ...]]:
    """逐句修缮母本时改掉的识别错误：{句子 id: ((原来, 改成, 原因), ...)}。"""
    out: Dict[str, List[Tuple[str, str, str]]] = {}
    try:
        text = BUILTIN_FIXES.read_text(encoding="utf-8")
    except OSError:
        return {}
    for ln in text.splitlines():
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if len(parts) >= 3 and parts[1] and parts[2]:
            out.setdefault(parts[0], []).append((parts[1], parts[2], parts[3] if len(parts) > 3 else ""))
    return {k: tuple(v) for k, v in out.items()}


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
def _norm_line(text: str) -> str:
    return " ".join(str(text or "").split())


class Reference:
    """处理好的逐字稿：每个字的读音、按读音找位置的索引、哪些写法出现过。"""

    def __init__(self, text: Any, progress: Optional[ProgressFn] = None, own_from: int = 0,
                 vetted_lines: Optional[int] = None):
        """text：一整段文字，或者 [(句子 id, 文字)]（有 id 的句子会记下它在哪里，比对同一句时可以跳过它自己）。
        own_from：从第几行开始是老师上传的（这些行和某一句一模一样时算「它自己」；程序自带的修缮过的母本不算）。
        vetted_lines：前面这么多行是修缮过的（程序自带的母本），后面的是老师上传、没修缮过的（打字的讲稿、别的识别软件的文字，
        可能有同音错字）——只对上后面这些的单个字不直接改（见 check_text）。不给：都当修缮过的（以前的做法）。"""
        if isinstance(text, (list, tuple)):
            lines = [(str(i or ""), str(x or "")) for i, x in text]
        else:
            lines = [("", str(text or ""))]
        self.text = "\n".join(x for _, x in lines)
        starts, pos = [], 0
        for _, x in lines:
            starts.append(pos)
            pos += len(x) + 1
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
        import bisect

        # 每一句在哪里：按 id（一个 id 可能出现好几次：程序自带的母本和老师上传的 transcripts.csv 里都有同一句）、
        # 按文字（没有 id 的 txt 里和这一句一模一样的那一行就是它自己，不能拿来证明它没错）
        line_span: Dict[int, Tuple[int, int]] = {}
        for k, tk in enumerate(self.toks):
            li = bisect.bisect_right(starts, tk.start) - 1
            if 0 <= li < len(lines):
                a, _b = line_span.get(li, (k, k + 1))
                line_span[li] = (a, k + 1)
        self.id_ranges: Dict[str, List[Tuple[int, int]]] = {}
        self.text_ranges: Dict[str, List[Tuple[int, int]]] = {}
        for li in sorted(line_span):
            rid, x = lines[li]
            if rid:
                self.id_ranges.setdefault(rid, []).append(line_span[li])
            if li >= own_from:
                self.text_ranges.setdefault(_norm_line(x), []).append(line_span[li])
        self.last_line = max(line_span) if line_span else -1  # 太长被截掉时：最后用到了第几行
        # 每一句的第一个字 / 最后一个字后面在哪里（母本优先：只对上一部分时，那一部分必须正好是母本里完整的一句）
        self.line_firsts: Set[int] = {a for a, _b in line_span.values()}
        self.line_ends: Set[int] = {b for _a, b in line_span.values()}
        self.line_of: Dict[int, int] = {a: li for li, (a, _b) in line_span.items()}  # 一句的第一个字 → 第几行
        self.line_of_end: Dict[int, int] = {b: li for li, (_a, b) in line_span.items()}  # 一句的最后一个字后面 → 第几行
        self.line_chars: List[Tuple[int, int]] = [(st, st + len(x)) for st, (_i, x) in zip(starts, lines)]
        # 老师上传的（没修缮过的）从第几个字 / 词开始
        firsts = [line_span[li][0] for li in line_span if vetted_lines is not None and li >= vetted_lines]
        self.unvetted_from = min(firsts) if firsts else len(self.toks)

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
    strong: bool = False  # 整句几乎一样、前后都对得上：按母本直接改
    unvetted: bool = False  # 只对上了老师上传的母本（没修缮过）的单个字：不直接改，读音很像的只给没把握的建议


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
        self.cov = self.matched / n if n else 0.0
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
        """母本证明没错的字（识别文字里的位置）：只有整句几乎一样（≥ 85% 的字对得上）时，连着 ≥ 2 个一模一样的字才算。
        局部对上（「这个句子」这种常说的话）不能证明录音里就是这么说的，不算。"""
        if self.mode != "S" or self.cov < STRONG_COVERAGE:
            return set()
        need = 2
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


STRONG_COVERAGE = 0.85  # 整句这么多字都对得上，并且不一样的地方前后各有 ≥ 2 个一样的字：按母本直接改
_STRONG_KINDS = ("near", "same", "cjk_en", "en_cjk", "en")
_UNVETTED_KINDS = ("near", "same")  # 只对上老师上传的母本时不直接改的（单个汉字）
UNVETTED_WEIGHT = 0.6  # 这种只给没把握的建议（一键校正不自动采用，老师听录音决定）


def _strong(al: "_Align", kind: str, i1: int, i2: int, j1: int, j2: int) -> bool:
    if al.mode != "S" or al.cov < STRONG_COVERAGE or kind not in _STRONG_KINDS:
        return False
    left, right, at_start, at_end = al.ctx(i1, i2, j1, j2)
    return (left >= 2 or at_start) and (right >= 2 or at_end) and left + right >= 2


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
                reason = f"「{_q(cs)}」和母本里的「{_q(rep)}」读音一样（不影响训练，改不改都行）"
                kind = "same"
            else:
                if al.mode == "L" and not _absent_around(clip, ref, a1, a2):
                    continue  # 识别出来的写法逐字稿里也有：那也是老师的说法
                need = 2 if (al.mode == "L" and a2 - a1 >= 2 and all_diff) else 1
                if need == 2 and sum(al.ctx(a1, a2, b1, b2)[:2]) < 4:
                    continue
                reason = f"「{_q(cs)}」读音和母本里的「{_q(rep)}」很像，可能是识别错了"
                kind = "near"
        elif kinds == {"lat"}:
            if al.mode == "L" and (ref.latin.get(ct[0].key) or a2 - a1 > 2):
                continue
            rep = _rep_text(ref, b1, b2, "en")
            reason = f"英文「{_q(cs)}」母本里写的是「{_q(rep)}」（读音一样，可能是识别错了）"
            kind = "en"
            need = 1
        else:
            continue
        out.append(Prop(a1, a2, rep, kind, al.mode, W[(kind, al.mode)], reason, need, {b1}, (b1, b2),
                        strong=need == 1 and _strong(al, kind, a1, a2, b1, b2)))
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
                     f"「{_q(cs)}」可能是英文「{_q(rep)}」（母本里是 {_q(rep)}）", 1, {j1}, (j1, j2),
                     strong=_strong(al, "cjk_en", i1, i2, j1, j2))]
    if ck == {"lat"} and rk == {"han"} and len(ct) <= 2:
        # 汉字被写成了英文（the → 的）：读音必须像（以前整句对齐时「容易听错的英文词」不看读音也算，
        # 结果「who在定语从句中」被对到「词在……」上，一键校正把 who 改成了「词」）
        words = [t.key for t in ct]
        ok = sounds_like_english([t.tone for t in rt], words)
        if al.mode == "L":
            ok = ok and not any(ref.latin.get(w) for w in words)
        if not ok:
            return []
        rep = _rep_text(ref, j1, j2, "en_cjk")
        return [Prop(i1, i2, rep, "en_cjk", al.mode, W[("en_cjk", al.mode)],
                     f"「{_q(cs)}」可能是中文「{_q(rep)}」（母本里是「{_q(rep)}」）", 1, {j1}, (j1, j2),
                     strong=_strong(al, "en_cjk", i1, i2, j1, j2))]
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
                     f"英文「{_q(cs)}」母本里写的是「{_q(rep)}」（可能拼错了）", 1, {j1}, (j1, j2),
                     strong=_strong(al, "en", i1, i2, j1, j2))]
    if ck == {"num"} and rk == {"num"} and len(ct) == 1 and len(rt) == 1:
        a = _num_pinyin(clip.text[ct[0].start:ct[0].end])
        b = _num_pinyin(ref.text[rt[0].start:rt[0].end])
        if not a or not b or len(a) != len(b) or [fuzzy(x) for x in a] != [fuzzy(x) for x in b]:
            return []
        rep = ref.text[rt[0].start:rt[0].end]
        return [Prop(i1, i2, rep, "num", al.mode, W[("num", al.mode)],
                     f"数字「{_q(cs)}」读音和母本里的「{_q(rep)}」很像，可能是识别错了", 1, {j1}, (j1, j2))]
    return []


@dataclass
class ClipResult:
    props: List[Prop]
    confirmed_chars: Set[int]
    aligned: bool  # 整句对齐了
    ref_text: str


def check_text(text: str, ref: Reference, exclude_id: str = "", exclude_texts: Iterable[str] = ()) -> ClipResult:
    """一句识别文字和母本比：返回可能有错的地方、母本证明没错的字（字符位置）、整句对齐了没有。

    exclude_id：母本里同一句（同一个 id，就是这一句自己）不拿来比；exclude_texts：老师上传的母本里和这些文字一模一样的行
    （这一句现在的 / 保存的 / 最初识别的样子，比如下载的「改好的文字」）也不拿来比——它就是这一句自己，证明不了什么。
    程序自带的修缮过的母本照样能证明（同一句话换了 id 的片段）。"""
    clip = _Clip(text, ref)
    skips = list(ref.id_ranges.get(exclude_id, [])) if exclude_id else []
    for t in set(_norm_line(x) for x in exclude_texts if x):
        skips += ref.text_ranges.get(t, [])
    if not clip.toks or not len(ref):
        return ClipResult([], set(), False, "")
    found: Dict[Tuple[int, int, str], Prop] = {}
    confirmed_tok: Set[int] = set()
    aligned = False
    best_region: Optional[Tuple[int, int, int]] = None  # (对上的字数, 开始, 结束)
    for w0, w1 in _windows(clip, ref):
        for a, b in skips:  # 母本里同一个 id 的句子（每一处都）跳过：窗口切掉那一段，剩下的太短就不比
            if w0 < b and a < w1:
                if w0 < a - 2:
                    w1 = a
                elif w1 > b + 2:
                    w0 = b
                else:
                    w1 = w0
        if w1 - w0 < 2:
            continue
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
                if p.strong and p.kind in _UNVETTED_KINDS and p.i2 - p.i1 == 1 and p.ref[0] >= ref.unvetted_from:
                    # 只对上了老师上传的母本（没修缮过）：读音一样 / 很像的单个字，说不准是识别错了还是上传的文字打错了
                    # （拼音输入法打的讲稿常有「主雨」「过去试」），不直接改（以前把对的字直接改成了上传文字里的错字）
                    p.strong, p.unvetted = False, True
                key = (p.i1, p.i2, p.rep)
                old = found.get(key)
                if old is None:
                    found[key] = p
                else:
                    old.locs |= p.locs
                    if p.weight > old.weight:
                        old.weight, old.mode, old.reason, old.need, old.ref = p.weight, p.mode, p.reason, p.need, p.ref
                    old.need = min(old.need, p.need)
                    old.strong = old.strong or p.strong
                    old.unvetted = old.unvetted or p.unvetted
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
_CJK_OR_PUNCT = "[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff01-\uff60]"


def _tidy(text: str) -> str:
    """改完以后整理空格：去掉删词留下的两个空格、开头结尾的空格、两个中文字（标点）之间的空格。
    （不像 review.apply_edits 那样整理整句的标点，免得多出别的改动。）"""
    out = re.sub(r"[ \t]{2,}", " ", text)
    out = re.sub(rf"(?<={_CJK_OR_PUNCT}) (?={_CJK_OR_PUNCT})", "", out)
    return out.strip()


def _apply(text: str, edits: Sequence[Tuple[int, int, str]]) -> str:
    """从后往前改；重叠的跳过。改过的才整理（没改的原样返回）：整理成和校对表一样的写法（clean_transcript），
    和老师自己改、点「采用」存进去的文字一模一样——不然「艾子，→ as，」存成全角逗号，老师一点「采用」又变成半角，
    整句对不上（随机操作脚本发现的）。"""
    out, left = text, len(text) + 1
    for s, e, rep in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        if not (0 <= s <= e <= len(text)) or e > left or (e == left and s == e):
            continue
        out = out[:s] + rep + out[e:]
        left = s
    return clean_transcript(_tidy(out)) if out != text else out


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


def props_to_fixes(cur: str, res: ClipResult, lex: Any = None) -> List[Any]:
    """和母本对齐找出来的（Prop）→ 统一的改法（lexicon_fix.Fix）。整句几乎一样的直接改，别的只给建议。

    只给建议的再筛一遍（母本里有很多相似的句子，对齐到别的句子上容易误报）：标准库里的词（「及物动词」）不动；
    只差一个字的不提示；「英文被写成汉字」的那几个字本来就是常用的词（「它」「那么」「短语」）不提示。"""
    from voicetwin.data.lexicon_fix import Fix

    clip = tokens(cur)
    out = []
    for p in res.props:
        s, e = clip[p.i1].start, clip[p.i2 - 1].end
        weight, reason = p.weight, p.reason
        if not p.strong:
            if lex is not None and lex.inside_vocab(cur, s, e):
                continue
            if p.kind in ("near", "same") and p.i2 - p.i1 == 1:
                if not (p.unvetted and p.kind == "near"):
                    continue
                # 只对上了老师上传的母本、读音很像（声调不一样，影响训练）的单个字：给一个没把握的建议，老师听录音决定；
                # 读音一样的（不影响训练）不提示
                weight = min(weight, UNVETTED_WEIGHT)
                reason = reason.replace("母本里", "你上传的母本里", 1)
            if p.kind == "cjk_en" and lex is not None and lex.has_common_word(cur[s:e]):
                continue
            if p.kind == "cjk_en" and p.mode == "L" and _real_word(cur[s:e]):
                # 只是局部对上（「在这个地方」+ whose）、那几个汉字本身是个正常的词（出错）：母本优先以后，局部对上
                # 常说的话不算母本里有这一句，这种猜测不提示（以前把新内容里的「出错」猜成 whose）
                continue
        out.append(Fix(s, e, pc._pad(cur, s, e, p.rep), "align", bool(p.strong), weight, reason))
    return out


LOCAL_EN_MAX_FREQ = 100  # 局部对上时「汉字可能是英文」：这几个汉字在 jieba 词典里这么常见（出错 156）就是正常的词，不提示


def _real_word(piece: str) -> bool:
    """这几个汉字是不是一个正常的词（jieba 词典里出现 ≥ LOCAL_EN_MAX_FREQ 次；艾子 3、威驰 0 不算）。没有 jieba 时不算。"""
    from voicetwin.data.lexicon_fix import has_jieba, word_freq

    return has_jieba() and word_freq(str(piece or "").strip()) >= LOCAL_EN_MAX_FREQ


SURE_WEIGHT = 0.8  # 不是直接改的建议：分量这么大（或者另一个识别引擎也听成这样）才让「一键全部文字校正」自动采用


def _auto_edit_sure(cur: str, s: int, e: int, rep: str, lex: Any = None) -> bool:
    """自动查错字（另一个识别引擎）的一处建议，标准库能不能证明它对：只认「不是常用词的汉字，读音像英文」
    （艾子 → as：老师说的英文被写成了汉字）。别的（两个引擎听得不一样的中文、多 / 少的字）不知道哪个对，
    一键校正不自动采用，留着红色和建议，老师听录音自己点「采用」。"""
    old, new = cur[s:e].strip(), str(rep or "").strip()
    if not old or not new or lex is None:
        return False
    from voicetwin.data.lexicon_fix import word_bounds

    bounds = word_bounds(cur)  # 必须刚好是完整的词（「结构」里的「构」不算）
    if bounds is None or s not in bounds or e not in bounds:
        return False
    ot, nt = tokens(old), tokens(new)
    if not ot or not nt or {t.kind for t in ot} != {"han"} or {t.kind for t in nt} != {"lat"} or len(nt) > 2:
        return False
    return sounds_like_english([t.tone for t in ot], [t.key for t in nt]) and not lex.has_common_word(old)


def _core_fix(cur: str, f: Any) -> Any:
    """一处改法去掉前后没变的字（「关键代词 → 关系代词」只算「键 → 系」），免得把旁边别的标记也盖住。"""
    a, b = cur[f.start:f.end], str(f.rep)
    if not a or not b or a == b:
        return f
    p = 0
    while p < len(a) and p < len(b) and a[p] == b[p]:
        p += 1
    q = 0
    while q < len(a) - p and q < len(b) - p and a[len(a) - 1 - q] == b[len(b) - 1 - q]:
        q += 1
    if p == 0 and q == 0:
        return f
    from dataclasses import replace as _replace

    return _replace(f, start=f.start + p, end=f.end - q, rep=b[p:len(b) - q])


def _distinct_spans(spans: Sequence[Sequence[int]], text: str) -> List[List[int]]:
    """标红的地方：去掉无效的、重复的，排好序，但**不把挨着的合成一段**——改好的字和旁边自动查错字的标红合成一段以后，
    改好那几个字一变，整段都不红了；再点一次又冒出来（检查时发现的）。显示时表格自己会把挨着的红连起来。"""
    out: List[List[int]] = []
    for sp in spans:
        try:
            a, b = max(0, int(sp[0])), min(len(text), int(sp[1]))
        except (TypeError, ValueError, IndexError):
            continue
        if b > a and [a, b] not in out:
            out.append([a, b])
    return sorted(out)


def _same_place(ed: Tuple[int, int, str], span: Sequence[int]) -> bool:
    return ed[0] == span[0] and ed[1] == span[1]


def _in_covered(s: int, e: int, covered: Sequence[Tuple[int, int]]) -> bool:
    """[s, e) 碰到母本对上的部分（补字的位置在里面或者正好在边上也算）。"""
    if e <= s:
        return any(a <= s <= b for a, b in covered)
    return any(s < b and a < e for a, b in covered)


def _outside(spans: Sequence[Sequence[int]], covered: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """标红的地方去掉母本对上的部分（剩下的才是母本管不到的）。"""
    out: List[Tuple[int, int]] = []
    for sp in spans:
        parts = [(int(sp[0]), int(sp[1]))]
        for a, b in covered:
            nxt = []
            for x, y in parts:
                if y <= a or b <= x:
                    nxt.append((x, y))
                    continue
                if x < a:
                    nxt.append((x, a))
                if b < y:
                    nxt.append((b, y))
            parts = nxt
        out += [(x, y) for x, y in parts if y > x]
    return out


_QUOTE = re.compile(r"「([^」]+)」")


def _reason_inside(reason: str, cur: str, covered: Sequence[Tuple[int, int]]) -> bool:
    """自动查错字的一条说明讲的是不是母本对上的部分（说明里引用的这一句的字，每一处都在母本对上的部分里）：
    那里的建议已经去掉了，说明也去掉（不然说明里还写着和母本矛盾的「另一个引擎听成……」）。"""
    hits = []
    for q in _QUOTE.findall(str(reason or "")):
        k = cur.find(q)
        while k >= 0:
            hits.append((k, k + len(q)))
            k = cur.find(q, k + 1)
    return bool(hits) and all(any(a <= s and e <= b for a, b in covered) for s, e in hits)


def merge_with_auto(cur: str, fixes: Sequence[Any], confirmed: Set[int], auto: Optional[Dict[str, Any]],
                    rec: Dict[str, Any], ref_text: str = "", lex: Any = None,
                    allow_unchanged: bool = False, rejected: Any = None,
                    changed: Optional[Tuple[Set[int], Set[int]]] = None,
                    covered: Sequence[Tuple[int, int]] = ()
                    ) -> Tuple[Optional[Dict[str, Any]], str, List[Tuple[int, int, str]]]:
    """标准库 / 母本找出来的改法（fixes）和原来自动查错字的结果（auto）合起来。

    返回 (新的 suspect 或 None, 发生了什么, 要直接改的地方 [(开始, 结束, 改成)])。
    发生了什么：fixed = 有直接改好的；found = 只有建议；cleared = 原来标红、母本证明没错，去掉了；
    kept_auto = 只剩自动检查的标红（去掉了一部分）；unchanged_auto = 原样保留；none = 没有标红。
    没把握的建议（分量不够、整句换掉的、标准库证明不了的自动查错字建议）：suspect["sure_alt"] 是只用有把握的改出来的
    那一句；这一行的「采用」照样全部能用，但「一键全部文字校正」只按 sure_alt 改，没把握的留着红色让老师听录音决定。
    allow_unchanged=True：自动检查的结果原样保留时直接返回 auto（默认重新写一份，位置按现在的文字算，
    这样每一处建议有没有把握都记下了）。
    covered：母本里对上的部分（母本优先，[开始, 结束)）：那里母本就是标准答案——自动查错字（另一个识别引擎、规则）在那里的
    标红和建议都不要（和母本一样的已经在 fixes 里，和母本矛盾的是错的），说明里按母本的排在最前面。"""
    from voicetwin.data import review as _review
    from voicetwin.data.lexicon_fix import resolve

    fixes = [_core_fix(cur, f) for f in resolve(list(fixes))]  # 只算真正改到的字（前后没变的字不算）
    fixes.sort(key=lambda f: (0 if f.kind.startswith("mother") else 1, f.start, f.end))  # 按母本的排在最前面
    a_red: List[Tuple[int, int]] = []
    a_edits: List[Tuple[int, int, str]] = []
    a_reasons: List[str] = []
    a_score = 0.0
    a_total = False
    if auto:
        info = _review.analyze(dict(rec, suspect=auto), cur)
        a_red, a_edits = list(info["red"]), list(info["edits"])
        a_total = _review.whole_sentence_suggestion(auto, _review.suspect_base(dict(rec, suspect=auto)))
        a_reasons = [r for r in info["reasons"] if r]
        try:
            a_score = float(auto.get("score") or 0.6)
        except (TypeError, ValueError):
            a_score = 0.6
    tokchars = _token_chars(cur)
    if covered:  # 母本里对上的字：母本证明没错（要改的那几个字下面单独算）
        confirmed = set(confirmed) | {k for a, b in covered for k in range(a, b) if k in tokchars}
        a_red = _outside(a_red, covered)
        a_edits = [ed for ed in a_edits if not _in_covered(ed[0], ed[1], covered)]
        a_reasons = [r for r in a_reasons if not _reason_inside(r, cur, covered)]
    fixed_chars = {k for f in fixes for k in range(f.start, f.end)}
    # 老师撤销过的自动查错字建议：不再建议，那几个字也不再标红（和 🔍 自动查找一样）
    a_rej = [ed for ed in a_edits if _review.is_rejected(rejected, cur, *ed)] if rejected else []
    red_keep = [sp for sp in a_red if not _is_confirmed(sp[0], sp[1], confirmed, tokchars)
                and not all(k in fixed_chars for k in range(sp[0], sp[1]) if k in tokchars)
                and not any(sp[0] < max(e, s + 1) and s < sp[1] for s, e, _ in a_rej)
                and not (changed and _touches_changed(sp[0], sp[1], changed))]  # 老师自己改的字不标红
    t_edits: List[Tuple[int, int, str]] = []
    direct: List[Tuple[int, int, str]] = []
    spans: List[List[int]] = []
    reasons: List[str] = []
    weights: List[float] = []
    unsure: List[List[int]] = []
    for f in fixes:
        w, reason = f.weight, f.reason
        if any(es == f.start and ee == f.end and [x.key for x in pc.tokenize(er)] ==
               [x.key for x in pc.tokenize(f.rep)] for es, ee, er in a_edits):
            w = min(0.95, w + AGREE_BONUS)
            reason += "（另一个识别引擎也听成这样）"
        t_edits.append((f.start, f.end, f.rep))
        if f.direct:
            direct.append((f.start, f.end, f.rep))
            if f.kind.startswith("mother"):  # 「按母本：……」→「已按母本改好：……」
                reason = "已" + reason.replace("母本：", "母本改好：", 1)
            else:
                reason = "已按标准库改好：" + reason
        elif w < SURE_WEIGHT - 1e-9:
            unsure.append([f.start, f.end])
            reason = "没把握（请听录音）：" + reason
        spans.append([f.start, max(f.end, f.start + 1)])
        reasons.append(reason)
        weights.append(w)
    edits_keep = [ed for ed in a_edits if not _is_confirmed(ed[0], ed[1], confirmed, tokchars)
                  and all(ed[1] <= s or e <= ed[0] for s, e, _ in t_edits)
                  and any(not (ed[1] <= rs or re_ <= ed[0]) or ed[0] == ed[1] for rs, re_ in red_keep)
                  and not _review.is_rejected(rejected, cur, *ed)  # 老师撤销过的不再建议
                  and not (changed and _touches_changed(ed[0], ed[1], changed))]  # 老师自己改过的字不建议改回去
    auto_left = bool(red_keep or edits_keep)
    if not fixes:
        if not auto:
            return None, "none", []
        if not auto_left:
            return None, "cleared", []
        if allow_unchanged and not covered and len(red_keep) == len(a_red) and len(edits_keep) == len(a_edits):
            return auto, "unchanged_auto", []
    if auto_left:
        spans += [list(sp) for sp in red_keep]
        reasons += [(AUTO_PREFIX + r) if fixes else r for r in a_reasons]  # 只有自动检查的结果时不加前缀（和原来一样）
        weights.append(a_score)
        for ed in edits_keep:  # 另一个引擎整句听得都不一样、或者标准库证明不了：不知道哪个对，不自动采用
            if a_total or not _auto_edit_sure(cur, ed[0], ed[1], ed[2], lex):
                unsure.append([ed[0], ed[1]])
    edits = t_edits + edits_keep
    alt = _apply(cur, edits) if edits else ""
    sus: Dict[str, Any] = {"spans": _distinct_spans(spans, cur), "alt": alt if alt != cur else "",
                           "reasons": _limit_reasons(reasons), "score": round(_noisy_or(weights), 3),
                           "text": cur, "src": "transcript"}
    if unsure and sus["alt"]:
        # 只用有把握的改出来的那一句（一键校正只按它改）：不能靠位置判断哪一处没把握——同样的字挨着时
        # （看看、我们我们）两次比对的位置会差一个字，没把握的「补上 / 删掉」就混进来了（检查时发现的）
        sure_edits = [ed for ed in edits if not any(_same_place(ed, u) for u in unsure)]
        sus["sure_alt"] = _apply(cur, sure_edits) if sure_edits else cur
    if direct:  # 直接改好以后的整句（采用 / 撤销时整句换，不用对位置）
        sus["direct_alt"] = _apply(cur, direct)
    mother = [(f.start, f.end, f.rep) for f in fixes if f.kind.startswith("mother")]
    if mother:  # 只按母本改出来的整句：「修改建议」那一列按它分出哪些是「按母本：」的
        sus["mother_alt"] = _apply(cur, mother)
    if ref_text and fixes:
        sus["ref"] = ref_text
    what = "fixed" if direct else ("found" if fixes else "kept_auto")
    return sus, what, direct


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


def _similarity(a: str, b: str) -> float:
    """两句话有多像（按字 / 英文词比，0 ~ 1）。"""
    ka, kb = [x.key for x in tokens(a)], [x.key for x in tokens(b)]
    if not ka or not kb:
        return 0.0
    return difflib.SequenceMatcher(None, ka, kb, autojunk=False).ratio()


ROW_MIN_SIMILAR = 0.6  # 逐句修缮记录：这一句和母本里同一个 id 的句子至少这么像，才算同一句（新的录音碰巧同一个 id 时不乱改）


def _row_fixes(rid: str, cur: str, table: Dict[str, Sequence[Tuple[str, str, str]]],
               mother: Optional[str] = None) -> List[Any]:
    """逐句修缮母本时这一句改掉的错（按句子 id）：那几个字还在就直接改（已经改过的不动）。
    mother：母本里这个 id 的句子；给了就先看是不是同一句（不像就不改）。"""
    from voicetwin.data.lexicon_fix import Fix

    out: List[Any] = []
    entries = table.get(rid, ())
    if not entries or (mother is not None and _similarity(cur, mother) < ROW_MIN_SIMILAR):
        return out
    for wrong, right, why in entries:
        k = cur.find(wrong)
        while k >= 0:
            out.append(Fix(k, k + len(wrong), right, "same_row", True, 0.9,
                           f"「{_q(wrong)}」应该是「{_q(right)}」（逐句修缮母本时改的：{why or '识别错'}）"))
            k = cur.find(wrong, k + len(wrong))
    return out


SAME_ID_DIRECT = 0.8  # 和老师上传的 transcripts.csv 里同一个 id 的句子这么像：按它直接改
SAME_ID_MIN = 0.5  # 不到这么像：不是同一句（id 碰巧一样），不用它


def _same_id_fixes(cur: str, mother: str, edited: bool) -> List[Any]:
    """老师上传的 transcripts.csv 里有同一句（同一个 id）：和它不一样的地方按它改（老师改过的样子）。

    edited：这一句老师已经自己改过（保存过或者有没保存的修改）→ 完全不用（老师后来的修改为准，不建议改回去）。
    很像（≥ 80%）的直接改；有点像的只给建议；不像的不是同一句，不用。"""
    from voicetwin.data.lexicon_fix import Fix

    if edited:
        return []
    a, b = tokens(cur), tokens(mother)
    if not a or not b:
        return []
    sm = difflib.SequenceMatcher(None, [x.key for x in a], [x.key for x in b], autojunk=False)
    ratio = sm.ratio()
    if ratio < SAME_ID_MIN:
        return []
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if i2 > i1:
            s, e = a[i1].start, a[i2 - 1].end
        elif i1 == 0:
            s = e = a[0].start
        elif i1 >= len(a):
            s = e = a[-1].end  # 补在最后一个字后面（句号前面）
        else:  # 补在中间：母本里补的字前面有标点，就补在这一句的标点后面，否则紧跟前一个字
            gap = mother[b[j1 - 1].end:b[j1].start] if 0 < j1 < len(b) else ""
            s = e = a[i1].start if gap.strip() else a[i1 - 1].end
        rep = mother[b[j1].start:b[j2 - 1].end] if j2 > j1 else ""
        if not rep and e <= s:
            continue
        rep = pc._pad(cur, s, e, rep)
        direct = ratio >= SAME_ID_DIRECT  # 只有点像的：可能是切的位置不一样（录音里没有这几个字），没把握
        out.append(Fix(s, e, rep, "same_row", direct, 0.85 if direct else 0.6,
                       f"母本里这一句是「{_q(rep.strip() or '（没有）')}」（现在是「{_q(cur[s:e] or '（没有）')}」）"))
    return out


def _row_texts(project: Any) -> Set[str]:
    """校对表里每一句现在的（含没保存的修改）、保存的、最初识别的文字。"""
    from voicetwin.data import review as _review

    draft = _review.load_draft(project)
    out: Set[str] = set()
    for r in project.load_manifest():
        for x in (_review.current_values(r, draft.get(r.get("id")))["text"], r.get("text"), _review.original_text(r)):
            if x:
                out.add(_norm_line(str(x)))
    return out


def _text_edited(rec: Dict[str, Any]) -> bool:
    """这一句的文字老师已经改过、保存了（和最初识别的不一样）。"""
    orig = rec.get("orig_text")
    return bool(rec.get("text_edited")) or (orig is not None and str(orig) != str(rec.get("text") or ""))


def _clean_uploaded(lines: List[Tuple[str, str]], row_table: Dict[str, Sequence[Tuple[str, str, str]]],
                    builtin_by_id: Dict[str, str], cleaner: Any = None) -> List[Tuple[str, str]]:
    """老师上传的母本：先把里面的识别错改掉（老师上传的可能是修缮以前的 transcripts.csv 或者 txt，里面还有「借词」）——
    同一个 id 的句子按逐句修缮记录改，所有的句子按对照表改；改好以后和程序自带的一模一样的就不重复用了。
    不改的话，母本里旧的错写法会把已经改好的句子又「对齐」改回去（检查时发现的）。"""
    out: List[Tuple[str, str]] = []
    for rid, text in lines:
        if rid and rid in row_table:
            if builtin_by_id.get(rid) is None or _similarity(text, builtin_by_id[rid]) >= ROW_MIN_SIMILAR:
                for wrong, right, _why in row_table[rid]:
                    text = text.replace(wrong, right)
                text = clean_transcript(text)
        if cleaner is not None:
            fixes = cleaner.list_fixes(text)
            if fixes:
                text = _apply(text, [(f.start, f.end, f.rep) for f in fixes])
        if rid and builtin_by_id.get(rid) == text:
            continue
        out.append((rid, text))
    return out


def _changed_chars(rec: Dict[str, Any], cur: str) -> Tuple[Set[int], Set[int]]:
    """现在的文字里和最初识别的不一样的字（老师改过的、上次一键校正改好的）的位置；删掉字的地方另外记一个「点」。"""
    from voicetwin.data import review as _review

    orig = _review.original_text(rec)
    chars: Set[int] = set()
    points: Set[int] = set()
    if orig == cur:
        return chars, points
    if not orig:  # 最初没有识别出文字，整句都是老师自己打的：一个字都不动
        return set(range(len(cur))), points
    for tag, i1, i2, j1, j2 in _review._opcodes(orig, cur):
        if tag == "equal":
            continue
        if j2 > j1:
            chars.update(range(j1, j2))
        else:
            points.add(j1)
    return chars, points


def _touches_changed(s: int, e: int, changed: Tuple[Set[int], Set[int]]) -> bool:
    """[s, e) 碰到改过的字：改过的字在里面；删掉字的地方在中间（挨着删掉的地方不算）；插入正好插在删掉的地方。"""
    chars, points = changed
    if s == e:
        return s in points or (s - 1 in chars and s in chars)
    return any(k in chars for k in range(s, e)) or any(s < p < e for p in points)


def _protect(fixes: Sequence[Any], cur: str, changed: Tuple[Set[int], Set[int]], lex: Any) -> List[Any]:
    """所有改法再把一道关：
    - 碰到已经改过的字（老师自己改的、上次改好的）不动——老师的修改为准，母本里旧的写法也不能把它改回去；
    - 和母本对齐找出来的：改完以后标准库马上又会说有错的（改成了「借词」这种），不改。"""
    out = []
    for f in fixes:
        if _touches_changed(f.start, f.end, changed):
            continue
        if f.kind in ("align", "mother_upload"):  # 老师上传的母本（没修缮过）里可能有错字：标准库马上又会说错的不改
            if lex is not None:
                new = _apply(cur, [(f.start, f.end, f.rep)])
                e2 = f.start + len(f.rep)
                if any(g.start < max(e2, f.start + 1) and f.start < max(g.end, g.start + 1) for g in lex.find(new)):
                    continue
        out.append(f)
    return out


def _applied_in(base: str, cur: str, s: int, e: int, rep: str) -> bool:
    """查错字时文字（base）的 [s, e) 换成 rep 这一处，现在的文字里是不是已经改成这样了。"""
    from voicetwin.data import review as _review

    blocks = _review._equal_blocks(base, cur)
    js, je = _review.map_range(blocks, s, s), _review.map_range(blocks, e, e)
    return js is not None and je is not None and js[0] <= je[0] and cur[js[0]:je[0]] == rep


def _same_result(rec: Dict[str, Any], old: Dict[str, Any], new: Dict[str, Any], cur: str) -> bool:
    """这次查出来的（new，按现在的文字算）和原来的标记（old）是不是一回事：现在的文字正好是原来记下的某个整句
    （直接改好以后 / 有把握的改好以后 / 都改好以后），建议改成的整句一样、有把握的整句一样、标红的地方一样。
    用整句比，不一处一处对位置（同样的字挨着时会配错）。"""
    from voicetwin.data import review as _review

    st = _review.known_states(dict(rec, suspect=old))
    if not st or cur == st["base"] or cur not in (st["alt"], st.get("direct"), st.get("sure")):
        return False
    new_alt = str(new.get("alt") or "") or cur
    new_sure = (str(new.get("sure_alt") or "") or new_alt) if "sure_alt" in new else new_alt
    if new_alt != st["alt"] or new_sure != st.get("sure", st["alt"]):
        return False
    a = _review.analyze(dict(rec, suspect=new), cur)["red"]
    b = _review.analyze(dict(rec, suspect=old), cur)["red"]
    return a == b


def _drop_rejected(rec: Dict[str, Any], sus: Dict[str, Any], rejected: Any, cur: Optional[str] = None) -> Dict[str, Any]:
    """留着的旧标记里，老师撤销过的建议（点了红色按钮、自己改回去、撤销这一行的修改）去掉：不再显示成「采用」，
    那几个字也不再标红；别的（还能撤销的、还没采用的）照旧。同样的改法有两处、只撤销了一处时，还改着的那一处留着。"""
    from voicetwin.data import review as _review

    if not rejected or not isinstance(sus, dict):
        return sus
    base = _review.suspect_base(dict(rec, suspect=sus))
    edits = _review.suggestion_edits(base, str(sus.get("alt") or ""))
    bad = [ed for ed in edits if _review.is_rejected(rejected, base, *ed)
           and not (cur is not None and _applied_in(base, cur, *ed))]
    if not bad:
        return sus
    keep = [ed for ed in edits if ed not in bad]
    out = dict(sus, alt=_review.apply_edits(base, keep) if keep else "")
    out.pop("direct_alt", None)
    if "sure_alt" in sus:
        sure = [ed for ed in _review.suggestion_edits(base, str(sus.get("sure_alt") or base))
                if not _review.is_rejected(rejected, base, *ed)]
        out["sure_alt"] = _review.apply_edits(base, sure) if sure else base
    out["spans"] = [sp for sp in (sus.get("spans") or [])
                    if not any(int(sp[0]) < max(e, s + 1) and s < int(sp[1]) for s, e, _r in bad)]
    pairs = [(str(a).replace(" ", ""), str(b).replace(" ", "")) for a, b in rejected]  # 说明里提到撤销过的改法的那几条也去掉
    out["reasons"] = [x for x in (sus.get("reasons") or [])
                      if not any(a and b and a in str(x).replace(" ", "") and b in str(x).replace(" ", "") for a, b in pairs)]
    return out


def _rebase(rec: Dict[str, Any], sus: Dict[str, Any], cur: str, old_undo: Sequence[Tuple[int, int, str]]) -> Dict[str, Any]:
    """这一行以前采用过建议（还能撤销），这次又有新的：新的结果改成按「把以前采用的撤销以后」的文字记，
    这样以前采用的和这次改的都能用这一行的红色按钮撤销（老师自己改的别处两边一样，不会被撤销）。
    换算不过去、或者换算以后显示的不一样，就不换（只能撤销这次的）。"""
    from voicetwin.data import review as _review

    out, left = cur, len(cur) + 1
    for s, e, rep in sorted(old_undo, key=lambda x: (x[0], x[1]), reverse=True):
        if not (0 <= s <= e <= len(cur)) or e > left:
            return sus
        out, left = out[:s] + rep + out[e:], s
    out = clean_transcript(out)
    if not out or out == cur:
        return sus
    inv = [(j1, j2, i1, i2) for i1, i2, j1, j2 in _review._equal_blocks(out, cur)]
    spans = []
    for sp in sus.get("spans") or []:
        m = _review.map_range(inv, int(sp[0]), int(sp[1]))
        if m is None:
            return sus
        spans.append([m[0], m[1]])
    cand = dict(sus, text=out, spans=spans)
    if not cand.get("alt"):  # 这次没有新的建议：「建议的样子」就是现在的文字（以前采用的才能撤销）
        cand["alt"] = cur
    a = _review.analyze(dict(rec, suspect=sus), cur)
    b = _review.analyze(dict(rec, suspect=cand), cur)
    if (a["red"], a["edits"], a["sure"]) != (b["red"], b["edits"], b["sure"]):
        return sus
    return cand


def _global_fp(all_lines: Sequence[Tuple[str, str]], row_table: Dict[str, Any], lex: Any,
               use_builtin: bool, use_row_fixes: bool, merge_only: bool = False) -> str:
    """这次文字校正用的标准库（母本、按句子的修缮记录、对照表、术语、程序版本、母本优先的做法）的指纹。
    merge_only（自动查错字以后只合并、不改字）也算进去：一键校正再点时要重新算，按母本直接改。"""
    import hashlib
    import json

    from voicetwin import __version__
    from voicetwin.data import mother_first as _mf
    from voicetwin.data.lexicon_fix import has_jieba

    data = [__version__, MOTHER_FIRST_VERSION, _mf.MATCH_MIN, merge_only, use_builtin, use_row_fixes, has_pinyin(),
            has_jieba(), [list(x) for x in all_lines],
            sorted((k, [list(v) for v in vs]) for k, vs in row_table.items()), sorted(lex.corrections.items()),
            sorted(lex.vocab)]
    return hashlib.sha1(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _row_fp(gfp: str, auto: Optional[Dict[str, Any]], rejected: Any, orig: str) -> str:
    """一行的指纹：标准库 + 这一行自动查错字的结果 + 老师撤销过的改法 + 最初识别的文字。"""
    import hashlib
    import json

    data = [gfp, auto or None, sorted([str(a), str(b)] for a, b in (rejected or [])), orig]
    return hashlib.sha1(json.dumps(data, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _program_states(rec: Dict[str, Any], sus: Dict[str, Any]) -> Set[str]:
    """上次点完以后程序留下的样子：直接改好的（没有直接改的就是查错字时的样子）、有把握的也采用了、都采用了。"""
    from voicetwin.data import review as _review

    st = _review.known_states(dict(rec, suspect=sus))
    if not st:
        return set()
    return {x for x in (st.get("direct") or st["base"], st.get("sure"), st["alt"]) if x}


#: 母本优先的做法改了就加一（指纹里有它：老师再点一键校正 / 自动查错字时按新的做法重新算）
MOTHER_FIRST_VERSION = 1
MOTHER_WEIGHT = 0.95  # 按母本的改法：不是直接改的时候（自动查错字以后合并）也算有把握，一键校正会采用


def _mother_first(cur: str, rid: str, ref: Optional[Reference], selves: Sequence[str], own_line: bool = True
                  ) -> Tuple[List[Any], List[Tuple[int, int]], str, bool]:
    """母本优先：这一句按内容在母本里找对应的那一段（mother_first.find_segments），和母本不一样的地方都按母本改。
    返回 (改法, 母本说了算的部分 [(开始, 结束)]（只算程序自带的、修缮过的母本）, 母本里的原句, 整句是不是都由它说了算)。

    不拿来比的：老师上传的母本里和这一句现在的 / 保存的 / 最初识别的文字一模一样的行（就是它自己，证明不了什么）。
    同一个 id 的那一句（程序自带的、上传的 transcripts.csv 里的）照样用，id 只当提示（文字也对得上才优先用它）；
    老师自己改过的字一律不动（_protect）。
    对上的是老师上传的母本（没修缮过，可能有打字的同音错字「主雨」）时：读音一样的单个字只给没把握的建议，
    改完以后标准库马上又会说错的不改（_protect）。
    own_line=False（实测里的「考试」：不用逐句修缮的结果）：同一个 id 的那一句也不拿来比、不当提示。"""
    from voicetwin.data import mother_first as mf
    from voicetwin.data.lexicon_fix import Fix

    if ref is None or not len(ref):
        return [], [], "", False
    skips: List[Tuple[int, int]] = []
    for t in set(_norm_line(x) for x in selves if x):
        skips += ref.text_ranges.get(t, [])
    if not own_line:
        skips += list(ref.id_ranges.get(rid, []))
    toks, segs = mf.find_segments(cur, ref, hint_id=rid if own_line else "", skips=skips)
    out: List[Any] = []
    covered: List[Tuple[int, int]] = []
    snippet = ""
    used = 0
    for seg in segs:
        if seg.ambiguous:  # 母本里好几处一样像、写法又不一样：分不出是哪一处，这一段不按母本改
            continue
        upload = seg.m2 > ref.unvetted_from
        if not snippet:
            snippet = ref.snippet(seg.m1, seg.m2, pad=0, limit=120)
        who = "按你上传的母本" if upload else "按母本"
        holes: List[Tuple[int, int]] = []
        for s, e, rep in mf.segment_edits(cur, toks, ref, seg):
            item = _edit_item(cur, s, e, rep)
            if upload and not _sound_alike(cur[s:e], rep):
                # 老师上传的文字没修缮过，可能是讲课以前写的讲稿：讲的时候多说的「呢、那」、换的说法、页码不一样，
                # 读音不像识别错（实测：按讲稿改会把 7 / 45 句实际说的话改掉，见 research/文字校正/母本优先/讲稿实测.py）
                # → 这种地方不按上传的文字改，交给标准库和另一个识别引擎
                holes.append((s, e))
                continue
            if upload and _one_homophone(cur, s, e, rep):
                # 只对上了老师上传的母本（没修缮过）、读音一样的一个字：说不准是识别错了还是上传的文字打错了
                out.append(Fix(s, e, rep, "mother_upload", False, UNVETTED_WEIGHT,
                               f"没把握（请听录音）：{who}：{item}"))
                continue
            out.append(Fix(s, e, rep, "mother_upload" if upload else "mother", True, MOTHER_WEIGHT, f"{who}：{item}"))
        if not upload:
            # 只有程序自带的、老师修缮过的母本才「说了算」：对上的部分别的办法都不用、和它矛盾的自动建议不要。
            # 老师上传的（没修缮过、可能是讲稿）只当多一种改法：标准库（对照表、术语）照样查整句，自动查错字的结果照样留着
            # （上传讲稿时的实测：上传的也「说了算」的话，对照表能改好的「猪语 → 主语」这种反而没改，31 句里少改对 3 句）
            covered += _minus((toks[seg.r1].start, toks[seg.r2 - 1].end), holes)
            used += seg.length
    return out, covered, snippet, bool(toks) and used >= len(toks)


def _sound_alike(old: str, new: str) -> bool:
    """一处改动像不像识别错（读音一样 / 很像）：汉字读音（模糊音）一样、汉字读音像英文（艾子 / as）、英文拼法很像
    （clouse / clause）、中文数字读音一样。多出来、少了的字，读音不一样的说法（高考 / 考试、三十六 / 三十五）都不算。"""
    a, b = tokens(old), tokens(new)
    if not a or not b:
        return False
    ka, kb = {t.kind for t in a}, {t.kind for t in b}
    if ka == {"han"} and kb == {"lat"}:
        return sounds_like_english([t.tone for t in a], [t.key for t in b])
    if ka == {"lat"} and kb == {"han"}:
        return sounds_like_english([t.tone for t in b], [t.key for t in a])
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x.kind != y.kind:
            return False
        if x.kind == "han" and x.fz != y.fz:
            return False
        if x.kind == "lat" and difflib.SequenceMatcher(None, x.key, y.key, autojunk=False).ratio() < 0.75 \
                and x.snd != y.snd:
            return False
        if x.kind == "num":
            pa, pb = _num_pinyin(old[x.start:x.end]), _num_pinyin(new[y.start:y.end])
            if not pa or not pb or [fuzzy(z) for z in pa] != [fuzzy(z) for z in pb]:
                return False
        if x.kind == "other" and x.key != y.key:
            return False
    return True


def _minus(rng: Tuple[int, int], holes: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """母本对上的范围去掉不按母本改的地方（剩下的才算母本管的）。"""
    parts = [rng]
    for s, e in holes:
        nxt = []
        for a, b in parts:
            if e < a or b < s or (s == e and not (a < s < b)):
                nxt.append((a, b))
                continue
            if a < s:
                nxt.append((a, s))
            if max(e, s) < b:
                nxt.append((max(e, s), b))
        parts = nxt
    return [(a, b) for a, b in parts if b > a]


def _edit_item(cur: str, s: int, e: int, rep: str) -> str:
    """一处按母本的改法怎么说（和表格里一样带上所在的词：「定于从句 → 定语从句」、「补上「中」」）。"""
    from voicetwin.data import review as _review

    items = _review._change_items(cur, cur[:s] + rep + cur[e:])
    if items:
        return items[0]
    return f"「{_q(cur[s:e] or '（没有）')}」→「{_q(rep or '（没有）')}」"


def _one_homophone(cur: str, s: int, e: int, rep: str) -> bool:
    """一个汉字换成读音一样（或很像）的另一个汉字。"""
    a, b = tokens(cur[s:e]), tokens(rep)
    return len(a) == 1 and len(b) == 1 and a[0].kind == b[0].kind == "han" and a[0].fz == b[0].fz


def _mother_notes(cur: str, mfixes: Sequence[Any], changed: Tuple[Set[int], Set[int]], rejected: Any) -> List[str]:
    """按母本要改、但不改的地方的说明：老师自己改过的字（老师的修改为准）、老师撤销过的改法（老师的决定为准）。"""
    from voicetwin.data import review as _review

    out: List[str] = []
    for f in mfixes:
        # 带上前后各两个字，看得出是哪里（只写「绍」看不懂）：「和介绍词一」/「和介词一」
        left, right = cur[max(0, f.start - 2):f.start], cur[f.end:f.end + 2]
        now, want = left + cur[f.start:f.end] + right, left + str(f.rep) + right
        if _touches_changed(f.start, f.end, changed):
            # 和最初识别的不一样的字：老师自己打的，或者老师以前采用、保存过的修改（分不清是哪一种，都算老师定的）
            out.append(f"母本里这里是「{_q(want)}」，现在是「{_q(now)}」（你改过这里，或者以前采用过别的修改）："
                       "程序没有动（你的修改为准；如果是错的，请双击「文字」改成母本的写法）")
        elif _review.is_rejected(rejected, cur, f.start, f.end, f.rep):
            out.append(f"母本里这里是「{_q(want)}」，这个改法你撤销过：程序没有再改（你的决定为准）")
    return out


def check_with_transcript(project: Any, progress: Optional[ProgressFn] = None,
                          lines: Optional[Sequence[Tuple[str, str]]] = None, use_builtin: bool = True,
                          names: Optional[Sequence[str]] = None, use_row_fixes: bool = True,
                          only: Optional[Iterable[str]] = None, merge_only: bool = False) -> Dict[str, Any]:
    """📝 文字校正：以标准库（老师的母本 + 语法术语 + 对照表）为标准检查这个声音的校对表。

    母本优先（老师 10-04 的要求）：每一句先按内容在母本里找「差不多或者原模原样」的那一句（_mother_first，
    不按片段 id：重新准备素材、换了文件夹以后 id 全变了；切的位置不一样也找得到），找到了母本就是标准答案，
    和母本不一样的地方都按母本改；母本里没有的部分才用逐句修缮记录、对照表、术语、和别的句子对齐、另一个识别引擎。
    直接改的存成没保存的修改（草稿），建议和原因写进「可能有错」列（record["suspect"]）。
    lines：老师上传的母本（不给就读声音文件夹里存的）；use_builtin：用不用程序自带的母本（测试时可以关掉）。
    use_row_fixes=False（实测的「考试」）：不用逐句修缮的结果——按 id 的修缮记录、母本里同一个 id 的那一句都不用。
    only：只检查这些句子（id），别的句子一点都不动（一键全部文字校正每批素材只能用一次：以后只改新加的句子）。
    merge_only=True：🔍 自动查找（加了新素材时准备素材也会自动查）以后，把新查出来的结果和一键校正的结果合在一起
    （以前一键校正的结果会被冲掉：建议没了、母本证明没错的标红又回来了），一个字都不改（标准库能确定的也只当建议），
    也不算用了一次一键校正。"""
    from voicetwin.data import review as _review
    from voicetwin.data.lexicon_fix import Lexicon, builtin_info, has_jieba

    t0 = time.time()
    by_file = lines is None  # 读声音文件夹里存的：按文件记下哪些用上了
    if by_file:
        per_file = [(name, [(rid, x) for rid, x, _n in fl]) for name, fl in load_transcript_files(project)]
        names = [name for name, _fl in per_file]
    else:
        per_file = [("", list(lines or []))]
    builtin = list(builtin_mother()) if use_builtin else []
    row_table = dict(builtin_fixes()) if (use_builtin and use_row_fixes) else {}
    builtin_by_id = {rid: x for rid, x in builtin if rid}
    # 老师上传的母本里和校对表某一句（现在的 / 保存的 / 最初识别的样子）一模一样的行：就是那一句自己（比如下载的
    # 「改好的文字」），什么也证明不了，不用（不然没检查过的句子会「自己证明自己没错」，自动查错字的标红被去掉）
    selves = _row_texts(project)
    cleaner = Lexicon.build([]) if any(fl for _n, fl in per_file) else None
    lines, file_of = [], []
    for k, (_name, fl) in enumerate(per_file):
        fl = _filter_upload(fl, selves, row_table, builtin_by_id, cleaner)
        lines += fl
        file_of += [k] * len(fl)
    all_lines = builtin + lines
    _report(progress, 0.02, "正在读母本和语法术语……")
    ref = Reference(all_lines, own_from=len(builtin), vetted_lines=len(builtin)) if all_lines else None
    records = project.load_manifest()
    # 不再从校对表里「学」老师改过的错：保存的修改里也有程序自己改的（采用的建议），学进去会越改越错（检查时发现的）
    lex = Lexicon.build([x for _, x in all_lines])
    # 把关用的标准库只用程序自带的母本：老师上传的文字里的错字（「过去试」）会被当成老师的说法，
    # 「改完以后标准库马上又会说有错的不改」这一关就失效了，对的「过去式」被改成「过去试」（检查时发现的）
    guard = Lexicon.build([x for _, x in builtin]) if (lines and builtin) else lex
    by_id = {rid: x for rid, x in lines if rid}  # 老师上传的 transcripts.csv 里的句子（按 id）
    gfp = _global_fp(all_lines, row_table, lex, use_builtin, use_row_fixes, merge_only)
    _report(progress, 0.15, f"标准库：母本 {len(ref) if ref else 0} 个字 / 词，语法术语和常说的词 {len(lex.vocab)} 个，"
                            f"对照表 {len(lex.corrections)} 条，开始一句一句检查……")
    draft = _review.load_draft(project)
    rejected = _review.load_rejected(project)
    todo = []
    dismissed = 0
    dismissed_ids: Set[str] = set()
    only_ids = None if only is None else {str(x) for x in only}
    for r in records:
        if r.get("deleted") or (only_ids is not None and str(r.get("id")) not in only_ids):
            continue
        entry = draft.get(r["id"])
        vals = _review.current_values(r, entry)
        cur = str(vals["text"] or "")
        if not cur.strip() or not vals["keep"]:
            continue
        if r.get("suspect_ok") and r.get("suspect_ok") == cur:
            dismissed += 1
            dismissed_ids.add(r["id"])
            continue
        todo.append((r, cur, _review.is_dirty(r, entry) or _text_edited(r)))
    results: Dict[str, Tuple[str, List[Any], ClipResult, Tuple[Set[int], Set[int]], List[Tuple[int, int]]]] = {}
    notes: Dict[str, List[str]] = {}
    n = len(todo)
    for i, (r, cur, edited) in enumerate(todo, 1):
        _check_cancel()
        rid = r["id"]
        selves = (cur, str(r.get("text") or ""), _review.original_text(r))
        changed = _changed_chars(r, cur)
        # 母本优先（老师 10-04 的要求）：先按内容在母本里找这一句（不按 id：id 只当提示）；找到的部分母本就是标准答案
        mfixes, covered, snippet, full = _mother_first(cur, rid, ref, selves, own_line=use_row_fixes)
        if full:  # 整句都在母本里：母本说了算，别的办法（对照表、术语、和别的句子对齐）都不用
            res = ClipResult([], set(), True, snippet)
            fixes = list(mfixes)
        else:  # 母本里没有的部分：再用标准库（对照表、术语）、和母本里别的句子对齐
            res = (check_text(cur, ref, exclude_id=rid, exclude_texts=selves) if ref is not None
                   else ClipResult([], set(), False, ""))
            rest = _row_fixes(rid, cur, row_table, builtin_by_id.get(rid)) + lex.find(cur) + props_to_fixes(cur, res, lex)
            if rid in by_id:
                rest += _same_id_fixes(cur, by_id[rid], edited)
            fixes = list(mfixes) + [f for f in rest if not _in_covered(f.start, f.end, covered)]
            if snippet:
                res = replace(res, ref_text=snippet)
        # 按母本要改、但老师自己改过（或者撤销过）的地方：不动，记一句说明（点这一行时看得到）
        notes[rid] = _mother_notes(cur, mfixes, changed, rejected.get(rid))
        fixes = _protect(fixes, cur, changed, guard)
        # 老师撤销过的改法（点过红色按钮、自己改回去、撤销这一行的修改）：不再改回来，也不再建议
        fixes = [f for f in fixes if not _review.is_rejected(rejected.get(rid), cur, f.start, f.end, f.rep)]
        if merge_only:  # 只合并结果：一个字都不改（能确定的也只当建议，老师自己决定）
            fixes = [replace(f, direct=False) if f.direct else f for f in fixes]
        results[rid] = (cur, fixes, res, changed, covered)
        if i % 20 == 0 or i == n:
            _report(progress, 0.15 + 0.8 * i / max(n, 1), f"已检查 {i} / {n} 条")
    stats: Counter = Counter()
    examples: List[str] = []
    with _review._LOCK:
        records = project.load_manifest()
        draft = _review.load_draft(project)
        rejected_now = _review.load_rejected(project)  # 检查期间老师可能又撤销了：按现在的算
        changed_draft = False
        handled: List[str] = [str(x) for x in dismissed_ids]  # 这次真的处理过的句子（「这句没错」的也算）
        for r in records:
            if r.get("id") in dismissed_ids:  # 「这句没错」：以前留下的标红、建议都去掉（不然一键会采用旧建议）
                vals = _review.current_values(r, draft.get(r["id"]))
                if r.get("suspect_ok") == vals["text"]:
                    r.pop("suspect", None)
                    r.pop("suspect_auto", None)
                    r.pop("mother_note", None)
                continue
            item = results.get(r.get("id"))
            if item is None:
                continue
            cur, fixes, res, changed, covered = item
            entry = draft.get(r["id"])
            vals = _review.current_values(r, entry)
            if str(vals["text"] or "") != cur:  # 检查期间改过（这一句这次没处理，下次还能用一键校正）
                continue
            handled.append(str(r["id"]))
            if notes.get(r["id"]):
                r["mother_note"] = {"text": cur, "notes": notes[r["id"]]}
            else:
                r.pop("mother_note", None)
            old = r.get("suspect") if isinstance(r.get("suspect"), dict) else None
            auto = auto_suspect(r)
            if auto:  # 自动查错字的结果是按当时保存的文字算的：记下那段文字，保存修改以后位置也换算得对
                auto = dict(auto, text=str(auto.get("text") or r.get("text") or ""))
            fp = _row_fp(gfp, auto, rejected_now.get(r["id"]), _review.original_text(r))
            if old and old.get("src") == "transcript" and old.get("fp") == fp and cur in _program_states(r, old):
                # 上次点完以后什么都没变（母本、自动查错字的结果、撤销记录都一样，文字还是程序改成的样子）：
                # 结果原样留着。不然这次是从改好的文字算的，挨着改好的字的建议会算得不一样（随机操作发现：连点两次不一样）
                stats["same"] += 1
                stats["flagged"] += 1
                if "sure_alt" in old:
                    stats["unsure"] += 1
                continue
            old_undo = _review.analyze(r, cur)["undo"] if old else []
            sus, what, direct = merge_with_auto(cur, fixes, res.confirmed_chars, auto, r, res.ref_text, lex,
                                                rejected=rejected.get(r["id"]), changed=changed, covered=covered)
            if sus is None and old_undo:
                # 这一行以前采用过的建议（按钮是红的，可以撤销）：没有新的问题也留着，不然撤销不了；
                # 里面老师已经撤销（改回去）的建议去掉，不再显示成「采用」
                sus, what = _drop_rejected(r, old, rejected.get(r["id"]), cur), "kept_undo"
            elif sus is not None and old_undo and sus.get("src") == "transcript":
                reb = _rebase(r, sus, cur, old_undo)
                if reb is sus and _same_result(r, old, sus, cur):
                    # 换算不过去，但这次查出来的和原来的标记是一回事（建议改成的整句一样、标红一样）：留着原来的
                    # （再点一次一键校正、老师什么都没做，「已采用」的红色按钮不能没了）
                    reb = _drop_rejected(r, old, rejected.get(r["id"]), cur)
                sus = reb
            stats[what] += 1
            stats["aligned"] += int(res.aligned or bool(covered))
            stats["mother_rows"] += int(bool(covered))  # 母本里找到了差不多的句子（按内容）
            if sus is not None and sus.get("src") == "transcript" and auto:
                r["suspect_auto"] = auto
            else:
                r.pop("suspect_auto", None)
            if sus is None:
                r.pop("suspect", None)
            else:
                if sus.get("src") == "transcript":
                    sus = dict(sus, fp=fp)  # 这次用的东西记下来（下次什么都没变就原样留着）
                r["suspect"] = sus
                stats["flagged"] += 1
                if "sure_alt" in sus and sus.get("src") == "transcript":
                    stats["unsure"] += 1
            if direct and not merge_only:
                new = _apply(cur, direct)
                if new.strip() and new != cur:
                    nv = {"text": new, "keep": vals["keep"], "lang": _review.lang_after_edit(cur, vals["lang"], new)}
                    if nv == _review.saved_values(r):
                        draft.pop(r["id"], None)
                    else:
                        draft[r["id"]] = nv
                    changed_draft = True
                    stats["fixes"] += len(direct)
                    stats["mother_fixes"] += sum(1 for f in fixes if f.direct and f.kind.startswith("mother"))
                    # 例子按整句比（和表格里的说法一样）：以前按改动的那几个字说，英文被切开（「Caesa → 's scisso」）、
                    # 汉字没有前后文（「到 → 道」）；现在是「Tony Caesars → Tony's scissors」「报到 → 报道」
                    for it in _review._change_items(cur, new):
                        if len(examples) < 8:
                            examples.append(it)
        project.save_manifest(records)
        if changed_draft:
            _review.save_draft(project, draft)
    # 上传的文件哪些真的用上了（以前不管用没用上都说「另外用了你上传的」）：一句都没用上的（和校对表一模一样）、
    # 太长被截掉的（只用了前面的），页面上分开说
    files_used, files_cut, files_same = list(names or []), [], []
    if by_file:
        files_used = []
        last = ref.last_line if ref is not None else -1
        truncated = bool(ref is not None and ref.truncated)
        for k, (name, fl) in enumerate(per_file):
            idx = [len(builtin) + i for i, f in enumerate(file_of) if f == k]
            if not idx:
                if fl:
                    files_same.append(name)
                continue
            if not truncated or min(idx) <= last:
                files_used.append(name)
            if truncated and max(idx) > last:
                files_cut.append(name)
    secs = round(time.time() - t0, 1)
    info = builtin_info()
    out = {"checked": n, "flagged": stats["flagged"], "fixed_rows": stats["fixed"], "fixes": stats["fixes"],
           "found": stats["found"], "aligned": stats["aligned"], "cleared": stats["cleared"],
           "kept_auto": stats["kept_auto"] + stats["unchanged_auto"], "dismissed": dismissed,
           "chars": len(ref) if ref else 0, "files": files_used, "files_cut": files_cut, "files_same": files_same,
           "room": upload_room(), "builtin_lines": len(builtin),
           "terms": len(lex.vocab), "builtin_terms": info["terms"], "corrections": len(lex.corrections),
           "unsure": stats["unsure"], "kept_undo": stats["kept_undo"], "pinyin": has_pinyin(), "jieba": has_jieba(),
           "mother_rows": stats["mother_rows"], "mother_fixes": stats["mother_fixes"],
           "truncated": bool(ref.truncated) if ref else False, "examples": examples, "seconds": secs,
           "handled": handled}
    log.info(f"文字校正完成：检查了 {n} 条，母本里找到了差不多的句子 {out['mother_rows']} 条（母本优先）；"
             f"直接改好 {out['fixes']} 处（{out['fixed_rows']} 条，存成没保存的修改，其中按母本 {out['mother_fixes']} 处），"
             f"另外 {out['found']} 条标红给了建议；{out['cleared']} 条原来的标红被母本证明没错、已去掉，"
             f"保留自动检查标红 {out['kept_auto']} 条；用时 {secs} 秒。")
    _report(progress, 1.0, f"检查完了：直接改好 {out['fixes']} 处，另外 {out['found']} 条给了建议")
    return out


__all__ = [
    "TRANSCRIPT_DIR", "read_text_file", "save_transcripts", "load_transcripts", "load_transcript_files",
    "transcript_info", "upload_room", "Reference",
    "check_text", "check_with_transcript", "merge_with_auto", "auto_suspect", "tokens", "fuzzy", "en_code",
    "sounds_like_english", "has_pinyin", "parse_mother", "builtin_mother", "builtin_fixes", "props_to_fixes",
]
