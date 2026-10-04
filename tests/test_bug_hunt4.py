"""第四轮全面找 bug 找到的问题，每个一个测试（在修复以前的代码上都失败）。记录：research/全面找bug/第四轮/。"""

import os
import shutil
import sys
import textwrap
import threading
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from voicetwin import workflows as wf
from voicetwin.data import review


# ============================================================================ g4：素材准备（切片、字幕、降噪、参考音频）
def _cfg(tmp_path, **extra):
    from conftest import make_cfg

    return make_cfg(tmp_path / "ws", **extra)


def _lecture_copy(lecture_dir, dest):
    shutil.copytree(lecture_dir, dest)
    return dest


def _rows(cfg, voice):
    return wf.open_project(cfg, voice, must_exist=True).load_manifest()


def _copy_voice(prepared, tmp_path):
    from conftest import make_cfg

    cfg, project, _ = prepared
    ws = tmp_path / "ws"
    shutil.copytree(project.root, ws / project.voice)
    models = ws / project.voice / "models.json"
    if models.exists():
        models.unlink()
    cfg2 = make_cfg(ws)
    return cfg2, project.voice, wf.open_project(cfg2, project.voice, must_exist=True)


# ---------------------------------------------------------------------------- pipeline#2 同一个视频一次处理两遍
def test_same_video_uploaded_and_in_folder_is_cut_once(prepared, tmp_path, lecture_dir):
    """网页上传了 第1课.mp4，旁边又填了它所在的文件夹（或者文件夹里有备份 / 「副本」）：以前同一次准备里切两遍，
    每句话训练两次（还可能一份当训练、一份当考试）。现在只处理一次，留有同名字幕的那一份。"""
    n_single = len(prepared[1].load_manifest())
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    up = wf.Project(cfg, "重复").root / "uploads"
    up.mkdir(parents=True)
    shutil.copyfile(folder / "第1课.wav", up / "第1课.wav")  # 上传的只有视频，没有字幕
    res = wf.run_prepare(cfg, "重复", [str(up), str(folder)])
    rows = _rows(cfg, "重复")
    assert len(rows) == n_single and len({r["source"] for r in rows}) == 1
    assert all(Path(r["source_file"]).parent == folder.resolve() for r in rows)  # 用的是有字幕的那一份
    assert all(r["text"] for r in rows)
    assert any("只处理了一次" in w for w in res["warnings"])

    # 文件夹里有备份、Windows 的「副本」（名字不一样，内容一样）
    cfg2 = _cfg(tmp_path / "b")
    top = tmp_path / "备份的文件夹"
    _lecture_copy(lecture_dir, top / "上学期")
    (top / "备份").mkdir()
    for ext in (".wav", ".srt"):
        shutil.copyfile(top / "上学期" / f"第1课{ext}", top / "备份" / f"第1课 - 副本{ext}")
    res2 = wf.run_prepare(cfg2, "备份", [str(top)])
    rows2 = _rows(cfg2, "备份")
    assert len(rows2) == n_single and res2["files_new"] == 1 and res2["files_total"] == 2


# ---------------------------------------------------------------------------- pipeline#3 / synth#2 字幕编码
SRT_TEXT = ("1\n00:00:00,500 --> 00:00:02,000\n大家好，今天我们学习函数。\n\n"
            "2\n00:00:02,500 --> 00:00:04,000\n先看一个例子：The book is mine.\n")


@pytest.mark.parametrize("enc", ["gbk", "utf-16", "utf-16-le", "utf-8-sig", "utf-8"])
def test_subtitles_saved_as_ansi_or_unicode_are_read(tmp_path, enc):
    """记事本另存为 ANSI（GBK）/「Unicode」（UTF-16）的字幕：以前中文全变成乱码（训练文字是乱码），UTF-16 一条都读不出。
    第③步上传的字幕（按字幕时间生成）也一样。"""
    from voicetwin.data.subtitles import parse_subtitles
    from voicetwin.synth.script import read_script_file

    p = tmp_path / "第1课.srt"
    p.write_bytes(SRT_TEXT.replace("\n", "\r\n").encode(enc))
    want = ["大家好，今天我们学习函数。", "先看一个例子：The book is mine."]
    assert [c.text for c in parse_subtitles(p)] == want
    assert [c.text for c in read_script_file(p)[1]] == want


