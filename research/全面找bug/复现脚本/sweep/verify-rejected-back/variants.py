"""独立复现：老师撤销过的建议，再点 🔍 自动查找 / 加新素材后的自动查找，会不会又回来。"""
from common import *

ok = True
def check(label, project, rid, want_no=None, want_has=None):
    global ok
    info = show(project, rid, label)
    rec, text = cur(project, rid)
    ed = [(text[s:e], r) for s, e, r in info["edits"]]
    if want_no is not None and want_no in ed:
        print("   !!! REJECTED SUGGESTION BACK:", want_no); ok = False
    if want_has is not None and want_has not in ed:
        print("   !!! expected suggestion missing:", want_has); ok = False
    return info

# V1: adopt -> unadopt (unsaved) -> 🔍 directly, no one-click
print("== V1 adopt/unadopt, unsaved, then 🔍 (via workflows.run_proofcheck)")
cfg, project = voice(["今天王芳同学回答得很好", "下面我们来看第二个例子"])
fake_engine({"c000": "今天黄芳同学回答得很好", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)
check("auto", project, "c000", want_has=("王", "黄"))
review.adopt_suggestion(project, "c000"); review.unadopt_suggestion(project, "c000")
print("rejected:", review.load_rejected(project), "draft:", review.load_draft(project))
wf.run_proofcheck(cfg, "v")
check("after 🔍", project, "c000", want_no=("王", "黄"))
wf.run_proofcheck(cfg, "v")
check("after 🔍 x2", project, "c000", want_no=("王", "黄"))

# V2: adopt -> save -> unadopt -> save -> 🔍
print("== V2 adopt/save/unadopt/save then 🔍")
cfg, project = voice(["今天王芳同学回答得很好", "下面我们来看第二个例子"])
fake_engine({"c000": "今天黄芳同学回答得很好", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)
review.adopt_suggestion(project, "c000"); review.save_rows(project)
check("adopted+saved", project, "c000")
review.unadopt_suggestion(project, "c000"); review.save_rows(project)
print("rejected:", review.load_rejected(project))
pc.find_suspects(project, cfg)
check("after 🔍", project, "c000", want_no=("王", "黄"))

# V3: adopt -> save -> teacher types the original back -> save -> 🔍
print("== V3 adopt/save, then teacher retypes original, save, 🔍")
cfg, project = voice(["今天王芳同学回答得很好", "下面我们来看第二个例子"])
fake_engine({"c000": "今天黄芳同学回答得很好", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)
review.adopt_suggestion(project, "c000"); review.save_rows(project)
review.set_draft(project, "c000", text="今天王芳同学回答得很好"); review.save_rows(project)
print("rejected:", review.load_rejected(project))
pc.find_suspects(project, cfg)
check("after 🔍", project, "c000", want_no=("王", "黄"))

# V4: two suggestions, teacher undoes only one by retyping -> 🔍 keeps the other
print("== V4 two suggestions, revert one, 🔍")
cfg, project = voice(["今天王芳同学回答得很号", "下面我们来看第二个例子"])
fake_engine({"c000": "今天黄芳同学回答得很好", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)
check("auto", project, "c000")
review.adopt_suggestion(project, "c000")
check("adopted", project, "c000")
review.set_draft(project, "c000", text="今天王芳同学回答得很好")  # 王 back, 好 kept
print("rejected:", review.load_rejected(project))
review.save_rows(project)
pc.find_suspects(project, cfg)
check("after 🔍", project, "c000", want_no=("王", "黄"))

# V5: new material added later -> auto check over all rows (find_suspects on whole manifest)
print("== V5 new material appended, auto check")
cfg, project = voice(["今天王芳同学回答得很好", "下面我们来看第二个例子"])
fake_engine({"c000": "今天黄芳同学回答得很好", "c001": "下面我们来看第二个例子", "c002": "这是新加的句子"})
pc.find_suspects(project, cfg)
review.adopt_suggestion(project, "c000"); review.unadopt_suggestion(project, "c000")
recs = project.load_manifest()
sf.write(str(project.root / "clips/c002.wav"), np.zeros(1700, dtype=np.float32), 16000)
recs.append({"id": "c002", "path": "clips/c002.wav", "text": "这是新加的句字", "lang": "zh", "duration": 3.0, "keep": True, "split": "train"})
project.save_manifest(recs)
pc.find_suspects(project, cfg)
check("after new material 🔍", project, "c000", want_no=("王", "黄"))
check("new row", project, "c002")

# V6: English 艾子 -> as rejection
print("== V6 English-style rejection")
cfg, project = voice(["我们先来看艾子引导的定语从句"])
fake_engine({"c000": "我们先来看as引导的定语从句"})
pc.find_suspects(project, cfg)
info = check("auto", project, "c000")
if info["edits"]:
    review.adopt_suggestion(project, "c000"); review.unadopt_suggestion(project, "c000")
    print("rejected:", review.load_rejected(project))
    pc.find_suspects(project, cfg)
    rec, text = cur(project, "c000")
    i2 = review.analyze(rec, text)
    rej = review.load_rejected(project).get("c000")
    back = [ed for ed in i2["edits"] if review.is_rejected(rej, text, *ed)]
    show(project, "c000", "after 🔍")
    if back: print("   !!! rejected back", back); ok = False

print("ALL OK" if ok else "PROBLEM FOUND")
