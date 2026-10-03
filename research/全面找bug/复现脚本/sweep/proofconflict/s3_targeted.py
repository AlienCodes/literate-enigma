"""undo-replace message after a row was already reverted; proofcheck message vs header count; proofcheck after saving one-click."""
import sys, re, zlib, random
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc

which = sys.argv[1:] or ["undomsg", "proofcount", "proofundo"]
strip = lambda s: re.sub("<[^>]+>", "", str(s or ""))


def ids(p):
    return [r["id"] for r in p.load_manifest()]


if "undomsg" in which:
    cfg, p, ui = fresh("undomsg")
    ui.do_find(VOICE, "我们", True, False)
    st, _, _, _ = ui.do_replace_all(VOICE, "我们", "咱们", True, False)
    print("[undomsg] replace all:", strip(st)[-90:])
    rid = [k for k in ids(p) if "咱们" in cur(p, k)["text"]][0]
    msg, _, _ = act(ui, "revert", rid)        # ⋯ 选项 → 撤销这一行的修改
    print("[undomsg] revert one row:", msg, "| text now:", cur(p, rid)["text"])
    st, _, _, _ = ui.do_undo_replace(VOICE, False)
    print("[undomsg] undo replace says:", strip(st).split("<br>")[-1][-160:])
    print("[undomsg] that row text:", cur(p, rid)["text"])

if "proofcount" in which:
    cfg, p, ui = fresh("proofcount")
    rs = p.load_manifest()
    target = rs[2]["id"]   # 首先我们看一个最简单的例子。

    def rec2(self, rec, lang):
        t = str(rec.get("text") or "")
        if rec["id"] == target:
            return t.replace("例子", "栗子"), None, "funasr"
        return t, None, "funasr"

    pc._EngineRunner.recognize = rec2
    # the teacher already retyped that word herself (unsaved draft) before running the check
    act(ui, "edit", target, text="首先我们看一个最简单的栗子。")
    outs = list(ui.do_proofcheck(VOICE, False))
    last = dict(zip(ui.PROOF_OUT, outs[-1]))
    print("[proofcount] proofcheck message:", strip(last["proof_md"]).splitlines()[0])
    m = re.search(r"\*\*(\d+)\*\* 条可能有错", last["clips_count"])
    print("[proofcount] header count:", m.group(0) if m else "(no 可能有错 line)")
    count, rows = ui.refresh_clips(VOICE, True)
    print("[proofcount] rows in 只看可能有错的:", [(r[0], strip(r[4]), strip(r[5]), strip(r[6])) for r in rows])

if "proofundo" in which:
    cfg, p, ui = fresh("proofundo")
    rs = p.load_manifest()
    a = rs[1]["id"]
    for r in rs:
        r.pop("suspect", None)
    rs[1]["text"] = "我们先来看艾子引导的定语从句。"
    p.save_manifest(rs)
    list(ui.do_textfix(VOICE))
    rows = A._clips_table(cfg, VOICE)
    row = [r for r in rows if r[1] == a][0]
    print("[proofundo] after one-click:", cur(p, a)["text"], "| suggest:", strip(row[6]))
    ui.do_save(VOICE)
    row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
    print("[proofundo] after save: suggest:", strip(row[6]))

    def same(self, rec, lang):
        return str(rec.get("text") or ""), None, "funasr"

    pc._EngineRunner.recognize = same
    list(ui.do_proofcheck(VOICE, False))
    row = [r for r in A._clips_table(cfg, VOICE) if r[1] == a][0]
    print("[proofundo] after 🔍 自动查找: text", cur(p, a)["text"], "| colored:", strip(row[5]), "| suggest:", repr(strip(row[6])))
