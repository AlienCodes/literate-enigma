from common import *
m = tf.builtin_mother()
print(len(m)); import random
random.seed(3)
cands = [x for _, x in m if 14 <= len(x) <= 30]
texts = []
for x in random.sample(cands, 40):
    # 把一个字换成同音的另一个字（模拟识别错）
    from pypinyin import lazy_pinyin
    i = random.randrange(2, len(x)-2)
    texts.append(x[:i] + "了" + x[i+1:])
cfg, project = voice(texts, write_wav=False)
res = tf.check_with_transcript(project)
draft = review.load_draft(project)
n=0
for r in project.load_manifest():
    s = r.get("suspect")
    if s and s.get("src") == "transcript" and r["id"] not in draft:
        t = r["text"]; info = review.analyze(r, t)
        if info["edits"]:
            n+=1
            if n<=5: print(r["id"], t, [(t[a:b], c) for a,b,c in info["edits"]], "sure" if info["sure"] else "unsure")
print("rows with suggestion but no direct fix:", n, "of", len(texts), "; direct-fixed rows:", len(draft))
