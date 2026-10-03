"""Teacher keeps her videos under the VoiceTwin folder and types that parent folder (or D:\\) as the material folder:
prepare's rglob also picks up the program's own workspace files (clips, raw, references, generated outputs, uploads)."""
import shutil
from pathlib import Path
from common import cleanup, lecture, make_cfg, workspace
from voicetwin import workflows as wf
from voicetwin.data.prepare import discover_sources
base = workspace("parent")              # like D:\VoiceTwin
videos = base / "讲课视频"; shutil.copytree(lecture(2), videos)
cfg = make_cfg(base / "workspace")
s = wf.run_prepare(cfg, "张老师", [str(videos)])
wf.run_narrate(cfg, "张老师", "大家好，这是生成出来的一句话。", quality="fast")   # a generated file in outputs/
found = discover_sources([str(base)])
print("files that a re-run on the parent folder would treat as lecture material:")
for f in found:
    print("   ", f.relative_to(base))
s2 = wf.run_prepare(cfg, "张老师", [str(base)])
print("clips before:", s["clips_total"], "after re-run on parent folder:", s2["clips_total"], "| new files processed:", s2["files_new"])
srcs = {r.get("source_file", "").split("/workspace/")[-1] for r in wf.Project(cfg, "张老师").load_manifest() if "/workspace/" in r.get("source_file", "")}
print("clips cut from the program's own files:", sorted(srcs)[:6])
cleanup()
