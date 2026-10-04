"""「一模一样」第 7 步：训练（设计方案 §2 P7、§5.1 tests/test_deep_training.py）。

训练计划（标准的一个数都不变）、实测显卡一次能练几条、显存不够每批减 1 条、分两路提取特征、实际参加训练的条数、
从头练 / 接着练 / 不重新练、原来的模型参加比较、硬盘检查、实测用时、素材检查、网页和命令行的「训练方式」。
用到仿真 GPT-SoVITS 的 s1 训练（要 yaml）的测试在整合包同版本的环境里跳过（已知的环境问题，见 test_gptsovits_fake）；
只用 s2 / 1A / 1B / 1C 的测试（只要标准库）三个环境都跑。"""

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
from voicetwin.backends.base import TrainStepError, get_backend
from voicetwin.backends.gptsovits import (
    GPTSoVITSBackend,
    _capture_s1,
    _capture_s2,
    _disk_save_every,
    _report_lines,
    _trained_counts,
    plan_training,
    resolve_train_mode,
)
from voicetwin.project import Project
from voicetwin.utils import gpu as gpu_mod

from conftest import confirm_material, make_cfg
from fake_gptsovits import build_fake_root


def _fake_python_ok() -> bool:
    try:
        proc = subprocess.run([str(Path(sys.executable).resolve()), "-c", "import yaml"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


needs_fake_python = pytest.mark.skipif(not _fake_python_ok(), reason="这个环境里 fake GPT-SoVITS 的子进程缺少 yaml（已知的环境问题）")


class _Log(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


@pytest.fixture
def vt_log():
    h = _Log()
    logger = logging.getLogger("voicetwin")
    old = logger.level
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
    try:
        yield h
    finally:
        logger.removeHandler(h)
        logger.setLevel(old)


@pytest.fixture
def gsv_env(prepared, tmp_path, monkeypatch):
    """复制一份测试声音 + 仿真 GPT-SoVITS；显卡当作 12 GB（不读真显卡）；处理文字用测试模式（不加载 BERT）。"""
    _, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "POLL_SECONDS", 0.05)
    monkeypatch.setattr(GPTSoVITSBackend, "PROBE_POLL_SECONDS", 0.05)
    monkeypatch.setenv("FAKE_GSV_CLIP_SLEEP", "0")
    monkeypatch.setenv("VOICETWIN_TEXT_DRYRUN", "1")

    def make(**train):
        cfg = make_cfg(ws, backend="gptsovits", backends={"gptsovits": {
            "root": str(root), "python": sys.executable, "is_half": True, "train": train}})
        p = wf.open_project(cfg, project.voice, must_exist=True)
        return cfg, p, get_backend("gptsovits", cfg, p)

    return make


def _features(b, parts=1, **kw):
    from voicetwin.data.exporters import export_gptsovits

    exp = export_gptsovits(b.project, speaker=b.exp_name)
    res = b._prepare_features(Path(exp["list"]), Path(exp["wav_dir"]), None, n_clips=int(exp["count"]), parts=parts, **kw)
    return res, int(exp["count"])


def _epochs(paths):
    return sorted(gsv._epoch(Path(p)) for p in paths)


# ============================================================================ 训练计划
def _plan(**kw):
    return plan_training(984, 32.8, 7.96, 6.8, **kw)


def _nums(p):
    return p["batch_size"], p["sovits_epochs"], p["sovits_save_every"], p["gpt_epochs"], p["gpt_save_every"]


def test_standard_plan_is_unchanged():
    std = _plan()
    assert _nums(std) == (4, 12, 2, 15, 3) and std["if_dpo"] is False and std["mode"] == "standard"
    assert std["summary"] == ("训练计划：显存 8 GB → 每批 4 条；素材 32.8 分钟（984 条） → 音色 SoVITS 12 轮、语气 GPT 15 轮；"
                              "音色每 2 轮、语气每 3 轮存一次模型，训练完自动挑最像你的那个；"
                              "不开 DPO（官方实验功能，显存也不够；需要的话可以在高级设置里手动打开）。")
    # 标准方式不管实测的每批条数
    assert _nums(_plan(mode="standard", probe_batch=6)) == (4, 12, 2, 15, 3)


def test_identical_plan_numbers():
    deep = _plan(mode="identical")
    assert _nums(deep) == (4, 24, 2, 20, 1) and deep["if_dpo"] is False and deep["mode"] == "identical"
    assert _nums(_plan(mode="identical", probe_batch=6)) == (6, 36, 3, 30, 2)
    # 音色和语气实测出来的不一样；轮数有上限（音色 48、语气 50），最后一轮一定存下来
    d = _plan(mode="identical", probe_batch={"sovits": 8, "gpt": 12})
    assert (d["batch_size"], d["gpt_batch_size"]) == (8, 12)
    assert (d["sovits_epochs"], d["sovits_save_every"], d["gpt_epochs"], d["gpt_save_every"]) == (48, 4, 48, 3)
    assert any("语气（GPT）轮数从 50 调整为 48" in n for n in d["notes"])
    for b in range(1, 13):
        p = plan_training(5000, 300, 23.99, None, mode="identical", probe_batch=b)
        assert p["sovits_epochs"] % p["sovits_save_every"] == 0 and p["sovits_epochs"] <= 48
        assert p["gpt_epochs"] % p["gpt_save_every"] == 0 and p["gpt_epochs"] <= 50
    # 你自己填的数优先（填了每批数量就不用实测的；每批不到 4 条时语气轮数按 4 条算，还是 20 轮）
    u = _plan(mode="identical", probe_batch=6, user={"sovits_epochs": 30, "gpt_save_every": 5, "batch_size": 3})
    assert (u["batch_size"], u["sovits_epochs"], u["gpt_epochs"], u["gpt_save_every"]) == (3, 30, 20, 5)
    assert "音色 SoVITS 30 轮（你指定的）" in u["summary"] and "每批 3 条（你指定的）" in u["summary"]
    # config.yaml 可以改每批 4 条时的训练量
    assert _nums(_plan(mode="identical", deep={"sovits_epochs": 16, "gpt_epochs": 10})) == (4, 16, 2, 10, 1)


def test_identical_plan_summary_says_only_what_will_happen():
    s = _plan(mode="identical", will_probe=True, n_val=20, mixed_text=True, en_lines=559)["summary"]
    assert s.startswith("训练计划：「一模一样」训练——显存 8 GB → 先实测一次能练几条（按显存估计每批 4 条）；")
    assert "音色 SoVITS 24 轮、每 2 轮存一个；语气 GPT 20 轮、每轮存一个（实测的每批条数不一样时，轮数按比例调整，模型更新的次数不变）" in s
    assert "中文和英文都参加训练（素材里有 559 句夹着英文）" in s
    assert "训练完用你没参加训练的 20 句录音把第 4 轮以后存下的每个版本都试一遍，挑最像你的" in s
    measured = _plan(mode="identical", probe_batch=6, will_probe=True)
    assert "每批 6 条（实测）" in measured["summary"] and "先实测" not in measured["summary"]
    assert any("练得太多可能变差，所以第 4 轮以后存下的每个版本都会拿来比较" in n for n in measured["notes"])
    assert "每批 4 条（和上次一样）" in _plan(mode="identical", probe_batch=4, batch_source="previous")["summary"]
    # 只实测出音色的：语气的每批条数按显存的公式，说明里不能写成实测的
    one = plan_training(984, 32.8, 11.99, 11.2, mode="identical", probe_batch={"sovits": 8, "gpt": None})
    assert (one["batch_size"], one["gpt_batch_size"]) == (8, 6)
    assert "音色每批 8 条（实测）、语气每批 6 条（按显存估计）" in one["summary"]
    cpu = plan_training(984, 32.8, None, None, mode="identical")
    assert "没有检测到能用的 N 卡" in cpu["summary"] and "仍然按「一模一样」训练，但用处理器会非常慢" in cpu["summary"]
    for p in (cpu, measured, _plan(mode="identical")):
        assert "V4" not in p["summary"] and "检查用的句子" not in p["summary"]


def test_train_mode_resolution(monkeypatch):
    for v in (None, "", "auto", "自动", "identical", "一模一样", "一模一样（默认）"):
        assert resolve_train_mode(v) == "identical"
    for v in ("standard", "标准", "标准：和以前一样"):
        assert resolve_train_mode(v) == "standard"
    assert resolve_train_mode("garbage") == "identical"
    cfg = make_cfg(Path("."), backend="gptsovits")
    assert wf.train_mode(cfg) == "identical" and wf.train_mode(cfg, "standard") == "standard"
    cfg2 = make_cfg(Path("."), backend="gptsovits", backends={"gptsovits": {"train": {"mode": "standard"}}})
    assert wf.train_mode(cfg2) == "standard" and wf.train_mode(cfg2, "identical") == "identical"


def test_train_stage_tables():
    deep = GPTSoVITSBackend.train_stages_for("identical")
    assert [n for _, n in deep] == ["检查显卡、整理训练素材", "处理文字", "提取声音特征", "提取语义", "实测显卡一次能练几条",
                                    "训练音色（SoVITS）", "训练语气和节奏（GPT）", "保存模型、核对实际参加训练的条数"]
    assert GPTSoVITSBackend.train_stages_for("standard") == GPTSoVITSBackend.train_stages
    assert [f for f, _ in deep] == sorted(f for f, _ in deep)
    for mode, table in gsv.TRAIN_POS.items():  # 进度条的每一步和训练时报的进度对得上
        stages = dict((n, f) for f, n in GPTSoVITSBackend.train_stages_for(mode))
        assert stages["训练音色（SoVITS）"] == table["sovits"] and stages["训练语气和节奏（GPT）"] == table["gpt"]
    cfg = make_cfg(Path("."), backend="gptsovits")
    st = wf.task_stages("train", cfg, "gptsovits", mode="identical")
    assert st[-1] == (wf.TRAIN_SELECT_SPLIT_IDENTICAL, "自动挑选最像你的模型")
    assert not any("V4" in n for _, n in st)


# ============================================================================ 子进程：练够了就停
def _dummy_backend(prepared, tmp_path):
    _, project, _ = prepared
    shutil.copytree(project.root, tmp_path / "wsd" / project.voice)
    cfg = make_cfg(tmp_path / "wsd")
    return get_backend("dummy", cfg, wf.open_project(cfg, project.voice, must_exist=True))


def test_run_logged_stop_when_and_on_poll(prepared, tmp_path):
    b = _dummy_backend(prepared, tmp_path)
    script = tmp_path / "forever.py"
    script.write_text("import time\ni = 0\nwhile True:\n    i += 1\n    print(f'step {i}', flush=True)\n"
                      "    time.sleep(0.01)\n", encoding="utf-8")
    seen = []

    def stop_when(line):
        seen.append(line)
        return line == "step 20"

    t0 = time.time()
    res = b.run_logged([sys.executable, str(script)], tmp_path, backend_base.subprocess_env(), "probe_test",
                       stop_when=stop_when)
    assert res["stopped"] is True and time.time() - t0 < 20 and "step 20" in seen
    polls = []

    def on_poll():
        polls.append(time.time())
        return len(polls) >= 3

    res = b.run_logged([sys.executable, str(script)], tmp_path, backend_base.subprocess_env(), "probe_test",
                       on_poll=on_poll, poll_interval=0.05)
    assert res["stopped"] is True and len(polls) >= 3
    ok = b.run_logged([sys.executable, "-c", "print('done')"], tmp_path, backend_base.subprocess_env(), "probe_test")
    assert ok == {"stopped": False, "code": 0, "oom": False}


def test_gpu_sampler_measures_only_when_nvidia_smi_works(monkeypatch):
    samples = iter([40.0, 60.0, 80.0] + [80.0] * 1000)

    def fake(index=0):
        u = next(samples)
        return {"used_gb": u / 10.0, "total_gb": 12.0, "util": u}

    monkeypatch.setattr(gpu_mod, "smi_sample", fake)
    s = gpu_mod.GpuSampler(0.02).start()
    time.sleep(0.2)
    r = s.stop()
    assert r["n"] >= 3 and r["peak_gb"] == 8.0 and 40.0 < r["util_avg"] <= 80.0
    monkeypatch.setattr(gpu_mod, "smi_sample", lambda index=0: None)
    assert gpu_mod.GpuSampler(0.02).start().stop() == {"util_avg": None, "peak_gb": None, "n": 0}


# ============================================================================ 实测显卡一次能练几条
def _probe_smi(b, per_batch=1.0, base=2.0):
    """假的 nvidia-smi：显存用量按正在实测的每批条数算（从实测用的训练设置里读）。"""
    def fake(index=0):
        for name in ("tmp_probe_s2.json", "tmp_probe_s1.yaml"):
            p = b.work_dir / name
            if p.exists():
                text = p.read_text(encoding="utf-8")
                try:
                    bs = json.loads(text)["train"]["batch_size"]
                except ValueError:
                    import yaml

                    bs = yaml.safe_load(text)["train"]["batch_size"]
                return {"used_gb": base + per_batch * bs, "total_gb": 12.0, "util": 97.0}
        return None

    return fake


def test_probe_picks_the_fastest_batch_and_cleans_up(gsv_env, monkeypatch, vt_log):
    _, project, b = gsv_env()
    _, n = _features(b)
    monkeypatch.setenv("FAKE_GSV_SLOW_ABOVE", "5")   # 每批超过 5 条就不再更快
    monkeypatch.setattr(gpu_mod, "smi_sample", _probe_smi(b))
    probe = b._build_probe_dir(b._opt_dir())
    names = [ln.split("\t")[0] for ln in (probe / "2-name2text.txt").read_text(encoding="utf-8").strip().split("\n")]
    assert len(names) == min(gsv.PROBE_CLIPS, n) and len(set(names)) == len(names)
    assert len(list((probe / "4-cnhubert").glob("*.pt"))) == len(names)
    best, table = b._probe_batch("sovits", [4, 5, 6], probe)
    assert best == 5 and [r["bs"] for r in table] == [4, 5, 6] and all(r["ok"] for r in table)
    assert table[1]["samples_per_s"] > 1.05 * table[0]["samples_per_s"] > 0
    assert table[2]["samples_per_s"] < table[1]["samples_per_s"]       # 6 条反而更慢：不用
    assert [r["peak_gb"] for r in table] == [6.0, 7.0, 8.0]
    assert any(m == "音色：选定每批 5 条（实测最快，显存没有溢出）" for m in vt_log.messages)
    assert any(m.startswith("实测显卡一次能练几条（音色）：正在试每批 4 条") for m in vt_log.messages)
    # 练够 40 步就停：日志里没有练完 100 轮；没有存任何模型文件
    log_text = (project.logs_dir / "gsv_probe_sovits.log").read_text(encoding="utf-8")
    assert "training done" not in log_text and "saving ckpt" not in log_text
    assert not list(b.p("SoVITS_weights_v2ProPlus").glob(f"{b.exp_name}*")) if b.p("SoVITS_weights_v2ProPlus").exists() else True
    assert not list(probe.rglob("*.pth"))
    # 显存满了（再多会借用内存、变慢）：不再试更大的
    monkeypatch.setenv("FAKE_GSV_SLOW_ABOVE", "8")
    monkeypatch.setattr(gpu_mod, "smi_sample", _probe_smi(b, per_batch=1.3))
    best, table = b._probe_batch("sovits", [4, 6, 8], probe)
    assert best == 6 and table[-1]["ok"] is False and table[-1]["why"].startswith("显存满了")
    # 训练时实测完把实测用的文件夹删掉（_probe_or_cached）
    pos = gsv.TRAIN_POS["identical"]
    shutil.rmtree(probe, ignore_errors=True)
    monkeypatch.setattr(gpu_mod, "smi_sample", _probe_smi(b))
    monkeypatch.setattr(gsv, "PROBE_GPT", (4,))
    monkeypatch.setattr(GPTSoVITSBackend, "_probe_batch",
                        lambda self, kind, cands, d, progress=None, prange=(0, 1):
                        (max(cands), [{"bs": max(cands), "ok": True}]) if kind == "sovits" else (None, []))
    res, secs = b._probe_or_cached(b._opt_dir(), "digest-1", n, False, None, pos)
    assert res["sovits"] == min(6, n // 4) and not b.p(f"logs/{b.exp_name}_probe").exists()
    # 同一份素材再来一次（例如上次训练中途停下）：用上次实测的结果
    again, secs2 = b._probe_or_cached(b._opt_dir(), "digest-1", n, False, None, pos)
    assert again["sovits"] == res["sovits"] and secs2 is None


@needs_fake_python
def test_probe_for_gpt(gsv_env, monkeypatch):
    _, project, b = gsv_env()
    _features(b)
    monkeypatch.setenv("FAKE_GSV_SLOW_ABOVE", "4")
    monkeypatch.setattr(gpu_mod, "smi_sample", _probe_smi(b))
    probe = b._build_probe_dir(b._opt_dir())
    best, table = b._probe_batch("gpt", [4, 6], probe)
    assert best == 4 and len(table) == 2 and table[0]["samples_per_s"] > table[1]["samples_per_s"]
    assert "Epoch" in (project.logs_dir / "gsv_probe_gpt.log").read_text(encoding="utf-8")
    assert not list(probe.rglob("*.ckpt"))


@needs_fake_python
def test_training_measures_the_batch_first(gsv_env, monkeypatch):
    """「一模一样」、每批数量是自动的：先实测（音色超过 5 条不再更快 → 5 条），轮数按实测的条数算。"""
    cfg, project, b = gsv_env()
    monkeypatch.setenv("FAKE_GSV_SLOW_ABOVE", "5")
    monkeypatch.setattr(gpu_mod, "smi_sample", _probe_smi(b))
    confirm_material(cfg, project.voice)
    info = wf.run_train(cfg, project.voice, "gptsovits", select=False)
    p = info["params"]
    assert p["mode"] == "identical" and p["probe"]["sovits"] == 5 and p["batch_size"] == 5
    assert (p["sovits_epochs"], p["sovits_save_every"]) == (30, 3)  # ⌈24 × 5 / 4⌉ = 30，每 round(2.5) = 3 轮
    assert p["timing"]["probe_s"] is not None and "（实测）" in p["summary"]
    assert not b.p(f"logs/{b.exp_name}_probe").exists()


@needs_fake_python
def test_plan_does_not_claim_a_probe_that_found_nothing(gsv_env, monkeypatch):
    """实测没有结果（每个数量都没成功）：按显存的公式练，存下来的、网页上显示的训练计划都不能再写「先实测」。"""
    cfg, project, b = gsv_env()
    monkeypatch.setattr(GPTSoVITSBackend, "_probe_batch",
                        lambda self, kind, cands, d, progress=None, prange=(0, 1):
                        (None, [{"bs": c, "ok": False, "why": "测试"} for c in cands]))
    confirm_material(cfg, project.voice)
    msgs = []
    info = wf.run_train(cfg, project.voice, "gptsovits", select=False, progress=lambda f, m="": msgs.append(m))
    p = info["params"]
    assert p["mode"] == "identical" and "先实测" not in p["summary"] and "（实测）" not in p["summary"]
    assert project.load_models()["gptsovits"]["params"]["summary"] == p["summary"]
    plans = [m for m in msgs if m.startswith("训练计划：")]
    assert "先实测" in plans[0] and plans[-1] == p["summary"]


# ============================================================================ 显存不够：每批减 1 条
def test_oom_ladder_steps_one_at_a_time(gsv_env, vt_log):
    _, _, b = gsv_env()
    calls = []

    def run(bs):
        calls.append(bs)
        if bs > 5:
            raise TrainStepError("x", oom=True)

    assert b._oom_ladder("训练音色（SoVITS）", 6, run, None, 0.3) == 5 and calls == [6, 5]
    assert vt_log.messages[-1] == "训练音色（SoVITS）：显存不够：每批从 6 条减到 5 条，接着练（已经练好的部分会接着用）"
    calls.clear()

    def always(bs):
        calls.append(bs)
        raise TrainStepError("x", oom=True)

    with pytest.raises(TrainStepError):
        b._oom_ladder("x", 8, always, None, 0.3)
    assert calls == [8, 7, 6, 5]                      # 最多减 3 次
    calls.clear()
    with pytest.raises(TrainStepError):
        b._oom_ladder("x", 2, always, None, 0.3, floor_bs=1)
    assert calls == [2, 1]
    calls.clear()
    with pytest.raises(TrainStepError):              # 不是显存不够：不重试
        b._oom_ladder("x", 6, lambda bs: (calls.append(bs), (_ for _ in ()).throw(TrainStepError("y"))), None, 0.3)
    assert calls == [6]
    fixed = []
    calls.clear()

    def needs_resort(bs):
        calls.append(bs)
        if not fixed:
            raise TrainStepError("x", oom=True)

    assert b._oom_ladder("x", 1, needs_resort, None, 0.3, last_resort=lambda: fixed.append(1)) == 1
    assert calls == [1, 1]


@needs_fake_python
def test_training_oom_steps_down_and_records_the_batch(gsv_env, monkeypatch):
    cfg, project, b = gsv_env(batch_probe=False)     # 不实测：按显存的公式每批 6 条
    monkeypatch.setenv("FAKE_GSV_OOM_ABOVE", "5")
    confirm_material(cfg, project.voice)
    info = wf.run_train(cfg, project.voice, "gptsovits", select=False)
    p = info["params"]
    assert p["batch_size"] == 6 and p["batch_size_used"] == 5 and p["gpt_batch_size_used"] == 5 and p["oom_retry"]
    s2 = json.loads((project.models_dir / "gptsovits" / "tmp_s2.json").read_text(encoding="utf-8"))
    assert s2["train"]["batch_size"] == 5 and s2["train"]["log_interval"] == 20
    import yaml

    s1 = yaml.safe_load((project.models_dir / "gptsovits" / "tmp_s1.yaml").read_text(encoding="utf-8"))
    assert s1["data"]["num_workers"] == max(2, min(8, (os.cpu_count() or 4) - 2))


# ============================================================================ 分两路提取特征
def test_features_in_two_parts_are_merged(gsv_env, monkeypatch, vt_log):
    _, project, b = gsv_env()
    monkeypatch.setenv("FAKE_GSV_FAIL_PART_ONCE", "1")   # 第 2 路第一次出错：单独再做一次
    res, n = _features(b, parts=2)
    opt = b._opt_dir()
    text = [ln.split("\t")[0] for ln in (opt / "2-name2text.txt").read_text(encoding="utf-8").strip().split("\n")]
    sem = (opt / "6-name2semantic.tsv").read_text(encoding="utf-8").strip().split("\n")
    assert sem[0] == "item_name\tsemantic_audio"
    sem_names = [ln.split("\t")[0] for ln in sem[1:]]
    assert len(text) == len(set(text)) == n and sorted(sem_names) == sorted(text) and len(set(sem_names)) == n
    assert len(list((opt / "4-cnhubert").glob("*.pt"))) == n and len(list((opt / "7-sv_cn").glob("*.pt"))) == n
    assert not list(opt.glob("2-name2text-*.txt")) and not list(opt.glob("6-name2semantic-*.tsv"))
    assert (project.logs_dir / "gsv_1b_hubert_2.log").exists() and (project.logs_dir / "gsv_1c_semantic_2.log").exists()
    assert any(m.startswith("「提取声音特征」第 2 路出错了") and m.endswith("单独把这一路再做一次……") for m in vt_log.messages)
    counted = b._count_features(opt, n)
    assert counted == {"expected": n, "text": n, "semantic": n, "hubert": n, "wav32k": n, "sv": n, "bert": 0}
    # 显卡档位决定几路：8 GB 档以上 2 路
    assert (b._feature_parts("high"), b._feature_parts("mid"), b._feature_parts("low"), b._feature_parts("none")) == (2, 2, 1, 1)
    _, _, b3 = gsv_env(feature_parts=3)
    assert b3._feature_parts("low") == 3


# ============================================================================ 实际参加训练的条数
def _caps(s2_lines, s1_lines):
    s2, s1 = {}, {}
    for ln in s2_lines:
        _capture_s2(ln, s2)
    for ln in s1_lines:
        _capture_s1(ln, s1)
    return s2, s1


def test_trained_counts_from_the_real_log_lines():
    s2, s1 = _caps(["INFO:vt:start training from epoch 1", "phoneme_data_len: 984", "wav_data_len: 984",
                    "Zero duration for D:/GSV/logs/vt/5-wav32k/abc_0001.wav, skipping...",
                    "skipped_phone:  0 , skipped_dur:  34", "total left:  950"],
                   ["ckpt_path: None", "semantic_data_len: 984", "phoneme_data_len: 984", "dataset.__len__(): 984"])
    tc = _trained_counts(s2, s1, 984)
    assert (tc["sovits"], tc["gpt"], tc["expected"]) == (950, 984, 984) and tc["ids"] == ["abc_0001"]
    assert tc["reasons"] == {"声音太短（不到 0.6 秒）或太长（54 秒以上）": 34}
    lines = _report_lines({"trained_counts": tc})
    assert lines[0] == "实际参加训练：音色 950 条、语气 984 条（一共 984 条）。"
    assert lines[1] == ("有 34 条没参加训练（原因：声音太短（不到 0.6 秒）或太长（54 秒以上） 34 条），一般是文字和声音对不上"
                        "或者太短；不影响使用，可以在校对表里看看这几条：abc_0001。")
    # 语气：删掉的写原因；都在：不提醒
    s2, s1 = _caps(["total left:  984", "wav_data_len: 984"],
                   ["semantic_data_len: 984", "deleted 30 audios who's phoneme/sec are bigger than 25 or smaller than 3"])
    tc = _trained_counts(s2, s1, 984)
    assert tc["gpt"] == 954 and "多半是文字和声音对不上" in _report_lines({"trained_counts": tc})[1]
    tc = _trained_counts(*_caps(["total left:  984", "wav_data_len: 984"], ["semantic_data_len: 984"]), 984)
    assert _report_lines({"trained_counts": tc}) == ["实际参加训练：音色 984 条、语气 984 条（一共 984 条）。"]
    # 素材少于 100 条时训练程序把整份重复几遍：按重复前的条数算
    tc = _trained_counts(*_caps(["phoneme_data_len: 24", "wav_data_len: 96", "total left:  96"], []), 24)
    assert tc["sovits"] == 24 and tc["gpt"] is None
    assert _report_lines({"trained_counts": tc})[0] == "实际参加训练：音色 24 条、语气 （没测出来） 条（一共 24 条）。"
    # 接着练的时候从第几轮开始
    s2, s1 = _caps(["start training from epoch 13"], ["ckpt_path: X/ckpt/epoch=14-step=30.ckpt", "semantic_data_len: 5"])
    assert s2["resumed_from"] == 12 and s1["resumed_from"] == 15


def test_trained_counts_from_the_fake_s2_run(gsv_env, monkeypatch):
    _, _, b = gsv_env()
    _, n = _features(b)
    monkeypatch.setenv("FAKE_GSV_S2_DROP", "3")
    params = {"batch_size": 4, "sovits_epochs": 2, "sovits_save_every": 1, "mode": "identical", "tier": "mid"}
    counts = {}
    assert b._train_sovits(b._opt_dir(), params, None, gsv.TRAIN_POS["identical"], counts) == 4
    tc = _trained_counts(counts, {}, n)
    assert tc["sovits"] == n - 3 and len(tc["ids"]) == 3
    lines = _report_lines({"trained_counts": tc})
    assert lines[1].startswith("有 3 条没参加训练（原因：") and "可以在校对表里看看这几条：" in lines[1]


def test_report_lines_only_show_measured_numbers():
    p = {"trained_counts": {"sovits": 984, "gpt": 984, "expected": 984}, "text_frontend": "mixed", "en_lines": 559,
         "en_phones": 8123, "batch_size": 6, "gpt_batch_size": 6,
         "gpu": {"sovits": {"util_avg": 62.4, "peak_gb": 10.51, "n": 9}, "gpt": {"util_avg": None, "peak_gb": None, "n": 0}},
         "timing": {"features_s": 600, "probe_s": 300, "sovits_s_per_epoch": 58.2, "gpt_s_per_epoch": 30.1}}
    lines = _report_lines(p)
    assert "英文：559 句里的英文这次也参加了训练（一共 8123 个英文音素）。" in lines
    assert ("显卡（实测）：音色训练每批 6 条，显存最高 10.5 GB，平均使用率 62%。这一步主要卡在处理器或读文件上，显卡没法再更忙。"
            in lines)
    assert "用时（实测）：处理文字和提取特征 10.0 分钟、实测显卡 5.0 分钟、音色每轮 58 秒、语气每轮 30 秒。" in lines
    p["text_frontend"] = "official"
    p["gpu"] = {}
    lines = _report_lines(p)
    assert not any(ln.startswith("英文") or ln.startswith("显卡") for ln in lines)


# ============================================================================ 从头练 / 接着练 / 不重新练
@needs_fake_python
def test_run_states_extend_skip_fresh(gsv_env, monkeypatch, vt_log):
    cfg, project, b = gsv_env(batch_size=4)   # 每批 4 条（你填的）：不实测
    confirm_material(cfg, project.voice)
    std = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="standard")
    assert std["params"]["mode"] == "standard" and std["params"]["run_state"] == "fresh"
    assert _epochs(std["sovits"]) == [2, 4, 6, 8] and _epochs(std["gpt"]) == [3, 6, 9, 12, 15]

    # 素材没变、换成「一模一样」：接着上次往下练，上次存下的也在
    deep = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="identical")
    p = deep["params"]
    assert p["run_state"] == "extend" and p["mode"] == "identical"
    assert _epochs(deep["sovits"]) == list(range(2, 25, 2))
    assert _epochs(deep["gpt"]) == [3, 6, 9, 12, 15, 16, 17, 18, 19, 20]
    assert "素材没变：接着上次的训练往下练（上次存下的版本也一起参加比较）。" in vt_log.messages
    s2_log = (project.logs_dir / "gsv_s2_train.log").read_text(encoding="utf-8")
    assert s2_log.rstrip().split("=====")[-1].count("start training from epoch 9") == 1
    ck = b.checkpoints(all=True)
    assert {c["sovits_epoch"] for c in ck} == set(range(4, 25, 2)) and {c["gpt_epoch"] for c in ck} == {6, 9, 12, 15, 16, 17, 18, 19, 20}
    assert len(b.checkpoints()) == 12   # 标准的挑法还是 4 × 3
    timing = p["timing"]
    assert timing["sovits_s_per_epoch"] is not None and timing["features_s"] >= 0
    entry = project.load_models()["gptsovits"]
    assert entry["params"]["train_minutes"] == deep["train_minutes"]
    # 接着练只做了一部分：「训练方式」后面的「上次实测」不记它（不然下次从头练看起来快很多），网页上还是写估计
    assert set(entry["timing_by_mode"]) == {"standard"}
    assert wf.measured_train_minutes(cfg, project.voice, "gptsovits").get("identical") is None
    assert "实际参加训练：音色" in p["report"][0]

    # 再练一次：素材没变、已经按「一模一样」练过 → 不重新训练（训练日志不变）
    size = (project.logs_dir / "gsv_s2_train.log").stat().st_size
    again = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="identical")
    assert again["params"]["run_state"] == "skip" and again["sovits"] == deep["sovits"]
    assert (project.logs_dir / "gsv_s2_train.log").stat().st_size == size
    assert "素材没变，已经按「一模一样」练过了：这次不重新训练，直接重新挑选。" in vt_log.messages
    # 没重新训练：上次实测的用时不改
    assert project.load_models()["gptsovits"]["params"]["train_minutes"] == deep["train_minutes"]
    # 这次什么都没练：显示的是上次训练实测的结果，标明是上次的，不写「这次」
    rep = again["params"]["report"]
    assert rep[0].startswith("这次没有重新训练；下面是上次训练（") and rep[0].endswith("）实测的结果：")
    assert rep[1:] == _report_lines(deep["params"], previous=True) and not any("这次" in ln for ln in rep[1:])
    from voicetwin.webui import app as A

    md = A._train_done_md(again, show_plan=False)
    assert "素材没变，这次不用重新训练" in md and "这次也参加了训练" not in md and "上次训练（" in md
    # 网页预览也知道
    assert b.training_plan(quick=True)["state"] == "skip"

    # 素材改了：从头练，原来用的模型记下来、一起比较
    from voicetwin.data import review

    recs = project.load_manifest()
    for r in [r for r in recs if r.get("keep", True) and r.get("split", "train") == "train"][:3]:
        r["keep"] = False
    project.save_manifest(recs)
    review.save_confirmed(project, recs)
    confirm_material(cfg, project.voice)
    assert b.training_plan(quick=True)["state"] == "fresh"
    assert "这次会从头训练（原因：素材改过）。你原来的模型会备份起来，一起参加比较" in b.training_plan(quick=True)["state_note"]
    fresh = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="identical")
    assert fresh["params"]["run_state"] == "fresh"
    # 从头完整练了一次：这次的用时记成「一模一样」的实测用时
    assert project.load_models()["gptsovits"]["timing_by_mode"]["identical"]["train_minutes"] == fresh["train_minutes"]
    prev = project.load_models()["gptsovits"]["previous_selected"]
    assert prev["pending"] is True and prev["id"] == "s24-g20" and Path(prev["sovits"]).exists()
    (old,) = list((b._opt_dir() / "old_runs").iterdir())
    assert prev["sovits"].startswith(str(old))
    cands = GPTSoVITSBackend(cfg, project).checkpoints(all=True)
    assert cands[-1]["id"] == "prev-s24-g20" and cands[-1]["previous"] is True
    assert set(fresh["sovits"]).isdisjoint({c["sovits"] for c in cands if c.get("previous")})


