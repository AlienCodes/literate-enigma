"""errors.explain()：把报错翻译成「出了什么问题 + 怎么办」。"""

import re
import subprocess

import pytest

from voicetwin.errors import FATAL_KEYS, UNKNOWN_TITLE, Friendly, explain, friendly_line, friendly_md, is_fatal


class TaskCancelled(BaseException):
    """和 voicetwin.utils.progress.TaskCancelled 同名（errors 只按类型名识别，不导入它）。"""


def _err(cls, msg, cause=None):
    e = cls(msg)
    if cause is not None:
        e.__cause__ = cause
    return e


GSV_ENV_MSG = ("GPT-SoVITS 环境有问题：\n- 缺少预训练模型：GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large\n"
               "- 可运行 voicetwin download-models 自动下载（国内加 --source hf-mirror）")

TRAIN_TAIL = ("gsv_s2_train 失败（退出码 1）。最后的日志：\n"
              "INFO:root:loading pretrained\n"
              "UserWarning: something timed out while caching\n"
              "Traceback (most recent call last):\n"
              "  File \"GPT_SoVITS/s2_train.py\", line 600, in <module>\n"
              "torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB")

# (报错, 期望的规则 key, 标题里必须有的文字)
CASES = [
    # 计划里点名的用例
    (RuntimeError("torch.cuda.OutOfMemoryError: CUDA out of memory"), "gpu_oom", "显卡内存（显存）不够"),
    (MemoryError(), "ram", "电脑内存不够"),
    (PermissionError(13, "Permission denied", "transcripts.csv"), "file_locked", "被别的程序占用"),
    ("[Errno 28] No space left on device", "disk", "硬盘空间不够"),
    (RuntimeError("ffmpeg 执行失败 … Output file #0 does not contain any stream"), "no_audio", "这个视频里没有声音"),
    (RuntimeError(GSV_ENV_MSG), "models_missing", "缺少 GPT-SoVITS 的模型文件"),
    (RuntimeError("还没有名为「我的声音」的声音，请先运行：voicetwin prepare -v 我的声音 -i 你的视频文件夹"),
     "not_prepared", "还没有准备素材"),
    # 显卡 / 驱动
    ("RuntimeError: CUDA error: out of memory", "gpu_oom", "显存"),
    ("CUBLAS_STATUS_ALLOC_FAILED when calling cublasCreate(handle)", "gpu_oom", "显存"),
    ("RuntimeError: Found no NVIDIA driver on your system. Please check that you have an NVIDIA GPU", "driver",
     "显卡驱动"),
    ("RuntimeError: No CUDA GPUs are available\nRuntimeError: no CUDA-capable device is detected", "driver", "显卡驱动"),
    ("RuntimeError: The NVIDIA driver on your system is too old (found version 11040).", "driver", "显卡驱动"),
    ("NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.", "driver", "显卡驱动"),
    ("RuntimeError: Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False.",
     "driver", "显卡驱动"),
    ("AssertionError: Torch not compiled with CUDA enabled", "torch_cpu", "不支持显卡"),
    ("RuntimeError: CUDA error: no kernel image is available for execution on the device", "gpu_arch", "显卡太新"),
    ("RuntimeError: CUDA error: an illegal memory access was encountered", "gpu_crash", "显卡"),
    # 内存 / 虚拟内存 / 硬盘
    ("numpy.core._exceptions._ArrayMemoryError: Unable to allocate 3.2 GiB for an array", "ram", "电脑内存不够"),
    ("RuntimeError: [enforce fail at alloc_cpu.cpp:114] DefaultCPUAllocator: not enough memory", "ram",
     "电脑内存不够"),
    ("OSError: [WinError 1455] 页面文件太小，无法完成操作。 Error loading \"D:\\GPT-SoVITS\\runtime\\torch\\lib\\x.dll\"",
     "pagefile", "虚拟内存"),
    (OSError(28, "No space left on device", "D:\\VoiceTwin\\workspace\\a.wav"), "disk", "D 盘空间不够"),
    ("OSError: [WinError 112] 磁盘空间不足。", "disk", "空间不够"),
    ("RuntimeError: [enforce fail at inline_container.cc:337] . unexpected pos 1234 vs 5678", "disk", "空间不够"),
    # 文件被占用 / 没权限 / 找不到 / 路径太长
    ("PermissionError: [WinError 32] 另一个程序正在使用此文件，进程无法访问。: 'D:\\\\ws\\\\transcripts.csv'",
     "file_locked", "「transcripts.csv」被别的程序占用"),
    ("The process cannot access the file because it is being used by another process", "file_locked", "占用"),
    (FileNotFoundError(2, "No such file or directory", "D:\\视频\\第1课.mp4"), "not_found", "第1课.mp4"),
    ("FileNotFoundError: [WinError 3] 系统找不到指定的路径。: 'D:\\\\不存在'", "not_found", "找不到文件或文件夹"),
    (OSError(206, "文件名或扩展名太长。"), "path_too_long", "路径太长"),
    # 网络 / 下载
    (RuntimeError("预训练模型下载失败：HTTPSConnectionPool(host='hf-mirror.com', port=443): Read timed out. "
                  "(read timeout=60)。也可以手动从 https://huggingface.co/lj1995/GPT-SoVITS 下载"), "net_timeout", "下载失败"),
    ("requests.exceptions.SSLError: HTTPSConnectionPool(host='huggingface.co', port=443): [SSL: "
     "CERTIFICATE_VERIFY_FAILED] certificate verify failed", "net_proxy", "被拦住"),
    ("HTTPSConnectionPool(host='huggingface.co', port=443): Max retries exceeded (Caused by ProxyError("
     "'Cannot connect to proxy.', NewConnectionError('127.0.0.1:7890 refused')))", "net_proxy", "被拦住"),
    ("socket.gaierror: [Errno 11001] getaddrinfo failed", "network", "网络"),
    ("ConnectionError: HTTPSConnectionPool(host='download.example.com', port=443): Max retries exceeded with url: /x",
     "network", "网络"),
    ("ConnectionError: HTTPSConnectionPool(host='hf-mirror.com', port=443): Max retries exceeded with url: /x",
     "net_hf", "下载模型失败"),
    ("huggingface_hub.utils._errors.LocalEntryNotFoundError: Cannot find an appropriate cached snapshot folder",
     "net_hf", "下载模型失败"),
    ("modelscope.hub.errors.NotExistError: https://www.modelscope.cn/api/v1/models/iic/x 无法访问", "net_modelscope",
     "ModelScope"),
    ("requests.exceptions.HTTPError: 503 Server Error: Service Unavailable for url: https://hf-mirror.com/x",
     "net_busy", "太忙"),
    ("requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://hf-mirror.com/x", "net_refused",
     "拿不到"),
    # 本机的 GPT-SoVITS 推理服务（127.0.0.1）出问题不是「网络问题」
    ("HTTPConnectionPool(host='127.0.0.1', port=9880): Max retries exceeded with url: /tts (Caused by "
     "NewConnectionError('<x>: Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。'))",
     "api_down", "GPT-SoVITS 意外停止了"),
    ("HTTPConnectionPool(host='127.0.0.1', port=9880): Read timed out. (read timeout=600)", "api_slow", "没有回应"),
    (RuntimeError("GPT-SoVITS 推理服务启动失败：\nTraceback ...\nSystemError: boom"), "api_start", "GPT-SoVITS 没能启动"),
    (RuntimeError("GPT-SoVITS 推理服务启动超时，请查看 D:/ws/logs/gptsovits_api.log"), "api_start", "没能启动"),
    (RuntimeError("qwen3 启动失败（退出码 1）：\nboom"), "api_start", "合成引擎没能启动"),
    (subprocess.TimeoutExpired(["nvidia-smi"], 30), "cmd_timeout", "太久"),
    # 端口
    (OSError(98, "Address already in use"), "port", "端口被占用"),
    ("OSError: [WinError 10048] 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。", "port", "端口被占用"),
    ("OSError: Cannot find empty port in range: 7860-7959.", "port", "端口被占用"),
    # 缺组件
    (ModuleNotFoundError("No module named 'faster_whisper'"), "module", "语音识别（faster-whisper）"),
    (_err(RuntimeError, "未安装 funasr：请执行 pip install \"voicetwin[funasr]\"",
          ModuleNotFoundError("No module named 'funasr'")), "module", "funasr"),
    (RuntimeError("网页界面需要 gradio：pip install \"voicetwin[webui]\""), "module", "网页界面（gradio）"),
    (RuntimeError("读取 Word 讲稿需要：pip install python-docx（或另存为 txt）"), "module", "Word"),
    (RuntimeError("去背景音乐需要安装 demucs：pip install \"voicetwin[separate]\""), "module", "demucs"),
    (ModuleNotFoundError("No module named 'torch'"), "module", "PyTorch"),
    ("ImportError: DLL load failed while importing _C: 找不到指定的模块。", "dll", "运行库"),
    ("ImportError: numpy.core.multiarray failed to import", "import_version", "版本不对"),
    # 视频 / 音频文件
    (RuntimeError("ffmpeg 执行失败：-y -i D:\\课程\\第5课 上.mp4 -vn -sn -dn\n"
                  "Output file #0 does not contain any stream"), "no_audio", "这个视频里没有声音：第5课 上.mp4"),
    (RuntimeError("ffmpeg 执行失败：-y -i D:/a/坏.mp4 -vn\n[mov,mp4 @ 0x1] moov atom not found\n"
                  "D:/a/坏.mp4: Invalid data found when processing input"), "media_broken", "损坏"),
    (RuntimeError("ffmpeg 执行失败：-y -i D:/a/x.rmvb -vn\nDecoder (codec none) not found for input stream #0:1"),
     "media_codec", "格式不支持"),
    (RuntimeError("ffmpeg 执行失败：-y -i D:/a/怪.mp4 -vn\nsomething odd"), "ffmpeg", "处理视频或音频时出错"),
    (RuntimeError("找不到 ffmpeg。请执行 `pip install imageio-ffmpeg`，或安装系统 ffmpeg 并加入 PATH。"), "ffmpeg_missing",
     "ffmpeg 没装好"),
    # 设置文件 / 编码
    (UnicodeDecodeError("utf-8", b"\xb5\xc4", 0, 1, "invalid start byte"), "encoding", "编码"),
    # 应用自己的中文提示
    (RuntimeError("找不到 GPT-SoVITS 目录：D:/GPT-SoVITS（请运行安装脚本）"), "gsv_missing", "没找到 GPT-SoVITS 整合包"),
    (RuntimeError("D:/x 不是完整的 GPT-SoVITS 目录（缺少 api_v2.py）"), "gsv_missing", "整合包"),
    (RuntimeError("这个声音还没有参考音频，请先运行素材准备（voicetwin prepare）。"), "not_prepared", "还没有准备素材"),
    (RuntimeError("没有可用于评估的片段"), "not_prepared", "还没有准备素材"),
    (RuntimeError("没有可用于训练的片段，请先运行素材准备并检查 transcripts.csv。"), "no_clips", "没有可以用来训练的句子"),
    (FileNotFoundError("没有找到任何视频或音频文件。支持：.mp4 .wav"), "no_media", "没找到视频或录音"),
    (ValueError("讲稿里没有可以朗读的内容"), "empty_script", "讲稿是空的"),
    (RuntimeError("连接不上 GPT-SoVITS 服务 http://10.0.0.2:9880，请先启动 api_v2.py"), "external_api", "连不上"),
    # 外层包装：找不到根本原因时
    (RuntimeError("gsv_s1_train 失败（退出码 1）。最后的日志：\nepoch 3\nsaving"), "step_failed",
     "GPT-SoVITS「训练语气和节奏（GPT）」这一步出错了"),
    (RuntimeError("训练结束但没有找到权重文件，请查看 logs/gsv_s2_train.log 与 logs/gsv_s1_train.log"), "train_no_output",
     "没有得到模型"),
    (RuntimeError("第 12 句合成失败：今天我们来学习"), "sentence_failed", "第 12 句没能生成"),
    (RuntimeError("所有模型都合成失败，请检查引擎日志"), "select_failed", "所有模型都没能生成声音"),
    (RuntimeError("GPT-SoVITS 合成失败：tts failed"), "synth_failed", "GPT-SoVITS 没能生成声音"),
    (RuntimeError("切换 GPT 模型失败：bad"), "model_switch", "加载训练好的模型失败"),
    (RuntimeError("Demucs 执行失败：\nlog"), "demucs", "去背景音乐"),
    ("RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory",
     "model_corrupt", "模型文件"),
    # 停止
    (TaskCancelled(), "stopped", "已停止"),
    (KeyboardInterrupt(), "stopped", "已停止"),
]


