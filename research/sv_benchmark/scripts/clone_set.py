"""Zero-shot voice-clone test set: real prompt recordings + clones of them by 6 TTS systems (IndexTTS demo page:
IndexTTS, XTTS, CosyVoice2, FireRedTTS, F5-TTS, FishSpeech), 20 speakers (mostly Mandarin), plus a few clone
pairs from other repos (Step-Audio, VALL-E, Spark-TTS)."""
import glob
import os

import librosa
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(HERE, "repos", "index-tts_index-tts.github.io")
SYSTEMS = ["IndexTTS", "XTTS", "CosyVoice2", "FireRedTTS", "F5-TTS", "FishSpeech"]


def load(p):
    y, _ = librosa.load(p, sr=16000, mono=True)
    return y.astype(np.float32)


audio, spk, kind, system, name = [], [], [], [], []


def add(path, s, k, sysname):
    audio.append(load(path)); spk.append(s); kind.append(k); system.append(sysname)
    name.append(os.path.relpath(path, HERE))


for p in sorted(glob.glob(os.path.join(IDX, "examples_part1", "Prompt", "*.wav"))):
    s = os.path.basename(p)[:-4]
    add(p, "p1_" + s, "prompt", "real")
    for sy in SYSTEMS:
        for c in sorted(glob.glob(os.path.join(IDX, "examples_part1", sy, f"{s}_*.wav"))):
            add(c, "p1_" + s, "clone", sy)
for p in sorted(glob.glob(os.path.join(IDX, "examples_part2", "Prompt", "*.wav"))):
    s = os.path.basename(p)[:-4]
    add(p, "p2_" + s, "prompt", "real")
    for sy in SYSTEMS:
        c = os.path.join(IDX, "examples_part2", sy, f"{s}.wav")
        if os.path.exists(c):
            add(c, "p2_" + s, "clone", sy)
C = os.path.join(HERE, "data", "clones")
extra = [("stepfun-ai_Step-Audio__examples_prompt_wav_lixueqin.wav", "lixueqin", "prompt", "real"),
         ("stepfun-ai_Step-Audio__examples_clone_wav_lixueqin.wav", "lixueqin", "clone", "Step-Audio"),
         ("stepfun-ai_Step-Audio__examples_prompt_wav_yuqian.wav", "yuqian", "prompt", "real"),
         ("stepfun-ai_Step-Audio__examples_clone_wav_yuqian.wav", "yuqian", "clone", "Step-Audio"),
         ("lifeiteng_vall-e__egs_aishell1_prompts_ch_24k.wav", "aishell_valle", "prompt", "real"),
         ("lifeiteng_vall-e__egs_aishell1_demos_0_demo.wav", "aishell_valle", "clone", "VALL-E"),
         ("SparkAudio_Spark-TTS__example_prompt_audio.wav", "spark", "prompt", "real"),
         ("SparkAudio_Spark-TTS__example_results_20250225113521.wav", "spark", "clone", "Spark-TTS")]
for f, s, k, sy in extra:
    add(os.path.join(C, f), s, k, sy)
print(len(audio), "files,", len(set(spk)), "speakers,", sum(k == "clone" for k in kind), "clones")
np.savez_compressed(os.path.join(HERE, "set_clone.npz"), audio=np.array(audio, dtype=object), labels=np.array(spk),
                    kind=np.array(kind), system=np.array(system), name=np.array(name), allow_pickle=True)
