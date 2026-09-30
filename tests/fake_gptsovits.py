"""构造一个"假的" GPT-SoVITS 目录：脚本名、参数、环境变量、输出文件都和真的一致，
但不做任何深度学习计算。用来验证 VoiceTwin 对 GPT-SoVITS 的训练编排和推理服务管理。"""

import json
import textwrap
from pathlib import Path

COMMON = '''
import os, sys, json
def need(*keys):
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print("missing env", missing); sys.exit(3)
'''

GET_TEXT = COMMON + '''
need("inp_text", "inp_wav_dir", "exp_name", "opt_dir", "bert_pretrained_dir", "i_part", "all_parts", "version", "is_half")
assert os.environ["version"] == os.environ.get("EXPECT_VERSION", "v2ProPlus"), os.environ["version"]
assert os.path.isdir(os.environ["bert_pretrained_dir"])
# GPT-SoVITS 依赖 PYTHONPATH 里有 GPT_SoVITS 目录
assert any(p.endswith("GPT_SoVITS") for p in os.environ["PYTHONPATH"].split(os.pathsep))
opt = os.environ["opt_dir"]; os.makedirs(opt, exist_ok=True)
lines = open(os.environ["inp_text"], encoding="utf8").read().strip("\\n").split("\\n")
out = []
for line in lines:
    wav, spk, lang, text = line.split("|")
    assert lang in ("zh", "en"), lang
    assert os.path.exists(os.path.join(os.environ["inp_wav_dir"], wav)), wav
    out.append(f"{wav}\\tph\\t1\\t{text}")
open(f"{opt}/2-name2text-{os.environ['i_part']}.txt", "w", encoding="utf8").write("\\n".join(out))
'''

GET_HUBERT = COMMON + '''
need("inp_text", "exp_name", "opt_dir", "cnhubert_base_dir", "i_part", "all_parts")
opt = os.environ["opt_dir"]
for d in ("4-cnhubert", "5-wav32k"):
    os.makedirs(f"{opt}/{d}", exist_ok=True)
'''

GET_SV = COMMON + '''
need("opt_dir", "sv_path")
assert os.path.exists(os.environ["sv_path"])
os.makedirs(os.environ["opt_dir"] + "/7-sv_cn", exist_ok=True)
'''

GET_SEMANTIC = COMMON + '''
need("inp_text", "exp_name", "opt_dir", "pretrained_s2G", "s2config_path", "i_part")
assert os.path.exists(os.environ["pretrained_s2G"])
assert os.path.exists(os.environ["s2config_path"])
opt = os.environ["opt_dir"]
names = [l.split("\\t")[0] for l in open(f"{opt}/2-name2text.txt", encoding="utf8").read().strip().split("\\n")]
open(f"{opt}/6-name2semantic-{os.environ['i_part']}.tsv", "w", encoding="utf8").write("\\n".join(f"{n}\\t1 2 3" for n in names))
'''

S2_TRAIN = '''
import json, os, sys
cfg = json.load(open(sys.argv[sys.argv.index("--config") + 1], encoding="utf8"))
t = cfg["train"]
assert os.path.exists(t["pretrained_s2G"]) and os.path.exists(t["pretrained_s2D"])
assert os.path.exists(cfg["data"]["exp_dir"] + "/6-name2semantic.tsv")
assert cfg["model"]["version"] == cfg["version"]
os.makedirs(cfg["save_weight_dir"], exist_ok=True)
for e in range(1, t["epochs"] + 1):
    print(f"====> Epoch: {e}", flush=True)
    if e % t["save_every_epoch"] == 0 or e == t["epochs"]:
        open(f"{cfg['save_weight_dir']}/{cfg['name']}_e{e}_s{e * 10}.pth", "wb").write(b"x")
'''

S1_TRAIN = '''
import os, sys, yaml
cfg = yaml.safe_load(open(sys.argv[sys.argv.index("--config_file") + 1], encoding="utf8"))
t = cfg["train"]
assert os.path.exists(cfg["pretrained_s1"])
assert os.path.exists(cfg["train_semantic_path"]) and os.path.exists(cfg["train_phoneme_path"])
assert os.environ.get("hz") == "25hz"
os.makedirs(t["half_weights_save_dir"], exist_ok=True)
for e in range(1, t["epochs"] + 1):
    print(f"Epoch {e}: 100%", flush=True)
    if e % t["save_every_n_epoch"] == 0 or e == t["epochs"]:
        open(f"{t['half_weights_save_dir']}/{t['exp_name']}-e{e}.ckpt", "wb").write(b"x")
'''

