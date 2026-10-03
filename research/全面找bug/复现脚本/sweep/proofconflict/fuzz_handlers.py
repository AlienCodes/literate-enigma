"""Random mixed sequences of proofreading-table features, driven through the real WebUI handlers.

usage: fuzz_handlers.py SEED NSTEP
Checks after every step (see README in the report): no exception, teacher edits not lost, counts consistent,
confirm invalidated after any saved change, deleted rows never in training, one-click lock per batch."""
import random, sys, json, re, traceback, shutil, zlib, os
from pathlib import Path
from common import *  # noqa
from voicetwin.webui import app as A
from voicetwin.data import proofcheck as pc, lexicon_fix as lf
from voicetwin.data.exporters import train_records
from voicetwin.utils.textutil import clean_transcript

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
NSTEP = int(sys.argv[2]) if len(sys.argv) > 2 else 40
rng = random.Random(seed)

# ---------------------------------------------------------------- fake second recognizer for 🔍 自动查找可能的错字
SUBS = "的地得在再做作那哪他她它们门以已像向"


def fake_recognize(self, rec, lang):
    t = str(rec.get("text") or "")
    r2 = random.Random(zlib.crc32(f"{seed}|{rec['id']}|{t}".encode()))
    if not t or r2.random() < 0.4:
        return t, None, "funasr"          # same text: nothing flagged
    i = r2.randrange(len(t))
    other = t[:i] + r2.choice(SUBS) + t[i + 1:]
    return other, None, "funasr"


pc._EngineRunner.recognize = fake_recognize

# ---------------------------------------------------------------- data: base voice with corrupted mother lines
corpus = [x for _, x in tf.builtin_mother() if 10 <= len(x) <= 24]
corr = lf.builtin_corrections()
inv = {}
for k, v in corr.items():
    inv.setdefault(v, []).append(k)


def corrupt(s, n=2):
    for _ in range(n):
        cands = [(v, k) for v, ks in inv.items() for k in ks if v in s]
        if cands and rng.random() < 0.85:
            v, k = rng.choice(cands)
            s = s.replace(v, k, 1)
    return clean_transcript(s)


good = [x for x in corpus if any(v in x for v in inv)]
cfg, p, ui = fresh(f"fz{seed}")
rs = p.load_manifest()
for r in rs:
    if rng.random() < 0.7:
        r["text"] = corrupt(rng.choice(good))
        r["_stats_text"] = None
for r in rs:
    x = rng.random()
    if x < 0.12:
        r["asr"] = {"engine": "x", "avg_logprob": -1.6, "no_speech_prob": 0.1}   # grey: low confidence
    elif x < 0.18:
        r["text"] = ""; r["asr_done"] = False; r["_stats_text"] = None          # ASR not finished
p.save_manifest(rs)
wf.apply_review(cfg, VOICE, read_csv=False)

V = VOICE
deleted_text = {}
probs = []
hist = []
only_sus = False
deleted_model = set(r["id"] for r in p.load_manifest() if r.get("deleted"))
confirmed_sig = None    # (id, text, lang) of material at the last successful confirm
confirmed_sig_nolang = None
typed = {}              # rows the teacher typed: id -> text she typed
textfix_ok_once = False


def strip(s):
    return re.sub(r"<[^>]+>", "", str(s or ""))


def full_view():
    """what every row shows (ignoring find / only-sus filters)."""
    out = {}
    draft = review.load_draft(p)
    conf = bool(review.load_confirmed(p))
    for r in p.load_manifest():
        e = draft.get(r["id"])
        vals = review.current_values(r, e)
        info = review.analyze(r, vals["text"])
        deleted = bool(r.get("deleted"))
        colored = A._colored_html(info)
        sug = "" if deleted or not colored else A._suggest_cell(info)
        out[r["id"]] = dict(text=vals["text"], lang=vals["lang"], keep=vals["keep"], deleted=deleted,
                            colored=colored, sug=sug, dirty=review.is_dirty(r, e) and not deleted,
                            active=info["active"], red=bool(info["red"]), edits=bool(info["edits"]))
    return out


def sig(with_lang=True):
    return sorted((r["id"], r.get("text"), r.get("lang") if with_lang else "") for r in p.load_manifest()
                  if review.is_material(r))