@pytest.mark.parametrize("err,key,title_part", CASES, ids=[f"{i}-{c[1]}" for i, c in enumerate(CASES)])
def test_explain_rules(err, key, title_part):
    f = explain(err)
    assert isinstance(f, Friendly)
    assert f.key == key, (f.key, f.title, f.detail)
    assert title_part in f.title, f.title
    assert f.advice, "认出来的问题都要有「怎么办」"
    assert re.search(r"[\u4e00-\u9fff]", f.title) and re.search(r"[\u4e00-\u9fff]", f.advice)
    assert len(f.title) <= 60, f.title
    assert f.detail


def test_cuda_oom_wins_over_general_memory_rule():
    assert explain("torch.cuda.OutOfMemoryError: CUDA out of memory").title == "显卡内存（显存）不够"
    assert explain(MemoryError()).title == "电脑内存不够"


def test_real_cause_in_training_log_tail_wins_over_wrapper_and_warnings():
    f = explain(RuntimeError(TRAIN_TAIL))
    assert f.key == "gpu_oom"
    assert "每批数量" in f.advice and "2" in f.advice


def test_exception_lines_beat_earlier_warning_lines():
    # 普通的警告行里有 Permission denied，真正的报错是缺组件：应该说缺组件
    text = ("gsv_1a_text 失败（退出码 1）。最后的日志：\n"
            "UserWarning: could not write cache: [Errno 13] Permission denied: 'C:\\\\cache'\n"
            "Traceback (most recent call last):\n"
            "ModuleNotFoundError: No module named 'jieba_fast'")
    f = explain(RuntimeError(text))
    assert f.key == "module"
    assert "GPT-SoVITS" in f.title and "jieba_fast" in f.title
    assert "完整解压" in f.advice


