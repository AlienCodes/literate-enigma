"""重算说话习惯（改一句文字并保存）时接着用「前后两句的音色变化」要多花多少时间，按老师那么大的素材
（校对表 1004 段、参考录音库约 900 条、3 个声纹模型）合成假数据量：

1. 参考录音库没变：读 refs_bank.json + 算 timbre_key，接着用上次的（平常都是这一条）；
2. 库里前后两段的关系变了 / twin_profile.json 没了：从 cache/bank_emb.npz 读缓存的声纹重新算（很少见）。

用法：PYTHONPATH=. python research/一模一样/scripts/time_timbre_keep.py"""
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from conftest import make_cfg  # noqa: E402
from voicetwin.data import references as R  # noqa: E402
from voicetwin.project import Project  # noqa: E402
from voicetwin.style import twin_profile as tp  # noqa: E402

ws = Path(tempfile.mkdtemp())
p = Project(make_cfg(ws), "大")
p.ensure()
recs, entries = [], []
text = "今天我们来学习Python里面的列表推导式，它可以让代码更简洁。"
for i in range(1004):
    sid = f"第{i // 60 + 1}课_abcdef"
    path = p.clips_dir / f"{sid}_{i:04d}.wav"
    path.write_bytes(b"x" * 100)  # 只用来算「文件大小 + 修改时间」
    recs.append({"id": f"{sid}_{i:04d}", "source": sid, "start": (i % 60) * 7.0, "end": (i % 60) * 7.0 + 6.2,
                 "text": text, "path": p.relpath(path), "keep": True, "split": "train"})
    if i % 10:
        entries.append({"id": recs[-1]["id"], "path": recs[-1]["path"], "wav": "x", "text": text, "lang": "zh",
                        "kind": "statement", "syllables": 30, "en_ratio": 0.2, "rate": 4.5, "dur": 6.1,
                        "trim": [1000, 98000, 16000], "source": sid, "start": recs[-1]["start"], "gap_before": 0.6,
                        "para_initial": False, "max_pause": 0.3, "base": 3.1, "f0_med": 151.2, "self_pct": 97.3})
models = ["a", "b", "c"]
bank = {"version": 1, "bank_sig": R.bank_signature(entries), "judge_sig": "abc", "judge_models": models,
        "n": len(entries), "seconds": [3.2, 9.8], "entries": entries}
R.bank_path(p).write_text(tp.dumps(bank), encoding="utf-8")
rng = np.random.default_rng(0)
cache = {}
for e in entries:
    base = R._emb_base(p, e)
    for m, dim in zip(models, (192, 256, 512)):
        cache[f"{base}|{m}"] = rng.normal(size=dim).astype(np.float32)
    cache[f"{base}|{R._done_tag(models)}"] = np.asarray([5.5])
R._save_bank_emb(p, cache)
print(f"refs_bank.json {R.bank_path(p).stat().st_size // 1024} KB（{len(entries)} 条）；校对表 {len(recs)} 段；"
      f"bank_emb.npz {(p.cache_dir / R.BANK_EMB_FILE).stat().st_size / 1e6:.1f} MB（{len(models)} 个模型）")

t1, t2 = [], []
for _ in range(5):
    t = time.perf_counter()
    b = R.load_reference_bank(p)
    tp.timbre_key(b, recs)
    t1.append(time.perf_counter() - t)
    t = time.perf_counter()
    embs = R.cached_bank_embeddings(p, b)
    tp._timbre_stats(recs, embs, "abc", "k")
    t2.append(time.perf_counter() - t)
print("1. 库没变（读库 + 算 key，接着用）：" + " / ".join(f"{x * 1000:.0f}" for x in t1) + " 毫秒")
print("2. 用缓存的声纹重新算：" + " / ".join(f"{x * 1000:.0f}" for x in t2) + " 毫秒")

import shutil  # noqa: E402

shutil.rmtree(ws, ignore_errors=True)
