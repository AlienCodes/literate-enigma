"""「一模一样」P6 拼接的实测（开发机，只用处理器，合成的声音，不是老师的数据）。

1. 整篇再挑一遍（Viterbi）：300 句 × 每句 6 个版本，动态规划本身用多久（设计方案里实测 3 毫秒的那一步）；
   读一句留下来的版本的记录和声纹（store_items，不读声音）用多久。
2. 停顿量了再改：40 句测试引擎的声音（底噪约 −54 dB），目标按她的分布随机取；改 0 / 1 / 2 遍以后量出来的停顿和目标差多少，
   句子起点放不放在 10 毫秒的格子上各量一次（说明为什么要放在格子上）；10 分钟的讲课音频拼一次 + 量一次用多久。
3. 量停顿的逐帧电平：整个算和分段算（frame_rms_db_chunked）各用多少内存、多少时间，结果差多少。
4. 每句音量：一句 +6 dB 一句 −6 dB 的合成声音，调完以后句子之间的音量差、整篇响度和目标差多少。
5. 切首尾：80 毫秒的指数衰减尾音，以前的切法 / 「一模一样」的切法各留下多少毫秒；只有嘶嘶声时切完剩多少。

运行：python research/一模一样/scripts/p6_assembly_check.py（结果写到旁边的 p6_assembly_check_结果.txt）
"""

from __future__ import annotations

import json
import random
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import numpy as np  # noqa: E402

from voicetwin.backends.workers.dummy_worker import synth_speech  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.project import Project  # noqa: E402
from voicetwin.synth import engine as eng  # noqa: E402
from voicetwin.synth import search as S  # noqa: E402
from voicetwin.synth.script import ScriptSegment  # noqa: E402
from voicetwin.utils.audio import frame_rms_db, frame_rms_db_chunked, measure_lufs, speech_level_db  # noqa: E402

OUT = Path(__file__).with_name("p6_assembly_check_结果.txt")
LINES = []


def say(text: str = "") -> None:
    print(text)
    LINES.append(text)


class _Backend:
    name, display_name, supports_aux_refs, supports_batch, bcfg = "dummy", "测试", False, False, {}
    release_gpu_callback = None

    def model_id(self):
        return "m"

    def speed_calibration(self):
        return {"zh": 1.0}


def narrator(tmp: Path) -> eng.Narrator:
    cfg = load_config(overrides={"workspace": str(tmp / "ws"), "backend": "dummy", "speaker_encoder": "mfcc"},
                      user_config=False)
    project = Project(cfg, "实测")
    project.root.mkdir(parents=True, exist_ok=True)
    project.references_path.write_text("[]", encoding="utf-8")
    n = eng.Narrator(cfg, project, _Backend(), quality="identical", tier="none")
    n._identical = {"twin": {}, "pool": [], "bank_sig": "", "prior": {}, "prior_version": "", "weights": {},
                    "weights_version": "default", "block": {}, "profile_sig": "x"}
    n.profile = {"loudness": {"source_lufs": -20.0}}
    return n


def seg(i: int, kind: str) -> ScriptSegment:
    return ScriptSegment(text=f"第{i}句", display=f"第{i}句", lang="zh", kind="statement", index=i, pause_after=kind)


def check_dp(n: eng.Narrator) -> None:
    say("## 1. 整篇再挑一遍（Viterbi）")
    rng = np.random.default_rng(0)
    stats = {"f0": (0.0, 1.0), "rate": (0.0, 0.1)}
    states = [[{"total": float(rng.normal(1.0, 0.05)), "f0": float(150 * 2 ** rng.normal(0, 1 / 12)),
                "rate": float(rng.normal(4.5, 0.3)), "emb": {}, "current": k == 0} for k in range(6)]
              for _ in range(300)]
    t0 = time.perf_counter()
    acc = [st["total"] for st in states[0]]
    for i in range(1, len(states)):
        acc = [max(acc[j] - n._edge_cost(a, b, stats) for j, a in enumerate(states[i - 1])) + b["total"]
               for b in states[i]]
    dt = time.perf_counter() - t0
    say(f"300 句 × 6 个版本（音调 + 语速两项）：{dt * 1000:.1f} 毫秒")
    # 读一句留下来的版本的记录和声纹
    folder = n.project.cache_dir / "segments" / "aa" / "aa.cands"
    cands = []
    for k in range(6):
        wav = synth_speech("测试一句话的声音", sr=16000, seed=k, noise=0.0)
        c = S.SearchCand(wav=wav, sr=16000, arm=S.Arm("r1", 0, 0), seed=k, req_seed=k, row=0, req_no=0, req_n=1,
                         speed=1.0)
        c.awav, c.empty = n._analysis_pair(wav, 16000)
        c.embs = {"m1": rng.normal(size=192).astype(np.float32), "m2": rng.normal(size=512).astype(np.float32)}
        from voicetwin.eval.metrics import Score

        c.score = Score(total=1.0, rate=4.5)
        cands.append(c)
    S.store_candidates(folder, cands, 6)  # 第一次：librosa 要准备一下（程序里只有第一次慢）
    t0 = time.perf_counter()
    S.store_candidates(folder, cands, 6)
    t_store = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(20):
        S.store_items(folder)
    t_read = (time.perf_counter() - t0) / 20
    say(f"存 6 个版本（含每个版本量音高）：{t_store * 1000:.0f} 毫秒；只读记录和声纹（不读声音）：{t_read * 1000:.1f} 毫秒")
    say()


