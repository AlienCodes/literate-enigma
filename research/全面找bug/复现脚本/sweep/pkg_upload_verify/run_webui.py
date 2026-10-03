import os, sys
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
os.chdir(sys.argv[2])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.app import build_app
app = build_app(load_config())
app.queue()
app.launch(server_name="127.0.0.1", server_port=int(sys.argv[1]), inbrowser=False, show_api=False, quiet=True)
