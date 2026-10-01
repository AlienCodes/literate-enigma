"""VoiceTwin 网页界面（Gradio 4.24）。启动：voicetwin webui（或双击 start_webui.bat）。

文件结构：
- 上半部分是纯函数（不需要 gradio，可以直接测试）：表格、摘要、状态卡、声音库、环境检查……
- ``WebUI`` 类：每个按钮的处理函数（``do_*`` / ``on_*``）。它们只返回普通的值和 ``_upd(...)``
  （和 ``gr.update(...)`` 完全一样的字典），所以没有 gradio 4.24 的环境里也能测试。
- ``WebUI.build()``：用 gradio 画页面、连接事件。

几条约定（改代码时请保持）：
- 耗时任务一律交给 ``webui.tasks.stream_task``：后台线程做事，网页每 0.6 秒刷新一次进度条；
  同一时间只做一件事；刷新网页不会打断任务。
- 每个流式处理函数的每一次 yield 都必须和它的 outputs 一一对应。这里用 ``self._o(名字列表, ...)``
  按名字生成，没写到的输出一律是“不变”，所以长度永远对得上。
- 表格的行一律用「id」或「#」那一列找对应的数据，不用行号（浏览器里排序、筛选后行号会变）。
- 给老师看的文字只用简单中文；英文报错和 Traceback 只写进黑色窗口和日志文件。
"""

import csv
import difflib
import functools
import glob
import html
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import voicetwin
from voicetwin import workflows as wf
from voicetwin.config import Config
from voicetwin.synth import engine as _engine
from voicetwin.utils.log import get_logger
from voicetwin.utils.progress import PROGRESS_CSS, format_elapsed, render_notice_html
from voicetwin.webui.tasks import KIND_TABS, current_task, request_stop, stream_task, task_banner_md

try:  # 浏览器标签页标题显示进度、完成时响一声（U1 提供；没有也不影响使用）
    from voicetwin.utils.progress import PROGRESS_JS
except ImportError:  # pragma: no cover - 各部分分开合并时
    PROGRESS_JS = None

try:  # 显卡状态（U9 提供）
    from voicetwin.utils import gpu as _gpu
except ImportError:  # pragma: no cover - 各部分分开合并时
    _gpu = None

log = get_logger("webui")

# 不向 gradio 官方发送统计、不检查更新：一切都在本机运行，也不会再提示"please upgrade"
# （整合包自带的 gradio 版本是配套好的，不需要也不应该单独升级）
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

APP_TITLE = "声音分身 VoiceTwin"
APP_VERSION = str(getattr(voicetwin, "__version__", "") or "")
DEFAULT_VOICE = "我的声音"

NEED_VOICE = "请先在页面最上面的「声音名称」里选择或填写声音（例如：我的声音）。"
NEED_PREPARE = "这个声音还没有准备素材，请先完成「① 准备素材」。"

if os.name == "nt":
    NOTE = "运行期间电脑不会自动睡眠；可以去做别的事，但不要关闭黑色窗口。"
else:
    NOTE = "可以去做别的事，但不要关闭运行程序的窗口。"

STOP_LABEL = "⏹ 停止"
STOP_CONFIRM = "再点一次确认停止（5 秒内）"
STOP_PENDING = "正在停止……（等这一小步做完）"
STOP_EXPIRED = "确认超时了，请在 5 秒内再点一次"
STOP_WINDOW = 5.0
STOPPED_MD = "### ⏹ 已停止\n\n已经做好的部分不会丢。需要时再点一次开始就行。"

PREP_BTN, PREP_BUSY = "开始准备素材", "⏳ 正在准备素材……"
TRAIN_BTN, TRAIN_BUSY = "开始训练", "⏳ 正在训练……"
SELECT_BTN, SELECT_BUSY = "重新挑选最佳模型", "⏳ 正在挑选……"
GEN_BTN, GEN_BUSY = "生成", "⏳ 正在生成……"
PROOF_BTN, PROOF_BUSY = "🔍 自动查找可能的错字", "⏳ 正在查找……"
DL_BTN, DL_BUSY = "⬇️ 下载缺少的模型", "⏳ 正在下载……"
SPEED_BTN, SPEED_BUSY = "▶ 试听语速", "⏳ 正在生成试听……"
VERIFY_BTN, VERIFY_BUSY = "开始鉴别", "⏳ 正在鉴别……"
BLIND_BTN, BLIND_BUSY = "生成盲听测试", "⏳ 正在生成盲听测试……"

PREP_NEXT = "去「② 训练模型」 →"
TRAIN_NEXT = "去「③ 生成讲课音频」 →"
ADOPT_BTN = "✅ 采用建议"
SUBMIT_BTN = "提交答案"

LOG_ACCORDION = "详细过程（出问题时可以复制给帮你的人）"
ADV_LABEL = "高级设置（一般不用改）"

INTRO = (f"# 🎙️ {APP_TITLE}" + (f" v{APP_VERSION}" if APP_VERSION else "") + "\n"
         "用你自己的讲课视频/录音，复刻你的**音色、语气和节奏**（中文 + 英文）。按 ① → ② → ③ 的顺序操作就行。")

HONEST_SIM = "相似度是声纹模型自动打分，越高越像，但不是绝对精确，最终以耳朵为准。"
PCT_HELP = ("「像你本人」的百分比：100% = 和你自己的真实录音一样像。"
            "有可靠的声纹模型时，低于 85% 的会被自动淘汰或标红。")
MFCC_NOTE = ("⚠️ 这次没有可靠的声纹模型（只有简易的 MFCC），百分比只能粗略参考，也不会按 85% 自动淘汰。"
             "GPT-SoVITS 整合包里自带的声纹模型能用时会自动用上。")

# ---------------------------------------------------------------------------- 表头
CLIP_HEADERS = ["#", "id", "保留（是/否）", "语言", "秒", "文字", "可能有错（红色）", "丢弃原因"]
CLIP_TYPES = ["number", "str", "str", "str", "number", "str", "markdown", "str"]
COL_ID, COL_KEEP, COL_LANG, COL_SEC, COL_TEXT, COL_SUSPECT, COL_DROP = CLIP_HEADERS[1:]
LIB_HEADERS = ["#", "名称", "素材（分钟 / 条）", "状态", "最佳模型", "最后修改时间"]
DOC_HEADERS = ["#", "状态", "项目", "说明"]
GEN_HEADERS = ["#", "句子", "像你本人（%）", "状态", "提示"]
VERIFY_HEADERS = ["#", "文件", "各模型 %", "综合 %", "排名", "是否 ≥85%"]

PASS_PCT = 85.0
GREAT_PCT = 95.0
MAX_BLIND = 24

_LANG_NAMES = {"zh": "中文", "en": "英文"}
_LANG_CODES = {"中文": "zh", "zh": "zh", "英文": "en", "en": "en"}
_KIND_NAMES = {"statement": "陈述", "question": "提问", "exclaim": "感叹", "exclamation": "感叹"}

# ---------------------------------------------------------------------------- 选项（中文名, 内部值）
ASR_CHOICES = [("通用（中英文都行，推荐）", "faster-whisper"), ("纯中文课更准", "funasr"), ("不识别（只用字幕）", "none")]
LANG_CHOICES = [("自动识别", "auto"), ("中文", "zh"), ("英文", "en")]
DENOISE_CHOICES = [("自动", "auto"), ("开", "on"), ("关", "off")]
TRAIN_BACKENDS = [("GPT-SoVITS（推荐）", "gptsovits"), ("Qwen3-TTS", "qwen3tts")]
SYNTH_BACKENDS = [("GPT-SoVITS（推荐，用你训练的模型）", "gptsovits"), ("Qwen3-TTS", "qwen3tts"),
                  ("IndexTTS（不用训练）", "indextts")]
DUMMY_BACKEND = ("测试引擎（不是你的声音）", "dummy")
DPO_CHOICES = [("自动（推荐）", "auto"), ("开", "on"), ("关", "off")]
FORMAT_CHOICES = [("WAV（音质最好，剪映/后期用）", "wav"), ("MP3（文件小，方便发微信、上传）", "mp3")]

# 质量档位的中文名和说明只在 synth/engine.py 里写一份（网页、命令行、报告用的是同一套名字）
QUALITY_CHOICES: List[Tuple[str, str]] = wf.quality_choices()
QUALITY_SHORT: Dict[str, str] = dict(_engine.QUALITY_SHORT)
QUALITY_NOTE = ("越往下越慢，但每句会多试几次、自动挑最像你的，结果更稳定。不会 100% 一模一样："
                "素材的质量和数量、认真校对文字，对像不像影响最大。")
TIER_QUALITY = {"high": "perfect", "mid": "perfect", "low": "max", "none": "balanced"}

SPEED_LABEL = "语速（← 往左更快　·　中间 0 = 和你原声一样　·　往右更慢 →）"
SPEED_NOTE = "语速调得越极端（超过 ±20%），越可能不自然；建议在 −15～+15 之间。"
SPEED_SAMPLE = "大家好，今天我们来学习新的内容，请大家认真听。"

SCRIPT_TEXT_EXTS = (".txt", ".md", ".docx")
SCRIPT_SUB_EXTS = (".srt", ".vtt")

# 第一条：show_progress="hidden" 的事件（长任务）运行时，gradio 4.24 仍会在每个输出上加一圈闪烁的橙色边框
# 和一块空白（StatusTracker 的 "wrap default hidden generating"）。我们有自己的进度条，所以把它整个隐藏。
# 第二条：空的 Markdown 在任务运行期间会被撑高 96 像素（.min），进度条下面会空出一大块；vt-md 的不撑高。
APP_CSS = """
.wrap.default.hidden,.wrap.center.hidden{display:none!important}
.vt-md .min{min-height:0!important}
.vt-header h1{margin-bottom:2px}
.vt-honest{color:var(--body-text-color-subdued);font-size:var(--text-sm)}
.vt-diff{margin:4px 0;padding:8px 12px;border-left:4px solid #dc2626;background:var(--background-fill-secondary);
  border-radius:4px;line-height:1.7;overflow-wrap:anywhere}
.vt-diff .vt-diff-row{margin:2px 0}
.vt-diff .vt-diff-tag{display:inline-block;min-width:4.5em;font-weight:700}
.vt-diff .vt-diff-reason{color:var(--body-text-color-subdued);font-size:var(--text-sm)}
"""


# gradio 4.24 的保护（浏览器里实测）：流式输出的头两条消息挤在一起到达时，偶尔有一个 Markdown 收到的是「差异」列表，
# 它的 message.trim() 会报错，Svelte 的刷新从此停住（进度条不动、换页也换不了）。给列表补一个 trim，
# 让这个 Markdown 暂时显示空白、页面照常工作；紧跟着的完整结果会把内容补上。（webui/tasks.py 也把头两次产出隔开了。）
GUARD_JS = """() => {
  try {
    if (!Array.prototype.trim) {
      Object.defineProperty(Array.prototype, 'trim', {value: function () { return ''; }, configurable: true, writable: true});
    }
  } catch (e) {}
}"""


def page_js() -> str:
    """交给 gr.Blocks(js=...) 的函数：先装上面的保护，再运行进度条用的脚本（标签页标题显示进度、完成时响一声）。"""
    parts = [GUARD_JS] + ([PROGRESS_JS] if PROGRESS_JS else [])
    calls = "\n".join(f"  try {{ ({p.strip()})(); }} catch (e) {{}}" for p in parts)
    return "() => {\n" + calls + "\n}"


# ============================================================================ 通用小工具
def _upd(**kwargs: Any) -> Dict[str, Any]:
    """等同 gr.update(...)（gradio 4.x 里它就是一个带 __type__ 的字典），这样不导入 gradio 也能用。"""
    kwargs["__type__"] = "update"
    return kwargs


def _btn(label: str, **kwargs: Any) -> Dict[str, Any]:
    """按钮的更新：一定带上按钮上的字。

    gradio 4.24 的坑（实测）：一开始 visible=False 的按钮，之后只用 gr.update(visible=True) 显示出来时，
    按钮上会显示「undefined」。所以显示/隐藏按钮时总是连同文字一起发。"""
    return _upd(value=label, **kwargs)


def _info(msg: str) -> None:
    """右上角的提示框（只能在网页的处理函数里调用，后台线程里调用只会打印到黑色窗口）。"""
    try:
        import gradio as gr

        gr.Info(msg)
    except Exception:
        pass


def _voice_name(value: Any) -> str:
    """下拉框的值统一成字符串。

    部分 gradio 版本（例如 GPT-SoVITS 整合包自带的 4.24）在更新选项或刷新页面后，会把下拉框的值传成
    列表（[] 或 ["我的声音"]）甚至 None，直接拿去用会报错。"""
    if isinstance(value, (list, tuple)):
        value = next((v for v in value if v), "")
    return str(value).strip() if value else ""


def _voices(cfg: Config) -> List[str]:
    try:
        return [str(v["voice"]) for v in wf.list_voices(cfg)]
    except Exception as exc:  # 工作目录读不了时不让整个页面打不开
        log.warning(f"读取声音列表失败：{exc}")
        return []


def _int(value: Any, default: int = 0) -> int:
    """数字框清空后 gradio 会传 None；也可能是 '3'、3.0。统一成 ≥0 的整数。"""
    try:
        if value is None or value == "":
            return default
        f = float(value)
        if f != f:  # NaN
            return default
        return max(0, int(round(f)))
    except (TypeError, ValueError):
        return default


def _path_of(f: Any) -> str:
    """gr.File 传来的值可能是路径字符串，也可能是带 .name 的对象。"""
    if f is None:
        return ""
    if isinstance(f, (str, Path)):
        return str(f)
    return str(getattr(f, "name", "") or getattr(f, "path", "") or "")


def _paths_of(files: Any) -> List[str]:
    if not files:
        return []
    if not isinstance(files, (list, tuple)):
        files = [files]
    return [p for p in (_path_of(f) for f in files) if p]


def _md_text(s: Any) -> str:
    """放进 Markdown 的用户文字：转义 HTML 和会改变格式的符号，表格里的 | 也转义。"""
    text = html.escape(str(s if s is not None else ""), quote=False)
    return re.sub(r"([\\`*_\[\]#|~$])", r"\\\1", text).replace("\n", " ")


def _local_time(ts: Any) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def _fmt_duration(seconds: Any) -> str:
    try:
        s = max(0, int(round(float(seconds))))
    except (TypeError, ValueError):
        return "—"
    m, s = divmod(s, 60)
    return f"{m} 分 {s} 秒" if m else f"{s} 秒"


def _num(value: Any) -> Optional[float]:
    try:
        if value is None or isinstance(value, bool):
            return None
        f = float(value)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def _pct_text(p: Optional[float]) -> str:
    return "—" if p is None else f"{p:.1f}%"


_PCT_KEYS = ("pct", "percent", "similarity_pct", "sim_pct", "speaker_pct", "like_pct", "像你本人（%）", "像你本人")


def _pct_of(item: Any) -> Optional[float]:
    """从 U3 的结果里取「像你本人」百分比（0~100）。不同版本的键名不完全一样，这里都认。"""
    if not isinstance(item, dict):
        return None
    for key in _PCT_KEYS:
        v = _num(item.get(key))
        if v is not None:
            return v
    sim = item.get("similarity")
    if isinstance(sim, dict):
        return _pct_of(sim)
    return None


def _label_for_sim(sim: Optional[float]) -> str:
    try:
        from voicetwin.eval.metrics import similarity_label

        return similarity_label(sim, "")
    except Exception:
        return "未知" if sim is None else f"{sim:.2f}"


def _status_for_pct(pct: Optional[float]) -> str:
    if pct is None:
        return ""
    if pct >= GREAT_PCT:
        return "✅ 很像"
    if pct >= PASS_PCT:
        return "🟢 比较像"
    return "🔴 不够像"


def _friendly(exc: Any, what: str = "", log_path: str = "") -> str:
    """把报错变成给老师看的 Markdown（优先用 errors.friendly_md；没有时退回简单的一行）。"""
    try:
        from voicetwin.errors import friendly_md

        return friendly_md(exc, what=what, log_path=log_path)
    except Exception:
        title = str(exc).strip()[:300] if exc is not None else ""
        return f"### ❌ {what}没有完成：" + _md_text(title or "出现了意外错误")


def _log_path(cfg: Config, voice: str) -> str:
    try:
        return str(wf.Project(cfg, voice).logs_dir / "voicetwin.log") if voice else ""
    except Exception:
        return ""


