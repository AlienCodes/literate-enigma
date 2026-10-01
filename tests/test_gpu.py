"""网页顶部的显卡状态（voicetwin/utils/gpu.py）：用假的 PyTorch 和假的 nvidia-smi 输出测试。"""

import subprocess
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from voicetwin.utils import gpu

GIB = 1024 ** 3
DRIVER_FAIL = ("NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. "
               "Make sure that the latest NVIDIA driver is installed and running.")
RTX5070_SMI = "NVIDIA GeForce RTX 5070, 12227, 1680, 10547, 576.02\n"  # 名字, 总显存, 已用, 可用 (MiB), 驱动
RTX5070_MSG = "✅ 显卡正常：NVIDIA GeForce RTX 5070（显存 12.0 GB，可用 10.3 GB）"


class FakeCuda:
    def __init__(self, available=True, name="NVIDIA GeForce RTX 5070", cap=(12, 0),
                 arch=("sm_75", "sm_80", "sm_86", "sm_90", "sm_100", "sm_120"),
                 total_gib=11.94, free_gib=10.3, broken=()):
        self.available, self.name, self.cap, self.arch = available, name, cap, arch
        self.total_gib, self.free_gib, self.broken = total_gib, free_gib, broken
        self.calls = []

    def _call(self, what):
        self.calls.append(what)
        if what in self.broken:
            raise RuntimeError(f"{what} exploded")

    def is_available(self):
        self._call("is_available")
        return self.available

    def get_device_name(self, idx=0):
        self._call("get_device_name")
        return self.name

    def get_device_capability(self, idx=0):
        self._call("get_device_capability")
        return self.cap

    def get_arch_list(self):
        self._call("get_arch_list")
        return list(self.arch)

    def get_device_properties(self, idx=0):
        self._call("get_device_properties")
        return SimpleNamespace(total_memory=int(self.total_gib * GIB))

    def mem_get_info(self, idx=0):
        self._call("mem_get_info")
        return int(self.free_gib * GIB), int(self.total_gib * GIB)


def fake_torch(cuda="12.8", version="2.7.1+cu128", **kw):
    return SimpleNamespace(__version__=version, version=SimpleNamespace(cuda=cuda), cuda=FakeCuda(**kw))


def setup(monkeypatch, torch=None, smi=None, torch_error=""):
    """torch：假的 torch 模块或 None（没装）；smi：None（没有 nvidia-smi）、(退出码, 输出) 或要抛出的异常。"""
    monkeypatch.setattr(gpu, "_load_torch", lambda: (torch, torch_error))
    calls = {"smi": 0}
    if smi is None:
        monkeypatch.setattr(gpu, "_find_nvidia_smi", lambda: None)
    else:
        monkeypatch.setattr(gpu, "_find_nvidia_smi", lambda: "nvidia-smi")

        def run(exe):
            calls["smi"] += 1
            if isinstance(smi, BaseException):
                raise smi
            return smi

        monkeypatch.setattr(gpu, "_run_nvidia_smi", run)
    return calls


@pytest.fixture(autouse=True)
def _fresh_cache():
    gpu.clear_cache()
    yield
    gpu.clear_cache()


REQUIRED_KEYS = {"ok", "level", "name", "total_gb", "free_gb", "used_gb", "driver", "torch_cuda", "torch_version",
                 "message", "advice"}


def assert_driver_advice(st):
    assert gpu.DRIVER_URL in st["advice"]
    assert "重启" in st["advice"] and "nvidia50" in st["advice"]


