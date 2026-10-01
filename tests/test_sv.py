"""精准声纹打分（v0.1.7）：前端（人声检测、fbank）、模型下载与校验、AS-norm 和两头校准、生成时用到的地方。"""

import hashlib
import json
import types

import numpy as np
import pytest

from voicetwin import workflows as wf
from voicetwin.eval import speaker as spk
from voicetwin.eval import sv_frontend as fe
from voicetwin.eval import sv_models

from conftest import make_cfg


# ---------------------------------------------------------------------------- 前端
def test_kaldi_fbank_matches_torchaudio():
    """和 3D-Speaker / WeSpeaker 训练时用的 torchaudio.compliance.kaldi.fbank 一致（参考值由 torchaudio 算出）。"""
    x = sv_models.selftest_signal(1.0)
    f = fe.kaldi_fbank(x)
    assert f.shape == (98, 80) and f.dtype == np.float32
    for (i, j), want in {(0, 0): -9.4279, (10, 5): -3.4473, (30, 40): -7.0927, (60, 79): -15.9424,
                         (97, 20): -4.8129}.items():
        assert abs(float(f[i, j]) - want) < 0.01
    f32 = fe.kaldi_fbank(x, scale=32768.0)
    assert abs(float(f32[10, 5]) - 17.3471) < 0.01 and abs(float(f32[97, 20]) - 15.9815) < 0.01
    assert fe.kaldi_fbank(np.zeros(100, np.float32)).shape == (0, 80)


class _FakeVadSession:
    """假的 silero-vad：按预先给定的概率序列逐窗输出。"""

    def __init__(self, probs):
        self.probs = list(probs)
        self.i = 0

    def run(self, _outputs, feeds):
        assert feeds["x"].shape == (1, fe.VAD_WINDOW)
        p = self.probs[self.i] if self.i < len(self.probs) else 0.0
        self.i += 1
        return np.array([[p]], np.float32), feeds["h"], feeds["c"]


def _vad(probs):
    vad = fe.SileroVAD.__new__(fe.SileroVAD)
    vad.sess = _FakeVadSession(probs)
    vad.threshold, vad.min_silence, vad.min_speech = 0.5, 0.25, 0.10
    import threading

    vad._lock = threading.Lock()
    return vad


def test_vad_spans_follow_sherpa_rules():
    w = fe.VAD_WINDOW
    # 10 窗说话、5 窗安静（0.16 秒 < 0.25 秒，不算说完）、10 窗说话、20 窗安静、2 窗说话（0.064 秒 < 0.1 秒，丢掉）
    probs = [0.9] * 10 + [0.1] * 5 + [0.9] * 10 + [0.1] * 20 + [0.9] * 2 + [0.1] * 10
    spans = _vad(probs).spans(np.zeros(len(probs) * w, np.float32))
    assert spans == [(0, 25 * w)]
    # 概率在 0.35~0.5 之间：既不开始也不结束
    probs = [0.4] * 5 + [0.9] * 8 + [0.4] * 30 + [0.1] * 10
    assert _vad(probs).spans(np.zeros(len(probs) * w, np.float32)) == [(5 * w, 43 * w)]


def test_speech_only_drops_pauses_whatever_they_contain():
    """停顿是绝对静音还是有环境声，去掉之后剩下的人声完全一样：分数不受停顿影响。"""
    w = fe.VAD_WINDOW
    rng = np.random.default_rng(0)
    speech = (0.3 * rng.standard_normal(20 * w)).astype(np.float32)
    probs = [0.9] * 20 + [0.0] * 40 + [0.9] * 20
    quiet = np.concatenate([speech, np.zeros(40 * w, np.float32), speech])
    roomy = np.concatenate([speech, (0.01 * rng.standard_normal(40 * w)).astype(np.float32), speech])
    a = _vad(probs).speech_only(quiet)
    b = _vad(probs).speech_only(roomy)
    pad = int(fe.VAD_PAD_SECONDS * fe.SR)
    assert a.size == b.size == 2 * (20 * w + pad)
    np.testing.assert_array_equal(a[: 20 * w], speech)
    np.testing.assert_array_equal(b[-20 * w:], speech)
    # 几乎没有人声：用整段（太短的声纹不可靠）
    short = np.zeros(30 * w, np.float32)
    assert _vad([0.9] * 3 + [0.0] * 27).speech_only(short).size == short.size


