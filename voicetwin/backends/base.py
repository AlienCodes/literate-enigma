"""合成引擎统一接口。"""

from __future__ import annotations

import dataclasses
import itertools
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from voicetwin.backends.worker import subprocess_env
from voicetwin.config import Config, resolve_path
from voicetwin.project import Project
from voicetwin.utils.log import get_logger
from voicetwin.utils.winsys import kill_with_parent

try:  # U1：停止按钮（CANCEL 事件 + TaskCancelled）
    from voicetwin.utils.progress import CANCEL as _CANCEL
    from voicetwin.utils.progress import TaskCancelled
except ImportError:  # pragma: no cover - 单独合并 U4 时
    _CANCEL = None

    class TaskCancelled(BaseException):  # type: ignore[no-redef]
        """用户点了停止（没有 utils.progress 时的替身）。"""

log = get_logger("backend")
ProgressFn = Callable[[float, str], None]
Stage = Tuple[float, str]
ParseResult = Union[None, float, Tuple[float, str]]

#: 训练子进程日志里出现这些字样，就是显卡内存（显存）不够
OOM_PATTERN = re.compile(
    r"CUDA out of memory|CUDA error: out of memory|OutOfMemoryError|CUBLAS_STATUS_ALLOC_FAILED|"
    r"CUDNN_STATUS_ALLOC_FAILED|cudaErrorMemoryAllocation|CUDA_ERROR_OUT_OF_MEMORY", re.I)

#: 多久检查一次「停止」按钮（秒）
CANCEL_POLL_SECONDS = 1.0
#: 同一步里，两行进度日志之间至少隔多久（秒）；每走 10% 和「…轮完成」不受限制
LOG_EVERY_SECONDS = 15.0
#: 失败时报错里带多少行日志尾巴
TAIL_LINES = 30
#: 一次要好几个版本、一个一个生成时，第 k 个用的随机种子是 seed + k × SEED_STEP
#: （和生成引擎里每个候选之间相差的数一样；一个大质数，和每句之间相差的 7919 错开，不会撞上别的句子的种子）
SEED_STEP = 104729
#: synthesize_many 写的文件名 = 这次运行程序随机取的一串字 + 这次运行里的流水号。
#: 流水号每次运行都从 1 数起，只靠它的话，下次运行写进同一个文件夹会覆盖上次的文件，所以前面加上这串字
_MANY_RUN = uuid.uuid4().hex[:8]
_MANY_IDS = itertools.count(1)


def many_prefix(out_dir: Path) -> str:
    """synthesize_many 这一次调用写的文件名开头（后面接 _r0.wav、_b4_r0.wav……）。

    同一个文件夹里多次调用、哪怕是不同次运行程序写进去的，也不会重名、互相覆盖：
    万一文件夹里已经有这个开头的文件（几乎不会发生），就换下一个流水号。"""
    while True:
        prefix = f"many{_MANY_RUN}-{next(_MANY_IDS)}"
        if not any(Path(out_dir).glob(prefix + "_*")):
            return prefix


@dataclass
class SynthRequest:
    text: str
    lang: str                       # zh（可夹英文）| en
    ref_audio: Path
    ref_text: str
    ref_lang: str
    aux_refs: List[Path] = field(default_factory=list)
    seed: int = 0
    speed: float = 1.0
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


class TrainStepError(RuntimeError):
    """训练类子进程失败（退出码不是 0）。

    消息第一行是中文说明（能认出原因时带上原因），第二行保留「<日志名> 失败（退出码 N）」，
    errors.explain 靠它认出是哪一步。属性 oom=True 表示日志里出现了显存不够。"""

    def __init__(self, message: str, log_name: str = "", label: str = "", code: Optional[int] = None,
                 tail: Optional[List[str]] = None, log_path: Optional[Path] = None, oom: bool = False) -> None:
        super().__init__(message)
        self.log_name = log_name
        self.label = label
        self.code = code
        self.tail = list(tail or [])
        self.log_path = log_path
        self.oom = oom


