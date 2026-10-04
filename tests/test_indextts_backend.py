"""v18.7：IndexTTS25 是唯一的引擎。接口照着官方 indextts/infer_v2_5.py（commit d9e41aa）：
用 tests/fake_indextts 里参数签名一模一样的假 IndexTTS2 真的启动 worker 子进程，检查传过去的每一个参数。"""

import json
import shutil
import sys
import wave
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from voicetwin.backends.base import SynthRequest
from voicetwin.backends.indextts import (AUX_DIRS, AUX_FILES, MODEL_FILES_25, IndexTTSBackend, SAMPLING_DEFAULTS,
                                         label_for, send_lang)
from voicetwin.project import Project

from conftest import make_cfg

FAKE = Path(__file__).with_name("fake_indextts")


def _root(tmp_path: Path, complete: bool = True) -> Path:
    root = tmp_path / "index-tts"
    shutil.copytree(FAKE, root)
    md = root / "checkpoints"
    md.mkdir()
    if complete:
        for f in MODEL_FILES_25 + AUX_FILES:
            (md / f).parent.mkdir(parents=True, exist_ok=True)
            (md / f).write_text("x", encoding="utf-8")
        (md / "multilingual_zh_ja_yue_char_del.tiktoken").write_text("x", encoding="utf-8")
        for d in AUX_DIRS:
            (md / d).mkdir(parents=True, exist_ok=True)
            (md / d / "model.safetensors").write_text("x", encoding="utf-8")
    return root


def _project(cfg):
    pr = Project(cfg, "测试声音")
    pr.ensure()
    return pr


def _backend(tmp_path: Path, root: Path, **bcfg) -> IndexTTSBackend:
    cfg = make_cfg(tmp_path / "ws", backend="indextts",
                   backends={"indextts": {"root": str(root), "python": sys.executable, **bcfg}})
    return IndexTTSBackend(cfg, _project(cfg))


def _ref(tmp_path: Path) -> Path:
    p = tmp_path / "ref.wav"
    sf.write(str(p), (0.1 * np.sin(np.arange(16000 * 2) / 8)).astype(np.float32), 16000)
    return p


def _req(ref: Path, text: str, lang: str = "zh", **kw) -> SynthRequest:
    return SynthRequest(text=text, lang=lang, ref_audio=ref, ref_text="参考录音的文字", ref_lang="zh", **kw)


