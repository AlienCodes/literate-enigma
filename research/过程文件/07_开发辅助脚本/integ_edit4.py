from pathlib import Path

W = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11')


def patch(rel, pairs):
    p = W / rel
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (rel, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


patch('tests/test_webui_helpers.py', [
    ('''    assert "找不到 GPT-SoVITS" in A._quick_problems(cfg2)[0]''',
     '''    assert any("找不到 GPT-SoVITS" in p for p in A._quick_problems(cfg2))'''),
    ('''def test_choose_variant_fallback_copies(tmp_path, prepared):
    cfg, name = _copy_voice(prepared, tmp_path)
    a, b, final = tmp_path / "x_未去杂音.wav", tmp_path / "x_去杂音.wav", tmp_path / "x.wav"
    a.write_bytes(b"A")
    b.write_bytes(b"B")
    final.write_bytes(b"A")
    report = tmp_path / "x.report.json"
    report.write_text("{}", encoding="utf-8")
    state = {"voice": name, "audio": str(final), "report": str(report),
             "variants": [{"name": "未去杂音", "path": str(a), "score": 0.91, "recommended": True},
                          {"name": "去杂音", "path": str(b), "score": 0.90, "recommended": False}]}
    audio, note = A.WebUI(cfg).on_choose_variant(name, state, "去杂音")
    assert final.read_bytes() == b"B" and audio["value"] == str(b) and "版本 B" in note
    assert json.loads(report.read_text(encoding="utf-8"))["final"] == "去杂音"''',
     '''def test_choose_variant_copies_through_workflow(tmp_path, prepared):
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
    report.write_text(json.dumps({"audio": str(final), "variants": variants, "final": "未去杂音"}, ensure_ascii=False),
                      encoding="utf-8")
    state = {"voice": name, "audio": str(final), "report": str(report), "variants": variants}
    audio, note = A.WebUI(cfg).on_choose_variant(name, state, "去杂音")
    assert final.read_bytes() == b"B" and audio["value"] == str(b) and "版本 B" in note and str(final) in note
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["final"] == "去杂音" and [v["final"] for v in data["variants"]] == [False, True]
    # 没生成过（state 是空的）：只给一句提示，不报错
    audio2, note2 = A.WebUI(cfg).on_choose_variant(name, {}, "去杂音")
    assert _is_update(audio2) and "请先生成一次" in note2'''),
])
print("ok")
