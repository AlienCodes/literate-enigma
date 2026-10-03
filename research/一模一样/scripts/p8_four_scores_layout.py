"""P8 四项评分：老师母本里三组句子各有几句（按 voicetwin/eval/lang_groups.text_group 自动分组），
以及综合总评分的比例。

真正的比例是程序在老师电脑上按每段素材实测的人声时长（manifest 的 voiced）算的，存进 models.json
（identical.lang.shares）；这里没有老师的录音，只能数句子、数音节——音节比例只是**估计**（中文、英文每个音节的时长不一样）。
运行：python research/一模一样/scripts/p8_four_scores_layout.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from voicetwin.eval import lang_groups as LG  # noqa: E402
from voicetwin.utils.textutil import en_words, syllable_count  # noqa: E402

path = ROOT / "research" / "文字校正" / "老师的母本" / "母本_修缮后.csv"
rows = [r for r in csv.DictReader(path.open(encoding="utf-8-sig")) if r["keep"] == "1"]
n = {g: 0 for g in LG.GROUP_ORDER}
syl = {g: 0 for g in LG.GROUP_ORDER}
words = 0
for r in rows:
    g = LG.text_group(r["text"])
    if not g:
        continue
    n[g] += 1
    syl[g] += syllable_count(r["text"])
    words += len(en_words(r["text"]))
total_syl = sum(syl.values())
print(f"母本（修缮后）留用的句子：{len(rows)} 句")
for g in LG.GROUP_ORDER:
    print(f"  {LG.GROUP_LABELS[g]}：{n[g]} 句，{syl[g]} 个音节（占 {100 * syl[g] / total_syl:.1f}%）")
print(f"  英文单词一共 {words} 个")
w_lines, _ = LG.composite_weights({g: n[g] for g in LG.GROUP_ORDER}, [g for g in LG.GROUP_ORDER if n[g]])
w_syl, _ = LG.composite_weights({g: syl[g] for g in LG.GROUP_ORDER}, [g for g in LG.GROUP_ORDER if syl[g]])
print("综合总评分的比例（只是估计；程序在老师电脑上按实测的人声时长算）：")
print("  按句数：" + "、".join(f"{LG.GROUP_LABELS[g]} {100 * v:.1f}%" for g, v in w_lines.items()))
print("  按音节：" + "、".join(f"{LG.GROUP_LABELS[g]} {100 * v:.1f}%" for g, v in w_syl.items()))
print("纯英文这一组没有句子：综合总评分不算它，比例在另外两组之间重新分配。")
