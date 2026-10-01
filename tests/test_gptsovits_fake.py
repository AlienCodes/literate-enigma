"""用仿真 GPT-SoVITS 目录验证：训练编排（1A/1B/1C/SoVITS/GPT）、进度、自动训练设置、显存不够自动重试、
停止、素材变化后从头训练、权重发现、自动挑选、推理服务启动/切换/关闭。"""

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from voicetwin import workflows as wf
from voicetwin.backends import base as backend_base
from voicetwin.backends import gptsovits as gsv
from voicetwin.backends.base import SynthRequest, TaskCancelled, TrainStepError, get_backend
from voicetwin.backends.gptsovits import (
    GPTSoVITSBackend,
    _auto_save_every,
    _gpt_parser,
    _line_counter,
    _sovits_parser,
    _spread,
    plan_training,
)

from conftest import make_cfg
from fake_gptsovits import build_fake_root


# ---------------------------------------------------------------------------- 小工具
def _fake_python_ok() -> bool:
    """fake GPT-SoVITS 的脚本用解析后的解释器运行（和真的整合包一样）；有的 venv 解析后找不到 yaml，那就跳过。"""
    try:
        proc = subprocess.run([str(Path(sys.executable).resolve()), "-c", "import yaml"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


needs_fake_python = pytest.mark.skipif(not _fake_python_ok(), reason="这个环境里 fake GPT-SoVITS 的子进程缺少 yaml（已知的环境问题）")


class Rec:
    """记录进度回调。"""

    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, frac, msg=""):
        with self.lock:
            self.calls.append((float(frac), str(msg)))

    @property
    def msgs(self):
        return [m for _, m in self.calls]

    def train_part(self):
        """训练这一段（到「训练完成」为止；之后是自动挑选，可能从 0 重新开始）。"""
        out = []
        for f, m in self.calls:
            out.append((f, m))
            if "训练完成" in m:
                break
        return out


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def messages(self, level=None):
        return [r.getMessage() for r in self.records if level is None or r.levelno == level]


@pytest.fixture
def vt_log():
    h = ListHandler()
    logger = logging.getLogger("voicetwin")
    logger.addHandler(h)
    old = logger.level
    logger.setLevel(logging.INFO)
    try:
        yield h
    finally:
        logger.removeHandler(h)
        logger.setLevel(old)


@pytest.fixture
def no_users_pth(monkeypatch):
    # 测试环境里不要往当前 Python 的 site-packages 写 users.pth；也不要去读真显卡（慢）
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "POLL_SECONDS", 0.05)


def _gcfg(project, root, port, **train):
    return make_cfg(project.root.parent, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": port, "startup_timeout": 60, "is_half": True,
        "train": train,
    }})


def _copy_project(project, dest_ws):
    shutil.copytree(project.root, dest_ws / project.voice)
    return dest_ws


def _pid_alive(pid):
    if os.name == "nt":  # Windows 上 os.kill(pid, 0) 会直接结束进程，不能用来检查
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL).stdout.decode(errors="replace")
        return str(pid) in out.split()
    if Path("/proc/self").exists():
        try:  # 僵尸进程（已经结束、还没被回收）不算活着
            return Path(f"/proc/{pid}/stat").read_text().split(")")[-1].split()[0] != "Z"
        except OSError:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------- 完整流程