# ---------------------------------------------------------------------------- 驱动坏了
@pytest.mark.parametrize("rc", [9, 0])  # 有些版本出错时退出码仍是 0
def test_driver_failure_text_without_torch_is_error(monkeypatch, rc):
    setup(monkeypatch, torch=None, smi=(rc, DRIVER_FAIL))
    st = gpu.gpu_status()
    assert REQUIRED_KEYS <= set(st)
    assert st["ok"] is False and st["level"] == "error"
    assert st["message"].startswith("❌ 显卡没有正常工作")
    assert_driver_advice(st)
    assert st["torch_cuda"] is None and st["torch_version"] == ""
    assert "NVIDIA-SMI has failed" in st["detail"]
    assert gpu.vram_tier(st) == "none"

    badge = gpu.render_gpu_badge_html(st)
    assert badge.startswith('<div class="vt-gpu vt-gpu-error"') and badge.endswith("</div>")
    assert "\n" not in badge  # 只有一行
    assert "显卡没有正常工作" in badge and "怎么办" in badge
    assert f'<a href="{gpu.DRIVER_URL}" target="_blank"' in badge


def test_driver_failure_with_cuda_torch_that_sees_no_gpu(monkeypatch):
    torch = fake_torch(available=False)
    setup(monkeypatch, torch=torch, smi=(9, DRIVER_FAIL))
    st = gpu.gpu_status()
    assert st["level"] == "error" and st["ok"] is False
    assert st["torch_cuda"] is False and st["torch_version"] == "2.7.1+cu128"
    assert "驱动" in st["message"]
    assert_driver_advice(st)
    assert "get_device_name" not in torch.cuda.calls


def test_torch_sees_no_cuda_but_nvidia_smi_works_is_error(monkeypatch):
    # 例如驱动太旧，PyTorch 用不了；nvidia-smi 还能列出显卡
    setup(monkeypatch, torch=fake_torch(available=False), smi=(0, RTX5070_SMI))
    st = gpu.gpu_status()
    assert st["level"] == "error"
    assert st["message"] == "❌ 显卡没有正常工作：训练程序用不了这块显卡（NVIDIA GeForce RTX 5070）"
    assert "is_available() 是 False" in st["detail"]
    assert st["name"] == "NVIDIA GeForce RTX 5070" and st["driver"] == "576.02"
    assert_driver_advice(st)
    assert gpu.vram_tier(st) == "none"


def test_nvidia_smi_timeout_is_error(monkeypatch):
    setup(monkeypatch, torch=None, smi=subprocess.TimeoutExpired("nvidia-smi", 10))
    st = gpu.gpu_status()
    assert st["level"] == "error" and "10 秒" in st["detail"]
    assert_driver_advice(st)


def test_nvidia_smi_no_devices_is_error(monkeypatch):
    setup(monkeypatch, torch=None, smi=(0, "No devices were found"))
    st = gpu.gpu_status()
    assert st["level"] == "error"


def test_rtx50_with_old_torch_is_error(monkeypatch):
    # 旧整合包（cu124）不认识 sm_120：is_available() 仍然是 True，但训练会报 no kernel image
    torch = fake_torch(version="2.5.1+cu124", arch=("sm_50", "sm_60", "sm_70", "sm_75", "sm_80", "sm_86", "sm_90"))
    setup(monkeypatch, torch=torch, smi=(0, RTX5070_SMI))
    st = gpu.gpu_status()
    assert st["level"] == "error" and st["ok"] is False
    assert "不支持" in st["message"] and "RTX 5070" in st["message"]
    assert "nvidia50" in st["advice"] and "sm_120" in st["detail"]
    assert gpu.vram_tier(st) == "none"


def test_same_major_architecture_counts_as_supported(monkeypatch):
    # RTX 4090（8.9）用只带 sm_86 的 PyTorch：和 PyTorch 自己的判断一样，算支持
    smi = (0, "NVIDIA GeForce RTX 4090, 24564, 500, 24064, 576.02")
    setup(monkeypatch, torch=fake_torch(name="NVIDIA GeForce RTX 4090", cap=(8, 9), arch=("sm_80", "sm_86")), smi=smi)
    st = gpu.gpu_status()
    assert st["level"] == "ok" and gpu.vram_tier(st) == "high"


