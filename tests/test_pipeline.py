"""端到端：素材准备 → 风格分析 → 挑选/校准 → 合成（用测试引擎，不需要显卡）。"""

import csv
import json
import shutil

from voicetwin import workflows as wf
from voicetwin.backends.base import get_backend
from voicetwin.synth.engine import Narrator

from conftest import make_cfg


def test_prepare_summary(prepared):
    cfg, project, summary = prepared
    assert summary["clips_kept"] >= 25
    assert set(summary["minutes_by_lang"]) == {"zh", "en"}
    assert summary["val_clips"] >= 1
    refs = project.load_references()
    assert refs and all(3.0 <= r["duration"] <= 10.0 for r in refs)
    assert {r["lang"] for r in refs} == {"zh", "en"}
    assert any(r["kind"] == "question" for r in refs)
    prof = project.load_profile()
    assert 3.5 < prof["rate"]["zh"]["p50"] < 5.5
    assert 130 < prof["pitch"]["zh"]["f0_median"] < 170
    assert 0.3 < prof["pauses"]["sentence"] < 1.2


def test_review_roundtrip(prepared, tmp_path):
    # 在副本上改（共用的 prepared 素材改了以后，后面的测试「确认训练素材」的记录就对不上了）
    _, shared, _ = prepared
    shutil.copytree(shared.root, tmp_path / "ws" / shared.voice)
    cfg = make_cfg(tmp_path / "ws")
    project = wf.open_project(cfg, shared.voice, must_exist=True)
    rows = list(csv.DictReader(open(project.csv_path, encoding="utf-8-sig")))
    target = next(r for r in rows if r["keep"] == "1" and r["split"] == "train")
    target["keep"] = "0"
    with open(project.csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summary = wf.apply_review(cfg, project.voice)
    assert summary["changed"]["keep"] == 1
    rec = next(r for r in project.load_manifest() if r["id"] == target["id"])
    assert rec["keep"] is False and rec["manual_keep"] is False
    # 再次运行过滤也不会把手动删除的片段恢复
    wf.apply_review(cfg, project.voice)
    rec = next(r for r in project.load_manifest() if r["id"] == target["id"])
    assert rec["keep"] is False


def test_incremental_prepare_skips_done_sources(prepared, lecture_dir):
    cfg, project, summary = prepared
    again = wf.run_prepare(cfg, project.voice, [str(lecture_dir)])
    assert again["clips_total"] == summary["clips_total"]


def test_select_calibrates_speed(prepared, tmp_path):
    cfg, project, _ = prepared
    slow = make_cfg(project.root.parent, backends={"dummy": {"rate": 4.0}})
    backend = get_backend("dummy", slow, project)
    from voicetwin.synth.select import select_and_calibrate

    with backend:
        info = select_and_calibrate(slow, project, backend, use_asr=False)
    assert info["speed"]["zh"] > 1.05  # 模型比本人慢 → 校准为加速
    project.update_models("dummy", {"speed": {}})


def test_narrate_cache_redo_srt(prepared, tmp_path):
    cfg, project, _ = prepared
    backend = get_backend("dummy", cfg, project)
    script = "# 标题\n\n大家好，今天我们学习函数。函数可以重复使用！\n\n你们明白了吗？[停顿=1.2]Let's continue with an example."
    with backend:
        r1 = Narrator(cfg, project, backend, quality="balanced").narrate(script, tmp_path / "a.wav")
        r2 = Narrator(cfg, project, backend, quality="balanced").narrate(script, tmp_path / "b.wav", redo=[2])
    assert r1.audio_path.exists() and r1.srt_path.exists()
    assert not any(s["cached"] for s in r1.segments)
    assert [s["cached"] for s in r2.segments] == [i != 1 for i in range(len(r2.segments))]
    srt = r1.srt_path.read_text(encoding="utf-8")
    assert "你们明白了吗？" in srt and "-->" in srt
    report = json.loads(r1.report_path.read_text(encoding="utf-8"))
    assert report["mean_speaker_sim"] is not None
    # 明确的 1.2 秒停顿
    seg = {s["text"]: s for s in r1.segments}
    q = seg["你们明白了吗？"]
    nxt = r1.segments[r1.segments.index(q) + 1]
    assert abs((nxt["start"] - q["end"]) - 1.2) < 0.02


def test_srt_timed_narration(prepared, tmp_path):
    cfg, project, _ = prepared
    srt = tmp_path / "timeline.srt"
    srt.write_text("1\n00:00:01,000 --> 00:00:03,000\n第一句话在一秒开始。\n\n"
                   "2\n00:00:08,000 --> 00:00:10,000\n第二句在八秒开始。\n", encoding="utf-8")
    res = wf.run_narrate(cfg, project.voice, str(srt), out=str(tmp_path / "t.wav"), quality="fast")
    starts = [s["start"] for s in res.segments]
    assert abs(starts[0] - 1.0) < 1e-3 and abs(starts[1] - 8.0) < 1e-3


def test_mp3_output(prepared, tmp_path):
    cfg, project, _ = prepared
    res = wf.run_narrate(cfg, project.voice, "测试一下输出 mp3 格式。", out=str(tmp_path / "x.mp3"), quality="fast")
    assert res.audio_path.suffix == ".mp3" and res.audio_path.exists()


def test_references_are_unique_sentences(prepared):
    from voicetwin.utils.textutil import normalize_for_cer

    _, project, _ = prepared
    texts = [normalize_for_cer(r["text"]) for r in project.load_references()]
    assert len(texts) == len(set(texts))  # 素材里重复出现的句子只选一次


def test_evaluate_whole_narration_has_no_false_alarms(prepared, tmp_path):
    from voicetwin.synth.select import evaluate_file

    cfg, project, _ = prepared
    script = "大家好，今天我们学习函数。\n\n函数可以重复使用。[停顿=1.5]\n\n我们来看一个例子。这是第二句话。"
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "n.wav"), quality="fast")
    out = evaluate_file(cfg, project, res.audio_path)
    assert "结论" in out and out["声纹相似度"] is not None
    assert out["提示"] == ["无"], out["提示"]