def test_previous_selected_run_is_kept_until_the_next_selection(gsv_env):
    _, project, b = gsv_env()
    opt = b._opt_dir()
    old_root = opt / "old_runs"
    runs = []
    for i in range(4):  # 4 次以前的备份（只留最近 2 次）
        d = old_root / f"2026010{i}_000000"
        (d / "SoVITS_weights_v2ProPlus").mkdir(parents=True)
        (d / "GPT_weights_v2ProPlus").mkdir(parents=True)
        (d / "SoVITS_weights_v2ProPlus" / f"{b.exp_name}_e8_s80.pth").write_bytes(b"06" + b"x" * 2000)
        (d / "GPT_weights_v2ProPlus" / f"{b.exp_name}-e15.ckpt").write_bytes(b"x" * 2000)
        os.utime(d, (1_700_000_000 + i * 1000, 1_700_000_000 + i * 1000))
        runs.append(d)
    oldest = runs[0]
    prev = {"id": "s8-g15", "sovits": str(oldest / "SoVITS_weights_v2ProPlus" / f"{b.exp_name}_e8_s80.pth"),
            "gpt": str(oldest / "GPT_weights_v2ProPlus" / f"{b.exp_name}-e15.ckpt"), "pending": True}
    cur_s, cur_g = b.p("SoVITS_weights_v2ProPlus"), b.p("GPT_weights_v2ProPlus")
    cur_s.mkdir(parents=True)
    cur_g.mkdir(parents=True)
    (cur_s / f"{b.exp_name}_e4_s40.pth").write_bytes(b"06" + b"x" * 2000)
    (cur_g / f"{b.exp_name}-e5.ckpt").write_bytes(b"x" * 2000)
    project.update_models("gptsovits", {"previous_selected": prev, "selected": {
        "id": "s4-g5", "sovits": str(cur_s / f"{b.exp_name}_e4_s40.pth"), "gpt": str(cur_g / f"{b.exp_name}-e5.ckpt")}})
    b._archive_old_run(opt)   # 挑选还没做完：原来的模型那次备份不删（别的旧备份照常只留最近的）
    left = sorted(p.name for p in old_root.iterdir())
    assert oldest.name in left and runs[1].name not in left
    assert project.load_models()["gptsovits"]["previous_selected"]["id"] == "s8-g15"   # 没挑完：留着实测挑出来的那个
    # 挑选做完以后（pending = False）：下次备份时就不再特别保留
    entry = project.load_models()["gptsovits"]
    project.update_models("gptsovits", {"previous_selected": dict(entry["previous_selected"], pending=False)})
    for name in ("SoVITS_weights_v2ProPlus", "GPT_weights_v2ProPlus"):
        b.p(name).mkdir(parents=True, exist_ok=True)
    (cur_s / f"{b.exp_name}_e8_s80.pth").write_bytes(b"06" + b"x" * 2000)
    b._archive_old_run(opt)
    assert oldest.name not in [p.name for p in old_root.iterdir()]


