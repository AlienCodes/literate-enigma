import json
import socket
import sys
import threading
import types
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from voicetwin.webui import launcher


def _listen(port=0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", port))
    s.listen(5)
    return s


def _free_base_port():
    """找一段连续空闲端口的起点（测试里要用 base 和 base+1……）。"""
    for _ in range(50):
        s = _listen(0)
        base = s.getsockname()[1]
        s.close()
        if base + 12 > 65535:
            continue
        if all(launcher._bind_ok("127.0.0.1", p) for p in range(base, base + 12)):
            return base
    pytest.skip("找不到连续的空闲端口")


class _Server:
    """在后台线程里跑一个很小的 http 服务，/config 返回指定的网页标题。"""

    def __init__(self, title, port=0):
        payload = json.dumps({"title": title, "version": "4.24.0"}, ensure_ascii=False).encode("utf-8")

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path.rstrip("/") == "/config":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *args):
                pass

        self.httpd = HTTPServer(("127.0.0.1", port), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def test_free_port_skips_busy_port():
    base = _free_base_port()
    s = _listen(base)
    try:
        assert launcher._free_port(base, "127.0.0.1") == base + 1
    finally:
        s.close()
    assert launcher._free_port(base, "127.0.0.1") == base


def test_existing_instance_closed_port():
    base = _free_base_port()
    assert launcher._existing_instance(f"http://127.0.0.1:{base}") is False


def test_existing_instance_detects_voicetwin():
    srv = _Server("声音分身 VoiceTwin")
    try:
        assert launcher._existing_instance(srv.url) is True
        assert launcher._existing_instance(srv.url + "/") is True
    finally:
        srv.close()
    other = _Server("Gradio")
    try:
        assert launcher._existing_instance(other.url) is False
    finally:
        other.close()


def test_find_existing_scans_next_ports():
    base = _free_base_port()
    blocker = _listen(base)  # 7860 被别的软件占着
    srv = _Server("声音分身 VoiceTwin", port=base + 1)  # 上一次启动改用了 7861
    try:
        assert launcher._find_existing("127.0.0.1", base) == f"http://127.0.0.1:{base + 1}"
    finally:
        srv.close()
        blocker.close()
    assert launcher._find_existing("127.0.0.1", base) is None


def test_prepare_proxy_env_appends_localhost(monkeypatch):
    for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "no_proxy", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("no_proxy", "example.com, intranet")
    monkeypatch.setattr(launcher.sys, "platform", "linux")
    launcher._prepare_proxy_env()
    import os

    hosts = os.environ["no_proxy"].split(",")
    assert hosts[:2] == ["example.com", "intranet"]
    assert "127.0.0.1" in hosts and "localhost" in hosts
    assert "127.0.0.1" in os.environ["NO_PROXY"].split(",")
    # 再调用一次不会重复添加
    launcher._prepare_proxy_env()
    assert os.environ["no_proxy"].split(",").count("127.0.0.1") == 1


def test_prepare_proxy_env_copies_registry_on_windows(monkeypatch):
    import os
    import urllib.request

    for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "no_proxy", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(launcher.sys, "platform", "win32")
    monkeypatch.setattr(urllib.request, "getproxies_registry",
                        lambda: {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}, raising=False)
    launcher._prepare_proxy_env()
    assert os.environ["https_proxy"] == "http://127.0.0.1:7890"
    assert os.environ["HTTP_PROXY"] == "http://127.0.0.1:7890"
    assert "127.0.0.1" in os.environ["no_proxy"].split(",")
    # 已经有代理环境变量时不改
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("https_proxy", raising=False)
    monkeypatch.setattr(urllib.request, "getproxies_registry", lambda: {"https": "http://other:1"}, raising=False)
    launcher._prepare_proxy_env()
    assert os.environ["HTTPS_PROXY"] == "http://proxy.example:8080"
    assert "https_proxy" not in os.environ


def test_prepare_proxy_env_never_raises(monkeypatch):
    import urllib.request

    for name in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(launcher.sys, "platform", "win32")

    def boom():
        raise OSError("no registry")

    monkeypatch.setattr(urllib.request, "getproxies_registry", boom, raising=False)
    launcher._prepare_proxy_env()


class FakeApp:
    def __init__(self, fail=None):
        self.queued = False
        self.launch_kwargs = None
        self.fail = fail

    def queue(self):
        self.queued = True
        return self

    def launch(self, **kwargs):
        self.launch_kwargs = kwargs
        if self.fail is not None:
            raise self.fail


@pytest.fixture
def fake_env(monkeypatch):
    """不真的启动 gradio、不打开浏览器、不改真正的控制台。"""
    import voicetwin.webui.app as app_mod

    opened = []
    monkeypatch.setitem(sys.modules, "gradio", types.ModuleType("gradio"))
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url, *a, **k: opened.append(url))
    monkeypatch.setattr(launcher, "_prepare_proxy_env", lambda: None)
    monkeypatch.delenv("GRADIO_ANALYTICS_ENABLED", raising=False)
    return types.SimpleNamespace(app_mod=app_mod, opened=opened, monkeypatch=monkeypatch)


