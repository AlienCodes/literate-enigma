"""用仿真 GPT-SoVITS 目录验证：训练编排（1A/1B/1C/SoVITS/GPT）、权重发现、自动挑选、推理服务启动/切换/关闭。"""

import sys

from voicetwin import workflows as wf
from voicetwin.backends.base import get_backend

from conftest import make_cfg
from fake_gptsovits import build_fake_root


def test_train_select_and_narrate(prepared, tmp_path, monkeypatch):
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    # 测试环境里不要往当前 Python 的 site-packages 写 users.pth
    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    gcfg = make_cfg(project.root.parent, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": 19880, "startup_timeout": 60, "is_half": True,
        "train": {"sovits_epochs": 8, "gpt_epochs": 10, "batch_size": 2, "sovits_save_every": 4, "gpt_save_every": 5},
    }})
    info = wf.run_train(gcfg, project.voice, "gptsovits", select=True)

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

    res = wf.run_narrate(gcfg, project.voice, "大家好，这是用 GPT-SoVITS 引擎生成的一句话。Hello!",
                         out=str(tmp_path / "gsv.wav"), backend_name="gptsovits", quality="fast")
    assert res.audio_path.exists() and res.duration > 1.0

    # 训练素材变化时会清理旧特征重新提取
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


def test_selected_model_survives_moving_gptsovits(prepared, tmp_path):
    """models.json 记录的是旧位置的绝对路径（例如 Windows 上的 D:\\GPT-SoVITS\\...），
    整合包移动 / 换电脑后应按文件名在新 root 里找到训练好的模型，而不是退回底模。"""
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV-moved")
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {"root": str(root), "python": sys.executable}})
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
