p = '<仓库>/.claude/worktrees/wf_08725f86-d54-4/voicetwin/errors.py'
s = open(p, encoding='utf-8').read()
old_new = [
    ('from typing import Any, Callable, Dict, Iterator, List, Optional, Pattern, Tuple, Union',
     'from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union'),
    ('''        self.pattern: Pattern[str] = re.compile(pattern, re.I)''',
     '''        self.pattern: re.Pattern[str] = re.compile(pattern, re.I)'''),
    ('''        self.exclude: Optional[Pattern[str]] = re.compile(exclude, re.I) if exclude else None''',
     '''        self.exclude: Optional[re.Pattern[str]] = re.compile(exclude, re.I) if exclude else None'''),
    ('''_DRIVE = re.compile(r"(?<![A-Za-z])([A-Za-z]):[\\\\/]")
_LOCAL = re.compile(r"127\\.0\\.0\\.1|localhost", re.I)
''', '''_DRIVE = re.compile(r"(?<![A-Za-z])([A-Za-z]):[\\\\/]")
'''),
    ('''#: 这些问题重试也没用（同一个原因会一直失败），调用方可以立刻停下，不必再试别的候选或别的文件。
FATAL_KEYS = frozenset({
    "stopped", "gpu_oom", "pagefile", "ram", "disk", "torch_cpu", "gpu_arch", "driver",
    "gsv_missing", "models_missing", "api_start", "module", "import_version", "dll",
})''', '''#: 这些问题和输入无关，换一个候选、换一个文件再试也会一样失败，调用方可以立刻停下。
#: （电脑内存不够 'ram' 不算：可能只是某个视频太长，换个文件也许就行。）
FATAL_KEYS = frozenset({
    "stopped", "gpu_oom", "disk", "torch_cpu", "gpu_arch", "driver", "gsv_missing", "models_missing",
    "api_start", "module", "import_version", "dll", "speaker_model", "ffmpeg_missing",
})'''),
    ('''          r"couldn't communicate with the NVIDIA driver|no NVIDIA driver|NVIDIA driver on your system|"''',
     '''          r"couldn't communicate with the NVIDIA driver|no NVIDIA driver|NVIDIA driver on your system|"
          r"显卡驱动没有正常工作|显卡没有正常工作|显卡驱动未安装|"'''),
    ('''          r"通常每个套接字地址|Cannot find empty port|port \\d+ is (?:already )?in use|error while attempting to bind",''',
     '''          r"通常每个套接字地址|Cannot find empty port|port \\d+ is (?:already )?in use|error while attempting to bind|"
          r"WinError 10013\\b|访问权限不允许的方式做了一个访问套接字",'''),
    ('''          "GPT-SoVITS 推理服务意外断开了",''', '''          "GPT-SoVITS 意外停止了（连不上它）",'''),
    ('''          r"ConnectTimeout|ReadTimeout|timed out|WinError 10060|连接尝试失败|TimeoutError|IncompleteRead|"''',
     '''          r"ConnectTimeout|ReadTimeout|timed out|WinError 10060|连接尝试失败|IncompleteRead|"'''),
    ('''          r"huggingface\\.co|hf-mirror\\.com|LocalEntryNotFoundError|OfflineModeIsEnabled|HfHubHTTPError|"
          r"snapshot_download|huggingface_hub",''',
     '''          r"huggingface\\.co|hf-mirror\\.com|LocalEntryNotFoundError|OfflineModeIsEnabled|HfHubHTTPError|"
          r"outgoing traffic has been disabled|appropriate snapshot folder",'''),
    ('''    _Rule("net_modelscope", r"modelscope",''',
     '''    _Rule("net_modelscope",
          r"modelscope\\.cn|modelscope\\.hub\\.errors|modelscope[^\\n]{0,200}(?:download|下载|connect|HTTP)",'''),
]
for o, n in old_new:
    assert o in s, o
    s = s.replace(o, n)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
