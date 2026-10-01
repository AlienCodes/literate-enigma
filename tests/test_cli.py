import json
import logging
import re

import pytest

from voicetwin.cli import _parse_redo, build_parser


def test_parse_redo():
    assert _parse_redo("3,5，8-10") == [3, 5, 8, 9, 10]
    assert _parse_redo("") == []


@pytest.mark.parametrize("text,expected", [
    ("3、5、8到10", [3, 5, 8, 9, 10]),
    ("第3句 第5句", [3, 5]),
    ("8~10", [8, 9, 10]),
    ("8～10", [8, 9, 10]),
    ("10-8", [8, 9, 10]),
    ("8 到 10", [8, 9, 10]),
    ("第3句到第5句", [3, 4, 5]),
    ("３，５", [3, 5]),
    ("5,3,5", [3, 5]),
    ("2;4；6", [2, 4, 6]),
    ("   ", []),
    (None, []),
])
def test_parse_redo_chinese_forms(text, expected):
    assert _parse_redo(text) == expected


@pytest.mark.parametrize("text", ["abc", "0", "3-", "-3", "3.5", "第一句", "1-0"])
def test_parse_redo_rejects_bad_input(text):
    with pytest.raises(ValueError) as ei:
        _parse_redo(text)
    assert "请这样填" in str(ei.value)


def test_parse_redo_rejects_absurd_range():
    with pytest.raises(ValueError):
        _parse_redo("1-99999999")


def test_parser_commands():
    ap = build_parser()
    args = ap.parse_args(["narrate", "-v", "我的声音", "讲稿.md", "-q", "best", "--redo", "2"])
    assert args.command == "narrate" and args.quality == "best" and args.redo == "2"
    args = ap.parse_args(["prepare", "-v", "x", "-i", "a", "b", "--asr", "funasr"])
    assert args.input == ["a", "b"] and args.asr == "funasr"
    for q in ("max", "perfect"):
        assert ap.parse_args(["say", "-v", "x", "你好", "-q", q]).quality == q
    assert ap.parse_args(["download-models", "--check"]).check is True
    assert ap.parse_args(["select", "-v", "x"]).items is None  # 默认交给 run_select 自己决定


def test_init_config_updates_in_place(tmp_path, monkeypatch):
    from voicetwin.cli import main
    from voicetwin.config import load_config

    monkeypatch.chdir(tmp_path)
    main(["init-config", "--backend", "indextts"])
    cfg_path = tmp_path / "config.yaml"
    text = re.sub(r"(?m)^(\s+quality:\s*)[A-Za-z_]+", r"\1fast", cfg_path.read_text(encoding="utf-8"), count=1)
    cfg_path.write_text(text, encoding="utf-8")
    # 再次运行（例如重新运行安装程序）：只更新指定项，保留用户改过的其它设置
    main(["init-config", "--gptsovits-root", str(tmp_path / "GSV"), "--backend", "gptsovits"])
    cfg = load_config(str(cfg_path))
    assert cfg["backend"] == "gptsovits"
    assert cfg.get_path("synth.quality") == "fast"
    assert cfg.backend("gptsovits")["root"].endswith("GSV")
    assert (tmp_path / "config.yaml.bak").exists()
    # 不带参数时保持不变
    main(["init-config"])
    assert load_config(str(cfg_path)).get_path("synth.quality") == "fast"


def test_init_config_updates_gbk_and_crlf_file(tmp_path, monkeypatch):
    from voicetwin.cli import main
    from voicetwin.config import load_config

    monkeypatch.chdir(tmp_path)
    main(["init-config"])
    cfg_path = tmp_path / "config.yaml"
    text = cfg_path.read_text(encoding="utf-8")
    # 记事本另存为「ANSI」（GBK）+ Windows 换行
    cfg_path.write_bytes(text.replace("\n", "\r\n").encode("gbk", errors="replace"))
    main(["init-config", "--backend", "indextts"])
    raw = cfg_path.read_bytes()
    assert b"\r\r\n" not in raw
    raw.decode("utf-8")  # 写回后是 UTF-8
    assert load_config(str(cfg_path))["backend"] == "indextts"


def test_verbose_after_subcommand():
    ap = build_parser()
    assert ap.parse_args(["narrate", "-v", "x", "a.md", "--verbose"]).verbose is True
    assert ap.parse_args(["--verbose", "doctor"]).verbose is True
    assert ap.parse_args(["doctor"]).verbose is False


