"""进度条的完整流程：每个长任务报告的进度都只往前走（逐个记录每一次 frac），最后到 100%。

还覆盖：开始前检查、坏视频跳过、训练成功但挑选失败、阻止睡眠、查错字接入、阶段表。
"""

import contextlib
import re
import subprocess
import sys
import time
import types
import uuid
from pathlib import Path

import pytest

from voicetwin import workflows as wf

from conftest import make_cfg, make_lecture, confirm_material


class Rec:
    """记录每一次进度回调 (frac, msg)。"""

    def __init__(self):
        self.calls = []

    def __call__(self, frac, msg=""):
        self.calls.append((float(frac), str(msg)))

    @property
    def fracs(self):
        return [f for f, _ in self.calls]

    @property
    def msgs(self):
        return [m for _, m in self.calls]

    def assert_monotonic(self):
        assert self.calls, "没有任何进度"
        for (a, ma), (b, mb) in zip(self.calls, self.calls[1:]):
            assert b >= a - 1e-9, f"进度倒退：{a:.4f}（{ma}）→ {b:.4f}（{mb}）"
        assert all(0.0 <= f <= 1.0 for f in self.fracs)


def _unique(text: str) -> str:
    """每次测试用不同的句子，避免 session 级缓存让引擎不启动。"""
    return text + "编号" + "".join(str(int(c, 16) % 10) for c in uuid.uuid4().hex[:6]) + "。"


# ---------------------------------------------------------------------------- 素材准备
def test_prepare_progress_monotonic_and_style_stage(tmp_path, lecture_dir):
    rec = Rec()
    summary = wf.run_prepare(make_cfg(tmp_path / "ws"), "v", [str(lecture_dir)], progress=rec)
    rec.assert_monotonic()
    assert rec.fracs[-1] == 1.0
    assert any(f >= 0.95 and "风格" in m for f, m in rec.calls)
    assert any(re.search(r"\[第 1/1 个文件\]", m) for m in rec.msgs)
    assert any("切成小段" in m for m in rec.msgs)
    assert summary["skipped_files"] == []
    # 素材准备本身（prepare）不报 100%：只有 run_prepare 最后一步报
    assert sum(1 for f in rec.fracs if f >= 1.0) == 1

    # 再准备一次同一个文件夹：第一条消息就说之前处理过，并且有"没有新视频"的提醒
    rec2 = Rec()
    again = wf.run_prepare(make_cfg(tmp_path / "ws"), "v", [str(lecture_dir)], progress=rec2)
    assert "之前已经处理过" in rec2.msgs[0]
    assert any("没有找到新的视频" in w for w in again["warnings"])
    rec2.assert_monotonic()


def test_prepare_missing_folder_is_reported_before_work(tmp_path):
    with pytest.raises(FileNotFoundError, match="找不到文件夹"):
        wf.run_prepare(make_cfg(tmp_path / "ws"), "v", [str(tmp_path / "没有这个文件夹")])
    # 带引号粘贴的路径也能认出来
    d = tmp_path / "有引号"
    make_lecture(d / "a.wav", repeats=1)
    assert wf._clean_input(f'"{d}"') == str(d)


def test_prepare_fails_early_when_asr_module_missing(tmp_path, lecture_dir, monkeypatch):
    cfg = make_cfg(tmp_path / "ws", prepare={"asr": {"engine": "faster-whisper"}, "segmentation": "energy"})
    monkeypatch.setattr("voicetwin.data.asr.engine_importable", lambda engine: False)
    t0 = time.time()
    with pytest.raises(RuntimeError, match="语音识别组件没装好"):
        wf.run_prepare(cfg, "v", [str(lecture_dir)])
    assert time.time() - t0 < 5  # 不会先处理一小时才失败


