"""第四轮 g1 真实浏览器检查的准备：建一个声音（测试引擎、合成的讲课录音、不识别），放好要用的几行。
用法：python setup.py <仓库> <工作文件夹>"""
import os
import sys
from pathlib import Path

REPO, root = sys.argv[1], Path(sys.argv[2]).resolve()
sys.path.insert(0, REPO + "/tests")
sys.path.insert(0, REPO)
from conftest import make_lecture  # noqa: E402

root.mkdir(parents=True, exist_ok=True)
lect = root / "lectures"
make_lecture(lect / "第1课.wav", repeats=3)
(root / "config.yaml").write_text("""workspace: ./ws
backend: dummy
speaker_encoder: mfcc
prepare:
  asr:
    engine: none
similarity:
  model_dir: ./sv
""", encoding="utf-8")
os.chdir(root)
from voicetwin.config import load_config  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.data import review  # noqa: E402

cfg = load_config()
wf.run_prepare(cfg, "我的声音", [str(lect)])
project = wf.open_project(cfg, "我的声音", must_exist=True)
recs = project.load_manifest()
for r in recs:
    r.pop("suspect", None)
    r.update(keep=True, manual_keep=True)
    r.pop("drop_reason", None)


def sus(t, a, b, alt):
    return {"spans": [[a, b]], "alt": alt, "reasons": ["测试"], "score": 0.7}


T0 = "我们今天学习定语从句。"
recs[0].update(text=T0, lang="zh", suspect=sus(T0, 6, 7, "我们今天学习状语从句。"))
T1 = "我们我们来看看第二个第二个例子。"
recs[1].update(text=T1, lang="zh", suspect={"spans": [[0, 2], [9, 12]], "alt": "我们来看看第二个例子。",
                                           "reasons": ["测试"], "score": 0.7})
T2 = "在这个句子中，which前面的借词是in。"
i = T2.index("借词")
recs[2].update(text=T2, lang="zh", suspect=sus(T2, i, i + 2, T2.replace("借词", "介词")))
T3 = "艾子在这里是关系代词。"
recs[3].update(text=T3, lang="zh", suspect=sus(T3, 0, 2, "as在这里是关系代词。"))
T4 = "这里有一个借词。"
recs[4].update(text=T4, lang="zh", suspect=sus(T4, 5, 7, "这里有一个介词。"))
T5 = "这个借词很短。"
recs[5].update(text=T5, lang="zh", keep=False, drop_reason="太短", suspect=sus(T5, 2, 4, "这个介词很短。"))
recs[5].pop("manual_keep", None)
MD = ["我们  来看  *设置*  和 _下划线_ 还有 `代码` [括号] <b>粗</b> 1. 开头",
      "Let's look at it, as you see.",
      "全角，标点：和（括号）还有 ABC１２３",
      "a|b # c > d ~ e $ f & g",
      "http://example.com/a_b 和 www.example.com 网址"]
for k, t in enumerate(MD):
    recs[6 + k].update(text=t, lang="zh")
project.save_manifest(recs)
project.export_csv(recs)
review.set_draft(project, recs[1]["id"], text="我们我们来看第二个第二个例子。")  # 老师先自己改了一处：采用会被拒绝
print("ok", len(recs), [r["id"] for r in recs[:11]])