def _safe(what: str, n_out: int, md_pos: int = 0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """给不流式的按钮用：出错时不弹 gradio 的空白「Error」，而是把说明写进这个按钮的 Markdown 输出。"""

    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                log.error(f"「{what}」出错：{exc}", exc_info=True)
                md = _friendly(exc, what)
                if n_out == 1:
                    return md
                out: List[Any] = [_upd() for _ in range(n_out)]
                out[md_pos] = md
                return tuple(out)

        return wrapper

    return deco


#: 流式任务最后一次产出之后，再等这么久才真正结束（见 _settled）
SETTLE_SECONDS = 0.6


def _settled(fn: Callable[..., Iterator[Any]]) -> Callable[..., Iterator[Any]]:
    """给流式（边做边显示进度）的按钮用：最后一次产出之后停一下再结束。

    gradio 4.24 的坑（浏览器里实测）：任务结束时，最后一次进度更新、「任务完成」和「关闭连接」三条消息几乎同时到达网页。
    网页把前两条推迟处理，却立刻处理「关闭连接」，顺手丢掉了这个任务记着的上一次的值；推迟的那条进度更新只是「和上次比的差异」，
    于是被原样当成了新的值：没变化的输出收到一个空列表 []。「只重新生成第几句」的框就这样变成了 []，下一次点「生成」
    会提示「看不懂「[]」」（Markdown 收到列表时还会报 trim 错、整个页面不再刷新）。最后停一下，让网页先把最后一条进度更新
    按差异处理完，「关闭连接」再到。"""

    @functools.wraps(fn)
    def run(*args: Any, **kwargs: Any) -> Iterator[Any]:
        yield from fn(*args, **kwargs)
        time.sleep(SETTLE_SECONDS)

    return run


def _text_in(value: Any) -> str:
    """文字框传来的值统一成字符串。

    碰上 _settled 说的那个 gradio 4.24 的坑时（例如旧版本留下的网页还开着），文字框里存的会是一个列表，
    交回来时变成字符串 "[]"。列表 / "[]" 都当成空的，不要把它当成老师填的内容。"""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "".join(str(v) for v in value if isinstance(v, (str, int, float)))
    text = str(value)
    return "" if text.strip() in ("[]", "{}") else text


def _stages(cfg: Config, kind: str, backend: Optional[str] = None, **kw: Any) -> Optional[List[Tuple[float, str]]]:
    """每种任务分哪几步（wf.task_stages）。生成要把选的质量传进来（quality=，「完美」档多一步），
    素材准备要传 overrides=（会不会自动查错字）。出错时返回 None（进度条照样能用，只是不显示第几步）。"""
    try:
        return list(wf.task_stages(kind, cfg, backend, **kw))
    except Exception as exc:
        log.debug(f"task_stages({kind}) 不可用：{exc}")
        return None


def _blank_rows(headers: Sequence[str]) -> List[List[Any]]:
    """还没有结果的表格的初始值：一行空格子。

    不能不给值：gradio 4.24 会用 0 填「数字」列，表格里就多出一行「0」（看起来像第 0 条结果）；
    也不能给 []：那样表头会被换成 1、2、3……"""
    return [[""] * len(headers)]


def _table_records(table: Any, headers: Sequence[str]) -> List[Dict[str, Any]]:
    """gradio 传来的表格（pandas.DataFrame 或二维列表）→ 每行一个 {表头: 值}。"""
    if table is None:
        return []
    if hasattr(table, "to_dict") and hasattr(table, "columns"):
        try:
            rows = table.to_dict("records")
            return [{str(k): v for k, v in r.items()} for r in rows]
        except Exception:
            return []
    if isinstance(table, dict) and "data" in table:
        heads = table.get("headers") or list(headers)
        return [dict(zip(heads, row)) for row in (table.get("data") or []) if row]
    out = []
    for row in table or []:
        if isinstance(row, dict):
            out.append(row)
        elif isinstance(row, (list, tuple)) and row:
            out.append(dict(zip(headers, row)))
    return out


def _cell(table: Any, headers: Sequence[str], row: int, column: str) -> Any:
    recs = _table_records(table, headers)
    if 0 <= row < len(recs):
        return recs[row].get(column)
    return None


def _evt_index(evt: Any) -> Tuple[int, int]:
    idx = getattr(evt, "index", None)
    if isinstance(idx, (list, tuple)):
        r = idx[0] if idx else 0
        c = idx[1] if len(idx) > 1 else 0
    else:
        r, c = idx or 0, 0
    try:
        return int(r), int(c)
    except (TypeError, ValueError):
        return -1, -1


def _clean_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v != v:
        return ""
    return str(v).strip()


# ============================================================================ 显卡
def _gpu_status(refresh: bool = False) -> Dict[str, Any]:
    if _gpu is None:
        return {"ok": False, "level": "warn", "message": "⚠️ 暂时检查不了显卡状态", "advice": ""}
    try:
        return _gpu.gpu_status(refresh=refresh)
    except Exception as exc:  # gpu_status 本身不会抛异常，这里只是保险
        return {"ok": False, "level": "warn", "message": "⚠️ 暂时检查不了显卡状态", "advice": str(exc)}


def _gpu_badge(status: Optional[Dict[str, Any]] = None) -> str:
    if _gpu is None:
        return render_notice_html("⚠️ 暂时检查不了显卡状态", "warn")
    try:
        return _gpu.render_gpu_badge_html(status if status is not None else _gpu_status())
    except Exception:
        return render_notice_html("⚠️ 暂时检查不了显卡状态", "warn")


def _gpu_pending() -> str:
    try:
        return _gpu.render_gpu_pending_html() if _gpu is not None else ""
    except Exception:
        return ""


def _vram_tier(status: Optional[Dict[str, Any]]) -> str:
    if _gpu is None or status is None:
        return "none"
    try:
        return str(_gpu.vram_tier(status))
    except Exception:
        return "none"


def _recommended_quality(status: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """按显卡推荐默认质量：高/中档 → 完美；小显存 → 极致；没有能用的 N 卡 → 均衡。返回 (值, 一句说明)。"""
    tier = _vram_tier(status)
    q = TIER_QUALITY.get(tier, "balanced")
    gb = None
    if status:
        gb = _num(status.get("nominal_gb")) or _num(status.get("total_gb"))
    size = f"显存 {gb:.0f} GB" if gb else "你的显卡"
    if tier == "none":
        note = (f"没检测到能用的 N 卡（NVIDIA 显卡），已先选「{QUALITY_SHORT[q]}」。用 CPU 生成会很慢，"
                "「极致」「完美」会更慢。")
    elif tier == "low":
        note = f"已按你的显卡自动选好「{QUALITY_SHORT[q]}」（{size}，显存偏小，「完美」会非常慢）。"
    else:
        note = f"已按你的显卡自动选好「{QUALITY_SHORT[q]}」（{size}）。"
    return q, note


# ============================================================================ 声音状态 / 声音库
def _prepare_summary(project: Any) -> Dict[str, Any]:
    try:
        return project.read_json(project.root / "prepare_summary.json", {}) or {}
    except Exception:
        return {}


def _material_stats(project: Any) -> Tuple[float, int]:
    """(可用分钟, 可用条数)：优先读 prepare_summary.json，没有就从 manifest 算。"""
    s = _prepare_summary(project)
    minutes, clips = _num(s.get("minutes_kept")), s.get("clips_kept")
    if minutes is None or clips is None:
        kept = project.load_manifest(only_kept=True)
        minutes = sum(float(r.get("duration", 0) or 0) for r in kept) / 60.0
        clips = len(kept)
    return round(float(minutes or 0.0), 1), int(clips or 0)


def _best_selection(entry: Dict[str, Any]) -> Tuple[str, str]:
    """一个引擎的 models.json 条目 → (最佳版本编号, 像不像的说明)。"""
    sel = entry.get("selection") or {}
    if isinstance(sel.get("selection"), dict):  # run_train 返回值里套了一层
        sel = sel["selection"]
    best = str(sel.get("best") or (entry.get("selected") or {}).get("id") or "")
    label = ""
    for r in sel.get("results") or []:
        if str(r.get("id")) == best:
            pct = _pct_of(r)
            if pct is not None:
                label = f"像你本人 {pct:.1f}%"
            elif r.get("speaker_sim") is not None:
                label = _label_for_sim(_num(r.get("speaker_sim")))
            break
    return best, label


def _voice_status_md(cfg: Config, voice: Any) -> str:
    """页面顶部的「当前声音状态」：做到哪一步了、下一步点哪里。"""
    v = _voice_name(voice)
    if not v:
        return "👆 先在上面「声音名称」里给你的声音起个名字，例如：我的声音"
    try:
        project = wf.Project(cfg, v)
    except ValueError as exc:
        return "⚠️ " + _md_text(exc)
    name = _md_text(v)
    running = _running_line(v)
    if running and not project.exists:  # 第一次准备素材，还在做：不要再说「还没有素材，请点开始」
        return running.strip()
    if not project.exists:
        return (f"「{name}」是新声音，还没有素材。👉 下一步：在「① 准备素材」里填讲课视频所在的文件夹，"
                "点「开始准备素材」。")
    minutes, clips = _material_stats(project)
    trained = [(k, e) for k, e in (project.load_models() or {}).items() if isinstance(e, dict) and e.get("selected")]
    if not trained:
        md = (f"① 素材 ✅ {minutes} 分钟（{clips} 条）　② 训练 ⬜ 还没训练　"
              "👉 下一步：去「② 训练模型」点「开始训练」（通常要 30~90 分钟）")
    else:
        entry = trained[0][1]
        for k, e in trained:  # 有 GPT-SoVITS 时优先显示它
            if k == "gptsovits":
                entry = e
        _best, label = _best_selection(entry)
        when = entry.get("trained_at") or ""
        done = f"{when} 完成" if when else "已完成"
        md = (f"① 素材 ✅ {minutes} 分钟　② 训练 ✅ {_md_text(done)}"
              + (f"（自动挑选：{_md_text(label)}）" if label else "")
              + "　👉 现在可以去「③ 生成讲课音频」了")
    if minutes < 10:
        md += "\n\n⚠️ 素材偏少（不到 10 分钟），声音可能不够像，建议再加一些讲课视频"
    return running + md


def _running_line(voice: str) -> str:
    info = current_task()
    if info and info.get("running") and str(info.get("voice") or "") == voice:
        pct = (info.get("snap") or {}).get("pct", 0)
        return f"🔄 后台正在「{_md_text(info.get('label'))}」（完成 {pct}%），做完后这里会更新。\n\n"
    return ""


def _gen_warn_md(cfg: Config, voice: Any, backend: Any) -> str:
    """③ 页顶部的提醒：还没准备素材 / 还没训练。"""
    v = _voice_name(voice)
    if not v:
        return ""
    try:
        project = wf.Project(cfg, v)
    except ValueError:
        return ""
    if not project.exists:
        return "⚠️ " + NEED_PREPARE
    name = str(backend or cfg.get("backend") or "gptsovits")
    if name == "gptsovits" and not (project.load_models().get("gptsovits") or {}).get("selected"):
        return ("⚠️ 这个声音还没有训练，现在生成用的是通用模型，听起来不太像你。"
                "建议先去「② 训练模型」点「开始训练」。")
    return ""


def _library_status(e: Dict[str, Any]) -> str:
    status = str(e.get("status") or "").strip()
    if status:
        return status
    trained = e.get("trained")
    if isinstance(trained, (list, tuple)):
        trained = bool(trained)
    if trained:
        return "✅ 已训练，可以生成"
    if (_num(e.get("minutes")) or 0) > 0 or (e.get("clips_kept") or e.get("clips")):
        return "⚠️ 素材已准备，还没训练"
    return "⏳ 还没准备素材"


def _library_entries(cfg: Config) -> List[Dict[str, Any]]:
    """声音库：每个已保存的声音一条（名称、素材、状态、最佳模型、主参考音频、修改时间），最近改过的排前面。"""
    try:
        entries = [dict(e) for e in (wf.voice_library(cfg) or [])]
    except Exception as exc:  # 工作目录读不了时不让整个页面打不开
        log.warning(f"读取声音库失败：{exc}")
        entries = []
    out = []
    for e in entries:
        name = str(e.get("voice") or e.get("name") or "").strip()
        if not name:
            continue
        minutes = _num(e.get("minutes"))
        clips = e.get("clips_kept", e.get("clips"))
        out.append({
            "name": name,
            "minutes": minutes,
            "clips": _int(clips) if clips is not None else None,
            "status": _library_status(e),
            "best_model": str(e.get("best_model") or ""),
            "main_reference": str(e.get("main_reference") or ""),
            "modified": e.get("modified"),
        })
    return out


def _library_rows(entries: Sequence[Dict[str, Any]]) -> List[List[Any]]:
    rows = []
    for i, e in enumerate(entries, 1):
        minutes = "—" if e.get("minutes") is None else f"{e['minutes']:g} 分钟"
        clips = "—" if e.get("clips") is None else f"{e['clips']} 条"
        rows.append([i, e["name"], f"{minutes} / {clips}", e["status"], e.get("best_model") or "—",
                     _local_time(e.get("modified")) or "—"])
    return rows


def _library_label(n: int) -> str:
    return f"🎙️ 我的声音库（共 {n} 个）"


def _library_total_md(n: int) -> str:
    if not n:
        return "还没有保存的声音。在上面「声音名称」里起个名字，然后去「① 准备素材」。"
    return f"共 {n} 个声音。👆 点表格里的某一行，就会选中这个声音，并可以在下面试听。"


# ============================================================================ ① 校对表
_MD_ESC = {c: "&#%d;" % ord(c) for c in "\\`*_{}[]()#+-.!|~>$"}
_RED_SPAN = '<span style="color:#dc2626;font-weight:700;background:#fee2e2">'
_GREEN_SPAN = '<span style="color:#15803d;font-weight:700;background:#dcfce7">'


def _cell_esc(s: str) -> str:
    """放进 markdown 表格格子的文字：HTML 转义 + markdown 符号变成数字实体（研究里实测过能原样显示）。"""
    return "".join(_MD_ESC.get(c, c) for c in html.escape(str(s), quote=True))


def _merge_spans(spans: Any, n: int) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for sp in spans or []:
        try:
            s, e = max(0, int(sp[0])), min(n, int(sp[1]))
        except (TypeError, ValueError, IndexError):
            continue
        if e > s:
            out.append((s, e))
    out.sort()
    merged: List[Tuple[int, int]] = []
    for s, e in out:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _render_marked(text: str, spans: Any) -> str:
    """可疑的字标红（优先用 U8 的 proofcheck.render_marked）。"""
    try:
        from voicetwin.data.proofcheck import render_marked

        return str(render_marked(text, spans))
    except ImportError:
        pass
    except Exception as exc:
        log.debug(f"render_marked 出错：{exc}")
    text = str(text or "")
    out, pos = [], 0
    for s, e in _merge_spans(spans, len(text)):
        out += [_cell_esc(text[pos:s]), _RED_SPAN, _cell_esc(text[s:e]), "</span>"]
        pos = e
    out.append(_cell_esc(text[pos:]))
    return "".join(out)


def _render_diff(text: str, alt: str, spans: Any = None) -> str:
    """两次识别结果对比（优先用 U8 的 proofcheck.render_diff_html；没有建议时把可疑的字标红）。"""
    try:
        from voicetwin.data.proofcheck import render_diff_html

        return str(render_diff_html(text, alt, spans))
    except ImportError:
        pass
    except Exception as exc:
        log.debug(f"render_diff_html 出错：{exc}")
    text, alt = str(text or ""), str(alt or "")
    if not alt:
        return (f'<div class="vt-diff-row"><span class="vt-diff-tag">识别 A：</span>{html.escape(text)}</div>'
                '<div class="vt-diff-row vt-diff-reason">（没有建议）</div>')
    a_out, b_out = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, text, alt, autojunk=False).get_opcodes():
        a, b = html.escape(text[i1:i2]), html.escape(alt[j1:j2])
        if op == "equal":
            a_out.append(a)
            b_out.append(b)
        else:
            if a:
                a_out.append(_RED_SPAN + a + "</span>")
            if b:
                b_out.append(_GREEN_SPAN + b + "</span>")
    return (f'<div class="vt-diff-row"><span class="vt-diff-tag">识别 A：</span>{"".join(a_out)}</div>'
            f'<div class="vt-diff-row"><span class="vt-diff-tag">识别 B：</span>{"".join(b_out)}</div>')


def _suspect(rec: Dict[str, Any]) -> Dict[str, Any]:
    s = rec.get("suspect")
    return s if isinstance(s, dict) and (s.get("spans") or s.get("alt") or s.get("reasons")) else {}


def _clips_table(cfg: Config, voice: Any, only_suspect: bool = False) -> List[List[Any]]:
    """校对表：每条片段一行。# 是显示的序号（从 1 开始），找片段一律用 id 列。"""
    voice = _voice_name(voice)
    if not voice:
        return []
    project = wf.Project(cfg, voice)
    rows = []
    for r in project.load_manifest():
        sus = _suspect(r)
        if only_suspect and not sus:
            continue
        text = str(r.get("text", "") or "")
        marked = _render_marked(text, sus.get("spans") or []) if sus else ""
        rows.append([len(rows) + 1, r["id"], "是" if r.get("keep", True) else "否",
                     _LANG_NAMES.get(r.get("lang", ""), r.get("lang", "")), round(float(r.get("duration", 0) or 0), 1),
                     text, marked, r.get("drop_reason", "") or ""])
    return rows


_EDIT_COLS = (COL_KEEP, COL_LANG, COL_TEXT)  # 老师能改的三列


def _row_edited(row: Dict[str, Any], rec: Dict[str, Any]) -> bool:
    """表格的这一行（按表头的字典）和硬盘上的片段比，「保留 / 语言 / 文字」有没有不一样（判断方法和「保存修改」一样）。"""
    text = _clean_cell(row.get(COL_TEXT))
    if text and text != str(rec.get("text", "") or "").strip():
        return True
    if _parse_keep(row.get(COL_KEEP)) != bool(rec.get("keep", True)):
        return True
    lang = _LANG_CODES.get(_clean_cell(row.get(COL_LANG)), rec.get("lang", ""))
    return lang != rec.get("lang", "")


def _pending_edits(cfg: Config, voice: Any, table: Any, skip: Sequence[str] = ()) -> Dict[str, Dict[str, Any]]:
    """表格里改了、还没点「保存修改」的行：{id: 这一行}。

    和硬盘上的校对表比，所以只在这三列没被别的步骤改过时用（查错字只改标红；采用建议只改那一条，用 skip 排除）。"""
    v = _voice_name(voice)
    rows = _table_records(table, CLIP_HEADERS)
    if not v or not rows:
        return {}
    try:
        records = {r["id"]: r for r in wf.Project(cfg, v).load_manifest()}
    except ValueError:
        return {}
    skip_set = {str(x) for x in skip}
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        rid = _clean_cell(row.get(COL_ID))
        rec = records.get(rid)
        if rec is not None and rid not in skip_set and _row_edited(row, rec):
            out[rid] = row
    return out


def _keep_pending(rows: List[List[Any]], pending: Dict[str, Dict[str, Any]]) -> List[List[Any]]:
    """把还没保存的修改放回刚从硬盘读出来的表格里（按 id 找行）。被「只看可能有错的」筛掉的行也留在表格最后，
    这样修改不会因为换了显示方式就没了。改过文字的行，红色标记是按原来的文字算的，先不显示。"""
    if not pending:
        return rows
    i_id, i_text, i_sus = (CLIP_HEADERS.index(h) for h in (COL_ID, COL_TEXT, COL_SUSPECT))
    out: List[List[Any]] = []
    seen = set()
    for row in rows:
        row = list(row)
        p = pending.get(str(row[i_id]))
        if p is not None:
            seen.add(str(row[i_id]))
            old_text = str(row[i_text] or "").strip()
            for col in _EDIT_COLS:
                val = _clean_cell(p.get(col))
                if val or col != COL_TEXT:  # 文字格清空了：「保存修改」会保持原文，这里也一样
                    row[CLIP_HEADERS.index(col)] = val
            if str(row[i_text] or "").strip() != old_text:
                row[i_sus] = ""
        out.append(row)
    for rid, p in pending.items():
        if rid not in seen:
            out.append([p.get(h) if h == COL_SEC else _clean_cell(p.get(h)) for h in CLIP_HEADERS])
    for n, row in enumerate(out, 1):
        row[0] = n
    return out


def _pending_note(n: int) -> str:
    return f"✏️ 表格里还有 **{n}** 条修改没有保存（已经帮你留在表格里），记得点下面的「保存修改」。"


def _clips_count_md(cfg: Config, voice: Any) -> str:
    """校对表上方的总数：一共多少条、保留多少条（多少分钟）、不保留多少条、几条可能有错。"""
    voice = _voice_name(voice)
    if not voice:
        return NEED_VOICE
    try:
        records = wf.Project(cfg, voice).load_manifest()
    except ValueError as exc:
        return "⚠️ " + _md_text(exc)
    if not records:
        return "还没有片段，请先点上面的「开始准备素材」。"
    kept = [r for r in records if r.get("keep", True)]
    minutes = sum(float(r.get("duration", 0) or 0) for r in kept) / 60.0
    val = sum(1 for r in kept if r.get("split") == "val")
    sus = sum(1 for r in records if _suspect(r))
    by_lang: Dict[str, int] = {}
    for r in kept:
        by_lang[r.get("lang", "")] = by_lang.get(r.get("lang", ""), 0) + 1
    langs = "，".join(f"{_LANG_NAMES.get(k, k or '未知')} {v} 条" for k, v in sorted(by_lang.items()))
    text = (f"### 📊 一共 **{len(records)}** 条片段：保留 **{len(kept)}** 条（{minutes:.1f} 分钟），"
            f"不保留 **{len(records) - len(kept)}** 条")
    if sus:
        text += f"，其中 **{sus}** 条可能有错（已标红）"
    details = [x for x in (langs, f"其中 {val} 条留作「考试题」（用来自动挑选最像你的模型）" if val else "") if x]
    return text + ("\n\n" + "；".join(details) if details else "")


_DROP_WORDS = {"否", "不", "不要", "删", "删除", "n", "no", "false", "0", "x", "×", "✘", "✗", "ｘ", "✕"}
_KEEP_WORDS = {"是", "要", "保留", "y", "yes", "true", "1", "✔", "✓", "√", ""}


def _parse_keep(v: Any) -> Optional[bool]:
    """「保留」列：是/否（也认 ✔ ✘ 1 0 yes no 等）。看不懂时返回 None（保持原样）。"""
    if v is None:
        return True
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and not (isinstance(v, float) and v != v):
        if v in (0, 1):
            return bool(v)
        return None
    if isinstance(v, float):  # NaN：空格子
        return True
    s = str(v).strip().lower()
    if s.endswith(".0") and s[:-2] in ("0", "1"):
        s = s[:-2]
    if s in _DROP_WORDS:
        return False
    if s in _KEEP_WORDS:
        return True
    return None


def _write_csv_atomic(path: Path, rows: List[Dict[str, Any]], fields: Sequence[str]) -> None:
    """先写临时文件再替换：写到一半出错也不会留下半个文件。被 Excel 打开时会抛 PermissionError。"""
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fields))
        w.writeheader()
        for row in rows:
            w.writerow(row)
    try:
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


# ============================================================================ ① 摘要
def _summary_md(s: Dict[str, Any]) -> str:
    """素材准备完成后的说明：不出现 Python 字典和术语，列表都编号。"""
    if not s:
        return ""
    md: List[str] = []
    by_lang = s.get("minutes_by_lang") or {}
    lang_part = "，".join(f"{_LANG_NAMES.get(k, k or '其他')} {v} 分钟" for k, v in sorted(by_lang.items()))
    md.append(f"### ✅ 素材准备好了：可用 **{s.get('minutes_kept', 0)} 分钟**"
              + (f"（{lang_part}）" if lang_part else "") + f"，一共 {s.get('clips_kept', 0)} 条")
    dropped = s.get("dropped") or {}
    if dropped:
        total = sum(int(v or 0) for v in dropped.values())
        items = "\n".join(f"{i}. {_md_text(k)}：{v} 条" for i, (k, v) in enumerate(dropped.items(), 1))
        md.append(f"自动去掉了 {total} 条（共 {len(dropped)} 种原因）：\n\n{items}")
    warnings = list(s.get("warnings") or [])
    if warnings:
        if len(warnings) == 1:
            md.append(f"> ⚠️ {_md_text(warnings[0])}")
        else:
            md.append(f"> ⚠️ 提醒（共 {len(warnings)} 条）：\n>\n"
                      + "\n".join(f"> {i}. {_md_text(w)}" for i, w in enumerate(warnings, 1)))
    prof = s.get("profile") or {}
    rates = []
    for lang, r in (prof.get("rate") or {}).items():
        p50 = _num((r or {}).get("p50")) if isinstance(r, dict) else None
        if p50 is None:
            continue
        rates.append(f"中文每秒 {p50:.1f} 个字" if lang == "zh" else f"英文每秒 {p50:.1f} 个音节")
    if rates:
        md.append("**你的语速**：" + "；".join(rates))
    p = prof.get("pauses") or {}
    if all(_num(p.get(k)) is not None for k in ("clause", "sentence", "paragraph")):
        md.append(f"**你的停顿习惯**：逗号处约 {p['clause']:.1f} 秒，句号处约 {p['sentence']:.1f} 秒，"
                  f"段落之间约 {p['paragraph']:.1f} 秒")
    if s.get("val_clips"):
        md.append(f"其中 {s['val_clips']} 条留作「考试题」：训练后用来自动挑出最像你的模型")
    refs = s.get("references") or []
    if refs:
        lines = [f"{i}. [{_LANG_NAMES.get(r.get('lang', ''), r.get('lang', ''))}·{_KIND_NAMES.get(r.get('kind', ''), '陈述')}] "
                 f"{_md_text(r.get('text', ''))}" for i, r in enumerate(refs[:3], 1)]
        md.append(f"**自动挑选的参考录音**（一共 {len(refs)} 条，下面是前 {min(3, len(refs))} 条）：\n\n" + "\n".join(lines))
    skipped = s.get("skipped_files") or []
    if skipped:
        lines = [f"{i}. {_md_text(Path(str(x.get('file', ''))).name or x.get('file', ''))}（{_md_text(x.get('reason', ''))}）"
                 for i, x in enumerate(skipped, 1) if isinstance(x, dict)]
        md.append(f"⚠️ 有 {len(skipped)} 个文件没能处理：\n\n" + "\n".join(lines)
                  + "\n\n换个文件后再点「开始准备素材」，已处理的不会重做。")
    return "\n\n".join(md)


