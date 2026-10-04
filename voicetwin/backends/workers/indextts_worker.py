"""IndexTTS2.5（也能跑 IndexTTS2）worker：在 index-tts 仓库自己的 uv 环境中运行。

零样本克隆（不需要训练）。本文件不依赖 voicetwin 包。照着官方 indextts/infer_v2_5.py（commit d9e41aa）的真实接口写：
- 构造：IndexTTS2(cfg_path, model_dir, use_bf16, use_cuda_kernel=False, use_deepspeed=False, use_qwen_emo=False)。
  use_cuda_kernel 默认是 None（= 启动时去编译 BigVGAN 的 CUDA 扩展，Windows 上要 nvcc + MSVC，一般电脑上没有），
  所以一定要传 False；不加载 QwenEmotion（省大约 1 GB 显存，我们不用文字控制情绪）。
- 显卡小于 10 GB 时，官方会把超过 40 个字的句子在标点处切开、分开生成、中间插 200 毫秒静音（low_vram）。
  VoiceTwin 自己已经按句子切好、按老师的说话习惯放停顿，所以默认关掉这个切法（一句话一口气生成，语调连贯）；
  真的显存不够（CUDA out of memory）时这一句再用官方的切法重来一次，中间的静音用请求里给的 interval_silence。
- 输出：22050 Hz 16 位 wav；写完检查文件真的在、不是空的，不然报错（infer 在某些情况下返回 None、什么也不写）。
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import random
import sys
import traceback

#: duration_factor 的有效范围（官方 README：0.5~2.0，代码里没有限制，超出以后声音会变怪）
DURATION_MIN, DURATION_MAX = 0.5, 2.0


def _is_oom(exc: BaseException) -> bool:
    return "out of memory" in str(exc).lower() or type(exc).__name__ == "OutOfMemoryError"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--model_dir", default="checkpoints")
    ap.add_argument("--version", default="2.5")
    ap.add_argument("--half", default="true")
    ap.add_argument("--device", default="")
    ap.add_argument("--low_vram_split", default="oom")  # oom（默认：显存不够时才切）| always（照官方）| never
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
        cuda = torch.cuda.is_available() and not args.device.startswith("cpu")
        info = {"cuda": bool(cuda)}
        if cuda:
            try:
                props = torch.cuda.get_device_properties(0)
                info["gpu"] = props.name
                info["vram_gb"] = round(props.total_memory / 1024 ** 3, 1)
            except Exception:
                pass
        if args.version.startswith("2.5"):
            from indextts.infer_v2_5 import IndexTTS2

            # bf16 只在显卡支持时用（RTX 30 系列以后都支持；官方网页也是这么判断的）
            bf16 = bool(half and cuda and getattr(torch.cuda, "is_bf16_supported", lambda: False)())
            kw = {"cfg_path": cfg_path, "model_dir": model_dir, "use_bf16": bf16, "use_cuda_kernel": False,
                  "use_deepspeed": False}
            if "use_qwen_emo" in inspect.signature(IndexTTS2.__init__).parameters:
                kw["use_qwen_emo"] = False
            if args.device:
                kw["device"] = args.device
            tts = IndexTTS2(**kw)
            info["bf16"] = bf16
        else:
            from indextts.infer_v2 import IndexTTS2

            kw = {"cfg_path": cfg_path, "model_dir": model_dir, "use_fp16": half and cuda, "use_cuda_kernel": False,
                  "use_deepspeed": False}
            if "use_qwen_emo" in inspect.signature(IndexTTS2.__init__).parameters:
                kw["use_qwen_emo"] = False
            tts = IndexTTS2(**kw)
        low_vram = bool(getattr(tts, "low_vram", False))
        info["low_vram"] = low_vram
        if low_vram and args.low_vram_split != "always":
            tts.low_vram = False  # 一句话一口气生成；显存不够时下面再用官方的切法
        infer_params = set(inspect.signature(tts.infer).parameters)
    except Exception as exc:
        reply({"event": "error", "error": f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"})
        return

    reply({"event": "ready", "backend": "indextts", "version": args.version, **info})
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
            p = req.get("params") or {}
            out = req["out"]
            kwargs = {"spk_audio_prompt": req["ref_audio"], "text": req["text"], "output_path": out,
                      "verbose": False}
            if "lang" in infer_params:
                kwargs["lang"] = req.get("lang") or "ZH"
            if "duration_factor" in infer_params and p.get("duration_factor"):
                kwargs["duration_factor"] = min(DURATION_MAX, max(DURATION_MIN, float(p["duration_factor"])))
            if "interval_silence" in infer_params and p.get("interval_silence") is not None:
                kwargs["interval_silence"] = int(p["interval_silence"])
            for key in ("temperature", "top_p", "top_k", "num_beams", "repetition_penalty"):
                if p.get(key) is not None:
                    kwargs[key] = p[key]

            def run():
                random.seed(seed)
                np.random.seed(seed % (2 ** 32))
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(seed)
                if os.path.isfile(out):
                    os.remove(out)
                tts.infer(**kwargs)

            split = False
            try:
                run()
            except Exception as exc:
                if not (_is_oom(exc) and low_vram and args.low_vram_split == "oom"):
                    raise
                # 显存不够：清掉缓存，这一句用官方的低显存切法再来一次（在标点处切开，中间是精确的数字静音）
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                tts.low_vram = True
                try:
                    run()
                finally:
                    tts.low_vram = False
                split = True
            if not os.path.isfile(out) or os.path.getsize(out) <= 44:
                raise RuntimeError("IndexTTS 没有写出音频文件（可能是文字里没有能读的字）")
            reply({"id": rid, "ok": True, "out": out, "split": split})
        except Exception as exc:
            reply({"id": rid, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
            print(traceback.format_exc(), file=sys.stderr)


if __name__ == "__main__":
    main()