def test_utf8_subtitle_with_one_broken_byte_is_still_read_as_utf8(tmp_path):
    """UTF-8 的字幕里坏了一个字节（复制时断了）：照 UTF-8 读，只坏那一个字；不能整个当成 GBK 读成乱码。"""
    from voicetwin.data.subtitles import parse_subtitles

    raw = SRT_TEXT.encode("utf-8")
    cut = raw.index("函数".encode("utf-8"))
    p = tmp_path / "a.srt"
    p.write_bytes(raw[:cut] + raw[cut + 1:])  # 「函」的第一个字节没了
    texts = [c.text for c in parse_subtitles(p)]
    assert texts[0].startswith("大家好，今天我们学习") and texts[1] == "先看一个例子：The book is mine."


def test_gbk_sidecar_subtitle_keeps_all_material(prepared, tmp_path, lecture_dir):
    """视频旁边的同名字幕是 GBK：以前中文句子全是乱码、被当成「疑似识别错误」丢掉，只剩英文句子。"""
    base = prepared[1].load_manifest()
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    srt = folder / "第1课.srt"
    srt.write_bytes(srt.read_text(encoding="utf-8").encode("gbk"))
    wf.run_prepare(cfg, "gbk", [str(folder)])
    rows = _rows(cfg, "gbk")
    assert sorted(r["text"] for r in rows) == sorted(r["text"] for r in base)
    assert sum(1 for r in rows if r["keep"]) == sum(1 for r in base if r["keep"])


def test_unreadable_sidecar_falls_back_to_silence_slicing(tmp_path, lecture_dir):
    """同名字幕读不出一条（不是字幕文件、坏了）：以前这个视频一段都切不出来，还记成处理过（以后也不再处理）。
    现在说明原因，改用按停顿切 + 语音识别。"""
    import logging

    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    (folder / "第1课.srt").write_bytes(b"\x00\x01\x02 not a subtitle \xff\xfe\x00" * 50)
    msgs = []

    class H(logging.Handler):
        def emit(self, record):
            msgs.append(record.getMessage())

    h = H(level=logging.WARNING)
    logging.getLogger("voicetwin").addHandler(h)
    try:
        wf.run_prepare(cfg, "坏字幕", [str(folder)])
    finally:
        logging.getLogger("voicetwin").removeHandler(h)
    rows = _rows(cfg, "坏字幕")
    assert len(rows) >= 5 and all(r["seg_mode"] == "energy" for r in rows)
    assert any("字幕" in m and "静音切分" in m for m in msgs)


def test_file_without_any_speech_is_reported(tmp_path, lecture_dir):
    """没录上声音的视频（整段静音）：以前「处理完了」，一段都没有也什么都不说。"""
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    sf.write(str(folder / "第2课.wav"), np.zeros(44100 * 20, np.float32), 44100)
    res = wf.run_prepare(cfg, "静音", [str(folder)])
    assert any("第2课.wav" in w and "没有找到" in w for w in res["warnings"])


def test_english_utf8_subtitle_with_one_broken_byte_stays_english(tmp_path):
    """英文字幕（UTF-8）里坏了一个字节：不是英文字母的只有几个弯引号 ’，坏一个就占两三成，第一次修的时候整个当成 GBK 读，
    读出「we鈥ll」「It鈥檚」「don鈥檛」：英文训练文字里冒出汉字，后面的 s、t 也被吃掉。现在照 UTF-8 读，只坏那一个字。"""
    from voicetwin.data.subtitles import parse_subtitles

    lines = ["Today we’ll look at relative clauses.", "It’s used for things that don’t have a finished time.",
             "Let’s see an example: The book is mine."]
    srt = "".join(f"{k}\n00:00:0{2 * k},000 --> 00:00:0{2 * k + 1},500\n{t}\n\n" for k, t in enumerate(lines, 1))
    raw = srt.encode("utf-8")
    cut = raw.index("’".encode("utf-8")) + 2
    p = tmp_path / "Lesson 1.srt"
    p.write_bytes(raw[:cut] + raw[cut + 1:])  # 第一个 ’ 的最后一个字节没了
    texts = [c.text for c in parse_subtitles(p)]
    assert not any("一" <= ch <= "鿿" for t in texts for ch in t), texts
    assert texts[1:] == lines[1:]
    assert texts[0].startswith("Today we") and texts[0].endswith("ll look at relative clauses.")


