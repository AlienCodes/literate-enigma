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
import re  # noqa: E402

import pytest

from voicetwin.data.review import analyze  # noqa: E402

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
    # 改成了建议的写法：不再算可能有错（采用的记录留着，校对表里按钮是红的、可以撤销）
    assert recs["a"]["text"] == "今天我们讲函数。" and not analyze(recs["a"])["active"] and recs["a"]["keep"] is True
    assert analyze(recs["a"])["adopted"] and recs["a"]["orig_text"] == "今天我们讲VFIXED。"
    assert abs(recs["a"]["rate"] - 7 / 2.0) < 1e-6
    assert recs["b"]["keep"] is False and "suspect" in recs["b"]  # 文字没改：标记留着；「保留」空着：不变
    assert recs["c"]["keep"] is False and recs["c"]["manual_keep"] is False


def test_set_clip_text(tmp_path):
    project = _project(tmp_path)
    _manifest(project)
    rec = project.set_clip_text("a", "今天我们讲函数。")
    assert rec["text"] == "今天我们讲函数。" and not analyze(rec)["active"]
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
    assert saved["text"] == "今天我们讲函数。" and not analyze(saved)["active"] and "csv_locked" not in saved


# ============================================================================ 第四轮找 bug（g5：讲稿解析）
@pytest.mark.parametrize("mark", ["【停顿=2】", "[停顿＝2]", "［停顿=2］", "【停顿2秒】", "【 停顿 = ２ 】", "[停顿=2秒钟]"])
def test_pause_mark_typed_with_chinese_input_method(mark):
    """中文输入法下打 [ ] 会变成【 】、等号数字也可能是全角的：以前认不出来，没有停顿，「停顿=2」还被读出来、显示在字幕里。"""
    segs = parse_script(f"第一句话讲完了呢。{mark}第二句话开始了。")
    assert [s.text for s in segs] == ["第一句话讲完了呢。", "第二句话开始了。"]
    assert segs[0].pause_after == 2.0 and "停顿" not in segs[1].display
    assert not any(s.extra.get("unread_mark") for s in segs)


def test_pause_mark_without_seconds_and_in_minutes():
    segs = parse_script("第一句话讲完了呢。【停顿】第二句话开始了。")
    assert segs[0].pause_after == "paragraph" and segs[1].text == "第二句话开始了。"
    assert parse_script("先想一想这道题怎么做。[停顿=1分钟]好，我们来看答案吧。")[0].pause_after == 60.0


def test_unrecognized_pause_mark_is_kept_and_reported():
    """统一以后还认不出来的（【暂停一下】这种小标题、写错的单位）原样保留，并记下来（生成时提醒老师会被读出来）。"""
    segs = parse_script("【暂停一下】我们休息一会儿再继续讲。")
    assert segs[0].display.startswith("【暂停一下】") and segs[0].extra["unread_mark"] == "【暂停一下】"
    assert "unread_mark" not in parse_script("第一句话讲完了呢。[停顿=2]第二句话开始了。")[1].extra
    full = parse_script("［停顿一下］我们休息一会儿再继续讲。")[0]
    assert full.extra["unread_mark"] == "［停顿一下］" and "［" not in full.text  # 全角方括号不再原样发给合成引擎


def test_pause_at_the_very_start_is_kept():
    """讲稿最前面的 [停顿=3]：以前直接丢掉（第一句前面没有句子可以挂）。"""
    segs = parse_script("[停顿=3]第一句话在这里讲。")
    assert segs[0].extra.get("pause_before") == 3.0
    assert parse_script("【停顿=2.5】第一句话在这里讲。第二句话在这里讲。")[0].extra.get("pause_before") == 2.5
    assert "pause_before" not in parse_script("第一句话在这里讲。")[0].extra
    assert parse_script("第一句话在这里讲。[停顿=3]")[-1].pause_after == 3.0  # 结尾的本来就留着


