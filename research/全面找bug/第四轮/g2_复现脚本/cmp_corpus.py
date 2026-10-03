# 新旧 clean_transcript 在程序自带母本、老师母本原文 / 修缮后上的结果比较（应该一句都不变）
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import csv, sys, importlib.util
sys.path.insert(0, str(ROOT))
import subprocess, tempfile
_tmp = tempfile.TemporaryDirectory()  # 跑完自动删掉
_old = Path(_tmp.name) / "textutil_old.py"  # 修以前的版本（第四轮开始时的提交 c46f66c）
_old.write_bytes(subprocess.check_output(["git", "-C", str(ROOT), "show", "c46f66c:voicetwin/utils/textutil.py"]))
spec = importlib.util.spec_from_file_location("old", str(_old))
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
from voicetwin.utils.textutil import clean_transcript as new
R = str(ROOT) + "/"
texts = []
for ln in open(R + "voicetwin/data/lexicon/core_corpus.tsv", encoding="utf-8"):
    if ln.strip() and not ln.startswith("#"):
        texts.append(ln.rstrip("\n").split("\t")[-1])
for f in ("母本_原文.csv", "母本_修缮后.csv"):
    with open(R + "research/文字校正/老师的母本/" + f, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            texts.append(row.get("text") or "")
diff = 0
for t in texts:
    a, b = old.clean_transcript(t), new(t)
    if a != b:
        diff += 1
        print("DIFF", repr(t[:60]), repr(a[:60]), repr(b[:60]))
    if new(b) != b:
        print("NOT IDEMPOTENT", repr(t[:60]))
print("texts", len(texts), "diff", diff)
