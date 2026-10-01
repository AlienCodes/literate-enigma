"""启动网页界面：重复双击图标时直接打开已经在运行的网页；端口被占就自动换一个；出错时说中文。

用法：voicetwin webui（桌面图标 start_webui.bat 运行的就是它）。
"""

from __future__ import annotations

import json
import os
import socket
import sys
import urllib.request
import webbrowser
from typing import Any, List, Optional

APP_TITLE_MARK = "声音分身"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1", "[::1]")
WILDCARD_HOSTS = ("0.0.0.0", "::", "[::]", "")
SCAN_PORTS = 10  # 第一次启动时 7860 被占、改用了 7861……再次双击时也要能找到它

ALREADY_RUNNING_MSG = "声音分身已经在运行了（在另一个黑色窗口里），已经帮你打开网页。这个窗口可以关掉。"
ALREADY_RUNNING_REMOTE_MSG = "声音分身已经在运行了（在另一个黑色窗口里），网页地址：{url}。这个窗口可以关掉。"


def _quiet_gradio_env() -> None:
    """不向 gradio 官方发统计、不检查更新（必须在 import gradio 之前设置）。"""
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


def _split_hosts(value: str) -> List[str]:
    return [h.strip() for h in (value or "").split(",") if h.strip()]


def _prepare_proxy_env() -> None:
    """让本机地址不走代理，同时保留下载模型用的代理。

    gradio 启动时会用 httpx 访问 http://127.0.0.1:端口 自检；电脑开着代理软件（系统代理）时，这个请求会被转给代理，
    然后 gradio 报一句英文「请设置 share=True」就退出。Windows 上环境变量里一旦有任何 *_proxy，Python 就不再读取
    注册表里的系统代理，所以先把系统代理（http/https）抄到环境变量里，再把本机地址加进 no_proxy。
    """
    try:
        names = ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")
        if sys.platform == "win32" and not any(os.environ.get(n) for n in names):
            try:
                reg = urllib.request.getproxies_registry()  # type: ignore[attr-defined]
            except Exception:
                reg = {}
            for scheme in ("http", "https"):
                value = (reg or {}).get(scheme)
                if value:
                    os.environ[f"{scheme}_proxy"] = value
                    os.environ[f"{scheme.upper()}_PROXY"] = value
        # 不加 "::1"：旧版 httpx 解析不了 no_proxy 里的 IPv6 地址，反而会让所有请求出错
        local = ["localhost", "127.0.0.1"]
        for name in ("no_proxy", "NO_PROXY"):
            hosts = _split_hosts(os.environ.get(name, ""))
            lowered = {h.lower() for h in hosts}
            hosts += [h for h in local if h not in lowered]
            os.environ[name] = ",".join(hosts)
    except Exception:  # 只是增强，出任何问题都不影响启动
        pass


def _browser_host(host: str) -> str:
    """浏览器里应该打开的主机名。"""
    if host in WILDCARD_HOSTS or host in LOOPBACK_HOSTS:
        return "127.0.0.1"
    return host


def _url(host: str, port: int) -> str:
    h = _browser_host(host)
    if ":" in h and not h.startswith("["):
        h = f"[{h}]"
    return f"http://{h}:{port}"


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))  # 访问本机，不走任何代理


def _existing_instance(url: str, timeout: float = 2.0) -> bool:
    """url 上是不是已经有一个声音分身网页在运行（看 /config 里的网页标题）。"""
    try:
        with _opener().open(url.rstrip("/") + "/config", timeout=timeout) as resp:
            if getattr(resp, "status", 200) != 200:
                return False
            data: Any = json.loads(resp.read(2_000_000).decode("utf-8", errors="replace"))
        return APP_TITLE_MARK in str((data or {}).get("title", ""))
    except Exception:
        return False


def _port_listening(host: str, port: int, timeout: float = 0.3) -> bool:
    """这个端口上有没有程序在接受连接。"""
    try:
        with socket.create_connection((_browser_host(host).strip("[]"), port), timeout=timeout):
            return True
    except OSError:
        return False


def _bind_ok(host: str, port: int) -> bool:
    bind_host = "127.0.0.1" if host in LOOPBACK_HOSTS else (host.strip("[]") or "0.0.0.0")
    family = socket.AF_INET6 if ":" in bind_host else socket.AF_INET
    with socket.socket(family, socket.SOCK_STREAM) as s:
        try:
            s.bind((bind_host, port))
            return True
        except OSError:
            return False