# ---------------------------------------------------------------------------- 正常的 RTX 5070 12GB
def test_healthy_rtx5070_with_torch_and_nvidia_smi(monkeypatch):
    torch = fake_torch()
    calls = setup(monkeypatch, torch=torch, smi=(0, RTX5070_SMI))
    st = gpu.gpu_status()
    assert st["ok"] is True and st["level"] == "ok" and st["advice"] == ""
    assert st["message"] == RTX5070_MSG
    assert st["name"] == "NVIDIA GeForce RTX 5070"
    assert st["total_gb"] == pytest.approx(11.94, abs=0.01)
    assert st["free_gb"] == pytest.approx(10.30, abs=0.01)
    assert st["used_gb"] == pytest.approx(1.64, abs=0.01)
    assert st["nominal_gb"] == 12.0
    assert st["driver"] == "576.02"
    assert st["torch_cuda"] is True and st["torch_version"] == "2.7.1+cu128"
    assert st["source"] == "torch" and st["count"] == 1
    assert calls["smi"] == 1
    # 有 nvidia-smi 时不用 mem_get_info（它会在网页进程里占一块显存）
    assert "mem_get_info" not in torch.cuda.calls
    assert gpu.vram_tier(st) == "mid"

    badge = gpu.render_gpu_badge_html(st)
    assert badge.startswith('<div class="vt-gpu vt-gpu-ok" data-level="ok"')
    assert RTX5070_MSG in badge and "怎么办" not in badge
    assert "驱动 576.02" in badge  # 鼠标悬停时的提示


def test_healthy_rtx5070_torch_only(monkeypatch):
    torch = fake_torch(total_gib=11.94, free_gib=10.3)
    setup(monkeypatch, torch=torch, smi=None)
    st = gpu.gpu_status()
    assert st["level"] == "ok" and st["message"] == RTX5070_MSG
    assert st["source"] == "torch" and st["driver"] == ""
    assert st["used_gb"] == pytest.approx(1.64, abs=0.01)
    assert "mem_get_info" in torch.cuda.calls


def test_healthy_rtx5070_nvidia_smi_only(monkeypatch):
    setup(monkeypatch, torch=None, smi=(0, RTX5070_SMI))
    st = gpu.gpu_status()
    assert st["level"] == "ok" and st["message"] == RTX5070_MSG
    assert st["torch_cuda"] is None and st["torch_version"] == ""
    assert st["source"] == "nvidia-smi"


def test_cpu_only_torch_falls_back_to_nvidia_smi(monkeypatch):
    # .venv 安装方式：网页用 CPU 版 PyTorch，训练用整合包里的 Python。不能因此说显卡坏了。
    setup(monkeypatch, torch=fake_torch(cuda=None, version="2.4.0+cpu", available=False), smi=(0, RTX5070_SMI))
    st = gpu.gpu_status()
    assert st["level"] == "ok" and st["torch_cuda"] is False and st["torch_version"] == "2.4.0+cpu"
    assert st["source"] == "nvidia-smi"


def test_broken_torch_import_falls_back_to_nvidia_smi(monkeypatch):
    setup(monkeypatch, torch=None, smi=(0, RTX5070_SMI), torch_error="OSError: [WinError 126] c10.dll")
    st = gpu.gpu_status()
    assert st["level"] == "ok" and "WinError 126" in st["detail"]


def test_healthy_torch_ignores_odd_nvidia_smi_failure(monkeypatch):
    torch = fake_torch()
    setup(monkeypatch, torch=torch, smi=subprocess.TimeoutExpired("nvidia-smi", 10))
    st = gpu.gpu_status()
    assert st["level"] == "ok" and st["message"] == RTX5070_MSG


