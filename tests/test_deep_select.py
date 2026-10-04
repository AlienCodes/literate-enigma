"""「一模一样」P8：深度挑选、排序权重校准、试听参考录音、生成前的准备，以及老师要的四项评分
（research/一模一样/设计方案原文.md §1.3、§1.4、§2 P8，测试清单 §5.1；四项评分见 research/一模一样/记录.md）。

测的东西：
- 假的引擎：声音的「像不像」按（音色模型轮数, 语气模型轮数）定好（离设计好的最佳越远，音高越偏）；假的声纹模型按音高打分。
  三步挑出来的正好是设计好的最佳；第一步只换语气模型、第二步只换音色模型、第三步按音色模型排在一起；
- 有几句没能生成的模型输掉；再挑一次时一个请求都不发（接着用存下的结果）；生成线程开着时结果一样；
- 分不出来时两个都留着；没参加训练的录音不到 8 句时语速不调；你原来的模型排第一时继续用它；
- 排序权重的校准：能找回埋进去的权重，纯随机时照旧用默认的；
- 试听参考录音：请求数 = 参考录音条数 × 句数，不到 6 句时不做；
- 「一模一样」的挑选出错时自动改用标准的挑法，记下 selection_error；停止按钮不算出错；
- 以前的版本练的模型（models.json 里没有 identical）：准备时做一次小校准，只做一次；生成前会先准备；
- 真实 api_v2：第三步的请求带辅助参考、种子各不一样、参考录音是给这句挑的那两条；
- 四项评分：分组、每组单独校准（不到 8 句用总体标准并说明）、按人声时长加权、2000 次重新抽样的误差范围、
  综合总评分按你素材里的时间比例（没有的组不算）、某一组明显差不能当第一、差别在误差范围内说「分不出来」、
  显示的格式、量不出来不写数。
"""

import dataclasses
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from conftest import make_cfg
from voicetwin.eval import lang_groups as LG
from voicetwin.eval.speaker import JudgeMember, SimilarityJudge
from voicetwin.project import Project
from voicetwin.synth import calibrate_rank as CR
from voicetwin.synth import select as sel
from voicetwin.synth.probe_texts import LONG_MIN_SYLLABLES, TEST_TEXTS, probe_items
from voicetwin.utils.textutil import syllable_count

SR = 16000
BASE_F = 200.0

ZH_TEXTS = ["我们先来复习一下上节课讲过的内容。", "今天的作业大家一定要按时完成。", "这个句子的结构其实并不复杂。",
            "请大家把书翻到第一页看一看。", "下面我们来做几道简单的练习。", "这一部分是考试经常会考的地方。",
            "注意这里的时态要和前面保持一致。", "我们把这个句子再读一遍好不好。", "大家先自己想一想再看答案。",
            "这个规则只要多练几次就能记住。", "我们来看一下课本上的例子。", "今天就先讲到这里吧。"]
MIXED_TEXTS = ["这里的 which 指的是前面整个句子。", "注意 as 引导的从句可以放在句首。", "这个单词 because 后面要接句子。",
               "我们说 I think so 的时候语气要轻。", "比如 This is my book 就是一个简单句。", "这里要用 have done 的形式。",
               "大家记住 look forward to 这个搭配。", "如果是 everyone 后面就用单数。", "这里的 that 可以省略掉。",
               "我们再看一个 if 引导的条件句。", "这个 phrase 的意思是期待。", "注意 the 在元音前面要读重一点。"]


def _dur(text: str) -> float:
    return 0.6 + 0.07 * syllable_count(text)


