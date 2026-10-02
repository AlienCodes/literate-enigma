"""把报错翻译成大白话：哪里出错了、怎么办。

网页（以及进度条）出错时，不再把一大段英文 traceback 甩给老师，而是：
- 一个简短的中文标题（出了什么问题）；
- 具体的中文建议（「怎么办」）；
- 原始的技术细节（给帮她安装的人看）。

用法::

    from voicetwin.errors import explain, friendly_md
    try:
        ...
    except Exception as exc:
        f = explain(exc)          # Friendly(title=..., advice=..., detail=..., key=...)
        md = friendly_md(f, what="训练", log_path=str(log_file))

说明：
- 这个模块只用标准库（不导入 torch / gradio 等），任何地方都可以放心导入。
- ``explain`` 永远不会抛出异常；不认识的报错也会给出一个能用的结果。
- 规则按顺序匹配：先认「根本原因」（显存不够、硬盘满了、网络……），
  最后才认「外层包装」（某一步失败、推理服务没启动……），
  这样 GPT-SoVITS 日志尾巴里真正的原因会优先显示出来。
- 命令行仍然打印原始文字；这里的建议是按网页的按钮和页面写的。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

__all__ = [
    "Friendly",
    "explain",
    "friendly_md",
    "friendly_line",
    "is_fatal",
    "FATAL_KEYS",
]


@dataclass
class Friendly:
    """一条翻译好的报错。

    - title：简短的中文标题，例如「显卡内存（显存）不够」。
    - advice：中文的「怎么办」；应用自己的中文提示本身就说清楚了时为空字符串。
    - detail：原始报错文字（给帮忙的人看），最长约 2000 字。
    - key：命中的规则名，例如 'gpu_oom'、'disk'、'stopped'；没认出来时是 'unknown'，
      应用自己的中文提示是 'app'。其它模块可以用它做判断（例如 key == 'disk' 时不再继续处理后面的文件）。
    """

    title: str
    advice: str
    detail: str
    key: str = ""

    def __str__(self) -> str:  # 方便直接 str() 或写进日志
        return self.title + (f"。怎么办：{self.advice}" if self.advice else "")


# --------------------------------------------------------------------------- 常量

DRIVER_URL = "https://www.nvidia.cn/drivers/lookup/"
VCREDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"

UNKNOWN_TITLE = "出现了意外错误"
UNKNOWN_ADVICE = "可以先再点一次试试；还不行的话，把下面「技术细节」里的文字复制下来，发给帮你安装的人。"

DETAIL_LIMIT = 2000
MD_DETAIL_LIMIT = 600
_SEARCH_LIMIT = 20000

#: 这些问题和输入无关，换一个候选、换一个文件再试也会一样失败，调用方可以立刻停下。
#: （电脑内存不够 'ram' 不算：可能只是某个视频太长，换个文件也许就行。）
FATAL_KEYS = frozenset({
    "stopped", "gpu_oom", "disk", "torch_cpu", "gpu_arch", "driver", "gsv_missing", "models_missing",
    "api_start", "api_mismatch", "module", "import_version", "dll", "speaker_model", "ffmpeg_missing",
})

_CJK = re.compile(r"[\u4e00-\u9fff]")
_URL = re.compile(r"https?://[^\s，。；、）」』】]+")
# Python 报错行：「xxx.YyyError: ……」或单独一行「KeyboardInterrupt」。故意区分大小写，不认「ERROR:」「UserWarning:」。
_EXC_LINE = re.compile(
    r"^[ \t]*(?:[A-Za-z_]\w*\.)*(?:[A-Za-z_]\w*)?(?:Error|Exception|Interrupt|Cancelled|Exit|Failure)(?::[^\n]*)?[ \t]*$",
    re.M,
)
_MEDIA_EXT = (r"mp4|m4v|mov|mkv|avi|flv|f4v|wmv|webm|ts|mts|m2ts|mpg|mpeg|3gp|rmvb|rm|vob|"
              r"mp3|wav|flac|aac|m4a|ogg|opus|wma|amr|ape")
_FFMPEG_INPUT = re.compile(r"-i (.+?\.(?:" + _MEDIA_EXT + r"))(?=\s|$)", re.I)
_QUOTED_FILE = re.compile(r"['\"]([^'\"\n]{1,400}?\.[A-Za-z0-9]{1,6})['\"]")
_DRIVE = re.compile(r"(?<![A-Za-z])([A-Za-z]):[\\/]")

# GPT-SoVITS 训练各步骤的日志名（backends 的 run_logged）→ 中文步骤名
STEP_NAMES = {
    "gsv_1a_text": "处理文字",
    "gsv_1b_hubert": "提取声音特征",
    "gsv_1b_sv": "提取声纹",
    "gsv_1c_semantic": "提取语义",
    "gsv_s2_train": "训练音色（SoVITS）",
    "gsv_s1_train": "训练语气和节奏（GPT）",
    "qwen3_download": "下载 Qwen3-TTS 模型",
    "qwen3_prepare": "准备 Qwen3-TTS 训练数据",
    "qwen3_sft": "训练 Qwen3-TTS",
}

# 缺少的 Python 包 → 是哪个组件
_COMPONENTS = {
    "faster_whisper": "语音识别（faster-whisper）",
    "ctranslate2": "语音识别（faster-whisper）",
    "funasr": "中文语音识别（funasr）",
    "modelscope": "中文语音识别（funasr）",
    "gradio": "网页界面（gradio）",
    "gradio_client": "网页界面（gradio）",
    "torch": "PyTorch（显卡计算）",
    "torchaudio": "PyTorch（显卡计算）",
    "resemblyzer": "声纹打分（resemblyzer）",
    "webrtcvad": "声纹打分（resemblyzer）",
    "webrtcvad_wheels": "声纹打分（resemblyzer）",
    "speechbrain": "声纹打分（speechbrain）",
    "noisereduce": "降噪（noisereduce）",
    "demucs": "去背景音乐（demucs）",
    "docx": "读取 Word 讲稿（python-docx）",
    "python_docx": "读取 Word 讲稿（python-docx）",
    "yaml": "读取设置文件（PyYAML）",
    "pyyaml": "读取设置文件（PyYAML）",
    "imageio_ffmpeg": "ffmpeg（处理视频和音频）",
    "voicetwin": "声音分身本身",
    "qwen_tts": "Qwen3-TTS（可选引擎）",
    "indextts": "IndexTTS（可选引擎）",
}
for _m in ("numpy", "scipy", "soundfile", "librosa", "pyloudnorm", "numba", "llvmlite", "audioread", "soxr",
           "requests", "urllib3", "huggingface_hub", "tqdm"):
    _COMPONENTS.setdefault(_m, f"基础组件（{_m}）")
del _m

_EXTRAS = {
    "asr": "语音识别（faster-whisper）",
    "webui": "网页界面（gradio）",
    "funasr": "中文语音识别（funasr）",
    "separate": "去背景音乐（demucs）",
    "denoise": "降噪（noisereduce）",
    "docx": "读取 Word 讲稿（python-docx）",
}

# 这些模块属于 GPT-SoVITS 整合包本身（缺了说明整合包不完整）
_GSV_MODULES = frozenset({
    "gpt_sovits", "ar", "module", "text", "feature_extractor", "tools", "process_ckpt", "my_utils", "bigvgan",
    "sv", "eres2net", "transformers", "pytorch_lightning", "lightning", "jieba_fast", "jieba", "pypinyin",
    "g2p_en", "cn2an", "langsegment", "fast_langdetect", "wordsegment", "pyopenjtalk", "ffmpeg", "peft",
    "x_transformers", "rotary_embedding_torch", "opencc", "g2pk2", "ko_pron", "tojyutping", "split_lang",
    "sentencepiece", "nltk", "tensorboard", "matplotlib", "einops", "torchmetrics", "onnxruntime",
    "fastapi", "uvicorn", "soundfile_backend",
})


# --------------------------------------------------------------------------- 规则

class _Ctx:
    """匹配时的上下文：原始异常、全文、命中位置。"""

    def __init__(self, err: Optional[BaseException], text: str, match: "re.Match[str]") -> None:
        self.err = err
        self.text = text
        self.match = match

    @property
    def line(self) -> str:
        start = self.text.rfind("\n", 0, self.match.start()) + 1
        end = self.text.find("\n", self.match.end())
        return self.text[start:] if end < 0 else self.text[start:end]


Filler = Callable[[_Ctx], Dict[str, str]]


class _Rule:
    __slots__ = ("key", "pattern", "title", "advice", "fill", "exclude", "wrapper")

    def __init__(self, key: str, pattern: str, title: str, advice: str, fill: Optional[Filler] = None,
                 exclude: Optional[str] = None, wrapper: bool = False) -> None:
        self.key = key
        self.pattern: re.Pattern[str] = re.compile(pattern, re.I)
        self.title = title
        self.advice = advice
        self.fill = fill
        # exclude：如果命中的那一行同时符合 exclude，就不算命中（例如本机 127.0.0.1 的连接错误不是「网络问题」）
        self.exclude: Optional[re.Pattern[str]] = re.compile(exclude, re.I) if exclude else None
        # wrapper：外层包装类的报错（「某一步失败」等），只在找不到根本原因时才用
        self.wrapper = wrapper

    def find(self, err: Optional[BaseException], text: str) -> Optional[_Ctx]:
        for m in self.pattern.finditer(text):
            ctx = _Ctx(err, text, m)
            if self.exclude is not None and self.exclude.search(ctx.line):
                continue
            return ctx
        return None


class _Blank(dict):
    def __missing__(self, key: str) -> str:
        return ""


def _basename(path: str) -> str:
    parts = [p for p in re.split(r"[\\/]+", path.strip().strip("'\"")) if p]
    return parts[-1] if parts else ""


def _useful_name(name: str) -> bool:
    """临时文件、内部文件名对老师没有意义，不显示。"""
    low = name.lower()
    return bool(name) and not low.endswith((".part", ".tmp", ".src.wav", ".lock")) and len(name) <= 120


def _iter_chain(err: Optional[BaseException]) -> Iterator[BaseException]:
    seen = set()
    depth = 0
    while err is not None and id(err) not in seen and depth < 6:
        seen.add(id(err))
        yield err
        nxt = err.__cause__
        if nxt is None and not getattr(err, "__suppress_context__", False):
            nxt = err.__context__
        err = nxt
        depth += 1


def _file_from(ctx: _Ctx) -> str:
    """尽量找出出问题的文件名（只要文件名，不要整条路径）。"""
    names: List[str] = []
    for e in _iter_chain(ctx.err):
        for attr in ("filename2", "filename"):  # os.replace(a, b) 失败时 b 才是被占用的那个
            v = getattr(e, attr, None)
            if isinstance(v, (str, bytes)) and v:
                names.append(v.decode("utf-8", "replace") if isinstance(v, bytes) else v)
    names += list(reversed(_QUOTED_FILE.findall(ctx.line)))
    for raw in names:
        name = _basename(str(raw))
        if _useful_name(name):
            return name
    return ""


def _fill_file(ctx: _Ctx) -> Dict[str, str]:
    name = _file_from(ctx)
    return {"file": name, "file_q": f"「{name}」" if name else "", "file_s": f"：{name}" if name else ""}


_UNQUOTED_MISSING = re.compile(
    r"((?:[A-Za-z]:)?[^\s:'\"]+\.[A-Za-z0-9]{1,6}): (?:No such file or directory|Invalid data found)")


def _fill_path(ctx: _Ctx) -> Dict[str, str]:
    """找不到的文件：先看异常里的 filename / 引号里的路径，再看 ffmpeg 的「路径: No such file or directory」。"""
    values = _fill_file(ctx)
    if values["file"]:
        return values
    for m in (_UNQUOTED_MISSING.search(ctx.line), _FFMPEG_INPUT.search(ctx.text)):
        if m:
            name = _basename(m.group(1))
            if _useful_name(name):
                return {"file": name, "file_q": f"「{name}」", "file_s": f"：{name}"}
    return values


def _fill_media(ctx: _Ctx) -> Dict[str, str]:
    m = _FFMPEG_INPUT.search(ctx.text)
    name = _basename(m.group(1)) if m else ""
    if not _useful_name(name):
        name = ""
    return {"file": name, "file_s": f"：{name}" if name else ""}


def _fill_drive(ctx: _Ctx) -> Dict[str, str]:
    drive = ""
    for e in _iter_chain(ctx.err):
        v = getattr(e, "filename", None)
        if isinstance(v, str):
            m = _DRIVE.search(v)
            if m:
                drive = m.group(1).upper()
                break
    if not drive:
        m = _DRIVE.search(ctx.line)
        drive = m.group(1).upper() if m else ""
    if drive:
        return {"where": f"{drive} 盘", "clean": f" {drive} 盘（还有 C 盘）"}
    return {"where": "硬盘", "clean": "放声音分身和 GPT-SoVITS 的那个盘（一般是 D 盘）和 C 盘"}


def _fill_yaml(ctx: _Ctx) -> Dict[str, str]:
    m = re.search(r'in "([^"\n]+)", line (\d+)', ctx.text)
    name = _basename(m.group(1)) if m else ""
    if not name or name.startswith("<"):
        name = "config.yaml"
    line = m.group(2) if m else ""
    path = m.group(1) if m and not m.group(1).startswith("<") else name
    return {"name": name, "path": path, "at": f"（第 {line} 行附近）" if line else "",
            "look": f"看第 {line} 行附近" if line else "看看哪里写得不对"}


def _component(ctx: _Ctx) -> Tuple[str, str]:
    """返回（组件中文名, 模块名），找不到时组件名为空。"""
    patterns = (
        r"No module named ['\"]?([\w.]+)",
        r"cannot import name ['\"]?\w+['\"]? from ['\"]?([\w.]+)",
        r"未安装\s*([A-Za-z][\w.\-]*)",
        r"需要安装\s*([A-Za-z][\w.\-]*)",
        r"没有安装\s*([A-Za-z][\w.\-]*)",
        r"pip install\s+(?:-U\s+)?[\"']?([A-Za-z][\w.\-]*(?:\[\w+\])?)",
        r"\b(numpy)\.core\.multiarray",
        r"NumPy (\d)\.x",
    )
    m = None
    for text in (ctx.line, ctx.text):  # 先看命中的那一行（真正的报错行），再看全文
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                break
        if m:
            break
    if m:
        raw = m.group(1)
        if raw in ("1", "2"):
            raw = "numpy"
        extra = re.search(r"\[(\w+)\]", raw)
        if extra and extra.group(1).lower() in _EXTRAS:
            return _EXTRAS[extra.group(1).lower()], raw.split("[")[0]
        mod = raw.split("[")[0].split(".")[0]
        norm = mod.lower().replace("-", "_")
        if norm in _COMPONENTS:
            return _COMPONENTS[norm], mod
        return mod, mod
    return "", ""


def _is_gsv_module(mod: str, text: str) -> bool:
    norm = mod.lower().replace("-", "_")
    if norm in _COMPONENTS:
        return False
    return norm in _GSV_MODULES or bool(re.search(r"GPT_SoVITS[\\/]|api_v2\.py|\bgsv_\w+", text))


_REINSTALL = "请重新双击 install_windows.bat 安装一次（你的数据不会丢）。"
_GSV_REINSTALL = ("这是 GPT-SoVITS 整合包里的组件。请确认整合包是完整解压出来的（不要在压缩包里直接运行），"
                  "然后重新双击 install_windows.bat（你的数据不会丢）。")


def _fill_module(ctx: _Ctx) -> Dict[str, str]:
    comp, mod = _component(ctx)
    if mod and _is_gsv_module(mod, ctx.text):
        return {"what": f"GPT-SoVITS 整合包里的组件（{mod}）", "advice": _GSV_REINSTALL}
    tip = ""
    norm = mod.lower().replace("-", "_")
    if "funasr" in comp:
        tip = "也可以在「① 准备素材」的「高级设置」里把识别引擎换成「通用」，就用不到它了。"
    elif "demucs" in comp:
        tip = "也可以先把「视频有背景音乐」的勾去掉。"
    elif "Word" in comp:
        tip = "也可以直接把讲稿文字复制粘贴到「讲稿」框里。"
    elif norm in ("qwen_tts", "indextts"):
        tip = "这是可选的引擎，不装也行：把引擎换回「GPT-SoVITS」就可以。"
    return {"what": f"「{comp}」组件" if comp else "组件", "advice": _REINSTALL + tip}


def _fill_step(ctx: _Ctx) -> Dict[str, str]:
    log_name = ctx.match.group(1)
    step = STEP_NAMES.get(log_name, log_name)
    engine = "GPT-SoVITS" if log_name.startswith("gsv_") else ""
    return {"step": step, "engine": engine, "log": f"{log_name}.log"}


def _fill_engine(ctx: _Ctx) -> Dict[str, str]:
    # 英文名后面留一个空格再接中文；没认出是哪个引擎时说「合成引擎」
    if "GPT-SoVITS" in ctx.text or "api_v2" in ctx.text:
        return {"engine": "GPT-SoVITS "}
    m = re.search(r"(Qwen3-TTS|IndexTTS)", ctx.text, re.I)
    return {"engine": m.group(1) + " " if m else "合成引擎"}


def _fill_voice(ctx: _Ctx) -> Dict[str, str]:
    m = re.search(r"还没有名为「([^」\n]{1,60})」的声音", ctx.text)
    return {"voice": f"「{m.group(1)}」这个声音" if m else "这个声音"}


def _fill_sentence(ctx: _Ctx) -> Dict[str, str]:
    m = re.search(r"第\s*(\d+)\s*句", ctx.text)
    return {"n": f"第 {m.group(1)} 句" if m else "有一句"}


_GPU_FREE = "关掉游戏、剪映、在线视频等占用显卡的程序"
_LOCAL_EXCLUDE = r"proxy|代理|huggingface|hf-mirror|modelscope"
_NET_EXCLUDE = r"127\.0\.0\.1|localhost"

# 顺序很重要：越具体、越像「根本原因」的越靠前；wrapper=True 的是外层包装，放最后。
_RULES: List[_Rule] = [
    # ---- 用户自己停下的
    _Rule("stopped", r"\bTaskCancelled\b|\bKeyboardInterrupt\b",
          "已停止",
          "任务已经按你的要求停下了。想继续的话，再点一次开始按钮就行。"),

    # ---- 显卡、内存、硬盘
    _Rule("gpu_oom",
          r"CUDA out of memory|CUDA error: out of memory|OutOfMemoryError|CUBLAS_STATUS_ALLOC_FAILED|"
          r"CUDNN_STATUS_ALLOC_FAILED|cudaErrorMemoryAllocation|CUDA_ERROR_OUT_OF_MEMORY",
          "显卡内存（显存）不够",
          _GPU_FREE + "，再点一次。训练时：打开「② 训练模型」的「高级设置」，把「每批数量」改成 2 再试；"
          "生成时：把「质量」选低一档再试。"),
    _Rule("pagefile", r"WinError 1455|页面文件太小|paging file is too small",
          "电脑的虚拟内存不够",
          "先关掉其他程序再试一次；如果经常出现，重启电脑，或者请懂电脑的人把 C 盘的「虚拟内存」调大"
          "（建议 32 GB 以上），并保证 C 盘有足够的空闲空间。"),
    _Rule("ram",
          r"\bMemoryError\b|Unable to allocate|bad allocation|std::bad_alloc|DefaultCPUAllocator|"
          r"not enough memory|WinError 8\]|Not enough memory resources|存储空间不足，无法处理此命令",
          "电脑内存不够",
          "关掉其他程序（特别是开了很多网页的浏览器、剪映等）再试；如果某个视频超过 2 小时，先剪成 1 小时以内的几段。"),
    _Rule("disk",
          r"No space left|Errno 28\]|\bENOSPC\b|WinError 112\b|not enough space on the disk|磁盘空间不足|"
          r"PytorchStreamWriter failed writing|unexpected pos \d+ vs \d+",
          "{where}空间不够",
          "请清理{clean}，至少空出 30 GB 再试：可以清空回收站、删掉不用的大视频。",
          fill=_fill_drive),
    _Rule("path_too_long",
          r"WinError 206\b|文件名或扩展名太长|filename or extension is too long|File name too long|Errno 36\]",
          "文件路径太长",
          "把声音分身和视频放在短一点的路径里（比如 D:\\VoiceTwin 和 D:\\视频），文件名也尽量短一点，再试一次。"),
    _Rule("file_locked",
          r"WinError 32\b|being used by another process|另一个程序正在使用此文件|Errno 13\]|Permission denied|"
          r"PermissionError|WinError 5\]|Access is denied|拒绝访问",
          "文件{file_q}被别的程序占用",
          "如果用 Excel 或 WPS 打开了 transcripts.csv，或者用播放器打开了音频，请先关掉再试。"
          "还不行的话，重启电脑后再试；另外不要把声音分身放在 C:\\Program Files 这类系统文件夹里。",
          fill=_fill_file),

    # ---- 显卡驱动 / 整合包版本
    _Rule("torch_cpu", r"Torch not compiled with CUDA enabled",
          "现在用的 PyTorch 不支持显卡",
          "请确认用的是 NVIDIA 显卡版的 GPT-SoVITS 整合包（RTX 50 系列要用 nvidia50 版），"
          "然后重新双击 install_windows.bat，输入整合包的位置。"),
    _Rule("gpu_arch",
          r"no kernel image is available|sm_\d+ is not compatible|not compatible with the current PyTorch installation",
          "显卡太新，这个整合包不支持",
          "RTX 50 系列（5060、5070、5080、5090）请换用 nvidia50 版的 GPT-SoVITS 整合包，"
          "然后重新双击 install_windows.bat，输入新整合包的位置。"),
    _Rule("driver",
          r"no CUDA-capable device|CUDA driver version is insufficient|NVIDIA-SMI has failed|"
          r"couldn't communicate with the NVIDIA driver|no NVIDIA driver|NVIDIA driver on your system|"
          r"显卡驱动没有正常工作|显卡没有正常工作|显卡驱动未安装|"
          r"NVIDIA driver (?:is )?(?:not|too old)|CUDA unknown error|"
          r"CUDA driver initialization failed|cudaGetDeviceCount|torch\.cuda\.is_available\(\) is False|"
          r"CUDA initialization|CUDA_ERROR_NO_DEVICE|CUDA_ERROR_NOT_INITIALIZED|nvcuda\.dll",
          "显卡驱动没装好或太旧",
          f"到 {DRIVER_URL} 下载安装最新的显卡驱动，装好后重启电脑，再点一次。"
          "RTX 50 系列显卡还要用 nvidia50 版的整合包；没有 NVIDIA 显卡的电脑没法训练。"),
    _Rule("gpu_crash",
          r"CUDA error: an illegal memory access|CUDA error: unspecified launch failure|CUDA error: misaligned address|"
          r"CUDA error: the launch timed out|CUDA_ERROR_LAUNCH_FAILED|cudaErrorLaunchFailure|CUDA error: unknown error",
          "显卡计算时出错了",
          f"关掉其他占用显卡的程序，重启电脑后再试；还不行就到 {DRIVER_URL} 更新显卡驱动。"),

    # ---- 端口
    _Rule("port",
          r"Address already in use|Errno 98\]|Errno 10048|WinError 10048|only one usage of each socket address|"
          r"通常每个套接字地址|Cannot find empty port|port \d+ is (?:already )?in use|error while attempting to bind|"
          r"WinError 10013\b|访问权限不允许的方式做了一个访问套接字",
          "端口被占用（可能已经开着一个声音分身）",
          "先看看浏览器里是不是已经打开了声音分身的网页；如果没有，关掉所有声音分身的黑色窗口，"
          "再双击桌面上的「声音分身 VoiceTwin」。还不行就重启电脑。"),

    # ---- 应用自己的中文提示（比较准，放在网络规则前面）
    _Rule("gsv_missing",
          r"找不到 GPT-SoVITS 目录|不是完整的 GPT-SoVITS 目录|缺少 api_v2\.py|can't open file [^\n]*api_v2\.py",
          "没找到 GPT-SoVITS 整合包",
          "重新双击 install_windows.bat，输入整合包的位置（例如 D:\\GPT-SoVITS）。"
          "如果你移动过整合包的文件夹，就输入新的位置。"),
    _Rule("models_missing",
          r"缺少预训练模型|"
          r"(?:No such file or directory|Errno 2\]|WinError [23]\]|does not exist|not found|找不到)[^\n]{0,300}pretrained_models|"
          r"pretrained_models[^\n]{0,300}(?:No such file or directory|does not exist|not found)",
          "缺少 GPT-SoVITS 的模型文件",
          "到「🩺 环境检查」页点「⬇️ 下载缺少的模型」，下载完再试。"),
    _Rule("no_clips", r"没有可用于训练的片段",
          "没有可以用来训练的句子",
          "到「① 准备素材」的校对表里，把要用的句子的「保留」改成「是」，再点「保存修改」；"
          "如果表是空的，先点「开始准备素材」。"),
    _Rule("not_prepared", r"还没有名为「|还没有参考音频|没有参考音频|没有可用于评估的片段|没有验证集|还没有可用的素材",
          "{voice}还没有准备素材",
          "先在「① 准备素材」里点「开始准备素材」，完成后再做这一步。"
          "如果已经准备过，看看页面上方的「声音名称」有没有选对。",
          fill=_fill_voice),
    _Rule("no_media", r"没有找到任何视频或音频文件|找不到文件夹|文件夹不存在",
          "文件夹里没找到视频或录音",
          "检查文件夹路径有没有写对（可以在文件夹窗口顶部的地址栏复制路径，再粘贴过来）；"
          "支持 mp4、mov、mkv、mp3、wav、m4a 等常见格式。"),
    _Rule("empty_script", r"讲稿里没有可以朗读的内容",
          "讲稿是空的",
          "在「讲稿」框里粘贴文字，或者上传 txt / Word 文件。"),
    _Rule("external_api", r"连接不上 GPT-SoVITS 服务",
          "连不上单独运行的 GPT-SoVITS 服务",
          "设置文件 config.yaml 里填了 backends.gptsovits.api_url：请先把那个 GPT-SoVITS 服务启动起来；"
          "如果不需要，就把这一项清空，让声音分身自己启动。"),
    _Rule("speaker_model", r"没有可用的声纹模型",
          "声纹打分组件没装好",
          _REINSTALL),
    _Rule("ffmpeg_missing",
          r"找不到 ffmpeg|'ffmpeg' 不是内部或外部命令|ffmpeg(?:\.exe)?['\"]? is not recognized|"
          r"No such file or directory: ['\"]ffmpeg",
          "ffmpeg 没装好（处理视频和音频要用它）",
          "重新双击 install_windows.bat 安装一次；如果用的是 GPT-SoVITS 整合包，确认整合包文件夹里有 ffmpeg.exe。"),

    # ---- 缺组件 / 组件坏了
    _Rule("import_version",
          r"cannot import name|numpy\.core\.multiarray failed to import|compiled using NumPy 1\.x cannot be run|"
          r"_ARRAY_API not found",
          "有组件的版本不对",
          _REINSTALL),
    _Rule("module", r"No module named|ModuleNotFoundError|未安装|需要安装|没有安装|pip install",
          "缺少{what}",
          "{advice}",
          fill=_fill_module),
    _Rule("dll",
          r"DLL load failed|WinError 126\b|找不到指定的模块|Error loading [^\n]*\.dll|WinError 193\b|"
          r"is not a valid Win32 application|不是有效的 Win32 应用程序",
          "有组件加载不了（可能缺少系统运行库）",
          f"请安装微软 VC++ 运行库（{VCREDIST_URL} ），装好后重启电脑；"
          "还不行就重新解压 GPT-SoVITS 整合包，再双击 install_windows.bat。"),
    _Rule("model_corrupt",
          r"PytorchStreamReader failed|failed finding central directory|invalid load key|SafetensorError|"
          r"HeaderTooLarge|Unable to load weights from pytorch checkpoint",
          "模型文件{file_q}坏了（可能没下载完整）",
          "把这个模型文件删掉，再到「🩺 环境检查」页点「⬇️ 下载缺少的模型」重新下载；"
          "如果是自己训练出来的模型，就重新训练一次。",
          fill=_fill_file),

    # ---- 设置文件、文字编码
    _Rule("config_yaml",
          r"\b(?:ScannerError|ParserError|ComposerError|ConstructorError|ReaderError|MarkedYAMLError|YAMLError)\b|"
          r"while scanning a|while parsing a|mapping values are not allowed|could not find expected ':'|"
          r"that cannot start any token|expected <block end>|found undefined alias|unacceptable character",
          "设置文件 {name} 写错了{at}",
          "用记事本打开 {path}，{look}：冒号「:」后面要有一个空格，缩进要用空格、不要用 Tab，标点要用英文的。"
          "改不好的话，把这个文件改个名字（比如 config.bak.yaml），再重新双击 install_windows.bat，会生成一份新的设置文件。",
          fill=_fill_yaml),
    _Rule("encoding", r"UnicodeDecodeError|codec can't decode",
          "文件的文字编码不对（不是 UTF-8）",
          "如果是 transcripts.csv：在 WPS 或 Excel 里「另存为」时选「CSV UTF-8」，或者直接在网页的校对表里改；"
          "如果是 config.yaml：用记事本打开，「另存为」时编码选「UTF-8」。"),
    _Rule("console_encoding", r"UnicodeEncodeError|codec can't encode",
          "显示文字时出错（编码问题）",
          "请用桌面上的「声音分身 VoiceTwin」图标启动（不要直接运行 python）；还不行就把技术细节发给帮你的人。"),

    # ---- 网络：代理/证书最先（本机代理 127.0.0.1:7890 也算），然后是本机推理服务，最后是外网下载
    _Rule("net_proxy",
          r"SSLError|SSL: |CERTIFICATE_VERIFY_FAILED|certificate verify failed|ProxyError|Cannot connect to proxy|"
          r"Tunnel connection failed",
          "下载失败：网络连接被拦住了",
          "如果开着 VPN、加速器或代理，先关掉再试；再看看电脑右下角的日期和时间对不对（时间不对也会连不上）；"
          "然后再点一次。"),
    _Rule("api_down",
          r"(?:127\.0\.0\.1|localhost)[^\n]*(?:Max retries exceeded|Connection refused|ConnectionRefusedError|"
          r"ConnectionResetError|RemoteDisconnected|Connection aborted|actively refused|WinError 10061|WinError 10054|"
          r"积极拒绝|强迫关闭|Failed to establish a new connection)|"
          r"(?:Connection refused|ConnectionRefusedError|RemoteDisconnected|Connection aborted|actively refused|"
          r"积极拒绝)[^\n]*(?:127\.0\.0\.1|localhost)",
          "GPT-SoVITS 意外停止了（连不上它）",
          "它可能因为显存不够或者出错退出了。" + _GPU_FREE + "，再点一次；还不行就到「🩺 环境检查」页看看，"
          "或者把 logs 文件夹里的 gptsovits_api.log 发给帮你的人。",
          exclude=_LOCAL_EXCLUDE),
    _Rule("api_slow",
          r"(?:127\.0\.0\.1|localhost)[^\n]*(?:timed out|timeout)",
          "GPT-SoVITS 很久没有回应",
          "可能是显存不够，或者这一句太长。" + _GPU_FREE + "再试；把特别长的句子拆短一点。",
          exclude=_LOCAL_EXCLUDE),
    _Rule("cmd_timeout", r"TimeoutExpired|timed out after \d+(?:\.\d+)? seconds",
          "有一步运行太久，被停下了",
          "可能是电脑太忙或者卡住了。关掉其他程序，再点一次；还不行就重启电脑后再试。"),
    _Rule("net_busy",
          r"429 Client Error|Too Many Requests|\b5\d\d Server Error|Bad Gateway|Service Unavailable|Gateway Time-?out",
          "下载网站暂时太忙",
          "等 10 分钟再点一次；如果一直这样，换个时间（比如晚上）再试。",
          exclude=_NET_EXCLUDE),
    _Rule("net_refused",
          r"\b40[0134] Client Error|Repository Not Found|\bEntryNotFoundError|RevisionNotFoundError|GatedRepoError",
          "下载网站上拿不到这个模型文件",
          "可能是下载网站临时出了问题，过一会儿再点一次；如果开着 VPN 或加速器，先关掉再试。还不行就把技术细节发给帮你的人。",
          exclude=_NET_EXCLUDE),
    _Rule("net_timeout",
          r"ConnectTimeout|ReadTimeout|timed out|WinError 10060|连接尝试失败|IncompleteRead|"
          r"ChunkedEncodingError|Connection broken",
          "下载失败：网络太慢或者断了",
          "检查网络后再点一次（已经下载完的文件不会重新下载）；如果开着 VPN 或加速器，先关掉再试。",
          exclude=_NET_EXCLUDE),
    _Rule("net_hf",
          r"huggingface\.co|hf-mirror\.com|LocalEntryNotFoundError|OfflineModeIsEnabled|HfHubHTTPError|"
          r"outgoing traffic has been disabled|appropriate snapshot folder",
          "下载模型失败（连不上下载网站）",
          "第一次使用需要联网下载模型（语音识别模型大约 3 GB）。请检查网络能不能打开网页，"
          "关掉 VPN 或加速器后再点一次；已经下载完的文件不会重新下载。",
          exclude=_NET_EXCLUDE),
    _Rule("net_modelscope",
          r"modelscope\.cn|modelscope\.hub\.errors|modelscope[^\n]{0,200}(?:download|下载|connect|HTTP)",
          "下载中文识别模型失败（连不上 ModelScope）",
          "检查网络后再点一次；如果一直失败，可以在「① 准备素材」的「高级设置」里把识别引擎换成「通用」。",
          exclude=_NET_EXCLUDE),
    _Rule("network",
          r"HTTPSConnectionPool|HTTPConnectionPool|Max retries exceeded|ConnectionError|getaddrinfo|"
          r"Name or service not known|Temporary failure in name resolution|nodename nor servname|"
          r"Failed to establish a new connection|Network is unreachable|NewConnectionError|RemoteDisconnected|"
          r"Connection reset by peer|ConnectionResetError|WinError 1005[14]|WinError 1006[15]|WinError 1100[14]|"
          r"预训练模型下载失败|下载失败",
          "下载失败（网络问题）",
          "检查网络是否通畅（能不能打开网页），然后再点一次；如果开着 VPN 或加速器，先关掉再试；"
          "第一次使用需要联网下载模型。",
          exclude=_NET_EXCLUDE),

    # ---- 视频 / 音频文件本身的问题（ffmpeg）
    _Rule("no_audio",
          r"does not contain any stream|matches no streams|no audio stream",
          "这个视频里没有声音{file_s}",
          "换一个有声音的视频，或者把它从文件夹里拿走。",
          fill=_fill_media),
    _Rule("media_broken",
          r"Invalid data found when processing input|moov atom not found|partial file|Error while decoding stream|"
          r"Truncating packet|corrupt (?:input|decoded frame)",
          "视频文件损坏或没复制完整{file_s}",
          "重新复制这个视频，或者用剪映重新导出一次，再试。",
          fill=_fill_media),
    _Rule("media_codec",
          r"Decoder \([^)\n]*\) not found|Unknown decoder|Unsupported codec|could not find codec parameters|"
          r"Unknown format",
          "这个文件的格式不支持{file_s}",
          "用剪映或格式工厂把它转成 MP4 再试。",
          fill=_fill_media),
    _Rule("not_found",
          r"No such file or directory|Errno 2\]|WinError [23]\]|系统找不到指定的|cannot find the (?:file|path) specified",
          "找不到文件或文件夹{file_s}",
          "检查路径有没有写对，文件是不是被移动、改名或删除了。路径可以在文件夹窗口顶部的地址栏复制，再粘贴过来。",
          fill=_fill_path),

    # ---- 外层包装：只有找不到根本原因时才用
    _Rule("unsaved_edits", r"条修改没有保存，这次没有开始训练",
          "还有修改没有保存，所以没有开始训练",
          "没保存的修改不会用来训练。到「① 准备素材」的校对表点「保存修改」（或者最下面的「✅ 确认训练素材」），"
          "再回来点「开始训练」。红灯的那几行就是没保存的。",
          wrapper=True),
    _Rule("not_confirmed", r"还没有确认训练素材，这次没有开始训练",
          "还没有确认训练素材，所以没有开始训练",
          "到「① 准备素材」，把校对表看一遍、改好、删好以后，点最下面绿色的「✅ 确认训练素材」，再回来点「开始训练」。"
          "只有确认过的素材才会用来训练。",
          wrapper=True),
    _Rule("confirm_stale", r"确认训练素材以后，校对表又改过",
          "确认以后素材又改过，所以没有开始训练",
          "到「① 准备素材」再点一次最下面绿色的「✅ 确认训练素材」（会用现在保存好的文字和没删除的句子），"
          "再回来点「开始训练」。",
          wrapper=True),
    _Rule("api_mismatch", r"推理服务打开了，但是程序没法和它对上话",
          "GPT-SoVITS 已经打开了，但和声音分身对不上",
          "多半是 GPT-SoVITS 整合包的版本和声音分身不配套，或者有别的程序占着同一个端口。"
          "先关掉所有声音分身的黑色窗口再打开试一次；还不行就把「详细过程」里的问题报告"
          "（或者 logs 文件夹里最新的「问题报告」文件）发给帮你的人。",
          wrapper=True),
    _Rule("api_start", r"推理服务启动失败|推理服务启动超时|启动失败（退出码|启动超时（|意外退出",
          "{engine}没能启动",
          "关掉所有声音分身的黑色窗口，再重新打开试试；还不行就到「🩺 环境检查」页看看，或者重启电脑后再试。"
          "再不行就把「详细过程」里的问题报告（或者 logs 文件夹里最新的「问题报告」文件）发给帮你的人。",
          fill=_fill_engine, wrapper=True),
    _Rule("text_step_empty", r"1A 文本处理没有产出",
          "GPT-SoVITS「处理文字」这一步没有结果",
          "先到「① 准备素材」看看校对表里是不是有文字；再到「🩺 环境检查」页看看模型是不是齐全。"
          "还不行就把 logs 文件夹里的 gsv_1a_text.log 发给帮你的人。",
          wrapper=True),
    _Rule("train_no_output", r"训练结束但没有找到权重文件|微调结束但没有找到",
          "训练结束了，但是没有得到模型",
          "通常是显存不够或者硬盘满了。" + _GPU_FREE + "、清理硬盘后，再点一次「开始训练」。"
          "还不行就把 logs 文件夹里的 gsv_s2_train.log 和 gsv_s1_train.log 发给帮你的人。",
          wrapper=True),
    _Rule("step_failed", r"([A-Za-z0-9_]+) 失败（退出码 -?\d+）",
          "{engine}「{step}」这一步出错了",
          _GPU_FREE + "，再点一次试试。还是不行，就把下面的技术细节（或者 logs 文件夹里的 {log}）发给帮你的人。",
          fill=_fill_step, wrapper=True),
    _Rule("select_failed", r"所有模型都合成失败",
          "所有模型都没能生成声音",
          "通常是 GPT-SoVITS 没有正常运行（比如显存不够）。" + _GPU_FREE + "再试；"
          "还不行就把 logs 文件夹里的 gptsovits_api.log 发给帮你的人。",
          wrapper=True),
    _Rule("model_switch", r"切换 (?:GPT|SoVITS) 模型失败",
          "加载训练好的模型失败",
          "模型文件可能坏了或者被删了。到「② 训练模型」点「重新挑选最佳模型」；还不行就重新训练一次。",
          wrapper=True),
    _Rule("sentence_failed", r"第\s*\d+\s*句(?:合成失败|没能生成)",
          "{n}没能生成",
          "把这一句改短一点，或者去掉里面的特殊符号，再生成一次。如果很多句都失败，" + _GPU_FREE + "后再试。",
          fill=_fill_sentence, wrapper=True),
    _Rule("synth_failed", r"合成失败",
          "{engine}没能生成声音",
          _GPU_FREE + "，再试一次；还不行就把 logs 文件夹里的 gptsovits_api.log 发给帮你的人。",
          fill=_fill_engine, wrapper=True),
    _Rule("gsv_env", r"GPT-SoVITS 环境有问题",
          "GPT-SoVITS 整合包有问题",
          "到「🩺 环境检查」页看看检查结果（打开这一页会自动检查），按提示处理；缺少模型的话点「⬇️ 下载缺少的模型」。",
          wrapper=True),
    _Rule("demucs", r"Demucs 执行失败|Demucs 没有输出",
          "去背景音乐时出错了",
          "先把「视频有背景音乐」的勾去掉再试；如果确实需要去背景音乐，" + _GPU_FREE + "后再试。",
          wrapper=True),
    _Rule("ffmpeg", r"ffmpeg 执行失败|FFmpegError",
          "处理视频或音频时出错了{file_s}",
          "这个文件可能损坏、没复制完整，或者格式比较特殊。重新复制一次，或者用剪映重新导出成 MP4 再试。",
          fill=_fill_media, wrapper=True),
]

_RULE_KEYS = frozenset(r.key for r in _RULES)

# 中文提示末尾给开发者看的命令（网页上没用），兜底标题里去掉
_CMD_HINT = re.compile(
    r"[，,。；;（(]?\s*(?:请先?运行|请执行|可以?运行|可运行|请先执行)[:：]?\s*`?(?:voicetwin|pip|python)\b.*$")


# --------------------------------------------------------------------------- 主函数

def _safe_str(obj: Any) -> str:
    try:
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return str(obj)
    except Exception:
        try:
            return repr(obj)
        except Exception:
            return f"<{type(obj).__name__}>"


def _one(err: BaseException) -> Tuple[str, str]:
    """（「类型名: 消息」，额外输出），额外输出来自 subprocess.CalledProcessError 之类的 stdout/stderr。"""
    name = type(err).__name__
    msg = _safe_str(err)
    head = f"{name}: {msg}" if msg else name
    extra: List[str] = []
    for attr in ("stderr", "output"):
        v = getattr(err, attr, None)
        if isinstance(v, (bytes, str)) and v:
            s = _safe_str(v).strip()
            if s and s not in msg and s not in extra:
                extra.append(s[-DETAIL_LIMIT:])
    return head, "\n".join(extra)


def _clip(text: str, limit: int) -> str:
    """太长时保留开头和结尾（报错的真正原因通常在最后几行）。"""
    if len(text) <= limit:
        return text
    head = max(limit // 4, 1)
    tail = max(limit - head - 12, 1)
    return text[:head].rstrip() + "\n……（中间省略）……\n" + text[-tail:].lstrip()


def _build(err: Union[BaseException, str, Any]) -> Tuple[Optional[BaseException], str, str, str]:
    """返回（异常对象或 None, 完整文字, 重点文字, 第一行消息）。"""
    if isinstance(err, BaseException):
        parts: List[str] = []
        focus: List[str] = []
        first = ""
        for i, e in enumerate(_iter_chain(err)):
            head, extra = _one(e)
            if i == 0:
                first = _safe_str(e)
                parts.append(head)
            else:
                parts.append(f"（原因：{head}）")
            if extra:
                parts.append(extra)
            focus.append(head.split("\n", 1)[0])
        full = "\n".join(parts)
        return err, full, "\n".join(focus), first
    text = _safe_str(err) if err is not None else ""
    return None, text, text.strip().split("\n", 1)[0] if text.strip() else "", text


def _render(rule: _Rule, ctx: _Ctx) -> Tuple[str, str]:
    values: Dict[str, str] = _Blank()
    if rule.fill is not None:
        try:
            values.update(rule.fill(ctx))
        except Exception:
            pass
    try:
        title = rule.title.format_map(values)
        advice = rule.advice.format_map(values)
    except Exception:  # 模板出问题也不能让报错翻译本身报错
        title, advice = rule.title, rule.advice
    return title.strip(), advice.strip()


def _match(err: Optional[BaseException], full: str, focus: str) -> Optional[Tuple[_Rule, _Ctx]]:
    # 第一遍：只看「类型名 + 第一行」和日志里真正的报错行（不看普通的警告行），且不用外层包装规则。
    exc_lines = [m.group(0).strip() for m in _EXC_LINE.finditer(full)]
    focus_text = "\n".join([focus] + exc_lines)
    for rule in _RULES:
        if rule.wrapper:
            continue
        ctx = rule.find(err, focus_text)
        if ctx is not None:
            return rule, _Ctx(err, full, _relocate(rule, full, ctx))
    # 第二遍：全文按顺序找。
    for rule in _RULES:
        ctx = rule.find(err, full)
        if ctx is not None:
            return rule, ctx
    return None


def _relocate(rule: _Rule, full: str, ctx: _Ctx) -> "re.Match[str]":
    """第一遍是在重点文字里找到的；尽量换成全文里对应的位置，方便取文件名等信息。"""
    needle = ctx.line
    pos = full.find(needle) if needle else -1
    if pos >= 0:
        m = rule.pattern.search(full, pos, pos + len(needle))
        if m is not None:
            return m
    m = rule.pattern.search(full)
    return m if m is not None else ctx.match


def explain(err: Union[BaseException, str]) -> Friendly:
    """把异常（或一段报错文字）翻译成 Friendly(title, advice, detail, key)。永远不抛异常。"""
    try:
        return _explain(err)
    except Exception:  # pragma: no cover - 兜底，理论上走不到
        detail = _clip(_safe_str(err), DETAIL_LIMIT)
        return Friendly(UNKNOWN_TITLE, UNKNOWN_ADVICE, detail, "unknown")


def _explain(err: Union[BaseException, str]) -> Friendly:
    if isinstance(err, Friendly):
        return err
    exc, full, focus, first = _build(err)
    detail = _clip(full.strip(), DETAIL_LIMIT)
    search = _clip(full, _SEARCH_LIMIT)
    found = _match(exc, search, focus)
    if found is not None:
        rule, ctx = found
        title, advice = _render(rule, ctx)
        return Friendly(title, advice, detail, rule.key)
    lines = [ln.strip() for ln in first.splitlines() if ln.strip()]
    if lines and _CJK.search(first):
        title = _CMD_HINT.sub("", lines[0]).strip() or lines[0]
        return Friendly(title[:200], "", detail, "app")
    return Friendly(UNKNOWN_TITLE, UNKNOWN_ADVICE, detail, "unknown")


def is_fatal(err: Union[BaseException, str, Friendly]) -> bool:
    """这个错误是不是「重试也没用」的那种（显存不够、驱动坏了、硬盘满了、推理服务起不来……）。

    生成时遇到这种错误，不必再给同一句话试别的候选；处理素材时遇到硬盘满了，也不必继续处理后面的文件。
    """
    f = err if isinstance(err, Friendly) else explain(err)
    return f.key in FATAL_KEYS


# --------------------------------------------------------------------------- 输出格式

_MD_SPECIAL = re.compile(r"([\\`*_\[\]<>#|~$])")


def _md_escape(text: str) -> str:
    """转义 Markdown 特殊字符，但不动网址（否则链接会坏）。"""
    out: List[str] = []
    last = 0
    for m in _URL.finditer(text):
        out.append(_MD_SPECIAL.sub(r"\\\1", text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(_MD_SPECIAL.sub(r"\\\1", text[last:]))
    return "".join(out)


def _as_friendly(f: Any) -> Friendly:
    return f if isinstance(f, Friendly) else explain(f)


def friendly_md(f: Friendly, what: str = "", log_path: str = "", report_path: str = "") -> str:
    """生成给网页 gr.Markdown 用的报错说明。

    ### ❌ 训练没有完成：显卡内存（显存）不够
    **怎么办**：……
    详细记录在：`D:/.../voicetwin.log`
    技术细节（给帮你的人看）：```……```

    （不用 <details> 折叠，因为 gradio 4.24 的 Markdown 过滤规则没有验证过。）
    """
    f = _as_friendly(f)
    what = (what or "").strip()
    title = _md_escape(f.title or UNKNOWN_TITLE)
    advice = _md_escape(f.advice) if f.advice else ""
    if f.key == "stopped":
        md = f"### ⏹ {_md_escape(what)}已停止" if what else "### ⏹ 已停止"
        if advice:
            md += f"\n\n{advice}"
        return md
    md = f"### ❌ {_md_escape(what)}没有完成：{title}" if what else f"### ❌ {title}"
    if advice:
        md += f"\n\n**怎么办**：{advice}"
    if report_path:
        md += ("\n\n📋 已自动生成问题报告（也显示在下面的「详细过程」里），需要帮忙时把这个文件发给帮你的人：`"
               + str(report_path).replace("`", "'") + "`")
    if log_path:
        md += "\n\n详细记录在：`" + str(log_path).replace("`", "'") + "`"
    detail = (f.detail or "").strip()
    if detail:
        detail = _clip(detail, MD_DETAIL_LIMIT).replace("```", "'''")
        md += "\n\n技术细节（给帮你的人看）：\n\n```text\n" + detail + "\n```"
    return md


def friendly_line(f: Union[Friendly, BaseException, str], what: str = "") -> str:
    """一行纯文字（写进日志框、命令行用），例如「❌ 训练没有完成：显卡内存（显存）不够。怎么办：……」。"""
    f = _as_friendly(f)
    what = (what or "").strip()
    if f.key == "stopped":
        return f"⏹ {what}已停止" if what else "⏹ 已停止"
    head = f"❌ {what}没有完成：{f.title}" if what else f"❌ 出错了：{f.title}"
    return head + (f"。怎么办：{f.advice}" if f.advice else "")
