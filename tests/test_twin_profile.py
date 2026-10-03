"""「一模一样」档：实测你本人的说话习惯（voicetwin/style/twin_profile.py）和参考录音库（data/references.build_reference_bank）。

设计见 research/一模一样/设计方案原文.md 的 P3 和 §5.1。只用处理器、不联网。"""

import json
import shutil

import numpy as np
import pytest
import soundfile as sf

from voicetwin import workflows as wf
from voicetwin.data import references as R
from voicetwin.data.slicer import find_segments
from voicetwin.style import twin_profile as tp
from voicetwin.utils.audio import mask_runs, save_audio, silent_runs, speech_runs

SR = 16000


@pytest.fixture
def voice(prepared, tmp_path):
    """准备好的测试声音复制一份（不改共用的那份）。"""
    from conftest import make_cfg

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    _no_bank(ws / project.voice)
    cfg2 = make_cfg(ws)
    return cfg2, wf.Project(cfg2, project.voice)


def _no_bank(root):
    """共用的测试声音可能已经被别的测试（「一模一样」生成时）建过参考录音库：复制出来的这份从没有库开始。
    第 8 步起生成前的准备会建带声纹的库，顺便填 twin_profile.json 的音色变化（deltas.timbre）：也一起去掉。"""
    (root / "refs_bank.json").unlink(missing_ok=True)
    (root / "cache" / "bank_emb.npz").unlink(missing_ok=True)
    prof_path = root / "twin_profile.json"
    if prof_path.exists():
        prof = json.loads(prof_path.read_text(encoding="utf-8"))
        if (prof.get("deltas") or {}).get("timbre") is not None:
            prof["deltas"]["timbre"] = None
            prof_path.write_text(json.dumps(prof, ensure_ascii=False), encoding="utf-8")
    (root / "cache" / "bank_emb.npz").unlink(missing_ok=True)
    shutil.rmtree(root / "references" / "bank", ignore_errors=True)


def _truth_pauses():
    """测试讲课录音（conftest.make_lecture）里真实的停顿长度：同样的种子、不加噪声时数字静音有多长。"""
    from conftest import SENTENCES
    from voicetwin.backends.workers.dummy_worker import synth_speech

    sr = 44100
    rng = np.random.default_rng(1)
    lead, trail, inner, gaps = [], [], [], []
    for rep in range(3):
        for i, s in enumerate(SENTENCES):
            w = synth_speech(s, sr=sr, seed=rep * 100 + i + 1000, f0=150.0, noise=0.0)
            nz = np.flatnonzero(w != 0)
            lead.append(nz[0] / sr)
            trail.append((len(w) - 1 - nz[-1]) / sr)
            for a, b in mask_runs(w == 0, int(0.1 * sr)):
                if a > 0 and b < len(w):
                    inner.append((b - a) / sr)
            gaps.append(rng.uniform(0.4, 1.0))
    sentence = [trail[k] + gaps[k] + lead[k + 1] for k in range(len(gaps) - 1)]
    return float(np.median(inner)), float(np.median(sentence))


# ---------------------------------------------------------------------------- 测试声音（素材准备时就量好）
def test_prepare_writes_twin_profile_with_measured_habits(prepared, voice):
    _, project, _ = prepared
    assert (project.root / tp.TWIN_PROFILE_FILE).exists()  # 素材准备完顺便量好了
    _, proj = voice
    prof = tp.build_twin_profile(proj)
    assert prof["version"] == tp.TWIN_PROFILE_VERSION and prof["source"] == "raw" and prof["clips"] >= 20
    comma_truth, sentence_truth = _truth_pauses()
    comma = prof["pauses"]["comma"]
    sentence = prof["pauses"]["sentence"]
    assert comma["n"] >= 8 and 0.19 <= comma["median"] <= 0.29
    assert abs(comma["median"] - comma_truth) <= 0.04
    # 句子之间：真实的数字静音是 句末停顿 + 句子之间的空白 + 下一句开头（约 1.2 秒），重新量的和它差不到 0.06 秒
    # （原来 profile.json 用字幕时间算的「句号 0.77 秒」少算了句子音频里自带的静音）
    assert sentence["n"] >= 20 and abs(sentence["median"] - sentence_truth) <= 0.06
    assert sentence["n_final"] >= 20 and comma["p_pause"] == 1.0
    assert 140 <= prof["prosody"]["f0_median_hz"]["value"] <= 160
    # 每个统计都带 n；少于 8 个时值是 null
    assert prof["pauses"]["enum"] == {**prof["pauses"]["enum"], "n": 0, "q": None, "median": None}
    assert prof["deltas"]["clause"]["f0_med_st"] == {"mean": None, "sd": None, "n": 0}
    assert prof["deltas"]["sentence"]["f0_med_st"]["n"] >= 8 and prof["deltas"]["timbre"] is None
    assert prof["loudness"]["n"] >= 8 and prof["loudness"]["sd"] is not None
    assert prof["edges"]["offset_ms"]["n"] >= 8 and len(prof["ltas"]["mean"]) == 22
    st = prof["prosody"]["groups"]["statement|lt10"]["features"]["f0_med_st"]
    assert st["n"] >= 8 and st["from"] == "statement|lt10"
    q = prof["prosody"]["groups"]["question|ge30"]["features"]
    assert q["final_slope"]["from"] in (None, "question|all")  # 句末升降不借陈述句的
    assert q["f0_range_st"]["from"] in ("question|all", "statement|ge30", "statement|all")


