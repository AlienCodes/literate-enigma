"""把准备好的素材导出成各训练引擎需要的格式。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from voicetwin.project import Project
from voicetwin.utils.audio import load_audio, save_audio
from voicetwin.utils.textutil import ensure_final_punct


def train_records(project: Project, include_val: bool = False) -> List[Dict[str, Any]]:
    recs = [r for r in project.load_manifest(only_kept=True) if r.get("text")]
    if not include_val:
        recs = [r for r in recs if r.get("split", "train") == "train"]
    return recs


def export_gptsovits(project: Project, speaker: str, include_val: bool = False) -> Dict[str, Any]:
    """GPT-SoVITS 训练列表：`音频文件名|说话人|语言|文字`，音频统一放在 clips/ 目录。"""
    out_dir = project.exports_dir / "gptsovits"
    out_dir.mkdir(parents=True, exist_ok=True)
    recs = train_records(project, include_val)
    if not recs:
        raise RuntimeError("没有可用于训练的片段，请先运行素材准备并检查 transcripts.csv。")
    lines = []
    for r in recs:
        wav = project.abspath(r["path"])
        text = ensure_final_punct(r["text"].replace("|", " "), r["lang"])
        lines.append(f"{wav.name}|{speaker}|{r['lang']}|{text}")
    list_path = out_dir / "train.list"
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"list": list_path, "wav_dir": project.clips_dir, "count": len(lines),
            "minutes": round(sum(r["duration"] for r in recs) / 60.0, 1)}


def export_qwen3(project: Project, ref_wav: Path, include_val: bool = False) -> Dict[str, Any]:
    """Qwen3-TTS 微调数据：24kHz 音频 + JSONL（audio / text / ref_audio）。"""
    out_dir = project.exports_dir / "qwen3"
    wav_dir = out_dir / "wav24k"
    wav_dir.mkdir(parents=True, exist_ok=True)
    recs = train_records(project, include_val)
    if not recs:
        raise RuntimeError("没有可用于训练的片段，请先运行素材准备并检查 transcripts.csv。")
    ref_wav24, sr = load_audio(ref_wav, sr=24000)
    ref24 = save_audio(out_dir / "ref_24k.wav", ref_wav24, sr)
    jsonl = out_dir / "train_raw.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in recs:
            dst = wav_dir / (Path(r["path"]).stem + ".wav")
            if not dst.exists():
                wav, sr = load_audio(project.abspath(r["path"]), sr=24000)
                save_audio(dst, wav, sr)
            f.write(json.dumps({"audio": str(dst.resolve()), "text": ensure_final_punct(r["text"], r["lang"]),
                                "ref_audio": str(ref24.resolve())}, ensure_ascii=False) + "\n")
    return {"jsonl": jsonl, "ref": ref24, "count": len(recs)}


def validation_items(project: Project, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    recs = [r for r in project.load_manifest(only_kept=True) if r.get("split") == "val" and r.get("text")]
    return recs[:limit] if limit else recs
