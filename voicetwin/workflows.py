"""高层工作流：命令行和网页界面共用。"""

from __future__ import annotations

import importlib
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from voicetwin.config import Config
from voicetwin.project import Project
from voicetwin.utils.log import get_logger, setup_logging

log = get_logger("workflow")
ProgressFn = Callable[[float, str], None]


def open_project(cfg: Config, voice: str, must_exist: bool = False) -> Project:
    project = Project(cfg, voice)
    if must_exist and not project.exists:
        raise RuntimeError(f"还没有名为「{voice}」的声音，请先运行：voicetwin prepare -v {voice} -i 你的视频文件夹")
    project.ensure()
    setup_logging(log_file=project.logs_dir / "voicetwin.log")
    return project


def list_voices(cfg: Config) -> List[Dict[str, Any]]:
    from voicetwin.config import resolve_path

    ws = resolve_path(cfg, cfg.get("workspace", "./workspace"))
    out = []
    if ws and ws.exists():
        for d in sorted(p for p in ws.iterdir() if p.is_dir()):
            proj = Project(cfg, d.name)
            if not proj.exists:
                continue
            summary = proj.read_json(proj.root / "prepare_summary.json", {}) or {}
            models = proj.load_models()
            out.append({"voice": d.name, "minutes": summary.get("minutes_kept"), "clips": summary.get("clips_kept"),
                        "trained": [k for k, v in models.items() if v.get("selected")],
                        "profile": proj.profile_path.exists()})
    return out


