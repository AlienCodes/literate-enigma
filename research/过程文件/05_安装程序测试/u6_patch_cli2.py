from pathlib import Path

p = Path("<仓库>/.claude/worktrees/wf_08725f86-d54-6/voicetwin/cli.py")
s = p.read_text(encoding="utf-8")

rep = [
(
'''        p.add_argument("--speed", type=float, help="语速倍数（默认 1.0 = 和你本人一样）")
''',
'''        speed_group = p.add_mutually_exclusive_group()
        speed_group.add_argument("--speed", type=float, help="语速倍数（默认 1.0 = 和你本人一样；1.2 = 快 20%%）")
        speed_group.add_argument("--faster", type=float, metavar="百分比", help="比你原声快多少（例如 --faster 20 = 快 20%%）")
        speed_group.add_argument("--slower", type=float, metavar="百分比", help="比你原声慢多少（例如 --slower 15 = 慢 15%%）")
'''),
(
'''                                 quality=args.quality, candidates=args.candidates, speed=args.speed, reference=args.ref,
''',
'''                                 quality=args.quality, candidates=args.candidates, speed=_speed_arg(args),
                                 reference=args.ref,
'''),
(
'''def _print_narration(res: Any, is_narrate: bool) -> None:
    print(f"\\n✅ 音频：{res.audio_path}（{res.duration:.1f} 秒）")
    if res.srt_path:
        print(f"   字幕：{res.srt_path}")
    print(f"   报告：{res.report_path}")
''',
'''SPEED_PERCENT_MAX = 50.0


def _speed_arg(args: Any) -> Optional[float]:
    """--speed 倍数，或者 --faster / --slower 百分比（快 20% = 1.20 倍，慢 15% = 0.85 倍）。"""
    faster = getattr(args, "faster", None)
    slower = getattr(args, "slower", None)
    if faster is None and slower is None:
        return getattr(args, "speed", None)
    pct = float(faster if faster is not None else slower)
    if not 0 <= pct <= SPEED_PERCENT_MAX:
        raise ValueError(f"语速百分比要在 0 到 {SPEED_PERCENT_MAX:g} 之间（建议不超过 15，太极端会不自然），"
                         f"例如 --faster 10 或 --slower 15")
    return round(1.0 + pct / 100.0 if faster is not None else 1.0 - pct / 100.0, 4)


def _variant_score_text(v: Dict[str, Any]) -> str:
    for key in ("pct", "percent", "similarity_pct"):
        if isinstance(v.get(key), (int, float)):
            return f"像你本人 {float(v[key]):.1f}%"
    score = v.get("score")
    if isinstance(score, (int, float)):
        return f"相似度 {float(score):.1f}%" if score > 1.0 else f"相似度 {float(score):.3f}"
    return ""


def _print_narration(res: Any, is_narrate: bool) -> None:
    print(f"\\n✅ 音频：{res.audio_path}（{res.duration:.1f} 秒）")
    variants = [v for v in (getattr(res, "variants", None) or []) if isinstance(v, dict)]
    if variants:
        print(f"   共 {len(variants)} 个版本（{res.audio_path} 是现在用的那个）：")
        for i, v in enumerate(variants, 1):
            label = chr(ord("A") + i - 1) if i <= 26 else str(i)
            score = _variant_score_text(v)
            star = "  ⭐ 推荐：更像你的原声" if v.get("recommended") else ""
            print(f"   版本 {label}：{v.get('name', '')}  {v.get('path', '')}" + (f"（{score}）" if score else "") + star)
    if res.srt_path:
        print(f"   字幕：{res.srt_path}")
    print(f"   报告：{res.report_path}")
'''),
]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
p.write_text(s, encoding="utf-8")
print("patched")
