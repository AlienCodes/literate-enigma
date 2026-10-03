from common import *
from voicetwin.webui import app as A
ws = Path(sys.argv[1]); cfg = make_cfg(ws); ui = A.WebUI(cfg)
print("BLOCK:", BLOCK, "has_pinyin:", tf.has_pinyin(), "has_jieba:", lf.has_jieba())
print("button now:", ui.textfix_btn(V)["interactive"])
outs = list(ui.do_textfix(V))
last = dict(zip(ui.TEXTFIX_OUT, outs[-1]))
print("click result bar:", str(last.get("proof_bar"))[:300])
print("tr_info:", str(last.get("tr_info"))[:200])