def _tone(freq: float, dur: float, sr: int = SR) -> np.ndarray:
    t = np.arange(int(dur * sr)) / sr
    x = 0.3 * np.sin(2 * np.pi * freq * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    return np.concatenate([np.zeros(int(0.1 * sr)), x, np.zeros(int(0.25 * sr))]).astype(np.float32)


def _dominant(wav: np.ndarray, sr: int) -> float:
    x = np.asarray(wav, dtype=np.float64)
    x = x - x.mean()
    n = 1 << 16
    spec = np.abs(np.fft.rfft(x, n))
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    spec[freqs < 60] = 0
    return float(freqs[int(np.argmax(spec))])


class FreqEncoder:
    """假的声纹模型：声纹 = 音高离 200 Hz 多远（转成角度），所以 200 Hz 的声音和「你」一模一样，越偏越不像。"""
    name = "freq"
    reliable = True

    def embed(self, wav, sr):
        th = (_dominant(wav, sr) - BASE_F) / 40.0
        return np.array([np.cos(th), np.sin(th)], dtype=np.float32)

    def embed_file(self, path):
        import soundfile as _sf

        wav, sr = _sf.read(str(path), dtype="float32")
        return self.embed(wav, sr)


def _judge():
    return SimilarityJudge([JudgeMember(FreqEncoder(), np.array([1.0, 0.0]), {"p50": 1.0, "sig": "freq-test"})])


def _project(tmp_path, n_val=8, name="深度挑选", mixed_freq=BASE_F, n_train=16, sources=4, en_val=0):
    """合成的声音素材：训练集一半纯中文一半中英夹在一起（4.5 秒，参考录音库能用），验证集 n_val 句（一半一半）。"""
    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, name)
    project.root.mkdir(parents=True, exist_ok=True)
    project.clips_dir.mkdir(parents=True, exist_ok=True)
    recs = []

    def add(cid, text, split, dur, freq, src):
        from voicetwin.utils.audio import speech_activity

        path = project.clips_dir / f"{cid}.wav"
        wav = _tone(freq, dur)
        sf.write(str(path), wav, SR, subtype="PCM_16")
        voiced = speech_activity(wav, SR)[0]  # 和素材准备时一样量人声时长
        recs.append({"id": cid, "path": project.relpath(path), "text": text, "lang": "zh", "split": split, "keep": True,
                     "duration": round(len(wav) / SR, 3), "voiced": round(voiced, 3), "source": f"v{src}", "start": 0.0,
                     "end": dur, "forced_cuts": 0})

    for k in range(n_train):
        text = (MIXED_TEXTS if k % 2 else ZH_TEXTS)[k // 2 % 12]
        add(f"t{k:02d}", text, "train", 4.5, mixed_freq if k % 2 else BASE_F, k % sources)
    for k in range(n_val):
        text = (MIXED_TEXTS if k % 2 else ZH_TEXTS)[(k // 2 + 6) % 12]
        add(f"v{k:02d}", text, "val", _dur(text), mixed_freq if k % 2 else BASE_F, k % sources)
    for k in range(en_val):
        text = ["This is the first English sentence.", "We will read it again tomorrow."][k % 2]
        add(f"e{k:02d}", text, "val", _dur(text), BASE_F, 0)
    project.save_manifest(recs)
    return cfg, project


class FakeQualityBackend:
    """假的 GPT-SoVITS：声音的音高 = 200 Hz + 偏差，偏差按（音色模型轮数, 语气模型轮数）定（默认最佳是 s8-g6）；
    长短 = ratio × 按字数算的长度。记下每次请求、每次换模型、在哪个线程里生成。"""

    name = "gptsovits"
    display_name = "测试"
    supports_training = True
    supports_aux_refs = True
    supports_batch = False
    release_gpu_callback = None

    def __init__(self, project, sovits=(4, 6, 8, 10), gpt=(4, 5, 6, 7), quality=None, ratio=1.0, fail=(),
                 prev=None, n_test=2, final=4):
        self.project = project
        self.bcfg = {"train": {"select_test_texts": n_test, "select_screen_seeds": 2, "select_final_candidates": final}}
        wdir = project.root / "fakeweights"
        wdir.mkdir(parents=True, exist_ok=True)
        self.sov = {e: str(wdir / f"s_e{e}.pth") for e in sovits}
        self.gpt = {e: str(wdir / f"g_e{e}.ckpt") for e in gpt}
        for p in list(self.sov.values()) + list(self.gpt.values()):
            if not Path(p).exists():  # 模型文件没变（再挑一次时文件的大小、修改时间都一样）
                Path(p).write_bytes(b"x" * 64)
        self.quality = quality or (lambda s, g: 2.0 * abs(s - 8) + 3.0 * abs(g - 6))
        self.ratio = ratio
        self.fail = set(fail)
        self.prev = None
        if prev is not None:
            ps, pg = str(wdir / "old_s_e24.pth"), str(wdir / "old_g_e20.ckpt")
            for q in (ps, pg):
                if not Path(q).exists():
                    Path(q).write_bytes(b"y" * 64)
            self.prev = {"id": "prev-s24-g20", "sovits": ps, "gpt": pg, "sovits_epoch": 24, "gpt_epoch": 20,
                         "previous": True, "_offset": float(prev)}
        self.cur = None
        self.calls = []
        self.loads = []
        self.threads = set()
        self.started = 0

    def checkpoints(self, all=False):  # noqa: A002
        out = [{"id": f"s{s}-g{g}", "sovits": sp, "gpt": gp, "sovits_epoch": s, "gpt_epoch": g}
               for s, sp in sorted(self.sov.items()) for g, gp in sorted(self.gpt.items())]
        if self.prev is not None:
            out.append({k: v for k, v in self.prev.items() if not k.startswith("_")})
        return out

    def use_checkpoint(self, ck):
        self.cur = ck
        self.loads.append((ck["sovits"], ck["gpt"]))

    def selected_checkpoint(self):
        return (self.project.load_models().get(self.name) or {}).get("selected")

    def speed_calibration(self):
        return {}

    def model_id(self):
        return f"fake-{(self.cur or {}).get('id', 'current')}"

    def start(self):
        self.started += 1

    def stop(self):
        pass

    def start_hint(self):
        return ""

    def _offset(self):
        ck = self.cur or self.selected_checkpoint() or {}
        if ck.get("previous"):
            return float(self.prev["_offset"])
        return float(self.quality(int(ck.get("sovits_epoch", 8)), int(ck.get("gpt_epoch", 6))))

    def synthesize_many(self, req, n, out_dir):
        import threading

        self.threads.add(threading.current_thread().name)
        cid = (self.cur or {}).get("id", "current")
        self.calls.append((dataclasses.replace(req), int(n), cid))
        if (cid, req.text) in self.fail:
            raise RuntimeError("模拟：这一句生成失败")
        freq = BASE_F + self._offset()
        out = []
        for k in range(int(n)):
            path = Path(out_dir) / f"f{len(self.calls)}_{k}.wav"
            sf.write(str(path), _tone(freq, self.ratio * _dur(req.text)), SR, subtype="PCM_16")
            out.append((path, k))
        return out


@pytest.fixture
def fast(monkeypatch):
    """测试里不算音调走向（DTW）和音调起伏 / 频谱（真的算法另有测试），没有 N 卡（不开生成线程），试听每次同时生成 2 个。"""
    from voicetwin.eval.identical_judge import IdenticalScorer

    monkeypatch.setattr(sel, "_mfcc_f0", lambda wav, sr: {"mfcc": np.zeros((20, 1)), "st": np.zeros(1)})
    monkeypatch.setattr(IdenticalScorer, "_shape", lambda self, wav, sr, text: (None, None))
    monkeypatch.setattr(sel, "_vram_tier", lambda: "none")
    monkeypatch.setattr(sel, "AUDITION_B", 2)


def _run(cfg, project, backend, **kw):
    return sel.select_deep(cfg, project, backend, use_asr=False, judge=_judge(), **kw)


# ============================================================================ 检查用的句子
def test_probe_texts_are_generic_and_cover_three_kinds():
    assert len(TEST_TEXTS) == 24 and len({t["id"] for t in TEST_TEXTS}) == 24
    kinds = [t["kind"] for t in TEST_TEXTS]
    assert kinds.count("question") == kinds.count("mixed") == kinds.count("long") == 8
    for t in TEST_TEXTS:
        if t["kind"] == "question":
            assert t["text"].endswith("？") and LG.text_group(t["text"]) == "zh"
        if t["kind"] == "mixed":
            assert LG.text_group(t["text"]) == "mixed"
        if t["kind"] == "long":
            assert syllable_count(t["text"]) >= LONG_MIN_SYLLABLES and LG.text_group(t["text"]) == "zh"
        assert "@" not in t["text"] and not any(ch.isdigit() for ch in t["text"])
    assert [t["kind"] for t in probe_items(5)] == ["question", "mixed", "long", "question", "mixed"]
    assert len(probe_items(99)) == 24


# ============================================================================ 三步挑选
@pytest.fixture
def deep_run(tmp_path, fast, monkeypatch):
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project)
    b.marks = {}
    orig = sel._DeepSelect.final

    def final(self, combos, lo, hi, label):  # 记下第三步从第几次换模型开始、到第几次结束
        b.marks["c0"] = len(b.loads)
        out = orig(self, combos, lo, hi, label)
        b.marks["c1"] = len(b.loads)
        return out

    monkeypatch.setattr(sel._DeepSelect, "final", final)
    info = _run(cfg, project, b)
    return cfg, project, b, info


def test_stages_pick_the_designed_best(deep_run):
    cfg, project, b, info = deep_run
    s = info["selection"]
    assert s["method"] == "deep" and s["best"] == "s8-g6" and info["selected"]["id"] == "s8-g6"
    # 第一步：音色模型固定在训练一半（最大 10 轮 → 6 轮），语气模型 g6 最好
    assert [r["id"] for r in s["stages"]["A"]][0] == "s6-g6"
    assert {r["id"] for r in s["stages"]["A"]} == {"s6-g4", "s6-g5", "s6-g6", "s6-g7"}
    # 第二步：第一步最好的语气模型 × 每个音色模型，s8 最好
    assert [r["id"] for r in s["stages"]["B"]][0] == "s8-g6"
    # 第三步：3 × 3 组
    assert len(s["results"]) == 9 and s["ranking"][0] == "s8-g6"
    top = s["results"][0]
    for key in ("pct", "four", "total", "se", "n_items", "n_seeds", "val_mean", "test_mean"):
        assert key in top
    assert top["n_items"] == 10 and top["n_seeds"] == 2 and top["four"]["composite"]["status"] == "ok"
    assert top["pct"] == pytest.approx(100.0, abs=0.01)
    # 存进 models.json
    entry = project.load_models()["gptsovits"]
    block = entry["identical"]
    for key in ("version", "run_stamp", "ckpts", "ranking", "ci_p", "speed", "weights", "weights_version", "ref_prior",
                "ref_prior_version", "bank_sig", "model_ids", "items", "seeds", "evaluated_at", "note_bias"):
        assert key in block, key
    assert block["ckpts"][0]["id"] == "s8-g6" and block["items"] == {"val": 8, "test": 2}
    assert block["note_bias"] == sel.NOTE_BIAS and entry["selected"]["id"] == "s8-g6"
    assert b.loads[-1] == (b.sov[8], b.gpt[6])  # 最后换成挑出来的那个
    lines = s["lines"]
    assert lines[0] == "挑选结果（实测，10 句：没参加训练的录音 8 句、检查用的句子 2 句）："
    # 每类只有 5 句（8 句录音 + 2 句检查用的句子）：只写平均、不写误差范围
    assert lines[1].startswith("第 1 名 s8-g6：中英夹在一起 100.0%（只有 5 句，太少，量不出误差范围）｜纯中文 100.0%（只有 5 句")
    assert "错字率（没测出来）" in lines[1]
    assert sel.BIAS_LINE in lines and LG.EN_NOTE + "。" in lines


def test_weight_switches_are_minimised(deep_run):
    _, _, b, info = deep_run
    loads = b.loads[:-1]
    # 第一步：只换语气模型（音色模型一直是 s6），每个语气模型只加载一次
    a = loads[:4]
    assert {s for s, _ in a} == {b.sov[6]} and len({g for _, g in a}) == 4
    # 第三步：9 组，按音色模型排在一起（3 个音色模型，每个只出现一段）
    c = [s for s, _ in b.loads[b.marks["c0"]:b.marks["c1"]]]
    changes = sum(1 for i in range(1, len(c)) if c[i] != c[i - 1])
    assert len(c) == 9 and len(set(c)) == 3 and changes == 2


def test_second_run_resumes_with_zero_synth_calls(deep_run):
    cfg, project, b, info = deep_run
    assert b.calls
    b2 = FakeQualityBackend(project)
    info2 = _run(cfg, project, b2)
    assert b2.calls == [] and info2["selection"]["best"] == "s8-g6"
    assert info2["selection"]["requests"]["requests"] == 0 and info2["selection"]["requests"]["cached"] > 0
    assert info2["selection"]["ranking"] == info["selection"]["ranking"]


def test_pipeline_gives_the_same_result_in_a_producer_thread(tmp_path, fast, monkeypatch):
    cfg, project = _project(tmp_path)
    monkeypatch.setattr(sel, "_vram_tier", lambda: "mid")
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6, 7))
    info = _run(cfg, project, b)
    assert b.threads == {"vt-identical-gen"}  # 只有生成线程跟引擎说话，主线程同时打分
    cfg2, project2 = _project(tmp_path / "b")
    monkeypatch.setattr(sel, "_vram_tier", lambda: "none")
    b2 = FakeQualityBackend(project2, sovits=(8, 10), gpt=(6, 7))
    info2 = _run(cfg2, project2, b2)
    assert "vt-identical-gen" not in b2.threads
    assert info["selection"]["ranking"] == info2["selection"]["ranking"]
    assert [r["total"] for r in info["selection"]["results"]] == [r["total"] for r in info2["selection"]["results"]]


def test_a_checkpoint_that_fails_some_items_loses(tmp_path, fast):
    cfg, project = _project(tmp_path)
    val = [r["text"] for r in project.load_manifest() if r["split"] == "val"]
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6, 7), fail={("s8-g6", t) for t in val[:2]})
    info = _run(cfg, project, b)
    s = info["selection"]
    assert s["best"] != "s8-g6" and s["best"] == "s8-g7"   # 没失败的里面最好的（偏差 3 Hz；s10-g6 是 4 Hz）
    bad = next(r for r in s["results"] if r["id"] == "s8-g6")
    assert bad["failed"] == 2 and "有 2 句没能生成（按最差算）" in " ".join(s["lines"])


def test_bootstrap_tie_keeps_two_checkpoints(tmp_path, fast):
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6,), quality=lambda s, g: 0.0)
    info = _run(cfg, project, b)
    block = info["identical"]
    assert block["tie"] is True and len(block["ckpts"]) == 2
    assert {c["id"] for c in block["ckpts"]} == {"s8-g6", "s10-g6"}
    assert info["selection"]["two"] and any("分不出来" in x for x in info["selection"]["lines"])
    # 用第 2 名生成的那一步还没做：照实说，不叫老师去比两个模型（她没法用第 2 名生成）
    line = next(x for x in info["selection"]["lines"] if "分不出来" in x)
    assert "现在生成只用第 1 名（用第 2 名生成的功能还没做好）" in line and "两个的差别" not in line