def test_picks_the_gpu_that_torch_uses(monkeypatch):
    smi = (0, "NVIDIA GeForce GTX 1050, 2048, 100, 1948, 576.02\nNVIDIA GeForce RTX 5070, 12227, 1680, 10547, 576.02\n")
    setup(monkeypatch, torch=fake_torch(), smi=smi)
    st = gpu.gpu_status()
    assert st["message"] == RTX5070_MSG and st["count"] == 2
    assert "共 2 块显卡" in gpu.render_gpu_badge_html(st)


# ---------------------------------------------------------------------------- 没有显卡
@pytest.mark.parametrize("torch", [None, "cpu", "cuda"])
def test_no_nvidia_gpu_at_all_is_error(monkeypatch, torch):
    t = {None: None, "cpu": fake_torch(cuda=None, version="2.4.0+cpu", available=False),
         "cuda": fake_torch(available=False)}[torch]
    setup(monkeypatch, torch=t, smi=None)
    st = gpu.gpu_status()
    assert st["ok"] is False and st["level"] == "error"
    assert st["message"].startswith("❌ 显卡没有正常工作") and "没有找到 NVIDIA 显卡" in st["message"]
    assert gpu.DRIVER_URL in st["advice"] and "非常慢" in st["advice"]
    assert st["total_gb"] is None and st["free_gb"] is None and st["used_gb"] is None
    assert gpu.vram_tier(st) == "none"
    assert "vt-gpu-error" in gpu.render_gpu_badge_html(st)


# ---------------------------------------------------------------------------- 显存小 / 可用显存少
def test_small_vram_card_warns(monkeypatch):
    setup(monkeypatch, torch=None, smi=(0, "NVIDIA GeForce GTX 1650, 4096, 300, 3796, 531.79"))
    st = gpu.gpu_status()
    assert st["ok"] is True and st["level"] == "warn"
    assert st["message"] == "⚠️ 显卡能用，但显存比较小：NVIDIA GeForce GTX 1650（显存 4.0 GB，可用 3.7 GB）"
    assert "每批数量" in st["advice"]
    assert gpu.vram_tier(st) == "low"
    badge = gpu.render_gpu_badge_html(st)
    assert 'class="vt-gpu vt-gpu-warn"' in badge and "怎么办" in badge


def test_low_free_vram_warns(monkeypatch):
    setup(monkeypatch, torch=fake_torch(), smi=(0, "NVIDIA GeForce RTX 5070, 12227, 11000, 1227, 576.02"))
    st = gpu.gpu_status()
    assert st["ok"] is True and st["level"] == "warn"
    assert "可用显存不多" in st["message"] and "可用 1.2 GB" in st["message"]
    assert "正在训练" in st["advice"]
    assert gpu.vram_tier(st) == "mid"  # 档位按总显存，不按一时的可用显存


def test_6gb_card_is_not_warned_but_low_tier(monkeypatch):
    # 6 GB 的卡 PyTorch 只报 5.8 GiB：按包装盒大小算，不提醒「小于 6 GB」
    setup(monkeypatch, torch=fake_torch(name="NVIDIA GeForce RTX 2060", cap=(7, 5), total_gib=5.8, free_gib=5.0),
          smi=None)
    st = gpu.gpu_status()
    assert st["level"] == "ok" and "显存 6.0 GB" in st["message"]
    assert gpu.vram_tier(st) == "low"


# ---------------------------------------------------------------------------- 档位
@pytest.mark.parametrize("total,tier", [
    (3.9, "low"), (5.8, "low"), (6.0, "low"),
    (7.6, "mid"), (7.99, "mid"), (8.0, "mid"), (11.76, "mid"), (11.94, "mid"), (15.0, "mid"),
    (15.2, "high"), (15.6, "high"), (15.99, "high"), (23.65, "high"), (47.99, "high"),
])
def test_vram_tier_thresholds(total, tier):
    assert gpu.vram_tier({"ok": True, "level": "ok", "total_gb": total}) == tier
    assert gpu.vram_tier({"ok": True, "level": "warn", "total_gb": total}) == tier