def test_launch_uses_build_app_local_and_free_port(fake_env, capsys):
    import os

    calls = []
    app = FakeApp()

    def build_app(cfg, local=True):
        calls.append(("local", local))
        return app

    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", build_app)
    base = _free_base_port()
    blocker = _listen(base)  # 首选端口被别的软件占了
    try:
        launcher.launch({"x": 1}, host="127.0.0.1", port=base)
    finally:
        blocker.close()
    out = capsys.readouterr().out
    assert calls == [("local", True)]
    assert app.queued
    kw = app.launch_kwargs
    assert kw["server_port"] == base + 1 and kw["server_name"] == "127.0.0.1"
    assert kw["show_error"] is True and kw["show_api"] is False and kw["inbrowser"] is True and kw["share"] is False
    assert os.environ["GRADIO_ANALYTICS_ENABLED"] == "False"
    assert f"{base} 端口被别的软件占用了，这次改用 {base + 1} 端口" in out
    assert f"网页地址：http://127.0.0.1:{base + 1}" in out
    assert "不要关闭这个黑色窗口" in out


def test_launch_falls_back_when_build_app_has_no_local(fake_env):
    app = FakeApp()
    calls = []

    def old_build_app(cfg):
        calls.append(cfg)
        return app

    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", old_build_app)
    base = _free_base_port()
    launcher.launch({"y": 2}, port=base)
    assert calls == [{"y": 2}]
    assert app.launch_kwargs["server_port"] == base


def test_launch_not_local_when_listening_on_all_addresses(fake_env):
    app = FakeApp()
    seen = []
    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app",
                                 lambda cfg, local=True: seen.append(local) or app)
    base = _free_base_port()
    launcher.launch({}, host="0.0.0.0", port=base)
    assert seen == [False]
    assert app.launch_kwargs["inbrowser"] is False


def test_launch_reuses_running_instance(fake_env, capsys):
    def build_app(cfg, local=True):
        raise AssertionError("已经在运行时不应该再启动一个")

    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", build_app)
    srv = _Server("声音分身 VoiceTwin")
    try:
        launcher.launch({}, port=srv.port)
    finally:
        srv.close()
    assert fake_env.opened == [srv.url]
    assert "声音分身已经在运行了" in capsys.readouterr().out


def test_launch_port_error_is_chinese(fake_env):
    app = FakeApp(fail=OSError("Cannot find empty port in range"))
    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", lambda cfg, local=True: app)
    fake_env.monkeypatch.setattr(launcher, "PORT_RETRY_SECONDS", 0.0)
    base = _free_base_port()
    with pytest.raises(RuntimeError) as ei:
        launcher.launch({}, port=base)
    assert f"端口 {base} 被占用" in str(ei.value) and "关掉其它黑色窗口" not in str(ei.value)
    fd = launcher._acquire_instance_lock(base)  # 出错后锁也放开了
    assert fd is not None
    launcher._release_instance_lock(fd)


def test_double_click_race_opens_the_running_one(fake_env, capsys):
    """两个窗口同时启动：后启动的那个占不到端口时，不能叫老师关掉能用的那个，而是直接打开它。"""
    base = _free_base_port()
    servers = []

    class RacingApp(FakeApp):
        def launch(self, **kwargs):
            servers.append(_Server("声音分身 VoiceTwin", port=kwargs["server_port"]))  # 另一个窗口先占了端口
            raise OSError("Cannot find empty port in range")

    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", lambda cfg, local=True: RacingApp())
    try:
        launcher.launch({}, port=base)
    finally:
        for srv in servers:
            srv.close()
    assert fake_env.opened == [f"http://127.0.0.1:{base}"]
    assert "声音分身已经在运行了" in capsys.readouterr().out


def test_second_window_waits_for_the_first_one(fake_env, capsys):
    """第一个窗口还在建网页（端口还没占上）时又双击了一次：第二个窗口不再启动一个，等第一个好了就打开它。"""
    base = _free_base_port()

    def build_app(cfg, local=True):
        raise AssertionError("另一个窗口正在启动时不应该再建一个网页")

    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", build_app)
    held = launcher._acquire_instance_lock(base)
    assert held is not None and held >= 0
    servers = []
    timer = threading.Timer(1.2, lambda: servers.append(_Server("声音分身 VoiceTwin", port=base)))
    timer.start()
    try:
        launcher.launch({}, port=base)
    finally:
        timer.join()
        for srv in servers:
            srv.close()
        launcher._release_instance_lock(held)
    out = capsys.readouterr().out
    assert "正在另一个黑色窗口里启动" in out and "声音分身已经在运行了" in out
    assert fake_env.opened == [f"http://127.0.0.1:{base}"]


def test_launch_proxy_error_is_chinese(fake_env):
    app = FakeApp(fail=ValueError("When localhost is not accessible, a shareable link must be created. "
                                  "Please set share=True or check your proxy settings to allow access to localhost."))
    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", lambda cfg, local=True: app)
    with pytest.raises(RuntimeError) as ei:
        launcher.launch({}, port=_free_base_port())
    assert "代理" in str(ei.value)


def test_launch_real_type_error_is_not_swallowed(fake_env):
    def build_app(cfg, local=True):
        raise TypeError("unsupported operand type(s) for +: 'int' and 'str'")

    fake_env.monkeypatch.setattr(fake_env.app_mod, "build_app", build_app)
    with pytest.raises(TypeError):
        launcher.launch({}, port=_free_base_port())


def test_banner_mentions_version_and_url():
    from voicetwin import __version__

    text = launcher.banner("http://127.0.0.1:7861")
    assert f"v{__version__}" in text and "http://127.0.0.1:7861" in text and "选择" in text


def test_cli_webui_uses_launcher(monkeypatch):
    from voicetwin import cli

    seen = {}

    def fake_launch(cfg, host="127.0.0.1", port=7860, share=False):
        seen.update(host=host, port=port, share=share)

    monkeypatch.setattr(launcher, "launch", fake_launch)
    cli.main(["webui", "--port", "7999"])
    assert seen == {"host": "127.0.0.1", "port": 7999, "share": False}