def test_component_taken_from_real_error_line_not_benign_warning():
    text = ("gsv_s2_train 失败（退出码 1）。最后的日志：\n"
            "A matching Triton is not available. Error caught was: No module named 'triton'\n"
            "ModuleNotFoundError: No module named 'pytorch_lightning'")
    f = explain(RuntimeError(text))
    assert f.key == "module" and "pytorch_lightning" in f.title


def test_chained_cause_is_searched_and_kept_in_detail():
    inner = ModuleNotFoundError("No module named 'faster_whisper'")
    outer = _err(RuntimeError, "语音识别没能开始", inner)
    f = explain(outer)
    assert f.key == "module"
    assert "faster_whisper" in f.detail and "语音识别没能开始" in f.detail


def test_implicit_context_and_cycles_do_not_hang():
    a = ValueError("外层")
    b = KeyError("内层")
    a.__context__ = b
    b.__context__ = a  # 人为制造循环
    f = explain(a)
    assert f.title == "外层"


def test_chinese_app_message_is_kept_as_title():
    f = explain(ValueError("声音名称不能包含 /"))
    assert f.title == "声音名称不能包含 /"
    assert f.advice == ""
    assert f.key == "app"
    assert f.detail == "ValueError: 声音名称不能包含 /"


def test_chinese_fallback_drops_developer_command_hint():
    f = explain(RuntimeError("这个功能暂时不能用，请先运行：voicetwin doctor"))
    assert f.title == "这个功能暂时不能用"