def test_signature_unchanged_means_no_work(voice, monkeypatch):
    _, proj = voice
    first = tp.build_twin_profile(proj)
    monkeypatch.setattr(tp, "collect_clips", lambda *a, **k: pytest.fail("素材没变，不该重新量"))
    assert tp.build_twin_profile(proj) == first


def test_json_is_deterministic(voice):
    _, proj = voice
    path = proj.root / tp.TWIN_PROFILE_FILE
    tp.build_twin_profile(proj, force=True)
    a = path.read_bytes()
    tp.build_twin_profile(proj, force=True)  # 用缓存
    b = path.read_bytes()
    (proj.cache_dir / tp.CLIP_CACHE_FILE).unlink()
    (proj.cache_dir / tp.SOURCE_CACHE_FILE).unlink()
    tp.build_twin_profile(proj, force=True)  # 全部重新量
    assert a == b == path.read_bytes()
    assert b"NaN" not in a and json.loads(a.decode("utf-8"))["signature"]


def test_raw_deleted_falls_back_to_clips(voice):
    _, proj = voice
    before = tp.build_twin_profile(proj)
    for f in proj.raw_dir.glob("*.wav"):
        f.unlink()
    prof = tp.build_twin_profile(proj)  # 原始录音没了：signature 跟着变，自动重算
    assert prof["signature"] != before["signature"]
    assert prof["source"] == "clips" and prof["sources"] == {"raw": 0, "clips": 1}
    assert prof["pauses"]["sentence"]["n_final"] == 0  # 片段后面的停顿量不了（切片记的偏长，不用）
    assert prof["pauses"]["comma"]["n"] >= 8  # 片段里面的停顿照样量


def test_too_few_clips_gives_null(voice):
    _, proj = voice
    recs = proj.load_manifest()
    for r in recs[5:]:
        r["deleted"], r["keep"] = True, False
    proj.save_manifest(recs)
    prof = tp.build_twin_profile(proj)
    assert prof["clips"] == 5
    assert prof["prosody"]["f0_median_hz"] == {"value": None, "n": 5}
    assert prof["pauses"]["sentence"]["q"] is None and prof["pauses"]["sentence"]["n"] < 8
    assert prof["duration_model"]["coef"] is None and prof["duration_model"]["global_rate"] is None
    assert prof["loudness"]["sd"] is None and prof["inner_pause_p97"]["value"] is None
    assert all(v is None for v in prof["ltas"]["mean"])
    assert tp.expected_voiced(prof["duration_model"], "今天我们学习。") is None  # 没测出来就是没有