def test_ort_session_turns_on_denormals_as_zero(monkeypatch, tmp_path):
    calls = {}

    class Opts:
        def __init__(self):
            self.entries = {}

        def add_session_config_entry(self, k, v):
            self.entries[k] = v

    def session(path, sess_options=None, providers=None):
        calls.setdefault("providers", []).append(providers)
        calls["entries"] = sess_options.entries
        if providers[0] == "CUDAExecutionProvider":
            raise RuntimeError("没有 CUDA")
        return "sess"

    fake = types.SimpleNamespace(SessionOptions=Opts, InferenceSession=session, set_default_logger_severity=lambda v: None,
                                 get_available_providers=lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"])
    monkeypatch.setitem(__import__("sys").modules, "onnxruntime", fake)
    assert fe.ort_session(tmp_path / "m.onnx", device="cpu") == "sess"
    assert calls["entries"]["session.set_denormal_as_zero"] == "1"
    assert calls["providers"] == [["CPUExecutionProvider"]]
    calls.clear()
    assert fe.ort_session(tmp_path / "m.onnx", device="auto") == "sess"  # 显卡用不了：自动改用 CPU
    assert calls["providers"] == [["CUDAExecutionProvider", "CPUExecutionProvider"], ["CPUExecutionProvider"]]


# ---------------------------------------------------------------------------- 模型
class _FakeSess:
    def __init__(self, dim=8):
        self.dim = dim
        self.seen = []

    def run(self, _outputs, feeds):
        x = next(iter(feeds.values()))
        self.seen.append(x.shape)
        v = np.ones(self.dim, np.float32) * (1.0 + 0.001 * x.shape[1])
        return [v[None]]


def _embedder(kind="wave"):
    spec = sv_models.SVModel(key="fake", label="假模型", file="fake.onnx", kind=kind, size=0, sha256=None, sources=())
    emb = sv_models.OnnxEmbedder.__new__(sv_models.OnnxEmbedder)
    import threading

    emb.spec, emb.sess, emb.input, emb._lock = spec, _FakeSess(), "x", threading.Lock()
    return emb


def test_embedder_windows_long_audio_and_pads_short():
    emb = _embedder("wave")
    sr = 16000
    out = emb.embed16k(np.zeros(sr * 50, np.float32))
    assert out.shape == (8,) and len(emb.sess.seen) == 3 and max(s[1] for s in emb.sess.seen) <= sr * 20
    emb.sess.seen.clear()
    emb.embed16k(np.zeros(sr * 22, np.float32))
    assert len(emb.sess.seen) == 1  # 不到 25 秒一次算完
    emb.sess.seen.clear()
    emb.embed16k(np.zeros(1000, np.float32))
    assert emb.sess.seen[0][1] >= 8000  # 太短的重复到半秒
    fb = _embedder("fbank")
    fb.embed16k(np.zeros(sr * 3, np.float32) + 0.01)
    assert fb.sess.seen[0] == (1, 298, 80)


def test_registry_is_consistent():
    assert sv_models.DEFAULT_ENSEMBLE and all(k in sv_models.MODELS for k in sv_models.DEFAULT_ENSEMBLE)
    for m in list(sv_models.MODELS.values()) + [sv_models.VAD_MODEL]:
        assert m.sources and all(u.startswith("https://") for u in m.sources)
        assert m.sources[0].startswith(sv_models.RELEASE_BASE)  # 先从本项目的发布页下载
        assert m.sha256 is None or len(m.sha256) == 64
    cfg = make_cfg(__import__("pathlib").Path("/tmp/x"))
    assert sv_models.ensemble_keys(cfg) == list(sv_models.DEFAULT_ENSEMBLE)
    cfg = make_cfg(__import__("pathlib").Path("/tmp/x"), similarity={"sv_models": "campplus-zh-en，不存在的"})
    assert sv_models.ensemble_keys(cfg) == ["campplus-zh-en"]


class _Resp:
    def __init__(self, data, status=200):
        self.data, self.status = data, status
        self.headers = {"Content-Length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        if self.status >= 400:
            raise IOError(f"HTTP {self.status}")

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self.data), chunk_size):
            yield self.data[i:i + chunk_size]


