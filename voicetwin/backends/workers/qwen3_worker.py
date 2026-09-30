"""Qwen3-TTS worker：在 Qwen3-TTS 自己的 Python 环境中运行（pip install qwen-tts）。

两种模式：
- clone：Base 模型 + 参考音频（零样本克隆，3 秒即可）
- custom：你微调出来的模型（speaker=你的声音名），最像
本文件不依赖 voicetwin 包。
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import traceback


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--attn", default="auto")
    ap.add_argument("--mode", default="clone", choices=["clone", "custom"])
    ap.add_argument("--speaker", default="")
    args = ap.parse_args()

    proto = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
    os.dup2(2, 1)
    sys.stdout = sys.stderr

    def reply(obj):
        proto.write(json.dumps(obj, ensure_ascii=False) + "\n")
        proto.flush()

    try:
        import numpy as np
        import soundfile as sf
        import torch
        from qwen_tts import Qwen3TTSModel

        dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}.get(args.dtype, torch.bfloat16)
        device = args.device
        if device.startswith("cuda") and not torch.cuda.is_available():
            print("CUDA 不可用，改用 CPU（会很慢）", file=sys.stderr)
            device, dtype = "cpu", torch.float32
        attn = args.attn
        if attn == "auto":
            try:
                import flash_attn  # noqa: F401

                attn = "flash_attention_2" if device.startswith("cuda") and dtype != torch.float32 else "sdpa"
            except Exception:
                attn = "sdpa"
        model = Qwen3TTSModel.from_pretrained(args.model, device_map=device, dtype=dtype, attn_implementation=attn)
    except Exception as exc:
        reply({"event": "error", "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"})
        return

    prompts = {}
    reply({"event": "ready", "backend": "qwen3tts", "mode": args.mode, "attn": attn})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        rid = req.get("id")
        try:
            if req.get("cmd") == "shutdown":
                reply({"id": rid, "ok": True})
                break
            if req.get("cmd") == "ping":
                reply({"id": rid, "ok": True})
                continue
            seed = int(req.get("seed") or 0)
            random.seed(seed)
            np.random.seed(seed % (2 ** 32))
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            p = req.get("params") or {}
            gen = {"do_sample": True}
            for key in ("temperature", "top_p", "top_k", "repetition_penalty", "max_new_tokens"):
                if p.get(key) is not None:
                    gen[key] = p[key]
            language = req.get("language") or "Auto"
            if args.mode == "custom":
                wavs, sr = model.generate_custom_voice(text=req["text"], speaker=args.speaker, language=language,
                                                       instruct=p.get("instruct") or None, **gen)
            else:
                key = (req["ref_audio"], req.get("ref_text", ""))
                if key not in prompts:
                    prompts[key] = model.create_voice_clone_prompt(ref_audio=req["ref_audio"], ref_text=req.get("ref_text") or None,
                                                                   x_vector_only_mode=not bool(req.get("ref_text")))
                wavs, sr = model.generate_voice_clone(text=req["text"], language=language,
                                                      voice_clone_prompt=prompts[key], **gen)
            sf.write(req["out"], np.asarray(wavs[0], dtype=np.float32), int(sr))
            reply({"id": rid, "ok": True, "out": req["out"], "sr": int(sr)})
        except Exception as exc:
            reply({"id": rid, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
            print(traceback.format_exc(), file=sys.stderr)


if __name__ == "__main__":
    main()
