"""母本优先（10-04 老师的要求）的实测：同一批讲课的句子，片段 id 一样 / 不一样 / 切的位置也不一样时，
「📝 一键全部文字校正」和「🔍 自动查找可能的错字」的结果是不是都以母本为准。

老师的原话（10-04）：「识别出来的这些句子，先去跟母本对照。一般母本都会有差不多或者原模原样的句子。
跟母本不一样的地方，那很明显就是错误的地方。」「母本是最优先级。」

数据：research/文字校正/老师的母本/母本_原文.csv（老师修缮以前、识别引擎写的 1008 句）当成识别出来的文字，
母本_修缮后.csv（逐句修缮好的）当成正确答案（123 句不一样，138 处）。程序自带的母本（core_corpus.tsv）就是修缮好的这些句子。

三种情况（老师可能遇到的）：
  A：片段 id 和母本一模一样（同一个文件夹、没重新准备过）；
  B：片段 id 全都不一样（重新准备过、视频挪了地方、上传视频而不是选文件夹、升级以后新建了声音……
     id 里有视频的完整路径和大小算出来的编号，见 voicetwin/data/prepare.py 的 source_id）；
  C：id 不一样，而且切的位置也不一样（一部分相邻的两句合成一句、一部分长句子在逗号处切成两句）。
每种情况再加：
  - 「自动查错字」（第二个识别引擎）听到的和母本矛盾的建议（定语 → 定于、介词 → 借词……），一部分放在本来就对的句子上，
    一部分放在有错的句子上（另一个错的写法），还有一部分和母本一致；
  - 新内容对照：母本里没有的 40 句新讲课的话（自己写的、没有错字）：一个字都不应该被母本改。

流程（和老师一样）：准备素材以后自动查错字（find_suspects，第二个引擎是假的，按上面的规则回答）→ 量一次
→ 点「📝 一键全部文字校正」（run_transcript_fix，once=True）→ 量一次 → 再点「🔍 自动查找可能的错字」→ 量一次。

量什么（只算没删除、要用、有文字的句子）：
  - 和母本不一样的句子里：表格里的文字（含没保存的修改）变得和母本一模一样的、没动的、改成别的样子的；
  - 本来就对的句子被改了几句；新内容被改了几句；
  - 「修改建议」那一列：还没采用的建议一共几处、其中和母本矛盾的几处（采用以后离母本更远或者不更近：
    review._on_path 判断「是不是在去母本的最短路上」）；和母本不一样的句子里，点一下「采用」就和母本一模一样的有几句。

运行（仓库根目录，要用和整合包一样有 pypinyin、jieba 的环境）：
  PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/实测.py 旧代码
结果写到同一个文件夹的 结果_<名字>.txt / 结果_<名字>.json。
"""

import csv
import difflib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from voicetwin import workflows as wf  # noqa: E402
from voicetwin.config import load_config  # noqa: E402
from voicetwin.data import proofcheck as pc  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.data import transcript_fix as tf  # noqa: E402
from voicetwin.data.lexicon_fix import has_jieba  # noqa: E402
from voicetwin.utils.textutil import clean_transcript  # noqa: E402

HERE = Path(__file__).resolve().parent
D = ROOT / "research" / "文字校正" / "老师的母本"
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}

