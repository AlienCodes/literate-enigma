"""Targeted conflict scenarios driven through the real WebUI handlers."""
import sys, json
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data.exporters import gptsovits_list_text

which = sys.argv[1:] or ["lang", "skipped", "findsus", "confirmdirty"]
R = {}


def ids(p):
    return [r["id"] for r in p.load_manifest()]


# ---------------------------------------------------------------- 1. language change after confirm
if "lang" in which:
    cfg, p, ui = fresh("lang")
    md, count, rows = ui.do_confirm(VOICE)
    assert "训练素材已确认" in md, md
    i0 = ids(p)[1]
    msg, count, rows = act(ui, "lang", i0)
    print("[lang] action msg:", msg)
    md, count, rows = ui.do_save(VOICE)
    print("[lang] save msg:", md.splitlines()[0])
    print("[lang] saved lang now:", recs(p)[i0]["lang"])
    print("[lang] training_blocker:", repr(wf.training_blocker(p)))
    print("[lang] count shows confirmed:", "训练素材已确认" in count, "| shows changed-warning:", "以后又改过" in count)
    line = [l for l in gptsovits_list_text(p, "spk").splitlines() if recs(p)[i0]["path"].split("/")[-1] in l]
    print("[lang] training list line:", line)

# ---------------------------------------------------------------- 2. one-click marks skipped rows (grey / no text yet) as used
if "skipped" in which:
    cfg, p, ui = fresh("skipped")
    rs = p.load_manifest()
    a, b, c = rs[1]["id"], rs[2]["id"], rs[3]["id"]
    for r in rs:
        r.pop("suspect", None)
        if r["id"] == a:
            r["text"] = "我们先来看艾子引导的定语从句。"
            r["_stats_text"] = None
        if r["id"] == b:   # program judged unusable (low ASR confidence) -> grey row
            r["text"] = "关系代词that不能和借词一起提前。"
            r["asr"] = {"engine": "x", "avg_logprob": -1.6, "no_speech_prob": 0.1}
            r["_stats_text"] = None
        if r["id"] == c:   # ASR step not finished yet (teacher stopped prepare) -> no text
            r["text"] = ""
            r["asr_done"] = False
            r["_stats_text"] = None
    p.save_manifest(rs)
    wf.apply_review(cfg, VOICE, read_csv=False)
    rr = recs(p)
    print("[skipped] before: a keep", rr[a]["keep"], "| b keep", rr[b]["keep"], rr[b]["drop_reason"], "| c keep", rr[c]["keep"], repr(rr[c]["text"]))
    count = A._clips_count_md(cfg, VOICE)
    print("[skipped] count note mentions pending ASR:", "还没有识别出文字" in count)
    print("[skipped] button before:", ui.textfix_btn(VOICE)["interactive"])
    outs = list(ui.do_textfix(VOICE))
    last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
    print("[skipped] after one-click: button interactive =", last["tr_btn"]["interactive"])
    print("[skipped] a text:", cur(p, a)["text"])
    # teacher: grey row b -> "这一条也要用" + save
    msg, _, _ = act(ui, "use", b)
    md, _, _ = ui.do_save(VOICE)
    # prepare re-run finishes ASR on c (what prepare() does: text + asr_done, then filters)
    rs = p.load_manifest()
    for r in rs:
        if r["id"] == c:
            r.update(text="这里的借词后面要接宾语。", lang="zh", asr_done=True)
    p.save_manifest(rs)
    wf.apply_review(cfg, VOICE, read_csv=False)
    rr = recs(p)
    print("[skipped] now: b keep", rr[b]["keep"], "| c keep", rr[c]["keep"])
    print("[skipped] textfix_used =", wf.textfix_used(cfg, VOICE), "| button interactive =", ui.textfix_btn(VOICE)["interactive"])
    print("[skipped] b text:", cur(p, b)["text"], "| c text:", cur(p, c)["text"])
    outs = list(ui.do_textfix(VOICE))
    last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
    print("[skipped] clicking again ->", A.re.sub("<[^>]+>", "", str(last["proof_bar"]))[:120])

# ---------------------------------------------------------------- 3. find + only-suspect filter together
if "findsus" in which:
    cfg, p, ui = fresh("findsus")
    rs = p.load_manifest()
    for r in rs:
        r.pop("suspect", None)
    # one suspect row that does NOT contain the search word
    rs[3]["suspect"] = {"spans": [[0, 2]], "alt": "大伙" + rs[3]["text"][2:], "reasons": ["两次识别不一样"], "score": 0.6}
    p.save_manifest(rs)
    q = "我们"
    hits = [r["id"] for r in rs if q in r["text"]]
    print("[findsus] rows containing", q, ":", len(hits))
    status, count, rows, _ = ui.do_find(VOICE, q, True, True)   # only_sus checked
    shown = [row[1] for row in rows]
    st = A.re.sub("<[^>]+>", "", status)
    print("[findsus] find status:", st[:140])
    print("[findsus] table rows shown:", len(shown), "| current-match id in table:",
          A.re.search(r'data-cur-id="([^"]+)"', status).group(1) in shown)
    # 替换这一处 replaces the orange match that is not visible
    status, count, rows, _ = ui.do_replace_one(VOICE, q, "咱们", True, True)
    print("[findsus] after 替换这一处:", A.re.sub("<[^>]+>", "", status)[:160])
    changed = [k for k in hits if "咱们" in cur(p, k)["text"]]
    print("[findsus] replaced rows:", changed, "| visible:", [k in [row[1] for row in rows] for k in changed])
    print("[findsus] count md:", [l for l in count.split("\n") if "正在查找" in l])

# ---------------------------------------------------------------- 4. confirmed + later unsaved drafts: what the header says
if "confirmdirty" in which:
    cfg, p, ui = fresh("confirmdirty")
    md, count, rows = ui.do_confirm(VOICE)
    i0 = ids(p)[2]
    act(ui, "edit", i0, text="首先我们看一个最最简单的例子。")
    count = A._clips_count_md(cfg, VOICE)
    print("[confirmdirty] header confirmed:", "训练素材已确认" in count, "| unsaved note:", "没有保存" in count)
    print("[confirmdirty] training_blocker:", wf.training_blocker(p)[:60])