def test_speed_needs_eight_val_items(tmp_path, fast):
    cfg, project = _project(tmp_path, n_val=8)
    b = FakeQualityBackend(project, sovits=(8,), gpt=(6,), ratio=1.2)
    info = _run(cfg, project, b)
    assert info["speed"]["zh"] == pytest.approx(1.2, abs=0.02) and info["identical"]["speed"] == info["speed"]
    assert f"语速（实测，中文 8 句）：模型读得比你本人慢 20%，生成时按 {info['speed']['zh']:g} 倍速读，和你本人一样快。" \
        in info["selection"]["lines"]
    cfg2, project2 = _project(tmp_path / "few", n_val=5)
    b2 = FakeQualityBackend(project2, sovits=(8,), gpt=(6,), ratio=1.2)
    info2 = _run(cfg2, project2, b2)
    assert info2["speed"] == {"zh": 1.0} and info2["identical"]["speed"] == {"zh": 1.0}
    assert "语速（中文）：没参加训练的录音只有 5 句能比（不到 8 句，量不准），这次没测，语速先不调。" in info2["selection"]["lines"]


def test_previous_selected_stays_selected_when_it_ranks_first(tmp_path, fast):
    from voicetwin import workflows as wf

    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6, 7), quality=lambda s, g: 6.0 + abs(s - 8) + abs(g - 6),
                           prev=0.0)
    project.update_models("gptsovits", {"previous_selected": {"id": "s24-g20", "pending": True}})
    info = _run(cfg, project, b)
    assert info["selection"]["ranking"][0] == "prev-s24-g20" and info["selected"]["previous"] is True
    assert project.load_models()["gptsovits"]["selected"]["id"] == "prev-s24-g20"
    assert "第 1 名 prev-s24-g20（你原来的模型）" in info["selection"]["lines"][1]
    wf._previous_model_result(project, "gptsovits", info)
    assert info["previous_note"] == "新模型实测没有比原来的好，继续用原来的模型。"


# ============================================================================ 排序权重的校准
def _cands(rng, n_groups, w_true, cap=110.0, noise=False):
    groups = {}
    for gi in range(n_groups):
        cands = []
        for _ in range(8):
            c = {"pct_raw": float(rng.uniform(80, 130)), "spread": float(rng.uniform(0, 10)), "cer": 0.0,
                 "dur_dev": float(rng.uniform(0, 0.3)), "prosody_z": float(rng.uniform(0, 2)),
                 "ltas_d": float(rng.uniform(0, 3)), "f0_rmse": 1.0, "dur_ratio": 1.0, "item": f"i{gi}"}
            c["to_real"] = float(rng.normal()) if noise else CR.production_score(c, w_true, cap)
            cands.append(c)
        groups[f"m|i{gi}"] = cands
    return groups


def test_calibrate_rank_recovers_planted_weights():
    planted = {"rate": 0.8, "pros": 0.3, "ltas": 0.04, "cap": "none"}
    res = CR.calibrate(_cands(np.random.default_rng(7), 30, planted), cap_value=110.0)
    assert res["adopted"] is True and res["weights"] == planted and res["gain"] >= CR.MIN_GAIN
    assert res["version"].startswith("cal-") and res["n_items"] == 30


def test_calibrate_rank_keeps_defaults_on_noise():
    for seed in (1, 2, 3):
        res = CR.calibrate(_cands(np.random.default_rng(seed), 60, CR.DEFAULTS, noise=True), cap_value=110.0)
        assert res["adopted"] is False and res["weights"] == {} and res["version"] == "default"
        # 纯随机时平均也可能碰巧好 0.05 以上（seed 3 就是）：误差范围的下限不比默认的好，照样不换
        assert res["gain"] is not None and (res["gain"] < CR.MIN_GAIN or res["gain_lo"] <= 0)
        assert "照旧用默认的" in CR.describe(res)
    assert CR.calibrate({}, cap_value=None)["adopted"] is False
    assert "照旧用默认的" in CR.describe(CR.calibrate({}, cap_value=None))


def test_identical_scorer_uses_calibrated_rate_and_cap():
    from voicetwin.eval.identical_judge import IdenticalScorer

    sc = IdenticalScorer({}, None, None, {"rate": 0.4}, None, judge=None, twin={},
                         rank_weights={"rate": 0.8, "pros": 0.3, "ltas": 0.04, "cap": "none"})
    assert sc.w["rate"] == 0.8 and sc.rank_w == {"pros": 0.3, "ltas": 0.04} and sc.cap_mode == "none"
    sc.configure(twin={}, rank_weights={})
    assert sc.w["rate"] == 0.4 and sc.rank_w == {"pros": 0.0, "ltas": 0.0} and sc.cap_mode == "p90"


# ============================================================================ 试听参考录音
def test_audition_request_count_and_skip(tmp_path, fast):
    cfg, project = _project(tmp_path, n_val=8, n_train=12, sources=3)
    b = FakeQualityBackend(project, sovits=(8,), gpt=(6,))
    project.update_models("gptsovits", {"selected": b.checkpoints()[0]})
    sim = sel._Sim(cfg, project, judge=_judge())
    res = sel.audition_references(cfg, project, b, sim=sim, use_asr=False)
    # 训练集 12 条、3 个视频，每个视频最多 3 条 → 9 条参考；× 6 句
    assert res["n_refs"] == 9 and res["n_items"] == 6 and len(b.calls) == 9 * 6 == res["requests"]
    assert all(n == sel.AUDITION_B for _, n, _ in b.calls)
    assert len(res["prior"]) == 9 and res["version"].startswith("aud-")
    # 不到 6 句：不做
    cfg2, project2 = _project(tmp_path / "few", n_val=5)
    b2 = FakeQualityBackend(project2, sovits=(8,), gpt=(6,))
    res2 = sel.audition_references(cfg2, project2, b2, sim=sel._Sim(cfg2, project2, judge=_judge()), use_asr=False)
    assert res2["prior"] is None and b2.calls == [] and "至少要 6 句" in res2["skipped"]


# ============================================================================ 出错时改用标准的挑法
@pytest.fixture
def gsv_project(prepared, tmp_path, monkeypatch):
    from voicetwin import workflows as wf
    from voicetwin.backends.gptsovits import GPTSoVITSBackend
    from fake_gptsovits import build_fake_root

    _, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    return cfg, wf.open_project(cfg, project.voice, must_exist=True)


class _Log:
    """记下 voicetwin 的日志（不用 caplog：别的测试可能把 voicetwin 的日志设成不往上传）。"""

    def __init__(self):
        import logging

        self.messages = []
        h = logging.Handler(logging.DEBUG)
        h.emit = lambda record: self.messages.append(record.getMessage())
        self.handler = h


@pytest.fixture
def vt_log():
    import logging

    rec = _Log()
    logger = logging.getLogger("voicetwin")
    old = logger.level
    logger.addHandler(rec.handler)
    logger.setLevel(logging.INFO)
    try:
        yield rec
    finally:
        logger.removeHandler(rec.handler)
        logger.setLevel(old)


def test_select_deep_error_falls_back_to_the_standard_selection(gsv_project, monkeypatch, vt_log):
    from voicetwin import workflows as wf

    cfg, project = gsv_project
    seen = []

    def boom(*a, **k):
        seen.append("deep")
        raise RuntimeError("测试：深度挑选出错了")

    def standard(cfg, project, backend, max_items=20, use_asr=None, progress=None, all_checkpoints=False):
        seen.append(("standard", all_checkpoints))
        return {"selection": {"ranking": ["s8-g15"], "best": "s8-g15"}, "speed": {"zh": 1.0}}

    monkeypatch.setattr(sel, "select_deep", boom)
    monkeypatch.setattr(sel, "select_and_calibrate", standard)
    res = wf.run_select(cfg, project.voice, "gptsovits", mode="identical")
    assert seen == ["deep", ("standard", False)]
    assert "测试：深度挑选出错了" in res["selection_error"] and res["fallback"] == "standard"
    warn = next(m for m in vt_log.messages if "「一模一样」的挑选这次没成功" in m)
    # 标准的挑法也可能出错（例如引擎起不来）：不许诺「保证一定有挑好的模型」
    assert "改用标准的挑法（从早到晚均匀挑几个版本比）再挑一次" in warn and "保证" not in warn
    assert Path(res["selection_error_report"]).exists()
    from voicetwin.webui import app as A

    md = A._select_done_md(res)
    assert "已经自动改用标准的挑法" in md and "测试：深度挑选出错了" in md
    # 停止按钮不算出错：不改用标准的挑法
    from voicetwin.utils.progress import TaskCancelled

    def cancel(*a, **k):
        raise TaskCancelled()

    seen.clear()
    monkeypatch.setattr(sel, "select_deep", cancel)
    with pytest.raises(TaskCancelled):
        wf.run_select(cfg, project.voice, "gptsovits", mode="identical")
    assert seen == []
    # 标准的挑法不经过 select_deep
    monkeypatch.setattr(sel, "select_deep", boom)
    wf.run_select(cfg, project.voice, "gptsovits", mode="standard")
    assert seen == [("standard", False)]


# ============================================================================ 生成前的准备
def _old_model(project, b):
    """以前的版本练的模型：models.json 里有训练记录和选定的模型，没有 identical。"""
    ck = next(c for c in b.checkpoints() if c["id"] == "s8-g6")
    project.update_models("gptsovits", {"trained_at": "2026-09-01 10:00", "sovits": sorted(b.sov.values()),
                                        "gpt": sorted(b.gpt.values()), "selected": ck, "speed": {"zh": 1.0}})
    return ck


