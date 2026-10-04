"""Measure how much of the teacher's English is inside zh-tagged training lines, and show what GPT-SoVITS
1-get-text.py (clean_text(text, "zh") -> chinese2.text_normalize -> replace_punctuation) keeps of such lines.
Run from the repo root: python3 <this file>"""
import csv, re, sys
sys.path.insert(0, ".")
from voicetwin.utils.textutil import detect_lang, en_words, syllable_count, ends_sentence

punctuation = ["!", "?", "…", ",", ".", "-"]  # GPT_SoVITS/text/symbols.py @20250606v2pro
rep_map = {"：": ",", "；": ",", "，": ",", "。": ".", "！": "!", "？": "?", "\n": ".", "·": ",", "、": ",",
           "...": "…", "$": ".", "/": ",", "—": "-", "~": "…", "～": "…"}  # chinese2.py rep_map


def replace_punctuation(text):  # chinese2.py L62-70 (TextNormalizer step before it omitted)
    text = text.replace("嗯", "恩").replace("呣", "母")
    pattern = re.compile("|".join(re.escape(p) for p in rep_map))
    t = pattern.sub(lambda x: rep_map[x.group()], text)
    return re.sub(r"[^一-龥" + "".join(re.escape(p) for p in punctuation) + r"]+", "", t)


rows = [r for r in csv.DictReader(open("research/文字校正/老师的母本/母本_修缮后.csv", encoding="utf-8-sig"))
        if r["keep"] == "1"]
zh = [r for r in rows if detect_lang(r["text"]) == "zh"]
mixed = [r for r in zh if en_words(r["text"])]
en_syl = sum(sum(syllable_count(w) for w in en_words(r["text"])) for r in mixed)
tot = sum(syllable_count(r["text"]) for r in rows)
print(f"kept {len(rows)}; zh-tagged {len(zh)}; en-tagged {len(rows) - len(zh)}; zh lines with English {len(mixed)}")
print(f"English words dropped from training phones: {sum(len(en_words(r['text'])) for r in mixed)}; "
      f"English syllables {en_syl} = {en_syl / tot:.1%} of all syllables")
print("lines not ending a sentence (export appends 。):", sum(1 for r in rows if not ends_sentence(r["text"])))
for r in mixed[:3]:
    print(" ", r["text"][:70], "\n   ->", replace_punctuation(r["text"])[:70])