def test_vram_tier_edge_cases(monkeypatch):
    assert gpu.vram_tier({"ok": False, "level": "error", "total_gb": 24.0}) == "none"
    assert gpu.vram_tier({"ok": True, "level": "ok", "total_gb": None}) == "low"  # 能用但不知道多大：保守
    assert gpu.vram_tier({"total_gb": 12.0}) == "mid"
    assert gpu.vram_tier({}) == "none"
    assert gpu.vram_tier({"total_gb": "abc"}) == "none"
    assert gpu.vram_tier({"ok": True, "level": "ok", "total_gb": float("nan")}) == "low"
    assert gpu.vram_tier("garbage") == "none"  # type: ignore[arg-type]
    setup(monkeypatch, torch=None, smi=(0, RTX5070_SMI))
    assert gpu.vram_tier() == "mid"  # 不传时自己检查


@pytest.mark.parametrize("total,nominal", [(11.94, 12.0), (11.76, 12.0), (12.0, 12.0), (7.6, 8.0), (5.8, 6.0),
                                           (23.65, 24.0), (23.99, 24.0), (4.0, 4.0), (None, None), (0.0, None)])
def test_nominal_gb(total, nominal):
    assert gpu.nominal_gb(total) == nominal


# ---------------------------------------------------------------------------- 解析和判断
def test_parse_nvidia_smi_formats():
    out = ("NVIDIA GeForce RTX 5070, 12227, 1680, 10547, 576.02\n"
           "NVIDIA GeForce RTX 3060, 12288 MiB, [N/A], [N/A], 576.02\n"
           "Quadro P1000, 4096, 1024, 576.02\n"  # 四列（没有 memory.free）
           "garbage\n\n")
    gpus = gpu.parse_nvidia_smi(out)
    assert [g["name"] for g in gpus] == ["NVIDIA GeForce RTX 5070", "NVIDIA GeForce RTX 3060", "Quadro P1000"]
    assert gpus[0]["total_gb"] == pytest.approx(12227 / 1024) and gpus[0]["free_gb"] == pytest.approx(10547 / 1024)
    assert gpus[1]["total_gb"] == 12.0 and gpus[1]["used_gb"] is None and gpus[1]["free_gb"] is None
    assert gpus[2]["free_gb"] == 3.0 and gpus[2]["driver"] == "576.02"
    assert gpu.parse_nvidia_smi("") == []


@pytest.mark.parametrize("rc,out", [
    (9, DRIVER_FAIL), (0, DRIVER_FAIL), (0, ""), (0, "   "), (1, RTX5070_SMI),
    (0, "Unable to determine the device handle for GPU0000:01:00.0: Unknown Error"),
    (0, RTX5070_SMI), (0, "NVIDIA GeForce RTX 5070, 12227 MiB, 576.02"),
])
def test_smi_status_matches_workflows_check(rc, out):
    from voicetwin.workflows import nvidia_smi_status

    assert gpu.smi_status(rc, out)[0] == nvidia_smi_status(rc, out)[0]


def test_run_nvidia_smi_uses_query_and_10s_timeout(monkeypatch):
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"], seen["kw"] = cmd, kw
        return SimpleNamespace(returncode=0, stdout=RTX5070_SMI.encode("utf-8"))

    monkeypatch.setattr(gpu.subprocess, "run", fake_run)
    rc, out = gpu._run_nvidia_smi("nvidia-smi")
    assert (rc, out) == (0, RTX5070_SMI)
    assert seen["cmd"] == ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,driver_version",
                           "--format=csv,noheader,nounits"]
    assert seen["kw"]["timeout"] == 10
    assert gpu.SMI_TIMEOUT == 10 and gpu.CACHE_SECONDS == 10


# ---------------------------------------------------------------------------- 缓存、线程、永不报错
class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def monotonic(self):
        return self.t