def test_selection_reports_where_the_old_model_ranked(tmp_path):
    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, "排名")
    project.root.mkdir(parents=True)
    project.update_models("gptsovits", {"previous_selected": {"id": "s8-g15", "pending": True}})
    res = {"selection": {"ranking": ["s24-g20", "prev-s8-g15", "s20-g18"]}}
    wf._previous_model_result(project, "gptsovits", res)
    assert res["previous_rank"] == 2 and res["previous_note"] == "你原来的模型也参加了比较：排第 2 名。"
    assert project.load_models()["gptsovits"]["previous_selected"]["pending"] is False
    project.update_models("gptsovits", {"previous_selected": {"id": "s8-g15", "pending": True}})
    res = {"selection": {"ranking": ["prev-s8-g15", "s24-g20"]}}
    wf._previous_model_result(project, "gptsovits", res)
    assert res["previous_note"] == "新模型实测没有比原来的好，继续用原来的模型。"


# ============================================================================ 硬盘检查
def test_disk_save_every_math():
    MB, GB = 1 << 20, 1 << 30
    room = 2 * GB + 300 * MB   # 留出 2 GB 以后还有 300 MB
    assert _disk_save_every(100 * MB, 20, 1, 1, room) == 10      # 每 10 轮存一个：还剩 2 个 = 200 MB
    assert _disk_save_every(100 * MB, 20, 1, 1, 100 * GB) is None
    assert _disk_save_every(100 * MB, 20, 1, 1, 2 * GB) == 20     # 一个都存不下：只存最后一轮
    assert _disk_save_every(100 * MB, 20, 1, 20, 2 * GB) is None   # 已经只存最后一轮了
    for total in (24, 30, 48):
        k = _disk_save_every(100 * MB, total, 0, 2, 2 * GB + 500 * MB)
        assert total % k == 0 and k >= 4