@needs_fake_python
def test_train_select_and_narrate(prepared, tmp_path, monkeypatch, no_users_pth, vt_log):
    monkeypatch.setenv("FAKE_GSV_CLIP_SLEEP", "0.03")
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    gcfg = _gcfg(project, root, 19880, sovits_epochs=8, gpt_epochs=10, batch_size=2)
    rec = Rec()
    # 高级设置里明确指定的保存间隔要照办
    info = wf.run_train(gcfg, project.voice, "gptsovits", select=True, progress=rec, sovits_save_every=4,
                        gpt_save_every=5)

    backend = get_backend("gptsovits", gcfg, project)
    exp = backend.exp_name
    lines = (project.exports_dir / "gptsovits" / "train.list").read_text(encoding="utf-8").strip().splitlines()
    assert lines and all(len(l.split("|")) == 4 and l.split("|")[1] == exp for l in lines)
    opt_dir = root / "logs" / exp
    assert (opt_dir / "2-name2text.txt").exists()
    assert (opt_dir / "6-name2semantic.tsv").read_text(encoding="utf-8").startswith("item_name\tsemantic_audio")
    assert (opt_dir / "7-sv_cn").is_dir()

    models = project.load_models()["gptsovits"]
    assert [p.rsplit("_e", 1)[1].split("_")[0] for p in models["sovits"]] == ["4", "8"]
    assert [p.rsplit("-e", 1)[1].split(".")[0] for p in models["gpt"]] == ["5", "10"]
    assert models["selected"]["id"] in {c["id"] for c in backend.checkpoints()}
    assert len(models["selection"]["results"]) == 4
    assert set(models["speed"]) <= {"zh", "en"}
    assert models["params"]["summary"].startswith("训练计划：")
    assert info["params"]["batch_size"] == 2 and info["params"]["if_dpo"] is False

    # 进度：一直往前走，中文说明，轮数不超前
    part = rec.train_part()
    fracs = [f for f, _ in part]
    # 训练占整个任务的 0~scale（只训练时是 1.0；训练后接着自动挑选时 workflows 可能把训练压到 0~0.88）
    scale = fracs[-1]
    assert fracs == sorted(fracs) and fracs[0] == 0.0 and scale in (1.0, 0.88)
    msgs = [m for _, m in part]
    assert msgs[-1] == "GPT-SoVITS 训练完成"
    assert msgs[0].startswith("检查显卡、整理训练素材")
    assert any(m.startswith("训练计划：") for m in msgs)
    assert any(m.startswith("处理文字 ") and m.endswith(f"/{len(lines)}") for m in msgs)
    assert sum(1 for m in msgs if m.startswith("提取声音特征 ")) >= 2
    assert any(m.startswith("提取声纹") for m in msgs)
    assert "训练音色：第 1/8 轮（0%）" in msgs and "训练音色：第 8/8 轮完成" in msgs
    assert "训练语气和节奏：第 1/10 轮（50%）" in msgs and "训练语气和节奏：第 10/10 轮（100%）" in msgs
    first_sovits = next(f for f, m in part if m.startswith("训练音色：第"))
    assert abs(first_sovits - 0.25 * scale) < 1e-6  # 「start training from epoch 1」不能让进度一开始就跳到 1/8
    # 主日志：没有旧格式的「gsv_s2_train 进度 38%」刷屏，有中文的 ▶ 步骤行
    log_msgs = vt_log.messages()
    assert not any(" 进度 " in m and "gsv_" in m for m in log_msgs)
    assert any(m.startswith("▶ 训练音色（详细日志：gsv_s2_train.log）") for m in log_msgs)
    assert sum(1 for m in log_msgs if "训练音色：第" in m) <= 20
    # 详细日志里有完整命令
    s2_log = (project.logs_dir / "gsv_s2_train.log").read_text(encoding="utf-8")
    assert "命令：" in s2_log and "s2_train.py" in s2_log and "INFO:" in s2_log

    res = wf.run_narrate(gcfg, project.voice, "大家好，这是用 GPT-SoVITS 引擎生成的一句话。Hello!",
                         out=str(tmp_path / "gsv.wav"), backend_name="gptsovits", quality="fast")
    assert res.audio_path.exists() and res.duration > 1.0

    stamp = (opt_dir / "voicetwin_list.sha1").read_text()
    assert len(stamp) == 40


def test_check_reports_missing_models(prepared, tmp_path):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV2")
    (root / "GPT_SoVITS/pretrained_models/s1v3.ckpt").unlink()
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    backend = get_backend("gptsovits", gcfg, project)
    problems = backend.check()
    assert any("s1v3.ckpt" in p for p in problems)
    assert backend.missing_pretrained() == ["GPT_SoVITS/pretrained_models/s1v3.ckpt"]


def test_half_downloaded_models_count_as_missing(prepared, tmp_path):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV3")
    pm = root / "GPT_SoVITS/pretrained_models"
    bert = pm / "chinese-roberta-wwm-ext-large"
    shutil.rmtree(bert)
    bert.mkdir()
    (bert / "config.json").write_text("{}", encoding="utf-8")
    (bert / "pytorch_model.bin.part").write_bytes(b"x" * 4096)  # 下载到一半
    (pm / "s1v3.ckpt").write_bytes(b"")                        # 0 字节的坏文件
    hubert = pm / "chinese-hubert-base"
    (hubert / "preprocessor_config.json").unlink()
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    backend = get_backend("gptsovits", gcfg, project)
    assert backend.missing_pretrained() == [gsv.BERT_DIR, gsv.HUBERT_DIR, "GPT_SoVITS/pretrained_models/s1v3.ckpt"]
    # 补齐以后就不算缺了（tokenizer 用 vocab.txt 也行）
    (bert / "pytorch_model.bin").write_bytes(b"x" * 4096)
    (bert / "vocab.txt").write_text("[PAD]\n", encoding="utf-8")
    (hubert / "preprocessor_config.json").write_text("{}", encoding="utf-8")
    (pm / "s1v3.ckpt").write_bytes(b"x" * 4096)
    assert backend.missing_pretrained() == []


