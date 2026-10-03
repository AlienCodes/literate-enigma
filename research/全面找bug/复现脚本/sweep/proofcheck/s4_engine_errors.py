"""识别引擎装了但用不了（下载失败、缺模块、显存不够、DLL 坏了）：给老师的说明是不是中文、会不会让任务失败。"""
from common import *
errs = [
    ModuleNotFoundError("No module named 'funasr.models.paraformer'"),
    ConnectionError("HTTPSConnectionPool(host='www.modelscope.cn', port=443): Max retries exceeded with url: /api/v1/models/iic/speech_paraformer"),
    RuntimeError("CUDA out of memory. Tried to allocate 20.00 MiB (GPU 0; 4.00 GiB total capacity)"),
    OSError("[WinError 126] 找不到指定的模块。 Error loading \"C:\\GPT-SoVITS\\runtime\\lib\\site-packages\\torch\\lib\\caffe2_nvrtc.dll\""),
    ValueError("Unrecognized model in iic/speech_paraformer. Should have a `model_type` key in its config.json"),
    KeyError("model"),
    AssertionError(),
    FileNotFoundError(2, "No such file or directory", "C:\\Users\\x\\.cache\\modelscope\\hub\\iic\\model.pt"),
    PermissionError(13, "Permission denied", "C:\\Users\\x\\.cache\\modelscope\\hub\\._____temp"),
]
for exc in errs:
    cfg, project = voice(["我们今天讲十个函数", "下面我们来看第二个例子"])
    fake_engine({}, installed=("funasr", "modelscope", "torch", "faster_whisper"), load_error=exc)
    res = pc.find_suspects(project, cfg)
    print(f"{type(exc).__name__:22s} -> engine={res['engine']!r} checked={res['checked']} note={res['note']}")
# recognize() 一直出错（每段都出错）
cfg, project = voice(["我们今天讲十个函数", "下面我们来看第二个例子", "第三句", "第四句"])
fake_engine({}, fail={"*"})
res = pc.find_suspects(project, cfg)
print("all-fail:", res["engine"], res["errors"], res["note"])
