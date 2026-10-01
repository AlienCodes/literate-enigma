import threading

from voicetwin.utils import winsys


class FakeKernel32:
    """记录调用的假 kernel32。"""

    def __init__(self, console_mode=0x01F7, get_ok=1, set_ok=1, handle=7):
        self.calls = []
        self.console_mode = console_mode
        self.get_ok = get_ok
        self.set_ok = set_ok
        self.handle = handle

    def SetThreadExecutionState(self, flags):
        self.calls.append(("SetThreadExecutionState", flags))
        return 0x80000000

    def GetStdHandle(self, which):
        self.calls.append(("GetStdHandle", which))
        return self.handle

    def GetConsoleMode(self, handle, ref):
        self.calls.append(("GetConsoleMode", handle))
        ref._obj.value = self.console_mode  # ctypes.byref(x)._obj 就是 x
        return self.get_ok

    def SetConsoleMode(self, handle, mode):
        self.calls.append(("SetConsoleMode", handle, mode))
        return self.set_ok


def _exec_states(k):
    return [c[1] for c in k.calls if c[0] == "SetThreadExecutionState"]


def test_noop_on_linux(monkeypatch):
    monkeypatch.setattr(winsys.sys, "platform", "linux")

    def boom():
        raise AssertionError("不应该访问 kernel32")

    monkeypatch.setattr(winsys, "_kernel32", boom)
    with winsys.keep_awake():
        with winsys.keep_awake():
            pass
    assert winsys.disable_quick_edit() is False


def test_model_download_keeps_pc_awake(monkeypatch, tmp_path):
    """下载模型（1~2 GB）时电脑不能睡眠：网页上写着「运行期间电脑不会自动睡眠」。"""
    from conftest import make_cfg

    from voicetwin import workflows as wf
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    k = FakeKernel32()
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    seen = []

    def fake_download(self, source="auto", progress=None):
        seen.append(list(_exec_states(k)))
        return ["a.bin"]

    monkeypatch.setattr(GPTSoVITSBackend, "download_pretrained", fake_download)
    assert wf.download_models(make_cfg(tmp_path / "ws")) == ["a.bin"]
    assert seen == [[0x80000001]] and _exec_states(k) == [0x80000001, 0x80000000]


def test_keep_awake_nested_sets_once(monkeypatch, caplog):
    k = FakeKernel32()
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    with winsys.keep_awake():
        with winsys.keep_awake():
            with winsys.keep_awake():
                assert _exec_states(k) == [0x80000001]
        assert _exec_states(k) == [0x80000001]
    assert _exec_states(k) == [0x80000001, 0x80000000]
    # 再来一次：又会重新设置
    with winsys.keep_awake():
        pass
    assert _exec_states(k) == [0x80000001, 0x80000000, 0x80000001, 0x80000000]


def test_keep_awake_restores_after_exception(monkeypatch):
    k = FakeKernel32()
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    try:
        with winsys.keep_awake():
            raise KeyError("x")
    except KeyError:
        pass
    assert _exec_states(k) == [0x80000001, 0x80000000]
    with winsys.keep_awake():  # 深度计数已经恢复
        pass
    assert _exec_states(k)[-2:] == [0x80000001, 0x80000000]


def test_keep_awake_never_raises(monkeypatch):
    monkeypatch.setattr(winsys.sys, "platform", "win32")

    def broken():
        raise OSError("no kernel32")

    monkeypatch.setattr(winsys, "_kernel32", broken)
    with winsys.keep_awake():
        with winsys.keep_awake():
            pass


def test_keep_awake_is_per_thread(monkeypatch):
    k = FakeKernel32()
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    inside = threading.Event()
    release = threading.Event()

    def worker():
        with winsys.keep_awake():
            inside.set()
            release.wait(5)

    t = threading.Thread(target=worker)
    t.start()
    assert inside.wait(5)
    with winsys.keep_awake():  # 主线程是自己的最外层，也要设置
        pass
    release.set()
    t.join(5)
    assert _exec_states(k).count(0x80000001) == 2
    assert _exec_states(k).count(0x80000000) == 2


def test_quick_edit_mask():
    assert winsys.quick_edit_mask(0x01F7) == (0x01F7 & ~0x0040) | 0x0080
    assert winsys.quick_edit_mask(0x0040) == 0x0080
    assert winsys.quick_edit_mask(0x0007) & 0x0040 == 0


def test_disable_quick_edit_sets_mask(monkeypatch):
    k = FakeKernel32(console_mode=0x01F7)
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    assert winsys.disable_quick_edit() is True
    assert ("GetStdHandle", -10) in k.calls
    sets = [c for c in k.calls if c[0] == "SetConsoleMode"]
    assert sets == [("SetConsoleMode", 7, (0x01F7 & ~0x0040) | 0x0080)]


def test_disable_quick_edit_restores_mode_at_exit(monkeypatch):
    """程序结束时把原来的设置改回去（只登记一次）。"""
    k = FakeKernel32(console_mode=0x01F7)
    registered = []
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    monkeypatch.setattr(winsys, "_RESTORE_REGISTERED", False)
    monkeypatch.setattr(winsys.atexit, "register", lambda fn, *a: registered.append((fn, a)))
    assert winsys.disable_quick_edit() is True
    assert winsys.disable_quick_edit() is True
    assert len(registered) == 1
    fn, args = registered[0]
    fn(*args)
    assert k.calls[-1] == ("SetConsoleMode", 7, 0x01F7)


def test_disable_quick_edit_failures(monkeypatch):
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    k = FakeKernel32(get_ok=0)  # 没有控制台（例如被重定向）
    monkeypatch.setattr(winsys, "_kernel32", lambda: k)
    assert winsys.disable_quick_edit() is False
    k2 = FakeKernel32(handle=-1)
    monkeypatch.setattr(winsys, "_kernel32", lambda: k2)
    assert winsys.disable_quick_edit() is False
    k3 = FakeKernel32(set_ok=0)
    monkeypatch.setattr(winsys, "_kernel32", lambda: k3)
    assert winsys.disable_quick_edit() is False

    def broken():
        raise OSError("boom")

    monkeypatch.setattr(winsys, "_kernel32", broken)
    assert winsys.disable_quick_edit() is False


def test_open_path_missing_and_never_raises(tmp_path, monkeypatch):
    assert winsys.open_path(tmp_path / "nope.wav") is False
    calls = []

    class FakePopen:
        def __init__(self, cmd, **kw):
            calls.append(cmd)

    monkeypatch.setattr(winsys.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(winsys.sys, "platform", "linux")
    f = tmp_path / "a.wav"
    f.write_bytes(b"x")
    assert winsys.open_path(f, select=True) is True
    assert calls[-1] == ["xdg-open", str(tmp_path)]
    assert winsys.open_path(tmp_path) is True
    assert calls[-1] == ["xdg-open", str(tmp_path)]

    def boom(*a, **kw):
        raise OSError("no xdg-open")

    monkeypatch.setattr(winsys.subprocess, "Popen", boom)
    assert winsys.open_path(f) is False


def test_open_path_windows_select(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(winsys.subprocess, "Popen", lambda cmd, **kw: calls.append(cmd))
    monkeypatch.setattr(winsys.sys, "platform", "win32")
    f = tmp_path / "带 空格.wav"
    f.write_bytes(b"x")
    assert winsys.open_path(f, select=True) is True
    assert calls == [f'explorer /select,"{f.resolve()}"']
