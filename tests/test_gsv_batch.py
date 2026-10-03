"""「一模一样」P4：一次请求同时生成同一句话的好几个版本（同一句话复制 n 份、用换行隔开、batch_size = n）。

测的东西（设计方案 §5.1 的 test_gsv_batch）：
- 按数字静音切开（_split_fragments）：正常、里面多一段静音、段数不对、太短、48 kHz、最后不到结尾、半精度溢出也修好；
- 按官方切分规则复刻（_batch_text）：老师 1004 句素材全部正好 4 段、和单独生成的一样；「好的。」只能单独生成；
- 单独生成的请求和以前一个字段、一个数都不差（_payload）；
- 拿真实的 api_v2.py（两个版本，只把模型换成假的）跑：一次请求拿到 4 个不同的版本、显存不够减半、
  减到 1 个还不够时先让出显存再试一次、「语速 1.0001」自检没通过时只有语速 1.0 的句子一个一个生成、切不开时改成一个一个生成；
- 不开引擎也能查的：一个一个生成的原因写的是真正的原因（自检里显存不够 / 自检出错没做完 / 自检没通过）、
  只有真的让出了显存才记 gpu_releases、自检通过的日志只写量出来的数、两次运行程序写进同一个文件夹不会覆盖文件；
- 识别校验模型让出显卡（CERChecker.release_gpu）。
"""

import csv
import io
import json
import logging
import math
import os
import socket
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from voicetwin import workflows as wf
from voicetwin.backends.base import SEED_STEP, Backend, SynthRequest, get_backend
from voicetwin.backends.gptsovits import (
    BATCH_PAD,
    BATCH_SPEED,
    GPTSoVITSBackend,
    _answer_error,
    _batch_text,
    _gsv_pre_seg,
    _split_fragments,
    _split_wav,
)

from conftest import make_cfg
from fake_gptsovits import REAL_API_V2, REAL_API_V2_2025, build_fake_root

ROOT = Path(__file__).resolve().parents[1]
MASTER_CSV = ROOT / "research" / "文字校正" / "老师的母本" / "母本_修缮后.csv"
TEXT = "大家好，今天我们讲第一课。"
APIS = pytest.mark.parametrize("api_src", [REAL_API_V2, REAL_API_V2_2025], ids=["abe9843", "20250606v2pro"])


# ---------------------------------------------------------------------------- 小工具
def _wav(x, sr):
    buf = io.BytesIO()
    sf.write(buf, np.asarray(x, dtype=np.int16), sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def _frag(rng, sec, sr, inner_zero=0.0):
    a = (rng.standard_normal(int(sec * sr)) * 3000).astype(np.int16)
    a[a == 0] = 1  # 随机数里偶尔有 0，不影响，但让「片段里没有长静音」更明确
    if inner_zero:
        k = len(a) // 2
        a[k:k + int(inner_zero * sr)] = 0
    return a


def _join(frags, zeros):
    return np.concatenate([np.concatenate([f, np.zeros(zeros, np.int16)]) for f in frags])


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self):
        return [r.getMessage() for r in self.records]


@pytest.fixture
def vt_log():
    h = ListHandler()
    logger = logging.getLogger("voicetwin")
    logger.addHandler(h)
    old = logger.level
    logger.setLevel(logging.INFO)
    try:
        yield h
    finally:
        logger.removeHandler(h)
        logger.setLevel(old)


# ---------------------------------------------------------------------------- 按数字静音切开
def test_split_normal_case_gives_n_pieces_with_padding():
    rng = np.random.default_rng(0)
    sr = 32000
    frags = [_frag(rng, s, sr) for s in (4.1, 5.0, 3.7, 4.4)]
    pieces = _split_fragments(_wav(_join(frags, int(0.5 * sr)), sr), 4, 0.5)
    assert pieces is not None and len(pieces) == 4
    pad = int(round(BATCH_PAD * sr))
    for got, want in zip(pieces, frags):
        assert got.dtype == np.int16
        assert np.array_equal(got[:-pad], want)  # 一个采样点都不差
        assert len(got) == len(want) + pad and not got[-pad:].any()  # 后面补 0.3 秒的 0（和单独生成时一样）


