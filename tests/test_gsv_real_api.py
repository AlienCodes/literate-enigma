"""拿真实的 GPT-SoVITS 推理服务代码（tests/gsv_real/api_v2.py，老师电脑上的版本 abe9843）来测。

为什么要有这个文件：v18.2 时，程序判断「引擎好了没有」用的是不带参数的 GET /tts。我们自己写的模拟版对它回 400，
测试全部通过；可真实的 api_v2.py 对它报错回 500，结果老师那里引擎明明一分钟内就开好了，程序却一直等到 10 分钟超时。
所以这里不用模拟版，直接运行真实的 api_v2.py（只把模型换成假的，见 fake_gptsovits.REAL_API_STUBS），
把「启动 → 换模型 → 合成 → 停止」以及「训练 → 自动挑选 → 生成讲课音频」整条流程都跑一遍。

需要 fastapi + uvicorn（pip install -e ".[dev]" 会装上）；没有的话跳过。
"""

import json
import os
import socket
import sys
import time
from pathlib import Path

import pytest
import soundfile as sf

from voicetwin import workflows as wf
from voicetwin.backends.base import SynthRequest, get_backend
from voicetwin.backends.gptsovits import GPTSoVITSBackend

from conftest import make_cfg
from fake_gptsovits import REAL_API_V2, build_fake_root

pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")
pytest.importorskip("yaml")


@pytest.fixture
def quick(monkeypatch):
    # 测试环境里不要往当前 Python 的 site-packages 写 users.pth；也不要去读真显卡（慢）
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "POLL_SECONDS", 0.05)
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)


def _port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _calls(root: Path):
    f = root / "_real_api_calls.jsonl"
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def _api_log(project) -> str:
    return (project.logs_dir / "gptsovits_api.log").read_text(encoding="utf-8", errors="replace")


def _assert_clean_api_log(project):
    """最后一次启动的引擎记录里没有报错。

    唯一的例外是停止时的 /control?command=exit：真实的 api_v2 先 os.kill(自己, SIGTERM) 再 exit(0)。
    Windows 上 SIGTERM 就是立刻结束进程，什么也来不及打印；Linux 上 uvicorn 先接住信号慢慢关，
    接着 exit(0) 在请求里抛出 SystemExit，记录里多一段 Traceback 和一个 500——这是官方代码本身的行为，不影响使用。"""
    from voicetwin.utils.logtail import _units, last_run

    text = last_run(_api_log(project))
    assert "Uvicorn running on" in text
    kept = []
    for unit in _units(text.splitlines()):
        if unit[0].startswith("Traceback") and unit[-1].startswith("SystemExit"):
            continue
        if len(unit) == 1 and "/control?command=exit" in unit[0]:
            continue
        kept.extend(unit)
    rest = "\n".join(kept)
    assert "500 Internal Server Error" not in rest, rest[-3000:]
    assert "Traceback" not in rest, rest[-3000:]


def _ref(project):
    r = project.load_references()[0]
    return project.abspath(r["path"]), r["text"], r.get("lang", "zh")


def test_vendored_api_is_the_teachers_version():
    """tests/gsv_real/api_v2.py 必须是原样的官方文件（老师的报错在第 484 行：text_lang.lower()）。"""
    lines = REAL_API_V2.read_text(encoding="utf-8").splitlines()
    assert lines[483].strip() == '"text_lang": text_lang.lower(),'
    assert '@APP.get("/control")' in lines[447]


def test_real_api_start_switch_synthesize_stop(prepared, tmp_path, quick):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=True)
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    ref, ref_text, ref_lang = _ref(p2)
    t0 = time.time()
    try:
        b.start()
        assert time.time() - t0 < 30  # 引擎一开就认出来，不会白等
        assert b._alive()
        pid = b.proc.pid
        # 换模型：真实的 /set_*_weights
        pm = root / "GPT_SoVITS" / "pretrained_models"
        b.use_checkpoint({"gpt": str(pm / "s1v3.ckpt"), "sovits": str(pm / "v2Pro" / "s2Gv2Pro.pth")})
        kinds = [(c["kind"], Path(c.get("path", "")).name) for c in _calls(root)]
        assert ("init_t2s_weights", "s1v3.ckpt") in kinds and ("init_vits_weights", "s2Gv2Pro.pth") in kinds
        # 合成：请求要通过真实 api_v2 的参数检查，返回真实格式的 WAV
        out = b.synthesize(SynthRequest(text="大家好，今天我们讲第一课。", lang="zh", ref_audio=ref, ref_text=ref_text,
                                        ref_lang=ref_lang, speed=0.9, seed=7), tmp_path / "a.wav")
        info = sf.info(str(out))
        assert info.samplerate == 32000 and info.subtype == "PCM_16" and info.frames > 32000
        run = [c for c in _calls(root) if c["kind"] == "run"][-1]["req"]
        assert run["text_split_method"] == "cut0" and run["text_lang"] == "zh" and run["seed"] == 7
        # 英文句子
        out2 = b.synthesize(SynthRequest(text="Hello everyone.", lang="en", ref_audio=ref, ref_text=ref_text,
                                         ref_lang=ref_lang), tmp_path / "b.wav")
        assert sf.info(str(out2)).frames > 0
    finally:
        b.stop()
    assert b.proc is None
    deadline = time.time() + 15
    while time.time() < deadline and _pid_alive(pid):
        time.sleep(0.2)
    assert not _pid_alive(pid)
    _assert_clean_api_log(p2)