def test_bad_video_is_skipped_and_retried(tmp_path):
    src = tmp_path / "in"
    make_lecture(src / "好的.wav", repeats=2)
    (src / "bad.mp4").write_bytes(b"")
    cfg = make_cfg(tmp_path / "ws")
    rec = Rec()
    summary = wf.run_prepare(cfg, "v", [str(src)], progress=rec)
    rec.assert_monotonic()
    assert summary["clips_kept"] > 0
    assert [x["file"] for x in summary["skipped_files"]] == ["bad.mp4"]
    assert summary["skipped_files"][0]["reason"]
    project = wf.open_project(cfg, "v", must_exist=True)
    db = project.read_json(project.sources_path, {})
    bad = [v for v in db.values() if v["file"].endswith("bad.mp4")]
    assert bad and "done" not in bad[0] and bad[0]["failed"]
    # 下次再准备：坏文件会再试一次（好的文件不会重做）
    rec2 = Rec()
    again = wf.run_prepare(cfg, "v", [str(src)], progress=rec2)
    assert "其中 1 个是新的" in rec2.msgs[0]
    assert [x["file"] for x in again["skipped_files"]] == ["bad.mp4"]


def test_unexpected_errors_keep_the_real_cause_in_the_log(tmp_path, monkeypatch):
    """跳过文件、自动查错字失败这类「接着做」的地方：网页上只显示中文，但原始报错要写进日志（给帮忙的人查）。"""
    import logging

    from voicetwin.data import prepare as prep

    src = tmp_path / "in"
    make_lecture(src / "a.wav", repeats=2)
    make_lecture(src / "b.wav", repeats=2, seed=5)
    orig = prep.enhance_file

    bad_sid = prep.source_id(src / "b.wav")

    def flaky(raw, clean, *a, **k):
        if Path(clean).stem == bad_sid:
            raise IndexError("REAL-CAUSE-PREP list index out of range")
        return orig(raw, clean, *a, **k)

    monkeypatch.setattr(prep, "enhance_file", flaky)

    def boom(*a, **k):
        raise ValueError("REAL-CAUSE-PROOF bad value")

    monkeypatch.setattr(wf, "proofcheck_plan", lambda cfg, overrides=None: (True, "funasr", "测试"))
    monkeypatch.setattr(wf, "_proofcheck_module", lambda: types.SimpleNamespace(find_suspects=boom))
    records = []

    class H(logging.Handler):
        def emit(self, record):
            records.append(record)

    h = H(level=logging.DEBUG)
    logging.getLogger("voicetwin").addHandler(h)
    try:
        cfg = make_cfg(tmp_path / "ws")
        summary = wf.run_prepare(cfg, "v", [str(src)])
    finally:
        logging.getLogger("voicetwin").removeHandler(h)
    assert [x["file"] for x in summary["skipped_files"]] == ["b.wav"]
    with_exc = [r for r in records if r.exc_info]
    causes = " ".join(repr(r.exc_info[1]) for r in with_exc)
    assert "REAL-CAUSE-PREP" in causes
    # 网页上显示的那一行（getMessage）只有中文说明，没有英文报错
    assert all("REAL-CAUSE" not in r.getMessage() for r in records)
    project = wf.open_project(cfg, "v", must_exist=True)
    db = project.read_json(project.sources_path, {})
    assert any("REAL-CAUSE-PREP" in str(v.get("error", "")) for v in db.values())
    assert any("自动查错字没有完成" in w for w in summary["warnings"]) and "REAL-CAUSE-PROOF" in causes


def test_all_videos_broken_gives_friendly_error(tmp_path):
    src = tmp_path / "in"
    src.mkdir()
    (src / "坏1.mp4").write_bytes(b"")
    with pytest.raises(RuntimeError, match="所有视频都没能处理"):
        wf.run_prepare(make_cfg(tmp_path / "ws"), "v", [str(src)])


def test_disk_full_stops_immediately(tmp_path, monkeypatch):
    import errno

    src = tmp_path / "in"
    make_lecture(src / "a.wav", repeats=1)
    make_lecture(src / "b.wav", repeats=1, seed=5)
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr("voicetwin.data.prepare.extract_audio", boom)
    with pytest.raises(OSError):
        wf.run_prepare(make_cfg(tmp_path / "ws"), "v", [str(src)])
    assert len(calls) == 1  # 第二个文件不再尝试