# ============================================================================ v0.1.6：档位、相似度、静音、两个版本、语速
import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402
import uuid  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from voicetwin.synth import engine as eng  # noqa: E402
from voicetwin.utils.audio import load_audio  # noqa: E402


def _uniq(text):
    return text + "编号" + "".join(str(int(c, 16) % 10) for c in uuid.uuid4().hex[:6]) + "。"


class FakeJudge:
    """可控的"像你本人（%）"：按调用顺序返回给定的百分比（用完后一直返回最后一个）。"""

    available = True
    reliable = True
    calibrated = True
    models = ["fake"]
    members = []

    def __init__(self, pcts):
        self.pcts = list(pcts)
        self.calls = 0

    def judge(self, wav, sr):
        p = self.pcts[min(self.calls, len(self.pcts) - 1)]
        self.calls += 1
        return {"pct": p, "pcts": {"fake": p}, "sims": {"fake": round(p / 125.0, 4)}, "sim": round(p / 125.0, 4)}

    def info(self):
        return {"models": ["fake"], "labels": ["fake"], "reliable": True, "calibration": {}, "definition": "", "note": ""}


def _use_judge(monkeypatch, judge):
    monkeypatch.setattr(eng.SimilarityJudge, "for_project", classmethod(lambda cls, cfg, project, **k: judge))


class FakeChecker:
    """可控的识别校验：按顺序返回 (错字率, 错字数)。"""

    seq = []

    def __init__(self, *a, **k):
        self.i = 0

    def check(self, wav, sr, text, lang):
        cer, errors = FakeChecker.seq[min(self.i, len(FakeChecker.seq) - 1)]
        self.i += 1
        return {"cer": cer, "hyp": "识别出来的字", "errors": errors, "units": 10, "engine": "fake", "strong": False}

    def strong(self, lang, text=""):
        return False

    def wants_paraformer(self, lang, text=""):
        return False

    def _load(self):
        return True

    def _load_paraformer(self):
        return False


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


def test_pauses_and_edges_are_absolute_silence(prepared, tmp_path):
    cfg, project, _ = prepared
    script = _uniq("第一句，停顿要是绝对的静音") + "\n\n" + _uniq("第二句话在这里") + _uniq("第三句也一样")
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "z.wav"), quality="fast")
    assert len(res.segments) >= 3
    wav, sr = _gaps_are_zero(res.audio_path, res.segments)
    assert np.any(wav != 0.0)


def test_trim_edges_removes_hiss_and_starts_at_zero():
    sr = 16000
    rng = np.random.default_rng(0)

    def hiss(n):
        return rng.normal(0, 0.003, n).astype(np.float32)

    t = np.arange(int(0.8 * sr)) / sr
    tone = (0.4 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
    wav = np.concatenate([hiss(int(0.5 * sr)), tone + hiss(len(tone)), hiss(int(0.6 * sr))])
    out = eng.trim_edges(wav, sr)
    assert out[0] == 0.0 and out[-1] == 0.0
    assert len(tone) <= len(out) <= len(tone) + int(0.12 * sr)  # 首尾杂音几乎全切掉
    assert eng.trim_edges(np.zeros(1000, np.float32), sr).size == 0


def test_trim_edges_keeps_onset_when_audio_starts_with_speech():
    """真实的 GPT-SoVITS 输出开头没有空白（第一个采样就是声音），后面补 0.3 秒的 0：
    不能把第一个字的开头淡掉，只允许 4 毫秒以内的防「咔哒」淡入。"""
    sr = 32000
    t = np.arange(int(0.8 * sr)) / sr
    tone = (0.4 * np.sin(2 * np.pi * 180 * t)).astype(np.float32)
    wav = np.concatenate([tone, np.zeros(int(0.3 * sr), np.float32)])
    out = eng.trim_edges(wav, sr)
    assert out[0] == 0.0 and out[-1] == 0.0
    head = out[int(0.005 * sr):int(0.030 * sr)]
    ref = tone[int(0.005 * sr):int(0.030 * sr)]
    assert np.allclose(head, ref, atol=1e-6)  # 5 毫秒以后和原来一模一样（以前要到 34 毫秒以后）


def test_denoise_falls_back_without_noisereduce(monkeypatch):
    monkeypatch.setitem(sys.modules, "noisereduce", None)  # import 会失败
    assert eng.denoise_light(np.ones(16000, np.float32) * 0.1, 16000) is None


def _fake_noisereduce(monkeypatch):
    nr = types.ModuleType("noisereduce")

    def reduce_noise(y, sr, y_noise=None, stationary=False, prop_decrease=1.0, **kw):
        return (np.asarray(y, dtype=np.float32) * 0.97).astype(np.float32)

    nr.reduce_noise = reduce_noise
    monkeypatch.setitem(sys.modules, "noisereduce", nr)
    return nr


def test_perfect_writes_two_versions_with_silent_pauses(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _fake_noisereduce(monkeypatch)
    monkeypatch.setattr("voicetwin.eval.metrics.Scorer.in_normal_range", lambda self, s, lang, speed=1.0: True)
    script = _uniq("完美档，第一句话，有逗号停顿") + "\n\n" + _uniq("完美档的第二句话")
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "课.wav"), quality="perfect")
    names = [v["name"] for v in res.variants]
    assert names == ["未去杂音", "去杂音"]
    for v in res.variants:
        assert Path(v["path"]).exists() and isinstance(v["score"], float) and isinstance(v["recommended"], bool)
        _gaps_are_zero(v["path"], res.segments)
    assert Path(res.variants[0]["path"]).name == "课_未去杂音.wav"
    assert Path(res.variants[1]["path"]).name == "课_去杂音.wav"
    assert res.audio_path.name == "课.wav"
    best = max(res.variants, key=lambda v: (v["score"], v["name"] == "未去杂音"))
    assert [v["name"] for v in res.variants if v["recommended"]] == [best["name"]]
    assert res.audio_path.read_bytes() == Path(best["path"]).read_bytes()
    report = json.loads(res.report_path.read_text(encoding="utf-8"))
    assert report["final"] == best["name"] and len(report["variants"]) == 2
    assert {v["rank"] for v in report["variants"]} == {1, 2}
    # 选另一个版本作为最终版本
    other = next(v for v in res.variants if not v["recommended"])
    out = wf.choose_variant(cfg, project.voice, str(res.report_path), other["name"])
    assert out["final"] == other["name"]
    assert res.audio_path.read_bytes() == Path(other["path"]).read_bytes()
    report = json.loads(res.report_path.read_text(encoding="utf-8"))
    assert report["final"] == other["name"] and [v["final"] for v in report["variants"]].count(True) == 1
    wf.choose_variant(cfg, project.voice, str(res.report_path), "A")
    assert res.audio_path.read_bytes() == Path(res.variants[0]["path"]).read_bytes()
    with pytest.raises(ValueError, match="没有"):
        wf.choose_variant(cfg, project.voice, str(res.report_path), "版本 C")


