"""Independent check: after the one-click text fix is used (button grey), what does 下载改好的文字 say?
Also: can she actually follow its advice (upload as 母本 and click the one-click) on the same batch?"""
import sys, tempfile, shutil
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
from pathlib import Path
from conftest import make_cfg
from voicetwin import workflows as wf
from voicetwin.webui import app as A

tmp = Path(tempfile.mkdtemp(dir=sys.argv[1]))
try:
    cfg = make_cfg(tmp / "ws")
    V = "我的声音"
    project = wf.Project(cfg, V).ensure()
    texts = ["今天我们讲借词的用法", "艾子这个词表示原因", "大家把书翻到第三页", "这个句子的主语是什么"]
    project.save_manifest([{"id": f"c{i:03d}", "path": f"clips/c{i:03d}.wav", "text": t, "lang": "zh",
                            "duration": 3.0, "keep": True, "split": "train"} for i, t in enumerate(texts)])
    ui = A.WebUI(cfg)
    print("before: button interactive =", ui.textfix_btn(V)["interactive"])
    md0, f0 = ui.do_download_text(V)
    print("before: download message last para:", md0.split("\n\n")[1] if "\n\n" in md0 else md0)
    outs = list(ui.do_textfix(V))
    print("one-click ran, outputs:", len(outs))
    print("after: button interactive =", ui.textfix_btn(V)["interactive"])
    md, f = ui.do_download_text(V)
    print("after: full download message:\n" + md)
    print("---")
    # follow the advice: upload the downloaded txt as 母本 and click the one-click (old page where the button is still clickable)
    path = f["value"]
    outs2 = list(ui.do_textfix(V, [path]))
    last = outs2[-1]
    O = ui.TEXTFIX_OUT
    d = dict(zip(O, last))
    pb = d.get("proof_bar")
    print("following advice → proof_bar:", pb if isinstance(pb, str) else pb)
    print("transcript saved?", wf.transcript_info(cfg, V))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
