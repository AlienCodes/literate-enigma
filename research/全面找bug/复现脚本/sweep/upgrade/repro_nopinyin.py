"""Machine without pypinyin / jieba: the one-click runs in a weaker mode, tells the teacher to reinstall with option 1,
but the button is already locked for this batch, so after reinstalling she can never run the full check."""
import sys
sys.modules["pypinyin"] = None  # import pypinyin -> ImportError (like the independent .venv install route)
sys.modules["jieba"] = None
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin.webui import app as A
from voicetwin.data import transcript_fix as tf
WS = Path(sys.argv[1]); V = "我的声音"
cfg = make_cfg(WS); ui = A.WebUI(cfg)
print("has_pinyin:", tf.has_pinyin())
outs = list(ui.do_textfix(V))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
md = str(last["proof_md"])
print("warning shown:", "pypinyin" in md, "|", [l for l in md.split("\n") if "pypinyin" in l][0][:140])
print("button after:", ui.textfix_btn(V)["interactive"])