# ---------------------------------------------------------------------------- config.yaml 写坏 / 编码
def test_bad_yaml_gives_chinese_error_with_line(tmp_path):
    from voicetwin.config import ConfigError, load_config

    p = tmp_path / "config.yaml"
    p.write_text("backend: gptsovits\nsynth:\n  quality: best\n    speed: 1.0\n", encoding="utf-8")
    with pytest.raises(ConfigError) as ei:
        load_config(str(p))
    msg = str(ei.value)
    assert "第 4 行" in msg and "格式不对" in msg and "config.yaml.bak" in msg


def test_non_mapping_yaml_is_rejected(tmp_path):
    from voicetwin.config import ConfigError, load_config

    p = tmp_path / "config.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(str(p))


def test_gbk_and_bom_config_load(tmp_path):
    from voicetwin.config import load_config

    p = tmp_path / "config.yaml"
    p.write_bytes("# 我的设置\nworkspace: ./工作区\n".encode("gbk"))
    assert load_config(str(p))["workspace"] == "./工作区"
    p.write_bytes("﻿# 设置\nbackend: indextts\n".encode("utf-8"))
    assert load_config(str(p))["backend"] == "indextts"


def test_cli_bad_config_prints_chinese(tmp_path, monkeypatch, capsys):
    from voicetwin.cli import main

    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.yaml").write_text("synth:\n  quality: best\n    speed: 1\n", encoding="utf-8")
    with pytest.raises(SystemExit) as ei:
        main(["list"])
    assert ei.value.code == 1
    err = capsys.readouterr().err
    assert "格式不对" in err and "第 3 行" in err


# ---------------------------------------------------------------------------- 环境检查
ROWS = [
    {"item": "Python", "status": "✅", "detail": "3.9"},
    {"item": "funasr（中文识别，可选）", "status": "⚠️", "detail": "未安装", "optional": True},
    {"item": "NVIDIA 显卡", "status": "❌", "detail": "驱动没有正常工作"},
    {"item": "gradio（网页界面）", "status": "⚠️", "detail": "未安装"},
    {"item": "ffmpeg", "status": "✅", "detail": "ok"},
]


def test_doctor_summary_and_order(capsys):
    from voicetwin.cli import _doctor_summary, _print_doctor

    summary = _doctor_summary(ROWS)
    assert summary.startswith("环境检查结果（共 5 项）：❌ 1 项需要处理，⚠️ 1 项需要注意，✅ 2 项正常")
    assert "另有 1 个可选组件没装，不影响使用" in summary
    code = _print_doctor(ROWS)
    assert code == 2
    out = capsys.readouterr().out
    assert "· 可选，不用管" in out
    assert " 1. ✅ Python" in out  # 编号从 1 开始
    ok_rows = [r for r in ROWS if r["status"] == "✅"]
    assert _doctor_summary(ok_rows) == "环境检查结果（共 2 项）：✅ 2 项全部正常"
    assert _print_doctor(ok_rows) == 0


def test_doctor_rows_sorted_without_wf_helper():
    import types

    from voicetwin.cli import _doctor_rows

    fake_wf = types.SimpleNamespace(doctor=lambda cfg: list(ROWS))
    rows = _doctor_rows(fake_wf, {})
    assert [r["status"] for r in rows][:3] == ["❌", "⚠️", "✅"]
    assert rows[-1].get("optional") is True
    sorted_by_wf = types.SimpleNamespace(doctor=lambda cfg: list(ROWS), sort_doctor_rows=lambda rows: rows[::-1])
    assert _doctor_rows(sorted_by_wf, {}) == ROWS[::-1]


def test_cli_doctor_exit_code(monkeypatch, tmp_path, capsys):
    from voicetwin import workflows as wf
    from voicetwin.cli import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(wf, "doctor", lambda cfg: list(ROWS))
    with pytest.raises(SystemExit) as ei:
        main(["doctor"])
    assert ei.value.code == 2
    assert capsys.readouterr().out.startswith("环境检查结果")
    monkeypatch.setattr(wf, "doctor", lambda cfg: [ROWS[0]])
    main(["doctor"])  # 没有 ❌：正常结束（退出码 0）


