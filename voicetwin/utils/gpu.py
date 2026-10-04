"""显卡状态：网页顶部那一行「✅ 显卡正常 / ⚠️ 显存不多 / ❌ 显卡没有正常工作」。

- 不导入 gradio，命令行、环境检查和训练参数也能用。
- 任何情况下都不抛出异常：检查不了时返回 level='error' 或 'warn' 的结果。
- 结果缓存 10 秒；nvidia-smi 最多等 10 秒。第一次调用会导入 PyTorch，可能要几秒。

判断方法：
1. 能导入 PyTorch（GPT-SoVITS 整合包里的 CUDA 版）时，以 PyTorch 为准：
   torch.cuda.is_available()、get_device_name、显卡架构是否被这个 PyTorch 支持（RTX 50 + 旧整合包）。
2. 显存数字和驱动版本优先用 nvidia-smi 读（不会在网页进程里占用显存）；
   没有 nvidia-smi 时才用 torch.cuda.mem_get_info。
3. 没有 PyTorch 或者是 CPU 版 PyTorch（.venv 安装方式）时，以 nvidia-smi 为准。
   驱动坏掉时 nvidia-smi 也会输出一段报错文字，判断方法和 workflows.nvidia_smi_status 一样
   （这里复制一份，避免循环导入）。

字段：ok（显卡能用，warn 也算能用）、level（'ok' | 'warn' | 'error'）、name、total_gb / free_gb / used_gb
（PyTorch / nvidia-smi 报告的 GiB 原始数字，可能是 None）、nominal_gb（包装盒上的大小，只用于显示）、
driver、torch_cuda（None = 没有 PyTorch）、torch_version、message（一行中文）、advice（怎么办，正常时为 ''）、
detail（技术细节，给帮忙的人看）、source（'torch' | 'nvidia-smi' | 'none'）、count（显卡数量）、checked_at。
"""

from __future__ import annotations

import html
import locale
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

CACHE_SECONDS = 10.0
SMI_TIMEOUT = 10.0
DRIVER_URL = "https://www.nvidia.cn/drivers/lookup/"
SMI_QUERY = "--query-gpu=name,memory.total,memory.used,memory.free,driver_version"
SMI_FORMAT = "--format=csv,noheader,nounits"

# PyTorch / nvidia-smi 报的显存比包装盒上写的少一点（12 GB 的卡报 11.8~11.9）。
# GPT-SoVITS 官方代码也是加 0.4 再判断，所以档位和「显存小」的判断都先加上它。
REPORTED_FUDGE_GB = 0.4
LOW_FREE_GB = 2.0  # 可用显存少于它：提醒
SMALL_TOTAL_GB = 6.0  # 显存（按包装盒大小）少于它：提醒
TIER_MID_GB = 7.5  # 加 0.4 之后 ≥ 7.5 算 8 GB 档（mid）
TIER_HIGH_GB = 15.5  # 加 0.4 之后 ≥ 15.5 算 16 GB 档（high）

_GIB = 1024.0 ** 3
_LOCK = threading.Lock()
_CACHE: Optional[Tuple[float, Dict[str, Any]]] = None  # (time.monotonic(), 结果)

ADVICE_DRIVER = (f"请到 {DRIVER_URL} 下载安装最新的显卡驱动，装好后重启电脑，再重新打开声音分身。"
                 "RTX 50 系列显卡还需要使用 nvidia50 版的 GPT-SoVITS 整合包。")
ADVICE_NO_GPU = ("没有 N 卡（NVIDIA 显卡）也能用，但训练会非常慢（可能要十几个小时）。"
                 f"如果电脑其实有 N 卡，请到 {DRIVER_URL} 下载安装最新的显卡驱动，装好后重启电脑，再重新打开声音分身。")
ADVICE_ARCH = ("这个整合包太旧，认不出这块显卡。RTX 50 系列显卡请下载 nvidia50 版的 GPT-SoVITS 整合包，"
               "然后重新双击 install_windows.bat 安装一次（你的数据不会丢）。")
