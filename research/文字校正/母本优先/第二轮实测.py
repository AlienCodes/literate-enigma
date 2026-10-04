"""母本优先第二轮实测（两位检查的人 10-04 提的 11 条）：在第一轮（实测.py）的三种情况上加了几种第一轮没考到的情况。

第一轮只考了「同一批讲课」和「完全没关系的新内容」，两位检查的人发现中间这一块没考到、出了问题：
  1. 新讲的课用了母本里的说法、只换了一个词（定语从句 → 状语从句、可以 → 不可以、两个 → 三个、which → that……）：
     旧的做法把它改回母本的写法（意思都反了）；
  2. 讲的时候换了个说法（那么 → 那、我们 → 咱们、少说一个「就是」）：也被改成母本的写法；
  3. 母本里的一句后面 / 前面跟着几个母本里没有的字（「……不一样。今天我们」）：被改成母本下一句 / 上一句的字；
  4. 母本里的一句和一句新的话在同一个片段里：母本那一句的识别错有一部分没改；
  5. 一句切在任意一个字中间（不在逗号处）：几句对的被加上 / 去掉了标点。

这一轮的三种情况（和第一轮一样的数据：母本_原文.csv 当识别出来的文字，母本_修缮后.csv 是正确答案）：
  A：片段 id 和母本一样；B：id 全变；C：id 全变 + 切的位置不一样（两句 / 三句合成一句、在逗号处切开、
     在字中间切开），C 里还有一部分句子前后加了母本里没有的几个字、或者和一句新的话放在同一个片段里（上面的 3、4）。
每种情况后面再接一段「新讲的课」（另一个视频，片段是新的）：
  - 新内容：第一轮的 40 句（和母本没关系）；
  - 换了一个词的母本句子（上面的 1，按下面 SWAPS 每种挑几句）：一个字都不应该被直接改（最多给「没把握」的建议）；
  - 换了说法的母本句子（上面的 2）：同样；
  - 「同一份讲稿又讲了一遍」：母本里连着的 18 句照着讲，每三句换一个词（如实记下结果：前后几句都和母本连着对上，
    程序会当成同一批录音——这是这种做法分不出来的情况）。
第二个识别引擎（假的）和第一轮一样，另外在新讲的课里 20% 的句子上听错一个词（定语 → 定位……）。

流程：自动查错字 → 量 → 一键校正（once=True）→ 量 → 再点 🔍 → 量。

运行：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/第二轮实测.py <名字> [A B C]
  环境变量 VT_CODE=<另一份代码的文件夹>：用那份代码量（量修改以前的版本时用，数据还是这个仓库里的）。
结果写到同一个文件夹的 第二轮结果_<名字>.txt / .json。
"""

import csv
import difflib
import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CODE = Path(os.environ.get("VT_CODE") or ROOT)
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(HERE))

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.data import proofcheck as pc  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.data import transcript_fix as tf  # noqa: E402
from voicetwin.data.lexicon_fix import has_jieba  # noqa: E402
from voicetwin.utils.textutil import clean_transcript  # noqa: E402

from 实测 import NEW_CONTENT, OTHER_WRONG, WRONG_FOR_RIGHT, _comma_cut  # noqa: E402

D = ROOT / "research" / "文字校正" / "老师的母本"
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}

#: 新讲的课换掉的一个词（讲下一种从句时会这么说；否定、数字、前后、英文例句里的词）
SWAPS = [("定语从句", "状语从句"), ("定语从句", "宾语从句"), ("关系代词", "关系副词"), ("关系代词", "连接代词"),
         ("先行词", "主句"), ("非限定性", "限定性"), ("限定性定语", "非限定性定语"), ("可以", "不可以"),
         ("能够", "不能够"), ("一个", "两个"), ("两个", "三个"), ("第一", "第二"), ("前面", "后面"),
         ("主语", "宾语"), ("翻译成中文", "翻译成英文"), ("Tom", "Lucy")]
#: 讲的时候换的说法
SPOKEN = [("那么", "那"), ("就是", "是"), ("的话", ""), ("其实", ""), ("我们", "咱们"), ("这个", "那个")]
#: 句子后面 / 前面多出来的、母本里没有的几个字
TAILS = ["好，那我们", "今天我们", "下面我们来看", "所以我们", "然后呢我们"]
HEADS = ["今天的", "好，", "那你看", "大家注意"]
CONTROL_KINDS = ("new", "near", "spoken", "reteach_swap", "reteach_plain")


def norm(s):
    return clean_transcript(str(s or ""))


def _video(rid):
    return rid.rsplit("_", 1)[0]