LONG_NO_COMMA = "今天我们要讲的内容是英语考试里面经常出现的各种各样的陷阱和常见错误以及怎么避免它们的方法还有一些别的东西"


def test_hard_split_never_adds_a_full_stop_in_the_middle():
    """一个分句太长又没有逗号时硬切：以前每段末尾补「。」（语调落下来、像一句话说完了），现在补「，」，最后一段才是句号。"""
    segs = parse_script(LONG_NO_COMMA)
    assert len(segs) >= 2 and all(syllable_count(s.text) <= 50 for s in segs)
    assert all(s.text.endswith("，") and s.pause_after == "clause" for s in segs[:-1])
    assert segs[-1].text.endswith("。") and "".join(s.text for s in segs).replace("，", "").rstrip("。") == LONG_NO_COMMA
    assert min(syllable_count(s.text) for s in segs) >= 10  # 长短差不多，不会剩下「东西。」两个字单独合成


def test_hard_split_cuts_at_spaces_and_keeps_english_words_whole():
    from voicetwin.synth.script import _hard_split

    spaced = ("我们先来看一下第一个例句 然后我们一起来分析它的结构和用法 最后再做几道练习题巩固一下今天学的内容 "
              "然后我们一起来分析它的结构和用法")
    pieces = _hard_split(spaced, 50)
    assert len(pieces) >= 2 and all(syllable_count(p) <= 50 for p in pieces)
    words = spaced.split()
    for p in pieces:  # 在空格处切开：每段都是完整的几截，没有从「一起」中间切开
        assert p.rstrip("，").replace(" ", "") in {"".join(words[i:j]) for i in range(len(words))
                                                    for j in range(i + 1, len(words) + 1)}
    mixed = "一" * 48 + "beautiful" + "二" * 10
    pieces = _hard_split(mixed, 50)
    assert all(syllable_count(p) <= 50 for p in pieces)
    assert any("beautiful" in p for p in pieces)  # 以前切成「beautif」「ul」
    assert _hard_split("one two three four five six seven eight nine ten eleven twelve", 6)[0].endswith(",")


@pytest.mark.skipif(not __import__("voicetwin.data.lexicon_fix", fromlist=["has_jieba"]).has_jieba(),
                    reason="没有装 jieba（整合包里有）")
def test_hard_split_cuts_between_words_with_jieba():
    from voicetwin.synth.script import _hard_split

    text = "这个句子里的先行词非常重要我们在做题的时候所以要特别注意它的用法和位置还有它前面的介词以及后面的从句结构"
    for n in (20, 25, 30, 35):
        pieces = [p.rstrip("，") for p in _hard_split(text, n)]
        assert "".join(pieces) == text
        joints = [pieces[i][-1] + pieces[i + 1][0] for i in range(len(pieces) - 1)]
        assert not any(j in ("特别", "注意", "用法", "位置", "句子", "重要") for j in joints), (n, pieces)


def _docx_lesson(path, rows, before="第三课 定语从句", after="下课。"):
    docx = pytest.importorskip("docx")
    d = docx.Document()
    if before:
        d.add_paragraph(before)
    if rows:
        t = d.add_table(rows=len(rows), cols=len(rows[0]))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                t.cell(i, j).text = val
    if after:
        d.add_paragraph(after)
    d.save(str(path))
    return path


def test_docx_tables_are_read_in_order(tmp_path):
    """教案常常写在 Word 表格里（教学环节 | 讲解内容）：以前只读表格外面的段落，表格里讲课的字全丢了。"""
    p = _docx_lesson(tmp_path / "教案.docx", [["教学环节", "讲解内容"], ["导入", "同学们好，今天我们学习定语从句。"],
                                             ["讲解", "先看一个例句：The book which I bought is new."]])
    text, cues = read_script_file(p)
    assert cues is None
    lines = text.split("\n\n")
    assert lines[0] == "第三课 定语从句" and lines[-1] == "下课。"
    assert text.index("同学们好") < text.index("The book which I bought") < text.index("下课")
    assert "导入\n同学们好，今天我们学习定语从句。" in lines  # 表格一行一段，格子之间换行
    from voicetwin.synth.script import docx_info

    assert docx_info(p) == {"tables": 1, "textboxes": 0}


