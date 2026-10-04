# 复查（第四轮 g2 的检查意见）用的复现脚本，原样保留；不给参数就用这个仓库：/tmp/gsv39/bin/python 复查_p4_corr.py
import sys
from pathlib import Path
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]; sys.path[:0] = [str(ROOT)]
from voicetwin.data import lexicon_fix as lf
lex = lf.Lexicon.build([])
for t in ["be动词是一个系统词，后面要接表语。", "这里的is是系统词，不是实义动词。", "这个是系统词库里面的词。",
          "我们来看系统词和实义动词的区别。", "这个who在这里修饰进行词the man。", "接下来我们进行词的辨析，看看这两个词有什么区别。"]:
    print(t, [(f.start, f.end, f.rep, f.direct) for f in lex.find(t)])