def test_split_rejects_ambiguous_answers():
    rng = np.random.default_rng(1)
    sr = 32000
    z = int(0.5 * sr)
    # 片段里面多出一段 0.4 秒的数字静音：段数不对，不能猜
    inner = _join([_frag(rng, 4, sr, inner_zero=0.4), _frag(rng, 4, sr)], z)
    assert _split_fragments(_wav(inner, sr), 2, 0.5) is None
    # 要 3 个，只回来 2 个
    two = _join([_frag(rng, 4, sr), _frag(rng, 4, sr)], z)
    assert _split_fragments(_wav(two, sr), 3, 0.5) is None
    # 有一段太短（0.2 秒 < 0.3 秒）
    short = _join([_frag(rng, 4, sr), _frag(rng, 0.2, sr)], z)
    pieces, _sr, why = _split_wav(_wav(short, sr), 2, 0.5)
    assert pieces is None and "第 2 个版本太短" in why
    # 最后一段静音没有到结尾（后面还有声音）
    tail = np.concatenate([two, _frag(rng, 0.01, sr)])
    pieces, _sr, why = _split_wav(_wav(tail, sr), 2, 0.5)
    assert pieces is None and "结尾" in why
    # 差 1 个采样点以内算到结尾
    assert _split_fragments(_wav(np.concatenate([two, [5]]), sr), 2, 0.5) is not None
    # 不是 WAV
    assert _split_fragments(b"not a wav", 2) is None
    # 静音不够长（0.25 秒 < 0.6 × 0.5 秒）：认不出是版本之间的静音
    assert _split_fragments(_wav(_join([_frag(rng, 2, sr)] * 2, int(0.25 * sr)), sr), 2, 0.5) is None


def test_split_48k_with_zeros_sized_at_32k():
    """V3 / V4 的输出是 48 kHz，引擎按 32 kHz 算的 0.5 秒静音只有 16000 个 0：也够长（≥ 0.6 × 0.5 × 48000）。"""
    rng = np.random.default_rng(2)
    sr = 48000
    frags = [_frag(rng, 4, sr) for _ in range(3)]
    pieces = _split_fragments(_wav(_join(frags, 16000), sr), 3, 0.5)
    assert pieces is not None and [round((len(p) - int(BATCH_PAD * sr)) / sr, 2) for p in pieces] == [4.0, 4.0, 4.0]


def test_split_repairs_int16_wrap_first():
    """半精度时 1.0 溢出成 -32768（「咔哒」）：切开前先修好（和单独生成用的是同一个 _fix_int16_wrap）。"""
    rng = np.random.default_rng(3)
    sr = 32000
    f = np.abs(_frag(rng, 1.0, sr)).astype(np.int16) + 10
    f[1000] = -32768  # 两边都是正的：溢出
    pieces = _split_fragments(_wav(_join([f, f], int(0.5 * sr)), sr), 2, 0.5)
    assert pieces is not None and pieces[0][1000] == 32767 and pieces[1][1000] == 32767


# ---------------------------------------------------------------------------- 按官方切分规则复刻
def test_batch_text_on_all_teacher_lines():
    """老师的 1004 句（母本修缮后、保留的）按程序生成时的样子整理后，复制 4 份全部正好切成 4 段、每段和单独生成的一样。"""
    from voicetwin.synth.script import tts_normalize

    rows = [r for r in csv.DictReader(open(MASTER_CSV, encoding="utf-8-sig")) if r["keep"] == "1"]
    assert len(rows) == 1004
    ok = 0
    for r in rows:
        t = tts_normalize(r["text"])
        bt = _batch_text(t, "zh", 4)
        single = _gsv_pre_seg(t, "zh")
        if bt is not None and len(single) == 1 and _gsv_pre_seg(bt, "zh") == single * 4 and bt.count("\n") == 3:
            ok += 1
    assert ok == 1004


def test_batch_text_rules():
    assert _batch_text("好的。", "zh", 4) is None  # 「。好的。」只有 4 个字：会和后面一份合在一起，只剩 2 段
    assert _gsv_pre_seg("\n".join(["。好的。"] * 4), "zh") == ["。好的。。好的。", "。好的。。好的。"]
    # 第一个标点前不到 4 个字：每份开头加「。」（单独生成时引擎自己也会加）
    assert _batch_text(TEXT, "zh", 3) == "\n".join(["。" + TEXT] * 3)
    assert _gsv_pre_seg(TEXT, "zh") == ["。" + TEXT]
    assert _batch_text("我们今天学习关系代词。", "zh", 2) == "我们今天学习关系代词。\n我们今天学习关系代词。"
    assert _batch_text("Yes.", "en", 4) == "\n".join([".Yes."] * 4)  # 加了「.」正好 5 个字，不会被合并
    assert _batch_text("有换行\n的句子。", "zh", 2) is None
    assert _batch_text("长" * 401 + "。", "zh", 2) is None
    assert _batch_text(TEXT, "zh", 1) is None
    # 结尾没有标点：单独生成时引擎补「。」，同时生成时每段也补
    assert _gsv_pre_seg(_batch_text("我们今天学习关系代词", "zh", 2), "zh") == ["我们今天学习关系代词。"] * 2


# ---------------------------------------------------------------------------- 请求内容
def _bare_backend(prepared, tmp_path):
    cfg, project, _ = prepared
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(tmp_path / "GSV")}})
    return get_backend("gptsovits", gcfg, wf.open_project(gcfg, project.voice, must_exist=True))


