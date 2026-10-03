"""More targeted conflicts: manual language lost after a text change; edit during one-click; stale one-click button."""
import sys, json, threading, time, re
from common import *  # noqa
from voicetwin.webui import app as A

which = sys.argv[1:] or ["langlost", "editduring", "stalebtn"]


def ids(p):
    return [r["id"] for r in p.load_manifest()]


if "langlost" in which:
    cfg, p, ui = fresh("langlost")
    rs = p.load_manifest()
    rid = rs[4]["id"]   # "Next, let's look at a slightly more complex example."
    # a mostly-English sentence with one Chinese term: detect_lang says zh, the teacher sets 英文 by double-click
    rs[4]["text"] = "Next, let's look at the 定语 clause example."
    rs[4]["lang"] = "zh"
    p.save_manifest(rs)
    act(ui, "lang", rid)
    ui.do_save(VOICE)
    print("[langlost] after teacher set language + save:", recs(p)[rid]["lang"])
    # later: she fixes one word by double-click editing the text
    act(ui, "edit", rid, text="Next, let's look at the 定语 clause examples.")
    print("[langlost] draft lang after a text edit:", cur(p, rid)["lang"])
    md, _, rows = ui.do_save(VOICE)
    print("[langlost] save message:", md.splitlines()[0])
    print("[langlost] saved lang now:", recs(p)[rid]["lang"])
    # same with 全部替换
    act(ui, "lang", rid)
    ui.do_save(VOICE)
    print("[langlost] teacher sets 英文 again:", recs(p)[rid]["lang"])
    ui.do_find(VOICE, "clause", True, False)
    ui.do_replace_all(VOICE, "clause", "Clause", True, False)
    print("[langlost] draft lang after 全部替换 clause->Clause:", cur(p, rid)["lang"])

if "editduring" in which:
    cfg, p, ui = fresh("editduring")
    rs = p.load_manifest()
    a, b = rs[1]["id"], rs[2]["id"]
    for r in rs:
        r.pop("suspect", None)
    rs[1]["text"] = "我们先来看艾子引导的定语从句。"
    rs[2]["text"] = "关系代词that不能和借词一起提前。"
    p.save_manifest(rs)
    real = tf.check_text
    started = threading.Event()

    def slow(*a_, **k_):
        started.set()
        time.sleep(0.15)
        return real(*a_, **k_)

    tf.check_text = slow
    out = {}
    th = threading.Thread(target=lambda: out.setdefault("r", list(ui.do_textfix(VOICE))))
    th.start()
    started.wait(30)
    time.sleep(0.2)
    # while the one-click runs (the button is busy), the teacher double-clicks row b and adds a word at the end
    msg, _, _ = act(ui, "edit", b, text="关系代词that不能和借词一起提前呢。")
    print("[editduring] teacher edit during one-click:", msg)
    th.join()
    tf.check_text = real
    last = dict(zip(ui.TEXTFIX_OUT, out["r"][-1]))
    print("[editduring] result:", re.sub("<[^>]+>", "", last["proof_md"]).splitlines()[0])
    print("[editduring] a:", cur(p, a)["text"])
    print("[editduring] b:", cur(p, b)["text"])
    print("[editduring] textfix_used:", wf.textfix_used(cfg, VOICE), "button:", ui.textfix_btn(VOICE)["interactive"])

if "stalebtn" in which:
    cfg, p, ui = fresh("stalebtn")
    rid = ids(p)[5]
    act(ui, "delete", rid)
    outs = list(ui.do_textfix(VOICE))
    last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
    print("[stalebtn] after one-click: button", last["tr_btn"]["interactive"])
    res = act(ui, "restore", rid)
    print("[stalebtn] restore handler returns", len(res), "outputs (msg, count, table) -> no button update")
    print("[stalebtn] backend now says used =", wf.textfix_used(cfg, VOICE), "| new ids:", tf.textfix_new_ids(p))
    print("[stalebtn] info text still says locked:", "只能用一次" in ui.textfix_info(VOICE))