# ---------------------------------------------------------------------------- 查错字接入（U8 的 proofcheck，用假的代替）
def _fake_proofcheck(engine="funasr", flag_ids=2):
    mod = types.ModuleType("voicetwin.data.proofcheck")
    seen = {}

    def available_checker(cfg):
        return engine, "用另一个识别引擎再听一遍"

    def find_suspects(project, cfg, progress=None, only_kept=True, limit=None):
        recs = project.load_manifest()
        todo = [r for r in recs if r.get("text") and (r.get("keep", True) or not only_kept)][:limit]
        flagged = 0
        for i, r in enumerate(todo, 1):
            if progress:
                progress(i / len(todo), f"检查 {i}/{len(todo)}")
            if flagged < flag_ids:
                r["suspect"] = {"spans": [[0, 1]], "alt": "改过的" + r["text"], "reasons": ["测试"], "score": 0.9}
                flagged += 1
        project.save_manifest(recs)
        seen["called"] = True
        return {"checked": len(todo), "flagged": flagged, "engine": engine, "note": ""}

    mod.available_checker = available_checker
    mod.find_suspects = find_suspects
    mod.seen = seen
    return mod


@pytest.fixture
def fake_proofcheck(monkeypatch):
    import voicetwin.data

    mod = _fake_proofcheck()
    monkeypatch.setitem(sys.modules, "voicetwin.data.proofcheck", mod)
    monkeypatch.setattr(voicetwin.data, "proofcheck", mod, raising=False)
    return mod


def test_prepare_runs_proofcheck_stage_when_second_engine_available(tmp_path, lecture_dir, fake_proofcheck):
    cfg = make_cfg(tmp_path / "ws")
    stages = wf.task_stages("prepare", cfg)
    assert stages == wf.STAGES_PREPARE_PROOFCHECK
    assert [f for f, _ in stages] == sorted(f for f, _ in stages)
    assert stages[-1][1] == "查找可能的错字"
    rec = Rec()
    summary = wf.run_prepare(cfg, "v", [str(lecture_dir)], progress=rec)
    rec.assert_monotonic()
    assert fake_proofcheck.seen.get("called")
    assert summary["proofcheck"]["flagged"] == 2
    assert any("可能有错" in w for w in summary["warnings"])
    assert any(f >= wf.PROOFCHECK_START and "错字" in m for f, m in rec.calls)
    # 素材准备部分被压缩到 0.85 以内，风格分析在 0.85
    assert any(abs(f - wf.PROOFCHECK_PREPARE_END) < 1e-9 and "风格" in m for f, m in rec.calls)
    assert max(f for f, m in rec.calls if "素材整理完成" in m) <= wf.PROOFCHECK_PREPARE_END + 1e-9
    assert rec.fracs[-1] == 1.0
    # proofcheck: off 时阶段表不变
    off = make_cfg(tmp_path / "ws2", prepare={"asr": {"engine": "none"}, "proofcheck": "off"})
    assert wf.task_stages("prepare", off) == wf.STAGES_PREPARE


def test_proofcheck_auto_needs_a_different_engine(tmp_path, monkeypatch):
    import voicetwin.data

    same = _fake_proofcheck(engine="faster-whisper")
    monkeypatch.setitem(sys.modules, "voicetwin.data.proofcheck", same)
    monkeypatch.setattr(voicetwin.data, "proofcheck", same, raising=False)
    cfg = make_cfg(tmp_path, prepare={"asr": {"engine": "faster-whisper"}})
    assert wf.proofcheck_plan(cfg)[0] is False  # 和主识别引擎一样：auto 不做
    assert wf.proofcheck_plan(cfg, {"proofcheck": "on"})[0] is True
    assert wf.proofcheck_plan(cfg, {"asr": {"engine": "funasr"}})[0] is True  # 网页选了 funasr，whisper 就是第二个
    words = _fake_proofcheck(engine="faster-whisper-words")
    monkeypatch.setitem(sys.modules, "voicetwin.data.proofcheck", words)
    monkeypatch.setattr(voicetwin.data, "proofcheck", words, raising=False)
    assert wf.proofcheck_plan(cfg)[0] is False  # 只是重新跑一遍同一个引擎，太慢，auto 不做


def test_proofcheck_failure_does_not_fail_prepare(tmp_path, lecture_dir, monkeypatch):
    import voicetwin.data

    mod = _fake_proofcheck()

    def broken(*a, **k):
        raise RuntimeError("模型下载失败")

    mod.find_suspects = broken
    monkeypatch.setitem(sys.modules, "voicetwin.data.proofcheck", mod)
    monkeypatch.setattr(voicetwin.data, "proofcheck", mod, raising=False)
    rec = Rec()
    summary = wf.run_prepare(make_cfg(tmp_path / "ws"), "v", [str(lecture_dir)], progress=rec)
    assert summary["clips_kept"] > 0 and rec.fracs[-1] == 1.0
    assert any("自动查错字没有完成" in w for w in summary["warnings"])


