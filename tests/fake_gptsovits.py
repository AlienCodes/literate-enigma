"""构造一个"假的" GPT-SoVITS 目录：脚本名、参数、环境变量、输出文件、日志格式都和真的一致，
但不做任何深度学习计算。用来验证 VoiceTwin 对 GPT-SoVITS 的训练编排和推理服务管理。

和真实 GPT-SoVITS（RVC-Boss/GPT-SoVITS @ 48b1a01）对照过的行为：
- 1-get-text.py：每处理一条素材打印一行文件名（xxx.wav）。
- 2-get-hubert-wav32k.py / 2-get-sv.py：不打印进度，每条素材写一个 4-cnhubert/xxx.wav.pt / 7-sv_cn/xxx.wav.pt。
- s2_train.py：打印「start training from epoch N」；logger 通过 basicConfig 打到 stdout，
  格式「INFO:<实验名>:Train Epoch: 3 [45%]」「INFO:<实验名>:====> Epoch: 3」；
  只在 epoch % save_every_epoch == 0 时保存（logs_s2_<版本>/G_233333333333.pth 用来接着练，
  以及 SoVITS_weights_<版本>/<名字>_e<轮>_s<步数>.pth）；logs_s2 里有 G_*.pth 时从上次的下一轮接着练。
- s1_train.py：Lightning 进度条写到 stderr，「Epoch 0:  50%|…」（轮数从 0 开始，用 \\r 刷新）；
  只在 (轮+1) % save_every_n_epoch == 0 时保存（<output_dir>/ckpt/epoch=<轮>-step=<步>.ckpt 和
  GPT_weights_<版本>/<名字>-e<轮+1>.ckpt）；ckpt 目录里有旧的 checkpoint 时接着练（打印 ckpt_path: …）。
- 显存不够时打印 PyTorch 的报错「torch.OutOfMemoryError: CUDA out of memory. …」并以退出码 1 结束。
- api_v2.py：合成出错时返回 400 {"message": "tts failed", "Exception": "<原因>"}。

测试用的开关（环境变量）：
- FAKE_GSV_OOM_ABOVE=N：每批数量大于 N 时，s2/s1 训练报显存不够。
- FAKE_GSV_CLIP_SLEEP=秒：1B / 声纹每条素材睡多久（默认 0.01），用来观察「数文件」的进度。
- FAKE_GSV_HANG=1：s2 训练一直不结束（并开一个子进程），用来测试「停止」会结束整个进程树。
- FAKE_GSV_API_DELAY=秒：推理服务启动前先等一会儿（模拟加载模型）。
- 合成的文字里有「【测试显存不够】」时，api 返回真实格式的合成失败。
"""

import json
import textwrap
from pathlib import Path

COMMON = '''
import os, sys, json, time
def need(*keys):
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print("missing env", missing); sys.exit(3)
def clip_names():
    lines = open(os.environ["inp_text"], encoding="utf8").read().strip("\\n").split("\\n")
    return [os.path.basename(l.split("|")[0]) for l in lines if l.strip()]
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
    print(os.path.basename(wav))  # 真实脚本 1-get-text.py:91 就是这样逐条打印文件名
    out.append(f"{wav}\\tph\\t1\\t{text}")
open(f"{opt}/2-name2text-{os.environ['i_part']}.txt", "w", encoding="utf8").write("\\n".join(out))
'''

GET_HUBERT = COMMON + '''
need("inp_text", "exp_name", "opt_dir", "cnhubert_base_dir", "i_part", "all_parts")
opt = os.environ["opt_dir"]
for d in ("4-cnhubert", "5-wav32k"):
    os.makedirs(f"{opt}/{d}", exist_ok=True)
sleep = float(os.environ.get("FAKE_GSV_CLIP_SLEEP", "0.01"))
for name in clip_names():
    hubert_path = f"{opt}/4-cnhubert/{name}.pt"
    if os.path.exists(hubert_path):  # 真实脚本也会跳过已经提取过的
        continue
    open(f"{opt}/5-wav32k/{name}", "wb").write(b"RIFF")
    open(hubert_path, "wb").write(b"pt")
    time.sleep(sleep)
'''

GET_SV = COMMON + '''
need("opt_dir", "sv_path")
assert os.path.exists(os.environ["sv_path"])
opt = os.environ["opt_dir"]
os.makedirs(opt + "/7-sv_cn", exist_ok=True)
sleep = float(os.environ.get("FAKE_GSV_CLIP_SLEEP", "0.01"))
for name in clip_names():
    sv_path = f"{opt}/7-sv_cn/{name}.pt"
    if os.path.exists(sv_path):
        continue
    assert os.path.exists(f"{opt}/5-wav32k/{name}"), name  # 真实脚本从 5-wav32k 读音频
    open(sv_path, "wb").write(b"pt")
    time.sleep(sleep)
'''

