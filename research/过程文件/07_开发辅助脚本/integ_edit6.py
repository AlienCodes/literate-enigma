from pathlib import Path

W = Path('<仓库>/.claude/worktrees/wf_08725f86-d54-11')


def patch(rel, pairs):
    p = W / rel
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        assert s.count(old) == 1, (rel, old[:80], s.count(old))
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')


patch('tests/test_gptsovits_fake.py', [
    ('''    assert u["sovits_save_every"] == "auto" and u["gpt_save_every"] == "auto" and u["if_dpo"] is None
    u = b._user_settings({"sovits_save_every": 4''',
     '''    # default_config.yaml 写的是 if_dpo: auto（和没写一样，都是自动）
    assert u["sovits_save_every"] == "auto" and u["gpt_save_every"] == "auto" and u["if_dpo"] in (None, "auto")
    u = b._user_settings({"sovits_save_every": 4'''),
])
patch('tests/test_webui_helpers.py', [
    ('''    # 没生成过也没上传：提示先生成
    cfg2, name2 = _copy_voice(prepared, tmp_path / "b")
    out = list(A.WebUI(cfg2).do_verify(name2, None, None, {}))''',
     '''    # 没生成过也没上传：提示先生成（共享的 prepared 可能已经被别的测试生成过音频，副本里删掉）
    cfg2, name2 = _copy_voice(prepared, tmp_path / "b")
    shutil.rmtree(wf.Project(cfg2, name2).outputs_dir, ignore_errors=True)
    out = list(A.WebUI(cfg2).do_verify(name2, None, None, {}))'''),
])
print("ok")
