"""GPT-SoVITS V5（v5dev / v5turbo）：默认用 v5dev，同时练 v2ProPlus 做对比，练完用老师没参加训练的录音实测挑更像的。

V5 的音色模型是 LoRA 微调（官方 s2_train_v3_lora.py）：不用 s2D，模型文件名多一个 _l{rank}，开头 2 字节 07 / 08。"""

import sys

import pytest

from voicetwin import workflows as wf
from voicetwin.backends import gptsovits as g
from voicetwin.backends.base import get_backend
from voicetwin.config import load_config

from conftest import confirm_material, make_cfg
from fake_gptsovits import build_fake_root
from test_gptsovits_fake import Rec, needs_fake_python, no_users_pth  # noqa: F401  (pytest 夹具)


def _v5cfg(project, root, port, version="v5dev", **train):
    return make_cfg(project.root.parent, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": port, "startup_timeout": 60, "is_half": True,
        "version": version, "train": train,
    }})


def test_shipped_default_is_v5dev_with_v2proplus_compare():
    cfg = load_config(user_config=False)
    assert cfg["backends"]["gptsovits"]["version"] == "v5dev" == g.DEFAULT_VERSION == g.LATEST_VERSION
    assert cfg["backends"]["gptsovits"]["train"]["compare_versions"] == "auto"
    assert g.is_lora_version("v5dev") and g.is_lora_version("v5turbo") and not g.is_lora_version("v2ProPlus")
    assert g.PRETRAINED_SOVITS["v5dev"].endswith("gsv-v5-pretrained/s2Gv5dev.pth")
    assert g.VOCODER["v5dev"] == g.VOCODER["v5turbo"] == "GPT_SoVITS/pretrained_models/gsv-v5-pretrained/vocoder.pth"
    assert g.PRETRAINED_GPT["v5dev"].endswith("s1v3.ckpt")


def test_detect_v5_files(tmp_path):
    for head, ver in ((b"07", "v5dev"), (b"08", "v5turbo")):
        p = tmp_path / f"{ver}.pth"
        p.write_bytes(head + b"\0" * 100)
        got = g.detect_sovits_version(p)
        assert got["version"] == ver and got["lora"] is True
    # 官方 process_ckpt.py 的底模 MD5（开头 8192 字节）
    assert g.SOVITS_HASH_VERSION["c4ce1f839a0d271e41963f9fb16ade76"] == "v5dev"
    assert g.SOVITS_HASH_VERSION["6bc5cb2a195cc8ec22b2e723cd4d6f47"] == "v5turbo"


def test_plan_lora_batch_epochs_and_user_settings():
    p = g.plan_lora("v5dev", 11.99, 11.2, mode="identical", n_clips=200)
    assert (p["batch_size"], p["epochs"], p["save_every"], p["rank"]) == (1, g.LORA_EPOCHS_DEEP, 1, 32)
    assert g.plan_lora("v5dev", 23.99, 23.0, mode="standard", n_clips=200)["batch_size"] == 3
    assert g.plan_lora("v5dev", 23.99, 23.0, mode="standard", n_clips=200)["epochs"] == g.LORA_EPOCHS_STANDARD
    assert g.plan_lora("v5dev", 23.99, 23.0, is_half=False, n_clips=200)["batch_size"] == 1
    assert g.plan_lora("v5dev", 47.99, 47.0, n_clips=8)["batch_size"] == 2       # 不超过素材条数的 1/4
    u = g.plan_lora("v5dev", 11.99, 11.2, user={"lora_batch_size": 2, "lora_epochs": 7, "lora_save_every": 2,
                                                 "lora_rank": 64})
    assert (u["batch_size"], u["epochs"], u["save_every"], u["rank"]) == (2, 8, 2, 64)  # 最后一轮一定存下来
    assert g.plan_lora("v5dev", 11.99, 11.2, user={"lora_epochs": 99})["epochs"] == g.LORA_MAX_EPOCHS
    assert g.plan_lora("v5dev", 11.99, 11.2, user={"lora_rank": 48})["rank"] == 32
    assert "LoRA" in p["summary"] and "最像" in p["summary"]


