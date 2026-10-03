"""「一模一样」P6：拼接、两个版本、报告，以及老师 10-03 定的文件名规则
（research/一模一样/设计方案原文.md §1.9、§2 P6、§4.4，测试清单 §5.1 test_assembly_identical.py）。

测的东西：
- 测试引擎整篇生成「一模一样」：两个版本都写出来，句子之间每一个采样都是 0；报告里有 search 块、每句的组合和
  选中的组合、整篇再挑一遍换没换；小结里的每个数都能在报告里找到；
- 停顿：按你本人的分布（u 在 0.2~0.8）、段落 0.85~0.97、写明的秒数不变、语速倍数照样除、少于 8 个时和以前一样；
  量了再改以后，用量你本人停顿的同一个方法量出来的停顿和目标差 10 毫秒以内；逗号处的停顿在你本人的分布里；
- 音量：句子之间差 ±6 dB 的合成声音，调完以后差得不比你本人多；0 的个数不变；最高点超过 −1 dBFS 的句子单独调低、
  每句都不超过 −1 dBFS；整篇响度和目标差 0.5 dB 以内（被最高点限制时如实写在报告里）；
- 切首尾：不传参数时和以前一模一样；80 毫秒的指数衰减尾音留下至少 70 毫秒；第一个和最后一个采样是 0；
  只有嘶嘶声时切成空的；句尾留多少按你本人的收音长度（30~120 毫秒）；
- 整篇再挑一遍（Viterbi）：避开 4 个半音的跳变；重新生成时没点名的句子不动；读错的版本永远不会被挑上；
- 两个版本：量不出底噪的句子在 B 里和 A 一模一样；分数一样时推荐没处理过的；每句都量不出底噪时两个版本完全一样并说明；
- 文件名：最后是实际用的模型名（假 GPT-SoVITS 的 v2ProPlus / v4 模型文件头 → _v2ProPlus / _V4，wav、mp3、字幕、报告、
  两个版本都是）；同一分钟里重名时 _2 在模型名前面；检测不出来写 _模型未知；一篇用了两种写 _V4和v2ProPlus；
  老师输入的点、空格、括号换成 _；所有给老师的文件名只有汉字、字母、数字、下划线和一个扩展名；WAV / MP3 里面也写着模型名。
"""

import hashlib
import json
import re
import shutil
import sys
import types
import uuid
from pathlib import Path

import numpy as np
import pytest

from conftest import make_cfg
from fake_gptsovits import build_fake_root
from test_identical_search import FakeScorer, _narrator, _tone
from voicetwin import workflows as wf
from voicetwin.backends.base import MODEL_UNKNOWN, get_backend, model_label
from voicetwin.backends.workers.dummy_worker import synth_speech
from voicetwin.eval.metrics import Score
from voicetwin.eval.speaker import PCT_HELP
from voicetwin.synth import engine as eng
from voicetwin.synth import search as S
from voicetwin.synth.script import ScriptSegment
from voicetwin.utils.audio import (
    audio_comment,
    frame_rms_db,
    load_audio,
    measure_lufs,
    speech_level_db,
)
from voicetwin.utils.ffmpeg import read_tags
from voicetwin.utils.textutil import TEACHER_FILE_RE, file_stem

SR = 16000


def _uniq(text: str) -> str:
    return text + "编号" + "".join(str(int(c, 16) % 10) for c in uuid.uuid4().hex[:6]) + "。"


def _fake_noisereduce(monkeypatch):
    nr = types.ModuleType("noisereduce")

    def reduce_noise(y, sr, y_noise=None, stationary=False, prop_decrease=1.0, **kw):
        return (np.asarray(y, dtype=np.float32) * 0.97).astype(np.float32)

    nr.reduce_noise = reduce_noise
    monkeypatch.setitem(sys.modules, "noisereduce", nr)


def _gaps_are_zero(path, segments, margin=0.002):
    wav, sr = load_audio(path)
    m = int(margin * sr)
    first = int(round(segments[0]["start"] * sr))
    assert first > m and np.all(wav[: first - m] == 0.0), "开头不是绝对静音"
    for a, b in zip(segments, segments[1:]):
        lo, hi = int(round(a["end"] * sr)) + m, int(round(b["start"] * sr)) - m
        assert hi > lo
        assert np.all(wav[lo:hi] == 0.0), f"第 {a['index']} 句和第 {b['index']} 句之间不是绝对静音"
    last = int(round(segments[-1]["end"] * sr)) + m
    assert np.all(wav[last:] == 0.0), "结尾不是绝对静音"
    return wav, sr


def _numbers(obj, out=None):
    """报告里所有的数（按小结可能用的几种写法：整数、1 位、2 位小数）。"""
    out = set() if out is None else out
    if isinstance(obj, bool) or obj is None:
        return out
    if isinstance(obj, (int, float)):
        v = float(obj)
        out |= {f"{v:.0f}", f"{v:.1f}", f"{v:.2f}"}
        if float(v).is_integer():
            out.add(str(int(v)))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers(v, out)
        out.add(str(len(obj)))  # 「共 N 句」= 报告里逐句结果的个数
    return out


