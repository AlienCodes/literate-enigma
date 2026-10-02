"""出错时自动生成的「问题报告」（voicetwin/report.py）和整理记录的小工具（voicetwin/utils/logtail.py）。"""

import logging
import time
from pathlib import Path

import pytest

from voicetwin import report
from voicetwin.utils import logtail
from voicetwin.utils.log import get_logger, setup_logging
from voicetwin.utils.progress import clear_cancel
from voicetwin.webui import tasks

TRACEBACK = """INFO:     127.0.0.1:{port} - "GET /tts HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "D:\\GPT-SoVITS\\runtime\\lib\\site-packages\\uvicorn\\protocols\\http\\h11_impl.py", line 407, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
  File "D:\\GPT-SoVITS\\runtime\\lib\\site-packages\\starlette\\routing.py", line 74, in app
    response = await f(request)
  File "D:\\GPT-SoVITS\\runtime\\lib\\site-packages\\fastapi\\routing.py", line 191, in run_endpoint_function
    return await dependant.call(**values)
  File "D:\\GPT-SoVITS\\runtime\\lib\\site-packages\\fastapi\\routing.py", line 278, in app
    raw_response = await run_endpoint_function(
  File "D:\\GPT-SoVITS\\api_v2.py", line 484, in tts_get_endpoint
    "text_lang": text_lang.lower(),
AttributeError: 'NoneType' object has no attribute 'lower'
"""


def teacher_like_log(repeats=300, runs=2) -> str:
    """和 v18.2 时老师的 gptsovits_api.log 一样的样子（自己造的，不是老师的文件）。"""
    out = ""
    for r in range(runs):
        out += (f"{logtail.RUN_MARKER} 18.2 启动推理服务 2026-10-02 15:4{r}:24（端口 9880，模型 s8-g15）=====\n"
                "-" * 45 + "TTS Config" + "-" * 45 + "\nversion             : v2ProPlus\n" + "-" * 100 + "\n\n"
                "Loading Text2Semantic weights from D:\\GPT-SoVITS\\GPT_weights_v2ProPlus\\vt-e15.ckpt\n"
                "Loading VITS weights from D:\\x.pth. _IncompatibleKeys(missing_keys=[" + "'enc_q.x', " * 400 + "])\n"
                f"INFO:     Started server process [{29260 + r}]\nINFO:     Waiting for application startup.\n"
                "INFO:     Application startup complete.\n"
                "INFO:     Uvicorn running on http://127.0.0.1:9880 (Press CTRL+C to quit)\n")
        for i in range(repeats):
            out += TRACEBACK.format(port=50000 + i)
    return out


# ---------------------------------------------------------------------------- logtail
def test_condense_collapses_repeats_and_long_lines():
    text = logtail.last_run(teacher_like_log())
    assert text.startswith(logtail.RUN_MARKER) and "[29261]" in text and "[29260]" not in text
    c = logtail.condense(text, max_lines=60)
    assert c.count("AttributeError: 'NoneType' object has no attribute 'lower'") == 1
    assert "又重复了 299 次" in c
    assert "这一行太长" in c and len(max(c.splitlines(), key=len)) < 400
    assert "层 Python 库内部的调用，省略" in c and 'api_v2.py", line 484' in c
    assert "Uvicorn running on" in c


def test_condense_keeps_head_and_tail_when_long():
    text = "\n".join(f"第 {i} 行" for i in range(500))
    c = logtail.condense(text, max_lines=40, head=10).splitlines()
    assert len(c) == 40 and c[0] == "第 0 行" and c[-1] == "第 499 行" and "中间省略" in c[10]


def test_diagnose_teacher_case():
    notes = logtail.diagnose_gsv_api(logtail.last_run(teacher_like_log()))
    assert notes[0].startswith("引擎记录显示：合成引擎已经加载完模型并打开了（http://127.0.0.1:9880）")
    assert "回答了 300 次「内部错误」（HTTP 500）" in notes[1]
    assert any("AttributeError" in n and "共 300 次" in n for n in notes)


def test_diagnose_stuck_while_loading_and_oom():
    notes = logtail.diagnose_gsv_api("TTS Config\nLoading Text2Semantic weights from a\nLoading BERT weights from b\n")
    assert notes == ["引擎记录显示：合成引擎还没有打开，最后在做的是「Loading BERT weights」（加载模型）。"]
    notes = logtail.diagnose_gsv_api("Traceback (most recent call last):\n  File \"x\", line 1\n"
                                     "torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2 GiB\n")
    assert any("显存" in n for n in notes)


def test_read_text_tail_of_big_file(tmp_path):
    p = tmp_path / "big.log"
    p.write_text("旧" * 100 + "\n" + "x" * 1000 + "\n最后一行\n", encoding="utf-8")
    assert logtail.read_text(p, max_bytes=50).endswith("最后一行\n")
    assert logtail.read_text(tmp_path / "没有.log") == ""