def _log(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_label_and_lang():
    assert label_for("2.5") == "IndexTTS25" and label_for("2") == "IndexTTS2"
    # 有一个汉字就是 ZH（中英夹在一起也是 ZH，不然中文会被当英文读）；没有汉字、标成英文才是 EN
    assert send_lang("这个句子I have a sister.", "en") == "ZH"
    assert send_lang("I have a sister who is a doctor.", "en") == "EN"
    assert send_lang("I have a sister.", "zh") == "ZH"


def test_payload_follows_the_official_api(tmp_path):
    be = _backend(tmp_path, _root(tmp_path))
    ref = _ref(tmp_path)
    p = be.build_payload(_req(ref, "例如这个句子who is a doctor。", lang="en"), tmp_path / "o.wav")
    assert p["lang"] == "ZH" and p["ref_audio"] == str(ref.resolve())
    assert {k: p["params"][k] for k in SAMPLING_DEFAULTS} == SAMPLING_DEFAULTS  # 没指定就用 IndexTTS 自己的默认
    assert "duration_factor" not in p["params"] and "emo_audio" not in p["params"]  # 同一段录音当情绪参考没有作用
    # 语速：duration_factor = 1/语速，限制在官方的 0.5~2.0
    assert be.build_payload(_req(ref, "好", speed=1.25), tmp_path / "o.wav")["params"]["duration_factor"] == 0.8
    assert be.build_payload(_req(ref, "好", speed=3.0), tmp_path / "o.wav")["params"]["duration_factor"] == 0.5
    assert be.build_payload(_req(ref, "好", speed=0.2), tmp_path / "o.wav")["params"]["duration_factor"] == 2.0
    q = be.build_payload(_req(ref, "好", temperature=0.6, top_k=20, top_p=0.9), tmp_path / "o.wav")["params"]
    assert (q["temperature"], q["top_k"], q["top_p"]) == (0.6, 20, 0.9)


def test_check_says_what_is_missing(tmp_path):
    be = _backend(tmp_path, tmp_path / "没有")
    probs = be.check()
    assert len(probs) == 1 and "找不到 IndexTTS 程序" in probs[0] and "install_windows.bat" in probs[0]
    root = _root(tmp_path, complete=False)
    probs = _backend(tmp_path, root).check()
    assert any("gpt.pth" in x and "模型没下载完整" in x for x in probs)
    assert any("hf_cache/bigvgan/bigvgan_generator.pt" in x and "辅助模型" in x for x in probs)
    assert _backend(tmp_path / "b", _root(tmp_path / "b")).check() == []


def test_check_needs_its_own_python(tmp_path):
    root = _root(tmp_path)
    cfg = make_cfg(tmp_path / "ws", backend="indextts", backends={"indextts": {"root": str(root)}})
    be = IndexTTSBackend(cfg, _project(cfg))
    assert any(".venv" in x and "Python 环境" in x for x in be.check())


def test_worker_env_prefers_modelscope(tmp_path, monkeypatch):
    be = _backend(tmp_path, _root(tmp_path))
    monkeypatch.delenv("USE_MODELSCOPE", raising=False)
    monkeypatch.delenv("HF_ENDPOINT", raising=False)
    env = be.worker_env()
    assert env["USE_MODELSCOPE"] == "true" and env["HF_ENDPOINT"] == "https://hf-mirror.com"
    monkeypatch.setenv("HF_ENDPOINT", "https://example.org")
    assert be.worker_env()["HF_ENDPOINT"] == "https://example.org"  # 帮忙的人自己设过的不改


def test_worker_end_to_end_with_fake_indextts(tmp_path, monkeypatch):
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FAKE_INDEXTTS_LOG", str(log))
    monkeypatch.delenv("FAKE_TORCH_CUDA", raising=False)
    be = _backend(tmp_path, _root(tmp_path))
    ref = _ref(tmp_path)
    try:
        out = be.synthesize(_req(ref, "大家好，我们今天学习定语从句。", speed=0.8), tmp_path / "a.wav")
        out2 = be.synthesize(_req(ref, "I have a sister who is a doctor.", lang="en", seed=7), tmp_path / "b.wav")
    finally:
        be.stop()
    with wave.open(str(out)) as w:
        assert w.getframerate() == 22050 and w.getnframes() > 0
    assert out2.is_file()
    calls = _log(log)
    init = calls[0]
    assert init["kind"] == "init" and init["use_cuda_kernel"] is False and init["use_deepspeed"] is False
    assert init["use_qwen_emo"] is False and init["use_bf16"] is False  # 没有显卡：不用 bf16
    a, b = [c for c in calls if c["kind"] == "infer"]
    assert a["lang"] == "ZH" and a["duration_factor"] == 1.25 and a["emo_audio_prompt"] is None
    assert a["generation_kwargs"] == SAMPLING_DEFAULTS
    assert b["lang"] == "EN" and b["duration_factor"] == 1.0


def test_low_vram_card_speaks_whole_sentence_and_splits_only_on_oom(tmp_path, monkeypatch):
    """8 GB 显卡：官方会把超过 40 个字的句子在标点处切开、中间插 200 毫秒静音。VoiceTwin 自己按句子切、按老师的习惯放停顿，
    所以默认一句话一口气生成；真的显存不够时这一句才用官方的切法再来一次。"""
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FAKE_INDEXTTS_LOG", str(log))
    monkeypatch.setenv("FAKE_TORCH_CUDA", "1")
    monkeypatch.setenv("FAKE_TORCH_VRAM_GB", "8")
    monkeypatch.setenv("FAKE_INDEXTTS_OOM_ONCE", "1")
    be = _backend(tmp_path, _root(tmp_path), interval_silence=150)
    ref = _ref(tmp_path)
    long_text = "所以说在这种情况下，我们只能使用that来引导后面的定语从句，这是非常重要的一个知识点。"
    try:
        be.synthesize(_req(ref, long_text), tmp_path / "a.wav")
        info = dict(be.client.ready_info)
    finally:
        be.stop()
    assert info.get("low_vram") is True and info.get("bf16") is True and info.get("vram_gb") == 8.0
    calls = [c for c in _log(log) if c["kind"] == "infer"]
    assert [c["low_vram"] for c in calls] == [False, True]  # 先一口气生成，显存不够才切
    assert calls[1]["interval_silence"] == 150


def test_worker_reports_missing_output(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_INDEXTTS_NONE", "1")
    monkeypatch.delenv("FAKE_TORCH_CUDA", raising=False)
    be = _backend(tmp_path, _root(tmp_path))
    try:
        with pytest.raises(Exception) as ei:
            be.synthesize(_req(_ref(tmp_path), "……"), tmp_path / "a.wav")
    finally:
        be.stop()
    assert "没有写出音频文件" in str(ei.value)