# ============================================================================ 整篇
def test_identical_narration_two_variants_zero_silence_and_report(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _fake_noisereduce(monkeypatch)
    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    script = _uniq("第一句话在这里，先看这个例子") + _uniq("第二句话也在这里") + "\n\n" + _uniq("新的一段从这里开始")
    rec = []
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "课.wav"), candidates=2,
                         progress=lambda f, m: rec.append((f, m)))
    assert res.quality == "identical" and [v["name"] for v in res.variants] == ["未去杂音", "去杂音"]
    for v in res.variants:  # 两个版本句子之间每一个采样都是 0（WAV 16 位）
        wav, _ = _gaps_are_zero(v["path"], res.segments)
        assert np.any(wav != 0.0)
    _gaps_are_zero(res.audio_path, res.segments)
    rep = json.loads(res.report_path.read_text(encoding="utf-8"))
    for key in ("batch_used", "speed_trick", "oom_backoffs", "split_fallbacks", "candidates_per_s",
                "seconds_per_sentence", "gpu_util_avg", "gpu_peak_gb"):
        assert key in rep["search"], key
    assert rep["search"]["seconds_per_sentence"] > 0 and rep["search"]["fresh_sentences"] == 3
    for s in rep["segments"]:
        assert s["arms"] and s["arm"] and s["model"] == "dummy" and isinstance(s["dp_changed"], bool)
    assert rep["continuity"]["applied"] is True and rep["model_name"] == "dummy"
    assert rep["pauses"]["fit_passes"] == 2 and rep["loudness"]["applied"] is True
    # 进度：整篇再挑一遍、按你的停顿和音量拼接（设计方案 §4.4），一直往前走
    msgs = [m for _, m in rec]
    assert "整篇再挑一遍，让前后句子衔接自然……" in msgs and "按你本人的停顿长短和音量拼接，再量一遍停顿……" in msgs
    fr = [f for f, _ in rec]
    assert fr == sorted(fr)
    # 小结里的每个数都能在报告里找到（不写没量过的数）；3 句都是新生成的，最后一句之后不说「还要多久」
    nums = _numbers(rep)
    keys = ("本次生成", "整篇像你本人", "停顿（实测）", "句子之间的音量差（实测）", "这次实际速度")
    lines = [n for n in rep["notes"] if n.startswith(keys)]
    assert {k for k in keys if any(n.startswith(k) for n in lines)} == set(keys)
    for line in lines:
        for x in re.findall(r"\d+(?:\.\d+)?", line.replace(PCT_HELP, "")):
            assert x in nums, (x, line)
    assert not any(m.startswith("按刚才实测的速度估算") for m in msgs)
    pause_line = next(n for n in lines if n.startswith("停顿（实测）"))
    assert "逗号处" not in pause_line.split("这次")[1]  # 这一篇没有在逗号处拆开的句子：不写逗号处


def test_measured_gaps_hit_targets_and_comma_pauses_follow_her(prepared, tmp_path, monkeypatch):
    """拼好以后用量你本人停顿的同一个方法量：每两句之间的停顿和目标差 10 毫秒以内；逗号处的停顿在你本人逗号停顿的
    p20~p80 里（u 在 0.2~0.8），中位数在 p25~p75 里（设计方案测试清单写的是 p25~p75，算法 §1.9 写的是 u 在 0.2~0.8）。"""
    cfg, project, _ = prepared
    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    tag = uuid.uuid4().hex[:6]
    parts = [("我们先看第一个例子", "clause"), ("然后接着往下说", "clause"), ("这一句话说完了", "sentence"),
             ("第二句也是这样开始", "clause"), ("中间再停一下", "clause"), ("最后再说一点", "clause"),
             ("这一段就到这里", "paragraph"), ("新的一段从这里开始", "sentence")]
    segs = []
    for i, (t, k) in enumerate(parts):
        text = f"{t}{tag}{i}" + ("，" if k == "clause" else "。")
        segs.append(ScriptSegment(text=text, display=text, lang="zh", kind="statement", index=i, pause_after=k))
    backend = get_backend("dummy", cfg, project)
    try:
        n = eng.Narrator(cfg, project, backend, quality="identical", candidates=2, variants=False, tier="none")
        res = n.narrate(segs, tmp_path / "停顿.wav")
    finally:
        backend.stop()
    rep = json.loads(res.report_path.read_text(encoding="utf-8"))
    p = rep["pauses"]
    assert len(p["targets"]) == len(p["measured"]) == len(segs) - 1
    for t, m in zip(p["targets"], p["measured"]):
        assert t is not None and m is not None and abs(m - t) <= 0.0105, (t, m)
    q = n._identical_ctx()["twin"]["pauses"]["comma"]["q"]
    comma = [m for m, k in zip(p["measured"], p["kinds"]) if k == "clause"]
    assert len(comma) == 5
    for m in comma:
        assert q["p20"] - 0.011 <= m <= q["p80"] + 0.011, (m, q)
    assert q["p25"] - 0.011 <= float(np.median(comma)) <= q["p75"] + 0.011
    for t, k in zip(p["targets"], p["kinds"]):  # 目标本身：逗号 p20~p80，段落句号的 p85~p97
        if k == "clause":
            assert q["p20"] - 1e-9 <= t <= q["p80"] + 1e-9
        if k == "paragraph":
            qs = n._identical_ctx()["twin"]["pauses"]["sentence"]["q"]
            assert qs["p85"] - 1e-9 <= t <= qs["p97"] + 1e-9
    _gaps_are_zero(res.audio_path, res.segments)