def test_selected_model_survives_moving_gptsovits(prepared, tmp_path):
    """models.json 记录的是旧位置的绝对路径（例如 Windows 上的 D:\\GPT-SoVITS\\...），
    整合包移动 / 换电脑后应按文件名在新 root 里找到训练好的模型，而不是退回底模。"""
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-moved")
    gcfg = make_cfg(ws, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    project = wf.open_project(gcfg, project.voice, must_exist=True)
    backend = get_backend("gptsovits", gcfg, project)
    exp = backend.exp_name
    sov = root / "SoVITS_weights_v2ProPlus" / f"{exp}_e8_s80.pth"
    gpt = root / "GPT_weights_v2ProPlus" / f"{exp}-e15.ckpt"
    for p in (sov, gpt):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"0")
    old = "D:\\GPT-SoVITS-old"
    project.update_models("gptsovits", {
        "sovits": [f"{old}\\SoVITS_weights_v2ProPlus\\{sov.name}"], "gpt": [f"{old}\\GPT_weights_v2ProPlus\\{gpt.name}"],
        "selected": {"id": "s8-g15", "sovits": f"{old}\\SoVITS_weights_v2ProPlus\\{sov.name}",
                     "gpt": f"{old}\\GPT_weights_v2ProPlus\\{gpt.name}"},
    })
    w = backend._current_weights()
    assert w["id"] == "s8-g15" and w["sovits"] == str(sov) and w["gpt"] == str(gpt)
    assert [c["id"] for c in backend.checkpoints()] == ["s8-g15"]