def lecture(n_sent: int, seed: int = 1):
    out = []
    for i in range(n_sent):
        w = synth_speech("今天我们来学习这个例子，大家注意听这一句话" if i % 3 else "好的我们继续往下看",
                         sr=32000, seed=seed * 1000 + i)  # 自带约 −54 dB 的底噪
        out.append(eng.trim_edges(w, 32000, tail_pad_ms=30.0, **eng.ID_TRIM))
    return out


def check_fit(n: eng.Narrator) -> None:
    say("## 2. 停顿量了再改")
    sr = 32000
    wavs = lecture(40)
    kinds = ["clause" if i % 3 != 2 else "sentence" for i in range(40)]
    results = [eng.SegmentResult(seg(i, k), w, sr, {}, "r", False, i) for i, (w, k) in enumerate(zip(wavs, kinds))]
    rnd = random.Random(7)
    targets = [rnd.uniform(0.17, 0.23) if k == "clause" else rnd.uniform(1.0, 1.5) for k in kinds]
    n._pause = lambda s, i: targets[i]  # 和真的一样：拼的时候先按目标放，再量、再改
    pieces = [(w, sr) for w in wavs]
    for snap in (False, True):
        for passes in (0, 1, 2):
            layout = n._layout(results)
            if passes:
                old_passes = eng.FIT_PASSES
                eng.FIT_PASSES = passes
                try:
                    if snap:
                        layout, _ = n._fit_pauses(layout, pieces, sr)
                    else:
                        layout = _fit_no_snap(n, layout, pieces, sr, passes)
                finally:
                    eng.FIT_PASSES = old_passes
            gaps = n._measure_gaps(n._render(layout, pieces, sr), sr, layout)
            err = np.array([abs(g - t) for g, t in zip(gaps, n._pause_targets) if g is not None and t is not None])
            say(f"{'放在 10 毫秒格子上' if snap else '不放在格子上'}，改 {passes} 遍：和目标差 中位数 {np.median(err) * 1000:.1f} 毫秒、"
                f"最大 {err.max() * 1000:.1f} 毫秒、超过 10 毫秒的 {int((err > 0.0105).sum())}/{err.size} 处")
    # 10 分钟的讲课音频拼一次 + 量一次
    del n._pause
    long = lecture(150, seed=2)
    rs = [eng.SegmentResult(seg(i, "sentence"), w, sr, {}, "r", False, i) for i, w in enumerate(long)]
    layout = n._layout(rs)
    t0 = time.perf_counter()
    audio = n._render(layout, [(w, sr) for w in long], sr)
    t_render = time.perf_counter() - t0
    t0 = time.perf_counter()
    n._measure_gaps(audio, sr, layout)
    t_measure = time.perf_counter() - t0
    say(f"{len(audio) / sr / 60:.1f} 分钟（{len(long)} 句）：拼一次 {t_render:.2f} 秒，量一次停顿 {t_measure:.2f} 秒"
        f"（量了再改一共拼 2 次、量 2 次，报告里再量 1 次）")
    say()


def _fit_no_snap(n, layout, pieces, sr, passes):
    """对照：不放在格子上的改法（第一版的写法）。"""
    targets = n._pause_targets
    cur = list(layout)
    for _ in range(passes):
        gaps = n._measure_gaps(n._render(cur, pieces, sr), sr, cur)
        new = [cur[0]]
        for i in range(1, len(cur)):
            zero = cur[i][0] - (cur[i - 1][0] + cur[i - 1][1] / sr)
            t, m = targets[i - 1], gaps[i - 1]
            m = zero if m is None else m
            delta = float(np.clip(t - m, -0.15, 0.15)) if t is not None else 0.0
            new.append((new[i - 1][0] + new[i - 1][1] / sr + max(0.08, zero + delta), cur[i][1]))
        cur = new
    return cur


