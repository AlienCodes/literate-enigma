"""先写临时文件再换上去：两个地方同时写同一个文件也不会出错（10-03 浏览器实测：保存修改还在写 profile.json 时
点「确认训练素材」，报「No such file or directory: ...profile.json.tmp」）。"""

import json
import threading

from voicetwin.project import Project
from voicetwin.utils import atomic


def test_many_threads_writing_the_same_json_never_fail(tmp_path):
    path = tmp_path / "profile.json"
    errors = []

    def work(k):
        try:
            for i in range(60):
                Project.write_json(path, {"k": k, "i": i})
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))

    threads = [threading.Thread(target=work, args=(k,)) for k in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert set(json.loads(path.read_text(encoding="utf-8"))) == {"k", "i"}  # 留下的是完整的一份
    assert not list(tmp_path.glob("*.tmp"))  # 临时文件都换掉了


def test_failed_replace_leaves_no_temp_file(tmp_path, monkeypatch):
    import os

    import pytest

    def boom(a, b):
        raise PermissionError("被别的程序打开了")

    monkeypatch.setattr(os, "replace", boom)
    monkeypatch.setattr(atomic, "RETRY_WAITS", [0.0, 0.0])
    with pytest.raises(PermissionError):
        atomic.write_text(tmp_path / "a.json", "{}")
    assert not list(tmp_path.iterdir())


def test_replace_waits_when_windows_says_the_file_is_busy(tmp_path, monkeypatch):
    """Windows 上正式文件这一刻正被别的线程读 / 换时，换文件会被拒绝一下：等一会儿再试就好。"""
    import os

    real = os.replace
    calls = []

    def flaky(a, b):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError(13, "另一个程序正在使用此文件")
        return real(a, b)

    monkeypatch.setattr(os, "replace", flaky)
    monkeypatch.setattr(atomic, "RETRY_WAITS", [0.0] * 5)
    atomic.write_text(tmp_path / "a.json", '{"ok": 1}')
    assert (tmp_path / "a.json").read_text(encoding="utf-8") == '{"ok": 1}' and len(calls) == 3
    assert not list(tmp_path.glob("*.tmp"))


# ---------------------------------------------------------------------------- 第四轮找 bug（g3）
def test_files_are_on_disk_before_they_replace_the_old_ones(tmp_path, monkeypatch):
    """以前只交给系统、从来不 fsync：保存以后几秒内断电，Windows 记得「换过了」、内容却没写进去，开机以后 manifest.jsonl
    是空的或者一堆 0，整张校对表没了。现在先让临时文件真的写到硬盘上，再换上去（校对表、transcripts.csv、草稿都一样）。"""
    import os

    from conftest import make_cfg
    from voicetwin import workflows as wf

    events = []
    real_fsync, real_replace = os.fsync, os.replace
    monkeypatch.setattr(os, "fsync", lambda fd: (events.append("fsync"), real_fsync(fd))[1])
    monkeypatch.setattr(os, "replace", lambda a, b: (events.append(("replace", os.path.basename(str(b)))),
                                                     real_replace(a, b))[1])
    atomic.write_text(tmp_path / "a.json", "{}")
    assert events == ["fsync", ("replace", "a.json")]
    project = wf.Project(make_cfg(tmp_path / "ws"), "v").ensure()
    events.clear()
    project.save_manifest([{"id": "c1", "path": "clips/c1.wav", "text": "一句话。", "duration": 3.0}])
    project.export_csv()
    names = [e[1] for e in events if isinstance(e, tuple)]
    assert names[:2] == ["manifest.jsonl", "transcripts.csv"]
    for i, e in enumerate(events):  # 每次换文件之前都先 fsync 过
        if isinstance(e, tuple):
            assert i > 0 and events[i - 1] == "fsync", events


def test_fsync_not_supported_still_saves(tmp_path, monkeypatch):
    """个别网络盘 / 虚拟盘不支持 fsync：照样保存（和以前一样）。"""
    import os

    def nope(fd):
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr(os, "fsync", nope)
    atomic.write_text(tmp_path / "a.json", '{"ok": 1}')
    assert (tmp_path / "a.json").read_text(encoding="utf-8") == '{"ok": 1}'


def test_empty_manifest_does_not_wipe_the_last_copy_of_the_texts(tmp_path):
    """断电后 manifest.jsonl 空了（或者全是 0）：照着网页说的再点「开始准备素材」，以前 transcripts.csv 也被空表冲掉，
    最后一份改好的文字没了。现在少了句子时先把上次的 transcripts.csv 另存一份备份。"""
    from conftest import make_cfg
    from voicetwin import workflows as wf

    project = wf.Project(make_cfg(tmp_path / "ws"), "v").ensure()
    recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"老师改好的第{i}句。", "duration": 3.0} for i in range(3)]
    project.save_manifest(recs)
    project.export_csv(recs)
    (project.clips_dir / "c0.wav").write_bytes(b"RIFF")
    project.manifest_path.write_bytes(b"\x00" * 300)  # 断电以后 Windows 留下的样子
    assert project.load_manifest() == []
    project.export_csv(project.load_manifest())
    backups = list(project.root.glob("transcripts_备份_*.csv"))
    assert len(backups) == 1 and "老师改好的第2句。" in backups[0].read_text(encoding="utf-8-sig")
    project.export_csv([])  # 再写一次空的：上次写的已经是空表，不再另存
    assert len(list(project.root.glob("transcripts_备份_*.csv"))) == 1
    project.export_csv(recs + [dict(recs[0], id="c9")])  # 正常加了句子：不另存
    assert len(list(project.root.glob("transcripts_备份_*.csv"))) == 1


