"""手动看一遍：准备素材 → 完美档生成 → 打印进度和日志（测试引擎）。"""
import json
import sys
import shutil
from pathlib import Path

sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-8")
sys.path.insert(0, "<仓库>/.claude/worktrees/wf_08725f86-d54-8/tests")

from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402

base = Path("<草稿目录>/u3demo")
shutil.rmtree(base, ignore_errors=True)
make_lecture(base / "in" / "第1课.wav", repeats=3)
cfg = make_cfg(base / "ws")
steps = []


def prog(f, m):
    steps.append((round(f, 3), m))


summary = wf.run_prepare(cfg, "演示", [str(base / "in")], progress=prog)
print("PREPARE steps:", len(steps))
for s in steps[:6] + steps[-6:]:
    print("  ", s)
steps.clear()
res = wf.run_narrate(cfg, "演示", "大家好，今天我们学习函数。\n\n函数可以重复使用，非常方便！\n\n你们明白了吗？",
                     out=str(base / "out" / "演示课.wav"), quality="perfect", progress=prog)
print("NARRATE steps:", len(steps))
for s in steps:
    print("  ", s)
print("variants:", json.dumps(res.variants, ensure_ascii=False, indent=1))
print("notes:", res.notes)
print("flagged:", res.flagged)
print("table:", wf.narration_table(res.segments))
print("library:", wf.voice_library_rows(cfg))
