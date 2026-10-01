"""Demo only: put two typical ASR mistakes into the prepared voice so 「自动查找可能的错字」 has something to mark."""
import os
import sys
sys.path.insert(0, '<仓库>')

sys.path.insert(0, "<仓库>")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from voicetwin.config import load_config  # noqa: E402
from voicetwin.project import Project  # noqa: E402

cfg = load_config("config.yaml")
p = Project(cfg, "我的声音")
recs = p.load_manifest()
zh = [r for r in recs if r.get("lang") == "zh" and r.get("keep", True)]
zh[1]["text"] = "今天我们来学习 VFIXED 里面的列表推导式。"
zh[3]["text"] = "首先我们来看看看一个最简单简单的例子。"
p.save_manifest(recs)
p.export_csv(recs)
print("changed:", zh[1]["id"], zh[3]["id"])