def test_perfect_without_noisereduce_keeps_one_version(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    monkeypatch.setitem(sys.modules, "noisereduce", None)
    monkeypatch.setattr("voicetwin.eval.metrics.Scorer.in_normal_range", lambda self, s, lang, speed=1.0: True)
    res = wf.run_narrate(cfg, project.voice, _uniq("没有降噪组件时只有一个版本"), out=str(tmp_path / "one.wav"),
                         quality="perfect")
    assert [v["name"] for v in res.variants] == ["未去杂音"] and res.variants[0]["recommended"]
    assert any("noisereduce" in w for w in res.warnings)
    assert res.audio_path.exists() and Path(res.variants[0]["path"]).exists()


def test_candidates_below_85_are_eliminated_and_similarity_dominates(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    judge = FakeJudge([70.0, 96.0, 86.0])
    _use_judge(monkeypatch, judge)
    res = wf.run_narrate(cfg, project.voice, _uniq("相似度排序测试"), out=str(tmp_path / "s.wav"), quality="balanced",
                         variants=False)
    seg = res.segments[0]
    assert seg["pct"] == 96.0 and seg["status"] == "✅" and not seg["flagged"]
    cands = seg["candidates"]
    assert [c["pct"] for c in cands] == [96.0, 86.0, 70.0]  # 从高到低排好
    assert [c["chosen"] for c in cands] == [True, False, False]
    assert [c["eliminated"] for c in cands] == [False, False, True]
    assert res.overall_pct == 96.0
    report = json.loads(res.report_path.read_text(encoding="utf-8"))
    assert report["similarity_filter"] is True and report["segments"][0]["candidates"][0]["chosen"]
    headers, rows = wf.narration_table(res.segments)
    assert headers == ["#", "句子", "像你本人（%）", "状态", "提示"]
    assert rows[0][0] == 1 and rows[0][2] == "96.0" and rows[0][3] == "✅"


def test_all_candidates_below_85_keeps_best_and_flags_red(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    judge = FakeJudge([80.0, 82.0, 81.0, 79.0])
    _use_judge(monkeypatch, judge)
    res = wf.run_narrate(cfg, project.voice, _uniq("都不够像的一句"), out=str(tmp_path / "r.wav"), quality="balanced",
                         variants=False)
    seg = res.segments[0]
    assert seg["status"] == "🔴" and seg["flagged"] and "低于 85%" in seg["hint"]
    assert seg["pct"] == 82.0
    assert seg["tries"] == 3 + 2 + 2  # 不够像 → 两轮重做
    assert res.flagged == [1]
    assert any("低于 85%" in w for w in res.warnings)
    assert all(c["eliminated"] for c in seg["candidates"])


def test_max_tier_prefers_correct_reading_over_similarity(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _use_judge(monkeypatch, FakeJudge([97.0] * 8 + [90.0, 96.0, 96.0]))
    FakeChecker.seq = [(0.3, 4)] * 8 + [(0.0, 0), (0.3, 4), (0.3, 4)]
    monkeypatch.setattr(eng, "CERChecker", FakeChecker)
    res = wf.run_narrate(cfg, project.voice, _uniq("极致档读错重做"), out=str(tmp_path / "m.wav"), quality="max",
                         variants=False)
    seg = res.segments[0]
    assert seg["tries"] == 8 + 3
    assert seg["cer"] == 0.0 and seg["pct"] == 90.0  # 读对的永远排在读错的前面
    assert not seg["flagged"]


def test_max_tier_short_error_floor(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _use_judge(monkeypatch, FakeJudge([97.0]))
    FakeChecker.seq = [(0.17, 1)]  # 6 个字错 1 个：可能只是识别误差，不算读错
    monkeypatch.setattr(eng, "CERChecker", FakeChecker)
    res = wf.run_narrate(cfg, project.voice, _uniq("短句"), out=str(tmp_path / "f.wav"), quality="max", variants=False)
    assert res.segments[0]["tries"] == 8 and not res.segments[0]["flagged"]


def test_max_tier_stops_early_when_clearly_good(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _use_judge(monkeypatch, FakeJudge([99.5]))
    FakeChecker.seq = [(0.0, 0)]
    monkeypatch.setattr(eng, "CERChecker", FakeChecker)
    res = wf.run_narrate(cfg, project.voice, _uniq("极致档提前结束"), out=str(tmp_path / "e.wav"), quality="max",
                         variants=False)
    assert res.segments[0]["tries"] == 4


def test_perfect_adaptive_stops_when_targets_met(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _use_judge(monkeypatch, FakeJudge([95.0] * 4 + [99.5] * 50))
    FakeChecker.seq = [(0.0, 0)]
    monkeypatch.setattr(eng, "CERChecker", FakeChecker)
    monkeypatch.setattr("voicetwin.eval.metrics.Scorer.in_normal_range", lambda self, s, lang, speed=1.0: True)
    res = wf.run_narrate(cfg, project.voice, _uniq("完美档提前停止"), out=str(tmp_path / "a.wav"), quality="perfect",
                         variants=False)
    seg = res.segments[0]
    assert seg["tries"] == 8 and seg["met"] is True and seg["pct"] == 99.5 and not seg["flagged"]
    assert any("达到了「完美」的严格标准" in n for n in res.notes)


def test_perfect_adaptive_hard_cap_and_flag(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    _use_judge(monkeypatch, FakeJudge([95.0]))
    FakeChecker.seq = [(0.0, 0)]
    monkeypatch.setattr(eng, "CERChecker", FakeChecker)
    monkeypatch.setattr("voicetwin.eval.metrics.Scorer.in_normal_range", lambda self, s, lang, speed=1.0: True)
    res = wf.run_narrate(cfg, project.voice, _uniq("完美档试满"), out=str(tmp_path / "c.wav"), quality="perfect",
                         variants=False)
    seg = res.segments[0]
    assert seg["tries"] == 20 and seg["met"] is False
    assert seg["flagged"] and "可能不够像" in seg["hint"] and seg["status"] == "⚠️"
    assert any("需要注意的句子：第 1 句" in n for n in res.notes)


def test_perfect_adaptive_stops_when_any_candidate_meets_targets(prepared, tmp_path, monkeypatch):
    """综合分最高的候选不一定达标（语速/音高偏差也扣分）：只要有一个候选达到全部严格标准就停，并且用达标的那个。"""
    from voicetwin.eval import metrics

    cfg, project, _ = prepared
    _use_judge(monkeypatch, FakeJudge([99.4] + [100.0] * 50))
    FakeChecker.seq = [(0.0, 0)]
    monkeypatch.setattr(eng, "CERChecker", FakeChecker)
    orig = metrics.Scorer.score

    def score(self, *a, **k):
        sc = orig(self, *a, **k)
        if sc.pct == 100.0:
            sc.total += 1.0  # 百分比更高、综合分也更高，但语速不在你平时的范围里
        return sc

    monkeypatch.setattr(metrics.Scorer, "score", score)
    monkeypatch.setattr(metrics.Scorer, "in_normal_range", lambda self, s, lang, speed=1.0: s.pct != 100.0)
    res = wf.run_narrate(cfg, project.voice, _uniq("完美档有一个达标就停"), out=str(tmp_path / "m.wav"),
                         quality="perfect", variants=False)
    seg = res.segments[0]
    assert seg["tries"] == 4 and seg["met"] is True and seg["pct"] == 99.4 and not seg["flagged"]
    # 都不达标时：提示写真正没达到的那一项（这里是语速/音调，不是「不够像」）
    _use_judge(monkeypatch, FakeJudge([100.0]))
    res2 = wf.run_narrate(cfg, project.voice, _uniq("完美档语速一直不对"), out=str(tmp_path / "m2.wav"),
                          quality="perfect", variants=False)
    seg2 = res2.segments[0]
    assert seg2["tries"] == 20 and seg2["met"] is False and "语速或音调" in seg2["hint"]


def test_similarity_target_pct_from_config(prepared):
    """配置文件里的 similarity.target_pct 要真的生效；synth.tiers.perfect.target_pct 更优先。"""
    cfg, project, _ = prepared
    backend = get_backend("dummy", cfg, project)
    base = dict(cfg.data) if hasattr(cfg, "data") else dict(cfg)
    n = eng.Narrator({**base, "similarity": {**(base.get("similarity") or {}), "target_pct": 95}}, project, backend,
                     quality="perfect", tier="high")
    assert n.target_pct == 95.0
    synth = {**(base.get("synth") or {}), "tiers": {"perfect": {"target_pct": 97}}}
    n2 = eng.Narrator({**base, "synth": synth, "similarity": {"target_pct": 95}}, project, backend, quality="perfect",
                      tier="high")
    assert n2.target_pct == 97.0
    n3 = eng.Narrator({**base, "similarity": {"target_pct": "auto"}}, project, backend, quality="perfect", tier="high")
    assert n3.target_pct == 99.0


def test_redo_clears_stale_denoised_cache(prepared, tmp_path, monkeypatch):
    """重新生成某一句后，旁边旧的「去杂音」缓存是旧句子做的：长度一样也不能再用。"""
    cfg, project, _ = prepared
    _fake_noisereduce(monkeypatch)
    monkeypatch.setattr("voicetwin.eval.metrics.Scorer.in_normal_range", lambda self, s, lang, speed=1.0: True)
    text = _uniq("重做以后去杂音版本也要跟着换")
    wf.run_narrate(cfg, project.voice, text, out=str(tmp_path / "r1.wav"), quality="perfect")
    backend = get_backend("dummy", cfg, project)
    n = eng.Narrator(cfg, project, backend, quality="perfect", tier="none")
    seg = n._segments(text)[0]
    plan = n._plan(seg)
    assert plan.cached and list(plan.wav_path.parent.glob(plan.wav_path.stem + ".dn*.wav"))
    n.synthesize_segment(seg, force=True)  # 和「只重新生成第几句」一样：同一个缓存文件写入新的一句
    assert not list(plan.wav_path.parent.glob(plan.wav_path.stem + ".dn*.wav"))
    # 直接检查 _denoised：缓存比这句的音频旧时不用它
    seg_wav = tmp_path / "seg.wav"
    w = (np.sin(np.linspace(0, 400, 16000)) * 0.3).astype(np.float32)
    eng.save_audio(seg_wav, w, 16000)
    cache = seg_wav.with_name(seg_wav.stem + ".dn16000.wav")
    eng.save_audio(cache, np.zeros_like(w), 16000, subtype="FLOAT")
    os.utime(cache, (1, 1))  # 比音频旧
    r = types.SimpleNamespace(path=seg_wav)
    out = n._denoised(r, w, 16000)
    assert out is not None and np.abs(out).max() > 0.1  # 重新算了，不是旧缓存（全是 0）


def test_quality_tiers_and_labels(prepared):
    cfg, project, _ = prepared
    assert [v for _, v in eng.quality_choices()] == ["fast", "balanced", "best", "max", "perfect"]
    assert eng.QUALITY_LABELS["max"].startswith("极致（") and eng.QUALITY_LABELS["perfect"].startswith("完美：每句最多试 20 次")
    assert set(eng.QUALITY_HELP) == set(eng.QUALITY_ORDER)
    assert eng.resolve_quality("完美") == "perfect" and eng.resolve_quality(eng.QUALITY_LABELS["max"]) == "max"
    assert eng.resolve_quality(["best"]) == "best" and eng.resolve_quality("不知道") == "balanced"
    assert eng.recommended_quality("high")[0] == "perfect" and eng.recommended_quality("mid")[0] == "perfect"
    assert eng.recommended_quality("low")[0] == "max" and eng.recommended_quality("none")[0] == "balanced"
    assert eng.resolve_quality("auto", tier="low") == "max"
    assert wf.recommended_quality("mid")[0] == "perfect" and "慢" in wf.recommended_quality("mid")[1]
    assert [v for _, v in wf.quality_choices()] == list(eng.QUALITY_ORDER) and "note" in wf.quality_help()
    backend = get_backend("dummy", cfg, project)
    low = Narrator(cfg, project, backend, quality="max", tier="low")
    assert low.n_candidates == 6 and low._n_aux() == 2 and any("显存较小" in n for n in low.notes)
    mid = Narrator(cfg, project, backend, quality="max", tier="mid")
    assert mid.n_candidates == 8 and mid._n_aux() == 3 and mid.use_asr
    perfect = Narrator(cfg, project, backend, quality="perfect", tier="high")
    assert perfect.adaptive and perfect.max_candidates == 20 and perfect.n_candidates == 4 and perfect.want_variants
    assert Narrator(cfg, project, backend, quality="perfect", tier="low").max_candidates == 12
    fast = Narrator(cfg, project, backend, quality="fast", tier="high")
    assert fast.n_candidates == 1 and not fast.use_asr and not fast.want_variants
    assert Narrator(cfg, project, backend, quality="max", asr_check=False, tier="mid").use_asr is False


def test_perfect_picks_reference_with_closest_length(prepared):
    from voicetwin.synth.script import ScriptSegment

    cfg, project, _ = prepared
    backend = get_backend("dummy", cfg, project)
    nar = Narrator(cfg, project, backend, quality="perfect", tier="high")
    nar.refs = [
        {"id": "short", "lang": "zh", "kind": "statement", "text": "好的我们开始。", "path": "a.wav"},
        {"id": "long", "lang": "zh", "kind": "statement", "text": "今天我们来学习一个非常重要而且很有意思的概念，请大家认真听讲。",
         "path": "b.wav"},
    ]
    short = ScriptSegment(text="好，下课。", display="好，下课。", lang="zh")
    long = ScriptSegment(text="接下来我们要讲的内容比较多，大家先把书翻到第三十页，然后跟着我一起看。", display="x", lang="zh")
    assert nar._ref_for(short)["id"] == "short" and nar._ref_for(long)["id"] == "long"
    best = Narrator(cfg, project, backend, quality="best")
    best.refs = nar.refs
    assert best._ref_for(long)["id"] == "short"  # 其它档：按分数第一条


class SpyBackend:
    """包一层测试引擎，记下每次合成时传给引擎的语速。"""

    def __init__(self, inner):
        self.inner = inner
        self.speeds = []

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def synthesize(self, req, out_path):
        self.speeds.append(req.speed)
        return self.inner.synthesize(req, out_path)


def test_speed_is_applied_inside_the_model_and_pauses_scale(prepared, tmp_path, monkeypatch):
    from voicetwin.style.prosody import f0_stats

    cfg, project, _ = prepared
    project.update_models("dummy", {"speed": {}})
    resampled = []
    real_resample = eng.resample
    monkeypatch.setattr(eng, "resample", lambda w, a, b: (resampled.append((a, b)), real_resample(w, a, b))[1])
    script = _uniq("语速测试的第一句话") + "\n\n" + _uniq("第二句话，用来测停顿") + _uniq("第三句话")
    out, f0 = {}, {}
    for speed in (0.85, 1.0, 1.2):
        spy = SpyBackend(get_backend("dummy", cfg, project))
        res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / f"v{speed}.wav"), quality="balanced",
                             speed=speed, backend=spy, variants=False)
        spy.inner.stop()
        assert spy.speeds and all(abs(s - speed) < 1e-9 for s in spy.speeds)  # 每个候选都把语速交给模型
        out[speed] = res
        wav, sr = load_audio(res.audio_path)
        f0[speed] = f0_stats(wav, sr)["f0_median"]
    assert all(a == b for a, b in resampled)  # 没有为了调语速去重采样波形
    semis = [abs(12 * np.log2(f0[s] / f0[1.0])) for s in (0.85, 1.2)]
    assert max(semis) < 0.5, semis  # 音高几乎不变
    assert out[1.2].duration < out[1.0].duration < out[0.85].duration

    def gaps(res):
        return [b["start"] - a["end"] for a, b in zip(res.segments, res.segments[1:])]

    for g085, g1 in zip(gaps(out[0.85]), gaps(out[1.0])):
        assert abs(g085 - g1 / 0.85) < 0.01  # 说得慢，停顿也按比例变长


def test_explicit_pause_is_not_scaled_by_speed(prepared, tmp_path):
    cfg, project, _ = prepared
    res = wf.run_narrate(cfg, project.voice, _uniq("明确的停顿") + "[停顿=1.2]" + _uniq("下一句"),
                         out=str(tmp_path / "ep.wav"), quality="fast", speed=0.8)
    a, b = res.segments[0], res.segments[1]
    assert abs((b["start"] - a["end"]) - 1.2) < 0.02


def test_speed_slider_mapping():
    assert wf.slider_to_speed(0) == 1.0 and wf.slider_to_speed(-20) == 1.2 and wf.slider_to_speed(15) == 0.85
    assert wf.slider_to_speed(-99) == 1.3 and wf.slider_to_speed(None) == 1.0
    assert wf.speed_note(0) == "当前：和你原声一样"
    assert wf.speed_note(-20) == "当前：比你原声快 20%" and wf.speed_note(15) == "当前：比你原声慢 15%"
    assert "建议" in wf.speed_note(25)


def test_preview_speed(prepared):
    cfg, project, _ = prepared
    res = wf.preview_speed(cfg, project.voice, "试听语速用这一句。后面这句不会读到这里来的。", value=-10)
    assert res.audio_path.exists() and res.audio_path.name == "试听语速_快10%.wav"
    assert [s["text"] for s in res.segments] == ["试听语速用这一句。"]
    res2 = wf.preview_speed(cfg, project.voice, "", value=0)
    assert res2.audio_path.name == "试听语速_原速.wav" and res2.segments[0]["text"] == wf.DEFAULT_SAMPLE_ZH


def _fake_voice(cfg, name, trained=False, clips=True, models_backend="gptsovits"):
    import soundfile as sf

    project = wf.Project(cfg, name).ensure()
    project.save_manifest([{"id": "c1", "path": "clips/c1.wav", "keep": True, "text": "你好", "duration": 3.0}])
    if clips:
        sf.write(str(project.refs_dir / "c1.wav"), np.zeros(16000, np.float32), 16000)
        project.write_json(project.references_path, [{"id": "c1", "path": "references/c1.wav", "lang": "zh",
                                                      "kind": "statement", "text": "你好"}])
        project.write_json(project.root / "prepare_summary.json", {"clips_kept": 40, "minutes_kept": 12.5})
    if trained:
        project.update_models(models_backend, {"selected": {"id": "s8-g15"}})
    return project


def test_voice_library(tmp_path):
    cfg = make_cfg(tmp_path / "ws", backend="gptsovits")
    _fake_voice(cfg, "已训练", trained=True)
    time.sleep(0.05)
    _fake_voice(cfg, "没训练")
    time.sleep(0.05)
    _fake_voice(cfg, "空的", clips=False)
    lib = wf.voice_library(cfg)
    assert [v["no"] for v in lib] == [1, 2, 3]
    by = {v["voice"]: v for v in lib}
    assert by["已训练"]["status"] == "✅ 已训练，可以生成" and by["已训练"]["trained"] is True
    assert by["已训练"]["best_model"] == "s8-g15"
    assert by["没训练"]["status"] == "⚠️ 素材已准备，还没训练" and by["没训练"]["trained"] is False
    assert by["空的"]["status"] == "⏳ 还没准备素材"
    assert by["没训练"]["minutes"] == 12.5 and by["没训练"]["clips_kept"] == 40
    assert Path(by["没训练"]["main_reference"]).is_absolute() and Path(by["没训练"]["main_reference"]).exists()
    assert by["空的"]["main_reference"] == ""
    assert isinstance(by["已训练"]["modified"], float)
    assert time.strftime("%Y-%m-%d", time.localtime()) in by["已训练"]["modified_text"]
    assert lib[0]["voice"] == "空的"  # 最近改过的排在前面
    rows = wf.voice_library_rows(cfg)
    assert [r[0] for r in rows] == [1, 2, 3] and len(rows[0]) == len(wf.VOICE_LIBRARY_HEADERS)
    assert "12.5 分钟 / 40 条" in [r[2] for r in rows]
    zero_shot = make_cfg(tmp_path / "ws", backend="dummy")
    assert {v["voice"]: v for v in wf.voice_library(zero_shot)}["没训练"]["status"].startswith("✅ 素材已准备")


def test_blind_test_build_and_grade(prepared):
    cfg, project, _ = prepared
    rec = []
    out = wf.build_blind_test(cfg, project.voice, n=3, quality="fast", progress=lambda f, m: rec.append((f, m)), seed=7)
    fr = [f for f, _ in rec]
    assert fr == sorted(fr) and fr[-1] == 1.0
    d = Path(out["dir"])
    assert d.name.startswith("盲听测试_") and out["count"] == 2 * out["n_real"]
    assert [it["file"] for it in out["items"]] == [f"{i:02d}.wav" for i in range(1, out["count"] + 1)]
    assert all((d / it["file"]).exists() and "truth" not in it for it in out["items"])
    # 答案不能放在要发给听众的文件夹里，放在旁边
    assert not any("答案" in p.name for p in d.iterdir()) and not (d / "答案.json").exists()
    answer_file = Path(out["answer_path"])
    assert answer_file.parent == d.parent and answer_file.name == d.name + wf.BLIND_ANSWER_SUFFIX
    assert wf.blind_answer_path(d) == answer_file
    answers = json.loads(answer_file.read_text(encoding="utf-8"))
    truths = [a["truth"] for a in answers["items"]]
    assert truths.count("真人") == truths.count("生成") == out["n_real"]
    card = (d / "听众答题卡.txt").read_text(encoding="utf-8-sig")
    assert f"共 {out['count']} 段" in card and "01. ________（真人 / 生成）" in card and "批改收上来的答题卡" in card
    assert [t["dir"] for t in wf.list_blind_tests(cfg, project.voice)][0] == str(d)
    # 收上来的答题卡直接贴文字也能批改
    typed = "\n".join(f"{a['no']:02d}. {a['truth']}（真人 / 生成）" for a in answers["items"])
    assert wf.grade_blind_test(out["dir"], typed)["accuracy"] == 1.0
    # 所有的都填"真人"：正确率 50%，听众基本分辨不出
    g = wf.grade_blind_test(out["dir"], {i: "真人" for i in range(1, out["count"] + 1)})
    assert g["accuracy"] == 0.5 and "基本分辨不出" in g["verdict"] and g["total"] == out["count"]
    perfect = wf.grade_blind_test(out["dir"], [a["truth"] for a in answers["items"]])
    assert perfect["accuracy"] == 1.0 and "容易分辨" in perfect["verdict"] and perfect["tips"]
    none = wf.grade_blind_test(out["dir"], {})
    assert none["accuracy"] is None and none["answered"] == 0


def test_verify_files_ranked_table(prepared, tmp_path):
    cfg, project, _ = prepared
    res = wf.run_narrate(cfg, project.voice, _uniq("机器鉴别用的句子"), out=str(tmp_path / "g.wav"), quality="fast")
    defaults = wf.verify_defaults(cfg, project.voice)
    assert defaults["originals"] and all(Path(p).exists() for p in defaults["generated"])
    gens = [str(res.audio_path)] + [str(project.abspath(s["clip"])) for s in res.segments]
    out = wf.verify_files(cfg, project.voice, gens)
    assert out["count"] == len(gens) and out["headers"][:2] == ["#", "文件"] and "综合（%）" in out["headers"]
    assert [r[0] for r in out["table"]] == list(range(1, len(gens) + 1))
    pcts = [r["pct"] for r in out["rows"]]
    assert pcts == sorted(pcts, reverse=True) and [r["rank"] for r in out["rows"]] == list(range(1, len(gens) + 1))
    with_orig = wf.verify_files(cfg, project.voice, gens, originals=defaults["originals"][:3])
    assert with_orig["originals"] and with_orig["count"] == len(gens)
    with pytest.raises(ValueError):
        wf.verify_files(cfg, project.voice, [str(tmp_path / "没有.wav")])


def test_evaluate_reports_calibrated_percentage(prepared, tmp_path):
    from voicetwin.synth.select import evaluate_file

    cfg, project, _ = prepared
    res = wf.run_narrate(cfg, project.voice, "评估百分比的一句话。", out=str(tmp_path / "e.wav"), quality="fast")
    out = evaluate_file(cfg, project, res.audio_path)
    assert "像你本人（%）" in out and out["像你本人（%）"] is not None and 0 <= out["像你本人（%）"] <= 100
    assert "说明" in out


def test_doctor_rows_sorted_and_quick_check(tmp_path):
    from fake_gptsovits import build_fake_root

    rows = [{"item": "a", "status": "✅", "detail": ""}, {"item": "b", "status": "⚠️", "detail": "", "optional": True},
            {"item": "c", "status": "❌", "detail": ""}, {"item": "d", "status": "⚠️", "detail": ""},
            {"item": "e", "status": "✅", "detail": "", "optional": True}]
    assert [r["item"] for r in wf.sort_doctor_rows(rows)] == ["c", "d", "a", "b", "e"]
    headers, table, total = wf.doctor_table(rows)
    assert [r[0] for r in table] == [1, 2, 3, 4, 5] and "共 5 项" in total and "可选，不用管" in table[3][3]
    root = build_fake_root(tmp_path / "GSV")
    (root / "GPT_SoVITS/pretrained_models/s1v3.ckpt").unlink()
    cfg = make_cfg(tmp_path / "ws", backend="gptsovits", backends={"gptsovits": {"root": str(root),
                                                                                 "python": sys.executable}})
    t0 = time.time()
    problems = wf.quick_check(cfg)
    assert time.time() - t0 < 1.0
    assert any("s1v3.ckpt" in p for p in problems)
    assert not (Path(cfg["workspace"]) / "__quick_check__").exists()


def test_doctor_marks_optional_rows(tmp_path):
    rows = wf.doctor(make_cfg(tmp_path / "ws", backend="gptsovits"))
    by = {r["item"]: r for r in rows}
    assert all("optional" in r for r in rows)
    assert by["funasr（中文识别、查错字，可选）"]["optional"] is True
    assert any(r["item"].startswith("引擎 ") and r["optional"] for r in rows)  # 不是默认引擎的都是可选
    assert not by["numpy"]["optional"]



def test_doctor_hides_third_party_import_warnings(tmp_path, monkeypatch, capfd):
    """老师的整合包里 funasr 导入时会打印 SyntaxWarning / FutureWarning，夹在检查结果前面像出错：检查时不显示。"""
    import sys as _sys
    import warnings

    pkg = tmp_path / "fakemods"
    pkg.mkdir()
    (pkg / "funasr.py").write_text(
        "import warnings\n"
        "vad = 1\n"
        "if vad is not -2:\n"  # 和 funasr 一样：编译时就会出 SyntaxWarning
        "    pass\n"
        "warnings.warn('torch.cuda.amp.autocast(args...) is deprecated', FutureWarning)\n"
        "__version__ = '1.0.27'\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(pkg))
    monkeypatch.delitem(_sys.modules, "funasr", raising=False)
    monkeypatch.setattr(_sys, "dont_write_bytecode", True)
    with warnings.catch_warnings(record=True) as shown:
        warnings.simplefilter("always")  # 平时会显示的警告都记下来；doctor 自己要把它们关掉
        rows = {r["item"]: r for r in wf.doctor(make_cfg(tmp_path / "ws"))}
    assert rows["funasr（中文识别、查错字，可选）"]["detail"] == "1.0.27"
    assert not [w for w in shown if "fakemods" in str(w.filename)], [str(w.message) for w in shown]
    assert "Warning" not in capfd.readouterr().err


def test_whisper_download_shows_megabytes(tmp_path, monkeypatch):
    from voicetwin.data import asr

    monkeypatch.setattr(asr, "hf_cache_dir", lambda: tmp_path / "hub")
    fw = types.ModuleType("faster_whisper")

    class WhisperModel:
        def __init__(self, name, device="cpu", compute_type="int8"):
            d = tmp_path / "hub" / f"models--Systran--faster-whisper-{name}" / "blobs"
            d.mkdir(parents=True)
            for i in range(3):
                (d / f"part{i}.incomplete").write_bytes(b"0" * (1024 * 1024))
                time.sleep(0.2)

    fw.WhisperModel = WhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fw)
    msgs = []
    tr = asr.Transcriber({"engine": "faster-whisper", "model": "small", "device": "cpu"})
    tr.progress = lambda f, m: msgs.append((f, m))
    tr._load()
    assert any("MB" in m for _, m in msgs)
    assert all(0.40 <= f <= 0.44 for f, _ in msgs)


def test_cer_details_counts_errors():
    from voicetwin.eval.metrics import cer_details

    assert cer_details("今天天气很好。", "今天天气很好") == (0.0, 0, 6)
    rate, errors, units = cer_details("我们今天讲十个函数", "我们今天讲个函数")
    assert errors == 1 and units == 9 and abs(rate - 1 / 9) < 1e-9
    assert cer_details("2024年的课", "二零二四年的课")[1] == 0
    try:
        import pypinyin  # noqa: F401

        homophone_errors = 0  # 有 pypinyin：同音字不算错
    except ImportError:
        homophone_errors = 1
    assert cer_details("今天天气很好", "今天天汽很好")[1] == homophone_errors


def test_paraformer_not_used_for_sentences_with_english(monkeypatch):
    from voicetwin.eval import metrics

    monkeypatch.setattr(metrics, "_has_module", lambda mod: True)
    checker = metrics.CERChecker("auto", vram_tier="mid")
    assert checker.wants_paraformer("zh", "今天我们学习列表。")
    assert not checker.wants_paraformer("zh", "今天我们学习 Python 的列表。")  # Paraformer 拼不出英文
    assert not checker.wants_paraformer("en", "Hello there.")
    assert checker.whisper_model() == "large-v3-turbo" and metrics.CERChecker("auto", vram_tier="low").whisper_model() == "small"
    assert checker.strong("zh", "今天") and checker.strong("en", "Hi") and not metrics.CERChecker("small").strong("en")
    assert metrics.engine_is_strong("paraformer") and metrics.engine_is_strong("whisper-large-v3-turbo")
    assert not metrics.engine_is_strong("whisper-small") and not metrics.engine_is_strong("")


class FailingBackend(SpyBackend):
    """每次合成都失败的引擎（用来看报错是不是说人话）。"""

    def __init__(self, inner, message):
        super().__init__(inner)
        self.message = message
        self.calls = 0

    def synthesize(self, req, out_path):
        self.calls += 1
        raise RuntimeError(self.message)


def test_failed_sentence_reports_real_reason(prepared, tmp_path):
    cfg, project, _ = prepared
    bad = FailingBackend(get_backend("dummy", cfg, project), "GPT-SoVITS 合成失败：参考音频在3~10秒范围外")
    with pytest.raises(RuntimeError, match=r"第 1 句没能生成（原因："):
        wf.run_narrate(cfg, project.voice, _uniq("一直失败的一句"), out=str(tmp_path / "x.wav"), quality="balanced",
                       backend=bad)
    assert bad.calls == 3 + 2 + 2  # 普通错误：每个候选都试过
    bad.inner.stop()


def test_fatal_error_stops_trying_other_candidates(prepared, tmp_path):
    cfg, project, _ = prepared
    oom = FailingBackend(get_backend("dummy", cfg, project), "torch.cuda.OutOfMemoryError: CUDA out of memory.")
    with pytest.raises(RuntimeError, match="第 1 句没能生成"):
        wf.run_narrate(cfg, project.voice, _uniq("显存不够的一句"), out=str(tmp_path / "y.wav"), quality="balanced",
                       backend=oom)
    assert oom.calls == 1  # 显存不够：换种子也没用，马上停
    oom.inner.stop()


def test_stop_button_interrupts_narration(prepared, tmp_path):
    progress = pytest.importorskip("voicetwin.utils.progress")
    cfg, project, _ = prepared
    progress.request_cancel()
    try:
        with pytest.raises(progress.TaskCancelled):
            wf.run_narrate(cfg, project.voice, _uniq("点了停止"), out=str(tmp_path / "s.wav"), quality="fast")
    finally:
        progress.clear_cancel()