def test_unknown_english_error():
    f = explain(KeyError("x"))
    assert f.title == UNKNOWN_TITLE == "出现了意外错误"
    assert "技术细节" in f.advice
    assert f.key == "unknown"
    assert f.detail == "KeyError: 'x'"


def test_string_input_is_treated_as_message():
    f = explain("[Errno 28] No space left on device")
    assert f.detail == "[Errno 28] No space left on device"
    f2 = explain("声音名称不能为空")
    assert f2.title == "声音名称不能为空" and f2.detail == "声音名称不能为空"


def test_never_raises_on_weird_input():
    class Bad(Exception):
        def __str__(self):
            raise RuntimeError("str() 坏了")

    for obj in (None, "", b"CUDA out of memory", 12345, Bad(), Exception(), object()):
        f = explain(obj)  # type: ignore[arg-type]
        assert isinstance(f, Friendly) and f.title
    assert explain(b"CUDA out of memory").key == "gpu_oom"
    assert explain(None).title == UNKNOWN_TITLE


def test_friendly_passes_through():
    f = Friendly("标题", "建议", "细节")
    assert explain(f) is f
    assert f.key == ""  # 第四个字段有默认值，按接口 D 只传三个参数也能用


def test_long_detail_keeps_the_end():
    lines = [f"line {i} " + "x" * 50 for i in range(200)]
    msg = "gsv_s2_train 失败（退出码 1）。最后的日志：\n" + "\n".join(lines) + "\nValueError: 最后一行才是原因"
    f = explain(RuntimeError(msg))
    assert len(f.detail) <= 2100
    assert f.detail.startswith("RuntimeError: gsv_s2_train 失败")
    assert f.detail.rstrip().endswith("最后一行才是原因")
    md = friendly_md(f)
    assert "最后一行才是原因" in md


