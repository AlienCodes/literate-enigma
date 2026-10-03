"""Reproduce: following the written upgrade steps (extract to D:\\ -> D:\\VoiceTwin) when the
teacher's real install is D:\\VoiceTwin-Windows-v18.2\\VoiceTwin.

Simulates fake drive D under the scratch dir. Uses the real release zip built by
scripts/build_windows_release.py, the real init-config CLI path, and the real web UI status function.
"""
import os, subprocess, sys, zipfile, re, shutil, json
from pathlib import Path

REPO = Path("/home/user/literate-enigma")
SCR = Path(__file__).resolve().parent
D = SCR / "fakeD"
DIST = SCR / "dist"
PY = sys.executable
shutil.rmtree(D, ignore_errors=True); shutil.rmtree(DIST, ignore_errors=True)
D.mkdir(); DIST.mkdir()

# 1. build the real zip + release notes
r = subprocess.run([PY, str(REPO / "scripts/build_windows_release.py"), "--out", str(DIST),
                    "--notes", str(DIST / "notes.md")], capture_output=True, text=True, cwd=str(SCR))
print("build:", r.returncode, r.stdout.strip(), r.stderr.strip()[-400:])
zips = list(DIST.glob("VoiceTwin-Windows-v*.zip"))
assert zips, "no zip"
zp = zips[0]
with zipfile.ZipFile(zp) as zf:
    tops = sorted({n.split("/")[0] for n in zf.namelist()})
    guide = zf.read("VoiceTwin/使用教程（先看我）.html").decode("utf-8")
print("zip top-level folders:", tops)
notes = (DIST / "notes.md").read_text(encoding="utf-8")
for label, text in (("release notes", notes), ("guide html in zip", guide)):
    hits = [l.strip() for l in re.split(r"[\n]", re.sub(r"<[^>]+>", "", text)) if "位置填" in l or "install_windows.bat" in l][:4]
    print(f"--- {label} upgrade lines:"); [print("   ", h[:200]) for h in hits]

def extract(dest: Path):
    with zipfile.ZipFile(zp) as zf:
        zf.extractall(dest)

def init_config(install: Path):
    # what install_windows.ps1 step "生成设置文件" does (gsv mode): cwd = $Here
    r = subprocess.run([PY, "-m", "voicetwin", "init-config", "--backend", "gptsovits"], cwd=str(install),
                       capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=str(REPO)))
    print(f"init-config in {install.relative_to(SCR)}:", r.returncode, r.stdout.strip()[-200:], r.stderr.strip()[-300:])

# 2. the teacher's real install: D:\VoiceTwin-Windows-v18.2\VoiceTwin with a prepared, confirmed, trained voice
old_root = D / "VoiceTwin-Windows-v18.2"
extract(old_root)
old = old_root / "VoiceTwin"
init_config(old)

sys.path.insert(0, str(REPO))
from voicetwin.config import load_config
from voicetwin import workflows as wf
from voicetwin.webui import app as webapp

def cfg_for(install: Path):
    os.chdir(install)  # start_webui.bat does: cd /d "%~dp0"
    return load_config(None)

cfg_old = cfg_for(old)
proj = wf.Project(cfg_old, "我的声音").ensure()
recs = [{"id": f"c{i:04d}", "path": f"clips/c{i:04d}.wav", "text": f"第{i}句已经校对好的讲课内容", "lang": "zh",
         "duration": 3.0, "keep": True, "split": "train"} for i in range(1000)]
proj.save_manifest(recs)
from voicetwin.data import review
review.save_confirmed(proj, proj.load_manifest())
proj.update_models("gptsovits", {"selected": {"gpt": "x.ckpt", "sovits": "y.pth"}, "trained_at": "2026-10-02 18:00"})
print("\nOLD install workspace:", proj.root if hasattr(proj, "root") else "?")
print("OLD install status   :", webapp._voice_status_md(cfg_old, "我的声音")[:160])

# 3. follow the written upgrade steps: extract to D:\ (-> D:\VoiceTwin), run D:\VoiceTwin\install_windows.bat
extract(D)
new = D / "VoiceTwin"
init_config(new)
cfg_new = cfg_for(new)
print("\nNEW install exists at :", new.relative_to(SCR), "| old install untouched:", (old / "workspace" / "我的声音" / "manifest.jsonl").exists())
print("NEW install workspace has voices:", sorted(p.name for p in (new / "workspace").glob("*")) if (new / "workspace").exists() else "(no workspace folder)")
print("NEW install status   :", webapp._voice_status_md(cfg_new, "我的声音"))
# Show-ExistingVoices equivalent for $Here = new
ws = new / "workspace"
voices = [p.name for p in ws.glob("*") if p.is_dir() and not p.name.startswith("__") and (p / "manifest.jsonl").exists()] if ws.exists() else []
print("Show-ExistingVoices($Here=D:\\VoiceTwin) would list:", voices or "nothing (prints no line)")