GET_SEMANTIC = COMMON + '''
need("inp_text", "exp_name", "opt_dir", "pretrained_s2G", "s2config_path", "i_part")
assert os.path.exists(os.environ["pretrained_s2G"])
assert os.path.exists(os.environ["s2config_path"])
opt = os.environ["opt_dir"]
names = [l.split("\\t")[0] for l in open(f"{opt}/2-name2text.txt", encoding="utf8").read().strip().split("\\n")]
open(f"{opt}/6-name2semantic-{os.environ['i_part']}.tsv", "w", encoding="utf8").write("\\n".join(f"{n}\\t1 2 3" for n in names))
'''

OOM = '''
def maybe_oom(bs):
    limit = os.environ.get("FAKE_GSV_OOM_ABOVE")
    if limit and bs > int(limit):
        print("Traceback (most recent call last):", flush=True)
        print('  File "GPT_SoVITS/train.py", line 1, in <module>', flush=True)
        print(f"torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB (GPU 0; 11.99 GiB total "
              f"capacity; 9.80 GiB already allocated; batch {bs})", flush=True)
        sys.exit(1)
'''

S2_TRAIN = '''
import json, math, os, subprocess, sys, time
''' + OOM + '''
cfg = json.load(open(sys.argv[sys.argv.index("--config") + 1], encoding="utf8"))
t = cfg["train"]
assert os.path.exists(t["pretrained_s2G"]) and os.path.exists(t["pretrained_s2D"])
exp_dir = cfg["data"]["exp_dir"]
assert os.path.exists(exp_dir + "/6-name2semantic.tsv")
assert cfg["model"]["version"] == cfg["version"]
assert os.path.isdir(exp_dir + "/4-cnhubert") and os.path.isdir(exp_dir + "/5-wav32k")
name = cfg["name"]
def info(msg):  # utils.py: logging.basicConfig(stream=sys.stdout, level=INFO) → 「INFO:<logger名>:<消息>」
    print(f"INFO:{os.path.basename(exp_dir)}:{msg}", flush=True)
n_items = len(open(exp_dir + "/2-name2text.txt", encoding="utf8").read().strip().split("\\n"))
steps_per_epoch = max(1, math.ceil(n_items / t["batch_size"]))
ckpt_dir = f"{exp_dir}/logs_s2_{cfg['model']['version']}"
latest = os.path.join(ckpt_dir, "G_233333333333.pth")
epoch_str = 1
if os.path.exists(latest):  # s2_train.py:206-221 自动接着上次练
    info("loaded D")
    epoch_str = int(open(latest).read().strip()) + 1
info(cfg)
maybe_oom(t["batch_size"])
if os.environ.get("FAKE_GSV_HANG"):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])  # 模拟 mp.spawn 的子进程
    open(exp_dir + "/fake_child.pid", "w").write(str(child.pid))
    print("start training from epoch %s" % epoch_str, flush=True)
    while True:
        info("Train Epoch: %d [%.0f%%]" % (epoch_str, 0.0))
        time.sleep(0.2)
print("start training from epoch %s" % epoch_str, flush=True)
os.makedirs(cfg["save_weight_dir"], exist_ok=True)
for e in range(epoch_str, t["epochs"] + 1):
    info("Train Epoch: {} [{:.0f}%]".format(e, 0.0))
    info("Train Epoch: {} [{:.0f}%]".format(e, 50.0))
    global_step = e * steps_per_epoch
    if e % t["save_every_epoch"] == 0:  # s2_train.py:514
        if t.get("if_save_latest"):
            os.makedirs(ckpt_dir, exist_ok=True)
            open(latest, "w").write(str(e))
            open(os.path.join(ckpt_dir, "D_233333333333.pth"), "w").write(str(e))
        if t.get("if_save_every_weights"):
            ck = f"{name}_e{e}_s{global_step}"
            open(f"{cfg['save_weight_dir']}/{ck}.pth", "wb").write(b"x" * 64)
            info("saving ckpt %s_e%s:%s" % (name, e, "Success."))
    info("====> Epoch: {}".format(e))
print("training done", flush=True)
'''

