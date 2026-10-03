import sys
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.data import proofcheck as pc
t = "比如说这个句子I would like to read books where it's quiet就是一个例子"
h = "比如说这个句子爱伍德莱克图瑞德布克斯威尔伊茨快尔就是一个例子"
c = pc.compare(t, h, engine=pc.ENGINE_FUNASR, vocab=pc.english_vocab([]))
print("ratio", c.ratio, "total", c.total, [(e.kind, e.weight) for e in c.evidence])
print(pc.build_suspect(t, h, None, engine=pc.ENGINE_FUNASR, lang="zh", vocab=pc.english_vocab([])))
t2 = "比如说这个句子I would like to study English where it's quiet就是由主句"
h2 = "比如说这个句子爱伍德莱克图斯塔迪英格利希威尔伊茨快尔就是由主句"
c = pc.compare(t2, h2, engine=pc.ENGINE_FUNASR, vocab=pc.english_vocab([]))
print("ratio", c.ratio, "total", c.total)
