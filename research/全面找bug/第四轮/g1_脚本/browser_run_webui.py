import os
import sys

REPO, work, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.chdir(work)
sys.path.insert(0, REPO)
os.environ.pop("GRADIO_TEMP_DIR", None)  # 和老师一样没有设：临时文件应该放进工作文件夹的 __gradio_cache
from voicetwin.config import load_config  # noqa: E402
from voicetwin.webui.launcher import launch  # noqa: E402

launch(load_config(), host="127.0.0.1", port=port)
