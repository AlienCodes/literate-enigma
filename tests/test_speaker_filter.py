"""声纹：素材里混入别人的声音要被剔除；"像你本人（%）"的校准、多模型打分、GPT-SoVITS 自带的 ERes2NetV2 加载。"""

import contextlib
import sys
import textwrap
import types

import numpy as np
import pytest

from voicetwin import workflows as wf
from voicetwin.eval import speaker as spk

from conftest import make_cfg, make_lecture


def test_other_speaker_is_filtered(tmp_path):
    pytest.importorskip("resemblyzer")
    src = tmp_path / "in"
    make_lecture(src / "本人_第1课.wav", repeats=3, f0=150, seed=1)
    make_lecture(src / "本人_第2课.wav", repeats=2, f0=150, seed=2)
    make_lecture(src / "学生提问.wav", repeats=1, f0=235, seed=3)  # 另一个人
    cfg = make_cfg(tmp_path / "ws", speaker_encoder="resemblyzer")
    summary = wf.run_prepare(cfg, "本人", [str(src)])
    project = wf.open_project(cfg, "本人", must_exist=True)
    recs = project.load_manifest()
    other = [r for r in recs if r["source"].startswith("学生提问")]
    mine = [r for r in recs if r["source"].startswith("本人")]
    assert other and all(not r["keep"] for r in other), [r.get("speaker_sim") for r in other]
    assert sum(r["keep"] for r in mine) >= 0.9 * len(mine)
    assert "声音不像本人（可能是别人说话）" in summary["dropped"]


# ---------------------------------------------------------------------------- 校准百分比
def test_pct_formula_and_status():
    assert spk.pct_from_sim(0.8, 0.8) == 100.0
    assert spk.pct_from_sim(0.9, 0.8) == 100.0  # 封顶 100%：和你自己的录音一样像
    assert spk.pct_from_sim(0.6, 0.8) == 75.0
    assert spk.pct_from_sim(-0.2, 0.8) == 0.0
    assert spk.pct_from_sim(0.7, None) is None and spk.pct_from_sim(None, 0.8) is None
    assert spk.status_for_pct(99.0) == "✅" and spk.status_for_pct(90.0) == "🟢" and spk.status_for_pct(84.9) == "🔴"
    assert spk.status_for_pct(None) == ""


def test_judge_is_calibrated_on_held_out_clips(prepared, tmp_path):
    cfg, project, _ = prepared
    judge = spk.SimilarityJudge.for_project(cfg, project)
    assert judge.available and judge.models == ["mfcc-stats"] and not judge.reliable
    member = judge.members[0]
    assert member.calib["source"] == "val" and member.calib["n"] >= 1 and member.p50 is not None
    info = judge.info()
    assert info["definition"] == spk.PCT_HELP and "以耳朵为准" in info["note"]
    # 打分用的平均声纹只用训练片段：验证集留给校准
    _, ids = spk.judge_centroid(project, member.encoder)
    val_ids = {r["id"] for r in project.load_manifest(only_kept=True) if r.get("split") == "val"}
    assert ids and not (set(ids) & val_ids)
    # 你自己的真实片段：接近 100%；另一个人（音高差很多）：明显更低
    val = [r for r in project.load_manifest(only_kept=True) if r.get("split") == "val"]
    real = [judge.judge_file(project.abspath(r["path"]))["pct"] for r in val]
    assert np.median(real) >= 95.0
    other = make_lecture(tmp_path / "别人.wav", repeats=1, f0=260, seed=9, with_srt=False)
    from voicetwin.utils.audio import load_audio

    wav, sr = load_audio(other)
    assert judge.judge(wav[: sr * 4], sr)["pct"] < np.median(real)
    # 第二次直接用缓存（结果一样）
    again = spk.SimilarityJudge.for_project(cfg, project)
    assert again.members[0].calib == member.calib


def test_judge_from_uploaded_originals(prepared):
    cfg, project, _ = prepared
    base = spk.SimilarityJudge.for_project(cfg, project)
    clips = [project.abspath(r["path"]) for r in project.load_manifest(only_kept=True)][:4]
    loo = spk.SimilarityJudge.from_files(cfg, clips, fallback=base)
    assert loo.members[0].calib["source"] == "uploaded_loo" and loo.members[0].p50 is not None
    one = spk.SimilarityJudge.from_files(cfg, clips[:1], fallback=base)
    assert one.members[0].calib["source"] == "voice_calibration" and one.members[0].p50 == base.members[0].p50
    alone = spk.SimilarityJudge.from_files(cfg, clips[:1])
    assert alone.members[0].p50 is None and not alone.calibrated
    res = alone.judge_file(clips[0])
    assert res["pct"] is None and res["sims"]  # 没法换算百分比时，只给原始相似度