def _shift_srt_hours(text):
    """字幕时间都往后挪一个小时（像是另一个视频的字幕，和这个视频对不上）。"""
    import re

    return re.sub(r"(?m)(^|--> )00:", r"\g<1>01:", text)


def test_zero_clip_video_is_prepared_again_after_fixing_subtitle(prepared, tmp_path, lecture_dir):
    """同名字幕是另一个视频的（时间对不上），一段也没切出来：以前记成「处理过」，老师把字幕换成对的再准备，还是 0 段、
    什么都不说（改名字也没用，改了名字也认得出是同一个视频）。现在换了字幕就重新处理；没换就再提醒一次怎么办。"""
    n_single = len(prepared[1].load_manifest())
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    srt = folder / "第1课.srt"
    good = srt.read_text(encoding="utf-8")
    srt.write_text(_shift_srt_hours(good), encoding="utf-8")
    res = wf.run_prepare(cfg, "对不上", [str(folder)])
    assert len(_rows(cfg, "对不上")) == 0
    assert any("第1课.wav" in w and "字幕换成对的" in w for w in res["warnings"])

    res = wf.run_prepare(cfg, "对不上", [str(folder)])  # 什么都没换：不再处理，但要说清楚为什么、怎么办
    assert res["files_new"] == 0 and len(_rows(cfg, "对不上")) == 0
    assert any("第1课.wav" in w and "以前处理过" in w and "字幕换成对的" in w for w in res["warnings"])

    srt.write_text(good, encoding="utf-8")  # 换成对的字幕
    res = wf.run_prepare(cfg, "对不上", [str(folder)])
    rows = _rows(cfg, "对不上")
    assert res["files_new"] == 1 and len(rows) == n_single and all(r["text"] for r in rows)
    res = wf.run_prepare(cfg, "对不上", [str(folder)])  # 切好了以后再准备：不再切一遍
    assert res["files_new"] == 0 and len(_rows(cfg, "对不上")) == n_single


def test_zero_clip_video_left_by_an_older_version_is_prepared_again(prepared, tmp_path, lecture_dir):
    """以前的版本读不了「Unicode」（UTF-16）字幕，这个视频 0 段、记成处理过（sources.json 里没有字幕指纹）：
    修好以后再准备，还是 0 段，改名字也没用。现在这样的记录再处理一次。"""
    from voicetwin.data.prepare import content_key, source_id

    n_single = len(prepared[1].load_manifest())
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    srt = folder / "第1课.srt"
    srt.write_bytes(srt.read_text(encoding="utf-8").encode("utf-16"))
    media = (folder / "第1课.wav").resolve()
    project = wf.Project(cfg, "旧版本")
    project.ensure()
    project.write_json(project.sources_path, {source_id(media): {  # 以前的版本写的样子
        "file": str(media), "key": content_key(media), "clean": "raw/x.wav", "segments": 0, "speech_seconds": 0.0,
        "done": True}})
    res = wf.run_prepare(cfg, "旧版本", [str(folder)])
    rows = _rows(cfg, "旧版本")
    assert res["files_new"] == 1 and len(rows) == n_single and all(r["text"] for r in rows)


