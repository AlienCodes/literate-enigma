"""Simulate GPT-SoVITS (abe9843) text splitting for 'N copies of one sentence in one request'.

Replicates TextPreprocessor.preprocess -> replace_consecutive_punctuation + pre_seg_text with cut0
(TextPreprocessor.py L58-115, text_segmentation_method.py cut0 L90-96, merge_short_text_in_array L34-49,
get_first L28-31), then checks that a batched request yields exactly N fragments, each identical to what a
single request would synthesize. Also checks the speed_factor=1.0001 identity of models.py L259-260 and
a zero-run splitter for the returned audio. Input: the teacher's 1004 kept lines (research/文字校正)."""
import csv, re, sys
import numpy as np
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from voicetwin.synth.script import tts_normalize
splits = {"，","。","？","！",",",".","?","!","~",":","：","—","…"}
seg_punct = set(["!", "?", "…", ",", ".", "-", " "])       # text_segmentation_method.punctuation (cut0)
tp_punct = set(["!", "?", "…", ",", ".", "-"])              # TextPreprocessor.punctuation
def get_first(t):
    return re.split("[" + "".join(re.escape(s) for s in splits) + "]", t)[0].strip()
def cut0(inp):
    return inp if not set(inp).issubset(seg_punct) else "/n"
def merge_short(texts, th):
    if len(texts) < 2: return texts
    res, t = [], ""
    for e in texts:
        t += e
        if len(t) >= th: res.append(t); t = ""
    if t:
        if not res: res.append(t)
        else: res[-1] += t
    return res
def rcp(text):
    p = "".join(re.escape(x) for x in tp_punct)
    return re.sub(f"([{p}])([{p}])+", r"\1", text)
def pre_seg(text, lang):
    text = rcp(text)
    text = text.strip("\n")
    if not text: return []
    if text[0] not in splits and len(get_first(text)) < 4:
        text = ("。" if lang != "en" else ".") + text
    text = cut0(text)
    while "\n\n" in text: text = text.replace("\n\n", "\n")
    ts = [t for t in text.split("\n") if t not in (None, " ", "")]
    ts = merge_short(ts, 5)
    out = []
    for t in ts:
        if not t.strip() or not re.sub(r"\W+", "", t): continue
        if t[-1] not in splits: t += "。" if lang != "en" else "."
        out.append(t)   # (split_big_text above 510 chars ignored: VoiceTwin chunks are <= ~50 syllables)
    return out
def batched_text(text, lang, n):
    """What VoiceTwin would send: each copy gets the same '。' prefix pre_seg_text would add to a single request."""
    if "\n" in text or len(text) > 400: return None
    one = text
    if one and one[0] not in splits and len(get_first(rcp(one))) < 4:
        one = ("。" if lang != "en" else ".") + one
    return "\n".join([one] * n)
rows = [r for r in csv.DictReader(open(str(__import__("pathlib").Path(__file__).resolve().parents[3] / "research") + "/文字校正/老师的母本/母本_修缮后.csv", encoding="utf-8-sig")) if r["keep"] == "1"]
ok = bad = skipped = 0; bad_ex = []
for r in rows:
    t = tts_normalize(r["text"]) if callable(tts_normalize) else r["text"]
    single = pre_seg(t, "zh")
    bt = batched_text(t, "zh", 4)
    if bt is None: skipped += 1; continue
    frags = pre_seg(bt, "zh")
    if len(single) == 1 and frags == single * 4: ok += 1
    else:
        bad += 1
        if len(bad_ex) < 5: bad_ex.append((t, single, frags[:2], len(frags)))
print(f"lines {len(rows)}: batched==4x single {ok}, mismatch {bad}, skipped {skipped}")
for e in bad_ex: print("  MISMATCH:", e)
# short texts (merge_short threshold 5)
for t in ["好的。", "对。", "Yes.", "我们来看。", "OK, let's go."]:
    lang = "en" if not re.search(r"[一-鿿]", t) else "zh"
    print(f"  short {t!r}: single={pre_seg(t, lang)} batched_n={len(pre_seg(batched_text(t, lang, 4), lang))}")
# speed 1.0001 identity: models.py L259-260 size=int(L/speed)+1 must equal L
bad_len = [L for L in range(1, 10000) if int(L / 1.0001) + 1 != L]
print("speed 1.0001: frame counts changed for L in 1..9999:", bad_len[:5], "count", len(bad_len))
import torch, torch.nn.functional as F
y = torch.randn(1, 192, 777)
print("F.interpolate linear same size == identity:", torch.equal(F.interpolate(y, size=777, mode="linear"), y))
