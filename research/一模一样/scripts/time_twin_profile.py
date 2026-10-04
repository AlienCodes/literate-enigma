"""开发机（4 核处理器，没有显卡）上实测 twin_profile（P3）各部分要多久。不是老师的数据：合成的「讲课」录音。

做法：44.1 kHz（和素材准备存的片段一样）的合成录音，像说话的声音（谐波 + 音节起伏 + 60 ms 衰减）之间放已知长度的
数字静音（中位数 0.45 秒），用真的切片程序 find_segments 切开，每段一句话（字数和长度成正比）。然后量：
- 原始录音分块读、找停顿（source_gaps_file）：每分钟录音多少秒；
- 每段片段的声音特征（acoustic_features：停顿、音调、音量、句首句尾、频谱、去静音）：每段多少毫秒；
- build_twin_profile：第一次（全部要量）、素材没变（signature 一样）、改了一句文字（声音特征有缓存，只重新对齐）；
- 参考录音库（不算声纹）；
- 重新量的句号停顿 vs 真实值 vs 切片记下的「片段后面的停顿」。
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import numpy as np  # noqa: E402

from conftest import make_cfg  # noqa: E402
from voicetwin.data import references as R  # noqa: E402
from voicetwin.data.slicer import find_segments  # noqa: E402
from voicetwin.project import Project  # noqa: E402
from voicetwin.style import twin_profile as tp  # noqa: E402
from voicetwin.utils.audio import load_audio, save_audio  # noqa: E402

SR = 44100
N_BURSTS = 130


def burst(rng, sec, f0=210.0, level=0.25, decay=0.06):
    n = int(sec * SR)
    t = np.arange(n) / SR
    f = f0 * (1 + 0.04 * np.sin(2 * np.pi * 0.7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 8)) * (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.3 * t)))
    d = int(decay * SR)
    e = np.ones(n)
    e[:d] = 1 - np.exp(-np.arange(d) / (d / 5))
    e[-d:] = np.exp(-np.arange(d) / (d / 5))
    return (level * x * e / np.max(np.abs(x * e))).astype(np.float32)


def main():
    ws = Path(tempfile.mkdtemp(prefix="twin_time_"))
    try:
        rng = np.random.default_rng(7)
        proj = Project(make_cfg(ws), "计时")
        proj.ensure()
        pieces, spans, gaps, t = [np.zeros(int(0.5 * SR), np.float32)], [], [], 0.5
        for _ in range(N_BURSTS):
            b = burst(rng, rng.uniform(1.2, 4.0))
            pieces.append(b)
            spans.append((t, t + len(b) / SR))
            t += len(b) / SR
            z = int(float(np.exp(rng.normal(np.log(0.45), 0.45))) * SR)
            gaps.append(z / SR)
            pieces.append(np.zeros(z, np.float32))
            t += z / SR
        wav = np.concatenate(pieces)
        wav += rng.normal(0, 1e-4, len(wav)).astype(np.float32)
        sid = "lec_time01"
        raw = proj.raw_dir / f"{sid}.wav"
        save_audio(raw, wav, SR)
        minutes = len(wav) / SR / 60
        segs = find_segments(wav, SR)
        chars = "我们今天学习一个新的内容大家注意听讲"
        recs = []
        for i, s in enumerate(segs):
            a, b = s.speech_start / SR, s.speech_end / SR
            text = ""
            for k, (x, y) in enumerate(spans):
                if x < b and y > a:
                    text += "".join(chars[(k * 3 + j) % len(chars)] for j in range(max(2, round((y - x) * 4.6)))) + "。"
            cid = f"{sid}_{i:04d}"
            path = proj.clips_dir / f"{cid}.wav"
            save_audio(path, wav[s.start:s.end], SR)
            recs.append({"id": cid, "path": proj.relpath(path), "source": sid, "start": round(s.start / SR, 3),
                         "end": round(s.end / SR, 3), "duration": round((s.end - s.start) / SR, 3), "text": text,
                         "lang": "zh", "keep": True, "split": "train", "gap_before": s.gap_before,
                         "gap_after": s.gap_after, "forced_cuts": s.forced_cuts})
        proj.save_manifest(recs)
        legacy = [s.gap_after for s in segs if s.gap_after]
        durs = [r["duration"] for r in recs]
        print(f"合成录音：{minutes:.1f} 分钟，44.1 kHz；切成 {len(recs)} 段（每段中位数 {np.median(durs):.1f} 秒）")

        t0 = time.perf_counter()
        for _ in range(3):
            tp.source_gaps_file(raw)
        per_min = (time.perf_counter() - t0) / 3 / minutes
        print(f"原始录音分块读、找停顿：每分钟录音 {per_min * 1000:.0f} 毫秒")

        w, sr = load_audio(proj.abspath(recs[0]["path"]))
        t0 = time.perf_counter()
        tp.acoustic_features(w, sr)  # 第一次：librosa 要先准备（只在程序里第一次用到时有）
        print(f"第一次算声音特征（librosa 准备）：{(time.perf_counter() - t0) * 1000:.0f} 毫秒")
        times = []
        for r in recs[1:61]:
            w, sr = load_audio(proj.abspath(r["path"]))
            t0 = time.perf_counter()
            tp.acoustic_features(w, sr)
            times.append(time.perf_counter() - t0)
        print(f"每段片段的声音特征（含读文件以外的全部计算）：中位数 {np.median(times) * 1000:.0f} 毫秒、"
              f"最慢 {max(times) * 1000:.0f} 毫秒（{len(times)} 段）")

        t0 = time.perf_counter()
        prof = tp.build_twin_profile(proj)
        cold = time.perf_counter() - t0
        t0 = time.perf_counter()
        tp.build_twin_profile(proj)
        same = time.perf_counter() - t0
        recs[3]["text"] = recs[3]["text"].replace("。", "，", 1)
        proj.save_manifest(recs)
        t0 = time.perf_counter()
        tp.build_twin_profile(proj)
        edit = time.perf_counter() - t0
        print(f"build_twin_profile：第一次 {cold:.2f} 秒（{len(recs)} 段，平均每段 {cold / len(recs) * 1000:.0f} 毫秒，"
              f"含读原始录音）；素材没变 {same * 1000:.0f} 毫秒；改了一句文字 {edit * 1000:.0f} 毫秒")
        t0 = time.perf_counter()
        bank = R.build_reference_bank(proj, proj.load_manifest())
        print(f"参考录音库（不算声纹）：{len(bank)} 条，{(time.perf_counter() - t0) * 1000:.0f} 毫秒")
        st = prof["pauses"]["sentence"]
        print(f"句号停顿：真实中位数 {np.median(gaps):.3f} 秒；重新量的 {st['median']:.3f} 秒（n = {st['n']}，"
              f"片段里面 {st['n_inner']} + 片段后面 {st['n_final']}）；切片记下的「片段后面的停顿」"
              f"{np.median(legacy):.3f} 秒（n = {len(legacy)}）")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    main()
