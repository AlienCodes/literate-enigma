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