#: 新内容对照：母本里没有的讲课的话（开发时自己写的，没有错字）。母本一个字都不应该改它们
NEW_CONTENT = [
    "今天我们来学习一下名词性从句里面的主语从句。",
    "主语从句就是在整个复合句当中充当主语的那个从句。",
    "比如说 What he said is true，这里的 what he said 就是一个主语从句。",
    "为了避免句子头重脚轻，我们经常会用 it 作形式主语，把真正的主语从句放到后面去。",
    "接下来我们看一下宾语从句的语序问题。",
    "宾语从句一定要用陈述句的语序，不能用疑问句的语序。",
    "很多同学在写作文的时候特别容易在这个地方出错。",
    "我们再来对比一下表语从句和同位语从句的区别。",
    "同位语从句是对前面那个抽象名词的内容进行解释说明。",
    "常见的抽象名词有 fact、news、idea、hope 这些词。",
    "好，下面我们做几道选择题来巩固一下刚才讲的内容。",
    "第一题的答案选 B，因为空格后面的句子缺少主语。",
    "第二题考的是 whether 和 if 的区别，大家注意一下。",
    "whether 可以和 or not 直接连用，但是 if 一般不行。",
    "在介词后面引导宾语从句的时候，只能用 whether 不能用 if。",
    "我们来总结一下今天这节课的三个重点。",
    "第一个重点是名词性从句的四种类型。",
    "第二个重点是连接词的选择，要看从句里面缺不缺成分。",
    "第三个重点是语序，一律使用陈述句语序。",
    "下节课我们会开始学习状语从句里面的时间状语从句。",
    "时间状语从句最常见的引导词有 when、while 和 as。",
    "请大家课后把练习册第十二页的题目做完。",
    "如果有不明白的地方，可以在群里面给我留言。",
    "我们先来复习一下上节课讲过的虚拟语气。",
    "与现在事实相反的虚拟语气，从句要用一般过去时。",
    "主句要用 would 加上动词原形的结构。",
    "注意在虚拟语气当中，be 动词一律用 were。",
    "比如 If I were you, I would study harder。",
    "那么与过去事实相反的时候，从句就要用过去完成时。",
    "这种题目在考试当中出现的频率非常高。",
    "大家一定要把这几个时态的对应关系记清楚。",
    "现在我们来看一个比较难的长难句。",
    "拿到长难句以后，第一步是先找到句子的谓语动词。",
    "找到谓语动词以后，再去划分句子的主干和修饰成分。",
    "这样一层一层地分析，再长的句子也不会觉得难。",
    "我们再来看一下非谓语动词作状语的情况。",
    "现在分词表示主动，过去分词表示被动。",
    "判断的方法就是看逻辑主语和这个动词之间的关系。",
    "好，今天的课就上到这里，同学们再见。",
    "希望大家回去以后好好复习，我们下次课再见。",
]

#: 第二个识别引擎「听错」的规则：本来对的词 → 另一个引擎听成的错词（和母本矛盾）
WRONG_FOR_RIGHT = [("定语", "定于"), ("介词", "借词"), ("谓语", "位于"), ("宾语", "冰语"), ("先行词", "先行次"),
                   ("从句", "从具"), ("关系代词", "关系待词"), ("主语", "主雨"), ("连词", "联系")]
#: 有错的句子：另一个引擎听成另一个错的写法（也和母本矛盾）
OTHER_WRONG = [("借词", "接词"), ("关系带词", "关系待词"), ("定语从剧", "定语从具"), ("主位结构", "主味结构"),
               ("叙述词", "序述词"), ("带着墨镜", "代着墨镜"), ("现行词", "现形词"), ("三大从具", "三大从剧"),
               ("定语从中", "定语中从"), ("系统词", "系桶词"), ("述之", "树之")]


def norm(s):
    return clean_transcript(str(s or ""))


# ============================================================================ 三种情况的句子
def build_rows(variant):
    """[(id, 识别出来的文字, 正确答案, 种类, keep, deleted)]；种类：same（本来就对）/ diff（和母本不一样）/ new（新内容）。
    另外返回合并 / 切开的统计。"""
    rows, stats = [], {"merged": 0, "split": 0, "merged_diff": 0, "split_diff": 0}
    base = [(r["id"], r["text"], CLEAN[r["id"]], r["keep"] == "1", r["drop_reason"] == "老师删除") for r in ORIG]
    if variant in ("A", "B"):
        for k, (rid, t, c, keep, dele) in enumerate(base):
            nid = rid if variant == "A" else f"0099_b0b0b0_{k:04d}"
            rows.append((nid, t, c, keep, dele))
    else:
        k, i = 0, 0
        while i < len(base):
            rid, t, c, keep, dele = base[i]
            usable = keep and not dele
            nxt = base[i + 1] if i + 1 < len(base) else None
            if (usable and nxt and nxt[3] and not nxt[4] and i % 9 == 4 and len(t) + len(nxt[1]) <= 120
                    and nxt[0].split("_")[1] == rid.split("_")[1]):  # 同一个视频里相邻的两句合成一句
                rows.append((f"0100_c0ffee_{k:04d}", t + nxt[1], c + nxt[2], True, False))
                stats["merged"] += 1
                stats["merged_diff"] += int(t != c or nxt[1] != nxt[2])
                k, i = k + 1, i + 2
                continue
            cut = _comma_cut(t, c) if (usable and i % 6 == 2 and len(t) >= 24) else None
            if cut:
                (ta, tb), (ca, cb) = cut
                rows.append((f"0100_c0ffee_{k:04d}", ta, ca, True, False))
                rows.append((f"0100_c0ffee_{k + 1:04d}", tb, cb, True, False))
                stats["split"] += 1
                stats["split_diff"] += int(t != c)
                k, i = k + 2, i + 1
                continue
            rows.append((f"0100_c0ffee_{k:04d}", t, c, keep, dele))
            k, i = k + 1, i + 1
    out = []
    for rid, t, c, keep, dele in rows:
        kind = "same" if norm(t) == norm(c) else "diff"
        out.append((rid, t, c, kind, keep, dele))
    for n, t in enumerate(NEW_CONTENT):
        out.append((f"0200_newnew_{n:04d}", t, t, "new", True, False))
    return out, stats