def test_disk_guard_doubles_the_save_interval_and_resumes(gsv_env, monkeypatch, vt_log):
    _, _, b = gsv_env()
    _features(b)
    monkeypatch.setenv("FAKE_GSV_EPOCH_SLEEP", "0.6")
    real = shutil.disk_usage
    monkeypatch.setattr(gsv.shutil, "disk_usage",
                        lambda p: real(p)._replace(free=2 * 1024 ** 3 + 200))   # 留出 2 GB 以后只剩 200 字节
    params = {"batch_size": 4, "sovits_epochs": 8, "sovits_save_every": 1, "mode": "identical", "tier": "mid"}
    counts = {}
    b._train_sovits(b._opt_dir(), params, None, gsv.TRAIN_POS["identical"], counts)
    # 重新开始时日志里是「start training from epoch 2」，但这一步是从第 0 轮开始练的：每轮用时要除以 8 轮，不是 7 轮
    assert counts["resumed_from"] >= 1 and counts["start_epoch"] == 0 and gsv._stage_start(counts, 0) == 0
    # 第 1 轮的模型 64 字节：剩下每轮存一个要 448 字节 → 每 4 轮存一个（还剩 2 个 128 字节）
    assert params["sovits_save_every"] == 4 and params["disk_guard"]["sovits"]["save_every"] == 4
    assert any(m.startswith("硬盘空间不够存这么多版本：每个模型实测") and m.endswith("已改成每 4 轮存一个。")
               for m in vt_log.messages)
    sov, _ = b._list_weights()
    got = _epochs(sov)
    assert got[0] == 1 and got[-2:] == [4, 8] and 6 not in got
    s2 = json.loads((b.work_dir / "tmp_s2.json").read_text(encoding="utf-8"))
    assert s2["train"]["save_every_epoch"] == 4


