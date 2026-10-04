# 老师 1004 句在 5 种上传情况下点一次一键校正：需要改的 123 句是不是改得和逐句修缮一模一样、有没有多改（g2 修改后复查）
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # 仓库根目录
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import csv, io, json, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(ROOT))
from voicetwin.data import review, transcript_fix as tf

D = Path(str(ROOT) + "/research/文字校正/老师的母本")
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = list(csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig")))


class P:
    def __init__(self, root, recs):
        self.root, self.voice, self.recs = Path(root), "v", recs

    def load_manifest(self):
        return json.loads(json.dumps(self.recs))

    def save_manifest(self, recs):
        self.recs = json.loads(json.dumps(recs))


def csv_text(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


cases = [("不上传", None),
         ("修缮前 csv", ("transcripts.csv", csv_text(ORIG).encode("utf-8"))),
         ("修缮后 csv", ("transcripts.csv", csv_text(CLEAN).encode("utf-8"))),
         ("GBK csv", ("transcripts.csv", csv_text(CLEAN).encode("gb18030"))),
         ("修缮前 txt", ("讲稿.txt", "\n".join(r["text"] for r in ORIG).encode("utf-8"))),
         ("修缮后 txt", ("讲稿.txt", "\n".join(r["text"] for r in CLEAN).encode("utf-8")))]
need = {o["id"] for o, c in zip(ORIG, CLEAN) if o["text"] != c["text"] and o["drop_reason"] != "老师删除"}
clean = {c["id"]: c["text"] for c in CLEAN}
for title, up in cases:
    tmp = tempfile.TemporaryDirectory()  # 跑完自动删掉
    root = tmp.name
    recs = [{"id": r["id"], "text": r["text"], "keep": r["keep"] == "1", "deleted": r["drop_reason"] == "老师删除",
             "path": "x.wav"} for r in ORIG]
    p = P(root, recs)
    if up:
        f = Path(root) / "up" / up[0]
        f.parent.mkdir()
        f.write_bytes(up[1])
        tf.save_transcripts(p, [str(f)])
    t0 = time.time()
    res = tf.check_with_transcript(p)
    draft = review.load_draft(p)
    exact = sum(1 for i in need if i in draft and draft[i]["text"] == clean[i])
    extra = [i for i in draft if i not in need or draft[i]["text"] != clean[i]]
    red = 0
    for r in p.recs:
        if r.get("deleted"):
            continue
        cur = review.current_values(r, draft.get(r["id"]))["text"]
        if review.analyze(r, cur)["active"]:
            red += 1
    print(f"{title}: 改对 {exact}/{len(need)}，多改 {len(extra)} 句 {extra[:3]}，剩下标红 {red} 句，用时 {time.time() - t0:.1f} 秒")
    tmp.cleanup()