def test_single_request_payload_is_unchanged(prepared, tmp_path):
    """单独生成的请求和 P4 以前 synthesize 发的一模一样（字段、类型、数值）。"""
    b = _bare_backend(prepared, tmp_path)
    ref = tmp_path / "ref.wav"
    req = SynthRequest(text="你好。", lang="zh", ref_audio=ref, ref_text="参考", ref_lang="zh",
                       aux_refs=[tmp_path / "a.wav"], seed=7, speed=0.9)
    want = {
        "text": "你好。", "text_lang": "zh", "ref_audio_path": str(ref.resolve()),
        "aux_ref_audio_paths": [str((tmp_path / "a.wav").resolve())], "prompt_text": "参考", "prompt_lang": "zh",
        "top_k": 15, "top_p": 1.0, "temperature": 1.0, "text_split_method": "cut0", "batch_size": 1,
        "speed_factor": 0.9, "fragment_interval": 0.3, "seed": 7, "media_type": "wav", "streaming_mode": False,
        "parallel_infer": True, "repetition_penalty": 1.35, "sample_steps": 32, "super_sampling": False,
    }
    got = b._payload(req)
    assert got == want and json.dumps(got, sort_keys=True) == json.dumps(want, sort_keys=True)
    assert [type(got[k]) for k in want] == [type(want[k]) for k in want]
    # 语速不合理时按 1.0，超出范围时限制在 0.25~4.0（和以前一样）
    assert b._payload(SynthRequest("x", "en", ref, "r", "en", speed=float("nan")))["speed_factor"] == 1.0
    assert b._payload(SynthRequest("x", "en", ref, "r", "en", speed=9))["speed_factor"] == 4.0
    many = b._payload(req, batch=4, interval=0.5, speed=BATCH_SPEED)
    assert {k for k in want if many[k] != want[k]} == {"batch_size", "fragment_interval", "speed_factor"}
    assert (many["batch_size"], many["fragment_interval"], many["speed_factor"]) == (4, 0.5, 1.0001)


def test_oom_flag_only_looks_at_this_reason():
    """只看这一次的原因：记录里以前的显存不够，不能让别的错误也被当成显存不够。"""
    assert _answer_error("GPT-SoVITS 合成失败：RuntimeError: CUDA out of memory.", "RuntimeError: CUDA out of memory.").oom
    err = _answer_error("GPT-SoVITS 合成失败：ValueError: x\n引擎记录：torch.OutOfMemoryError: CUDA out of memory",
                        "ValueError: x")
    assert type(err) is RuntimeError and not err.oom


def test_default_synthesize_many_loops_with_seed_steps(tmp_path):
    """通用做法：一个一个生成，第 k 个用种子 seed + k × 104729，编号 0..n-1。"""
    class Rec(Backend):
        name = "rec"

        def __init__(self):
            self.seeds = []

        def synthesize(self, req, out_path):
            self.seeds.append(req.seed)
            Path(out_path).write_bytes(b"x")
            return Path(out_path)

    b = Rec()
    out = b.synthesize_many(SynthRequest("你好。", "zh", tmp_path / "r.wav", "r", "zh", seed=11), 3, tmp_path / "o")
    assert [k for _, k in out] == [0, 1, 2] and all(p.exists() for p, _ in out)
    assert len({p for p, _ in out}) == 3
    assert b.seeds == [11, 11 + SEED_STEP, 11 + 2 * SEED_STEP] and SEED_STEP == 104729
    assert Backend.supports_batch is False and GPTSoVITSBackend.supports_batch is True
    again = b.synthesize_many(SynthRequest("你好。", "zh", tmp_path / "r.wav", "r", "zh", seed=11), 1, tmp_path / "o")
    assert again[0][0] not in {p for p, _ in out}  # 同一个文件夹里再要一次，不会覆盖上次的文件


# ---------------------------------------------------------------------------- 真实的 api_v2.py
@pytest.fixture
def quick(monkeypatch):
    # 和 test_gsv_real_api.py 一样：不写 users.pth、不读真显卡；让推理服务的 Python 找得到当前环境装的包
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    import sysconfig

    paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(p for p in dict.fromkeys(paths) if p))
    for k in ("FAKE_GSV_MAX_BATCH", "FAKE_GSV_SPEED_TRICK_BROKEN", "FAKE_GSV_INNER_ZERO"):
        monkeypatch.delenv(k, raising=False)


def _port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _runs(root, real=True):
    f = root / ("_real_api_calls.jsonl" if real else "_fake_api_calls.jsonl")
    if not f.exists():
        return []
    return [json.loads(x)["req"] for x in f.read_text(encoding="utf-8").splitlines()
            if x.strip() and json.loads(x)["kind"] == "run"]


def _backend(prepared, tmp_path, api_src):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=api_src)
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    r = p2.load_references()[0]
    return b, root, (p2.abspath(r["path"]), r["text"], r.get("lang", "zh"))


def _req(ref, text=TEXT, speed=1.0, seed=7):
    return SynthRequest(text=text, lang="zh", ref_audio=ref[0], ref_text=ref[1], ref_lang=ref[2], speed=speed, seed=seed)