def test_download_verifies_and_falls_back(tmp_path, monkeypatch):
    good = b"G" * 4096
    spec = sv_models.SVModel(key="m1", label="模型一", file="m1.onnx", kind="fbank", size=len(good),
                             sha256=hashlib.sha256(good).hexdigest(), sources=("https://a/m1", "https://b/m1"))
    vad = sv_models.SVModel(key="silero-vad", label="VAD", file="vad.onnx", kind="vad", size=len(good),
                            sha256=hashlib.sha256(good).hexdigest(), sources=("https://b/vad",))
    monkeypatch.setattr(sv_models, "VAD_MODEL", vad)
    monkeypatch.setattr(sv_models, "MODELS", {"m1": spec})
    monkeypatch.setattr(sv_models, "DEFAULT_ENSEMBLE", ("m1",))
    monkeypatch.setattr(sv_models.time, "sleep", lambda s: None)
    hits = []

    class Session:
        def get(self, url, stream=True, timeout=60):
            hits.append(url)
            if url.startswith("https://a/"):
                return _Resp(b"X" * 4096)  # 内容不对：sha256 核对不通过
            return _Resp(good)

    import requests

    monkeypatch.setattr(requests, "Session", Session)
    cfg = make_cfg(tmp_path, similarity={"model_dir": str(tmp_path / "sv")})
    assert [m.key for m in sv_models.missing(cfg)] == ["silero-vad", "m1"]
    seen = []
    got = sv_models.download(cfg, progress=lambda f, m: seen.append(f))
    assert sorted(got) == ["m1.onnx", "vad.onnx"]
    assert hits.count("https://a/m1") == sv_models.DOWNLOAD_ATTEMPTS and "https://b/m1" in hits
    assert (tmp_path / "sv" / "m1.onnx").read_bytes() == good and not list((tmp_path / "sv").glob("*.part"))
    assert sv_models.missing(cfg) == [] and seen and max(seen) < 1.0
    assert sv_models.download(cfg) == []  # 已经齐全：什么也不做

    class Broken:
        def get(self, url, stream=True, timeout=60):
            return _Resp(b"", status=404)

    monkeypatch.setattr(requests, "Session", Broken)
    (tmp_path / "sv" / "m1.onnx").write_bytes(b"Y" * 4096)  # 被改坏的文件
    with pytest.raises(RuntimeError, match="模型一 下载失败"):
        sv_models.download(cfg)
    assert not (tmp_path / "sv" / "m1.onnx").exists()  # 核对不通过的文件不会留下来


def test_selftest_catches_a_broken_model(monkeypatch, tmp_path):
    spec = sv_models.SVModel(key="rd", label="RD", file="rd.onnx", kind="wave", size=0, sha256=None, sources=("https://x",))
    monkeypatch.setitem(sv_models.SELFTEST, "rd", {"head": [1.0] * 16, "norm": 4.0})

    class Emb:
        def __init__(self, s, p):
            pass

        def embed16k(self, x):
            return np.ones(16, np.float32) * value

    monkeypatch.setattr(sv_models, "OnnxEmbedder", Emb)
    path = tmp_path / "rd.onnx"
    path.write_bytes(b"0" * 2048)
    value = 1.0
    assert sv_models.file_ok(spec, path, deep=True)
    path.write_bytes(b"1" * 2049)  # 换了文件（大小不同）：重新核对
    value = 3.0  # 方向一样但范数不对
    assert not sv_models.file_ok(spec, path, deep=True)


# ---------------------------------------------------------------------------- AS-norm 和两头校准
def _unit(v):
    v = np.asarray(v, np.float64)
    return v / np.linalg.norm(v)


def _world(seed=0, dim=32, n_cohort=200):
    rng = np.random.default_rng(seed)
    me = _unit(rng.normal(size=dim))
    cohort = np.stack([_unit(rng.normal(size=dim)) for _ in range(n_cohort)]).astype(np.float32)
    mu, sd = spk.cohort_self_stats(cohort)
    noisy = lambda base, s: _unit(base + s * rng.normal(size=dim) / np.sqrt(dim))  # noqa: E731
    return rng, me, {"emb": cohort, "mu": mu, "sd": sd}, noisy


