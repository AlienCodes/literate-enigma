"""v18.4 浏览器实测的准备：假整合包（推理服务用真实的 api_v2.py，只有模型是假的）+ 合成的讲课录音 + 准备素材（还没确认训练素材）。"""
import sys
from pathlib import Path

REPO = "/home/user/literate-enigma"
sys.path.insert(0, REPO + "/tests")
sys.path.insert(0, REPO)
from conftest import make_lecture  # noqa: E402
from fake_gptsovits import build_fake_root  # noqa: E402

root = Path(sys.argv[1]).resolve()
build_fake_root(root / "GSV", real_api=True)
lect = root / "lectures"
lect.mkdir(exist_ok=True)
make_lecture(lect / "第1课.wav", repeats=2)
# GPT-SoVITS 的子进程用系统的 Python 3.11（装着 fastapi / uvicorn），网页用和整合包同版本的 Python 3.9 + gradio 4.24
(root / "config.yaml").write_text("""workspace: ./ws
backend: gptsovits
speaker_encoder: mfcc
backends:
  gptsovits:
    root: ./GSV
    python: /usr/local/bin/python3
    startup_timeout: 60
    train:
      sovits_epochs: 2
      gpt_epochs: 2
      batch_size: 2
prepare:
  asr:
    engine: none
similarity:
  model_dir: ./sv
""", encoding="utf-8")
import os  # noqa: E402

os.chdir(root)
from voicetwin.config import load_config  # noqa: E402
from voicetwin import workflows as wf  # noqa: E402

cfg = load_config()
wf.run_prepare(cfg, "老师的声音", [str(lect)])
print("ok")
