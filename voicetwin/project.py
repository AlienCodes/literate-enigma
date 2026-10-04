"""声音项目：一个"声音"（例如"我的讲课声音"）对应 workspace 下的一个目录。"""

from __future__ import annotations

import csv
import io
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from voicetwin.config import Config, resolve_path

from voicetwin.utils.log import get_logger

log = get_logger("project")

MANIFEST_FIELDS_CSV = ["id", "keep", "split", "lang", "duration", "text", "drop_reason", "audio"]
_WARNED_EMPTY: set = set()  # 已经说过「manifest.jsonl 空了 / 坏了 / 不见了」的声音（每个只说一次）


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
        self.manifest_lost_path = self.root / "manifest.lost.json"  # 读的时候发现 manifest 丢了：写 CSV 以前先另存
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
            self._note_lost_manifest("不见了")  # transcripts.csv 里还有句子时才算（新建的声音两个都没有）
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
            self._note_lost_manifest(f"有 {bad} 行坏了")
        elif not records:
            self._note_lost_manifest("是空的")
        if only_kept:  # 校对表里删除的一定不算（delete_clip 也会把 keep 设成 False，这里再保险一次）
            records = [r for r in records if r.get("keep", True) and not r.get("deleted")]
        if split:
            records = [r for r in records if r.get("split", "train") == split]
        return records

    def _note_lost_manifest(self, why: str) -> None:
        """manifest.jsonl 空了 / 坏了 / 不见了：多半是保存的时候断电了（以前一声不吭，网页只说「还没有片段」）。
        transcripts.csv 里还有句子（上次保存的文字，常常是最后一份）：记下来（manifest.lost.json），下一次写 transcripts.csv
        以前一定先另存一份（_keep_old_csv）——照着网页说的再点「开始准备素材」，视频可能重新切一遍，片段编号和原来一模一样，
        只比编号、比文字都不一定看得出来少了什么（例如老师只删了几句）。
        黑色窗口 / 记录里每个声音只说一次（这个函数一直被调用）。"""
        noted = False
        try:
            noted = self.manifest_lost_path.exists()
            if not noted and self.csv_path.exists() and self._csv_texts() != {}:  # 有句子，或者有内容却读不出来
                from voicetwin.utils import atomic

                atomic.write_text(self.manifest_lost_path, json.dumps(
                    {"why": f"manifest.jsonl {why}", "time": time.strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False))
                noted = True
        except OSError as exc:  # 记不下来：只靠写的时候比句子和文字（_keep_old_csv 的另外两条）
            log.warning(f"没能记下「校对表 manifest.jsonl {why}」（{exc}）")
        key = str(self.manifest_path)
        if key in _WARNED_EMPTY:
            return
        if noted:
            _WARNED_EMPTY.add(key)
            log.warning(f"校对表 manifest.jsonl {why}：多半是保存的时候电脑断电或死机了。上次保存的文字在 {self.csv_path.name} "
                        f"里还有一份：下次写 {self.csv_path.name} 以前，程序会先把它另存成「transcripts_备份_日期_时间.csv」"
                        "（在这个声音的文件夹里，原来改好的文字在里面）")
            return
        if why == "不见了":
            return
        try:
            has_clips = any(self.clips_dir.glob("*.wav"))
        except OSError:
            has_clips = False
        if has_clips:
            _WARNED_EMPTY.add(key)
            log.warning(f"校对表 manifest.jsonl {why}，可是切好的片段还在（{self.clips_dir}）：多半是保存的时候电脑断电或死机了")

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
        try:  # 发现 manifest 丢了以后的第一次已经写完（要另存的上面已经另存了）
            self.manifest_lost_path.unlink()
        except OSError:
            pass
        return self.csv_path

    def _keep_old_csv(self, records: List[Dict[str, Any]]) -> Optional[Path]:
        """写 transcripts.csv 以前：里面有这次要写的表里没有的东西，先把它另存一份「transcripts_备份_日期_时间.csv」再写——
        manifest.jsonl 断电坏了以后，它常常是最后一份老师改好的文字（以前照着网页说的再点「开始准备素材」，它也被冲掉了）。
        下面任何一条就另存：
        1. 读校对表的时候发现 manifest.jsonl 空了 / 坏了 / 不见了（manifest.lost.json，_note_lost_manifest 记的）；
        2. 上次写的句子这次少了（正常只会多不会少，删除也只是标成紫色）；
        3. 上次写的一句有字，这次换成了别的字，这一条却没有被人改过（没有 text_edited）：程序自己从来不改有字的句子（识别只填
           没字的），多半是 manifest 丢了以后视频重新切了一遍——片段编号和原来一模一样，只比编号看不出来，字幕 / 识别的字会把
           老师改好的字冲掉；
        4. 上次写了什么读不出来（见下）。
        「上次写的」看 transcripts.exported.json；它坏了 / 没有（和 manifest.jsonl 同一次保存写的，断电时常常一起坏）就直接读
        transcripts.csv。transcripts.csv 本身是空的 / 一堆 0 就没有什么可留的；和已有的一份备份一模一样也不再另存（例如被 Excel
        开着、这次又没写成）。另存不了就报错（OSError），这次不写 transcripts.csv。返回备份的位置（不用另存返回 None）。"""
        from voicetwin.utils import atomic

        try:
            data = self.csv_path.read_bytes()
        except OSError:
            return None
        if not data.strip(b"\x00 \r\n\t"):
            return None
        why = []
        if self.manifest_lost_path.exists():
            why.append("读校对表的时候发现 manifest.jsonl 空了 / 坏了 / 不见了")
        snap = self.read_json(self.csv_snapshot_path, None)
        if isinstance(snap, dict):
            last: Optional[Dict[str, str]] = {str(k): str(v[0] if isinstance(v, list) and v else "") for k, v in snap.items()}
        else:
            last = self._csv_texts(data)
        if last is None:
            why.append("上次写的内容读不出来")
        else:
            now = {str(r.get("id")): r for r in records}
            lost = sum(1 for k in last if k not in now)
            if lost:
                why.append(f"这次比上次少了 {lost} 句")
            changed = sum(1 for k, t in last.items() if k in now and t.strip() and not now[k].get("text_edited")
                          and str(now[k].get("text", "") or "") != t)
            if changed:
                why.append(f"有 {changed} 句的字要换成没人改过的字（多半是视频重新切了一遍）")
        if not why:
            return None
        for old in self.root.glob("transcripts_备份_*.csv"):  # 一模一样的已经有了
            try:
                if old.stat().st_size == len(data) and old.read_bytes() == data:
                    return old
            except OSError:
                continue
        stamp = time.strftime("%Y%m%d_%H%M%S")
        dest = self.root / f"transcripts_备份_{stamp}.csv"
        k = 2
        while dest.exists():
            dest = self.root / f"transcripts_备份_{stamp}_{k}.csv"
            k += 1
        tmp = atomic.tmp_for(dest)
        try:
            tmp.write_bytes(data)
            atomic.finish(tmp, dest)
        except OSError as exc:
            try:
                tmp.unlink()
            except OSError:
                pass
            # 另存不了就先不写 transcripts.csv：写了，上次保存的文字就一份都没有了（校对表 manifest.jsonl 已经存好了，
            # 下次保存时再试）
            log.warning(f"没能另存 transcripts.csv 的备份（{exc}），这次先不写 transcripts.csv，免得上次保存的文字一份都不剩")
            raise
        log.warning(f"{'；'.join(why)}：上次的 transcripts.csv 另存成了 {dest.name}（在 {self.root}），里面是上次保存的文字"
                    "（包括改好的）。需要的话用 Excel / WPS 打开它，把文字抄回网页上的校对表")
        return dest

    def _csv_texts(self, data: Optional[bytes] = None) -> Optional[Dict[str, str]]:
        """transcripts.csv 里的句子（编号 → 文字）。没有 / 空的 / 一堆 0 / 只有表头 → {}；有内容却读不出来（断电留下的乱码、
        Excel 另存成了别的样子、表头被改了）→ None。"""
        if data is None:
            try:
                data = self.csv_path.read_bytes()
            except FileNotFoundError:
                return {}
        if not data.strip(b"\x00 \r\n\t"):
            return {}
        for enc in ("utf-8-sig", "gb18030"):  # Excel「另存为」CSV 默认是 GBK
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
        try:
            reader = csv.DictReader(io.StringIO(text, newline=""))
            rows = list(reader)
        except csv.Error:
            return None
        if "id" not in (reader.fieldnames or []):
            return None
        return {str(r.get("id") or "").strip(): str(r.get("text") or "") for r in rows if str(r.get("id") or "").strip()}

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