def test_docx_merged_cells_are_read_once(tmp_path):
    docx = pytest.importorskip("docx")
    d = docx.Document()
    t = d.add_table(rows=2, cols=2)
    t.cell(0, 0).text = "导入"
    t.cell(0, 1).text = "同学们好。"
    t.cell(1, 1).text = "今天学习定语从句。"
    t.cell(0, 0).merge(t.cell(1, 0))      # 竖着合并
    row = d.add_table(rows=1, cols=2)
    row.cell(0, 0).text = "横着合并的一格。"
    row.cell(0, 0).merge(row.cell(0, 1))  # 横着合并
    d.save(str(tmp_path / "合并.docx"))
    text, _ = read_script_file(tmp_path / "合并.docx")
    assert text.count("导入") == 1 and text.count("横着合并的一格。") == 1 and "今天学习定语从句。" in text


def test_docx_upload_message_tells_about_tables_and_empty_files(tmp_path):
    from conftest import make_cfg
    from voicetwin.webui import app as A

    ui = A.WebUI(make_cfg(tmp_path))
    p = _docx_lesson(tmp_path / "教案.docx", [["导入", "同学们好，今天我们学习定语从句。"]])
    text, f, hint, _ = ui.on_script_upload(str(p), "")
    assert "同学们好" in text and f is None and "放进上面的讲稿框" in hint and "表格" in hint
    plain = _docx_lesson(tmp_path / "普通.docx", [], before="大家好。", after="")
    _, _, hint2, _ = ui.on_script_upload(str(plain), "")
    assert "表格" not in hint2
    # 什么都没读到：讲稿框里原来的字不清掉，也不说「已放进讲稿框」
    empty = _docx_lesson(tmp_path / "空的.docx", [], before="", after="")
    t3, _, hint3, _ = ui.on_script_upload(str(empty), "")
    assert isinstance(t3, dict) and "value" not in t3 and "没有读到文字" in hint3 and "放进上面的讲稿框" not in hint3


def test_hard_split_pieces_never_exceed_the_limit():
    """硬切出来的每一段都不能超过上限（太长的一段合成引擎可能读乱）；英文单词和数字连着写时以前个别段会超过。"""
    import random

    from voicetwin.synth.script import _hard_split

    rng = random.Random(1)
    words = ["我们", "一起", "来看", "这个", "句子", "先行词", "the", "beautiful", "interesting", "book", "特别", "注意",
             " ", "3.14159", "2024年", "Python3", "https://example.com/abc"]
    for _ in range(400):
        s = "".join(rng.choice(words) for _ in range(rng.randint(10, 80)))
        for mx in (20, 30, 50):
            pieces = _hard_split(s, mx)
            assert all(syllable_count(p) <= mx for p in pieces), (s, mx, pieces)
            body = [p[:-1] if i < len(pieces) - 1 and p.endswith(("，", ",")) else p for i, p in enumerate(pieces)]
            assert "".join(body).replace(" ", "") == s.replace(" ", "")  # 一个字都不丢


# ----------------------------------------------------------------------------- 第四轮找 bug（g5 复查：硬切补的逗号）
def _mother_long_sentences():
    """程序自带的母本：去掉标点（英文单词之间的空格留着），拼成 51–100 个音节、中间没有逗号的长句
    （从语音转文字工具复制来的讲稿就是这样）。"""
    from voicetwin.data.transcript_fix import builtin_mother

    punct = re.compile(r"[，。！？、；：,.!?;:“”\"'‘’（）()《》〈〉【】\[\]…—\-]+")
    out, cur = [], ""
    for _, t in builtin_mother():
        p = re.sub(r"(?<![A-Za-z0-9])\s+|\s+(?![A-Za-z0-9])", "", punct.sub(" ", t))
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue
        latin_join = cur[-1:].isascii() and cur[-1:].isalnum() and p[:1].isascii() and p[:1].isalnum()
        cur = cur + (" " if latin_join else "") + p
        n = syllable_count(cur)
        if n > 100:
            cur = ""
        elif n > 50:
            out.append(cur + "。")
            cur = ""
    return out