def test_prepare_identical_runs_the_mini_calibration_once(tmp_path, fast):
    cfg, project = _project(tmp_path, n_val=8)
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6, 7), ratio=1.1)
    ck = _old_model(project, b)
    assert sel.identical_stale(project, b)
    rec = []
    got = sel.prepare_identical(cfg, project, b, progress=lambda f, m: rec.append((f, m)), judge=_judge(), use_asr=False)
    assert got["mini"] is True and b.calls
    block = project.load_models()["gptsovits"]["identical"]
    assert block["mini"] is True and block["ckpts"] == [ck] and block["speed"]["zh"] == pytest.approx(1.1, abs=0.02)
    assert block["items"] == {"val": 8, "test": 0}
    assert {c[2] for c in b.calls} == {"s8-g6"}  # 只试选定的模型
    assert not any(c[0].text in {t["text"] for t in TEST_TEXTS} for c in b.calls)  # 不加检查用的句子
    assert project.load_models()["gptsovits"]["speed"] == {"zh": 1.0}  # 别的档位的语速不动
    assert any("准备「一模一样」（这个模型只做一次）" in m for _, m in rec)
    assert [f for f, _ in rec] == sorted(f for f, _ in rec)
    # 再准备一次：不再做
    n = len(b.calls)
    got2 = sel.prepare_identical(cfg, project, b, judge=_judge(), use_asr=False)
    assert got2["mini"] is False and len(b.calls) == n and not sel.identical_stale(project, b)
    # 换了选定的模型（比如按标准的挑法重新挑过）→ 又过期了
    project.update_models("gptsovits", {"selected": next(c for c in b.checkpoints() if c["id"] == "s10-g7")})
    assert sel.identical_stale(project, b)


def test_prepare_skips_engines_that_cannot_train(tmp_path, fast):
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project)
    b.supports_training = False
    got = sel.prepare_identical(cfg, project, b, judge=_judge(), use_asr=False)
    assert got["mini"] is False and b.calls == [] and got["bank"] is True
    bank = json.loads((project.root / "refs_bank.json").read_text(encoding="utf-8"))
    assert bank["judge_models"] == ["freq"] and bank["eligible_sig"]


def test_narrator_prepares_before_identical_generation(prepared, tmp_path, monkeypatch):
    import uuid

    from voicetwin import workflows as wf
    from voicetwin.synth import engine as eng

    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    cfg, project, _ = prepared
    order = []
    real = sel.prepare_identical

    def spy(*a, **k):
        order.append("prepare")
        return real(*a, **k)

    monkeypatch.setattr(sel, "prepare_identical", spy)
    rec = []
    text = f"准备测试的一句话，编号{uuid.uuid4().hex[:6]}。"
    wf.run_narrate(cfg, project.voice, text, out=str(tmp_path / "p.wav"), variants=False,
                   progress=lambda f, m: rec.append(m))
    assert order == ["prepare"]
    k = next(i for i, m in enumerate(rec) if m.startswith("准备「一模一样」"))
    assert k < next(i for i, m in enumerate(rec) if m.startswith("开始生成"))
    # 测试引擎不能训练：不做小校准（models.json 里没有 identical）
    assert "identical" not in (project.load_models().get("dummy") or {})


def test_identical_generation_on_an_old_model_prepares_once(tmp_path, fast, monkeypatch):
    """以前练的模型第一次按「一模一样」生成：先做小校准（进度一直往前走、停在「启动合成引擎」之前），第二次不再做；
    小校准出来的语速用在生成上（缓存键里的语速跟着变）。"""
    from voicetwin.synth import engine as eng
    from voicetwin.synth.script import ScriptSegment

    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project, sovits=(8,), gpt=(6,), ratio=1.15)
    _old_model(project, b)
    seg = ScriptSegment(text="今天我们复习一下上节课的内容。", display="今天我们复习一下上节课的内容。", lang="zh",
                        kind="statement", index=0, pause_after="sentence")
    rec = []
    n = eng.Narrator(cfg, project, b, quality="identical", tier="none", asr_check=False,
                     progress=lambda f, m: rec.append((f, m)))
    n._gen_range = (0.08, 0.88)
    n.synthesize_all([seg])
    block = project.load_models()["gptsovits"]["identical"]
    assert block["mini"] is True and block["speed"]["zh"] == pytest.approx(1.15, abs=0.03)
    fr = [f for f, _ in rec]
    assert fr == sorted(fr)
    prep = [f for f, m in rec if "准备「一模一样」（这个模型只做一次）" in m]
    assert prep and max(prep) < 0.06 and rec[-1][0] >= 0.08
    assert n._speed_for("zh") == pytest.approx(block["speed"]["zh"])
    calls = len(b.calls)
    n2 = eng.Narrator(cfg, project, b, quality="identical", tier="none", asr_check=False)
    n2._gen_range = (0.08, 0.88)
    n2.synthesize_all([seg])
    assert not any(c[0].seed >= sel.SEED_BASE and c[1] == 2 and c[0].speed == 1.0 for c in b.calls[calls:])
    assert project.load_models()["gptsovits"]["identical"]["evaluated_at"] == block["evaluated_at"]


