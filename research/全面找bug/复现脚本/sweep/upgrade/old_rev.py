import sys, json
SRC=sys.argv[1]; sys.path.insert(0, SRC); sys.path.insert(0, SRC+"/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
import voicetwin; print("old", voicetwin.__version__)
WS = Path(sys.argv[2]); V="我的声音"
cfg = make_cfg(WS); p = wf.open_project(cfg, V, must_exist=True)
rid = p.load_manifest()[7]["id"]  # 壮与从剧放在据首 (old suspect 壮与从剧->状语从句)
review.adopt_suggestion(p, rid); wf.review_save(cfg, V, [rid])
review.unadopt_suggestion(p, rid); wf.review_save(cfg, V, [rid])
r = {x["id"]: x for x in p.load_manifest()}[rid]
print(json.dumps({k: r.get(k) for k in ("text","orig_text","text_edited","suspect")}, ensure_ascii=False))
wf.review_confirm(cfg, V)