ADVICE_SMALL = ("显存小于 6 GB：训练和生成都会比较慢。如果训练时提示「显存不够」，可以在「② 训练模型」的「高级设置」里"
                "把「每批数量」改成 2。")
ADVICE_LOW_FREE = ("可用显存不到 2 GB：如果正在训练或生成，这是正常的；否则请关掉游戏、剪映、在线视频等占用显卡的程序，"
                   "再刷新一下网页（按 F5）。")
ADVICE_RETRY = "请刷新一下网页（按 F5）再试一次。"

MSG_BROKEN = "❌ 显卡没有正常工作"


# ---------------------------------------------------------------------------- 小工具
def smi_status(returncode: int, output: str) -> Tuple[bool, str]:
    """和 workflows.nvidia_smi_status 相同的判断：驱动没装好时 nvidia-smi 也会输出报错文字，不能当成正常。

    返回（是否正常, 正常时是完整输出，不正常时是第一行报错）。
    """
    text = (output or "").strip()
    if returncode != 0 or not text or "failed" in text.lower() or "error" in text.lower():
        first = text.splitlines()[0][:160] if text else "没有输出"
        return False, first
    return True, text


def _num(value: str) -> Optional[float]:
    """'12227' / '12227 MiB' → 12227.0；'[N/A]'、'[Not Supported]' → None。"""
    m = re.search(r"\d+(?:\.\d+)?", value or "")
    if not m or "n/a" in (value or "").lower() or "not supported" in (value or "").lower():
        return None
    try:
        v = float(m.group(0))
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def parse_nvidia_smi(output: str) -> List[Dict[str, Any]]:
    """解析 `nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,driver_version
    --format=csv,noheader,nounits` 的输出（每块显卡一行，显存单位 MiB）。

    也接受没有 memory.free 的四列格式（name,memory.total,memory.used,driver_version）。
    返回 [{'name', 'total_gb', 'used_gb', 'free_gb', 'driver'}]，显存为 GiB，可能是 None。
    """
    gpus: List[Dict[str, Any]] = []
    for line in (output or "").splitlines():
        fields = [f.strip() for f in line.split(",")]
        if len(fields) >= 5:  # 名字里万一有逗号：从右边数
            name, total, used, free, driver = ",".join(fields[:-4]), fields[-4], fields[-3], fields[-2], fields[-1]
        elif len(fields) == 4:
            name, total, used, driver = fields
            free = ""
        else:
            continue
        if not name:
            continue
        total_mib, used_mib, free_mib = _num(total), _num(used), _num(free)
        if free_mib is None and total_mib is not None and used_mib is not None:
            free_mib = max(total_mib - used_mib, 0.0)
        gpus.append({
            "name": name,
            "total_gb": None if total_mib is None else total_mib / 1024.0,
            "used_gb": None if used_mib is None else used_mib / 1024.0,
            "free_gb": None if free_mib is None else free_mib / 1024.0,
            "driver": "" if driver.startswith("[") else driver,
        })
    return gpus


def nominal_gb(total_gb: Optional[float]) -> Optional[float]:
    """显卡包装盒上写的大小（只用于显示）：11.94 → 12.0，7.6 → 8.0，23.65 → 24.0。"""
    if total_gb is None:
        return None
    try:
        t = float(total_gb)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(t) or t <= 0:
        return None
    if t + REPORTED_FUDGE_GB < 1.0:
        return round(t, 1)
    return float(math.floor(t + REPORTED_FUDGE_GB + 0.5))


def _round(v: Optional[float]) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return round(f, 2) if math.isfinite(f) else None


# ---------------------------------------------------------------------------- 外部探测（测试里会替换）
def _load_torch() -> Tuple[Any, str]:
    """返回（torch 模块或 None, 导入出错的说明）。Windows 上缺 DLL 时 import 会抛 OSError，也算没有。"""
    try:
        import torch  # type: ignore

        return torch, ""
    except ImportError:
        return None, ""
    except Exception as exc:  # OSError: [WinError 126] 等
        return None, f"{type(exc).__name__}: {exc}"[:300]


