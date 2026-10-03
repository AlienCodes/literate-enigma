"""Independent repro: does the training log's "其中 N 条是你改过文字的" count val (考试题) sentences and
sentences changed back to exactly the recognized text?

usage: python repro.py <code_root> <work_dir> <scenario>
  code_root: directory that contains the voicetwin package to test (HEAD extract or the working tree)
  scenario:  A = edit one val sentence only + edit a train sentence and change it back (reporter's case)
             B = control: edit one train sentence (really changed) -> must count 1
             C = edit only one val sentence -> trained-edited must be 0
             D = change a train sentence then back only -> must be 0
"""
import logging
import shutil
import sys
from pathlib import Path

code_root, work, scen = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, code_root)

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402

import voicetwin  # noqa: E402
assert str(Path(voicetwin.__file__).resolve()).startswith(str(Path(code_root).resolve())), voicetwin.__file__

from voicetwin.backends.workers.dummy_worker import synth_speech  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.data.subtitles import Cue, write_srt  # noqa: E402
from voicetwin.eval import sv_models  # noqa: E402

sv_models.download = lambda cfg, progress=None, keys=None: []  # no network
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.data.exporters import gptsovits_list_text, train_records  # noqa: E402

SENT = ["今天我们来学习Python里面的列表推导式。", "它可以让代码变得更加简洁，也更容易阅读。", "首先我们看一个最简单的例子。",
        "大家想一想，这段代码输出的结果是什么？", "Next, let's look at a slightly more complex example.",
        "We can add a condition at the end of the expression.", "好，这就是今天的全部内容，我们下节课再见！",
        "接下来我们讲字典推导式，它和列表推导式非常相似。", "区别在于我们需要同时给出键和值。",
        "This makes it very convenient to build lookup tables."]


def make_lecture(path, repeats=3, sr=44100, seed=1):
    rng = np.random.default_rng(seed)
    parts, cues, t = [np.zeros(int(0.6 * sr))], [], 0.6
    for rep in range(repeats):
        for i, s in enumerate(SENT):
            w = synth_speech(s, sr=sr, seed=rep * 100 + i + seed * 1000, f0=150.0)
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
    write_srt(cues, path.with_suffix(".srt"))


if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
make_lecture(work / "lect" / "第1课.wav")
ws = work / "ws"
cfg = load_config(overrides={"workspace": str(ws), "backend": "dummy", "prepare": {"asr": {"engine": "none"}},
                             "speaker_encoder": "mfcc", "similarity": {"model_dir": str(ws / "_sv_models")}},
                  user_config=False)
V = "测试声音"
wf.run_prepare(cfg, V, [str(work / "lect")])
project = wf.open_project(cfg, V, must_exist=True)
recs = project.load_manifest()
val = next(r for r in recs if r.get("keep") and r.get("text") and r.get("split") == "val")
tr = next(r for r in recs if r.get("keep") and r.get("text") and r.get("split", "train") == "train")
print(f"[{scen}] clips={len(recs)} val_id={val['id']} train_id={tr['id']}")

if scen in ("A", "C"):  # teacher fixes a typo in a 考试题 sentence, via the web table (draft -> save row)
    review.set_draft(project, val["id"], text=val["text"].rstrip("。") + "（老师改过）。")
    wf.review_save(cfg, V, ids=[val["id"]])
if scen in ("A", "D"):  # changes a train sentence, saves, then changes it back exactly and saves again
    old = tr["text"]
    review.set_draft(project, tr["id"], text=old + "改")
    wf.review_save(cfg, V, ids=[tr["id"]])
    review.set_draft(project, tr["id"], text=old)
    wf.review_save(cfg, V, ids=[tr["id"]])
if scen == "B":
    review.set_draft(project, tr["id"], text=tr["text"].rstrip("。") + "（老师改过）。")
    wf.review_save(cfg, V, ids=[tr["id"]])

res = wf.review_confirm(cfg, V)
print(f"[{scen}] confirmed={res.get('confirmed')} blocker={wf.training_blocker(project)!r}")

m = {r["id"]: r for r in project.load_manifest()}
for name, rid in (("val", val["id"]), ("train", tr["id"])):
    r = m[rid]
    print(f"[{scen}] {name}: split={r.get('split')} keep={r.get('keep')} text_edited={r.get('text_edited')} "
          f"orig_set={'orig_text' in r} text==orig={r.get('text') == r.get('orig_text')}")

# what actually goes into GPT-SoVITS train.list (same function the backend uses)
trained = train_records(project)
listing = gptsovits_list_text(project, "x", trained)
real_trained_edited = sum(1 for r in trained if r.get("orig_text") is not None and r["orig_text"] != r.get("text"))
print(f"[{scen}] train.list rows={len(trained)} val clip in train.list="
      f"{Path(m[val['id']]['path']).name in listing}; trained rows whose text differs from recognized="
      f"{real_trained_edited}")

lines = []


class H(logging.Handler):
    def emit(self, rec):
        lines.append(rec.getMessage())


logging.getLogger("voicetwin").addHandler(H())
logging.getLogger("voicetwin").setLevel(logging.INFO)
wf._check_material_before_training(project)  # the exact function run_train calls before training
print(f"[{scen}] LOG: " + " | ".join(x for x in lines if x.startswith("这次训练用")))
