"""母本优先第二轮：「同一批录音的证据」（transcript_fix._SameBatch）前后看几个片段（WINDOW）、母本里最多隔几句（LINES）
怎么定——在老师的数据上量。

为什么要这个证据：第二轮检查的人发现，新讲的课用了母本里的说法、只换了一个词（定语从句 → 状语从句、可以 → 不可以），
旧的做法把它改回母本的写法。读音不像听错的地方（多的 / 少的字、读音不像的字），只有确定是同一批录音时才按母本直接改。

量两样（第二轮实测.py 的三种情况 + 新讲的课）：
1. 同一批讲课：和母本不一样的句子里，需要证据的（有读音不像听错的改动）有几句、其中有证据的几句（要全部都有）；
2. 新讲的课（换了一个词 / 换了说法的母本句子、和母本没关系的新内容）：有证据的几句（要尽量是 0；「同一份讲稿又讲一遍」
   单独列：前后几句都和母本连着对上，这种做法分不出来）。

运行：PYTHONPATH=. /tmp/gsv39/bin/python research/文字校正/母本优先/证据分析.py → 证据分析结果.txt
"""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from voicetwin.data import mother_first as mf  # noqa: E402
from voicetwin.data import transcript_fix as tf  # noqa: E402

import 第二轮实测 as T  # noqa: E402

SETTINGS = [(1, 1), (1, 2), (2, 2), (3, 2), (3, 3), (3, 5), (5, 5)]


def analyse(variant, ref):
    rows, _st = T.build_rows(variant)
    records = [{"id": r["id"], "text": r["text"], "source": r["source"], "deleted": r["dele"]} for r in rows]
    texts = {r["id"]: r["text"] for r in rows}
    matches = {}

    def matcher(rec):
        rid = rec["id"]
        if rid not in matches:
            matches[rid] = tf._mother_match(texts[rid], rid, ref, (texts[rid],))
        return matches[rid]

    need = {}  # 每一句：有读音不像听错的改动的那几段（要证据才能直接按母本改）
    for r in rows:
        if not r["keep"] or r["dele"]:
            continue
        toks, segs = matcher(r)
        idx = []
        for k, seg in enumerate(segs):
            if seg.ambiguous or seg.m2 > ref.unvetted_from:
                continue
            kinds = {tf._piece_kind(r["text"], s, e, rep) for (s, e, rep), _w in mf.segment_pieces(r["text"], toks, ref, seg)}
            if kinds - {"alike"}:
                idx.append(k)
        if idx:
            need[r["id"]] = (r, idx)
    out = {}
    for window, lines in SETTINGS:
        tf._SameBatch.WINDOW, tf._SameBatch.LINES = window, lines
        batch = tf._SameBatch(records, texts, ref, matcher)
        cnt = {}
        for rid, (r, idx) in need.items():
            ev = batch.evidence(rid, matcher(r)[1])
            kind = r["kind"]
            c = cnt.setdefault(kind, [0, 0])
            c[0] += 1
            c[1] += int(all(ev[k] for k in idx))
        out[(window, lines)] = cnt
    return out


def main():
    t0 = time.time()
    builtin = list(tf.builtin_mother())
    ref = tf.Reference(builtin, own_from=len(builtin), vetted_lines=len(builtin))
    keep = (tf._SameBatch.WINDOW, tf._SameBatch.LINES)
    lines = [f"「同一批录音的证据」怎么定（{time.strftime('%Y-%m-%d %H:%M')}；现在用的 WINDOW = {keep[0]}、LINES = {keep[1]}）", "",
             "每一格：需要证据的句子（有读音不像听错的改动）有几句 / 其中有证据的几句。",
             "同一批讲课（diff = 和母本不一样、same = 本来对的）要全部有证据；新讲的课（near、spoken、new）越少越好。", ""]
    for variant in ("A", "B", "C"):
        res = analyse(variant, ref)
        lines.append(f"## 情况 {variant}")
        for (w, ln), cnt in res.items():
            mark = "  ← 现在用的" if (w, ln) == keep else ""
            lines.append(f"- 前后看 {w} 个片段、母本里最多隔 {ln} 句：" +
                         "，".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(cnt.items())) + mark)
        lines.append("")
    tf._SameBatch.WINDOW, tf._SameBatch.LINES = keep
    lines.append(f"用时 {time.time() - t0:.1f} 秒")
    text = "\n".join(lines)
    print(text)
    (HERE / "证据分析结果.txt").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