def test_pause_rules_explicit_speed_and_fallback(tmp_path):
    n, _ = _narrator(tmp_path, tier="none")
    q = {f"p{k:02d}": 0.15 + 0.002 * k for k in list(range(5, 100, 5)) + [97]}
    qs = {f"p{k:02d}": 0.6 + 0.01 * k for k in list(range(5, 100, 5)) + [97]}
    n._identical["twin"] = {"pauses": {"comma": {"n": 20, "q": q}, "sentence": {"n": 30, "q": qs}}}

    def seg(i, kind):
        return ScriptSegment(text="测试", display="测试", lang="zh", kind="statement", index=i, pause_after=kind)

    import random

    def expect(table, i, lo, hi):
        u = random.Random(n.base_seed + i).uniform(lo, hi)
        xs = sorted(table.items(), key=lambda kv: int(kv[0][1:]))
        return float(np.interp(u, [int(k[1:]) / 100 for k, _ in xs], [v for _, v in xs]))

    assert n._pause(seg(3, "clause"), 3) == pytest.approx(expect(q, 3, 0.2, 0.8))
    assert n._pause(seg(4, "sentence"), 4) == pytest.approx(expect(qs, 4, 0.2, 0.8))
    assert n._pause(seg(5, "paragraph"), 5) == pytest.approx(expect(qs, 5, 0.85, 0.97))
    assert n._pause(seg(6, 1.5), 6) == 1.5  # 讲稿里写明的 [停顿=1.5秒] 不变
    # 少于 8 个：和以前的方法一模一样（「完美」档用的就是以前的方法）
    n._identical["twin"] = {"pauses": {"comma": {"n": 5, "q": q}, "sentence": {"n": 3, "q": None}}}
    p, _ = _narrator(tmp_path / "p", tier="none", name="完美")
    p.quality = "perfect"
    for i, kind in enumerate(("clause", "sentence", "paragraph")):
        assert n._pause(seg(i, kind), i) == p._pause(seg(i, kind), i)
    # 语速倍数：停顿也跟着除（写明的秒数不除）
    fast, _ = _narrator(tmp_path / "f", tier="none", name="快", speed=1.25)
    fast._identical["twin"] = {"pauses": {"comma": {"n": 20, "q": q}, "sentence": {"n": 30, "q": qs}}}
    rs = [eng.SegmentResult(seg(i, k), np.ones(SR, np.float32) * 0.1, SR, {}, "r1", False, 0)
          for i, k in enumerate(("clause", 2.0, "sentence"))]
    fast._layout(rs)
    assert fast._pause_targets[0] == pytest.approx(expect(q, 0, 0.2, 0.8) / 1.25)
    assert fast._pause_targets[1] == 2.0


# ============================================================================ 音量
def _speechy(seed: int, gain: float = 1.0) -> np.ndarray:
    w = synth_speech("今天我们来学习这个例子大家注意听", sr=SR, seed=seed, noise=0.0) * gain
    return w.astype(np.float32)


def _results(wavs):
    out = []
    for i, w in enumerate(wavs):
        seg = ScriptSegment(text=f"第{i}句", display=f"第{i}句", lang="zh", kind="statement", index=i,
                            pause_after="sentence")
        out.append(eng.SegmentResult(seg, w, SR, {}, "r1", False, i))
    return out


def test_levels_shrink_to_her_spread_keep_zeros_and_respect_peaks(tmp_path):
    n, _ = _narrator(tmp_path, tier="none")
    n._identical["twin"] = {"loudness": {"sd": 1.3, "p05": -2.3, "p95": 1.2, "n": 30}}
    n.profile = {"loudness": {"source_lufs": -22.0}}
    wavs = [_speechy(k, 2.0 if k % 2 else 0.5) * 0.25 for k in range(6)]  # 一句 +6 dB 一句 −6 dB
    results = _results(wavs)
    layout = n._layout(results)
    pieces = [(w, SR) for w in wavs]
    before = [speech_level_db(w, SR) for w in wavs]
    assert np.std(np.asarray(before) - np.median(before), ddof=1) > 5.0
    gains, info = n._levels(results, layout, SR)
    after = np.asarray([speech_level_db(w * g, SR) for w, g in zip(wavs, gains)])
    assert np.std(after - np.median(after), ddof=1) <= 1.3 + 1e-6  # 不比你本人差得多
    plain = n._render(layout, pieces, SR)
    leveled = n._render(layout, pieces, SR, gains)
    assert np.count_nonzero(plain == 0.0) == np.count_nonzero(leveled == 0.0)  # 只乘系数：0 还是 0，别的不会变成 0
    assert not info["peak_lowered"] and abs(measure_lufs(leveled, SR) - (-22.0)) <= 0.5
    # 目标很响：有几句调上去会超过 −1 dBFS，这几句单独调低（不用限幅器），每句都不超过 −1 dBFS；整篇达不到目标时如实写
    n.profile = {"loudness": {"source_lufs": -8.0}}
    gains, info = n._levels(results, layout, SR)
    assert info["peak_lowered"]
    for w, g in zip(wavs, gains):
        assert float(np.max(np.abs(w * g))) <= 10 ** (-1 / 20) + 1e-6
    loud = measure_lufs(n._render(layout, pieces, SR, gains), SR)
    assert loud < -8.0 - 0.5 and info["target_lufs"] == -8.0