def _peak_hz(x, sr):
    x = np.asarray(x[:sr], dtype=np.float64)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    return float(np.argmax(spec) * sr / len(x))


@APIS
def test_four_candidates_in_one_real_request(prepared, tmp_path, quick, vt_log, api_src):
    b, root, ref = _backend(prepared, tmp_path, api_src)
    try:
        b.start()
        out = b.synthesize_many(_req(ref), 4, tmp_path / "out")
        assert b.batch_stats["speed_trick"] is True  # 自检：1.0 和 1.0001 一样、同时生成 2 个能切开
        runs = _runs(root)
        big = [r for r in runs if r["batch_size"] == 4]
        assert len(big) == 1
        r4 = big[0]
        assert r4["speed_factor"] == 1.0001 and r4["fragment_interval"] == 0.5 and r4["text_split_method"] == "cut0"
        assert r4["text"].split("\n") == ["。" + TEXT] * 4 and r4["seed"] == 7 and r4["text_lang"] == "zh"
        # 自检用的请求：同一个种子 1.0 和 1.0001 各一次，再同时生成 2 个
        checks = [(r["batch_size"], r["speed_factor"]) for r in runs if r is not r4]
        assert checks == [(1, 1.0), (1, 1.0001), (2, 1.0001)]
        assert [k for _, k in out] == [0, 1, 2, 3]
        wavs = []
        for path, _k in out:
            x, sr = sf.read(str(path), dtype="int16")
            assert sr == 32000 and sf.info(str(path)).subtype == "PCM_16"
            pad = int(round(BATCH_PAD * sr))
            assert not x[-pad:].any() and x[:-pad].any()
            wavs.append(x)
        assert all(not np.array_equal(wavs[i], wavs[j]) for i in range(4) for j in range(i + 1, 4))
        # 第 k 个就是第 k 行：模拟的引擎每行一个音高（150 + 10 × ((7 + k) % 7) Hz）
        assert [round(_peak_hz(w, 32000) / 10) * 10 for w in wavs] == [150, 160, 170, 180]
        st = b.batch_stats
        assert st["requests"] == 1 and st["pieces"] == 4 and st["by_batch"]["4"]["pieces"] == 4
        assert st["oom_backoffs"] == 0 and st["split_fallbacks"] == 0
        assert b.last_many == {"mode": "batch", "batch": 4, "seed": 7, "speed": 1.0001}
        # 自检每次启动引擎只做一次；语速不是 1.0 时照原样发
        out2 = b.synthesize_many(_req(ref, speed=0.9, seed=8), 3, tmp_path / "out")
        runs2 = _runs(root)[len(runs):]
        assert [(r["batch_size"], r["speed_factor"]) for r in runs2] == [(3, 0.9)] and len(out2) == 3
        assert len({p for p, _ in out + out2}) == 7  # 同一个文件夹，文件不会互相覆盖
        assert any("自检通过" in m for m in vt_log.messages())
        # 很短的句子（会被引擎合在一起读）：一个一个生成，也不用自检
        n_before = len(_runs(root))
        short = b.synthesize_many(_req(ref, text="好的。", seed=3), 2, tmp_path / "out")
        rs = _runs(root)[n_before:]
        assert [(r["batch_size"], r["seed"], r["text"]) for r in rs] == [(1, 3, "好的。"), (1, 3 + SEED_STEP, "好的。")]
        assert len(short) == 2 and b.last_many["mode"] == "single"
        assert list(b.batch_stats["single_reasons"]) == ["这句话不能同时生成（很短的句子会被引擎合在一起读、有换行或者太长）"]
        # 重新启动引擎：自检要重新做
        b.stop()
        b.start()
        assert b._speed_trick is None and b.batch_stats["speed_trick"] is None
    finally:
        b.stop()


@APIS
def test_oom_halves_the_batch(prepared, tmp_path, quick, monkeypatch, vt_log, api_src):
    monkeypatch.setenv("FAKE_GSV_MAX_BATCH", "2")  # 同时生成 3 个以上就显存不够
    b, root, ref = _backend(prepared, tmp_path, api_src)
    try:
        b.start()
        out = b.synthesize_many(_req(ref), 4, tmp_path / "out")
        assert len(out) == 2 and [k for _, k in out] == [0, 1]
        assert b.batch_stats["oom_backoffs"] == 1 and b._max_batch == 2 and b.batch_stats["max_batch"] == 2
        big = [r["batch_size"] for r in _runs(root) if r["batch_size"] > 1]
        assert big == [2, 4, 2]  # 自检的 2 个、显存不够的 4 个、减半以后的 2 个
        assert "显存不够：每次同时生成的数量从 4 减到 2，接着试（不会停下）" in vt_log.messages()
        # 记住了：以后最多同时生成 2 个
        n = len(_runs(root))
        assert len(b.synthesize_many(_req(ref, seed=9), 4, tmp_path / "out")) == 2
        assert [r["batch_size"] for r in _runs(root)[n:]] == [2]
    finally:
        b.stop()


