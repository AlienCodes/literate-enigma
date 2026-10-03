"""声音项目：一个"声音"（例如"我的讲课声音"）对应 workspace 下的一个目录。"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from voicetwin.config import Config, resolve_path

from voicetwin.utils.log import get_logger

log = get_logger("project")

MANIFEST_FIELDS_CSV = ["id", "keep", "split", "lang", "duration", "text", "drop_reason", "audio"]
_WARNED_EMPTY: set = set()  # 已经说过「manifest.jsonl 是空的」的声音（每个只说一次）


def _safe_voice_name(name: str) -> str:
    name = name.strip().rstrip(". ")  # Windows 的文件夹名结尾不能是点和空格
    if not name:
        raise ValueError("声音名称不能为空（也不能只有点「.」）")
    if re.search(r"[\\/:*?\"<>|]", name):
        raise ValueError("声音名称不能包含 \\ / : * ? \" < > | 这些字符")
    if any(ord(ch) < 32 for ch in name):
        raise ValueError("声音名称里不能有换行、Tab 这样的特殊字符")
    return name


class Project:
    def __init__(self, cfg: Config, voice: str):
        self.cfg = cfg
        self.voice = _safe_voice_name(voice)
        workspace = resolve_path(cfg, cfg.get("workspace", "./workspace")) or Path("workspace").resolve()
        self.root = workspace / self.voice
        self.raw_dir = self.root / "raw"
        self.clips_dir = self.root / "clips"
        self.refs_dir = self.root / "references"
        self.exports_dir = self.root / "exports"
        self.models_dir = self.root / "models"
        self.outputs_dir = self.root / "outputs"
        self.cache_dir = self.root / "cache"
        self.logs_dir = self.root / "logs"
        self.manifest_path = self.root / "manifest.jsonl"
        self.csv_path = self.root / "transcripts.csv"
        self.csv_snapshot_path = self.root / "transcripts.exported.json"
        self.sources_path = self.root / "sources.json"
        self.references_path = self.root / "references.json"
        self.profile_path = self.root / "profile.json"
        self.models_path = self.root / "models.json"
        self.centroid_path = self.root / "speaker_centroid.npy"
        self.lexicon_path = self.root / "lexicon.txt"

    # ------------------------------------------------------------------ 基础
    def ensure(self) -> "Project":
        for d in (self.root, self.raw_dir, self.clips_dir, self.refs_dir, self.exports_dir, self.models_dir,
                  self.outputs_dir, self.cache_dir, self.logs_dir):
            d.mkdir(parents=True, exist_ok=True)
        if not self.lexicon_path.exists():
            self.lexicon_path.write_text(LEXICON_TEMPLATE, encoding="utf-8")
        return self

    @property
    def exists(self) -> bool:
        return self.manifest_path.exists()

    def abspath(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (self.root / p)

    def relpath(self, path: Path) -> str:
        try:
            return Path(path).resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return str(Path(path).resolve())

    # ------------------------------------------------------------------ JSON
    @staticmethod
    def read_json(path: Path, default: Any = None) -> Any:
        """读 JSON；没有 → default。坏了（写到一半断电、硬盘满了留下的空文件 / 半个文件）：留一份 .bad 副本，
        当作 default（不让整个程序一直报「出现了意外错误」）。一时被占用（Windows）等一会儿再读。"""
        from voicetwin.utils import atomic

        try:
            text = atomic.read_text(Path(path))
        except FileNotFoundError:
            return default
        try:
            return json.loads(text)
        except ValueError:
            log.warning(f"文件坏了，当作没有（留了一份 {Path(path).name}.bad）：{path}")
            atomic.keep_bad_copy(Path(path))
            return default

    @staticmethod
    def write_json(path: Path, data: Any) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        from voicetwin.utils import atomic

        atomic.write_text(path, json.dumps(data, ensure_ascii=False, indent=2))

    # ------------------------------------------------------------------ manifest
    def load_manifest(self, only_kept: bool = False, split: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return []
        from voicetwin.utils import atomic

        records = []
        bad = 0
        for line in atomic.read_text(self.manifest_path).splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                bad += 1
                continue
            if isinstance(rec, dict) and rec.get("id"):
                records.append(rec)
            else:
                bad += 1
        if bad:  # 坏了的行（写到一半断电）：跳过、留一份副本，别的照常用（以前整个校对表打不开、保存 / 确认一直失败）
            log.warning(f"校对表 manifest.jsonl 有 {bad} 行坏了，跳过（留了一份 manifest.jsonl.bad）")
            atomic.keep_bad_copy(self.manifest_path)
        elif not records:
            self._warn_empty_manifest()
        if only_kept:  # 校对表里删除的一定不算（delete_clip 也会把 keep 设成 False，这里再保险一次）
            records = [r for r in records if r.get("keep", True) and not r.get("deleted")]
        if split:
            records = [r for r in records if r.get("split", "train") == split]
        return records

    def _warn_empty_manifest(self) -> None:
        """manifest.jsonl 在、却是空的，切好的片段还在：多半是保存的时候断电了（以前一声不吭，网页只说「还没有片段」）。
        每个声音只在黑色窗口 / 记录里说一次（这个函数一直被调用）。"""
        key = str(self.manifest_path)
        if key in _WARNED_EMPTY:
            return
        try:
            has_clips = any(self.clips_dir.glob("*.wav"))
        except OSError:
            has_clips = False
        if has_clips:
            _WARNED_EMPTY.add(key)
            log.warning(f"校对表 manifest.jsonl 是空的，可是切好的片段还在（{self.clips_dir}）：多半是保存的时候电脑断电或死机了。"
                        f"上次保存的文字在 {self.csv_path.name} 里还有一份，程序不会再用空的校对表把它冲掉（会先另存一份备份）")

    def save_manifest(self, records: Iterable[Dict[str, Any]]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        from voicetwin.utils import atomic

        atomic.write_text(self.manifest_path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))

    def export_csv(self, records: Optional[List[Dict[str, Any]]] = None) -> Path:
        """导出校对表（用 Excel/WPS 打开，改错字、把 keep 改成 0 可删掉片段）。"""
        from voicetwin.utils import atomic

        records = records if records is not None else self.load_manifest()
        self._keep_old_csv(records)
        tmp = atomic.tmp_for(self.csv_path)  # 先写临时文件再换上去：被 Excel 打开着时不会留下半个表
        try:
            with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS_CSV)
                writer.writeheader()
                for r in records:
                    writer.writerow({
                        "id": r["id"],
                        "keep": 1 if r.get("keep", True) else 0,
                        "split": r.get("split", "train"),
                        "lang": r.get("lang", ""),
                        "duration": f"{r.get('duration', 0):.2f}",
                        "text": r.get("text", ""),
                        "drop_reason": r.get("drop_reason", ""),
                        "audio": str(self.abspath(r["path"])),
                    })
        except BaseException:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise
        atomic.finish(tmp, self.csv_path)
        # 记下这次写进 CSV 的内容：读回时只用老师在 Excel 里真改过的格子（CSV 上次没能更新——被 Excel 打开着——
        # 的时候，里面是旧的字，不能把网页上后来保存的修改改回去）
        snap = {r["id"]: [str(r.get("text", "") or ""), 1 if r.get("keep", True) else 0, str(r.get("lang", "") or "")]
                for r in records}
        try:
            atomic.write_text(self.csv_snapshot_path, json.dumps(snap, ensure_ascii=False))
        except OSError:
            pass
        return self.csv_path

    def _keep_old_csv(self, records: List[Dict[str, Any]]) -> Optional[Path]:
        """这次要写的校对表比上次写的少了句子：正常情况下句子只会多不会少（删除也只是标成紫色），少了多半是 manifest.jsonl
        坏了 / 空了（保存的时候断电）。先把上次的 transcripts.csv 另存一份「transcripts_备份_时间.csv」，再写新的——
        以前照着网页说的再点「开始准备素材」，最后一份改好的文字也被空表冲掉了。返回备份的位置（没备份返回 None）。"""
        import shutil
        import time

        if not self.csv_path.exists():
            return None
        snap = self.read_json(self.csv_snapshot_path, None)
        if not isinstance(snap, dict) or not snap:
            return None
        ids = {str(r.get("id")) for r in records}
        lost = sum(1 for k in snap if k not in ids)
        if not lost:
            return None
        dest = self.root / f"transcripts_备份_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        k = 2
        while dest.exists():
            dest = self.root / f"transcripts_备份_{time.strftime('%Y%m%d_%H%M%S')}_{k}.csv"
            k += 1
        try:
            shutil.copy2(self.csv_path, dest)
        except OSError as exc:
            log.warning(f"没能另存 transcripts.csv 的备份（{exc}）")
            return None
        log.warning(f"这次的校对表比上次少了 {lost} 句（多半是 manifest.jsonl 坏了 / 空了）：上次的 transcripts.csv 另存成了 "
                    f"{dest.name}，里面有原来改好的文字")
        return dest

    def import_csv(self) -> Dict[str, int]:
        """读回校对表，把修改（文字、keep、语言）同步到 manifest。

        - 改了文字的片段：去掉"可能有错"的标记（suspect），重新算语速；
        - 「保留」那一格空着：保持原来的选择（不再当成"删掉"）。
        """
        from voicetwin.utils.textutil import clean_transcript

        if not self.csv_path.exists():
            raise FileNotFoundError(f"找不到校对表 {self.csv_path}")
        records = {r["id"]: r for r in self.load_manifest()}
        from voicetwin.data.review import upgrade_confirmed

        upgrade_confirmed(self, list(records.values()))  # 旧版本的确认记录先换成新算法（Excel 里只改了语言也看得出来）
        changed = {"text": 0, "keep": 0, "lang": 0}
        snap = self.read_json(self.csv_snapshot_path, None)
        snap = snap if isinstance(snap, dict) else {}
        with open(self.csv_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rid = (row.get("id") or "").strip()
                if rid not in records:
                    continue
                rec = records[rid]
                old = snap.get(rid) if isinstance(snap.get(rid), list) and len(snap.get(rid)) == 3 else None
                text = clean_transcript(row.get("text") or "")
                if old is not None and text == clean_transcript(old[0]):
                    text = ""  # 这一格在 Excel 里没改过：不动（网页上后来改的为准）
                if text and text != rec.get("text"):
                    apply_text_edit(rec, text)
                    changed["text"] += 1
                raw_keep = str(row.get("keep") if row.get("keep") is not None else "").strip()
                if raw_keep and old is not None and (raw_keep not in KEEP_FALSE_VALUES) == bool(old[1]):
                    raw_keep = ""  # 没改过
                if raw_keep:
                    keep = raw_keep not in KEEP_FALSE_VALUES
                    if keep != rec.get("keep", True):
                        rec["keep"] = keep
                        rec["manual_keep"] = keep
                        rec["edited"] = True
                        if not keep:
                            rec["drop_reason"] = rec.get("drop_reason") or "手动删除"
                        changed["keep"] += 1
                lang = (row.get("lang") or "").strip().lower()
                if old is not None and lang == str(old[2]).lower():
                    lang = ""  # 没改过
                if lang in ("zh", "en") and lang != rec.get("lang"):
                    rec["lang"] = lang
                    changed["lang"] += 1
                    rec["edited"] = True
        self.save_manifest(records.values())
        return changed

    def set_clip_text(self, clip_id: str, text: str) -> Dict[str, Any]:
        """改一个片段的文字（例如采用"可能有错"的建议），保存 manifest 并重新导出校对表。

        manifest 才是真正的数据：transcripts.csv 正被 Excel/WPS 打开（Windows 上会锁住文件）时，
        修改照样生效，只是 CSV 这次没能同步——返回值里 ``csv_locked`` 为 True，界面会提醒关掉 Excel 后再保存一次。"""
        from voicetwin.utils.textutil import clean_transcript

        records = self.load_manifest()
        rec = next((r for r in records if r.get("id") == clip_id), None)
        if rec is None:
            raise KeyError(f"找不到片段 {clip_id}")
        text = clean_transcript(text or "")
        if not text:
            raise ValueError("文字不能为空")
        if text != rec.get("text"):
            apply_text_edit(rec, text)
        else:
            rec.pop("suspect", None)
        self.save_manifest(records)
        try:
            self.export_csv(records)
        except PermissionError:
            out = dict(rec)
            out["csv_locked"] = True
            return out
        return rec

    def last_modified(self) -> float:
        """这个声音最后一次改动的时间（素材、校对、训练、生成里最新的那个）。"""
        latest = 0.0
        for p in (self.manifest_path, self.csv_path, self.models_path, self.profile_path, self.references_path,
                  self.root / "prepare_summary.json"):
            try:
                latest = max(latest, p.stat().st_mtime)
            except OSError:
                continue
        try:
            for p in self.outputs_dir.iterdir():
                try:
                    latest = max(latest, p.stat().st_mtime)
                except OSError:
                    continue
        except OSError:
            pass
        return latest

    # ------------------------------------------------------------------ 其它产物
    def load_references(self) -> List[Dict[str, Any]]:
        return self.read_json(self.references_path, []) or []

    def load_profile(self) -> Dict[str, Any]:
        return self.read_json(self.profile_path, {}) or {}

    def load_models(self) -> Dict[str, Any]:
        return self.read_json(self.models_path, {}) or {}

    def update_models(self, backend: str, info: Dict[str, Any], drop: Iterable[str] = ()) -> Dict[str, Any]:
        """把 info 合并进 models.json 里这个引擎的记录。drop 里的键先删掉（例如重新训练后，
        旧模型的挑选结果和语速校准已经不对了）。"""
        models = self.load_models()
        entry = models.get(backend, {})
        for key in drop:
            entry.pop(key, None)
        entry.update(info)
        models[backend] = entry
        self.write_json(self.models_path, models)
        return entry

    def load_lexicon(self) -> List[tuple]:
        """lexicon.txt：每行 `原文 => 读法`，用来纠正多音字、专业术语、英文缩写的读法。

        中文输入法打出来的 ＝＞、＝>、=＞、->、→、⇒ 和全角空格也都认。
        """
        pairs = []
        if not self.lexicon_path.exists():
            return pairs
        raw = self.lexicon_path.read_bytes()
        try:
            content = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = raw.decode("gb18030", errors="replace")  # 记事本另存为 ANSI 的情况
        for line in content.splitlines():
            line = normalize_lexicon_line(line)
            if not line or line.startswith("#") or "=>" not in line:
                continue
            src, dst = line.split("=>", 1)
            src, dst = src.strip(), dst.strip()
            if src:
                pairs.append((src, dst))
        return pairs


KEEP_FALSE_VALUES = ("0", "false", "False", "FALSE", "否", "n", "N", "no", "No", "x", "X", "×", "✘", "✗", "删", "删除",
                     "不", "不要", "不保留")
_ARROWS = ("＝＞", "＝>", "=＞", "⇒", "→", "->", "＞＞")


def normalize_lexicon_line(line: str) -> str:
    line = (line or "").replace("\u3000", " ").strip()
    if line.startswith("＃"):
        line = "#" + line[1:]
    for arrow in _ARROWS:
        line = line.replace(arrow, "=>")
    return line


def apply_text_edit(rec: Dict[str, Any], text: str) -> None:
    """片段文字被人改过：更新语言和语速；记下最初识别的文字（orig_text，校对表用蓝色显示改过的字）。

    "可能有错"的标记：改过的地方不再标红；没改到的红字留着（记下它们是针对哪段文字算的，显示时换算位置）；
    红字一处都不剩、也没有采用过的建议时去掉整个标记。"""
    from voicetwin.utils.textutil import detect_lang, syllable_count

    from voicetwin.data.review import lang_after_edit

    old = str(rec.get("text", "") or "")
    if text != old:  # 最初没有识别出文字（old 是空的）也记下：老师自己打的字要认得出来（标蓝、一键校正不动）
        rec.setdefault("orig_text", old)
    rec["text"] = text
    rec["lang"] = lang_after_edit(old, str(rec.get("lang") or ""), text) or detect_lang(text)
    if rec.get("voiced"):
        rec["rate"] = syllable_count(text) / max(rec["voiced"], 1e-3)
    auto = rec.get("suspect_auto")
    if isinstance(auto, dict) and old:  # 文字校正以前自动查错字的结果（再点一次文字校正时用）：也记下它是按哪段文字算的
        auto.setdefault("text", old)
    sus = rec.get("suspect")
    if isinstance(sus, dict) and old:
        sus.setdefault("text", old)
        from voicetwin.data.review import analyze

        info = analyze(rec)
        if not info["active"] and not info["undo"]:  # 采用了的建议留着记录：按钮一直是红的，也能撤销
            rec.pop("suspect", None)
    else:
        rec.pop("suspect", None)
    rec["text_edited"] = True


LEXICON_TEMPLATE = """# 读音纠正词典：每行一条，格式为  原文 => 实际朗读的文字
# 合成前会把讲稿中的"原文"替换成"读法"（字幕里仍显示原文）。
# 适合用来纠正：多音字、专业术语、英文缩写、你习惯的特殊读法。
# 例子（去掉行首的 # 即可生效）：
# SQL => sequel
# GPT => G P T
# 重庆 => 虫庆
# 行长 => 航长
# ≥ => 大于等于
"""