# ============================================================================ 切首尾
def _old_trim(wav, sr, pad_ms=30.0):
    """P6 以前的 trim_edges（原样抄下来）：不传参数时新的必须和它一模一样。"""
    wav = np.asarray(wav, dtype=np.float32)
    if wav.size == 0:
        return wav
    db10 = frame_rms_db(wav, sr)
    d = db10[db10 > -100]
    if d.size == 0:
        thr = -40.0
    else:
        noise, speech = float(np.percentile(d, 3)), float(np.percentile(d, 95))
        thr = float(min(max(speech - 30.0, noise + 6.0, -65.0), speech - 15.0))
    hop_ms, win_ms = 5.0, 20.0
    db = frame_rms_db(wav, sr, hop_ms=hop_ms, win_ms=win_ms)
    voiced = np.where(db >= thr)[0]
    if voiced.size == 0:
        return wav[:0]
    hop, half, pad = sr * hop_ms / 1000.0, sr * win_ms / 2000.0, int(sr * pad_ms / 1000.0)
    v0, v1 = int(voiced[0] * hop - half), int(voiced[-1] * hop + half)
    start, end = max(0, v0 - pad), min(len(wav), v1 + pad)
    out = wav[start:end].astype(np.float32, copy=True)
    n = len(out)
    if n < 4:
        return out[:0]
    lead, tail = max(0, v0 - start), max(0, end - v1)
    n_in = min(n // 2, max(int(sr * 0.002), lead + int(sr * 0.004)))
    n_out = min(n // 2, max(int(sr * 0.002), tail + int(sr * 0.008)))
    if n_in > 1:
        out[:n_in] *= (0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, n_in))).astype(np.float32)
    if n_out > 1:
        out[-n_out:] *= (0.5 + 0.5 * np.cos(np.linspace(0.0, np.pi, n_out))).astype(np.float32)
    out[0] = 0.0
    out[-1] = 0.0
    return out


