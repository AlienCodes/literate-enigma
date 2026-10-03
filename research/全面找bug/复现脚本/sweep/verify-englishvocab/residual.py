"""当前代码：报告里的机制（confusable 规则 + if_heur 拼进中文）之外的相关情况。只调用 build_suspect（不加载模型）。"""
import sys
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.data import proofcheck as pc, transcript_fix as tf
m = [x for _, x in tf.builtin_mother()]
vocab = pc.english_vocab([{"id": "x", "text": t} for t in m[:3]])  # 新声音：素材很少，靠母本词表
cases = [
    ("Whose后面一定要接名词", "户字后面一定要接名词"),
    ("ｗｈｙ引导的从句", "外引导的从句"),
    ("关系代词有who、whose、which和that", "关系代词有胡户字威奇和则特"),
    ("whose、why、he三个词都很常见", "户字外喜三个词都很常见"),
    ("比如说这个句子I would like to study English where it's quiet就是由主句", "比如说这个句子爱伍德莱克图斯塔迪英格利希威尔伊茨快尔就是由主句"),
    ("how引导感叹句", "好引导感叹句"),  # how 不在母本、只出现一次：设计上仍会标（可能是把「好」听成 how）
]
for t, h in cases:
    s = pc.build_suspect(t, h, None, engine=pc.ENGINE_FUNASR, lang="zh", vocab=vocab)
    if s:
        print(f"FLAG {t!r}: red={[t[a:b] for a, b in s['spans']]} alt={s['alt']!r} score={s['score']} reasons={s['reasons']}")
    else:
        print(f"ok   {t!r}")
