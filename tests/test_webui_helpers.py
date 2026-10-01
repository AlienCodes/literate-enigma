"""网页界面的辅助函数和处理函数（不需要 gradio 4.24，在两个测试环境里都能跑）和环境检查里的显卡判断。"""

import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from voicetwin import workflows as wf
from voicetwin.webui import app as A
from voicetwin.webui.app import CLIP_HEADERS, NEED_VOICE, _clips_count_md, _clips_table, _voice_name
from voicetwin.workflows import nvidia_smi_status


def _copy_voice(prepared, tmp_path, name=None):
    """复制一份已经准备好的声音到新的工作目录（会改数据的测试不能动共享的 prepared）。"""
    from conftest import make_cfg

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    name = name or project.voice
    shutil.copytree(project.root, ws / name)
    # 别的测试文件可能已经用共享的 prepared 训练过（写了 models.json）；这里的副本一律从「还没训练」开始
    models = ws / name / "models.json"
    if models.exists():
        models.unlink()
    return make_cfg(ws), name


def _is_update(v):
    return isinstance(v, dict) and v.get("__type__") == "update"


# ---------------------------------------------------------------------------- 校对表
def test_clip_table_has_row_numbers_and_count(prepared):
    cfg, project, _ = prepared
    rows = _clips_table(cfg, project.voice)
    records = project.load_manifest()
    assert len(rows) == len(records) > 0
    assert all(len(r) == len(CLIP_HEADERS) for r in rows)
    assert [r[0] for r in rows] == list(range(1, len(records) + 1))
    assert rows[0][1] == records[0]["id"]
    assert {r[2] for r in rows} <= {"是", "否"}

    md = _clips_count_md(cfg, project.voice)
    kept = sum(1 for r in records if r.get("keep", True))
    assert f"一共 **{len(records)}** 条片段" in md
    assert f"保留 **{kept}** 条" in md
    assert f"不保留 **{len(records) - kept}** 条" in md
    assert "可能有错" not in md  # 还没查过错字


def test_clip_count_for_voice_without_clips(tmp_path):
    from conftest import make_cfg

    cfg = make_cfg(tmp_path)
    assert "还没有片段" in _clips_count_md(cfg, "新声音")
    assert _clips_count_md(cfg, "") == NEED_VOICE
    assert _clips_count_md(cfg, []) == NEED_VOICE
    assert "不能包含" in _clips_count_md(cfg, "a/b")


def test_voice_dropdown_value_is_normalized(prepared):
    # gradio 4.24（整合包自带）更新选项或刷新页面后，下拉框的值可能变成列表或 None
    assert _voice_name(None) == "" and _voice_name([]) == "" and _voice_name([""]) == ""
    assert _voice_name(["我的声音"]) == "我的声音" and _voice_name(" 我的声音 ") == "我的声音"
    cfg, project, _ = prepared
    assert _clips_table(cfg, [project.voice]) == _clips_table(cfg, project.voice)


def test_suspect_column_count_and_filter(prepared, tmp_path):
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    recs = project.load_manifest()
    recs[1]["text"] = "我们今天讲 VFIXED 的用法"
    recs[1]["suspect"] = {"spans": [[6, 12]], "alt": "我们今天讲 V fixed 的用法", "reasons": ["像是听错的英文"], "score": 0.7}
    project.save_manifest(recs)
    rows = _clips_table(cfg, name)
    col = CLIP_HEADERS.index("可能有错（红色）")
    assert rows[1][col].count("color:#dc2626") == 1 and "VFIXED" in rows[1][col]
    assert rows[0][col] == ""
    only = _clips_table(cfg, name, only_suspect=True)
    assert len(only) == 1 and only[0][0] == 1 and only[0][1] == recs[1]["id"]  # 序号重新从 1 开始，id 不变
    assert "其中 **1** 条可能有错（已标红）" in _clips_count_md(cfg, name)


def test_render_marked_fallback_escapes_markup():
    out = A._render_marked("1. *设置* <b>x</b> $$", [[3, 7], [5, 9]])
    assert "<b>" not in out and "*" not in out and "$$" not in out
    assert out.count(A._RED_SPAN) == 1  # 重叠的范围合并成一个


@pytest.mark.parametrize("value,expected", [
    ("是", True), ("否", False), ("✔", True), ("✘", False), ("×", False), ("X", False), ("no", False),
    ("NO", False), ("0", False), (0, False), ("1", True), (1.0, True), ("", True), (None, True), ("保留", True),
    ("删除", False), ("ｘ", False), ("也许", None), ("2", None),
])
def test_parse_keep(value, expected):
    assert A._parse_keep(value) is expected


def test_on_clip_pick_uses_id_not_row_number(prepared):
    cfg, project, _ = prepared
    ui = A.WebUI(cfg)
    rows = _clips_table(cfg, project.voice)
    shuffled = list(reversed(rows))  # 浏览器里点表头排序后，行的顺序变了
    audio, panel, adopt, cid = ui.on_clip_pick(project.voice, shuffled, 0, 5)
    rec = {r["id"]: r for r in project.load_manifest()}[shuffled[0][1]]
    assert cid == rec["id"]
    assert audio["value"] == str(project.abspath(rec["path"]))
    assert audio["label"].startswith(f"试听：第 {shuffled[0][0]} 条")
    assert panel == "" and adopt["visible"] is False
    # 点在 id 那一列：直接用格子里的值
    audio2, _, _, cid2 = ui.on_clip_pick(project.voice, shuffled, 3, 1, shuffled[2][1])
    assert cid2 == shuffled[2][1]


def test_do_save_round_trip_and_guards(prepared, tmp_path, monkeypatch):
    cfg, name = _copy_voice(prepared, tmp_path)
    ui = A.WebUI(cfg)
    project = wf.Project(cfg, name)
    rows = _clips_table(cfg, name)
    first = rows[0][1]
    rows[0][2] = "×"  # 输入法打出来的叉也算「不要」
    rows[1][5] = rows[1][5] + "改"
    rows[2][2] = "也许"
    rows[1][CLIP_HEADERS.index("可能有错（红色）")] = "<span>乱改的格式代码</span>"  # 这一列只用来看，不读
    md, count_md, table = ui.do_save(name, rows)
    assert md.startswith("✅ 已保存：改了 1 处文字、1 处「保留」") and "看不懂，已保持原样" in md
    assert "{" not in md
    recs = {r["id"]: r for r in project.load_manifest()}
    assert recs[first]["keep"] is False and recs[rows[1][1]]["text"].endswith("改")
    assert table[0][1] == first
    assert not Path(str(project.csv_path) + ".tmp").exists()

    # 别的声音的表格：不写
    other = [[1, "不存在的id", "是", "中文", 1.0, "文字", "", ""]]
    md2, _, _ = ui.do_save(name, other)
    assert "不属于" in md2 and "重新载入" in md2

    # Excel 正打开 transcripts.csv
    def locked(*a, **k):
        raise PermissionError("locked")

    monkeypatch.setattr(A, "_write_csv_atomic", locked)
    md3, c3, t3 = ui.do_save(name, rows)
    assert "Excel/WPS" in md3 and "不会丢" in md3 and _is_update(c3) and _is_update(t3)
    assert ui.do_save("", rows)[0] == NEED_VOICE


def test_do_save_clears_suspect_when_text_changes(prepared, tmp_path):
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[0, 1]], "alt": "x", "reasons": ["r"], "score": 0.6}
    recs[1]["suspect"] = {"spans": [[0, 1]], "alt": "y", "reasons": ["r"], "score": 0.6}
    project.save_manifest(recs)
    rows = _clips_table(cfg, name)
    rows[0][5] = "这是改过的新文字。"
    A.WebUI(cfg).do_save(name, rows)
    after = {r["id"]: r for r in project.load_manifest()}
    assert "suspect" not in after[recs[0]["id"]]
    assert "suspect" in after[recs[1]["id"]]  # 没改的保持标记


