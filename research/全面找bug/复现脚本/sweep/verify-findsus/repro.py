"""Independent repro: 查找 / 替换 while 「只看可能有错的」 is ticked (quick-start step 3 then step 5)."""
import sys, re, shutil, tempfile
from pathlib import Path
ROOT = "/home/user/literate-enigma"
sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.data import review
import voicetwin.webui.app as A

TMP = Path(tempfile.mkdtemp(dir=str(Path(__file__).parent)))
def strip(s): return re.sub("<[^>]+>", "", s or "")

def make(name, texts, sus):
    cfg = make_cfg(TMP / name / "ws")
    p = wf.Project(cfg, "v").ensure()
    recs = []
    for i, t in enumerate(texts):
        r = {"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh", "duration": 3.0,
             "keep": True, "split": "train"}
        if i in sus:
            s0, s1, alt = sus[i]
            r["suspect"] = {"spans": [[s0, s1]], "alt": alt, "reasons": ["两次识别不一样"], "score": 0.6}
        recs.append(r)
    p.save_manifest(recs)
    return cfg, p

def cur_text(p, rid):
    rec = {r["id"]: r for r in p.load_manifest()}[rid]
    return review.current_values(rec, review.load_draft(p).get(rid))["text"]

def show(tag, status, count, rows):
    m = re.search(r'data-cur-id="([^"]+)"', status or "")
    cid = m.group(1) if m else None
    ids = [r[1] for r in rows]
    print(f"  [{tag}] status : {strip(status)[:170]}")
    print(f"  [{tag}] header : {[l for l in count.split(chr(10)) if '正在查找' in l]}")
    print(f"  [{tag}] table ids: {ids} | current match id={cid} visible={cid in ids if cid else None}")
    return ids, cid

# ---------- Scenario A: documented flow. Some 艾子 rows were flagged by 自动查找, some were not.
print("=== Scenario A: 艾子 in 3 rows, only c000 is flagged red; teacher has 只看可能有错的 ticked ===")
cfg, p = make("A", ["我们先来看艾子引导的定语从句。", "艾子在这里是关系代词。", "这一句里也有艾子。",
                    "大家今天天气很好。", "没有那个词。", "普通的一句话。"],
               {0: (5, 7, "我们先来看as引导的定语从句。"), 3: (0, 2, "大伙今天天气很好。")})
ui = A.WebUI(cfg)
_, rows = ui.load_clips("v", True)
print("  only_sus table before find:", [r[1] for r in rows])
st, cnt, rows, _ = ui.do_find("v", "艾子", True, True)
show("find", st, cnt, rows)
st, cnt, rows, _ = ui.do_find_move("v", 1, True)
ids, cid = show("next", st, cnt, rows)
before = cur_text(p, cid)
st, cnt, rows, _ = ui.do_replace_one("v", "艾子", "as", True, True)
ids2, _ = show("replace-one", st, cnt, rows)
print(f"  row {cid}: before='{before}' after='{cur_text(p, cid)}' (was it visible when replaced? {cid in ids})")
# unchecking the box during find (gradio .change -> refresh_clips)
_, rows = ui.refresh_clips("v", False)
print("  after un-ticking only_sus while find active:", [r[1] for r in rows])

# ---------- Scenario B: reporter's case: search word only in non-flagged rows
print("\n=== Scenario B: 我们 only in non-flagged rows; only c003 flagged ===")
cfg, p = make("B", ["我们先来看定语从句。", "我们再看一个例子。", "我们今天讲as。", "大家今天天气很好。"],
               {3: (0, 2, "大伙今天天气很好。")})
ui = A.WebUI(cfg)
st, cnt, rows, _ = ui.do_find("v", "我们", True, True)
ids, cid = show("find", st, cnt, rows)
st, cnt, rows, _ = ui.do_replace_one("v", "我们", "咱们", True, True)
show("replace-one", st, cnt, rows)
print(f"  {cid} now: '{cur_text(p, cid)}' (was visible before replace: {cid in ids})")

# ---------- Scenario C: same as A with only_sus=False (control)
print("\n=== Control: Scenario A data, 只看可能有错的 NOT ticked ===")
cfg, p = make("C", ["我们先来看艾子引导的定语从句。", "艾子在这里是关系代词。", "这一句里也有艾子。",
                    "大家今天天气很好。", "没有那个词。", "普通的一句话。"],
               {0: (5, 7, "我们先来看as引导的定语从句。"), 3: (0, 2, "大伙今天天气很好。")})
ui = A.WebUI(cfg)
st, cnt, rows, _ = ui.do_find("v", "艾子", True, False)
show("find", st, cnt, rows)

shutil.rmtree(TMP, ignore_errors=True)