def _selection_info(info: Dict[str, Any]) -> Dict[str, Any]:
    sel = info.get("selection") if isinstance(info, dict) else None
    if isinstance(sel, dict) and isinstance(sel.get("selection"), dict):
        return sel
    return info if isinstance(info, dict) else {}


PLAN_PREFIX = "训练计划："


def _strip_plan(text: str) -> str:
    text = str(text or "").strip()
    return text[len(PLAN_PREFIX):].strip() if text.startswith(PLAN_PREFIX) else text


def _plan_text(info: Any) -> str:
    """训练结果里的自动训练设置：GPT-SoVITS 放在 params["summary"]（models.json 里也有一份）。"""
    if not isinstance(info, dict):
        return ""
    params = info.get("params")
    if isinstance(params, dict) and isinstance(params.get("summary"), str) and params["summary"].strip():
        return _strip_plan(params["summary"])
    for key in ("plan_text", "auto_plan", "plan", "auto"):
        v = info.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for k2 in ("text", "summary", "message"):
                if isinstance(v.get(k2), str) and v[k2].strip():
                    return v[k2].strip()
    return ""


_PLAN_RE = re.compile(r"(显存.*(batch|每批|轮|DPO))|(自动.*(训练方案|选择).*(轮|batch))", re.I)


def _plan_line(log_text: str) -> str:
    """从运行记录里找 GPT-SoVITS 打印的那行「训练计划：显存 12 GB → 每批 6 条；素材 85 分钟 → …」。"""
    for line in reversed(str(log_text or "").splitlines()):
        msg = line.split(" | ", 1)[-1].strip()
        if msg.startswith(PLAN_PREFIX) or _PLAN_RE.search(msg):
            return _strip_plan(msg)
    return ""


def _plan_md(text: str) -> str:
    return f"🧠 **这次自动选择的训练方案**：{_md_text(_strip_plan(text))}" if text else ""


PLAN_DEFAULT = ("🧠 不用自己调参数：电脑会根据你的显卡（显存）和素材多少，自动选择每批数量、训练轮数和保存间隔，"
                "训练完自动挑出最像你的那一版。具体方案开始训练后会显示在这里。")


def _train_done_md(info: Dict[str, Any], plan: str = "", show_plan: bool = True) -> str:
    """训练完成的说明。show_plan=False：训练页上方已经单独显示了训练方案，这里不再重复。"""
    mins = _num(info.get("train_minutes")) if isinstance(info, dict) else None
    if mins is None:
        head = "### ✅ 训练完成"
    elif mins < 1:  # 素材没变、接着上次练完的：几秒钟就结束了
        head = "### ✅ 训练完成（用时不到 1 分钟）"
    else:
        head = f"### ✅ 训练完成（用时 {mins:g} 分钟）"
    err = info.get("selection_error") if isinstance(info, dict) else None
    plan_md = _plan_md(plan or _plan_text(info)) if show_plan else ""
    if err:
        md = (f"{head}\n\n⚠️ 「自动挑选最像你的模型」这一步没成功（{_md_text(err)}），现在先用最后一轮的模型。"
              "可以稍后点「重新挑选最佳模型」再试。")
    else:
        sel = _selection_info(info)
        best, label = _best_selection({"selection": sel.get("selection"), "selected": info.get("selected")})
        if sel.get("selection"):
            md = (f"{head}\n\n已经自动挑出最像你的版本" + (f"（{_md_text(label)}）" if label else "")
                  + "，并把语速调得和你本人一样。\n\n👉 下一步：去「③ 生成讲课音频」。")
        else:
            md = f"{head}\n\n现在用的是最后一轮的模型。\n\n👉 下一步：去「③ 生成讲课音频」。"
        if best:
            md += f"\n\n<small>版本编号：{_md_text(best)}</small>"
    if plan_md:
        md += "\n\n" + plan_md
    return md


def _select_done_md(info: Dict[str, Any]) -> str:
    best, label = _best_selection({"selection": info.get("selection"), "selected": info.get("selected")})
    speed = info.get("speed") or {}
    calibrated = any(abs((_num(v) or 1.0) - 1.0) > 1e-6 for v in speed.values()) if isinstance(speed, dict) else False
    parts = [x for x in (label, f"版本 {best}" if best else "") if x]
    return ("### ✅ 已重新挑好最像你的模型" + (f"（{_md_text('，'.join(parts))}）" if parts else "")
            + f"；语速：{'已校准' if calibrated else '和你本人一致，不用调'}")


# ============================================================================ ③ 生成结果
def _segments(res: Any) -> List[Dict[str, Any]]:
    segs = getattr(res, "segments", None)
    if segs is None and isinstance(res, dict):
        segs = res.get("segments")
    return [s for s in (segs or []) if isinstance(s, dict)]


def _seg_no(seg: Dict[str, Any], fallback: int) -> int:
    n = seg.get("index")
    try:
        return int(n)
    except (TypeError, ValueError):
        return fallback


def _seg_flagged(seg: Dict[str, Any]) -> bool:
    """这一句要不要提醒重做：以生成引擎的判断为准（seg["flagged"]）；老的报告里没有这个字段时，
    有问题（issues）或低于 85% 就提醒。"""
    if "flagged" in seg:
        return bool(seg.get("flagged"))
    pct = _pct_of(seg)
    return bool(seg.get("issues")) or (pct is not None and pct < PASS_PCT)


def _seg_tips(seg: Dict[str, Any]) -> str:
    """「提示」列：生成引擎写好的提示（低于 85%、可能有读错的字……）+ 具体问题 + 是否沿用上次。"""
    tips = [t for t in str(seg.get("hint") or "").split("；") if t.strip()]
    tips += [str(x) for x in (seg.get("issues") or []) if x]
    if "flagged" not in seg and not tips:  # 老的报告：没有引擎的判断时自己按 85% 提醒
        pct = _pct_of(seg)
        if pct is not None and pct < PASS_PCT:
            tips.append("低于 85%，建议重新生成或改写这一句")
    if seg.get("flagged") and not tips:
        tips.append("这一句可能不够像，建议重新生成或改写")
    if seg.get("cached"):
        tips.append("沿用上次")
    return "；".join(dict.fromkeys(tips))


_STATUS_TEXT = {"🟢": "🟢 比较像", "🔴": "🔴 不够像", "⚠️": "⚠️ 需要注意"}


def _seg_status(seg: Dict[str, Any], pct: Optional[float]) -> str:
    """「状态」列。生成引擎给的是 ✅ / 🟢 / 🔴 / ⚠️（只有声纹模型可靠时才按 85% 淘汰、标红）。"""
    status = str(seg.get("status") or "").strip()
    if status == "✅":
        return "✅ 很像" if pct is not None and pct >= GREAT_PCT else "✅"
    if status in _STATUS_TEXT:
        return _STATUS_TEXT[status]
    if status:
        return status
    if pct is not None:
        return _status_for_pct(pct)
    if seg.get("flagged"):
        return "🔴 可能不够像"
    if seg.get("issues"):
        return "⚠️ 需要注意"
    if seg.get("speaker_sim") is not None:
        return "🙂 " + _label_for_sim(_num(seg.get("speaker_sim")))
    return "✅"


def _gen_rows(res: Any) -> List[List[Any]]:
    """逐句结果表：#（从 1 开始，和「只重新生成第几句」填的编号一样）、句子、像你本人（%）、状态、提示。"""
    rows = []
    for i, s in enumerate(_segments(res), 1):
        pct = _pct_of(s)
        rows.append([_seg_no(s, i), str(s.get("text", "")), _pct_text(pct), _seg_status(s, pct), _seg_tips(s)])
    return rows


def _flagged_numbers(res: Any) -> List[int]:
    flagged = getattr(res, "flagged", None)
    if flagged:
        try:
            return sorted({int(x) for x in flagged})
        except (TypeError, ValueError):
            pass
    return [_seg_no(s, i) for i, s in enumerate(_segments(res), 1) if _seg_flagged(s)]


def _mean_pct(res: Any) -> Optional[float]:
    for key in ("pct", "mean_pct", "overall_pct"):
        v = _num(getattr(res, key, None))
        if v is not None:
            return v
    vals = [p for p in (_pct_of(s) for s in _segments(res)) if p is not None]
    return sum(vals) / len(vals) if vals else None


def _gen_summary_md(res: Any, redo: Optional[Sequence[int]] = None) -> str:
    """生成完成后的说明：多长、存在哪、哪几句可能要重做。不会出现 None 或 Python 字典。"""
    segs = _segments(res)
    md = [f"### ✅ 生成好了：音频长 {_fmt_duration(getattr(res, 'duration', 0))}，共 {len(segs)} 句"]
    if redo:
        md.append("已重新生成第 " + "、".join(str(int(x)) for x in redo) + " 句。")
    mean = _mean_pct(res)
    sims = [x for x in (_num(s.get("speaker_sim")) for s in segs) if x is not None]
    if mean is not None:
        md.append(f"整体听起来：像你本人 **{mean:.1f}%**（每句的平均）")
        if _report_field(res, "similarity_filter") is False:
            md.append(MFCC_NOTE)
    elif sims:
        avg = sum(sims) / len(sims)
        md.append(f"整体听起来：{_label_for_sim(avg)}（平均相似度 {avg:.2f}）")
    audio = getattr(res, "audio_path", "")
    if audio:
        srt = getattr(res, "srt_path", None)
        md.append(f"已保存到：`{str(audio).replace('`', '')}`" + ("（同一个文件夹里还有同名的 .srt 字幕）" if srt else ""))
    flagged = _flagged_numbers(res)
    if flagged:
        nums = "、".join(str(n) for n in flagged)
        md.append(f"⚠️ 第 {nums} 句可能有问题（下面的表格里写了原因）。想重做的话，在「只重新生成第几句」里填："
                  f"{','.join(str(n) for n in flagged)}，再点「生成」，只重做这几句，很快。")
    others = [w for w in (getattr(res, "warnings", None) or []) if not re.match(r"^第\s*\d+\s*句[：:]", str(w))]
    if others:
        md.append("\n".join(f"> ⚠️ {_md_text(w)}" for w in others[:10])
                  + (f"\n>\n> 还有 {len(others) - 10} 条" if len(others) > 10 else ""))
    # 生成引擎的小结：平均每句试了几次、几句达到了「完美」的严格标准……（整篇百分比、要注意的句子上面已经说了）
    notes = [str(n) for n in (getattr(res, "notes", None) or [])
             if str(n).strip() and not str(n).startswith(("整篇像你本人", "需要注意的句子", "没有需要特别注意"))]
    if notes:
        md.append("<small>" + "<br>".join(_md_text(n) for n in notes[:6]) + "</small>")
    if mean is not None or sims:
        md.append(f"<small>{HONEST_SIM}{PCT_HELP if mean is not None else ''}</small>")
    return "\n\n".join(md)


def _report_field(res: Any, key: str) -> Any:
    """读这次生成报告（*.report.json）里的一个字段；读不到时返回 None。"""
    path = getattr(res, "report_path", None)
    try:
        if path and Path(str(path)).exists():
            return json.loads(Path(str(path)).read_text(encoding="utf-8")).get(key)
    except Exception:
        pass
    return None


def _variants(res: Any) -> List[Dict[str, Any]]:
    vs = getattr(res, "variants", None)
    if vs is None and isinstance(res, dict):
        vs = res.get("variants")
    return [v for v in (vs or []) if isinstance(v, dict) and v.get("path")]


def _variant_letter(v: Dict[str, Any], i: int) -> str:
    name = str(v.get("name") or "")
    if name == "未去杂音":
        return "A"
    if name == "去杂音":
        return "B"
    return "AB"[i] if i < 2 else str(i + 1)


def _variant_score_text(v: Dict[str, Any]) -> str:
    pct = _pct_of(v)
    if pct is not None:
        return f"像你本人 {pct:.1f}%"
    sc = _num(v.get("score"))
    return f"相似度 {sc:.3f}" if sc is not None else ""


def _variant_title(v: Dict[str, Any], i: int) -> str:
    score = _variant_score_text(v)
    return f"版本 {_variant_letter(v, i)}：{v.get('name') or ''}" + (f"（{score}）" if score else "")


def _variants_md(vs: Sequence[Dict[str, Any]]) -> str:
    """「完美」质量的两个版本：分数、推荐哪个。"""
    if len(vs) < 2:
        return ""
    lines = ["#### 🎧 这次做了两个版本，听一听，选你更喜欢的"]
    for i, v in enumerate(vs):
        star = "　⭐ 推荐：更像你的原声" if v.get("recommended") else ""
        lines.append(f"{i + 1}. **{_md_text(_variant_title(v, i))}**{star}")
    rec_i = next((i for i, v in enumerate(vs) if v.get("recommended")), None)
    if rec_i is not None:
        rec = vs[rec_i]
        other = [v for j, v in enumerate(vs) if j != rec_i]
        gap = ""
        pr, po = _pct_of(rec), _pct_of(other[0]) if other else None
        sr, so = _num(rec.get("score")), _num(other[0].get("score")) if other else None
        if pr is not None and po is not None and pr - po >= 0.05:
            gap = f"（高 {pr - po:.1f} 个百分点）"
        elif pr is not None and po is not None and po - pr >= 0.05:
            # 推荐是按综合得分挑的（声纹为主，再扣语速、音高的偏差），所以百分比可能反而低一点：照实说
            extra = f"，但综合得分高 {abs(sr - so):.3f}" if sr is not None and so is not None else ""
            gap = f"（百分比低 {po - pr:.1f}{extra}：语速、音高更接近你平时说话）"
        elif sr is not None and so is not None and abs(sr - so) >= 0.0005:
            # 百分比一样时按综合得分推荐（声纹为主，再看语速、音高和你本人差多少）
            gap = f"（百分比差不多，综合得分高 {abs(sr - so):.3f}）" if pr is not None else f"（相似度高 {abs(sr - so):.3f}）"
        elif pr is not None or sr is not None:
            gap = "（两个版本几乎一样像，听哪个顺耳就用哪个）"
        lines.append(f"\n⭐ 推荐：版本 {_variant_letter(rec, rec_i)}，更像你的原声{gap}")
    lines.append(f"\n<small>两个版本的文字、停顿和字幕完全一样，只是 B 去掉了轻微的杂音。{HONEST_SIM}</small>")
    return "\n".join(lines)


def _gen_files(audio: Any, srt: Any, vs: Sequence[Dict[str, Any]]) -> List[str]:
    """「下载（音频 / 字幕）」列表：最终音频、字幕、两个版本各自的文件（只列硬盘上真有的）。"""
    audio = str(audio or "")
    files = [audio] + ([str(srt)] if srt else []) + [str(x.get("path") or "") for x in vs
                                                      if str(x.get("path") or "") != audio]
    return [f for f in dict.fromkeys(files) if f and Path(f).exists()]


def _recommended_variant(vs: Sequence[Dict[str, Any]]) -> str:
    for v in vs:
        if v.get("recommended"):
            return str(v.get("name") or "")
    return str(vs[0].get("name") or "") if vs else ""


def _speed_factor(value: Any) -> float:
    """语速滑块（−30…+30）→ 合成用的语速系数：往左（负数）更快，往右（正数）更慢。"""
    v = _num(value) or 0.0
    v = max(-30.0, min(30.0, round(v)))
    return round(1.0 - v / 100.0, 2)


def _speed_text(value: Any) -> str:
    v = int(max(-30.0, min(30.0, round(_num(value) or 0.0))))
    if v == 0:
        return "当前：和你原声一样"
    return f"当前：比你原声{'快' if v < 0 else '慢'} {abs(v)}%"


def _first_sentence(text: str, limit: int = 40) -> str:
    text = str(text or "").strip()
    if not text:
        return ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("[") and line.endswith("]"):
            continue
        m = re.match(r"(.+?[。！？!?.；;])", line)
        s = (m.group(1) if m else line).strip()
        return s[:limit]
    return ""


def _output_path(project: Any, name: str, fmt: str, fallback: str) -> Path:
    from voicetwin.utils.textutil import safe_name

    stem = safe_name((name or "").strip() or fallback or "讲课音频", 30)
    fmt = fmt if fmt in ("wav", "mp3") else "wav"
    return Path(project.outputs_dir) / f"{stem}_{_time_suffix()}.{fmt}"


def _time_suffix(t: Optional[float] = None) -> str:
    """文件名里的时间「10月01日21点30分」。中文字不能放进 strftime 的格式里：
    Windows 上的 Python 3.9 会按系统的非 Unicode 语言（例如英文系统的 cp1252）编码格式串，遇到「月」就报错。"""
    lt = time.localtime(t)
    return f"{lt.tm_mon:02d}月{lt.tm_mday:02d}日{lt.tm_hour:02d}点{lt.tm_min:02d}分"


# ============================================================================ ④ 评估
_EVAL_SKIP = {"结论", "声纹相似度", "相似度参考", "说明"}  # 「说明」和卡片最后那行诚实提示是同一句话


def _flat(v: Any) -> str:
    if isinstance(v, dict):
        return "；".join(f"{k}：{_flat(x)}" for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return "；".join(_flat(x) for x in v) or "无"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".")
    return "—" if v is None else str(v)


def _eval_md(result: Dict[str, Any]) -> str:
    """把 evaluate_file 的结果画成一张卡片（键名不认识的也会以「名字：值」显示，不出现 Python 字典）。"""
    if not isinstance(result, dict) or not result:
        return ""
    pct = _pct_of(result)
    sim = _num(result.get("声纹相似度"))
    concl = str(result.get("结论") or "")
    icon = "🙂" if (pct or 0) >= PASS_PCT or concl in ("非常像", "比较像") else "🤔"
    if pct is not None:
        head = f"## {icon} 像你本人 {pct:.1f}%" + (f"（{_md_text(concl)}）" if concl else "")
    elif concl:
        head = f"## {icon} {_md_text(concl)}" + (f"（{sim:.2f}）" if sim is not None else "")
    else:
        head = "## 评估结果"
    lines = [head]
    if result.get("相似度参考"):
        lines.append(f"<small>参考：{_md_text(result['相似度参考'])}</small>")
    for k, v in result.items():
        if k in _EVAL_SKIP or k in _PCT_KEYS:
            continue
        lines.append(f"- {_md_text(k)}：{_md_text(_flat(v))}")
    lines.append(f"\n<small>{HONEST_SIM}{PCT_HELP}</small>")
    return "\n".join(lines)


