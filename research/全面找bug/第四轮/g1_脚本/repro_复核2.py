"""第四轮 g1 复核第 2 次发现的两个问题（不需要浏览器）。用法：python repro_复核2.py <仓库> <临时目录>

1. gradio 的临时文件放进工作文件夹（__gradio_cache）以后：老师点了听的片段被 gradio 复制到那里，老师在「文件夹路径」
   里填了包含工作文件夹的上一层，再点「开始准备素材」，这些副本又被当成新素材（片段数变多，同一段话重复）。
2. 第一次准备完素材（还没确认训练素材）：提示说先确认，「去「② 训练模型」 →」按钮却照样显示。"""
import hashlib
import os
import shutil
import sys
from pathlib import Path

REPO, TMP = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, REPO + "/tests")
sys.path.insert(0, REPO)
from conftest import make_cfg, make_lecture  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402
from voicetwin.webui import app as A  # noqa: E402
from voicetwin.webui import launcher  # noqa: E402

TMP.mkdir(parents=True, exist_ok=True)
root = TMP / "复核2"
shutil.rmtree(root, ignore_errors=True)

# ---- 1. __gradio_cache 里的副本
make_lecture(root / "讲课视频" / "第1课.wav", repeats=1)
cfg = make_cfg(root / "ws")
wf.run_prepare(cfg, "我的声音", [str(root / "讲课视频")])
proj = wf.Project(cfg, "我的声音")
n0 = len(proj.load_manifest())
os.environ.pop("GRADIO_TEMP_DIR", None)
cache = Path(launcher._use_workspace_cache(cfg))
for r in proj.load_manifest()[:3]:  # 老师在校对表里点了 3 行听：gradio 4.24 复制到 <临时文件夹>/<内容 hash>/<原名>
    src = proj.root / r["path"]
    d = cache / hashlib.sha1(src.read_bytes()).hexdigest()
    d.mkdir(exist_ok=True)
    shutil.copy2(src, d / src.name)
wf.run_prepare(cfg, "我的声音", [str(root)])  # 文件夹路径填的是包含工作文件夹的上一层
recs = proj.load_manifest()
print("1. 片段数：准备前", n0, "→ 再准备以后", len(recs))
print("   来源：", sorted({str(r.get("source")) for r in recs}))

# ---- 2. 准备完的「去「② 训练模型」 →」按钮
toasts = []
A._info = lambda m: toasts.append(m)
ui = A.WebUI(make_cfg(root / "ws2"))
last = dict(zip(ui.PREP_OUT, list(ui.do_prepare("g1", None, str(root / "讲课视频"), "none", "auto", "off", False))[-1]))
print("2. 提示：", toasts[-1])
print("   按钮：", {k: last["prep_next"].get(k) for k in ("value", "visible")})
shutil.rmtree(root, ignore_errors=True)