def cancel_requested() -> bool:
    """用户是不是点了「停止」。"""
    return _CANCEL is not None and _CANCEL.is_set()


def check_cancel() -> None:
    """点了「停止」就抛出 TaskCancelled（没有 utils.progress 时什么都不做）。"""
    if cancel_requested():
        raise TaskCancelled("已按你的要求停止")


def kill_process_tree(proc: Optional["subprocess.Popen[Any]"]) -> None:
    """结束子进程以及它开的所有子进程（GPT-SoVITS 的 s2_train 用 mp.spawn 开了子进程）。永远不抛异常。

    Windows 用 taskkill /F /T；其它系统靠启动时的 start_new_session（进程组）用 killpg 一起结束。"""
    if proc is None:
        return
    if os.name == "nt":
        try:
            if proc.poll() is None:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=30,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)  # type: ignore[attr-defined]
        except Exception:
            pass
    try:
        if proc.poll() is None:
            proc.kill()
    except Exception:
        pass


def _explain_title(text: str) -> str:
    """用 errors.explain 认出日志尾巴里的根本原因（认不出时返回 ''）。"""
    try:
        from voicetwin.errors import explain
    except ImportError:  # pragma: no cover - 单独合并 U4 时
        return ""
    try:
        f = explain(text)
    except Exception:  # pragma: no cover - explain 自己保证不抛异常
        return ""
    if getattr(f, "key", "") in ("", "unknown", "app", "stopped"):
        return ""
    return str(getattr(f, "title", "") or "")


def _step_name(log_name: str, label: str) -> str:
    if label:
        return label
    try:
        from voicetwin.errors import STEP_NAMES
    except ImportError:  # pragma: no cover
        return log_name
    return STEP_NAMES.get(log_name, log_name)


#: 文件名里的模型名找不到 / 检测不出来时写这个（老师的规定：绝不猜）
MODEL_UNKNOWN = "模型未知"
_FP_CACHE: Dict[Tuple[str, int, int], str] = {}


def model_label(version: Any) -> Optional[str]:
    """检测出来的模型版本 → 文件名、网页、报告里统一的写法（老师定的）：v4 → V4、v5 → V5（「v + 一个数字」写成大写 V），
    v2ProPlus、v2Pro 照原样；只留英文字母和数字（不放点、空格）。没有版本（检测不出来）返回 None。"""
    v = str(version or "").strip()
    if not v:
        return None
    m = re.fullmatch(r"[vV](\d+)", v)
    if m:
        return f"V{m.group(1)}"
    v = re.sub(r"[^A-Za-z0-9]", "", v)
    return v or None


def file_fingerprint(path: Any) -> str:
    """模型文件的指纹：整个文件内容的 sha256 前 16 位（写进报告：以后能核对生成时用的到底是哪个文件）。
    同一个文件（路径、大小、修改时间都一样）只算一次；读不了时是空字符串。"""
    import hashlib

    try:
        p = Path(str(path))
        st = p.stat()
        key = (str(p), int(st.st_size), int(st.st_mtime_ns))
        got = _FP_CACHE.get(key)
        if got is None:
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for block in iter(lambda: fh.read(1 << 20), b""):
                    h.update(block)
            got = _FP_CACHE[key] = h.hexdigest()[:16]
        return got
    except (OSError, ValueError):
        return ""