class _NoisyEncoder(spk.SpeakerEncoder):
    """假的声纹模型：每段录音 = 同一个人的声纹 + 随机噪声（两段录音之间余弦约 0.65，像真的 ERes2NetV2 那样）。"""

    name = "noisy"
    reliable = True

    def __init__(self, dim=192, sigma=0.735):
        rng = np.random.default_rng(1)
        self.s = spk._l2(rng.normal(size=dim))
        self.dim, self.sigma = dim, sigma

    def embed_file(self, path):
        seed = sum(ord(ch) for ch in str(path)) * 7919 % (2 ** 32)
        n = np.random.default_rng(seed).normal(size=self.dim) / np.sqrt(self.dim)
        return spk._l2(self.s + self.sigma * n)


def test_one_or_two_originals_are_not_deflated(prepared):
    """只上传 1~2 段原声：「100%」的标准要用同样的方式算（素材里的真实录音和这 1~2 段比），
    不能借用「和几十段平均声纹比」的校准——那样你自己的真实录音也只有 80% 左右，被标成 🔴。"""
    cfg, project, _ = prepared
    enc = _NoisyEncoder()
    recs = project.load_manifest(only_kept=True)
    paths = [project.abspath(r["path"]) for r in recs]
    cen_many = spk.centroid([enc.embed_file(p) for p in paths[:40]])
    p50_many = float(np.median([spk.cosine(enc.embed_file(p), cen_many) for p in paths[:40]]))
    base = spk.SimilarityJudge([spk.JudgeMember(enc, cen_many, {"p50": p50_many, "source": "val"})])
    upload = paths[:1]
    judge = spk.SimilarityJudge.from_files(cfg, upload, fallback=base, encoders=[enc], project=project)
    member = judge.members[0]
    assert member.calib["source"] == "voice_clips_vs_uploaded" and member.p50 is not None
    others = paths[1:]
    new = np.median([judge.judge_embeddings({"noisy": enc.embed_file(p)})["pct"] for p in others])
    one_cen = spk.centroid([enc.embed_file(p) for p in upload])
    old = np.median([spk.pct_from_sim(spk.cosine(enc.embed_file(p), one_cen), p50_many) for p in others])
    assert old < 90.0 <= new  # 以前的做法：你自己的录音只有 80% 左右；现在接近 100%
    # 没给 project：直接用这个声音原来的标准（平均声纹和校准都是它自己的），不再把两种标准混在一起
    alone = spk.SimilarityJudge.from_files(cfg, upload, fallback=base, encoders=[enc])
    assert alone.members[0].calib["source"] == "voice_calibration"
    assert np.allclose(alone.members[0].centroid, cen_many) and alone.members[0].p50 == base.members[0].p50


