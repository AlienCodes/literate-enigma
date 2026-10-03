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
- api_v2.py（对照 api_v2.py @ abe9843，也就是老师电脑上的版本）：
  - 不带参数的 GET /tts 会报错回 500（真实代码在检查参数之前先做 text_lang.lower()）——
    v18.2 以前这里写成了回 400，和真的不一样，所以没测出「引擎永远等不到就绪」的问题；
  - GET /control 不带 command 回 400 {"message": "command is required"}；command=exit 结束自己；
  - /set_gpt_weights、/set_sovits_weights 成功回 200 {"message": "success"}，失败回 400；
  - 合成出错时返回 400 {"message": "tts failed", "Exception": "<原因>"}。
  另外 tests/gsv_real/ 里有真实的 api_v2.py，test_gsv_real_api.py 直接拿它测（只把模型换成假的）。

测试用的开关（环境变量）：
- FAKE_GSV_OOM_ABOVE=N：每批数量大于 N 时，s2/s1 训练报显存不够。
- FAKE_GSV_CLIP_SLEEP=秒：1B / 声纹每条素材睡多久（默认 0.01），用来观察「数文件」的进度。
- FAKE_GSV_HANG=1：s2 训练一直不结束（并开一个子进程），用来测试「停止」会结束整个进程树。
- FAKE_GSV_API_DELAY=秒：推理服务启动前先等一会儿（模拟加载模型）。
- 合成的文字里有「【测试显存不够】」时，api 和真的一样：记录里打印 Traceback，回 200 + 1 秒静音。
- FAKE_GSV_MAX_BATCH=N：合成请求的 batch_size 大于 N 时，和真的显存不够一样：记录里打印「CUDA out of memory」的
  Traceback，回 200 + 1 秒 16 kHz 的静音。
- FAKE_GSV_SPEED_TRICK_BROKEN=1：语速不是 1.0 时声音长 5%（模拟「语速写成 1.0001」在某个版本上和 1.0 不一样）。
- FAKE_GSV_INNER_ZERO=1：每一段声音中间都有 0.4 秒的数字静音（模拟同时生成的几个版本切不开）。

一次请求同时生成好几个版本（文字里有换行，「一模一样」档）：和真的 pre_seg_text 一样按换行切开（不到 5 个字的段和后面的
合在一起），每段一个不同音高的正弦波（150 + 10 × ((seed + 第几段) % 7) Hz，长短按这一段的字数、模型轮数和语速算），
每段后面补 fragment_interval 秒的 0（TTS.py 的 audio_postprocess）。没有换行（一次一个）时和以前完全一样（150 Hz）。
两个推理服务都把每次合成请求记下来（真实 api_v2 的在 _real_api_calls.jsonl，模拟版的在 _fake_api_calls.jsonl）。
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
# 真实的 s2_train.py 不建 save_weight_dir（只有官方 webui.py 会建）；没有这个文件夹时存不下模型（process_ckpt.savee 吞掉报错）
weights_ok = os.path.isdir(cfg["save_weight_dir"])
if not weights_ok:
    print("saving ckpt failed: [Errno 2] No such file or directory: %r" % cfg["save_weight_dir"], flush=True)
for e in range(epoch_str, t["epochs"] + 1):
    info("Train Epoch: {} [{:.0f}%]".format(e, 0.0))
    info("Train Epoch: {} [{:.0f}%]".format(e, 50.0))
    global_step = e * steps_per_epoch
    if e % t["save_every_epoch"] == 0:  # s2_train.py:514
        if t.get("if_save_latest"):
            os.makedirs(ckpt_dir, exist_ok=True)
            open(latest, "w").write(str(e))
            open(os.path.join(ckpt_dir, "D_233333333333.pth"), "w").write(str(e))
        if t.get("if_save_every_weights") and weights_ok:
            ck = f"{name}_e{e}_s{global_step}"
            # 和真的一样：Pro / v3 / v4 的模型文件开头 2 个字节是版本标记（process_ckpt.py 的 my_save2），v2 是 zip（PK）
            head = {"v3": b"03", "v4": b"04", "v2Pro": b"05", "v2ProPlus": b"06"}.get(cfg["model"]["version"], b"PK")
            open(f"{cfg['save_weight_dir']}/{ck}.pth", "wb").write(head + b"x" * 62)
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
# 真实的 s1_train.py 也不建 half_weights_save_dir
if not os.path.isdir(t["half_weights_save_dir"]):
    print("FileNotFoundError: [Errno 2] No such file or directory: %r" % t["half_weights_save_dir"], flush=True)
    sys.exit(1)
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