# ============================================================================ 素材检查
def test_material_audit_counts(tmp_path):
    from voicetwin.data.audit import material_audit

    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, "检查")
    project.root.mkdir(parents=True)
    recs = [
        {"id": "a1", "path": "clips/a1.wav", "text": "今天学Python的列表。", "lang": "zh", "split": "train", "source": "s1",
         "duration": 3.0},
        {"id": "a2", "path": "clips/a2.wav", "text": "翻译成英文就是I have a pen", "lang": "zh", "split": "train",
         "source": "s1", "duration": 3.0, "forced_cuts": 1},
        {"id": "a3", "path": "clips/a3.wav", "text": "这道题怎么做？", "lang": "zh", "split": "train", "source": "s2",
         "duration": 3.0, "suspect": {"spans": []}},
        {"id": "a4", "path": "clips/a4.wav", "text": "大家想一想", "lang": "zh", "split": "val", "source": "s2",
         "duration": 3.0},
        {"id": "a5", "path": "clips/a5.wav", "text": "为什么呢？", "lang": "zh", "split": "val", "source": "s3",
         "duration": 3.0},
        {"id": "a6", "path": "clips/a6.wav", "text": "删掉的？", "lang": "zh", "split": "train", "source": "s3",
         "duration": 3.0, "deleted": True, "keep": False},
        {"id": "a7", "path": "clips/a7.wav", "text": "Hello there.", "lang": "en", "split": "train", "source": "s3",
         "duration": 3.0},
    ]
    project.save_manifest(recs)
    project.write_json(project.sources_path, {"s1": {"denoised": True, "done": True}, "s2": {"separated": True},
                                              "s3": {"done": True}, "s4": {"denoised": True}})
    a = material_audit(project)
    assert (a["train"], a["val"]) == (4, 2)
    assert (a["sources_denoised"], a["sources_separated"], a["train_sources_denoised"], a["train_clips_denoised"]) == (2, 1, 1, 2)
    assert a["forced_cuts"] == 1 and a["no_final_punct"] == 1
    assert (a["en_lines"], a["en_words"]) == (2, 5)
    assert (a["questions_train"], a["questions_val"]) == (1, 1) and a["suspects"] == 1
    assert a["lines"] == ["有 1 个素材文件在准备时去过杂音（去杂音可能会被当成你的音色学进去）。",
                          "有 1 条训练素材是在没有停顿的地方硬切开的。"]
    # 没有这些情况：什么都不说
    project.save_manifest([recs[0]])
    project.write_json(project.sources_path, {"s1": {"done": True}})
    assert material_audit(project)["lines"] == []


