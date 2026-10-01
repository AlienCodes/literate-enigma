"""网页顶部的模型型号：从模型文件本身读出 GPT-SoVITS 的版本（和 GPT-SoVITS 自己的判断方法一样），不照抄设置。"""

import hashlib
import sys
from pathlib import Path

from voicetwin import workflows as wf
from voicetwin.backends import gptsovits as g
from voicetwin.webui import app as A

from conftest import make_cfg
from fake_gptsovits import build_fake_root


def _w(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_detect_version_from_file_head_hash_and_size(tmp_path, monkeypatch):
    assert g.detect_sovits_version(_w(tmp_path / "a.pth", b"06" + b"\0" * 100))["version"] == "v2ProPlus"
    assert g.detect_sovits_version(_w(tmp_path / "b.pth", b"05" + b"\0" * 100))["version"] == "v2Pro"
    v4 = g.detect_sovits_version(_w(tmp_path / "c.pth", b"04" + b"\0" * 100))
    assert v4["version"] == "v4" and v4["lora"] is True
    old = g.detect_sovits_version(_w(tmp_path / "d.pth", b"PK" + b"\0" * 100))  # 旧格式：按大小，小文件是 v1
    assert old["version"] == "v1" and "大小" in old["how"]
    unknown = g.detect_sovits_version(_w(tmp_path / "e.pth", b"07" + b"\0" * 100))  # 不认识的标记：不猜
    assert unknown["version"] is None and "不认识" in unknown["how"]
    assert g.detect_sovits_version(tmp_path / "没有这个文件.pth")["how"] == "找不到模型文件"
    # 官方底模按开头 8192 字节的 MD5 认（底模文件开头不是版本标记）
    base = _w(tmp_path / "s2Gv2ProPlus.pth", b"PK" + b"\1" * 9000)
    monkeypatch.setitem(g.SOVITS_HASH_VERSION, hashlib.md5(base.read_bytes()[:8192]).hexdigest(), "v2ProPlus")
    got = g.detect_sovits_version(base)
    assert got["version"] == "v2ProPlus" and "底模" in got["how"]


def test_builtin_tables_match_gptsovits_and_new_versions_come_from_the_package(tmp_path):
    # 内置对照表和 GPT-SoVITS 官方 process_ckpt.py（2026-08-18 主分支）一致
    assert g.SOVITS_HEAD_VERSION[b"06"] == ("v2ProPlus", False) and g.SOVITS_HEAD_VERSION[b"04"] == ("v4", True)
    # 以后官方出了 v5：整合包里的 process_ckpt.py 有新标记，就能认出来（不用等声音分身更新）
    _w(tmp_path / "GSV" / "GPT_SoVITS" / "process_ckpt.py", (
        'head2version = {\n    b"00": ["v1", "v1", False],\n    b"07": ["v2", "v5", False],\n}\n'
        'hash_pretrained_dict = {\n    "0123456789abcdef0123456789abcdef": ["v2", "v5", False],  # s2Gv5.pth\n}\n'
    ).encode("utf-8"))
    f = _w(tmp_path / "x.pth", b"07" + b"\0" * 10)
    assert g.detect_sovits_version(f, tmp_path / "GSV")["version"] == "v5"
    assert g.detect_sovits_version(f)["version"] is None  # 没有整合包的对照表：如实说不认识
    _w(tmp_path / "GSV2" / "GPT_SoVITS" / "process_ckpt.py", b"head2version = {broken\n")  # 读不懂：用内置的
    assert g.detect_sovits_version(_w(tmp_path / "y.pth", b"06xx"), tmp_path / "GSV2")["version"] == "v2ProPlus"


def _gsv_cfg(tmp_path):
    root = build_fake_root(tmp_path / "GSV")
    return make_cfg(tmp_path / "ws", backend="gptsovits",
                    backends={"gptsovits": {"root": str(root), "python": sys.executable}}), root


def test_badge_reads_the_trained_model_of_the_selected_voice(tmp_path):
    cfg, root = _gsv_cfg(tmp_path)
    proj = wf.Project(cfg, "我的声音").ensure()
    proj.manifest_path.write_text("", encoding="utf-8")
    weight = _w(root / "SoVITS_weights_v2ProPlus" / "vt_e8_s80.pth", b"06" + b"x" * 62)
    proj.update_models("gptsovits", {"selected": {"id": "s8-g15", "sovits": str(weight), "gpt": str(weight)}})
    b = wf.model_badge(cfg, "我的声音")
    assert b["text"] == "GPT-SoVITS v2ProPlus" and b["source"] == "trained" and b["note"] == "" and b["level"] == "ok"
    assert "vt_e8_s80.pth" in b["detail"]
    # 换成 v4 训练的模型（假设以后支持）：如实显示 v4，并说明和设置里的不一样
    weight.write_bytes(b"04" + b"x" * 62)
    b = wf.model_badge(cfg, "我的声音")
    assert b["text"] == "GPT-SoVITS v4" and b["level"] == "warn" and "v2ProPlus" in b["detail"]


def test_badge_for_untrained_voice_reads_the_base_model_and_creates_no_folder(tmp_path, monkeypatch):
    cfg, root = _gsv_cfg(tmp_path)
    base = root / "GPT_SoVITS" / "pretrained_models" / "v2Pro" / "s2Gv2ProPlus.pth"
    monkeypatch.setitem(g.SOVITS_HASH_VERSION, hashlib.md5(base.read_bytes()[:8192]).hexdigest(), "v2ProPlus")
    b = wf.model_badge(cfg, "还没有的声音")
    assert b["text"] == "GPT-SoVITS v2ProPlus" and b["source"] == "pretrained" and "还没训练" in b["note"]
    ws = Path(cfg["workspace"])
    assert not (ws / "还没有的声音").exists() and not [p for p in ws.glob("__model_badge*")]
    # 训练过、但训练好的模型文件被删掉 / 移走了：生成时会退回底模，顶部如实说明
    proj = wf.Project(cfg, "模型丢了").ensure()
    proj.manifest_path.write_text("", encoding="utf-8")
    proj.update_models("gptsovits", {"selected": {"id": "s8-g15", "sovits": str(tmp_path / "没了.pth"), "gpt": ""}})
    b = wf.model_badge(cfg, "模型丢了")
    assert b["source"] == "pretrained" and "找不到训练好的模型文件" in b["note"] and b["level"] == "warn"
    # 底模文件认不出来（假文件）：如实说读不出来，不照抄设置里的 v2ProPlus
    monkeypatch.setattr(g, "SOVITS_HASH_VERSION", {})
    b = wf.model_badge(cfg, "还没有的声音")
    assert b["version"] is None and "读不出来" in b["text"] and b["level"] == "warn"


def test_badge_for_engines_without_training(tmp_path):
    b = wf.model_badge(make_cfg(tmp_path / "ws"), "")
    assert b["text"] == "测试引擎(dummy)" and b["version"] is None


def test_header_shows_badge_next_to_title():
    html = A.header_md({"text": "GPT-SoVITS v2ProPlus", "note": "", "detail": "从模型文件读出来的", "level": "ok"})
    title, sub = html.split("\n", 1)
    assert title.startswith(A.INTRO_TITLE) and "模型：GPT-SoVITS v2ProPlus" in title and 'title="从模型文件读出来的"' in title
    assert "vt-model-ok" in title and sub == A.INTRO_SUB
    assert "&lt;b&gt;" in A.header_md({"text": "<b>", "level": "warn"}) and "vt-model-warn" in A.header_md({"text": "x", "level": "warn"})
    assert A.MODEL_PENDING in A.INTRO


def test_fake_trainer_writes_version_head():
    # 浏览器实测用的假 GPT-SoVITS 也和真的一样写版本标记，顶部才能显示 v2ProPlus
    src = (Path(__file__).parent / "fake_gptsovits.py").read_text(encoding="utf-8")
    assert '"v2ProPlus": b"06"' in src
