"""训练前看一遍素材（只读，什么都不改）：只数实际有的东西，显示在「② 训练模型」页上。

设计方案 §1.1 A：去过杂音 / 去过背景音乐的素材文件、在没有停顿的地方硬切开的片段、末尾没有标点的句子、
夹着英文的句子和英文单词数、问句、标成「可能有错」的句子。所有数字都是从 manifest.jsonl 和 sources.json 里数出来的；
数不出来（文件读不了）时对应的项是 None，不写进说明。去过杂音的素材不会自动重新处理（只告诉老师）。"""

from __future__ import annotations

from typing import Any, Dict, List

from voicetwin.project import Project
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import count_cjk, en_words, ensure_final_punct_train, sentence_kind

log = get_logger("audit")


def material_audit(project: Project) -> Dict[str, Any]:
    """返回实测的计数 + lines（给老师看的几句话，只有真的有这种情况时才写）。"""
    from voicetwin.data.exporters import train_records

    out: Dict[str, Any] = {"lines": []}
    try:
        records = train_records(project, include_val=True)
    except Exception as exc:  # 读不了校对表：什么都不说（不能乱写）
        log.debug(f"素材检查读不了校对表：{exc}")
        return out
    train = [r for r in records if r.get("split", "train") == "train"]
    val = [r for r in records if r.get("split") == "val"]
    try:
        sources = project.read_json(project.sources_path, {}) or {}
    except Exception:
        sources = None
    out.update(train=len(train), val=len(val))
    if isinstance(sources, dict):
        used = {str(r.get("source") or "") for r in train}
        info = {sid: s for sid, s in sources.items() if isinstance(s, dict)}
        out["sources_denoised"] = sum(1 for s in info.values() if s.get("denoised"))
        out["sources_separated"] = sum(1 for s in info.values() if s.get("separated"))
        den_used = {sid for sid, s in info.items() if sid in used and s.get("denoised")}
        out["train_sources_denoised"] = len(den_used)
        out["train_clips_denoised"] = sum(1 for r in train if str(r.get("source") or "") in den_used)
    out["forced_cuts"] = sum(1 for r in train if int(r.get("forced_cuts") or 0) > 0)
    out["no_final_punct"] = sum(1 for r in train
                                if ensure_final_punct_train(str(r.get("text") or ""), str(r.get("lang") or "zh"))
                                != str(r.get("text") or "").strip())
    mixed = [r for r in train if count_cjk(str(r.get("text") or "")) and en_words(str(r.get("text") or ""))]
    out["en_lines"] = len(mixed)
    out["en_words"] = sum(len(en_words(str(r.get("text") or ""))) for r in mixed)
    out["questions_train"] = sum(1 for r in train if sentence_kind(str(r.get("text") or "")) == "question")
    out["questions_val"] = sum(1 for r in val if sentence_kind(str(r.get("text") or "")) == "question")
    out["suspects"] = sum(1 for r in train if r.get("suspect"))
    lines: List[str] = []
    if out.get("train_sources_denoised"):
        lines.append(f"有 {out['train_sources_denoised']} 个素材文件在准备时去过杂音（去杂音可能会被当成你的音色学进去）。")
    if out["forced_cuts"]:
        lines.append(f"有 {out['forced_cuts']} 条训练素材是在没有停顿的地方硬切开的。")
    out["lines"] = lines
    return out