def test_pretrained_warning_only_once(prepared, tmp_path, vt_log):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-warn")
    gcfg = make_cfg(ws, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    project = wf.open_project(gcfg, project.voice, must_exist=True)
    if project.models_path.exists():
        project.models_path.unlink()
    backend = get_backend("gptsovits", gcfg, project)
    for _ in range(3):
        assert backend._current_weights()["id"] == "pretrained"
        backend.model_id()
    warnings = [m for m in vt_log.messages(logging.WARNING) if "还没有训练好的 GPT-SoVITS 模型" in m]
    assert len(warnings) == 1


# ---------------------------------------------------------------------------- 日志 → 进度
def test_sovits_parser_real_format():
    p = _sovits_parser(12)
    assert p("start training from epoch 1") is None
    assert p("INFO:vt_x:start training from epoch 7") is None
    frac, text = p("INFO:vt_abc:Train Epoch: 3 [45%]")
    assert abs(frac - 2.45 / 12) < 1e-9 and text == "训练音色：第 3/12 轮（45%）"
    frac, text = p("INFO:vt_abc:====> Epoch: 3")
    assert frac == 0.25 and text == "训练音色：第 3/12 轮完成"
    assert p("INFO:vt_abc:====> Epoch: 14")[0] == 1.0
    assert p("INFO:vt_abc:[1.2, 3.4, 100, 0.0001]") is None


def test_gpt_parser_real_format():
    p = _gpt_parser(15)
    frac, text = p("Epoch 0:  45%|████▌     | 20/44 [00:10<00:12,  2.00it/s, v_num=0]")
    assert abs(frac - 0.03) < 1e-9 and text == "训练语气和节奏：第 1/15 轮（45%）"
    assert p("Epoch 14: 100%|██████████| 44/44")[0] == 1.0
    frac, text = p("ckpt_path: D:/GSV/logs/vt_x/logs_s1_v2ProPlus/ckpt/epoch=9-step=100.ckpt")
    assert abs(frac - 10 / 15) < 1e-9 and text == "训练语气和节奏：第 10/15 轮完成"
    # v2 底模的文件名里也有 epoch=12，不能当成进度
    assert p("loading GPT_SoVITS/pretrained_models/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt") is None
    assert p("ckpt_path: None") is None


def test_line_counter():
    p = _line_counter(4, "处理文字")
    assert p("Building prefix dict from the default dictionary ...") is None
    assert p("abc_0001.wav") == (0.25, "处理文字 1/4")
    assert p("abc_0002.WAV") == (0.5, "处理文字 2/4")
    for _ in range(4):
        last = p("x.wav")
    assert last == (1.0, "处理文字 4/4")


# ---------------------------------------------------------------------------- run_logged
def _script(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def _plain_backend(prepared, tmp_path):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    cfg2 = make_cfg(ws)
    return get_backend("dummy", cfg2, wf.open_project(cfg2, project.voice, must_exist=True))


def test_run_logged_progress_messages_and_errors(prepared, tmp_path, vt_log):
    b = _plain_backend(prepared, tmp_path)
    script = _script(tmp_path, "steps.py", "import sys\nfor i in range(1, 51):\n    print(f'step {i}/50', flush=True)\n"
                                           "print('torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2 GiB')\n"
                                           "sys.exit(3)\n")
    rec = Rec()

    def parse(line):
        if line.startswith("step "):
            return int(line.split()[1].split("/")[0]) / 50.0
        return None

    with pytest.raises(TrainStepError) as ei:
        b.run_logged([sys.executable, str(script)], tmp_path, backend_base.subprocess_env(), "gsv_s2_train", rec,
                     (0.2, 0.6), parse, label="训练音色")
    err = ei.value
    assert err.oom and err.code == 3 and err.log_name == "gsv_s2_train"
    first, second = str(err).splitlines()[:2]
    assert first == "「训练音色」这一步出错了：显卡内存（显存）不够"
    assert second.startswith("gsv_s2_train 失败（退出码 3）")
    assert "CUDA out of memory" in str(err)
    # 进度：映射到 0.2~0.6，说明是「训练音色：NN%」
    assert rec.calls[0] == (pytest.approx(0.2 + 0.4 * 0.02), "训练音色：2%")
    assert rec.calls[-1] == (pytest.approx(0.6), "训练音色：100%")
    # 主日志每 10% 一行，不刷屏
    lines = [m for m in vt_log.messages() if m.startswith("  训练音色：")]
    assert 5 <= len(lines) <= 12
    assert any(m == "▶ 训练音色（详细日志：gsv_s2_train.log）" for m in vt_log.messages())
    # 网页上的大白话报错认得出来
    from voicetwin.errors import explain

    assert explain(err).key == "gpu_oom"


def test_run_logged_unknown_failure_keeps_step_name(prepared, tmp_path):
    b = _plain_backend(prepared, tmp_path)
    script = _script(tmp_path, "bad.py", "import sys\nprint('something odd happened')\nsys.exit(2)\n")
    with pytest.raises(TrainStepError) as ei:
        b.run_logged([sys.executable, str(script)], tmp_path, backend_base.subprocess_env(), "gsv_1c_semantic")
    assert str(ei.value).splitlines()[0] == "「提取语义」这一步出错了"
    assert not ei.value.oom
    from voicetwin.errors import explain

    f = explain(ei.value)
    assert f.key == "step_failed" and "提取语义" in f.title


def test_run_logged_poll_progress(prepared, tmp_path):
    b = _plain_backend(prepared, tmp_path)
    out_dir = tmp_path / "feat"
    script = _script(tmp_path, "files.py", f"import os, time\nos.makedirs({str(out_dir)!r}, exist_ok=True)\n"
                                           f"for i in range(10):\n    open(os.path.join({str(out_dir)!r}, f'{{i}}.wav.pt'), 'w').close()\n"
                                           "    time.sleep(0.05)\n")
    rec = Rec()
    b.run_logged([sys.executable, str(script)], tmp_path, backend_base.subprocess_env(), "gsv_1b_hubert", rec,
                 (0.12, 0.18), label="提取声音特征", poll_progress=gsv._count_files(out_dir, "*.pt", 10),
                 poll_interval=0.03)
    counted = [m for m in rec.msgs if m.startswith("提取声音特征 ")]
    assert len(counted) >= 3
    fracs = [f for f, _ in rec.calls]
    assert fracs == sorted(fracs) and all(0.12 <= f <= 0.18 for f in fracs)


def test_run_logged_cancel_kills_process_tree(prepared, tmp_path, monkeypatch):
    from voicetwin.utils.progress import clear_cancel, request_cancel

    monkeypatch.setattr(backend_base, "CANCEL_POLL_SECONDS", 0.2)
    b = _plain_backend(prepared, tmp_path)
    pid_file = tmp_path / "child.pid"
    script = _script(tmp_path, "hang.py",
                     "import subprocess, sys, time\n"
                     "c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
                     f"open({str(pid_file)!r}, 'w').write(str(c.pid))\n"
                     "while True:\n    print('working', flush=True)\n    time.sleep(0.1)\n")
    clear_cancel()
    timer = threading.Timer(1.0, request_cancel)
    timer.start()
    t0 = time.time()
    try:
        with pytest.raises(TaskCancelled):
            b.run_logged([sys.executable, str(script)], tmp_path, backend_base.subprocess_env(), "gsv_s2_train",
                         label="训练音色")
    finally:
        timer.cancel()
        clear_cancel()
    assert time.time() - t0 < 6.0
    child = int(pid_file.read_text())
    deadline = time.time() + 5
    while _pid_alive(child) and time.time() < deadline:
        time.sleep(0.1)
    assert not _pid_alive(child)


def test_run_logged_refuses_to_start_after_stop(prepared, tmp_path):
    from voicetwin.utils.progress import clear_cancel, request_cancel

    b = _plain_backend(prepared, tmp_path)
    request_cancel()
    try:
        with pytest.raises(TaskCancelled):
            b.run_logged([sys.executable, "-c", "print(1)"], tmp_path, backend_base.subprocess_env(), "x")
    finally:
        clear_cancel()


# ---------------------------------------------------------------------------- 自动训练设置
def test_auto_save_every_keeps_last_epoch():
    table = {8: (8, 2), 12: (12, 2), 15: (15, 3), 10: (10, 2), 20: (20, 4), 25: (25, 5), 13: (14, 2), 11: (12, 2),
             1: (1, 1), 2: (2, 1), 3: (3, 1), 7: (7, 1), 9: (9, 3)}
    for epochs, expected in table.items():
        assert _auto_save_every(epochs) == expected, epochs
    for epochs in range(3, 51):
        e, s = _auto_save_every(epochs)
        assert e % s == 0 and 2 <= e // s <= 8 and e in (epochs, epochs + 1)


def _plan(total, minutes=45.0, clips=300, free=None, **kw):
    return plan_training(clips, minutes, total, free, **kw)


def test_plan_by_vram():
    # 包装盒上的大小 → PyTorch / nvidia-smi 报告的数字
    assert _plan(3.8)["batch_size"] == 1                   # 4 GB
    assert _plan(5.8)["batch_size"] == 2                   # 6 GB（官方公式是 3，小显存保守一点）
    assert _plan(7.6)["batch_size"] == 4                   # 8 GB：要加 0.4 才是官方的 4
    assert _plan(9.77)["batch_size"] == 5                  # 10 GB
    p12 = _plan(11.99, free=11.2)                          # 12 GB
    assert p12["batch_size"] == 6 and p12["tier"] == "mid"
    assert _plan(15.6)["batch_size"] == 8 and _plan(15.6)["tier"] == "high"
    assert _plan(23.99)["batch_size"] == 12
    assert _plan(47.5)["batch_size"] == 12                 # 再大只会更快，不会更好
    cpu = _plan(None)
    assert cpu["batch_size"] == 2 and cpu["tier"] == "none" and "没有检测到能用的 N 卡" in cpu["summary"]
    # 每批不超过素材条数 / 4；全精度时减半
    assert _plan(23.99, clips=20)["batch_size"] == 5
    assert _plan(11.99, is_half=False)["batch_size"] == 3


def test_plan_summary_12gb():
    p = _plan(11.99, free=11.2)
    assert (p["sovits_epochs"], p["gpt_epochs"], p["sovits_save_every"], p["gpt_save_every"]) == (12, 15, 2, 3)
    assert p["if_dpo"] is False and p["gpt_batch_size"] == 6
    s = p["summary"]
    assert s.startswith("训练计划：显存 12 GB → 每批 6 条；素材 45 分钟（300 条） → 音色 SoVITS 12 轮、语气 GPT 15 轮")
    assert "音色每 2 轮、语气每 3 轮存一次模型，训练完自动挑最像你的那个" in s
    assert "不开 DPO（它是实验功能，要显存 ≥ 22 GB" in s
    assert "\n" not in s and p["notes"] == []


def test_plan_epochs_by_material_not_vram():
    assert _plan(23.99, minutes=20)["sovits_epochs"] == 8
    assert _plan(5.8, minutes=20)["sovits_epochs"] == 8
    assert _plan(5.8, minutes=95)["sovits_epochs"] == 12
    assert _plan(23.99, minutes=300)["gpt_epochs"] == 15
    noisy = _plan(11.99, minutes=95, noisy=True)
    assert noisy["sovits_epochs"] == 8 and any("底噪" in n for n in noisy["notes"])


def test_plan_dpo_only_when_research_supports_it():
    big = _plan(23.99, minutes=85, clips=600, free=23.5)
    assert big["if_dpo"] is True and big["gpt_batch_size"] == 6 and big["batch_size"] == 12
    assert "开启 DPO（官方实验功能，用来减少重复、漏字；语气训练每批 6 条，会慢 2～4 倍）" in big["summary"]
    assert _plan(47.5)["gpt_batch_size"] == 8
    assert _plan(19.6)["if_dpo"] is False                   # 20 GB 不自动开
    assert _plan(23.99, noisy=True)["if_dpo"] is False
    sus = _plan(23.99, clips=100, suspects=10)
    assert sus["if_dpo"] is False and "还有 10 条文字可能有错" in sus["summary"]
    off = _plan(23.99, user={"if_dpo": False})
    assert off["if_dpo"] is False and "你在高级设置里关掉了" in off["summary"]
    forced = _plan(7.6, user={"if_dpo": "true"})
    assert forced["if_dpo"] is True and forced["gpt_batch_size"] == 1 and any("12 GB" in n for n in forced["notes"])
    assert "开启 DPO（你指定的；官方实验功能" in forced["summary"]
    assert _plan(11.99, user={"if_dpo": "开"})["notes"] == []


def test_plan_free_vram_and_explicit_overrides():
    busy = _plan(11.99, free=5.0)
    assert busy["batch_size"] == 2 and any("被别的程序占着" in n for n in busy["notes"])
    assert "现在空闲 5.0 GB" in busy["summary"]
    desktop = _plan(11.99, free=10.6)             # 桌面和浏览器本来就占一点：不影响
    assert desktop["batch_size"] == 6 and desktop["notes"] == [] and "空闲" not in desktop["summary"]
    user = {"batch_size": 3, "sovits_epochs": 10, "sovits_save_every": 4, "gpt_epochs": 13, "gpt_save_every": "auto"}
    p = _plan(23.99, user=user)
    assert p["batch_size"] == 3 and p["gpt_batch_size"] == 3
    assert (p["sovits_epochs"], p["sovits_save_every"]) == (12, 4)    # 10 不是 4 的倍数 → 12
    assert (p["gpt_epochs"], p["gpt_save_every"]) == (14, 2)          # 13 是质数 → 14
    assert sum("调整为" in n for n in p["notes"]) == 2
    assert "每批 3 条（你指定的）" in p["summary"] and "SoVITS 12 轮（你指定的）" in p["summary"]
    assert p["auto"]["batch_size"] is False and p["auto"]["gpt_save_every"] is True
    capped = _plan(11.99, user={"sovits_epochs": 99, "gpt_epochs": 99})
    assert capped["sovits_epochs"] == 25 and capped["gpt_epochs"] == 50


def test_user_settings_treat_legacy_save_every_as_auto(prepared, tmp_path):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV-set")
    old = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(root), "python": sys.executable, "train": {
        "batch_size": "auto", "sovits_save_every": 4, "gpt_save_every": 5}}})
    b = get_backend("gptsovits", old, project)
    u = b._user_settings({})
    assert u["sovits_save_every"] == "auto" and u["gpt_save_every"] == "auto" and u["if_dpo"] is None
    u = b._user_settings({"sovits_save_every": 4, "batch_size": None, "gpt_epochs": 20, "if_dpo": False})
    assert u["sovits_save_every"] == 4 and u["batch_size"] == "auto" and u["gpt_epochs"] == 20 and u["if_dpo"] is False
    mine = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(root), "python": sys.executable, "train": {
        "sovits_save_every": 3, "if_dpo": "auto"}}})
    u = get_backend("gptsovits", mine, project)._user_settings({})
    assert u["sovits_save_every"] == 3 and u["if_dpo"] == "auto"


