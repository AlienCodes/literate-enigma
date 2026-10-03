"""变体在校对表里的样子：老师删掉多余的「看」、保存以后，「可能有错」列还标红「看看」吗？"""
import logging, re
from common import *
logging.disable(logging.CRITICAL)
from voicetwin.webui import app
for saved, heard, fixed in [("看看看这个例子", "看看看那个例子", "看看这个例子"),
                            ("定语从句定语从句 VFIXED 很重要", "定语从句定语从句 VFIXED 很重要", "定语从句 VFIXED 很重要"),
                            ("定语从句定语从句很重要", "定语从句定语从句很重要", "定语从句很重要")]:
    cfg, project = voice([saved])
    fake_engine({"c000": heard})
    pc.find_suspects(project, cfg)
    review.set_draft(project, "c000", text=fixed)
    review.save_rows(project)
    tbl = app._clips_table(cfg, "v", False)
    data = tbl["value"]["data"] if isinstance(tbl, dict) and "value" in tbl else getattr(tbl, "value", tbl)
    if isinstance(data, dict): data = data.get("data")
    hdr = app.CLIP_HEADERS
    row = data[0]
    sus_cell = [c for c in row if isinstance(c, str) and "vt-" in c]
    reds = [re.sub("<[^>]+>", "", m) for c in sus_cell for m in re.findall(r'<span class="vt-red[^>]*>(.*?)</span>', c)]
    print(f"{saved!r} -> {fixed!r}: red in table = {reds}")
