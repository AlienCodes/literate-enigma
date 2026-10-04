"""最小的假 torch：只有 indextts_worker.py 用到的几个函数（CI 里没有装 torch）。"""

from . import cuda  # noqa: F401


def manual_seed(seed):
    return None