def test_called_process_error_output_is_searched():
    err = subprocess.CalledProcessError(1, ["python", "x.py"], output=b"", stderr=b"CUDA out of memory")
    assert explain(err).key == "gpu_oom"


def test_config_yaml_error_names_file_and_line():
    yaml = pytest.importorskip("yaml")
    try:
        yaml.safe_load("workspace: ./ws\nbackend: gptsovits: x\n")
    except yaml.YAMLError as exc:
        f = explain(exc)
    else:  # pragma: no cover
        pytest.fail("yaml 应该报错")
    assert f.key == "config_yaml"
    assert "config.yaml" in f.title and "第 2 行" in f.title
    assert "冒号" in f.advice and "Tab" in f.advice

    try:
        yaml.safe_load("a:\n\t- x\n")
    except yaml.YAMLError as exc:
        assert explain(exc).key == "config_yaml"

    msg = ('while scanning a simple key\n  in "D:\\VoiceTwin\\config.yaml", line 12, column 1\n'
           "could not find expected ':'\n  in \"D:\\VoiceTwin\\config.yaml\", line 13, column 1")
    f = explain(msg)
    assert f.key == "config_yaml" and "第 12 行" in f.title
    assert "D:\\VoiceTwin\\config.yaml" in f.advice


def test_paths_inside_messages_do_not_cause_wrong_network_rules():
    # modelscope 缓存路径里的「找不到文件」不是「连不上 ModelScope」
    f = explain(FileNotFoundError(2, "No such file or directory",
                                  "C:\\Users\\a\\.cache\\modelscope\\hub\\iic\\paraformer\\config.yaml"))
    assert f.key == "not_found" and "config.yaml" in f.title
    # 自己代码里的 TimeoutError（中文提示）不是网络问题
    assert explain(TimeoutError("等待 GPT-SoVITS 超时")).title == "等待 GPT-SoVITS 超时"
    # 本机推理服务返回 400 不算「下载网站」的问题
    assert not explain("400 Client Error: Bad Request for url: http://127.0.0.1:9880/tts").key.startswith("net_")


def test_gpu_status_message_from_doctor_is_driver_problem():
    msg = ("显卡驱动没有正常工作（NVIDIA-SMI has failed）。请到 https://www.nvidia.cn/drivers/lookup/ "
           "下载安装最新驱动，然后重启电脑")
    assert explain(RuntimeError(msg)).key == "driver"


def test_fatal_keys_are_real_rules():
    from voicetwin.errors import _RULE_KEYS

    assert set(FATAL_KEYS) <= set(_RULE_KEYS)
    assert "ram" not in FATAL_KEYS  # 某个视频太长导致内存不够时，别的文件还可以继续处理


