import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voicetwin.backends.workers.dummy_worker import synth_speech  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.data.subtitles import Cue, write_srt  # noqa: E402

SENTENCES = [
    "今天我们来学习Python里面的列表推导式。",
    "它可以让代码变得更加简洁，也更容易阅读。",
    "首先我们看一个最简单的例子。",
    "大家想一想，这段代码输出的结果是什么？",
    "Next, let's look at a slightly more complex example.",
    "We can add a condition at the end of the expression.",
    "好，这就是今天的全部内容，我们下节课再见！",
    "接下来我们讲字典推导式，它和列表推导式非常相似。",
    "区别在于我们需要同时给出键和值。",
    "This makes it very convenient to build lookup tables.",
]


def make_lecture(path: Path, repeats: int = 3, sr: int = 44100, f0: float = 150.0, with_srt: bool = True, seed: int = 1):
    rng = np.random.default_rng(seed)
    parts = [np.zeros(int(0.6 * sr))]
    cues = []
    t = 0.6
    for rep in range(repeats):
        for i, s in enumerate(SENTENCES):
            w = synth_speech(s, sr=sr, seed=rep * 100 + i + seed * 1000, f0=f0)
            parts.append(w)
            cues.append(Cue(t + 0.05, t + len(w) / sr - 0.05, s))
            t += len(w) / sr
            gap = rng.uniform(0.4, 1.0)
            parts.append(np.zeros(int(gap * sr)))
            t += gap
    wav = np.concatenate(parts).astype(np.float32)
    wav += rng.normal(0, 0.0015, len(wav)).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), wav, sr)
    if with_srt:
        write_srt(cues, path.with_suffix(".srt"))
    return path


@pytest.fixture(scope="session")
def lecture_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("lectures")
    make_lecture(d / "第1课.wav")
    return d


@pytest.fixture(autouse=True)
def _no_sv_download(monkeypatch):
    """测试不联网下载声纹模型（要测下载本身的测试自己换回真的 download，并换掉网络请求）。"""
    from voicetwin.eval import sv_models

    monkeypatch.setattr(sv_models, "download", lambda cfg, progress=None, keys=None: [])


def make_cfg(workspace: Path, **extra):
    overrides = {"workspace": str(workspace), "backend": "dummy", "prepare": {"asr": {"engine": "none"}},
                 "speaker_encoder": "mfcc", "similarity": {"model_dir": str(Path(workspace) / "_sv_models")}}
    for k, v in extra.items():
        overrides[k] = dict(overrides[k], **v) if k == "similarity" else v
    return load_config(overrides=overrides, user_config=False)


@pytest.fixture(scope="session")
def prepared(tmp_path_factory, lecture_dir):
    """素材准备 + 风格分析，session 级共享（较慢）。"""
    from voicetwin import workflows as wf

    ws = tmp_path_factory.mktemp("ws")
    cfg = make_cfg(ws)
    summary = wf.run_prepare(cfg, "测试声音", [str(lecture_dir)])
    project = wf.open_project(cfg, "测试声音", must_exist=True)
    return cfg, project, summary