def test_bad_inputs_never_crash(voice):
    _, proj = voice
    recs = proj.load_manifest()
    src = recs[0]
    extra = []
    for k, wav in enumerate([np.zeros(SR * 2, np.float32), np.zeros(int(SR * 0.05), np.float32),
                             0.3 * np.sin(np.arange(int(SR * 0.2)) * 0.2).astype(np.float32)]):
        path = proj.clips_dir / f"bad_{k}.wav"
        save_audio(path, wav, SR)
        extra.append(dict(src, id=f"bad_{k}", path=proj.relpath(path), start=None, end=None, duration=len(wav) / SR))
    extra.append(dict(src, id="no_text", text=""))
    extra.append(dict(src, id="missing_file", path="clips/does_not_exist.wav"))
    extra.append(dict(src, id="deleted_row", deleted=True, keep=False))
    proj.save_manifest(recs + extra)
    prof = tp.build_twin_profile(proj)
    assert prof["clips"] >= len(recs) and prof["clips_skipped"] >= 3
    feat = tp.acoustic_features(np.full(SR, np.nan, np.float32), SR)  # NaN 的音频：量不出来，不报错
    assert feat["f0_med_hz"] is None and feat["voiced"] == 0.0
    assert tp.clip_features(np.zeros(100, np.float32), SR, "好的。")["rate"] is None
    proj.save_manifest([])
    empty = tp.build_twin_profile(proj)
    assert empty["clips"] == 0 and empty["pauses"]["sentence"]["q"] is None
    assert empty["duration_model"]["ok"] is False


# ---------------------------------------------------------------------------- 已知停顿的合成录音
def _burst(sec, f0=210.0, level=0.25, decay=0.06):
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


def _known_gap_project(tmp_path, n=160, seed=7):
    """research/一模一样/scripts/gap_bias_sim.py 的做法：像说话的声音之间放已知长度的数字静音，用真的切片程序切开，
    每段一句话（字数和长度成正比）。返回 (项目, 真实停顿, 切片记下的「片段后面的停顿」)。"""
    from conftest import make_cfg

    rng = np.random.default_rng(seed)
    proj = wf.Project(make_cfg(tmp_path / "ws"), "合成")
    proj.ensure()
    pieces, spans, gaps, t = [np.zeros(int(0.5 * SR), np.float32)], [], [], 0.5
    for _ in range(n):
        b = _burst(rng.uniform(1.2, 4.0))
        pieces.append(b)
        spans.append((t, t + len(b) / SR))
        t += len(b) / SR
        g = float(np.exp(rng.normal(np.log(0.45), 0.45)))
        z = int(g * SR)
        gaps.append(z / SR)
        pieces.append(np.zeros(z, np.float32))
        t += z / SR
    wav = np.concatenate(pieces)
    wav += rng.normal(0, 1e-4, len(wav)).astype(np.float32)
    sid = "lec_abc123"
    save_audio(proj.raw_dir / f"{sid}.wav", wav, SR)
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
                     "gap_after": s.gap_after, "forced_cuts": s.forced_cuts, "seg_mode": "energy"})
    proj.save_manifest(recs)
    return proj, gaps, [s.gap_after for s in segs if s.gap_after]


def test_remeasured_sentence_pauses_match_truth_and_legacy_is_biased(tmp_path):
    proj, gaps, legacy = _known_gap_project(tmp_path)
    prof = tp.build_twin_profile(proj)
    truth = float(np.median(gaps))
    st = prof["pauses"]["sentence"]
    assert prof["source"] == "raw" and st["n"] >= 150  # 几乎每个停顿都量到了（片段里面的 + 片段后面的）
    assert st["n_inner"] > 0 and st["n_final"] > 0
    assert abs(st["median"] - truth) <= 0.04
    assert float(np.median(legacy)) > truth + 0.06  # 只在切开的地方记的停顿：系统性地偏长
    assert prof["pauses"]["hesitation"]["n"] <= 3
    # 分块读文件和整个读进来量的停顿一样
    raw = proj.raw_dir / "lec_abc123.wav"
    w, sr = sf.read(str(raw), dtype="float32")
    in_mem = tp.source_gaps(w, sr)
    streamed, total = tp.source_gaps_file(raw)
    assert len(in_mem) == len(streamed) >= 150 and abs(total - len(w) / sr) < 1e-9
    assert np.allclose(np.asarray(in_mem), np.asarray(streamed), atol=1e-9)


