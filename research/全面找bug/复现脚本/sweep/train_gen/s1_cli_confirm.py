"""CLI: README flow prepare -> review -> train, and `auto`, with the GPT-SoVITS backend."""
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
    print("\n$ voicetwin", " ".join(argv))
    try:
        cli.main(["-c", str(cfgp)] + argv)
        print("-> exit 0")
    except SystemExit as e:
        print("-> exit", e.code)
which = sys.argv[1]
if which == "train":
    run(["prepare", "-v", "甲", "-i", lec])
    run(["review", "-v", "甲"])
    run(["train", "-v", "甲", "--no-select"])
else:
    run(["auto", "-v", "乙", "-i", lec])