def test_eres2netv2_embeds_long_audio_in_windows():
    """ERes2NetV2 一次只看约 10 秒：整篇讲课分段算再平均（一次送进去会显存不够）。"""
    enc = spk.ERes2NetV2Encoder.__new__(spk.ERes2NetV2Encoder)
    seen = []

    class Model:
        def __call__(self, x):
            seen.append(x.a.shape[1])
            return _T(np.ones((1, 4), np.float32))

    enc._torch, enc._model, enc._device = _fake_torch(), Model(), "cpu"
    enc._kaldi = types.SimpleNamespace(fbank=lambda x, **k: _T(np.zeros(((x.a.shape[1] - 400) // 160 + 1, 80))))
    import threading

    enc._lock = threading.Lock()
    sr = 16000
    rng = np.random.default_rng(0)
    long_wav = (0.2 * rng.normal(size=sr * 95)).astype(np.float32)
    emb = enc.embed(long_wav, sr)
    assert emb.shape == (4,) and len(seen) == 10 and max(seen) <= 1001  # 每段不超过 10 秒（约 1000 帧）
    seen.clear()
    enc.embed(long_wav[: sr * 8], sr)
    assert len(seen) == 1  # 短的照旧一次算完


def test_empty_judge_returns_nothing():
    judge = spk.SimilarityJudge([])
    assert not judge.available and judge.judge(np.zeros(16000, np.float32), 16000)["pct"] is None


def test_ensemble_names_follow_config(tmp_path):
    assert spk.ensemble_names(make_cfg(tmp_path)) == ["mfcc"]  # 测试配置指定了 mfcc
    auto = make_cfg(tmp_path, speaker_encoder="auto")
    assert spk.ensemble_names(auto) == [spk.SV_AUTO, "eres2netv2", "resemblyzer"]  # 先精准声纹模型，没下载时用旧的
    assert spk.ensemble_names(make_cfg(tmp_path, speaker_encoder="auto", similarity={"models": "resemblyzer，mfcc"})) \
        == ["resemblyzer", "mfcc"]


def test_ensemble_falls_back_to_mfcc(tmp_path, monkeypatch):
    monkeypatch.setattr(spk, "_has_module", lambda mod: False)
    cfg = make_cfg(tmp_path, speaker_encoder="auto", backends={"gptsovits": {"root": str(tmp_path / "没有")}})
    encs = spk.get_speaker_ensemble(cfg)
    assert [e.name for e in encs] == ["mfcc-stats"]


def test_eres2netv2_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        spk.ERes2NetV2Encoder(tmp_path)


# ---------------------------------------------------------------------------- 用假的 torch 走一遍 ERes2NetV2 的加载和打分流程
class _T:
    """极简的"张量"：只实现 ERes2NetV2Encoder 用到的几个方法。"""

    def __init__(self, a):
        self.a = np.asarray(a, dtype=np.float32)

    def unsqueeze(self, dim):
        return _T(np.expand_dims(self.a, dim))

    def to(self, device):
        return self

    def mean(self, dim=0, keepdim=False):
        return _T(self.a.mean(axis=dim, keepdims=keepdim))

    def __sub__(self, other):
        return _T(self.a - other.a)

    def reshape(self, *shape):
        return _T(self.a.reshape(*shape))

    def float(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.a


def _fake_torch():
    torch = types.ModuleType("torch")
    torch.from_numpy = lambda a: _T(a)
    torch.no_grad = contextlib.nullcontext
    torch.cuda = types.SimpleNamespace(is_available=lambda: False)
    torch.loaded = []

    def load(path, map_location=None, weights_only=None):
        torch.loaded.append(path)
        return {"state_dict": {"w": 1}}

    torch.load = load
    return torch


ERES_PY = textwrap.dedent('''
    import numpy as np
    import torch  # 测试里是假的 torch
    import pooling_layers  # 和真的 GPT-SoVITS 一样：同目录的顶层导入
    from fusion import AFF

    class ERes2NetV2:
        def __init__(self, baseWidth=26, scale=2, expansion=2, **kw):
            assert (baseWidth, scale, expansion) == (24, 4, 4)
            self.state = None

        def load_state_dict(self, state):
            self.state = state

        def eval(self):
            return self

        def to(self, device):
            return self

        def __call__(self, x):  # (B, T, F) -> (B, 160)；减过均值的 fbank，用逐频带的起伏当"声纹"
            feat = x.a.std(axis=1)
            return torch.from_numpy(np.concatenate([feat, feat], axis=1))
''')

KALDI_PY = textwrap.dedent('''
    import numpy as np
    import torch

    def fbank(x, num_mel_bins=23, sample_frequency=16000, dither=1.0):
        assert num_mel_bins == 80 and sample_frequency == 16000 and dither == 0.0
        w = x.a[0]
        n = (len(w) - 400) // 160 + 1
        frames = np.stack([w[i * 160:i * 160 + 400] for i in range(n)])
        spec = np.abs(np.fft.rfft(frames * np.hanning(400), axis=1))[:, :80] + 1e-6
        return torch.from_numpy(np.log(spec))
''')


def test_eres2netv2_loader_with_fake_torch(tmp_path, monkeypatch):
    root = tmp_path / "GPT-SoVITS"
    eres = root / spk.ERES_DIR_REL
    eres.mkdir(parents=True)
    (eres / "ERes2NetV2.py").write_text(ERES_PY, encoding="utf-8")
    (eres / "kaldi.py").write_text(KALDI_PY, encoding="utf-8")
    (eres / "pooling_layers.py").write_text("X = 1\n", encoding="utf-8")
    (eres / "fusion.py").write_text("class AFF:\n    pass\n", encoding="utf-8")
    ckpt = root / spk.SV_CKPT_REL
    ckpt.parent.mkdir(parents=True)
    ckpt.write_bytes(b"0")
    torch = _fake_torch()
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torchaudio", None)  # 没有 torchaudio：用整合包里的 kaldi.py
    for name in ("voicetwin_gsv_ERes2NetV2", "voicetwin_gsv_kaldi", "pooling_layers", "fusion"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    try:
        enc = spk.ERes2NetV2Encoder(root, device="cpu")
        assert torch.loaded == [str(ckpt)] and enc._model.state == {"w": 1}  # state_dict 外面那层被拆掉
        assert str(eres) not in sys.path  # 临时加的路径用完就拿掉
        sr = 16000
        t = np.arange(sr * 2) / sr
        rng = np.random.default_rng(0)
        a = (0.3 * np.sin(2 * np.pi * 150 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t))
             + rng.normal(0, 0.01, len(t))).astype(np.float32)
        b = (0.3 * np.sin(2 * np.pi * 420 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t))
             + rng.normal(0, 0.05, len(t))).astype(np.float32)
        ea, ea2, eb = enc.embed(a, sr), enc.embed(a * 0.5, sr), enc.embed(b, sr)
        assert ea.shape == (160,) and abs(float(np.linalg.norm(ea)) - 1.0) < 1e-5
        assert spk.cosine(ea, ea2) > spk.cosine(ea, eb)
        assert enc.embed(a[:4000], sr).shape == (160,)  # 很短的片段也能打分
    finally:
        for name in ("voicetwin_gsv_ERes2NetV2", "voicetwin_gsv_kaldi", "pooling_layers", "fusion"):
            sys.modules.pop(name, None)
