"""P5 实测：程序里的搜索（synth/search.py）和打分的辅助部分，只用处理器、不用模型。

1. 挑参考录音：用老师 1004 句（母本修缮后、保留的）的文字当一个假的参考录音库（每句当一条，15 个视频轮流，
   原来挑参考的分数用固定种子的随机数），每句挑 3 条参考 + 每条 3 条辅助参考要多久；
   英文占 15% 以上的句子里，挑到的参考有没有一条英文也占 15% 以上（设计方案 §1.5 第 3 条）；
2. 搜索本身的开销（一般的显卡：每批 8 个、每句 64 个版本；假引擎直接写文件、假打分器不花时间）：每句多少秒；
3. 一边生成一边打分（假引擎每次请求 0.25 秒、假打分器每个版本 0.04 秒）：总时间和两样加起来的比；
4. 留下最好的 6 个版本（每个 5 秒、32 kHz，FLAC 无损）：存一次、读一次多少毫秒，占多少硬盘；
5. 中英文分开查错字的比对（最长公共子序列）：老师夹英文的句子每句多少微秒。
"""
import csv
import dataclasses
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from voicetwin.backends.base import SEED_STEP  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.eval import identical_judge as IJ  # noqa: E402
from voicetwin.eval.metrics import Score, _cjk_units, _lcs_len, _pinyin_fn  # noqa: E402
from voicetwin.project import Project  # noqa: E402
from voicetwin.style.twin_profile import en_share  # noqa: E402
from voicetwin.synth import engine as eng  # noqa: E402
from voicetwin.synth import search as S  # noqa: E402
from voicetwin.synth.script import ScriptSegment, tts_normalize  # noqa: E402
from voicetwin.utils.textutil import EN_WORD_RE, sentence_kind, syllable_count  # noqa: E402

rows = [r for r in csv.DictReader(open(ROOT / "research/文字校正/老师的母本/母本_修缮后.csv", encoding="utf-8-sig"))
        if r["keep"] == "1"]
texts = [tts_normalize(r["text"]) for r in rows]
rng = np.random.default_rng(20261003)

# ---------------------------------------------------------------------------- 1. 挑参考录音
bank = [{"id": f"c{k:04d}", "path": f"clips/c{k:04d}.wav", "text": t, "lang": "zh", "kind": sentence_kind(t),
         "syllables": syllable_count(t), "en_ratio": round(en_share(t), 4), "source": f"v{k % 15}",
         "dur": float(rng.uniform(3.2, 9.8)), "para_initial": bool(rng.random() < 0.1),
         "max_pause": float(rng.uniform(0.0, 1.2)), "base": float(rng.normal(3.0, 0.4))} for k, t in enumerate(texts)]
prior = S.prior_scores(bank)
t0 = time.perf_counter()
need_en = got_en = 0
for k, t in enumerate(texts):
    seg = ScriptSegment(text=t, display=t, lang="zh", kind=sentence_kind(t), index=k)
    refs = S.shortlist_refs(seg, bank, prior, 3)
    for r in refs:
        S.aux_set(r, bank, prior, 3)
    if en_share(t) >= 0.15:
        need_en += 1
        got_en += any(r["en_ratio"] >= 0.15 for r in refs)
dt = time.perf_counter() - t0
print(f"1. 挑参考录音：假的库 {len(bank)} 条，{len(texts)} 句每句挑 3 条参考 + 每条 3 条辅助参考，"
      f"平均每句 {dt / len(texts) * 1000:.1f} 毫秒")
print(f"   英文占 15% 以上的句子 {need_en} 句，挑到的参考里有英文也占 15% 以上的：{got_en} 句")


# ---------------------------------------------------------------------------- 2./3. 搜索的开销、一边生成一边打分
class Backend:
    name, display_name, supports_aux_refs, supports_batch, bcfg = "dummy", "测试", True, False, {}

    def __init__(self, delay=0.0):
        self.delay, self.calls, self.seconds = delay, 0, 0.0

    def model_id(self):
        return "fake"

    def speed_calibration(self):
        return {"zh": 1.0}

    def start(self):
        pass

    def synthesize_many(self, req, n, out_dir):
        t1 = time.perf_counter()
        self.calls += 1
        time.sleep(self.delay)
        out = []
        for j in range(n):
            x = (0.3 * np.sin(2 * np.pi * (120 + (req.seed + j * SEED_STEP) % 80) * np.arange(80000) / 16000))
            path = Path(out_dir) / f"r{self.calls}_{j}.wav"
            sf.write(str(path), x.astype(np.float32), 16000, subtype="PCM_16")
            out.append((path, j))
        self.seconds += time.perf_counter() - t1
        return out


class Scorer:
    def __init__(self, delay=0.0):
        self.delay, self.i, self.seconds, self.by = delay, 0, 0.0, {}

    def prepare(self, wav, sr):
        return None

    def quick(self, wav, sr, text, lang, mult=1.0):
        t1 = time.perf_counter()
        time.sleep(self.delay)
        self.i += 1
        self.by[id(wav)] = 0.01 * self.i
        self.seconds += time.perf_counter() - t1
        return IJ.QuickScore(total=0.01 * self.i, pct_raw=None, voiced=4.0, expected=None, dur_dev=None, gate_ok=True)

    def full(self, wav, sr, text, lang, mult=1.0, prepared=None, use_asr=True, cer=None):
        t1 = time.perf_counter()
        time.sleep(self.delay)
        self.seconds += time.perf_counter() - t1
        return Score(total=self.by.get(id(wav), 0.0), stage="full")

    def in_normal_range(self, s, lang, speed=1.0):
        return True

    def timbre_term(self, s):
        return 0.0

    def non_timbre(self, s):
        return s.total

    def resid_sd(self):
        return None