# ---------------------------------------------------------------------------- pipeline#4 改了名字的视频
def test_renamed_video_is_not_cut_again(tmp_path, lecture_dir):
    """处理过的 0006.mp4 改名成「第6课 定语从句.mp4」（或者重新下载成「0006 (1).mp4」再上传）：以前当成新视频再切一遍，
    同一段话训练两次（新的一份还是没改过的错字）。"""
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    wf.run_prepare(cfg, "改名", [str(folder)])
    n = len(_rows(cfg, "改名"))
    for ext in (".wav", ".srt"):
        (folder / f"第1课{ext}").rename(folder / f"第6课 定语从句{ext}")
    res = wf.run_prepare(cfg, "改名", [str(folder)])
    assert res["files_new"] == 0 and len(_rows(cfg, "改名")) == n


# ---------------------------------------------------------------------------- pipeline#5 改好的文字还被旧的识别置信度挡住
def test_corrected_low_confidence_clip_is_used_for_training(prepared, tmp_path):
    """语音识别没把握（置信度低 / 可能不是语音）的句子，老师把文字改对、保存以后：以前还按旧文字的置信度丢掉，
    表格里灰色、不写原因，不用来训练。改回原来识别的字，旧的置信度又算数。"""
    cfg, v, project = _copy_voice(prepared, tmp_path)
    recs = project.load_manifest()
    right_a, right_b = "首先我们看一个最简单的例子。", "区别在于我们需要同时给出键和值。"
    wrong_a, wrong_b = "首先我们看一个最简单的栗子。", "区别在于我们需要同时给出建和值。"
    a = next(r for r in recs if r["text"] == right_a and r["keep"])
    b = next(r for r in recs if r["text"] == right_b and r["keep"])
    a.update(text=wrong_a, asr={"engine": "faster-whisper", "avg_logprob": -1.35, "no_speech_prob": 0.1})
    b.update(text=wrong_b, asr={"engine": "faster-whisper", "avg_logprob": -0.3, "no_speech_prob": 0.75})
    project.save_manifest(recs)
    wf.apply_review(cfg, v, read_csv=False)
    got = {r["id"]: r for r in project.load_manifest()}
    assert got[a["id"]]["drop_reason"] == "识别置信度低" and got[b["id"]]["drop_reason"] == "可能不是语音"

    review.set_draft(project, a["id"], text=right_a)
    review.set_draft(project, b["id"], text=right_b)
    wf.review_save(cfg, v)
    got = {r["id"]: r for r in project.load_manifest()}
    assert got[a["id"]]["keep"] and got[a["id"]]["drop_reason"] == ""
    assert got[b["id"]]["keep"] and got[b["id"]]["drop_reason"] == ""

    review.set_draft(project, a["id"], text=wrong_a)  # 改回识别出来的字
    wf.review_save(cfg, v)
    assert {r["id"]: r for r in project.load_manifest()}[a["id"]]["drop_reason"] == "识别置信度低"


def test_text_corrected_in_v18_without_orig_text_is_used_for_training(prepared, tmp_path):
    """v18 改过的文字只记了 text_edited、没有 orig_text（orig_text 是后来才加的）：第一次修的时候把没有 orig_text 当成
    「没改过」，老师在 v18 改对的句子还按旧文字的识别置信度丢掉。以前的版本只有文字真的改了才记 text_edited。"""
    cfg, v, project = _copy_voice(prepared, tmp_path)
    recs = project.load_manifest()
    a = next(r for r in recs if r["text"] == "首先我们看一个最简单的例子。" and r["keep"])
    b = next(r for r in recs if r["text"] == "区别在于我们需要同时给出键和值。" and r["keep"])
    for r, asr in ((a, {"avg_logprob": -1.35, "no_speech_prob": 0.1}), (b, {"avg_logprob": -0.3, "no_speech_prob": 0.75})):
        r.update(text_edited=True, asr={"engine": "faster-whisper", **asr})
        r.pop("orig_text", None)
    project.save_manifest(recs)
    wf.apply_review(cfg, v, read_csv=False)
    got = {r["id"]: r for r in project.load_manifest()}
    assert got[a["id"]]["keep"] and got[a["id"]]["drop_reason"] == ""
    assert got[b["id"]]["keep"] and got[b["id"]]["drop_reason"] == ""


