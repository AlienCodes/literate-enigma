"""One damaged models.json / prepare_summary.json in ONE voice -> the web page's voice dropdown and voice library
become completely empty (all voices 'disappear')."""
import shutil
from common import cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.webui import app as webapp

ws = workspace("uilist")
cfg = make_cfg(ws)
wf.run_prepare(cfg, "张老师", [str(lecture(2))])
shutil.copytree(ws / "张老师", ws / "李老师")
shutil.copytree(ws / "张老师", ws / "王老师")
print("before:", webapp._voices(cfg), [e["name"] for e in webapp._library_entries(cfg)])
# simulate what a power cut right after an (un-fsynced) atomic replace can leave behind: an empty file
(ws / "李老师" / "models.json").write_bytes(b"")
print("after damaging 李老师/models.json:", webapp._voices(cfg), [e["name"] for e in webapp._library_entries(cfg)])
(ws / "李老师" / "models.json").unlink()
(ws / "王老师" / "prepare_summary.json").write_bytes(b"\x00" * 64)
print("after damaging 王老师/prepare_summary.json:", webapp._voices(cfg), [e["name"] for e in webapp._library_entries(cfg)])
cleanup()