# ============================================================================ 真实 api_v2：第三步的请求
def test_real_api_stage_c_requests_carry_aux_seeds_and_shortlisted_refs(prepared, tmp_path, monkeypatch):
    import os
    import socket
    import sysconfig

    from fake_gptsovits import REAL_API_V2, build_fake_root
    from voicetwin import workflows as wf
    from voicetwin.backends.base import get_backend
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    monkeypatch.setattr(sel, "_vram_tier", lambda: "none")
    paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(p for p in dict.fromkeys(paths) if p))
    for k in ("FAKE_GSV_MAX_BATCH", "FAKE_GSV_SPEED_TRICK_BROKEN", "FAKE_GSV_INNER_ZERO"):
        monkeypatch.delenv(k, raising=False)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    _, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=REAL_API_V2)
    cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": port, "startup_timeout": 60,
        "train": {"select_test_texts": 2, "select_final_candidates": 4}}})
    p2 = wf.open_project(cfg, project.voice, must_exist=True)
    recs = p2.load_manifest()
    for i, r in enumerate(recs):  # 两个视频：辅助参考要来自别的视频
        r["source"] = f"第{i % 2 + 1}课"
    p2.save_manifest(recs)
    for f in ("refs_bank.json", "twin_profile.json"):
        if (p2.root / f).exists():
            (p2.root / f).unlink()
    b = get_backend("gptsovits", cfg, p2)
    try:
        info = sel.select_deep(cfg, p2, b, use_asr=False)
    finally:
        b.stop()
    calls = [json.loads(x) for x in (root / "_real_api_calls.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    # 第三步：每句 2 条参考 × 一次请求同时生成 2 个（select_final_candidates 4 = 2 × 2）；不算「语速 1.0001」自检的请求
    runs = [c["req"] for c in calls if c["kind"] == "run" and c["req"].get("batch_size") == 2 and "\n" in c["req"]["text"]]
    n_items = info["identical"]["items"]["val"] + info["identical"]["items"]["test"]
    want = {sel.SEED_BASE + i * sel.ITEM_SEED_STEP + j * sel.REF_SEED_STEP for i in range(n_items) for j in range(2)}
    assert want <= {r["seed"] for r in runs}  # 每句、每条参考的种子都不一样（1234 + 第几句 × 7919 + 第几条参考 × 104729）
    assert all(r["speed_factor"] == 1.0001 for r in runs)
    from voicetwin.synth import search as S

    data = json.loads((p2.root / "refs_bank.json").read_text(encoding="utf-8"))
    bank = {e["id"]: e for e in data["entries"]}
    pool = S.pool_from_bank(data)
    prior = S.prior_scores(pool, None)
    by_text = {}
    for r in runs:
        by_text.setdefault(r["text"], set()).add(Path(r["ref_audio_path"]).stem)
    # 每句用的是给它挑的两条不一样的参考录音（参考录音库里的）
    assert all(len(v) == 2 and v <= set(bank) for v in by_text.values()) and len(by_text) == n_items
    # 辅助参考：就是给主参考挑的那几条（同语言、陈述句、别的视频、4~9.8 秒、不是主参考本身），有的话一定带上
    with_aux = 0
    for r in runs:
        main = Path(r["ref_audio_path"]).stem
        aux = [Path(p).stem for p in r["aux_ref_audio_paths"]]
        assert aux == [e["id"] for e in S.aux_set(dict(bank[main], _bank=True), pool, prior, 3)]
        assert main not in aux and all(bank[a]["source"] != bank[main]["source"] for a in aux)
        with_aux += bool(aux)
    assert with_aux >= 2


# ============================================================================ 四项评分
def test_text_groups_ignore_punctuation_and_digits():
    assert LG.text_group("首先，as这个关系代词，它最经常出现。") == "mixed"
    assert LG.text_group("我们今天学习第 3 课，共 12 页。") == "zh"
    assert LG.text_group("This is a book, isn't it? 123") == "en"
    assert LG.text_group("123，。！") == "" and LG.text_group("") == ""
    assert LG.text_group("比如 This is a very long English example sentence used to show the rule.") == "mixed"


def test_teacher_material_layout_and_weights():
    """老师的母本：1004 句（keep）里 559 句中英夹在一起、445 句纯中文、0 句纯英文（research/文字校正/老师的母本/）。"""
    import csv

    path = Path(__file__).resolve().parents[1] / "research" / "文字校正" / "老师的母本" / "母本_修缮后.csv"
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8-sig")) if r["keep"] == "1"]
    counts = {g: sum(1 for r in rows if LG.text_group(r["text"]) == g) for g in LG.GROUP_ORDER}
    assert len(rows) == 1004 and counts == {"mixed": 559, "zh": 445, "en": 0}
    # 没有量过人声时长时按片段长度；没有纯英文的组 → 综合总评分只算两组、比例重新分配
    recs = [{"text": r["text"], "duration": 2.0, "keep": True} for r in rows]
    sh = LG.material_shares(recs)
    assert sh["n"] == counts and sh["source"] == "duration" and sh["shares"]["en"] == 0
    w, src = LG.composite_weights(sh["shares"], ["mixed", "zh"])
    assert src == "material" and w["mixed"] == pytest.approx(559 / 1004) and set(w) == {"mixed", "zh"}


def test_material_shares_use_voiced_time_and_exclude_empty_groups():
    recs = [{"text": "纯中文的句子。", "voiced": 3.0}, {"text": "夹着 English 的句子。", "voiced": 1.0},
            {"text": "删掉的句子 with words。", "voiced": 50.0, "deleted": True},
            {"text": "不用的句子。", "voiced": 50.0, "keep": False}, {"text": "没有文字也不算", "voiced": 0}]
    sh = LG.material_shares(recs)
    assert sh["seconds"] == {"mixed": 1.0, "zh": 3.0, "en": 0.0} and sh["shares"]["zh"] == pytest.approx(0.75)
    items = [{"key": "a", "group": "zh", "pct": 90.0, "w": 1.0}, {"key": "b", "group": "mixed", "pct": 70.0, "w": 1.0}]
    sc = LG.group_scores(items, sh["shares"])
    assert sc["composite"]["weights"] == {"mixed": 0.25, "zh": 0.75}
    assert sc["composite"]["mean"] == pytest.approx(0.75 * 90 + 0.25 * 70)
    assert sc["groups"]["en"]["status"] == "none"
    # 你的素材里各组都是 0（量不出来）：按这次检查的句子的时长
    sc2 = LG.group_scores(items, {})
    assert sc2["composite"]["weights_source"] == "items"


def test_group_scores_are_weighted_by_voiced_time_with_a_bootstrap_interval():
    rng = np.random.default_rng(3)
    items = [{"key": f"k{i}", "group": "mixed", "pct": float(v), "w": float(w)}
             for i, (v, w) in enumerate(zip(rng.uniform(80, 100, 30), rng.uniform(1, 6, 30)))]
    sc = LG.group_scores(items, {"mixed": 1.0})
    x = np.array([it["pct"] for it in items])
    w = np.array([it["w"] for it in items])
    g = sc["groups"]["mixed"]
    assert g["mean"] == pytest.approx(float((x * w).sum() / w.sum()), abs=0.01)
    assert g["mean"] != pytest.approx(float(x.mean()), abs=0.01)  # 真的按时长加权
    assert g["lo"] < g["mean"] < g["hi"]
    assert g["pm"] == pytest.approx(max(g["mean"] - g["lo"], g["hi"] - g["mean"]), abs=0.02)
    assert sc["n_boot"] == 2000 and sc["seed"] == 1234 and g["n"] == g["n_measured"] == 30
    assert LG.group_scores(items, {"mixed": 1.0}) == sc  # 固定的种子：每次一样
    narrow = LG.group_scores(items * 4, {"mixed": 1.0})["groups"]["mixed"]
    assert (narrow["hi"] - narrow["lo"]) < (g["hi"] - g["lo"])  # 句子越多误差范围越小
    assert sc["composite"]["mean"] == g["mean"] and sc["composite"]["lo"] == g["lo"]


def test_group_calibration_per_group_with_fallback(tmp_path):
    # 中英夹在一起的录音音高偏 10 Hz（按总体标准只有 96.9%）、只有 3 句纯英文（太少，按总体标准）
    cfg, project = _project(tmp_path, n_val=8, mixed_freq=210.0, en_val=3)
    judge = _judge()
    cal = LG.build_group_calibration(project, judge)
    mixed, zh, en = cal["groups"]["mixed"], cal["groups"]["zh"], cal["groups"]["en"]
    assert mixed["calibrated"] and mixed["n"] == 12 and mixed["median_pct"]["freq"] == pytest.approx(
        100 * np.cos(10 / 40), abs=0.3)
    assert mixed["factors"]["freq"] == pytest.approx(1 / np.cos(10 / 40), abs=0.005)
    assert zh["calibrated"] and zh["factors"]["freq"] == pytest.approx(1.0, abs=0.003)
    assert not en["calibrated"] and en["n"] == 3 and "录音太少（只有 3 句，至少要 8 句），按总体标准算" in en["note"]
    # 一句夹英文的生成：按总体标准 96.9%，和你自己同一类录音的中位数比就是 100%
    raws = {"freq": 100 * float(np.cos(10 / 40))}
    assert LG.calibrated_pct(raws, "mixed", cal) == pytest.approx(100.0, abs=0.3)
    assert LG.calibrated_pct(raws, "en", cal) == pytest.approx(raws["freq"])   # 按总体标准
    assert LG.calibrated_pct({}, "zh", cal) is None
    notes = LG.calibration_notes(cal, ["mixed", "zh", "en"])
    assert notes == [en["note"]]
    # 结果缓存：素材、打分标准没变时直接用
    assert LG.build_group_calibration(project, judge) == cal
    # 拿来算平均声纹的片段不用（自己给自己打分会偏高）
    (project.root / "speaker_centroid.freq.judge.json").write_text(json.dumps({"ids": ["t01", "t03"]}), encoding="utf-8")
    cal2 = LG.build_group_calibration(project, judge)
    assert cal2["groups"]["mixed"]["n"] == 10 and cal2["excluded_centroid"] == 2


def _res(rid, pcts, groups, cer=None, w=None, total=0.0):
    per = {f"i{k}": {"S": total, "pct": p, "cer": cer, "group": g, "w": (w or [1.0] * len(pcts))[k], "kind": "val"}
           for k, (p, g) in enumerate(zip(pcts, groups))}
    four = LG.group_scores([{"key": k, "group": v["group"], "pct": v["pct"], "w": v["w"]} for k, v in per.items()],
                           {"mixed": 0.56, "zh": 0.44})
    return {"id": rid, "ckpt": {"id": rid}, "previous": False, "four": four, "cer": cer, "total": total,
            "per_item": per, "failed": 0, "n_items": len(pcts), "pct": four["composite"]["mean"]}


def test_guard_rule_clearly_worse_group_cannot_be_first():
    groups = ["mixed"] * 12 + ["zh"] * 12
    # A：中英夹在一起很好、纯中文明显差；B：两类都不错 → A 的综合总评分更高也不能当第一
    a = _res("A", [100.0] * 12 + [88.0 + (k % 3) for k in range(12)], groups)
    b = _res("B", [95.0 + (k % 2) for k in range(12)] + [93.0 + (k % 2) for k in range(12)], groups)
    assert a["four"]["composite"]["mean"] > b["four"]["composite"]["mean"]
    # B 在中英夹在一起上明显差 → 两个各有长处（都不能被「压过」）→ 按综合总评分，A 第一，两个都留着
    rk = sel.rank_results([a, b])
    assert rk["first"]["id"] == "A" and rk["keep_two"] and rk["tradeoff"] == ["zh"]
    # C：和 A 一样好，纯中文也不差 → A 被压过（纯中文明显差、没有哪一类明显更好）→ C 第一
    c = _res("C", [100.0] * 12 + [92.0 + (k % 3) for k in range(12)], groups)
    a2 = _res("A", [100.0] * 12 + [80.0 + (k % 3) for k in range(12)], groups)
    a2["four"]["composite"]["mean"] = 120.0  # 就算综合总评分算得更高
    rk2 = sel.rank_results([a2, c])
    assert rk2["first"]["id"] == "C"
    assert any("「纯中文」明显比 C 差（超出误差范围），所以不能排第一" in n for n in rk2["notes"])


def test_within_interval_difference_is_a_tie():
    rng = np.random.default_rng(5)
    groups = ["mixed"] * 10 + ["zh"] * 10
    base = rng.uniform(85, 100, 20)
    a = _res("A", list(base + rng.normal(0.3, 3, 20)), groups)
    b = _res("B", list(base + rng.normal(0.0, 3, 20)), groups)
    rk = sel.rank_results([a, b])
    assert rk["tie"] and rk["keep_two"] and rk["ci_p"] is not None
    lines = sel.deep_summary_lines({"results": [rk["order"][0], rk["order"][1]], "val_items": 20, "test_items": 0,
                                    "two": ["A", "B"], "tie": True, "tradeoff": [], "four_ok": True,
                                    "lang_weights": rk["weights"], "lang_weights_source": "material"})
    assert any("差别在误差范围内（分不出来）：两个都记下了；现在生成只用第 1 名" in x for x in lines)
    assert any(x.startswith("综合总评分按你素材里各类句子实际说话时间的比例算：中英夹在一起 56%、纯中文 44%") for x in lines)


def test_cer_gates_the_first_place():
    groups = ["zh"] * 16
    good = _res("A", [100.0] * 16, groups, cer=0.0)
    bad = _res("B", [100.0] * 16, groups, cer=0.0)
    for k in range(16):  # B 每句都读错不少
        bad["per_item"][f"i{k}"]["cer"] = 0.2
    bad["cer"] = 0.2
    bad["four"]["composite"]["mean"] = 101.0
    rk = sel.rank_results([bad, good])
    assert rk["first"]["id"] == "A" and "B" in rk["gated"] and not rk["keep_two"]
    assert any("读错的字明显比 A 多（错字率 20.0% 对 0.0%" in n for n in rk["notes"])


def test_four_scores_display_text():
    items = ([{"key": f"m{k}", "group": "mixed", "pct": 90.0 + k % 3, "w": 2.0} for k in range(9)]
             + [{"key": f"z{k}", "group": "zh", "pct": 95.0, "w": 2.0} for k in range(8)])
    sc = LG.group_scores(items, {"mixed": 0.56, "zh": 0.44})
    text = LG.four_scores_text(sc)
    m, z = sc["groups"]["mixed"], sc["groups"]["zh"]
    assert text == (f"中英夹在一起 {m['mean']:.1f}% ± {m['pm']:.1f}（9 句）｜纯中文 95.0% ± 0.0（8 句）｜"
                    f"纯英文 —（没有这类句子）｜综合总评分 {sc['composite']['mean']:.1f}% ± {sc['composite']['pm']:.1f}")
    assert LG.has_english(sc)
    assert not LG.has_english(LG.group_scores(items[9:], {"zh": 1.0}))
    # 一类不到 8 句：只写量到的平均，不写误差范围（句子太少，重新抽样量出来的范围不可信）
    few = LG.group_scores(items + [{"key": "e0", "group": "en", "pct": 95.0, "w": 2.0}], {"mixed": 0.5, "zh": 0.4, "en": 0.1})
    assert few["groups"]["en"]["few"] is True and few["groups"]["en"]["pm"] is None and few["groups"]["en"]["lo"] is None
    assert "｜纯英文 95.0%（只有 1 句，太少，量不出误差范围）｜" in LG.four_scores_text(few)
    assert LG.few_groups(few) == ["en"] and LG.few_groups(sc) == []


def test_no_unmeasured_numbers():
    import re

    # 没有声纹打分：每句的「像你本人」量不出来（None）→ 四项都写「（没测出来）」，不写数
    items = [{"key": "a", "group": "mixed", "pct": None, "w": 1.0}, {"key": "b", "group": "zh", "pct": None, "w": 1.0}]
    sc = LG.group_scores(items, {"mixed": 0.5, "zh": 0.5})
    text = LG.four_scores_text(sc)
    assert text == "中英夹在一起（没测出来）｜纯中文（没测出来）｜纯英文 —（没有这类句子）｜综合总评分（没测出来）"
    assert not re.search(r"\d+(\.\d+)?%", text)
    assert LG.four_scores_text(None).count("（没测出来）") == 4
    res = {"id": "s8-g6", "four": sc, "cer": None, "previous": False}
    lines = sel.deep_summary_lines({"results": [res], "val_items": 1, "test_items": 1, "four_ok": False})
    assert "（没测出来）" in lines[1] and not re.search(r"\d+(\.\d+)?%", lines[1])
    assert any("四项评分这次没测出来" in x for x in lines)


def test_unmeasured_judge_selection_still_ranks_and_says_so(tmp_path, fast, monkeypatch):
    """没有可用的声纹打分（judge 是 None、只有简易声纹）：照样挑出来（按综合分），四项都写「（没测出来）」。"""
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6,))

    class _NoJudgeSim(sel._Sim):
        def __init__(self, cfg, project, judge=None):
            self.judge = None

            class Enc:
                name = "freq"
                reliable = True

                def embed(self, wav, sr):
                    return FreqEncoder().embed(wav, sr)

            self.encoder = Enc()
            self.cen = np.array([1.0, 0.0])

    monkeypatch.setattr(sel, "_Sim", _NoJudgeSim)
    info = sel.select_deep(cfg, project, b, use_asr=False)
    s = info["selection"]
    assert s["best"] == "s8-g6" and s["four_ok"] is False and s["results"][0]["pct"] is None
    assert "（没测出来）" in s["lines"][1]