def table():
    return A._clips_table(cfg, V, only_sus)


def shown_ids():
    return [row[1] for row in table()]


def problem(kind, detail):
    probs.append((kind, len(hist), hist[-1] if hist else None, detail))


def check(op, rid, before, after, extra):
    # deleted rows never in training
    tr = {r["id"] for r in train_records(p, include_val=True)}
    for k in deleted_model:
        if k in tr:
            problem("deleted row in training", k)
        if not after[k]["deleted"]:
            problem("deleted row came back", k)
    for k, v in after.items():
        if v["deleted"] and k not in deleted_model:
            problem("row deleted without teacher", k)
    # text changes allowed per op
    changed = {k for k in after if k in before and after[k]["text"] != before[k]["text"]}
    allowed = set()
    if op in ("edit", "adopt", "unadopt", "revert", "use", "lang", "ok", "save_row", "delete", "restore"):
        allowed = {rid}
    elif op == "replace_one":
        allowed = set(extra.get("cands", []))
        if len(changed) > 1:
            problem("replace_one changed >1 rows", sorted(changed))
    elif op == "replace_all":
        allowed = set(extra.get("cands", []))
    elif op == "undo_replace":
        allowed = set(extra.get("undo_rows", []))
    elif op == "textfix":
        allowed = set(extra.get("only", []))
    elif op == "asr_finish":
        allowed = set(extra.get("filled", []))
    if changed - allowed:
        problem(f"{op} changed text of other rows", {k: (before[k]["text"], after[k]["text"]) for k in changed - allowed})
    if op == "textfix":   # rows not in this batch: display must not change at all
        for k in after:
            if k in before and k not in allowed and (after[k]["colored"], after[k]["sug"]) != (before[k]["colored"], before[k]["sug"]):
                problem("textfix changed display of an old-batch row", (k, strip(before[k]["sug"]), strip(after[k]["sug"])))
    if op in ("save", "confirm"):  # display-neutral (except lights)
        for k in after:
            if k in before and (after[k]["text"], after[k]["colored"], after[k]["sug"]) != (before[k]["text"], before[k]["colored"], before[k]["sug"]):
                if not after[k]["deleted"]:
                    problem(f"{op} changed what a row shows", (k, before[k]["text"], strip(before[k]["sug"]), "->",
                                                              after[k]["text"], strip(after[k]["sug"])))
    # teacher's typed text survives ops that do not target the row
    for k, t in list(typed.items()):
        if after[k]["text"] != t:
            if k in allowed or op in ("textfix",):
                typed.pop(k)
            else:
                problem("teacher edit lost", (k, t, after[k]["text"]))
                typed.pop(k)
    # count md consistency
    md = A._clips_count_md(cfg, V)
    m = re.search(r"\*\*(\d+)\*\* 条可能有错", md)
    n_md = int(m.group(1)) if m else 0
    vis = [k for k, v in after.items() if not v["deleted"] and ("vt-red" in v["colored"] or "vt-sug-blue" in v["sug"])]
    act_rows = [k for k, v in after.items() if not v["deleted"] and v["active"]]
    if n_md != len(vis):
        problem("可能有错 N != rows showing red/采用", (n_md, len(vis), sorted(set(act_rows) ^ set(vis))))
        if os.environ.get("DUMP") and not globals().get("_dumped"):
            globals()["_dumped"] = True
            for k in sorted(set(act_rows) ^ set(vis)):
                r = recs(p)[k]
                v = after[k]
                info = review.analyze(r, v["text"])
                print("DUMP row", k, "deleted", v["deleted"], "keep", v["keep"])
                print("DUMP text      :", v["text"])
                print("DUMP saved text:", r.get("text"), "| orig:", r.get("orig_text"))
                print("DUMP suspect   :", json.dumps(r.get("suspect"), ensure_ascii=False))
                print("DUMP info red/edits/undo/blue:", info["red"], info["edits"], info["undo"], info["blue"], info["deleted"])
                print("DUMP colored:", repr(v["colored"]), "| sug:", repr(v["sug"]))
                print("DUMP draft:", review.load_draft(p).get(k))
    m = re.search(r"还有 \*\*(\d+)\*\* 条修改没有保存", md)
    n_uns = int(m.group(1)) if m else 0
    dirty = [k for k, v in after.items() if v["dirty"]]
    if n_uns != len(dirty):
        problem("unsaved N != red lights", (n_uns, len(dirty)))
    # lights in the real table
    rows = A._clips_table(cfg, V, False)
    if not review.load_find(p):
        lit = [row[1] for row in rows if A.LIGHT_DIRTY in row[7]]
        if sorted(lit) != sorted(dirty):
            problem("table red lights != dirty rows", (lit, dirty))
        sus_rows = {row[1] for row in A._clips_table(cfg, V, True)}
        if set(act_rows) - sus_rows:
            problem("只看可能有错的 misses counted rows", sorted(set(act_rows) - sus_rows))
    for row in rows:
        if A.FLAG_DELETED in row[7] and row[6]:
            problem("deleted row has suggestion buttons", row[1])
    # confirm state
    shown_ok = "训练素材已确认" in md
    if confirmed_sig is not None:
        same = sig(True) == confirmed_sig
        same_nolang = sig(False) == confirmed_sig_nolang
        if shown_ok and not same:
            problem("confirm still shown after saved change" + (" (lang only)" if same_nolang else ""), op)
        if not wf.training_blocker(p) and not same:
            problem("training allowed after saved change" + (" (lang only)" if same_nolang else ""), op)
    # one-click lock
    new = tf.textfix_new_ids(p)
    btn = ui.textfix_btn(V)["interactive"]
    if btn != bool(new):
        problem("textfix button state wrong", (btn, new))