def test_run_proofcheck_and_apply_suggestion(tmp_path, lecture_dir, fake_proofcheck):
    cfg = make_cfg(tmp_path / "ws", prepare={"asr": {"engine": "none"}, "proofcheck": "off"})
    wf.run_prepare(cfg, "v", [str(lecture_dir)])
    rec = Rec()
    res = wf.run_proofcheck(cfg, "v", progress=rec)
    rec.assert_monotonic()
    assert res["flagged"] == 2 and rec.fracs[-1] == 1.0 and "可能有错" in rec.msgs[-1]
    project = wf.open_project(cfg, "v", must_exist=True)
    target = next(r for r in project.load_manifest() if r.get("suspect"))
    out = wf.apply_suggestion(cfg, "v", target["id"])
    assert out["text"].startswith("改过的")
    after = next(r for r in project.load_manifest() if r["id"] == target["id"])
    from voicetwin.data.review import analyze

    assert after["text"] == out["text"] and not analyze(after)["active"]  # 不再标红（采用的记录留着，可以撤销）
    assert out["text"] in project.csv_path.read_text(encoding="utf-8-sig")
    with pytest.raises(ValueError, match="没有可以采用的建议"):
        wf.apply_suggestion(cfg, "v", target["id"])
    with pytest.raises(ValueError, match="找不到"):
        wf.apply_suggestion(cfg, "v", "不存在的片段")


def test_run_proofcheck_without_module_is_friendly(tmp_path, lecture_dir, monkeypatch):
    monkeypatch.setattr(wf, "_proofcheck_module", lambda: None)
    with pytest.raises(RuntimeError, match="查错字功能没有装好"):
        wf.run_proofcheck(make_cfg(tmp_path), "v")


# ---------------------------------------------------------------------------- 训练 → 自动挑选
def _stub_train_backend():
    from voicetwin.backends.dummy import DummyBackend

    class StubTrain(DummyBackend):
        supports_training = True

        def train(self, progress=None, **opts):
            for f in (0.0, 0.1, 0.5, 0.95, 1.0):  # 真引擎训练完会报 1.0
                if progress:
                    progress(f, f"训练 {f:.0%}")
            return {"selected": {"id": "last"}}

    return StubTrain


def test_train_progress_does_not_jump_back_after_training(prepared, monkeypatch):
    cfg, project, _ = prepared
    stub = _stub_train_backend()
    monkeypatch.setattr("voicetwin.backends.base.get_backend", lambda name, c, p: stub(c, p))
    rec = Rec()
    confirm_material(cfg, project.voice)
    info = wf.run_train(cfg, project.voice, "dummy", progress=rec, select=True)
    rec.assert_monotonic()
    assert rec.fracs[-1] == 1.0
    train_part = [f for f, m in rec.calls if m.startswith("训练 ")]
    assert max(train_part) <= wf.TRAIN_SELECT_SPLIT + 1e-9  # 训练 100% 只走到 88%
    assert any(wf.TRAIN_SELECT_SPLIT <= f <= 1.0 and "挑选" in m for f, m in rec.calls)
    assert any("切换到模型" in m for m in rec.msgs)
    assert "selection" in info and "selection_error" not in info
    project.update_models("dummy", {"speed": {}})


def test_train_without_select_passes_progress_unchanged(prepared, monkeypatch):
    cfg, project, _ = prepared
    stub = _stub_train_backend()
    monkeypatch.setattr("voicetwin.backends.base.get_backend", lambda name, c, p: stub(c, p))
    rec = Rec()
    confirm_material(cfg, project.voice)
    wf.run_train(cfg, project.voice, "dummy", progress=rec, select=False)
    assert ("训练 100%" in rec.msgs) and max(f for f, m in rec.calls if m == "训练 100%") == 1.0


