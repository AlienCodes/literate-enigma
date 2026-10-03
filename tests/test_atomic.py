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
    with pytest.raises(PermissionError):
        atomic.write_text(tmp_path / "a.json", "{}")
    assert not list(tmp_path.iterdir())