def check_chunked() -> None:
    say("## 3. 量停顿的逐帧电平：整个算 / 分段算")
    sr = 32000
    x = np.random.default_rng(0).normal(0, 0.1, sr * 600).astype(np.float32)  # 10 分钟
    for name, fn in (("整个算", lambda: frame_rms_db(x, sr)), ("分段算", lambda: frame_rms_db_chunked(x, sr))):
        tracemalloc.start()
        t0 = time.perf_counter()
        db = fn()
        dt = time.perf_counter() - t0
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        say(f"10 分钟 32 kHz {name}：{dt:.2f} 秒，最多多用 {peak / 2 ** 20:.0f} MB 内存")
        if name == "整个算":
            ref = db
    say(f"两种算法的结果最大差 {float(np.max(np.abs(ref - frame_rms_db_chunked(x, sr)))):.2e} dB")
    say()


def check_levels(n: eng.Narrator) -> None:
    say("## 4. 每句音量（她：句子之间差 ±1.3 dB，p05 −2.3、p95 +1.2；目标 −20 LUFS）")
    sr = 16000
    n._identical["twin"] = {"loudness": {"sd": 1.3, "p05": -2.3, "p95": 1.2, "n": 30}}
    wavs = [synth_speech("今天我们来学习这个例子大家注意听", sr=sr, seed=k, noise=0.0) * (0.5 if k % 2 else 0.125)
            for k in range(10)]
    rs = [eng.SegmentResult(seg(i, "sentence"), w.astype(np.float32), sr, {}, "r", False, i) for i, w in enumerate(wavs)]
    layout = n._layout(rs)
    before = np.array([speech_level_db(w, sr) for w in wavs])
    gains, info = n._levels(rs, layout, sr)
    after = np.array([speech_level_db(w * g, sr) for w, g in zip(wavs, gains)])
    audio = n._render(layout, [(w, sr) for w in wavs], sr, gains)
    say(f"调之前句子之间差 ±{np.std(before - np.median(before), ddof=1):.2f} dB，调之后 ±"
        f"{np.std(after - np.median(after), ddof=1):.2f} dB；整篇 {measure_lufs(audio, sr):.2f} LUFS（目标 −20）；"
        f"单独调低的句子 {info['peak_lowered'] or '没有'}")
    say()


def check_trim() -> None:
    say("## 5. 切首尾")
    sr = 32000
    t = np.arange(int(0.6 * sr)) / sr
    tone = (0.5 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
    for tail_ms in (80, 200):
        n_tail = int(tail_ms / 1000 * sr)
        tt = np.arange(n_tail) / sr
        tail = 0.5 * np.sin(2 * np.pi * 180 * (tt + t[-1] + 1 / sr)) * np.exp(-tt / (tail_ms / 1000 / np.log(1000.0)))
        w = np.concatenate([tone, tail, np.zeros(int(0.3 * sr))]).astype(np.float32)
        a = eng.trim_edges(w, sr)
        b = eng.trim_edges(w, sr, tail_pad_ms=80.0, **eng.ID_TRIM)
        say(f"{tail_ms} 毫秒衰减到 −60 dB 的尾音：以前的切法留下 {(len(a) - len(tone)) / sr * 1000:.0f} 毫秒，"
            f"「一模一样」（句尾留 80 毫秒）留下 {(len(b) - len(tone)) / sr * 1000:.0f} 毫秒")
    hiss = np.random.default_rng(0).normal(0, 0.01, sr).astype(np.float32)
    say(f"1 秒嘶嘶声：以前的切法剩 {len(eng.trim_edges(hiss, sr)) / sr:.2f} 秒，「一模一样」剩 "
        f"{len(eng.trim_edges(hiss, sr, tail_pad_ms=30.0, **eng.ID_TRIM)) / sr:.2f} 秒")
    steady = np.concatenate([tone, np.zeros(9600, np.float32)])
    say(f"0.6 秒很平稳的音调（不是噪声）：「一模一样」剩 {len(eng.trim_edges(steady, sr, tail_pad_ms=30.0, **eng.ID_TRIM)) / sr:.2f} 秒")
    say()


def main() -> None:
    say(f"Python {sys.version.split()[0]}，numpy {np.__version__}")
    say()
    with tempfile.TemporaryDirectory() as d:
        n = narrator(Path(d))
        check_dp(n)
        check_fit(n)
        check_chunked()
        check_levels(n)
        check_trim()
    OUT.write_text("\n".join(LINES) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