def test_save_refused_while_prepare_runs(prepared, monkeypatch):
    cfg, project, _ = prepared
    monkeypatch.setattr(A, "current_task", lambda: {"running": True, "voice": project.voice, "kind": "prepare",
                                                    "label": "准备素材"})
    md, a, b = A.WebUI(cfg).do_save(project.voice, [])
    assert "请等它完成后再点「保存修改」" in md and _is_update(a) and _is_update(b)


# ---------------------------------------------------------------------------- 状态卡 / 声音库
def test_voice_status_card(prepared, tmp_path):
    from conftest import make_cfg

    cfg, name0 = _copy_voice(prepared, tmp_path / "fresh")
    assert "起个名字" in A._voice_status_md(cfg, "")
    assert "是新声音" in A._voice_status_md(make_cfg(tmp_path), "没有这个声音")
    assert A._voice_status_md(cfg, "a/b").startswith("⚠️")
    md = A._voice_status_md(cfg, name0)
    assert "还没训练" in md and "分钟" in md
    assert A._voice_status_md(cfg, [name0]) == md

    cfg2, name = _copy_voice(prepared, tmp_path)
    p2 = wf.Project(cfg2, name)
    p2.update_models("gptsovits", {"selected": {"id": "s8-g15"}, "trained_at": "2026-09-28 10:00",
                                   "selection": {"best": "s8-g15", "results": [{"id": "s8-g15", "speaker_sim": 0.8}]}})
    md2 = A._voice_status_md(cfg2, name)
    assert "训练 ✅" in md2 and "2026-09-28 10:00" in md2 and "比较像" in md2
    assert A._gen_warn_md(cfg2, name, "gptsovits") == ""
    assert "还没有训练" in A._gen_warn_md(cfg, name0, "gptsovits")
    assert A._gen_warn_md(cfg, name0, "dummy") == ""
    assert "准备素材" in A._gen_warn_md(make_cfg(tmp_path / "x"), "新的", "gptsovits")


def test_voice_library_entries(prepared, tmp_path):
    cfg, name = _copy_voice(prepared, tmp_path)
    p = wf.Project(cfg, name)
    p.update_models("gptsovits", {"selected": {"id": "s8-g15"}, "selection": {"best": "s8-g15", "results": []}})
    entries = A._library_entries(cfg)
    assert len(entries) == 1
    e = entries[0]
    # 测试配置的默认引擎是 dummy，所以会注明「GPT-SoVITS」；老师的电脑上默认就是 GPT-SoVITS，只显示编号
    assert e["name"] == name and e["status"] == "✅ 已训练，可以生成" and e["best_model"] == "s8-g15（GPT-SoVITS）"
    assert e["main_reference"] and Path(e["main_reference"]).exists()
    rows = A._library_rows(entries)
    assert rows[0][0] == 1 and rows[0][1] == name and "分钟" in rows[0][2] and "条" in rows[0][2]
    assert time.strftime("%Y-") in rows[0][5]
    assert A._library_label(1) == "🎙️ 我的声音库（共 1 个）"
    assert "共 1 个声音" in A._library_total_md(1)

    ui = A.WebUI(cfg)
    voice_upd, audio_upd = ui.on_library_pick(rows, 0)
    assert voice_upd["value"] == name and audio_upd["value"] == e["main_reference"]
    acc, table, total = ui.library(open_it=True)
    assert acc["label"].endswith("（共 1 个）") and acc["open"] is True and table == rows


def test_voice_library_uses_workflow_when_available(prepared, monkeypatch):
    cfg, project, _ = prepared
    monkeypatch.setattr(wf, "voice_library", lambda c: [
        {"voice": "甲", "minutes": 12.5, "clips_kept": 100, "trained": False, "status": "⚠️ 素材已准备，还没训练",
         "best_model": "", "main_reference": "", "modified": 0},
        {"name": "乙", "minutes": None, "clips": None, "trained": True},
    ], raising=False)
    entries = A._library_entries(cfg)
    rows = A._library_rows(entries)
    assert [r[0] for r in rows] == [1, 2]
    assert rows[0][3] == "⚠️ 素材已准备，还没训练" and rows[1][3] == "✅ 已训练，可以生成"
    assert rows[0][2] == "12.5 分钟 / 100 条" and rows[1][2] == "— / —" and rows[1][4] == "—"


# ---------------------------------------------------------------------------- 摘要
def test_summary_md_has_no_python_dicts(prepared):
    _, _, summary = prepared
    md = A._summary_md(summary)
    assert "分钟" in md and "{" not in md and "'zh'" not in md
    assert "考试题" in md or not summary.get("val_clips")
    assert "1. [" in md  # 参考录音有编号
    skipped = dict(summary, skipped_files=[{"file": "D:/课/坏.mp4", "reason": "没有声音"}],
                   dropped={"太短": 3, "识别置信度低": 2})
    md2 = A._summary_md(skipped)
    assert "有 1 个文件没能处理" in md2 and "1. 坏.mp4（没有声音）" in md2
    assert "自动去掉了 5 条" in md2 and "1. 太短：3 条" in md2 and "2. 识别置信度低：2 条" in md2


def test_train_and_select_done_md():
    info = {"train_minutes": 42.5, "selected": {"id": "s12-g20"},
            "selection": {"speed": {"zh": 1.04}, "selection": {"best": "s12-g20", "results": [
                {"id": "s12-g20", "speaker_sim": 0.88}]}}}
    md = A._train_done_md(info, "显存 12 GB → batch 8；素材 85 分钟 → SoVITS 16 轮")
    assert "用时 42.5 分钟" in md and "非常像" in md and "s12-g20" in md and "自动选择的训练方案" in md
    err = A._train_done_md({"train_minutes": 3, "selection_error": "合成失败"})
    assert "没成功" in err and "重新挑选最佳模型" in err
    sel = A._select_done_md({"speed": {"zh": 1.0}, "selection": {"best": "s4-g10", "results": []}})
    assert "s4-g10" in sel and "和你本人一致，不用调" in sel
    assert "已校准" in A._select_done_md({"speed": {"zh": 1.08}, "selection": {"best": "x"}})
    log_text = "21:00:01 | 开始训练\n21:00:02 | 显存 12 GB → batch 8；素材 85 分钟 → SoVITS 16 轮、GPT 25 轮；每 2 轮保存一次\n"
    assert A._plan_line(log_text).startswith("显存 12 GB")
    assert A._plan_line("21:00 | 训练音色：第 3/12 轮（45%）") == ""


def _fake_res(**extra):
    segs = [
        {"index": 1, "text": "大家好。", "speaker_sim": None, "issues": [], "cached": True},
        {"index": 2, "text": "今天讲 a|b。", "speaker_sim": 0.81, "issues": ["可能漏字"]},
        {"index": 3, "text": "再见。", "speaker_sim": 0.9, "issues": [], "pct": 96.2},
        {"index": 4, "text": "谢谢。", "speaker_sim": 0.7, "issues": [], "pct": 80.0},
    ]
    base = dict(audio_path=Path("/tmp/out.wav"), srt_path=Path("/tmp/out.srt"), report_path=Path("/tmp/out.report.json"),
                duration=75.4, segments=segs, warnings=["第 2 句：可能漏字", "第 3 句比字幕时间轴晚了 1.2 秒（上一句太长）"])
    base.update(extra)
    return SimpleNamespace(**base)


def test_gen_summary_and_rows():
    res = _fake_res()
    md = A._gen_summary_md(res, redo=[3, 5])
    assert "生成好了" in md and "1 分 15 秒" in md and "共 4 句" in md
    assert "第 2、4 句可能有问题" in md and "2,4" in md
    assert "已重新生成第 3、5 句" in md
    assert "晚了 1.2 秒" in md and "None" not in md and "{" not in md
    assert str(Path("/tmp/out.wav")) in md and ".srt" in md  # Windows 上路径显示成 \\tmp\\out.wav
    rows = A._gen_rows(res)
    assert [r[0] for r in rows] == [1, 2, 3, 4]
    assert rows[0][2] == "—" and "沿用上次" in rows[0][4]
    assert rows[2][2] == "96.2%" and rows[2][3].startswith("✅")
    assert rows[3][3].startswith("🔴") and "低于 85%" in rows[3][4]
    assert "可能漏字" in rows[1][4]
    assert all("None" not in str(c) for r in rows for c in r)
    # U3 给了 flagged（从 1 开始）时优先用它
    assert A._flagged_numbers(_fake_res(flagged=[4])) == [4]


