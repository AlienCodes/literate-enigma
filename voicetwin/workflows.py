"""高层工作流：命令行和网页界面共用。

进度约定（interface E）：每个长任务的进度都是 0~1、只往前走：
- 素材准备：prepare() 只报 0.00~0.95；run_prepare 报 0.95（分析说话风格）和 1.0。
  要自动"查找可能的错字"时，prepare() 压缩到 0~0.85，风格分析 0.85，查错字 0.87~0.99。
- 训练：backend.train 占 0~0.88，自动挑选最佳模型占 0.88~1.0。
- 网页上传文件时复制文件占 0.00~0.02（网页那边做）。
"""

from __future__ import annotations

import importlib
import json
import platform
import random
import re
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from voicetwin.config import Config, deep_merge
from voicetwin.project import Project
from voicetwin.utils.log import get_logger, setup_logging

try:  # U6：任务进行中阻止电脑睡眠（同一线程可以嵌套）
    from voicetwin.utils.winsys import keep_awake
except ImportError:  # pragma: no cover - 没有 U6 时什么都不做
    from contextlib import nullcontext as keep_awake  # type: ignore

try:  # U1：停止按钮
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover
    def _check_cancel() -> None:
        return None

log = get_logger("workflow")
ProgressFn = Callable[[float, str], None]
Stage = Tuple[float, str]

# ---------------------------------------------------------------------------- 进度阶段表
STAGES_PREPARE: List[Stage] = [(0.00, "整理要处理的文件"), (0.02, "提取声音、降噪、切成小段"), (0.40, "识别每段话的文字"),
                               (0.74, "分析语速和停顿"), (0.80, "检查是不是你本人的声音"), (0.90, "挑选参考音频、保存结果"),
                               (0.95, "分析你的说话风格")]
STAGES_SELECT: List[Stage] = [(0.00, "加载打分模型"), (0.05, "启动合成引擎"), (0.10, "逐个试听每个模型，挑最像你的")]
STAGES_NARRATE: List[Stage] = [(0.00, "启动合成引擎"), (0.03, "逐句生成"), (0.95, "拼接音频、生成字幕")]
#: 「完美」档多一步：做「去杂音」版本并比较
STAGES_NARRATE_VARIANTS: List[Stage] = [(0.00, "启动合成引擎"), (0.03, "逐句生成"), (0.90, "拼接音频、生成字幕"),
                                        (0.93, "做「去杂音」版本并比较哪个更像你")]
STAGES_DOWNLOAD: List[Stage] = [(0.0, "下载模型文件")]
STAGES_PROOFCHECK: List[Stage] = [(0.00, "准备识别引擎"), (0.02, "逐条检查文字，标出可能的错字")]
STAGES_TEXTFIX: List[Stage] = [(0.00, "读母本和语法术语"), (0.15, "一句一句检查")]
STAGES_BLIND_TEST: List[Stage] = [(0.00, "挑选你的真实录音"), (0.05, "用同样的文字生成"), (0.90, "统一音量、打乱顺序、保存")]
STAGES_VERIFY: List[Stage] = [(0.00, "加载声纹模型"), (0.10, "逐个打分")]
TRAIN_SELECT_SPLIT = 0.88
PROOFCHECK_PREPARE_END = 0.85     # 要查错字时，prepare() 的 0.95 压缩到这里
PROOFCHECK_START = 0.87
PROOFCHECK_END = 0.99
STAGES_PREPARE_PROOFCHECK: List[Stage] = (
    [(round(f * PROOFCHECK_PREPARE_END / 0.95, 4), n) for f, n in STAGES_PREPARE[:-1]]
    + [(PROOFCHECK_PREPARE_END, "分析你的说话风格"), (PROOFCHECK_START, "查找可能的错字")]
)

SPEED_SLIDER_MIN, SPEED_SLIDER_MAX = -30, 30
SPEED_NOTE = "语速调得越极端（超过 ±20%），越可能不自然；建议在 −15～+15 之间。"
SPEED_LABEL = "语速（← 往左更快　·　中间 0 = 和你原声一样　·　往右更慢 →）"
DEFAULT_SAMPLE_ZH = "大家好，这是试听语速的一句话，你听听快慢合不合适。"
DEFAULT_SAMPLE_EN = "Hello everyone, this is a short sample to check the speaking speed."


def _sub(progress: Optional[ProgressFn], lo: float, hi: float) -> Optional[ProgressFn]:
    """把子任务自己的 0~1 进度映射到 [lo, hi]。progress 为 None 时返回 None。"""
    if progress is None:
        return None

    def sub(frac: float, msg: str = "") -> None:
        try:
            f = float(frac)
        except (TypeError, ValueError):
            f = 0.0
        progress(lo + (hi - lo) * max(0.0, min(1.0, f)), msg)

    return sub


def _report(progress: Optional[ProgressFn], frac: float, msg: str) -> None:
    """写一行日志并更新进度条；进度条出问题不影响任务（TaskCancelled 是 BaseException，照常传出去）。"""
    log.info(msg)
    if progress is not None:
        try:
            progress(max(0.0, min(1.0, frac)), msg)
        except Exception:
            pass


def _explain_title(exc: BaseException) -> str:
    try:
        from voicetwin.errors import explain

        return explain(exc).title
    except Exception:
        return str(exc)[:80] or type(exc).__name__


def _backend_class(name: str) -> Any:
    """不创建引擎对象，只拿到它的类（看 train_stages / supports_training 用）。"""
    from voicetwin.backends.base import _BACKENDS

    mod_name, cls_name = _BACKENDS[name].split(":")
    return getattr(importlib.import_module(mod_name), cls_name)


def _effective_cfg(cfg: Config, overrides: Optional[Dict[str, Any]]) -> Config:
    """把网页/命令行传来的素材准备选项（overrides）合并进配置，返回新的 Config。"""
    if not overrides:
        return cfg
    merged = Config(deep_merge(dict(cfg), {"prepare": dict(overrides)}))
    return merged


def _proofcheck_module() -> Any:
    try:
        from voicetwin.data import proofcheck  # U8

        return proofcheck
    except ImportError:
        return None


def proofcheck_plan(cfg: Config, overrides: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, str]:
    """素材准备最后要不要自动"查找可能的错字"：返回（要不要做, 引擎名, 中文说明）。

    prepare.proofcheck：auto（默认，装了和主识别引擎不同的第二个引擎时才做）| on（总是做）| off。
    """
    eff = _effective_cfg(cfg, overrides)
    mode = eff.get_path("prepare.proofcheck", "auto")
    if mode is True:
        mode = "on"
    elif mode is False:
        mode = "off"
    mode = str(mode or "auto").strip().lower()
    if mode in ("off", "false", "no", "0", "none"):
        return False, "", ""
    mod = _proofcheck_module()
    if mod is None:
        return False, "", "查错字功能还没装好"
    try:
        engine, reason = mod.available_checker(eff)
    except Exception as exc:
        return False, "", f"查不到可用的识别引擎（{exc}）"
    if mode in ("on", "true", "yes", "1"):
        return True, str(engine or ""), str(reason or "")
    primary = str(eff.get_path("prepare.asr.engine", "faster-whisper") or "faster-whisper").lower()
    second = engine in ("funasr", "faster-whisper") and engine != primary
    return bool(second), str(engine or ""), str(reason or "")


def task_stages(kind: str, cfg: Optional[Config] = None, backend_name: Optional[str] = None, select: bool = True,
                quality: Optional[str] = None, proofcheck: Optional[bool] = None,
                overrides: Optional[Dict[str, Any]] = None) -> List[Stage]:
    """给进度条用的阶段表：[(开始的进度, 中文步骤名), ...]，从小到大。

    kind：prepare | train | select | narrate（= generate）| download | proofcheck | textfix | blind_test | verify。
    narrate 请把网页上选的 quality 一起传进来（「完美」档多一步）；prepare 可以传 overrides / proofcheck。
    """
    kind = (kind or "").strip().lower()
    if kind == "prepare":
        plan = proofcheck if proofcheck is not None else (proofcheck_plan(cfg, overrides)[0] if cfg is not None else False)
        return list(STAGES_PREPARE_PROOFCHECK if plan else STAGES_PREPARE)
    if kind == "select":
        return list(STAGES_SELECT)
    if kind in ("narrate", "generate", "say"):
        from voicetwin.synth.engine import QUALITY_PRESETS, resolve_quality

        q = resolve_quality(quality if quality not in (None, "") else
                            ((cfg or {}).get("synth", {}) or {}).get("quality", "auto"))
        return list(STAGES_NARRATE_VARIANTS if QUALITY_PRESETS[q].get("variants") else STAGES_NARRATE)
    if kind == "download":
        return list(STAGES_DOWNLOAD)
    if kind == "proofcheck":
        return list(STAGES_PROOFCHECK)
    if kind == "textfix":
        return list(STAGES_TEXTFIX)
    if kind in ("blind_test", "blind"):
        return list(STAGES_BLIND_TEST)
    if kind == "verify":
        return list(STAGES_VERIFY)
    if kind == "train":
        name = str(backend_name or (cfg or {}).get("backend") or "gptsovits").lower()
        try:
            stages = list(getattr(_backend_class(name), "train_stages", None) or [(0.0, "训练模型")])
        except Exception:
            stages = [(0.0, "训练模型")]
        stages = sorted((float(f), str(n)) for f, n in stages)
        if select:
            return [(round(f * TRAIN_SELECT_SPLIT, 4), n) for f, n in stages] + [(TRAIN_SELECT_SPLIT, "自动挑选最像你的模型")]
        return stages
    return []


# ---------------------------------------------------------------------------- 声音
def open_project(cfg: Config, voice: str, must_exist: bool = False) -> Project:
    project = Project(cfg, voice)
    if must_exist and not project.exists:
        raise RuntimeError(f"还没有名为「{voice}」的声音，请先运行：voicetwin prepare -v {voice} -i 你的视频文件夹")
    project.ensure()
    setup_logging(log_file=project.logs_dir / "voicetwin.log")
    return project