def pick(cond, rows=None):
    rows = table() if rows is None else rows
    c = [row for row in rows if cond(row)]
    return rng.choice(c) if c else None


def mutate(t):
    if not t:
        return "这是老师自己打上去的一句话。"
    i = rng.randrange(len(t))
    k = rng.random()
    if k < 0.4:
        return t[:i] + rng.choice("我你他好的了在是有和") + t[i + 1:]
    if k < 0.7:
        return t[:i] + rng.choice("呢吧啊嘛") + t[i:]
    return (t[:i] + t[i + 1:]) or t + "啊"


add_k = 0
OPS = ["textfix", "textfix", "proofcheck", "adopt", "adopt", "unadopt", "ok", "edit", "edit", "revert", "delete",
       "restore", "use", "lang", "save", "save_row", "confirm", "confirm", "find", "find_next", "replace_one",
       "replace_all", "undo_replace", "find_close", "download", "only_sus", "add_material", "asr_finish", "use", "use"]
for step in range(NSTEP):
    op = rng.choice(OPS)
    global_ok = textfix_ok_once
    before = full_view()
    rid = None
    extra = {}
    try:
        if op == "textfix":
            extra["only"] = tf.textfix_new_ids(p)
            was = ui.textfix_btn(V)["interactive"]
            outs = list(ui.do_textfix(V, None, only_sus))
            last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
            if was and "完成" not in strip(last["proof_md"]):
                problem("textfix did not finish", strip(last["proof_md"])[:200] + strip(last["proof_bar"])[:200])
            if was and tf.textfix_new_ids(p):
                problem("after textfix there are still new ids", tf.textfix_new_ids(p))
            if not was:
                extra["only"] = []
            else:
                textfix_ok_once = True
            ui.refresh_clips(V, only_sus)
        elif op == "proofcheck":
            outs = list(ui.do_proofcheck(V, only_sus))
            last = dict(zip(ui.PROOF_OUT, outs[-1]))
            if "检查完了" not in strip(last["proof_md"]):
                problem("proofcheck did not finish", strip(last["proof_md"])[:300])
            m1 = re.search(r"其中 \*\*(\d+)\*\* 条可能有错", last["proof_md"])
            m2 = re.search(r"\*\*(\d+)\*\* 条可能有错", last["clips_count"])
            n1, n2 = int(m1.group(1)) if m1 else 0, int(m2.group(1)) if m2 else 0
            if n1 != n2:
                problem("proofcheck says N, header says M", (n1, n2))
            ui.refresh_clips(V, only_sus)
        elif op == "adopt":
            row = pick(lambda r: "vt-sug-blue" in r[6] and A.FLAG_DELETED not in r[7])
            if row is None:
                continue
            rid = row[1]
            msg, _, _ = act(ui, "adopt", rid, only_sus)
        elif op == "unadopt":
            row = pick(lambda r: "vt-sug-red" in r[6] and A.FLAG_DELETED not in r[7])
            if row is None:
                continue
            rid = row[1]
            msg, _, _ = act(ui, "unadopt", rid, only_sus)
        elif op == "ok":
            row = pick(lambda r: "vt-red" in r[5] and A.FLAG_DELETED not in r[7])
            if row is None:
                continue
            rid = row[1]
            act(ui, "ok", rid, only_sus)
        elif op == "edit":
            row = pick(lambda r: A.FLAG_DELETED not in r[7])
            if row is None:
                continue
            rid = row[1]
            t = clean_transcript(mutate(before[rid]["text"]))
            if not t:
                continue
            msg, _, _ = act(ui, "edit", rid, only_sus, text=t)
            typed[rid] = review.current_values(recs(p)[rid], review.load_draft(p).get(rid))["text"]
            extra["t"] = t
        elif op == "revert":
            row = pick(lambda r: A.LIGHT_DIRTY in r[7])
            if row is None:
                continue
            rid = row[1]
            act(ui, "revert", rid, only_sus)
        elif op == "delete":
            row = pick(lambda r: A.FLAG_DELETED not in r[7])
            if row is None:
                continue
            rid = row[1]
            act(ui, "delete", rid, only_sus)
            deleted_model.add(rid)
            deleted_text[rid] = before[rid]["text"]
            typed.pop(rid, None)
        elif op == "restore":
            row = pick(lambda r: A.FLAG_DELETED in r[7])
            if row is None:
                continue
            rid = row[1]
            act(ui, "restore", rid, only_sus)
            deleted_model.discard(rid)
            if rid in deleted_text and cur(p, rid)["text"] != deleted_text[rid]:
                problem("restore lost the row's text", (rid, deleted_text[rid], cur(p, rid)["text"]))
        elif op == "use":
            row = pick(lambda r: A.FLAG_UNUSED in r[7])
            if row is None:
                continue
            rid = row[1]
            act(ui, "use", rid, only_sus)
        elif op == "lang":
            row = pick(lambda r: A.FLAG_DELETED not in r[7])
            if row is None or rng.random() < 0.5:
                continue
            rid = row[1]
            act(ui, "lang", rid, only_sus)
        elif op == "save":
            ui.do_save(V, None, only_sus)
        elif op == "save_row":
            row = pick(lambda r: A.LIGHT_DIRTY in r[7])
            if row is None:
                continue
            rid = row[1]
            act(ui, "save_row", rid, only_sus)
        elif op == "confirm":
            md, _, _ = ui.do_confirm(V, only_sus)
            if "训练素材已确认" in md:
                confirmed_sig, confirmed_sig_nolang = sig(True), sig(False)
        elif op == "find":
            words = [w for v in before.values() if not v["deleted"] for w in re.findall(r"[一-鿿]{2}", v["text"])]
            if not words:
                continue
            q = rng.choice(words)
            ui.do_find(V, q, True, only_sus)
        elif op == "find_next":
            ui.do_find_move(V, 1, only_sus)
        elif op == "replace_one":
            f = review.load_find(p)
            if not f:
                continue
            ms = review.find_matches(p, f["q"], f.get("word", True))
            extra["cands"] = sorted({m[0] for m in ms})
            ui.do_replace_one(V, f["q"], rng.choice(["", "某某", f["q"][:1]]), f.get("word", True), only_sus)
        elif op == "replace_all":
            f = review.load_find(p)
            if not f:
                continue
            ms = review.find_matches(p, f["q"], f.get("word", True))
            extra["cands"] = sorted({m[0] for m in ms})
            ui.do_replace_all(V, f["q"], rng.choice(["某某", f["q"][:1]]), f.get("word", True), only_sus)
        elif op == "undo_replace":
            try:
                extra["undo_rows"] = list(json.loads((p.root / review.UNDO_FILE).read_text("utf-8"))["rows"])
            except (OSError, ValueError, KeyError):
                extra["undo_rows"] = []
            try:
                undo_data = json.loads((p.root / review.UNDO_FILE).read_text("utf-8"))["rows"]
            except (OSError, ValueError, KeyError):
                undo_data = {}
            st, _, _, _ = ui.do_undo_replace(V, only_sus)
            mk = re.search(r"另有 (\d+) 句替换以后又改过", strip(st))
            if mk:
                really = [k for k, e in undo_data.items() if k in before and not before[k]["deleted"]
                          and before[k]["text"] not in (e.get("after"), e.get("text"))]
                dele = [k for k in undo_data if k in before and before[k]["deleted"]]
                if int(mk.group(1)) != len(really) + len(dele):
                    problem("undo-replace 'kept' count wrong", (int(mk.group(1)), len(really), len(dele)))
        elif op == "asr_finish":
            rs = p.load_manifest()
            emp = [r for r in rs if not str(r.get("text") or "").strip() and not r.get("deleted")]
            if not emp:
                continue
            extra["filled"] = [r["id"] for r in emp]
            for r in emp:
                r.update(text=corrupt(rng.choice(good)), asr_done=True, lang="zh")
            p.save_manifest(rs)
            wf.apply_review(cfg, V, read_csv=False)
            ui.after_prepare_clips(V, only_sus, None, {"voice": V})
            mat = [r["id"] for r in p.load_manifest() if r["id"] in {e["id"] for e in emp} and review.is_material(r)]
            if mat and not tf.textfix_new_ids(p) and textfix_ok_once:
                problem("rows recognised later can never get one-click", mat)
        elif op == "find_close":
            ui.do_find_close(V, only_sus)
        elif op == "download":
            o = ui.do_download_text(V)
            d = dict(zip(ui.DLTXT_OUT, o))
            path = d["dl_txt_file"].get("value")
            if path:
                lines = Path(path).read_bytes().decode("utf-8-sig").split("\r\n")[:-1]
                want = [re.sub(r"\s+", " ", v["text"]).strip() for v in before.values() if not v["deleted"] and v["text"].strip()]
                if lines != want:
                    problem("download != table texts", (len(lines), len(want)))
        elif op == "only_sus":
            only_sus = not only_sus
            ui.refresh_clips(V, only_sus)
        elif op == "add_material":
            rs = p.load_manifest()
            src = rng.choice(rs)
            add_k += 1
            new = []
            for j in range(rng.choice([1, 2, 3])):
                nid = f"新课_{seed}_{add_k}_{j}"
                dst = p.root / "clips" / f"{nid}.wav"
                shutil.copyfile(p.abspath(src["path"]), dst)
                rec = {k: v for k, v in src.items() if k not in ("suspect", "suspect_auto", "suspect_ok", "orig_text",
                                                                    "text_edited", "edited", "edited_at", "deleted",
                                                                    "before_delete", "manual_keep", "split", "_stats_text")}
                rec.update(id=nid, path=f"clips/{nid}.wav", text=corrupt(rng.choice(good)))
                new.append(rec)
            p.save_manifest(rs + new)
            wf.apply_review(cfg, V, read_csv=False)
            ui.after_prepare_clips(V, only_sus, None, {"voice": V})
            extra["added"] = [r["id"] for r in new]
            if not tf.textfix_new_ids(p) and any(review.is_material(r) for r in p.load_manifest() if r["id"] in extra["added"]):
                problem("new material did not light one-click", extra["added"])
    except Exception as exc:  # noqa
        hist.append((step, op, rid))
        problem("exception", traceback.format_exc()[-1500:])
        continue
    hist.append((step, op, rid))
    after = full_view()
    try:
        check(op, rid, before, after, extra)
    except Exception:
        problem("checker crashed", traceback.format_exc()[-800:])

seen = {}
for kind, n, h, d in probs:
    seen.setdefault(kind, []).append((n, h, d))
print(f"seed {seed}: {len(hist)} steps, {len(probs)} problems")
for kind, items in seen.items():
    print(f"  [{kind}] x{len(items)}; first at step {items[0][0]} after {items[0][1]}: {str(items[0][2])[:600]}")
print("  ops:", " ".join(f"{h[1]}" for h in hist))
shutil.rmtree(Path(cfg.get('workspace')).parent, ignore_errors=True)
