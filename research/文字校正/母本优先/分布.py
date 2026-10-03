"""母本优先：「找到了」的门槛（相似度 MATCH_MIN）怎么定——在老师的母本上量相似度的分布。

相似度 = 读音对上的字数 ÷ max(这一句的字数, 母本那一段的字数)（voicetwin/data/mother_first.py）。

量四种：
1. 同一句（真的对得上）：老师修缮以前的 1004 句（母本_原文.csv）在程序自带的母本（修缮好的，里面有它自己）里找：
   相似度多少；按找到的那一段改完是不是和修缮好的一模一样。
2. 新的话（不该对上）：母本里每一句（修缮好的）当成「新录的、母本里没有的话」，从母本里拿掉它自己再找：
   找到的最像的一段相似度多少；到门槛的话会不会被硬改（改了就是错的——录音里就是这么说的）。
   老师讲课会重复说差不多的话，所以这一项最能说明门槛够不够高。
3. 同样，修缮以前有错的 123 句拿掉它自己再找（新的话里有识别错的时候，母本里别的句子能不能帮上忙）。
4. 自己写的 40 句新内容（实测.py 里的 NEW_CONTENT）：最像的一段相似度多少。

运行（仓库根目录，要有 pypinyin）：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/分布.py
结果写到 分布结果.txt。
"""

import csv
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from voicetwin.data import mother_first as mf  # noqa: E402
from voicetwin.data import review  # noqa: E402
from voicetwin.data import transcript_fix as tf  # noqa: E402
from voicetwin.utils.textutil import clean_transcript  # noqa: E402

import 实测  # noqa: E402

D = ROOT / "research" / "文字校正" / "老师的母本"
ORIG = list(csv.DictReader(open(D / "母本_原文.csv", encoding="utf-8-sig")))
CLEAN = {r["id"]: r["text"] for r in csv.DictReader(open(D / "母本_修缮后.csv", encoding="utf-8-sig"))}
THRESHOLDS = (0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)


def apply_all(text, toks, ref, segs):
    edits = [ed for s in segs for ed in mf.segment_edits(text, toks, ref, s)]
    return tf._apply(text, edits), edits


def best_any(text, ref, skips=()):
    """不管门槛，最像的一段（相似度、这一句被盖住的比例、按它改了几处）。"""
    old = mf.MATCH_MIN
    mf.MATCH_MIN = 0.0
    try:
        toks, segs = mf.find_segments(text, ref, skips=skips)
    finally:
        mf.MATCH_MIN = old
    if not segs:
        return 0.0, 0.0, 0, None, toks, segs
    top = max(segs, key=lambda s: s.length)
    cov = sum(s.length for s in segs) / max(len(toks), 1)
    new, edits = apply_all(text, toks, ref, [top])
    return top.sim, cov, len(edits), top, toks, segs


def hist(vals):
    c = Counter()
    for v in vals:
        c[min(int(v * 20) / 20, 0.95)] += 1
    return "  ".join(f"{k:.2f}~:{c[k]}" for k in sorted(c))


