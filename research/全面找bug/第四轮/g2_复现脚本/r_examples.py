# 复现 appC#4：一键校正结果里的「例如：」把英文词切开、只给单个字
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import csv, sys, tempfile
sys.path.insert(0, str(ROOT) + "/tests")
from conftest import make_cfg
from pathlib import Path
from voicetwin import workflows as wf
from voicetwin.data import review
from voicetwin.webui.app import WebUI
IDS = ["0006_9498bb_0031", "0006_9498bb_0037", "0006_9498bb_0043", "0006_9498bb_0072", "0006_9498bb_0104", "0007_d8ade5_0073"]
rows = {r["id"]: r["text"] for r in csv.DictReader(open(str(ROOT) + "/research/文字校正/老师的母本/母本_原文.csv", encoding="utf-8-sig"))}
with tempfile.TemporaryDirectory() as d:
    cfg = make_cfg(Path(d) / "ws")
    project = wf.Project(cfg, "v").ensure()
    project.save_manifest([{"id": i, "path": f"clips/{i}.wav", "text": rows[i], "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for i in IDS])
    res = wf.run_transcript_fix(cfg, "v", once=True)
    print("raw examples:", res["examples"], res["adopted"].get("examples"))
    md = WebUI._textfix_md(res)
    print([ln for ln in md.splitlines() if ln.startswith("例如")])
    draft = review.load_draft(project)
    for i in IDS:
        if i in draft:
            print(" ", review.describe_change(rows[i], draft[i]["text"]))