def _nopunct_cut(t, c):
    """在两边都没改过的地方、两个汉字中间切开（不在标点处：识别引擎在停顿处切），尽量靠中间，两边都至少 6 个字。"""
    best = None
    for tag, i1, i2, j1, _j2 in difflib.SequenceMatcher(None, t, c, autojunk=False).get_opcodes():
        if tag != "equal":
            continue
        for p in range(i1 + 1, i2):
            if p >= 6 and len(t) - p >= 6 and "一" <= t[p - 1] <= "鿿" and "一" <= t[p] <= "鿿":
                score = abs(p - len(t) / 2)
                if best is None or score < best[0]:
                    best = (score, p, j1 + (p - i1))
    if best is None:
        return None
    _s, p, q = best
    return (t[:p], t[p:]), (c[:q], c[q:])


def _row(rid, text, truth, keep=True, dele=False, tag="", source="", kind=None):
    if kind is None:
        kind = "same" if norm(text) == norm(truth) else "diff"
    return {"id": rid, "text": text, "truth": truth, "kind": kind, "keep": keep, "dele": dele, "tag": tag,
            "source": source}


def _pick(pool, old, new, n, seen):
    out = []
    for t in pool:
        if t in seen or t.count(old) != 1 or not (14 <= len(t) <= 70):
            continue
        if old.isascii() and old.isalpha():
            k = t.find(old)
            if (k > 0 and t[k - 1].isascii() and t[k - 1].isalpha()) or \
                    (k + len(old) < len(t) and t[k + len(old)].isascii() and t[k + len(old)].isalpha()):
                continue
        x = t.replace(old, new, 1)
        if x in CLEAN.values():
            continue  # 换完正好是母本里的另一句：不算新的话
        out.append(x)
        seen.add(t)
        if len(out) >= n:
            break
    return out


def controls():
    """新讲的课（接在最后，另一个视频）。"""
    pool = [CLEAN[r["id"]] for r in ORIG if r["keep"] == "1" and r["drop_reason"] != "老师删除"]
    random.Random(7).shuffle(pool)  # 固定的打乱（每次一样）：新讲的课里挨着的句子不会正好是母本里挨着的句子
    seen = set()
    rows = []
    for n, t in enumerate(NEW_CONTENT):
        rows.append(_row(f"0200_newnew_{n:04d}", t, t, kind="new", source="新课_1"))
    near = [x for old, new in SWAPS for x in _pick(pool, old, new, 4, seen)]
    for n, t in enumerate(near):
        rows.append(_row(f"0201_nearnr_{n:04d}", t, t, kind="near", source="新课_2"))
    spoken = [x for old, new in SPOKEN for x in _pick(pool, old, new, 4, seen)]
    for n, t in enumerate(spoken):
        rows.append(_row(f"0202_spokn_{n:04d}", t, t, kind="spoken", source="新课_3"))
    # 同一份讲稿又讲了一遍：母本里连着的 18 句，每三句换一个词
    base = [CLEAN[r["id"]] for r in ORIG[600:640] if r["keep"] == "1" and r["drop_reason"] != "老师删除"][:18]
    for n, t in enumerate(base):
        x = t
        if n % 3 == 1:
            for old, new in SWAPS:
                if t.count(old) == 1:
                    x = t.replace(old, new, 1)
                    break
        rows.append(_row(f"0203_reteach_{n:04d}", x, x, kind="reteach_swap" if x != t else "reteach_plain",
                         source="新课_4"))
    return rows