# ---------------------------------------------------------------------------- 素材
def run_prepare(cfg: Config, voice: str, inputs: Iterable[str], progress: Optional[ProgressFn] = None,
                overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from voicetwin.data.prepare import prepare
    from voicetwin.style.profile import build_profile

    project = open_project(cfg, voice)
    summary = prepare(project, list(inputs), cfg, progress, overrides)
    if summary["clips_kept"]:
        summary["profile"] = build_profile(project)
    return summary


def apply_review(cfg: Config, voice: str) -> Dict[str, Any]:
    """读回你在 transcripts.csv 里的修改，重新统计、过滤、挑参考音频。"""
    from voicetwin.data.prepare import _clip_stats, apply_filters, assign_splits, summarize
    from voicetwin.data.references import select_references
    from voicetwin.style.profile import build_profile

    project = open_project(cfg, voice, must_exist=True)
    changed = project.import_csv()
    records = project.load_manifest()
    for r in records:
        if r.get("_stats_text") != r.get("text"):
            _clip_stats(project, r)
            r["_stats_text"] = r.get("text")
    pcfg = cfg.get("prepare", {})
    apply_filters(project, records, pcfg, cfg)
    assign_splits(records, int(pcfg.get("validation_count", 12)))
    project.save_manifest(records)
    refs = select_references(project, records, pcfg)
    project.export_csv(records)
    build_profile(project)
    summary = summarize(project, records, refs)
    summary["changed"] = changed
    project.write_json(project.root / "prepare_summary.json", summary)
    return summary


def run_analyze(cfg: Config, voice: str) -> Dict[str, Any]:
    from voicetwin.style.profile import build_profile

    return build_profile(open_project(cfg, voice, must_exist=True))


# ---------------------------------------------------------------------------- 训练 / 挑选
def run_train(cfg: Config, voice: str, backend_name: Optional[str] = None, progress: Optional[ProgressFn] = None,
              select: bool = True, **opts: Any) -> Dict[str, Any]:
    from voicetwin.backends.base import get_backend

    project = open_project(cfg, voice, must_exist=True)
    backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
    if not backend.supports_training:
        raise RuntimeError(f"{backend.display_name} 不需要训练（零样本克隆），可以直接合成")
    t0 = time.time()
    info = backend.train(progress=progress, **opts)
    info["train_minutes"] = round((time.time() - t0) / 60.0, 1)
    if select:
        info["selection"] = run_select(cfg, voice, backend.name, progress=progress)
    return info


def run_select(cfg: Config, voice: str, backend_name: Optional[str] = None, items: int = 12,
               use_asr: Optional[bool] = None, progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    from voicetwin.backends.base import get_backend
    from voicetwin.synth.select import select_and_calibrate

    project = open_project(cfg, voice, must_exist=True)
    backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
    with backend:
        return select_and_calibrate(cfg, project, backend, max_items=items, use_asr=use_asr, progress=progress)


# ---------------------------------------------------------------------------- 合成
def default_output(project: Project, stem: str, fmt: str) -> Path:
    from voicetwin.utils.textutil import safe_name

    return project.outputs_dir / f"{safe_name(stem, 30)}_{time.strftime('%Y%m%d_%H%M%S')}.{fmt}"


def run_narrate(cfg: Config, voice: str, source: str, out: Optional[str] = None, backend_name: Optional[str] = None,
                quality: Optional[str] = None, candidates: Optional[int] = None, speed: Any = None,
                reference: str = "", redo: Iterable[int] = (), subtitles: Optional[bool] = None,
                asr_check: Optional[bool] = None, progress: Optional[ProgressFn] = None, backend=None):
    from voicetwin.backends.base import get_backend
    from voicetwin.synth.engine import Narrator

    project = open_project(cfg, voice, must_exist=True)
    fmt = cfg.get("synth", {}).get("output_format", "wav")
    src_path = Path(source) if len(source) < 1024 and "\n" not in source else None
    if src_path is not None and src_path.exists():
        stem = src_path.stem
    else:
        stem = source.strip().splitlines()[0][:20] if source.strip() else "output"
    out_path = Path(out) if out else default_output(project, stem, fmt)
    own_backend = backend is None
    backend = backend or get_backend(backend_name or cfg.get("backend"), cfg, project)
    try:
        narrator = Narrator(cfg, project, backend, quality=quality, candidates=candidates, speed=speed,
                            reference=reference, asr_check=asr_check, progress=progress)
        return narrator.narrate(source if src_path is None or not src_path.exists() else src_path, out_path,
                                redo=redo, subtitles=subtitles)
    finally:
        if own_backend:
            backend.stop()


def run_auto(cfg: Config, voice: str, inputs: Iterable[str], backend_name: Optional[str] = None,
             skip_train: bool = False, progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    """一条龙：素材准备 → 风格分析 → 训练 → 挑最佳模型 → 生成试听。"""
    from voicetwin.backends.base import get_backend

    def sub(lo: float, hi: float) -> Optional[ProgressFn]:
        if progress is None:
            return None
        return lambda f, m: progress(lo + (hi - lo) * f, m)

    result: Dict[str, Any] = {"prepare": run_prepare(cfg, voice, inputs, sub(0.0, 0.25))}
    project = open_project(cfg, voice, must_exist=True)
    backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
    if backend.supports_training and not skip_train:
        result["train"] = run_train(cfg, voice, backend.name, sub(0.25, 0.9), select=True)
    else:
        result["selection"] = run_select(cfg, voice, backend.name, progress=sub(0.25, 0.9))
    demo = []
    refs = project.load_references()
    if any(r["lang"] == "zh" for r in refs):
        demo.append("大家好，欢迎来到今天的课程。今天我们要讲的内容非常重要，大家一定要认真听。")
    if any(r["lang"] == "en" for r in refs) or not demo:
        demo.append("Hello everyone, welcome back. Today we're going to learn something really useful.")
    res = run_narrate(cfg, voice, "\n\n".join(demo), out=str(project.outputs_dir / "试听_demo.wav"),
                      backend_name=backend.name, progress=sub(0.9, 1.0))
    result["demo"] = str(res.audio_path)
    return result


# ---------------------------------------------------------------------------- 环境检查
def doctor(cfg: Config) -> List[Dict[str, str]]:
    from voicetwin.backends.base import available_backends, get_backend

    rows: List[Dict[str, str]] = []

    def add(item: str, ok: Optional[bool], detail: str) -> None:
        rows.append({"item": item, "status": "✅" if ok else ("⚠️" if ok is None else "❌"), "detail": detail})

    add("Python", sys.version_info >= (3, 9), f"{platform.python_version()}（{platform.system()} {platform.machine()}）")
    try:
        from voicetwin.utils.ffmpeg import find_ffmpeg

        add("ffmpeg", True, find_ffmpeg())
    except Exception as exc:
        add("ffmpeg", False, str(exc))
    for mod, label, required in (
        ("numpy", "numpy", True), ("scipy", "scipy", True), ("soundfile", "soundfile", True),
        ("librosa", "librosa", True), ("pyloudnorm", "pyloudnorm", True),
        ("faster_whisper", "faster-whisper（语音识别）", False), ("funasr", "funasr（中文识别，可选）", False),
        ("resemblyzer", "resemblyzer（声纹打分）", False), ("gradio", "gradio（网页界面）", False),
        ("noisereduce", "noisereduce（降噪，可选）", False), ("demucs", "demucs（去背景音乐，可选）", False),
    ):
        try:
            m = importlib.import_module(mod)
            add(label, True, getattr(m, "__version__", "已安装"))
        except Exception:
            add(label, False if required else None, "未安装" + ("（必需）" if required else ""))
    smi = shutil.which("nvidia-smi")
    if smi:
        try:
            out = subprocess.run([smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20).stdout.decode().strip()
            add("NVIDIA 显卡", bool(out), out or "未检测到")
        except Exception as exc:
            add("NVIDIA 显卡", None, str(exc))
    else:
        add("NVIDIA 显卡", None, "没有找到 nvidia-smi（没有 N 卡时只能用 CPU，训练会非常慢）")
    dummy = Project(cfg, "__doctor__")
    for name in available_backends():
        if name == "dummy":
            continue
        try:
            b = get_backend(name, cfg, dummy)
            problems = b.check()
            py = getattr(b, "python", "")
            add(f"引擎 {b.display_name}", not problems if name == cfg.get("backend") else (None if problems else True),
                ("；".join(problems) if problems else "就绪") + (f"（Python：{py}）" if py else ""))
        except Exception as exc:
            add(f"引擎 {name}", None, str(exc))
    shutil.rmtree(dummy.root, ignore_errors=True)
    return rows