def _voice_dirs(cfg: Config) -> List[Project]:
    from voicetwin.config import resolve_path

    ws = resolve_path(cfg, cfg.get("workspace", "./workspace"))
    out: List[Project] = []
    if ws and ws.exists():
        for d in sorted(p for p in ws.iterdir() if p.is_dir()):
            if d.name.startswith("__"):  # 环境检查等临时目录
                continue
            try:
                proj = Project(cfg, d.name)
            except ValueError:
                continue
            if proj.exists:
                out.append(proj)
    return out


def list_voices(cfg: Config) -> List[Dict[str, Any]]:
    out = []
    for proj in _voice_dirs(cfg):
        summary = proj.read_json(proj.root / "prepare_summary.json", {}) or {}
        models = proj.load_models()
        out.append({"voice": proj.voice, "minutes": summary.get("minutes_kept"), "clips": summary.get("clips_kept"),
                    "trained": [k for k, v in models.items() if v.get("selected")],
                    "profile": proj.profile_path.exists()})
    return out


def model_badge(cfg: Config, voice: str = "") -> Dict[str, Any]:
    """网页顶部「声音分身 VoiceTwin v0.1.x」右边显示的模型型号。

    GPT-SoVITS：从这个声音生成时实际要用的 SoVITS 模型文件里读出版本（训练好的模型；还没训练就读底模），
    不照抄设置；读不出来就如实说读不出来。其他引擎（不需要训练）显示引擎名字。
    返回 {"text": "GPT-SoVITS v2ProPlus", "note": "", "detail": 悬停时的说明, "version": "v2ProPlus" / None,
          "source": "trained" / "pretrained" / "external" / "", "level": "ok" / "warn"}。"""
    from voicetwin.backends.base import get_backend

    name = str(cfg.get("backend") or "gptsovits").lower()
    out: Dict[str, Any] = {"text": "", "note": "", "detail": "", "version": None, "source": "", "level": "ok"}
    probe: Optional[Project] = None
    try:
        proj: Optional[Project] = None
        if voice:
            try:
                proj = Project(cfg, voice)
            except ValueError:
                proj = None
        if proj is None or not proj.exists:  # 还没有这个声音：用临时目录看底模，不在声音库里多建一个文件夹
            proj = probe = Project(cfg, f"__model_badge_{time.time_ns()}__")
        backend = get_backend(name, cfg, proj)
        label = str(getattr(backend, "display_name", name))
        info = backend.model_version_info() if hasattr(backend, "model_version_info") else None
        if info is None:
            out.update(text=label, detail=f"{label}：零样本克隆，不需要训练（没有 GPT-SoVITS 那样的模型版本）")
            return out
        ver, src = info.get("version"), info.get("source", "")
        out.update(version=ver, source=src)
        fname = Path(str(info.get("file") or "")).name
        if ver:
            out["text"] = f"{label} {ver}"
            out["detail"] = f"从模型文件读出来的版本（{info.get('how')}）：{fname}"
            if src == "pretrained":
                out["note"] = ("找不到训练好的模型文件，现在用的是底模" if info.get("trained_missing")
                               else "底模，这个声音还没训练")
                out["level"] = "warn" if info.get("trained_missing") else out["level"]
            configured = str(info.get("configured") or "")
            if configured and configured != ver:
                out["level"] = "warn"
                out["detail"] += f"；设置里的版本是 {configured}，重新训练后会换成 {configured}"
        else:
            out.update(text=f"{label} 版本读不出来", level="warn", detail=str(info.get("how") or ""))
            if fname:
                out["detail"] += f"：{fname}"
    except Exception as exc:
        out.update(text=f"{name} 版本读不出来", level="warn", detail=_explain_title(exc))
    finally:
        if probe is not None:
            shutil.rmtree(probe.root, ignore_errors=True)
    return out


def _main_reference(proj: Project) -> str:
    try:
        from voicetwin.data.references import pick_reference

        refs = proj.load_references()
        if not refs:
            return ""
        langs = [r.get("lang") for r in refs]
        lang = "zh" if "zh" in langs else langs[0]
        path = proj.abspath(pick_reference(refs, lang, "statement")["path"])
        return str(path.resolve()) if path.exists() else ""
    except Exception:
        return ""


def voice_library(cfg: Config) -> List[Dict[str, Any]]:
    """我的声音库：每个已保存的声音一行（最近改过的排前面）。

    键：no（从 1 开始）、voice / name、minutes、clips_kept / clips、trained（bool）、trained_backends、
    best_model、main_reference（绝对路径或 ''）、modified（时间戳）、modified_text（"2026-10-01 21:30"）、status（中文）。
    """
    default_backend = str(cfg.get("backend") or "gptsovits").lower()
    try:
        needs_training = bool(getattr(_backend_class(default_backend), "supports_training", True))
    except Exception:
        needs_training = True
    rows: List[Dict[str, Any]] = []
    for proj in _voice_dirs(cfg):
        summary = proj.read_json(proj.root / "prepare_summary.json", {}) or {}
        models = proj.load_models()
        trained_backends = [k for k, v in models.items() if isinstance(v, dict) and v.get("selected")]
        best = ""
        for name in [default_backend] + [b for b in trained_backends if b != default_backend]:
            sel = (models.get(name) or {}).get("selected") if isinstance(models.get(name), dict) else None
            if sel:
                best = str(sel.get("id") or "")
                if name != default_backend:  # 不是默认引擎训练的：注明是哪个引擎（用中文界面上的名字）
                    try:
                        label = str(getattr(_backend_class(name), "display_name", name))
                    except Exception:
                        label = name
                    best += f"（{label}）"
                break
        clips = summary.get("clips_kept")
        minutes = summary.get("minutes_kept")
        if trained_backends:
            status = "✅ 已训练，可以生成"
        elif clips and not needs_training:
            status = "✅ 素材已准备，可以生成（这个引擎不需要训练）"
        elif clips:
            status = "⚠️ 素材已准备，还没训练"
        else:
            status = "⏳ 还没准备素材"
        modified = proj.last_modified()
        rows.append({
            "voice": proj.voice, "name": proj.voice, "minutes": minutes, "clips_kept": clips, "clips": clips,
            "trained": bool(trained_backends), "trained_backends": trained_backends, "best_model": best,
            "main_reference": _main_reference(proj), "modified": modified,
            "modified_text": time.strftime("%Y-%m-%d %H:%M", time.localtime(modified)) if modified else "",
            "status": status, "profile": proj.profile_path.exists(),
        })
    rows.sort(key=lambda r: (-(r["modified"] or 0.0), r["voice"]))
    for i, r in enumerate(rows, 1):
        r["no"] = i
    return rows


VOICE_LIBRARY_HEADERS = ["#", "名称", "素材（分钟 / 条）", "状态", "最佳模型", "最后修改时间"]


def voice_library_rows(cfg: Config) -> List[List[Any]]:
    """声音库表格的行（列见 VOICE_LIBRARY_HEADERS），# 从 1 开始。"""
    out = []
    for r in voice_library(cfg):
        mats = f"{float(r.get('minutes') or 0):g} 分钟 / {r['clips_kept']} 条" if r.get("clips_kept") else "—"
        out.append([r["no"], r["voice"], mats, r["status"], r["best_model"] or "—", r["modified_text"] or "—"])
    return out


# ---------------------------------------------------------------------------- 素材
def _clean_input(p: Any) -> str:
    s = str(p or "").strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'“”":
        s = s[1:-1].strip()
    return s.strip("“”").strip()


def _precheck_prepare(cfg: Config, voice: str, inputs: List[str], overrides: Optional[Dict[str, Any]]) -> List[str]:
    """开始前先检查（几秒钟）：文件夹在不在、识别组件装没装、硬盘空间。返回要提醒的话。"""
    from voicetwin.data.asr import engine_importable
    from voicetwin.data.prepare import discover_sources
    from voicetwin.data.subtitles import find_sidecar_subtitle

    for p in inputs:
        if not Path(p).expanduser().exists():
            raise FileNotFoundError(f"找不到文件夹：{p}。请在文件夹窗口顶部的地址栏复制路径，再粘贴过来")
    eff = _effective_cfg(cfg, overrides)
    project = Project(cfg, voice)
    from voicetwin.data.prepare import _own_dirs, already_done, load_sources

    sources_db = load_sources(project, project.load_manifest())
    files = discover_sources(inputs, exclude=_own_dirs(project, eff))
    new = []
    for f in files:
        try:
            if not already_done(sources_db, f):
                new.append(f)
        except OSError:
            continue
    pending = [r for r in project.load_manifest() if not r.get("text") and not r.get("asr_done")]
    engine = str(eff.get_path("prepare.asr.engine", "faster-whisper") or "faster-whisper").lower()
    seg_mode = str(eff.get_path("prepare.segmentation", "auto") or "auto").lower()
    need_asr = bool(pending) or any(not (seg_mode in ("auto", "srt") and find_sidecar_subtitle(f)) for f in new)
    if need_asr and engine != "none" and not engine_importable(engine):
        raise RuntimeError("语音识别组件没装好，请重新双击 install_windows.bat 安装一次")
    notes: List[str] = []
    try:
        size = sum(f.stat().st_size for f in new)
        root = project.root if project.root.exists() else project.root.parent
        root.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(str(root)).free
        if free < 1.5 * size + 2 * 1024 ** 3:
            msg = f"⚠️ 硬盘剩余空间可能不够（还剩 {free / 1024 ** 3:.1f} GB），建议先清理一下再处理"
            log.warning(msg)
            notes.append(msg)
    except OSError:
        pass
    return notes