@APIS
def test_oom_at_one_releases_gpu_then_fatal(prepared, tmp_path, quick, monkeypatch, vt_log, api_src):
    from voicetwin.errors import explain, is_fatal

    monkeypatch.setenv("FAKE_GSV_MAX_BATCH", "0")  # 一个也生成不了
    b, root, ref = _backend(prepared, tmp_path, api_src)
    calls = []
    b.release_gpu_callback = lambda: calls.append(1) or True  # 和 CERChecker.release_gpu 一样：卸掉了模型回 True
    try:
        b.start()
        with pytest.raises(RuntimeError) as ei:
            b.synthesize_many(_req(ref, speed=0.9), 4, tmp_path / "out")
        assert calls == [1]  # 让出显存只叫一次，再试一次还不行就报错
        assert str(ei.value).startswith("GPT-SoVITS 合成失败：RuntimeError: CUDA out of memory")
        assert explain(ei.value).key == "gpu_oom" and is_fatal(ei.value)
        assert [r["batch_size"] for r in _runs(root)] == [4, 2, 1, 1]
        st = b.batch_stats
        assert st["oom_backoffs"] == 2 and st["gpu_releases"] == 1 and b._max_batch == 1
        msgs = vt_log.messages()
        assert "显存不够：每次同时生成的数量从 2 减到 1，接着试（不会停下）" in msgs
        assert "显存不够：一次只生成一个也不够。已经让出了一部分显存，再试一次……" in msgs
        assert not list((tmp_path / "out").glob("*.wav"))
    finally:
        b.stop()


def test_oom_in_self_check_switches_to_singles_once(prepared, tmp_path, quick, monkeypatch, vt_log):
    """自检里同时生成 2 个就显存不够：记下「一次一个」，以后不再每句都自检。"""
    monkeypatch.setenv("FAKE_GSV_MAX_BATCH", "1")
    b, root, ref = _backend(prepared, tmp_path, REAL_API_V2)
    try:
        b.start()
        out = b.synthesize_many(_req(ref), 3, tmp_path / "out")
        assert len(out) == 3 and b._max_batch == 1 and b._speed_trick is None
        assert b.batch_stats["speed_trick"] is None and "自检时出错" in b.batch_stats["speed_trick_reason"]
        runs = [(r["batch_size"], r["speed_factor"]) for r in _runs(root)]
        assert runs == [(1, 1.0), (1, 1.0001), (2, 1.0001)] + [(1, 1.0)] * 3  # 出错后不换种子再试
        msgs = vt_log.messages()
        assert "显存不够：同时生成 2 个也不够，改成一次生成一个（不会停下）" in msgs
        assert any(m.startswith("「语速 1.0001」自检没做成") for m in msgs)
        # 记下的原因是真正的原因（显存不够），不是「自检没通过」（自检根本没做完）
        assert b.batch_stats["single_reasons"] == {"显存不够，已经改成一次生成一个": 1}
        n = len(_runs(root))
        assert len(b.synthesize_many(_req(ref, seed=2), 2, tmp_path / "out")) == 2
        assert [r["batch_size"] for r in _runs(root)[n:]] == [1, 1]  # 没有再自检
        assert b.batch_stats["single_reasons"] == {"显存不够，已经改成一次生成一个": 2}
    finally:
        b.stop()


@APIS
def test_broken_speed_trick_only_affects_speed_one(prepared, tmp_path, quick, monkeypatch, vt_log, api_src):
    monkeypatch.setenv("FAKE_GSV_SPEED_TRICK_BROKEN", "1")  # 语速不是 1.0 时长 5%：1.0001 和 1.0 不一样
    b, root, ref = _backend(prepared, tmp_path, api_src)
    try:
        b.start()
        out = b.synthesize_many(_req(ref, seed=5), 3, tmp_path / "out")
        assert len(out) == 3
        st = b.batch_stats
        assert st["speed_trick"] is False and "长度差了" in st["speed_trick_reason"] and b._speed_trick is False
        runs = _runs(root)
        checks, singles = runs[:4], runs[4:]
        assert [(r["batch_size"], r["speed_factor"]) for r in checks] == [(1, 1.0), (1, 1.0001)] * 2  # 2 个种子
        assert [(r["batch_size"], r["speed_factor"], r["seed"], r["fragment_interval"]) for r in singles] == [
            (1, 1.0, 5 + k * SEED_STEP, 0.3) for k in range(3)]
        assert any(m.startswith("自检没通过（长度差了") for m in vt_log.messages())
        assert st["single_reasons"] == {"「语速 1.0001」自检没通过（语速正好 1.0 的句子）": 1}
        # 语速不是 1.0：照样同时生成（不用 1.0001 的办法）
        n = len(runs)
        out2 = b.synthesize_many(_req(ref, speed=0.9), 3, tmp_path / "out")
        assert [(r["batch_size"], r["speed_factor"]) for r in _runs(root)[n:]] == [(3, 0.9)] and len(out2) == 3
        # 没通过的结果记住了（这次启动不再自检）
        n = len(_runs(root))
        b.synthesize_many(_req(ref), 2, tmp_path / "out")
        assert [r["batch_size"] for r in _runs(root)[n:]] == [1, 1]
    finally:
        b.stop()