def _free_port(preferred: int, host: str = "127.0.0.1") -> int:
    """从 preferred 开始找一个空闲端口（能绑定、而且没有程序在监听）。都不行时返回 preferred。"""
    for port in [preferred] + list(range(preferred + 1, preferred + 50)):
        if port > 65535:
            break
        try:
            # 先用绑定测试（很快）；Windows 上别的程序监听 0.0.0.0 时绑定 127.0.0.1 也可能成功，所以再试着连一下
            if _bind_ok(host, port) and not _port_listening(host, port):
                return port
        except Exception:
            continue
    return preferred


def _find_existing(host: str, preferred: int, span: int = SCAN_PORTS) -> Optional[str]:
    """在 preferred 附近找已经在运行的声音分身网页，返回它的地址。"""
    for port in range(preferred, min(preferred + span, 65536)):
        try:
            # 绑定失败 = 有程序占着这个端口（很快）；只对首选端口再额外试连一次（Windows 上连接关闭的端口比较慢）
            busy = not _bind_ok(host, port) or (port == preferred and _port_listening(host, port))
        except Exception:
            busy = False
        if busy and _existing_instance(_url(host, port)):
            return _url(host, port)
    return None


def banner(url: str) -> str:
    try:
        from voicetwin import __version__
    except Exception:  # pragma: no cover
        __version__ = "?"
    line = "=" * 50
    return (f"{line}\n"
            f"  声音分身 VoiceTwin v{__version__} 正在启动\n"
            f"  网页地址：{url}\n"
            f"  浏览器没有自动打开？把上面的地址复制到浏览器地址栏\n"
            f"  使用期间请不要关闭这个黑色窗口（可以最小化）\n"
            f"  不要用鼠标点击这个黑色窗口里面；如果窗口标题出现「选择」两个字，按一下回车键就能继续\n"
            f"{line}")


def _say(text: str) -> None:
    try:
        print(text, flush=True)
    except Exception:  # 控制台编码不支持时也不要因为打印失败而退出
        try:
            sys.stdout.write(text.encode("ascii", "replace").decode("ascii") + "\n")
            sys.stdout.flush()
        except Exception:
            pass


def _build(cfg: Any, local: bool) -> Any:
    from voicetwin.webui.app import build_app

    try:
        return build_app(cfg, local=local)
    except TypeError as exc:
        if "local" not in str(exc):  # build_app 内部真正的 TypeError 不要吞掉
            raise
        return build_app(cfg)


def launch(cfg: Any, host: str = "127.0.0.1", port: int = 7860, share: bool = False) -> None:
    """启动网页界面（会一直运行，直到关闭黑色窗口或按 Ctrl+C）。"""
    _quiet_gradio_env()
    try:
        from voicetwin.utils.winsys import disable_quick_edit

        disable_quick_edit()
    except Exception:
        pass
    _prepare_proxy_env()
    try:
        import gradio  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("网页界面需要 gradio 组件，但是没有装上。请重新双击 install_windows.bat 安装一次"
                           "（命令行用户：pip install \"voicetwin[webui]\"）。") from exc

    host = (host or "127.0.0.1").strip()
    port = int(port or 7860)
    local = host in LOOPBACK_HOSTS and not share

    existing = _find_existing(host, port)
    if existing:
        if local:
            _say(ALREADY_RUNNING_MSG)
            try:
                webbrowser.open(existing)
            except Exception:
                pass
        else:
            _say(ALREADY_RUNNING_REMOTE_MSG.format(url=existing))
        return

    p = _free_port(port, host)
    if p != port:
        _say(f"{port} 端口被别的软件占用了，这次改用 {p} 端口。")
    url = _url(host, p)
    _say(banner(url))

    app = _build(cfg, local)
    app.queue()
    try:
        app.launch(server_name=host, server_port=p, share=share, inbrowser=local, show_error=True,
                   show_api=False, quiet=not share)
    except OSError as exc:
        raise RuntimeError(f"网页界面没能启动：端口 {p} 被占用。请关掉其它黑色窗口，或者重启电脑后再试。") from exc
    except ValueError as exc:
        if "localhost is not accessible" in str(exc) or "share=True" in str(exc):
            raise RuntimeError("网页界面没能启动：电脑上的代理软件（VPN、加速器）挡住了本机地址 127.0.0.1。"
                               "请先关掉代理软件，或者在代理软件里把 127.0.0.1 和 localhost 设为「直连 / 不走代理」，"
                               "然后重新双击桌面图标。") from exc
        raise
