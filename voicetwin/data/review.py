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
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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


def set_draft(project: Any, clip_id: str, **changes: Any) -> Dict[str, Any]:
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
            n = 1 if draft.pop(clip_id, None) is not None else 0
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


def touched(ops: Sequence[Tuple[str, int, int, int, int]], s: int, e: int) -> bool:
    """旧文字的 [s, e) 有没有被改到。挨着边的插入也算改到（查错字时"这里漏了字"标的是缺字位置两边的字）；
    s == e（建议在这里插入）时，这个位置上或者两边有改动都算。"""
    for tag, i1, i2, _j1, _j2 in ops:
        if tag == "equal":
            continue
        if i1 == i2:
            if s <= i1 <= e:
                return True
        elif s == e:
            if i1 <= s <= i2:
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
      undo      [(s, e, 换回什么)] 已经采用了的建议，撤销时怎么改回去（位置按现在的文字算）
      adopted   建议已经全部用上了（「修改建议」的按钮变红）
      reasons   标红的原因
      active    这一行还算不算「可能有错」（还有红字或者还有没采用的建议）
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
    undo: List[Edit] = []
    adopted = False
    reasons = [str(x) for x in (sus.get("reasons") or []) if x]
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
        if alt and alt != base and cur != base:  # 建议的地方现在是不是就是建议的写法（= 采用过）
            ops2 = _opcodes(alt, cur) if alt != cur else [("equal", 0, len(alt), 0, len(cur))]
            blocks2 = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in ops2 if tag == "equal"]
            for s, e, rep in suggestion_edits(alt, base):
                m = None if touched(ops2, s, e) else map_range(blocks2, s, e)
                if m is not None:
                    undo.append((m[0], m[1], rep))
        adopted = bool(undo) and not edits
    red = _merge(red, len(cur))
    return {"text": cur, "blue": _merge(blue, len(cur)), "deleted": deleted, "red": red, "edits": edits,
            "undo": undo, "adopted": adopted, "reasons": reasons, "active": bool(red or edits)}


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
        new = apply_edits(vals["text"], info["edits"])
        if not new:
            raise ValueError("采用建议以后文字是空的，没有改。请听一听录音，双击「文字」自己改")
        out = set_draft(project, clip_id, text=new)
        out.update(old_text=vals["text"], text=new, changes=describe_edits(vals["text"], info["edits"], limit=6))
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
        new = apply_edits(vals["text"], info["undo"])
        if not new:
            raise ValueError("撤销以后文字是空的，没有改")
        out = set_draft(project, clip_id, text=new)
        out.update(old_text=vals["text"], text=new, changes=describe_adopted(vals["text"], info["undo"], limit=6))
        return out


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
