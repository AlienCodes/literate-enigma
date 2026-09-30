"""素材里混入别人的声音（例如学生提问），应当被声纹过滤自动剔除。需要 resemblyzer。"""

import pytest

from voicetwin import workflows as wf

from conftest import make_cfg, make_lecture


def test_other_speaker_is_filtered(tmp_path):
    pytest.importorskip("resemblyzer")
    src = tmp_path / "in"
    make_lecture(src / "本人_第1课.wav", repeats=3, f0=150, seed=1)
    make_lecture(src / "本人_第2课.wav", repeats=2, f0=150, seed=2)
    make_lecture(src / "学生提问.wav", repeats=1, f0=235, seed=3)  # 另一个人
    cfg = make_cfg(tmp_path / "ws", speaker_encoder="resemblyzer")
    summary = wf.run_prepare(cfg, "本人", [str(src)])
    project = wf.open_project(cfg, "本人", must_exist=True)
    recs = project.load_manifest()
    other = [r for r in recs if r["source"].startswith("学生提问")]
    mine = [r for r in recs if r["source"].startswith("本人")]
    assert other and all(not r["keep"] for r in other), [r.get("speaker_sim") for r in other]
    assert sum(r["keep"] for r in mine) >= 0.9 * len(mine)
    assert "声音不像本人（可能是别人说话）" in summary["dropped"]