# ---------------------------------------------------------------------------- pipeline#6 爆音过滤永远不起作用
def test_clipped_recording_is_dropped_as_clipping(tmp_path):
    """话筒太近 / 音量开太大录出来的爆音：以前先统一了音量再查爆音（这时已经不可能有满格的样本），一条都查不出来，
    破音的句子都拿去训练。现在在统一音量以前查；保存校对表以后也还在。"""
    from conftest import make_lecture

    src = tmp_path / "in"
    p = make_lecture(src / "爆音.wav", repeats=1)
    wav, sr = sf.read(str(p), dtype="float32")
    sf.write(str(p), np.clip(wav * 3.0, -1.0, 1.0), sr, subtype="PCM_16")  # 约 5% 的样本削顶
    cfg = _cfg(tmp_path)
    res = wf.run_prepare(cfg, "爆音", [str(src)])
    rows = _rows(cfg, "爆音")
    clipped = [r for r in rows if r["drop_reason"] == "有爆音"]
    assert len(clipped) >= 0.8 * len(rows) and res["dropped"].get("有爆音") == len(clipped)
    wf.apply_review(cfg, "爆音", read_csv=False)  # 保存校对表（重新统计）以后照样认得出来
    assert sum(1 for r in _rows(cfg, "爆音") if r["drop_reason"] == "有爆音") == len(clipped)


# ---------------------------------------------------------------------------- pipeline#7 降噪的噪声样本取成了说话声
def _speech_first_lecture(sr, seed=0):
    """开头 20 秒一直在说话（没有停顿），后面每句之间停一下。返回 (干净的声音, 哪些样本是说话)。"""
    from conftest import SENTENCES
    from voicetwin.backends.workers.dummy_worker import synth_speech

    rng = np.random.default_rng(seed)
    parts, mask, t, k = [], [], 0.0, 0
    while t < 20.0:
        w = synth_speech(SENTENCES[k % len(SENTENCES)], sr=sr, seed=k)
        parts.append(w)
        mask.append(np.ones(len(w), bool))
        t += len(w) / sr
        k += 1
    for _ in range(12):
        w = synth_speech(SENTENCES[k % len(SENTENCES)], sr=sr, seed=k)
        k += 1
        z = np.zeros(int(rng.uniform(0.6, 1.2) * sr), np.float32)
        parts += [w, z]
        mask += [np.ones(len(w), bool), np.zeros(len(z), bool)]
    return np.concatenate(parts).astype(np.float32), np.concatenate(mask)


def test_denoise_takes_its_noise_sample_from_pauses(monkeypatch):
    """自动降噪：以前不给噪声样本，noisereduce 拿录音开头 13.6 秒（多半是老师在说话）当「噪声」，把老师的声音削掉一块。
    现在噪声样本取停顿里最安静的部分。"""
    import types

    from voicetwin.data import enhance

    sr = 16000
    clean, speech = _speech_first_lecture(sr)
    noise = np.random.default_rng(3).normal(0, 0.005, len(clean)).astype(np.float32)
    got = {}

    def fake_reduce(y, sr, y_noise=None, **kw):
        got["y_noise"] = y_noise
        return y

    monkeypatch.setitem(sys.modules, "noisereduce", types.SimpleNamespace(reduce_noise=fake_reduce))
    enhance.denoise(clean + noise, sr, 0.6)
    y_noise = got.get("y_noise")
    assert y_noise is not None and len(y_noise) >= sr  # 至少 1 秒的噪声样本
    rms = float(np.sqrt(np.mean(np.asarray(y_noise, np.float64) ** 2)))
    assert rms < 0.005 * 1.5  # 只有底噪，没有说话声