def _find_nvidia_smi() -> Optional[str]:
    exe = shutil.which("nvidia-smi")
    if exe:
        return exe
    if sys.platform.startswith("win"):  # 旧驱动把它装在 NVSMI 目录里，不一定在 PATH 上
        for cand in (
            os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "nvidia-smi.exe"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "NVIDIA Corporation", "NVSMI",
                         "nvidia-smi.exe"),
        ):
            if os.path.isfile(cand):
                return cand
    return None


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(locale.getpreferredencoding(False) or "utf-8", errors="replace")


def _run_nvidia_smi(exe: str) -> Tuple[int, str]:
    """运行 nvidia-smi，返回（退出码, 输出）。超时抛 subprocess.TimeoutExpired。"""
    kwargs: Dict[str, Any] = {}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.run([exe, SMI_QUERY, SMI_FORMAT], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL, timeout=SMI_TIMEOUT, **kwargs)
    return proc.returncode, _decode(proc.stdout or b"")


# ---------------------------------------------------------------------------- 分别问 PyTorch 和 nvidia-smi
def _query_smi() -> Optional[Dict[str, Any]]:
    """None = 没有 nvidia-smi；否则 {'ok', 'gpus', 'detail'}。"""
    exe = _find_nvidia_smi()
    if not exe:
        return None
    try:
        rc, out = _run_nvidia_smi(exe)
    except subprocess.TimeoutExpired:
        return {"ok": False, "gpus": [], "detail": f"nvidia-smi {int(SMI_TIMEOUT)} 秒没有响应", "timeout": True}
    except Exception as exc:
        return {"ok": False, "gpus": [], "detail": f"nvidia-smi 运行失败：{type(exc).__name__}: {exc}"[:300]}
    ok, text = smi_status(rc, out)
    if not ok:
        return {"ok": False, "gpus": [], "detail": f"nvidia-smi：{text}"}
    gpus = parse_nvidia_smi(text)
    if not gpus:
        first = text.splitlines()[0][:160] if text else ""
        return {"ok": False, "gpus": [], "detail": f"nvidia-smi 没有列出显卡：{first}"}
    return {"ok": True, "gpus": gpus, "detail": ""}