def test_plan_preview_shows_state_and_audit(gsv_env):
    cfg, project, b = gsv_env()
    text = wf.training_plan(cfg, project.voice, "gptsovits")
    first, *rest = text.split("\n")
    assert first.startswith("训练计划：「一模一样」训练——显存 12 GB → 先实测一次能练几条")
    # 第 8 步起「一模一样」的挑选另外加 24 句检查用的句子（config.yaml 的 select_test_texts）
    assert "中文和英文都参加训练（素材里有" in first and "句录音和 24 句检查用的句子，把第 4 轮以后存下的每个版本都试一遍" in first
    std = wf.training_plan(cfg, project.voice, "gptsovits", mode="standard")
    assert std.split("\n")[0].startswith("训练计划：显存 12 GB → 每批")
    # 素材检查里实际有的情况（测试素材：没有去过杂音、硬切开的就不说）
    from voicetwin.data.audit import material_audit

    assert rest == list(material_audit(project)["lines"])


# ============================================================================ 网页和命令行的「训练方式」
def test_web_training_mode_radio(gsv_env, monkeypatch):
    from voicetwin.webui import app as A

    cfg, project, _ = gsv_env()
    ui = A.WebUI(cfg)
    assert [v for _, v in A.TRAIN_MODE_CHOICES] == ["identical", "standard"]
    assert A.TRAIN_MODE_LABELS["identical"].startswith("一模一样（默认）") and "（很慢）" in A.TRAIN_MODE_LABELS["identical"]
    assert A.TRAIN_MODE_LABELS["standard"] == "标准：和以前一样的训练量，训练完挑一次（快很多）"
    assert "估计要几个小时" in A.TRAIN_INTRO and "实际用的时间" in A.TRAIN_INTRO
    for t in (A.TRAIN_MODE_LABELS["identical"], A.TRAIN_INTRO, A.TRAIN_MODE_INFO, A.SELECT_HINT["identical"]):
        assert "第 4 轮以后存下的每个版本都试一遍" in t and "把每个版本" not in t
    # 「训练方式」也决定「重新挑选最佳模型」怎么比：页面上写清楚，进度条上说快慢（标准的分钟数标明是估计）
    assert "重新挑选最佳模型" in A.TRAIN_MODE_INFO and "估计" in A.SELECT_HINT["standard"]
    for t in list(A.TRAIN_MODE_LABELS.values()) + [A.TRAIN_INTRO]:
        assert "V4" not in t and "检查用的句子" not in t
    upd = ui.on_load_train_mode(project.voice)
    assert upd["value"] == "identical" and [v for _, v in upd["choices"]] == ["identical", "standard"]
    assert ui._train_opts(0, 0, 0, 0, "auto", "standard")["mode"] == "standard"
    assert ui._train_opts(0, 0, 0, 0)["mode"] == "identical"
    # 做完过一次：后面写上次实测用了多久
    project.update_models("gptsovits", {"timing_by_mode": {"standard": {"train_minutes": 31.5, "select_minutes": 6.2}}})
    labels = dict((v, lab) for lab, v in ui.train_mode_choices(project.voice))
    assert labels["standard"].endswith("（上次实测：训练 31.5 分钟、挑选 6.2 分钟）")
    assert labels["identical"] == A.TRAIN_MODE_LABELS["identical"]
    assert ui._train_hint(project.voice, "gptsovits", "standard").startswith("上次实测：训练 31.5 分钟")
    assert "估计" in ui._train_hint(project.voice, "gptsovits", "identical")
    md = ui.train_plan_preview(project.voice, "gptsovits", 0, 0, 0, "auto", "standard")
    assert "**电脑会自动这样训练**：显存 12 GB" in md


def test_web_page_has_training_mode(tmp_path):
    gr = pytest.importorskip("gradio")
    if not str(getattr(gr, "__version__", "")).startswith("4."):
        pytest.skip("这个测试只针对 gradio 4.x（整合包自带 4.24）")
    from voicetwin.webui import app as A

    ui = A.WebUI(make_cfg(tmp_path / "ws"))
    app = ui.build()
    assert ui.c["train_mode"].value == "identical" and ui.c["train_mode"].label == "训练方式"
    assert ui.c["train_mode"].info == A.TRAIN_MODE_INFO
    conf = json.dumps(app.get_config_file(), ensure_ascii=False)
    assert A.TRAIN_INTRO in conf and "V4" not in conf


def test_cli_mode_argument(monkeypatch, tmp_path, capsys):
    from voicetwin import cli

    ap = cli.build_parser()
    for cmd in (["train", "-v", "x"], ["select", "-v", "x"], ["auto", "-v", "x", "-i", "a"]):
        assert ap.parse_args(cmd).mode is None
        assert ap.parse_args(cmd + ["--mode", "standard"]).mode == "standard"
    with pytest.raises(SystemExit):
        ap.parse_args(["train", "-v", "x", "--mode", "fast"])
    seen = {}

    def fake_train(cfg, voice, backend, progress=None, select=True, mode=None, **opts):
        seen.update(mode=mode, select=select)
        return {"train_minutes": 1.0, "selected": {"id": "s1-g1"},
                "params": {"report": ["实际参加训练：音色 9 条、语气 9 条（一共 9 条）。"]},
                "selection": {"previous_note": "你原来的模型也参加了比较：排第 2 名。"}}

    monkeypatch.setattr(wf, "run_train", fake_train)
    monkeypatch.chdir(tmp_path)
    cli.main(["train", "-v", "x", "--mode", "standard"])
    out = capsys.readouterr().out
    assert seen == {"mode": "standard", "select": True}
    assert "实际参加训练：音色 9 条" in out and "排第 2 名" in out