def test_training_plan_preview(prepared, tmp_path, no_users_pth):
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV-plan")
    b = get_backend("gptsovits", _gcfg(project, root, 19881), project)
    plan = b.training_plan()
    assert plan["summary"].startswith("训练计划：显存 12 GB")
    assert plan["n_clips"] > 0 and plan["minutes"] > 0 and plan["noisy"] is False
    assert b.training_plan(batch_size=1)["batch_size"] == 1


def test_material_noise_from_sources(prepared, tmp_path):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-noise")
    gcfg = make_cfg(ws, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    assert b._material_quality()[0] is False
    sources = p2.read_json(p2.sources_path, {})
    for sid in sources:
        sources[sid]["snr_before"] = 12.0
    p2.write_json(p2.sources_path, sources)
    noisy, share, suspects = b._material_quality()
    assert noisy is True and share == 1.0 and suspects == 0


# ---------------------------------------------------------------------------- 检查点挑选
def test_checkpoints_spread_early_to_late(prepared, tmp_path):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-ck")
    gcfg = make_cfg(ws, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    if p2.models_path.exists():
        p2.models_path.unlink()
    b = get_backend("gptsovits", gcfg, p2)
    sd, gd = root / "SoVITS_weights_v2ProPlus", root / "GPT_weights_v2ProPlus"
    sd.mkdir(parents=True)
    gd.mkdir(parents=True)
    for e in (2, 4, 6, 8, 10, 12):
        (sd / f"{b.exp_name}_e{e}_s{e * 30}.pth").write_bytes(b"x")
    for e in (3, 6, 9, 12, 15):
        (gd / f"{b.exp_name}-e{e}.ckpt").write_bytes(b"x")
    ids = [c["id"] for c in b.checkpoints()]
    assert len(ids) == 12 and ids[-1] == "s12-g15"
    assert {c["sovits_epoch"] for c in b.checkpoints()} == {4, 6, 10, 12}
    assert {c["gpt_epoch"] for c in b.checkpoints()} == {6, 12, 15}
    assert len(b.checkpoints(max_sovits=2, max_gpt=1)) == 2
    assert [p for p in _spread([1, 2, 3], 4)] == [1, 2, 3]
    assert _spread(list(range(1, 11)), 1) == [10]


# ---------------------------------------------------------------------------- 显存不够自动重试
@needs_fake_python
def test_oom_retry_halves_batch_once(prepared, tmp_path, monkeypatch, no_users_pth, vt_log):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-oom")
    gcfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": 19882, "is_half": True,
        "train": {"sovits_epochs": 4, "gpt_epochs": 4, "batch_size": 4}}})
    monkeypatch.setenv("FAKE_GSV_OOM_ABOVE", "2")
    rec = Rec()
    info = wf.run_train(gcfg, project.voice, "gptsovits", select=False, progress=rec)
    params = info["params"]
    assert params["oom_retry"] is True and params["batch_size_used"] == 2 and params["gpt_batch_size_used"] == 2
    warn = [m for m in vt_log.messages(logging.WARNING) if "显存不够：自动把每批数量从 4 减到 2" in m]
    assert len(warn) == 2 and warn[0].startswith("训练音色（SoVITS）") and warn[1].startswith("训练语气和节奏（GPT）")
    assert len(info["sovits"]) == 4 and len(info["gpt"]) == 4  # 4 轮：每轮都存
    fracs = [f for f, _ in rec.train_part()]
    assert fracs == sorted(fracs)
    tmp_s2 = json.loads((wf.open_project(gcfg, project.voice).models_dir / "gptsovits" / "tmp_s2.json").read_text("utf-8"))
    assert tmp_s2["train"]["batch_size"] == 2