def build_rows(variant):
    base = [(r["id"], r["text"], CLEAN[r["id"]], r["keep"] == "1", r["drop_reason"] == "老师删除") for r in ORIG]
    rows = []
    st = {"merge2": 0, "merge3": 0, "comma": 0, "nopunct": 0, "tail": 0, "head": 0, "new_after": 0, "new_before": 0}
    if variant in ("A", "B"):
        for k, (rid, t, c, keep, dele) in enumerate(base):
            nid = rid if variant == "A" else f"0099_b0b0b0_{k:04d}"
            src = _video(rid) if variant == "A" else _video(rid) + "_moved"
            rows.append(_row(nid, t, c, keep, dele, source=src))
    else:
        k, i, e = 0, 0, 0

        def nid():
            nonlocal k
            k += 1
            return f"0100_c0ffee_{k:04d}"

        while i < len(base):
            rid, t, c, keep, dele = base[i]
            src = _video(rid) + "_moved"
            usable = keep and not dele
            nxt = [b for b in base[i + 1:i + 3]]
            same_vid = [b for b in nxt if b[3] and not b[4] and _video(b[0]) == _video(rid)]
            if usable and i % 37 == 10 and len(same_vid) == 2 and len(t) + sum(len(b[1]) for b in same_vid) <= 160:
                rows.append(_row(nid(), t + same_vid[0][1] + same_vid[1][1], c + same_vid[0][2] + same_vid[1][2],
                                 tag="merge3", source=src))
                st["merge3"] += 1
                i += 3
                continue
            if usable and i % 9 == 4 and same_vid[:1] and same_vid[0] is nxt[0] and len(t) + len(nxt[0][1]) <= 120:
                rows.append(_row(nid(), t + nxt[0][1], c + nxt[0][2], tag="merge2", source=src))
                st["merge2"] += 1
                i += 2
                continue
            cut, how = None, ""
            if usable and i % 6 == 2 and len(t) >= 24:
                cut, how = _comma_cut(t, c), "comma"
            elif usable and i % 11 == 7 and len(t) >= 24:
                cut, how = _nopunct_cut(t, c), "nopunct"
            if cut:
                (ta, tb), (ca, cb) = cut
                rows.append(_row(nid(), ta, ca, tag=how, source=src))
                rows.append(_row(nid(), tb, cb, tag=how, source=src))
                st[how] += 1
                i += 1
                continue
            if usable and i % 17 == 5 and len(t) >= 12:
                how = ("tail", "head", "new_after", "new_before")[e % 4]
                extra = (TAILS[e % len(TAILS)], HEADS[e % len(HEADS)], NEW_CONTENT[e % len(NEW_CONTENT)],
                         NEW_CONTENT[(e + 7) % len(NEW_CONTENT)])[e % 4]
                e += 1
                if how in ("tail", "new_after"):
                    rows.append(_row(nid(), t + extra, c + extra, tag=how, source=src))
                else:
                    rows.append(_row(nid(), extra + t, extra + c, tag=how, source=src))
                st[how] += 1
                i += 1
                continue
            rows.append(_row(nid(), t, c, keep, dele, source=src))
            i += 1
    return rows + controls(), st


def auto_other(rows):
    """第二个识别引擎听到的文字：第一轮的规则 + 新讲的课里 20% 的句子听错一个词。"""
    other = {}
    n = {"contradict_on_correct": 0, "contradict_on_wrong": 0, "agrees_with_master": 0, "on_new_lecture": 0}
    for idx, r in enumerate(rows):
        rid, t, c, kind = r["id"], r["text"], r["truth"], r["kind"]
        if not r["keep"] or r["dele"]:
            continue
        if kind in CONTROL_KINDS:
            if idx % 5 == 0:
                for good, bad in WRONG_FOR_RIGHT + [("定语", "定位")]:
                    if good in t:
                        other[rid] = t.replace(good, bad, 1)
                        n["on_new_lecture"] += 1
                        break
        elif kind == "same" and idx % 4 == 1 and n["contradict_on_correct"] < 60:
            for good, bad in WRONG_FOR_RIGHT:
                if good in t:
                    other[rid] = t.replace(good, bad, 1)
                    n["contradict_on_correct"] += 1
                    break
        elif kind == "diff":
            done = False
            for bad, worse in OTHER_WRONG:
                if bad in t and idx % 3 != 0:
                    other[rid] = t.replace(bad, worse, 1)
                    n["contradict_on_wrong"] += 1
                    done = True
                    break
            if not done and idx % 3 == 0:
                other[rid] = c
                n["agrees_with_master"] += 1
    return other, n


class FakeChecker:
    name = pc.ENGINE_FUNASR
    label = "假的第二个识别引擎"
    diff = True
    model_id = "fake"

    def __init__(self, answers):
        self.answers = answers

    def applies(self, rec):
        return True

    def load(self):
        pass

    def recognize(self, wav, lang):
        rid, text = wav
        return self.answers.get(rid, text), None

    def close(self):
        pass


def install_fake_engine(answers):
    pc._engine_chain = lambda cfg: [pc.ENGINE_FUNASR]
    pc._make_checker = lambda name, cfg: FakeChecker(answers)
    pc._load_wav16 = lambda project, rec: (rec["id"], str(rec.get("text") or ""))