def test_cache_10_seconds_and_refresh(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(gpu, "time", SimpleNamespace(monotonic=clock.monotonic, time=time.time,
                                                      strftime=time.strftime, localtime=time.localtime))
    calls = setup(monkeypatch, torch=None, smi=(0, RTX5070_SMI))
    first = gpu.gpu_status()
    first["message"] = "被调用方改掉了"  # 返回的是副本，不会弄脏缓存
    clock.t += 9.0
    assert gpu.gpu_status()["message"] == RTX5070_MSG
    assert calls["smi"] == 1
    clock.t += 1.5
    gpu.gpu_status()
    assert calls["smi"] == 2
    gpu.gpu_status(refresh=True)
    assert calls["smi"] == 3


def test_concurrent_callers_probe_once(monkeypatch):
    calls = setup(monkeypatch, torch=None, smi=None)
    monkeypatch.setattr(gpu, "_find_nvidia_smi", lambda: "nvidia-smi")

    def slow_run(exe):
        calls["smi"] += 1
        time.sleep(0.05)
        return 0, RTX5070_SMI

    monkeypatch.setattr(gpu, "_run_nvidia_smi", slow_run)
    results = []
    threads = [threading.Thread(target=lambda: results.append(gpu.gpu_status())) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert calls["smi"] == 1 and len(results) == 8
    assert all(r["message"] == RTX5070_MSG for r in results)


def test_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("意外")

    monkeypatch.setattr(gpu, "_load_torch", boom)
    st = gpu.gpu_status()
    assert st["level"] == "warn" and st["ok"] is False and "检查不了" in st["message"]
    assert gpu.vram_tier(st) == "none"
    assert "vt-gpu-warn" in gpu.render_gpu_badge_html(st)

    # torch 的每个函数都报错：当成用不了显卡
    gpu.clear_cache()
    torch = fake_torch(broken=("is_available",))
    setup(monkeypatch, torch=torch, smi=None)
    st = gpu.gpu_status()
    assert st["level"] == "error" and "is_available exploded" in st["detail"]

    gpu.clear_cache()
    setup(monkeypatch, torch=fake_torch(broken=("get_device_name",)), smi=(0, RTX5070_SMI))
    assert gpu.gpu_status()["level"] == "error"

    gpu.clear_cache()  # 架构、显存都问不到：仍然算能用，档位保守
    torch = fake_torch(broken=("get_device_capability", "get_device_properties", "mem_get_info"))
    setup(monkeypatch, torch=torch, smi=None)
    st = gpu.gpu_status()
    assert st["level"] == "ok" and st["message"] == "✅ 显卡正常：NVIDIA GeForce RTX 5070"
    assert gpu.vram_tier(st) == "low"

    assert 'class="vt-gpu vt-gpu-warn"' in gpu.render_gpu_badge_html("garbage")  # type: ignore[arg-type]
    assert 'class="vt-gpu vt-gpu-warn"' in gpu.render_gpu_badge_html({"level": "???"})


def test_badge_escapes_html():
    st = {"ok": True, "level": "ok", "message": '✅ 显卡正常：<b>"X" & Y</b>', "advice": "", "driver": '1"2'}
    badge = gpu.render_gpu_badge_html(st)
    assert "<b>" not in badge and "&lt;b&gt;" in badge and "&amp; Y" in badge
    assert 'title="驱动 1&quot;2"' in badge


def test_css_and_no_gradio_import():
    for cls, color in (("vt-gpu-ok", "#16a34a"), ("vt-gpu-warn", "#d97706"), ("vt-gpu-error", "#dc2626")):
        assert f".{cls}" in gpu.GPU_CSS and color in gpu.GPU_CSS
    assert ".dark .vt-gpu-error" in gpu.GPU_CSS
    src = Path(gpu.__file__).read_text(encoding="utf-8")
    assert "import gradio" not in src and "from gradio" not in src
    assert "vt-gpu-pending" in gpu.render_gpu_pending_html()
