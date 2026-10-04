# 复查（第四轮 g2 的检查意见）用的复现脚本，原样保留；不给参数就用这个仓库：/tmp/gsv39/bin/python 复查_p3_oldcsv.py
# Upload the teacher's original (pre-curation) mother csv into a NEW voice through the web button
import sys, tempfile, shutil
from pathlib import Path
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import transcript_fix as tf
from voicetwin.webui import app as A
d = Path(tempfile.mkdtemp())
try:
    cfg = make_cfg(d / "ws")
    project = wf.Project(cfg, "新声音").ensure()
    rows = ["今天我们来讲一讲非限定性定语从句里面的关系代词艾子。", "这个句子完全没有错误，我们继续往下看。"]
    project.save_manifest([{"id": f"n{i}", "path": f"clips/n{i}.wav", "text": t, "lang": "zh", "duration": 3.0,
                            "keep": True, "split": "train"} for i, t in enumerate(rows)])
    src = ROOT / "research/文字校正/老师的母本/母本_原文.csv"
    up = d / "transcripts.csv"
    shutil.copy(src, up)
    lines = tf.parse_mother(up.name, tf.read_text_file(up))
    print("lines in upload:", len(lines))
    ui = A.WebUI(cfg)
    out = dict(zip(ui.TEXTFIX_OUT, list(ui.do_textfix("新声音", [str(up)]))[-1]))
    bar = out["proof_bar"]
    import re
    print("BAR:", re.sub(r"<[^>]+>", "", str(bar))[:600])
    print("saved files:", tf.load_transcripts(project)[1])
    # store it the old way (run_transcript_fix(files=...) / older version) and look at the info line + result
    tf.save_transcripts(project, [str(up)])
    print("INFO:", ui.textfix_info("新声音"))
    res = tf.check_with_transcript(project, only=[])
    print("files", res["files"], "files_same", res["files_same"])
    print("MD:", [l for l in A.WebUI._textfix_md(res).splitlines() if "上传" in l])
finally:
    shutil.rmtree(d, ignore_errors=True)
