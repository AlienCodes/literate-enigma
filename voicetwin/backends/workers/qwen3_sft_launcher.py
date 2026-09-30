"""启动 Qwen3-TTS 官方微调脚本 sft_12hz.py 的包装器。

官方脚本写死了 attn_implementation="flash_attention_2"，没装 flash-attn（例如 Windows）时会直接报错。
这里在没有 flash-attn 时自动改用 PyTorch 自带的 sdpa，其余逻辑完全不变。
用法：python qwen3_sft_launcher.py <sft_12hz.py 路径> [sft_12hz.py 的参数...]
"""

import os
import runpy
import sys


def main() -> None:
    script = os.path.abspath(sys.argv[1])
    sys.argv = [script] + sys.argv[2:]
    sys.path.insert(0, os.path.dirname(script))
    try:
        import flash_attn  # noqa: F401
    except Exception:
        from qwen_tts import Qwen3TTSModel

        original = Qwen3TTSModel.from_pretrained.__func__

        def patched(cls, path, **kwargs):
            if kwargs.get("attn_implementation") == "flash_attention_2":
                print("[voicetwin] 未安装 flash-attn，改用 sdpa 注意力", file=sys.stderr)
                kwargs["attn_implementation"] = "sdpa"
            return original(cls, path, **kwargs)

        Qwen3TTSModel.from_pretrained = classmethod(patched)
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