@pytest.mark.skipif(not __import__("importlib").util.find_spec("noisereduce"), reason="没有装 noisereduce（整合包里有）")
def test_denoise_does_not_cut_the_voice_of_a_lecture_that_starts_with_speech():
    """真的 noisereduce：开头就在说话的讲课录音，降噪以前把说话声削掉约 7 dB（比不降噪还差）；现在不超过 3 dB。"""
    from voicetwin.data.enhance import denoise

    sr = 44100
    clean, speech = _speech_first_lecture(sr)
    noisy = clean + np.random.default_rng(5).normal(0, 0.02, len(clean)).astype(np.float32)
    out = denoise(noisy, sr, 0.6)
    energy = lambda x: float(np.mean(x[speech].astype(np.float64) ** 2))  # noqa: E731
    change = 10 * np.log10(energy(out) / energy(noisy))
    assert change > -3.0, change


# ---------------------------------------------------------------------------- pipeline#8 先记「处理过」、后写校对表
def test_failed_manifest_write_does_not_lose_a_video(tmp_path, monkeypatch):
    """写校对表（manifest）失败（硬盘满了、被同步软件占着超过 3 秒）：以前 sources.json 已经记了「处理过」，
    再点准备素材时这个视频被跳过，它的片段永远不在校对表里。"""
    from conftest import make_lecture
    from voicetwin.project import Project

    src = tmp_path / "in"
    make_lecture(src / "a.wav", repeats=1)
    make_lecture(src / "b.wav", repeats=1, seed=5)
    cfg = _cfg(tmp_path)
    real = Project.save_manifest
    calls = {"n": 0}

    def flaky(self, records):
        calls["n"] += 1
        if calls["n"] == 2:  # 第 2 个视频切完以后写校对表
            raise PermissionError(13, "另一个程序正在使用此文件")
        return real(self, records)

    monkeypatch.setattr(Project, "save_manifest", flaky)
    with pytest.raises(PermissionError):
        wf.run_prepare(cfg, "断电", [str(src)])
    monkeypatch.setattr(Project, "save_manifest", real)
    wf.run_prepare(cfg, "断电", [str(src)])
    per_source = {}
    for r in _rows(cfg, "断电"):
        per_source[Path(r["source_file"]).name] = per_source.get(Path(r["source_file"]).name, 0) + 1
    assert per_source.get("a.wav", 0) > 0 and per_source.get("b.wav", 0) > 0


def test_sources_record_and_manifest_out_of_step_are_repaired(tmp_path, lecture_dir):
    """以前的版本留下的：sources.json 记了「处理过、切出 N 段」，校对表里却一段都没有（上面那个问题）→ 再准备一次就补上。
    反过来：校对表里有、sources.json 没记（写完校对表就断电）→ 不再切一遍（老师改过的字不会被冲掉）。"""
    import json

    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    wf.run_prepare(cfg, "补上", [str(folder)])
    project = wf.open_project(cfg, "补上", must_exist=True)
    rows = project.load_manifest()
    n = len(rows)
    project.save_manifest([])
    wf.run_prepare(cfg, "补上", [str(folder)])
    assert len(project.load_manifest()) == n

    first = project.load_manifest()[0]
    review.set_draft(project, first["id"], text="老师改好的一句话。")
    wf.review_save(cfg, "补上")
    project.sources_path.write_text(json.dumps({}), encoding="utf-8")
    res = wf.run_prepare(cfg, "补上", [str(folder)])
    assert res["files_new"] == 0 and len(project.load_manifest()) == n
    assert {r["id"]: r for r in project.load_manifest()}[first["id"]]["text"] == "老师改好的一句话。"


# ---------------------------------------------------------------------------- pipeline#9 去背景音乐（Demucs）
FAKE_DEMUCS = textwrap.dedent('''
    import os, shutil, sys, time
    args = sys.argv[1:]
    out = args[args.index("-o") + 1]
    src = args[-1]
    mode = os.environ.get("FAKE_DEMUCS_MODE", "ok")
    pid_file = os.environ.get("FAKE_DEMUCS_PID")
    if pid_file:
        open(pid_file, "w").write(str(os.getpid()))
    if mode == "sleep":
        time.sleep(60)
    if mode == "fail":
        print("boom: demucs failed")
        sys.exit(3)
    stem = os.path.splitext(os.path.basename(src))[0]
    d = os.path.join(out, "htdemucs", stem)
    os.makedirs(d, exist_ok=True)
    shutil.copyfile(src, os.path.join(d, "vocals.wav"))
    shutil.copyfile(src, os.path.join(d, "no_vocals.wav"))
''')


