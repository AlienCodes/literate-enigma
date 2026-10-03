"""随机操作：自动查错字（find_suspects）和老师的各种操作、一键全部文字校正（每批一次）穿插着做。
每次「🔍 自动查找」以后检查：
  A 没保存的修改（草稿）一个字都没变（查错字不能改老师的字）
  B 红字不落在改过的字（蓝 / 绿）上
  C 「其中 M 条可能有错」的 M = 表格里真的「可能有错」的行数
  D 「这句没错」的行（文字没再改过）不标红
  E 查之前有「已采用」（可以撤销）的行，查完还能撤销
  F 查之前标准库（一键校正）给的建议，查完还在
  G 马上再查一次，校对表一模一样（点两次结果一样）
  H 任何时候 analyze / 表格不报错
用法：python fuzz_auto.py 种子数"""
import json, random, sys, traceback, collections
from common import *

BASE = ["我们今天讲十个函数，十个函数很重要", "这个主剧的结构也很完整", "小明昨天说借词后面接名词",
        "我们先来看艾子引导的定语从句", "那么到底什么是定语从句呢", "下面我们来看第二个例子",
        "我们一起来看看这个从剧的结构", "我们用Excel的VLOOKUP函数查一下", "who引导的定语从句修饰人",
        "今天天气很好我们去公园"]
HEARD = {0: "我们今天讲是个函数，是个函数很重要", 1: "这个主剧的结构也很完成", 2: "小明昨天说借词后面接名词",
         3: "我们先来看a子引导的定语从句", 4: "那么到底什么是定语从句呢", 5: "下面我们来看第二个列子",
         6: "我们一起来看看这个从句的结构", 7: "我们用一克塞尔的VLOOKUP函数查一下", 8: "户引导的定语从句修饰人",
         9: "今天天气很好我们去公园"}
CH = "的了是在有我他这个们中来上大为和国地到以说时要就出会可也你对生能而子那得于着下自之年过发后作里用道行所然家种事成方多经么去法学如都同现当没动面起看定天分还进好小部其些主样理心她本前开但因只从想实"
viol = collections.Counter()
examples = {}


def note(k, msg):
    viol[k] += 1
    examples.setdefault(k, msg)


def state(project):
    draft = review.load_draft(project)
    out = {}
    for r in project.load_manifest():
        t = review.current_values(r, draft.get(r["id"]))["text"]
        info = review.analyze(r, t)
        out[r["id"]] = (r, t, info, draft.get(r["id"]))
    return out


def run(seed):
    rnd = random.Random(seed)
    texts = [rnd.choice(BASE) for _ in range(6)]
    cfg, project = voice(texts)
    ids = [r["id"] for r in project.load_manifest()]
    heard = {i: HEARD[BASE.index(t)] for i, t in zip(ids, texts)}
    fake_engine(heard)
    hist = []
    for step in range(14):
        op = rnd.choice(["edit", "adopt", "unadopt", "revert", "save", "dismiss", "auto", "auto", "oneclick",
                         "replace", "undo_replace", "save_row"])
        rid = rnd.choice(ids)
        hist.append((op, rid))
        try:
            st = state(project)
            r, t, info, entry = st[rid]
            if op == "edit":
                k = rnd.randrange(len(t))
                kind = rnd.random()
                if kind < 0.4:
                    new = t[:k] + rnd.choice(CH) + t[k + 1:]
                elif kind < 0.7:
                    new = (t[:k] + t[k + 1:]) or t
                else:
                    new = t[:k] + t[k:k + 2] + t[k:]  # 重复两个字（像口误）
                review.set_draft(project, rid, text=new)
            elif op == "adopt" and info["edits"]:
                review.adopt_suggestion(project, rid)
            elif op == "unadopt" and info["undo"]:
                review.unadopt_suggestion(project, rid)
            elif op == "revert":
                review.discard_draft(project, rid)
            elif op == "save":
                review.save_rows(project)
            elif op == "save_row":
                review.save_rows(project, [rid])
            elif op == "dismiss":
                pc.dismiss_suspect(project, rid)
            elif op == "oneclick":
                try:
                    wf.run_transcript_fix(cfg, "v", once=True)
                except ValueError:
                    pass
            elif op == "replace":
                q = rnd.choice(["函数", "定语", "我们", "结构"])
                review.replace_matches(project, q, rnd.choice(["方法", "状语", "咱们", "结构体"]), whole_word=False)
            elif op == "undo_replace":
                review.undo_replace(project)
            elif op == "auto":
                before = st
                draft_before = json.dumps(review.load_draft(project), sort_keys=True, ensure_ascii=False)
                res = pc.find_suspects(project, cfg)
                after = state(project)
                if json.dumps(review.load_draft(project), sort_keys=True, ensure_ascii=False) != draft_before:
                    note("A", (seed, list(hist)))
                active = 0
                for i2, (r2, t2, inf2, e2) in after.items():
                    if not r2.get("keep", True) or r2.get("deleted"):
                        continue
                    if inf2["active"]:
                        active += 1
                    blue = {k for s, e in inf2["blue"] for k in range(s, e)}
                    if any(k in blue for s, e in inf2["red"] for k in range(s, e)):
                        note("B", (seed, list(hist), i2, t2, inf2["red"], inf2["blue"]))
                    if r2.get("suspect_ok") == t2 and inf2["active"]:
                        note("D", (seed, list(hist), i2, t2))
                    rej = review.load_rejected(project).get(i2)
                    if any(review.is_rejected(rej, t2, *ed) for ed in inf2["edits"]):
                        note("I:rejected-suggested-again", (seed, list(hist), i2, t2, rej))
                    b = before[i2]
                    if b[2]["undo"] and not inf2["undo"]:
                        kind = ("transcript" if (b[0].get("suspect") or {}).get("src") == "transcript" else "auto") + \
                               ("+dirty" if review.is_dirty(b[0], b[3]) else "+saved")
                        note("E:" + kind, (seed, list(hist), i2, b[1], b[2]["undo"]))
                    if (b[0].get("suspect") or {}).get("src") == "transcript" and b[2]["edits"] and not inf2["edits"]:
                        note("F", (seed, list(hist), i2, b[1], b[2]["edits"]))
                if res["flagged"] != active:
                    why = []
                    for i2, (r2, t2, inf2, e2) in after.items():
                        if inf2["active"] or not r2.get("keep", True):
                            continue
                        s2 = r2.get("suspect") or {}
                        if s2.get("src") == "transcript" and r2.get("suspect_auto"):
                            why.append("hidden-in-suspect_auto")
                        elif s2 and review.is_dirty(r2, e2):
                            why.append("masked-by-unsaved-edit")
                        elif s2:
                            why.append("other:" + i2)
                    note("C:" + "+".join(sorted(set(why))), (seed, list(hist), res["flagged"], active))
                m1 = project.manifest_path.read_text(encoding="utf-8")
                pc.find_suspects(project, cfg)
                if project.manifest_path.read_text(encoding="utf-8") != m1:
                    note("G", (seed, list(hist)))
            # 表格（网页里真的会算的）不报错
            state(project)
        except (ValueError, KeyError) as exc:
            if not isinstance(exc, ValueError):
                note("H", (seed, list(hist), repr(exc)))
        except Exception as exc:  # noqa
            note("H", (seed, list(hist), traceback.format_exc()[-400:]))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    for s in range(start, start + n):
        run(s)
        common._cleanup() if hasattr(common := __import__("common"), "_cleanup") else None
        common._tmps.clear()
    print("violations:", dict(viol))
    for k, v in sorted(examples.items()):
        print("==", k, ":", str(v)[:900])
