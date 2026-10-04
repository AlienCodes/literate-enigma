"""端口小工具：检查一个本机端口现在是不是空着（网页启动器和 GPT-SoVITS 推理服务共用）。

只用标准库，任何函数都不会抛出异常。
"""

from __future__ import annotations

import socket


def exclusive_bind_ok(host: str, port: int) -> bool:
    """这个端口现在能不能绑定（没有别的程序占着）。

    Windows 默认允许不同的地址"共用"同一个端口：别的程序监听 0.0.0.0:9880 时，普通方式绑定 127.0.0.1:9880 照样成功，
    会把占着的端口误当成空闲。用独占方式（SO_EXCLUSIVEADDRUSE）绑定时，只要有任何程序占着这个端口就会失败。
    其它系统没有这个选项，普通绑定本来就会失败。"""
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    try:
        with socket.socket(family, socket.SOCK_STREAM) as s:
            excl = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
            if excl is not None:
                s.setsockopt(socket.SOL_SOCKET, excl, 1)
            s.bind((host, port))
            return True
    except (OSError, OverflowError):
        return False
