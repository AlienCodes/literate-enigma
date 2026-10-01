"""生成"陌生人声纹库" voicetwin/eval/sv_cohort.npz（开发用，用户不需要运行）。

    python scripts/build_sv_cohort.py --manifest cohort.json --models D:/VoiceTwin/models/sv

cohort.json：[{"speaker": "唯一名字", "lang": "zh" | "en", "files": ["a.wav", ...]}, ...]，每人一条，
同一个人的几段录音会拼起来（只取人声部分）再算声纹。库里只保存声纹向量（每人一个），不保存任何声音。

用到的公开数据（都允许这样使用）：
- Google Speech Commands v0.02（CC-BY 4.0）：400 位英语说话人；
- 各开源语音项目（3D-Speaker、sherpa-onnx、CosyVoice、IndexTTS、MaskGCT 等）公开的中文示例录音。

处理方式和打分时完全一样（同一个人声检测、同一个前端、同一个模型），这样 AS-norm 和「0%」的标准才对得上。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from voicetwin.eval import sv_models
    from voicetwin.eval.speaker import AS_NORM_TOPK, COHORT_FILE, OnnxSVEncoder, cohort_self_stats
    from voicetwin.eval.sv_frontend import SileroVAD
    from voicetwin.utils.audio import load_audio

    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--models", required=True, help="放 ONNX 模型的文件夹")
    ap.add_argument("--keys", default=",".join(sv_models.MODELS), help="要生成哪些模型的库（逗号分隔）")
    ap.add_argument("--out", default=str(COHORT_FILE))
    ap.add_argument("--max-seconds", type=float, default=12.0, help="每人最多用多少秒人声")
    ap.add_argument("--dedup", type=float, default=0.80, help="两个人的声纹相似度高于这个值就当成同一个人")
    args = ap.parse_args()

    people = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    model_dir = Path(args.models)
    vad = SileroVAD(model_dir / sv_models.VAD_MODEL.file)
    speech = []
    for p in people:
        parts, total = [], 0
        for f in p["files"]:
            wav, _ = load_audio(f, sr=16000)
            s = vad.speech_only(wav)
            parts.append(s)
            total += s.size
            if total >= args.max_seconds * 16000:
                break
        speech.append(np.concatenate(parts)[: int(args.max_seconds * 16000)])
    print(f"{len(speech)} 人，平均人声 {np.mean([s.size for s in speech]) / 16000:.1f} 秒")
    zh = np.array([p.get("lang") == "zh" for p in people])
    embs = {}
    for key in [k.strip() for k in args.keys.split(",") if k.strip()]:
        spec = sv_models.MODELS[key]
        path = model_dir / spec.file
        if not path.exists():
            print(f"跳过 {key}：没有 {path}")
            continue
        enc = OnnxSVEncoder(spec, path, vad)
        embs[key] = np.stack([enc.embed_prepared(s) for s in speech]).astype(np.float32)
        print(f"{key}: {embs[key].shape}")
    # 同一个人出现在两个项目的示例里（几个模型平均的余弦相似度很高）：只留一个，免得"陌生人"里有重复的人
    mean_sim = np.mean([e @ e.T for e in embs.values()], axis=0)
    keep = np.ones(len(people), dtype=bool)
    for i in range(len(people)):
        if keep[i] and np.any(mean_sim[i, :i][keep[:i]] > args.dedup):
            keep[i] = False
    print(f"去掉重复的人 {int((~keep).sum())} 个：" + "、".join(p["speaker"] for p, k in zip(people, keep) if not k))
    out = {}
    for key, e in embs.items():
        unit = e[keep].astype(np.float16).astype(np.float32)
        unit /= np.linalg.norm(unit, axis=1, keepdims=True)
        mu, sd = cohort_self_stats(unit, AS_NORM_TOPK)
        out[f"{key}__emb"] = e[keep].astype(np.float16)
        out[f"{key}__mu"] = mu
        out[f"{key}__sd"] = sd
        out[f"{key}__zh"] = zh[keep]
    np.savez_compressed(args.out, **out)
    print(f"已写入 {args.out}（{Path(args.out).stat().st_size / 1024:.0f} KB）")


if __name__ == "__main__":
    main()