def _comma_cut(t, c):
    """在一个两边都没改过的逗号处切开（识别文字和修缮好的文字一起切），两边都至少 6 个字。"""
    best = None
    sm = difflib.SequenceMatcher(None, t, c, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            continue
        for p in range(i1, i2):
            if t[p] in "，," and p >= 6 and len(t) - p - 1 >= 6:
                q = j1 + (p - i1)
                score = abs(p - len(t) / 2)
                if best is None or score < best[0]:
                    best = (score, p, q)
    if best is None:
        return None
    _s, p, q = best
    return (t[:p + 1].strip(), t[p + 1:].strip()), (c[:q + 1].strip(), c[q + 1:].strip())


def auto_other(rows):
    """第二个识别引擎听到的文字：{id: 文字}。规则见文件开头；按位置轮流选，固定不随机。"""
    other, kinds = {}, {}
    n_right = n_wrong = n_agree = 0
    for idx, (rid, t, c, kind, keep, dele) in enumerate(rows):
        if not keep or dele or kind == "new":
            continue
        if kind == "same" and idx % 4 == 1 and n_right < 60:
            for good, bad in WRONG_FOR_RIGHT:
                if good in t:
                    other[rid], kinds[rid] = t.replace(good, bad, 1), "contradict_on_correct"
                    n_right += 1
                    break
        elif kind == "diff":
            done = False
            for bad, worse in OTHER_WRONG:
                if bad in t and idx % 3 != 0:
                    other[rid], kinds[rid] = t.replace(bad, worse, 1), "contradict_on_wrong"
                    n_wrong += 1
                    done = True
                    break
            if not done and idx % 3 == 0:
                other[rid], kinds[rid] = c, "agrees_with_master"  # 另一个引擎听对了（和母本一样）
                n_agree += 1
    return other, kinds, {"contradict_on_correct": n_right, "contradict_on_wrong": n_wrong, "agrees_with_master": n_agree}


# ============================================================================ 建声音、假的第二个引擎
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
    for k, (rid, t, _c, _kind, keep, dele) in enumerate(rows):
        rec = {"id": rid, "path": f"clips/{rid}.wav", "text": t, "lang": "zh", "duration": 4.0, "keep": keep,
               "split": "train", "asr_done": True, "source": "第1课", "start": float(k * 4), "end": float(k * 4 + 4)}
        if dele:
            rec["deleted"], rec["drop_reason"] = True, "老师删除"
        recs.append(rec)
    project.save_manifest(recs)
    return cfg, project


# ============================================================================ 量
def measure(project, rows):
    truth = {rid: (c, kind) for rid, _t, c, kind, keep, dele in rows if keep and not dele}
    orig = {rid: t for rid, t, *_ in rows}
    draft = review.load_draft(project)
    m = {"diff": 0, "diff_exact": 0, "diff_untouched": 0, "diff_other": 0, "same": 0, "same_changed": 0,
         "new": 0, "new_changed": 0, "pending_edits": 0, "contradict_edits": 0, "contradict_rows": 0,
         "diff_reachable": 0, "sure_contradict": 0, "mother_label_rows": 0}
    examples = {"diff_other": [], "diff_untouched": [], "same_changed": [], "new_changed": [], "contradict": []}
    for rec in project.load_manifest():
        rid = rec.get("id")
        if rid not in truth:
            continue
        c, kind = truth[rid]
        cur = str(review.current_values(rec, draft.get(rid))["text"] or "")
        t0 = orig[rid]
        info = review.analyze(rec, cur)
        m[kind] += 1
        if kind == "diff":
            if norm(cur) == norm(c):
                m["diff_exact"] += 1
            elif cur == t0:
                m["diff_untouched"] += 1
                examples["diff_untouched"].append(f"{rid}：{_change(t0, c)}")
            else:
                m["diff_other"] += 1
                examples["diff_other"].append(f"{rid}：应该 {_change(t0, c)}；实际 {_change(t0, cur)}")
        elif cur != t0:
            m[f"{kind}_changed"] += 1
            examples[f"{kind}_changed"].append(f"{rid}：{_change(t0, cur)}")
        edits = list(info["edits"])
        m["pending_edits"] += len(edits)
        bad = [ed for ed in edits if not review._on_path(cur, review.apply_edits(cur, [ed]), norm(c))]
        m["contradict_edits"] += len(bad)
        m["contradict_rows"] += int(bool(bad))
        for ed in bad[:1]:
            if len(examples["contradict"]) < 12:
                examples["contradict"].append(f"{rid}：「{cur[ed[0]:ed[1]]}」→「{ed[2]}」（母本：{_change(cur, c) or '和现在一样'}）")
        sure_bad = [ed for ed in info["sure"] if not review._on_path(cur, review.apply_edits(cur, [ed]), norm(c))]
        m["sure_contradict"] += len(sure_bad)
        if kind == "diff" and norm(cur) != norm(c) and edits and norm(review.apply_edits(cur, edits)) == norm(c):
            m["diff_reachable"] += 1
        sus = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else {}
        if any("按母本" in str(x) for x in (sus.get("reasons") or [])):
            m["mother_label_rows"] += 1
    return m, {k: v[:12] for k, v in examples.items()}


def _change(a, b):
    return "；".join(review._change_items(a, b)[:3])


def run_variant(variant):
    rows, stats = build_rows(variant)
    other, kinds, kstats = auto_other(rows)
    tmp = tempfile.mkdtemp(prefix="mother_")
    try:
        cfg, project = make_voice(tmp, rows)
        install_fake_engine(other)
        out = {"variant": variant, "rows": len(rows), "boundaries": stats, "auto": kstats}
        t0 = time.time()
        pc.find_suspects(project, cfg)
        out["t_auto1"] = round(time.time() - t0, 1)
        out["auto_before_oneclick"] = measure(project, rows)
        t0 = time.time()
        res = wf.run_transcript_fix(cfg, "我的声音", once=True)
        out["t_oneclick"] = round(time.time() - t0, 1)
        out["oneclick_result"] = {k: res.get(k) for k in ("checked", "fixes", "fixed_rows", "found", "unsure")}
        out["oneclick_result"]["adopted"] = res.get("adopted", {}).get("changes")
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


def report(results, label):
    lines = [f"母本优先实测（{label}，{time.strftime('%Y-%m-%d %H:%M')}，pypinyin：{'有' if tf.has_pinyin() else '没有'}，"
             f"jieba：{'有' if has_jieba() else '没有'}）", ""]
    for r in results:
        b = r["boundaries"]
        lines.append(f"## 情况 {r['variant']}：{ {'A': 'id 和母本一样', 'B': 'id 全都不一样', 'C': 'id 不一样 + 切的位置不一样'}[r['variant']] }")
        lines.append(f"句子 {r['rows']} 句（含新内容 {len(NEW_CONTENT)} 句）；合成一句的 {b['merged']} 处（其中有错的 {b['merged_diff']}），"
                     f"切成两句的 {b['split']} 处（其中有错的 {b['split_diff']}）；自动查错字放进去的建议：{r['auto']}")
        lines.append(f"用时：自动查错字 {r['t_auto1']} 秒、一键校正 {r['t_oneclick']} 秒、再查一次 {r['t_auto2']} 秒；"
                     f"一键校正：{r['oneclick_result']}")
        for key in ("auto_before_oneclick", "after_oneclick", "auto_after_oneclick"):
            m, ex = r[key]
            lines.append(f"### {TITLES[key]}")
            lines.append(f"- 和母本不一样的 {m['diff']} 句：和母本一模一样 {m['diff_exact']}、没动 {m['diff_untouched']}、"
                         f"改成别的样子 {m['diff_other']}；还不一样、点一下「采用」就和母本一样的 {m['diff_reachable']} 句")
            lines.append(f"- 本来就对的 {m['same']} 句：被改了 {m['same_changed']} 句；新内容 {m['new']} 句：被改了 {m['new_changed']} 句")
            lines.append(f"- 还没采用的建议 {m['pending_edits']} 处，其中和母本矛盾的 {m['contradict_edits']} 处（{m['contradict_rows']} 句）；"
                         f"一键校正会自动采用的（有把握的）里和母本矛盾的 {m['sure_contradict']} 处；说明里写着「按母本」的 {m['mother_label_rows']} 句")
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
    (HERE / f"结果_{label}.txt").write_text(text + "\n", encoding="utf-8")
    (HERE / f"结果_{label}.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