def make_voice(tmp, rows):
    cfg = load_config(overrides={"workspace": str(Path(tmp) / "ws"), "backend": "dummy",
                                 "prepare": {"asr": {"engine": "none"}}, "speaker_encoder": "mfcc",
                                 "similarity": {"model_dir": str(Path(tmp) / "sv")}}, user_config=False)
    project = wf.Project(cfg, "我的声音").ensure()
    recs = []
    for k, r in enumerate(rows):
        rec = {"id": r["id"], "path": f"clips/{r['id']}.wav", "text": r["text"], "lang": "zh", "duration": 4.0,
               "keep": r["keep"], "split": "train", "asr_done": True, "source": r["source"],
               "start": float(k * 4), "end": float(k * 4 + 4)}
        if r["dele"]:
            rec["deleted"], rec["drop_reason"] = True, "老师删除"
        recs.append(rec)
    project.save_manifest(recs)
    return cfg, project


def _change(a, b):
    return "；".join(review._change_items(a, b)[:3])


def measure(project, rows):
    truth = {r["id"]: r for r in rows if r["keep"] and not r["dele"]}
    draft = review.load_draft(project)
    m = {"diff": 0, "diff_exact": 0, "diff_untouched": 0, "diff_other": 0, "same": 0, "same_changed": 0,
         "pending_edits": 0, "contradict_edits": 0, "sure_contradict": 0, "diff_reachable": 0, "diff_sure_reachable": 0,
         "mother_label_rows": 0}
    for k in CONTROL_KINDS:
        m.update({k: 0, f"{k}_changed": 0, f"{k}_sure_rows": 0, f"{k}_unsure_mother_rows": 0})
    tags = {}
    ex = {"diff_other": [], "diff_untouched": [], "same_changed": [], "contradict": []}
    for k in CONTROL_KINDS:
        ex[f"{k}_changed"] = []
        ex[f"{k}_sure"] = []
    for rec in project.load_manifest():
        r = truth.get(rec.get("id"))
        if r is None:
            continue
        c, kind, t0 = r["truth"], r["kind"], r["text"]
        cur = str(review.current_values(rec, draft.get(rec["id"]))["text"] or "")
        info = review.analyze(rec, cur)
        sus = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else {}
        reasons = [str(x) for x in (sus.get("reasons") or [])]
        m[kind] += 1
        if r["tag"]:
            tg = tags.setdefault(r["tag"], {"rows": 0, "ok": 0})
            tg["rows"] += 1
            tg["ok"] += int(norm(cur) == norm(c))
        if kind == "diff":
            if norm(cur) == norm(c):
                m["diff_exact"] += 1
            elif cur == t0:
                m["diff_untouched"] += 1
                ex["diff_untouched"].append(f"{rec['id']}：{_change(t0, c)}")
            else:
                m["diff_other"] += 1
                ex["diff_other"].append(f"{rec['id']}：应该 {_change(t0, c)}；实际 {_change(t0, cur)}")
        elif cur != t0:
            m[f"{kind}_changed"] += 1
            ex[f"{kind}_changed"].append(f"{rec['id']}：{_change(t0, cur)}")
        edits = list(info["edits"])
        bad = [ed for ed in edits if not review._on_path(cur, review.apply_edits(cur, [ed]), norm(c))]
        if kind not in CONTROL_KINDS:
            m["pending_edits"] += len(edits)
            m["contradict_edits"] += len(bad)
            for ed in bad[:1]:
                if len(ex["contradict"]) < 12:
                    ex["contradict"].append(f"{rec['id']}：「{cur[ed[0]:ed[1]]}」→「{ed[2]}」（母本：{_change(cur, c) or '和现在一样'}）")
            m["sure_contradict"] += sum(1 for ed in info["sure"]
                                        if not review._on_path(cur, review.apply_edits(cur, [ed]), norm(c)))
        else:
            sure_m = [ed for ed in info["sure"] if any("按母本" in x and not x.startswith("没把握") for x in reasons)]
            if sure_m:
                m[f"{kind}_sure_rows"] += 1
                ex[f"{kind}_sure"].append(f"{rec['id']}：{_change(cur, review.apply_edits(cur, sure_m))}")
            if any("按母本" in x and "没把握" in x for x in reasons):
                m[f"{kind}_unsure_mother_rows"] += 1
        if kind == "diff" and norm(cur) != norm(c) and edits and norm(review.apply_edits(cur, edits)) == norm(c):
            m["diff_reachable"] += 1
        if kind == "diff" and norm(cur) != norm(c) and info["sure"] and norm(review.apply_edits(cur, info["sure"])) == norm(c):
            m["diff_sure_reachable"] += 1
        if any("按母本" in x for x in reasons):
            m["mother_label_rows"] += 1
    return m, tags, {k: v[:10] for k, v in ex.items()}