S1_TRAIN = '''
import os, re, sys, yaml
''' + OOM + '''
cfg = yaml.safe_load(open(sys.argv[sys.argv.index("--config_file") + 1], encoding="utf8"))
t = cfg["train"]
assert os.path.exists(cfg["pretrained_s1"])
assert os.path.exists(cfg["train_semantic_path"]) and os.path.exists(cfg["train_phoneme_path"])
assert os.environ.get("hz") == "25hz"
assert isinstance(t["if_dpo"], bool)
ckpt_dir = os.path.join(cfg["output_dir"], "ckpt")
os.makedirs(ckpt_dir, exist_ok=True)
start = 0
old = sorted(os.listdir(ckpt_dir))
ckpt_path = os.path.join(ckpt_dir, old[-1]) if old else None
print("ckpt_path:", ckpt_path, flush=True)
if ckpt_path:  # Lightning trainer.fit(ckpt_path=...) 接着上次练
    start = int(re.search(r"epoch=(\\d+)", ckpt_path).group(1)) + 1
maybe_oom(t["batch_size"])
os.makedirs(t["half_weights_save_dir"], exist_ok=True)
for e in range(start, t["epochs"]):
    # Lightning 的进度条写到 stderr，用 \\r 刷新同一行
    sys.stderr.write(f"Epoch {e}:  50%|█████     | 1/2 [00:00<00:00]\\r")
    sys.stderr.write(f"Epoch {e}: 100%|██████████| 2/2 [00:01<00:00]\\r")
    sys.stderr.flush()
    if (e + 1) % t["save_every_n_epoch"] == 0:  # s1_train.py:50
        if t.get("if_save_latest"):
            for f in os.listdir(ckpt_dir):
                os.remove(os.path.join(ckpt_dir, f))
        open(os.path.join(ckpt_dir, f"epoch={e}-step={(e + 1) * 2}.ckpt"), "w").write("x")
        if t.get("if_save_every_weights"):
            open(f"{t['half_weights_save_dir']}/{t['exp_name']}-e{e + 1}.ckpt", "wb").write(b"x" * 64)
sys.stderr.write("\\n")
'''

API_V2 = '''
import argparse, io, json, os, sys, threading, time, wave
import math, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import yaml

ap = argparse.ArgumentParser()
ap.add_argument("-a", default="127.0.0.1"); ap.add_argument("-p", type=int, default=9880); ap.add_argument("-c")
args = ap.parse_args()
cfg = yaml.safe_load(open(args.c, encoding="utf8"))["custom"]
state = {"gpt": cfg["t2s_weights_path"], "sovits": cfg["vits_weights_path"], "calls": 0}
time.sleep(float(os.environ.get("FAKE_GSV_API_DELAY", "0") or 0))  # 真实的服务加载模型要几十秒

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
        if "【测试显存不够】" in req["text"]:  # api_v2.py:444-445 的真实返回格式
            return self._json(400, {"message": "tts failed",
                                    "Exception": "CUDA out of memory. Tried to allocate 1.00 GiB"})
        data = make_wav(req["text"], float(req.get("speed_factor", 1.0)), state["gpt"])
        self.send_response(200); self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

srv = ThreadingHTTPServer((args.a, args.p), H)
print("fake api_v2 ready", flush=True)
srv.serve_forever()
'''

#: 真实的模型文件都有几百 MB；这里写 2 KB，刚好超过「小于 1 KB 算没下载完」的门槛
FAKE_WEIGHT = b"x" * 2048


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
    # 和 Hugging Face 上 lj1995/GPT-SoVITS 里这两个文件夹的文件一致
    for d in ("chinese-roberta-wwm-ext-large", "chinese-hubert-base"):
        (pm / d / "config.json").write_text("{}", encoding="utf-8")
        (pm / d / "pytorch_model.bin").write_bytes(FAKE_WEIGHT)
    (pm / "chinese-roberta-wwm-ext-large" / "tokenizer.json").write_text("{}", encoding="utf-8")
    (pm / "chinese-hubert-base" / "preprocessor_config.json").write_text("{}", encoding="utf-8")
    for f in ("v2Pro/s2Gv2Pro.pth", "v2Pro/s2Dv2Pro.pth", "v2Pro/s2Gv2ProPlus.pth", "v2Pro/s2Dv2ProPlus.pth", "s1v3.ckpt",
              "sv/pretrained_eres2netv2w24s4ep4.ckpt", "gsv-v2final-pretrained/s2G2333k.pth",
              "gsv-v2final-pretrained/s2D2333k.pth",
              "gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"):
        (pm / f).write_bytes(FAKE_WEIGHT)
    return root
