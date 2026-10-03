"""Verify: the one-click button state on the page is only refreshed on load / voice change / prepare / one-click.
Simulate the page's button state as 'page_btn' = whatever the last handler that outputs tr_btn returned."""
import sys, re
from pathlib import Path
from common import *  # noqa
from conftest import make_lecture
from voicetwin.webui import app as A

cfg, p, ui = fresh("rev")
ids0 = [r["id"] for r in p.load_manifest()]
# 1) page load -> button
page_btn = ui.textfix_btn(VOICE)["interactive"]
print("1 load: page button", page_btn, "backend used", wf.textfix_used(cfg, VOICE))
# 2) one-click (button output)
outs = list(ui.do_textfix(VOICE)); last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
page_btn = last["tr_btn"]["interactive"]
print("2 one-click: page button", page_btn, "backend used", wf.textfix_used(cfg, VOICE))
# 3) add new material (prepare refreshes tr_btn by .then)
lec2 = Path(p.root).parent.parent / "lec2"
make_lecture(lec2 / "第2课.wav", repeats=1, seed=7)
wf.run_prepare(cfg, VOICE, [str(lec2)])
new = [r["id"] for r in p.load_manifest() if r["id"] not in ids0]
page_btn = ui.textfix_btn(VOICE)["interactive"]
print("3 new material:", len(new), "new rows; page button", page_btn, "new ids", len(tf.textfix_new_ids(p)))
# 4) delete all new rows via the table (handler outputs: msg, count, table only)
for rid in new:
    res = act(ui, "delete", rid)
    assert len(res) == 3
print("4 deleted all new rows: page button (not refreshed)", page_btn, "| backend used", wf.textfix_used(cfg, VOICE),
      "| info locked line:", A.TEXTFIX_LOCKED_INFO[:20] in ui.textfix_info(VOICE))
# 5) she clicks the still-lit button
outs = list(ui.do_textfix(VOICE)); last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("5 click lit button -> bar:", re.sub("<[^>]+>", "", str(last["proof_bar"]))[:80])
page_btn = last["tr_btn"]["interactive"]
print("  page button now", page_btn)
# 6) she restores one of the new rows
act(ui, "restore", new[0])
print("6 restore one new row: page button (not refreshed)", page_btn, "| backend used", wf.textfix_used(cfg, VOICE),
      "| new ids", tf.textfix_new_ids(p))
# 7) what a reload would show + does the one-click actually work now?
print("7 reload would show button", ui.textfix_btn(VOICE)["interactive"])
outs = list(ui.do_textfix(VOICE)); last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("  one-click now:", re.sub("<[^>]+>", "", str(last["proof_md"])).splitlines()[0] if last["proof_md"] else last["proof_bar"])
