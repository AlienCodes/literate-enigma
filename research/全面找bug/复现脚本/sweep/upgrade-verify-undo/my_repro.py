"""Run CURRENT code (v18.5) on a workspace built by v18.4 (replace 借词->介词, saved, confirmed).
Scenario A: one-click, then 撤销刚才的替换. Scenario B (arg 'noclick'): just 撤销刚才的替换."""
import sys, json, re
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
import voicetwin
assert voicetwin.__version__ == "18.5", voicetwin.__file__
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review, transcript_fix
from voicetwin.webui import app as A
ws, mode = Path(sys.argv[1]), sys.argv[2]
cfg = make_cfg(ws); V = "我的声音"; p = wf.open_project(cfg, V, must_exist=True); ui = A.WebUI(cfg)
def row6():
    recs = p.load_manifest(); r = recs[6]; d = review.load_draft(p).get(r["id"])
    return r["id"], r["text"], review.current_values(r, d)["text"], review.is_dirty(r, d)
print("version", voicetwin.__version__, "| undo file exists:", review.has_undo(p))
print("undo record:", json.loads((p.root / review.UNDO_FILE).read_text(encoding="utf-8")))
print("row6 before:", row6())
print("blocker before:", repr(wf.training_blocker(p)))
ui.on_voice_change(V)
if mode == "click":
    print("textfix_used before:", wf.textfix_used(cfg, V))
    outs = list(ui.do_textfix(V))
    print("textfix done; textfix_used after:", wf.textfix_used(cfg, V), "| undo file still exists:", review.has_undo(p))
    print("row6 after one-click:", row6())
    # save + confirm after the one-click (as the page tells her) -- does the undo record survive this too?
    if len(sys.argv) > 3 and sys.argv[3] == "save":
        r = wf.review_confirm(cfg, V); print("confirm after one-click:", r.get("confirmed"), "| undo exists:", review.has_undo(p))
status = ui.do_undo_replace(V)[0]
print("undo status:", re.sub("<[^>]+>", "", str(status))[:300])
print("row6 after undo:", row6())
rid = row6()[0]
print("rejected for row6:", review.load_rejected(p).get(rid))
print("blocker after:", repr(wf.training_blocker(p))[:200])
print("textfix button grey (used):", wf.textfix_used(cfg, V))
# Does the one-click refuse now?
try:
    wf.run_transcript_fix(cfg, V, once=True); print("one-click ran again")
except ValueError as e:
    print("one-click refused:", str(e)[:60])
