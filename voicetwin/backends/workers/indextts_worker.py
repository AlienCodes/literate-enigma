"""IndexTTS2 / IndexTTS2.5 worker：在 index-tts 仓库自己的 uv 环境中运行。

零样本克隆（不需要训练），支持情绪参考和时长控制。本文件不依赖 voicetwin 包。
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import random
import sys
import traceback


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--model_dir", default="checkpoints")
    ap.add_argument("--version", default="2.5")
    ap.add_argument("--half", default="true")
    args = ap.parse_args()

    proto = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
    os.dup2(2, 1)
    sys.stdout = sys.stderr

    def reply(obj):
        proto.write(json.dumps(obj, ensure_ascii=False) + "\n")
        proto.flush()

    try:
        os.chdir(args.root)
        sys.path.insert(0, args.root)
        import numpy as np
        import torch

        model_dir = args.model_dir if os.path.isabs(args.model_dir) else os.path.join(args.root, args.model_dir)
        cfg_path = os.path.join(model_dir, "config.yaml")
        half = args.half.lower() in ("1", "true", "yes")
        if args.version.startswith("2.5"):
            from indextts.infer_v2_5 import IndexTTS2

            tts = IndexTTS2(cfg_path=cfg_path, model_dir=model_dir, use_bf16=half)
        else:
            from indextts.infer_v2 import IndexTTS2

            tts = IndexTTS2(cfg_path=cfg_path, model_dir=model_dir, use_fp16=half, use_cuda_kernel=False,
                            use_deepspeed=False)
        infer_params = set(inspect.signature(tts.infer).parameters)
    except Exception as exc:
        reply({"event": "error", "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"})
        return

    reply({"event": "ready", "backend": "indextts", "version": args.version})
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
            kwargs = {"spk_audio_prompt": req["ref_audio"], "text": req["text"], "output_path": req["out"],
                      "verbose": False}
            if "lang" in infer_params:
                kwargs["lang"] = req.get("lang") or "ZH"
            if p.get("emo_audio"):
                kwargs["emo_audio_prompt"] = p["emo_audio"]
                kwargs["emo_alpha"] = float(p.get("emo_alpha", 0.6))
            if "duration_factor" in infer_params and p.get("duration_factor"):
                kwargs["duration_factor"] = float(p["duration_factor"])
            for key in ("temperature", "top_p", "top_k"):
                if p.get(key) is not None:
                    kwargs[key] = p[key]
            tts.infer(**kwargs)
            reply({"id": rid, "ok": True, "out": req["out"]})
        except Exception as exc:
            reply({"id": rid, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
            print(traceback.format_exc(), file=sys.stderr)


if __name__ == "__main__":
    main()
