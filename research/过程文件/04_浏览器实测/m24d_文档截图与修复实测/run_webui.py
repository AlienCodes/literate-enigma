import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from voicetwin.config import load_config  # noqa: E402
from voicetwin.webui.launcher import launch  # noqa: E402

launch(load_config(), host="127.0.0.1", port=7877)