def main():
    t0 = time.time()
    builtin = list(tf.builtin_mother())
    ref = tf.Reference(builtin)
    out = [f"母本优先：相似度的分布（{time.strftime('%Y-%m-%d %H:%M')}，pypinyin：{'有' if tf.has_pinyin() else '没有'}；"
           f"母本 {len(builtin)} 句、{len(ref)} 个字 / 词；现在的门槛 MATCH_MIN = {mf.MATCH_MIN}，"
           f"最短 MIN_TOKENS = {mf.MIN_TOKENS}，只对上一部分时至少 PART_MIN = {mf.PART_MIN}）", ""]

    # 1. 同一句
    sims_diff, sims_same, exact, wrong_rows, short = [], [], 0, [], []
    for r in ORIG:
        if r["keep"] != "1" or r["drop_reason"] == "老师删除":
            continue
        text, truth = r["text"], CLEAN[r["id"]]
        toks, segs = mf.find_segments(text, ref)
        top = max(segs, key=lambda s: s.length) if segs else None
        new, _e = apply_all(text, toks, ref, [s for s in segs if not s.ambiguous])
        same = clean_transcript(new) == clean_transcript(truth)
        if text != truth:
            sims_diff.append(top.sim if top else 0.0)
            exact += int(same)
            if not same:
                wrong_rows.append(f"{r['id']}（相似度 {top.sim if top else 0:.2f}）：应该 {实测._change(text, truth)}；"
                                  f"按母本改成 {实测._change(text, new) or '没改'}")
        else:
            sims_same.append(top.sim if top else 0.0)
            if not same:
                wrong_rows.append(f"{r['id']}（本来就对，相似度 {top.sim if top else 0:.2f}）：被改成 {实测._change(text, new)}")
            if not segs:
                short.append(r["id"])
    out += ["## 1. 同一句（修缮以前的句子在程序自带的母本里找）",
            f"和母本不一样的 {len(sims_diff)} 句：相似度最低 {min(sims_diff):.3f}；分布 {hist(sims_diff)}",
            f"  按找到的那一段改完和修缮好的一模一样：{exact} / {len(sims_diff)}",
            f"本来就对的 {len(sims_same)} 句：相似度最低 {min(sims_same):.3f}；没找到（太短等）{len(short)} 句",
            f"改得不对 / 本来对的被改：{len(wrong_rows)} 句"] + [f"  - {w}" for w in wrong_rows[:20]] + [""]

    # 2. 新的话：每一句拿掉它自己
    loo = []
    for rid, text in builtin:
        skips = ref.id_ranges.get(rid, [])
        sim, cov, n_ed, top, toks, segs = best_any(text, ref, skips)
        loo.append((sim, cov, n_ed, rid, text, top, toks))
    out += ["## 2. 新的话：母本里每一句拿掉它自己再找（找到的都不是它，改了就是改错）",
            f"{len(loo)} 句：最像的一段相似度分布 {hist([x[0] for x in loo])}"]
    for th in THRESHOLDS:
        hit = [x for x in loo if x[0] >= th - 1e-9]
        forced = [x for x in hit if x[2] > 0]
        full = [x for x in forced if x[1] >= 0.999]
        out.append(f"  门槛 {th:.2f}：到门槛的 {len(hit)} 句，其中会被改的 {len(forced)} 句（整句都对上的 {len(full)} 句）")
    th = mf.MATCH_MIN
    forced = sorted([x for x in loo if x[0] >= th - 1e-9 and x[2] > 0], key=lambda x: -x[0])
    out.append(f"  现在的门槛 {th} 会被硬改的句子（全部列出）：")
    for sim, cov, n_ed, rid, text, top, toks in forced:
        new, _e = apply_all(text, toks, ref, [top])
        out.append(f"  - {rid}（相似度 {sim:.3f}，盖住 {cov:.0%}）：{实测._change(text, new)}　原句：{text[:60]}")
    out.append("")

    # 3. 有错的 123 句拿掉它自己
    loo_err = []
    for r in ORIG:
        if r["text"] == CLEAN[r["id"]] or r["keep"] != "1":
            continue
        skips = ref.id_ranges.get(r["id"], [])
        sim, cov, n_ed, top, toks, segs = best_any(r["text"], ref, skips)
        good = None
        if sim >= th:
            new, _e = apply_all(r["text"], toks, ref, [top])
            good = clean_transcript(new) == clean_transcript(CLEAN[r["id"]])
        loo_err.append((sim, good))
    out += ["## 3. 有错的 123 句拿掉它自己再找（母本里别的句子能不能帮上忙）",
            f"相似度分布 {hist([x[0] for x in loo_err])}；到门槛 {th} 的 {sum(1 for x in loo_err if x[0] >= th)} 句，"
            f"其中改完正好对的 {sum(1 for x in loo_err if x[1])} 句", ""]

    # 4. 自己写的新内容
    news = [(best_any(t, ref)[0], t) for t in 实测.NEW_CONTENT]
    out += ["## 4. 自己写的 40 句新内容",
            f"最像的一段相似度分布 {hist([x[0] for x in news])}；最高 {max(x[0] for x in news):.3f}"]
    out += [f"  - {s:.3f}：{t}" for s, t in sorted(news, reverse=True)[:5]]
    out.append("")
    out.append(f"用时 {time.time() - t0:.1f} 秒")
    text = "\n".join(out)
    print(text)
    (Path(__file__).resolve().parent / "分布结果.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