@pytest.fixture
def fake_demucs(tmp_path, monkeypatch):
    d = tmp_path / "fake_demucs"
    (d / "demucs").mkdir(parents=True)
    (d / "demucs" / "__init__.py").write_text("", encoding="utf-8")
    (d / "demucs" / "__main__.py").write_text(FAKE_DEMUCS, encoding="utf-8")
    monkeypatch.syspath_prepend(str(d))
    monkeypatch.setenv("PYTHONPATH", str(d) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    yield d
    sys.modules.pop("demucs", None)


def test_stop_ends_demucs_right_away(tmp_path, fake_demucs, monkeypatch):
    """去背景音乐（Demucs，一两个小时的视频要二三十分钟）的时候点「停止」：以前要等 Demucs 做完才停；临时文件夹也留着。"""
    from voicetwin.data import enhance
    from voicetwin.utils import progress
    from voicetwin.utils.progress import TaskCancelled

    pid_file = tmp_path / "pid.txt"
    monkeypatch.setenv("FAKE_DEMUCS_MODE", "sleep")
    monkeypatch.setenv("FAKE_DEMUCS_PID", str(pid_file))
    work = tmp_path / "raw"
    work.mkdir()
    src = work / "a.src.wav"
    sf.write(str(src), np.zeros(16000, np.float32), 16000)
    out = {}

    def run():
        try:
            enhance.separate_vocals(src, work)
        except BaseException as exc:  # noqa: BLE001
            out["exc"] = exc
        out["t"] = time.time()

    th = threading.Thread(target=run)
    th.start()
    for _ in range(200):
        if pid_file.exists() and pid_file.read_text().strip():
            break
        time.sleep(0.05)
    t0 = time.time()
    progress.request_cancel()
    try:
        th.join(15)
    finally:
        progress.clear_cancel()
    assert not th.is_alive()
    assert isinstance(out.get("exc"), TaskCancelled) and out["t"] - t0 < 5
    pid = int(pid_file.read_text())
    with pytest.raises(OSError):
        os.kill(pid, 0)
    assert not list(work.glob("demucs_*"))


def test_separated_vocals_files_are_cleaned_up(tmp_path, lecture_dir, fake_demucs, monkeypatch):
    """勾了「视频有背景音乐」：以前每个视频都在 raw/ 里留下一个和整个视频一样长的 .vocals.wav（两小时约 1 GB）；
    Demucs 出错时 demucs_* 临时文件夹也留着。"""
    cfg = _cfg(tmp_path)
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    wf.run_prepare(cfg, "去音乐", [str(folder)], overrides={"separate_vocals": True})
    project = wf.open_project(cfg, "去音乐", must_exist=True)
    assert project.load_manifest()
    assert not list(project.raw_dir.glob("*.vocals.wav")) and not list(project.raw_dir.glob("demucs_*"))

    monkeypatch.setenv("FAKE_DEMUCS_MODE", "fail")
    from voicetwin.data import enhance

    src = project.raw_dir / "x.src.wav"
    sf.write(str(src), np.zeros(16000, np.float32), 16000)
    with pytest.raises(RuntimeError, match="Demucs 执行失败"):
        enhance.separate_vocals(src, project.raw_dir)
    assert not list(project.raw_dir.glob("demucs_*"))


# ---------------------------------------------------------------------------- pipeline#10 疑问句参考音频
def _clip(path, seconds, sr=16000, seed=0):
    """一段「说话」：前后各 0.4 秒安静。"""
    rng = np.random.default_rng(seed)
    n = int((seconds - 0.8) * sr)
    t = np.arange(n) / sr
    body = (0.3 * np.sin(2 * np.pi * 180 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t))).astype(np.float32)
    pad = np.zeros(int(0.4 * sr), np.float32)
    wav = np.concatenate([pad, body, pad]) + rng.normal(0, 0.0005, n + 2 * len(pad)).astype(np.float32)
    sf.write(str(path), wav, sr)


