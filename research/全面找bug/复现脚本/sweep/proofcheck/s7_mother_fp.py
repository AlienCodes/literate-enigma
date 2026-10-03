"""老师自己逐句修缮过的母本（= 正确的文字）：自动查错字只按规则就会标红多少句？（全是误报）"""
from common import *
import collections
m = [x for _, x in tf.builtin_mother()]
recs = [{"id": f"m{i}", "text": t} for i, t in enumerate(m)]
vocab = pc.voice_vocab(recs)
freq = pc._frequent_caps(recs)
flag = 0
why = collections.Counter()
ex = collections.defaultdict(list)
for t in m:
    sus = pc.build_suspect(t, None, None, lang="zh", frequent=freq, vocab=vocab)
    if sus:
        flag += 1
        for s, e in sus["spans"]:
            w = t[s:e]
            why[w] += 1
            if len(ex[w]) < 2:
                ex[w].append(t)
print(f"rules alone flag {flag} of {len(m)} correct sentences")
for w, c in why.most_common(15):
    print(f"  {w!r}: {c}  e.g. {ex[w][0][:40]}")
# 第二个引擎听到的和母本完全一样（最好的情况）
flag2 = sum(1 for t in m if pc.build_suspect(t, t, None, engine="funasr", lang="zh", frequent=freq, vocab=vocab))
print(f"even when FunASR heard exactly the same text: {flag2} flagged")