# ---------------------------------------------------------------------------- 标点和停顿对齐
def test_align_pauses_matches_marks_and_finds_hesitations():
    text = "首先我们看，这个例子；然后大家想一想。最后总结一下"
    marks = tp.text_marks(text)
    assert [c for _, c in marks] == ["comma", "colon_semi", "sentence"]
    pauses = [(marks[0][0] + 0.03, 0.25), (0.62, 0.4), (marks[2][0] - 0.02, 0.7), (0.9, 0.3)]
    pairs, hes, counts = tp.align_pauses(text, pauses)
    assert pairs == [("comma", 0.25), ("sentence", 0.7)]
    assert sorted(hes) == [0.3, 0.4] and counts == {"comma": 1, "enum": 0, "colon_semi": 1, "sentence": 1}
    # 位置差超过 0.12：不硬对
    pairs, hes, _ = tp.align_pauses("一二三四五，六七八九十", [(0.8, 0.3)])
    assert pairs == [] and hes == [0.3]
    # 数字里的点和逗号、缩写不是停顿；连着的标点算一个，取最强的
    assert [c for _, c in tp.text_marks("价格是3.14元，一共1,000个，e.g. 例子")] == ["comma", "comma"]
    assert [c for _, c in tp.text_marks("真的吗？！我们继续、好吗")] == ["sentence", "enum"]
    assert tp.final_mark("好的。”") == "sentence" and tp.final_mark("我们今天") is None
    assert tp.duration_features("我们今天，学习 cat dog 12。") == [6.0, 2.0, 2.0, 1.0]


# ---------------------------------------------------------------------------- 语速模型
def test_duration_model_recovers_coefficients_and_falls_back():
    rng = np.random.default_rng(3)
    true = {"const": 0.3, "n_cjk": 0.2, "en_syllables": 0.25, "n_digits": 0.35, "n_clause_punct": 0.15}
    X = np.column_stack([rng.integers(5, 40, 400), rng.integers(0, 12, 400), rng.integers(0, 4, 400),
                         rng.integers(0, 4, 400)]).astype(float)
    y = true["const"] + X @ np.array([true[k] for k in tp.DURATION_TERMS[1:]]) + rng.normal(0, 0.03, 400)
    m = tp.fit_duration_model(X.tolist(), y.tolist())
    assert m["ok"] and m["n"] == 400 and m["r2"] > 0.99
    for k, v in true.items():
        assert abs(m["coef"][k] - v) <= 0.05 * v, k
    text = "我们今天，学习 cat dog 12。"
    want = true["const"] + 6 * 0.2 + 2 * 0.25 + 2 * 0.35 + 1 * 0.15
    assert abs(tp.expected_voiced(m, text) - want) < 0.05 * want
    # 拟合得不好（时长和文字没关系）：ok = False，用整体语速
    bad_y = rng.uniform(1.0, 8.0, 400)
    bad = tp.fit_duration_model(X.tolist(), bad_y.tolist())
    assert bad["ok"] is False and bad["r2"] < 0.3 and bad["global_rate"] > 0
    assert tp.expected_voiced(bad, text) == pytest.approx(10 / bad["global_rate"])
    # 句子太少（< 50）：也不 ok
    few = tp.fit_duration_model(X[:30].tolist(), y[:30].tolist())
    assert few["ok"] is False and few["n"] == 30 and few["coef"] is not None


# ---------------------------------------------------------------------------- 接到工作流里
def test_review_save_updates_profile_cheaply_and_failures_are_not_fatal(voice, monkeypatch):
    from voicetwin.data import review

    cfg, proj = voice
    before = tp.build_twin_profile(proj)
    rec = next(r for r in proj.load_manifest() if "，" in r["text"])
    review.set_draft(proj, rec["id"], text=rec["text"].replace("，", "、", 1))
    wf.review_save(cfg, proj.voice)  # 保存时顺便更新（声音特征有缓存，只重新对齐标点）
    after = tp.load_twin_profile(proj)
    assert after["signature"] != before["signature"]
    assert after["pauses"]["enum"]["n_marks"] == 1 and after["pauses"]["comma"]["n_marks"] == \
        before["pauses"]["comma"]["n_marks"] - 1
    # 第一次（还没量过）要量的太多：保存时先不量（留到素材准备 / 生成「一模一样」），保存照样成功
    (proj.cache_dir / tp.CLIP_CACHE_FILE).unlink()
    monkeypatch.setattr(wf, "TWIN_REVIEW_MAX_NEW_CLIPS", 3)
    review.set_draft(proj, rec["id"], text=rec["text"])
    wf.review_save(cfg, proj.voice)
    assert tp.load_twin_profile(proj)["signature"] == after["signature"]  # 没重算
    # 出错不影响别的功能：只记一条中文提醒
    warned = []
    monkeypatch.setattr(wf.log, "warning", lambda msg, *a, **k: warned.append(msg))

    def boom(*a, **k):
        raise ValueError("测试用的错误")

    monkeypatch.setattr(tp, "build_twin_profile", boom)
    assert wf.run_analyze(cfg, proj.voice)["clips"] > 0
    assert any("说话习惯" in m for m in warned)