def test_cli_list_numbered(monkeypatch, tmp_path, capsys):
    from voicetwin import workflows as wf
    from voicetwin.cli import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(wf, "list_voices", lambda cfg: [
        {"voice": "甲", "minutes": 12.5, "clips": 200, "trained": ["gptsovits"]},
        {"voice": "乙", "minutes": None, "clips": None, "trained": []},
    ])
    monkeypatch.delattr(wf, "voice_library", raising=False)
    main(["list"])
    out = capsys.readouterr().out
    assert "共 2 个声音" in out and " 1. 甲" in out and " 2. 乙" in out and "还没训练" in out


# ---------------------------------------------------------------------------- 下载模型 --check
def _gsv_config(tmp_path, root):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(f"workspace: {json.dumps(str(tmp_path / 'ws'))}\nbackend: gptsovits\n"
                   f"backends:\n  gptsovits:\n    root: {json.dumps(str(root))}\n", encoding="utf-8")
    return cfg


def test_download_models_check_exit_codes(tmp_path, monkeypatch, capsys):
    from voicetwin.backends import gptsovits as g
    from voicetwin.cli import main

    root = tmp_path / "GSV"
    root.mkdir()
    (root / "api_v2.py").write_text("", encoding="utf-8")
    cfg = _gsv_config(tmp_path, root)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as ei:
        main(["-c", str(cfg), "download-models", "--check"])
    assert ei.value.code == 3
    out = capsys.readouterr().out
    assert "缺少" in out and " 1. " in out
    assert not (tmp_path / "ws" / "__download__").exists()  # 临时项目已清理
    # 只下了一半（权重只有 1 字节、文件夹里只有 config.json）：仍然算缺少
    for rel in (g.BERT_DIR, g.HUBERT_DIR):
        (root / rel).mkdir(parents=True, exist_ok=True)
        (root / rel / "config.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as ei:
        main(["-c", str(cfg), "download-models", "--check"])
    assert ei.value.code == 3
    capsys.readouterr()
    # 补齐所有模型后：退出码 0
    from fake_gptsovits import build_fake_root

    build_fake_root(root)
    main(["-c", str(cfg), "download-models", "--check"])
    assert "齐全" in capsys.readouterr().out


def test_download_models_check_missing_root(tmp_path, monkeypatch, capsys):
    from voicetwin.cli import main

    cfg = _gsv_config(tmp_path, tmp_path / "不存在")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as ei:
        main(["-c", str(cfg), "download-models", "--check"])
    assert ei.value.code == 1
    assert "找不到 GPT-SoVITS 整合包" in capsys.readouterr().err


# ---------------------------------------------------------------------------- 命令行进度
class _Lines(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


@pytest.fixture
def log_lines():
    h = _Lines()
    logger = logging.getLogger("voicetwin")
    logger.addHandler(h)
    yield h.lines
    logger.removeHandler(h)


def test_console_progress_throttles():
    from voicetwin.cli import _ConsoleProgress

    now = [0.0]
    lines = []
    p = _ConsoleProgress("准备素材", lines.append, clock=lambda: now[0])
    for i in range(101):
        now[0] = i * 0.1
        p(i / 100, f"第 {i} 段\r")
    assert 18 <= len(lines) <= 22  # 大约每 5% 一行
    assert all(line.startswith("⏳") and "\r" not in line for line in lines)
    n = len(lines)
    p(0.5, "倒退的进度不会让百分比变小")
    now[0] = 100.0
    p(1.0, "很久以后")  # 超过 30 秒：即使百分比没变也打印一行
    assert len(lines) == n + 1 and lines[-1].startswith("⏳ 100%")
    p.finish(True)
    assert lines[-1].startswith("✅ 准备素材完成")
    p("bad", "不会出错")  # type: ignore[arg-type]


def test_cli_progress_prints_lines(log_lines, tmp_path):
    from voicetwin.cli import _cli_progress

    from conftest import make_cfg  # noqa: E402

    progress = _cli_progress("prepare", make_cfg(tmp_path / "ws"), "准备素材")
    for i in range(0, 101, 10):
        progress(i / 100, f"处理第 {i} 段")
    progress.finish(True)
    prog = [line for line in log_lines if line.startswith("⏳")]
    assert prog and all("\r" not in line for line in prog)
    assert any(line.startswith("✅") for line in log_lines)


def test_cli_prepare_prints_progress(lecture_dir, tmp_path, monkeypatch, log_lines, capsys):
    from voicetwin.cli import main

    cfg = tmp_path / "config.yaml"
    cfg.write_text(f"workspace: {json.dumps(str(tmp_path / 'ws'))}\nbackend: dummy\nspeaker_encoder: mfcc\n"
                   "prepare:\n  asr:\n    engine: none\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    main(["-c", str(cfg), "prepare", "-v", "命令行", "-i", str(lecture_dir)])
    prog = [line for line in log_lines if line.startswith("⏳")]
    assert len(prog) >= 2 and all("\r" not in line for line in prog)
    assert "素材：保留" in capsys.readouterr().out


# ---------------------------------------------------------------------------- --redo 的编号 = 结果表里的 #
def test_cli_redo_numbers_match_report_index(prepared, tmp_path, monkeypatch, capsys):
    from voicetwin.cli import main

    cfg, project, _ = prepared
    conf = tmp_path / "config.yaml"
    conf.write_text(f"workspace: {json.dumps(str(project.root.parent))}\nbackend: dummy\nspeaker_encoder: mfcc\n"
                    "prepare:\n  asr:\n    engine: none\n", encoding="utf-8")
    script = tmp_path / "编号测试.md"
    script.write_text("第一句用来测试编号。\n\n第二句也是测试编号的。\n\n第三句同样用来测试编号。\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    base = ["-c", str(conf), "narrate", "-v", project.voice, str(script), "-q", "fast"]
    main(base + ["-o", str(tmp_path / "a.wav")])
    first = json.loads((tmp_path / "a.report.json").read_text(encoding="utf-8"))["segments"]
    assert [s["index"] for s in first] == list(range(1, len(first) + 1))  # 显示的编号从 1 开始
    assert len(first) >= 3
    # 用户在结果表里看到第 2 句不好 → --redo 2 → 只有 # 为 2 的那句重新生成
    main(base + ["-o", str(tmp_path / "b.wav"), "--redo", "第2句"])
    second = json.loads((tmp_path / "b.report.json").read_text(encoding="utf-8"))["segments"]
    regenerated = [s["index"] for s in second if not s["cached"]]
    assert regenerated == [2]
    capsys.readouterr()


def test_print_narration_redo_hint(capsys):
    import types

    from voicetwin.cli import _print_narration

    res = types.SimpleNamespace(audio_path="a.wav", duration=3.0, srt_path=None, report_path="a.report.json",
                                warnings=["第 2 句：可能漏字", "第 5 句：语速偏快"], flagged=[2, 5])
    _print_narration(res, True)
    out = capsys.readouterr().out
    assert "提示（共 2 条）" in out and " 1. ⚠️ 第 2 句" in out
    assert "加上 --redo 2,5" in out
    res.flagged = []
    _print_narration(res, True)
    assert "--redo" not in capsys.readouterr().out


# ---------------------------------------------------------------------------- 日志不再串到别的声音
def test_logs_do_not_leak_between_voices(tmp_path):
    from voicetwin import workflows as wf
    from voicetwin.utils.log import get_logger

    from conftest import make_cfg  # noqa: E402

    cfg = make_cfg(tmp_path / "ws")
    a = wf.open_project(cfg, "声音甲")
    log = get_logger("test")
    log.info("写给甲的日志")
    b = wf.open_project(cfg, "声音乙")
    log.info("写给乙的日志")
    for h in logging.getLogger("voicetwin").handlers:
        h.flush()
    a_text = (a.logs_dir / "voicetwin.log").read_text(encoding="utf-8")
    b_text = (b.logs_dir / "voicetwin.log").read_text(encoding="utf-8")
    assert "写给甲的日志" in a_text and "写给乙的日志" not in a_text
    assert "写给乙的日志" in b_text
    # 同一个声音的 prepare.log 和 voicetwin.log 都保留
    from voicetwin.utils.log import setup_logging

    setup_logging(log_file=b.logs_dir / "prepare.log")
    log.info("乙的准备日志")
    for h in logging.getLogger("voicetwin").handlers:
        h.flush()
    assert "乙的准备日志" in (b.logs_dir / "voicetwin.log").read_text(encoding="utf-8")
    assert "乙的准备日志" in (b.logs_dir / "prepare.log").read_text(encoding="utf-8")


def test_background_task_keeps_its_own_log(tmp_path):
    """网页里：后台线程在给甲训练，同时页面打开了乙 —— 甲的日志不丢，也不会写进乙的日志。"""
    import threading

    from voicetwin import workflows as wf
    from voicetwin.utils.log import get_logger

    from conftest import make_cfg  # noqa: E402

    cfg = make_cfg(tmp_path / "ws")
    log = get_logger("test")
    opened, release = threading.Event(), threading.Event()
    holder = {}

    def worker():
        holder["a"] = wf.open_project(cfg, "后台甲")
        opened.set()
        release.wait(5)
        log.info("甲的训练日志")

    t = threading.Thread(target=worker)
    t.start()
    assert opened.wait(5)
    b = wf.open_project(cfg, "页面乙")
    log.info("页面乙的日志")
    release.set()
    t.join(5)
    for h in logging.getLogger("voicetwin").handlers:
        h.flush()
    a_text = (holder["a"].logs_dir / "voicetwin.log").read_text(encoding="utf-8")
    b_text = (b.logs_dir / "voicetwin.log").read_text(encoding="utf-8")
    assert "甲的训练日志" in a_text and "页面乙的日志" not in a_text
    assert "页面乙的日志" in b_text and "甲的训练日志" not in b_text


def test_setup_logging_keeps_verbose_level():
    from voicetwin.utils.log import setup_logging

    logger = logging.getLogger("voicetwin")
    old = logger.level
    try:
        setup_logging(logging.DEBUG)
        setup_logging()  # 例如 open_project 里只传 log_file
        assert logger.level == logging.DEBUG
    finally:
        logger.setLevel(old)


def test_print_summary_numbered(capsys):
    from voicetwin.cli import _print_summary

    _print_summary({"voice": "甲", "clips_kept": 90, "clips_total": 100, "minutes_kept": 12.5,
                    "dropped": {"太短": 6, "不是你本人的声音": 4},
                    "skipped_files": [{"file": "坏.mp4", "reason": "读不出声音"}],
                    "warnings": ["可用素材只有 12.5 分钟。"], "transcripts_csv": "t.csv"})
    out = capsys.readouterr().out
    assert "丢弃原因（共 2 种，10 条）" in out and "  1. 太短：6 条" in out and "  2. 不是你本人的声音：4 条" in out
    assert "跳过的文件（共 1 个）" in out and "  1. 坏.mp4：读不出声音" in out
    assert "提示（共 1 条）" in out


# ---------------------------------------------------------------------------- 语速百分比 / 两个版本
def test_speed_percent_options():
    from voicetwin.cli import _speed_arg

    ap = build_parser()
    assert _speed_arg(ap.parse_args(["say", "-v", "x", "你好"])) is None
    assert _speed_arg(ap.parse_args(["say", "-v", "x", "你好", "--speed", "1.1"])) == 1.1
    assert _speed_arg(ap.parse_args(["say", "-v", "x", "你好", "--faster", "20"])) == 1.2
    assert _speed_arg(ap.parse_args(["narrate", "-v", "x", "a.md", "--slower", "15"])) == 0.85
    with pytest.raises(ValueError):
        _speed_arg(ap.parse_args(["say", "-v", "x", "你好", "--slower", "80"]))
    with pytest.raises(SystemExit):  # 不能同时用
        ap.parse_args(["say", "-v", "x", "你好", "--speed", "1.1", "--faster", "10"])


def test_print_narration_variants(capsys):
    import types

    from voicetwin.cli import _print_narration

    res = types.SimpleNamespace(
        audio_path="课.wav", duration=12.0, srt_path="课.srt", report_path="课.report.json", warnings=[], flagged=[],
        variants=[{"name": "未去杂音", "path": "课_未去杂音.wav", "score": 0.912, "recommended": True},
                  {"name": "去杂音", "path": "课_去杂音.wav", "score": 0.905, "recommended": False}])
    _print_narration(res, True)
    out = capsys.readouterr().out
    assert "共 2 个版本" in out
    assert "版本 A：未去杂音" in out and "0.912" in out and "⭐ 推荐" in out
    assert "版本 B：去杂音" in out and out.count("⭐") == 1