def test_selection_failure_does_not_fail_training(prepared, monkeypatch):
    cfg, project, _ = prepared

    class Stub:
        supports_training = True
        name = "gptsovits"
        display_name = "GPT-SoVITS"

        def train(self, progress=None, **opts):
            return {"selected": {"id": "x"}}

    monkeypatch.setattr("voicetwin.backends.base.get_backend", lambda name, c, p: Stub())

    def boom(*a, **k):
        raise RuntimeError("所有模型都合成失败，请检查引擎日志")

    monkeypatch.setattr(wf, "run_select", boom)
    confirm_material(cfg, project.voice)
    info = wf.run_train(cfg, project.voice, "gptsovits", select=True)
    assert info["selection_error"]
    assert info["selected"] == {"id": "x"}
    # 挑选没成功时也自动生成问题报告
    rep = Path(info["selection_error_report"])
    assert rep.parent == project.logs_dir and "所有模型都合成失败" in rep.read_text(encoding="utf-8-sig")


def test_train_stages_table():
    gcfg = make_cfg(Path("."), backend="gptsovits")
    for mode, split in (("standard", wf.TRAIN_SELECT_SPLIT), ("identical", wf.TRAIN_SELECT_SPLIT_IDENTICAL),
                        (None, wf.TRAIN_SELECT_SPLIT_IDENTICAL)):  # 不写训练方式 = config.yaml 的 auto = 「一模一样」
        stages = wf.task_stages("train", gcfg, "gptsovits", mode=mode)
        assert [f for f, _ in stages] == sorted(f for f, _ in stages)
        assert stages[-1] == (split, "自动挑选最像你的模型")
        assert all(f <= split for f, _ in stages)
    assert ("实测显卡一次能练几条" in [n for _, n in wf.task_stages("train", gcfg, "gptsovits", mode="identical")])
    assert ("实测显卡一次能练几条" not in [n for _, n in wf.task_stages("train", gcfg, "gptsovits", mode="standard")])
    no_sel = wf.task_stages("train", gcfg, "gptsovits", select=False)
    assert no_sel and no_sel[-1][1] != "自动挑选最像你的模型"
    assert wf.task_stages("select", gcfg) == wf.STAGES_SELECT
    assert wf.task_stages("download", gcfg) == wf.STAGES_DOWNLOAD
    assert wf.task_stages("narrate", gcfg, quality="balanced") == wf.STAGES_NARRATE
    assert wf.task_stages("narrate", gcfg, quality="perfect") == wf.STAGES_NARRATE_VARIANTS
    for kind in ("prepare", "proofcheck", "blind_test", "verify"):
        st = wf.task_stages(kind, gcfg)
        assert st and [f for f, _ in st] == sorted(f for f, _ in st)
    assert wf.task_stages("不知道", gcfg) == []


def _gsv_python_ok() -> bool:
    """fake GPT-SoVITS 用解析后的解释器跑脚本；某些 venv 里它找不到 yaml，那就跳过（已知的环境问题）。"""
    try:
        proc = subprocess.run([str(Path(sys.executable).resolve()), "-c", "import yaml, numpy"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        return proc.returncode == 0
    except Exception:
        return False


def test_train_flow_with_fake_gptsovits(prepared, tmp_path, monkeypatch):
    if not _gsv_python_ok():
        pytest.skip("这个环境里 fake GPT-SoVITS 的子进程用不了（已知的环境问题）")
    from fake_gptsovits import build_fake_root

    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS")
    gcfg = make_cfg(project.root.parent, backend="gptsovits", backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": 19890, "startup_timeout": 60, "is_half": True,
        "train": {"sovits_epochs": 8, "gpt_epochs": 10, "batch_size": 2, "sovits_save_every": 4, "gpt_save_every": 5},
    }})
    rec = Rec()
    confirm_material(gcfg, project.voice)
    info = wf.run_train(gcfg, project.voice, "gptsovits", select=True, progress=rec)
    rec.assert_monotonic()
    assert rec.fracs[-1] == 1.0
    # 默认「一模一样」：训练占前 62%，后面是挑选（第 4 轮以后存下的每个版本都试）
    split = wf.TRAIN_SELECT_SPLIT_IDENTICAL
    assert any(split <= f <= 1.0 and "挑选" in m for f, m in rec.calls)
    assert all(f <= split + 1e-9 for f, m in rec.calls if m.startswith("训练音色") or m.startswith("训练语气"))
    assert any("切换到模型" in m for m in rec.msgs)
    assert "selection" in info