# ============================================================================ 网页、命令行、阶段表
def test_web_select_result_shows_the_measured_table(deep_run):
    from voicetwin.webui import app as A

    _, _, _, info = deep_run
    md = A._select_done_md(info)
    assert "综合总评分 100.0%" in md and "挑选结果（实测，10 句" in md and "第 1 名 s8-g6：" in md
    assert "中英夹在一起" in md and sel.BIAS_LINE in md and "V4" not in md
    # 8 句录音量到了语速（和本人一样快）：实测的，才能说「一致」
    assert md.splitlines()[0].endswith("；语速：实测和你本人一致，不用调")
    # 训练完自动挑选的结果也显示
    tmd = A._train_done_md({"train_minutes": 3.0, "selection": info, "selected": info["selected"]}, show_plan=False)
    assert "第 1 名 s8-g6：" in tmd and "综合总评分 100.0%" in tmd


def test_cli_prints_selection_lines(deep_run):
    from voicetwin import cli

    _, _, _, info = deep_run
    lines = cli._selection_lines(info)
    assert lines == info["selection"]["lines"]
    assert cli._selection_lines({"selection_error": "出错了", "selection": {}})[0].startswith("⚠️ 按「一模一样」的方式挑选")


def test_select_stage_table_for_identical():
    from voicetwin import workflows as wf

    cfg = make_cfg(Path("."), backend="gptsovits")
    assert wf.task_stages("select", cfg, mode="identical") == wf.STAGES_SELECT_IDENTICAL
    assert wf.task_stages("select", cfg, mode="standard") == wf.STAGES_SELECT
    assert wf.task_stages("select", cfg) == wf.STAGES_SELECT
    names = [n for _, n in wf.STAGES_SELECT_IDENTICAL]
    assert names[1:] == ["挑选：先比语气模型", "挑选：再比音色模型", "挑选：最后几组按「一模一样」的方式比", "试听参考录音、校准打分"]


def test_progress_is_monotonic_and_has_the_stage_messages(tmp_path, fast):
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project)
    rec = []
    _run(cfg, project, b, progress=lambda f, m: rec.append((f, m)))
    fr = [f for f, _ in rec]
    assert fr == sorted(fr) and fr[-1] == 1.0
    msgs = [m for _, m in rec]
    assert any(m.startswith("挑选第一步：比较 4 个语气模型（每个读 10 句、每句 2 遍）……") for m in msgs)
    assert any(m.startswith("挑选第二步：比较 4 个音色模型……") for m in msgs)
    assert any(m.startswith("挑选第三步：最好的几组按「一模一样」的方式比……") for m in msgs)
    assert any(m.startswith("试听参考录音、校准打分") for m in msgs)


def test_f0_dtw_on_synthetic_contours():
    """音调走向：同一条音高曲线（时间拉长了）对齐以后 r_F0 接近 1；反过来的曲线 r_F0 是负的。"""
    def glide(f0a, f0b, dur):
        t = np.arange(int(dur * SR)) / SR
        f = np.linspace(f0a, f0b, t.size)
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = 0.3 * np.sin(ph) + 0.15 * np.sin(2 * ph)
        return np.concatenate([np.zeros(1600), x, np.zeros(1600)]).astype(np.float32)

    real = sel._mfcc_f0(glide(120, 220, 2.0), SR)
    same = sel._mfcc_f0(glide(120, 220, 2.4), SR)
    rev = sel._mfcc_f0(glide(220, 120, 2.0), SR)
    r1, rmse1 = sel._f0_dtw(same, real)
    r2, _ = sel._f0_dtw(rev, real)
    assert r1 is not None and r1 > 0.9 and rmse1 < 2.0
    assert r2 is not None and r2 < r1
    assert sel._f0_dtw({"mfcc": np.zeros((20, 1)), "st": np.zeros(1)}, real) == (None, None)


def test_paired_bootstrap():
    a = [1.0] * 20
    assert sel._paired_bootstrap(a, [0.0] * 20) == 1.0 and sel._paired_bootstrap([0.0] * 20, a) == 0.0
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 40)
    p = sel._paired_bootstrap(x, x + rng.normal(0, 0.01, 40))
    assert 0.0 < p < 1.0 and sel._paired_bootstrap(x, x + 0.0) == 0.0


# ============================================================================ 审查后的修改（两位审查员的意见，都先写了测试、改之前都失败）
class _AsrChecker:
    """假的识别校验：g6（音高偏 4 Hz）读错很多（错字率 0.3），别的都读对；第 fail_at 次调用时出错一次（之后照常）。"""

    def __init__(self, fail_at=None):
        self.n = 0
        self.fail_at = fail_at

    def check_mixed(self, wav, sr, text):
        self.n += 1
        if self.fail_at is not None and self.n == self.fail_at:
            raise RuntimeError("模拟：识别模型显存不够")
        cer = 0.3 if abs(_dominant(wav, sr) - BASE_F - 4.0) < 1.0 else 0.0
        return {"cer": cer, "errors": 5 if cer else 0, "engine": "paraformer", "hyp": text}

    def check(self, wav, sr, text, lang):
        return self.check_mixed(wav, sr, text)


