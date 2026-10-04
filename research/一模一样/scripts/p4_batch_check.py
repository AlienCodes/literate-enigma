"""P4 实测：程序里的 _batch_text / _split_wav（不是设计时的模拟脚本）。

1. 老师的 1004 句（母本修缮后、保留的，按生成时一样先 tts_normalize）复制 n 份（n = 2 / 4 / 8 / 12）：
   按官方切分规则算，正好切成 n 段、每段和单独生成时一样的有几句；
2. 几个很短的句子能不能同时生成；
3. 速度：_batch_text 每句多少微秒；_split_wav 切一次 12 个 × 5 秒（32 kHz）的回答多少毫秒。
只用处理器，不用模型。"""
import csv
import io
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from voicetwin.backends.gptsovits import _batch_text, _gsv_pre_seg, _split_wav  # noqa: E402
from voicetwin.synth.script import tts_normalize  # noqa: E402

rows = [r for r in csv.DictReader(open(ROOT / "research/文字校正/老师的母本/母本_修缮后.csv", encoding="utf-8-sig"))
        if r["keep"] == "1"]
texts = [tts_normalize(r["text"]) for r in rows]
print(f"老师的句子：{len(texts)} 句，最长 {max(len(t) for t in texts)} 个字")
for n in (2, 4, 8, 12):
    ok = 0
    for t in texts:
        bt = _batch_text(t, "zh", n)
        single = _gsv_pre_seg(t, "zh")
        if bt is not None and len(single) == 1 and _gsv_pre_seg(bt, "zh") == single * n:
            ok += 1
    print(f"复制 {n} 份：{ok}/{len(texts)} 句正好切成 {n} 段、每段和单独生成的一样")
for t, lang in (("好的。", "zh"), ("对。", "zh"), ("我们来看。", "zh"), ("Yes.", "en"), ("OK, let's go.", "en")):
    bt = _batch_text(t, lang, 4)
    print(f"  {t!r}：{'能同时生成' if bt else '只能一个一个生成'}（单独生成时引擎读的是 {_gsv_pre_seg(t, lang)}）")

t0 = time.perf_counter()
for _ in range(3):
    for t in texts:
        _batch_text(t, "zh", 12)
per = (time.perf_counter() - t0) / (3 * len(texts)) * 1e6
print(f"_batch_text（12 份）：平均每句 {per:.0f} 微秒")

rng = np.random.default_rng(0)
sr = 32000
frag = [(rng.standard_normal(5 * sr) * 3000).astype(np.int16) for _ in range(12)]
x = np.concatenate([np.concatenate([f, np.zeros(sr // 2, np.int16)]) for f in frag])
buf = io.BytesIO()
sf.write(buf, x, sr, format="WAV", subtype="PCM_16")
data = buf.getvalue()
times = []
for _ in range(10):
    t0 = time.perf_counter()
    pieces, _sr, why = _split_wav(data, 12, 0.5)
    times.append(time.perf_counter() - t0)
assert pieces is not None and len(pieces) == 12
print(f"_split_wav（12 个 × 5 秒，32 kHz，{len(data) / 1e6:.1f} MB）：中位数 {np.median(times) * 1000:.1f} 毫秒")
