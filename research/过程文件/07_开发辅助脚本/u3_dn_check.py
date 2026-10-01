import sys; sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-8")
import numpy as np

from voicetwin.backends.workers.dummy_worker import synth_speech
from voicetwin.synth.engine import denoise_light, trim_edges
from voicetwin.utils.audio import frame_rms_db

sr = 32000
w = synth_speech("大家好，今天我们来学习，一个非常重要的概念。然后，我们看一个例子。", sr=sr, seed=3, noise=0.01)
t = trim_edges(w, sr)
d = denoise_light(t, sr)
print("len", len(w), len(t), None if d is None else len(d))
if d is not None:
    db_t = frame_rms_db(t, sr)
    db_d = frame_rms_db(d, sr)
    q = db_t < np.percentile(db_t, 20)
    print("quiet frames dB before/after", float(np.median(db_t[q])), float(np.median(db_d[q])))
    loud = db_t > np.percentile(db_t, 80)
    print("loud frames dB before/after", float(np.median(db_t[loud])), float(np.median(db_d[loud])))
    print("edges", d[0], d[-1], "identical?", np.array_equal(d, t))