def test_oom_with_batch_one_gives_friendly_error(prepared, tmp_path, monkeypatch, no_users_pth):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-oom1")
    gcfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "train": {"sovits_epochs": 2, "gpt_epochs": 2, "batch_size": 1}}})
    monkeypatch.setenv("FAKE_GSV_OOM_ABOVE", "0")
    with pytest.raises(TrainStepError) as ei:
        wf.run_train(gcfg, project.voice, "gptsovits", select=False)
    from voicetwin.errors import explain

    f = explain(ei.value)
    assert f.key == "gpu_oom" and "每批数量" in f.advice
    assert str(ei.value).startswith("「训练音色」这一步出错了：显卡内存（显存）不够")


# ---------------------------------------------------------------------------- 素材变了：从头训练
@needs_fake_python
def test_retrain_after_material_change_starts_fresh(prepared, tmp_path, no_users_pth, vt_log):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-re")
    gcfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "train": {"sovits_epochs": 4, "gpt_epochs": 4, "batch_size": 2}}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    first = wf.run_train(gcfg, project.voice, "gptsovits", select=False)
    exp = first["exp_name"]
    opt_dir = root / "logs" / exp
    assert not (opt_dir / "old_runs").exists()
    assert (opt_dir / "logs_s2_v2ProPlus" / "G_233333333333.pth").exists()

    # 同样的素材再练一次：GPT-SoVITS 接着上次的进度，0 轮可练，模型还是原来那些
    again = wf.run_train(gcfg, project.voice, "gptsovits", select=False)
    assert again["sovits"] == first["sovits"] and again["gpt"] == first["gpt"]

    # 换了素材（删掉 3 条）：旧进度备份走，从第 1 轮开始练，models.json 只记新模型
    time.sleep(0.05)
    recs = p2.load_manifest()
    kept = [r for r in recs if r.get("keep", True) and r.get("split", "train") == "train"]
    for r in kept[:3]:
        r["keep"] = False
    p2.save_manifest(recs)
    second = wf.run_train(gcfg, project.voice, "gptsovits", select=False)
    old_runs = list((opt_dir / "old_runs").iterdir())
    assert len(old_runs) == 1 and (old_runs[0] / "logs_s2_v2ProPlus").is_dir() and (old_runs[0] / "logs_s1_v2ProPlus").is_dir()
    assert any("检测到素材有变化：这次会从头训练新模型（旧的训练进度已备份到" in m for m in vt_log.messages())
    s2_log = (p2.logs_dir / "gsv_s2_train.log").read_text(encoding="utf-8")
    assert s2_log.rstrip().split("=====")[-1].count("start training from epoch 1") == 1
    started = float((opt_dir / gsv.RUN_STAMP).read_text())
    for path in second["sovits"] + second["gpt"]:
        assert Path(path).stat().st_mtime >= started - 2
    assert set(second["sovits"]).isdisjoint(first["sovits"])   # 步数不同 → 新文件名；旧文件不混进来
    assert len(second["sovits"]) == 4 and len(second["gpt"]) == 4
    # 旧素材的模型文件还在硬盘上（以前选中的模型不会突然消失），只是不再参加挑选
    assert all(Path(p).exists() for p in first["sovits"])
    b = get_backend("gptsovits", gcfg, p2)
    assert {c["sovits"] for c in b.checkpoints()} <= set(second["sovits"])


