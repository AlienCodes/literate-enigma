from common import *
orig, heard = "我们今天讲是个函数王芳同学回答", "我们今天讲十个函数黄芳同学回答"
for save_between in (False, True):
    print("== save_between", save_between)
    cfg, project = voice([orig])
    fake_engine({"c000": heard})
    pc.find_suspects(project, cfg)
    show(project, "c000", "auto")
    review.adopt_suggestion(project, "c000")
    if save_between: review.save_rows(project)
    show(project, "c000", "adopted both")
    review.set_draft(project, "c000", text="我们今天讲是个函数黄芳同学回答")  # revert 十→是 only
    if save_between: review.save_rows(project)
    print("rejected:", review.load_rejected(project))
    show(project, "c000", "after typing 是 back (before 🔍)")
    pc.find_suspects(project, cfg)
    rec, t = cur(project, "c000"); i = review.analyze(rec, t)
    show(project, "c000", "after 🔍")
    rej = review.load_rejected(project).get("c000")
    print("   rejected-suggested:", [ (t[s:e], r) for s, e, r in i["edits"] if review.is_rejected(rej, t, s, e, r)])
    # one-click too
    wf.run_transcript_fix(cfg, "v", once=True)
    show(project, "c000", "after one-click")
