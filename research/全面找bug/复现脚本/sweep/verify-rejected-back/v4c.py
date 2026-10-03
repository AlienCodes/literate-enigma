from common import *
for orig, heard in [("今天王芳同学回答得很好我们去公圆", "今天黄芳同学回答得很好我们去公园"),
                    ("我们今天讲是个函数王芳同学回答", "我们今天讲十个函数黄芳同学回答"),
                    ("小王同学说这个主剧的结构也很完成", "小黄同学说这个主句的结构也很完整")]:
    cfg, project = voice([orig])
    fake_engine({"c000": heard})
    pc.find_suspects(project, cfg)
    info = show(project, "c000", "auto")
    if len(info["edits"]) < 2:
        continue
    rec, text = cur(project, "c000")
    first = info["edits"][0]
    # reject only the first suggestion: adopt all, then retype so that only first is reverted
    review.adopt_suggestion(project, "c000")
    rec, t2 = cur(project, "c000")
    i2 = review.analyze(rec, t2)
    u = sorted(i2["undo"])[0]
    reverted = t2[:u[0]] + u[2] + t2[u[1]:]
    review.set_draft(project, "c000", text=reverted); review.save_rows(project)
    review.set_draft(project, "c000", text=orig, remember=False); review.save_rows(project)
    print("rejected:", review.load_rejected(project))
    pc.find_suspects(project, cfg)
    show(project, "c000", "after 🔍 (rejected one gone, other kept)")
    break
