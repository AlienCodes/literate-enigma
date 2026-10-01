"""Write cohort.json for scripts/build_sv_cohort.py: 400 English speakers (Speech Commands cohort group, up to
12 one-word files each) + Mandarin voices from public repos (zh set minus the 2-speaker MOSS file, clone-set prompts,
FunAudioLLM demo prompts). Mandarin duplicates (same voice in two repos) are removed later by embedding similarity."""
import glob
import json
import os
import random

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, "data", "sc")
RNG = random.Random(20261001)

# English: same speaker split as build_sets.py -> the "cohort" group
by_spk = {}
for w in sorted(os.listdir(SC)):
    d = os.path.join(SC, w)
    if os.path.isdir(d) and not w.startswith("_"):
        for f in os.listdir(d):
            by_spk.setdefault(f.split("_nohash_")[0], []).append(os.path.join(d, f))
spks = sorted(s for s, fs in by_spk.items() if len(fs) >= 12)
random.Random(20261001).shuffle(spks)
cohort_en = spks[600:1000]
assert set(cohort_en) == set(np.load(os.path.join(HERE, "set_en_cohort.npz"), allow_pickle=True)["labels"].tolist())
people = []
for s in cohort_en:
    files = sorted(by_spk[s]); RNG.shuffle(files)
    people.append({"speaker": "sc_" + s, "lang": "en", "files": files[:12]})

zh_files = sorted(glob.glob(os.path.join(HERE, "data", "zh", "*"))) + \
    sorted(glob.glob(os.path.join(HERE, "data", "sr-data", "**", "*.wav"), recursive=True))
import re  # noqa: E402
import sys  # noqa: E402
sys.path.insert(0, HERE)
from build_sets import SAME  # noqa: E402
groups = {}
for f in zh_files:
    base = os.path.basename(f)
    if "single_reference" in base:
        continue
    spk = next((lab for pat, lab in SAME if re.search(pat, base)), base)
    groups.setdefault(spk, []).append(f)
for spk, files in sorted(groups.items()):
    people.append({"speaker": "zh_" + spk, "lang": "zh", "files": files})
idx = os.path.join(HERE, "repos", "index-tts_index-tts.github.io")
for f in sorted(glob.glob(os.path.join(idx, "examples_part[12]", "Prompt", "*.wav"))):
    people.append({"speaker": "idx_" + os.path.basename(f), "lang": "zh", "files": [f]})
for f in sorted(glob.glob(os.path.join(HERE, "repos", "FunAudioLLM_FunAudioLLM.github.io", "**", "*.wav"), recursive=True)):
    people.append({"speaker": "fun_" + os.path.relpath(f, HERE), "lang": "zh", "files": [f]})
json.dump(people, open(os.path.join(HERE, "cohort.json"), "w"), ensure_ascii=False, indent=0)
print(len(people), "people:", sum(p["lang"] == "en" for p in people), "en,", sum(p["lang"] == "zh" for p in people), "zh")