def _backups(project):
    return sorted(project.root.glob("transcripts_备份_*.csv"))


def test_csv_is_kept_when_the_snapshot_was_lost_in_the_same_power_cut(tmp_path):
    """transcripts.exported.json 和 manifest.jsonl 是同一次保存写的（它是最后写的）：断电时常常一起变成一堆 0 / 空文件。
    以前只看它判断「少了句子」，它坏了就不另存，transcripts.csv 里最后一份改好的文字直接被空表冲掉（审查 review#2 第 1 种）。
    现在它坏了就直接读 transcripts.csv；读校对表的时候发现 manifest 空了也记下来，下次写之前先另存。没有切好的片段也一样。"""
    from conftest import make_cfg
    from voicetwin import workflows as wf

    for junk in (b"\x00" * 300, b""):
        project = wf.Project(make_cfg(tmp_path / f"ws{len(junk)}"), "v").ensure()
        recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"第{i}句老师改好的文字。", "duration": 3.0}
                for i in range(5)]
        project.save_manifest(recs)
        project.export_csv(project.load_manifest())
        project.manifest_path.write_bytes(junk)
        project.csv_snapshot_path.write_bytes(junk[:200])
        project.export_csv(project.load_manifest())  # 例如准备素材 / 任何一次保存又写了一遍表格
        backups = _backups(project)
        assert len(backups) == 1, junk[:4]
        assert "第4句老师改好的文字。" in backups[0].read_text(encoding="utf-8-sig")
        project.export_csv(project.load_manifest())  # 表格已经是空的了：不再另存
        assert len(_backups(project)) == 1


def test_csv_is_kept_when_the_clips_come_back_with_the_same_ids(tmp_path):
    """manifest 丢了以后视频重新切一遍（sources.json 也坏了，或者 g4 组「校对表里一条都没有的视频再切一遍」）：片段编号和原来
    一模一样，只比编号看不出少了什么，字幕 / 识别的字把老师改好的字冲掉了，一份备份都没有（审查 review#2 第 2 种）。
    现在：有字的句子换成了别的字、这一条又没有被人改过（程序自己从来不改有字的句子），就先另存。"""
    from conftest import make_cfg
    from voicetwin import workflows as wf
    from voicetwin.project import apply_text_edit

    project = wf.Project(make_cfg(tmp_path / "ws"), "v").ensure()
    recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"识别的第{i}句。", "duration": 3.0} for i in range(5)]
    recs.append({"id": "c9", "path": "clips/c9.wav", "text": "", "duration": 3.0})  # 还没识别出文字
    project.save_manifest(recs)
    project.export_csv(recs)
    # 正常的修改都不另存：老师改字（保存）、识别填上没字的句子、加了新句子、删除（标紫色）
    apply_text_edit(recs[0], "老师改好的第0句。")
    apply_text_edit(recs[1], "老师改好的第1句。")
    recs[5]["text"] = "后来识别出来的。"
    recs[2].update(keep=False, deleted=True)
    recs.append({"id": "c10", "path": "clips/c10.wav", "text": "新视频的一句。", "duration": 3.0})
    project.save_manifest(recs)
    project.export_csv(recs)
    assert _backups(project) == []
    # 重新切出来的：编号一样，文字是字幕 / 识别的，没有「改过」的记号（manifest 没有坏：只靠比文字）
    again = [{"id": r["id"], "path": r["path"], "text": f"识别的第{i}句。" if i < 5 else r["text"], "duration": 3.0}
             for i, r in enumerate(recs)]
    project.save_manifest(again)
    project.export_csv(again)
    backups = _backups(project)
    assert len(backups) == 1
    kept = backups[0].read_text(encoding="utf-8-sig")
    assert "老师改好的第0句。" in kept and "老师改好的第1句。" in kept
    project.export_csv(again)  # 已经是重新切的样子了：不再另存
    assert len(_backups(project)) == 1


