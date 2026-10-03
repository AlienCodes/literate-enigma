import os, sys
os.chdir(sys.argv[2])
sys.path.insert(0, "/home/user/literate-enigma")
from voicetwin.config import load_config
from voicetwin.webui.launcher import launch
launch(load_config(), host="127.0.0.1", port=int(sys.argv[1]))
