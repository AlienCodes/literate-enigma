"""真的「开始准备素材」两次（第二次是新加的录音）：第一次以后点一键全部文字校正（每批只能一次）；
加新素材时准备素材会自动查错字（装了 FunASR 时），以前那批的标准库建议还在吗？"""
from common import *
import common
_tmps = common._tmps
from conftest import make_lecture

d = Path(tempfile.mkdtemp(dir=str(SCR)))
_tmps.append(d)
cfg = make_cfg(d / "ws")  # 字幕 + engine none（和测试一样）
make_lecture(d / "in1" / "第1课.wav", repeats=1, seed=1)
# 假装装了 FunASR → 准备素材最后会自动查错字（proofcheck: auto）
fake_engine({})  # 第二个引擎什么都听不出（不影响：只看标准库的建议会不会被冲掉）
class Echo(dict):  # 第二个引擎听到的 = 校对表里的文字（没有自动查出的错）
    def get(self, k, d=None):
        for r in wf.open_project(cfg, "v", must_exist=True).load_manifest():
            if r["id"] == k:
                return r["text"]
        return d
_answers = Echo()
pc._make_checker = lambda name, cfg: FakeChecker(name, answers=_answers)

s1 = wf.run_prepare(cfg, "v", [str(d / "in1")])
project = wf.open_project(cfg, "v", must_exist=True)
recs = project.load_manifest()
print("prepare 1:", s1.get("clips_kept"), "clips; proofcheck:", (s1.get("proofcheck") or {}).get("checked"))
# 一句话和老师上传的 transcripts.csv 里同一个 id 只是「有点像」→ 一键校正给一条没把握的建议（不自动改）
tid = next(r["id"] for r in recs if r["text"].startswith("首先"))
up = d / "transcripts.csv"
up.write_text(f"id,text\n{tid},我们今天来学习定语从句{next(r['text'] for r in recs if r['id']==tid)}\n", encoding="utf-8")
res = wf.run_transcript_fix(cfg, "v", files=[str(up)], once=True)
print("one-click:", res["adopted"])
show(project, tid, "after one-click")
review.save_rows(project)

make_lecture(d / "in2" / "第2课.wav", repeats=1, seed=7)
s2 = wf.run_prepare(cfg, "v", [str(d / "in1"), str(d / "in2")])
print("prepare 2 (new material):", s2.get("clips_kept"), "clips; proofcheck checked:", (s2.get("proofcheck") or {}).get("checked"))
show(project, tid, "after adding new material")
print("one-click button grey:", tf.textfix_used(project), "new ids:", len(tf.textfix_new_ids(project)))
res = wf.run_transcript_fix(cfg, "v", once=True)
print("one-click on new material: only", res.get("only"), "rows")
show(project, tid, "after one-click on new material")