def test_trim_defaults_unchanged_tail_kept_and_hiss_trims_to_empty(tmp_path):
    rng = np.random.default_rng(3)
    sr = 32000
    t = np.arange(int(0.6 * sr)) / sr
    tone = (0.5 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
    cases = [np.concatenate([rng.normal(0, 0.003, 8000), tone + rng.normal(0, 0.003, tone.size),
                             rng.normal(0, 0.003, 9000)]).astype(np.float32),
             np.concatenate([tone, np.zeros(9600)]).astype(np.float32),
             _speechy(5), np.zeros(1000, np.float32), rng.normal(0, 0.01, 3000).astype(np.float32)]
    for w in cases:  # 不传参数：和以前一个采样都不差
        assert np.array_equal(eng.trim_edges(w, sr), _old_trim(w, sr))
    # 80 毫秒的指数衰减尾音（从说话的音量降到 −60 dB）：留下至少 70 毫秒；第一个和最后一个采样是 0
    n_tail = int(0.08 * sr)
    tt = np.arange(n_tail) / sr
    tail = 0.5 * np.sin(2 * np.pi * 180 * (tt + t[-1] + 1.0 / sr)) * np.exp(-tt / (0.08 / np.log(1000.0)))
    w = np.concatenate([tone, tail, np.zeros(int(0.3 * sr))]).astype(np.float32)
    out = eng.trim_edges(w, sr, tail_pad_ms=80.0, **eng.ID_TRIM)
    assert out[0] == 0.0 and out[-1] == 0.0
    assert len(out) - len(tone) >= int(0.07 * sr)
    # 只有嘶嘶声：切成空的（以前的切法会留着）
    hiss = rng.normal(0, 0.01, sr).astype(np.float32)
    assert eng.trim_edges(hiss, sr, tail_pad_ms=30.0, **eng.ID_TRIM).size == 0
    assert eng.trim_edges(hiss, sr).size > 0
    # 很平稳的音调不是嘶嘶声（只看音量分不出来，所以还看频谱）：不能切成空的
    steady = np.concatenate([tone, np.zeros(9600)]).astype(np.float32)
    assert eng.trim_edges(steady, sr, tail_pad_ms=30.0, **eng.ID_TRIM).size > 0
    # 句尾留多少：你本人句尾收音的中位数，限制在 30~120 毫秒；没量出来时 None（和句首一样 30 毫秒）
    n, _ = _narrator(tmp_path, tier="none")
    for got, want in ((7.5, 30.0), (80.0, 80.0), (250.0, 120.0)):
        n._identical["twin"] = {"edges": {"offset_ms": {"median": got, "n": 30}}}
        assert n._tail_pad_ms() == want
    n._identical["twin"] = {"edges": {"offset_ms": {"median": None, "n": 3}}}
    assert n._tail_pad_ms() is None


# ============================================================================ 整篇再挑一遍
_TWIN_DELTAS = {"deltas": {"sentence": {"f0_med_st": {"mean": 0.0, "sd": 1.0, "n": 30},
                                        "log_rate": {"mean": 0.0, "sd": 0.1, "n": 30}},
                           "clause": {"f0_med_st": {"mean": 0.0, "sd": 1.0, "n": 30},
                                      "log_rate": {"mean": 0.0, "sd": 0.1, "n": 30}},
                           "timbre": None}}


def _dp_setup(tmp_path, monkeypatch, table):
    """table：每句 [(种子, 音高 Hz, 综合分, 错字率), ...]，第一个是现在用的。"""
    n, _ = _narrator(tmp_path, tier="none", scorer=FakeScorer())
    n._identical["twin"] = dict(_TWIN_DELTAS)
    f0 = {}
    monkeypatch.setattr(S, "_f0_of", lambda c: f0.get(int(c.seed)))
    results, plans = [], []
    for i, rows in enumerate(table):
        seg = ScriptSegment(text=f"整篇再挑一遍第{i}句话", display=f"整篇再挑一遍第{i}句话", lang="zh", kind="statement",
                            index=i, pause_after="sentence")
        plan = n._plan(seg)
        cands = []
        for seed, hz, total, cer in rows:
            f0[seed] = hz
            wav = _tone(seed, seg.text, 1.0)
            c = S.SearchCand(wav=wav, sr=SR, arm=S.Arm("r1", 0, 0), seed=seed, req_seed=seed, row=0, req_no=0, req_n=1,
                             speed=1.0, model="fake-model")
            c.awav, c.empty = n._analysis_pair(wav, SR)
            c.score = Score(total=total, cer=cer, errors=0 if cer == 0 else 5, rate=4.0, stage="full", checker="fake")
            cands.append(c)
        S.store_candidates(S.store_dir(n.project.cache_dir, plan.pool_key), cands, 6)
        cur = cands[0]
        results.append(eng.SegmentResult(seg, n._trim(cur.wav, SR), SR, cur.score.to_dict(), "r1", True, cur.seed,
                                         path=plan.wav_path, tries=6, met=True, model={"name": "V4"},
                                         extra={"arm": cur.arm.to_dict(),
                                                "chosen": {"seed": cur.seed, "row": 0, "speed": 1.0}}))
        plans.append(plan)
    n._plans = plans
    return n, results, plans


def test_viterbi_avoids_a_four_semitone_jump(tmp_path, monkeypatch):
    up4 = 150.0 * 2 ** (4 / 12)
    n, results, plans = _dp_setup(tmp_path, monkeypatch, [
        [(11, 150.0, 1.0, 0.0)],
        [(21, up4, 1.00, 0.0), (22, 151.0, 0.99, 0.0)],   # 现在用的跳了 4 个半音；另一个综合分低 0.01
        [(31, 150.0, 1.0, 0.0)]])
    info = n._continuity(results)
    assert info["applied"] and info["changed"] == 1 and info["features"]["sentence"] == ["f0", "rate"]
    assert results[1].seed == 22 and results[1].extra["dp"]["changed"] is True
    assert [r.seed for r in (results[0], results[2])] == [11, 31]
    meta = json.loads(plans[1].meta_path.read_text(encoding="utf-8"))  # 写回了这句的缓存：下次直接用换过的
    assert meta["seed"] == 22 and meta["dp"]["changed"] is True and meta["model_info"] == {"name": "V4"}
    assert np.array_equal(load_audio(plans[1].wav_path)[0], results[1].wav)
    assert results[1].wav[0] == 0.0 and results[1].wav[-1] == 0.0
    # 读回换过的那一句的缓存再挑一次：已经是最好的了，不再换
    reloaded = n._load_cached(results[1].segment, plans[1])
    assert reloaded.seed == 22 and reloaded.extra["chosen"]["seed"] == 22
    again = n._continuity([results[0], reloaded, results[2]])
    assert again["changed"] == 0


def test_viterbi_redo_keeps_neighbours_and_never_picks_cer_failures(tmp_path, monkeypatch):
    up4 = 150.0 * 2 ** (4 / 12)
    table = [[(11, up4, 1.0, 0.0), (12, 150.0, 0.999, 0.0)],
             [(21, 150.0, 1.0, 0.0), (22, up4, 0.995, 0.0)],
             [(31, up4, 1.0, 0.0), (32, 150.0, 0.999, 0.0)]]
    n, results, _ = _dp_setup(tmp_path, monkeypatch, table)
    info = n._continuity(results, free={1})  # 只重新生成了第 2 句：第 1、3 句一个都不动
    assert [r.seed for r in results] == [11, 22, 31] and info["changed"] == 1 and info["free"] == 1
    # 读错的版本（错字率 0.5）再像、衔接再好也不挑：现在用的那个读对了
    n2, results2, _ = _dp_setup(tmp_path / "b", monkeypatch, [
        [(41, 150.0, 1.0, 0.0)], [(51, up4, 1.0, 0.0), (52, 150.0, 1.5, 0.5)], [(61, 150.0, 1.0, 0.0)]])
    info2 = n2._continuity(results2)
    assert [r.seed for r in results2] == [41, 51, 61] and info2["changed"] == 0
    # 量不出你本人前后两句的变化：这一步跳过，如实写原因
    n2._identical["twin"] = {"deltas": {"sentence": {"f0_med_st": {"mean": None, "sd": None, "n": 2}}}}
    skipped = n2._continuity(results2)
    assert skipped["applied"] is False and "没测出来" in skipped["why"]


# ============================================================================ 两个版本
class _ConstScorer(FakeScorer):
    def full(self, wav, sr, text, lang, mult=1.0, prepared=None, use_asr=True, cer=None):
        return Score(total=1.0, pct=99.0, stage="full")


def _with_pause(seed, hiss=0.0):
    a, b = _speechy(seed)[: SR // 2], _speechy(seed + 1)[: SR // 2]
    w = np.concatenate([a, np.zeros(SR // 5, np.float32), b])
    if hiss:
        w = w + np.random.default_rng(seed).normal(0, hiss, w.size).astype(np.float32)
    return eng.trim_edges(w.astype(np.float32), SR)


def test_variants_only_denoise_noisy_sentences_and_tie_goes_to_raw(tmp_path, monkeypatch):
    _fake_noisereduce(monkeypatch)
    n, _ = _narrator(tmp_path, tier="none", scorer=_ConstScorer())
    clean, noisy = _with_pause(1), _with_pause(3, hiss=0.003)  # 一句停顿里是数字静音，一句有约 −50 dB 的底噪
    assert n._speech_floor_db(clean, SR) <= eng.DENOISE_FLOOR_DB < n._speech_floor_db(noisy, SR)
    results = _results([clean, noisy])
    layout = n._layout(results)
    audio_a = n._render(layout, [(r.wav, SR) for r in results], SR)
    variants, audio = n._make_variants(results, layout, audio_a, SR, 1.0)
    a, b = audio["未去杂音"], audio["去杂音"]
    (s0, n0), (s1, n1) = layout
    i0, i1 = int(round(s0 * SR)), int(round(s1 * SR))
    assert np.array_equal(a[i0:i0 + n0], b[i0:i0 + n0])          # 量不出底噪的句子：B 和 A 一模一样
    assert not np.array_equal(a[i1:i1 + n1], b[i1:i1 + n1])      # 有底噪的句子去了杂音
    assert np.all(b[i0 + n0:i1] == 0.0)
    vb = next(v for v in variants if v["name"] == "去杂音")
    assert vb["denoised_sentences"] == [2]
    assert [v["name"] for v in variants if v["recommended"]] == ["未去杂音"]  # 分数一样：推荐没处理过的
    # 每句都量不出底噪：两个版本完全一样，并且如实说
    n.notes.clear()
    results = _results([clean, _with_pause(7)])
    layout = n._layout(results)
    audio_a = n._render(layout, [(r.wav, SR) for r in results], SR)
    variants, audio = n._make_variants(results, layout, audio_a, SR, 1.0)
    assert np.array_equal(audio["未去杂音"], audio["去杂音"]) and variants[1]["same_as_raw"] is True
    assert "两个版本完全一样（每句里都量不出底噪，不需要去杂音）。" in n.notes
    assert [v["name"] for v in variants if v["recommended"]] == ["未去杂音"]


# ============================================================================ 文件名（老师 10-03 的规定）
def test_model_names_tags_and_file_stems():
    assert model_label("v4") == "V4" and model_label("v5") == "V5" and model_label("v2ProPlus") == "v2ProPlus"
    assert model_label("v2Pro") == "v2Pro" and model_label(None) is None and model_label("") is None
    from voicetwin.backends.indextts import IndexTTSBackend

    fake = types.SimpleNamespace(version="2.5")
    assert IndexTTSBackend.model_name_info(fake)["name"] == "IndexTTS25"  # 老师定的：不放点
    assert eng.model_tag([{"name": "V4"}]) == "V4"
    assert eng.model_tag([{"name": "V4"}, {"name": "v2ProPlus"}, {"name": "V4"}]) == "V4和v2ProPlus"
    # 按用得多少排（时长）：v2ProPlus 那一句更长
    assert eng.model_tag([{"name": "V4"}, {"name": "v2ProPlus"}], [1.0, 5.0]) == "v2ProPlus和V4"
    assert eng.model_tag([{"name": None}]) == MODEL_UNKNOWN == "模型未知"
    assert eng.model_tag([{"name": "V4"}, {}], [3.0, 1.0]) == "V4和模型未知"
    assert file_stem("第1.2课") == "第1_2课" and file_stem("第3课 牛顿第二定律") == "第3课_牛顿第二定律"
    assert file_stem("（第３课）-复习[1].v2") == "第3课_复习_1_v2" and file_stem("...") == "讲课音频"
    # 没写扩展名、名字里有点：「.2课」不是扩展名（不能用 with_suffix），整个都是名字
    assert eng.out_parts("x/第1.2课", "wav")[1:] == ("第1_2课", ".wav")
    assert eng.out_parts("x/第1.2课.mp3", "wav")[1:] == ("第1_2课", ".mp3")
    assert eng.out_parts("x/IndexTTS2.5", "mp3")[1:] == ("IndexTTS2_5", ".mp3")


def test_chunked_gap_detector_is_the_same_detector():
    """量整篇停顿时逐帧电平分段算（一小时的讲课音频整个算要好几 GB 内存）：和整个算的结果一模一样。"""
    from voicetwin.utils.audio import frame_rms_db_chunked, silent_runs

    rng = np.random.default_rng(1)
    for sr in (16000, 22050, 32000, 44100):
        x = (rng.normal(0, 0.1, sr * 5) * (rng.random(sr * 5) > 0.3)).astype(np.float32)
        x[sr:2 * sr] = 0.0
        x[3 * sr:int(3.3 * sr)] = 0.0
        assert np.allclose(frame_rms_db(x, sr), frame_rms_db_chunked(x, sr, chunk_frames=37), atol=1e-5)
        assert silent_runs(x, sr) == silent_runs(x, sr, chunked=True)


def test_narration_reports_new_and_old_names(tmp_path):
    """找生成过的报告：新的「<名字>_<模型名>.json」和以前的「<名字>.report.json」都认，盲听测试的答案等别的 .json 不算。"""
    import os
    import time

    old = tmp_path / "第1课.report.json"
    old.write_text(json.dumps({"audio": "a.wav", "segments": []}), encoding="utf-8")
    (tmp_path / ("盲听测试_1" + wf.BLIND_ANSWER_SUFFIX)).write_text(json.dumps({"items": []}), encoding="utf-8")
    (tmp_path / "坏的.json").write_text("{", encoding="utf-8")
    new = tmp_path / "第2课_V4.json"
    new.write_text(json.dumps({"audio": "b.wav", "segments": [{"index": 1}]}), encoding="utf-8")
    now = time.time()
    os.utime(old, (now - 100, now - 100))
    assert wf.narration_reports(tmp_path) == [new, old]


def _all_names(folder):
    return sorted(p.name for p in Path(folder).iterdir() if p.is_file())


def test_dummy_names_clash_sanitise_comment_and_unknown(prepared, tmp_path, monkeypatch):
    """测试引擎：同一分钟里重名时 _2 在模型名前面；老师输入的点、空格、括号换成 _；WAV 里面写着模型名；
    检测不出来写 _模型未知；所有文件名只有汉字、字母、数字、下划线和一个扩展名。"""
    from voicetwin.webui import app as A

    cfg, project, _ = prepared
    out_dir = tmp_path / "outputs"
    proj = types.SimpleNamespace(outputs_dir=out_dir)
    monkeypatch.setattr(A, "_time_suffix", lambda t=None: "10月05日09点30分")
    first = A._output_path(proj, "第3课", "wav", "x")
    assert first.name == "第3课_10月05日09点30分.wav"
    res = wf.run_narrate(cfg, project.voice, _uniq("文件名测试第一句"), out=str(first), quality="fast")
    assert res.audio_path.name == "第3课_10月05日09点30分_dummy.wav"
    assert res.srt_path.name == "第3课_10月05日09点30分_dummy.srt"
    assert res.report_path.name == "第3课_10月05日09点30分_dummy.json"
    assert "模型：dummy" in audio_comment(res.audio_path)
    # 这一版以前生成的句子（记录里没有模型名）：能用上缓存就说明是现在这个模型生成的，按现在的模型文件检测
    seg_meta = Path(project.abspath(res.segments[0]["clip"])).with_suffix(".json")
    meta = json.loads(seg_meta.read_text(encoding="utf-8"))
    meta.pop("model_info")
    meta.pop("model_name")
    seg_meta.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    again = wf.run_narrate(cfg, project.voice, res.segments[0]["text"], out=str(out_dir / "旧记录.wav"), quality="fast")
    assert again.segments[0]["cached"] and again.audio_path.name == "旧记录_dummy.wav"
    second = A._output_path(proj, "第3课", "wav", "x")  # 同一分钟又生成一次：_2 在模型名前面
    assert second.name == "第3课_10月05日09点30分_2.wav"
    res2 = wf.run_narrate(cfg, project.voice, _uniq("文件名测试第二次"), out=str(second), quality="fast")
    assert res2.audio_path.name == "第3课_10月05日09点30分_2_dummy.wav"
    assert first.with_name("第3课_10月05日09点30分_dummy.wav").exists()  # 第一次的没被覆盖
    # 老师输入的名字里有点、空格、括号、横杠
    typed = A._output_path(proj, "第1.2课 (复习)-A", "mp3", "x")
    assert typed.name == "第1_2课_复习_A_10月05日09点30分.mp3"
    res3 = wf.run_narrate(cfg, project.voice, _uniq("文件名测试第三次"), out=str(typed), quality="fast")
    assert res3.audio_path.name == "第1_2课_复习_A_10月05日09点30分_dummy.mp3"
    assert "模型：dummy" in read_tags(res3.audio_path).get("comment", "")
    # 检测不出来：_模型未知（不猜）
    monkeypatch.setattr(eng.Narrator, "_model_info", lambda self: {"name": None, "how": "读不出来", "files": []})
    res4 = wf.run_narrate(cfg, project.voice, _uniq("文件名测试第四次"), out=str(out_dir / "第4课.wav"),
                          quality="fast")
    assert res4.audio_path.name == "第4课_模型未知.wav"
    for name in _all_names(out_dir):
        assert TEACHER_FILE_RE.match(name), name


def test_mixed_models_join_with_he(prepared, tmp_path, monkeypatch):
    """一篇里用了两种模型（以后每句可以亲耳挑别的模型的版本）：按每一句实际记下的模型、按用得多少排，用「和」连起来。"""
    cfg, project, _ = prepared
    names = iter(["V4", "v2ProPlus", "V4"])
    monkeypatch.setattr(eng.Narrator, "_model_info", lambda self: {"name": next(names), "how": "测试", "files": []})
    tag = uuid.uuid4().hex[:6]
    script = "\n".join(f"混合模型测试第{k}句话，长度差不多一样，编号{tag}。" for k in "一二三")
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "混合.wav"), quality="fast")
    assert res.audio_path.name == "混合_V4和v2ProPlus.wav"
    rep = json.loads(res.report_path.read_text(encoding="utf-8"))
    assert [m["name"] for m in rep["models_used"]] == ["V4", "v2ProPlus"]
    assert [s["model"] for s in rep["segments"]] == ["V4", "v2ProPlus", "V4"]
    assert "模型：V4和v2ProPlus" in audio_comment(res.audio_path)
    # 再生成一次（都用缓存）：每句记下的模型名照样用，不是按现在的模型重新猜
    monkeypatch.setattr(eng.Narrator, "_model_info", lambda self: {"name": "V5", "how": "测试", "files": []})
    again = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "混合2.wav"), quality="fast")
    assert again.audio_path.name == "混合2_V4和v2ProPlus.wav"


def test_other_teacher_files_follow_the_name_rule(prepared, tmp_path):
    """下载的改好的文字、问题报告、盲听测试的答案、试听语速：文件名都只有汉字、字母、数字、下划线和一个扩展名。"""
    from voicetwin.report import report_failure

    cfg, project, _ = prepared
    txt = Path(wf.export_review_text(cfg, project.voice)["path"])
    assert TEACHER_FILE_RE.match(txt.name), txt.name
    rep = report_failure(RuntimeError("测试"), what="测试", logs_dir=tmp_path / "logs")
    assert rep is not None and TEACHER_FILE_RE.match(rep.name), rep
    assert TEACHER_FILE_RE.match("盲听测试_20261003_120000" + wf.BLIND_ANSWER_SUFFIX)
    # 以前的版本写的答案文件名（带括号）照样认
    d = tmp_path / "盲听测试_1"
    d.mkdir()
    old = d.with_name(d.name + wf.OLD_BLIND_ANSWER_SUFFIX)
    old.write_text("{}", encoding="utf-8")
    assert wf.blind_answer_path(d) == old
    res = wf.preview_speed(cfg, project.voice, "试听语速用这一句。", value=-10)
    assert TEACHER_FILE_RE.match(res.audio_path.name), res.audio_path.name


def _fake_python_ok() -> bool:
    import subprocess

    try:
        proc = subprocess.run([str(Path(sys.executable).resolve()), "-c", "import yaml"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


needs_fake_python = pytest.mark.skipif(not _fake_python_ok(),
                                       reason="这个环境里 fake GPT-SoVITS 的子进程缺少 yaml（已知的环境问题）")


@needs_fake_python
def test_fake_gptsovits_names_follow_the_weights_actually_used(prepared, tmp_path, monkeypatch):
    """假 GPT-SoVITS：用 v2ProPlus（文件头 06）的模型文件生成 → 所有文件名最后是 _v2ProPlus；换成 v4（文件头 04）
    的模型文件 → _V4（wav 和 mp3、字幕、报告、两个版本都是），文件里面的注释和报告里的模型文件指纹也对；
    还没训练（底模的文件头认不出来）→ _模型未知。"""
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    root = build_fake_root(tmp_path / "GSV")
    gcfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": 19896, "startup_timeout": 60}})
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    _fake_noisereduce(monkeypatch)
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    out = tmp_path / "out"

    def use(head: bytes, name: str):
        sov = root / "SoVITS_weights_v2ProPlus" / name
        gpt = root / "GPT_weights_v2ProPlus" / (name.replace(".pth", ".ckpt"))
        for f, data in ((sov, head + b"s" * 4000), (gpt, b"g" * 3000)):
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        p2.update_models("gptsovits", {"selected": {"id": name, "sovits": str(sov), "gpt": str(gpt)}})
        return sov

    sov = use(b"06", "vt_e8_s80.pth")
    text = _uniq("假引擎文件名测试第一句话，稍微长一点") + _uniq("第二句话")
    res = wf.run_narrate(gcfg, project.voice, text, out=str(out / "第3课_10月05日09点30分.wav"),
                         backend_name="gptsovits", candidates=1)
    base = "第3课_10月05日09点30分"
    assert res.audio_path.name == f"{base}_v2ProPlus.wav"
    assert [Path(v["path"]).name for v in res.variants] == [f"{base}_未去杂音_v2ProPlus.wav", f"{base}_去杂音_v2ProPlus.wav"]
    assert res.srt_path.name == f"{base}_v2ProPlus.srt" and res.report_path.name == f"{base}_v2ProPlus.json"
    assert "模型：v2ProPlus" in audio_comment(res.audio_path)
    rep = json.loads(res.report_path.read_text(encoding="utf-8"))
    files = rep["models_used"][0]["files"]
    assert files[0]["file"] == "vt_e8_s80.pth"
    assert files[0]["fingerprint"] == hashlib.sha256(sov.read_bytes()).hexdigest()[:16]
    assert all(s["model"] == "v2ProPlus" for s in rep["segments"])
    # 换成 v4 训练的模型文件，存成 mp3
    use(b"04", "vt_v4_e8_s80.pth")
    res2 = wf.run_narrate(gcfg, project.voice, text, out=str(out / "第3课_10月05日09点31分.mp3"),
                          backend_name="gptsovits", candidates=1)
    base2 = "第3课_10月05日09点31分"
    assert res2.audio_path.name == f"{base2}_V4.mp3"
    assert [Path(v["path"]).name for v in res2.variants] == [f"{base2}_未去杂音_V4.mp3", f"{base2}_去杂音_V4.mp3"]
    assert res2.srt_path.name == f"{base2}_V4.srt" and res2.report_path.name == f"{base2}_V4.json"
    assert "模型：V4" in read_tags(res2.audio_path).get("comment", "")
    # 还没训练过：底模的文件头认不出来 → _模型未知（不猜）
    p2.update_models("gptsovits", {"selected": None})
    res3 = wf.run_narrate(gcfg, project.voice, _uniq("没有训练好的模型"), out=str(out / "第5课.wav"),
                          backend_name="gptsovits", quality="fast")
    assert res3.audio_path.name == "第5课_模型未知.wav"
    for name in _all_names(out):
        assert TEACHER_FILE_RE.match(name), name