def test_cli_says_when_nothing_was_trained(monkeypatch, tmp_path, capsys):
    """素材没变、这次没训练：命令行不能说「训练完成（用时 0.0 分钟）」，上次的结果标明是上次的。"""
    from voicetwin import cli

    def fake_train(cfg, voice, backend, progress=None, select=True, mode=None, **opts):
        return {"train_minutes": 0.0, "selected": {"id": "s24-g20"},
                "params": {"run_state": "skip", "report": ["这次没有重新训练；下面是上次训练（2026-10-01 12:00）实测的结果：",
                                                           "实际参加训练：音色 9 条、语气 9 条（一共 9 条）。"]}}

    monkeypatch.setattr(wf, "run_train", fake_train)
    monkeypatch.chdir(tmp_path)
    cli.main(["train", "-v", "x"])
    out = capsys.readouterr().out
    assert "素材没变，这次不用重新训练" in out and "训练完成（用时" not in out
    assert "下面是上次训练（2026-10-01 12:00）实测的结果" in out


# ============================================================================ 审查后补的回归测试
def test_identical_never_trains_less_than_standard():
    """每批不到 4 条（没有 N 卡、4 GB / 6 GB 的卡、显存被别的程序占着、全精度）：轮数按每批 4 条算，
    「一模一样」不会比「标准」练得少（以前每批 1 条时只练音色 6 轮、语气 5 轮）。"""
    cases = [(None, None, {}), (4.0, 3.5, {}), (6.0, 5.5, {}), (7.96, 3.0, {}), (7.96, 6.8, {"is_half": False}),
             (7.96, 6.8, {}), (11.99, 11.2, {})]
    for total, free, kw in cases:
        std = plan_training(984, 32.8, total, free, **kw)
        deep = plan_training(984, 32.8, total, free, mode="identical", **kw)
        assert deep["batch_size"] == std["batch_size"], (total, free, kw)
        # 每批条数一样：轮数多 = 模型更新的次数多
        assert deep["sovits_epochs"] >= std["sovits_epochs"] and deep["gpt_epochs"] >= std["gpt_epochs"], (total, free, kw)
        assert deep["sovits_epochs"] >= 24 and deep["gpt_epochs"] >= 20
    cpu = plan_training(984, 32.8, None, None, mode="identical")
    assert _nums(cpu) == (2, 24, 2, 20, 1) and "音色 SoVITS 24 轮" in cpu["summary"] and "语气 GPT 20 轮" in cpu["summary"]
    # 显存不够退到每批 3 条以后，接着练 / 不重新练时沿用的每批条数小于 4：轮数也不减
    prev3 = plan_training(984, 32.8, 7.96, 6.8, mode="identical", probe_batch=3, batch_source="previous")
    assert _nums(prev3) == (3, 24, 2, 20, 1)


def test_identical_plan_drops_notes_that_do_not_apply():
    """「一模一样」的说明里不能有只对「标准」才对的话（有底噪时最多 8 轮、为了存下最后一轮把 12 轮改成几轮），
    每批条数是实测的时也不能说「按空闲的显存算」「全精度减半」。"""
    noisy_std = plan_training(984, 32.8, 7.96, 6.8, noisy=True)
    assert noisy_std["sovits_epochs"] == 8 and any("最多 8 轮" in n for n in noisy_std["notes"])   # 标准照旧
    noisy = plan_training(984, 32.8, 7.96, 6.8, mode="identical", noisy=True)
    assert noisy["sovits_epochs"] == 24 and not any("最多 8 轮" in n for n in noisy["notes"])
    u = plan_training(984, 32.8, 7.96, 6.8, mode="identical", user={"sovits_save_every": 5})
    assert u["sovits_epochs"] == 25 and any("从 24 调整为 25" in n for n in u["notes"])
    assert not any("从 12 调整为" in n for n in u["notes"])
    busy = plan_training(984, 32.8, 11.99, 3.0, mode="identical", probe_batch=6)
    assert busy["batch_size"] == 6 and not any("按空闲的显存算" in n for n in busy["notes"])
    assert "（现在空闲 3.0 GB）" in busy["summary"]   # 量到的空闲显存照样写
    half = plan_training(984, 32.8, 11.99, 11.2, mode="identical", probe_batch=6, is_half=False)
    assert half["batch_size"] == 6 and not any("减半" in n for n in half["notes"])
    # 只实测出音色的：语气还是按显存的公式算，这句话留着；没实测时也留着；标准方式照旧
    one = plan_training(984, 32.8, 11.99, 3.0, mode="identical", probe_batch={"sovits": 6, "gpt": None})
    assert any("按空闲的显存算" in n for n in one["notes"])
    assert any("按空闲的显存算" in n for n in plan_training(984, 32.8, 11.99, 3.0, mode="identical")["notes"])
    assert any("按空闲的显存算" in n for n in plan_training(984, 32.8, 11.99, 3.0)["notes"])
    assert any("减半" in n for n in plan_training(984, 32.8, 11.99, 11.2, is_half=False)["notes"])


def test_gpu_sampler_counts_only_while_training(monkeypatch):
    """start() 时训练程序还没开始、stop() 时已经结束：这两个时候显卡闲着，不能算进平均使用率。"""
    holder = {}

    def fake(index=0):
        s = holder.get("s")
        busy = s is not None and not s._stop.is_set()
        return {"used_gb": 9.0 if busy else 1.0, "total_gb": 12.0, "util": 100.0 if busy else 0.0}

    monkeypatch.setattr(gpu_mod, "smi_sample", fake)
    s = gpu_mod.GpuSampler(0.1)
    s.start()
    holder["s"] = s       # 训练程序这时才开始
    time.sleep(0.55)
    r = s.stop()          # 训练程序已经结束
    assert r["util_avg"] == 100.0 and r["peak_gb"] == 9.0 and r["n"] >= 3


def test_capture_s1_keeps_the_first_start_epoch():
    counts = {"start_epoch": 0}
    _capture_s1("Restoring states from the checkpoint path at /x/ckpt/epoch=2-step=30.ckpt", counts)
    _capture_s1("semantic_data_len: 10", counts)
    assert counts["resumed_from"] == 3 and counts["start_epoch"] == 0 and gsv._stage_start(counts, 5) == 0
    assert gsv._stage_start({"start_epoch": None}, 15) == 15 and gsv._stage_start({}, 8) == 8


def test_measured_minutes_only_from_a_full_run(tmp_path):
    """models.json 里只有一次接着练 / 接着没练完的用时：不能当成「一模一样」的实测用时。"""
    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, "用时")
    project.root.mkdir(parents=True)
    project.save_manifest([{"id": "a1", "path": "clips/a1.wav", "text": "今天。", "split": "train", "duration": 3.0}])
    for state in ("extend", "continue", "skip"):
        project.update_models("gptsovits", {"params": {"mode": "identical", "run_state": state, "train_minutes": 3.0}})
        assert wf.measured_train_minutes(cfg, "用时", "gptsovits") == {}
    project.update_models("gptsovits", {"params": {"mode": "identical", "run_state": "fresh", "train_minutes": 95.0}})
    assert wf.measured_train_minutes(cfg, "用时", "gptsovits") == {"identical": {"train_minutes": 95.0}}