def test_variants_md_and_recommendation():
    vs = [{"name": "未去杂音", "path": "/a.wav", "score": 0.912, "recommended": True},
          {"name": "去杂音", "path": "/b.wav", "score": 0.905, "recommended": False}]
    md = A._variants_md(vs)
    assert "版本 A：未去杂音（相似度 0.912）" in md and "版本 B：去杂音（相似度 0.905）" in md
    assert "⭐ 推荐：版本 A，更像你的原声（相似度高 0.007）" in md
    assert A._recommended_variant(vs) == "未去杂音"
    vs2 = [dict(vs[0], pct=91.2, recommended=False), dict(vs[1], pct=93.0, recommended=True)]
    md2 = A._variants_md(vs2)
    assert "像你本人 93.0%" in md2 and "⭐ 推荐：版本 B" in md2 and "高 1.8 个百分点" in md2
    assert A._variants_md(vs[:1]) == ""


def test_variants_md_recommended_with_lower_percentage_is_honest():
    """推荐是按综合得分挑的，推荐的版本百分比可能反而低：不能写成「高 X 个百分点」。"""
    vs = [{"name": "未去杂音", "path": "/a.wav", "score": 0.95, "pct": 98.2, "recommended": True},
          {"name": "去杂音", "path": "/b.wav", "score": 0.93, "pct": 99.1, "recommended": False}]
    md = A._variants_md(vs)
    line = next(x for x in md.splitlines() if x.startswith("⭐ 推荐"))
    assert "版本 A" in line and "高 0.9 个百分点" not in line
    assert "百分比低 0.9" in line and "综合得分高 0.020" in line


@pytest.mark.parametrize("value,factor,text", [
    (0, 1.0, "当前：和你原声一样"), (-20, 1.2, "当前：比你原声快 20%"), (15, 0.85, "当前：比你原声慢 15%"),
    (None, 1.0, "当前：和你原声一样"), (-99, 1.3, "当前：比你原声快 30%"), (30, 0.7, "当前：比你原声慢 30%"),
])
def test_speed_slider_mapping(value, factor, text):
    assert A._speed_factor(value) == pytest.approx(factor)
    assert A._speed_text(value) == text


def test_quality_choices_and_recommendation():
    values = [v for _, v in A.QUALITY_CHOICES]
    assert values == ["fast", "balanced", "best", "max", "perfect"]
    labels = dict((v, k) for k, v in A.QUALITY_CHOICES)
    assert labels["max"] == "极致（很慢，更稳更像，建议显存 ≥ 8GB）"  # 不写「最慢」：「完美」比它更慢
    assert labels["perfect"].startswith("完美：每句最多试 20 次")
    mid = {"ok": True, "level": "ok", "total_gb": 11.94, "nominal_gb": 12.0}
    high = {"ok": True, "level": "ok", "total_gb": 23.6}
    low = {"ok": True, "level": "warn", "total_gb": 5.8}
    bad = {"ok": False, "level": "error", "total_gb": None}
    assert A._recommended_quality(mid)[0] == "perfect" and "显存 12 GB" in A._recommended_quality(mid)[1]
    assert A._recommended_quality(high)[0] == "perfect"
    assert A._recommended_quality(low)[0] == "max"
    q, note = A._recommended_quality(bad)
    assert q == "balanced" and "很慢" in note