def test_question_reference_tries_the_next_question(tmp_path):
    """最好的那条疑问句去掉首尾静音后超过 9.8 秒：以前直接放弃，参考音频里没有疑问句（明明还有一条 6 秒的好问句），
    生成的问句只能用陈述句的语气。"""
    from voicetwin.data.references import select_references

    cfg = _cfg(tmp_path)
    project = wf.open_project(cfg, "问句")
    project.clips_dir.mkdir(parents=True, exist_ok=True)
    texts = [("长问句", "这一段代码运行以后输出的结果到底是什么呢大家想一想？", 10.8, 0.99),
             ("短问句", "大家想一想这段代码输出什么？", 6.0, 0.85)]
    texts += [(f"陈述{i}", f"这是第{'甲乙丙丁戊己庚辛'[i]}句完整的陈述句。", 6.0, 0.85) for i in range(8)]
    recs = []
    for i, (name, text, dur, sim) in enumerate(texts):
        path = project.clips_dir / f"c_{i:04d}.wav"
        _clip(path, dur, seed=i)
        recs.append({"id": f"c_{i:04d}", "path": project.relpath(path), "text": text, "lang": "zh", "keep": True,
                     "split": "train", "rate": 4.5, "forced_cuts": 0, "duration": dur, "speaker_sim": sim,
                     "snr": 30.0, "source": f"s{i}", "pauses": []})
    refs = select_references(project, recs, {"references": {"count": 4}})
    kinds = {r["id"]: r["kind"] for r in refs}
    assert kinds.get("c_0001") == "question" and "c_0000" not in kinds
    assert sum(1 for k in kinds.values() if k == "statement") >= 2


# ---------------------------------------------------------------------------- pipeline#11 按停顿切时跨过很长的停顿
def _burst(d, sr):
    t = np.arange(int(d * sr)) / sr
    return (0.3 * np.sin(2 * np.pi * 200 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 4 * t))).astype(np.float32)


def _signal(seq, sr=16000):
    rng = np.random.default_rng(0)
    parts = [(_burst(d, sr) if k == "b" else (rng.normal(0, 10 ** (-55 / 20), int(d * sr))).astype(np.float32))
             for k, d in seq]
    return np.concatenate(parts)


@pytest.mark.parametrize("seq", [
    [("s", .6), ("b", 1.0), ("s", 7.0), ("b", 2.5), ("s", .6)],        # 「好。」——写板书 7 秒——下一句
    [("s", .6), ("b", 5.0), ("s", 4.5), ("b", 1.0), ("s", .6)],        # 一句话——停 4.5 秒——最后一个「好。」
])
def test_slicer_never_glues_a_short_phrase_across_a_long_pause(seq):
    """「好。」说完写板书 7 秒再说下一句：以前切成一段 11 秒、中间有 7 秒底噪的训练片段（模型学会句子中间长时间停顿）。"""
    from voicetwin.data.slicer import find_segments

    sr = 16000
    segs = find_segments(_signal(seq, sr), sr, min_duration=2.0, max_duration=12.0)
    assert segs
    for s in segs:
        assert all(g <= 1.2 for g in s.inner_gaps), s.inner_gaps
        assert s.duration(sr) < 8.0


def test_slicer_change_keeps_ids_of_prepared_material(tmp_path, lecture_dir):
    """改了切法以后再准备一次：以前准备好的片段（编号、文字）一条都不变。"""
    cfg = _cfg(tmp_path, prepare={"asr": {"engine": "none"}, "segmentation": "energy"})
    folder = _lecture_copy(lecture_dir, tmp_path / "讲课")
    wf.run_prepare(cfg, "切法", [str(folder)])
    before = [(r["id"], r["start"], r["end"]) for r in _rows(cfg, "切法")]
    wf.run_prepare(cfg, "切法", [str(folder)])
    assert [(r["id"], r["start"], r["end"]) for r in _rows(cfg, "切法")] == before