def test_two_sided_calibration_maps_strangers_to_0_and_you_to_100():
    rng, me, cohort, noisy = _world()
    enrol = [noisy(me, 0.6) for _ in range(30)]
    cen = spk.centroid(enrol)
    held_out = [noisy(me, 0.6) for _ in range(20)]
    enc = types.SimpleNamespace(name="fake", reliable=True)
    probe = spk.JudgeMember(enc, cen, {}, cohort)
    stats = spk.calibration_stats([spk.cosine(e, cen) for e in held_out], [probe.norm_score(e) for e in held_out],
                                  spk.impostor_scores(cohort, cen))
    assert stats["norm"] == "asnorm" and stats["g50"] > stats["i0"] > stats["i50"]
    member = spk.JudgeMember(enc, cen, stats, cohort)
    judge = spk.SimilarityJudge([member])
    assert judge.calibrated and judge.precise
    mine = [judge.judge_embeddings({"fake": noisy(me, 0.6)})["pct"] for _ in range(40)]
    strangers = [judge.judge_embeddings({"fake": c})["pct"] for c in cohort["emb"][:40]]
    assert 80 <= np.median(mine) <= 100 and max(strangers) <= 30 and np.median(strangers) == 0.0
    res = judge.judge_embeddings({"fake": cen})
    assert res["pct"] == 100.0 and res["pct_raw"] > 100.0  # 显示封顶 100%，排序用的不封顶
    rng_ = judge.natural_range()
    assert rng_["p50"] == 100.0 and rng_["p10"] < rng_["p25"] < 100.0 < rng_["p90"]
    info = judge.info()
    assert info["precise"] and info["natural_range"] == rng_ and info["calibration"]["fake"]["norm"] == "asnorm"


def test_as_norm_matches_formula():
    _, me, cohort, noisy = _world(1)
    x = noisy(me, 0.5)
    m = spk.JudgeMember(types.SimpleNamespace(name="f"), me, {}, cohort)
    s = float(np.dot(x, me))
    te = spk.topk_stats(me, cohort["emb"])
    tt = spk.topk_stats(x, cohort["emb"])
    assert abs(m.norm_score(x) - 0.5 * ((s - te[0]) / te[1] + (s - tt[0]) / tt[1])) < 1e-6
    # 没有陌生人声纹库：就是余弦相似度；旧的换算方式（100 × s / p50，封顶 100）不变
    legacy = spk.JudgeMember(types.SimpleNamespace(name="f"), me, {"p50": 0.8})
    assert abs(legacy.norm_score(x) - s) < 1e-5 and not legacy.two_sided
    res = spk.SimilarityJudge([legacy]).judge_embeddings({"f": x})
    assert res["pct"] == spk.pct_from_sim(s, 0.8)


def test_cohort_file_roundtrip(tmp_path):
    rng = np.random.default_rng(3)
    emb = rng.normal(size=(50, 16)).astype(np.float16)
    path = tmp_path / "c.npz"
    np.savez(path, **{"m__emb": emb})
    c = spk.load_cohort("m", path)
    assert c["emb"].shape == (50, 16) and abs(float(np.linalg.norm(c["emb"][0])) - 1.0) < 1e-5
    assert c["mu"].shape == (50,) and np.all(c["sd"] > 0)
    assert spk.load_cohort("没有这个模型", path) is None
    assert spk.load_cohort("m", tmp_path / "不存在.npz") is None


def test_ensemble_prefers_precise_models(tmp_path, monkeypatch):
    auto = make_cfg(tmp_path, speaker_encoder="auto")
    assert spk.ensemble_names(auto)[0] == spk.SV_AUTO
    made = []

    def fake_onnx(name, cfg):
        if name == "eres2netv2-zh":
            raise FileNotFoundError("还没下载")
        made.append(name)
        return types.SimpleNamespace(name=name, reliable=True)

    monkeypatch.setattr(spk, "_onnx_encoder", fake_onnx)
    encs = spk.get_speaker_ensemble(auto)
    assert [e.name for e in encs] == [k for k in sv_models.DEFAULT_ENSEMBLE if k != "eres2netv2-zh"]

    def none(name, cfg):
        raise FileNotFoundError("还没下载")

    monkeypatch.setattr(spk, "_onnx_encoder", none)
    monkeypatch.setattr(spk, "_has_module", lambda mod: False)
    cfg = make_cfg(tmp_path, speaker_encoder="auto", backends={"gptsovits": {"root": str(tmp_path / "没有")}})
    assert [e.name for e in spk.get_speaker_ensemble(cfg)] == ["mfcc-stats"]  # 都没有：退回旧的方式


