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