def test_results_scored_after_the_asr_failure_are_not_reused_as_checked(tmp_path, fast):
    """识别校验中途出错以后量的版本没有错字率：不能存在「查错字」的缓存键下面；下次（识别正常）要重新量，
    名次和一开始就正常时一样（读错多的 g6 排最后）。"""
    def stage_a(info):
        return [r["id"] for r in info["selection"]["stages"]["A"]]

    cfg0, p0 = _project(tmp_path / "clean")
    clean = sel.select_deep(cfg0, p0, FakeQualityBackend(p0), use_asr=None, judge=_judge(), checker=_AsrChecker())
    assert stage_a(clean)[-1] == "s6-g6"
    cfg, project = _project(tmp_path / "poison")
    first = sel.select_deep(cfg, project, FakeQualityBackend(project), use_asr=None, judge=_judge(),
                            checker=_AsrChecker(fail_at=41))   # 第 41 次识别 = 第一步刚轮到 g6
    assert first["selection"]["asr_check"] is False
    b2 = FakeQualityBackend(project)
    second = sel.select_deep(cfg, project, b2, use_asr=None, judge=_judge(), checker=_AsrChecker())
    assert second["selection"]["asr_check"] is True
    assert stage_a(second) == stage_a(clean)
    assert {c[2] for c in b2.calls if c[2].startswith("s6-")} >= {"s6-g6"}   # 出错以后量的那些重新试了
    # 每条存下的结果都记着实际查没查错字，和里面每个版本量的一样（出错以后的请求存在「不查错字」的键下面）
    recs = [json.loads(f.read_text(encoding="utf-8")) for f in (project.cache_dir / "select_deep").glob("*/*.json")]
    assert recs and all(all(row["m"]["asr"] is r["asr"] for row in r["rows"]) for r in recs)
    assert {r["asr"] for r in recs} == {True, False}


def test_failed_requests_are_retried_on_the_next_selection(tmp_path, fast):
    """一次请求没生成出来（超时、连接断了……不算「重试也没用」的错误）不存：引擎好了再点「重新挑选」时重新试，
    不会永远按最差算。"""
    cfg, project = _project(tmp_path)
    val = [r["text"] for r in project.load_manifest() if r["split"] == "val"]

    class Flaky(FakeQualityBackend):
        def synthesize_many(self, req, n, out_dir):
            if ((self.cur or {}).get("id", "current"), req.text) in self.fail:
                self.calls.append((dataclasses.replace(req), int(n), (self.cur or {}).get("id")))
                raise RuntimeError("Read timed out. (read timeout=600)")
            return super().synthesize_many(req, n, out_dir)

    b1 = Flaky(project, sovits=(8, 10), gpt=(6, 7), fail={("s8-g6", t) for t in val[:2]})
    assert _run(cfg, project, b1)["selection"]["best"] == "s8-g7"
    b2 = Flaky(project, sovits=(8, 10), gpt=(6, 7))
    second = _run(cfg, project, b2)
    s = second["selection"]
    assert s["best"] == "s8-g6" and next(r for r in s["results"] if r["id"] == "s8-g6")["failed"] == 0
    assert {c[2] for c in b2.calls} == {"s8-g6"}   # 别的模型都用存下的结果；s8-g6 重新试了上次失败的两句（和试听）
    assert {c[0].text for c in b2.calls} >= set(val[:2])
    # 这次加载失败的模型也不存：下次再试（别的模型用存下的结果）
    cfg3, project3 = _project(tmp_path / "broken")
    b3 = Flaky(project3, sovits=(8, 10), gpt=(6, 7))
    loads = b3.use_checkpoint

    def broken(ck):
        if ck["id"] == "s10-g7":
            raise RuntimeError("模拟：模型文件读不了")
        loads(ck)

    b3.use_checkpoint = broken
    _run(cfg3, project3, b3)
    assert "s10-g7" not in {c[2] for c in b3.calls}
    b4 = Flaky(project3, sovits=(8, 10), gpt=(6, 7))
    _run(cfg3, project3, b4)
    assert {c[2] for c in b4.calls} == {"s10-g7"}


def test_mini_calibration_that_measured_nothing_is_retried_next_time(tmp_path, fast, vt_log):
    """生成前的小校准一句都没生成出来：不记成做完了（下次生成时再试），也不把挑模型时实测的语速盖成没测过的 1.0。"""
    cfg, project = _project(tmp_path, n_val=8)

    class Down(FakeQualityBackend):
        def synthesize_many(self, req, n, out_dir):
            self.calls.append((req, n, "x"))
            raise RuntimeError("Read timed out. (read timeout=600)")

    b = Down(project, sovits=(8, 10), gpt=(6, 7))
    _old_model(project, b)
    project.update_models("gptsovits", {"speed": {"zh": 1.12}})
    got = sel.prepare_identical(cfg, project, b, judge=_judge(), use_asr=False)
    entry = project.load_models()["gptsovits"]
    assert got["mini"] is False and "identical" not in entry and entry["speed"] == {"zh": 1.12}
    assert sel.identical_stale(project, b)
    assert any("小校准这次没做成" in m and "一句都没生成出来" in m for m in vt_log.messages)
    # 引擎好了：下次生成前再做（上次失败的请求没有存，重新试）
    ok = FakeQualityBackend(project, sovits=(8, 10), gpt=(6, 7), ratio=1.1)
    got2 = sel.prepare_identical(cfg, project, ok, judge=_judge(), use_asr=False)
    block = project.load_models()["gptsovits"]["identical"]
    assert got2["mini"] is True and ok.calls and block["speed"]["zh"] == pytest.approx(1.1, abs=0.02)
    assert block["ref_prior"] and min(block["ref_prior"].values()) > sel.FAIL_S


def test_mini_calibration_keeps_the_measured_speed_when_it_cannot_measure(tmp_path, fast, monkeypatch):
    """没参加训练的录音不到 8 句：小校准量不了语速，identical.speed 不写（不是 1.0），「一模一样」生成时照旧用挑模型时
    实测的语速（和别的档位一样），不会比「均衡」慢 15%。"""
    from voicetwin.synth import engine as eng

    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    cfg, project = _project(tmp_path, n_val=5)
    b = FakeQualityBackend(project, sovits=(8,), gpt=(6,), ratio=1.15)
    _old_model(project, b)
    project.update_models("gptsovits", {"speed": {"zh": 1.15}})
    b.speed_calibration = lambda: project.load_models()["gptsovits"].get("speed", {})
    got = sel.prepare_identical(cfg, project, b, judge=_judge(), use_asr=False)
    block = project.load_models()["gptsovits"]["identical"]
    assert got["mini"] is True and block["speed"] == {} and block["speed_info"]["n_items"] == {"zh": 5}
    n = eng.Narrator(cfg, project, b, quality="identical", tier="none", asr_check=False)
    assert n._speed_for("zh") == pytest.approx(1.15)


def test_audition_prior_leaves_out_references_that_were_never_measured(tmp_path, fast):
    """试听时某一条参考的请求全都没成功（不是这条参考的分数）：它不进先验（不给它 −3），别的照常。"""
    cfg, project = _project(tmp_path, n_val=8, n_train=12, sources=3)

    class OneBad(FakeQualityBackend):
        bad = None

        def synthesize_many(self, req, n, out_dir):
            stem = Path(str(req.ref_audio)).stem
            self.bad = self.bad or stem   # 第一条参考的请求全都失败
            if stem == self.bad:
                raise RuntimeError("Read timed out. (read timeout=600)")
            return super().synthesize_many(req, n, out_dir)

    b = OneBad(project, sovits=(8,), gpt=(6,))
    project.update_models("gptsovits", {"selected": b.checkpoints()[0]})
    res = sel.audition_references(cfg, project, b, sim=sel._Sim(cfg, project, judge=_judge()), use_asr=False)
    assert b.bad and b.bad not in res["prior"] and len(res["prior"]) == 8 and res["unmeasured_refs"] == 1
    assert min(res["prior"].values()) > sel.FAIL_S and res["n_refs"] == 8


def test_small_group_does_not_block_first_place():
    """只有 1 句纯英文：两个模型差 0.5% 不能算「明显更差（超出误差范围）」，综合总评分更高的照样排第一；
    显示时不写「± 0.0」。"""
    rng = np.random.default_rng(11)
    base_m, base_z = rng.uniform(88, 96, 20), rng.uniform(88, 96, 20)
    pa, pb, groups = [], [], []
    for i in range(20):
        pa += [float(base_m[i] + 0.5 + rng.normal(0, 2.0)), float(base_z[i] + 0.5 + rng.normal(0, 2.0))]
        pb += [float(base_m[i]), float(base_z[i])]
        groups += ["mixed", "zh"]
    a = _res("A", pa + [95.0], groups + ["en"], w=[2.0] * 41)
    b = _res("B", pb + [95.5], groups + ["en"], w=[2.0] * 41)
    for r in (a, b):  # 纯英文也算进综合总评分（素材里有一点）
        r["four"] = LG.group_scores([{"key": k, "group": v["group"], "pct": v["pct"], "w": v["w"]}
                                     for k, v in r["per_item"].items()], {"mixed": 0.5, "zh": 0.45, "en": 0.05})
    assert a["four"]["composite"]["mean"] > b["four"]["composite"]["mean"]
    rk = sel.rank_results([a, b])
    assert rk["first"]["id"] == "A" and not rk["notes"]
    cmp = LG.paired_compare([{"key": k, "group": v["group"], "pct": v["pct"], "w": v["w"]} for k, v in b["per_item"].items()],
                            [{"key": k, "group": v["group"], "pct": v["pct"], "w": v["w"]} for k, v in a["per_item"].items()],
                            rk["weights"])
    assert cmp["groups"]["en"]["few"] is True and cmp["groups"]["en"]["clear"] is None and cmp["groups"]["en"]["n"] == 1
    text = LG.four_scores_text(a["four"])
    assert "纯英文 95.0%（只有 1 句，太少，量不出误差范围）" in text and "± 0.0（1 句）" not in text
    lines = sel.deep_summary_lines({"results": [a, b], "val_items": 41, "test_items": 0, "four_ok": True})
    assert "「纯英文」只有 1 句，太少：这一类分不出两个模型谁更好，排名次时只算进综合总评分。" in lines


