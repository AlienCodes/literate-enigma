"""假的 indextts.infer_v2_5：参数签名照抄官方 commit d9e41aa，不加载模型。"""

import json
import math
import os
import struct
import wave


def _log(kind, data):
    path = os.environ.get("FAKE_INDEXTTS_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"kind": kind, **data}, ensure_ascii=False) + "\n")


class IndexTTS2:
    def __init__(
            self, cfg_path="checkpoints/config.yaml", model_dir="checkpoints", use_bf16=False, device=None,
            use_cuda_kernel=None, use_deepspeed=False, use_accel=False, use_torch_compile=False, use_qwen_emo=False
    ):
        if not os.path.isfile(cfg_path):
            raise FileNotFoundError(cfg_path)
        import torch

        self.low_vram = False
        if torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            self.low_vram = total < 10.0
        self._oom_left = 1 if os.environ.get("FAKE_INDEXTTS_OOM_ONCE") else 0
        _log("init", {"cfg_path": cfg_path, "model_dir": model_dir, "use_bf16": use_bf16, "device": device,
                      "use_cuda_kernel": use_cuda_kernel, "use_deepspeed": use_deepspeed,
                      "use_qwen_emo": use_qwen_emo, "low_vram": self.low_vram})

    def infer(self, spk_audio_prompt, text, output_path, lang,
              emo_audio_prompt=None, emo_alpha=1.0,
              emo_vector=None, use_emo_text=False, emo_text=None, use_random=False, interval_silence=200,
              verbose=False, max_text_tokens_per_segment=120, stream_return=False, more_segment_before=0,
              duration_factor=1.0, text_normalization=True, **generation_kwargs):
        _log("infer", {"spk_audio_prompt": spk_audio_prompt, "text": text, "output_path": output_path, "lang": lang,
                       "emo_audio_prompt": emo_audio_prompt, "emo_alpha": emo_alpha,
                       "interval_silence": interval_silence, "duration_factor": duration_factor,
                       "low_vram": self.low_vram, "generation_kwargs": generation_kwargs})
        if not os.path.isfile(spk_audio_prompt):
            raise FileNotFoundError(spk_audio_prompt)
        if self._oom_left and not self.low_vram and len(text) > 40:
            self._oom_left -= 1
            raise RuntimeError("CUDA out of memory. Tried to allocate 1.20 GiB")
        if os.environ.get("FAKE_INDEXTTS_NONE"):
            return None
        sr = 22050
        seconds = max(0.3, 0.12 * len(text)) * float(duration_factor)
        n = int(sr * seconds)
        with wave.open(output_path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 180 * i / sr)))
                                   for i in range(n)))
        return output_path
