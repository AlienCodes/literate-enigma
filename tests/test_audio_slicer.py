import numpy as np

from voicetwin.data.slicer import find_segments
from voicetwin.data.subtitles import group_cues, parse_subtitle_text
from voicetwin.utils.audio import measure_lufs, normalize_lufs, resample, speech_activity, trim_silence


def _burst(d, sr):
    t = np.arange(int(d * sr)) / sr
    return (0.3 * np.sin(2 * np.pi * 200 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t))).astype(np.float32)


def _signal(seq, sr=16000):
    parts = [(_burst(d, sr) if k == "b" else np.zeros(int(d * sr), np.float32)) for k, d in seq]
    wav = np.concatenate(parts)
    return wav + np.random.default_rng(0).normal(0, 0.001, len(wav)).astype(np.float32)


def test_slicer_boundaries_and_gaps():
    sr = 16000
    wav = _signal([("s", .5), ("b", 3.0), ("s", 1.0), ("b", 4.0), ("s", .8), ("b", 3.5), ("s", .5)], sr)
    segs = find_segments(wav, sr, min_duration=2.0, max_duration=12.0)
    assert len(segs) == 3
    assert abs(segs[0].gap_after - 1.0) < 0.1
    assert segs[0].gap_before is None and segs[-1].gap_after is None
    for s in segs:
        assert 2.0 <= s.duration(sr) <= 12.0


def test_slicer_splits_long_regions():
    sr = 16000
    wav = _signal([("s", .5), ("b", 30.0), ("s", .5)], sr)
    segs = find_segments(wav, sr, max_duration=12.0)
    assert len(segs) >= 3
    assert all(s.duration(sr) <= 12.5 for s in segs)
    assert any(s.forced_cuts for s in segs)


def test_speech_activity_measures_pauses():
    sr = 16000
    wav = _signal([("s", .3), ("b", 1.0), ("s", .5), ("b", 1.0), ("s", .3)], sr)
    voiced, pauses = speech_activity(wav, sr)
    assert abs(voiced - 2.0) < 0.15
    assert len(pauses) == 1 and abs(pauses[0] - 0.5) < 0.1


def test_trim_resample_loudness():
    sr = 16000
    wav = _signal([("s", 1.0), ("b", 1.0), ("s", 1.0)], sr)
    trimmed, a, b = trim_silence(wav, sr, pad_ms=50)
    assert 1.0 <= len(trimmed) / sr <= 1.2
    assert len(resample(wav, sr, 24000)) == int(len(wav) * 1.5)
    norm = normalize_lufs(wav, sr, -20.0)
    assert abs(measure_lufs(norm, sr) + 20.0) < 1.0


def test_subtitle_parse_and_group():
    raw = ("1\n00:00:00,500 --> 00:00:02,000\n第一句，\n\n2\n00:00:02,100 --> 00:00:04,000\n接着说完。\n\n"
           "3\n00:00:06,000 --> 00:00:08,000\n<i>Second</i> sentence.\n")
    cues = parse_subtitle_text(raw)
    assert [c.text for c in cues] == ["第一句，", "接着说完。", "Second sentence."]
    groups = group_cues(cues, min_duration=3.0, max_duration=12.0)
    assert len(groups) == 2
    assert groups[0].text == "第一句，接着说完。"
    assert abs(groups[0].gap_after - 2.0) < 1e-6
