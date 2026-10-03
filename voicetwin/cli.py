"""命令行入口：voicetwin <命令> …  （运行 voicetwin -h 查看全部命令）"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from voicetwin import __version__
from voicetwin.config import load_config, update_config_file, write_example_config

EPILOG = """
常用流程（把「我的声音」换成你喜欢的名字）：
  1. voicetwin doctor                                   检查环境
  2. voicetwin prepare -v 我的声音 -i D:/讲课视频        从视频/录音准备素材（自动识别文字）
  3. （可选）用 Excel 打开 workspace/我的声音/transcripts.csv 校对文字，然后 voicetwin review -v 我的声音
  4. voicetwin confirm -v 我的声音                       确认训练素材（训练前必须做；改过素材要再确认一次）
  5. voicetwin train -v 我的声音                         训练（GPT-SoVITS），完成后自动挑选最像的模型
  6. voicetwin narrate -v 我的声音 第1课讲稿.md          生成讲课音频 + 字幕
  或者一条命令全自动：voicetwin auto -v 我的声音 -i D:/讲课视频
  网页界面：voicetwin webui
"""


REDO_HELP = "请这样填：3,5,8-10（意思是第 3、5 句和第 8 到 10 句）"
REDO_MAX = 100000
_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")
_REDO_SEPARATORS = "、，,；;。和与及/／\u3000\t\r\n "
_REDO_DASHES = "到至~～〜—–－‐−-"


def _parse_redo(value: str) -> List[int]:
    """把「只重新生成第几句」的写法变成句子编号列表（从 1 开始，和结果表里的 # 一样）。

    支持 3,5,8-10 以及 3、5、第3句、8到10、8~10、10-8 这类写法；看不懂时抛出带说明的 ValueError。
    """
    original = str(value or "").strip()
    text = original.translate(_FULLWIDTH_DIGITS)
    for ch in "第句":
        text = text.replace(ch, "")
    for ch in _REDO_DASHES:
        text = text.replace(ch, "-")
    text = re.sub(r"\s*-\s*", "-", text)  # 「8 到 10」「8 - 10」
    for ch in _REDO_SEPARATORS:
        text = text.replace(ch, ",")
    out = set()
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not m:
            raise ValueError(f"看不懂「{original}」。{REDO_HELP}")
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) is not None else a
        if a > b:
            a, b = b, a
        if a < 1:
            raise ValueError(f"看不懂「{original}」：句子编号从 1 开始。{REDO_HELP}")
        if b > REDO_MAX:
            raise ValueError(f"「{original}」里的数字太大了，讲稿没有这么多句。{REDO_HELP}")
        out.update(range(a, b + 1))
    return sorted(out)


#: 和 synth/engine.py 的 QUALITY_ORDER 一样（测试会核对）。这里不 import 引擎：voicetwin -h、init-config 要很快
QUALITY_CHOICES = ["fast", "balanced", "best", "max", "perfect", "identical"]
QUALITY_HELP = ("质量档位：fast 快速 | balanced 均衡 | best 最好 | max 极致 | perfect 完美 | identical 一模一样（默认）"
                "（越往后越慢，但每句更稳、更像你；也可以写中文名，例如 -q 一模一样。"
                "不写就看 config.yaml 的 synth.quality，那里写 auto 或没写就是一模一样）")


def _quality_arg(value: str) -> str:
    """-q 的值：英文名、中文名（一模一样）、auto 都认；认不出时用中文说明可以写什么。"""
    from voicetwin.synth.engine import match_quality

    key = match_quality(value)
    if key is None:
        raise argparse.ArgumentTypeError(f"不认识的质量档位「{value}」。可选：{'/'.join(QUALITY_CHOICES)}（一模一样），"
                                         "也可以写中文名，例如 -q 一模一样")
    return key


def _config_quality_notes(cfg: Any) -> List[str]:
    """命令行没写 -q 时，config.yaml 里的 synth.quality 要不要提醒一句（只写真的会发生的事）。"""
    from voicetwin.synth.engine import AUTO_QUALITY, QUALITY_SHORT, match_quality

    if cfg.get("_legacy_quality"):
        return [f"设置文件 config.yaml 里的「quality: {cfg['_legacy_quality']}」是旧版本（v0.1.0～v0.1.3）自动写进去的默认值，"
                "不是你自己改的，所以这次按默认的「一模一样」生成。想一直用别的档位：把那一行改成那个档位，"
                "并删掉后面 # 开头的旧说明；或者在命令后面加 -q（例如 -q balanced）"]
    raw = cfg.get_path("synth.quality", "auto")
    text = str(raw if raw is not None else "").strip()
    key = match_quality(raw)
    if text.lower() in AUTO_QUALITY or key is None:  # 认不出的写法：引擎会说明并用「一模一样」
        return []
    name = text if text == QUALITY_SHORT.get(key) else f"{text}（{QUALITY_SHORT.get(key, key)}）"
    return [f"设置文件 config.yaml 里写了质量「{name}」，这次按它生成；想用默认的「一模一样」，"
            "把那一行改成 quality: auto，或者加 -q identical"]
# 这些命令不会长时间运行，不需要关闭黑色窗口的「快速编辑」
NO_QUICK_EDIT_COMMANDS = ("init-config", "doctor")


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="voicetwin", description=f"VoiceTwin 声音分身 v{__version__}：复刻你的音色、语气和节奏（中文+英文）",
                                 epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-c", "--config", help="配置文件路径（默认使用当前目录的 config.yaml）")
    ap.add_argument("--verbose", action="store_true", help="输出更详细的日志")
    # --verbose 放在子命令前后都可以（例如 voicetwin narrate ... --verbose）
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS, help="输出更详细的日志和完整错误信息")
    sub = ap.add_subparsers(dest="command", metavar="<命令>")
    _add = sub.add_parser
    sub.add_parser = lambda *a, **kw: _add(*a, parents=[common], **kw)  # type: ignore[method-assign]

    def voice_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("-v", "--voice", required=True, help="声音名称，例如：我的声音")

    def backend_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("-b", "--backend", choices=["gptsovits", "qwen3tts", "indextts", "dummy"],
                       help="合成引擎（默认看 config.yaml 的 backend）")

    p = sub.add_parser("init-config", help="在当前目录生成可编辑的 config.yaml")
    p.add_argument("--gptsovits-root", help="GPT-SoVITS（或整合包）所在目录")
    p.add_argument("--workspace", help="数据存放目录（默认 ./workspace）")
    p.add_argument("--backend", choices=["gptsovits", "qwen3tts", "indextts"], help="默认引擎")
    p.add_argument("--force", action="store_true", help="重新生成 config.yaml（旧文件备份为 config.yaml.bak）")
    sub.add_parser("doctor", help="检查运行环境、显卡和各引擎是否就绪")
    sub.add_parser("list", help="列出已有的声音")

    p = sub.add_parser("prepare", help="从视频/录音准备训练素材（提取、清理、切片、识别、过滤）")
    voice_arg(p)
    p.add_argument("-i", "--input", nargs="+", required=True, help="视频/音频文件或文件夹（可多个）")
    p.add_argument("--asr", choices=["faster-whisper", "funasr", "none"], help="识别引擎")
    p.add_argument("--asr-model", help="识别模型，如 large-v3 / paraformer-zh")
    p.add_argument("--language", choices=["auto", "zh", "en"], help="素材语言（默认逐段自动判断）")
    p.add_argument("--denoise", choices=["auto", "on", "off"], help="降噪")
    p.add_argument("--separate-vocals", action="store_true", help="去除背景音乐（需要 demucs）")
    p.add_argument("--segmentation", choices=["auto", "srt", "energy"], help="切分方式")

    p = sub.add_parser("review", help="读回 transcripts.csv 里的人工校对结果")
    voice_arg(p)

    p = sub.add_parser("confirm", help="确认训练素材（和网页上的「✅ 确认训练素材」一样；训练前必须做）")
    voice_arg(p)

    p = sub.add_parser("analyze", help="重新分析说话风格（语速、停顿、音高、响度）")
    voice_arg(p)

    p = sub.add_parser("train", help="用你的素材微调模型，完成后自动挑选最佳模型并校准语速")
    voice_arg(p)
    backend_arg(p)
    p.add_argument("--sovits-epochs", type=int, help="GPT-SoVITS：SoVITS 训练轮数（默认自动）")
    p.add_argument("--gpt-epochs", type=int, help="GPT-SoVITS：GPT 训练轮数（默认自动）")
    p.add_argument("--batch-size", type=int, help="批大小（默认按显存自动）")
    p.add_argument("--epochs", type=int, help="Qwen3-TTS：微调轮数")
    p.add_argument("--dpo", choices=["auto", "on", "off"], default="auto",
                   help="GPT-SoVITS 的 DPO（实验功能）：auto = 不开（默认；没有可靠证据说明它能让声音更像），on = 手动打开")
    p.add_argument("--no-select", action="store_true", help="训练后不自动挑选模型")

    p = sub.add_parser("select", help="用验证集自动挑选最像你的模型，并校准语速")
    voice_arg(p)
    backend_arg(p)
    p.add_argument("--items", type=int, default=None, help="用多少条验证句（默认自动）")
    p.add_argument("--asr", dest="asr", action="store_true", default=None, help="同时用识别模型检查错字")
    p.add_argument("--no-asr", dest="asr", action="store_false")

    for name, helptext in (("say", "合成一句话/一段话"), ("narrate", "把讲稿（txt/md/srt/docx）合成为完整讲课音频")):
        p = sub.add_parser(name, help=helptext)
        voice_arg(p)
        backend_arg(p)
        p.add_argument("text" if name == "say" else "script", help="要说的文字" if name == "say" else "讲稿文件路径")
        p.add_argument("-o", "--output", help="输出文件（.wav 或 .mp3），默认保存到 workspace/声音名/outputs/")
        p.add_argument("-q", "--quality", type=_quality_arg, metavar="档位", help=QUALITY_HELP)
        p.add_argument("-n", "--candidates", type=int,
                       help="每句生成几个候选（覆盖质量档位；「一模一样」档是每句最多试几个）")
        speed_group = p.add_mutually_exclusive_group()
        speed_group.add_argument("--speed", type=float, help="语速倍数（默认 1.0 = 和你本人一样；1.2 = 快 20%%）")
        speed_group.add_argument("--faster", type=float, metavar="百分比", help="比你原声快多少（例如 --faster 20 = 快 20%%）")
        speed_group.add_argument("--slower", type=float, metavar="百分比", help="比你原声慢多少（例如 --slower 15 = 慢 15%%）")
        p.add_argument("--ref", default="", help="指定参考音频 id（见 references.json）")
        p.add_argument("--asr-check", dest="asr_check", action="store_true", default=None, help="用识别模型检查漏字")
        if name == "narrate":
            p.add_argument("--redo", default="", help="只重新生成这几句（编号和结果报告里的 # 一样，从 1 开始），"
                                                       "如 3,5,8-10 或 3、5、8到10")
            p.add_argument("--no-srt", action="store_true", help="不输出字幕")

    p = sub.add_parser("evaluate", help="评估一段音频有多像你")
    voice_arg(p)
    p.add_argument("audio", help="音频文件")
    p.add_argument("--text", default="", help="音频对应的文字（提供后会检查错字）")

    p = sub.add_parser("auto", help="全自动：准备素材 → 训练 → 挑最佳模型 → 生成试听")
    voice_arg(p)
    backend_arg(p)
    p.add_argument("-i", "--input", nargs="+", required=True, help="视频/音频文件或文件夹")
    p.add_argument("--skip-train", action="store_true", help="不训练，只用零样本克隆")

    p = sub.add_parser("mux", help="把生成的讲解音频放进视频（替换原音轨）")
    p.add_argument("--video", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--keep-original", action="store_true", help="保留原音轨并混音")

    p = sub.add_parser("download-models", help="下载缺少的模型（GPT-SoVITS 预训练模型 + 精准声纹打分模型）")
    p.add_argument("--source", choices=["auto", "hf", "hf-mirror"], default="auto", help="下载源（国内推荐 hf-mirror）")
    p.add_argument("--check", action="store_true", help="只检查缺哪些 GPT-SoVITS 模型、不下载（缺模型时退出码为 3）")
    p.add_argument("--sv", action="store_true", help="只下载精准声纹打分的模型（约 170 MB；加 --check 只检查）")

    p = sub.add_parser("clear-cache", help="清空某个声音的句子缓存")
    voice_arg(p)

    p = sub.add_parser("webui", help="启动网页界面")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--share", action="store_true", help="生成公网分享链接（注意隐私）")
    return ap


def _safe_console() -> None:
    """输出被重定向到 GBK 编码的文件/管道时，遇到 ✅ 这类字符不要报错退出，用 ? 代替。
    老式黑色窗口的字体没有中文字时（中文会显示成 ?），换成有中文字的字体。"""
    try:
        from voicetwin.utils.winsys import use_chinese_console_font

        use_chinese_console_font()
    except Exception:
        pass
    for stream in (sys.stdout, sys.stderr):
        try:
            enc = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
            if enc not in ("utf8", "utf8sig") and hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def _disable_quick_edit() -> None:
    try:
        from voicetwin.utils.winsys import disable_quick_edit

        disable_quick_edit()
    except Exception:
        pass


def _fmt_secs(sec: float) -> str:
    sec = int(max(0, sec))
    if sec < 60:
        return f"{sec} 秒"
    if sec < 3600:
        return f"{sec // 60} 分 {sec % 60} 秒"
    return f"{sec // 3600} 小时 {sec % 3600 // 60} 分"


class _ConsoleProgress:
    """没有 ProgressTracker 时的简单命令行进度：每 5% 或每 30 秒打印一整行（不用 \\r）。"""

    def __init__(self, title: str, print_fn: Callable[[str], None], min_interval: float = 30.0, pct_step: int = 5,
                 clock: Callable[[], float] = time.time):
        self.title = title
        self.print_fn = print_fn
        self.min_interval = float(min_interval)
        self.pct_step = max(1, int(pct_step))
        self.clock = clock
        self.t0 = clock()
        self.frac = 0.0
        self.last_pct = -1
        self.last_t = self.t0
        self._lock = threading.Lock()

    def __call__(self, frac: float, msg: str = "") -> None:
        try:
            f = max(0.0, min(1.0, float(frac)))
        except Exception:
            return
        line = ""
        with self._lock:
            self.frac = max(self.frac, f)  # 只往前走
            pct = int(self.frac * 100)
            now = self.clock()
            if pct // self.pct_step > self.last_pct // self.pct_step or now - self.last_t >= self.min_interval:
                self.last_pct, self.last_t = pct, now
                text = " ".join(str(msg or "").split())
                head = f"⏳ {pct}%｜{text[:80]}" if text else f"⏳ {pct}%"
                line = f"{head}｜已用 {_fmt_secs(now - self.t0)}"
        if line:
            try:
                self.print_fn(line)
            except Exception:
                pass

    def finish(self, ok: bool = True, msg: str = "", stopped: bool = False) -> None:
        if ok:
            try:
                self.print_fn(f"✅ {self.title}完成，用时 {_fmt_secs(self.clock() - self.t0)}")
            except Exception:
                pass


def _cli_progress(kind: str, cfg: Any, title: str, backend: Optional[str] = None, select: bool = True,
                  **stage_kw: Any) -> Any:
    """给命令行的长任务做一个进度回调：返回的对象可以当 progress(frac, msg) 用，并有 finish(ok)。

    stage_kw 传给 wf.task_stages：生成时 quality=（「完美」档多一步），素材准备时 overrides=（会不会查错字）。"""
    from voicetwin import workflows as wf
    from voicetwin.utils.log import get_logger

    log = get_logger("cli")

    def emit(line: str) -> None:
        log.info(line)

    stages = None
    task_stages = getattr(wf, "task_stages", None)
    if task_stages is not None and kind:
        try:
            stages = task_stages(kind, cfg, backend, select=select, **stage_kw)
        except TypeError:  # 老版本的 task_stages 不认识这些参数
            try:
                stages = task_stages(kind, cfg, backend)
            except Exception:
                stages = None
        except Exception:
            stages = None
    try:
        from voicetwin.utils.progress import ProgressTracker, console_reporter  # type: ignore
    except ImportError:
        return _ConsoleProgress(title, emit)
    try:
        return ProgressTracker(stages, title=title, on_update=console_reporter(emit))
    except Exception:
        return _ConsoleProgress(title, emit)


def _finish(progress: Any) -> None:
    try:
        progress.finish(True)
    except Exception:
        pass


def _doctor_summary(rows: List[Dict[str, Any]]) -> str:
    def optional(r: Dict[str, Any]) -> bool:
        return bool(r.get("optional"))

    bad = sum(1 for r in rows if r.get("status") == "❌" and not optional(r))
    warn = sum(1 for r in rows if r.get("status") == "⚠️" and not optional(r))
    ok = sum(1 for r in rows if r.get("status") == "✅")
    opt_missing = sum(1 for r in rows if optional(r) and r.get("status") != "✅")
    parts = []
    if bad:
        parts.append(f"❌ {bad} 项需要处理")
    if warn:
        parts.append(f"⚠️ {warn} 项需要注意")
    parts.append(f"✅ {ok} 项正常" if (bad or warn) else f"✅ {ok} 项全部正常")
    text = f"环境检查结果（共 {len(rows)} 项）：" + "，".join(parts)
    if opt_missing:
        text += f"（另有 {opt_missing} 个可选组件没装，不影响使用）"
    return text


def _doctor_rows(wf: Any, cfg: Any) -> List[Dict[str, Any]]:
    rows = list(wf.doctor(cfg))
    sorter = getattr(wf, "sort_doctor_rows", None)
    if sorter is not None:
        try:
            return list(sorter(rows))
        except Exception:
            pass
    # 还没有 sort_doctor_rows 时：问题排前面，可选组件放最后
    order = {"❌": 0, "⚠️": 1, "✅": 2}
    return sorted(rows, key=lambda r: (1 if r.get("optional") else 0, order.get(str(r.get("status")), 1)))


def _print_doctor(rows: List[Dict[str, Any]]) -> int:
    """打印环境检查结果（先给结论、问题排前面），返回退出码：有 ❌ 时为 2，否则 0。"""
    print(_doctor_summary(rows))
    for i, row in enumerate(rows, 1):
        tag = " · 可选，不用管" if row.get("optional") and row.get("status") != "✅" else ""
        print(f"{i:>2}. {row.get('status')} {row.get('item')}：{row.get('detail')}{tag}")
    if any(r.get("status") == "❌" and not r.get("optional") for r in rows):
        print("\n请先处理上面标着 ❌ 的行（每行后面写了原因和办法），处理完再检查一次。")
        return 2
    return 0


def _print_voices(wf: Any, cfg: Any) -> None:
    library = getattr(wf, "voice_library", None)
    voices: List[Dict[str, Any]] = []
    if library is not None:
        try:
            voices = list(library(cfg))
        except Exception:
            voices = []
    if not voices:
        voices = list(wf.list_voices(cfg))
    if not voices:
        print("还没有任何声音。先运行：voicetwin prepare -v 我的声音 -i 你的视频文件夹")
        return
    print(f"共 {len(voices)} 个声音：")
    for i, v in enumerate(voices, 1):
        name = v.get("voice") or v.get("name") or "?"
        minutes = v.get("minutes") or 0
        clips = v.get("clips_kept", v.get("clips")) or 0
        trained = v.get("trained")
        status = v.get("status")
        if not status:
            if isinstance(trained, (list, tuple)):
                status = f"已训练：{'、'.join(map(str, trained))}" if trained else "还没训练"
            else:
                status = "已训练" if trained else "还没训练"
        best = v.get("best_model")
        print(f"{i:>2}. {name}：素材 {minutes} 分钟 / {clips} 条；{status}" + (f"；最佳模型：{best}" if best else ""))


def _download_sv_models(cfg: Any, check: bool) -> int:
    """精准声纹打分的模型（"像你本人"百分比）。返回退出码：0 = 齐全/下载完成，3 = 只检查且有缺失，4 = 下载失败。"""
    from voicetwin.eval import sv_models

    need = sv_models.missing(cfg)
    if not need:
        print("✅ 精准声纹打分的模型已齐全")
        return 0
    if check:
        print(f"缺少 {len(need)} 个精准声纹打分的模型：")
        for i, m in enumerate(need, 1):
            print(f"{i:>2}. {m.label}（{m.file}）")
        print("可以运行 voicetwin download-models --sv 自动下载。")
        return 3
    from voicetwin.workflows import keep_awake

    progress = _cli_progress("download", cfg, "下载声纹模型")
    try:
        with keep_awake():
            files = sv_models.download(cfg, progress=progress)
    except Exception as exc:
        print(f"⚠️ 声纹模型没有下载成功：{exc}")
        print("不影响使用（先用旧的打分方式，准确度低一些）；以后可以在网页上点「⬇️ 下载缺少的模型」再试。")
        return 4
    _finish(progress)
    print(f"✅ 已下载 {len(files)} 个声纹模型（在 {sv_models.model_dir(cfg)}）")
    return 0


def _download_models(cfg: Any, source: str, check: bool) -> int:
    """下载（或只检查）GPT-SoVITS 预训练模型。返回退出码：0 = 齐全/下载完成，3 = 只检查且有缺失。"""
    import shutil

    from voicetwin.backends.gptsovits import GPTSoVITSBackend
    from voicetwin.project import Project

    project = Project(cfg, "__download__")
    try:
        backend = GPTSoVITSBackend(cfg, project)
        if not backend.root or not backend.root.exists():
            raise RuntimeError(f"找不到 GPT-SoVITS 整合包：{backend.root}。请重新双击 install_windows.bat，输入整合包的位置。")
        if check:
            missing = backend.missing_pretrained()
            if not missing:
                print("✅ GPT-SoVITS 预训练模型已齐全")
                return 0
            print(f"缺少 {len(missing)} 个 GPT-SoVITS 预训练模型：")
            for i, rel in enumerate(missing, 1):
                print(f"{i:>2}. {rel}")
            print("可以运行 voicetwin download-models --source hf-mirror 自动下载（大约 1~2GB）。")
            return 3
        from voicetwin.workflows import download_models

        progress = _cli_progress("download", cfg, "下载模型")
        files = download_models(cfg, source, progress=progress)  # 包括精准声纹打分的模型；下载期间电脑不自动睡眠
        _finish(progress)
        print(f"✅ 已下载 {len(files)} 个文件" if files else "✅ 模型已齐全")
        return 0
    finally:
        shutil.rmtree(project.root, ignore_errors=True)


def main(argv: Optional[List[str]] = None) -> None:
    _safe_console()
    ap = build_parser()
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_help()
        return
    if args.command not in NO_QUICK_EDIT_COMMANDS:
        _disable_quick_edit()
    if args.command == "init-config":
        repl = {}
        if args.gptsovits_root:
            repl["backends.gptsovits.root"] = str(Path(args.gptsovits_root).expanduser().resolve()).replace("\\", "/")
        if args.workspace:
            repl["workspace"] = args.workspace
        if args.backend:
            repl["backend"] = args.backend
        path = Path.cwd() / "config.yaml"
        try:
            if path.exists() and not args.force:
                if repl:
                    done = {}
                    for key, value in repl.items():
                        try:
                            update_config_file(path, {key: value})
                            done[key] = value
                        except KeyError:
                            print(f"⚠️ {path} 里没有 {key} 这一项，已跳过（可手动添加）")
                    if done:
                        print(f"已更新 {path}：" + "，".join(f"{k} = {v}" for k, v in done.items()) + "（其余设置保持不变）")
                else:
                    print(f"{path} 已存在，保持不变（加 --force 可重新生成，旧文件会备份为 config.yaml.bak）。")
                return
            write_example_config(path, repl, overwrite=args.force)
        except Exception as exc:
            if args.verbose:
                raise
            print(f"\n❌ {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"已生成 {path}，按需修改即可。")
        return
    import logging

    from voicetwin.utils.log import setup_logging

    setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    try:
        cfg = load_config(args.config)
        from voicetwin import workflows as wf

        if args.command == "doctor":
            code = _print_doctor(_doctor_rows(wf, cfg))
            if code:
                sys.exit(code)
        elif args.command == "list":
            _print_voices(wf, cfg)
        elif args.command == "prepare":
            overrides: dict = {}
            asr: dict = {}
            if args.asr:
                asr["engine"] = args.asr
            if args.asr_model:
                asr["model"] = args.asr_model
            if args.language:
                asr["language"] = args.language
            if asr:
                overrides["asr"] = asr
            if args.denoise:
                overrides["denoise"] = args.denoise
            if args.separate_vocals:
                overrides["separate_vocals"] = True
            if args.segmentation:
                overrides["segmentation"] = args.segmentation
            progress = _cli_progress("prepare", cfg, "准备素材", overrides=overrides)
            summary = wf.run_prepare(cfg, args.voice, args.input, progress=progress, overrides=overrides)
            _finish(progress)
            _print_summary(summary)
        elif args.command == "review":
            summary = wf.apply_review(cfg, args.voice)
            print(f"已同步修改：{summary['changed']}")
            _print_summary(summary)
        elif args.command == "confirm":
            res = wf.review_confirm(cfg, args.voice)
            if res.get("confirmed"):
                print(f"✅ 训练素材已确认（{res.get('time', '')}）：可以运行 voicetwin train -v {args.voice}")
            else:
                print("⚠️ 现在一条能用来训练的片段都没有，没法确认（先准备素材、检查校对表）")
                sys.exit(1)
        elif args.command == "analyze":
            wf.run_analyze(cfg, args.voice)
        elif args.command == "train":
            opts = {"sovits_epochs": args.sovits_epochs, "gpt_epochs": args.gpt_epochs, "batch_size": args.batch_size,
                    "epochs": args.epochs, "if_dpo": {"on": True, "off": False}.get(str(args.dpo or "auto"))}
            progress = _cli_progress("train", cfg, "训练模型", args.backend, select=not args.no_select)
            info = wf.run_train(cfg, args.voice, args.backend, progress=progress, select=not args.no_select, **opts)
            _finish(progress)
            print(f"训练完成（用时 {info.get('train_minutes')} 分钟）。默认模型：{(info.get('selected') or {}).get('id')}")
            if info.get("selection_error"):
                print(f"⚠️ 训练成功了，但自动挑选模型没有完成：{info['selection_error']}\n"
                      f"   可以稍后运行：voicetwin select -v {args.voice}")
        elif args.command == "select":
            kw: Dict[str, Any] = {"use_asr": args.asr}
            if args.items is not None:
                kw["items"] = args.items
            progress = _cli_progress("select", cfg, "挑选最佳模型", args.backend)
            info = wf.run_select(cfg, args.voice, args.backend, progress=progress, **kw)
            _finish(progress)
            _print_json({"best": info["selection"]["best"], "speed": info["speed"]})
        elif args.command in ("say", "narrate"):
            source = args.text if args.command == "say" else args.script
            if args.command == "narrate" and not Path(source).exists():
                raise FileNotFoundError(f"找不到讲稿文件：{source}")
            redo = _parse_redo(getattr(args, "redo", ""))
            if args.quality is None:  # 没写 -q：按 config.yaml，旧版本写进去的默认值 / 手动写的档位都说一声
                for line in _config_quality_notes(cfg):
                    print(f"ℹ️ {line}")
            progress = _cli_progress("narrate", cfg, "生成音频", args.backend, quality=args.quality)
            res = wf.run_narrate(cfg, args.voice, source, out=args.output, backend_name=args.backend,
                                 quality=args.quality, candidates=args.candidates, speed=_speed_arg(args),
                                 reference=args.ref,
                                 redo=redo,
                                 subtitles=False if getattr(args, "no_srt", False) or args.command == "say" else None,
                                 asr_check=args.asr_check, progress=progress)
            _finish(progress)
            _print_narration(res, args.command == "narrate")
        elif args.command == "evaluate":
            from voicetwin.synth.select import evaluate_file

            project = wf.open_project(cfg, args.voice, must_exist=True)
            _print_json(evaluate_file(cfg, project, Path(args.audio), args.text))
        elif args.command == "auto":
            for line in _config_quality_notes(cfg):  # 最后生成试听时用 config.yaml 的质量
                print(f"ℹ️ {line}")
            progress = _cli_progress("", cfg, "全自动处理")
            result = wf.run_auto(cfg, args.voice, args.input, args.backend, skip_train=args.skip_train,
                                 progress=progress)
            _finish(progress)
            _print_summary(result["prepare"])
            print(f"\n✅ 全部完成！试听：{result['demo']}")
        elif args.command == "mux":
            from voicetwin.utils.ffmpeg import mux_audio_into_video

            out = mux_audio_into_video(Path(args.video), Path(args.audio), Path(args.output), args.keep_original)
            print(f"✅ 已生成 {out}")
        elif args.command == "download-models":
            code = _download_sv_models(cfg, args.check) if args.sv else _download_models(cfg, args.source, args.check)
            if code:
                sys.exit(code)
        elif args.command == "clear-cache":
            from voicetwin.synth.engine import clear_cache

            n = clear_cache(wf.open_project(cfg, args.voice, must_exist=True))
            print(f"已清除 {n} 条缓存")
        elif args.command == "webui":
            from voicetwin.webui.launcher import launch

            launch(cfg, host=args.host, port=args.port, share=args.share)
    except KeyboardInterrupt:
        print("\n已取消。")
        sys.exit(130)
    except Exception as exc:
        if args.verbose:
            raise
        print(f"\n❌ {exc}\n（加 --verbose 查看详细错误信息）", file=sys.stderr)
        sys.exit(1)


SPEED_PERCENT_MAX = 50.0


def _speed_arg(args: Any) -> Optional[float]:
    """--speed 倍数，或者 --faster / --slower 百分比（快 20% = 1.20 倍，慢 15% = 0.85 倍）。"""
    faster = getattr(args, "faster", None)
    slower = getattr(args, "slower", None)
    if faster is None and slower is None:
        return getattr(args, "speed", None)
    pct = float(faster if faster is not None else slower)
    if not 0 <= pct <= SPEED_PERCENT_MAX:
        raise ValueError(f"语速百分比要在 0 到 {SPEED_PERCENT_MAX:g} 之间（建议不超过 15，太极端会不自然），"
                         f"例如 --faster 10 或 --slower 15")
    return round(1.0 + pct / 100.0 if faster is not None else 1.0 - pct / 100.0, 4)


def _variant_score_text(v: Dict[str, Any]) -> str:
    for key in ("pct", "percent", "similarity_pct"):
        if isinstance(v.get(key), (int, float)):
            return f"像你本人 {float(v[key]):.1f}%"
    score = v.get("score")
    if isinstance(score, (int, float)):
        return f"相似度 {float(score):.1f}%" if score > 1.0 else f"相似度 {float(score):.3f}"
    return ""


def _print_narration(res: Any, is_narrate: bool) -> None:
    print(f"\n✅ 音频：{res.audio_path}（{res.duration:.1f} 秒）")
    overall = getattr(res, "overall_pct", None)
    if isinstance(overall, (int, float)):
        print(f"   整篇像你本人 {float(overall):.1f}%（100% = 和你自己的真实录音一样像；声纹模型自动打分，最终以耳朵为准）")
    variants = [v for v in (getattr(res, "variants", None) or []) if isinstance(v, dict)]
    if variants:
        print(f"   共 {len(variants)} 个版本（{res.audio_path} 是现在用的那个）：")
        for i, v in enumerate(variants, 1):
            label = chr(ord("A") + i - 1) if i <= 26 else str(i)
            score = _variant_score_text(v)
            star = "  ⭐ 推荐：更像你的原声" if v.get("recommended") else ""
            print(f"   版本 {label}：{v.get('name', '')}  {v.get('path', '')}" + (f"（{score}）" if score else "") + star)
    if res.srt_path:
        print(f"   字幕：{res.srt_path}")
    print(f"   报告：{res.report_path}")
    warnings = list(res.warnings or [])
    if warnings:
        more = "，下面只列出前 20 条" if len(warnings) > 20 else ""
        print(f"   提示（共 {len(warnings)} 条{more}）：")
        for i, w in enumerate(warnings[:20], 1):
            print(f"   {i:>2}. ⚠️ {w}")
    flagged = [int(n) for n in (getattr(res, "flagged", None) or [])]
    if flagged and is_narrate:
        print("   想只重做这几句：加上 --redo " + ",".join(map(str, flagged)))


def _print_summary(s: dict) -> None:
    print(f"\n素材：保留 {s['clips_kept']}/{s['clips_total']} 条，共 {s['minutes_kept']} 分钟 {s.get('minutes_by_lang', {})}")
    dropped = s.get("dropped") or {}
    if dropped:
        total = sum(v for v in dropped.values() if isinstance(v, (int, float)))
        print(f"丢弃原因（共 {len(dropped)} 种，{total:g} 条）：")
        for i, (k, v) in enumerate(dropped.items(), 1):
            print(f"{i:>3}. {k}：{v} 条")
    skipped = [x for x in (s.get("skipped_files") or []) if isinstance(x, dict)]
    if skipped:
        print(f"跳过的文件（共 {len(skipped)} 个）：")
        for i, x in enumerate(skipped, 1):
            print(f"{i:>3}. {x.get('file', '')}：{x.get('reason', '')}")
    warnings = list(s.get("warnings") or [])
    if warnings:
        print(f"提示（共 {len(warnings)} 条）：")
        for i, w in enumerate(warnings, 1):
            print(f"{i:>3}. ⚠️ {w}")
    if s.get("transcripts_csv"):
        print(f"校对表：{s['transcripts_csv']}（修改后运行 voicetwin review -v {s['voice']}）")


if __name__ == "__main__":
    main()
