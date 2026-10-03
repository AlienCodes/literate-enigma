"""校对表的数据逻辑（网页「① 准备素材」下面的校对表用）。

- **没保存的修改（草稿）**：老师在表格里改的文字 / 保留 / 语言，先存在 ``workspace/<声音>/review_draft.json``，
  点「保存修改」（或这一行的「💾 保存这一行」）才写进校对表（manifest + transcripts.csv）。
  草稿放在硬盘上：网页刷新、浏览器关掉、两次修改挤在一起提交，都不会丢。
- **蓝色 = 改过的字**：现在的文字和最初识别出来的文字（``orig_text``）比，不一样的地方。
- **红色 = 可能有错**：查错字时标出来的位置；那个地方被改过以后就不再标红（改过的地方变蓝）。
- **修改建议**：查错字时第二个识别引擎给的建议（``suspect.alt``），拆成一处一处的改动；
  点一下就把还没改的那几处改好（只改建议的地方，老师自己改过的地方不动）。
- **删除**：不是真的删文件，这一行在表格里变成灰色、不再用来训练；「⋯ 选项」里点「↩️ 撤销删除」就回来。

位置说明：``suspect`` 里的 spans / alt 是针对查错字那一刻的文字（``suspect["text"]``，没有这个键时 = 现在保存的文字）。
文字改过以后，用逐字对比把这些位置换算到新文字上。
"""

from __future__ import annotations

import difflib
import re
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from voicetwin.utils.textutil import clean_transcript, detect_lang

DRAFT_FILE = "review_draft.json"
DELETED_REASON = "老师删除"
_LOCK = threading.RLock()

Range = Tuple[int, int]
Edit = Tuple[int, int, str]


# ============================================================================ 草稿（没保存的修改）
def draft_path(project: Any) -> Path:
    return Path(project.root) / DRAFT_FILE


def load_draft(project: Any) -> Dict[str, Dict[str, Any]]:
    """{片段 id: {"text": ..., "keep": True/False, "lang": "zh"/"en"}}；文件坏了当作没有草稿。"""
    p = draft_path(project)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            out[str(k)] = {"text": str(v.get("text", "")), "keep": bool(v.get("keep", True)),
                           "lang": str(v.get("lang", ""))}
    return out


