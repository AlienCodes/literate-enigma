from pathlib import Path

W = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11')


def patch(rel, pairs):
    p = W / rel
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (rel, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


patch('voicetwin/workflows.py', [(
    '''            if sel:
                best = str(sel.get("id") or "") + ("" if name == default_backend else f"（{name}）")
                break''',
    '''            if sel:
                best = str(sel.get("id") or "")
                if name != default_backend:  # 不是默认引擎训练的：注明是哪个引擎（用中文界面上的名字）
                    try:
                        label = str(getattr(_backend_class(name), "display_name", name))
                    except Exception:
                        label = name
                    best += f"（{label}）"
                break''')])

patch('tests/test_webui_helpers.py', [
    ('''    assert e["name"] == name and e["status"] == "✅ 已训练，可以生成" and e["best_model"] == "s8-g15"''',
     '''    # 测试配置的默认引擎是 dummy，所以会注明「GPT-SoVITS」；老师的电脑上默认就是 GPT-SoVITS，只显示编号
    assert e["name"] == name and e["status"] == "✅ 已训练，可以生成" and e["best_model"] == "s8-g15（GPT-SoVITS）"'''),
    ('''def test_voice_library_fallback(prepared, tmp_path):''', '''def test_voice_library_entries(prepared, tmp_path):'''),
    ('''    labels = dict((v, k) for k, v in A.QUALITY_CHOICES)
    assert labels["max"] == "极致（最慢，最稳最像，建议显存 ≥ 8GB）"''',
     '''    labels = dict((v, k) for k, v in A.QUALITY_CHOICES)
    assert labels["max"] == "极致（很慢，更稳更像，建议显存 ≥ 8GB）"  # 不写「最慢」：「完美」比它更慢'''),
    ('''    problems = A._quick_problems(cfg)
    assert len(problems) == 1 and "下载缺少的模型" in problems[0]''',
     '''    problems = [p for p in A._quick_problems(cfg) if "ffmpeg" not in p]
    assert len(problems) == 1 and "下载缺少的模型" in problems[0] and "缺少 6 个" in problems[0]'''),
    ('''    assert not (tmp_path / "ws" / "__quick__").exists()''',
     '''    assert not (tmp_path / "ws" / "__quick__").exists() and not (tmp_path / "ws" / "__quick_check__").exists()'''),
    ('''def test_verify_through_task_with_fallback(prepared, tmp_path):''', '''def test_verify_through_task(prepared, tmp_path):'''),
])
print("ok")
