"""声音项目：一个"声音"（例如"我的讲课声音"）对应 workspace 下的一个目录。"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from voicetwin.config import Config, resolve_path

MANIFEST_FIELDS_CSV = ["id", "keep", "split", "lang", "duration", "text", "drop_reason", "audio"]


def _safe_voice_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("声音名称不能为空")
    if re.search(r"[\\/:*?\"<>|]", name):
        raise ValueError("声音名称不能包含 \\ / : * ? \" < > | 这些字符")
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
        if not Path(path).exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json(path: Path, data: Any) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

    # ------------------------------------------------------------------ manifest
    def load_manifest(self, only_kept: bool = False, split: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return []
        records = []
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        if only_kept:
            records = [r for r in records if r.get("keep", True)]
        if split:
            records = [r for r in records if r.get("split", "train") == split]
        return records

    def save_manifest(self, records: Iterable[Dict[str, Any]]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.manifest_path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tmp.replace(self.manifest_path)

    def export_csv(self, records: Optional[List[Dict[str, Any]]] = None) -> Path:
        """导出校对表（用 Excel/WPS 打开，改错字、把 keep 改成 0 可删掉片段）。"""
        records = records if records is not None else self.load_manifest()
        with open(self.csv_path, "w", encoding="utf-8-sig", newline="") as f:
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
        return self.csv_path

    def import_csv(self) -> Dict[str, int]:
        """读回校对表，把修改（文字、keep、语言）同步到 manifest。

        - 改了文字的片段：去掉"可能有错"的标记（suspect），重新算语速；
        - 「保留」那一格空着：保持原来的选择（不再当成"删掉"）。
        """
        from voicetwin.utils.textutil import clean_transcript

        if not self.csv_path.exists():
            raise FileNotFoundError(f"找不到校对表 {self.csv_path}")
        records = {r["id"]: r for r in self.load_manifest()}
        changed = {"text": 0, "keep": 0, "lang": 0}
        with open(self.csv_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rid = (row.get("id") or "").strip()
                if rid not in records:
                    continue
                rec = records[rid]
                text = clean_transcript(row.get("text") or "")
                if text and text != rec.get("text"):
                    apply_text_edit(rec, text)
                    changed["text"] += 1
                raw_keep = str(row.get("keep") if row.get("keep") is not None else "").strip()
                if raw_keep:
                    keep = raw_keep not in KEEP_FALSE_VALUES
                    if keep != rec.get("keep", True):
                        rec["keep"] = keep
                        rec["manual_keep"] = keep
                        if not keep:
                            rec["drop_reason"] = rec.get("drop_reason") or "手动删除"
                        changed["keep"] += 1
                lang = (row.get("lang") or "").strip().lower()
                if lang in ("zh", "en") and lang != rec.get("lang"):
                    rec["lang"] = lang
                    changed["lang"] += 1
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
    """片段文字被人改过：更新语言和语速，去掉"可能有错"的标记（它是针对旧文字的）。"""
    from voicetwin.utils.textutil import detect_lang, syllable_count

    rec["text"] = text
    rec["lang"] = detect_lang(text)
    if rec.get("voiced"):
        rec["rate"] = syllable_count(text) / max(rec["voiced"], 1e-3)
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
