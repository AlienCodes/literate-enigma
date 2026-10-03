"""老师的素材里，训练列表会被补句末标点的有几句；发给引擎的语言（send_lang）和以前不一样的有几句。
在仓库根目录运行：python3 research/一模一样/scripts/measure_final_punct.py"""
import collections
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from voicetwin.utils.textutil import (  # noqa: E402
    detect_lang, en_words, ends_sentence, ensure_final_punct, ensure_final_punct_train, send_lang)

rows = [r for r in csv.DictReader(open(ROOT / "research/文字校正/老师的母本/母本_修缮后.csv", encoding="utf-8-sig"))
        if r["keep"] == "1"]
not_end = [r for r in rows if not ends_sentence(r["text"])]
last = collections.Counter(r["text"].strip()[-1] for r in not_end)
old_add = [r for r in rows if ensure_final_punct(r["text"], detect_lang(r["text"])) != r["text"].strip()]
new = [ensure_final_punct_train(r["text"], detect_lang(r["text"])) for r in old_add]
print(f"保留的句子 {len(rows)}；不是句末结束的（ends_sentence 为假）{len(not_end)}，其中末尾是「，」{last['，']}、「,」{last[',']}")
print(f"以前的导出规则真的补了「。」的：{len(old_add)} 句；新规则改成补「，」/「,」：{sum(t[-1] in '，,' for t in new)} 句")
print("例子：" + " / ".join(t[-14:] for t in new[:5]))
bug = [r for r in rows if send_lang(r["text"], detect_lang(r["text"])) != detect_lang(r["text"])]
mixed = [r for r in rows if detect_lang(r["text"]) == "zh" and en_words(r["text"])]
print(f"发给引擎的语言和以前不一样的句子：{len(bug)} 句（训练素材全是 zh；这个问题出在讲稿里英文单词特别多的句子）")
print(f"中文句子里夹着英文：{len(mixed)} 句，共 {sum(len(en_words(r['text'])) for r in mixed)} 个英文单词")
