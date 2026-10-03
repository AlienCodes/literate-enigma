"""真实路径：9 句、3 秒「像说话」的音频（不是全 0，过滤器不会把所有行都变灰）。
1) 自动查找：c000 标红「十」；2) 老师把 c000 删短（还留着「十」），点这一行的「保存」→ 程序重新过滤，c000 变灰（语速异常）；
3) 再点自动查找；4) 老师在灰色的 c000 点「✅ 这一条也要用」（没保存），再点自动查找。每一步对比：提示里的数字、表格上方的数字、表格里的红行。"""
import re, json, logging
import numpy as np, soundfile as sf
from common import *
from voicetwin.webui import app as A

logging.disable(logging.CRITICAL)
A._info = lambda *a, **k: None
COL = A.CLIP_HEADERS.index(A.COL_SUSPECT)

texts = ["我们今天讲十个函数呀", "下面我们来看第二个例子", "那么到底什么是定语从句", "我们先来看这个句子结构",
         "这个句子的主语是什么呢", "今天我们继续讲这个语法", "大家看一下黑板上的例子", "这里的动词要用过去时态",
         "最后我们来做一个小练习"]
heard = {f"c{i:03d}": t for i, t in enumerate(texts)}
heard["c000"] = "我们今天讲是个函数呀"
cfg, project = voice(texts)
rng = np.random.default_rng(0)
for r in project.load_manifest():
    sr = 16000
    t = np.arange(int(3.0 * sr)) / sr
    env = (np.sin(2 * np.pi * 3.5 * t) > -0.2).astype(np.float32)  # 一段一段的「音节」，中间有停顿
    wav = 0.1 * rng.standard_normal(t.size).astype(np.float32) * env
    sf.write(str(project.root / r["path"]), wav, sr)
recs = project.load_manifest()
for k, r in enumerate(recs):
    r.update(source="lesson1.mp4", start=k * 3.0, end=k * 3.0 + 3.0)
project.save_manifest(recs)
fake_engine(heard)
ui = A.WebUI(cfg)


def look(label, last=None):
    count, rows = ui.refresh_clips("v", False, None)
    _, rows_sus = ui.refresh_clips("v", True, None)
    m = re.search(r"\*\*(\d+)\*\* 条可能有错", count)
    mm = re.search(r"其中 \*\*(\d+)\*\* 条可能有错", last["proof_md"]) if last else None
    unused = [r[1] for r in rows if A.FLAG_UNUSED in str(r[-1])]
    out = {"message": last["proof_md"].splitlines()[0] if last else None,
           "message_count": (int(mm.group(1)) if mm else 0) if last else None,
           "header_count": int(m.group(1)) if m else 0,
           "red_rows": [r[1] for r in rows if "vt-red" in str(r[COL]) or "vt-sus" in str(r[COL])],
           "only_sus_rows": [r[1] for r in rows_sus], "grey_rows": unused}
    print(f"[{label}]", json.dumps(out, ensure_ascii=False))


def proof():
    outs = list(ui.do_proofcheck("v", False))
    return dict(zip(ui.PROOF_OUT, outs[-1]))


# 先像网页一样保存一次（重新统计），确认一开始都能用
wf.apply_review(cfg, "v", read_csv=False)
look("0 start")
look("1 auto check", proof())
r = ui.do_clip_action("v", json.dumps({"action": "edit", "id": "c000", "no": "1", "text": "讲十个"}), False)
print("   edit:", r[0])
r = ui.do_clip_action("v", json.dumps({"action": "save_row", "id": "c000", "no": "1"}), False)
print("   save:", r[0].splitlines()[0])
rec = {x["id"]: x for x in project.load_manifest()}["c000"]
print("   c000 keep =", rec.get("keep"), "drop_reason =", rec.get("drop_reason"))
look("2 after save")
look("3 auto check again", proof())
r = ui.do_clip_action("v", json.dumps({"action": "use", "id": "c000", "no": "1"}), False)
print("   use:", r[0])
look("4a after use (unsaved)")
look("4b auto check again", proof())
r = ui.do_clip_action("v", json.dumps({"action": "save_row", "id": "c000", "no": "1"}), False)
print("   save:", r[0].splitlines()[0])
look("5a after saving 'use'")
look("5b auto check again", proof())
r = ui.do_clip_action("v", json.dumps({"action": "delete", "id": "c000", "no": "1"}), False)
print("   delete:", r[0].splitlines()[0])
look("6 deleted (purple), auto check again", proof())
