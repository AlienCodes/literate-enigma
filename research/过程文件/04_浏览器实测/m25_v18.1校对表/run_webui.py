import os
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from voicetwin.config import load_config  # noqa: E402
from voicetwin.webui.launcher import launch  # noqa: E402

launch(load_config(), host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 7901)