def test_compare_versions_setting(prepared, tmp_path):
    _, project, _ = prepared
    root = build_fake_root(tmp_path / "GSV-cmp")
    vers = lambda **t: get_backend("gptsovits", _v5cfg(project, root, 19893, **t), project).train_versions()
    assert vers() == ["v5dev", "v2ProPlus"]
    assert vers(compare_versions="none") == ["v5dev"]
    assert vers(compare_versions="v5turbo，v2ProPlus 不存在的") == ["v5dev", "v5turbo", "v2ProPlus"]
    b = get_backend("gptsovits", _v5cfg(project, root, 19893, version="v2ProPlus"), project)
    assert b.train_versions() == ["v2ProPlus"]   # 主版本不是 V4 / V5：auto 不加对比


@needs_fake_python
def test_train_v5dev_and_v2proplus_then_pick_by_measurement(prepared, tmp_path, monkeypatch, no_users_pth):
    monkeypatch.setenv("FAKE_GSV_CLIP_SLEEP", "0.03")
    monkeypatch.setenv("EXPECT_VERSION", "v5dev")    # 1A 处理文字时和官方 webui 一样传 v5dev
    _, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS-v5")
    gcfg = _v5cfg(project, root, 19891, sovits_epochs=8, gpt_epochs=10, batch_size=2, lora_epochs=4)
    confirm_material(gcfg, project.voice)
    rec = Rec()
    info = wf.run_train(gcfg, project.voice, "gptsovits", select=True, progress=rec, sovits_save_every=4,
                        gpt_save_every=5, mode="standard")
    assert info["versions"] == ["v5dev", "v2ProPlus"]

    backend = get_backend("gptsovits", gcfg, project)
    exp = backend.exp_name
    opt_dir = root / "logs" / exp
    # v5dev 用 LoRA 脚本：配置里没有 s2D，断点在 logs_s2_v5dev_lora_32
    assert (opt_dir / "logs_s2_v5dev_lora_32").is_dir()
    assert (opt_dir / "7-sv_cn").is_dir()             # 对比的 v2ProPlus 要声纹
    models = project.load_models()["gptsovits"]
    v5 = [p for p in models["sovits"] if "SoVITS_weights_v5dev" in p.replace("\\", "/")]
    pp = [p for p in models["sovits"] if "SoVITS_weights_v2ProPlus" in p.replace("\\", "/")]
    assert v5 and pp and all(p.endswith("_l32.pth") for p in v5)
    assert [int(p.rsplit("_e", 1)[1].split("_")[0]) for p in v5] == [1, 2, 3, 4]   # lora_epochs=4，每轮存一个
    for p in v5:
        assert g.detect_sovits_version(p)["version"] == "v5dev"
    # 两个版本都进了实测；挑出来的是实测里的一个
    ids = {c["id"] for c in backend.checkpoints()}
    assert any(i.startswith("v5dev-") for i in ids) and any(i.startswith("v2ProPlus-") for i in ids)
    assert models["selected"]["id"] in ids
    tested = {r.get("version") or r["id"].split("-")[0] for r in models["selection"]["results"]}
    assert {"v5dev", "v2ProPlus"} <= tested
    assert models["params"]["lora"]["rank"] == 32 and models["params"]["versions"] == ["v5dev", "v2ProPlus"]
    # 详细日志：v5dev 的音色训练用官方 LoRA 脚本
    lora_log = (project.logs_dir / "gsv_s2_train_v5dev.log").read_text(encoding="utf-8")
    assert "s2_train_v3_lora.py" in lora_log and "INFO:" in lora_log
    msgs = [m for _, m in rec.train_part()]
    assert any("v5dev" in m and "LoRA" in m for m in msgs) and msgs[-1] == "GPT-SoVITS 训练完成"

    res = wf.run_narrate(gcfg, project.voice, "大家好，这是用 V5 生成的一句话。Hello!",
                         out=str(tmp_path / "v5.wav"), backend_name="gptsovits", quality="fast")
    assert res.audio_path.exists() and res.duration > 1.0
