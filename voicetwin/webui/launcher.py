"""启动网页界面：重复双击图标时直接打开已经在运行的网页；端口被占就自动换一个；出错时说中文。

用法：voicetwin webui（桌面图标 start_webui.bat 运行的就是它）。
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
import tempfile
import time
import urllib.request
import webbrowser
from typing import Any, List, Optional

APP_TITLE_MARK = "声音分身"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1", "[::1]")
WILDCARD_HOSTS = ("0.0.0.0", "::", "[::]", "")
SCAN_PORTS = 10  # 第一次启动时 7860 被占、改用了 7861……再次双击时也要能找到它

ALREADY_RUNNING_MSG = "声音分身已经在运行了（在另一个黑色窗口里），已经帮你打开网页。这个窗口可以关掉。"
ALREADY_RUNNING_REMOTE_MSG = "声音分身已经在运行了（在另一个黑色窗口里），网页地址：{url}。这个窗口可以关掉。"
STARTING_ELSEWHERE_MSG = ("声音分身正在另一个黑色窗口里启动（刚才可能连着双击了两次图标）。"
                          "请不要关掉那个窗口，这里等它启动好就帮你打开网页……")
#: 升级以后旧版本还开着（老师没关旧的黑色窗口）：不能打开旧网页（看不到新功能，以为升级失败）
OLD_RUNNING_MSG = ("另一个黑色窗口里还开着旧版本的声音分身（{old}），新版本 {new} 没法同时打开。\n"
                   "请把那个旧的黑色窗口关掉（点它右上角的 ×）。关掉以后这里会自动接着启动新版本，不用再双击图标。")
#: 等老师关掉旧版本最多等多久（秒）；等不到就说明怎么办
OLD_WAIT_SECONDS = 1800.0
#: 网页里藏着的版本号（launcher 用它分辨开着的是不是这个版本）
VERSION_ELEM_ID = "vt-version"
#: 另一个窗口正在启动时最多等多久（第一次启动、电脑慢时要 30 秒以上）
STARTUP_WAIT_SECONDS = 180.0
#: 端口突然被占（几乎都是同时启动了两个）时，再找几秒已经在运行的那个
PORT_RETRY_SECONDS = 15.0


def _quiet_gradio_env() -> None:
    """不向 gradio 官方发统计、不检查更新（必须在 import gradio 之前设置）。"""
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


#: gradio 的临时文件（发给网页播放 / 下载的音频、上传的视频）放在工作文件夹里的这个文件夹（名字以 __ 开头，声音库里不显示）
GRADIO_CACHE_DIR = "__gradio_cache"
#: 每次启动时删掉多久以前的临时文件（秒）
GRADIO_CACHE_MAX_AGE = 86400.0


def _use_workspace_cache(cfg: Any) -> Optional[str]:
    """gradio 发给网页的每个文件（播放、下载的音频）、上传的视频，都会在它的临时文件夹里复制一份。默认在 C 盘的
    %TEMP%\\gradio；老师关掉黑色窗口（点 ×）时 gradio 自己的清理不会运行，它定时的清理在 gradio 4.24 里也从来不删
    （见 app.GRADIO_DELETE_CACHE），一直越积越多。改放到工作文件夹里的 __gradio_cache，每次启动时删掉一天以前的。
    已经设了 GRADIO_TEMP_DIR 的照旧用那里（也不去清理）；共用的 %TEMP%\\gradio 不动（GPT-SoVITS 自己的网页也用它）。
    必须在建网页之前调用。返回用的文件夹（没改时返回 None）。"""
    if os.environ.get("GRADIO_TEMP_DIR"):
        return None
    try:
        from voicetwin.config import resolve_path

        ws = resolve_path(cfg, cfg.get("workspace", "./workspace"))
        if ws is None:
            return None
        cache = ws / GRADIO_CACHE_DIR
        cache.mkdir(parents=True, exist_ok=True)
    except Exception:  # noqa: BLE001 - 建不了就还用 gradio 默认的地方，不影响启动
        return None
    os.environ["GRADIO_TEMP_DIR"] = str(cache)
    _clean_old_files(str(cache), GRADIO_CACHE_MAX_AGE)
    return str(cache)


def _clean_old_files(folder: str, max_age: float, now: Optional[float] = None) -> int:
    """删掉文件夹里 max_age 秒以前的文件和空了的子文件夹，返回删了几个文件。删不掉的（Windows 上正被占用）下次再删。
    时间按「修改时间、放进来的时间」里晚的那个算（gradio 复制文件时保留原来的修改时间，刚复制的旧视频不能算旧的）。"""
    now = time.time() if now is None else now
    removed = 0
    for root, _dirs, files in os.walk(folder, topdown=False):
        for name in files:
            path = os.path.join(root, name)
            try:
                st = os.lstat(path)
                if now - max(st.st_mtime, st.st_ctime) > max_age:
                    os.remove(path)
                    removed += 1
            except OSError:
                pass
        if os.path.normpath(root) != os.path.normpath(folder):
            try:
                os.rmdir(root)  # 只有空的才删得掉
            except OSError:
                pass
    return removed


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


def _instance_version(url: str, timeout: float = 2.0) -> str:
    """开着的声音分身网页是哪个版本（网页里藏着的 vt-version）；旧版本没有这个，返回 ""。"""
    try:
        with _opener().open(url.rstrip("/") + "/config", timeout=timeout) as resp:
            data: Any = json.loads(resp.read(5_000_000).decode("utf-8", errors="replace"))
        for comp in (data or {}).get("components") or []:
            props = comp.get("props") if isinstance(comp, dict) else None
            if isinstance(props, dict) and props.get("elem_id") == VERSION_ELEM_ID:
                m = re.search(r"data-vt-version=\"([^\"]+)\"", str(props.get("value") or ""))
                return m.group(1) if m else ""
    except Exception:
        return ""
    return ""


def _port_listening(host: str, port: int, timeout: float = 0.3) -> bool:
    """这个端口上有没有程序在接受连接。"""
    try:
        with socket.create_connection((_browser_host(host).strip("[]"), port), timeout=timeout):
            return True
    except OSError:
        return False


def _bind_ok(host: str, port: int) -> bool:
    """这个端口现在能不能绑定（没有别的程序占着）。"""
    from voicetwin.utils.net import exclusive_bind_ok

    bind_host = "127.0.0.1" if host in LOOPBACK_HOSTS else (host.strip("[]") or "0.0.0.0")
    # Windows 默认允许不同的地址"共用"同一个端口，绑定测试会把占着的端口误当成空闲：用独占方式绑定（和推理服务选端口共用）
    return exclusive_bind_ok(bind_host, port)


def _free_port(preferred: int, host: str = "127.0.0.1") -> int:
    """从 preferred 开始找一个空闲端口（能绑定、而且没有程序在监听）。

    连接测试只是辅助（有的电脑上连接测试不可靠，空闲的端口也会显示"连得上"）：都不行时，
    退回到第一个能绑定的端口；一个都绑定不了时才返回 preferred。"""
    first_bindable: Optional[int] = None
    for port in [preferred] + list(range(preferred + 1, preferred + 50)):
        if port > 65535:
            break
        try:
            if not _bind_ok(host, port):  # 绑定测试很快，先做
                continue
            if first_bindable is None:
                first_bindable = port
            if not _port_listening(host, port):
                return port
        except Exception:
            continue
    return first_bindable if first_bindable is not None else preferred


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


def _acquire_instance_lock(port: int) -> Optional[int]:
    """同一时间只让一个声音分身启动（文件锁，进程退出时系统自动放开）。

    返回锁住的文件描述符；另一个声音分身正在启动 / 运行时返回 None；锁文件建不了时返回 -1（照常启动）。"""
    try:
        path = os.path.join(tempfile.gettempdir(), f"voicetwin_webui_{int(port)}.lock")
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o666)
    except OSError:
        return -1
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except ImportError:
        return fd  # 没有文件锁可用：照常启动
    except OSError:
        os.close(fd)
        return None


def _release_instance_lock(fd: Optional[int]) -> None:
    if fd is None or fd < 0:
        return
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, 0)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        os.close(fd)  # 关闭文件时锁也会放开
    except OSError:
        pass


def _open_existing(url: str, local: bool) -> None:
    if local:
        _say(ALREADY_RUNNING_MSG)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    else:
        _say(ALREADY_RUNNING_REMOTE_MSG.format(url=url))


def _wait_for_existing(host: str, ports: List[int], seconds: float) -> Optional[str]:
    """等几秒，看另一个窗口里的声音分身是不是启动好了；找到就返回它的地址。"""
    deadline = time.time() + max(0.0, seconds)
    while True:
        for port in ports:
            found = _find_existing(host, port)
            if found:
                return found
        if time.time() >= deadline:
            return None
        time.sleep(1.0)


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
        from voicetwin.utils.winsys import disable_quick_edit, use_chinese_console_font

        use_chinese_console_font()  # 老式黑色窗口没有中文字体时，中文提示会显示成 ?
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
        from voicetwin import __version__

        old = _instance_version(existing)
        if old == __version__:
            _open_existing(existing, local)
            return
        # 开着的是别的版本（升级以后旧的黑色窗口没关）：等老师关掉它，再启动这个版本
        _say(OLD_RUNNING_MSG.format(old=f"v{old}" if old else "旧版本", new=f"v{__version__}"))
        deadline = time.time() + OLD_WAIT_SECONDS
        while _find_existing(host, port):
            if time.time() >= deadline:
                raise RuntimeError("旧版本的声音分身一直开着。请关掉所有黑色窗口，再双击一次桌面上的「声音分身」图标。")
            time.sleep(2.0)
        _say("旧版本已经关掉了，正在启动新版本……")

    # 第一个窗口要先建好网页（10~30 秒）才会占住端口；这段时间里再双击一次图标，不能再启动一个
    lock = _acquire_instance_lock(port)
    if lock is None:
        _say(STARTING_ELSEWHERE_MSG)
        deadline = time.time() + STARTUP_WAIT_SECONDS
        while True:
            existing = _wait_for_existing(host, [port], 1.0)
            if existing:
                _open_existing(existing, local)
                return
            lock = _acquire_instance_lock(port)
            if lock is not None:  # 那个窗口没启动成功（已经关掉了）：这次自己启动
                break
            if time.time() >= deadline:
                raise RuntimeError("另一个黑色窗口里的声音分身一直没有启动好。请关掉所有黑色窗口，再双击一次桌面图标。")

    try:
        p = _free_port(port, host)
        if p != port:
            _say(f"{port} 端口被别的软件占用了，这次改用 {p} 端口。")
        url = _url(host, p)
        _say(banner(url))

        _use_workspace_cache(cfg)  # 这个窗口真的要启动网页了（不是去打开已经开着的那个）：临时文件放工作文件夹、清掉旧的
        app = _build(cfg, local)
        app.queue()
        try:
            app.launch(server_name=host, server_port=p, share=share, inbrowser=local, show_error=True,
                       show_api=False, quiet=not share)
        except OSError as exc:
            # 几乎都是同时启动了两个（另一个先占了端口）：那个能用，直接打开它，别让老师去关掉能用的那个窗口
            existing = _wait_for_existing(host, list(dict.fromkeys([p, port])), PORT_RETRY_SECONDS)
            if existing:
                _open_existing(existing, local)
                return
            raise RuntimeError(f"网页界面没能启动：端口 {p} 被占用。如果浏览器里已经打开了声音分身的网页，直接用它就行；"
                               "否则请重启电脑后再试。") from exc
        except ValueError as exc:
            if "localhost is not accessible" in str(exc) or "share=True" in str(exc):
                raise RuntimeError("网页界面没能启动：电脑上的代理软件（VPN、加速器）挡住了本机地址 127.0.0.1。"
                                   "请先关掉代理软件，或者在代理软件里把 127.0.0.1 和 localhost 设为「直连 / 不走代理」，"
                                   "然后重新双击桌面图标。") from exc
            raise
    finally:
        _release_instance_lock(lock)