def save_draft(project: Any, draft: Dict[str, Dict[str, Any]]) -> None:
    p = draft_path(project)
    if not draft:
        try:
            p.unlink()
        except OSError:
            pass
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(draft, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def saved_values(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {"text": str(rec.get("text", "") or ""), "keep": bool(rec.get("keep", True)),
            "lang": str(rec.get("lang", "") or "")}


def current_values(rec: Dict[str, Any], entry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """表格里显示的值：有草稿用草稿，没有用保存过的。"""
    return dict(entry) if entry else saved_values(rec)


def is_dirty(rec: Dict[str, Any], entry: Optional[Dict[str, Any]]) -> bool:
    return bool(entry) and current_values(rec, entry) != saved_values(rec)


def has_saved_edit(rec: Dict[str, Any]) -> bool:
    """这一条老师改过、而且已经保存了（绿灯）：网页里保存过的修改（edited），或者改过文字（text_edited，
    也包括在 Excel 里改的）。"""
    return bool(rec.get("edited") or rec.get("text_edited"))


def _records(project: Any) -> Dict[str, Dict[str, Any]]:
    return {r["id"]: r for r in project.load_manifest()}


def set_draft(project: Any, clip_id: str, remember: bool = True, **changes: Any) -> Dict[str, Any]:
    """改一条（text / keep / lang 任选），只改草稿。和保存过的一样时草稿自动去掉。

    返回 {"dirty": 改完以后还有没保存的修改, "values": 现在的值}。"""
    with _LOCK:
        recs = _records(project)
        rec = recs.get(clip_id)
        if rec is None:
            raise KeyError(f"找不到这条片段（{clip_id}），请点「🔄 重新载入」")
        draft = load_draft(project)
        vals = current_values(rec, draft.get(clip_id))
        if "text" in changes and changes["text"] is not None:
            text = clean_transcript(str(changes["text"]))
            if not text:
                raise ValueError("文字不能是空的。不想要这一条，请用「选项」里的「🗑️ 删除这一行」")
            if text != vals["text"]:
                vals["text"] = text
                if "lang" not in changes:
                    vals["lang"] = detect_lang(text) or vals["lang"]
        if "keep" in changes and changes["keep"] is not None:
            vals["keep"] = bool(changes["keep"])
        if "lang" in changes and changes["lang"] in ("zh", "en"):
            vals["lang"] = changes["lang"]
        old_text = current_values(rec, draft.get(clip_id))["text"]
        if remember and vals["text"] != old_text:  # 老师自己打字把改过的地方改回去了：记下来，再点一键校正不再改回来
            _remember_rejects(project, clip_id, reverted_pieces(rec, old_text, vals["text"]))
        if vals == saved_values(rec):
            draft.pop(clip_id, None)
        else:
            draft[clip_id] = vals
        save_draft(project, draft)
        return {"dirty": clip_id in draft, "values": vals}


def discard_draft(project: Any, clip_id: Optional[str] = None) -> int:
    """撤销没保存的修改：一条（clip_id）或全部（None）。返回撤销了几条。"""
    with _LOCK:
        draft = load_draft(project)
        if clip_id is None:
            n = len(draft)
            draft = {}
        else:
            entry = draft.pop(clip_id, None)
            n = 1 if entry is not None else 0
            rec = _records(project).get(clip_id) if entry else None
            if rec is not None:  # 撤销这一行的修改：里面采用过的建议也算老师不要的，再点一键校正不再改回来
                old_text = current_values(rec, entry)["text"]
                _remember_rejects(project, clip_id, reverted_pieces(rec, old_text, saved_values(rec)["text"]))
        save_draft(project, draft)
        return n


def prune_draft(project: Any) -> int:
    """去掉已经不存在的片段、和保存过的一样的草稿（例如重新准备素材以后）。返回去掉了几条。"""
    with _LOCK:
        draft = load_draft(project)
        if not draft:
            return 0
        recs = _records(project)
        keep = {k: v for k, v in draft.items() if k in recs and is_dirty(recs[k], v)}
        removed = len(draft) - len(keep)
        if removed:
            save_draft(project, keep)
        return removed


def unsaved_count(project: Any) -> int:
    """还有几条没保存的修改（删除了的那几行不算：它们本来就不用来训练）。"""
    prune_draft(project)
    gone = {r.get("id") for r in project.load_manifest() if r.get("deleted")}
    return sum(1 for k in load_draft(project) if k not in gone)


# ============================================================================ 位置换算
def _opcodes(a: str, b: str) -> List[Tuple[str, int, int, int, int]]:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()


def _equal_blocks(a: str, b: str) -> List[Tuple[int, int, int, int]]:
    return [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in _opcodes(a, b) if tag == "equal"]


def map_range(blocks: Sequence[Tuple[int, int, int, int]], s: int, e: int) -> Optional[Range]:
    """旧文字里的 [s, e) 换算到新文字：整段都没被改过才换算得过去，碰到改过的地方返回 None。

    s == e（插入的位置）：落在没改过的地方（含两头）就算。"""
    for i1, i2, j1, j2 in blocks:
        if s == e:
            if i1 <= s <= i2:
                return (s - i1 + j1, s - i1 + j1)
        elif i1 <= s and e <= i2:
            return (s - i1 + j1, e - i1 + j1)
    return None


def touched(ops: Sequence[Tuple[str, int, int, int, int]], s: int, e: int, strict: bool = False) -> bool:
    """旧文字的 [s, e) 有没有被改到。挨着边的插入也算改到（查错字时"这里漏了字"标的是缺字位置两边的字）；
    s == e（建议在这里插入）时，这个位置上或者两边有改动都算。strict：插入的位置只有正好在改动中间、
    或者那里也插入了东西才算（换算「撤销」用）。"""
    for tag, i1, i2, _j1, _j2 in ops:
        if tag == "equal":
            continue
        if i1 == i2:
            if (s < i1 < e) if strict and s != e else (s <= i1 <= e):
                return True
        elif s == e:
            if (i1 < s < i2) if strict else (i1 <= s <= i2):
                return True
        elif i1 < e and s < i2:
            return True
    return False


def _merge(ranges: Iterable[Sequence[int]], n: int) -> List[Range]:
    out: List[List[int]] = []
    for s, e in sorted((max(0, int(a)), min(n, int(b))) for a, b in ranges):
        if e <= s:
            continue
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(a, b) for a, b in out]


# ============================================================================ 一行的分析：红 / 蓝 / 建议
WHOLE_SENTENCE_RATIO = 0.5  # 建议和原来的文字只有这么像（差不多整句都换了）：不知道哪个对，一键校正不自动采用


def whole_sentence_suggestion(sus: Dict[str, Any], base: str) -> bool:
    """这个建议差不多是把整句换掉（另一个识别引擎整句听得都不一样）。"""
    alt = str((sus or {}).get("alt") or "")
    if not alt or alt == base:
        return False
    if any("整句可能都不对" in str(r) for r in (sus.get("reasons") or [])):
        return True
    return difflib.SequenceMatcher(None, base, alt, autojunk=False).ratio() < WHOLE_SENTENCE_RATIO


def suspect_base(rec: Dict[str, Any]) -> str:
    sus = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else {}
    return str(sus.get("text") or rec.get("text", "") or "")


def original_text(rec: Dict[str, Any]) -> str:
    """最初识别出来的文字（老师第一次改之前）。"""
    return str(rec.get("orig_text") or rec.get("text", "") or "")


def _word_char(ch: str) -> bool:
    return ch.isascii() and ch.isalnum()


def suggestion_edits(base: str, alt: str) -> List[Edit]:
    """建议（alt）和查错字时的文字（base）逐字对比，拆成一处一处的改动 (start, end, 换成什么)，位置按 base 算。

    英文按整个单词改（VFIXED → V fixed，而不是 FIXED → fixed），老师看得懂、也不会只改半个词。"""
    if not alt or alt == base:
        return []
    spans: List[List[int]] = []
    for tag, i1, i2, j1, j2 in _opcodes(base, alt):
        if tag == "equal":
            continue
        while i1 > 0 and j1 > 0 and base[i1 - 1] == alt[j1 - 1] and _word_char(base[i1 - 1]) and (
                (i1 < len(base) and _word_char(base[i1])) or (j1 < len(alt) and _word_char(alt[j1]))):
            i1, j1 = i1 - 1, j1 - 1
        while i2 < len(base) and j2 < len(alt) and base[i2] == alt[j2] and _word_char(base[i2]) and (
                (i2 > 0 and _word_char(base[i2 - 1])) or (j2 > 0 and _word_char(alt[j2 - 1]))):
            i2, j2 = i2 + 1, j2 + 1
        if spans and i1 <= spans[-1][1] and j1 <= spans[-1][3]:  # 扩成整词以后和上一处连上了：合成一处
            spans[-1][1], spans[-1][3] = max(spans[-1][1], i2), max(spans[-1][3], j2)
        else:
            spans.append([i1, i2, j1, j2])
    return [(i1, i2, alt[j1:j2]) for i1, i2, j1, j2 in spans]


def analyze(rec: Dict[str, Any], text: Optional[str] = None) -> Dict[str, Any]:
    """一行要显示的东西。text = 现在的文字（草稿），默认用保存的文字。

    返回：
      text      现在的文字
      blue      [(s, e)] 现在的文字里改过的字（和最初识别的文字比）
      deleted   [(位置, 删掉的字)] 删掉的字，显示成蓝色删除线
      red       [(s, e)] 还可能有错、没改过的地方
      edits     [(s, e, 换成什么)] 还没采用的建议（位置按现在的文字算）
      sure      edits 里有把握的（「一键全部文字校正」只自动采用这些；没把握的要老师听录音，自己点这一行的「采用」）
      undo      [(s, e, 换回什么)] 已经采用了的建议，撤销时怎么改回去（位置按现在的文字算）
      adopted   建议已经全部用上了（「修改建议」的按钮变红）
      reasons   标红的原因
      active    这一行还算不算「可能有错」（还有红字或者还有没采用的建议）
      to_alt / to_base  现在的文字正好是记下的某个整句时：点「采用」/「已采用」以后会变成的整句（否则 None）
    """
    cur = str(rec.get("text", "") if text is None else text)
    orig = original_text(rec)
    blue: List[Range] = []
    deleted: List[Tuple[int, str]] = []
    if orig and cur != orig:
        for tag, i1, i2, j1, j2 in _opcodes(orig, cur):
            if tag in ("replace", "insert") and j2 > j1:
                while j1 > 0 and _word_char(cur[j1 - 1]) and _word_char(cur[j1]):  # 英文按整个单词变蓝
                    j1 -= 1
                while j2 < len(cur) and _word_char(cur[j2]) and _word_char(cur[j2 - 1]):
                    j2 += 1
                blue.append((j1, j2))
            elif tag == "delete" and i2 > i1:
                deleted.append((j1, orig[i1:i2]))
    sus = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else {}
    red: List[Range] = []
    edits: List[Edit] = []
    sure: List[Edit] = []
    undo: List[Edit] = []
    adopted = False
    reasons = [str(x) for x in (sus.get("reasons") or []) if x]
    st = known_states(rec) if sus else {}
    if sus:
        base = suspect_base(rec)
        ops = _opcodes(base, cur) if base != cur else [("equal", 0, len(base), 0, len(cur))]
        blocks = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in ops if tag == "equal"]
        for span in sus.get("spans") or []:
            try:
                s, e = int(span[0]), int(span[1])
            except (TypeError, ValueError, IndexError):
                continue
            m = None if touched(ops, s, e) else map_range(blocks, s, e)
            if m is not None and m[1] > m[0]:
                red.append(m)
        alt = str(sus.get("alt") or "")
        for s, e, rep in suggestion_edits(base, alt):
            m = None if touched(ops, s, e) else map_range(blocks, s, e)
            if m is not None:
                edits.append((m[0], m[1], rep))
        # 一键校正只自动采用「文字校正」检查过、有把握的建议：有 sure_alt 时只按它（只用有把握的改出来的那一句）；
        # 没经过文字校正的（自动查错字原来的建议）、整句都换掉的一律算没把握
        vetted = sus.get("src") == "transcript" and bool(alt) and not whole_sentence_suggestion(sus, base)
        if vetted:
            if "sure_alt" in sus:
                for s, e, rep in suggestion_edits(base, str(sus.get("sure_alt") or base)):
                    m = None if touched(ops, s, e) else map_range(blocks, s, e)
                    if m is not None:
                        sure.append((m[0], m[1], rep))
            else:
                sure = list(edits)
        if alt and alt != base and cur != base:  # 建议的地方现在是不是就是建议的写法（= 采用过）
            ops2 = _opcodes(alt, cur) if alt != cur else [("equal", 0, len(alt), 0, len(cur))]
            blocks2 = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in ops2 if tag == "equal"]
            for s, e, rep in suggestion_edits(alt, base):
                # 撤销「删掉的字」= 在那里补回去：旁边挨着老师改过的字不算碰到（不然采用以后没有撤销按钮）
                m = None if touched(ops2, s, e, strict=True) else map_range(blocks2, s, e)
                if m is not None:
                    undo.append((m[0], m[1], rep))
        mid = middle_state(st, cur) if alt and alt != base else None
        if mid:
            # 现在的文字是从中间的整句（直接改好 / 有把握的改好以后）改出来的：从那一句算还没采用的、采用过的，
            # 不从两头算——挨着的两个建议（一个采用了、一个没采用）从两头算会连成一处，撤销时把字改乱（「关系系带词」）
            ops3 = _opcodes(st[mid], cur) if st[mid] != cur else [("equal", 0, len(cur), 0, len(cur))]
            blocks3 = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in ops3 if tag == "equal"]

            def _mapped(dst: str, strict: bool = False) -> List[Edit]:
                out: List[Edit] = []
                for s, e, rep in suggestion_edits(st[mid], dst):
                    m = None if touched(ops3, s, e, strict=strict) else map_range(blocks3, s, e)
                    if m is not None:
                        out.append((m[0], m[1], rep))
                return out

            edits = _mapped(alt)
            undo = _mapped(base, strict=True)
            if vetted:
                sure = _mapped(st["sure"]) if mid == "direct" and st.get("sure") not in (None, st[mid]) else []
        adopted = bool(undo) and not edits
    red = _merge(red, len(cur))
    to_alt = to_base = None  # 现在的文字正好是记下的某个整句：采用 / 撤销以后会变成的整句
    if st:
        if cur != st["alt"] and cur in (st["base"], st.get("direct"), st.get("sure")):
            to_alt = st["alt"]
            if not edits:  # 一处一处对位置没对出来（同样的字挨着）：整句还是不一样，按钮照样要有
                edits = [(0, len(cur), st["alt"])]
        if cur != st["base"] and cur in (st["alt"], st.get("direct"), st.get("sure")):
            to_base = st["base"]
            if not undo:
                undo = [(0, len(cur), st["base"])]
        adopted = bool(undo) and not edits
    return {"text": cur, "blue": _merge(blue, len(cur)), "deleted": deleted, "red": red, "edits": edits,
            "sure": sure, "undo": undo, "adopted": adopted, "reasons": reasons, "active": bool(red or edits),
            "to_alt": to_alt, "to_base": to_base, "rec": rec}