def test_csv_is_kept_when_only_deletions_would_be_lost(tmp_path):
    """老师只删了几句（紫色）、没改字：manifest 断电变成一堆 0 以后重新切出来的字和原来一样，比文字也看不出来。
    读校对表时发现 manifest 空了就记下来（manifest.lost.json），下一次写 transcripts.csv 以前一定先另存一份。"""
    from conftest import make_cfg
    from voicetwin import workflows as wf

    project = wf.Project(make_cfg(tmp_path / "ws"), "v").ensure()
    recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"第{i}句。", "duration": 3.0} for i in range(4)]
    recs[3].update(keep=False, deleted=True, drop_reason="手动删除")
    project.save_manifest(recs)
    project.export_csv(recs)
    project.manifest_path.write_bytes(b"\x00" * 300)
    assert project.load_manifest() == []
    again = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"第{i}句。", "duration": 3.0} for i in range(4)]
    project.save_manifest(again)  # 重新切好、识别好，存了校对表（还没写 transcripts.csv 就被停止了也一样）
    project.export_csv(project.load_manifest())
    backups = _backups(project)
    assert len(backups) == 1 and "手动删除" in backups[0].read_text(encoding="utf-8-sig")
    project.export_csv(again)  # 只另存一次
    assert len(_backups(project)) == 1


def test_csv_backup_is_not_repeated_while_excel_keeps_it_locked(tmp_path, monkeypatch):
    """要另存、可是 transcripts.csv 被 Excel 开着这次没写成：每保存一次就多一份一模一样的备份。一样的只留一份。"""
    from conftest import make_cfg
    from voicetwin import workflows as wf

    project = wf.Project(make_cfg(tmp_path / "ws"), "v").ensure()
    recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"第{i}句。", "duration": 3.0} for i in range(3)]
    project.save_manifest(recs)
    project.export_csv(recs)
    real = atomic.finish

    def locked(tmp, path):
        if path.name == "transcripts.csv":
            tmp.unlink()
            raise PermissionError(13, "Permission denied")
        real(tmp, path)

    monkeypatch.setattr(atomic, "finish", locked)
    for _ in range(3):
        try:
            project.export_csv([])
        except PermissionError:
            pass
    assert len(_backups(project)) == 1


def test_csv_is_not_overwritten_when_the_backup_fails(tmp_path, monkeypatch):
    """要另存却存不了（例如杀毒软件占着新文件）：以前说一句就接着写，上次保存的文字一份都不剩。现在这次先不写 transcripts.csv
    （报错；校对表 manifest.jsonl 已经存好了），下次再试。"""
    import pytest
    from conftest import make_cfg
    from voicetwin import workflows as wf

    project = wf.Project(make_cfg(tmp_path / "ws"), "v").ensure()
    recs = [{"id": f"c{i}", "path": f"clips/c{i}.wav", "text": f"老师改好的第{i}句。", "duration": 3.0} for i in range(3)]
    project.save_manifest(recs)
    project.export_csv(recs)
    before = project.csv_path.read_bytes()
    project.manifest_path.write_bytes(b"\x00" * 300)
    project.load_manifest()
    real = atomic.finish

    def refuse(tmp, path):
        if "备份" in path.name:
            tmp.unlink()
            raise OSError(5, "Input/output error")
        real(tmp, path)

    monkeypatch.setattr(atomic, "finish", refuse)
    with pytest.raises(OSError):
        project.export_csv([])
    assert project.csv_path.read_bytes() == before and not _backups(project)
    assert project.manifest_lost_path.exists()  # 下次写的时候照样先另存
    monkeypatch.setattr(atomic, "finish", real)
    project.export_csv([])
    assert len(_backups(project)) == 1 and not project.manifest_lost_path.exists()