def _epoch(gpt_path):
    return int(gpt_path.rsplit("-e", 1)[-1].split(".")[0]) if "-e" in gpt_path else 1

def _dur(text, speed, gpt_path):
    # 时长与文字长度成正比；不同 GPT 权重读得快慢不同（模拟不同 epoch 的差异）
    dur = max(0.5, len(text) * (0.2 + 0.01 * _epoch(gpt_path)) / max(speed, 0.1))
    if speed != 1.0 and os.environ.get("FAKE_GSV_SPEED_TRICK_BROKEN"):
        dur *= 1.05
    return dur

def _inner_zero(n, sr):
    if not os.environ.get("FAKE_GSV_INNER_ZERO"):
        return (0, 0)
    return (n // 2, n // 2 + int(0.4 * sr))

def _wav_bytes(frames, sr):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(bytes(frames))
    return buf.getvalue()

def make_wav(text, speed, gpt_path):
    sr = 32000
    n = int(_dur(text, speed, gpt_path) * sr)
    pad = int(0.2 * sr)
    z0, z1 = _inner_zero(n, sr)
    frames = bytearray()
    for i in range(n + 2 * pad):
        v = 0.0
        if pad <= i < n + pad and not (z0 <= i - pad < z1):
            t = i / sr
            v = 0.3 * math.sin(2 * math.pi * 150 * t) * (0.6 + 0.4 * math.sin(2 * math.pi * 4 * t))
        frames += struct.pack("<h", int(v * 32767))
    return _wav_bytes(frames, sr)

def split_rows(text):
    """按换行切开：空行去掉，不到 5 个字的段和后面的合在一起（真实的 pre_seg_text + merge_short_text_in_array）。"""
    parts = [t for t in text.strip("\\n").split("\\n") if t not in ("", " ")]
    rows, cur = [], ""
    for t in parts:
        cur += t
        if len(cur) >= 5:
            rows.append(cur); cur = ""
    if cur:
        if rows: rows[-1] += cur
        else: rows.append(cur)
    return rows or [text]

def make_rows(rows, speed, gpt_path, seed, interval):
    """同时生成的几段：每段一个不同音高的正弦波，后面补 interval 秒的 0（开头不加空白，和 TTS.py 一样）。"""
    sr = 32000
    frames = bytearray()
    for k, row in enumerate(rows):
        n = int(_dur(row, speed, gpt_path) * sr)
        f = 150 + 10 * ((seed + k) % 7)
        z0, z1 = _inner_zero(n, sr)
        for i in range(n):
            v = 0.0
            if not (z0 <= i < z1):
                t = i / sr
                v = 0.3 * math.sin(2 * math.pi * f * t) * (0.6 + 0.4 * math.sin(2 * math.pi * 4 * t))
            frames += struct.pack("<h", int(v * 32767))
        frames += b"\\x00\\x00" * int(sr * interval)
    return _wav_bytes(frames, sr)

def silent_oom(handler, detail):
    # 真实的 TTS.run 出错时不报错（TTS.py @ abe9843 第 1516~1518 行）：打印 Traceback，回 200 + 1 秒 16 kHz 静音
    print("Traceback (most recent call last):\\n"
          '  File "GPT_SoVITS/TTS_infer_pack/TTS.py", line 1300, in run\\n'
          "    pred_semantic_list, idx_list = self.t2s_model.model.infer_panel(\\n"
          "torch.OutOfMemoryError: CUDA out of memory. " + detail, flush=True)
    data = _wav_bytes(b"\\x00\\x00" * 16000, 16000)
    handler.send_response(200); handler.send_header("Content-Type", "audio/wav")
    handler.send_header("Content-Length", str(len(data))); handler.end_headers(); handler.wfile.write(data)

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _json(self, code, obj):
        body = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/tts":
            if not q.get("text_lang") or not q.get("prompt_lang"):  # 真实的 api_v2：None.lower() 报错
                body = b"Internal Server Error"; self.send_response(500)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
                print("AttributeError: 'NoneType' object has no attribute 'lower'", flush=True); return
            return self._json(400, {"message": "ref_audio_path is required"})
        if u.path in ("/set_gpt_weights", "/set_sovits_weights"):
            p = q.get("weights_path", "")
            kind = "gpt" if "gpt" in u.path else "sovits"
            if not p:
                return self._json(400, {"message": f"{kind} weight path is required"})
            if not os.path.exists(p):
                return self._json(400, {"message": f"change {kind} weight failed", "Exception": "not found"})
            state[kind] = p
            return self._json(200, {"message": "success"})
        if u.path == "/control":
            if not q.get("command"):
                return self._json(400, {"message": "command is required"})
            if q.get("command") == "exit":
                self._json(200, {}); threading.Thread(target=srv.shutdown).start(); return
        self._json(404, {"detail": "Not Found"})
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        for k in ("text", "text_lang", "ref_audio_path", "prompt_lang"):
            if not req.get(k):
                return self._json(400, {"message": f"{k} is required"})
        if not os.path.exists(req["ref_audio_path"]):
            return self._json(400, {"message": "ref missing"})
        assert req["text_split_method"] == "cut0"
        with open("_fake_api_calls.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"kind": "run", "req": req}, ensure_ascii=False) + "\\n")
        if "【测试显存不够】" in req["text"]:
            return silent_oom(self, "Tried to allocate 1.00 GiB")
        bs = int(req.get("batch_size", 1) or 1)
        limit = os.environ.get("FAKE_GSV_MAX_BATCH")
        if limit not in (None, "") and bs > int(limit):
            return silent_oom(self, f"Tried to allocate 2.00 GiB (batch_size {bs})")
        speed = float(req.get("speed_factor", 1.0))
        if "\\n" in req["text"]:
            seed = int(req.get("seed", -1) if req.get("seed") is not None else -1)
            data = make_rows(split_rows(req["text"]), speed, state["gpt"], seed,
                             float(req.get("fragment_interval", 0.3) or 0))
        else:
            data = make_wav(req["text"], speed, state["gpt"])
        self.send_response(200); self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

srv = ThreadingHTTPServer((args.a, args.p), H)
print("fake api_v2 ready", flush=True)
srv.serve_forever()
'''

#: 真实的 api_v2.py（GPT-SoVITS @ abe9843，老师电脑上的版本，MIT 许可，见 tests/gsv_real/README.md）
REAL_API_V2 = Path(__file__).resolve().parent / "gsv_real" / "api_v2.py"
#: 2025 年中的整合包（20250606v2pro）里的 api_v2.py：老师以后也可能装这一版
REAL_API_V2_2025 = Path(__file__).resolve().parent / "gsv_real" / "api_v2_20250606v2pro.py"

#: real_api=True 时，真实 api_v2.py 要 import 的几个模块换成假的：不用 torch、不用模型，
#: 但输入检查和打印的内容照着真实的 TTS.py（@ abe9843）写，输出也是真实格式（int16、32000 Hz）。
REAL_API_STUBS = {
    "tools/i18n/i18n.py": '''
class I18nAuto:
    def __init__(self, *a, **k): pass
    def __call__(self, key): return key
''',
    "GPT_SoVITS/TTS_infer_pack/text_segmentation_method.py": '''
METHODS = {name: None for name in ("cut0", "cut1", "cut2", "cut3", "cut4", "cut5")}
def get_method_names() -> list:
    return list(METHODS.keys())
''',
    "GPT_SoVITS/TTS_infer_pack/TTS.py": '''
import json, math, os, time
import numpy as np
import soundfile as sf
import yaml

CALLS = os.path.join(os.getcwd(), "_real_api_calls.jsonl")

def _record(kind, **data):
    with open(CALLS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(kind=kind, **data), ensure_ascii=False) + "\\n")

def _rows(text):
    """同时生成好几个版本时按换行切开（真实的 pre_seg_text：空行去掉，不到 5 个字的段和后面的合在一起）；
    没有换行就是整句一段（和以前一样）。"""
    if "\\n" not in text:
        return [text]
    parts = [t for t in text.strip("\\n").split("\\n") if t not in ("", " ")]
    rows, cur = [], ""
    for t in parts:
        cur += t
        if len(cur) >= 5:
            rows.append(cur)
            cur = ""
    if cur:
        if rows:
            rows[-1] += cur
        else:
            rows.append(cur)
    return rows or [text]

class TTS_Config:
    v1_languages = ["auto", "en", "zh", "ja", "all_zh", "all_ja"]
    v2_languages = ["auto", "auto_yue", "en", "zh", "ja", "yue", "ko", "all_zh", "all_ja", "all_yue", "all_ko"]
    def __init__(self, configs):
        cfg = yaml.safe_load(open(configs, encoding="utf8"))["custom"]
        self.configs = cfg
        self.device = cfg["device"]; self.is_half = cfg["is_half"]; self.version = cfg["version"]
        self.t2s_weights_path = cfg["t2s_weights_path"]; self.vits_weights_path = cfg["vits_weights_path"]
        self.bert_base_path = cfg["bert_base_path"]; self.cnhuhbert_base_path = cfg["cnhuhbert_base_path"]
        self.languages = self.v1_languages if self.version == "v1" else self.v2_languages
    def __str__(self):
        s = "-" * 45 + "TTS Config" + "-" * 45 + "\\n"
        for k in ("device", "is_half", "version", "t2s_weights_path", "vits_weights_path", "bert_base_path",
                  "cnhuhbert_base_path"):
            s += f"{k:<20}: {getattr(self, k)}\\n"
        return s + "-" * 100 + "\\n"

class TTS:
    def __init__(self, configs):
        self.configs = configs
        time.sleep(float(os.environ.get("FAKE_GSV_API_DELAY", "0") or 0))  # 真实的加载模型要几十秒
        self.init_t2s_weights(configs.t2s_weights_path)
        self.init_vits_weights(configs.vits_weights_path)
        print(f"Loading BERT weights from {configs.bert_base_path}")
        print(f"Loading CNHuBERT weights from {configs.cnhuhbert_base_path}")
    def init_t2s_weights(self, weights_path):
        print(f"Loading Text2Semantic weights from {weights_path}")
        if not os.path.exists(weights_path):
            raise FileNotFoundError(weights_path)
        self.t2s = weights_path
        _record("init_t2s_weights", path=weights_path)
    def init_vits_weights(self, weights_path):
        print(f"Loading VITS weights from {weights_path}. <All keys matched successfully>")
        if not os.path.exists(weights_path):
            raise FileNotFoundError(weights_path)
        self.vits = weights_path
        _record("init_vits_weights", path=weights_path)
    def run(self, inputs):
        text = inputs.get("text", ""); text_lang = inputs.get("text_lang", "")
        ref = inputs.get("ref_audio_path", ""); prompt_lang = inputs.get("prompt_lang", "")
        assert text_lang in self.configs.languages  # TTS.py 里的同一句检查
        if inputs.get("prompt_text"):  # TTS.py：只在有参考文字时检查 prompt_lang
            assert prompt_lang in self.configs.languages
        if not os.path.exists(ref):
            raise FileNotFoundError(ref)
        info = sf.info(ref)  # TTS.py：参考音频必须在 3~10 秒之间（按 16 kHz 重采样后的长度判断）
        if not (3.0 <= info.frames / info.samplerate <= 10.0):
            raise OSError("参考音频在3~10秒范围外，请更换！")
        for p in inputs.get("aux_ref_audio_paths") or []:
            if not os.path.exists(p):  # TTS.py：辅助参考音频不存在时只打印一句、跳过
                print("音频文件不存在，跳过：", p)
        _record("run", req={k: v for k, v in inputs.items()}, t2s=self.t2s, vits=self.vits)
        try:
            if "【测试显存不够】" in text:
                raise RuntimeError("CUDA out of memory. Tried to allocate 1.00 GiB")
            bs = int(inputs.get("batch_size", 1) or 1)
            limit = os.environ.get("FAKE_GSV_MAX_BATCH")
            if limit not in (None, "") and bs > int(limit):  # 测试开关：同时生成太多个时显存不够
                raise RuntimeError(f"CUDA out of memory. Tried to allocate 2.00 GiB (batch_size {bs})")
            sr = 32000
            import re
            m = re.search(r"-e(\\d+)\\.ckpt$", self.t2s)
            epoch = int(m.group(1)) if m else 1
            speed = float(inputs.get("speed_factor", 1.0) or 1.0)
            seed = int(inputs.get("seed", -1) if inputs.get("seed") is not None else -1)
            rows = _rows(text)
            # TTS.py 的 audio_postprocess：开头不加空白，每段后面补 fragment_interval 秒的 0，最后转成 int16
            tail = np.zeros(int(sr * float(inputs.get("fragment_interval", 0.3) or 0)))
            parts = []
            for k, row in enumerate(rows):
                dur = max(0.5, len(row) * (0.2 + 0.01 * epoch) / max(speed, 0.1))
                if speed != 1.0 and os.environ.get("FAKE_GSV_SPEED_TRICK_BROKEN"):
                    dur *= 1.05
                t = np.arange(int(dur * sr)) / sr
                f = 150.0 if len(rows) == 1 else 150.0 + 10 * ((seed + k) % 7)  # 一次一个时和以前一样
                wav = 0.3 * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t))
                if os.environ.get("FAKE_GSV_INNER_ZERO"):
                    mid = len(wav) // 2
                    wav[mid:mid + int(0.4 * sr)] = 0
                parts += [wav, tail]
            audio = np.concatenate(parts)
            yield sr, (audio * 32768).clip(-32768, 32767).astype(np.int16)
        except Exception as e:  # TTS.py 第 1516~1518 行：不报错，打印 Traceback，回 1 秒 16 kHz 的静音
            import traceback
            traceback.print_exc()
            yield 16000, np.zeros(int(16000), dtype=np.int16)
