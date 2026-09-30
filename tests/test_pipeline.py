"""端到端：素材准备 → 风格分析 → 挑选/校准 → 合成（用测试引擎，不需要显卡）。"""

import csv
import json

from voicetwin import workflows as wf
from voicetwin.backends.base import get_backend
from voicetwin.synth.engine import Narrator

from conftest import make_cfg


def test_prepare_summary(prepared):
    cfg, project, summary = prepared
    assert summary["clips_kept"] >= 25
    assert set(summary["minutes_by_lang"]) == {"zh", "en"}
    assert summary["val_clips"] >= 1
    refs = project.load_references()
    assert refs and all(3.0 <= r["duration"] <= 10.0 for r in refs)
    assert {r["lang"] for r in refs} == {"zh", "en"}
    assert any(r["kind"] == "question" for r in refs)
    prof = project.load_profile()
    assert 3.5 < prof["rate"]["zh"]["p50"] < 5.5
    assert 130 < prof["pitch"]["zh"]["f0_median"] < 170
    assert 0.3 < prof["pauses"]["sentence"] < 1.2


def test_review_roundtrip(prepared):
    cfg, project, _ = prepared
    rows = list(csv.DictReader(open(project.csv_path, encoding="utf-8-sig")))
    target = next(r for r in rows if r["keep"] == "1" and r["split"] == "train")
    target["keep"] = "0"
    with open(project.csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summary = wf.apply_review(cfg, project.voice)
    assert summary["changed"]["keep"] == 1
    rec = next(r for r in project.load_manifest() if r["id"] == target["id"])
    assert rec["keep"] is False and rec["manual_keep"] is False
    # 再次运行过滤也不会把手动删除的片段恢复
    wf.apply_review(cfg, project.voice)
    rec = next(r for r in project.load_manifest() if r["id"] == target["id"])
    assert rec["keep"] is False


def test_incremental_prepare_skips_done_sources(prepared, lecture_dir):
    cfg, project, summary = prepared
    again = wf.run_prepare(cfg, project.voice, [str(lecture_dir)])
    assert again["clips_total"] == summary["clips_total"]


def test_select_calibrates_speed(prepared, tmp_path):
    cfg, project, _ = prepared
    slow = make_cfg(project.root.parent, backends={"dummy": {"rate": 4.0}})
    backend = get_backend("dummy", slow, project)
    from voicetwin.synth.select import select_and_calibrate

    with backend:
        info = select_and_calibrate(slow, project, backend, use_asr=False)
    assert info["speed"]["zh"] > 1.05  # 模型比本人慢 → 校准为加速
    project.update_models("dummy", {"speed": {}})


def test_narrate_cache_redo_srt(prepared, tmp_path):
    cfg, project, _ = prepared
    backend = get_backend("dummy", cfg, project)
    script = "# 标题\n\n大家好，今天我们学习函数。函数可以重复使用！\n\n你们明白了吗？[停顿=1.2]Let's continue with an example."
    with backend:
        r1 = Narrator(cfg, project, backend, quality="balanced").narrate(script, tmp_path / "a.wav")
        r2 = Narrator(cfg, project, backend, quality="balanced").narrate(script, tmp_path / "b.wav", redo=[2])
    assert r1.audio_path.exists() and r1.srt_path.exists()
    assert not any(s["cached"] for s in r1.segments)
    assert [s["cached"] for s in r2.segments] == [i != 1 for i in range(len(r2.segments))]
    srt = r1.srt_path.read_text(encoding="utf-8")
    assert "你们明白了吗？" in srt and "-->" in srt
    report = json.loads(r1.report_path.read_text(encoding="utf-8"))
    assert report["mean_speaker_sim"] is not None
    # 明确的 1.2 秒停顿
    seg = {s["text"]: s for s in r1.segments}
    q = seg["你们明白了吗？"]
    nxt = r1.segments[r1.segments.index(q) + 1]
    assert abs((nxt["start"] - q["end"]) - 1.2) < 0.02


def test_srt_timed_narration(prepared, tmp_path):
    cfg, project, _ = prepared
    srt = tmp_path / "timeline.srt"
    srt.write_text("1\n00:00:01,000 --> 00:00:03,000\n第一句话在一秒开始。\n\n"
                   "2\n00:00:08,000 --> 00:00:10,000\n第二句在八秒开始。\n", encoding="utf-8")
    res = wf.run_narrate(cfg, project.voice, str(srt), out=str(tmp_path / "t.wav"), quality="fast")
    starts = [s["start"] for s in res.segments]
    assert abs(starts[0] - 1.0) < 1e-3 and abs(starts[1] - 8.0) < 1e-3


def test_mp3_output(prepared, tmp_path):
    cfg, project, _ = prepared
    res = wf.run_narrate(cfg, project.voice, "测试一下输出 mp3 格式。", out=str(tmp_path / "x.mp3"), quality="fast")
    assert res.audio_path.suffix == ".mp3" and res.audio_path.exists()
