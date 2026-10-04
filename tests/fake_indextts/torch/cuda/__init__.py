import os
from types import SimpleNamespace


def is_available():
    return os.environ.get("FAKE_TORCH_CUDA") == "1"


def is_bf16_supported():
    return is_available()


def get_device_properties(idx):
    gb = float(os.environ.get("FAKE_TORCH_VRAM_GB", "8"))
    return SimpleNamespace(name="Fake RTX 5060", total_memory=int(gb * 1024 ** 3))


def manual_seed_all(seed):
    return None


def empty_cache():
    return None