def test_stage_c_does_not_reuse_screen_records(tmp_path, fast, monkeypatch):
    """第三步每句 4 个 = 2 条参考 × 2 个，和第一、二步每句 2 个一样：第三步也要自己量（排序权重校准要用音调起伏 / 频谱），
    不能拿第一、二步存下的结果。第一、二步之间照样共用。"""
    from voicetwin.eval.identical_judge import IdenticalScorer

    monkeypatch.setattr(IdenticalScorer, "_shape", lambda self, wav, sr, text: (1.5, 2.5))
    seen = {}
    orig = sel._DeepSelect.calibration

    def spy(self, results):
        rows = [m for r in results for v in r["per_item"].values() if v["kind"] == "val" for m in v["rows"]]
        seen["miss"], seen["tot"] = sum(1 for m in rows if m.get("prosody_z") is None), len(rows)
        return orig(self, results)

    monkeypatch.setattr(sel._DeepSelect, "calibration", spy)
    final = sel._DeepSelect.final
    cfg, project = _project(tmp_path)
    b = FakeQualityBackend(project, final=4)

    def mark(self, *a, **k):
        b.c0 = len(b.calls)
        return final(self, *a, **k)

    monkeypatch.setattr(sel._DeepSelect, "final", mark)
    _run(cfg, project, b)
    assert seen["tot"] > 0 and seen["miss"] == 0
    # 第一步和第二步都有 s6-g6（第二步 = 第一步最好的语气模型 × 每个音色模型）：第二步用第一步存下的，不再生成
    assert sum(1 for c in b.calls[:b.c0] if c[2] == "s6-g6") == 10


class _LenMember:
    """声纹分数只跟长短有关的假模型（和 JudgeMember 一样：短句子按同样长度的你自己的录音的标准）：
    6 秒以上 1.0，2.5 秒 0.85。"""
    name = "m"
    calib = {"p50": 1.0}

    @staticmethod
    def curve(seconds):
        return float(np.interp(seconds, [2.5, 6.0], [0.85, 1.0]))

    def pct_raw(self, emb, seconds=None):
        return 100.0 * float(emb[0]) / (self.curve(seconds) if seconds is not None else 1.0)


class _LenJudge:
    members = [_LenMember()]
    models = ["m"]

    def embed_with_seconds(self, wav, sr):
        secs = len(wav) / sr
        return {"m": np.array([_LenMember.curve(secs)])}, secs

    def signature(self):
        return "len-judge"


def test_group_calibration_uses_the_same_short_clip_standard_as_generated_sentences(tmp_path):
    """两组只是录音长短不一样（和中文英文无关）：按组校准不能把长短当成「这类句子天生分数低」。你自己的录音按给生成的
    句子打分一样的算法正好是 100%，一个 90% 像你的生成句子还是 90%。"""
    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, "长短")
    project.root.mkdir(parents=True, exist_ok=True)
    project.clips_dir.mkdir(parents=True, exist_ok=True)
    recs = []
    for k in range(12):
        for g, text, dur in (("mixed", MIXED_TEXTS[0], 2.5), ("zh", ZH_TEXTS[0], 6.0)):
            path = project.clips_dir / f"{g}{k:02d}.wav"
            sf.write(str(path), (0.1 * np.ones(int(dur * SR))).astype(np.float32), SR)
            recs.append({"id": f"{g}{k:02d}", "path": project.relpath(path), "text": text, "lang": "zh", "split": "train",
                         "keep": True, "duration": dur, "voiced": dur})
    project.save_manifest(recs)
    cal = LG.build_group_calibration(project, _LenJudge())
    assert cal["groups"]["mixed"]["factors"]["m"] == pytest.approx(1.0, abs=1e-6)
    assert cal["groups"]["mixed"]["median_pct"]["m"] == pytest.approx(100.0, abs=0.01)
    m = _LenMember()
    assert LG.calibrated_raw({"m": m.pct_raw(np.array([m.curve(2.5)]), 2.5)}, "mixed", cal) == pytest.approx(100.0)
    assert LG.calibrated_pct({"m": m.pct_raw(np.array([0.9]), 6.0)}, "mixed", cal) == pytest.approx(90.0)
    # 人声秒数存在声纹缓存里：再算一次（换了标准等）直接用，结果一样
    (project.cache_dir / LG.CALIB_FILE).unlink()
    assert LG.build_group_calibration(project, _LenJudge())["groups"] == cal["groups"]


def test_speed_lines_are_per_language():
    """没参加训练的录音是英文时：英文的语速量到了、调了，不能说「只有 0 句能比语速……语速先不调」。"""
    lines = sel.deep_summary_lines({"results": [], "val_items": 20, "test_items": 24, "four_ok": True,
                                    "speed_info": {"n_items": {"en": 20}, "median": {"en": 1.1}}})
    assert not any("只有 0 句" in x for x in lines)
    assert "语速（实测，英文 20 句）：模型读得比你本人慢 10%，生成时按 1.1 倍速读，和你本人一样快。" in lines
    two = sel.speed_lines({"n_items": {"zh": 12, "en": 3}, "median": {"zh": 0.98}, "applied": {"zh": 1.0, "en": 1.0}})
    assert two == ["语速（实测，中文 12 句）：模型读得比你本人快 2%，差不到 3%，不用调。",
                   "语速（英文）：没参加训练的录音只有 3 句能比（不到 8 句，量不准），这次没测，语速先不调。"]
    assert sel.speed_lines({"n_items": {"zh": 9}, "median": {"zh": 1.4}, "applied": {"zh": 1.25}}) == [
        "语速（实测，中文 9 句）：模型读得比你本人慢 40%，生成时按 1.25 倍速读（最多只能调到这么多，还会比你本人慢一点）。"]
    assert sel.speed_lines(None) == []


def test_status_line_and_result_screens_call_the_deep_score_the_same(deep_run):
    """「一模一样」的挑选里的分数是综合总评分：页面顶部的状态、训练完、重新挑选完都叫「综合总评分」，不叫「像你本人」。"""
    from voicetwin.webui import app as A

    cfg, project, _, info = deep_run
    entry = project.load_models()["gptsovits"]
    assert A._best_selection(entry) == ("s8-g6", "综合总评分 100.0%")
    status = A._voice_status_md(cfg, project.voice)
    assert "自动挑选：综合总评分 100.0%" in status and "像你本人" not in status
    # 标准的挑法照旧叫「像你本人」
    assert A._best_selection({"selection": {"best": "a", "results": [{"id": "a", "pct": 91.0}]}}) == ("a", "像你本人 91.0%")


def test_result_screens_do_not_claim_an_unmeasured_speed(tmp_path, fast):
    """没参加训练的录音不到 8 句时语速没量：结果页不能说「和你本人一致」「调得和你本人一样」。"""
    from voicetwin.webui import app as A

    cfg, project = _project(tmp_path, n_val=4)
    b = FakeQualityBackend(project, sovits=(8, 10), gpt=(6, 7), ratio=1.15)
    info = _run(cfg, project, b)
    head = A._select_done_md(info).splitlines()[0]
    assert head.endswith("；语速：这次没测（没参加训练的录音不到 8 句，量不准），先按正常速度") and "一致" not in head
    tmd = A._train_done_md({"train_minutes": 3.0, "selection": info, "selected": info["selected"]}, show_plan=False)
    assert "调得和你本人一样" not in tmd and "语速这次没测（没参加训练的录音不到 8 句，量不准），先按正常速度生成" in tmd
    # 量到了、调了：照实说
    cfg2, project2 = _project(tmp_path / "ok", n_val=8)
    info2 = _run(cfg2, project2, FakeQualityBackend(project2, sovits=(8,), gpt=(6,), ratio=1.15))
    assert A._select_done_md(info2).splitlines()[0].endswith("；语速：已按实测校准")
    assert "并按实测校准了语速" in A._train_done_md(
        {"train_minutes": 3.0, "selection": info2, "selected": info2["selected"]}, show_plan=False)
    # 标准的挑法没量到语速（speed 是空的）：也不说「一致」
    assert A._select_done_md({"speed": {}, "selection": {"best": "a", "results": []}}).endswith("；语速：这次没测出来，先按正常速度")


def test_ranking_weight_note_for_the_teacher_has_no_jargon():
    """排序权重的校准给老师看的那句话不写「留一句法」「+0.083」「p90」这些内部的东西（带数的说明只进日志和 models.json）。"""
    import re

    planted = {"rate": 0.8, "pros": 0.3, "ltas": 0.04, "cap": "none"}
    adopted = CR.calibrate(_cands(np.random.default_rng(7), 30, planted), cap_value=110.0)
    kept = CR.calibrate(_cands(np.random.default_rng(1), 60, CR.DEFAULTS, noise=True), cap_value=110.0)
    few = CR.calibrate({}, cap_value=None)
    assert adopted["adopted"] and "留一句法" in CR.describe(adopted)
    for res in (adopted, kept, few):
        text = CR.plain(res)
        assert text and not re.search(r"\d", text) and "留一句法" not in text and "p90" not in text
    assert "已经按你的录音调整过" in CR.plain(adopted) and "照旧" in CR.plain(kept) and "录音不够" in CR.plain(few)
    lines = sel.deep_summary_lines({"results": [], "val_items": 20, "test_items": 0, "four_ok": True,
                                    "weights_note": CR.describe(adopted), "weights_plain": CR.plain(adopted)})
    assert CR.plain(adopted) + "。" in lines and not any("留一句法" in x for x in lines)


def test_deep_selection_stores_the_plain_weights_sentence(deep_run):
    _, _, _, info = deep_run
    s = info["selection"]
    assert s["weights_plain"] and s["weights_plain"] + "。" in s["lines"]
    assert not any("留一句法" in x or "排序权重" in x for x in s["lines"])
