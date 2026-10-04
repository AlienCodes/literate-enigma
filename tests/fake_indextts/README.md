# 测试用的假 IndexTTS（不是真的模型）

`indextts/infer_v2_5.py` 的 `IndexTTS2` 构造参数和 `infer(...)` 的参数**一个字不差地照抄官方**
（https://github.com/index-tts/index-tts ，commit d9e41aa，2026-09-30），这样传错参数名测试就会失败。
它不加载任何模型，只把收到的参数记进 `FAKE_INDEXTTS_LOG`（每行一个 JSON），再写一段 22050 Hz 的正弦波 wav。

`torch/` 是最小的假 torch（CI 里没有装 torch），只有 worker 用到的几个函数；用环境变量模拟有没有显卡：
`FAKE_TORCH_CUDA=1`、`FAKE_TORCH_VRAM_GB=8`。`FAKE_INDEXTTS_OOM_ONCE=1`：关掉低显存切分时第一句超过 40 个字的话报一次显存不够。
`FAKE_INDEXTTS_NONE=1`：infer 什么也不写、返回 None（官方在某些情况下会这样）。