def narrator(tmp, backend, scorer, synth=None):
    cfg = load_config(overrides={"workspace": str(tmp), "backend": "dummy", "synth": synth or {}}, user_config=False)
    p = Project(cfg, "实测")
    p.root.mkdir(parents=True, exist_ok=True)
    refs = [{"id": e["id"], "path": e["path"], "text": e["text"], "lang": "zh", "kind": e["kind"],
             "source": e["source"], "duration": e["dur"], "score": e["base"]} for e in bank[:40]]
    p.write_json(p.references_path, refs)
    n = eng.Narrator(cfg, p, backend, quality="identical", tier="mid")
    pool = S.pool_from_refs(refs)
    n._identical = {"twin": {}, "bank": None, "pool": pool, "bank_sig": S.pool_signature(pool),
                    "prior": S.prior_scores(pool), "prior_version": "", "weights": {}, "weights_version": "default",
                    "block": {}, "profile_sig": "x"}
    n._scorer, n._judge, n.use_asr, n._started = scorer, None, False, True
    return n


with tempfile.TemporaryDirectory() as tmp:
    b, sc = Backend(), Scorer()
    n = narrator(Path(tmp) / "a", b, sc)
    times = []
    for k in range(5):
        seg = ScriptSegment(text=texts[k], display=texts[k], lang="zh", kind="statement", index=k)
        t1 = time.perf_counter()
        out = n._search_obj().run(seg, n._plan(seg))
        times.append(time.perf_counter() - t1)
    print(f"2. 搜索本身（每批 8 个、每句 {out.tries} 个版本、完整打分 {out.stats['full_scored']} 个）：每句 "
          f"{np.median(times):.2f} 秒（中位数，5 句；其中假引擎写文件 {b.seconds / 5:.2f} 秒）")
    b, sc = Backend(delay=0.25), Scorer(delay=0.04)
    n = narrator(Path(tmp) / "b", b, sc, synth={"tiers": {"identical": {"batch": 2, "min_candidates": 12,
                                                                         "max_candidates": 12}}})
    seg = ScriptSegment(text=texts[0], display=texts[0], lang="zh", kind="statement", index=0)
    t1 = time.perf_counter()
    out = n._search_obj().run(seg, n._plan(seg))
    wall = time.perf_counter() - t1
    print(f"3. 一边生成一边打分（{b.calls} 次请求 × 0.25 秒、{out.tries} 个版本各快速 + 完整打分 0.04 秒）：总共 "
          f"{wall:.2f} 秒；生成 {b.seconds:.2f} 秒 + 打分 {sc.seconds:.2f} 秒 = {b.seconds + sc.seconds:.2f} 秒"
          f"（{wall / (b.seconds + sc.seconds):.0%}）")

    # ------------------------------------------------------------------------ 4. 留下最好的 6 个
    folder = Path(tmp) / "c" / "x.cands"
    cands = []
    for k in range(6):
        x = (0.3 * np.sin(2 * np.pi * (150 + k) * np.arange(5 * 32000) / 32000)).astype(np.float32)
        x = np.round(x * 32768) / 32768
        c = S.SearchCand(wav=x.astype(np.float32), sr=32000, arm=S.Arm("r1", 0, 3), seed=k, req_seed=0, row=k,
                         req_no=0, req_n=6, speed=1.0, score=Score(total=1.0 - 0.1 * k, stage="full"),
                         embs={m: rng.standard_normal(192).astype(np.float32) for m in ("a", "b", "c")})
        cands.append(c)
    t1 = time.perf_counter()
    S.store_candidates(folder, cands, 6)
    t_store = time.perf_counter() - t1
    t1 = time.perf_counter()
    back = S.load_candidates(folder)
    t_load = time.perf_counter() - t1
    size = sum(p.stat().st_size for p in folder.iterdir())
    same = all(np.array_equal(a.wav, it["wav"]) for a, it in zip(cands, back))
    print(f"4. 留下 6 个版本（5 秒、32 kHz）：存 {t_store * 1000:.0f} 毫秒、读 {t_load * 1000:.0f} 毫秒，"
          f"一共 {size / 1024:.0f} KB；读回来的声音和存进去的{'一个数都不差' if same else '不一样'}")

# ---------------------------------------------------------------------------- 5. 中英文分开查错字的比对
pinyin = _pinyin_fn()
mixed = [t for t in texts if EN_WORD_RE.search(t)]
t0 = time.perf_counter()
for t in mixed:
    a = _cjk_units(t, pinyin)
    _lcs_len(a, a[1:] + ["x"])
    w = [x.lower() for x in EN_WORD_RE.findall(t)]
    _lcs_len(w, w[:-1])
dt = time.perf_counter() - t0
print(f"5. 中英文分开比对（{'用' if pinyin else '没有'} pypinyin）：夹英文的 {len(mixed)} 句，平均每句 "
      f"{dt / max(len(mixed), 1) * 1e6:.0f} 微秒")