def run_prepare(cfg: Config, voice: str, inputs: Iterable[str], progress: Optional[ProgressFn] = None,
                overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    from voicetwin.data.prepare import prepare
    from voicetwin.style.profile import build_profile

    inputs = [s for s in (_clean_input(p) for p in (inputs or [])) if s]
    notes = _precheck_prepare(cfg, voice, inputs, overrides)
    with keep_awake():
        project = open_project(cfg, voice)
        do_proof, engine, reason = proofcheck_plan(cfg, overrides)
        if do_proof:
            summary = prepare(project, inputs, cfg, _sub(progress, 0.0, PROOFCHECK_PREPARE_END / 0.95), overrides)
        else:
            summary = prepare(project, inputs, cfg, progress, overrides)
        summary["warnings"] = list(notes) + list(summary.get("warnings") or [])
        if summary["clips_kept"]:
            _report(progress, PROOFCHECK_PREPARE_END if do_proof else 0.95, "分析你的说话风格（语速、停顿、音高）……")
            summary["profile"] = build_profile(project)
        if do_proof and summary["clips_kept"]:
            _report(progress, PROOFCHECK_START, "查找可能的错字" + (f"（{reason}）" if reason else "") + "……")
            try:
                res = _proofcheck_module().find_suspects(project, _effective_cfg(cfg, overrides),
                                                         progress=_sub(progress, PROOFCHECK_START, PROOFCHECK_END))
                summary["proofcheck"] = res
                if (res or {}).get("flagged"):
                    summary["warnings"].append(f"其中 {res['flagged']} 条文字可能有错（已标红），请在校对表里看一看")
            except Exception as exc:
                why = _explain_title(exc)
                # exc_info：原始的报错（英文 Traceback）只写进黑色窗口和 voicetwin.log，给帮忙的人看；网页上只显示这一行中文
                log.warning(f"⚠️ 自动查错字没有完成（{why}），素材已经准备好了，不影响使用", exc_info=exc)
                summary["warnings"].append(f"自动查错字没有完成（{why}）。可以稍后在校对表上方点「🔍 自动查找可能的错字」再试")
        saved = {k: v for k, v in summary.items() if k != "profile"}
        project.write_json(project.root / "prepare_summary.json", saved)
        _report(progress, 1.0, "素材准备完成")
    return summary


#: apply_review 重新统计时算出来、写进校对表的东西（别的字段都是老师 / 别的功能改的，合并时不碰）
REVIEW_DERIVED = ("voiced", "pauses", "syllables", "rate", "snr", "clip_ratio", "_stats_text", "drop_reason",
                  "speaker_sim", "keep", "split")
#: 会影响上面这些的东西：期间变了就要重新算
REVIEW_INPUTS = ("id", "text", "lang", "deleted", "manual_keep", "duration", "path", "asr", "forced_cuts", "source",
                 "start")


def _same_review_inputs(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> bool:
    return len(a) == len(b) and all(all(x.get(k) == y.get(k) for k in REVIEW_INPUTS) for x, y in zip(a, b))


def apply_review(cfg: Config, voice: str, read_csv: bool = True) -> Dict[str, Any]:
    """读回你在 transcripts.csv 里的修改，重新统计、过滤、挑参考音频。

    read_csv=False：修改已经直接写进 manifest 了（网页校对表的保存），不再读 CSV
    （CSV 被 Excel 打开、没能同步时，读回去会把刚保存的修改改回旧的）。"""
    from voicetwin.data.prepare import _clip_stats, apply_filters, assign_splits, summarize
    from voicetwin.data.references import select_references
    from voicetwin.style.profile import build_profile

    import copy

    from voicetwin.data import review as _review

    project = open_project(cfg, voice, must_exist=True)
    changed = project.import_csv() if read_csv else {"text": 0, "keep": 0, "lang": 0}
    pcfg = cfg.get("prepare", {})

    def derive(records: List[Dict[str, Any]]) -> None:
        for r in records:
            if r.get("_stats_text") != r.get("text"):
                _clip_stats(project, r)
                r["_stats_text"] = r.get("text")
        apply_filters(project, records, pcfg, cfg)
        assign_splits(records, int(pcfg.get("validation_count", 20)))

    # 慢的部分（读音频、算声纹）不占着校对表的锁，算在一份拷贝上；写回时拿着锁重新读一遍，只把这次算出来的
    # 东西合进去——期间老师保存的另一行、删除、「这句没错」、一键校正都留着（以前整个写回旧的那份，会把它们冲掉）
    before = project.load_manifest()
    snapshot = copy.deepcopy(before)
    derive(snapshot)
    with _review._LOCK:
        fresh = project.load_manifest()
        if _same_review_inputs(before, fresh):
            for r, b, d in zip(fresh, before, snapshot):
                for k in REVIEW_DERIVED:
                    if k in d:
                        r[k] = d[k]
                    elif k in b:
                        r.pop(k, None)
        else:
            derive(fresh)  # 期间改了会影响统计的东西（文字、删除、要不要用）：拿着锁重新算一遍（很少见）
        records = fresh
        project.save_manifest(records)
    refs = select_references(project, records, pcfg)
    csv_locked = False
    try:
        project.export_csv(records)
    except PermissionError:
        if read_csv:
            raise
        csv_locked = True
    no_material = ""
    try:
        build_profile(project)
    except RuntimeError as exc:  # 一条能用的都没有（比如文字还没识别出来）：校对表的删除 / 保存照样要成功
        no_material = str(exc)
        log.warning(f"⚠️ 重新统计时没法分析说话风格：{exc}")
    summary = summarize(project, records, refs)
    summary["changed"] = changed
    if no_material:
        summary.setdefault("warnings", []).insert(
            0, "现在一条能用来训练的片段都没有（多半是文字还没识别出来），所以这次没法分析说话风格")
    project.write_json(project.root / "prepare_summary.json", summary)
    if csv_locked:
        summary["csv_locked"] = True
    return summary


def review_save(cfg: Config, voice: str, ids: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    """校对表「保存修改」（ids=None，全部）/「💾 保存这一行」（ids=[那一条]）：把没保存的修改写进校对表，
    再重新统计、过滤、挑参考音频（和以前的保存一样）。"""
    from voicetwin.data import review

    project = open_project(cfg, voice, must_exist=True)
    res = review.save_rows(project, ids)
    res["summary"] = apply_review(cfg, voice, read_csv=False) if res["saved"] else None
    if res["summary"] and res["summary"].get("csv_locked"):
        res["csv_locked"] = True
    return res


def review_confirm(cfg: Config, voice: str) -> Dict[str, Any]:
    """校对表「✅ 确认训练素材」：先把没保存的修改全部保存（和「保存修改」一样），重新统计，再记下现在用来训练的是哪些句子。

    一条能用来训练的都没有时不记（返回 confirmed=False），界面会说明原因。"""
    from voicetwin.data import review

    project = open_project(cfg, voice, must_exist=True)
    saved = review.save_rows(project)
    summary = apply_review(cfg, voice, read_csv=False)
    with review._LOCK:  # 记下的「确认了哪些句子」和这一刻的校对表一致（期间别的按钮改了也不会错开）
        records = project.load_manifest()
        counts = review.material_counts(records)
        out = {"saved": saved["saved"], "changed": saved["changed"], "summary": summary, "counts": counts,
               "csv_locked": bool(saved.get("csv_locked") or summary.get("csv_locked")), "confirmed": False}
        if counts["material"] > 0:
            out["confirmed"] = True
            out["time"] = review.save_confirmed(project, records)["time"]
            review.clear_undo(project)  # 确认以后「撤销刚才的替换」不能再把确认好的字改回去
    return out


def review_delete(cfg: Config, voice: str, clip_id: str) -> Dict[str, Any]:
    """校对表「🗑️ 删除这一行」：这一条不再用来训练（音频不删，可以恢复），马上保存并重新统计。"""
    from voicetwin.data import review

    project = open_project(cfg, voice, must_exist=True)
    res = review.delete_clip(project, clip_id)
    res["summary"] = apply_review(cfg, voice, read_csv=False)
    res["csv_locked"] = bool(res.get("csv_locked") or res["summary"].get("csv_locked"))
    return res


def review_restore(cfg: Config, voice: str, clip_id: str) -> Dict[str, Any]:
    """恢复删除的片段，马上保存并重新统计。"""
    from voicetwin.data import review

    project = open_project(cfg, voice, must_exist=True)
    res = review.restore_clip(project, clip_id)
    res["summary"] = apply_review(cfg, voice, read_csv=False)
    res["csv_locked"] = bool(res.get("csv_locked") or res["summary"].get("csv_locked"))
    return res


def run_proofcheck(cfg: Config, voice: str, progress: Optional[ProgressFn] = None, only_kept: bool = True,
                   limit: Optional[int] = None) -> Dict[str, Any]:
    """🔍 自动查找可能的错字：把每段再听一遍，标出可能识别错的字。返回 {checked, flagged, engine, note}。"""
    mod = _proofcheck_module()
    if mod is None:
        raise RuntimeError("查错字功能没有装好（缺少 voicetwin/data/proofcheck.py），请更新声音分身后再试")
    with keep_awake():
        project = open_project(cfg, voice, must_exist=True)
        _report(progress, 0.0, "准备识别引擎（第一次使用会先下载）……")
        res = mod.find_suspects(project, cfg, progress=_sub(progress, 0.02, 0.99), only_kept=only_kept, limit=limit)
        res = dict(res or {})
        _report(progress, 1.0, f"查完了：检查了 {res.get('checked', 0)} 条，其中 {res.get('flagged', 0)} 条可能有错（已标红）")
    return res


TEXTFIX_ONCE_MSG = ("这批素材已经用过「📝 一键全部文字校正」了：每批素材只能用一次，所以按钮是灰色的。"
                    "改好的地方都在下面的表格里，还没保存的请点「保存修改」；还要改的，请用每一行「修改建议」里的按钮，"
                    "或者双击「文字」自己改。以后加了新的素材、识别完，按钮会再亮起来（只改新加的句子）。")


TEXTFIX_NEED_TOOLS_MSG = ("这台电脑上的声音分身没有找到拼音 / 分词工具（pypinyin、jieba），一键全部文字校正只能改很少的一部分。"
                          "每批素材只能用一次，为了不白白用掉这次机会，这次没有开始，什么都没改。"
                          "请重新运行 install_windows.bat、选 1（装进 GPT-SoVITS 整合包，里面有这两个工具），再点这个按钮。")


def run_transcript_fix(cfg: Config, voice: str, files: Optional[Sequence[Any]] = None,
                       progress: Optional[ProgressFn] = None, adopt_all: bool = True,
                       once: bool = False) -> Dict[str, Any]:
    """📝 一键全部文字校正（v18.5）：以母本标准库为准检查校对表的文字，确定的错直接改好；
    adopt_all=True 时再把有把握的修改建议一次全部采用（没把握的留着红色，老师听录音自己点那一行的「采用」）。
    改的都存成没保存的修改（红灯），老师点「保存修改」才生效。

    files：这次上传的母本（txt / transcripts.csv，替换上次上传的）；不给时用上次存的（没有也行，程序自带母本）。
    once=True（网页上的按钮）：每批素材只能用一次（老师的要求）——只改还没用过的句子（新加的素材），别的句子一点不动；
    都用过了就不做（ValueError）；做完记下这些句子用过了，按钮变灰。"""
    from voicetwin.data import transcript_fix

    project = open_project(cfg, voice, must_exist=True)
    only = None
    if once:
        only = transcript_fix.textfix_new_ids(project)
        if not only:
            raise ValueError(TEXTFIX_ONCE_MSG)
        from voicetwin.data.lexicon_fix import has_jieba

        if not (transcript_fix.has_pinyin() and has_jieba()):  # 只能改一点点：不能用掉这批素材唯一的一次
            raise ValueError(TEXTFIX_NEED_TOOLS_MSG)
    if files:
        info = transcript_fix.save_transcripts(project, files)
        _report(progress, 0.01, f"已保存逐字稿：{'、'.join(info['files'])}（共 {info['chars']} 字）")
    res = dict(transcript_fix.check_with_transcript(project, progress=_sub(progress, 0.0, 0.95), only=only) or {})
    from voicetwin.data import review as _review

    _review.clear_undo(project)  # 一键校正以后「撤销刚才的替换」就不是「刚才的」了（会把一键校正前的字改回去）
    if adopt_all:  # 一键全部文字校正：剩下的有把握的修改建议（标准库的、自动查错字的）也一次全部采用
        from voicetwin.data import review

        _report(progress, 0.96, "把有把握的修改建议一次全部采用……")
        res["adopted"] = review.adopt_all_suggestions(project, only=only)
        _report(progress, 1.0, f"校正完了：一共改了 {res.get('fixes', 0) + res['adopted']['changes']} 处")
    if once:  # 做完才记（中途出错 / 停止的不算用过，可以再点）；在后台任务里记，网页关掉了也记得上；
        # 只记真的处理过的句子：检查期间老师又改了的、删除的、标了「不用」的这次没处理，
        # 以后（恢复、改成要用）还能用一次——每一句都只改一次
        handled = list(res.get("handled") or [])
        transcript_fix.mark_textfix_used(project, handled)
        res["only"] = len(only or [])
        res["skipped_edited"] = len(set(only or []) - set(handled))  # 检查期间又改过的（这次没处理，按钮还亮着）
        res["all_rows"] = len(transcript_fix.textfix_eligible_ids(project))
    return res


def textfix_ever_used(cfg: Config, voice: str) -> bool:
    """这个声音用过「一键全部文字校正」没有（按钮下面「已经用过了」的说明只在用过以后才显示）。"""
    from voicetwin.data import transcript_fix

    try:
        project = open_project(cfg, voice, must_exist=True)
    except (ValueError, RuntimeError, OSError):
        return False
    return transcript_fix.textfix_ever_used(project)


def textfix_new_ids(cfg: Config, voice: str) -> List[str]:
    """还没用过「一键全部文字校正」、现在能处理的句子（id）；声音还不存在时是空的。"""
    from voicetwin.data import transcript_fix

    try:
        project = open_project(cfg, voice, must_exist=True)
    except (ValueError, RuntimeError, OSError):
        return []
    return transcript_fix.textfix_new_ids(project)


def textfix_used(cfg: Config, voice: str) -> bool:
    """这个声音现在的素材是不是都用过「一键全部文字校正」了（用过了按钮是灰色的；加了新素材又变成 False）；
    声音还不存在时 False。"""
    from voicetwin.data import transcript_fix

    try:
        project = open_project(cfg, voice, must_exist=True)
    except (ValueError, RuntimeError, OSError):
        return False
    return transcript_fix.textfix_used(project)


def transcript_info(cfg: Config, voice: str) -> Dict[str, Any]:
    """存好的逐字稿：{"files": [...], "chars": n}；声音还不存在时返回空的。"""
    from voicetwin.data import transcript_fix

    try:
        project = open_project(cfg, voice, must_exist=True)
    except (ValueError, RuntimeError, OSError):
        return {"files": [], "chars": 0}
    return transcript_fix.transcript_info(project)


def export_review_text(cfg: Config, voice: str) -> Dict[str, Any]:
    """⬇️ 下载改好的文字（txt）：见 review.export_text。"""
    from voicetwin.data import review

    return review.export_text(open_project(cfg, voice, must_exist=True))


def apply_suggestion(cfg: Config, voice: str, clip_id: str) -> Dict[str, Any]:
    """✅ 采用建议（命令行 / 旧接口）：把"可能有错"的建议改进这条片段的文字（只改建议的那几处），马上保存并重新导出校对表。
    网页的校对表用 review.adopt_suggestion（先存成草稿，老师点保存才写进去）。"""
    project = open_project(cfg, voice, must_exist=True)
    rec = next((r for r in project.load_manifest() if r.get("id") == clip_id), None)
    if rec is None:
        raise ValueError(f"找不到这条片段（{clip_id}），请刷新一下校对表")
    from voicetwin.data.review import analyze, apply_edits

    old = rec.get("text", "")
    info = analyze(rec)
    if not info["edits"]:
        raise ValueError("这条没有可以采用的建议")
    new = project.set_clip_text(clip_id, apply_edits(old, info["edits"]))  # 只改建议的那几处
    log.info(f"已采用建议：{old} → {new.get('text')}")
    out = {"id": clip_id, "old_text": old, "text": new.get("text", ""), "lang": new.get("lang", "")}
    if new.get("csv_locked"):
        log.warning("transcripts.csv 正被别的程序（Excel/WPS）打开，这次没能同步更新；修改已经保存在 manifest 里")
        out["csv_locked"] = True
    return out


def run_analyze(cfg: Config, voice: str) -> Dict[str, Any]:
    from voicetwin.style.profile import build_profile

    return build_profile(open_project(cfg, voice, must_exist=True))


# ---------------------------------------------------------------------------- 训练 / 挑选
def download_models(cfg: Config, source: str = "auto", progress: Optional[ProgressFn] = None) -> List[str]:
    """下载 GPT-SoVITS 缺少的预训练模型（网页的「⬇️ 下载缺少的模型」和命令行 download-models 共用）。

    要下 1~2 GB，网慢时很久：下载期间电脑不会自动睡眠（网络流量不会让 Windows 觉得「有人在用」）。"""
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    from voicetwin.eval import sv_models

    with keep_awake():
        project = Project(cfg, "__download__")
        try:
            backend = GPTSoVITSBackend(cfg, project)
            files = list(backend.download_pretrained(source, progress=_sub(progress, 0.0, 0.85)) or [])
        finally:
            shutil.rmtree(project.root, ignore_errors=True)
        # 精准声纹打分的模型（约 170 MB）：下载失败不影响 GPT-SoVITS 的模型，只是先用旧的打分方式
        try:  # 停止按钮的 TaskCancelled 是 BaseException，照常传出去
            files += sv_models.download(cfg, progress=_sub(progress, 0.85, 1.0))
        except Exception as exc:
            log.warning(f"⚠️ 精准声纹打分的模型没有下载成功（{exc}）。先用旧的打分方式；以后再点一次「⬇️ 下载缺少的模型」就行")
        return files


def run_train(cfg: Config, voice: str, backend_name: Optional[str] = None, progress: Optional[ProgressFn] = None,
              select: bool = True, **opts: Any) -> Dict[str, Any]:
    from voicetwin.backends.base import get_backend

    with keep_awake():
        project = open_project(cfg, voice, must_exist=True)
        backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
        if not backend.supports_training:
            raise RuntimeError(f"{backend.display_name} 不需要训练（零样本克隆），可以直接合成")
        _check_material_before_training(project)
        t0 = time.time()
        info = backend.train(progress=_sub(progress, 0.0, TRAIN_SELECT_SPLIT) if select else progress, **opts)
        info["train_minutes"] = round((time.time() - t0) / 60.0, 1)
        if select:
            _report(progress, TRAIN_SELECT_SPLIT, "训练完成，开始自动挑选最像你的模型（大约 5~15 分钟）")
            t_select = time.time()
            try:
                selection = run_select(cfg, voice, backend.name, progress=_sub(progress, TRAIN_SELECT_SPLIT, 1.0))
                info["selection"] = selection
                if selection.get("selected"):
                    info["selected"] = selection["selected"]
            except Exception as exc:  # 训练已经成功了：不能显示成失败（停止按钮的 TaskCancelled 照常传出去）
                reason = _explain_title(exc)
                log.warning(f"⚠️ 训练已经成功完成并保存了，只是「自动挑选最像你的模型」这一步没成功（{reason}）。"
                            "现在先用最后一轮的模型；可以稍后在「② 训练模型」页点「重新挑选最佳模型」再试。", exc_info=exc)
                info["selection_error"] = reason
                info["selection_error_detail"] = repr(exc)[:500]
                from voicetwin.report import report_failure

                path = report_failure(exc, what="训练后自动挑选最像你的模型", voice=voice, logs_dir=project.logs_dir,
                                      since=t_select)
                if path is not None:
                    info["selection_error_report"] = str(path)
        _report(progress, 1.0, "训练完成")
    return info


def training_blocker(project: Project) -> str:
    """还不能开始训练的原因（空字符串 = 可以训练）。

    老师的要求（10-02）：
    - 绝对不能用没改好的文字训练 → 还有没保存的修改时不训练（直接训练会用改之前的旧文字）；
    - 必须先点「✅ 确认训练素材」才能训练 → 没确认过、或者确认以后又改过（改字、删除、撤销删除）时不训练。"""
    from voicetwin.data import review

    n = review.unsaved_count(project)
    if n:
        return (f"校对表里还有 {n} 条修改没有保存，这次没有开始训练（没保存的修改不会用来训练，"
                "直接训练就会用改之前的旧文字）。")
    records = project.load_manifest()
    conf = review.load_confirmed(project)
    if not conf:
        return ("还没有确认训练素材，这次没有开始训练（必须先在校对表下面点「✅ 确认训练素材」；"
                "用命令行的话运行 voicetwin confirm）。")
    if not review.confirmed_matches(conf, records):
        return ("确认训练素材以后，校对表又改过（改了文字、删除或撤销删除了句子），这次没有开始训练"
                f"（上次确认是 {str(conf.get('time') or '')[5:16]}；用命令行的话再运行一次 voicetwin confirm）。")
    return ""


def training_blocker_for(cfg: Config, voice: str) -> str:
    try:
        return training_blocker(open_project(cfg, voice, must_exist=True))
    except Exception:
        return ""


def _check_material_before_training(project: Project) -> None:
    """训练只用校对表里「保存」并「确认」过的文字（manifest），删除的句子不用；不满足就不开始（training_blocker），
    满足时在「详细过程」里写清楚这次用了哪些句子。"""
    from voicetwin.data.exporters import train_records

    why = training_blocker(project)
    if why:
        raise RuntimeError(why)
    records = project.load_manifest()
    material = train_records(project, include_val=True)
    val = sum(1 for r in material if r.get("split") == "val")
    edited = sum(1 for r in material if r.get("text_edited")
                 or (r.get("orig_text") is not None and r.get("orig_text") != r.get("text")))
    deleted = sum(1 for r in records if r.get("deleted"))
    log.info(f"这次训练用校对表里保存好的文字：{len(material) - val} 条训练、{val} 条当「考试题」"
             + (f"；其中 {edited} 条是你改过文字的，按改好的文字训练" if edited else "")
             + (f"；你删除的 {deleted} 条（音频和文字）都不用" if deleted else ""))


def material_changed_note(cfg: Config, voice: str, backend_name: Optional[str] = None) -> str:
    """校对表在上次训练以后又改过（文字、删除、恢复）时返回一句提醒；没训练过、没变、判断不了时返回空字符串。"""
    from voicetwin.backends.base import get_backend

    try:
        project = open_project(cfg, voice, must_exist=True)
        backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
        fn = getattr(backend, "trained_material_note", None)
        return str(fn() or "") if fn else ""
    except Exception:
        return ""


def run_select(cfg: Config, voice: str, backend_name: Optional[str] = None, items: Optional[int] = None,
               use_asr: Optional[bool] = None, progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    from voicetwin.backends.base import get_backend
    from voicetwin.synth.select import DEFAULT_ITEMS, select_and_calibrate

    with keep_awake():
        project = open_project(cfg, voice, must_exist=True)
        backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
        note = getattr(backend, "trained_material_note", lambda: "")()
        if note:
            log.warning(note)
        try:  # 引擎在 select_and_calibrate 里"启动合成引擎"那一步才启动，进度条上能看到
            return select_and_calibrate(cfg, project, backend, max_items=int(items or DEFAULT_ITEMS), use_asr=use_asr,
                                        progress=progress)
        finally:
            backend.stop()


# ---------------------------------------------------------------------------- 合成
def default_output(project: Project, stem: str, fmt: str) -> Path:
    from voicetwin.utils.textutil import safe_name

    return project.outputs_dir / f"{safe_name(stem, 30)}_{time.strftime('%Y%m%d_%H%M%S')}.{fmt}"


def recommended_quality(tier: Optional[str] = None) -> Tuple[str, str]:
    """网页「质量」的默认值和一句说明（按显卡：≥8GB → 完美；更小 → 极致；没有能用的显卡 → 均衡）。"""
    from voicetwin.synth.engine import recommended_quality as _rec

    return _rec(tier)


def quality_choices() -> List[Tuple[str, str]]:
    """网页「质量」单选框的 (中文标签, 值)，从快到慢；每档的一行说明见 quality_help()。"""
    from voicetwin.synth.engine import quality_choices as _choices

    return _choices()


def quality_help() -> Dict[str, str]:
    from voicetwin.synth.engine import QUALITY_HELP, QUALITY_NOTE

    return {**QUALITY_HELP, "note": QUALITY_NOTE}


def run_narrate(cfg: Config, voice: str, source: str, out: Optional[str] = None, backend_name: Optional[str] = None,
                quality: Optional[str] = None, candidates: Optional[int] = None, speed: Any = None,
                reference: str = "", redo: Iterable[int] = (), subtitles: Optional[bool] = None,
                asr_check: Optional[bool] = None, progress: Optional[ProgressFn] = None, backend=None,
                variants: Optional[bool] = None):
    from voicetwin.backends.base import get_backend
    from voicetwin.synth.engine import Narrator

    source = str(source or "")
    if not source.strip():
        raise ValueError("讲稿里没有可以朗读的内容")
    with keep_awake():
        project = open_project(cfg, voice, must_exist=True)
        fmt = cfg.get("synth", {}).get("output_format", "wav")
        src_path = _script_file(source)
        is_file = src_path is not None
        if is_file:
            stem = src_path.stem
        else:
            stem = source.strip().splitlines()[0][:20] if source.strip() else "output"
        out_path = Path(out) if out else default_output(project, stem, fmt)
        own_backend = backend is None
        backend = backend or get_backend(backend_name or cfg.get("backend"), cfg, project)
        note = getattr(backend, "trained_material_note", lambda: "")()
        if note:
            log.warning(note)
        try:
            narrator = Narrator(cfg, project, backend, quality=quality, candidates=candidates, speed=speed,
                                reference=reference, asr_check=asr_check, progress=progress, variants=variants)
            return narrator.narrate(src_path if is_file else source, out_path, redo=redo, subtitles=subtitles)
        finally:
            if own_backend:
                backend.stop()


def _script_file(source: str) -> Optional[Path]:
    """讲稿框里填的是文件路径（.txt / .docx）就返回路径，否则（是讲稿文字）返回 None。

    一行很长、里面有「.」的讲稿（比如「Python 3.9」、英文句子）不能当路径去问硬盘：
    Linux / Mac 上会报「文件名太长」（OSError），以前老师会看到「安装路径太长」之类不相干的提示。
    """
    text = source.strip()
    if not text or len(text) >= 1024 or "\n" in text:
        return None
    try:
        path = Path(text)
        return path if path.suffix and path.is_file() else None
    except (OSError, ValueError):
        return None


def narration_table(segments: Sequence[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
    """逐句结果表：(表头, 行)，表头 #, 句子, 像你本人（%）, 状态, 提示；# 从 1 开始，和「重做」填的编号一样。"""
    from voicetwin.synth.engine import RESULT_HEADERS, result_rows

    return list(RESULT_HEADERS), result_rows(segments)


def _variant_match(variants: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    want = str(name or "").strip()
    if not want:
        return None
    for v in variants:  # 先精确匹配名字（「去杂音」是「未去杂音」的一部分，不能用包含）
        if want == v.get("name") or want == v.get("label"):
            return v
    letter = want.upper().replace("版本", "").strip()
    if len(letter) == 1 and "A" <= letter <= "Z":
        idx = ord(letter) - ord("A")
        return variants[idx] if idx < len(variants) else None
    for v in variants:
        label = str(v.get("label") or "")
        if label and (want in label or label in want):
            return v
    return None


def choose_variant(cfg: Config, voice: str, report_path: str, name: str) -> Dict[str, Any]:
    """「完美」档的两个版本里，选一个作为最终版本：把它复制成 <名字>.wav，并在报告里记下 final。"""
    open_project(cfg, voice, must_exist=True)
    rp = Path(str(report_path))
    if not rp.exists():
        raise FileNotFoundError(f"找不到这次生成的报告：{rp}")
    report = json.loads(rp.read_text(encoding="utf-8"))
    variants = list(report.get("variants") or [])
    if not variants:
        raise ValueError("这次生成只有一个版本，不用选")
    v = _variant_match(variants, name)
    if v is None:
        names = "、".join(str(x.get("name")) for x in variants)
        raise ValueError(f"没有「{name}」这个版本，可以选：{names}")
    src = Path(str(v.get("path") or ""))
    dst = Path(str(report.get("audio") or ""))
    if not src.exists():
        raise FileNotFoundError(f"找不到「{v.get('name')}」的音频文件：{src}")
    if not dst.name:
        raise ValueError("报告里没有最终音频的位置")
    if src.resolve() != dst.resolve():
        shutil.copyfile(src, dst)
    for x in variants:
        x["final"] = x is v
    report["variants"] = variants
    report["final"] = v.get("name")
    if v.get("pct") is not None:  # 整篇百分比跟着最终版本走（和生成时的规则一样）
        report["overall_pct"] = v.get("pct")
    from voicetwin.utils import atomic

    atomic.write_text(rp, json.dumps(report, ensure_ascii=False, indent=1))
    log.info(f"最终版本改成「{v.get('name')}」：{dst}")
    return {"final": v.get("name"), "audio": str(dst), "variants": variants, "report": str(rp)}


# ---------------------------------------------------------------------------- 语速
def slider_to_speed(value: Any) -> float:
    """语速滑块（−30…+30，往左更快）→ 语速倍数：1 − value/100（−20 → 1.20 快 20%；+15 → 0.85 慢 15%）。"""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        v = 0.0
    v = max(float(SPEED_SLIDER_MIN), min(float(SPEED_SLIDER_MAX), v))
    return round(1.0 - v / 100.0, 4)


def speed_note(value: Any) -> str:
    """滑块下面那一行：当前：和你原声一样 / 比你原声快 20% / 比你原声慢 15%。"""
    try:
        v = int(round(float(value or 0)))
    except (TypeError, ValueError):
        v = 0
    v = max(SPEED_SLIDER_MIN, min(SPEED_SLIDER_MAX, v))
    if v == 0:
        text = "当前：和你原声一样"
    elif v < 0:
        text = f"当前：比你原声快 {-v}%"
    else:
        text = f"当前：比你原声慢 {v}%"
    if abs(v) > 20:
        text += "（太极端可能不自然，建议在 −15～+15 之间）"
    return text


def _first_sentence(cfg: Config, project: Project, text: str) -> str:
    from voicetwin.synth.script import parse_script

    text = str(text or "").strip()
    if text:
        try:
            segs = parse_script(text, lexicon=())
            if segs:
                return segs[0].display
        except Exception:
            pass
    langs = {r.get("lang") for r in project.load_references()}
    return DEFAULT_SAMPLE_ZH if ("zh" in langs or not langs) else DEFAULT_SAMPLE_EN


def preview_speed(cfg: Config, voice: str, text: str = "", value: Any = 0, backend_name: Optional[str] = None,
                  progress: Optional[ProgressFn] = None, backend=None):
    """▶ 试听语速：用「快速」档把讲稿第一句（或一句默认的话）按选的快慢读一遍。"""
    project = open_project(cfg, voice, must_exist=True)
    sentence = _first_sentence(cfg, project, text)
    speed = slider_to_speed(value)
    v = int(round((1.0 - speed) * 100))
    tag = "原速" if v == 0 else (f"快{-v}%" if v < 0 else f"慢{v}%")
    out = project.outputs_dir / f"试听语速_{tag}.wav"
    return run_narrate(cfg, voice, sentence, out=str(out), backend_name=backend_name, quality="fast", speed=speed,
                       subtitles=False, progress=progress, backend=backend, variants=False)


# ---------------------------------------------------------------------------- 鉴别：盲听测试
_REAL, _GEN = "真人", "生成"
#: 答案文件放在测试文件夹「旁边」，不放在里面：老师会把整个文件夹发给听众
BLIND_ANSWER_SUFFIX = "_答案（只给老师看，不要发给听众）.json"


def blind_answer_path(test_dir: Any) -> Path:
    """盲听测试的答案文件：<文件夹名>_答案（只给老师看，不要发给听众）.json，和文件夹放在一起。
    以前的版本把 答案.json 放在文件夹里面，也认。"""
    d = Path(str(test_dir))
    side = d.with_name(d.name + BLIND_ANSWER_SUFFIX)
    if side.exists() or not (d / "答案.json").exists():
        return side
    return d / "答案.json"


def list_blind_tests(cfg: Config, voice: str) -> List[Dict[str, Any]]:
    """这个声音做过的盲听测试（有答案文件的），新的在前：[{dir, name, count, created}]。"""
    project = open_project(cfg, voice, must_exist=True)
    out: List[Dict[str, Any]] = []
    if not project.outputs_dir.is_dir():
        return out
    for d in project.outputs_dir.iterdir():
        if not d.is_dir() or not d.name.startswith("盲听测试_"):
            continue
        ap = blind_answer_path(d)
        if not ap.exists():
            continue
        try:
            data = json.loads(ap.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({"dir": str(d), "name": d.name, "count": int(data.get("count") or len(data.get("items") or [])),
                    "created": str(data.get("created") or "")})
    out.sort(key=lambda x: x["name"], reverse=True)
    return out


_HINT_RE = re.compile(r"[（(]\s*真人\s*[/／|｜]\s*生成\s*[）)]")
_PAIR_RE = re.compile(r"(\d+)\s*[.、:：)）\]】\-—=]*\s*([^\d\s,，;；.、:：]+)")


def parse_blind_answers(text: Any) -> Any:
    """把老师贴进来的听众答案变成 grade_blind_test 认识的格式。认这几种写法：
    「1 真人 2 生成 3 真人」「1.真人 2.生成」「1真2假」、照着答题卡填的「01. 真人（真人 / 生成）」，
    或者不写编号、按顺序写「真人 生成 真人」。返回 {编号: 答案} 或按顺序的列表。"""
    s = _HINT_RE.sub(" ", str(text or ""))
    pairs: Dict[int, str] = {}
    for m in _PAIR_RE.finditer(s):
        word = m.group(2).strip("_＿-—（）()")
        if _norm_answer(word):
            pairs[int(m.group(1))] = word
    if pairs:
        return pairs
    words = [w for w in re.split(r"[\s,，;；、/／|｜]+", s) if w]
    return [w for w in words if _norm_answer(w)]


def _blind_pool(project: Project, n: int) -> List[Dict[str, Any]]:
    from voicetwin.eval.speaker import spread_sample

    recs = [r for r in project.load_manifest(only_kept=True) if r.get("text")]
    ref_ids = {r["id"] for r in project.load_references()}
    pool = [r for r in recs if r.get("split") == "val"]
    if len(pool) < n:
        extra = [r for r in recs if r.get("split", "train") != "val" and r["id"] not in ref_ids
                 and 2.5 <= float(r.get("duration", 0)) <= 10.0]
        pool += spread_sample(sorted(extra, key=lambda r: r["id"]), n - len(pool))
    return spread_sample(sorted(pool, key=lambda r: r["id"]), n)


def build_blind_test(cfg: Config, voice: str, n: int = 10, quality: Optional[str] = None,
                     backend_name: Optional[str] = None, progress: Optional[ProgressFn] = None, backend=None,
                     seed: Optional[int] = None) -> Dict[str, Any]:
    """观众盲听测试：挑 n 段你的真实录音（优先验证集），用现在最好的模型读同样的文字，
    统一音量后打乱顺序，存成 outputs/盲听测试_<时间>/01.wav…，还有一份 听众答题卡.txt，整个文件夹可以直接发给听众。
    答案放在文件夹旁边的 盲听测试_<时间>_答案（只给老师看，不要发给听众）.json（网页提交前不显示）。
    返回的 items 里不含答案。"""
    from voicetwin.backends.base import get_backend
    from voicetwin.synth.engine import QUALITY_SHORT, Narrator, trim_edges
    from voicetwin.utils.audio import load_audio, normalize_lufs, resample, save_audio

    n = max(2, min(int(n or 10), 50))
    with keep_awake():
        project = open_project(cfg, voice, must_exist=True)
        _report(progress, 0.0, "挑选你的真实录音（没参与训练的那部分）……")
        pool = _blind_pool(project, n)
        if len(pool) < 2:
            raise RuntimeError("真实录音太少，做不了盲听测试（至少要 2 段完整的话）")
        real_ids = {r["id"] for r in pool}
        own = backend is None
        backend = backend or get_backend(backend_name or cfg.get("backend"), cfg, project)
        pieces: List[Tuple[str, Dict[str, Any], Any, int, Optional[float]]] = []
        try:
            narrator = Narrator(cfg, project, backend, quality=quality, variants=False)
            narrator.refs = [r for r in narrator.refs if r["id"] not in real_ids] or narrator.refs
            for k, rec in enumerate(pool):
                _check_cancel()
                lo = 0.05 + 0.85 * k / len(pool)
                hi = 0.05 + 0.85 * (k + 1) / len(pool)
                _report(progress, lo, f"生成第 {k + 1}/{len(pool)} 句：{rec['text'][:20]}")
                narrator.progress = _sub(progress, lo, hi)
                wav, sr, results = narrator.synthesize_text(rec["text"])
                pct = results[0].pct if len(results) == 1 else None
                real, rsr = load_audio(project.abspath(rec["path"]))
                pieces.append((_REAL, rec, real, rsr, None))
                pieces.append((_GEN, rec, wav, sr, pct))
        finally:
            if own:
                backend.stop()
        _report(progress, 0.90, "统一音量、打乱顺序、保存……")
        out_sr = min(p[3] for p in pieces)  # 统一成较低的采样率，避免"音质高低"泄露答案
        rng = random.Random(seed if seed is not None else time.time_ns())
        order = list(range(len(pieces)))
        rng.shuffle(order)
        out_dir = project.outputs_dir / f"盲听测试_{time.strftime('%Y%m%d_%H%M%S')}"
        out_dir.mkdir(parents=True, exist_ok=True)
        answers, items = [], []
        width = max(2, len(str(len(order))))
        for no, idx in enumerate(order, 1):
            kind, rec, wav, sr, pct = pieces[idx]
            w = trim_edges(resample(wav, sr, out_sr), out_sr)  # 真人和生成的首尾做一样的处理
            w = normalize_lufs(w, out_sr, -20.0, ceiling_db=-1.0)
            name = f"{no:0{width}d}.wav"
            save_audio(out_dir / name, w, out_sr)
            items.append({"no": no, "file": name, "path": str(out_dir / name)})
            answers.append({"no": no, "file": name, "truth": kind, "text": rec["text"], "clip": rec["id"],
                            "pct": pct})
        quality_name = narrator.quality
        data = {"created": time.strftime("%Y-%m-%d %H:%M"), "voice": project.voice, "quality": quality_name,
                "count": len(items), "items": answers}
        answer_path = out_dir.with_name(out_dir.name + BLIND_ANSWER_SUFFIX)
        answer_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        card_lines = [f"听众答题卡（共 {len(items)} 段）", "",
                      "每段听完，在后面写「真人」或「生成」。只听一遍，凭第一感觉写，不要回头改。", ""]
        card_lines += [f"{it['no']:0{width}d}. ________（真人 / 生成）" for it in items]
        card_lines += ["", "答完后把答案交给老师：老师在「⑤ 鉴别」页的「批改收上来的答题卡」里选这次测试、"
                           "把答案填进去，就能看到正确率。"]
        card_path = out_dir / "听众答题卡.txt"
        card_path.write_text("\n".join(card_lines) + "\n", encoding="utf-8-sig")
        _report(progress, 1.0, f"盲听测试做好了：共 {len(items)} 段（{len(pool)} 段真人 + {len(pool)} 段生成），"
                               f"质量「{QUALITY_SHORT.get(quality_name, quality_name)}」")
    return {"dir": str(out_dir), "items": items, "count": len(items), "answer_path": str(answer_path),
            "card_path": str(card_path), "n_real": len(pool), "n_generated": len(pool), "quality": quality_name}


def _norm_answer(ans: Any) -> str:
    s = str(ans or "").strip().lower()
    if not s:
        return ""
    if s in ("真人", "真", "人", "real", "r", "human", "h", "原声", "本人"):
        return _REAL
    if s in ("生成", "合成", "假", "机器", "ai", "fake", "g", "gen", "generated", "tts", "克隆"):
        return _GEN
    if "真" in s or "本人" in s:
        return _REAL
    if "生成" in s or "合成" in s or "机器" in s:
        return _GEN
    return ""


def grade_blind_test(test_dir: str, answers: Any) -> Dict[str, Any]:
    """批改盲听测试。answers 可以是 {编号: '真人'/'生成'}，也可以是按顺序的列表。"""
    path = Path(str(test_dir))
    answer_file = blind_answer_path(path) if path.is_dir() else path
    if not answer_file.exists():
        raise FileNotFoundError(f"找不到这次盲听测试的答案文件：{answer_file.name}")
    data = json.loads(answer_file.read_text(encoding="utf-8"))
    if isinstance(answers, str):
        answers = parse_blind_answers(answers)
    items = data.get("items") or []
    if isinstance(answers, (list, tuple)):
        given_map = {i + 1: a for i, a in enumerate(answers)}
    else:
        given_map = {}
        for k, v in dict(answers or {}).items():
            try:
                given_map[int(str(k).strip().lstrip("0") or 0)] = v
            except ValueError:
                continue
    rows, correct, answered = [], 0, 0
    for it in items:
        given = _norm_answer(given_map.get(int(it["no"])))
        ok = bool(given) and given == it["truth"]
        answered += 1 if given else 0
        correct += 1 if ok else 0
        rows.append({"no": it["no"], "file": it.get("file"), "answer": given or "（没答）", "truth": it["truth"],
                     "correct": ok, "text": it.get("text", "")})
    acc = correct / answered if answered else None
    tips: List[str] = []
    if acc is None:
        verdict = "还没有填答案"
    elif acc <= 0.60:
        verdict = f"听众基本分辨不出（正确率 {acc:.0%}，和瞎猜的 50% 差不多）"
    elif acc <= 0.80:
        verdict = f"有时能分辨（正确率 {acc:.0%}）"
        tips = ["看看哪几段最容易被听出来，是语气、停顿还是个别字不像", "用「完美」档重新生成那几句"]
    else:
        verdict = f"容易分辨（正确率 {acc:.0%}）"
        tips = ["多加一些干净的讲课录音（1~3 小时最好），重新准备素材和训练",
                "在「① 准备素材」的校对表里把文字校对一遍（错字会让模型学歪）",
                "生成时用「完美」档", "看看哪几段最容易被听出来，是语气、停顿还是个别字不像"]
    if answered and answered < 6:
        verdict += "（题目太少，结果只能参考）"
    return {"items": rows, "answered": answered, "correct": correct, "total": len(items),
            "accuracy": None if acc is None else round(acc, 4), "pct": None if acc is None else round(acc * 100, 1),
            "verdict": verdict, "tips": tips}


# ---------------------------------------------------------------------------- 鉴别：机器打分
def verify_defaults(cfg: Config, voice: str, max_clips: int = 20) -> Dict[str, List[str]]:
    """「机器鉴别」默认要比的文件：原声 = 验证集里的真实录音；生成 = 最近一次生成的各个版本和逐句音频。"""
    project = open_project(cfg, voice, must_exist=True)
    originals = [str(project.abspath(r["path"])) for r in project.load_manifest(only_kept=True)
                 if r.get("split") == "val"][:10]
    generated: List[str] = []
    reports = sorted(project.outputs_dir.glob("*.report.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if reports:
        try:
            rep = json.loads(reports[0].read_text(encoding="utf-8"))
            for v in rep.get("variants") or []:
                if v.get("path") and Path(v["path"]).exists():
                    generated.append(str(v["path"]))
            if not generated and rep.get("audio") and Path(rep["audio"]).exists():
                generated.append(str(rep["audio"]))
            for s in (rep.get("segments") or [])[:max_clips]:
                clip = s.get("clip")
                if clip and project.abspath(clip).exists():
                    generated.append(str(project.abspath(clip)))
        except Exception:
            pass
    return {"originals": originals, "generated": generated}


def verify_files(cfg: Config, voice: str, generated: Sequence[str], originals: Optional[Sequence[str]] = None,
                 progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    """机器鉴别：给每个生成的文件打"像你本人（%）"（几个声纹模型分别打分再平均），按分数排名。

    originals 是你挑的原声（≥3 段时用它们当标准；1~2 段时用素材里留出的真实录音和它们比来校准；
    不选就用这个声音的验证集校准）。返回的 calibration_source 说明「100%」的标准实际是怎么来的。
    """
    from voicetwin.eval.speaker import HONEST_NOTE, PCT_HELP, SimilarityJudge, model_label

    project = open_project(cfg, voice, must_exist=True)
    gen = [Path(str(p)) for p in (generated or []) if p and Path(str(p)).exists()]
    if not gen:
        raise ValueError("请先选择或上传要鉴别的生成音频")
    min_pct = float((cfg.get("similarity") or {}).get("min_pct", 85) or 85)
    with keep_awake():
        _report(progress, 0.0, "加载声纹模型，计算你本人的声音标准……")
        base = SimilarityJudge.for_project(cfg, project)
        orig = [Path(str(p)) for p in (originals or []) if p and Path(str(p)).exists()]
        if orig:
            judge = SimilarityJudge.from_files(cfg, orig, fallback=base,
                                               encoders=[m.encoder for m in base.members] or None, project=project)
        else:
            judge = base
        if not judge.available:
            raise RuntimeError("没有可用的声纹模型，没法打分")
        rows: List[Dict[str, Any]] = []
        for k, p in enumerate(gen):
            _check_cancel()
            _report(progress, 0.10 + 0.88 * k / len(gen), f"打分 {k + 1}/{len(gen)}：{p.name}")
            res = judge.judge_file(p)
            pct = res.get("pct")
            rows.append({"file": p.name, "path": str(p), "pct": pct, "pcts": dict(res.get("pcts") or {}),
                         "sims": dict(res.get("sims") or {}), "pass": bool(pct is not None and pct >= min_pct)})
    ranked = sorted(rows, key=lambda r: (r["pct"] is None, -(r["pct"] or 0.0)))
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    names = judge.models
    labels = [model_label(n) for n in names]
    headers = ["#", "文件"] + [f"{lab}（%）" for lab in labels] + ["综合（%）", "排名", f"是否 ≥{min_pct:.0f}%"]
    table = []
    for i, r in enumerate(ranked, 1):
        per = [("" if r["pcts"].get(n) is None else f"{r['pcts'][n]:.1f}") for n in names]
        table.append([i, r["file"]] + per + ["" if r["pct"] is None else f"{r['pct']:.1f}", r["rank"],
                                             "✅ 是" if r["pass"] else "🔴 否"])
    _report(progress, 1.0, f"打分完成：共 {len(rows)} 个文件，{sum(1 for r in rows if r['pass'])} 个达到 {min_pct:.0f}%")
    return {"rows": ranked, "headers": headers, "table": table, "count": len(rows), "models": judge.info(),
            "originals": [p.name for p in orig], "calibrated": judge.calibrated, "min_pct": min_pct,
            "calibration_source": _calib_source(judge),
            "definition": PCT_HELP, "note": HONEST_NOTE}


def _calib_source(judge: Any) -> str:
    """几个声纹模型的「100%」标准是怎么来的（都一样时返回那一种；不一样时返回 mixed）。"""
    sources = {str((m.calib or {}).get("source") or "") for m in getattr(judge, "members", []) if m.p50 is not None}
    if not sources:
        return ""
    return sources.pop() if len(sources) == 1 else "mixed"


# ---------------------------------------------------------------------------- 一条龙
def run_auto(cfg: Config, voice: str, inputs: Iterable[str], backend_name: Optional[str] = None,
             skip_train: bool = False, progress: Optional[ProgressFn] = None) -> Dict[str, Any]:
    """一条龙：素材准备 → 风格分析 → 训练 → 挑最佳模型 → 生成试听。"""
    from voicetwin.backends.base import get_backend

    with keep_awake():
        result: Dict[str, Any] = {"prepare": run_prepare(cfg, voice, inputs, _sub(progress, 0.0, 0.25))}
        review_confirm(cfg, voice)  # 全自动：没有人工校对这一步，准备好的素材直接确认（不然训练不会开始）
        project = open_project(cfg, voice, must_exist=True)
        backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
        if backend.supports_training and not skip_train:
            result["train"] = run_train(cfg, voice, backend.name, _sub(progress, 0.25, 0.9), select=True)
        else:
            result["selection"] = run_select(cfg, voice, backend.name, progress=_sub(progress, 0.25, 0.9))
        demo = []
        refs = project.load_references()
        if any(r["lang"] == "zh" for r in refs):
            demo.append("大家好，欢迎来到今天的课程。今天我们要讲的内容非常重要，大家一定要认真听。")
        if any(r["lang"] == "en" for r in refs) or not demo:
            demo.append("Hello everyone, welcome back. Today we're going to learn something really useful.")
        res = run_narrate(cfg, voice, "\n\n".join(demo), out=str(project.outputs_dir / "试听_demo.wav"),
                          backend_name=backend.name, progress=_sub(progress, 0.9, 1.0))
        result["demo"] = str(res.audio_path)
    return result


# ---------------------------------------------------------------------------- 环境检查
def nvidia_smi_status(returncode: int, output: str) -> Tuple[bool, str]:
    """把 nvidia-smi 的结果翻译成（是否正常, 说明）。驱动没装好时它也会输出一段报错文字，不能当成正常。"""
    text = (output or "").strip()
    if returncode != 0 or not text or "failed" in text.lower() or "error" in text.lower():
        first = text.splitlines()[0][:160] if text else "没有输出"
        return False, (f"显卡驱动没有正常工作（{first}）。请到 https://www.nvidia.cn/drivers/lookup/ "
                       "下载安装最新驱动，然后重启电脑")
    return True, text


def _gpu_row() -> Optional[Tuple[Optional[bool], str]]:
    """用 U9 的 gpu_status 检查显卡；没有它时返回 None（退回旧的 nvidia-smi 检查）。"""
    try:
        from voicetwin.utils.gpu import gpu_status
    except ImportError:
        return None
    try:
        st = gpu_status(refresh=True)
    except Exception:
        return None
    level = st.get("level")
    ok: Optional[bool] = True if level == "ok" else (None if level == "warn" else False)
    detail = str(st.get("message") or "")
    if st.get("advice"):
        detail += "。怎么办：" + str(st["advice"])
    return ok, detail


def sv_status(cfg: Config) -> Tuple[Optional[bool], str]:
    """精准声纹打分（"像你本人"百分比）用的模型齐不齐：(True/None, 说明)。缺了不影响使用，只是退回旧的打分方式。"""
    from voicetwin.eval import sv_models
    from voicetwin.eval.speaker import COHORT_FILE

    try:
        import onnxruntime  # noqa: F401
    except Exception:
        return None, ("没有安装 onnxruntime，「像你本人（%）」只能用旧的打分方式（准确度低一些）。"
                      "怎么办：重新双击 install_windows.bat 安装一次")
    need = sv_models.missing(cfg)
    if need:
        mb = sum(m.size or (52 << 20) for m in need) / (1 << 20)
        return None, (f"还缺 {len(need)} 个模型（约 {mb:.0f} MB）：" + "、".join(m.label for m in need)
                      + "。现在用旧的打分方式（准确度低一些）。怎么办：点「⬇️ 下载缺少的模型」，"
                      "或运行 voicetwin download-models")
    if not COHORT_FILE.exists():
        return None, "陌生人声纹库（sv_cohort.npz）不见了，百分比只能按旧方式换算。怎么办：重新下载安装 VoiceTwin"
    labels = [sv_models.MODELS[k].label.split("（")[0] for k in sv_models.ensemble_keys(cfg) if k in sv_models.MODELS]
    return True, "已就绪：" + " + ".join(labels) + f"（模型在 {sv_models.model_dir(cfg)}）"


def doctor(cfg: Config) -> List[Dict[str, Any]]:
    # 整合包里的第三方库（funasr、rotary_embedding_torch 等）导入时会打印英文警告（SyntaxWarning、FutureWarning），
    # 夹在检查结果前面看着像出错，其实不影响使用：检查期间不显示
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _doctor(cfg)


def _doctor(cfg: Config) -> List[Dict[str, Any]]:
    from voicetwin.backends.base import available_backends, get_backend

    rows: List[Dict[str, Any]] = []

    def add(item: str, ok: Optional[bool], detail: str, optional: bool = False) -> None:
        rows.append({"item": item, "status": "✅" if ok else ("⚠️" if ok is None else "❌"), "detail": detail,
                     "optional": bool(optional)})

    add("Python", sys.version_info >= (3, 9), f"{platform.python_version()}（{platform.system()} {platform.machine()}）")
    try:
        from voicetwin.utils.ffmpeg import find_ffmpeg

        add("ffmpeg", True, find_ffmpeg())
    except Exception as exc:
        add("ffmpeg", False, str(exc))
    for mod, label, required, optional in (
        ("numpy", "numpy", True, False), ("scipy", "scipy", True, False), ("soundfile", "soundfile", True, False),
        ("librosa", "librosa", True, False), ("pyloudnorm", "pyloudnorm", True, False),
        ("faster_whisper", "faster-whisper（语音识别）", False, False),
        ("funasr", "funasr（中文识别、查错字，可选）", False, True),
        ("resemblyzer", "resemblyzer（声纹打分）", False, False), ("gradio", "gradio（网页界面）", False, False),
        ("noisereduce", "noisereduce（降噪、「完美」档的去杂音版本，可选）", False, True),
        ("demucs", "demucs（去背景音乐，可选）", False, True),
    ):
        try:
            m = importlib.import_module(mod)
            add(label, True, getattr(m, "__version__", "已安装"), optional)
        except Exception:
            hint = "（必需）" if required else ("（重新双击 install_windows.bat 安装一次就会装上）"
                                              if mod == "noisereduce" else "")
            add(label, False if required else None, "未安装" + hint, optional)
    gpu = _gpu_row()
    if gpu is not None:
        add("NVIDIA 显卡", gpu[0], gpu[1])
    else:
        smi = shutil.which("nvidia-smi")
        if smi:
            try:
                proc = subprocess.run([smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
                add("NVIDIA 显卡", *nvidia_smi_status(proc.returncode, proc.stdout.decode("utf-8", errors="replace")))
            except Exception as exc:
                add("NVIDIA 显卡", None, str(exc))
        else:
            add("NVIDIA 显卡", None, "没有找到 nvidia-smi（没有 N 卡时只能用 CPU，训练会非常慢）")
    try:  # 整合包环境里有 PyTorch：直接确认训练能不能用上显卡
        import torch  # type: ignore

        # 只有装在 GPT-SoVITS 整合包里（runtime\python.exe）时，这里的 torch 才是训练要用的那个
        in_gsv_runtime = (Path(sys.executable).resolve().parent.parent / "api_v2.py").exists()
        if torch.cuda.is_available():
            add("PyTorch 显卡加速", True, f"可用：{torch.cuda.get_device_name(0)}（torch {torch.__version__}）")
        else:
            add("PyTorch 显卡加速", False if in_gsv_runtime else None, f"不可用（torch {torch.__version__}）：训练会非常慢。"
                "请到 https://www.nvidia.cn/drivers/lookup/ 安装最新显卡驱动并重启电脑；RTX 50 系列请使用 nvidia50 版整合包")
    except ImportError:
        pass
    except Exception as exc:
        add("PyTorch 显卡加速", None, str(exc))
    add("精准声纹打分", *sv_status(cfg))
    try:
        from voicetwin.backends.gptsovits import LATEST_VERSION, SUPPORTED_VERSIONS, version_status

        raw = str(((cfg.get("backends") or {}).get("gptsovits") or {}).get("version") or LATEST_VERSION)
        latest, note = version_status(raw if raw in SUPPORTED_VERSIONS else LATEST_VERSION)
        add("GPT-SoVITS 模型版本", True if latest else None, note, optional=str(cfg.get("backend") or "") != "gptsovits")
    except Exception as exc:
        add("GPT-SoVITS 模型版本", None, str(exc), optional=True)
    default = str(cfg.get("backend") or "")
    dummy = Project(cfg, "__doctor__")
    for name in available_backends():
        if name == "dummy":
            continue
        try:
            b = get_backend(name, cfg, dummy)
            problems = b.check()
            py = getattr(b, "python", "")
            add(f"引擎 {b.display_name}", not problems if name == default else (None if problems else True),
                ("；".join(problems) if problems else "就绪") + (f"（Python：{py}）" if py else ""),
                optional=name != default)
        except Exception as exc:
            add(f"引擎 {name}", None, str(exc), optional=name != default)
    shutil.rmtree(dummy.root, ignore_errors=True)
    return rows


_STATUS_ORDER = {"❌": 0, "⚠️": 1, "✅": 2}


def sort_doctor_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """问题排前面：❌，然后不是可选的 ⚠️，然后 ✅，最后是可选组件。同一类里保持原来的顺序。"""
    return sorted(rows, key=lambda r: (1 if r.get("optional") else 0, _STATUS_ORDER.get(str(r.get("status")), 1)))


def doctor_table(rows: Sequence[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]], str]:
    """环境检查表：(表头, 行, 总数说明)。# 从 1 开始。"""
    rows = sort_doctor_rows(rows)
    table = [[i, r.get("status"), r.get("item"),
              str(r.get("detail") or "") + ("（可选，不用管）" if r.get("optional") and r.get("status") != "✅" else "")]
             for i, r in enumerate(rows, 1)]
    bad = sum(1 for r in rows if r.get("status") == "❌" and not r.get("optional"))
    warn = sum(1 for r in rows if r.get("status") == "⚠️" and not r.get("optional"))
    total = f"共 {len(rows)} 项：❌ {bad} 项，⚠️ {warn} 项"
    return ["#", "状态", "项目", "说明"], table, total


def quick_check(cfg: Config) -> List[str]:
    """打开网页时的快速自检（只看文件，不启动子进程、不导入 torch，一般不到 1 秒）。

    返回给老师看的中文问题列表：每个问题一行，直接说点哪里（缺几个模型文件也只占一行）。"""
    problems: List[str] = []
    try:
        from voicetwin.utils.ffmpeg import find_ffmpeg

        find_ffmpeg()
    except Exception:
        problems.append("没有找到 ffmpeg：请重新双击 install_windows.bat 安装一次（你的数据不会丢）")
    if str(cfg.get("backend") or "gptsovits").lower() == "gptsovits":
        probe = None
        try:
            from voicetwin.backends.base import get_backend

            probe = Project(cfg, "__quick_check__")
            b = get_backend("gptsovits", cfg, probe)
            root = getattr(b, "root", None)
            if getattr(b, "external_url", ""):
                pass
            elif not root or not Path(root).exists():
                problems.append("找不到 GPT-SoVITS 整合包。请重新双击 install_windows.bat，按提示填写整合包的位置。")
            elif not (Path(root) / "api_v2.py").exists():
                problems.append(f"{root} 不是完整的 GPT-SoVITS 整合包（缺少 api_v2.py）。"
                                "请重新双击 install_windows.bat，填写整合包解压后的那个文件夹。")
            else:
                missing = list(b.missing_pretrained())
                if missing:
                    names = "、".join(Path(m).name for m in missing[:3]) + ("等" if len(missing) > 3 else "")
                    problems.append(f"缺少 {len(missing)} 个 GPT-SoVITS 模型文件（{names}）。"
                                    "请打开「🩺 环境检查」页，点「⬇️ 下载缺少的模型」。")
        except Exception as exc:
            problems.append(f"检查 GPT-SoVITS 时出错：{_explain_title(exc)}")
        finally:
            if probe is not None:
                shutil.rmtree(probe.root, ignore_errors=True)
    return problems


def training_plan(cfg: Config, voice: str, backend_name: Optional[str] = None, **opts: Any) -> str:
    """训练前预览：电脑会怎么自动选训练设置（一行中文，例如「显存 12 GB → 每批 6 条；素材 85 分钟 → …」）。

    只读文件和 nvidia-smi，不训练、不启动 GPT-SoVITS 的 Python（读不到显卡时就按「没有显卡」说）。
    声音还没准备素材、或者引擎不需要训练时返回 ''。opts 和 run_train 的一样（None / "auto" = 自动）。"""
    from voicetwin.backends.base import get_backend

    project = Project(cfg, voice)
    if not project.exists:
        return ""
    backend = get_backend(backend_name or cfg.get("backend"), cfg, project)
    if not backend.supports_training:
        return ""
    fn = getattr(backend, "training_plan", None)
    if fn is None:
        return ""
    try:
        plan = fn(quick=True, **opts)
    except TypeError:
        plan = fn(**opts)
    if isinstance(plan, str):
        return plan.strip()
    return str((plan or {}).get("summary") or "").strip()