def test_stop_button_still_stops(voice, monkeypatch):
    from voicetwin.utils.progress import TaskCancelled

    cfg, proj = voice

    def stop(*a, **k):
        raise TaskCancelled("已按你的要求停止")

    monkeypatch.setattr(tp, "build_twin_profile", stop)
    with pytest.raises(TaskCancelled):
        wf.run_analyze(cfg, proj.voice)


# ---------------------------------------------------------------------------- 参考录音库
class FakeJudge:
    """假的声纹打分：每条录音的声纹由长度决定（同一条每次一样）。"""
    available = True
    models = ["m1", "m2"]

    def __init__(self):
        self.calls = 0

    def signature(self):
        return "fake-sig"

    def embed_with_seconds(self, wav, sr):
        self.calls += 1
        rng = np.random.default_rng(len(wav))
        return {m: (rng.normal(size=16) + 4).astype(np.float32) for m in self.models}, len(wav) / sr * 0.9

    def judge_embeddings(self, embs, seconds=None):
        return {"pct_raw": 96.5 if seconds else None}


def test_reference_bank_lazy_wavs_and_references_untouched(voice):
    _, proj = voice
    refs_before = proj.references_path.read_bytes()
    mtime = proj.references_path.stat().st_mtime_ns
    tp.build_twin_profile(proj)
    recs = proj.load_manifest()
    bank = R.build_reference_bank(proj, recs)
    assert len(bank) >= 5
    data = R.load_reference_bank(proj)
    assert data["n"] == len(bank) and data["bank_sig"] == R.bank_signature(bank)
    eligible = {r["id"] for r in recs if R.bank_eligible(r)}
    for e in bank:
        assert e["id"] in eligible and 3.2 <= e["dur"] <= 9.8 and e["self_pct"] is None
        assert e["kind"] in ("statement", "question", "exclaim") and 0.0 <= e["en_ratio"] <= 1.0
        assert e["syllables"] > 0 and e["base"] is not None and e["f0_med"] is not None
        assert isinstance(e["para_initial"], bool) and e["max_pause"] >= 0.0
    assert not R.bank_dir(proj).exists()  # 音频要用时才写
    first = R.bank_wav(proj, bank[0])
    assert sorted(p.name for p in R.bank_dir(proj).glob("*")) == [first.name]  # 只写了这一条，没有临时文件留下
    for e in bank:
        info = sf.info(str(R.bank_wav(proj, e)))
        assert 3.2 <= info.frames / info.samplerate <= 9.8
        assert abs(info.frames / info.samplerate - e["dur"]) < 0.002
    assert proj.references_path.read_bytes() == refs_before
    assert proj.references_path.stat().st_mtime_ns == mtime
    # 素材准备时清理：已经不能用的片段，库里的音频删掉
    recs[[r["id"] for r in recs].index(bank[0]["id"])]["deleted"] = True
    assert R.prune_bank_files(proj, recs) == 1 and not first.exists()


def test_bank_sig_changes_after_saved_text_edit(voice):
    from voicetwin.data import review

    cfg, proj = voice
    bank = R.build_reference_bank(proj, proj.load_manifest())
    sig = R.load_reference_bank(proj)["bank_sig"]
    e = bank[0]
    review.set_draft(proj, e["id"], text=e["text"][:-1] + "呀。")
    assert R.build_reference_bank(proj, proj.load_manifest()) and R.load_reference_bank(proj)["bank_sig"] == sig
    wf.review_save(cfg, proj.voice)  # 保存了才算
    R.build_reference_bank(proj, proj.load_manifest())
    assert R.load_reference_bank(proj)["bank_sig"] != sig