def run_variant(variant):
    rows, st = build_rows(variant)
    other, kst = auto_other(rows)
    tmp = tempfile.mkdtemp(prefix="mother2_")
    try:
        cfg, project = make_voice(tmp, rows)
        install_fake_engine(other)
        out = {"variant": variant, "rows": len(rows), "boundaries": st, "auto": kst}
        t0 = time.time()
        pc.find_suspects(project, cfg)
        out["t_auto1"] = round(time.time() - t0, 1)
        out["auto_before_oneclick"] = measure(project, rows)
        t0 = time.time()
        res = wf.run_transcript_fix(cfg, "我的声音", once=True)
        out["t_oneclick"] = round(time.time() - t0, 1)
        out["oneclick_result"] = {k: res.get(k) for k in ("checked", "fixes", "fixed_rows", "found", "unsure",
                                                          "mother_rows", "mother_fixes")}
        out["after_oneclick"] = measure(project, rows)
        t0 = time.time()
        pc.find_suspects(project, cfg)
        out["t_auto2"] = round(time.time() - t0, 1)
        out["auto_after_oneclick"] = measure(project, rows)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TITLES = {"auto_before_oneclick": "准备素材以后的自动查错字（还没点一键校正）",
          "after_oneclick": "点了「📝 一键全部文字校正」以后",
          "auto_after_oneclick": "一键校正以后再点「🔍 自动查找可能的错字」"}
KIND_NAMES = {"new": "新内容（和母本没关系）", "near": "换了一个词的母本句子", "spoken": "换了说法的母本句子",
              "reteach_swap": "同一份讲稿又讲一遍：换了词的句子", "reteach_plain": "同一份讲稿又讲一遍：没换词的句子"}


def report(results, label):
    lines = [f"母本优先第二轮实测（{label}，代码：{CODE}，{time.strftime('%Y-%m-%d %H:%M')}，"
             f"pypinyin：{'有' if tf.has_pinyin() else '没有'}，jieba：{'有' if has_jieba() else '没有'}）", ""]
    for r in results:
        lines.append(f"## 情况 {r['variant']}：{ {'A': 'id 和母本一样', 'B': 'id 全都不一样', 'C': 'id 不一样 + 切的位置不一样'}[r['variant']] }")
        lines.append(f"句子 {r['rows']} 句；切法 {r['boundaries']}；第二个引擎放进去的：{r['auto']}")
        lines.append(f"用时：自动查错字 {r['t_auto1']} 秒、一键校正 {r['t_oneclick']} 秒、再查一次 {r['t_auto2']} 秒；"
                     f"一键校正：{r['oneclick_result']}")
        for key in ("auto_before_oneclick", "after_oneclick", "auto_after_oneclick"):
            m, tags, ex = r[key]
            lines.append(f"### {TITLES[key]}")
            lines.append(f"- 和母本不一样的 {m['diff']} 句：和母本一模一样 {m['diff_exact']}、没动 {m['diff_untouched']}、"
                         f"改成别的样子 {m['diff_other']}；还不一样、点一下「采用」就和母本一样的 {m['diff_reachable']} 句"
                         f"（只用有把握的就一样的 {m['diff_sure_reachable']} 句）")
            lines.append(f"- 本来就对的 {m['same']} 句：被改了 {m['same_changed']} 句")
            lines.append(f"- 同一批讲课里还没采用的建议 {m['pending_edits']} 处，其中和母本矛盾的 {m['contradict_edits']} 处；"
                         f"有把握的里和母本矛盾的 {m['sure_contradict']} 处；说明里写着「按母本」的 {m['mother_label_rows']} 句")
            if tags:
                lines.append("- 切法 / 前后加字的句子（改完和正确答案一模一样 / 一共）：" +
                             "，".join(f"{k} {v['ok']}/{v['rows']}" for k, v in sorted(tags.items())))
            for k in CONTROL_KINDS:
                lines.append(f"- 新讲的课·{KIND_NAMES[k]} {m[k]} 句：被直接改了 {m[f'{k}_changed']} 句；"
                             f"有把握的「按母本」建议（一键校正会采用）{m[f'{k}_sure_rows']} 句；"
                             f"「没把握（请听录音）」的按母本建议 {m[f'{k}_unsure_mother_rows']} 句")
            for k, v in ex.items():
                if v:
                    lines.append(f"  - {k} 例子：" + " | ".join(v[:6]))
        lines.append("")
    return "\n".join(lines)


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "新代码"
    variants = sys.argv[2:] or ["A", "B", "C"]
    results = [run_variant(v) for v in variants]
    text = report(results, label)
    print(text)
    (HERE / f"第二轮结果_{label}.txt").write_text(text + "\n", encoding="utf-8")
    (HERE / f"第二轮结果_{label}.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