@APIS
def test_split_failure_falls_back_to_singles(prepared, tmp_path, quick, monkeypatch, vt_log, api_src):
    monkeypatch.setenv("FAKE_GSV_INNER_ZERO", "1")  # 每段中间有 0.4 秒的数字静音：分不开
    b, root, ref = _backend(prepared, tmp_path, api_src)
    try:
        b.start()
        out = b.synthesize_many(_req(ref, speed=0.9, seed=4), 3, tmp_path / "out")
        assert len(out) == 3 and [k for _, k in out] == [0, 1, 2]
        st = b.batch_stats
        assert st["split_fallbacks"] == 1 and "找到 6 段长的静音，应该是 3 段" == st["split_reason"]
        assert st["requests"] == 4 and st["pieces"] == 3 and st["by_batch"]["3"]["pieces"] == 0
        runs = _runs(root)
        assert [(r["batch_size"], r["seed"]) for r in runs] == [(3, 4)] + [(1, 4 + k * SEED_STEP) for k in range(3)]
        assert "这次没能把同时生成的几个版本分开（原因：找到 6 段长的静音，应该是 3 段），改成一个一个生成" in vt_log.messages()
        assert b.last_many == {"mode": "single", "seeds": [4 + k * SEED_STEP for k in range(3)], "speed": 0.9}
    finally:
        b.stop()


def test_v4_model_uses_single_requests(prepared, tmp_path, quick):
    """V3 / V4 模型（从模型文件读出来的版本）一个一个生成。"""
    b, root, ref = _backend(prepared, tmp_path, REAL_API_V2)
    v4 = tmp_path / "v4_e8_s100.pth"
    v4.write_bytes(b"04" + b"x" * 4000)  # 模型文件开头的版本标记 04 = v4 LoRA
    try:
        b.start()
        b.use_checkpoint({"id": "v4", "gpt": str(root / "GPT_SoVITS/pretrained_models/s1v3.ckpt"), "sovits": str(v4)})
        assert b._batch_version() == "v4"
        out = b.synthesize_many(_req(ref, speed=0.9), 2, tmp_path / "out")
        assert len(out) == 2 and [r["batch_size"] for r in _runs(root)] == [1, 1]
        assert b.batch_stats["single_reasons"] == {"v4 模型只能一个一个生成": 1}
    finally:
        b.stop()


def test_simple_fake_api_batches_and_halves(prepared, tmp_path, quick, monkeypatch):
    """模拟版的 api（tests/fake_gptsovits.API_V2）也认同时生成和显存不够。"""
    monkeypatch.setenv("FAKE_GSV_MAX_BATCH", "2")
    b, root, ref = _backend(prepared, tmp_path, False)
    try:
        b.start()
        out = b.synthesize_many(_req(ref), 4, tmp_path / "out")
        assert len(out) == 2 and b.batch_stats["oom_backoffs"] == 1 and b.batch_stats["speed_trick"] is True
        runs = _runs(root, real=False)
        assert [(r["batch_size"], r["speed_factor"]) for r in runs] == [(1, 1.0), (1, 1.0001), (2, 1.0001),
                                                                         (4, 1.0001), (2, 1.0001)]
        a, _ = sf.read(str(out[0][0]), dtype="int16")
        c, _ = sf.read(str(out[1][0]), dtype="int16")
        assert not np.array_equal(a, c)
    finally:
        b.stop()


# ---------------------------------------------------------------------------- 不开引擎：记下的原因、日志、文件名都是真的
_OOM = "torch.OutOfMemoryError: CUDA out of memory."


def _tone(sec, sr=32000, hz=200.0):
    x = (np.sin(2 * np.pi * hz * np.arange(int(sec * sr)) / sr) * 8000).astype(np.int16)
    x[x == 0] = 1
    return x


def _offline(prepared, tmp_path, answer):
    """不开推理服务的 GPT-SoVITS 后端：请求交给 answer(payload) 回答（回 WAV 字节或抛出错误），单独生成写一段声音。"""
    b = _bare_backend(prepared, tmp_path)
    b._alive = lambda: True
    b._batch_version = lambda: "v2ProPlus"
    b._tts_answer = answer
    seeds = []

    def synth(req, out_path):
        seeds.append(req.seed)
        Path(out_path).write_bytes(_wav(_tone(1.0), 32000))
        return Path(out_path)

    b.synthesize = synth
    return b, seeds


