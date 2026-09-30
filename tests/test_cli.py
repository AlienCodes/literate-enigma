from voicetwin.cli import _parse_redo, build_parser


def test_parse_redo():
    assert _parse_redo("3,5，8-10") == [3, 5, 8, 9, 10]
    assert _parse_redo("") == []


def test_parser_commands():
    ap = build_parser()
    args = ap.parse_args(["narrate", "-v", "我的声音", "讲稿.md", "-q", "best", "--redo", "2"])
    assert args.command == "narrate" and args.quality == "best" and args.redo == "2"
    args = ap.parse_args(["prepare", "-v", "x", "-i", "a", "b", "--asr", "funasr"])
    assert args.input == ["a", "b"] and args.asr == "funasr"


def test_init_config_updates_in_place(tmp_path, monkeypatch):
    from voicetwin.cli import main
    from voicetwin.config import load_config

    monkeypatch.chdir(tmp_path)
    main(["init-config", "--backend", "indextts"])
    cfg_path = tmp_path / "config.yaml"
    text = cfg_path.read_text(encoding="utf-8").replace("quality: balanced", "quality: best")
    cfg_path.write_text(text, encoding="utf-8")
    # 再次运行（例如重新运行安装程序）：只更新指定项，保留用户改过的其它设置
    main(["init-config", "--gptsovits-root", str(tmp_path / "GSV"), "--backend", "gptsovits"])
    cfg = load_config(str(cfg_path))
    assert cfg["backend"] == "gptsovits"
    assert cfg.get_path("synth.quality") == "best"
    assert cfg.backend("gptsovits")["root"].endswith("GSV")
    assert (tmp_path / "config.yaml.bak").exists()
    # 不带参数时保持不变
    main(["init-config"])
    assert load_config(str(cfg_path)).get_path("synth.quality") == "best"


def test_verbose_after_subcommand():
    ap = build_parser()
    assert ap.parse_args(["narrate", "-v", "x", "a.md", "--verbose"]).verbose is True
    assert ap.parse_args(["--verbose", "doctor"]).verbose is True
    assert ap.parse_args(["doctor"]).verbose is False
