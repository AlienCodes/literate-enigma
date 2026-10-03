"""Independent repro: confirm, then an unsaved edit -> what does the header say vs. training gate?"""
import sys, json, tempfile, shutil
from pathlib import Path
ROOT = sys.argv[1]            # code root to test (HEAD extract or the working tree)
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/tests")
from conftest import make_cfg, make_lecture
from voicetwin import workflows as wf
from voicetwin.webui import app as A
import voicetwin
print("code from:", Path(voicetwin.__file__).resolve().parent)

VOICE = "测试声音"
work = Path(tempfile.mkdtemp(prefix="cd_", dir=sys.argv[2]))
try:
    make_lecture(work / "lec" / "第1课.wav")
    cfg = make_cfg(work / "ws")
    wf.run_prepare(cfg, VOICE, [str(work / "lec")])
    ui = A.WebUI(cfg)
    md, count, rows = ui.do_confirm(VOICE)
    print("1) after confirm header has 已确认:", "训练素材已确认" in count)
    print("   training_blocker:", repr(wf.training_blocker(wf.Project(cfg, VOICE))))
    rid = [r["id"] for r in wf.Project(cfg, VOICE).load_manifest() if not r.get("deleted")][2]
    out = ui.do_clip_action(VOICE, json.dumps({"action": "edit", "id": rid, "no": "3", "text": "首先我们看一个最最简单的例子。"}, ensure_ascii=False))
    msg, count2 = out[0], out[1]
    print("2) edit msg:", msg)
    hdr = count2 if isinstance(count2, str) else A._clips_count_md(cfg, VOICE)
    conf_lines = [l for l in hdr.split("\n\n") if "确认" in l]
    print("   header confirm-related paragraphs:")
    for l in conf_lines:
        print("     |", l)
    print("   header shows plain '✅ **训练素材已确认**':", "✅ **训练素材已确认**" in hdr)
    print("   header shows unsaved note:", "没有保存" in hdr)
    why = wf.training_blocker(wf.Project(cfg, VOICE))
    print("3) training_blocker:", repr(why))
    first = next(ui.do_train(VOICE, "dummy", 0, 0, 0, 0))
    d = dict(zip(ui.TRAIN_OUT, first))
    print("4) do_train first output train_log:", d.get("train_log"))
    print("   voice status line:", A._voice_status_md(cfg, VOICE).split("\n")[0])
    # after saving, header should not claim confirmed (signature changed)
    sv = ui.do_save(VOICE)
    hdr3 = sv[1]
    print("5) after save: plain confirmed?", "✅ **训练素材已确认**" in hdr3, "| re-confirm prompt?", "再点一次" in hdr3)
    print("   blocker after save:", repr(wf.training_blocker(wf.Project(cfg, VOICE)))[:80])
finally:
    shutil.rmtree(work, ignore_errors=True)