class Backend:
    name = "base"
    display_name = "base"
    supports_training = False
    supports_speed = False           # 引擎本身能否调语速（不能的话由 ffmpeg atempo 变速不变调后处理）
    supports_aux_refs = False
    #: 一次请求能不能同时生成同一句话的好几个版本（synthesize_many 真的「同时」生成，而不是一个一个来）
    supports_batch = False
    #: 显存不够、一次只生成一个也不够时，先调用它让出显存（由生成引擎登记，例如把识别校验模型从显卡上拿下来），
    #: 再试一次；它返回真值表示真的让出了显存（CERChecker.release_gpu 卸掉了模型时返回 True）；None 表示没有登记
    release_gpu_callback: Optional[Callable[[], Any]] = None
    #: 训练的各个步骤（在这个引擎自己的 0~1 进度里的起点, 中文步骤名），从小到大
    train_stages: List[Stage] = [(0.0, "训练模型")]
    #: 生成的文件名最后写的「_模型名」（不需要训练、没有模型文件可以检测的引擎写自己的名字；None = 检测不出来）。
    #: GPT-SoVITS 不看这个：按每句实际用的模型文件检测（gptsovits.model_name_info）
    file_model_name: Optional[str] = None

    def __init__(self, cfg: Config, project: Project):
        self.cfg = cfg
        self.project = project
        self.bcfg: Dict[str, Any] = cfg.backend(self.name)
        self.work_dir = project.models_dir / self.name
        self.work_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ 生命周期
    def start(self) -> None:
        pass

    def start_hint(self) -> str:
        """进度条上「启动合成引擎」后面的说明（只写测出来的，例如「上次用了 40 秒」）；不知道就是空字符串。"""
        return ""

    def stop(self) -> None:
        pass

    def __enter__(self) -> "Backend":
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.stop()

    # ------------------------------------------------------------------ 合成
    def synthesize(self, req: SynthRequest, out_path: Path) -> Path:
        raise NotImplementedError

    def synthesize_many(self, req: SynthRequest, n: int, out_dir: Path) -> List[Tuple[Path, int]]:
        """同一句话要 n 个版本，写进 out_dir，返回 [(文件, 第几个)]，第几个从 0 数起。

        这里是通用的做法：一个一个生成，第 k 个用随机种子 seed + k × SEED_STEP。
        能在一次请求里同时生成好几个的引擎（supports_batch）自己实现；那时返回的个数可能比 n 少
        （比如显存不够、自动减少了同时生成的数量），调用的地方按实际拿到的个数算。"""
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = many_prefix(out_dir)
        out: List[Tuple[Path, int]] = []
        for k in range(max(1, int(n))):
            check_cancel()
            one = dataclasses.replace(req, seed=int(req.seed) + k * SEED_STEP)
            out.append((Path(self.synthesize(one, out_dir / f"{prefix}_r{k}.wav")), k))
        return out

    def model_id(self) -> str:
        """当前使用的模型标识（参与缓存键，换模型后缓存自动失效）。"""
        return self.name

    def model_name_info(self) -> Dict[str, Any]:
        """这一刻生成实际用的模型叫什么（生成的文件名最后的「_模型名」、文件里面的注释、报告都用它）：
        {"name": "V4" / None（检测不出来）, "how": 依据（中文）, "files": [{"kind", "file", "fingerprint"}]}。
        通用的引擎没有模型文件可以检测：写引擎自己的名字（file_model_name）；没有名字就是 None（文件名写「模型未知」）。"""
        name = self.file_model_name
        return {"name": name, "how": "引擎名（这个引擎没有要检测的模型文件）" if name else "这个引擎读不出模型名",
                "files": []}

    # ------------------------------------------------------------------ 训练 / 检查点
    def check(self) -> List[str]:
        """返回安装/配置问题列表（空列表表示一切正常）。"""
        return []

    def training_plan(self, **opts: Any) -> Dict[str, Any]:
        """训练前预览：这次会自动用什么训练设置（不训练）。不支持的引擎返回 {}。

        返回的 dict 里 'summary' 是一行中文说明，网页可以在点「开始训练」前后显示。"""
        return {}

    def train(self, progress: Optional[ProgressFn] = None, **opts: Any) -> Dict[str, Any]:
        raise NotImplementedError(f"{self.display_name} 不支持微调训练（只能零样本克隆）")

    def checkpoints(self) -> List[Dict[str, Any]]:
        """可供自动挑选的模型组合，例如 [{"id": "s8-g15", ...}, ...]。"""
        return []

    def use_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        pass

    def selected_checkpoint(self) -> Optional[Dict[str, Any]]:
        return (self.project.load_models().get(self.name) or {}).get("selected")

    def speed_calibration(self) -> Dict[str, float]:
        return (self.project.load_models().get(self.name) or {}).get("speed", {}) or {}

    # ------------------------------------------------------------------ 工具
    @staticmethod
    def step(progress: Optional[ProgressFn], frac: float, msg: str) -> None:
        """报告一个训练阶段：写入日志（网页/命令行可见），并更新进度条。

        进度条自己出的小错误不影响训练；用户点了停止（TaskCancelled）会照常传出去。"""
        log.info(msg)
        if progress:
            try:
                progress(frac, msg)
            except Exception:
                pass

    def resolve(self, key: str, default: str = "") -> Optional[Path]:
        return resolve_path(self.cfg, self.bcfg.get(key, default))

    def run_logged(self, cmd: List[Any], cwd: Optional[Path], env: Dict[str, str], log_name: str,
                   progress: Optional[ProgressFn] = None, progress_range: Tuple[float, float] = (0.0, 1.0),
                   parse_progress: Optional[Callable[[str], ParseResult]] = None, *, label: str = "",
                   poll_progress: Optional[Callable[[], Optional[Tuple[int, int]]]] = None,
                   poll_interval: float = 2.0, stop_when: Optional[Callable[[str], Any]] = None,
                   on_poll: Optional[Callable[[], Any]] = None) -> Dict[str, Any]:
        """运行训练类子进程：输出完整写进 logs/<log_name>.log，主日志只写简短的中文进度。

        - parse_progress(line) 可以返回 None、0~1 的小数，或 (小数, 中文说明)。
        - poll_progress() 返回 (已完成, 总数)：后台每 poll_interval 秒数一次文件（脚本自己不打印进度时用）。
        - stop_when(line) 返回真值、或 on_poll()（后台每 poll_interval 秒调用一次）返回 True：程序自己要它停下
          （例如「实测显卡一次能练几条」练够了步数）。结束整个子进程树，正常返回（不算失败）。
        - 点了停止：结束整个子进程树，抛出 TaskCancelled。
        - 失败：抛出 TrainStepError，第一行是中文说明，后面带日志尾巴。
        返回 {"stopped": 是不是程序自己让它停下的, "code": 退出码, "oom": 日志里有没有显存不够}。
        """
        check_cancel()
        log_path = self.project.logs_dir / f"{log_name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        step_name = _step_name(log_name, label)
        log.info(f"▶ {step_name}（详细日志：{log_path.name}）")
        lo, hi = float(progress_range[0]), float(progress_range[1])
        tail: List[str] = []
        oom = False
        lock = threading.Lock()
        state: Dict[str, Any] = {"key": None, "decile": -1, "logged_at": 0.0}

        def report(frac: float, text: str, key: Optional[str]) -> None:
            frac = max(0.0, min(1.0, frac))
            now = time.time()
            with lock:
                decile = int(frac * 10 + 1e-9)
                k = key if key is not None else str(decile)
                log_it = decile > state["decile"] or (
                    k != state["key"] and ("完成" in text or now - state["logged_at"] >= LOG_EVERY_SECONDS))
                if log_it:
                    state["logged_at"] = now
                    log.info(f"  {text}")
                state["decile"] = max(decile, state["decile"])
                state["key"] = k
                if progress is not None:
                    try:
                        progress(lo + (hi - lo) * frac, text)
                    except Exception:
                        pass

        done = threading.Event()
        cancelled = threading.Event()
        stopped = threading.Event()
        threads: List[threading.Thread] = []
        proc_box: List[Any] = []

        def request_stop() -> None:
            if not stopped.is_set():
                stopped.set()
                if proc_box:
                    kill_process_tree(proc_box[0])
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        popen_extra: Dict[str, Any] = {} if os.name == "nt" else {"start_new_session": True}
        cmd_s = [str(c) for c in cmd]
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} {step_name} =====\n"
                     f"命令：{subprocess.list2cmdline(cmd_s)}\n目录：{cwd or os.getcwd()}\n")
            fh.flush()
            proc = subprocess.Popen(cmd_s, cwd=str(cwd) if cwd else None, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, bufsize=0, creationflags=creationflags, **popen_extra)
            kill_with_parent(proc)  # 关掉声音分身时训练进程一起结束，不留在后台占显卡
            proc_box.append(proc)
            finished = False
            try:
                if _CANCEL is not None:
                    def watch_cancel() -> None:
                        while not done.wait(CANCEL_POLL_SECONDS):
                            if _CANCEL.is_set():
                                cancelled.set()
                                log.info(f"正在停止「{step_name}」……")
                                kill_process_tree(proc)
                                return

                    threads.append(threading.Thread(target=watch_cancel, name="vt-cancel-watch", daemon=True))
                if poll_progress is not None:
                    def poll() -> None:
                        last: Optional[Tuple[int, int]] = None
                        while not done.wait(max(0.01, float(poll_interval))):
                            try:
                                got = poll_progress()
                                if not got:
                                    continue
                                n_done, total = int(got[0]), int(got[1])
                                if total <= 0 or (n_done, total) == last:
                                    continue
                                last = (n_done, total)
                                report(n_done / float(total), f"{step_name} {min(n_done, total)}/{total}", None)
                            except BaseException:  # noqa: B036 - 后台线程什么都不能抛（停止由 watch_cancel 负责）
                                pass

                    threads.append(threading.Thread(target=poll, name="vt-poll-progress", daemon=True))
                if on_poll is not None:
                    def poll_hook() -> None:
                        while not done.wait(max(0.01, float(poll_interval))):
                            try:
                                if on_poll() is True:
                                    request_stop()
                                    return
                            except BaseException:  # noqa: B036 - 后台线程什么都不能抛
                                pass

                    threads.append(threading.Thread(target=poll_hook, name="vt-on-poll", daemon=True))
                for t in threads:
                    t.start()
                assert proc.stdout is not None
                buf = b""
                while True:
                    chunk = proc.stdout.read(1024)
                    if not chunk:
                        break
                    buf += chunk
                    parts = buf.replace(b"\r", b"\n").split(b"\n")
                    buf = parts.pop()
                    for raw in parts:
                        line = raw.decode("utf-8", errors="replace").rstrip()
                        if not line:
                            continue
                        fh.write(line + "\n")
                        tail.append(line)
                        if len(tail) > 60:
                            tail.pop(0)
                        if not oom and OOM_PATTERN.search(line):
                            oom = True
                        if stop_when is not None and not stopped.is_set():
                            try:
                                if stop_when(line):
                                    request_stop()
                            except Exception:
                                pass
                        if parse_progress is None:
                            continue
                        try:
                            res = parse_progress(line)
                        except Exception:
                            res = None
                        if res is None:
                            continue
                        try:
                            if isinstance(res, tuple):
                                frac, text = float(res[0]), str(res[1])
                                key: Optional[str] = text.split("（", 1)[0]
                            else:
                                frac = float(res)
                                text = f"{label}：{max(0.0, min(1.0, frac)):.0%}" if label else line[-120:]
                                key = None
                        except (TypeError, ValueError, IndexError):
                            continue
                        if math.isnan(frac):
                            continue
                        report(frac, text, key)
                if buf.strip():
                    line = buf.decode("utf-8", errors="replace").rstrip()
                    fh.write(line + "\n")
                    tail.append(line)
                    oom = oom or bool(OOM_PATTERN.search(line))
                fh.flush()
                code = proc.wait()
                finished = True
            finally:
                done.set()
                if not finished:  # 读日志时出了意外（包括进度回调里的停止）：把子进程树一起结束
                    kill_process_tree(proc)
                    try:
                        proc.wait(timeout=10)
                    except Exception:
                        pass
                for t in threads:
                    t.join(timeout=5)
        if cancelled.is_set():
            raise TaskCancelled("已按你的要求停止")
        if stopped.is_set():  # 程序自己让它停下的：被结束的退出码不算失败
            return {"stopped": True, "code": code, "oom": oom}
        if code != 0:
            raise self._step_error(log_name, step_name, code, tail, log_path, oom)
        return {"stopped": False, "code": code, "oom": oom}

    @staticmethod
    def _step_error(log_name: str, step_name: str, code: int, tail: List[str], log_path: Path,
                    oom: bool) -> TrainStepError:
        tail_text = "\n".join(tail[-TAIL_LINES:])
        reason = _explain_title(tail_text)
        head = f"「{step_name}」这一步出错了" + (f"：{reason}" if reason else "")
        msg = (f"{head}\n{log_name} 失败（退出码 {code}）。详细日志：{log_path}\n最后的日志：\n{tail_text}")
        return TrainStepError(msg, log_name=log_name, label=step_name, code=code, tail=tail, log_path=log_path, oom=oom)


