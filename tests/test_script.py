from voicetwin.synth.script import apply_lexicon, chunk_sentence, parse_script, split_sentences
from voicetwin.utils.textutil import syllable_count


def test_markdown_pauses_and_lexicon():
    md = """# 第一课

大家好。今天我们学习 **SQL** 的基础知识。[停顿=1.5]
```python
print("不应该被朗读")
```
那么，大家明白了吗？

Next, let's look at Dr. Smith's example. The value is 3.14.
"""
    segs = parse_script(md, lexicon=[("SQL", "sequel")])
    texts = [s.text for s in segs]
    assert texts[0] == "第一课。"
    assert segs[0].pause_after == "paragraph"
    assert any("sequel" in t for t in texts)
    assert any("SQL" in s.display for s in segs)
    assert not any("不应该被朗读" in t for t in texts)
    assert any(s.pause_after == 1.5 for s in segs)
    assert any(s.kind == "question" for s in segs)
    assert "Next, let's look at Dr. Smith's example." in texts
    assert segs[-1].pause_after == 0.0


def test_split_sentences_keeps_decimals_and_abbreviations():
    assert split_sentences("Pi is 3.14. Mr. Li said hi. 好的！走吧。") == ["Pi is 3.14.", "Mr. Li said hi.", "好的！", "走吧。"]


def test_long_sentence_is_chunked_at_clauses():
    s = "，".join(["这是一个比较长的分句用来测试"] * 8) + "。"
    chunks = chunk_sentence(s, 50)
    assert len(chunks) > 1
    assert all(syllable_count(c) <= 50 for c in chunks)


def test_short_sentences_are_merged():
    segs = parse_script("好。今天我们要学习一个非常重要的概念。")
    assert len(segs) == 1


def test_lexicon_word_boundary():
    assert apply_lexicon("MySQL and SQL", [("SQL", "sequel")]) == "MySQL and sequel"


def test_srt_script(tmp_path):
    p = tmp_path / "a.srt"
    p.write_text("1\n00:00:01,000 --> 00:00:03,000\n第一句话。\n\n2\n00:00:04,500 --> 00:00:06,000\nSecond line.\n", encoding="utf-8")
    segs = parse_script(p)
    assert [s.cue_start for s in segs] == [1.0, 4.5]


# ============================================================================ 讲稿文件、读音词典、校对表更宽容
import csv  # noqa: E402

import pytest  # noqa: E402

from voicetwin.project import Project  # noqa: E402
from voicetwin.synth.script import UNSUPPORTED_MSG, read_script_file  # noqa: E402


def test_renamed_binary_doc_is_rejected(tmp_path):
    fake = tmp_path / "讲稿.txt"  # 其实是 .doc 改了扩展名
    fake.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 600 + "正文".encode("utf-16-le") + b"\x00\x01" * 300)
    with pytest.raises(RuntimeError, match="另存为"):
        read_script_file(fake)
    for ext in (".doc", ".wps", ".pdf"):
        p = tmp_path / f"讲稿{ext}"
        p.write_bytes(b"%PDF-1.4 whatever")
        with pytest.raises(RuntimeError) as err:
            read_script_file(p)
        assert str(err.value) == UNSUPPORTED_MSG
    with pytest.raises(RuntimeError, match="另存为"):
        parse_script(tmp_path / "讲稿.doc")


def test_text_scripts_still_work(tmp_path):
    gbk = tmp_path / "gbk.txt"
    gbk.write_bytes("大家好，这是记事本存的讲稿。".encode("gbk"))
    assert read_script_file(gbk)[0] == "大家好，这是记事本存的讲稿。"
    u16 = tmp_path / "u16.txt"
    u16.write_bytes("﻿第二份讲稿。".encode("utf-16-le"))
    assert read_script_file(u16)[0].lstrip("﻿") == "第二份讲稿。"
    md = tmp_path / "a.markdown"
    md.write_text("# 标题\n\n内容在这里，句子足够长。", encoding="utf-8")
    assert parse_script(md)


def _project(tmp_path):
    from conftest import make_cfg

    project = Project(make_cfg(tmp_path), "词典测试").ensure()
    return project