def test_bank_embeddings_are_cached_and_fill_timbre_deltas(voice):
    _, proj = voice
    tp.build_twin_profile(proj)
    recs = proj.load_manifest()
    j = FakeJudge()
    bank = R.build_reference_bank(proj, recs, judge=j)
    assert j.calls == len(bank) and all(e["self_pct"] == 96.5 for e in bank)
    data = R.load_reference_bank(proj)
    assert data["judge_sig"] == "fake-sig" and data["judge_models"] == ["m1", "m2"]
    j2 = FakeJudge()
    again = R.build_reference_bank(proj, recs, judge=j2)
    assert j2.calls == 0 and again == bank  # 声纹按 id + 文件大小 + 修改时间缓存
    timbre = tp.load_twin_profile(proj)["deltas"]["timbre"]
    assert timbre["judge_sig"] == "fake-sig" and timbre["sentence"]["n"] >= 8
    assert 0.0 <= timbre["sentence"]["mean"] <= 2.0 and timbre["clause"]["mean"] is None
    # 片段文件变了（大小 / 修改时间）：这一条重新算
    clip = proj.abspath(bank[0]["path"])
    w, sr = sf.read(str(clip), dtype="float32")
    sf.write(str(clip), w, sr)
    import os

    os.utime(clip, ns=(clip.stat().st_atime_ns, clip.stat().st_mtime_ns + 10_000_000))
    j3 = FakeJudge()
    R.build_reference_bank(proj, recs, judge=j3)
    assert j3.calls == 1


def test_timbre_deltas_survive_rebuilds(voice):
    """建了带声纹的参考录音库以后，说话习惯重算（改一句文字并保存、twin_profile.json 删了）时前后两句的音色变化不能丢：
    库没变就沿用；库里前后两段的关系变了就用缓存的声纹重新算（不用打分模型）；没有库时是 null。"""
    from voicetwin.data import review

    cfg, proj = voice
    tp.build_twin_profile(proj)
    bank = R.build_reference_bank(proj, proj.load_manifest(), judge=FakeJudge())
    first = tp.load_twin_profile(proj)
    timbre = first["deltas"]["timbre"]
    assert timbre["judge_sig"] == "fake-sig" and timbre["sentence"]["n"] >= 8
    ids = {e["id"] for e in bank}
    recs = proj.load_manifest()
    # 改一句不在库里的话（验证集的）并保存：说话习惯重算了，音色变化照样在、一点没变
    other = next(r for r in recs if r["id"] not in ids and r.get("split") == "val" and r.get("text"))
    review.set_draft(proj, other["id"], text=other["text"].rstrip("。") + "啊。")
    wf.review_save(cfg, proj.voice)
    after = tp.load_twin_profile(proj)
    assert after["signature"] != first["signature"] and after["deltas"]["timbre"] == timbre
    # twin_profile.json 被删了：重算时用缓存的声纹算回来，和建库时算的一模一样
    tp.twin_profile_path(proj).unlink()
    assert tp.build_twin_profile(proj)["deltas"]["timbre"] == timbre
    # 库里一段的句末标点改了（这一对从「句子之间」变成「句子里面」）：按现在的文字重新算
    a, b, typ = tp.consecutive_pairs(recs, ids)[0]
    assert typ == "sentence"
    text_a = next(r["text"] for r in recs if r["id"] == a)
    review.set_draft(proj, a, text=text_a[:-1] + "，")
    wf.review_save(cfg, proj.voice)
    t2 = tp.load_twin_profile(proj)["deltas"]["timbre"]
    assert t2["clause"]["n"] == 1 and t2["sentence"]["n"] == timbre["sentence"]["n"] - 1
    assert t2["judge_sig"] == "fake-sig"
    # 没有参考录音库：没有就是没有
    R.bank_path(proj).unlink()
    assert tp.build_twin_profile(proj, force=True)["deltas"]["timbre"] is None


def _copy_voice(prepared, dst):
    from conftest import make_cfg

    cfg, project, _ = prepared
    shutil.copytree(project.root, dst / project.voice)
    _no_bank(dst / project.voice)
    cfg2 = make_cfg(dst)
    return cfg2, wf.Project(cfg2, project.voice)


def _hold_cold_build(proj, monkeypatch):
    """在另一个线程里第一次量 proj（缓存删掉），量第一段时停住，直到 release.set()。返回 (线程, release)。"""
    import threading

    (proj.cache_dir / tp.CLIP_CACHE_FILE).unlink()
    started, release = threading.Event(), threading.Event()
    real = tp.acoustic_features

    def slow(wav, sr):
        if threading.current_thread().name == "twin-cold":
            started.set()
            release.wait(60)
        return real(wav, sr)

    monkeypatch.setattr(tp, "acoustic_features", slow)
    th = threading.Thread(target=tp.build_twin_profile, args=(proj,), kwargs={"force": True}, name="twin-cold")
    th.start()
    assert started.wait(30)
    return th, release