def resolve_python(configured: Optional[str], root: Optional[Path], cfg: Config) -> str:
    """找到引擎自己的 Python 解释器。"""
    if configured and configured != "auto":
        raw = Path(os.path.expanduser(str(configured)))
        if not raw.is_absolute():
            raw = Path(cfg.get("_base_dir", ".")) / raw
        # 不解开符号链接：Linux 上 venv 里的 python 是指向系统 Python 的链接，解开以后就不是这个环境了（找不到装在里面的包）
        p = Path(os.path.abspath(raw))
        if p.exists():
            return str(p)
        return str(configured)  # 可能是 PATH 里的命令，如 "python"
    if root:
        for rel in ("runtime/python.exe", "runtime/python", "runtime/bin/python", ".venv/Scripts/python.exe",
                    ".venv/bin/python", "venv/Scripts/python.exe", "venv/bin/python", "env/python.exe"):
            cand = root / rel
            if cand.exists():
                return str(cand)
    return sys.executable


def python_has_module(python: str, module: str, env: Optional[Dict[str, str]] = None, cwd: Optional[Path] = None) -> bool:
    try:
        proc = subprocess.run([python, "-c", f"import {module}"], env=env or subprocess_env(), cwd=str(cwd) if cwd else None,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        return proc.returncode == 0
    except Exception:
        return False


def gpu_memory_gb(python: str, env: Optional[Dict[str, str]] = None) -> float:
    """用引擎自己的 Python（和训练用的同一个 PyTorch）读显存大小，单位 GiB（原始数字，没有加 0.4）。0 表示没有可用显卡。"""
    code = ("import torch;print(torch.cuda.get_device_properties(0).total_memory/1024**3 "
            "if torch.cuda.is_available() else 0)")
    try:
        out = subprocess.run([python, "-c", code], env=env or subprocess_env(), stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=180,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.decode().strip().splitlines()
        return float(out[-1]) if out else 0.0
    except Exception:
        return 0.0


_BACKENDS: Dict[str, str] = {
    "gptsovits": "voicetwin.backends.gptsovits:GPTSoVITSBackend",
    "qwen3tts": "voicetwin.backends.qwen3tts:Qwen3TTSBackend",
    "indextts": "voicetwin.backends.indextts:IndexTTSBackend",
    "dummy": "voicetwin.backends.dummy:DummyBackend",
}


def available_backends() -> List[str]:
    return list(_BACKENDS)


def get_backend(name: str, cfg: Config, project: Project) -> Backend:
    import importlib

    name = (name or cfg.get("backend") or "gptsovits").lower()
    if name not in _BACKENDS:
        raise ValueError(f"未知引擎 {name}，可选：{', '.join(_BACKENDS)}")
    mod_name, cls_name = _BACKENDS[name].split(":")
    cls = getattr(importlib.import_module(mod_name), cls_name)
    return cls(cfg, project)