# ============================================================================ 环境检查
def _sort_doctor(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fn = getattr(wf, "sort_doctor_rows", None)
    if callable(fn):
        try:
            return list(fn(rows))
        except Exception:
            pass
    order = {"❌": 0, "⚠️": 1, "✅": 2}
    return sorted(rows, key=lambda r: order.get(str(r.get("status")), 1))


def _doctor_advice(row: Dict[str, Any]) -> str:
    item, detail = str(row.get("item", "")), str(row.get("detail", ""))
    if "预训练模型" in detail or "download-models" in detail:
        return "点上面的「⬇️ 下载缺少的模型」按钮"
    if "ffmpeg" in item.lower() or item == "Python":
        return "请重新双击 install_windows.bat 安装一次（你的数据不会丢）"
    if "显卡" in item or "PyTorch" in item:
        return ("请到 https://www.nvidia.cn/drivers/lookup/ 下载安装最新显卡驱动，然后重启电脑；"
                "RTX 50 系列请使用 nvidia50 版整合包")
    if "找不到 GPT-SoVITS" in detail:
        return "请重新双击 install_windows.bat，按提示填写 GPT-SoVITS 整合包的位置"
    return detail


def _doctor_view(rows: Sequence[Dict[str, Any]]) -> Tuple[str, List[List[Any]], str, List[List[Any]], str]:
    """环境检查结果 → (结论, 主表, 主表总数, 可选组件表, 可选组件总数)。问题排在前面，每行有编号。"""
    rows = _sort_doctor([dict(r) for r in rows])
    main = [r for r in rows if not r.get("optional")]
    opt = [r for r in rows if r.get("optional")]
    bad = [r for r in main if r.get("status") == "❌"]
    warn = [r for r in main if r.get("status") == "⚠️"]
    if bad:
        summary = (f"### ❌ 有 {len(bad)} 项需要处理（处理完点「🔄 重新检查」）\n\n"
                   + "\n".join(f"{i}. **{_md_text(r.get('item', ''))}**：{_md_text(_doctor_advice(r))}"
                               for i, r in enumerate(bad, 1)))
    else:
        summary = "### ✅ 一切正常，可以开始使用" + (f"（有 {len(warn)} 项提醒，不影响使用）" if warn else "")
    main_rows = [[i, r.get("status", ""), r.get("item", ""), r.get("detail", "")] for i, r in enumerate(main, 1)]
    opt_rows = [[i, r.get("status", ""), r.get("item", ""), r.get("detail", "")] for i, r in enumerate(opt, 1)]
    return summary, main_rows, f"共 {len(main_rows)} 项", opt_rows, f"共 {len(opt_rows)} 项"


def _quick_problems(cfg: Config) -> List[str]:
    """打开网页时的快速检查（wf.quick_check：只看文件，不运行任何程序）。出错时不提示任何东西。"""
    try:
        return [str(x) for x in (wf.quick_check(cfg) or []) if x]
    except Exception as exc:
        log.debug(f"quick_check 出错：{exc}")
        return []


def _quick_html(problems: Sequence[str]) -> str:
    if not problems:
        return ""
    if len(problems) == 1:
        return render_notice_html("⚠️ 还差一步：" + problems[0], "error")
    return render_notice_html("⚠️ 还差几步：\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(problems, 1)), "error")


# ============================================================================ 后台任务（在 stream_task 的后台线程里运行）
def _prepare_job(cfg: Config, voice: str, upload_paths: Sequence[str], folder: str,
                 overrides: Dict[str, Any], progress: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
    """把上传的文件放进这个声音的 uploads 文件夹（硬链接或流式复制，不整个读进内存；同名同大小的不再复制），
    然后运行素材准备。已经处理过的文件按路径识别，不会重做。"""
    inputs: List[str] = []
    if upload_paths:
        updir = wf.Project(cfg, voice).root / "uploads"
        updir.mkdir(parents=True, exist_ok=True)
        n = len(upload_paths)
        for k, raw in enumerate(upload_paths, 1):
            src = Path(raw)
            dst = updir / src.name
            try:
                same = dst.exists() and dst.stat().st_size == src.stat().st_size
            except OSError:
                same = False
            if not same:
                if dst.exists():
                    dst.unlink()
                try:
                    os.link(str(src), str(dst))
                except OSError:
                    shutil.copyfile(str(src), str(dst))
            if progress:
                progress(0.02 * k / n, f"整理上传的文件 {k}/{n}：{src.name}")
        inputs.append(str(updir))
    if folder:
        inputs.append(folder)
    return wf.run_prepare(cfg, voice, inputs, progress=progress, overrides=overrides)


def _download_job(cfg: Config, progress: Optional[Callable[[float, str], None]] = None) -> List[str]:
    """下载 GPT-SoVITS 缺少的预训练模型（和命令行 voicetwin download-models 一样；下载时电脑不会自动睡眠）。"""
    return wf.download_models(cfg, "auto", progress=progress)


def _latest_report(project: Any) -> Dict[str, Any]:
    reports = sorted(Path(project.outputs_dir).glob("*.report.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in reports:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_path"] = str(p)
            return data
        except Exception:
            continue
    return {}


def _report_labels(report: Dict[str, Any], project: Any = None) -> Dict[str, str]:
    """一次生成里每个音频文件 → 给老师看的名字（「版本 A：未去杂音」「第 3 句：……」）。"""
    out: Dict[str, str] = {}
    for i, v in enumerate(report.get("variants") or []):
        if isinstance(v, dict) and v.get("path"):
            out[str(v["path"])] = f"版本 {_variant_letter(v, i)}：{v.get('name') or ''}（{Path(str(v['path'])).name}）"
    if report.get("audio") and str(report["audio"]) not in out:
        out[str(report["audio"])] = f"整篇：{Path(str(report['audio'])).name}"
    if project is not None:
        for k, seg in enumerate(report.get("segments") or [], 1):
            clip = seg.get("clip") if isinstance(seg, dict) else None
            if clip:
                try:
                    text = str(seg.get("text") or "")
                    out[str(project.abspath(str(clip)))] = (f"第 {_seg_no(seg, k)} 句：{text[:16]}"
                                                            + ("…" if len(text) > 16 else ""))
                except Exception:
                    pass
    return out


def _report_audio_files(report: Dict[str, Any], project: Any = None, max_clips: int = 20) -> List[str]:
    """一次生成的所有音频：两个版本（或最终音频）+ 前 max_clips 句的单句音频（机器鉴别默认就比这些）。"""
    files: List[str] = []
    for v in report.get("variants") or []:
        if isinstance(v, dict) and v.get("path"):
            files.append(str(v["path"]))
    if report.get("audio") and not files:  # 有两个版本时，最终音频只是其中一个的复制品
        files.append(str(report["audio"]))
    if project is not None:
        for seg in (report.get("segments") or [])[:max_clips]:
            clip = seg.get("clip") if isinstance(seg, dict) else None
            if clip:
                try:
                    files.append(str(project.abspath(str(clip))))
                except Exception:
                    pass
    seen, out = set(), []
    for f in files:
        if f not in seen and Path(f).exists():
            seen.add(f)
            out.append(f)
    return out


ATTACH_MISSED_MD = "刚才那个任务已经做完了，页面上已经换成最新的结果。"


def _attach_missed(*args: Any, **kwargs: Any) -> None:
    """接上正在进行的任务时用的占位函数：stream_task 发现同一个任务还在做就直接接上，不会调用它；
    万一任务恰好在这一瞬间做完了，它什么也不做（不会用空的输入重新开始一次）。"""
    return None


def _verify_job(cfg: Config, voice: str, originals: Sequence[str], generated: Sequence[str],
                progress: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
    """机器鉴别：wf.verify_files 用几个声纹模型分别打分再平均（注意它的参数顺序是 generated 在前）。"""
    return wf.verify_files(cfg, voice, generated=list(generated), originals=list(originals) or None,
                           progress=progress)


def _blind_job(cfg: Config, voice: str, n: int, quality: str,
               progress: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
    """观众盲听测试：wf.build_blind_test 挑 n 段真实录音、用现在最好的模型读同样的文字，打乱顺序编号。"""
    return dict(wf.build_blind_test(cfg, voice, n=n, quality=quality, progress=progress) or {})


def _model_label(name: str) -> str:
    try:
        from voicetwin.eval.speaker import MODEL_LABELS

        return str(MODEL_LABELS.get(name, name))
    except Exception:
        return str(name)


def _verify_rows(result: Dict[str, Any], labels: Optional[Dict[str, str]] = None) -> Tuple[List[List[Any]], str]:
    """机器鉴别结果 → 按综合 % 从高到低排名的表格（#、文件、各模型 %、综合 %、排名、是否 ≥85%）+ 总结。

    labels：{文件的绝对路径: 给老师看的名字}，例如单句音频显示成「第 2 句：今天我们……」而不是一串字母数字。"""
    labels = labels or {}
    rows = [r for r in (result.get("rows") or result.get("files") or []) if isinstance(r, dict)]
    min_pct = _num(result.get("min_pct")) or PASS_PCT
    ranked = sorted(rows, key=lambda r: (_pct_of(r) is None, -(_pct_of(r) or 0.0)))
    table = []
    for i, r in enumerate(ranked, 1):
        pcts = r.get("pcts") if isinstance(r.get("pcts"), dict) else r.get("models")
        sims = r.get("sims") if isinstance(r.get("sims"), dict) else r.get("raw")
        parts = []
        for name, v in (pcts or {}).items() if isinstance(pcts, dict) else []:
            raw = _num((sims or {}).get(name)) if isinstance(sims, dict) else None
            parts.append(f"{_model_label(name)} {_pct_text(_num(v))}" + (f"（原始 {raw:.3f}）" if raw is not None else ""))
        if not parts and isinstance(sims, dict):
            parts = [f"{_model_label(k)} 原始 {_num(v) or 0:.3f}" for k, v in sims.items()]
        pct = _pct_of(r)
        passed = r.get("pass")
        if passed is None:
            passed = pct is not None and pct >= min_pct
        mark = "—" if pct is None else ("✅ 是" if passed else "🔴 否")
        name = labels.get(str(r.get("path") or "")) or Path(str(r.get("file") or r.get("path") or "")).name
        table.append([i, name, "；".join(parts) or "—", _pct_text(pct), int(r.get("rank") or i), mark])
    n_pass = sum(1 for row in table if row[5] == "✅ 是")
    info = result.get("models") if isinstance(result.get("models"), dict) else {}
    model_labels = [str(x) for x in (info.get("labels") or [])]
    lines = [f"### 🤖 鉴别完成：共 {len(ranked)} 个文件，其中 {n_pass} 个 ≥ {min_pct:.0f}%"]
    if model_labels:
        lines.append("用到的声纹模型：" + "、".join(_md_text(x) for x in model_labels)
                     + ("（几个模型分别打分，「综合 %」是它们的平均）" if len(model_labels) > 1 else ""))
    n_orig = len(result.get("originals") or [])
    source = str(result.get("calibration_source") or ("uploaded_loo" if n_orig >= 3 else ""))
    if n_orig and source == "uploaded_loo":
        lines.append(f"「100%」的标准：你选的 {n_orig} 段原始录音彼此之间有多像。")
    elif n_orig and source == "voice_clips_vs_uploaded":
        lines.append(f"「100%」的标准：素材里留出来的你的真实录音，和你选的这 {n_orig} 段原始录音有多像"
                     "（选的不到 3 段，没法让它们互相比）。")
    elif n_orig and source in ("voice_calibration", "val", "train_unused", "train"):
        lines.append(f"你只选了 {n_orig} 段原始录音（不到 3 段）：「100%」的标准改用这个声音素材里你自己的真实录音。")
    elif n_orig and source == "mixed":
        lines.append(f"「100%」的标准：参考了你选的 {n_orig} 段原始录音和素材里你自己的真实录音。")
    if result.get("calibrated") is False:
        lines.append("⚠️ 你的真实录音太少，百分比只能粗略参考。")
    elif info.get("reliable") is False:
        lines.append(MFCC_NOTE.replace("，也不会按 85% 自动淘汰", ""))
    lines.append(f"<small>{HONEST_SIM}{PCT_HELP}</small>")
    return table, "\n\n".join(lines)


_REAL_WORDS = {"真人", "real", "human", "原声", "真人录音", "original", "recording", "true", "1", "yes"}
_FAKE_WORDS = {"生成", "generated", "fake", "synth", "synthetic", "tts", "合成", "ai", "false", "0", "no", "clone"}


def _is_real_value(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in _REAL_WORDS:
        return True
    if s in _FAKE_WORDS:
        return False
    return None


def _item_no(v: Any) -> Optional[int]:
    m = re.search(r"\d+", str(v))
    return int(m.group(0)) if m else None


def _blind_answers(data: Any) -> Dict[int, bool]:
    """读盲听测试的答案（答案.json）：返回 {第几段: 是不是真人}。兼容几种常见写法。"""
    if isinstance(data, dict):
        for key in ("answers", "items", "answer"):
            if key in data and isinstance(data[key], (list, dict)):
                return _blind_answers(data[key])
        out: Dict[int, bool] = {}
        for k, v in data.items():
            n, real = _item_no(k), _is_real_value(v if not isinstance(v, dict) else
                                                   v.get("kind", v.get("type", v.get("answer", v.get("is_real")))))
            if n is not None and real is not None:
                out[n] = real
        return out
    out = {}
    for i, it in enumerate(data or [], 1):
        if not isinstance(it, dict):
            real = _is_real_value(it)
            if real is not None:
                out[i] = real
            continue
        n = None
        for key in ("index", "no", "n", "number", "id", "file", "name", "path"):
            if it.get(key) is not None:
                n = _item_no(Path(str(it[key])).name if key in ("file", "path") else it[key])
                if n is not None:
                    break
        real = None
        for key in ("is_real", "real", "kind", "type", "answer", "label", "source", "truth"):
            if key in it:
                real = _is_real_value(it[key])
                if real is not None:
                    break
        if real is not None:
            out[n if n is not None else i] = real
    return out


def _blind_dir(result: Dict[str, Any]) -> str:
    for key in ("dir", "folder", "out_dir", "path", "root"):
        v = result.get(key)
        if v and Path(str(v)).is_dir():
            return str(v)
    for key in ("answer_path", "answers_path", "answer_file", "card_path"):
        v = result.get(key)
        if v and Path(str(v)).exists():
            return str(Path(str(v)).parent)
    return ""


def _blind_items(result: Dict[str, Any]) -> List[str]:
    items: List[str] = []
    for it in result.get("items") or result.get("files") or []:
        p = it if isinstance(it, str) else (it.get("path") or it.get("file") or it.get("audio")) if isinstance(it, dict) else None
        if p:
            path = Path(str(p))
            if not path.is_absolute() and _blind_dir(result):
                path = Path(_blind_dir(result)) / path
            items.append(str(path))
    if not items and _blind_dir(result):
        items = sorted(glob.glob(os.path.join(_blind_dir(result), "[0-9]*.wav")))
    return items[:MAX_BLIND]


def _blind_answer_file(result: Dict[str, Any]) -> str:
    for key in ("answer_path", "answers_path", "answer_file"):
        v = result.get(key)
        if v and Path(str(v)).exists():
            return str(v)
    d = _blind_dir(result)
    if not d:
        return ""
    finder = getattr(wf, "blind_answer_path", None)
    p = Path(finder(d)) if callable(finder) else Path(d) / "答案.json"
    return str(p) if p.exists() else ""


def _blind_verdict(acc: float) -> str:
    if acc <= 0.60:
        return "👍 听众基本分辨不出（和乱猜的 50% 差不多）。"
    if acc <= 0.80:
        return "🙂 有时能分辨出来。"
    return ("🤔 比较容易分辨出来。可以试试：多加一些讲课素材、认真校对文字、"
            "用「完美」质量重新生成。")


def _blind_result_md(choices: Sequence[Any], answers: Dict[int, bool]) -> str:
    lines = ["| # | 你的选择 | 正确答案 | 对不对 |", "|---|---|---|---|"]
    answered = correct = 0
    for i, ch in enumerate(choices, 1):
        if i not in answers:
            continue
        truth = "真人" if answers[i] else "生成"
        if ch in ("real", "fake"):
            answered += 1
            mine = "真人" if ch == "real" else "生成"
            ok = (ch == "real") == answers[i]
            correct += int(ok)
            lines.append(f"| {i} | {mine} | {truth} | {'✅' if ok else '❌'} |")
        else:
            lines.append(f"| {i} | （没选） | — | — |")  # 没答的不显示答案（不然答一段就能看到全部答案）
    if not answered:
        return "⚠️ 还没有选任何一段。请先在每段下面选「真人」或「生成」，再点「提交答案」。"
    acc = correct / answered
    head = (f"### 👂 盲听结果：答了 {answered} 段，答对 {correct} 段，正确率 **{acc:.0%}**\n\n"
            f"{_blind_verdict(acc)}\n\n")
    return head + "\n".join(lines)


def _blind_missing(choices: Sequence[Any], answers: Dict[int, bool]) -> List[int]:
    """还没选「真人 / 生成」的编号。"""
    return [i for i in sorted(answers) if i - 1 >= len(choices) or choices[i - 1] not in ("real", "fake")]


def _blind_grade_md(g: Dict[str, Any], name: str = "") -> str:
    """批改收上来的答题卡（wf.grade_blind_test 的结果）。没答的题不显示答案。"""
    if not g.get("answered"):
        return ("⚠️ 没看懂填的答案。请这样填：`1 真人 2 生成 3 真人 ……`，"
                "或者不写编号、按顺序写：`真人 生成 真人 ……`。")
    lines = ["| # | 听众的答案 | 正确答案 | 对不对 |", "|---|---|---|---|"]
    for r in g.get("items") or []:
        if r.get("answer") in (None, "", "（没答）"):
            lines.append(f"| {r.get('no')} | （没答） | — | — |")
        else:
            lines.append(f"| {r.get('no')} | {r.get('answer')} | {r.get('truth')} | {'✅' if r.get('correct') else '❌'} |")
    head = (f"### 📝 {_md_text(name) + '：' if name else ''}答了 {g.get('answered')} 段（共 {g.get('total')} 段），"
            f"答对 {g.get('correct')} 段，正确率 **{g.get('pct')}%**\n\n{_md_text(g.get('verdict') or '')}\n\n")
    tips = g.get("tips") or []
    tail = ("\n\n可以试试：\n" + "\n".join(f"- {_md_text(t)}" for t in tips)) if tips else ""
    return head + "\n".join(lines) + tail


def _blind_test_choices(cfg: Config, voice: Any) -> List[Tuple[str, str]]:
    v = _voice_name(voice)
    fn = getattr(wf, "list_blind_tests", None)
    if not v or not callable(fn):
        return []
    try:
        tests = fn(cfg, v)
    except Exception as exc:
        log.debug(f"列出盲听测试失败：{exc}")
        return []
    return [(f"{t['name']}（{t.get('count', 0)} 段{('，' + t['created']) if t.get('created') else ''}）", t["dir"])
            for t in tests]


#: 点过第一次、还没确认也还没过期的停止按钮（记的是第一次点的时间）
_STOP_ARMED: set = set()


def _float_or_zero(v: Any) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


class _StopOnce:
    """长任务进行中的停止按钮：只在第一次刷新时显示出来，之后不再改它。

    否则每 0.6 秒刷新一次进度条时，都会把「再点一次确认停止（5 秒内）」/「正在停止……」改回「⏹ 停止」
    （浏览器里实测：确认的字一闪就没了）。"""

    def __init__(self) -> None:
        self.shown = False

    def __call__(self) -> Dict[str, Any]:
        if self.shown:
            return _upd()
        self.shown = True
        return _upd(visible=True, value=STOP_LABEL, interactive=True)


# ============================================================================ 网页
class WebUI:
    """网页的全部处理函数。build() 画页面；其余方法都可以在没有 gradio 4.24 的环境里直接调用测试。"""

    # 每个流式按钮的输出（顺序就是 build() 里 outputs 的顺序）
    PREP_OUT = ("prep_bar", "prep_log", "prep_md", "voice", "clips_count", "prep_btn", "prep_stop",
                "voice_status", "prep_next", "clips_base")
    TRAIN_OUT = ("train_bar", "train_log", "train_md", "train_btn", "select_btn", "train_stop", "voice_status",
                 "train_next", "train_plan")
    GEN_OUT = ("gen_bar", "out_audio", "out_files", "gen_log", "gen_md", "gen_btn", "gen_stop", "redo", "gen_table",
               "var_box", "var_md", "var_a", "var_b", "var_choice", "gen_state", "speed_try", "gen_after", "var_note")
    SPEED_OUT = ("gen_bar", "gen_log", "speed_audio", "speed_try", "gen_btn", "gen_stop")
    PROOF_OUT = ("proof_bar", "proof_md", "clips_count", "proof_btn", "proof_stop", "prep_log")
    DL_OUT = ("doc_bar", "doc_log", "doc_md", "dl_btn", "dl_stop")
    VERIFY_OUT = ("vf_bar", "vf_md", "vf_table", "vf_btn", "vf_log")
    BLIND_OUT = (("bt_bar", "bt_md", "bt_btn", "bt_state", "bt_submit", "bt_result", "vf_log")
                 + tuple(f"bt_audio_{i}" for i in range(MAX_BLIND)) + tuple(f"bt_pick_{i}" for i in range(MAX_BLIND)))
    VOICE_OUT = ("voice_status", "clips_count", "clips", "gen_warn", "clip_diff", "adopt_btn", "sel_clip", "clip_audio")
    LIB_OUT = ("lib_acc", "lib_table", "lib_total")

    def __init__(self, cfg: Config, local: bool = True):
        self.cfg = cfg
        self.local = bool(local)
        self.c: Dict[str, Any] = {}
        self._doc_cache: Optional[Tuple[float, List[Dict[str, Any]]]] = None
        self.default_backend = str(cfg.get("backend") or "gptsovits")
        self.synth_backends = list(SYNTH_BACKENDS) + ([DUMMY_BACKEND] if self.default_backend == "dummy" else [])
        values = [v for _, v in self.synth_backends]
        self.default_synth = self.default_backend if self.default_backend in values else "gptsovits"
        train_values = [v for _, v in TRAIN_BACKENDS]
        self.default_train = self.default_backend if self.default_backend in train_values else "gptsovits"

    # ------------------------------------------------------------------ 输出拼装
    @staticmethod
    def _o(names: Sequence[str], **values: Any) -> Tuple[Any, ...]:
        """按输出名字拼出一次 yield 的值；没给的输出是「不变」。写错名字会直接报错（防止漏改）。"""
        unknown = set(values) - set(names)
        if unknown:
            raise KeyError(f"未知的输出：{sorted(unknown)}")
        return tuple(values[n] if n in values else _upd() for n in names)

    @staticmethod
    def _busy_btn(label: str) -> Dict[str, Any]:
        return _upd(interactive=False, value=label)

    @staticmethod
    def _idle_btn(label: str) -> Dict[str, Any]:
        return _upd(interactive=True, value=label)

    @staticmethod
    def _stop_hidden() -> Dict[str, Any]:
        return _upd(visible=False, value=STOP_LABEL, interactive=True)

    @staticmethod
    def _notice(text: str, tone: str = "warn") -> str:
        return render_notice_html(text, tone)

    def _final_md(self, st: Dict[str, Any], what: str, voice: str) -> str:
        if st.get("stopped"):
            return STOPPED_MD
        f = st.get("friendly") or st.get("error")
        if f is not None:
            return _friendly(f, what, _log_path(self.cfg, voice))
        return ""

    @staticmethod
    def _attaching(kind: str, voice: str) -> bool:
        """同一种任务、同一个声音正在后台做（例如刷新网页后再点一次同一个按钮）：直接接上看进度，
        不检查输入框（刷新后输入框是空的）。"""
        info = current_task()
        return bool(info and info.get("running") and info.get("kind") == kind
                    and str(info.get("voice") or "") == str(voice or ""))

    @staticmethod
    def _other_task(kind: str, voice: str) -> str:
        """另一件事正在做（不是同一种任务、同一个声音）时的说明；没有时返回 ''。

        在检查输入之前先说这个：例如素材还在准备时点「开始训练」，应该说「正在准备素材，请等它完成」，
        而不是「这个声音还没有准备素材」。"""
        info = current_task()
        if not info or not info.get("running"):
            return ""
        if info.get("kind") == kind and str(info.get("voice") or "") == str(voice or ""):
            return ""
        snap = info.get("snap") or {}
        who = f"（声音：{info['voice']}）" if info.get("voice") else ""
        tab = KIND_TABS.get(str(info.get("kind")), "")
        return (f"现在正在「{info.get('label')}」{who}，已经进行 {format_elapsed(snap.get('elapsed'))}"
                f"（{snap.get('pct', 0)}%）。同一时间只能做一件事，请等它完成后再点。"
                + (f"进度可以在「{tab}」页看到。" if tab else ""))

    @staticmethod
    def _missed(attach: bool, st: Dict[str, Any]) -> bool:
        return bool(attach and "value" in st and st.get("value") is None and not st.get("error"))

    def _project(self, voice: str) -> Tuple[Optional[Any], str]:
        """(Project, 出错说明)。名字不合法时返回说明而不是抛异常。"""
        try:
            return wf.Project(self.cfg, voice), ""
        except ValueError as exc:
            return None, "⚠️ " + str(exc)

    # ------------------------------------------------------------------ 顶部：声音、显卡、声音库
    def on_voice_change(self, voice: Any, only_sus: bool = False, backend: Any = None) -> Tuple[Any, ...]:
        v = _voice_name(voice)
        try:
            table = _clips_table(self.cfg, v, bool(only_sus)) if v else []
        except ValueError:
            table = []
        return self._o(self.VOICE_OUT, voice_status=_voice_status_md(self.cfg, v), clips_count=_clips_count_md(self.cfg, v),
                       clips=table, gen_warn=_gen_warn_md(self.cfg, v, backend or self.default_synth), clip_diff="",
                       adopt_btn=_btn(ADOPT_BTN, visible=False), sel_clip="", clip_audio=_upd(value=None, visible=False))

    def refresh_voices(self, current: Any = None) -> Dict[str, Any]:
        names = _voices(self.cfg)
        value = _voice_name(current) or (names[0] if names else DEFAULT_VOICE)
        return _upd(choices=names, value=value)

    def library(self, open_it: Optional[bool] = None) -> Tuple[Any, ...]:
        entries = _library_entries(self.cfg)
        acc = _upd(label=_library_label(len(entries))) if open_it is None else \
            _upd(label=_library_label(len(entries)), open=bool(open_it and entries))
        return self._o(self.LIB_OUT, lib_acc=acc, lib_table=_library_rows(entries), lib_total=_library_total_md(len(entries)))

    def on_library_pick(self, table: Any, row: int) -> Tuple[Any, Any]:
        """点声音库的某一行：选中这个声音（下拉框跟着变），播放它的主参考音频。"""
        name = _clean_cell(_cell(table, LIB_HEADERS, row, "名称"))
        if not name:
            return _upd(), _upd()
        ref = ""
        for e in _library_entries(self.cfg):
            if e["name"] == name:
                ref = e.get("main_reference") or ""
                break
        audio = _upd(value=ref or None, visible=True,
                     label=f"▶ 试听这个声音：{name}" + ("" if ref else "（还没有参考录音）"))
        return _upd(value=name), audio

    def on_load(self) -> Tuple[Any, ...]:
        """打开（或刷新）网页时：声音列表、当前声音的状态和片段、后台任务提示、快速检查、声音库。"""
        info = current_task()
        running_voice = str(info.get("voice") or "") if info and info.get("running") else ""
        # 后台有任务在做时，直接选中那个声音：再点同一个按钮就能接上进度（而不是提示「正在做别的事」）
        voice_upd = self.refresh_voices(running_voice or None)
        v = voice_upd.get("value") or ""
        status = self.on_voice_change(v)
        banner = task_banner_md()
        lib = self.library(open_it=True)
        quick = _quick_html(_quick_problems(self.cfg))
        return status + (voice_upd, _upd(value=banner, visible=bool(banner)), _upd(value=quick, visible=bool(quick))) + lib

    def on_load_gpu(self) -> Tuple[Any, Any, Any]:
        """打开网页时检查显卡，并按显卡推荐默认的生成质量。"""
        status = _gpu_status(refresh=False)
        q, note = _recommended_quality(status)
        return _gpu_badge(status), _upd(value=q), f"{QUALITY_NOTE}\n\n{note}"

    def refresh_gpu(self) -> str:
        return _gpu_badge(_gpu_status(refresh=True))

    def after_task(self) -> Tuple[Any, ...]:
        """每个长任务结束后：刷新显卡状态、声音库；页面顶部只在还有任务在做时显示提示。"""
        info = current_task()
        banner = task_banner_md() if info and info.get("running") else ""
        return (_gpu_badge(_gpu_status(refresh=True)), _upd(value=banner, visible=bool(banner))) + self.library()

    # ------------------------------------------------------------------ 停止按钮
    @staticmethod
    def on_stop(armed: Any) -> Tuple[Dict[str, Any], float]:
        """第一次点：按钮变成「再点一次确认停止」；5 秒内再点一次才真的停止。
        超过 5 秒才点第二次：不停止，按钮上明确写「确认超时了」（不能和第一次点完一模一样，否则看不出这次没生效）。"""
        now = time.time()
        armed_at = _float_or_zero(armed)
        _STOP_ARMED.discard(armed_at)
        if armed_at and now - armed_at <= STOP_WINDOW:
            if request_stop():
                return _upd(value=STOP_PENDING, interactive=False), 0.0
            return _btn(STOP_LABEL, visible=False, interactive=True), 0.0
        _STOP_ARMED.add(now)
        return _upd(value=STOP_EXPIRED if armed_at else STOP_CONFIRM), now

    @staticmethod
    def on_stop_expire(armed: Any, wait: bool = True) -> Tuple[Any, Any]:
        """点了第一次、5 秒内没确认：把按钮改回「⏹ 停止」（接在 on_stop 后面运行）。
        已经确认停止、或者又点了一次（重新开始计时）的，不动它。"""
        armed_at = _float_or_zero(armed)
        if not armed_at:
            return _upd(), _upd()
        if wait:
            time.sleep(max(0.0, armed_at + STOP_WINDOW + 0.3 - time.time()))
        if armed_at not in _STOP_ARMED:
            return _upd(), _upd()
        _STOP_ARMED.discard(armed_at)
        return _upd(value=STOP_LABEL), 0.0

    # ------------------------------------------------------------------ ① 准备素材
    def do_prepare(self, voice: Any, files: Any, folder: Any, asr: Any, lang: Any, denoise: Any,
                   separate: Any, only_sus: Any = False, table: Any = None) -> Iterator[Tuple[Any, ...]]:
        """「开始准备素材」。校对表不在这里刷新：做完后由 after_prepare_clips 刷新（那时才能拿到老师在等待期间改过的表格），
        这里只把开始时的表格和还没保存的修改记进 clips_base。"""
        O = self.PREP_OUT
        idle = dict(prep_btn=self._idle_btn(PREP_BTN), prep_stop=self._stop_hidden())
        v = _voice_name(voice)
        if not v:
            yield self._o(O, prep_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task("prepare", v)
        if busy:
            yield self._o(O, prep_bar=self._notice(busy), prep_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None:
            yield self._o(O, prep_bar=self._notice(err), prep_md="", **idle)
            return
        attach = self._attaching("prepare", v)
        uploads = _paths_of(files)
        folder_s = str(folder or "").strip().strip('"').strip("'").strip()
        if not attach and folder_s and not Path(folder_s).expanduser().exists():
            yield self._o(O, prep_bar=self._notice(
                f"找不到这个文件夹：{folder_s}。请检查是否写错（可以在文件夹窗口顶部的地址栏复制路径，再粘贴过来）。"), **idle)
            return
        if folder_s:
            folder_s = str(Path(folder_s).expanduser())
        if not attach and not uploads and not folder_s and not project.exists:
            yield self._o(O, prep_bar=self._notice("请上传文件或填写文件夹路径"), **idle)
            return
        overrides = {"asr": {"engine": asr or "faster-whisper", "language": lang or "auto"},
                     "denoise": denoise or "auto", "separate_vocals": bool(separate)}
        try:
            base = {"voice": v, "table": _table_records(table, CLIP_HEADERS),
                    "pending": sorted(_pending_edits(self.cfg, v, table))}
        except Exception as exc:  # 只是为了不丢表格里的修改，出问题也不影响准备素材
            log.debug(f"记录校对表的修改失败：{exc}")
            base = {"voice": v, "table": [], "pending": []}
        stream = stream_task("prepare", "准备素材", v, _attach_missed if attach else _prepare_job, self.cfg, v, uploads,
                             folder_s, overrides,
                             stages=_stages(self.cfg, "prepare", overrides=overrides), note=NOTE)
        stop_once = _StopOnce()
        for text, st in stream:
            if st.get("busy"):
                yield self._o(O, prep_bar=st.get("bar", ""), prep_log=text, **idle)
                return
            if not st.get("done"):
                yield self._o(O, prep_bar=st.get("bar", ""), prep_log=text, prep_btn=self._busy_btn(PREP_BUSY),
                              prep_stop=stop_once(), prep_next=_btn(PREP_NEXT, visible=False), clips_base=base)
                continue
            ok = "value" in st and not st.get("error")
            if self._missed(attach, st):
                md = ATTACH_MISSED_MD
            else:
                md = _summary_md(st.get("value") or {}) if ok else self._final_md(st, "素材准备", v)
            if ok and not self._missed(attach, st):
                _info("✅ 素材准备完成！可以去「② 训练模型」了")
            yield self._o(O, prep_bar=st.get("bar", ""), prep_log=text, prep_md=md,
                          voice=_upd(choices=_voices(self.cfg), value=v), clips_count=_clips_count_md(self.cfg, v),
                          voice_status=_voice_status_md(self.cfg, v), prep_next=_btn(PREP_NEXT, visible=ok),
                          clips_base=base, **idle)

    def after_prepare_clips(self, voice: Any, only_sus: Any = False, table: Any = None, base: Any = None
                            ) -> Tuple[Any, Any, Any]:
        """素材准备做完后刷新校对表（接在 do_prepare 后面）：按「只看可能有错的」筛选；
        开始前没保存的修改、等待期间在表格里改的内容都留着（准备素材会重新判断「保留」，所以不能直接和硬盘比）。

        返回 (片段总数, 表格, 清空的 clips_base)。这次没真正开始准备（没填声音、别的任务在做……）时 clips_base 是空的，
        什么都不改。"""
        v = _voice_name(voice)
        if not v or not isinstance(base, dict) or base.get("voice") != v:
            return _upd(), _upd(), {}
        b = base
        start = {_clean_cell(r.get(COL_ID)): r for r in _table_records(b.get("table") or [], CLIP_HEADERS)}
        end = {_clean_cell(r.get(COL_ID)): r for r in _table_records(table, CLIP_HEADERS)}
        ids = {str(x) for x in (b.get("pending") or [])}
        for rid, row in end.items():
            s0 = start.get(rid)
            if s0 is not None and any(_clean_cell(row.get(c)) != _clean_cell(s0.get(c)) for c in _EDIT_COLS):
                ids.add(rid)
        try:
            known = {r["id"] for r in wf.Project(self.cfg, v).load_manifest()}
        except ValueError:
            known = set()
        pending = {rid: (end.get(rid) or start[rid]) for rid in ids if rid in known and (rid in end or rid in start)}
        rows = _keep_pending(_clips_table(self.cfg, v, bool(only_sus)), pending)
        count = _clips_count_md(self.cfg, v) + ("\n\n" + _pending_note(len(pending)) if pending else "")
        return count, rows, {}

    # ------------------------------------------------------------------ ① 校对
    def load_clips(self, voice: Any, only_sus: Any = False) -> Tuple[Any, Any]:
        """「🔄 重新载入」：完全按硬盘上的校对表重新显示（没保存的修改不要了）。"""
        return _clips_count_md(self.cfg, voice), _clips_table(self.cfg, voice, bool(only_sus))

    def refresh_clips(self, voice: Any, only_sus: Any = False, table: Any = None) -> Tuple[Any, Any]:
        """切换「只看可能有错的」、查完错字以后刷新表格：按硬盘重新读，但表格里还没保存的修改原样留着。"""
        pending = _pending_edits(self.cfg, voice, table)
        rows = _keep_pending(_clips_table(self.cfg, voice, bool(only_sus)), pending)
        count = _clips_count_md(self.cfg, voice) + ("\n\n" + _pending_note(len(pending)) if pending else "")
        return count, rows

    def on_clip_pick(self, voice: Any, table: Any, row: int, col: int, value: Any = None) -> Tuple[Any, ...]:
        """点校对表的一行：按 id 找片段（排序、筛选后也不会播错），显示两次识别的对比。"""
        v = _voice_name(voice)
        cid = _clean_cell(value) if col == 1 else _clean_cell(_cell(table, CLIP_HEADERS, row, COL_ID))
        if not v or not cid:
            return _upd(), "", _btn(ADOPT_BTN, visible=False), ""
        project = wf.Project(self.cfg, v)
        rec = {r["id"]: r for r in project.load_manifest()}.get(cid)
        if rec is None:
            return (_upd(value=None, label="试听选中的片段"), self._notice("表格里的片段不属于这个声音，请先点「🔄 重新载入」。"),
                    _btn(ADOPT_BTN, visible=False), "")
        no = _clean_cell(_cell(table, CLIP_HEADERS, row, "#")) or "?"
        text = str(rec.get("text", "") or "")
        audio = _upd(value=str(project.abspath(rec["path"])), label=f"试听：第 {no} 条　{text[:24]}", visible=True)
        sus = _suspect(rec)
        if not sus:
            return audio, "", _btn(ADOPT_BTN, visible=False), cid
        reasons = "；".join(str(x) for x in (sus.get("reasons") or []) if x)
        alt = str(sus.get("alt") or "")
        panel = ('<div class="vt-diff">' + (f'<div class="vt-diff-reason">⚠️ 可能有错：{html.escape(reasons)}</div>'
                                             if reasons else "")
                 + _render_diff(text, alt, sus.get("spans")) + "</div>")
        can_adopt = bool(alt) and callable(getattr(wf, "apply_suggestion", None))
        return audio, panel, _btn(ADOPT_BTN, visible=can_adopt), cid

    def do_adopt(self, voice: Any, clip_id: Any, only_sus: Any = False, table: Any = None) -> Tuple[Any, ...]:
        """「✅ 采用建议」：把这条片段的文字改成第二次识别的结果，并刷新表格（别的行里还没保存的修改留着）。"""
        v = _voice_name(voice)
        cid = str(clip_id or "")
        if not v or not cid:
            return "请先点表格里标红的那一行。", _upd(), _upd(), "", _btn(ADOPT_BTN, visible=False)
        guard = self._edit_guard(v, "采用建议")
        if guard:
            return guard, _upd(), _upd(), _upd(), _upd()
        fn = getattr(wf, "apply_suggestion", None)
        if not callable(fn):
            return "这个版本还不能自动采用建议，请直接在表格的「文字」列里修改。", _upd(), _upd(), _upd(), _upd()
        pending = _pending_edits(self.cfg, v, table, skip=[cid])
        rec = fn(self.cfg, v, cid) or {}
        text = rec.get("text") if isinstance(rec, dict) else ""
        msg = f"✅ 已采用建议：{_md_text(text)}" if text else "✅ 已采用建议"
        if isinstance(rec, dict) and rec.get("csv_locked"):
            msg += ("\n\n⚠️ transcripts.csv 正被 Excel/WPS 打开，那个文件这次没能同步（网页里已经改好了）。"
                    "关掉 Excel/WPS 后点一次「保存修改」就会同步。")
        if pending:
            msg += "\n\n" + _pending_note(len(pending))
        rows = _keep_pending(_clips_table(self.cfg, v, bool(only_sus)), pending)
        return (msg, _clips_count_md(self.cfg, v), rows, "", _btn(ADOPT_BTN, visible=False))

    @staticmethod
    def _edit_guard(voice: str, action: str = "保存修改") -> str:
        """素材准备 / 查找错字正在改这个声音的片段时，不让表格的修改把它覆盖掉（反过来也一样）。"""
        info = current_task()
        if info and info.get("running") and info.get("voice") == voice and info.get("kind") in ("prepare", "proofcheck"):
            return (f"「{info.get('label')}」正在进行，请等它完成后再点「{action}」。"
                    "你在表格里改的内容还在，做完刷新表格时也会留着，不会丢。")
        return ""

    def do_save(self, voice: Any, table: Any, only_sus: Any = False) -> Tuple[Any, Any, Any]:
        """「保存修改」：把表格里的修改写回校对表，重新统计。被 Excel 打开时不丢修改。"""
        v = _voice_name(voice)
        if not v:
            return NEED_VOICE, _upd(), _upd()
        guard = self._edit_guard(v)
        if guard:
            return guard, _upd(), _upd()
        project = wf.Project(self.cfg, v)
        records = {r["id"]: r for r in project.load_manifest()}
        rows = _table_records(table, CLIP_HEADERS)
        out_rows: List[Dict[str, Any]] = []
        notes: List[str] = []
        changed_text: Dict[str, str] = {}
        for i, row in enumerate(rows, 1):
            rid = _clean_cell(row.get(COL_ID))
            rec = records.get(rid)
            if rec is None:
                continue
            keep = _parse_keep(row.get(COL_KEEP))
            if keep is None:
                notes.append(f"第 {_clean_cell(row.get('#')) or i} 行「保留」填的是「{_clean_cell(row.get(COL_KEEP))}」，看不懂，已保持原样")
                keep = bool(rec.get("keep", True))
            text = _clean_cell(row.get(COL_TEXT))
            if text and text != str(rec.get("text", "")).strip():
                changed_text[rid] = str(rec.get("text", ""))
            lang = _LANG_CODES.get(_clean_cell(row.get(COL_LANG)), rec.get("lang", ""))
            out_rows.append({"id": rid, "keep": 1 if keep else 0, "split": rec.get("split", "train"), "lang": lang,
                             "duration": rec.get("duration", 0), "text": text or rec.get("text", ""),
                             "drop_reason": _clean_cell(row.get(COL_DROP)), "audio": ""})
        if not out_rows:
            return (f"表格里的片段不属于「{_md_text(v)}」，请先点「🔄 重新载入」。", _upd(), _upd())
        fields = ["id", "keep", "split", "lang", "duration", "text", "drop_reason", "audio"]
        try:
            _write_csv_atomic(project.csv_path, out_rows, fields)
        except PermissionError:
            return ("transcripts.csv 正被 Excel/WPS 打开，请先关掉它，再点一次「保存修改」。"
                    "表格里的修改还在，不会丢。", _upd(), _upd())
        summary = wf.apply_review(self.cfg, v)
        if changed_text:  # 改过文字的片段：旧的「可能有错」标记已经不对了（U3 也会做，这里保险）
            recs = project.load_manifest()
            dirty = False
            for r in recs:
                if r.get("id") in changed_text and "suspect" in r and r.get("text") != changed_text[r["id"]]:
                    r.pop("suspect", None)
                    dirty = True
            if dirty:
                project.save_manifest(recs)
        ch = summary.get("changed") or {}
        md = f"✅ 已保存：改了 {ch.get('text', 0)} 处文字、{ch.get('keep', 0)} 处「保留」、{ch.get('lang', 0)} 处语言"
        if notes:
            md += "\n\n" + "\n".join(f"> ⚠️ {_md_text(n)}" for n in notes)
        md += "\n\n" + _summary_md(summary)
        return md, _clips_count_md(self.cfg, v), _clips_table(self.cfg, v, bool(only_sus))

    def do_proofcheck(self, voice: Any, only_sus: Any = False) -> Iterator[Tuple[Any, ...]]:
        O = self.PROOF_OUT
        idle = dict(proof_btn=self._idle_btn(PROOF_BTN), proof_stop=self._stop_hidden())
        v = _voice_name(voice)
        if not v:
            yield self._o(O, proof_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task("proofcheck", v)
        if busy:
            yield self._o(O, proof_bar=self._notice(busy), prep_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None or not project.exists:
            yield self._o(O, proof_bar=self._notice(err or NEED_PREPARE), **idle)
            return
        attach = self._attaching("proofcheck", v)
        fn = getattr(wf, "run_proofcheck", None)
        if not attach and not callable(fn):
            yield self._o(O, proof_bar=self._notice("这个版本还没有「自动查找错字」功能。"), **idle)
            return
        stream = stream_task("proofcheck", "查找可能的错字", v, _attach_missed if attach else fn, self.cfg, v,
                             stages=_stages(self.cfg, "proofcheck"), note=NOTE)
        stop_once = _StopOnce()
        for text, st in stream:
            if st.get("busy"):
                yield self._o(O, proof_bar=st.get("bar", ""), prep_log=text, **idle)
                return
            if not st.get("done"):
                yield self._o(O, proof_bar=st.get("bar", ""), prep_log=text, proof_btn=self._busy_btn(PROOF_BUSY),
                              proof_stop=stop_once())
                continue
            ok = "value" in st and not st.get("error")
            if self._missed(attach, st):
                md = ATTACH_MISSED_MD
            elif ok:
                r = st.get("value") or {}
                flagged = _int(r.get("flagged"))
                if flagged:
                    md = (f"### ✅ 检查完了：一共查了 {r.get('checked', 0)} 条，其中 **{flagged}** 条可能有错"
                          "（已在表格里标红）")
                else:
                    md = f"### ✅ 检查完了：一共查了 {r.get('checked', 0)} 条，没有发现可能有错的字"
                if r.get("note"):
                    md += f"\n\n{_md_text(r['note'])}"
                if flagged:
                    md += ("\n\n勾上「只看可能有错的」，可以只看标红的片段；点某一行能看到两次识别的对比，"
                           "有建议时可以点「✅ 采用建议」。")
                _info("✅ 检查完了，可能有错的字已经标红")
            else:
                md = self._final_md(st, "查找错字", v)
            # 表格不在这里刷新：这里拿到的是点按钮那一刻的表格，查错字期间老师改的内容会被冲掉。
            # 接在后面的 refresh_clips 读的是那时的表格，没保存的修改会留着。
            yield self._o(O, proof_bar=st.get("bar", ""), proof_md=md, prep_log=text,
                          clips_count=_clips_count_md(self.cfg, v), **idle)

    # ------------------------------------------------------------------ ② 训练
    def train_plan_preview(self, voice: Any, backend: Any = None, s_ep: Any = 0, g_ep: Any = 0, bs: Any = 0,
                           dpo: Any = "auto") -> str:
        """训练前就显示电脑会怎么自动选参数（wf.training_plan：看显卡和素材，只读文件和 nvidia-smi，很快）。"""
        v = _voice_name(voice)
        if v:
            try:
                text = wf.training_plan(self.cfg, v, str(backend or self.default_train),
                                        **self._train_opts(s_ep, g_ep, 0, bs, dpo))
                if text:
                    return ("🧠 **电脑会自动这样训练**：" + _md_text(_strip_plan(text))
                            + "（想自己改，可以打开下面的「高级设置」）")
            except Exception as exc:
                log.debug(f"training_plan 出错：{exc}")
        return PLAN_DEFAULT

    def _train_common(self, kind: str, voice: Any, backend: Any, opts: Dict[str, Any]) -> Iterator[Tuple[Any, ...]]:
        O = self.TRAIN_OUT
        idle = dict(train_btn=self._idle_btn(TRAIN_BTN), select_btn=self._idle_btn(SELECT_BTN),
                    train_stop=self._stop_hidden())
        v = _voice_name(voice)
        if not v:
            yield self._o(O, train_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task(kind, v)
        if busy:
            yield self._o(O, train_bar=self._notice(busy), train_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None or not project.exists:
            yield self._o(O, train_bar=self._notice(err or NEED_PREPARE), **idle)
            return
        backend = str(backend or self.default_train)
        attach = self._attaching(kind, v)
        if kind == "train":
            stream = stream_task("train", "训练模型", v, _attach_missed if attach else wf.run_train, self.cfg, v, backend,
                                 stages=_stages(self.cfg, "train", backend),
                                 hint="训练通常要 30~90 分钟（素材越多越久），可以先去做别的事", note=NOTE, **opts)
            what, busy = "训练", TRAIN_BUSY
        else:
            stream = stream_task("select", "重新挑选最佳模型", v, _attach_missed if attach else wf.run_select, self.cfg, v,
                                 backend,
                                 stages=_stages(self.cfg, "select"), note=NOTE)
            what, busy = "挑选模型", SELECT_BUSY
        plan = ""
        stop_once = _StopOnce()
        for text, st in stream:
            if st.get("busy"):
                yield self._o(O, train_bar=st.get("bar", ""), train_log=text, **idle)
                return
            plan = _plan_line(text) or plan
            if not st.get("done"):
                running = dict(train_btn=self._busy_btn(busy if kind == "train" else TRAIN_BTN),
                               select_btn=self._busy_btn(busy if kind == "select" else SELECT_BTN),
                               train_stop=stop_once(), train_next=_btn(TRAIN_NEXT, visible=False))
                yield self._o(O, train_bar=st.get("bar", ""), train_log=text,
                              train_plan=_plan_md(plan) if plan else _upd(), **running)
                continue
            ok = "value" in st and not st.get("error")
            info = st.get("value") or {}
            if self._missed(attach, st):
                md = ATTACH_MISSED_MD
            elif ok and kind == "train":
                md = _train_done_md(info, plan, show_plan=False)
                _info("✅ 训练完成！可以去「③ 生成讲课音频」了")
            elif ok:
                md = _select_done_md(info)
                _info("✅ 已重新挑好最像你的模型")
            else:
                md = self._final_md(st, what, v)
            final_plan = _plan_md(plan or (_plan_text(info) if ok else ""))
            yield self._o(O, train_bar=st.get("bar", ""), train_log=text, train_md=md,
                          voice_status=_voice_status_md(self.cfg, v), train_next=_btn(TRAIN_NEXT, visible=ok),
                          train_plan=final_plan or _upd(), **idle)

    @staticmethod
    def _train_opts(s_ep: Any, g_ep: Any, q_ep: Any, bs: Any, dpo: Any = "auto") -> Dict[str, Any]:
        """高级设置 → 训练选项（0 / 空 = 自动，交给引擎按显卡和素材决定）。"""
        opts: Dict[str, Any] = {"sovits_epochs": _int(s_ep) or None, "gpt_epochs": _int(g_ep) or None,
                                "epochs": _int(q_ep) or None, "batch_size": _int(bs) or None}
        d = str(dpo or "auto").strip().lower()
        opts["if_dpo"] = True if d == "on" else (False if d == "off" else None)
        return opts

    def do_train(self, voice: Any, backend: Any, s_ep: Any, g_ep: Any, q_ep: Any, bs: Any,
                 dpo: Any = "auto") -> Iterator[Tuple[Any, ...]]:
        yield from self._train_common("train", voice, backend, self._train_opts(s_ep, g_ep, q_ep, bs, dpo))

    def do_select(self, voice: Any, backend: Any) -> Iterator[Tuple[Any, ...]]:
        yield from self._train_common("select", voice, backend, {})

    # ------------------------------------------------------------------ ③ 生成
    def on_script_upload(self, f: Any, current_name: Any = "") -> Tuple[Any, Any, Any, Any]:
        """上传讲稿：txt / md / docx 的内容直接放进讲稿框；srt / vtt 保留文件（按字幕时间轴生成）。"""
        path = _path_of(f)
        if not path:
            return _upd(), _upd(), "", _upd()
        p = Path(path)
        ext = p.suffix.lower()
        name_upd = _upd(value=p.stem) if not str(current_name or "").strip() else _upd()
        if ext in SCRIPT_TEXT_EXTS:
            try:
                from voicetwin.synth.script import read_script_file

                text, _cues = read_script_file(p)
            except Exception as exc:
                title = str(exc)
                try:
                    from voicetwin.errors import explain

                    title = explain(exc).title
                except Exception:
                    pass
                return (_upd(), _upd(), f"❌ 读不了这个文件：{_md_text(title)}。Word 文件请另存为 .docx 或 .txt 再上传。",
                        _upd())
            return (text, None, f"已把「{_md_text(p.name)}」的内容放进上面的讲稿框，可以直接修改。", name_upd)
        if ext in SCRIPT_SUB_EXTS:
            return (_upd(), _upd(), f"已载入字幕文件「{_md_text(p.name)}」：会按字幕的时间轴生成（适合给视频配音）。"
                    "要改用上面的文字，请点文件右上角的 × 删除它。", name_upd)
        return (_upd(), None, "不支持这种文件（.doc / .wps / .pdf）。请在 Word 或 WPS 里点「文件 → 另存为」，"
                "类型选 .docx 或 .txt，再上传。", _upd())

    def _source(self, text: Any, sfile: Any) -> Tuple[str, str]:
        """(讲稿来源, 文件名用的名字)。字幕文件优先；否则用讲稿框里的文字。"""
        path = _path_of(sfile)
        if path and Path(path).suffix.lower() in SCRIPT_SUB_EXTS:
            return path, Path(path).stem
        if text and str(text).strip():
            return str(text), (_first_sentence(str(text), 20) or "讲课音频")
        if path and Path(path).exists():
            return path, Path(path).stem
        return "", ""

    def do_generate(self, voice: Any, text: Any, sfile: Any, backend: Any, quality: Any, speed: Any, ref: Any,
                    redo: Any, out_name: Any = "", out_fmt: Any = "") -> Iterator[Tuple[Any, ...]]:
        O = self.GEN_OUT
        idle = dict(gen_btn=self._idle_btn(GEN_BTN), gen_stop=self._stop_hidden(), speed_try=self._idle_btn(SPEED_BTN))
        v = _voice_name(voice)
        if not v:
            yield self._o(O, gen_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task("generate", v)
        if busy:
            yield self._o(O, gen_bar=self._notice(busy), gen_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None or not project.exists:
            yield self._o(O, gen_bar=self._notice(err or NEED_PREPARE), **idle)
            return
        attach = self._attaching("generate", v)
        try:
            from voicetwin.cli import _parse_redo

            redo_list = [] if attach else _parse_redo(_text_in(redo))
        except ValueError as exc:
            yield self._o(O, gen_bar=self._notice(str(exc)), **idle)
            return
        source, stem = self._source(text, sfile)
        if not source and not attach:
            yield self._o(O, gen_bar=self._notice("请先在「讲稿」框里粘贴讲稿，或上传讲稿文件。"), **idle)
            return
        fmt = str(out_fmt or self.cfg.get_path("synth.output_format", "wav") or "wav")
        out = _output_path(project, str(out_name or ""), fmt, stem)
        q = str(quality or "balanced")
        factor = _speed_factor(speed)
        log.info(f"质量 {q}（{QUALITY_SHORT.get(q, q)}），语速系数 {factor}")
        stream = stream_task("generate", "生成讲课音频", v, _attach_missed if attach else wf.run_narrate, self.cfg, v, source,
                             out=str(out),
                             backend_name=str(backend or self.default_synth), quality=q, speed=factor,
                             reference=str(ref or "").strip(), redo=redo_list,
                             stages=_stages(self.cfg, "narrate", quality=q), note=NOTE)
        stop_once = _StopOnce()
        for logs, st in stream:
            if st.get("busy"):
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, **idle)
                return
            if not st.get("done"):
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, gen_btn=self._busy_btn(GEN_BUSY),
                              gen_stop=stop_once(), speed_try=_upd(interactive=False))
                continue
            if self._missed(attach, st):
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, gen_md=ATTACH_MISSED_MD, **idle)
                continue
            if "value" not in st or st.get("error"):
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, gen_md=self._final_md(st, "生成", v), **idle)
                continue
            res = st["value"]
            vs = _variants(res)
            audio = str(getattr(res, "audio_path", "") or "")
            srt = getattr(res, "srt_path", None)
            files_out = _gen_files(audio, srt, vs)
            state = {"voice": v, "audio": audio, "report": str(getattr(res, "report_path", "") or ""),
                     "srt": str(srt or ""), "variants": [dict(x) for x in vs]}
            var: Dict[str, Any] = dict(var_box=_upd(visible=False), var_md="", var_note="")
            if len(vs) >= 2:
                choices = [(_variant_title(x, i).split("（")[0], str(x.get("name") or i)) for i, x in enumerate(vs)]
                var = dict(var_box=_upd(visible=True), var_md=_variants_md(vs),
                           var_a=_upd(value=str(vs[0]["path"]), label=_variant_title(vs[0], 0)),
                           var_b=_upd(value=str(vs[1]["path"]), label=_variant_title(vs[1], 1)),
                           var_choice=_upd(choices=choices, value=_recommended_variant(vs)), var_note="")
            _info("✅ 音频生成好了，点 ▶ 试听")
            yield self._o(O, gen_bar=st.get("bar", ""), out_audio=_upd(value=audio or None, label="结果"),
                          out_files=files_out, gen_log=logs, gen_md=_gen_summary_md(res, redo_list), redo="",
                          gen_table=_gen_rows(res), gen_state=state, gen_after=_upd(visible=True), **var, **idle)

    def on_choose_variant(self, voice: Any, state: Any, name: Any) -> Tuple[Any, Any, Any]:
        """「最终使用哪个版本」：把选中的版本复制成最终的 <名字>.wav，并更新上面的播放器和下载列表。

        返回 (结果播放器, 下载列表, 说明)。下载列表必须重新发一次：gradio 4.24 发文件时会按内容复制一份到它的缓存里，
        不重新发的话，列表里的 <名字>.wav 下载到的还是换版本之前的内容。"""
        v = _voice_name(voice) or (state or {}).get("voice", "")
        st = state if isinstance(state, dict) else {}
        vs = st.get("variants") or []
        chosen = next((x for x in vs if str(x.get("name")) == str(name)), None)
        if not v or chosen is None:
            return _upd(), _upd(), "请先生成一次（「完美」质量会做两个版本）。"
        try:  # 已经是最终版本就什么都不做（gradio 4.24：这组控件刚显示出来时也会触发一次 input，实测）
            current = json.loads(Path(str(st.get("report", ""))).read_text(encoding="utf-8")).get("final")
        except Exception:
            current = None
        if current is not None and str(current) == str(name):
            return _upd(), _upd(), _upd()
        res = wf.choose_variant(self.cfg, v, st.get("report", ""), str(name)) or {}
        final = str(res.get("audio") or st.get("audio") or "")
        i = vs.index(chosen)
        title = _variant_title(chosen, i)
        files = _gen_files(final, st.get("srt") or None, vs)
        # 播放器放版本自己的文件：最终文件名没变，浏览器可能还在用旧的缓存
        return (_upd(value=str(chosen["path"]), label=f"结果（{title}）"), files,
                f"✅ 已改用{_md_text(title.split('（')[0])}：`{final.replace('`', '')}` 现在就是这个版本"
                "（下面的下载列表也已经换好了）。")

    def on_gen_pick(self, state: Any, table: Any, row: int) -> Dict[str, Any]:
        """点逐句结果表的一行：单独播放这一句（按 # 列找，排序后也不会播错）。"""
        st = state if isinstance(state, dict) else {}
        no = _int(_cell(table, GEN_HEADERS, row, "#"), -1)
        report = st.get("report") or ""
        if no < 1 or not report or not Path(report).exists():
            return _upd()
        data = json.loads(Path(report).read_text(encoding="utf-8"))
        seg = next((s for i, s in enumerate(data.get("segments") or [], 1) if _seg_no(s, i) == no), None)
        if seg is None:
            return _upd()
        label = f"第 {no} 句：{str(seg.get('text', ''))[:30]}"
        project = wf.Project(self.cfg, st.get("voice") or "")
        clip = seg.get("clip")
        if clip and project.abspath(str(clip)).exists():
            return _upd(value=str(project.abspath(str(clip))), label=label, visible=True)
        audio = Path(st.get("audio") or data.get("audio") or "")
        start, end = _num(seg.get("start")), _num(seg.get("end"))
        if not audio.exists() or start is None or end is None or end <= start:
            return _upd()
        from voicetwin.utils.audio import load_audio, save_audio

        wav, sr = load_audio(audio)
        piece = wav[int(start * sr): int(end * sr)]
        out = project.cache_dir / "sentences" / f"{audio.stem}_第{no}句.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        save_audio(out, piece, sr)
        return _upd(value=str(out), label=label, visible=True)

    def do_speed_preview(self, voice: Any, text: Any, speed: Any, backend: Any) -> Iterator[Tuple[Any, ...]]:
        """「▶ 试听语速」：用最快的质量读一句话，先听听语速合不合适。"""
        O = self.SPEED_OUT
        idle = dict(speed_try=self._idle_btn(SPEED_BTN), gen_btn=self._idle_btn(GEN_BTN), gen_stop=self._stop_hidden())
        v = _voice_name(voice)
        if not v:
            yield self._o(O, gen_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task("speed", v)
        if busy:
            yield self._o(O, gen_bar=self._notice(busy), gen_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None or not project.exists:
            yield self._o(O, gen_bar=self._notice(err or NEED_PREPARE), **idle)
            return
        sentence = _first_sentence(str(text or "")) or SPEED_SAMPLE
        factor = _speed_factor(speed)
        out = project.cache_dir / "speed_preview" / f"语速_{int(round(_num(speed) or 0)):+d}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        attach = self._attaching("speed", v)
        stream = stream_task("speed", "试听语速", v, _attach_missed if attach else wf.run_narrate, self.cfg, v, sentence,
                             out=str(out),
                             backend_name=str(backend or self.default_synth), quality="fast", speed=factor,
                             subtitles=False, variants=False, stages=_stages(self.cfg, "narrate", quality="fast"))
        stop_once = _StopOnce()
        for logs, st in stream:
            if st.get("busy"):
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, **idle)
                return
            if not st.get("done"):
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, speed_try=self._busy_btn(SPEED_BUSY),
                              gen_btn=_upd(interactive=False), gen_stop=stop_once())
                continue
            if "value" in st and not st.get("error") and st.get("value") is not None:
                res = st["value"]
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs,
                              speed_audio=_upd(value=str(getattr(res, "audio_path", out)), visible=True,
                                               label=f"语速试听（{_speed_text(speed)[3:]}）：{sentence[:20]}"), **idle)
            else:
                yield self._o(O, gen_bar=st.get("bar", ""), gen_log=logs, **idle)

    def open_outputs(self, voice: Any, state: Any, select: bool = False) -> str:
        """「📂 打开保存文件夹」/「📍 在文件夹里找到这个文件」（只在本机使用时显示）。"""
        st = state if isinstance(state, dict) else {}
        v = _voice_name(voice) or st.get("voice", "")
        if not v:
            return NEED_VOICE
        try:
            from voicetwin.utils.winsys import open_path
        except ImportError:
            return "这个版本还不能直接打开文件夹。"
        project = wf.Project(self.cfg, v)
        target = Path(st.get("audio") or "") if select and st.get("audio") else project.outputs_dir
        if not target.exists():
            target = project.outputs_dir
            target.mkdir(parents=True, exist_ok=True)
        if open_path(target, select=select and target.is_file()):
            return ""
        return f"没能自动打开，请手动打开这个文件夹：`{str(target).replace('`', '')}`"

    # ------------------------------------------------------------------ ④ 评估
    def eval_impl(self, voice: Any, audio: Any, text: Any, progress: Any = None) -> str:
        from voicetwin.synth.select import evaluate_file

        v = _voice_name(voice)
        if not v:
            return NEED_VOICE
        info = current_task()
        if info and info.get("running"):
            return f"现在正在「{_md_text(info.get('label'))}」，评估也要用显卡，请等它完成后再试。"
        path = _path_of(audio)
        if not path:
            return "请先上传一段音频（或点「📥 评估刚才生成的音频」）。"
        project, err = self._project(v)
        if project is None or not project.exists:
            return err or NEED_PREPARE
        if progress is not None:
            try:
                progress(0.1, desc="正在加载声纹模型……")
            except Exception:
                pass
        project = wf.open_project(self.cfg, v, must_exist=True)
        if progress is not None and text:
            try:
                progress(0.5, desc="正在识别文字……")
            except Exception:
                pass
        return _eval_md(evaluate_file(self.cfg, project, Path(path), str(text or "")))

    # ------------------------------------------------------------------ ⑤ 鉴别
    def do_verify(self, voice: Any, originals: Any, generated: Any, state: Any) -> Iterator[Tuple[Any, ...]]:
        O = self.VERIFY_OUT
        idle = dict(vf_btn=self._idle_btn(VERIFY_BTN))
        v = _voice_name(voice)
        if not v:
            yield self._o(O, vf_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task("verify", v)
        if busy:
            yield self._o(O, vf_bar=self._notice(busy), vf_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None or not project.exists:
            yield self._o(O, vf_bar=self._notice(err or NEED_PREPARE), **idle)
            return
        attach = self._attaching("verify", v)
        gen = _paths_of(generated)
        labels: Dict[str, str] = {}
        if not gen and not attach:
            st = state if isinstance(state, dict) else {}
            report: Dict[str, Any] = {}
            if st.get("voice") == v and st.get("report") and Path(st["report"]).exists():
                try:
                    report = json.loads(Path(st["report"]).read_text(encoding="utf-8"))
                except Exception:
                    report = {}
            gen = _report_audio_files(report, project) if report else []
            if not gen:
                report = _latest_report(project)
                gen = _report_audio_files(report, project)
            labels = _report_labels(report, project)
        if not gen and not attach:
            yield self._o(O, vf_bar=self._notice("还没有生成过音频。请先在「③ 生成讲课音频」里生成一次，或在上面上传要鉴别的音频。"),
                          **idle)
            return
        stream = stream_task("verify", "机器鉴别", v, _attach_missed if attach else _verify_job, self.cfg, v,
                             _paths_of(originals), gen, stages=_stages(self.cfg, "verify"), note=NOTE)
        for text, st in stream:
            if st.get("busy"):
                yield self._o(O, vf_bar=st.get("bar", ""), vf_log=text, **idle)
                return
            if not st.get("done"):
                yield self._o(O, vf_bar=st.get("bar", ""), vf_log=text, vf_btn=self._busy_btn(VERIFY_BUSY))
                continue
            if self._missed(attach, st):
                yield self._o(O, vf_bar=st.get("bar", ""), vf_log=text, vf_md=ATTACH_MISSED_MD, **idle)
            elif "value" in st and not st.get("error"):
                table, md = _verify_rows(st.get("value") or {}, labels)
                yield self._o(O, vf_bar=st.get("bar", ""), vf_log=text, vf_md=md, vf_table=table, **idle)
            else:
                yield self._o(O, vf_bar=st.get("bar", ""), vf_log=text, vf_md=self._final_md(st, "鉴别", v), **idle)

    def _blind_slots(self, items: Sequence[str]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for i in range(MAX_BLIND):
            if i < len(items):
                out[f"bt_audio_{i}"] = _upd(value=items[i], visible=True, label=f"第 {i + 1} 段")
                out[f"bt_pick_{i}"] = _upd(value=None, visible=True, label=f"第 {i + 1} 段是：", interactive=True)
            else:
                out[f"bt_audio_{i}"] = _upd(value=None, visible=False)
                out[f"bt_pick_{i}"] = _upd(value=None, visible=False)
        return out

    def do_blind(self, voice: Any, n: Any, quality: Any) -> Iterator[Tuple[Any, ...]]:
        O = self.BLIND_OUT
        idle = dict(bt_btn=self._idle_btn(BLIND_BTN))
        v = _voice_name(voice)
        if not v:
            yield self._o(O, bt_bar=self._notice(NEED_VOICE), **idle)
            return
        busy = self._other_task("blind", v)
        if busy:
            yield self._o(O, bt_bar=self._notice(busy), vf_log=busy, **idle)
            return
        project, err = self._project(v)
        if project is None or not project.exists:
            yield self._o(O, bt_bar=self._notice(err or NEED_PREPARE), **idle)
            return
        attach = self._attaching("blind", v)
        fn = getattr(wf, "build_blind_test", None)
        if not attach and not callable(fn):
            yield self._o(O, bt_bar=self._notice("这个版本还没有「盲听测试」功能。"), **idle)
            return
        count = max(2, min(MAX_BLIND // 2, _int(n, 10) or 10))
        stream = stream_task("blind", "生成盲听测试", v, _attach_missed if attach else _blind_job, self.cfg, v, count,
                             str(quality or "balanced"),
                             stages=_stages(self.cfg, "blind"), note=NOTE)
        for text, st in stream:
            if st.get("busy"):
                yield self._o(O, bt_bar=st.get("bar", ""), vf_log=text, **idle)
                return
            if not st.get("done"):
                yield self._o(O, bt_bar=st.get("bar", ""), vf_log=text, bt_btn=self._busy_btn(BLIND_BUSY),
                              bt_submit=_btn(SUBMIT_BTN, visible=False))
                continue
            if self._missed(attach, st):
                yield self._o(O, bt_bar=st.get("bar", ""), vf_log=text, bt_md=ATTACH_MISSED_MD, **idle)
                continue
            if "value" not in st or st.get("error"):
                yield self._o(O, bt_bar=st.get("bar", ""), vf_log=text, bt_md=self._final_md(st, "盲听测试", v), **idle)
                continue
            result = st.get("value") or {}
            items = _blind_items(result)
            d = _blind_dir(result)
            card = Path(d) / "听众答题卡.txt" if d else None
            md = (f"### 👂 盲听测试做好了：一共 {len(items)} 段，真人和生成的顺序已经打乱\n\n"
                  "请让听众（或你自己）逐段听，选「真人」还是「生成」，全部选完后点「提交答案」。答案提交之前不会显示。"
                  + (f"\n\n想给别人离线测试：把这个文件夹发给他们（里面是编好号的录音和听众答题卡）："
                     f"`{str(card.parent).replace('`', '')}`。答案没有放在文件夹里，在它旁边的"
                     f"「…{getattr(wf, 'BLIND_ANSWER_SUFFIX', '_答案.json')}」，不要一起发。"
                     "收回答题卡后，在下面「批改收上来的答题卡」里填进去就能看到正确率。"
                     if card is not None and card.exists() else ""))
            state = {"voice": v, "dir": d, "answers": _blind_answer_file(result), "n": len(items)}
            yield self._o(O, bt_bar=st.get("bar", ""), vf_log=text, bt_md=md, bt_state=state, bt_result="",
                          bt_submit=_btn(SUBMIT_BTN, visible=bool(items)), **self._blind_slots(items), **idle)

    BLIND_SUBMIT_OUT = ("bt_result", "bt_submit") + tuple(f"bt_pick_{i}" for i in range(MAX_BLIND))
    BLIND_OPEN_OUT = (("bt_md", "bt_state", "bt_submit", "bt_result")
                      + tuple(f"bt_audio_{i}" for i in range(MAX_BLIND)) + tuple(f"bt_pick_{i}" for i in range(MAX_BLIND)))

    @classmethod
    def on_blind_submit(cls, state: Any, *choices: Any) -> Tuple[Any, ...]:
        """「提交答案」：每段都选了才显示答案；显示以后锁住选项（不能看了答案再改）。"""
        O = cls.BLIND_SUBMIT_OUT
        st = state if isinstance(state, dict) else {}
        path = st.get("answers") or ""
        if not path or not Path(path).exists():
            return cls._o(O, bt_result="⚠️ 找不到答案文件，请重新生成一次盲听测试，或在下面选一次以前做的测试。")
        try:
            answers = _blind_answers(json.loads(Path(path).read_text(encoding="utf-8")))
        except Exception as exc:
            return cls._o(O, bt_result=f"⚠️ 读不了答案文件：{_md_text(exc)}")
        n = int(st.get("n") or len(choices))
        picks = list(choices)[:n]
        missing = _blind_missing(picks, answers)
        if missing:
            nums = "、".join(str(i) for i in missing[:12]) + ("……" if len(missing) > 12 else "")
            return cls._o(O, bt_result=f"⚠️ 还有第 {nums} 段没选。每一段都选好「真人」或「生成」再点「提交答案」"
                                       "（提交以后才显示答案）。")
        locked = {f"bt_pick_{i}": _upd(interactive=False) for i in range(n)}
        md = (_blind_result_md(picks, answers) + "\n\n<small>答案已经显示，选项已锁住。想让别人再测：点「生成盲听测试」"
              "重新做一份，或者在下面「批改收上来的答题卡」里填他们的答案。</small>")
        return cls._o(O, bt_result=md, bt_submit=_btn(SUBMIT_BTN, visible=False), **locked)

    def blind_tests(self, voice: Any) -> Dict[str, Any]:
        """「批改收上来的答题卡」的下拉框：这个声音做过的盲听测试，新的在前。"""
        choices = _blind_test_choices(self.cfg, voice)
        return _upd(choices=choices, value=choices[0][1] if choices else None)

    def on_blind_open(self, voice: Any, test_dir: Any) -> Tuple[Any, ...]:
        """选一次以前做的盲听测试：把编好号的录音重新放到上面，可以在网页上再答一遍（网页刷新过也不怕）。"""
        O = self.BLIND_OPEN_OUT
        v = _voice_name(voice)
        d = str(test_dir or "")
        if not v or not d or not Path(d).is_dir():
            return self._o(O)
        items = _blind_items({"dir": d})
        state = {"voice": v, "dir": d, "answers": _blind_answer_file({"dir": d}), "n": len(items)}
        md = (f"### 👂 已打开以前的盲听测试：{_md_text(Path(d).name)}，一共 {len(items)} 段\n\n"
              "可以在上面逐段听、选「真人」还是「生成」，全部选完后点「提交答案」；收上来的纸质答题卡填在下面。")
        return self._o(O, bt_md=md, bt_state=state, bt_result="", bt_submit=_btn(SUBMIT_BTN, visible=bool(items)),
                       **self._blind_slots(items))

    def on_blind_grade(self, voice: Any, test_dir: Any, text: Any) -> str:
        """「📝 批改」：把收上来的答题卡（贴进来的文字）和这次测试的答案对一下。"""
        v = _voice_name(voice)
        if not v:
            return NEED_VOICE
        d = str(test_dir or "")
        if not d or not Path(d).is_dir():
            return "请先在「选一次盲听测试」里选要批改的那一次（没有的话先点上面的「生成盲听测试」）。"
        if not str(text or "").strip():
            return "请把听众的答案填在框里，例如：`1 真人 2 生成 3 真人 ……`"
        g = wf.grade_blind_test(d, str(text))
        return _blind_grade_md(g, Path(d).name)

    # ------------------------------------------------------------------ 环境检查
    def run_doctor(self, force: bool = False) -> Tuple[Any, ...]:
        """环境检查（结果缓存 60 秒；打开这一页会自动检查一次）。"""
        now = time.time()
        if force or self._doc_cache is None or now - self._doc_cache[0] > 60:
            self._doc_cache = (now, list(wf.doctor(self.cfg)))
        summary, main, main_total, opt, opt_total = _doctor_view(self._doc_cache[1])
        return summary, main, main_total, opt, _upd(label=f"可选组件（没装也不影响使用，{opt_total}）", visible=bool(opt))

    def do_download(self) -> Iterator[Tuple[Any, ...]]:
        O = self.DL_OUT
        idle = dict(dl_btn=self._idle_btn(DL_BTN), dl_stop=self._stop_hidden())
        busy = self._other_task("download", "")
        if busy:
            yield self._o(O, doc_bar=self._notice(busy), doc_log=busy, **idle)
            return
        attach = self._attaching("download", "")
        stream = stream_task("download", "下载模型", "", _attach_missed if attach else _download_job, self.cfg,
                             stages=_stages(self.cfg, "download"), note=NOTE)
        stop_once = _StopOnce()
        for text, st in stream:
            if st.get("busy"):
                yield self._o(O, doc_bar=st.get("bar", ""), doc_log=text, **idle)
                return
            if not st.get("done"):
                yield self._o(O, doc_bar=st.get("bar", ""), doc_log=text, dl_btn=self._busy_btn(DL_BUSY),
                              dl_stop=stop_once())
                continue
            if self._missed(attach, st):
                md = ATTACH_MISSED_MD
            elif "value" in st and not st.get("error"):
                files = st.get("value") or []
                md = (f"### ✅ 已下载 {len(files)} 个文件，可以开始训练了" if files else "### ✅ 模型文件都齐全，不用下载")
                self._doc_cache = None
                _info("✅ 模型准备好了")
            else:
                md = self._final_md(st, "下载", "")
            yield self._o(O, doc_bar=st.get("bar", ""), doc_log=text, doc_md=md, **idle)

    # ================================================================== 画页面
    def build(self) -> Any:
        import gradio as gr

        cfg = self.cfg
        c = self.c
        css = PROGRESS_CSS + (getattr(_gpu, "GPU_CSS", "") if _gpu is not None else "") + APP_CSS
        blocks_kw: Dict[str, Any] = dict(title=APP_TITLE, analytics_enabled=False, css=css, delete_cache=(86400, 86400))
        blocks_kw["js"] = page_js()
        heavy = dict(show_progress="hidden", concurrency_limit=None)
        quick = dict(show_progress="hidden")

        def log_box(name: str, lines: int = 12) -> None:
            with gr.Accordion(LOG_ACCORDION, open=False):
                c[name] = gr.Textbox(label="运行记录", lines=lines, max_lines=24, autoscroll=True, show_copy_button=True,
                                     interactive=False)

        def stop_button(name: str) -> Any:
            c[name] = gr.Button(STOP_LABEL, variant="stop", visible=False, scale=1)
            armed = gr.State(0.0)
            c[name].click(self.on_stop, armed, [c[name], armed], **quick).then(
                self.on_stop_expire, armed, [c[name], armed], **quick)
            return c[name]

        def outs(names: Sequence[str]) -> List[Any]:
            return [c[n] for n in names]

        with gr.Blocks(**blocks_kw) as app:
            # -------------------------------------------------------- 顶部
            gr.Markdown(INTRO, elem_classes="vt-header")
            with gr.Row(equal_height=True):
                with gr.Column(scale=8, min_width=240):
                    c["gpu_badge"] = gr.HTML(_gpu_pending())
                with gr.Column(scale=1, min_width=150):
                    gpu_btn = gr.Button("🔄 重新检查显卡", size="sm")
            c["quick_banner"] = gr.HTML(visible=False)
            c["task_banner"] = gr.Markdown(visible=False)
            with gr.Row():
                names = _voices(cfg)
                c["voice"] = gr.Dropdown(choices=names, value=(names or [DEFAULT_VOICE])[0], allow_custom_value=True,
                                         label="声音名称（新建请直接输入名字）", scale=5)
                with gr.Column(scale=1, min_width=150):
                    refresh = gr.Button("🔄 刷新声音列表", size="sm")
            c["voice_status"] = gr.Markdown(elem_classes="vt-md")
            with gr.Accordion(_library_label(len(names)), open=bool(names)) as lib_acc:
                c["lib_acc"] = lib_acc
                c["lib_total"] = gr.Markdown()
                c["lib_table"] = gr.Dataframe(headers=LIB_HEADERS, datatype=["number"] + ["str"] * 5, interactive=False,
                                              wrap=True, column_widths=["6%", "18%", "18%", "24%", "14%", "20%"])
                c["lib_audio"] = gr.Audio(label="▶ 试听这个声音", type="filepath", interactive=False, visible=False)

            with gr.Tabs() as tabs:
                # ---------------------------------------------------- ① 准备素材
                with gr.Tab("① 准备素材", id="prep"):
                    gr.Markdown("上传你的**讲课视频或录音**（越多越好，建议总时长 ≥30 分钟，1~3 小时最佳；"
                                "只要你本人说话的部分）。如果视频有同名 `.srt` 字幕，也一起放进去，会直接用字幕的文字，更准确。")
                    try:
                        from voicetwin.data.prepare import MEDIA_EXTS

                        file_types = sorted(MEDIA_EXTS) + [".srt", ".vtt"]
                    except Exception:
                        file_types = None
                    with gr.Row():
                        c["files"] = gr.File(label="上传视频/音频/字幕（可多选）", file_count="multiple", file_types=file_types)
                        c["folder"] = gr.Textbox(label="或者填写电脑上的文件夹路径（推荐）", placeholder=r"例如 D:\讲课视频",
                                                 info="视频很大（几个 GB）时，建议直接填文件夹路径，不用上传，更快，也不占 C 盘。")
                    c["separate"] = gr.Checkbox(label="视频有背景音乐（去除背景音乐，会慢一些）", value=False)
                    with gr.Accordion(ADV_LABEL, open=False):
                        with gr.Row():
                            asr_default = str(cfg.get_path("prepare.asr.engine", "faster-whisper") or "faster-whisper")
                            if asr_default not in [v for _, v in ASR_CHOICES]:
                                asr_default = "faster-whisper"
                            c["asr"] = gr.Radio(ASR_CHOICES, value=asr_default, label="识别文字用哪个引擎")
                            c["lang"] = gr.Radio(LANG_CHOICES, value="auto", label="素材语言")
                            c["denoise"] = gr.Radio(DENOISE_CHOICES, value="auto", label="降噪")
                    with gr.Row():
                        c["prep_btn"] = gr.Button(PREP_BTN, variant="primary", scale=3)
                        stop_button("prep_stop")
                    c["prep_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["prep_md"] = gr.Markdown(elem_classes="vt-md")
                    c["prep_next"] = gr.Button(PREP_NEXT, visible=False)
                    log_box("prep_log")

                    gr.Markdown("### ✍️ 校对文字（可选，但能明显提升效果）\n"
                                "**双击格子就能改错字，改完按回车**；不想要的片段把「保留」改成「否」；"
                                "**点一下某一行就能听**（播放器和两次识别的对比在表格下面）。"
                                "改完一定要点「保存修改」。（只改「文字」和「保留」两列就行）")
                    c["clips_count"] = gr.Markdown(elem_classes="vt-md")
                    with gr.Row():
                        c["proof_btn"] = gr.Button(PROOF_BTN, scale=2,
                                                   visible=callable(getattr(wf, "run_proofcheck", None)))
                        stop_button("proof_stop")
                        c["only_sus"] = gr.Checkbox(label="只看可能有错的", value=False, scale=1)
                        load_clips = gr.Button("🔄 重新载入", scale=1)
                    c["proof_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["proof_md"] = gr.Markdown(elem_classes="vt-md")
                    c["sel_clip"] = gr.State("")
                    c["clips_base"] = gr.State({})
                    c["clips"] = gr.Dataframe(headers=CLIP_HEADERS, datatype=CLIP_TYPES, interactive=True, wrap=True,
                                              latex_delimiters=[], col_count=(len(CLIP_HEADERS), "fixed"),
                                              column_widths=["5%", "9%", "8%", "6%", "6%", "34%", "22%", "10%"])
                    # 播放器、对比、「采用建议」都放在表格下面：点一行时它们会出现/消失，放在上面会把整张表顶上顶下，
                    # 双击改字时第二下就点到别的格子上了（gradio 4.24 只认同一个格子上的双击）
                    c["clip_audio"] = gr.Audio(label="试听选中的片段", type="filepath", autoplay=True, interactive=False,
                                               visible=False)
                    c["clip_diff"] = gr.HTML("")
                    c["adopt_btn"] = gr.Button(ADOPT_BTN, visible=False, size="sm")
                    gr.Markdown("标红只是提醒「可能有错」，不一定真错；也可能有个别错字没被发现。"
                                "「可能有错（红色）」这一列只用来看，改字请改「文字」列（双击它会看到格式代码，不用管）。",
                                elem_classes="vt-honest")
                    save_clips = gr.Button("保存修改", variant="primary")
                    c["review_md"] = gr.Markdown(elem_classes="vt-md")

                # ---------------------------------------------------- ② 训练
                with gr.Tab("② 训练模型", id="train") as train_tab:
                    gr.Markdown("直接点「开始训练」就行，电脑会自动完成（素材越多越久，通常 30~90 分钟）。"
                                "训练时可以去做别的事，但不要关闭黑色窗口。训练结束后会自动挑出最像你的模型，"
                                "并把语速调得和你本人一样。")
                    c["train_plan"] = gr.Markdown(PLAN_DEFAULT, elem_classes="vt-md")
                    with gr.Row():
                        c["train_btn"] = gr.Button(TRAIN_BTN, variant="primary", scale=3)
                        c["select_btn"] = gr.Button(SELECT_BTN, scale=2)
                        stop_button("train_stop")
                    c["train_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["train_md"] = gr.Markdown(elem_classes="vt-md")
                    c["train_next"] = gr.Button(TRAIN_NEXT, visible=False)
                    with gr.Accordion("高级设置（一般不用改，数字保持 0 = 自动）", open=False):
                        gr.Markdown("**GPT-SoVITS**（推荐）：用你的素材微调，最像你；需要 NVIDIA 显卡（6GB+）。"
                                    "**Qwen3-TTS** 也可以微调（显存需求更大）。**IndexTTS** 不需要训练，可以直接去第③步。")
                        c["t_backend"] = gr.Radio(TRAIN_BACKENDS, value=self.default_train, label="引擎")
                        with gr.Row():
                            c["s_ep"] = gr.Number(label="音色训练轮数（0 = 自动）", value=0, precision=0, minimum=0)
                            c["g_ep"] = gr.Number(label="语气训练轮数（0 = 自动）", value=0, precision=0, minimum=0)
                            c["q_ep"] = gr.Number(label="Qwen3 训练轮数（0 = 默认）", value=0, precision=0, minimum=0)
                            c["bs"] = gr.Number(label="每批数量 batch（0 = 自动；显存不够报错时改成 2）", value=0,
                                                precision=0, minimum=0)
                        c["dpo"] = gr.Radio(DPO_CHOICES, value="auto", label="DPO（GPT-SoVITS 的实验功能）",
                                            info="自动 = 不开（实验功能，没有可靠的证据说明能让声音更像）。"
                                                 "想试再选「开」：语气训练会慢 2～4 倍，显存最好 ≥ 22 GB，不够时容易出错。")
                    log_box("train_log", 16)

                # ---------------------------------------------------- ③ 生成
                with gr.Tab("③ 生成讲课音频", id="gen") as gen_tab:
                    c["gen_warn"] = gr.Markdown(elem_classes="vt-md")
                    gr.Markdown("粘贴讲稿或上传讲稿文件。空一行 = 段落停顿；`[停顿=1.5]` 指定停顿秒数。"
                                "多音字、术语读音可在 `workspace/声音名/lexicon.txt` 里纠正。")
                    with gr.Row():
                        with gr.Column(scale=3):
                            c["script"] = gr.Textbox(label="讲稿", lines=12, placeholder="大家好，今天我们来学习……")
                            c["script_file"] = gr.File(label="或上传讲稿文件（txt / docx / md / srt）", file_count="single",
                                                       file_types=list(SCRIPT_TEXT_EXTS + SCRIPT_SUB_EXTS))
                            c["script_hint"] = gr.Markdown(elem_classes="vt-md")
                            with gr.Row():
                                c["out_name"] = gr.Textbox(label="保存的文件名（可以不填）", placeholder="例如：第3课 牛顿第二定律",
                                                           scale=2)
                                fmt_default = str(cfg.get_path("synth.output_format", "wav") or "wav")
                                c["out_fmt"] = gr.Radio(FORMAT_CHOICES, value=fmt_default if fmt_default in ("wav", "mp3") else "wav",
                                                        label="保存格式", scale=2)
                        with gr.Column(scale=2):
                            c["quality"] = gr.Radio(QUALITY_CHOICES, value="balanced", label="质量")
                            c["quality_note"] = gr.Markdown(QUALITY_NOTE, elem_classes="vt-honest")
                            c["speed"] = gr.Slider(-30, 30, value=0, step=1, label=SPEED_LABEL)
                            c["speed_text"] = gr.Markdown(f"**{_speed_text(0)}**　<small>{SPEED_NOTE}</small>")
                            c["speed_try"] = gr.Button(SPEED_BTN, size="sm")
                            c["speed_audio"] = gr.Audio(label="语速试听", type="filepath", autoplay=True, visible=False,
                                                        interactive=False)
                            c["redo"] = gr.Textbox(label="只重新生成第几句（例如 3,5,8-10；留空 = 全部）", value="")
                            with gr.Accordion(ADV_LABEL, open=False):
                                c["s_backend"] = gr.Radio(self.synth_backends, value=self.default_synth, label="引擎")
                                c["ref"] = gr.Textbox(label="指定参考音频编号（留空 = 自动挑选）", value="")
                            with gr.Row():
                                c["gen_btn"] = gr.Button(GEN_BTN, variant="primary", scale=3)
                                stop_button("gen_stop")
                    c["gen_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["gen_md"] = gr.Markdown(elem_classes="vt-md")
                    c["out_audio"] = gr.Audio(label="结果", type="filepath", interactive=False)
                    with gr.Group(visible=False) as var_box:
                        c["var_box"] = var_box
                        c["var_md"] = gr.Markdown(elem_classes="vt-md")
                        with gr.Row():
                            c["var_a"] = gr.Audio(label="版本 A：未去杂音", type="filepath", interactive=False)
                            c["var_b"] = gr.Audio(label="版本 B：去杂音", type="filepath", interactive=False)
                        c["var_choice"] = gr.Radio([("版本 A：未去杂音", "未去杂音"), ("版本 B：去杂音", "去杂音")],
                                                   label="最终使用哪个版本", value=None)
                        c["var_note"] = gr.Markdown(elem_classes="vt-md")
                    c["out_files"] = gr.File(label="下载（音频 / 字幕）", file_count="multiple", interactive=False)
                    c["gen_state"] = gr.State({})
                    with gr.Row(visible=False) as gen_after:
                        c["gen_after"] = gen_after
                        open_dir = gr.Button("📂 打开保存文件夹", size="sm", visible=self.local)
                        locate = gr.Button("📍 在文件夹里找到这个文件", size="sm", visible=self.local)
                        ev_jump = gr.Button("④ 评估刚才生成的音频 →", size="sm")
                    c["open_msg"] = gr.Markdown(elem_classes="vt-md")
                    gr.Markdown("#### 每一句的情况　👆 点表格里任意一句，就能单独听这一句")
                    c["gen_table"] = gr.Dataframe(_blank_rows(GEN_HEADERS), headers=GEN_HEADERS,
                                                  datatype=["number", "str", "str", "str", "str"],
                                                  interactive=False, wrap=True, height=420,
                                                  column_widths=["7%", "50%", "13%", "12%", "18%"])
                    c["seg_audio"] = gr.Audio(label="单独听这一句", type="filepath", autoplay=True, interactive=False,
                                              visible=False)
                    gr.Markdown(f"{HONEST_SIM}{PCT_HELP}", elem_classes="vt-honest")
                    log_box("gen_log", 8)

                # ---------------------------------------------------- ④ 评估
                with gr.Tab("④ 试试像不像（可选）", id="eval"):
                    gr.Markdown("上传任意一段音频，看看它和你的声音有多像（可以用来对比不同引擎、不同参数）。\n\n"
                                f"<small>{HONEST_SIM}{PCT_HELP}</small>")
                    c["ev_audio"] = gr.Audio(label="音频", type="filepath")
                    c["ev_text"] = gr.Textbox(label="对应文字（可选，填了会检查错字）")
                    with gr.Row():
                        ev_btn = gr.Button("评估", variant="primary")
                        ev_last = gr.Button("📥 评估刚才生成的音频")
                    c["ev_out"] = gr.Markdown()

                # ---------------------------------------------------- ⑤ 鉴别
                with gr.Tab("⑤ 鉴别", id="verify") as verify_tab:
                    gr.Markdown("### 🤖 机器鉴别\n用声纹模型给生成的音频打分，看它们「像你本人」百分之多少，并排好名次。"
                                "不选文件时，自动用素材里留出的你的真实录音，和最近一次生成的结果。\n\n"
                                f"<small>{HONEST_SIM}{PCT_HELP}</small>")
                    with gr.Row():
                        c["vf_orig"] = gr.File(label="你的原始录音（可选，可多选）", file_count="multiple")
                        c["vf_gen"] = gr.File(label="要鉴别的生成音频（可选，可多选）", file_count="multiple")
                    c["vf_btn"] = gr.Button(VERIFY_BTN, variant="primary")
                    c["vf_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["vf_md"] = gr.Markdown(elem_classes="vt-md")
                    c["vf_table"] = gr.Dataframe(_blank_rows(VERIFY_HEADERS), headers=VERIFY_HEADERS,
                                                 datatype=["number", "str", "str", "str", "number", "str"],
                                                 interactive=False, wrap=True)
                    has_blind = callable(getattr(wf, "build_blind_test", None))
                    gr.Markdown("### 👂 观众盲听测试\n电脑从你的真实录音里挑几句，再用你的模型读同样的句子，"
                                "打乱顺序编上号。让听众逐段选「真人」还是「生成」，看大家能不能分辨出来。"
                                + ("（会用到显卡，大约几分钟）" if has_blind else "\n\n（这个版本还没有装上这个功能。）"))
                    with gr.Row(visible=has_blind):
                        c["bt_n"] = gr.Slider(2, MAX_BLIND // 2, value=min(10, MAX_BLIND // 2), step=1,
                                              label="用几句话（真人和生成的各这么多段）")
                        c["bt_btn"] = gr.Button(BLIND_BTN, variant="primary")
                    c["bt_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["bt_md"] = gr.Markdown(elem_classes="vt-md")
                    c["bt_state"] = gr.State({})
                    for i in range(MAX_BLIND):
                        with gr.Row():
                            c[f"bt_audio_{i}"] = gr.Audio(label=f"第 {i + 1} 段", type="filepath", visible=False,
                                                          interactive=False, scale=3)
                            c[f"bt_pick_{i}"] = gr.Radio([("真人", "real"), ("生成", "fake")], label=f"第 {i + 1} 段是：",
                                                         visible=False, scale=1)
                    c["bt_submit"] = gr.Button(SUBMIT_BTN, variant="primary", visible=False)
                    c["bt_result"] = gr.Markdown(elem_classes="vt-md")
                    with gr.Accordion("📝 批改收上来的答题卡（离线测试、网页刷新过也能用）", open=False, visible=has_blind):
                        gr.Markdown("选一次以前做的盲听测试（上面会重新显示那次的录音），把听众交回来的答案填进框里，点「批改」。"
                                    "可以写 `1 真人 2 生成 3 真人 ……`，也可以不写编号、按顺序写 `真人 生成 真人 ……`。")
                        with gr.Row():
                            c["bt_old"] = gr.Dropdown([], label="选一次盲听测试", value=None, scale=4)
                            bt_old_refresh = gr.Button("🔄 刷新", size="sm", scale=1)
                        c["bt_paste"] = gr.Textbox(label="听众的答案", lines=3,
                                                   placeholder="例如：1 真人 2 生成 3 真人 4 生成 ……")
                        bt_grade = gr.Button("📝 批改", variant="primary")
                        c["bt_grade_md"] = gr.Markdown(elem_classes="vt-md")
                    log_box("vf_log", 8)

                # ---------------------------------------------------- 环境检查
                with gr.Tab("🩺 环境检查", id="env") as env_tab:
                    c["doc_summary"] = gr.Markdown("打开这一页会自动检查一次（大约 10~30 秒）。")
                    with gr.Row():
                        doc_btn = gr.Button("🔄 重新检查（约 10~30 秒）", scale=2)
                        c["dl_btn"] = gr.Button(DL_BTN, variant="primary", scale=2)
                        stop_button("dl_stop")
                    c["doc_bar"] = gr.HTML("", elem_classes="vt-bar-box")
                    c["doc_md"] = gr.Markdown(elem_classes="vt-md")
                    c["doc_out"] = gr.Dataframe(_blank_rows(DOC_HEADERS), headers=DOC_HEADERS, datatype=["number", "str", "str", "str"],
                                                interactive=False, wrap=True, column_widths=["6%", "8%", "26%", "60%"])
                    c["doc_total"] = gr.Markdown()
                    with gr.Accordion("可选组件（没装也不影响使用）", open=False, visible=False) as doc_opt_acc:
                        c["doc_opt_acc"] = doc_opt_acc
                        c["doc_opt"] = gr.Dataframe(_blank_rows(DOC_HEADERS), headers=DOC_HEADERS,
                                                    datatype=["number", "str", "str", "str"],
                                                    interactive=False, wrap=True)
                    log_box("doc_log", 10)

            # ======================================================== 事件
            after_outs = [c["gpu_badge"], c["task_banner"]] + outs(self.LIB_OUT)
            voice_outs = outs(self.VOICE_OUT)

            def gen_warn(voice: Any, backend: Any) -> str:
                """③ 页顶部的提醒（还没准备素材 / 还没训练），按现在选的声音和引擎重新算。"""
                try:
                    return _gen_warn_md(cfg, voice, backend)
                except Exception as exc:
                    log.debug(f"刷新 ③ 的提醒失败：{exc}")
                    return ""

            # 顶部
            load_outs = voice_outs + [c["voice"], c["task_banner"], c["quick_banner"]] + outs(self.LIB_OUT)
            app.load(_safe("打开网页", len(load_outs), 0)(self.on_load), None, load_outs, **quick)
            app.load(self.on_load_gpu, None, [c["gpu_badge"], c["quality"], c["quality_note"]], **quick)
            gpu_btn.click(self.refresh_gpu, None, c["gpu_badge"], **quick)
            refresh.click(self.refresh_voices, c["voice"], c["voice"], **quick).then(
                self.library, None, outs(self.LIB_OUT), **quick)
            c["voice"].change(_safe("读取声音", len(voice_outs), 0)(self.on_voice_change),
                              [c["voice"], c["only_sus"], c["s_backend"]], voice_outs, **quick)
            plan_in = [c["voice"], c["t_backend"], c["s_ep"], c["g_ep"], c["bs"], c["dpo"]]
            c["voice"].change(self.train_plan_preview, plan_in, c["train_plan"], **quick)

            def lib_pick(table: Any, evt: gr.SelectData) -> Tuple[Any, Any]:
                try:
                    return self.on_library_pick(table, _evt_index(evt)[0])
                except Exception as exc:
                    log.warning(f"声音库选择出错：{exc}")
                    return _upd(), _upd()

            c["lib_table"].select(lib_pick, c["lib_table"], [c["voice"], c["lib_audio"]], **quick)

            # ①
            clip_outs = [c["clips_count"], c["clips"]]
            prep_in = [c["voice"], c["files"], c["folder"], c["asr"], c["lang"], c["denoise"], c["separate"],
                       c["only_sus"], c["clips"]]
            c["prep_btn"].click(_settled(self.do_prepare), prep_in, outs(self.PREP_OUT), **heavy).then(
                _safe("载入片段", 3, 0)(self.after_prepare_clips), [c["voice"], c["only_sus"], c["clips"], c["clips_base"]],
                clip_outs + [c["clips_base"]], **quick).then(
                self.after_task, None, after_outs, **quick).then(gen_warn, [c["voice"], c["s_backend"]], c["gen_warn"], **quick)
            c["prep_next"].click(lambda: gr.Tabs(selected="train"), None, tabs, **quick)
            load_clips.click(_safe("载入片段", 2, 0)(self.load_clips), [c["voice"], c["only_sus"]], clip_outs, **quick)
            c["only_sus"].change(_safe("载入片段", 2, 0)(self.refresh_clips), [c["voice"], c["only_sus"], c["clips"]],
                                 clip_outs, **quick)

            def clip_pick(voice: Any, table: Any, evt: gr.SelectData) -> Tuple[Any, ...]:
                try:
                    row, col = _evt_index(evt)
                    return self.on_clip_pick(voice, table, row, col, getattr(evt, "value", None))
                except Exception as exc:
                    log.warning(f"试听片段出错：{exc}")
                    return _upd(), "", _btn(ADOPT_BTN, visible=False), ""

            c["clips"].select(clip_pick, [c["voice"], c["clips"]],
                              [c["clip_audio"], c["clip_diff"], c["adopt_btn"], c["sel_clip"]], **quick)
            c["adopt_btn"].click(_safe("采用建议", 5, 0)(self.do_adopt), [c["voice"], c["sel_clip"], c["only_sus"], c["clips"]],
                                 [c["review_md"], c["clips_count"], c["clips"], c["clip_diff"], c["adopt_btn"]], **quick)
            save_clips.click(_safe("保存修改", 3, 0)(self.do_save), [c["voice"], c["clips"], c["only_sus"]],
                             [c["review_md"], c["clips_count"], c["clips"]], **quick)
            c["proof_btn"].click(_settled(self.do_proofcheck), [c["voice"], c["only_sus"]], outs(self.PROOF_OUT),
                                 **heavy).then(
                _safe("载入片段", 2, 0)(self.refresh_clips), [c["voice"], c["only_sus"], c["clips"]], clip_outs, **quick).then(
                self.after_task, None, after_outs, **quick)

            # ②
            train_in = [c["voice"], c["t_backend"], c["s_ep"], c["g_ep"], c["q_ep"], c["bs"], c["dpo"]]
            c["train_btn"].click(_settled(self.do_train), train_in, outs(self.TRAIN_OUT), **heavy).then(
                self.after_task, None, after_outs, **quick).then(gen_warn, [c["voice"], c["s_backend"]], c["gen_warn"], **quick)
            c["select_btn"].click(_settled(self.do_select), [c["voice"], c["t_backend"]], outs(self.TRAIN_OUT),
                                  **heavy).then(
                self.after_task, None, after_outs, **quick).then(gen_warn, [c["voice"], c["s_backend"]], c["gen_warn"], **quick)
            c["train_next"].click(lambda: gr.Tabs(selected="gen"), None, tabs, **quick)
            # 打开「② 训练模型」页、换引擎、改高级设置时，重新预览这次会怎么训练（只读文件和 nvidia-smi，很快）
            train_tab.select(self.train_plan_preview, plan_in, c["train_plan"], **quick)
            c["t_backend"].change(self.train_plan_preview, plan_in, c["train_plan"], **quick)
            c["dpo"].change(self.train_plan_preview, plan_in, c["train_plan"], **quick)
            for name in ("s_ep", "g_ep", "bs"):
                # 数字框每按一个键就触发一次；默认的 trigger_mode="once" 会把预览还没算完时按的键丢掉
                # （打「12」只预览到「1」）。always_last：算完后再按最后的值算一次。
                c[name].input(self.train_plan_preview, plan_in, c["train_plan"], trigger_mode="always_last", **quick)
                c[name].submit(self.train_plan_preview, plan_in, c["train_plan"], trigger_mode="always_last", **quick)

            # ③
            c["script_file"].upload(self.on_script_upload, [c["script_file"], c["out_name"]],
                                    [c["script"], c["script_file"], c["script_hint"], c["out_name"]], **quick)
            c["s_backend"].change(gen_warn, [c["voice"], c["s_backend"]], c["gen_warn"], **quick)
            # 刚做完素材准备/训练再切到这一页，提醒要跟着变（不然还写着「还没训练」）
            gen_tab.select(gen_warn, [c["voice"], c["s_backend"]], c["gen_warn"], **quick)
            c["speed"].change(lambda s: f"**{_speed_text(s)}**　<small>{SPEED_NOTE}</small>", c["speed"], c["speed_text"],
                              **quick)
            gen_in = [c["voice"], c["script"], c["script_file"], c["s_backend"], c["quality"], c["speed"], c["ref"], c["redo"],
                      c["out_name"], c["out_fmt"]]
            c["gen_btn"].click(_settled(self.do_generate), gen_in, outs(self.GEN_OUT), **heavy).then(
                self.after_task, None, after_outs, **quick)
            c["speed_try"].click(_settled(self.do_speed_preview), [c["voice"], c["script"], c["speed"], c["s_backend"]],
                                 outs(self.SPEED_OUT), **heavy)
            c["var_choice"].input(_safe("切换版本", 3, 2)(self.on_choose_variant), [c["voice"], c["gen_state"], c["var_choice"]],
                                  [c["out_audio"], c["out_files"], c["var_note"]], **quick)
            open_dir.click(_safe("打开文件夹", 1)(lambda v, s: self.open_outputs(v, s, False)), [c["voice"], c["gen_state"]],
                           c["open_msg"], **quick)
            locate.click(_safe("打开文件夹", 1)(lambda v, s: self.open_outputs(v, s, True)), [c["voice"], c["gen_state"]],
                         c["open_msg"], **quick)

            def gen_pick(state: Any, table: Any, evt: gr.SelectData) -> Any:
                try:
                    return self.on_gen_pick(state, table, _evt_index(evt)[0])
                except Exception as exc:
                    log.warning(f"单独播放这一句出错：{exc}")
                    return _upd()

            c["gen_table"].select(gen_pick, [c["gen_state"], c["gen_table"]], c["seg_audio"], **quick)

            # ④
            def do_eval(voice: Any, audio: Any, text: Any, progress: Any = gr.Progress()) -> str:
                return self.eval_impl(voice, audio, text, progress)

            ev_btn.click(_safe("评估", 1)(do_eval), [c["voice"], c["ev_audio"], c["ev_text"]], c["ev_out"])
            ev_last.click(lambda st: _upd(value=(st or {}).get("audio") or None), c["gen_state"], c["ev_audio"], **quick)
            ev_jump.click(lambda st: (gr.Tabs(selected="eval"), _upd(value=(st or {}).get("audio") or None)),
                          c["gen_state"], [tabs, c["ev_audio"]], **quick)

            # ⑤
            c["vf_btn"].click(_settled(self.do_verify), [c["voice"], c["vf_orig"], c["vf_gen"], c["gen_state"]],
                              outs(self.VERIFY_OUT), **heavy).then(self.after_task, None, after_outs, **quick)
            c["bt_btn"].click(_settled(self.do_blind), [c["voice"], c["bt_n"], c["quality"]], outs(self.BLIND_OUT),
                              **heavy).then(
                self.after_task, None, after_outs, **quick).then(self.blind_tests, c["voice"], c["bt_old"], **quick)
            c["bt_submit"].click(_safe("提交答案", len(self.BLIND_SUBMIT_OUT), 0)(self.on_blind_submit),
                                 [c["bt_state"]] + [c[f"bt_pick_{i}"] for i in range(MAX_BLIND)],
                                 outs(self.BLIND_SUBMIT_OUT), **quick)
            verify_tab.select(self.blind_tests, c["voice"], c["bt_old"], **quick)
            bt_old_refresh.click(self.blind_tests, c["voice"], c["bt_old"], **quick)
            c["bt_old"].input(_safe("打开盲听测试", len(self.BLIND_OPEN_OUT), 0)(self.on_blind_open),
                              [c["voice"], c["bt_old"]], outs(self.BLIND_OPEN_OUT), **quick)
            bt_grade.click(_safe("批改", 1)(self.on_blind_grade), [c["voice"], c["bt_old"], c["bt_paste"]],
                           c["bt_grade_md"], **quick)

            # 环境检查
            doc_outs = [c["doc_summary"], c["doc_out"], c["doc_total"], c["doc_opt"], c["doc_opt_acc"]]
            env_tab.select(_safe("环境检查", 5, 0)(lambda: self.run_doctor(False)), None, doc_outs)
            doc_btn.click(_safe("环境检查", 5, 0)(lambda: self.run_doctor(True)), None, doc_outs)
            c["dl_btn"].click(_settled(self.do_download), None, outs(self.DL_OUT), **heavy).then(
                self.after_task, None, after_outs, **quick)
        return app


def build_app(cfg: Config, local: bool = True) -> Any:
    """建好整个网页（不启动）。local=False 时（别的电脑通过网络访问）不显示「打开文件夹」按钮。"""
    return WebUI(cfg, local=local).build()


def launch(cfg: Config, host: str = "127.0.0.1", port: int = 7860, share: bool = False) -> None:
    """保留旧的入口：真正的启动逻辑（端口、已在运行、代理……）在 launcher 里。"""
    from voicetwin.webui.launcher import launch as _launch

    return _launch(cfg, host=host, port=port, share=share)