def apply_edits(text: str, edits: Sequence[Edit]) -> str:
    """从后往前改（前面的位置不会变）；和已经改过的地方重叠的跳过。"""
    out = text
    left = len(text) + 1
    for s, e, rep in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        if not (0 <= s <= e <= len(text)) or e > left or (e == left and s == e):
            continue
        out = out[:s] + rep + out[e:]
        left = s
    return clean_transcript(out)


def describe_change(old: str, new: str, limit: int = 3) -> str:
    """两句话哪里不一样（给老师看）：「像主语 → 了；补上「那个」」。按单位比（一个英文单词、一个汉字算一个），
    不会把「像主语、宾语 → 了、宾语」说成「像主 → 了、宾」。"""
    ua = [(m.start(), m.end(), m.group()) for m in _UNIT.finditer(old)]
    ub = [(m.start(), m.end(), m.group()) for m in _UNIT.finditer(new)]
    items: List[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [u[2] for u in ua], [u[2] for u in ub],
                                                       autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        a = old[ua[i1][0]:ua[i2 - 1][1]] if i2 > i1 else ""
        b = new[ub[j1][0]:ub[j2 - 1][1]] if j2 > j1 else ""
        if a and b:
            items.append(f"{a} → {b}")
        elif a:
            items.append(f"删掉「{a}」")
        elif b:
            items.append(f"补上「{b}」")
    parts = items[:limit]
    if len(items) > limit:
        parts.append(f"还有 {len(items) - limit} 处")
    return "；".join(parts)


def describe_states(rec: Dict[str, Any], a: str, b: str, limit: int = 3) -> str:
    """从整句 a 到整句 b 改了什么：按记下的顺序（查错字时 → 直接改好 → 有把握的改好 → 都改好）一步一步说，
    每一步小，不会配错（两处挨着的改动一起比，会说成「像主 → 了、宾」）。a、b 不在记下的里面时整句比。"""
    st = known_states(rec)
    seq: List[str] = []
    for k in ("base", "direct", "sure", "alt"):
        x = st.get(k)
        if x is not None and (not seq or seq[-1] != x):
            seq.append(x)
    if a not in seq or b not in seq or a == b:
        return describe_change(a, b, limit)
    i, j = seq.index(a), seq.index(b)
    path = seq[i:j + 1] if i < j else seq[j:i + 1]
    items: List[str] = []
    for x, y in zip(path, path[1:]):
        d = describe_change(x, y, limit=99)
        items += [t for t in d.split("；") if t and t not in items]
    if len(items) > limit:
        items = items[:limit] + [f"还有 {len(items) - limit} 处"]
    return "；".join(items)


def describe_adopted(text: str, undo: Sequence[Edit], limit: int = 3) -> str:
    """已经采用的建议改了哪里：和 describe_edits 一样的说法（艾子 → as）。undo 是撤销时怎么改回去。"""
    return describe_edits(text, undo, limit, flip=True)


def describe_edits(text: str, edits: Sequence[Edit], limit: int = 3, flip: bool = False) -> str:
    """建议改哪里（给老师看的一句话）：「艾子 → as；删掉「的」；补上「了」」。flip：edits 是"改回去"的（已采用的建议）。"""
    items: List[str] = []
    counts: Dict[str, int] = {}
    for s, e, rep in edits:
        old_s, rep_s = text[s:e].strip(), rep.strip()
        if flip:
            old_s, rep_s = rep_s, old_s
        if old_s and rep_s:
            item = f"{old_s} → {rep_s}"
        elif old_s:
            item = f"删掉「{old_s}」"
        elif rep_s:
            item = f"补上「{rep_s}」"
        else:
            continue
        if item not in counts:
            items.append(item)
        counts[item] = counts.get(item, 0) + 1
    parts = [x + (f"（{counts[x]} 处）" if counts[x] > 1 else "") for x in items[:limit]]
    if len(items) > limit:
        parts.append(f"还有 {sum(counts[x] for x in items[limit:])} 处")
    return "；".join(parts)


# ============================================================================ 老师撤销过的改法（不再自动改回来）
REJECTED_FILE = "review_rejected.json"  # {片段 id: [[原来的字, 程序想改成的字], ...]}：老师撤销过、不要的改法


def rejected_path(project: Any) -> Path:
    return Path(project.root) / REJECTED_FILE


def load_rejected(project: Any) -> Dict[str, List[List[str]]]:
    """老师撤销过的改法（单独一个文件，查错字 / 准备素材写校对表时不会把它冲掉）；文件坏了当作没有。"""
    try:
        data = json.loads(rejected_path(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, List[List[str]]] = {}
    for k, v in data.items():
        if isinstance(v, list):
            out[str(k)] = [[str(x[0]), str(x[1])] for x in v if isinstance(x, (list, tuple)) and len(x) == 2]
    return out


def _save_rejected(project: Any, data: Dict[str, List[List[str]]]) -> None:
    p = rejected_path(project)
    data = {k: v for k, v in data.items() if v}
    if not data:
        try:
            p.unlink()
        except OSError:
            pass
        return
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


_UNIT = re.compile(r"[A-Za-z0-9']+|\S")


def change_pieces(old: str, new: str) -> List[Tuple[str, str]]:
    """一处改动拆成最小的改动（原来的, 改成的）：按「单位」比（一个英文单词、一个汉字、一个标点是一个单位，空格不算），
    一样多的单位一对一拆开：「壮与从剧 → 状语从句」= [(壮, 状), (与, 语), (剧, 句)]，「eggs rainbow → egg scramble」=
    [(eggs, egg), (rainbow, scramble)]，「艾子 → as」= [(艾子, as)]。撤销的时候和以后检查的时候都这样拆，
    所以不管位置、不管几处连在一起、不管从哪边比，都对得上。"""
    if old == new:
        return []
    a, b = _UNIT.findall(old), _UNIT.findall(new)
    out: List[Tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and i2 - i1 == j2 - j1:
            pairs = [(a[i1 + k], b[j1 + k]) for k in range(i2 - i1)]
        else:
            pairs = [(" ".join(a[i1:i2]), " ".join(b[j1:j2]))]
        for x in pairs:
            if x[0] != x[1] and x not in out:
                out.append(x)
    return out


def is_rejected(pairs: Any, text: str, s: int, e: int, rep: str) -> bool:
    """在 text 的 [s, e) 换成 rep，里面有没有老师撤销过的改法（pairs：这一行的 [[原来的, 程序想改成的], ...]）。
    这一处单独比、放在整句里比，有一个对上就算（两种比法拆出来的偶尔不一样）。"""
    if not pairs or not (0 <= s <= e <= len(text)):
        return False
    bad = {(str(p[0]), str(p[1])) for p in pairs if isinstance(p, (list, tuple)) and len(p) == 2}
    if any(pc in bad for pc in change_pieces(text[s:e], rep)):
        return True
    new = text[:s] + rep + text[e:]
    # 存进表格的文字都整理过（英文后面的逗号变半角等），撤销时记下的也是整理过的：两种都比
    return any(pc in bad for pc in change_pieces(text, new) + change_pieces(text, clean_transcript(new)))


def _undo_pieces(text: str, undo: Sequence[Edit]) -> List[List[str]]:
    """撤销的那几处（位置按现在的文字算，现在的文字里是程序改成的样子）→ [[原来的, 程序想改成的], ...]：
    整句比一次、每一处单独比一次，都记下。"""
    out: List[List[str]] = []
    wanted = apply_edits(text, undo)
    found = change_pieces(wanted, text)
    for s, e, rep in undo:
        if 0 <= s <= e <= len(text):
            found += change_pieces(rep, text[s:e])
    for a, b in found:
        if [a, b] not in out:
            out.append([a, b])
    return out


def reverted_pieces(rec: Dict[str, Any], old: str, new: str) -> List[List[str]]:
    """老师把文字从 old 改成 new（自己打字、撤销这一行的修改）时，把以前改过的地方（程序改的、采用的建议）改回了最初识别的样子：
    返回这些改法 [[原来的, 改成的], ...]。和最初识别的文字比（不靠「可能有错」列还在不在：点过「这句没错」、
    重新查过错字以后也认得出来），句子开头 / 结尾、删掉的字、英文单词都一样。"""
    if old == new:
        return []
    orig = original_text(rec)
    if not orig or orig == old:
        return []
    undone = set(change_pieces(old, new))
    return [[a, b] for a, b in change_pieces(orig, old) if (b, a) in undone]


def _remember_rejects(project: Any, clip_id: str, pairs: Sequence[Sequence[str]]) -> None:
    pairs = [[str(a), str(b)] for a, b in pairs]
    if not pairs:
        return
    data = load_rejected(project)
    old = data.get(clip_id, [])
    data[clip_id] = (old + [p for p in pairs if p not in old])[-100:]
    _save_rejected(project, data)


def _forget_rejects(project: Any, clip_id: str, text: str, edits: Sequence[Edit]) -> None:
    """老师自己点「采用」：这些改法不再算撤销过的。"""
    data = load_rejected(project)
    if not data.get(clip_id):
        return
    used = {(a, b) for s, e, rep in edits if 0 <= s <= e <= len(text)
            for a, b in change_pieces(text[s:e], rep) + change_pieces(text, text[:s] + rep + text[e:])
            + change_pieces(text, clean_transcript(text[:s] + rep + text[e:]))}
    keep = [p for p in data[clip_id] if (p[0], p[1]) not in used]
    if keep != data[clip_id]:
        data[clip_id] = keep
        _save_rejected(project, data)


def _within(cur: str, new: str, allowed: Sequence[Tuple[str, str]]) -> bool:
    """cur → new 的每一处改动都是 allowed 里的（建议本身的改动）：不会多出别的字。"""
    ok = set(allowed)
    return all(pc in ok for pc in change_pieces(cur, new))


def _merge_onto(src: str, dst: str, other: str, strict: bool = False) -> str:
    """把 src → other 的改动（老师自己改的别处）搬到 dst 上：dst 里那几个地方和 src 一样时才搬。"""
    blocks = _equal_blocks(src, dst)
    ops = _opcodes(src, dst)
    edits: List[Edit] = []
    for s, e, rep in suggestion_edits(src, other):
        m = None if touched(ops, s, e, strict=strict) else map_range(blocks, s, e)
        if m is None:
            return ""
        edits.append((m[0], m[1], rep))
    return apply_edits(dst, edits) if edits else dst


def _clash(a: Edit, b: Edit) -> bool:
    """两处改动（位置按同一句算）碰到一起：重叠；或者一边是插入、正好插在另一边改的地方里面或者两头（不知道先后）；
    两个插入在同一个地方。两处改动只是首尾挨着（都不是插入）不算。"""
    (s1, e1, _r1), (s2, e2, _r2) = a, b
    if s1 == e1 and s2 == e2:
        return s1 == s2
    if s1 == e1:
        return s2 <= s1 <= e2
    if s2 == e2:
        return s1 <= s2 <= e1
    return s1 < e2 and s2 < e1


def merge3(src: str, a: str, b: str) -> str:
    """src → a 和 src → b 两边的改动合起来（三方合并，位置都按 src 算）：两边同一处改得一模一样算一处；
    有碰到一起的就返回 ""（不知道该怎么合，不猜）。"""
    ea, eb = suggestion_edits(src, a), suggestion_edits(src, b)
    out = list(ea)
    for ed in eb:
        if ed in ea:
            continue
        if any(_clash(ed, f) for f in ea):
            return ""
        out.append(ed)
    return apply_edits(src, out) if out else src


def safe_apply(cur: str, edits: Sequence[Edit], src: Union[str, Sequence[str]], dst: str) -> str:
    """文字不是记下的整句时（老师又改过别处）采用 / 撤销：把建议（src → dst）用到 cur 上。src 可以给几个记下的整句
    （现在的文字可能是从其中哪一句改出来的），离现在的文字最近的先试。

    办法：三方合并——老师改的（src → cur）和建议（src → dst）都按 src 的位置合起来；两边碰到一起就不合（不猜）。
    合不了再试一处一处改（edits），改完检查三条：cur → 结果的每一处都是建议本身的改动；老师改的别处都还在；
    把结果再改回去（dst → src）又正好是 cur。都不行返回 ""（不改，不能把文字改坏——检查时发现过「了、宾语、宾语」
    「关系系带词」）。"""
    srcs = [src] if isinstance(src, str) else list(src)
    srcs = sorted(dict.fromkeys(x for x in srcs if x and x != dst), key=lambda x: len(change_pieces(x, cur)))
    for x in srcs:
        cand = merge3(x, dst, cur)
        if (cand and cand != cur and _within(cur, cand, change_pieces(x, dst))
                and _within(dst, cand, change_pieces(x, cur))):
            return cand
    cand = apply_edits(cur, edits) if edits else ""
    if cand and cand != cur:
        for x in srcs:
            if (_within(cur, cand, change_pieces(x, dst)) and _within(dst, cand, change_pieces(x, cur))
                    and _merge_onto(dst, x, cand, strict=True) == cur):
                return cand
    return ""


def middle_state(st: Dict[str, str], cur: str) -> Optional[str]:
    """现在的文字是不是从中间的整句（direct 直接改好以后 / sure 有把握的改好以后）改出来的：比查错字时（base）和
    都改好以后（alt）都近（改动少）时，返回 "direct" / "sure"；否则 None（按两头算）。"""
    if not st or st.get("alt") == st.get("base"):
        return None
    mids = [k for k in ("direct", "sure") if st.get(k) is not None and st[k] not in (st["base"], st["alt"])]
    if not mids:
        return None  # 没有中间的整句（大多数行）：不用比
    best, dist = None, min(len(change_pieces(st["base"], cur)), len(change_pieces(st["alt"], cur)))
    for k in mids:
        d = len(change_pieces(st[k], cur))
        if d < dist:
            best, dist = k, d
    return best


def known_states(rec: Dict[str, Any]) -> Dict[str, str]:
    """「可能有错」标记里记下的几个完整的句子：base = 查错字时的样子，direct = 直接改好以后，sure = 有把握的都改好以后，
    alt = 所有建议都改好以后。表格里的文字正好是其中一个时，采用 / 撤销直接换成另一个整句——不用一处一处对位置
    （同样的字挨着时，对位置会配错，把文字改坏：检查时发现过「了、宾语、宾语」）。"""
    sus = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else None
    if not sus:
        return {}
    base = suspect_base(rec)
    alt = str(sus.get("alt") or "") or base
    out = {"base": base, "alt": alt}
    if sus.get("src") == "transcript":
        out["sure"] = str(sus.get("sure_alt") or "") or alt if "sure_alt" in sus else alt
        if sus.get("direct_alt"):
            out["direct"] = str(sus["direct_alt"])
    return out


_ORDER = ("base", "direct", "sure", "alt")


def _states_before(st: Dict[str, str], key: str) -> List[str]:
    """记下的整句里排在 key 前面的（采用时，现在的文字可能是从这些改出来的）。"""
    return [st[k] for k in _ORDER[:_ORDER.index(key)] if st.get(k) is not None]


def _states_after(st: Dict[str, str], key: str) -> List[str]:
    """记下的整句里排在 key 后面的（撤销时，现在的文字可能是从这些改出来的）。"""
    return [st[k] for k in _ORDER[_ORDER.index(key) + 1:] if st.get(k) is not None]


def adopt_suggestion(project: Any, clip_id: str) -> Dict[str, Any]:
    """「✅ 采用建议」：把还没采用的建议改进这一行的文字（存进草稿，红灯；保存以后变绿灯）。"""
    with _LOCK:
        recs = _records(project)
        rec = recs.get(clip_id)
        if rec is None:
            raise KeyError(f"找不到这条片段（{clip_id}），请点「🔄 重新载入」")
        vals = current_values(rec, load_draft(project).get(clip_id))
        info = analyze(rec, vals["text"])
        if not info["edits"]:
            raise ValueError("这一条已经没有可以采用的建议了")
        if info["to_alt"]:
            new = info["to_alt"]  # 整句换成「所有建议都改好以后」的样子（不会配错位置）
            changes = describe_states(rec, vals["text"], new, limit=6)
        else:
            st = known_states(rec)
            new = safe_apply(vals["text"], info["edits"], _states_before(st, "alt"), st["alt"]) if st else ""
            changes = describe_change(vals["text"], new, limit=6) if new else ""
            if not new:
                raise ValueError("这一行你改过别的地方，程序没法确定建议该放在哪里，所以没有改（免得把字改乱）。"
                                 "请听一听录音，双击「文字」自己改：" + describe_edits(vals["text"], info["edits"], limit=3))
        if not new:
            raise ValueError("采用建议以后文字是空的，没有改。请听一听录音，双击「文字」自己改")
        _forget_rejects(project, clip_id, vals["text"], info["edits"])
        out = set_draft(project, clip_id, text=new)
        out.update(old_text=vals["text"], text=out["values"]["text"], changes=changes)
        return out


def unadopt_suggestion(project: Any, clip_id: str) -> Dict[str, Any]:
    """再点一下变红的按钮：撤销已经采用的建议（只把建议改过的地方改回去，老师自己改的别处不动）。存进草稿。"""
    with _LOCK:
        recs = _records(project)
        rec = recs.get(clip_id)
        if rec is None:
            raise KeyError(f"找不到这条片段（{clip_id}），请点「🔄 刷新表格」")
        vals = current_values(rec, load_draft(project).get(clip_id))
        info = analyze(rec, vals["text"])
        if not info["undo"]:
            raise ValueError("这一条没有采用过的建议可以撤销")
        if info["to_base"]:
            new = info["to_base"]  # 整句换回查错字时的样子
            pairs = [list(x) for x in change_pieces(new, vals["text"])]
            changes = describe_states(rec, new, vals["text"], limit=6)
        else:
            st = known_states(rec)
            new = safe_apply(vals["text"], info["undo"], _states_after(st, "base"), st["base"]) if st else ""
            if not new:
                raise ValueError("这一行你改过别的地方，程序没法确定该撤销哪几个字，所以没有改（免得把字改乱）。"
                                 "请双击「文字」自己改回去")
            pairs = [list(x) for x in change_pieces(new, vals["text"])]
            changes = describe_change(new, vals["text"], limit=6)
        if not new:
            raise ValueError("撤销以后文字是空的，没有改")
        _remember_rejects(project, clip_id, pairs)  # 再点一键校正时不再改回来
        out = set_draft(project, clip_id, text=new)
        out.update(old_text=vals["text"], text=out["values"]["text"], changes=changes)
        return out


def adopt_all_suggestions(project: Any) -> Dict[str, Any]:
    """「一键全部文字校正」的第二步：所有有把握的修改建议一次全部采用（和一行一行点「采用」一样，存成草稿、红灯）。

    删除的行、不保留（不当训练素材）的行不动；只标红、没有建议的地方没法自动改（不知道该改成什么），留着红色；
    没把握的建议（分量不够、另一个引擎整句听得都不一样）也不自动采用，留着红色，老师听了录音自己点这一行的「采用」。
    返回 {"rows": 改了几条, "changes": 改了几处, "no_suggestion": 只标红没有建议的有几条,
          "unsure": 有建议但没把握、没有自动采用的有几条, "examples": [...]}。"""
    with _LOCK:
        records = project.load_manifest()
        draft = load_draft(project)
        rejected = load_rejected(project)
        rows = changes = no_sug = unsure = 0
        examples: List[str] = []
        for rec in records:
            if rec.get("deleted"):
                continue
            rid = rec.get("id")
            vals = current_values(rec, draft.get(rid))
            if not vals["keep"]:
                continue
            if rec.get("suspect_ok") and rec.get("suspect_ok") == vals["text"]:
                continue  # 老师点过「这句没错」（文字没再改过）：不动
            info = analyze(rec, vals["text"])
            todo = [ed for ed in info["sure"] if not is_rejected(rejected.get(rid), vals["text"], *ed)]
            st = known_states(rec)
            target = st.get("sure") if st else None
            if (todo and target and target != vals["text"] and vals["text"] in (st["base"], st.get("direct"))
                    and not is_rejected(rejected.get(rid), vals["text"], 0, len(vals["text"]), target)):
                new = target  # 整句换成「有把握的都改好以后」的样子（不会配错位置）
            elif todo and target:
                # 三方合并 / 一处一处改，改完检查；不确定就不改（这一行留给老师）
                new = safe_apply(vals["text"], todo, _states_before(st, "sure"), target) or vals["text"]
            else:
                new = vals["text"]
            new = clean_transcript(new) if new else new
            bad = {(str(a), str(b)) for a, b in (rejected.get(rid) or []) if isinstance(a, str) and isinstance(b, str)}
            if bad and new != vals["text"] and any(pc in bad for pc in change_pieces(vals["text"], new)):
                new = vals["text"]  # 里面有老师撤销过的改法：这一行不动
            after = analyze(rec, new) if new else info
            if after["edits"]:
                unsure += 1  # 采用了有把握的以后还剩下建议：没把握的，留给老师
            elif after["red"]:
                no_sug += 1  # 还有标红、没有建议的地方
            if not todo or not new or new == vals["text"]:
                continue
            if len(examples) < 6:
                examples.append(describe_edits(vals["text"], todo, limit=1))
            nv = dict(vals, text=new, lang=detect_lang(new) or vals["lang"])
            if nv == saved_values(rec):
                draft.pop(rid, None)
            else:
                draft[rid] = nv
            rows += 1
            changes += len(todo)
        if rows:
            save_draft(project, draft)
        return {"rows": rows, "changes": changes, "no_suggestion": no_sug, "unsure": unsure, "examples": examples}


# ============================================================================ 保存、删除、恢复
def _apply_text(rec: Dict[str, Any], text: str) -> None:
    """改文字（apply_text_edit 会记下最初识别的文字、换算没改到的红字位置）。"""
    from voicetwin.project import apply_text_edit

    apply_text_edit(rec, text)


def save_rows(project: Any, ids: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """把草稿写进校对表（manifest + transcripts.csv）。ids = None 时保存全部。

    返回 {"saved": [id...], "changed": {"text": n, "keep": n, "lang": n}, "csv_locked": bool}。
    transcripts.csv 正被 Excel/WPS 打开时，manifest（真正的数据）照样保存，csv_locked = True。"""
    with _LOCK:
        draft = load_draft(project)
        want = set(draft) if ids is None else {str(i) for i in ids} & set(draft)
        records = project.load_manifest()
        changed = {"text": 0, "keep": 0, "lang": 0}
        saved: List[str] = []
        for rec in records:
            rid = rec.get("id")
            if rid not in want or rec.get("deleted"):  # 删除（灰色）的行不保存，撤销删除以后还能接着改
                continue
            vals = draft[rid]
            touched = False
            if vals["text"] and vals["text"] != rec.get("text"):
                _apply_text(rec, vals["text"])
                changed["text"] += 1
                touched = True
            if vals["keep"] != bool(rec.get("keep", True)):
                rec["keep"] = vals["keep"]
                rec["manual_keep"] = vals["keep"]
                if not vals["keep"]:
                    rec["drop_reason"] = rec.get("drop_reason") or "手动不保留"
                changed["keep"] += 1
                touched = True
            if vals["lang"] in ("zh", "en") and vals["lang"] != rec.get("lang"):
                rec["lang"] = vals["lang"]
                changed["lang"] += 1
                touched = True
            if touched:
                rec["edited"] = True
                rec["edited_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            saved.append(rid)
            draft.pop(rid, None)
        project.save_manifest(records)
        save_draft(project, draft)
        locked = False
        try:
            project.export_csv(records)
        except PermissionError:
            locked = True
        return {"saved": saved, "changed": changed, "csv_locked": locked}


def delete_clip(project: Any, clip_id: str) -> Dict[str, Any]:
    """「🗑️ 删除这一行」：这一行变灰、不再用来训练（音频文件不删，随时可以撤销删除）。马上保存。"""
    with _LOCK:
        records = project.load_manifest()
        rec = next((r for r in records if r.get("id") == clip_id), None)
        if rec is None:
            raise KeyError(f"找不到这条片段（{clip_id}），请点「🔄 重新载入」")
        if not rec.get("deleted"):
            rec["deleted"] = True
            rec["before_delete"] = {"keep": bool(rec.get("keep", True)), "manual_keep": rec.get("manual_keep"),
                                    "drop_reason": rec.get("drop_reason", "")}
            rec["keep"] = False
            rec["manual_keep"] = False
            rec["drop_reason"] = DELETED_REASON
        project.save_manifest(records)  # 没保存的修改（草稿）留着：撤销删除以后还在
        locked = False
        try:
            project.export_csv(records)
        except PermissionError:
            locked = True
        return {"id": clip_id, "text": rec.get("text", ""), "csv_locked": locked}


def restore_clip(project: Any, clip_id: str) -> Dict[str, Any]:
    """撤销删除：回到删除之前的「保留」。"""
    with _LOCK:
        records = project.load_manifest()
        rec = next((r for r in records if r.get("id") == clip_id), None)
        if rec is None:
            raise KeyError(f"找不到这条片段（{clip_id}）")
        if rec.get("deleted"):
            before = rec.pop("before_delete", None) or {}
            rec.pop("deleted", None)
            rec["keep"] = bool(before.get("keep", True))
            if before.get("manual_keep") is None:
                rec.pop("manual_keep", None)
            else:
                rec["manual_keep"] = bool(before["manual_keep"])
            rec["drop_reason"] = str(before.get("drop_reason") or "")
        project.save_manifest(records)
        locked = False
        try:
            project.export_csv(records)
        except PermissionError:
            locked = True
        return {"id": clip_id, "text": rec.get("text", ""), "csv_locked": locked}


def deleted_records(project: Any) -> List[Dict[str, Any]]:
    return [r for r in project.load_manifest() if r.get("deleted")]


# ============================================================================ 训练素材：数量、确认
CONFIRM_FILE = "review_confirmed.json"


def is_material(rec: Dict[str, Any]) -> bool:
    """这一条会不会用来训练（含「考试题」）：没被删除、程序判断能用、有文字。"""
    return (not rec.get("deleted")) and bool(rec.get("keep", True)) and bool(str(rec.get("text") or "").strip())


def material_counts(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """校对表上方那一行的数字：一共 total − 你删除的 deleted − 程序判断不能用的 unusable = 用来训练的 material。

    material 里 val 条是「考试题」（不进训练，用来自动挑选最像你的模型），train = material − val。
    no_text：没有文字的片段（不算删除的）；pending：其中「识别文字」这一步还没做的（再点开始准备素材会接着识别）。"""
    total = len(records)
    deleted = sum(1 for r in records if r.get("deleted"))
    material = [r for r in records if is_material(r)]
    val = sum(1 for r in material if r.get("split") == "val")
    no_text = [r for r in records if not r.get("deleted") and not str(r.get("text") or "").strip()]
    return {"total": total, "deleted": deleted, "unusable": total - deleted - len(material),
            "material": len(material), "val": val, "train": len(material) - val,
            "minutes": round(sum(float(r.get("duration", 0) or 0) for r in material) / 60.0, 1),
            "no_text": len(no_text), "pending": sum(1 for r in no_text if not r.get("asr_done"))}


def material_signature(records: Sequence[Dict[str, Any]]) -> str:
    """用来训练的是哪些句子、文字是什么：确认以后又改过（删除、恢复、保存了修改）时这个值会变。"""
    import hashlib

    items = sorted(f"{r.get('id')}\t{r.get('text')}" for r in records if is_material(r))
    return hashlib.sha1("\n".join(items).encode("utf-8")).hexdigest()


def confirm_path(project: Any) -> Path:
    return Path(project.root) / CONFIRM_FILE


def load_confirmed(project: Any) -> Dict[str, Any]:
    """{"time": "...", "signature": "...", "counts": {...}}；还没确认过（或文件坏了）返回 {}。"""
    try:
        data = json.loads(confirm_path(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) and data.get("signature") else {}


def save_confirmed(project: Any, records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    data = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "signature": material_signature(records),
            "counts": material_counts(records)}
    p = confirm_path(project)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)
    return data


# ============================================================================ 下载改好的文字（txt）
EXPORT_DIR = "改好的文字"
KEEP_EXPORTS = 20


def export_text(project: Any) -> Dict[str, Any]:
    """「⬇️ 下载改好的文字（txt）」：把「文字」列现在的文字（含没保存的修改）按表格的顺序存成 txt，一行一句。

    删除的（紫色）行不要；没有文字的行跳过。存在 ``workspace/<声音>/改好的文字/``（只留最近 20 个），
    记事本能直接打开（UTF-8 带 BOM、Windows 换行）；下次可以当逐字稿上传，做「文字校正」。
    返回 {"path", "lines", "unsaved", "deleted"}：unsaved = 其中还没保存的修改有几条（提醒老师点保存）。"""
    with _LOCK:
        records = project.load_manifest()
        draft = load_draft(project)
        lines: List[str] = []
        unsaved = deleted = 0
        for rec in records:
            if rec.get("deleted"):
                deleted += 1
                continue
            entry = draft.get(rec.get("id"))
            text = re.sub(r"\s+", " ", str(current_values(rec, entry)["text"] or "")).strip()
            if not text:
                continue
            lines.append(text)
            if is_dirty(rec, entry):
                unsaved += 1
    if not lines:
        raise ValueError("校对表里还没有文字，没有可以下载的。请先点上面的「开始准备素材」。")
    folder = Path(project.root) / EXPORT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r'[\\/:*?"<>|\s]+', "_", str(getattr(project, "voice", "") or "声音")).strip("_") or "声音"
    path = folder / f"改好的文字_{safe}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    k = 2
    while path.exists():
        path = folder / f"改好的文字_{safe}_{time.strftime('%Y%m%d_%H%M%S')}_{k}.txt"
        k += 1
    path.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8-sig"))
    old = sorted(folder.glob("改好的文字_*.txt"), key=lambda q: q.stat().st_mtime)
    for q in old[:-KEEP_EXPORTS]:
        try:
            q.unlink()
        except OSError:
            pass
    return {"path": str(path), "lines": len(lines), "unsaved": unsaved, "deleted": deleted}


# ============================================================================ 查找 / 替换（像 Word）
FIND_FILE = "review_find.json"
UNDO_FILE = "review_undo.json"
_WORDISH = re.compile(r"[A-Za-z0-9]+(?:[ '\-][A-Za-z0-9]+)*")

Match = Tuple[str, int, int]  # (片段 id, 开始, 结束)：位置按这一行现在的文字（含没保存的修改）算


def find_pattern(query: Any, whole_word: bool = True) -> Optional["re.Pattern[str]"]:
    """查找用的规则：不分大小写；英文词（as、NVH、in the）勾了「只找整个单词」时不找单词里面的（as 不会找到 has）。
    中文、标点照原样找。空的返回 None。"""
    q = str(query or "").strip()
    if not q:
        return None
    body = re.escape(q)
    if whole_word and _WORDISH.fullmatch(q):
        body = r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])"
    return re.compile(body, re.IGNORECASE)


def find_matches(project: Any, query: Any, whole_word: bool = True) -> List[Match]:
    """所有没删除的句子里找到的地方，按表格顺序。"""
    pat = find_pattern(query, whole_word)
    if pat is None:
        return []
    draft = load_draft(project)
    out: List[Match] = []
    for rec in project.load_manifest():
        if rec.get("deleted"):
            continue
        text = current_values(rec, draft.get(rec["id"]))["text"]
        out += [(rec["id"], m.start(), m.end()) for m in pat.finditer(text) if m.end() > m.start()]
    return out


def load_find(project: Any) -> Dict[str, Any]:
    """现在正在找什么：{"q": 关键字, "word": 英文只找整个单词, "i": 现在是第几处（从 0 开始）,
    "ids": 这次查找找到过的句子}；没在找返回 {}。"""
    try:
        data = json.loads((Path(project.root) / FIND_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) and str(data.get("q") or "").strip() else {}


def save_find(project: Any, query: Any, whole_word: bool, index: int = 0, fresh: bool = False,
              extra: Iterable[str] = ()) -> Dict[str, Any]:
    """记下现在找什么、是第几处，和这次查找找到过的句子（ids）。

    找到过的句子在关闭查找之前一直列在表格里：换完、改完、删除以后那一句不会突然不见（删除的变紫色）。
    fresh=True（点「🔍 查找」、换了关键字）重新开始记。"""
    q, word = str(query or "").strip(), bool(whole_word)
    old = {} if fresh else load_find(project)
    ids = list(old.get("ids") or []) if old.get("q") == q and bool(old.get("word", True)) == word else []
    for rid in [m[0] for m in find_matches(project, q, word)] + list(extra):
        if rid not in ids:
            ids.append(rid)
    data = {"q": q, "word": word, "i": max(0, int(index)), "ids": ids}
    p = Path(project.root) / FIND_FILE
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)
    return data


def clear_find(project: Any) -> None:
    try:
        (Path(project.root) / FIND_FILE).unlink()
    except OSError:
        pass


def _replace_in_text(pat: "re.Pattern[str]", text: str, repl: str, start: Optional[int] = None) -> Tuple[str, int]:
    """把 text 里找到的换成 repl（start 给了时只换从这个位置开始的那一处）。返回 (新文字, 换了几处)。"""
    if start is None:
        new, n = pat.subn(lambda m: repl, text)
        return new, n
    m = pat.match(text, start)
    if not m or m.start() != start:
        return text, 0
    return text[:m.start()] + repl + text[m.end():], 1


def replace_matches(project: Any, query: Any, repl: Any, whole_word: bool = True,
                    target: Optional[Tuple[str, int]] = None) -> Dict[str, Any]:
    """替换：target=(id, 位置) 只换那一处，None 换全部。换完的句子存成没保存的修改（红灯），和自己改字一样，要保存才生效。
    换之前记下这些句子原来的样子，「撤销刚才的替换」可以改回去。

    返回 {"count": 换了几处, "rows": 改了几句, "skipped": 换完会变成空的、没换的句子数, "ids": [...]}。"""
    pat = find_pattern(query, whole_word)
    if pat is None:
        raise ValueError("请先在「查找」里输入要找的字")
    repl = str(repl or "")
    with _LOCK:
        draft = load_draft(project)
        rejected_before = load_rejected(project)  # 替换加了哪些撤销记录（「撤销刚才的替换」时去掉）
        recs = [r for r in project.load_manifest() if not r.get("deleted")]
        if target is not None:
            recs = [r for r in recs if r["id"] == target[0]]
        undo: Dict[str, Any] = {}
        count = rows = skipped = 0
        ids: List[str] = []
        for rec in recs:
            rid = rec["id"]
            before = current_values(rec, draft.get(rid))
            text = before["text"]
            new, n = _replace_in_text(pat, text, repl, target[1] if target is not None else None)
            if not n or new == text:
                continue
            if not clean_transcript(new):
                skipped += 1
                continue
            after = set_draft(project, rid, text=new)["values"]
            undo[rid] = {"text": text, "lang": before["lang"], "after": after["text"]}
            added = [x for x in load_rejected(project).get(rid, []) if x not in rejected_before.get(rid, [])]
            if added:  # 这次替换把采用过的建议改回去了：记下是替换加的，「撤销刚才的替换」时只去掉这些
                undo[rid]["rejected_added"] = added
            draft = load_draft(project)
            count += n
            rows += 1
            ids.append(rid)
        if undo:
            p = Path(project.root) / UNDO_FILE
            p.write_text(json.dumps({"query": str(query), "repl": repl, "rows": undo}, ensure_ascii=False),
                         encoding="utf-8")
        return {"count": count, "rows": rows, "skipped": skipped, "ids": ids}


def undo_replace(project: Any) -> Dict[str, int]:
    """撤销上一次替换：那几句的文字改回替换之前的样子（存成没保存的修改，和替换一样要保存才生效；
    替换以后已经保存了也能改回去）。替换以后又改过、或者删除了的句子不动（不把老师后来的修改冲掉）。

    返回 {"rows": 改回了几句, "kept": 又改过所以没动的句子数}；没有可撤销的两个都是 0。"""
    p = Path(project.root) / UNDO_FILE
    out = {"rows": 0, "kept": 0}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    rows = data.get("rows") if isinstance(data, dict) else None
    if not isinstance(rows, dict) or not rows:
        return out
    with _LOCK:
        draft = load_draft(project)
        known = {r["id"]: r for r in project.load_manifest()}
        for rid, entry in rows.items():
            rec = known.get(rid)
            if rec is None or not isinstance(entry, dict) or not str(entry.get("text") or "").strip():
                continue
            if rec.get("deleted") or current_values(rec, draft.get(rid))["text"] != entry.get("after"):
                out["kept"] += 1
                continue
            set_draft(project, rid, remember=False, text=entry["text"], lang=entry.get("lang"))  # 撤销替换不算老师不要程序的改法
            draft = load_draft(project)
            out["rows"] += 1
            added = [x for x in (entry.get("rejected_added") or []) if isinstance(x, list) and len(x) == 2]
            if added:  # 替换时加上的撤销记录去掉（之后老师自己撤销的留着）
                rej = load_rejected(project)
                rej[rid] = [x for x in rej.get(rid, []) if x not in added]
                _save_rejected(project, rej)
        p.unlink()
        return out


def has_undo(project: Any) -> bool:
    return (Path(project.root) / UNDO_FILE).exists()