# ---------------------------------------------------------------------------- 推理服务
def _ref(project):
    refs = project.load_references()
    r = refs[0]
    return project.abspath(r["path"]), r["text"], r.get("lang", "zh")


@needs_fake_python
def test_synthesis_failure_reports_real_reason(prepared, tmp_path, monkeypatch, vt_log):
    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-api")
    gcfg = make_cfg(ws, backends={"gptsovits": {"root": str(root), "python": sys.executable, "port": 19883,
                                                "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    monkeypatch.setenv("FAKE_GSV_API_DELAY", "1.0")
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    b = get_backend("gptsovits", gcfg, p2)
    ref, ref_text, ref_lang = _ref(p2)
    try:
        b.start()
        assert any(m.startswith("推理服务启动中……已等待") for m in vt_log.messages())
        out = b.synthesize(SynthRequest(text="你好。", lang="zh", ref_audio=ref, ref_text=ref_text, ref_lang=ref_lang,
                                        speed=0.85), tmp_path / "ok.wav")
        assert out.exists() and out.stat().st_size > 1000
        with pytest.raises(RuntimeError) as ei:
            b.synthesize(SynthRequest(text="【测试显存不够】这一句。", lang="zh", ref_audio=ref, ref_text=ref_text,
                                      ref_lang=ref_lang), tmp_path / "bad.wav")
        assert "CUDA out of memory" in str(ei.value) and str(ei.value).startswith("GPT-SoVITS 合成失败：")
        from voicetwin.errors import explain

        assert explain(ei.value).key == "gpu_oom"
    finally:
        b.stop()
    assert b.proc is None


@needs_fake_python
def test_cancel_while_inference_server_starts(prepared, tmp_path, monkeypatch):
    from voicetwin.utils.progress import clear_cancel, request_cancel

    cfg, project, _ = prepared
    ws = _copy_project(project, tmp_path / "ws")
    root = build_fake_root(tmp_path / "GSV-api2")
    gcfg = make_cfg(ws, backends={"gptsovits": {"root": str(root), "python": sys.executable, "port": 19884,
                                                "startup_timeout": 60}})
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    monkeypatch.setenv("FAKE_GSV_API_DELAY", "30")
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    b = get_backend("gptsovits", gcfg, p2)
    clear_cancel()
    timer = threading.Timer(0.8, request_cancel)
    timer.start()
    t0 = time.time()
    try:
        with pytest.raises(TaskCancelled):
            b.start()
    finally:
        timer.cancel()
        clear_cancel()
        b.stop()
    assert time.time() - t0 < 15 and b.proc is None


# ---------------------------------------------------------------------------- 其它引擎
def test_qwen3_declares_train_stages():
    from voicetwin.backends.qwen3tts import Qwen3TTSBackend, _epoch_parser

    assert Qwen3TTSBackend.train_stages == [(0.0, "准备"), (0.05, "提取音频编码"), (0.15, "微调训练")]
    assert GPTSoVITSBackend.train_stages[0] == (0.0, "检查显卡、整理训练素材")
    assert [f for f, _ in GPTSoVITSBackend.train_stages] == sorted(f for f, _ in GPTSoVITSBackend.train_stages)
    assert backend_base.Backend.train_stages == [(0.0, "训练模型")]
    p = _epoch_parser(3)
    assert p("Epoch 0 | Step 10 | Loss: 1.2345") == (0.0, "微调训练：第 1/3 轮")
    assert p("Epoch 2 | Step 10 | Loss: 1.2345") == (pytest.approx(2 / 3), "微调训练：第 3/3 轮")
    assert p("loading model") is None


# ---------------------------------------------------------------------------- 下载预训练模型
class _FakeResp:
    def __init__(self, data=b"", js=None, fail=False):
        self.data, self.js, self.fail = data, js, fail
        self.headers = {"Content-Length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        return None

    def json(self):
        return self.js

    def iter_content(self, chunk_size=1):
        half = len(self.data) // 2
        yield self.data[:half]
        if self.fail:
            raise ConnectionError("连接被重置")
        yield self.data[half:]


def test_download_retries_and_replaces_broken_files(prepared, tmp_path, monkeypatch, vt_log):
    import requests

    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV-dl")
    pm = root / "GPT_SoVITS/pretrained_models"
    (pm / "s1v3.ckpt").write_bytes(b"")                 # 坏文件：要重新下载
    shutil.rmtree(pm / "chinese-hubert-base")           # 整个文件夹没有
    calls = {"s1v3.ckpt": 0}
    weight = b"w" * 5000

    class FakeSession:
        def get(self, url, timeout=None, stream=False, params=None):
            if "/api/models/" in url:
                assert url.endswith("/tree/main/chinese-hubert-base")
                return _FakeResp(js=[{"type": "file", "path": "chinese-hubert-base/config.json", "size": 2},
                                     {"type": "file", "path": "chinese-hubert-base/preprocessor_config.json", "size": 2},
                                     {"type": "file", "path": "chinese-hubert-base/pytorch_model.bin",
                                      "lfs": {"size": len(weight)}}])
            name = url.rsplit("/", 1)[-1]
            if name == "s1v3.ckpt":
                calls[name] += 1
                return _FakeResp(weight, fail=calls[name] == 1)   # 第一次下到一半断了
            return _FakeResp(b"{}" if name.endswith(".json") else weight)

    monkeypatch.setattr(requests, "Session", FakeSession)
    monkeypatch.setattr(gsv, "DOWNLOAD_BACKOFF", (0.0, 0.0))
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
    b = get_backend("gptsovits", gcfg, project)
    assert b.missing_pretrained() == [gsv.HUBERT_DIR, "GPT_SoVITS/pretrained_models/s1v3.ckpt"]
    rec = Rec()
    got = b.download_pretrained(source="hf-mirror", progress=rec)
    assert "s1v3.ckpt" in got and "chinese-hubert-base/pytorch_model.bin" in got
    assert calls["s1v3.ckpt"] == 2 and (pm / "s1v3.ckpt").read_bytes() == weight
    assert not (pm / "s1v3.ckpt.part").exists()
    assert b.missing_pretrained() == []
    assert any("秒后重试" in m for m in vt_log.messages(logging.WARNING))
    assert any(m.startswith("下载 pytorch_model.bin：") for m in rec.msgs)
