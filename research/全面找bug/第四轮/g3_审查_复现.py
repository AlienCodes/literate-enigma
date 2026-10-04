"""第四轮找 bug，g3 组审查意见 review#2（transcripts.csv 的备份只看 transcripts.exported.json 里的编号）：两种情况一起复现。
用法（仓库根目录）：PYTHONPATH=. python research/全面找bug/第四轮/g3_审查_复现.py <临时目录>
1. manifest.jsonl 和 transcripts.exported.json 在同一次断电里都成了一堆 0 / 空文件，再写一次表格；
2. manifest.jsonl 和 sources.json 都成了一堆 0，再点「开始准备素材」：视频重新切一遍，片段编号和原来一模一样
   （和 g4 组合并以后「校对表里一条都没有的视频再切一遍」是同一条路）。
每种情况最后写 BUG（老师改好的字一份都没留下）或 ok（备份里有）。修以前两种都是 BUG，修以后都是 ok（输出见 g3.md）。"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.environ.get("PYTHONPATH", "."))
sys.path.insert(0, str(Path(os.environ.get("PYTHONPATH", ".")) / "tests"))
from conftest import make_cfg, make_lecture  # noqa: E402

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review as R  # noqa: E402

base = Path(tempfile.mkdtemp(dir=sys.argv[1] if len(sys.argv) > 1 else None))


def kept(p, word):
    """备份里有几处 word（找最多的那份）。"""
    return max([b.read_text(encoding="utf-8-sig").count(word) for b in p.root.glob("transcripts_备份_*.csv")] or [0])


# ---- 情况 1：transcripts.exported.json 也坏了
for junk, name in ((b"\x00" * 300, "一堆 0"), (b"", "空文件")):
    p = wf.Project(make_cfg(base / f"c1_{len(junk)}"), "v").ensure()
    p.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "duration": 3.0, "keep": True, "split": "train",
                      "lang": "zh", "text": f"第{i}句老师改好的文字。"} for i in range(5)])
    p.export_csv(p.load_manifest())
    p.manifest_path.write_bytes(junk)
    p.csv_snapshot_path.write_bytes(junk[:200])
    p.export_csv(p.load_manifest())
    n = kept(p, "老师改好的")
    print(f"情况 1（{name}）：表格里还剩 {p.csv_path.read_text(encoding='utf-8-sig').count(chr(10)) - 1} 行，"
          f"备份里有 {n} 句改好的 →", "ok" if n == 5 else "BUG")

# ---- 情况 2：视频重新切一遍，编号一样
lec = base / "lectures"
make_lecture(lec / "第1课.wav")
cfg = make_cfg(base / "c2")
wf.run_prepare(cfg, "v", [str(lec)])
p = wf.Project(cfg, "v")
recs = p.load_manifest()
for r in recs[:5]:
    R.set_draft(p, r["id"], text="老师改好的：" + r["id"])
wf.review_save(cfg, "v")
before = p.csv_path.read_text(encoding="utf-8-sig").count("老师改好的")
p.manifest_path.write_bytes(b"\x00" * 500)
p.sources_path.write_bytes(b"\x00" * 200)
wf.run_prepare(cfg, "v", [str(lec)])
after = p.load_manifest()
n = kept(p, "老师改好的")
print(f"情况 2：保存时 transcripts.csv 里 {before} 句改好的；重新切出 {len(after)} 段，编号一样："
      f"{ {r['id'] for r in after} == {r['id'] for r in recs} }；transcripts.csv 里还剩 "
      f"{p.csv_path.read_text(encoding='utf-8-sig').count('老师改好的')} 句，备份里有 {n} 句 →", "ok" if n == before else "BUG")