''',
}

#: 真实的模型文件都有几百 MB；这里写 2 KB，刚好超过「小于 1 KB 算没下载完」的门槛
FAKE_WEIGHT = b"x" * 2048


def build_fake_root(root: Path, version: str = "v2ProPlus", real_api=False) -> Path:
    """real_api=True（或者某个真实 api_v2.py 的路径）：推理服务用真实的 api_v2.py（只有模型是假的），
    用来保证程序和真的 GPT-SoVITS 对得上。"""
    root = Path(root)
    real_src = (REAL_API_V2 if real_api is True else Path(real_api)) if real_api else None
    files = {
        "api_v2.py": real_src.read_text(encoding="utf-8") if real_src else API_V2,
        "GPT_SoVITS/prepare_datasets/1-get-text.py": GET_TEXT,
        "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py": GET_HUBERT,
        "GPT_SoVITS/prepare_datasets/2-get-sv.py": GET_SV,
        "GPT_SoVITS/prepare_datasets/3-get-semantic.py": GET_SEMANTIC,
        "GPT_SoVITS/s2_train.py": S2_TRAIN,
        "GPT_SoVITS/s1_train.py": S1_TRAIN,
    }
    if real_api:
        files.update(REAL_API_STUBS)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if rel == "api_v2.py" else textwrap.dedent(content), encoding="utf-8")
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