# ---------------------------------------------------------------------------- 后台任务的工作函数
def test_prepare_job_links_uploads_once(tmp_path, monkeypatch):
    from conftest import make_cfg

    cfg = make_cfg(tmp_path / "ws")
    src = tmp_path / "up"
    src.mkdir()
    (src / "a.wav").write_bytes(b"x" * 100)
    (src / "a.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\n你好\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(wf, "run_prepare", lambda c, v, inputs, progress=None, overrides=None: calls.append(inputs) or {"ok": 1})
    seen = []
    out = A._prepare_job(cfg, "声音", [str(src / "a.wav"), str(src / "a.srt")], "D:/folder", {"x": 1},
                         progress=lambda f, m: seen.append((round(f, 3), m)))
    updir = wf.Project(cfg, "声音").root / "uploads"
    assert out == {"ok": 1} and calls[0] == [str(updir), "D:/folder"]
    assert (updir / "a.wav").read_bytes() == b"x" * 100 and (updir / "a.srt").exists()
    assert [f for f, _ in seen] == [0.01, 0.02] and "1/2" in seen[0][1]

    copied = []
    monkeypatch.setattr(A.os, "link", lambda *a: copied.append(a))
    monkeypatch.setattr(A.shutil, "copyfile", lambda *a: copied.append(a))
    A._prepare_job(cfg, "声音", [str(src / "a.wav")], "", {})
    assert copied == []  # 同名同大小：不再复制
    assert calls[1] == [str(updir)]


def test_download_job_cleans_up(tmp_path, monkeypatch):
    from conftest import make_cfg
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    cfg = make_cfg(tmp_path / "ws")
    seen = []

    def fake(self, source="auto", progress=None):
        progress(0.5, "x 1/2 MB")
        return ["a"]

    monkeypatch.setattr(GPTSoVITSBackend, "download_pretrained", fake)
    from voicetwin.eval import sv_models

    def fake_sv(cfg, progress=None, keys=None):
        progress(0.5, "下载声纹模型 y.onnx：1/2 MB")
        return ["y.onnx"]

    monkeypatch.setattr(sv_models, "download", fake_sv)
    assert A._download_job(cfg, progress=lambda f, m: seen.append((round(f, 3), m))) == ["a", "y.onnx"]
    assert seen == [(0.425, "x 1/2 MB"), (0.925, "下载声纹模型 y.onnx：1/2 MB")]  # 声纹模型排在最后 15%
    assert not wf.Project(cfg, "__download__").root.exists()

    def broken_sv(cfg, progress=None, keys=None):
        raise RuntimeError("网络断了")

    monkeypatch.setattr(sv_models, "download", broken_sv)
    assert A._download_job(cfg, progress=lambda f, m: None) == ["a"]  # 声纹模型下载失败不影响 GPT-SoVITS 的模型


# ---------------------------------------------------------------------------- 环境检查 / 评估 / 鉴别
def test_doctor_view_numbering_and_sorting():
    rows = [{"item": "Python", "status": "✅", "detail": "3.9"},
            {"item": "引擎 GPT-SoVITS", "status": "❌", "detail": "缺少预训练模型：x；可运行 voicetwin download-models"},
            {"item": "demucs", "status": "⚠️", "detail": "未安装", "optional": True}]
    summary, main, total, opt, opt_total = A._doctor_view(rows)
    assert summary.startswith("### ❌ 有 1 项需要处理") and "下载缺少的模型" in summary
    assert [r[0] for r in main] == [1, 2] and main[0][1] == "❌" and total == "共 2 项"
    assert opt == [[1, "⚠️", "demucs", "未安装"]] and opt_total == "共 1 项"
    ok_summary = A._doctor_view(rows[:1])[0]
    assert ok_summary.startswith("### ✅ 一切正常")


def test_quick_check_on_page_load(tmp_path):
    """打开网页时的快速检查：只看文件；缺模型时提示去「🩺 环境检查」下载；不留下临时文件夹。"""
    from conftest import make_cfg

    root = tmp_path / "GPT-SoVITS"
    root.mkdir()
    (root / "api_v2.py").write_text("", encoding="utf-8")
    cfg = make_cfg(tmp_path / "ws", backend="gptsovits", backends={"gptsovits": {"root": str(root)}})
    problems = [p for p in A._quick_problems(cfg) if "ffmpeg" not in p]
    assert len(problems) == 1 and "下载缺少的模型" in problems[0] and "缺少 6 个" in problems[0]
    assert "还差一步" in A._quick_html(problems) and "vt-note-error" in A._quick_html(problems)
    assert not (tmp_path / "ws" / "__quick__").exists() and not (tmp_path / "ws" / "__quick_check__").exists()
    cfg2 = make_cfg(tmp_path / "ws2", backend="gptsovits", backends={"gptsovits": {"root": str(tmp_path / "没有")}})
    assert any("找不到 GPT-SoVITS" in p for p in A._quick_problems(cfg2))
    assert A._quick_problems(make_cfg(tmp_path / "ws3")) == []  # 测试引擎：不检查
    assert A._quick_html([]) == ""


def test_eval_md_card():
    res = {"结论": "比较像", "声纹相似度": 0.82, "相似度参考": "≥0.86 非常像", "时长（秒）": 3.2,
           "语速（音节/秒）": 4.1, "提示": ["无"], "各模型": {"resemblyzer": 91.2, "eres2netv2": 93.4}}
    md = A._eval_md(res)
    assert md.startswith("## 🙂 比较像（0.82）") and "时长（秒）：3.2" in md and "resemblyzer：91.2" in md
    assert "{" not in md and "[" not in md.replace("\\[", "")
    md2 = A._eval_md(dict(res, pct=92.5))
    assert md2.startswith("## 🙂 像你本人 92.5%")


def test_verify_rows_are_ranked():
    result = {"rows": [{"file": "/x/a.wav", "models": {"m1": 80.0}, "pct": 80.0},
                       {"file": "/x/b.wav", "models": {"m1": 97.5, "m2": 95.1}, "pct": 96.3},
                       {"file": "/x/c.wav", "models": {}, "pct": None}], "note": "说明"}
    table, md = A._verify_rows(result)
    assert [r[1] for r in table] == ["b.wav", "a.wav", "c.wav"]
    assert [r[0] for r in table] == [1, 2, 3] and table[0][4] == 1
    assert table[0][5] == "✅ 是" and table[1][5] == "🔴 否" and table[2][5] == "—"
    assert "m1 97.5%；m2 95.1%" == table[0][2]
    assert "共 3 个文件，其中 1 个 ≥ 85%" in md


def test_verify_explains_the_100_percent_standard():
    """「100%」的标准要和实际用的一致：只选 1~2 段原声时不能说「你选的几段彼此之间有多像」。"""
    rows = [{"file": "a.wav", "pct": 97.0, "pcts": {"m": 97.0}}]
    _, md3 = A._verify_rows({"rows": rows, "originals": ["1", "2", "3"], "calibration_source": "uploaded_loo"})
    assert "你选的 3 段原始录音彼此之间有多像" in md3
    _, md1 = A._verify_rows({"rows": rows, "originals": ["1"], "calibration_source": "voice_clips_vs_uploaded"})
    assert "彼此之间" not in md1 and "和你选的这 1 段原始录音有多像" in md1
    _, md2 = A._verify_rows({"rows": rows, "originals": ["1", "2"], "calibration_source": "voice_calibration"})
    assert "彼此之间" not in md2 and "改用这个声音素材里你自己的真实录音" in md2
    _, md0 = A._verify_rows({"rows": rows})
    assert "「100%」的标准" not in md0


@pytest.mark.parametrize("data", [
    {"01": "真人", "02": "生成", "03": "real"},
    [{"index": 1, "kind": "real"}, {"index": 2, "kind": "generated"}, {"index": 3, "is_real": True}],
    {"answers": [{"file": "01.wav", "answer": "真人"}, {"file": "02.wav", "answer": "生成"},
                 {"file": "03.wav", "answer": "真人"}]},
])
def test_blind_answers_formats(data):
    assert A._blind_answers(data) == {1: True, 2: False, 3: True}


def test_blind_result_accuracy():
    answers = {1: True, 2: False, 3: True, 4: False}
    md = A._blind_result_md(["real", "real", "real", None], answers)
    assert "答了 3 段，答对 2 段" in md and "67%" in md and "有时能分辨" in md and "（没选）" in md
    assert "| 4 | （没选） | — | — |" in md  # 没答的那段不显示答案
    assert "还没有选" in A._blind_result_md([None, None], answers)
    assert "分辨不出" in A._blind_verdict(0.5) and "容易分辨" in A._blind_verdict(0.9)


def test_blind_items_and_answer_file(tmp_path):
    d = tmp_path / "盲听测试_1"
    d.mkdir()
    for i in (2, 1, 3):
        (d / f"{i:02d}.wav").write_bytes(b"")
    (d / "答案.json").write_text(json.dumps({"01": "真人"}), encoding="utf-8")  # 老版本：答案在文件夹里面
    res = {"dir": str(d)}
    assert [Path(p).name for p in A._blind_items(res)] == ["01.wav", "02.wav", "03.wav"]
    assert A._blind_answer_file(res).endswith("答案.json")
    st = {"answers": A._blind_answer_file(res), "n": 1}
    out = dict(zip(A.WebUI.BLIND_SUBMIT_OUT, A.WebUI.on_blind_submit(st, "real", None, None)))
    assert "答对 1 段" in out["bt_result"]
    # 新版本：答案在文件夹旁边（文件夹可以整个发给听众）
    side = tmp_path / ("盲听测试_1" + wf.BLIND_ANSWER_SUFFIX)
    side.write_text(json.dumps({"01": "生成"}), encoding="utf-8")
    assert A._blind_answer_file(res) == str(side)


def test_blind_submit_needs_every_answer_and_then_locks(tmp_path):
    """答一段就点提交：不能显示任何答案（否则看完答案改选项再交就是 100%）；全部答完才显示，并锁住选项。"""
    ans = tmp_path / "a.json"
    ans.write_text(json.dumps({"items": [{"no": 1, "truth": "真人"}, {"no": 2, "truth": "生成"},
                                         {"no": 3, "truth": "生成"}]}, ensure_ascii=False), encoding="utf-8")
    st = {"answers": str(ans), "n": 3}
    picks = ["real", None, None] + [None] * (A.MAX_BLIND - 3)
    out = dict(zip(A.WebUI.BLIND_SUBMIT_OUT, A.WebUI.on_blind_submit(st, *picks)))
    assert "还有第 2、3 段没选" in out["bt_result"] and "生成" not in out["bt_result"].split("没选")[0]
    assert "正确答案" not in out["bt_result"] and _is_update(out["bt_submit"]) and "visible" not in out["bt_submit"]
    picks = ["real", "real", "fake"] + [None] * (A.MAX_BLIND - 3)
    out = dict(zip(A.WebUI.BLIND_SUBMIT_OUT, A.WebUI.on_blind_submit(st, *picks)))
    assert "答对 2 段" in out["bt_result"] and out["bt_submit"]["visible"] is False
    assert all(out[f"bt_pick_{i}"]["interactive"] is False for i in range(3))


def test_blind_offline_grading_and_reopen(prepared, tmp_path, monkeypatch):
    """新开的网页（没有 bt_state）也能批改收上来的答题卡，也能重新打开以前的测试在网页上答。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    shutil.rmtree(project.outputs_dir, ignore_errors=True)  # 共享的 prepared 里可能已经有别的测试做的盲听测试
    d = project.outputs_dir / "盲听测试_20261001_090000"
    d.mkdir(parents=True)
    clips = [project.abspath(r["path"]) for r in project.load_manifest()][:4]
    truths = ["真人", "生成", "生成", "真人"]
    for i, src in enumerate(clips, 1):
        shutil.copyfile(src, d / f"{i:02d}.wav")
    data = {"created": "2026-10-01 09:00", "count": 4,
            "items": [{"no": i, "file": f"{i:02d}.wav", "truth": t} for i, t in enumerate(truths, 1)]}
    (project.outputs_dir / (d.name + wf.BLIND_ANSWER_SUFFIX)).write_text(json.dumps(data, ensure_ascii=False),
                                                                          encoding="utf-8")
    ui = A.WebUI(cfg)
    dd = ui.blind_tests(name)
    assert dd["value"] == str(d) and "4 段" in dd["choices"][0][0]
    md = ui.on_blind_grade(name, str(d), "01. 真人（真人 / 生成）\n02. 生成（真人 / 生成）\n03. 真人\n04. 真人")
    assert "答了 4 段" in md and "答对 3 段" in md and "75" in md
    md2 = ui.on_blind_grade(name, str(d), "1 真人 2 生成")
    assert "答了 2 段" in md2 and "| 3 | （没答） | — | — |" in md2  # 没答的不显示答案
    assert "没看懂" in ui.on_blind_grade(name, str(d), "随便写的")
    assert "请先在「选一次盲听测试」" in ui.on_blind_grade(name, "", "1 真人")
    opened = dict(zip(ui.BLIND_OPEN_OUT, ui.on_blind_open(name, str(d))))
    assert opened["bt_state"]["n"] == 4 and opened["bt_state"]["answers"].endswith(wf.BLIND_ANSWER_SUFFIX)
    assert opened["bt_audio_0"]["visible"] is True and opened["bt_pick_0"]["interactive"] is True
    assert opened["bt_audio_4"]["visible"] is False and opened["bt_submit"]["visible"] is True


# ---------------------------------------------------------------------------- 处理函数（不需要 gradio）
def test_handlers_early_returns_have_right_arity(prepared, tmp_path):
    cfg, project, _ = prepared
    ui = A.WebUI(cfg)
    out = list(ui.do_prepare("", None, "", "none", "auto", "auto", False))
    assert len(out) == 1 and len(out[0]) == len(ui.PREP_OUT)
    out = list(ui.do_prepare("新声音", None, str(tmp_path / "不存在的文件夹"), "none", "auto", "auto", False))
    assert "找不到这个文件夹" in out[0][0] and out[0][ui.PREP_OUT.index("prep_btn")]["interactive"] is True
    out = list(ui.do_prepare("a/b", None, "", "none", "auto", "auto", False))
    assert "不能包含" in out[0][0]
    out = list(ui.do_generate(project.voice, "大家好。", None, "dummy", "fast", 0, "", "3,x"))
    assert len(out) == 1 and len(out[0]) == len(ui.GEN_OUT) and "请这样填" in out[0][0]
    out = list(ui.do_generate(project.voice, "", None, "dummy", "fast", 0, "", ""))
    assert "请先在「讲稿」框里粘贴讲稿" in out[0][0]
    # gradio 4.24 的坑留下的 []（交回来是字符串 "[]"）当成空的，不能提示「看不懂「[]」」
    for stale in ("[]", [], None):
        out = list(ui.do_generate(project.voice, "", None, "dummy", "fast", 0, "", stale))
        assert "请先在「讲稿」框里粘贴讲稿" in out[0][0], out[0][0]
    out = list(ui.do_generate("没准备的声音", "大家好", None, "dummy", "fast", 0, "", ""))
    assert "还没有准备素材" in out[0][0]
    out = list(ui.do_train("没准备的声音", "gptsovits", None, "", 0, None))
    assert len(out[0]) == len(ui.TRAIN_OUT) and "还没有准备素材" in out[0][0]
    assert len(list(ui.do_select("", "gptsovits"))[0]) == len(ui.TRAIN_OUT)
    assert len(list(ui.do_speed_preview("", "", 0, "dummy"))[0]) == len(ui.SPEED_OUT)
    assert len(list(ui.do_proofcheck("", False))[0]) == len(ui.PROOF_OUT)
    assert len(list(ui.do_verify("", None, None, {}))[0]) == len(ui.VERIFY_OUT)
    assert len(list(ui.do_blind("", 10, "fast"))[0]) == len(ui.BLIND_OUT)
    assert len(ui.on_voice_change(project.voice)) == len(ui.VOICE_OUT)
    with pytest.raises(KeyError):
        ui._o(ui.PREP_OUT, typo=1)


def test_on_load_outputs(prepared, tmp_path):
    cfg, name = _copy_voice(prepared, tmp_path)
    ui = A.WebUI(cfg)
    out = ui.on_load()
    assert len(out) == len(ui.VOICE_OUT) + 3 + len(ui.LIB_OUT)
    voice_upd = out[len(ui.VOICE_OUT)]
    assert voice_upd["value"] == name and name in voice_upd["choices"]
    assert "还没训练" in out[0]


def test_stop_needs_two_clicks(monkeypatch):
    calls = []
    monkeypatch.setattr(A, "request_stop", lambda: calls.append(1) or True)
    btn, armed = A.WebUI.on_stop(0.0)
    assert btn["value"] == A.STOP_CONFIRM and armed > 0 and calls == []
    btn2, armed2 = A.WebUI.on_stop(armed)
    assert btn2["value"] == A.STOP_PENDING and calls == [1] and armed2 == 0.0
    btn3, armed3 = A.WebUI.on_stop(time.time() - 60)  # 太久以前点的第一次：重新确认，并且明说超时了
    assert btn3["value"] == A.STOP_EXPIRED != A.STOP_CONFIRM and calls == [1] and armed3 > 0


def test_stop_confirm_label_expires(monkeypatch):
    """点了第一次没确认：5 秒后按钮自己变回「⏹ 停止」；已经确认停止的不会被改回去。"""
    calls = []
    monkeypatch.setattr(A, "request_stop", lambda: calls.append(1) or True)
    btn, armed = A.WebUI.on_stop(0.0)
    assert btn["value"] == A.STOP_CONFIRM
    back, armed_back = A.WebUI.on_stop_expire(armed, wait=False)
    assert back["value"] == A.STOP_LABEL and armed_back == 0.0
    # 下一次点击又是正常的第一次
    btn2, armed2 = A.WebUI.on_stop(armed_back)
    assert btn2["value"] == A.STOP_CONFIRM and calls == []
    # 5 秒内确认了：过期处理什么都不改（按钮保持「正在停止……」）
    btn3, _ = A.WebUI.on_stop(armed2)
    assert btn3["value"] == A.STOP_PENDING and calls == [1]
    late, late_armed = A.WebUI.on_stop_expire(armed2, wait=False)
    assert late == {"__type__": "update"} and late_armed == {"__type__": "update"}
    # 没点过（armed=0）：什么都不改
    assert A.WebUI.on_stop_expire(0.0, wait=False) == ({"__type__": "update"}, {"__type__": "update"})


def test_script_upload(tmp_path):
    from conftest import make_cfg

    ui = A.WebUI(make_cfg(tmp_path))
    txt = tmp_path / "第3课 讲稿.txt"
    txt.write_text("大家好，今天讲牛顿第二定律。", encoding="utf-8")
    text, f, hint, name = ui.on_script_upload(str(txt), "")
    assert text.startswith("大家好") and f is None and "放进上面的讲稿框" in hint and name["value"] == "第3课 讲稿"
    srt = tmp_path / "配音.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\n你好\n", encoding="utf-8")
    t2, f2, hint2, n2 = ui.on_script_upload(str(srt), "我起的名字")
    assert _is_update(t2) and _is_update(f2) and "字幕" in hint2 and _is_update(n2) and "value" not in n2
    doc = tmp_path / "旧.doc"
    doc.write_bytes(b"\xd0\xcf")
    _, f3, hint3, _ = ui.on_script_upload(str(doc), "")
    assert f3 is None and "另存为" in hint3
    # 讲稿来源：字幕文件优先，其次是文字框
    assert ui._source("文字", str(srt))[0] == str(srt)
    assert ui._source("第一句。第二句。", None) == ("第一句。第二句。", "第一句。")


def test_text_in_treats_stale_lists_as_empty():
    assert A._text_in(None) == "" and A._text_in([]) == "" and A._text_in("[]") == "" and A._text_in(" {} ") == ""
    assert A._text_in("3,5") == "3,5" and A._text_in(["3,5"]) == "3,5" and A._text_in(3) == "3"


def test_settled_pauses_after_the_last_yield(monkeypatch):
    """流式处理函数最后一次产出之后要停一下再结束（gradio 4.24：不然最后一条进度更新会被网页当成新的值）。"""
    import inspect

    monkeypatch.setattr(A, "SETTLE_SECONDS", 0.2)

    def handler(voice, text="", n=2):
        for i in range(n):
            yield (voice, text, i)

    wrapped = A._settled(handler)
    assert inspect.isgeneratorfunction(wrapped)  # gradio 靠它判断是不是流式
    assert inspect.signature(wrapped) == inspect.signature(handler)  # gradio 按参数个数传输入
    it = wrapped("我的声音", text="x")
    assert [next(it), next(it)] == [("我的声音", "x", 0), ("我的声音", "x", 1)]
    t0 = time.monotonic()
    with pytest.raises(StopIteration):
        next(it)
    assert time.monotonic() - t0 >= 0.18


def test_every_streaming_button_is_settled():
    """每个流式按钮（do_ 开头的生成器）注册时都包了 _settled。"""
    import inspect
    import re

    src = Path(A.__file__).read_text(encoding="utf-8")
    streaming = {name for name, fn in inspect.getmembers(A.WebUI, inspect.isfunction)
                 if name.startswith("do_") and inspect.isgeneratorfunction(fn)}
    assert {"do_prepare", "do_generate", "do_verify"} <= streaming
    registered = set(re.findall(r"\.click\(\s*(?:_settled\()?self\.(do_\w+)", src))
    settled = set(re.findall(r"\.click\(\s*_settled\(self\.(do_\w+)\)", src))
    assert streaming <= registered, streaming - registered
    assert streaming <= settled, streaming - settled


def test_generate_with_dummy_backend(prepared, tmp_path):
    """用测试引擎完整跑一次「生成」：进度条、结果表从 1 开始、重做框清空、下载列表里没有 report.json。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    ui = A.WebUI(cfg)
    outs = list(ui.do_generate(name, "大家好，欢迎来到今天的课程。\n\n我们开始上课吧。", None, "dummy", "fast", -10,
                               "", "", "第1课", "wav"))
    assert all(len(o) == len(ui.GEN_OUT) for o in outs)
    last = dict(zip(ui.GEN_OUT, outs[-1]))
    assert "vt-done" in last["gen_bar"], last["gen_md"]
    assert last["redo"] == "" and last["gen_btn"]["interactive"] is True and last["gen_stop"]["visible"] is False
    assert last["gen_md"].startswith("### ✅ 生成好了")
    assert [r[0] for r in last["gen_table"]] == list(range(1, len(last["gen_table"]) + 1))
    assert all(not f.endswith(".report.json") for f in last["out_files"])
    audio = Path(last["out_audio"]["value"])
    assert audio.exists() and audio.name.startswith("第1课_")
    if len(outs) > 1:
        assert outs[0][ui.GEN_OUT.index("gen_btn")]["interactive"] is False
        assert _is_update(outs[0][ui.GEN_OUT.index("out_audio")])  # 运行中不清掉上一次的结果
    # 点结果表的第 2 句：单独播放这一句（没有 clip 时从整段里切出来）
    state = last["gen_state"]
    seg = ui.on_gen_pick(state, list(reversed(last["gen_table"])), len(last["gen_table"]) - 2)
    assert Path(seg["value"]).exists() and seg["label"].startswith("第 2 句")


def test_nvidia_smi_driver_failure_is_not_ok():
    msg = ("NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. "
           "Make sure that the latest NVIDIA driver is installed and running.")
    ok, detail = nvidia_smi_status(9, msg)
    assert ok is False and "驱动" in detail
    # 有些版本出错时退出码仍是 0
    assert nvidia_smi_status(0, msg)[0] is False
    assert nvidia_smi_status(0, "")[0] is False
    assert nvidia_smi_status(0, "NVIDIA GeForce RTX 5070, 12227 MiB, 576.02") == (
        True, "NVIDIA GeForce RTX 5070, 12227 MiB, 576.02")


def test_output_name_time_has_no_cjk_in_strftime(monkeypatch):
    """文件名里的「10月01日21点30分」不能靠 strftime 的中文格式（Windows 上非中文系统会报错）。"""
    calls = []
    real = time.strftime

    def spy(fmt, *a):
        calls.append(fmt)
        return real(fmt, *a)

    monkeypatch.setattr(A.time, "strftime", spy)
    t = time.mktime((2026, 10, 1, 21, 5, 0, 0, 0, -1))
    assert A._time_suffix(t) == "10月01日21点05分"
    assert all(ord(ch) < 128 for fmt in calls for ch in fmt)
    p = A._output_path(SimpleNamespace(outputs_dir="/tmp/x"), "第3课", "mp3", "")
    assert p.name.startswith("第3课_") and p.suffix == ".mp3" and "月" in p.name


def test_header_shows_version():
    import voicetwin

    assert f"声音分身 VoiceTwin v{voicetwin.__version__}" in A.INTRO


# ---------------------------------------------------------------------------- 更多处理函数（真的走后台任务）
def test_safe_decorator_returns_friendly_text():
    def boom(*a):
        raise RuntimeError("还没有名为「x」的声音")

    out = A._safe("保存修改", 3, 0)(boom)(1)
    assert len(out) == 3 and "保存修改没有完成" in out[0] and _is_update(out[1]) and _is_update(out[2])
    assert "没有完成" in A._safe("评估", 1)(boom)()


def test_proofcheck_through_task(prepared, tmp_path, monkeypatch):
    cfg, name = _copy_voice(prepared, tmp_path)

    def fake_run(c, voice, progress=None):
        project = wf.Project(c, voice)
        recs = project.load_manifest()
        for i, r in enumerate(recs, 1):
            progress(i / len(recs), f"检查 {i}/{len(recs)}")
        recs[0]["suspect"] = {"spans": [[0, 2]], "alt": "改过" + recs[0]["text"][2:], "reasons": ["两次识别不一样"],
                              "score": 0.6}
        project.save_manifest(recs)
        return {"checked": len(recs), "flagged": 1, "engine": "funasr", "note": "用 FunASR 又听了一遍"}

    monkeypatch.setattr(wf, "run_proofcheck", fake_run, raising=False)
    monkeypatch.setattr(wf, "apply_suggestion", lambda c, v, cid: {"text": "改过的文字"}, raising=False)
    ui = A.WebUI(cfg)
    outs = list(ui.do_proofcheck(name, False))
    assert all(len(o) == len(ui.PROOF_OUT) for o in outs)
    last = dict(zip(ui.PROOF_OUT, outs[-1]))
    assert "vt-done" in last["proof_bar"] and "其中 **1** 条可能有错" in last["proof_md"]
    assert "用 FunASR 又听了一遍" in last["proof_md"]
    assert "其中 **1** 条可能有错（已标红）" in last["clips_count"]
    # 表格由接在后面的 refresh_clips 刷新（读的是那时网页上的表格，查错字期间改的内容不会被冲掉）
    count, rows = ui.refresh_clips(name, False, None)
    col = CLIP_HEADERS.index("可能有错（红色）")
    assert "color:#dc2626" in rows[0][col] and "其中 **1** 条可能有错" in count
    # 点这一行：出现对比和「采用建议」按钮
    audio, panel, adopt, cid = ui.on_clip_pick(name, rows, 0, 0)
    assert "识别 A" in panel and "识别 B" in panel and adopt["visible"] is True and adopt["value"] == A.ADOPT_BTN
    msg, count, table, diff, adopt2 = ui.do_adopt(name, cid)
    assert msg.startswith("✅ 已采用建议") and adopt2["visible"] is False and adopt2["value"] == A.ADOPT_BTN


def _edit_rows(rows, edits):
    """模拟老师在网页表格里改了还没保存：{行号: {列名: 新值}}。"""
    rows = [list(r) for r in rows]
    for i, cols in edits.items():
        for k, v in cols.items():
            rows[i][CLIP_HEADERS.index(k)] = v
    return rows


def test_adopt_and_filter_keep_unsaved_edits(prepared, tmp_path):
    """校对时手改了几行还没保存，再点别的行「✅ 采用建议」、勾「只看可能有错的」：手改的内容不能被冲掉。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    recs = project.load_manifest()
    for r in recs:  # 共享的 prepared 可能被别的测试标过红
        r.pop("suspect", None)
    recs[-1]["suspect"] = {"spans": [[0, 1]], "alt": "建议的文字。", "reasons": ["两次识别不一样"], "score": 0.5}
    project.save_manifest(recs)
    ui = A.WebUI(cfg)
    text_col, keep_col = A.COL_TEXT, A.COL_KEEP
    flip = "否" if recs[1].get("keep", True) else "是"  # 共享的 prepared 可能被别的测试改过「保留」
    rows = _edit_rows(A._clips_table(cfg, name), {0: {text_col: "老师手动改的第一行"}, 1: {keep_col: flip}})
    sus_id = recs[-1]["id"]
    msg, count, table, diff, adopt = ui.do_adopt(name, sus_id, False, rows)
    assert msg.startswith("✅ 已采用建议") and "还有 **2** 条修改没有保存" in msg
    by_id = {r[1]: r for r in table}
    assert by_id[recs[0]["id"]][CLIP_HEADERS.index(text_col)] == "老师手动改的第一行"
    assert by_id[recs[1]["id"]][CLIP_HEADERS.index(keep_col)] == flip
    assert by_id[sus_id][CLIP_HEADERS.index(text_col)] == "建议的文字。"
    # 硬盘上只改了采用建议的那一条，手改的还等着「保存修改」
    saved = {r["id"]: r for r in project.load_manifest()}
    assert saved[recs[0]["id"]]["text"] == recs[0]["text"] and saved[sus_id]["text"] == "建议的文字。"
    # 勾「只看可能有错的」：没有标红的行了，但改过还没保存的两行留在表格里
    recs2 = project.load_manifest()
    recs2[2]["suspect"] = {"spans": [[0, 1]], "alt": "x", "reasons": ["r"], "score": 0.5}
    project.save_manifest(recs2)
    count2, filtered = ui.refresh_clips(name, True, table)
    ids = [r[1] for r in filtered]
    assert ids[0] == recs2[2]["id"] and set(ids[1:]) == {recs[0]["id"], recs[1]["id"]}
    assert [r[0] for r in filtered] == [1, 2, 3] and "还有 **2** 条修改没有保存" in count2
    assert {r[1]: r for r in filtered}[recs[0]["id"]][CLIP_HEADERS.index(text_col)] == "老师手动改的第一行"
    # 然后点「保存修改」：手改的内容真的存进去了
    ui.do_save(name, filtered, True)
    saved = {r["id"]: r for r in project.load_manifest()}
    assert saved[recs[0]["id"]]["text"] == "老师手动改的第一行" and saved[recs[1]["id"]]["keep"] is (flip == "是")
    # 没改过东西时：和「重新载入」一样，不多提示
    count3, plain = ui.refresh_clips(name, False, A._clips_table(cfg, name))
    assert "没有保存" not in count3 and plain == A._clips_table(cfg, name)


def test_after_prepare_keeps_edits_and_filter(prepared, tmp_path):
    """素材准备做完后刷新表格：按「只看可能有错的」筛选；开始前没保存的、等待期间改的都留着。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    recs = project.load_manifest()
    for r in recs:
        r.pop("suspect", None)
    recs[3]["suspect"] = {"spans": [[0, 1]], "alt": "x", "reasons": ["r"], "score": 0.5}
    project.save_manifest(recs)
    ui = A.WebUI(cfg)
    start = _edit_rows(A._clips_table(cfg, name), {0: {A.COL_TEXT: "开始前改的"}})
    base = {"voice": name, "table": A._table_records(start, CLIP_HEADERS),
            "pending": sorted(A._pending_edits(cfg, name, start))}
    # 准备素材期间：别的步骤把第 2 条的「保留」改了（不能被当成老师的修改），老师又改了第 3 条
    recs = project.load_manifest()
    recs[1]["keep"] = not recs[1].get("keep", True)
    project.save_manifest(recs)
    end = _edit_rows(start, {2: {A.COL_TEXT: "等待时改的"}})
    count, rows, cleared = ui.after_prepare_clips(name, True, end, base)
    assert cleared == {}
    by_id = {r[1]: r for r in rows}
    assert rows[0][1] == recs[3]["id"]  # 只看可能有错的：标红的在前面
    assert by_id[recs[0]["id"]][CLIP_HEADERS.index(A.COL_TEXT)] == "开始前改的"
    assert by_id[recs[2]["id"]][CLIP_HEADERS.index(A.COL_TEXT)] == "等待时改的"
    assert recs[1]["id"] not in by_id and "还有 **2** 条修改没有保存" in count
    # 没勾筛选、也没改过：就是最新的完整表格
    plain = A._clips_table(cfg, name)
    base2 = {"voice": name, "table": A._table_records(plain, CLIP_HEADERS), "pending": []}
    assert ui.after_prepare_clips(name, False, plain, base2)[1] == plain
    # 这次没真正开始准备（clips_base 是空的）：表格不动
    assert all(_is_update(x) for x in ui.after_prepare_clips(name, False, plain, {})[:2])


def test_adopt_when_csv_locked_still_refreshes(prepared, tmp_path, monkeypatch):
    """transcripts.csv 被 Excel/WPS 打开时点「采用建议」：照样改好、表格照样刷新，并提醒关掉 Excel 后再保存一次。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    recs = project.load_manifest()
    recs[0]["suspect"] = {"spans": [[0, 1]], "alt": "新的建议文字。", "reasons": ["r"], "score": 0.5}
    project.save_manifest(recs)

    def locked(self, records=None):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(wf.Project, "export_csv", locked)
    msg, count, table, diff, adopt = A.WebUI(cfg).do_adopt(name, recs[0]["id"], False, A._clips_table(cfg, name))
    assert msg.startswith("✅ 已采用建议") and "Excel/WPS" in msg
    assert {r[1]: r for r in table}[recs[0]["id"]][CLIP_HEADERS.index(A.COL_TEXT)] == "新的建议文字。"
    assert {r["id"]: r for r in project.load_manifest()}[recs[0]["id"]]["text"] == "新的建议文字。"


def test_blind_test_through_task(prepared, tmp_path, monkeypatch):
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    clips = [project.abspath(r["path"]) for r in project.load_manifest()][:4]

    def fake_build(c, voice, n=10, quality="balanced", progress=None):
        d = project.outputs_dir / "盲听测试_1"
        d.mkdir(parents=True, exist_ok=True)
        answers = []
        for i, src in enumerate(clips, 1):
            shutil.copyfile(src, d / f"{i:02d}.wav")
            answers.append({"index": i, "kind": "real" if i % 2 else "generated"})
            if progress:
                progress(i / len(clips), f"第 {i}/{len(clips)} 段")
        (d / "答案.json").write_text(json.dumps(answers), encoding="utf-8")
        (d / "听众答题卡.txt").write_text("1.\n2.\n", encoding="utf-8")
        return {"dir": str(d), "n": n, "quality": quality}

    monkeypatch.setattr(wf, "build_blind_test", fake_build, raising=False)
    ui = A.WebUI(cfg)
    outs = list(ui.do_blind(name, 2, "fast"))
    assert all(len(o) == len(ui.BLIND_OUT) for o in outs)
    last = dict(zip(ui.BLIND_OUT, outs[-1]))
    assert "一共 4 段" in last["bt_md"] and "听众答题卡" in last["bt_md"]
    assert last["bt_submit"]["visible"] is True and last["bt_submit"]["value"] == A.SUBMIT_BTN
    assert last["bt_audio_3"]["visible"] is True and last["bt_audio_4"]["visible"] is False
    out = dict(zip(ui.BLIND_SUBMIT_OUT, ui.on_blind_submit(last["bt_state"], "real", "fake", "fake", None,
                                                           *([None] * 20))))
    assert "还有第 4 段没选" in out["bt_result"]
    out = dict(zip(ui.BLIND_SUBMIT_OUT, ui.on_blind_submit(last["bt_state"], "real", "fake", "fake", "fake",
                                                           *([None] * 20))))
    assert "答了 4 段，答对 3 段" in out["bt_result"]


def test_verify_through_task(prepared, tmp_path):
    cfg, name = _copy_voice(prepared, tmp_path)
    project = wf.Project(cfg, name)
    rec = project.load_manifest()[0]
    gen = tmp_path / "生成的.wav"
    shutil.copyfile(project.abspath(rec["path"]), gen)
    ui = A.WebUI(cfg)
    outs = list(ui.do_verify(name, None, [str(gen)], {}))
    assert all(len(o) == len(ui.VERIFY_OUT) for o in outs)
    last = dict(zip(ui.VERIFY_OUT, outs[-1]))
    assert "鉴别完成：共 1 个文件" in last["vf_md"], last["vf_md"]
    row = last["vf_table"][0]
    assert row[0] == 1 and row[1] == "生成的.wav" and row[3].endswith("%")
    # 没生成过也没上传：提示先生成（共享的 prepared 可能已经被别的测试生成过音频，副本里删掉）
    cfg2, name2 = _copy_voice(prepared, tmp_path / "b")
    shutil.rmtree(wf.Project(cfg2, name2).outputs_dir, ignore_errors=True)
    out = list(A.WebUI(cfg2).do_verify(name2, None, None, {}))
    assert "还没有生成过音频" in out[0][0]


def test_download_through_task(tmp_path, monkeypatch):
    from conftest import make_cfg

    monkeypatch.setattr(A, "_download_job", lambda c, progress=None: (progress(0.5, "已下载 1 / 2 MB"), ["a", "b"])[1])
    ui = A.WebUI(make_cfg(tmp_path))
    outs = list(ui.do_download())
    last = dict(zip(ui.DL_OUT, outs[-1]))
    assert "已下载 2 个文件" in last["doc_md"] and last["dl_btn"]["interactive"] is True


def test_choose_variant_copies_through_workflow(tmp_path, prepared):
    """「最终使用哪个版本」：网页调用 wf.choose_variant，把选中的版本复制成最终文件，报告里记下 final。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    a, b, final = tmp_path / "x_未去杂音.wav", tmp_path / "x_去杂音.wav", tmp_path / "x.wav"
    a.write_bytes(b"A")
    b.write_bytes(b"B")
    final.write_bytes(b"A")
    variants = [{"name": "未去杂音", "label": "版本 A：未去杂音", "path": str(a), "score": 0.91, "pct": 96.2,
                 "recommended": True, "final": True},
                {"name": "去杂音", "label": "版本 B：去杂音", "path": str(b), "score": 0.90, "pct": 95.4,
                 "recommended": False, "final": False}]
    report = tmp_path / "x.report.json"
    report.write_text(json.dumps({"audio": str(final), "variants": variants, "final": "未去杂音", "overall_pct": 96.2},
                                 ensure_ascii=False), encoding="utf-8")
    srt = tmp_path / "x.srt"
    srt.write_text("1\n", encoding="utf-8")
    state = {"voice": name, "audio": str(final), "report": str(report), "variants": variants, "srt": str(srt)}
    audio, files, note = A.WebUI(cfg).on_choose_variant(name, state, "去杂音")
    assert final.read_bytes() == b"B" and audio["value"] == str(b) and "版本 B" in note and str(final) in note
    # 下载列表也要重新发（gradio 4.24 按内容缓存文件，不重新发的话 x.wav 下载到的还是旧版本）
    assert files == [str(final), str(srt), str(a), str(b)]
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["final"] == "去杂音" and [v["final"] for v in data["variants"]] == [False, True]
    assert data["overall_pct"] == 95.4  # 整篇百分比跟着最终版本走
    # 已经是最终版本：什么都不改、不提示（gradio 4.24 显示这组控件时会自动触发一次）
    final.write_bytes(b"B")
    audio_same, files_same, note_same = A.WebUI(cfg).on_choose_variant(name, state, "去杂音")
    assert _is_update(audio_same) and "value" not in audio_same and _is_update(note_same) and _is_update(files_same)
    # 没生成过（state 是空的）：只给一句提示，不报错
    audio2, files2, note2 = A.WebUI(cfg).on_choose_variant(name, {}, "去杂音")
    assert _is_update(audio2) and _is_update(files2) and "请先生成一次" in note2


def test_one_task_at_a_time_and_reattach(prepared, tmp_path, monkeypatch):
    """准备素材在跑时：点「开始训练」只给黄色提示、按钮恢复；再点「开始准备素材」接上原来的任务，不重新开始。"""
    import threading

    from voicetwin.webui import tasks

    cfg, name = _copy_voice(prepared, tmp_path)
    started, release = threading.Event(), threading.Event()
    calls = []

    def slow_prepare(c, voice, inputs, progress=None, overrides=None):
        calls.append(voice)
        progress(0.3, "识别每段话的文字 3/10")
        started.set()
        release.wait(20)
        return {"clips_kept": 1, "clips_total": 1, "minutes_kept": 0.1}

    monkeypatch.setattr(wf, "run_prepare", slow_prepare)
    ui = A.WebUI(cfg)
    gen1 = ui.do_prepare(name, None, str(tmp_path), "none", "auto", "auto", False)
    first = dict(zip(ui.PREP_OUT, next(gen1)))
    assert started.wait(10)
    try:
        assert first["prep_btn"]["interactive"] is False and first["prep_btn"]["value"] == A.PREP_BUSY
        busy = list(ui.do_train(name, "gptsovits", 0, 0, 0, 0))
        assert len(busy) == 1
        b = dict(zip(ui.TRAIN_OUT, busy[0]))
        assert "同一时间只能做一件事" in b["train_log"] and "vt-note-warn" in b["train_bar"]
        assert b["train_btn"]["interactive"] is True
        gen2 = ui.do_prepare(name, None, "", "none", "auto", "auto", False)
        att = dict(zip(ui.PREP_OUT, next(gen2)))
        assert tasks.ATTACHED_NOTE in att["prep_log"] and att["prep_btn"]["interactive"] is False
        assert "后台正在「准备素材」" in A.task_banner_md()
    finally:
        release.set()
    last = dict(zip(ui.PREP_OUT, list(gen2)[-1]))
    assert "vt-done" in last["prep_bar"] and last["prep_btn"]["interactive"] is True
    list(gen1)
    assert calls == [name]  # 只做了一次


def test_reattach_skips_input_checks(prepared, tmp_path, monkeypatch):
    """刷新网页后输入框是空的：再点同一个按钮要接上进度，而不是提示「请填写文件夹 / 讲稿」。
    这里模拟「点的一瞬间任务刚好做完」：不会用空输入重新开始，只提示结果已经刷新。"""
    cfg, name = _copy_voice(prepared, tmp_path)
    ui = A.WebUI(cfg)
    for kind in ("generate", "prepare"):
        monkeypatch.setattr(A, "current_task", lambda k=kind: {"running": True, "kind": k, "voice": name,
                                                               "label": "x"})
        if kind == "generate":
            outs = list(ui.do_generate(name, "", None, "dummy", "fast", 0, "", "看不懂的输入"))
            last = dict(zip(ui.GEN_OUT, outs[-1]))
            assert last["gen_md"] == A.ATTACH_MISSED_MD and _is_update(last["out_audio"])
        else:
            outs = list(ui.do_prepare(name, None, "", "none", "auto", "auto", False))
            last = dict(zip(ui.PREP_OUT, outs[-1]))
            assert last["prep_md"] == A.ATTACH_MISSED_MD and last["prep_btn"]["interactive"] is True


def test_eval_refused_while_task_runs(prepared, monkeypatch):
    cfg, project, _ = prepared
    monkeypatch.setattr(A, "current_task", lambda: {"running": True, "label": "训练模型", "voice": "x", "kind": "train"})
    assert "评估也要用显卡" in A.WebUI(cfg).eval_impl(project.voice, "/tmp/a.wav", "")
