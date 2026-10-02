"""在老师真实的 1004 句上实测「一键全部文字校正」（老师 10-03 上传的 transcripts.csv，老师同意公开）。

两项：
1. 正常用法（程序自带修缮过的母本 + 逐句修缮记录 + 语法术语 + 对照表）：老师修缮前的句子点一次，
   需要改的句子是不是改得和逐句修缮的一模一样，别的句子有没有被改。
2. 「考试」：不用逐句修缮记录，只靠标准库（术语、对照表、母本里别的句子）能找出多少处，改错多少处。
   注意：对照表本身是从这次修缮里总结的，所以这一项对以后的新录音偏乐观；真正的新录音要等老师用了再看。

运行：python research/文字校正/老师母本实测.py（要装 pypinyin 和 jieba，整合包里都有）；结果写到 老师母本实测结果.txt
"""

import csv
import difflib
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from voicetwin.data import lexicon_fix as lf  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.data import transcript_fix as tf  # noqa: E402

D = Path(__file__).resolve().parent / "老师的母本"
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = list(csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig")))
FIXES = [ln.rstrip("\n").split("\t") for ln in open(D / "修缮记录.tsv", encoding="utf-8")][1:]


class _Project:
    def __init__(self, root, recs):
        self.root, self.voice, self.recs = Path(root), "我的声音", recs

    def load_manifest(self):
        return json.loads(json.dumps(self.recs))

    def save_manifest(self, recs):
        self.recs = json.loads(json.dumps(recs))


def run(use_row_fixes):
    recs = [{"id": r["id"], "text": r["text"], "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
             "path": "x.wav"} for r in ORIG]
    p = _Project(tempfile.mkdtemp(), recs)
    t0 = time.time()
    res = tf.check_with_transcript(p, use_row_fixes=use_row_fixes)
    secs = time.time() - t0
    draft = review.load_draft(p)
    need = {o["id"] for o, c in zip(ORIG, CLEAN) if o["text"] != c["text"] and o["drop_reason"] != "老师删除"}
    exact = sum(1 for o, c in zip(ORIG, CLEAN) if o["id"] in draft and draft[o["id"]]["text"] == c["text"])
    by_id = {}
    for _n, rid, a, b, _why in FIXES:
        by_id.setdefault(rid, []).append((a, b))
    found = sum(1 for o in ORIG for a, b in by_id.get(o["id"], [])
                if o["id"] in draft and a not in draft[o["id"]]["text"] and b in draft[o["id"]]["text"])
    wrong = []
    for o in ORIG:
        if o["id"] not in draft:
            continue
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, o["text"], draft[o["id"]]["text"]).get_opcodes():
            if tag == "equal":
                continue
            seg = o["text"][i1:i2]
            if not any(a.find(seg) >= 0 or seg.find(a) >= 0 for a, _b in by_id.get(o["id"], [])):
                wrong.append(f"{o['id']}：「{seg}」→「{draft[o['id']]['text'][j1:j2]}」")
    sugg = [r for r in p.recs if r.get("suspect") and r["id"] not in draft]
    return res, secs, len(need), exact, found, wrong, sugg


def main():
    out = [f"老师母本实测（{time.strftime('%Y-%m-%d %H:%M')}，pypinyin：{'有' if tf.has_pinyin() else '没有'}，"
           f"jieba：{'有' if lf.has_jieba() else '没有'}）",
           f"老师的句子 {len(ORIG)} 句（删除的 {sum(r['drop_reason'] == '老师删除' for r in ORIG)} 句不查）；"
           f"逐句修缮改了 {len(FIXES)} 处（{len({f[1] for f in FIXES})} 句）", ""]
    for title, use in (("一、正常用法（自带母本 + 逐句修缮记录 + 术语 + 对照表）", True),
                       ("二、考试：不用逐句修缮记录", False)):
        res, secs, need, exact, found, wrong, sugg = run(use)
        out += [f"## {title}",
                f"直接改好 {res['fixes']} 处（{res['fixed_rows']} 句）；只给建议 {res['found']} 句；用时 {secs:.1f} 秒",
                f"需要改的 {need} 句里，改得和逐句修缮一模一样的：{exact} 句",
                f"逐句修缮的 {len(FIXES)} 处里找到了：{found} 处",
                f"改了逐句修缮没改的地方（可能改错）：{len(wrong)} 处"]
        out += [f"  - {w}" for w in wrong[:20]]
        out += [f"只给建议的句子：{len(sugg)} 句"] + [f"  - {r['id']}：{'；'.join(r['suspect']['reasons'])}" for r in sugg[:20]]
        out.append("")
    text = "\n".join(out)
    print(text)
    (Path(__file__).resolve().parent / "老师母本实测结果.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
