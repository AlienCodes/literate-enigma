"""Repro: upgrading while the old version's black window is still open. The old page has the same title
('声音分身 VoiceTwin v18', fixed since v18.0), so the new launcher treats it as 'already running', opens the OLD page
and exits -- the v18.5 banner never appears and the new features are not there."""
import json, threading, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, "/home/user/literate-enigma"); sys.path.insert(0, "/home/user/literate-enigma/tests")
PORT = 17931

class OldV184(BaseHTTPRequestHandler):   # stands in for a running v18.4 gradio page
    def do_GET(self):
        body = json.dumps({"title": "声音分身 VoiceTwin v18", "version": "4.24.0"}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", PORT), OldV184)
threading.Thread(target=srv.serve_forever, daemon=True).start()

from voicetwin.webui import launcher
import webbrowser
opened = []
webbrowser.open = lambda url, *a, **k: opened.append(url)
built = []
launcher._build = lambda cfg, local: built.append(1) or (_ for _ in ()).throw(SystemExit("new v18.5 app would be built"))
from conftest import make_cfg
import tempfile
cfg = make_cfg(tempfile.mkdtemp())
launcher.launch(cfg, port=PORT)
print("opened in browser:", opened, "| new app built:", bool(built))
srv.shutdown()
