"""README documents the command-line flow  prepare -> (edit CSV) -> review -> train  and  auto.
There is no CLI command that records 「确认训练素材」, so train / auto can never start for a training engine."""
import subprocess, sys, textwrap
from common import REPO, cleanup, lecture, workspace
sys.path.insert(0, str(REPO / "tests"))
from fake_gptsovits import build_fake_root

ws = workspace("cli")
root = build_fake_root(ws / "GPT-SoVITS")
cfgf = ws / "config.yaml"
cfgf.write_text(textwrap.dedent(f"""
workspace: "{ws / 'workspace'}"
backend: gptsovits
speaker_encoder: mfcc
prepare:
  asr:
    engine: none
backends:
  gptsovits:
    root: "{root}"
    python: "{sys.executable}"
similarity:
  model_dir: "{ws / '_sv'}"
"""), encoding="utf-8")
def vt(*args):
    r = subprocess.run([sys.executable, "-m", "voicetwin", "-c", str(cfgf), *args], cwd=str(REPO),
                       capture_output=True, text=True, timeout=600)
    out = (r.stdout + r.stderr).strip().splitlines()
    print(f"$ voicetwin {' '.join(args)}  -> exit {r.returncode}")
    for l in out[-3:]:
        print("   ", l[:200])
vt("prepare", "-v", "我的声音", "-i", str(lecture(2)))
vt("review", "-v", "我的声音")
vt("train", "-v", "我的声音", "--no-select")
vt("confirm", "-v", "我的声音")
vt("train", "-v", "我的声音", "--no-select")
vt("auto", "-v", "我的声音2", "-i", str(lecture(2)))
cleanup()
