import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from voicetwin.config import load_config
from voicetwin.webui.app import build_app
app = build_app(load_config()); app.queue(); app.launch(server_name='127.0.0.1', server_port=7870, inbrowser=False)