def _inserted_commas(source, pieces):
    """pieces 拼回去和 source 比（空格、全角空格不算）：只有不是最后一段的末尾可以多一个逗号（真的切开的地方）。
    返回出问题的地方（多出来的逗号在一段中间、或者丢了字），没有问题返回空列表。"""
    src, pos, bad = re.sub(r"\s", "", source), 0, []
    for i, p in enumerate(pieces):
        p = re.sub(r"\s", "", p)
        if src.startswith(p, pos):
            pos += len(p)
        elif i < len(pieces) - 1 and p[-1:] in "，," and src.startswith(p[:-1], pos):
            pos += len(p) - 1
        else:
            bad.append(p)
            break
    if not bad and pos != len(src):
        bad.append(src[pos:])
    return bad


def test_hard_split_comma_only_where_the_sentence_is_really_cut():
    """硬切补的「，」只能在真的切开的地方：以前硬切剩下「错误」两个字，chunk_sentence 又把它并回前一段，
    补的逗号就落在一段中间（「……陷阱和常见，错误。」「翻译成一个，形容词。」），合成时在那里停一下、字幕里也看得到。
    英文短语也不从中间切开（以前「which we，」「know……」）。"""
    s = "今天我们要讲的内容是关于现在完成时和一般过去时的区别以及它们在实际考试当中经常出现的各种各样的陷阱和常见错误。"
    segs = [x.display for x in parse_script(s)]
    assert len(segs) == 2 and not _inserted_commas(s, segs), segs
    assert all(syllable_count(d) >= 20 for d in segs)  # 长短差不多（54 个字切成 26 + 28 左右）
    sents = _mother_long_sentences()
    assert len(sents) > 100
    problems, short, en_cut = [], [], []
    for s in sents:
        segs = [x.display for x in parse_script(s)]
        assert all(syllable_count(d) <= 50 for d in segs), segs
        if _inserted_commas(s, segs):
            problems.append(" | ".join(segs))
        if min(syllable_count(d) for d in segs) < 10:
            short.append(" | ".join(segs))
        if any(re.search(r"[A-Za-z0-9][，,]$", a) and re.match(r"[A-Za-z0-9]", b) for a, b in zip(segs, segs[1:])):
            en_cut.append(" | ".join(segs))
    assert not problems, (len(problems), problems[:3])
    assert not short, (len(short), short[:3])
    assert not en_cut, (len(en_cut), en_cut[:3])


def test_chunk_sentence_never_puts_a_cut_comma_inside_a_chunk():
    """随机拼的长句（有的分句有逗号、有的没有）× 3 种上限：每段都不超过上限；拼回去和原文一样，
    只有真的切开的地方（不是最后一段的末尾）才多一个逗号。"""
    import random

    rng = random.Random(7)
    words = ["我们", "一起", "来看", "这个", "句子", "先行词", "the", "beautiful", "interesting", "book", "特别", "注意",
             " ", "3.14159", "2024年", "Python3", "错误", "形容词", "，"]
    for _ in range(300):
        s = "".join(rng.choice(words) for _ in range(rng.randint(10, 90))).strip(" ，") + "。"
        s = re.sub(r"，[\s，]*", "，", s)
        for mx in (20, 30, 50):
            chunks = chunk_sentence(s, mx)
            assert all(syllable_count(c) <= mx for c in chunks), (s, mx, chunks)
            assert not _inserted_commas(s, chunks), (s, mx, chunks)