@pytest.mark.parametrize("line", ["行长 ＝＞ 航长", "行长＝>航长", "行长 =＞ 航长", "行长 -> 航长", "行长 → 航长",
                                  "行长 ⇒ 航长", "　行长　=>　航长　"])
def test_lexicon_accepts_chinese_ime_arrows(tmp_path, line):
    project = _project(tmp_path)
    project.lexicon_path.write_text("# 注释\n＃ 全角注释 => 不算\n" + line + "\n", encoding="utf-8")
    assert project.load_lexicon() == [("行长", "航长")]


def test_lexicon_saved_as_ansi(tmp_path):
    project = _project(tmp_path)
    project.lexicon_path.write_bytes("重庆 => 虫庆\n".encode("gbk"))
    assert project.load_lexicon() == [("重庆", "虫庆")]


def _manifest(project):
    recs = [{"id": "a", "path": "clips/a.wav", "text": "今天我们讲VFIXED。", "lang": "zh", "keep": True,
             "duration": 3.0, "voiced": 2.0, "suspect": {"spans": [[5, 11]], "alt": "今天我们讲函数。", "reasons": ["x"],
                                                          "score": 0.7}},
            {"id": "b", "path": "clips/b.wav", "text": "第二段。", "lang": "zh", "keep": False, "duration": 3.0,
             "suspect": {"spans": [[0, 1]], "alt": "", "reasons": ["x"], "score": 0.5}},
            {"id": "c", "path": "clips/c.wav", "text": "第三段。", "lang": "zh", "keep": True, "duration": 3.0}]
    project.save_manifest(recs)
    project.export_csv(recs)
    return recs


def _edit_csv(project, changes):
    rows = list(csv.DictReader(open(project.csv_path, encoding="utf-8-sig")))
    for r in rows:
        r.update(changes.get(r["id"], {}))
    with open(project.csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def test_import_csv_drops_suspect_on_edit_and_empty_keep_keeps(tmp_path):
    project = _project(tmp_path)
    _manifest(project)
    _edit_csv(project, {"a": {"text": "今天我们讲函数。", "keep": ""}, "b": {"keep": ""}, "c": {"keep": "否"}})
    changed = project.import_csv()
    recs = {r["id"]: r for r in project.load_manifest()}
    assert changed == {"text": 1, "keep": 1, "lang": 0}
    assert recs["a"]["text"] == "今天我们讲函数。" and "suspect" not in recs["a"] and recs["a"]["keep"] is True
    assert abs(recs["a"]["rate"] - 7 / 2.0) < 1e-6
    assert recs["b"]["keep"] is False and "suspect" in recs["b"]  # 文字没改：标记留着；「保留」空着：不变
    assert recs["c"]["keep"] is False and recs["c"]["manual_keep"] is False


def test_set_clip_text(tmp_path):
    project = _project(tmp_path)
    _manifest(project)
    rec = project.set_clip_text("a", "今天我们讲函数。")
    assert rec["text"] == "今天我们讲函数。" and "suspect" not in rec
    assert "今天我们讲函数。" in project.csv_path.read_text(encoding="utf-8-sig")
    with pytest.raises(KeyError):
        project.set_clip_text("zzz", "x")
    with pytest.raises(ValueError):
        project.set_clip_text("c", "  ")


def test_set_clip_text_when_csv_locked_by_excel(tmp_path, monkeypatch):
    """transcripts.csv 被 Excel/WPS 锁住：manifest 照样改好（不能先改一半再报错），返回值提醒 CSV 没同步。"""
    project = _project(tmp_path)
    _manifest(project)
    project.export_csv()

    def locked(records=None):
        raise PermissionError(13, "Permission denied", str(project.csv_path))

    monkeypatch.setattr(project, "export_csv", locked)
    rec = project.set_clip_text("a", "今天我们讲函数。")
    assert rec["text"] == "今天我们讲函数。" and rec.get("csv_locked") is True
    saved = {r["id"]: r for r in project.load_manifest()}["a"]
    assert saved["text"] == "今天我们讲函数。" and "suspect" not in saved and "csv_locked" not in saved