API_V2 = '''
import argparse, io, json, os, sys, threading, wave
import math, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import yaml

ap = argparse.ArgumentParser()
ap.add_argument("-a", default="127.0.0.1"); ap.add_argument("-p", type=int, default=9880); ap.add_argument("-c")
args = ap.parse_args()
cfg = yaml.safe_load(open(args.c, encoding="utf8"))["custom"]
state = {"gpt": cfg["t2s_weights_path"], "sovits": cfg["vits_weights_path"], "calls": 0}

def make_wav(text, speed, gpt_path):
    sr = 32000
    # 时长与文字长度成正比；不同 GPT 权重读得快慢不同（模拟不同 epoch 的差异）
    epoch = int(gpt_path.rsplit("-e", 1)[-1].split(".")[0]) if "-e" in gpt_path else 1
    dur = max(0.5, len(text) * (0.2 + 0.01 * epoch) / max(speed, 0.1))
    n = int(dur * sr)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        pad = int(0.2 * sr)
        frames = bytearray()
        for i in range(n + 2 * pad):
            v = 0.0
            if pad <= i < n + pad:
                t = i / sr
                v = 0.3 * math.sin(2 * math.pi * 150 * t) * (0.6 + 0.4 * math.sin(2 * math.pi * 4 * t))
            frames += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(frames))
    return buf.getvalue()

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, code, obj):
        body = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/tts":
            return self._json(400, {"message": "ref_audio_path is required"})
        if u.path in ("/set_gpt_weights", "/set_sovits_weights"):
            p = q.get("weights_path", "")
            if not os.path.exists(p):
                return self._json(400, {"message": "not found"})
            state["gpt" if "gpt" in u.path else "sovits"] = p
            body = b"success"; self.send_response(200); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body); return
        if u.path == "/control" and q.get("command") == "exit":
            self._json(200, {}); threading.Thread(target=srv.shutdown).start(); return
        self._json(404, {"message": "no"})
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        for k in ("text", "text_lang", "ref_audio_path", "prompt_lang"):
            if not req.get(k):
                return self._json(400, {"message": f"{k} is required"})
        if not os.path.exists(req["ref_audio_path"]):
            return self._json(400, {"message": "ref missing"})
        assert req["text_split_method"] == "cut0"
        data = make_wav(req["text"], float(req.get("speed_factor", 1.0)), state["gpt"])
        self.send_response(200); self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

srv = ThreadingHTTPServer((args.a, args.p), H)
print("fake api_v2 ready", flush=True)
srv.serve_forever()
'''


def build_fake_root(root: Path, version: str = "v2ProPlus") -> Path:
    root = Path(root)
    files = {
        "api_v2.py": API_V2,
        "GPT_SoVITS/prepare_datasets/1-get-text.py": GET_TEXT,
        "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py": GET_HUBERT,
        "GPT_SoVITS/prepare_datasets/2-get-sv.py": GET_SV,
        "GPT_SoVITS/prepare_datasets/3-get-semantic.py": GET_SEMANTIC,
        "GPT_SoVITS/s2_train.py": S2_TRAIN,
        "GPT_SoVITS/s1_train.py": S1_TRAIN,
    }
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content), encoding="utf-8")
    cfgs = root / "GPT_SoVITS" / "configs"
    cfgs.mkdir(parents=True, exist_ok=True)
    s2 = {"train": {"fp16_run": True, "batch_size": 4, "epochs": 1}, "model": {"version": "v2"}, "data": {}}
    for name in ("s2.json", "s2v2Pro.json", "s2v2ProPlus.json"):
        (cfgs / name).write_text(json.dumps(s2), encoding="utf-8")
    (cfgs / "s1longer-v2.yaml").write_text("train:\n  batch_size: 8\n  epochs: 20\n  precision: 16-mixed\n", encoding="utf-8")
    pm = root / "GPT_SoVITS" / "pretrained_models"
    for d in ("chinese-roberta-wwm-ext-large", "chinese-hubert-base", "gsv-v2final-pretrained", "v2Pro", "sv"):
        (pm / d).mkdir(parents=True, exist_ok=True)
    for f in ("v2Pro/s2Gv2Pro.pth", "v2Pro/s2Dv2Pro.pth", "v2Pro/s2Gv2ProPlus.pth", "v2Pro/s2Dv2ProPlus.pth", "s1v3.ckpt",
              "sv/pretrained_eres2netv2w24s4ep4.ckpt", "gsv-v2final-pretrained/s2G2333k.pth",
              "gsv-v2final-pretrained/s2D2333k.pth",
              "gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"):
        (pm / f).write_bytes(b"x")
    return root