# ---------------------------------------------------------------------------- report
def test_report_failure_writes_file_and_short_text(tmp_path, caplog):
    logs = tmp_path / "我的声音" / "logs"
    logs.mkdir(parents=True)
    (logs / "gptsovits_api.log").write_text(teacher_like_log(), encoding="utf-8")
    (logs / "voicetwin.log").write_text("不应该重复出现在报告里\n", encoding="utf-8")
    exc = RuntimeError("GPT-SoVITS 推理服务启动超时（等了 600 秒）。引擎的完整记录在 D:\\x\\gptsovits_api.log")
    with caplog.at_level(logging.INFO, logger="voicetwin"):
        path = report.report_failure(exc, what="重新挑选最佳模型", voice="我的声音", where="停在第 2 步「启动合成引擎」",
                                     elapsed="10 分 27 秒", logs_dir=logs, task_lines=["15:43:24 | 启动合成引擎……"],
                                     since=time.time() - 60)
    assert path is not None and path.parent == logs and path.name.startswith("问题报告_")
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # 记事本按 UTF-8 打开
    full = raw.decode("utf-8-sig")
    for part in ("声音分身 VoiceTwin 问题报告", "做的事：重新挑选最佳模型（声音：我的声音）", "停在哪里：停在第 2 步「启动合成引擎」",
                 "原因：GPT-SoVITS 没能启动", "怎么办：", "【自动诊断出的线索】", "回答了 300 次「内部错误」",
                 "【技术细节】", "RuntimeError: GPT-SoVITS 推理服务启动超时", "【这次任务的运行记录（最后 1 行）】",
                 "【合成引擎的记录 gptsovits_api.log", "又重复了 299 次", "【电脑情况】", "系统：", "Python："):
        assert part in full, part
    assert "不应该重复出现在报告里" not in full
    short = "\n".join(r.getMessage() for r in caplog.records if r.getMessage().startswith("📋 问题报告"))
    assert "原因：GPT-SoVITS 没能启动" in short and "自动诊断出的线索：" in short and str(path) in short
    assert "【技术细节】" not in short  # 网页上只放简短的


def test_report_failure_without_logs_dir_still_logs(caplog):
    with caplog.at_level(logging.INFO, logger="voicetwin"):
        assert report.report_failure(ValueError("boom"), what="生成讲课音频") is None
    assert any(r.getMessage().startswith("📋 问题报告") for r in caplog.records)


def test_report_never_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "_technical", lambda exc: (_ for _ in ()).throw(RuntimeError("坏了")))
    monkeypatch.setattr(report, "_computer", lambda d: 1 / 0)
    path = report.report_failure(RuntimeError("x"), what="测试", logs_dir=tmp_path)
    assert path is not None and "原因：" in path.read_text(encoding="utf-8-sig")


def test_old_reports_are_cleaned(tmp_path, monkeypatch):
    monkeypatch.setattr(report, "KEEP_REPORTS", 3)
    for i in range(5):
        (tmp_path / f"问题报告_2020010{i}_000000.txt").write_text("旧", encoding="utf-8")
    report.report_failure(RuntimeError("x"), logs_dir=tmp_path)
    assert len(list(tmp_path.glob("问题报告_*.txt"))) == 3


# ---------------------------------------------------------------------------- 网页任务出错时
@pytest.fixture
def fresh_tasks(monkeypatch):
    monkeypatch.setattr(tasks, "POLL_SECONDS", 0.02)
    with tasks._LOCK:
        tasks._CURRENT = None
    clear_cancel()
    yield
    cur = tasks._CURRENT
    if cur is not None and cur.thread is not None:
        cur.thread.join(5)
    with tasks._LOCK:
        tasks._CURRENT = None
    clear_cancel()


def test_task_failure_puts_report_in_details_and_file(tmp_path, fresh_tasks):
    logs = tmp_path / "ws" / "报告声音" / "logs"
    setup_logging(log_file=logs / "voicetwin.log")
    lg = get_logger("test_report")

    def job(progress=None):
        progress(0.05, "启动合成引擎")
        lg.info("启动 GPT-SoVITS 推理服务（端口 9880）……")
        raise RuntimeError("GPT-SoVITS 推理服务启动超时（等了 600 秒，合成引擎一直没有加载完模型（端口没有打开））。")

    out = list(tasks.stream_task("select", "重新挑选最佳模型", "报告声音", job))
    text, state = out[-1]
    assert "📋 问题报告（出错时自动生成）" in text
    assert "原因：GPT-SoVITS 没能启动" in text and "做的事：重新挑选最佳模型（声音：报告声音）" in text
    assert "Traceback" not in text
    rep = Path(state["report"])
    assert rep.exists() and rep.parent == logs
    body = rep.read_text(encoding="utf-8-sig")
    assert "启动 GPT-SoVITS 推理服务（端口 9880）" in body and "RuntimeError" in body

    from voicetwin.errors import friendly_md

    md = friendly_md(state["friendly"], what="重新挑选最佳模型", report_path=state["report"])
    assert "📋 已自动生成问题报告" in md and str(rep) in md