# ---------------------------------------------------------------------------- 挑选 / 生成
def test_select_progress(prepared):
    cfg, project, _ = prepared
    rec = Rec()
    wf.run_select(cfg, project.voice, "dummy", use_asr=False, progress=rec)
    rec.assert_monotonic()
    assert rec.msgs[0].startswith("加载声纹和识别模型")
    assert any("启动合成引擎" in m for m in rec.msgs)
    assert any(re.search(r"切换到模型 .+（第 1/1 个）", m) for m in rec.msgs)
    assert any(re.search(r"试听模型 .+：\d+/\d+", m) for m in rec.msgs)
    project.update_models("dummy", {"speed": {}})


def test_select_progress_errors_do_not_stop_selection(prepared):
    cfg, project, _ = prepared

    def bad_progress(frac, msg=""):
        raise ValueError("进度条坏了")

    info = wf.run_select(cfg, project.voice, "dummy", use_asr=False, progress=bad_progress)
    assert info["selection"]["best"]
    project.update_models("dummy", {"speed": {}})


def test_narrate_progress(prepared, tmp_path):
    cfg, project, _ = prepared
    rec = Rec()
    script = _unique("第一句话用来测试进度") + "\n\n" + _unique("第二句话也是为了测试") + "\n\n" + _unique("第三句")
    res = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "p.wav"), quality="balanced", progress=rec)
    rec.assert_monotonic()
    assert "启动合成引擎" in rec.msgs[0]
    assert any("第 1/3 个版本" in m for m in rec.msgs)
    assert any("拼接音频" in m for m in rec.msgs)
    assert rec.fracs[-1] == 1.0
    assert isinstance(res.flagged, list)
    assert all(s.get("clip") and project.abspath(s["clip"]).exists() for s in res.segments)


def test_narrate_redo_out_of_range_warns(prepared, tmp_path):
    cfg, project, _ = prepared
    res = wf.run_narrate(cfg, project.voice, "大家好，这是重做编号的测试句子。", out=str(tmp_path / "r.wav"),
                         quality="fast", redo=[99, 0])
    assert any("不存在" in w and "第 0、99 句" in w for w in res.warnings)


def test_cached_narration_never_starts_engine(prepared, tmp_path, monkeypatch):
    from voicetwin.backends.base import get_backend

    cfg, project, _ = prepared
    script = _unique("缓存测试的一句话")
    first = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "c1.wav"), quality="fast")
    assert not first.segments[0]["cached"]
    backend = get_backend("dummy", cfg, project)
    starts = []
    orig = backend.start
    monkeypatch.setattr(backend, "start", lambda: (starts.append(1), orig())[1])
    rec = Rec()
    second = wf.run_narrate(cfg, project.voice, script, out=str(tmp_path / "c2.wav"), quality="fast", backend=backend,
                            progress=rec)
    backend.stop()
    assert starts == [] and all(s["cached"] for s in second.segments)
    assert not any("启动合成引擎" in m for m in rec.msgs)
    rec.assert_monotonic()
    assert rec.fracs[-1] == 1.0


def test_perfect_narration_progress_has_variant_stage(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    monkeypatch.setattr("voicetwin.eval.metrics.Scorer.in_normal_range", lambda self, s, lang, speed=1.0: True)
    rec = Rec()
    wf.run_narrate(cfg, project.voice, _unique("完美档的进度测试"), out=str(tmp_path / "pf.wav"), quality="perfect",
                   progress=rec)
    rec.assert_monotonic()
    assert any(abs(f - 0.93) < 1e-9 and "去杂音" in m for f, m in rec.calls)
    assert any(abs(f - 0.90) < 1e-9 and "拼接音频" in m for f, m in rec.calls)
    assert rec.fracs[-1] == 1.0


# ---------------------------------------------------------------------------- 阻止睡眠
def test_long_tasks_keep_computer_awake(prepared, tmp_path, monkeypatch):
    cfg, project, _ = prepared
    events = []

    @contextlib.contextmanager
    def recording():
        events.append("enter")
        try:
            yield
        finally:
            events.append("exit")

    monkeypatch.setattr(wf, "keep_awake", recording)
    wf.run_narrate(cfg, project.voice, "阻止睡眠测试的一句话。", out=str(tmp_path / "k.wav"), quality="fast")
    assert events and events.count("enter") == events.count("exit") >= 1
    events.clear()
    with pytest.raises(RuntimeError):
        wf.run_train(cfg, project.voice, "dummy")  # dummy 不能训练 → 报错也要退出
    assert events.count("enter") == events.count("exit") == 1