def test_real_api_bare_get_tts_is_a_trap(prepared, tmp_path, quick):
    """记下真实 api_v2 的行为：不带参数的 GET /tts 回 500（所以绝对不能用它判断引擎好了没有），
    GET /control 不带 command 回 400 而且什么也不做。"""
    import requests

    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=True)
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    try:
        b.start()
        s = requests.Session()
        s.trust_env = False
        r = s.get(f"{b.api_url}/tts", timeout=5, headers={"Connection": "close"})
        assert r.status_code == 500
        r = s.get(f"{b.api_url}/control", timeout=5, headers={"Connection": "close"})
        assert r.status_code == 400 and r.json() == {"message": "command is required"}
        assert b._alive()  # 刚才那个 500 不影响服务继续用
    finally:
        b.stop()


def test_real_api_full_flow_train_select_narrate(prepared, tmp_path, quick, monkeypatch):
    """从头到尾：训练（假的训练脚本）→ 自动挑选最像的模型 → 生成讲课音频，推理全程用真实的 api_v2.py。"""
    monkeypatch.setenv("FAKE_GSV_CLIP_SLEEP", "0.0")
    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    import shutil

    shutil.copytree(project.root, ws / project.voice)
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=True)
    gcfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 60, "is_half": True,
        "train": {"sovits_epochs": 4, "gpt_epochs": 4, "batch_size": 2}}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    info = wf.run_train(gcfg, project.voice, "gptsovits", select=True, sovits_save_every=2, gpt_save_every=2)
    assert "selection_error" not in info, info.get("selection_error_detail")
    models = p2.load_models()["gptsovits"]
    assert models["selected"]["id"] and models["selection"]["results"]
    res = wf.run_narrate(gcfg, project.voice, "大家好，这是用真实推理服务代码生成的一句话。Hello!",
                         out=str(tmp_path / "lecture.wav"), backend_name="gptsovits", quality="fast")
    assert res.audio_path.exists() and res.duration > 1.0
    assert any(c["kind"] == "run" for c in _calls(root))
    _assert_clean_api_log(p2)


def test_unrecognized_server_fails_fast_with_report(prepared, tmp_path, quick, monkeypatch):
    """端口开了但回答对不上（比如别的程序、或者以后的版本改了接口）：1 分钟内（测试里 1 秒）就报出原因，不白等 10 分钟。"""
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    (root / "api_v2.py").write_text(
        "import argparse, http.server\n"
        "ap = argparse.ArgumentParser(); ap.add_argument('-a'); ap.add_argument('-p', type=int); ap.add_argument('-c')\n"
        "a = ap.parse_args()\n"
        "class H(http.server.BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n"
        "        print('INFO:     127.0.0.1:1 - \"GET ' + self.path + ' HTTP/1.1\" 500 Internal Server Error', flush=True)\n"
        "        self.send_response(500); self.send_header('Content-Length', '5'); self.end_headers(); self.wfile.write(b'oops!')\n"
        "    def log_message(self, *x): pass\n"
        "print('INFO:     Uvicorn running on http://127.0.0.1:%d (Press CTRL+C to quit)' % a.p, flush=True)\n"
        "http.server.HTTPServer((a.a, a.p), H).serve_forever()\n", encoding="utf-8")
    monkeypatch.setattr(GPTSoVITSBackend, "MISMATCH_GRACE_SECONDS", 1.0)
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    t0 = time.time()
    with pytest.raises(RuntimeError) as ei:
        b.start()
    assert time.time() - t0 < 20
    msg = str(ei.value)
    assert "对上话" in msg and "HTTP 500" in msg and "oops!" in msg
    assert "引擎对程序的请求回答了" in msg and "Uvicorn running" in msg
    assert b.proc is None
    from voicetwin.errors import explain, is_fatal

    f = explain(ei.value)
    assert f.key == "api_mismatch" and "对不上" in f.title and is_fatal(f)


def test_timeout_message_says_where_it_got_stuck(prepared, tmp_path, quick, monkeypatch):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=True)
    monkeypatch.setenv("FAKE_GSV_API_DELAY", "30")
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": _port(), "startup_timeout": 3}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    with pytest.raises(RuntimeError) as ei:
        b.start()
    msg = str(ei.value)
    assert "推理服务启动超时（等了 3 秒，合成引擎一直没有加载完模型（端口没有打开））" in msg
    assert "gptsovits_api.log" in msg and "TTS Config" in msg
    from voicetwin.errors import explain

    assert explain(ei.value).key == "api_start"


def _pid_alive(pid):
    if os.name == "nt":
        import subprocess

        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL).stdout.decode(errors="replace")
        return str(pid) in out.split()
    if Path("/proc/self").exists():
        try:
            return Path(f"/proc/{pid}/stat").read_text().split(")")[-1].split()[0] != "Z"
        except OSError:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