def _torch_info(torch: Any) -> Dict[str, Any]:
    """问 PyTorch：是不是 CUDA 版、能不能用显卡、显卡名字、架构支不支持。不会创建 CUDA 上下文（不占显存）。"""
    info: Dict[str, Any] = {"version": "", "cuda_build": False, "available": None, "name": "", "arch_ok": None,
                            "capability": "", "error": ""}
    try:
        info["version"] = str(getattr(torch, "__version__", "") or "")
    except Exception:
        pass
    try:
        info["cuda_build"] = bool(getattr(getattr(torch, "version", None), "cuda", None))
    except Exception:
        info["cuda_build"] = False
    try:
        info["available"] = bool(torch.cuda.is_available())
    except Exception as exc:
        info["available"] = False
        info["error"] = f"torch.cuda.is_available: {type(exc).__name__}: {exc}"[:300]
    if not info["available"]:
        return info
    try:
        info["name"] = str(torch.cuda.get_device_name(0) or "")
    except Exception as exc:  # 说能用，结果一问名字就报错：当成不能用
        info["available"] = False
        info["error"] = f"torch.cuda.get_device_name: {type(exc).__name__}: {exc}"[:300]
        return info
    try:  # 和 torch.cuda._check_cubins 一样：同一代（主版本号相同）的架构才算支持
        major, minor = torch.cuda.get_device_capability(0)
        info["capability"] = f"{int(major)}.{int(minor)}"
        supported = []
        for arch in list(torch.cuda.get_arch_list() or []):
            m = re.match(r"sm_(\d+)", str(arch))
            if m:
                supported.append(int(m.group(1)))
        if supported:
            info["arch_ok"] = any(sm // 10 == int(major) for sm in supported)
    except Exception:
        pass
    return info


def _torch_memory(torch: Any) -> Tuple[Optional[float], Optional[float]]:
    """（总显存, 可用显存）GiB。只在没有 nvidia-smi 时才用：mem_get_info 会在本进程里占一点显存。"""
    total: Optional[float] = None
    free: Optional[float] = None
    try:
        total = float(torch.cuda.get_device_properties(0).total_memory) / _GIB
    except Exception:
        pass
    try:
        free_b, total_b = torch.cuda.mem_get_info(0)
        free = float(free_b) / _GIB
        if total is None:
            total = float(total_b) / _GIB
    except Exception:
        pass
    return total, free


# ---------------------------------------------------------------------------- 组合成结论
def _mem_text(total: Optional[float], free: Optional[float]) -> str:
    parts = []
    nom = nominal_gb(total)
    if nom is not None:
        parts.append(f"显存 {nom:.1f} GB")
    if free is not None:
        parts.append(f"可用 {max(free, 0.0):.1f} GB")
    return "（" + "，".join(parts) + "）" if parts else ""


def _empty() -> Dict[str, Any]:
    return {
        "ok": False, "level": "error", "name": "", "total_gb": None, "free_gb": None, "used_gb": None,
        "nominal_gb": None, "driver": "", "torch_cuda": None, "torch_version": "", "message": "", "advice": "",
        "detail": "", "source": "none", "count": 0, "checked_at": time.time(),
    }


def _set_error(st: Dict[str, Any], reason: str, advice: str, more_detail: str = "") -> Dict[str, Any]:
    st.update(ok=False, level="error", message=f"{MSG_BROKEN}：{reason}" if reason else MSG_BROKEN, advice=advice)
    if more_detail:
        st["detail"] = "；".join(d for d in (st.get("detail") or "", more_detail) if d)
    return st


def _set_working(st: Dict[str, Any], name: str, total: Optional[float], free: Optional[float],
                 used: Optional[float]) -> Dict[str, Any]:
    if used is None and total is not None and free is not None:
        used = max(total - free, 0.0)
    if free is None and total is not None and used is not None:
        free = max(total - used, 0.0)
    st.update(name=name, total_gb=_round(total), free_gb=_round(free), used_gb=_round(used),
              nominal_gb=nominal_gb(total), ok=True)
    label = name or "NVIDIA 显卡"
    mem = _mem_text(total, free)
    if total is not None and total + REPORTED_FUDGE_GB < SMALL_TOTAL_GB:
        st.update(level="warn", message=f"⚠️ 显卡能用，但显存比较小：{label}{mem}", advice=ADVICE_SMALL)
    elif free is not None and free < LOW_FREE_GB:
        st.update(level="warn", message=f"⚠️ 显卡能用，但可用显存不多：{label}{mem}", advice=ADVICE_LOW_FREE)
    else:
        st.update(level="ok", message=f"✅ 显卡正常：{label}{mem}", advice="")
    return st


def _pick_gpu(gpus: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
    """和 PyTorch 的 0 号显卡对上：名字相同的那块，没有就用第一块。"""
    for g in gpus:
        if name and g.get("name") == name:
            return g
    return gpus[0]


def _probe() -> Dict[str, Any]:
    st = _empty()
    torch, torch_err = _load_torch()
    tinfo = _torch_info(torch) if torch is not None else None
    smi = _query_smi()
    smi_gpus: List[Dict[str, Any]] = smi["gpus"] if smi and smi.get("ok") else []
    if tinfo is not None:
        st["torch_version"] = tinfo["version"]
        st["torch_cuda"] = bool(tinfo["available"]) if tinfo["cuda_build"] else False
    st["count"] = len(smi_gpus)
    details = [d for d in (torch_err, tinfo["error"] if tinfo else "", smi["detail"] if smi else "") if d]
    st["detail"] = "；".join(details)
    if smi_gpus:
        st["driver"] = str(_pick_gpu(smi_gpus, tinfo["name"] if tinfo else "").get("driver") or "")

    if tinfo is not None and tinfo["cuda_build"]:
        # 整合包里的 CUDA 版 PyTorch：训练用的就是它，以它为准
        st["source"] = "torch"
        if not tinfo["available"]:
            if smi is None:
                return _set_error(st, "没有找到 NVIDIA 显卡（或者显卡驱动没装）", ADVICE_NO_GPU)
            if not smi.get("ok"):
                return _set_error(st, "显卡驱动没装好或出了问题", ADVICE_DRIVER)
            g = _pick_gpu(smi_gpus, "")
            st.update(name=g["name"], total_gb=_round(g["total_gb"]), nominal_gb=nominal_gb(g["total_gb"]))
            return _set_error(st, f"训练程序用不了这块显卡（{g['name']}）", ADVICE_DRIVER,
                              f"PyTorch {tinfo['version']} 的 torch.cuda.is_available() 是 False")
        name = tinfo["name"]
        if tinfo["arch_ok"] is False:
            st["name"] = name
            cap = f"，sm_{tinfo['capability'].replace('.', '')}" if tinfo["capability"] else ""
            return _set_error(st, f"这个 GPT-SoVITS 整合包不支持 {name or '这块显卡'}", ADVICE_ARCH,
                              f"PyTorch {tinfo['version']} 不支持这块显卡的架构{cap}")
        if smi_gpus:
            g = _pick_gpu(smi_gpus, name)
            return _set_working(st, name or g["name"], g["total_gb"], g["free_gb"], g["used_gb"])
        total, free = _torch_memory(torch)
        return _set_working(st, name, total, free, None)

    # 没有 PyTorch，或者是 CPU 版 PyTorch（.venv 安装方式，训练用的是整合包里的 Python）：以 nvidia-smi 为准
    if smi is None:
        return _set_error(st, "没有找到 NVIDIA 显卡（或者显卡驱动没装）", ADVICE_NO_GPU)
    st["source"] = "nvidia-smi"
    if not smi.get("ok"):
        return _set_error(st, "显卡驱动没装好或出了问题", ADVICE_DRIVER)
    g = smi_gpus[0]
    return _set_working(st, g["name"], g["total_gb"], g["free_gb"], g["used_gb"])


# ---------------------------------------------------------------------------- 对外接口
def clear_cache() -> None:
    global _CACHE
    with _LOCK:
        _CACHE = None


def _unknown(exc: BaseException) -> Dict[str, Any]:
    """检查过程本身出了意外：黄色提醒，ok=False，档位算 'none'。"""
    st = _empty()
    st.update(level="warn", message="⚠️ 暂时检查不了显卡状态", advice=ADVICE_RETRY,
              detail=f"{type(exc).__name__}: {exc}"[:300])
    return st


def gpu_status(refresh: bool = False) -> Dict[str, Any]:
    """检查显卡，结果缓存 CACHE_SECONDS 秒；refresh=True 时重新检查。永远不抛异常，返回新的 dict。"""
    global _CACHE
    try:
        with _LOCK:  # 同一时间只检查一次，几个网页同时打开时不会同时跑好几个 nvidia-smi
            if not refresh and _CACHE is not None and time.monotonic() - _CACHE[0] < CACHE_SECONDS:
                return dict(_CACHE[1])
            try:
                st = _probe()
            except Exception as exc:
                st = _unknown(exc)
            st["checked_at"] = time.time()
            _CACHE = (time.monotonic(), st)
            return dict(st)
    except Exception as exc:  # 连缓存都出问题（几乎不可能）：也不能让网页报错
        return _unknown(exc)


def vram_tier(status: Optional[Dict[str, Any]] = None) -> str:
    """显存档位：'none'（显卡用不了）| 'low'（< 8 GB）| 'mid'（8~16 GB 以下）| 'high'（≥ 16 GB）。

    按包装盒大小分档：PyTorch / nvidia-smi 报告的数字先加 0.4（8 GB 的卡常报 7.6~8.0），
    再用 7.5 / 15.5 分界，所以 6 GB → low，8 GB / 12 GB → mid，16 GB / 24 GB → high。
    status 不传时调用 gpu_status()。显卡能用但读不到显存大小时保守地返回 'low'。
    """
    try:
        if status is None:
            status = gpu_status()
        if not isinstance(status, dict):
            return "none"
        level = status.get("level")
        if level == "error" or status.get("ok") is False:
            return "none"
        total = status.get("total_gb")
        try:
            g = float(total) + REPORTED_FUDGE_GB if total is not None else None
        except (TypeError, ValueError):
            g = None
        if g is None or not math.isfinite(g) or g <= REPORTED_FUDGE_GB:
            return "low" if level in ("ok", "warn") or status.get("ok") is True else "none"
        if g < TIER_MID_GB:
            return "low"
        if g < TIER_HIGH_GB:
            return "mid"
        return "high"
    except Exception:
        return "none"


_URL_RE = re.compile(r"https?://[^\s<>\"'（），。；！？、]+")


def _linkify(escaped: str) -> str:
    return _URL_RE.sub(lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noopener">{m.group(0)}</a>', escaped)


def _tooltip(status: Dict[str, Any]) -> str:
    parts = []
    try:
        if status.get("checked_at"):
            parts.append("检查时间 " + time.strftime("%H:%M:%S", time.localtime(float(status["checked_at"]))))
    except Exception:
        pass
    if status.get("driver"):
        parts.append(f"驱动 {status['driver']}")
    if status.get("torch_version"):
        tc = status.get("torch_cuda")
        parts.append(f"PyTorch {status['torch_version']}" + ("（能用显卡）" if tc else "（用不了显卡）" if tc is False else ""))
    if status.get("total_gb") is not None:
        parts.append(f"报告显存 {status['total_gb']} GiB")
    if (status.get("count") or 0) > 1:
        parts.append(f"共 {status['count']} 块显卡")
    if status.get("detail"):
        parts.append(str(status["detail"]))
    return "；".join(parts)


def render_gpu_badge_html(status: Optional[Dict[str, Any]] = None) -> str:
    """一行显卡状态：<div class="vt-gpu vt-gpu-ok|warn|error">…</div>。出错时是红色并带「怎么办」。

    status 不传时调用 gpu_status()。永远不抛异常。
    """
    try:
        if status is None:
            status = gpu_status()
        level = status.get("level")
        if level not in ("ok", "warn", "error"):
            level = "warn"
        msg = str(status.get("message") or "").strip()
        if not msg:
            msg = {"ok": "✅ 显卡正常", "warn": "⚠️ 显卡状态需要留意", "error": MSG_BROKEN}[level]
        advice = str(status.get("advice") or "").strip()
        body = html.escape(msg, quote=False)
        if advice and level != "ok":
            body += f' <span class="vt-gpu-advice">怎么办：{_linkify(html.escape(advice, quote=False))}</span>'
        tip = html.escape(_tooltip(status), quote=True)
        title = f' title="{tip}"' if tip else ""
        return f'<div class="vt-gpu vt-gpu-{level}" data-level="{level}"{title}>{body}</div>'
    except Exception:
        return ('<div class="vt-gpu vt-gpu-warn" data-level="warn">⚠️ 暂时检查不了显卡状态 '
                f'<span class="vt-gpu-advice">怎么办：{ADVICE_RETRY}</span></div>')


def render_gpu_pending_html() -> str:
    """还没检查完时先显示的一行（可选，用作 gr.HTML 的初始值）。"""
    return '<div class="vt-gpu vt-gpu-pending" data-level="pending">⏳ 正在检查显卡……</div>'


# ---------------------------------------------------------------------------- 训练 / 生成时实测显卡用了多少
SMI_SAMPLE_QUERY = "--query-gpu=index,memory.used,memory.total,utilization.gpu"
SMI_SAMPLE_TIMEOUT = 5.0


def smi_sample(index: Any = 0) -> Optional[Dict[str, float]]:
    """用 nvidia-smi 量一次第 index 块显卡：{"used_gb", "total_gb", "util"（使用率 %）}（GiB 原始数字）。

    没有 nvidia-smi、超时、读不出来时返回 None（不猜）。永远不抛异常。"""
    try:
        exe = _find_nvidia_smi()
        if not exe:
            return None
        kwargs: Dict[str, Any] = {}
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        proc = subprocess.run([exe, SMI_SAMPLE_QUERY, SMI_FORMAT], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, timeout=SMI_SAMPLE_TIMEOUT, **kwargs)
        ok, text = smi_status(proc.returncode, _decode(proc.stdout or b""))
        if not ok:
            return None
        want = str(index if index is not None else 0).split(",")[0].strip() or "0"
        for line in text.splitlines():
            fields = [f.strip() for f in line.split(",")]
            if len(fields) < 4 or fields[0] != want:
                continue
            used, total, util = _num(fields[1]), _num(fields[2]), _num(fields[3])
            if used is None or total is None:
                return None
            return {"used_gb": used / 1024.0, "total_gb": total / 1024.0, "util": util}
    except Exception:
        return None
    return None


class GpuSampler:
    """后台每 interval 秒用 nvidia-smi 量一次显卡（smi_sample），stop() 时返回实测的平均使用率和最高显存：
    {"util_avg": %, "peak_gb": GiB, "n": 量了几次}。没有 nvidia-smi（第一次就量不出来）时什么都不做，
    返回 {"util_avg": None, "peak_gb": None, "n": 0}——没量到的数字不显示。

    只算 start() 和 stop() 之间后台量到的：start() 里那一次只是看 nvidia-smi 能不能用（那时训练程序还没开始），
    stop() 也不再补量（训练程序已经结束了，显卡闲着）——这两次都会把平均使用率拉低。"""

    def __init__(self, interval: float = 5.0, index: Any = 0) -> None:
        self.interval = max(0.05, float(interval))
        self.index = index
        self._utils: List[float] = []
        self._peak: Optional[float] = None
        self._n = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _take(self) -> bool:
        s = smi_sample(self.index)
        if not s:
            return False
        if self._stop.is_set():  # stop() 已经叫停了：训练程序结束以后量到的不算
            return True
        with self._lock:
            self._n += 1
            if s.get("util") is not None:
                self._utils.append(float(s["util"]))
            used = s.get("used_gb")
            if used is not None and (self._peak is None or used > self._peak):
                self._peak = float(used)
        return True

    def start(self) -> "GpuSampler":
        if self._thread is not None or not smi_sample(self.index):   # 只看能不能量，这一次不算
            return self

        def loop() -> None:
            while not self._stop.wait(self.interval):
                self._take()

        self._thread = threading.Thread(target=loop, name="vt-gpu-sampler", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> Dict[str, Any]:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + SMI_SAMPLE_TIMEOUT + 1)
        with self._lock:
            util = round(sum(self._utils) / len(self._utils), 1) if self._utils else None
            peak = round(self._peak, 2) if self._peak is not None else None
            return {"util_avg": util, "peak_gb": peak, "n": self._n}


GPU_CSS = """
.vt-gpu{display:block;box-sizing:border-box;width:100%;margin:2px 0 6px;padding:8px 14px;border:1px solid;
  border-left-width:6px;border-radius:8px;font-size:15px;line-height:1.6;font-weight:600;word-break:break-word}
.vt-gpu a{color:inherit;text-decoration:underline}
.vt-gpu-advice{font-weight:400;margin-left:4px}
.vt-gpu-ok{color:#166534;background:#f0fdf4;border-color:#16a34a}
.vt-gpu-warn{color:#92400e;background:#fffbeb;border-color:#d97706}
.vt-gpu-error{color:#991b1b;background:#fef2f2;border-color:#dc2626}
.vt-gpu-pending{color:#374151;background:#f3f4f6;border-color:#6b7280;font-weight:400}
.dark .vt-gpu-ok{color:#bbf7d0;background:rgba(22,163,74,.18)}
.dark .vt-gpu-warn{color:#fde68a;background:rgba(217,119,6,.18)}
.dark .vt-gpu-error{color:#fecaca;background:rgba(220,38,38,.20)}
.dark .vt-gpu-pending{color:#e5e7eb;background:rgba(107,114,128,.20)}
"""