def test_audit_ignores_sources_that_were_not_really_denoised(tmp_path, monkeypatch):
    """没装 noisereduce 时降噪其实没做：sources.json 不记「去过杂音」；以前的版本记错的（降噪前后信噪比一样）也不算。"""
    import numpy as np

    from voicetwin.data import enhance
    from voicetwin.data.audit import material_audit
    from voicetwin.utils.audio import save_audio

    sr = 16000
    t = np.arange(sr * 2) / sr
    wav = (0.3 * np.sin(2 * np.pi * 220 * t) + 0.02 * np.random.default_rng(0).standard_normal(t.size)).astype(np.float32)
    src = tmp_path / "a.wav"
    save_audio(src, wav, sr)
    monkeypatch.setitem(sys.modules, "noisereduce", None)   # 没装 noisereduce
    _, info = enhance.enhance_file(src, tmp_path / "b.wav", {"denoise": "on", "sample_rate": sr}, tmp_path)
    assert "denoised" not in info and "snr_after" not in info and info["denoise_skipped"]

    cfg = make_cfg(tmp_path / "ws")
    project = Project(cfg, "降噪")
    project.root.mkdir(parents=True)
    project.save_manifest([{"id": "a1", "path": "clips/a1.wav", "text": "今天学列表。", "lang": "zh", "split": "train",
                            "source": "s1", "duration": 3.0}])
    for s1 in ({"done": True, "snr_before": 12.34, **info}, {"done": True, "denoised": True, "snr_before": 12.34,
                                                            "snr_after": 12.34}):
        project.write_json(project.sources_path, {"s1": s1})
        a = material_audit(project)
        assert a["lines"] == [] and a["train_sources_denoised"] == 0 and a["sources_denoised"] == 0
    project.write_json(project.sources_path, {"s1": {"done": True, "denoised": True, "snr_before": 12.34, "snr_after": 19.8}})
    assert material_audit(project)["lines"] == ["有 1 个素材文件在准备时去过杂音（去杂音可能会被当成你的音色学进去）。"]


def test_reselect_uses_the_mode_the_model_was_trained_with(gsv_env, monkeypatch):
    """「重新挑选最佳模型」/ voicetwin select 没指定挑法：按现在的模型是怎么练的（以前的版本、标准练的不会变成每个版本都试）。
    「一模一样」的挑法（第 8 步起）是 select_deep：分三步把第 4 轮以后存下的每个版本都试一遍；标准的是 4 × 3 个。"""
    from voicetwin.synth import select as sel

    cfg, project, _ = gsv_env()
    seen = []

    def fake_select(cfg, project, backend, max_items=20, use_asr=None, progress=None, all_checkpoints=False):
        seen.append(all_checkpoints)
        return {"selection": {"ranking": []}}

    def fake_deep(cfg, project, backend, progress=None, max_items=20, use_asr=None, judge=None, checker=None):
        seen.append(True)  # 「一模一样」：每个版本都试
        return {"selection": {"ranking": []}}

    monkeypatch.setattr(sel, "select_and_calibrate", fake_select)
    monkeypatch.setattr(sel, "select_deep", fake_deep)
    msgs = []

    def prog(frac, msg=""):
        msgs.append(msg)

    for params, every in (({}, False), ({"mode": "standard"}, False), ({"mode": "identical"}, True)):
        project.update_models("gptsovits", {"params": params})
        wf.run_select(cfg, project.voice, "gptsovits", progress=prog)
        assert seen[-1] is every, params
    # 指定了就按指定的（网页上按「训练方式」传进来）
    wf.run_select(cfg, project.voice, "gptsovits", mode="identical", progress=prog)
    assert seen[-1] is True
    wf.run_select(cfg, project.voice, "gptsovits", mode="standard", progress=prog)
    assert seen[-1] is False
    assert any("第 4 轮以后存下的每个版本都试一遍，比较慢" in m for m in msgs)
    assert any(m.startswith("挑选方式：标准") and "估计" in m for m in msgs)


def test_every_version_wording_matches_what_is_compared():
    """说「每个存下的版本都试一遍」的地方都写明「第 4 轮以后」（checkpoints(all=True) 不试第 1~3 轮的）。"""
    from voicetwin import cli

    texts = [plan_training(984, 32.8, 7.96, 6.8, mode="identical", n_val=20)["summary"],
             plan_training(984, 32.8, 7.96, 6.8, mode="identical")["summary"],
             cli.build_parser().format_help()]
    help_texts = []
    for action in cli.build_parser()._subparsers._group_actions[0].choices.values():
        help_texts += [a.help or "" for a in action._actions]
    for t in texts + help_texts:
        if "每个" in t and "版本" in t:
            assert "第 4 轮以后存下的每个版本" in t, t


@needs_fake_python
def test_explicit_settings_that_need_retraining_start_fresh(gsv_env, vt_log):
    """素材没变、已经按「一模一样」练过：你明确打开 DPO（或者改了保存间隔）只有重新训练才用得上 → 从头练
    （特征接着用，原来的模型备份、一起参加比较）；不重新练时的训练计划写上次实际怎么练的。"""
    cfg, project, b = gsv_env(batch_size=4)
    confirm_material(cfg, project.voice)
    first = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="identical")
    assert first["params"]["if_dpo"] is False
    st = b.training_plan(quick=True)
    assert st["state"] == "skip" and st["summary"].startswith("训练计划：这次不重新训练，沿用上次训练好的模型（上次：「一模一样」训练——")
    std = b.training_plan(quick=True, mode="standard")   # 标准练得更少：也不重新练，说明里不能写成这次要练 12 轮
    assert std["state"] == "skip" and "音色 SoVITS 24 轮" in std["summary"] and "12 轮" not in std["summary"]

    pre = b.training_plan(quick=True, if_dpo=True)
    assert pre["state"] == "fresh" and "这次会从头训练（原因：你改了训练设置（开启 DPO））" in pre["state_note"]
    text = b._opt_dir() / "2-name2text.txt"
    before = text.stat().st_mtime_ns
    s1_log = project.logs_dir / "gsv_s1_train.log"
    size = s1_log.stat().st_size
    dpo = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="identical", if_dpo=True)
    p = dpo["params"]
    assert p["run_state"] == "fresh" and p["if_dpo"] is True and "开启 DPO（你指定的；" in p["summary"]
    assert project.load_models()["gptsovits"]["params"]["if_dpo"] is True
    assert s1_log.stat().st_size > size and _epochs(dpo["gpt"]) == list(range(1, 21))
    assert text.stat().st_mtime_ns == before   # 素材没变：文字特征接着用
    prev = project.load_models()["gptsovits"]["previous_selected"]
    assert prev["pending"] is True and prev["id"] == first["selected"]["id"]
    (old,) = list((b._opt_dir() / "old_runs").iterdir())
    assert prev["sovits"].startswith(str(old))
    assert any(m.startswith("训练设置改了：这次会从头训练新模型") for m in vt_log.messages)

    # 同样的设置再练一次：不重新练
    assert b.training_plan(quick=True, if_dpo=True)["state"] == "skip"
    # 不重新练时，你指定的保存间隔和上次的不一样：从头练；自动的不算
    st = b.training_plan(quick=True, if_dpo=True, gpt_save_every=2)
    assert st["state"] == "fresh" and "你改了训练设置（语气每 2 轮存一个）" in st["state_note"]
    assert b.training_plan(quick=True, if_dpo=True, gpt_save_every="auto")["state"] == "skip"


@needs_fake_python
def test_unfinished_run_continues_without_archiving(gsv_env, vt_log):
    """上次已经提取好特征、训练没做完（models.json 里没有这份素材练好的模型）：接着往下练，不备份、不从头来。"""
    cfg, project, b = gsv_env(batch_size=4)
    confirm_material(cfg, project.voice)
    _features(b)
    assert b.training_plan(quick=True)["state"] == "continue"
    info = wf.run_train(cfg, project.voice, "gptsovits", select=False, mode="identical")
    assert info["params"]["run_state"] == "continue"
    assert "素材没变：接着上次没做完的训练往下练。" in vt_log.messages
    old_root = b._opt_dir() / "old_runs"
    assert not old_root.exists() or not any(old_root.iterdir())
    assert "previous_selected" not in project.load_models()["gptsovits"]
    # 只做了一部分：「上次实测」的用时不记
    assert "identical" not in (project.load_models()["gptsovits"].get("timing_by_mode") or {})
