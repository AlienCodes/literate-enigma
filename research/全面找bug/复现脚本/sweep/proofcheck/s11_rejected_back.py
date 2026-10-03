"""老师撤销过的建议（点「采用」再点「已采用」撤销 = 不要这个改法），一键全部文字校正以后不再建议；
再点「🔍 自动查找」（或者加新素材时自动查）以后，这个被老师否决的建议又回来了吗？"""
from common import *
cfg, project = voice(["今天王芳同学回答得很好", "下面我们来看第二个例子"])
fake_engine({"c000": "今天黄芳同学回答得很好", "c001": "下面我们来看第二个例子"})
pc.find_suspects(project, cfg)                 # 准备素材时自动查（另一个引擎听成「理化」）
show(project, "c000", "auto")
review.adopt_suggestion(project, "c000")       # 老师点「采用」听了听不对
review.unadopt_suggestion(project, "c000")     # 再点「已采用」撤销 → 记进 review_rejected.json
print("rejected:", review.load_rejected(project))
wf.run_transcript_fix(cfg, "v", once=True)     # 一键全部文字校正：不再建议（老师的决定为准）
show(project, "c000", "after one-click")
pc.find_suspects(project, cfg)                 # 再点「🔍 自动查找」/ 加新素材时自动查
show(project, "c000", "after auto check again")