def _bare_req(tmp_path, speed=1.0, seed=7):
    return _req((tmp_path / "ref.wav", "参考", "zh"), speed=speed, seed=seed)


def test_single_reason_tells_what_really_happened_in_the_self_check(prepared, tmp_path, vt_log):
    """自检没做完（出错了）时，记下的原因不能写成「自检没通过」：显存不够就写显存不够，别的错误写「没做成」和原因。"""
    tone = _wav(_tone(2.0), 32000)

    def oom_at_two(p):  # 一次一个没问题，同时生成 2 个显存就不够
        if p["batch_size"] > 1:
            raise _answer_error("GPT-SoVITS 合成失败：" + _OOM, _OOM)
        return tone

    b, seeds = _offline(prepared, tmp_path, oom_at_two)
    assert len(b.synthesize_many(_bare_req(tmp_path), 3, tmp_path / "o")) == 3 and len(seeds) == 3
    assert b._max_batch == 1 and b._speed_trick is None and b.batch_stats["speed_trick"] is None
    assert b.batch_stats["single_reasons"] == {"显存不够，已经改成一次生成一个": 1}

    def broken(p):  # 语速 1.0001 的请求出了别的错
        if p["speed_factor"] != 1.0:
            raise _answer_error("GPT-SoVITS 合成失败：ValueError: boom", "ValueError: boom")
        return tone

    b, seeds = _offline(prepared, tmp_path, broken)
    assert len(b.synthesize_many(_bare_req(tmp_path), 2, tmp_path / "o")) == 2
    assert b._speed_trick is None and b._max_batch is None
    assert b.batch_stats["single_reasons"] == {
        "「语速 1.0001」自检没做成（自检时出错：GPT-SoVITS 合成失败：ValueError: boom）": 1}

    def longer(p):  # 自检真的做完了、没通过（1.0001 长了 5%）
        return _wav(_tone(2.0 if p["speed_factor"] == 1.0 else 2.1), 32000)

    b, seeds = _offline(prepared, tmp_path, longer)
    assert len(b.synthesize_many(_bare_req(tmp_path), 2, tmp_path / "o")) == 2 and b._speed_trick is False
    assert b.batch_stats["single_reasons"] == {"「语速 1.0001」自检没通过（语速正好 1.0 的句子）": 1}


def test_gpu_release_is_counted_only_when_something_was_released(prepared, tmp_path, vt_log):
    """一次一个也显存不够：只有回调真的让出了显存才记 gpu_releases、日志才说让出了；不管让没让出，都再试一次。"""
    from voicetwin.eval import metrics

    b = _bare_backend(prepared, tmp_path)
    b._alive = lambda: True
    tries = []

    def synth(req, out_path):
        tries.append(req.seed)
        raise _answer_error("GPT-SoVITS 合成失败：" + _OOM, _OOM)

    def boom():
        raise RuntimeError("driver")

    b.synthesize = synth
    head = "显存不够：一次只生成一个也不够。"
    cases = [  # (回调, 到这里一共记了几次让出显存, 日志)
        (None, 0, head + "再试一次……"),
        (lambda: True, 1, head + "已经让出了一部分显存，再试一次……"),
        (lambda: False, 1, head + "没有能让出的显存，再试一次……"),
        (metrics.CERChecker("auto").release_gpu, 1, head + "没有能让出的显存，再试一次……"),  # 识别模型还没加载过
        (boom, 1, head + "没能让出显存（driver），再试一次……"),
    ]
    for cb, releases, msg in cases:
        b.release_gpu_callback = cb
        tries.clear()
        vt_log.records.clear()
        with pytest.raises(RuntimeError) as ei:
            b.synthesize_many(_bare_req(tmp_path, speed=0.9), 1, tmp_path / "o")
        assert getattr(ei.value, "oom", False) and len(tries) == 2  # 再试一次，还不行就照常报「显存不够」
        assert b.batch_stats["gpu_releases"] == releases, msg
        assert msg in vt_log.messages()
        if cb is None:
            assert not any("让出" in m for m in vt_log.messages())


def test_self_check_pass_log_only_says_what_was_measured(prepared, tmp_path, vt_log):
    """自检通过的日志只写量出来的（长度差、波形相关系数、2 个版本能分开），不说「一样」、不说没查过的「单独解码」。"""
    rng = np.random.default_rng(5)
    sr = 32000
    a = _tone(3.0)
    t = np.arange(int(len(a) * 1.0089))  # 长 0.89%、加了一点噪声：相关系数大约 0.992
    b_ = (np.sin(2 * np.pi * 200 * t / sr) * 8000 + rng.standard_normal(len(t)) * 720).astype(np.int16)

    def answer(p):
        if p["batch_size"] == 2:
            return _wav(_join([_frag(rng, 2, sr), _frag(rng, 2, sr)], int(0.5 * sr)), sr)
        return _wav(a if p["speed_factor"] == 1.0 else b_, sr)

    b, _seeds = _offline(prepared, tmp_path, answer)
    assert b._speed_trick_ok(_bare_req(tmp_path)) is True and b.batch_stats["speed_trick"] is True
    r = float(np.corrcoef(a.astype(np.float64), b_[:len(a)].astype(np.float64))[0, 1])
    assert 0.99 <= r < 0.995
    msg = [x for x in vt_log.messages() if x.startswith("自检通过")]
    assert msg == ["自检通过：语速写成 1.0001 和 1.0 生成的声音几乎一样（长度差 0.88%、波形相关系数 "
                   f"{math.floor(r * 1000) / 1000:.3f}），同时生成的 2 个版本也能按数字静音分开——可以同时生成好几个版本"]
    assert "单独解码" not in msg[0] and "和 1.0 一样" not in msg[0]