def _run_with_timeout(fn, seconds):
    import threading

    box = {}
    th = threading.Thread(target=lambda: box.setdefault("res", fn()), name="save")
    th.start()
    th.join(seconds)
    return th, box


def test_other_voice_save_does_not_wait_for_a_long_build(prepared, tmp_path, monkeypatch):
    """一个声音第一次量说话习惯（老师 1004 段估计要一分钟左右）的时候，另一个声音的「保存修改」不用等它。"""
    from voicetwin.data import review

    _, proj_a = _copy_voice(prepared, tmp_path / "wsA")
    cfg_b, proj_b = _copy_voice(prepared, tmp_path / "wsB")
    before = tp.build_twin_profile(proj_b)
    rec = next(r for r in proj_b.load_manifest() if "，" in r["text"])
    review.set_draft(proj_b, rec["id"], text=rec["text"].replace("，", "、", 1))
    th_a, release = _hold_cold_build(proj_a, monkeypatch)
    try:
        th_b, box = _run_with_timeout(lambda: wf.review_save(cfg_b, proj_b.voice), 20)
        assert not th_b.is_alive(), "另一个声音在量说话习惯，这个声音的保存不该等它"
        assert box["res"]["saved"] == [rec["id"]]
        assert tp.load_twin_profile(proj_b)["signature"] != before["signature"]  # 这个声音照样更新了
    finally:
        release.set()
        th_a.join(60)
        if "th_b" in locals():
            th_b.join(60)


def test_same_voice_save_skips_update_while_a_long_build_runs(voice, monkeypatch):
    """同一个声音正在第一次量（比如「重新分析说话风格」）的时候点「保存修改」：保存照样马上完成，
    说话习惯这次先不更新（量完以后下一次更新时会按新文字重算）。"""
    from voicetwin.data import review

    cfg, proj = voice
    tp.build_twin_profile(proj)
    monkeypatch.setattr(wf, "TWIN_REVIEW_LOCK_WAIT", 0.2)
    rec = next(r for r in proj.load_manifest() if "，" in r["text"])
    review.set_draft(proj, rec["id"], text=rec["text"].replace("，", "、", 1))
    th_a, release = _hold_cold_build(proj, monkeypatch)
    try:
        th_b, box = _run_with_timeout(lambda: wf.review_save(cfg, proj.voice), 20)
        assert not th_b.is_alive(), "同一个声音在量说话习惯，保存最多等一小会儿，不该一直等"
        assert box["res"]["saved"] == [rec["id"]]
    finally:
        release.set()
        th_a.join(60)
        if "th_b" in locals():
            th_b.join(60)
    stale = tp.load_twin_profile(proj)  # 量的是保存以前的文字
    prof = tp.build_twin_profile(proj)
    assert prof["signature"] != stale["signature"] and prof["pauses"]["enum"]["n_marks"] == 1


# ---------------------------------------------------------------------------- 共用的小工具
def test_silent_and_speech_runs():
    x = np.zeros(SR * 2, np.float32)
    x[int(0.3 * SR):int(0.8 * SR)] = 0.3 * np.sin(np.arange(int(0.5 * SR)) * 0.3)
    x[int(0.9 * SR):int(1.5 * SR)] = 0.3 * np.sin(np.arange(int(0.6 * SR)) * 0.3)  # 中间 0.1 秒的停顿不到 120 ms
    runs = silent_runs(x, SR)
    assert runs[0][0] == 0.0 and runs[-1][1] == 2.0 and len(runs) == 2
    sp = speech_runs(x, SR)
    assert len(sp) == 1 and abs(sp[0][0] - 0.3) < 0.03 and abs(sp[0][1] - 1.5) < 0.03
    assert len(speech_runs(x, SR, min_gap_ms=50)) == 2
    assert speech_runs(np.zeros(SR, np.float32), SR) == [] and mask_runs(np.array([], bool)) == []
    assert mask_runs(np.array([1, 1, 0, 1, 0, 0, 1, 1, 1], bool), 2) == [(0, 2), (6, 9)]
    assert tp.source_gaps(x, SR) == []  # 开头和结尾的静音不算停顿
