from common import *
cfg, project = voice(["今天王芳同学回答得很好"])
fake_engine({"c000": "今天黄芳同学回答得很好"})
pc.find_suspects(project, cfg)
review.adopt_suggestion(project, "c000"); review.unadopt_suggestion(project, "c000")
show(project, "c000", "single: right after 已采用 undo (before 🔍)")
# two suggestions, teacher clicks the red button (undo all), then 🔍
orig, heard = "我们今天讲是个函数王芳同学回答", "我们今天讲十个函数黄芳同学回答"
cfg, project = voice([orig]); fake_engine({"c000": heard})
pc.find_suspects(project, cfg)
review.adopt_suggestion(project, "c000"); review.unadopt_suggestion(project, "c000")
print("rejected:", review.load_rejected(project))
pc.find_suspects(project, cfg)
show(project, "c000", "two: undo-all via button, after 🔍")