_TWO_RUNS = r'''
import io, sys
from pathlib import Path

import numpy as np
import soundfile as sf

from voicetwin.backends.base import Backend, SynthRequest
from voicetwin.backends.gptsovits import GPTSoVITSBackend, _new_batch_stats

out, run = Path(sys.argv[1]), sys.argv[2]


def write(req, path):
    Path(path).write_text(run + ":" + str(req.seed), encoding="utf-8")
    return Path(path)


class Rec(Backend):
    name = "rec"

    def __init__(self):
        pass

    def synthesize(self, req, out_path):
        return write(req, out_path)


def answer(payload):
    sr, k = 32000, payload["text"].count("\n") + 1
    tone = (np.sin(np.arange(sr) / 5.0) * 8000).astype(np.int16)
    tone[tone == 0] = 1
    x = np.concatenate([np.concatenate([tone + int(run), np.zeros(sr // 2, np.int16)]) for _ in range(k)])
    buf = io.BytesIO()
    sf.write(buf, x, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


g = GPTSoVITSBackend.__new__(GPTSoVITSBackend)
g.batch_stats, g.last_many, g._max_batch, g.release_gpu_callback = _new_batch_stats(), {}, None, None
g._alive = lambda: True
g._single_reason = lambda req, n: ""
g._payload = lambda req, **kw: {"text_lang": "zh"}
g._tts_answer = answer
g.synthesize = write
req = SynthRequest("我们今天学习关系代词。", "zh", out / "r.wav", "r", "zh", seed=1)
Rec().synthesize_many(req, 2, out)
g._many_singles(req, 2, out)
g.synthesize_many(req, 2, out)
assert g.last_many["mode"] == "batch", g.last_many
'''


def test_many_file_names_do_not_repeat_across_runs(tmp_path):
    """两次运行程序（两个进程）往同一个文件夹写：通用的一个一个生成、GPT-SoVITS 一个一个生成、同时生成，都不覆盖上次的文件。"""
    import subprocess

    out = tmp_path / "same"
    out.mkdir()
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in (str(ROOT), os.environ.get("PYTHONPATH", "")) if p))
    seen = {}
    for run in ("1", "2"):
        res = subprocess.run([sys.executable, "-c", _TWO_RUNS, str(out), run], env=env, capture_output=True,
                             text=True, timeout=120)
        assert res.returncode == 0, res.stderr[-2000:]
        assert {n: (out / n).read_bytes() for n in seen} == seen  # 上次写的文件一个字节都没变
        new = {p.name: p.read_bytes() for p in out.glob("*.wav") if p.name not in seen}
        assert len(new) == 6, sorted(new)  # 每次 2 + 2 + 2 个新文件
        seen.update(new)
    assert len(list(out.glob("*.wav"))) == 12


# ---------------------------------------------------------------------------- 识别校验模型让出显卡
def test_cer_checker_release_gpu(monkeypatch):
    from voicetwin.eval import metrics

    c = metrics.CERChecker("auto", vram_tier="mid")
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    assert c.release_gpu() is False and c.device == "cpu"  # 什么都没加载：没东西可卸，也不报错

    c = metrics.CERChecker("auto", vram_tier="mid")
    c._model, c._para = object(), object()
    emptied = []
    fake_torch = types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda: True,
                                                                   empty_cache=lambda: emptied.append(1)))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    assert c.release_gpu() is True
    assert c._model is None and c._para is None and c.device == "cpu" and emptied == [1]

    # 以后再加载：在处理器上，Whisper 用 int8
    seen = {}

    class FakeTranscriber:
        def __init__(self, cfg):
            seen.update(cfg)

        def _load(self):
            pass

    import voicetwin.data.asr as asr

    monkeypatch.setattr(asr, "Transcriber", FakeTranscriber)
    assert c._load() and seen["device"] == "cpu" and seen["compute_type"] == "int8"

    # 清显存缓存出错也不抛出来
    def boom():
        raise RuntimeError("driver")

    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(
        cuda=types.SimpleNamespace(is_available=lambda: True, empty_cache=boom)))
    c._model = object()
    assert c.release_gpu() is True