def test_resliced_videos_after_a_power_cut_keep_the_teachers_corrections(tmp_path):
    """真的走一遍：准备素材、改 5 句保存；断电以后 manifest.jsonl 和 sources.json 都成了一堆 0，照着网页说的再点
    「开始准备素材」：视频重新切一遍，编号和原来一样，transcripts.csv 被字幕的字冲掉。以前一份备份都没有。"""
    from conftest import make_cfg, make_lecture
    from voicetwin import workflows as wf
    from voicetwin.data import review

    lec = tmp_path / "lectures"
    make_lecture(lec / "第1课.wav", repeats=1)
    cfg = make_cfg(tmp_path / "ws")
    wf.run_prepare(cfg, "v", [str(lec)])
    project = wf.Project(cfg, "v")
    recs = project.load_manifest()
    for r in recs[:5]:
        review.set_draft(project, r["id"], text="老师改好的：" + r["id"])
    wf.review_save(cfg, "v")
    assert project.csv_path.read_text(encoding="utf-8-sig").count("老师改好的") == 5
    project.manifest_path.write_bytes(b"\x00" * 500)
    project.sources_path.write_bytes(b"\x00" * 200)
    wf.run_prepare(cfg, "v", [str(lec)])
    assert {r["id"] for r in project.load_manifest()} == {r["id"] for r in recs}  # 重新切的：编号一模一样
    backups = _backups(project)
    assert len(backups) == 1 and backups[0].read_text(encoding="utf-8-sig").count("老师改好的") == 5


def test_lost_manifest_message_only_promises_what_happens(tmp_path, monkeypatch):
    """黑色窗口里的话：transcripts.csv 里有句子才说「下次写它以前先另存一份备份」；没有（还没写过）就不提它。"""
    import voicetwin.project as P
    from conftest import make_cfg
    from voicetwin import workflows as wf

    said = []
    monkeypatch.setattr(P.log, "warning", lambda msg, *a, **k: said.append(str(msg)))
    project = wf.Project(make_cfg(tmp_path / "ws1"), "v").ensure()
    (project.clips_dir / "c0.wav").write_bytes(b"RIFF")
    project.manifest_path.write_bytes(b"")
    project.load_manifest()
    assert said and not any("备份" in s or "transcripts.csv" in s for s in said)
    said.clear()
    project = wf.Project(make_cfg(tmp_path / "ws2"), "v").ensure()
    recs = [{"id": "c0", "path": "clips/c0.wav", "text": "一句话。", "duration": 3.0}]
    project.save_manifest(recs)
    project.export_csv(recs)
    project.manifest_path.write_bytes(b"")
    project.load_manifest()
    assert any("transcripts_备份_" in s for s in said)
    assert not _backups(project)  # 只是记下来，真的要写 transcripts.csv 的时候才另存
    project.export_csv([])
    assert len(_backups(project)) == 1


def test_useless_bad_copy_is_replaced(tmp_path):
    """以前只留第一次的 .bad 副本：第一次坏的是一堆 0（什么都没有），后来真正有内容的坏文件一份都留不下。"""
    p = tmp_path / "manifest.jsonl"
    p.write_bytes(b"\x00" * 50)
    atomic.keep_bad_copy(p)
    p.write_text('{"id": "c1", "text": "一句话"}\n{"id": "c2", "te', encoding="utf-8")
    atomic.keep_bad_copy(p)
    assert "一句话" in (tmp_path / "manifest.jsonl.bad").read_text(encoding="utf-8")
    p.write_bytes(b"")
    atomic.keep_bad_copy(p)  # 有内容的副本不会被空的换掉
    assert "一句话" in (tmp_path / "manifest.jsonl.bad").read_text(encoding="utf-8")


def test_remove_retries_and_never_pretends(tmp_path, monkeypatch):
    """删文件：Windows 上一时被占着就等一会儿再删；一直删不掉时给了替代内容就写成它，没给就报错（不悄悄当成删掉了）。"""
    from pathlib import Path

    import pytest

    monkeypatch.setattr(atomic, "RETRY_WAITS", [0.0] * 3)
    p = tmp_path / "review_draft.json"
    atomic.remove(p)  # 本来就没有：不报错
    p.write_text('{"c1": {}}', encoding="utf-8")
    real = Path.unlink
    fails = {"n": 2}

    def locked(self, *a, **kw):
        if fails["n"] > 0:
            fails["n"] -= 1
            raise PermissionError(32, "另一个程序正在使用此文件")
        return real(self, *a, **kw)

    monkeypatch.setattr(Path, "unlink", locked)
    atomic.remove(p)
    assert not p.exists()
    p.write_text('{"c1": {}}', encoding="utf-8")
    fails["n"] = 99
    atomic.remove(p, fallback_text="{}")
    assert p.read_text(encoding="utf-8") == "{}"
    fails["n"] = 99
    with pytest.raises(PermissionError):
        atomic.remove(p)
