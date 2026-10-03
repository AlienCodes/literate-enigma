"""Re-check: CLI prepare -> review -> train (without confirm), with confirm, and `auto`, GPT-SoVITS fake backend."""
import sys, tempfile
from pathlib import Path
import common
from common import HERE, build_fake_root, port
from voicetwin import cli
tmp = Path(tempfile.mkdtemp(prefix="cli_", dir=str(HERE / "tmp")))
root = build_fake_root(tmp / "GPT-SoVITS", real_api=True)
cfgp = tmp / "config.yaml"
cfgp.write_text(f"""workspace: {tmp/'ws'}
backend: gptsovits
speaker_encoder: mfcc
prepare:
  asr:
    engine: none
similarity:
  model_dir: {tmp/'sv'}
backends:
  gptsovits:
    root: {root}
    python: {sys.executable}
    port: {port()}
    train:
      sovits_epochs: 2
      gpt_epochs: 2
      batch_size: 2
""", encoding="utf-8")
lec = str(HERE / "base" / "lectures")
def run(argv):
    print("\n$ voicetwin", " ".join(argv), flush=True)
    try:
        cli.main(["-c", str(cfgp)] + argv)
        print("-> exit 0", flush=True); return 0
    except SystemExit as e:
        print("-> exit", e.code, flush=True); return e.code
which = sys.argv[1]
if which == "train":
    run(["prepare", "-v", "甲", "-i", lec])
    run(["review", "-v", "甲"])
    r1 = run(["train", "-v", "甲", "--no-select"])   # README old flow w/o confirm: expected refusal
    r2 = run(["confirm", "-v", "甲"])
    r3 = run(["train", "-v", "甲", "--no-select"])
    print("RESULT train-without-confirm", r1, "confirm", r2, "train-after-confirm", r3)
elif which == "confirm_empty":
    r = run(["confirm", "-v", "不存在"])
    print("RESULT confirm-nonexistent", r)
else:
    r = run(["auto", "-v", "乙", "-i", lec])
    print("RESULT auto", r)