def test_is_fatal():
    assert is_fatal(RuntimeError("CUDA out of memory"))
    assert is_fatal(RuntimeError("GPT-SoVITS 推理服务启动失败：\nboom"))
    assert is_fatal("NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver")
    assert is_fatal(OSError(28, "No space left on device"))
    assert is_fatal(TaskCancelled())
    assert not is_fatal(RuntimeError("第 3 句合成失败：你好"))
    assert not is_fatal(KeyError("x"))
    assert is_fatal(explain("CUDA out of memory"))
    assert {"gpu_oom", "disk", "driver", "api_start", "stopped"} <= set(FATAL_KEYS)


# --------------------------------------------------------------------------- friendly_md / friendly_line

def _fences_balanced(md: str) -> bool:
    return md.count("```") % 2 == 0


def test_friendly_md_structure():
    f = explain(RuntimeError("torch.cuda.OutOfMemoryError: CUDA out of memory"))
    md = friendly_md(f, what="训练", log_path="D:/VoiceTwin/workspace/我的声音/logs/voicetwin.log")
    assert md.startswith("### ❌ 训练没有完成：显卡内存（显存）不够")
    assert "**怎么办**：" in md
    assert "详细记录在：`D:/VoiceTwin/workspace/我的声音/logs/voicetwin.log`" in md
    assert "技术细节（给帮你的人看）" in md
    assert _fences_balanced(md)
    assert "<details>" not in md


def test_friendly_md_without_what_or_advice():
    md = friendly_md(explain(ValueError("声音名称不能为空")))
    assert md.startswith("### ❌ 声音名称不能为空")
    assert "怎么办" not in md  # 应用自己的中文提示已经说清楚了
    assert _fences_balanced(md)


def test_friendly_md_escapes_backticks_in_detail():
    f = Friendly("出错", "再试", "前面 ```python\nprint(1)\n``` 后面" + "y" * 1000)
    md = friendly_md(f)
    assert _fences_balanced(md)
    assert md.count("```") == 2
    assert "'''python" in md


def test_friendly_md_escapes_markdown_but_keeps_links():
    f = Friendly("名称不能包含 * 和 _ 还有 <b>", "看 https://www.nvidia.cn/drivers/lookup/ 和 https://a.b/x_y_z", "d")
    md = friendly_md(f)
    assert "\\*" in md and "\\_" in md and "\\<b\\>" in md
    assert "https://www.nvidia.cn/drivers/lookup/" in md
    assert "https://a.b/x_y_z" in md  # 网址里的下划线不能转义，否则链接会坏


def test_friendly_md_for_stopped_task_is_not_an_error():
    md = friendly_md(explain(TaskCancelled()), what="训练")
    assert md.startswith("### ⏹ 训练已停止")
    assert "❌" not in md and "技术细节" not in md


def test_friendly_md_accepts_exception_directly():
    md = friendly_md(MemoryError())  # type: ignore[arg-type]
    assert "电脑内存不够" in md


def test_every_rule_md_is_well_formed():
    for err, _, _ in CASES:
        md = friendly_md(explain(err), what="准备素材", log_path="C:/a`b.log")
        assert _fences_balanced(md), md
        assert md.startswith("### ")


def test_friendly_line_and_str():
    f = explain(MemoryError())
    line = friendly_line(f, what="准备素材")
    assert line.startswith("❌ 准备素材没有完成：电脑内存不够。怎么办：")
    assert "\n" not in line
    assert friendly_line(TaskCancelled()) == "⏹ 已停止"
    assert str(f).startswith("电脑内存不够。怎么办：")
    assert friendly_line(KeyError("x")).startswith("❌ 出错了：出现了意外错误")


def test_errors_module_has_no_heavy_imports():
    import os
    import subprocess as sp
    import sys
    from pathlib import Path

    root = str(Path(__file__).resolve().parents[1])
    env = dict(os.environ, PYTHONPATH=root + os.pathsep + os.environ.get("PYTHONPATH", ""))
    code = ("import sys, voicetwin.errors as e; assert e.__file__.startswith(sys.argv[1]), e.__file__; "
            "e.explain(RuntimeError('CUDA out of memory')); "
            "bad=[m for m in ('torch','gradio','numpy','yaml','requests') if m in sys.modules]; "
            "print(','.join(bad))")
    out = sp.run([sys.executable, "-c", code, root], capture_output=True, text=True, check=True, cwd=root, env=env)
    assert out.stdout.strip() == ""