def test_judge_shares_one_vad_pass_between_models():
    calls = []

    class Enc(spk.SpeakerEncoder):
        reliable = True
        prep_key = ("speech16k", 1)

        def __init__(self, name):
            self.name = name

        def prepare(self, wav, sr):
            calls.append("vad")
            return wav[::2]

        def embed_prepared(self, speech):
            return spk._l2(np.ones(4) + len(speech) % 3)

    judge = spk.SimilarityJudge([spk.JudgeMember(Enc("a"), spk._l2(np.ones(4)), {"p50": 0.9}),
                                 spk.JudgeMember(Enc("b"), spk._l2(np.ones(4)), {"p50": 0.9})])
    out = judge.embed(np.ones(16000, np.float32), 16000)
    assert set(out) == {"a", "b"} and calls == ["vad"]
    sig = judge.signature()
    assert sig == judge.signature() and len(sig) == 12
    judge.members[0].calib["p50"] = 0.8
    assert judge.signature() != sig


# ---------------------------------------------------------------------------- 环境检查 / 生成
def test_doctor_reports_sv_models(tmp_path, monkeypatch):
    cfg = make_cfg(tmp_path, similarity={"model_dir": str(tmp_path / "sv")})
    ok, detail = wf.sv_status(cfg)
    assert ok is None and ("下载缺少的模型" in detail or "onnxruntime" in detail)
    monkeypatch.setattr(sv_models, "missing", lambda cfg, keys=None: [])
    monkeypatch.setitem(__import__("sys").modules, "onnxruntime", types.SimpleNamespace())
    monkeypatch.setattr(spk, "COHORT_FILE", tmp_path / "没有.npz")
    ok, detail = wf.sv_status(cfg)
    assert ok is None and "陌生人声纹库" in detail
    (tmp_path / "c.npz").write_bytes(b"x")
    monkeypatch.setattr(spk, "COHORT_FILE", tmp_path / "c.npz")
    ok, detail = wf.sv_status(cfg)
    assert ok is True and "ReDimNet2" in detail


def test_shipped_cohort_covers_the_default_models():
    """程序附带的陌生人声纹库：每个默认模型都有，几百个人，中文和英文都有。"""
    for key in sv_models.DEFAULT_ENSEMBLE:
        c = spk.load_cohort(key)
        assert c is not None, key
        assert c["emb"].shape[0] >= 300 and c["emb"].shape[1] == sv_models.MODELS[key].dim
        assert c["zh"].sum() >= 50 and (~c["zh"]).sum() >= 200


def test_effective_target_uses_your_own_natural_range():
    from voicetwin.synth.engine import Narrator

    eng = Narrator.__new__(Narrator)
    eng.min_pct = 85.0
    eng._judge = types.SimpleNamespace(natural_range=lambda: {"p10": 82.0, "p25": 91.5, "p50": 100.0, "p90": 112.0})
    assert eng.effective_target(99.0) == 91.5  # 落在你自己录音的正常范围里就算达标
    eng._judge = types.SimpleNamespace(natural_range=lambda: {"p10": 70.0, "p25": 80.0, "p50": 100.0})
    assert eng.effective_target(99.0) == 85.0  # 不低于淘汰线
    eng._judge = types.SimpleNamespace(natural_range=lambda: None)
    assert eng.effective_target(99.0) == 99.0  # 旧的打分方式：照旧


def test_cached_sentences_are_rescored_when_the_judge_changes(tmp_path):
    from voicetwin.synth.engine import Narrator

    eng = Narrator.__new__(Narrator)
    eng.min_pct, eng.filter_mode = 85.0, "auto"
    judged = []

    class Judge:
        calibrated, reliable = True, True

        def signature(self):
            return "new"

        def judge(self, wav, sr):
            judged.append(len(wav))
            return {"pct": 72.0, "pct_raw": 72.4, "pcts": {"a": 72.0}, "sims": {"a": 0.5}, "sim": 0.5}

    eng._judge = Judge()
    eng._scorer = object()  # 已经"加载"过
    meta_path = tmp_path / "s.json"
    plan = types.SimpleNamespace(meta_path=meta_path)
    old = {"score": {"pct": 99.0, "issues": []}, "status": "✅", "hint": "", "flagged": False, "judge": "old"}
    meta = eng._rescore_cached(dict(old), np.zeros(1600, np.float32), 16000, plan)
    assert meta["score"]["pct"] == 72.0 and meta["status"] == "🔴" and "低于 85%" in meta["hint"]
    assert json.loads(meta_path.read_text(encoding="utf-8"))["judge"] == "new"
    again = eng._rescore_cached(meta, np.zeros(1600, np.float32), 16000, plan)
    assert again is meta and len(judged) == 1  # 标准没变：不再重复打分
