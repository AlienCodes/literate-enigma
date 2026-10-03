"""查找可能的错字（R6）：把每段素材的文字再检查一遍，标出可能识别错的地方（标红）。

三种证据，合在一起打分（noisy-OR：score = 1 - ∏(1 - w)，score ≥ 0.45 才标红）：

1. 第二个识别引擎再听一遍，和现在的文字逐字对比（不一样的地方就是可疑的地方）：
   - 主识别用 faster-whisper（默认）→ 用 FunASR（paraformer，阿里的中文模型）听中文片段；
   - 主识别用 FunASR → 用 faster-whisper；
   - 只用字幕（engine: none）→ 先用 FunASR，没有就用 faster-whisper。
2. faster-whisper 的逐词把握程度（word_timestamps=True 时每个词的 probability）：把握很低的字。
   没有第二个引擎、但装了 faster-whisper 时，就重新听一遍只取这个（"faster-whisper-words"）。
3. 规则（不需要任何模型）：中文里夹着像乱码的大写英文（VFIXED、WHOOZ）、像是把中文听成英文的
   单词（户字 → whose、的 → the）、同一个词或短语连续重复、不该出现的外文字符。

对比前先统一写法，所以下面这些不算错：标点、空格、全角半角、大小写、繁简体、
数字写法（2024 = 二零二四，50% = 百分之五十，3.5 = 三点五，1/3 = 三分之一）、
语气词（嗯、呃、那个）、同音字（他/她、的/得、在/再；训练按读音，不影响效果）、
另一个引擎把英文写成了中文音译（Python ↔ 派森）。

所有模型都是第一次用到时才加载（funasr 的导入就要好几秒）；没装、加载失败、或者某一段出错时，
自动退回到下一种方法，最差也会用规则检查，不会让整个任务失败。

对外接口（R6）：
- available_checker(cfg) -> (引擎名, 中文说明)
- find_suspects(project, cfg, progress=None, only_kept=True, limit=None) -> {checked, flagged, engine, note, ...}
- render_marked(text, spans) -> str：可疑的字标红（已转义，可放进 gradio 的 markdown 列）
- render_diff_html(text, alt, spans=None) -> str：「识别 A」「识别 B」两行对比
结果写进 record["suspect"] = {"spans": [[start, end], ...], "alt": str, "reasons": [str], "score": float}，
spans 是 record["text"] 里的字符位置；没问题的片段会删掉 "suspect"。
"""

from __future__ import annotations

import difflib
import gc
import html
import importlib.util
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import AbstractSet, Any, Callable, Dict, FrozenSet, Iterable, List, NamedTuple, Optional, Sequence, Set, Tuple

from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import clean_transcript, count_cjk

try:  # U1：停止按钮。没有 progress 模块（或太旧）时什么都不做
    from voicetwin.utils.progress import check_cancel as _check_cancel
except ImportError:  # pragma: no cover - 只在单独合并本单元时发生
    def _check_cancel() -> None:
        return None

log = get_logger("proofcheck")

ProgressFn = Callable[[float, str], None]

# ---------------------------------------------------------------------------- 引擎名（网页和说明里会显示，保持稳定）
ENGINE_FUNASR = "funasr"
ENGINE_WHISPER = "faster-whisper"
ENGINE_WHISPER_WORDS = "faster-whisper-words"
ENGINE_LABELS = {
    ENGINE_FUNASR: "FunASR（阿里的中文识别模型）",
    ENGINE_WHISPER: "faster-whisper",
    ENGINE_WHISPER_WORDS: "faster-whisper（逐字把握程度）",
    "": "规则检查",
}
ENGINE_SHORT = {ENGINE_FUNASR: "FunASR", ENGINE_WHISPER: "faster-whisper", ENGINE_WHISPER_WORDS: "faster-whisper",
                "": ""}

REASON_FUNASR = "用 FunASR（阿里的中文识别模型）把每段中文再听一遍，和现在的文字对比，不一样的地方标红"
REASON_WHISPER = "用 faster-whisper 把每段再听一遍，和现在的文字对比，并标出识别时没把握的字"
REASON_WHISPER_SUBS = "用 faster-whisper 把每段再听一遍，和字幕里的文字对比，不一样的地方标红"
REASON_WORDS = "没有装第二个识别引擎（FunASR）：用 faster-whisper 重新听一遍，标出识别时没把握的字"
REASON_NONE = "没有装可用的识别引擎，只按规则检查（比如中文里夹着奇怪的英文、同一句话连说几遍）；能发现的错字比较少"

#: GPT-SoVITS 整合包自带的 paraformer（和 GSV 的 tools/asr/funasr_asr.py 用的是同一个）
PARAFORMER_LOCAL = "tools/asr/models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
PARAFORMER_ID = "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
SEACO_ID = "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"  # = "paraformer-zh"

# ---------------------------------------------------------------------------- 打分
FLAG_THRESHOLD = 0.45  # 合起来的分数到这个值才标红
SHOW_MIN = 0.3  # 单条证据至少这么强，才在标红时画出来（太弱的只参与打分）
LOW_PROB = 0.45  # faster-whisper 逐词把握程度：低于它算"没把握"
VERY_LOW_PROB = 0.30
W_DIFF = 0.6  # 两个引擎听到的不一样（中文）
W_DIFF_SRT = 0.5  # 文字来自字幕（可能是人工做的）时稍微降低
W_TOTAL = 0.7  # 整句对不上
W_SILENT = 0.5  # 第二个引擎几乎什么都没听到
W_NUMBER = 0.6  # 数字不一样（三十 / 四十）
W_CAPS = 0.7  # 中文里的大写乱码英文
W_CAPS_FREQ = 0.4  # 同一个大写词出现在 3 段以上：多半是真的术语
W_SCRIPT = 0.8  # 不该有的外文字符（日文假名、韩文、俄文、乱码符号）
W_CONFUSABLE = 0.6  # 像是把中文听成了英文的单词
W_CONFUSABLE_SOFT = 0.35  # so / yeah / oh 这类老师常顺口说的英文
W_GARBAGE = 0.6
W_REPEAT = 0.5
W_REPEAT_LONG = 0.6
W_REPEAT_PUNCT = 0.4  # 中间隔着标点的整句重复：可能是故意强调
W_LOWP = 0.5
W_LOWP_WEAK = 0.3
W_EN_VS_CJK = 0.25  # 原文是英文、FunASR 写成了中文音译（Python ↔ 派森）：FunASR 拼不出英文，不算数
W_EN_GUESS = 0.15  # faster-whisper 把中文听成了 the / she 之类：多半是它自己听错
W_LATIN_WEAK = 0.3  # 英文单词拼法不同，但另一边是 FunASR（英文不准）
W_LATIN = 0.5  # 英文不同，另一边是 faster-whisper
W_PARTICLE = 0.2  # 多/少一个"的了着过儿"
W_STUTTER = 0.3  # 另一个引擎听到某个词说了两遍（口误重复）：Whisper 常把它省掉
W_LOGPROB = 0.15  # 整段识别置信度偏低（只在已有别的证据时加分）

SAVE_EVERY = 20  # 每检查这么多段存一次（中途停止也不白做）
MAX_REASONS = 6
MAX_LOAD_FAILS_BEFORE_OK = 3  # 一段都没成功就连续失败这么多次：认为引擎坏了，换下一种方法
MAX_CONSECUTIVE_FAILS = 20
CACHE_VERSION = 1

_LATIN_HEUR = ("caps", "confusable", "garbage")  # 这几种规则标出的英文，可以用第二个引擎的中文替换
#: 对比时"不可靠的那一边"造成的差别：只算弱证据，也不算进"整句对不上"
_WEAK_KINDS = frozenset({"en_vs_cjk", "en_vs_cjk_w", "en_guess", "cjk_vs_en_f", "latin_f", "ins_en_f", "del_en_f",
                         "particle", "stutter"})

# ---------------------------------------------------------------------------- 字符表
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_CN_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_SMALL = {"十": 10, "百": 100, "千": 1000}
_CN_BIG = {"万": 10 ** 4, "亿": 10 ** 8}
_CN_NUM = set(_CN_DIGITS) | set(_CN_SMALL) | set(_CN_BIG)

#: 符号的读法（"1+1=2" 和 "一加一等于二" 算一样）
_SYMBOL_READINGS = {"+": "加", "=": "等于", "×": "乘", "÷": "除以", "≈": "约等于", "≠": "不等于", "≥": "大于等于",
                    "≤": "小于等于", "℃": "摄氏度", "°": "度"}

FILLER_CHARS = set("嗯呃额啊哦噢喔唉诶欸哎呀吧呢嘛啦哈噻")
FILLER_WORDS = ("就是说", "那个", "这个", "就是", "然后", "对吧", "是吧", "的话")
PARTICLES = set("的地得了着过儿")

#: 没装 pypinyin 时用的同音字小表（同组的字读音和声调都一样）
_HOMO_GROUPS = ("他她它祂", "的地得", "在再", "做作坐座", "象像向项", "须需", "账帐", "副付负富复", "截节结",
                "以已", "到道", "是事市式试世示视室势适", "进近", "和合", "意义亿忆艺议亦易异益", "会汇绘惠",
                "气器汽弃", "字自", "力立利例厉")
_HOMO = {ch: g for g in _HOMO_GROUPS for ch in g}

#: 没装 zhconv / opencc 时用的繁体 → 简体小表（常用字，已对照 zhconv 检查过）
_T2S_PAIRS = (
    "們们個个這这講讲說说話话時时會会來来對对為为與与開开關关問问題题麼么點点經经過过還还現现發发從从動动應应種种樣样"
    "實实機机體体長长書书車车東东見见氣气電电語语頭头錯错讓让認认識识聽听寫写讀读習习課课員员價价學学數数後后裡里裏里"
    "邊边國国進进業业歡欢樂乐謝谢請请嗎吗號号碼码鐘钟歲岁萬万億亿兩两幾几張张條条雙双給给誰谁總总結结練练級级紅红綠绿"
    "線线網网絡络統统計计設设試试詞词該该論论證证議议變变選选達达運运遠远適适邏逻輯辑輸输轉转軟软輕轻較较載载辦办務务"
    "勢势區区醫医華华單单廣广廠厂慣惯戰战擇择據据擊击斷断極极構构標标權权歷历歸归決决沒没測测準准滿满漢汉無无熱热爾尔"
    "狀状獨独環环產产畫画當当盡尽監监確确稱称穩稳簡简類类純纯紙纸細细組组維维編编聯联聲声職职腦脑興兴舉举處处補补製制"
    "複复規规視视覺觉觀观訓训記记許许評评譯译貝贝負负財财責责貨货質质費费資资賽赛趕赶軍军輪轮農农連连週周遊游違违"
    "鄉乡釋释錄录鐵铁鏡镜門门閒闲間间陽阳階阶際际隨随險险隱隐雖虽雜杂雞鸡離离難难雲云靈灵靜静響响頁页項项順顺預预領领"
    "頻频顏颜願愿顯显風风飛飞飯饭館馆馬马驗验髮发鬆松魚鱼鳥鸟麵面黃黄齊齐齒齿龍龙歐欧鬥斗礎础禮礼競竞筆笔節节範范築筑"
    "簽签籃篮糧粮緊紧績绩繼继續续義义聖圣臉脸臨临葉叶藝艺蘇苏蘭兰蟲虫衛卫裝装親亲覽览誤误調调談谈謂谓護护讚赞豐丰買买"
    "賣卖賞赏購购輛辆辭辞郵邮針针銀银銷销鋼钢錢钱鍵键鎮镇閱阅隊队陸陆陳陈霧雾韓韩頓顿顧顾飲饮養养餘余驚惊驅驱鬧闹麥麦"
    "黨党齡龄詳详師师傳传僅仅優优儘尽兒儿內内凈净劃划劇剧劉刘勝胜勞劳協协厲厉參参喚唤嚴严圍围園园圖图團团報报場场塊块"
    "壓压壞坏夠够夢梦奮奋婦妇媽妈孫孙寧宁審审導导將将屆届層层島岛帶带幫帮庫库彈弹徑径復复恆恒惡恶愛爱態态慮虑憶忆懷怀"
    "戲戏拋抛換换揮挥損损搖摇攝摄擁拥擔担擴扩敵敌斂敛舊旧暫暂曆历術术桿杆棄弃檢检櫃柜殺杀漸渐潔洁濟济燈灯爭争爺爷牆墙"
    "獎奖瑪玛畢毕異异療疗盤盘穀谷筍笋糾纠紀纪約约紛纷終终絕绝絲丝綜综緒绪緣缘縣县縮缩罰罚羅罗聞闻肅肃脫脱臺台艱艰蔣蒋"
    "藥药蘋苹虛虚蝦虾蠻蛮")
_T2S = dict(zip(_T2S_PAIRS[0::2], _T2S_PAIRS[1::2]))

#: 常见的英文缩写 / 术语（大写比较）；都不当成"乱码"。项目的 lexicon.txt 里的词也会加进来。
ACRONYMS = frozenset("""
AI API APP CPU GPU NPU TPU RAM ROM SSD HDD USB HDMI WIFI PDF PPT PPTX DOC DOCX XLS XLSX CSV TXT JPG JPEG PNG GIF SVG
MP3 MP4 AVI MOV HTML CSS JSON XML SQL URL HTTP HTTPS FTP SSH IP TCP UDP DNS VPN LAN WAN NAS IT IOS OS PC CEO CFO CTO COO
HR KPI OKR ROI GDP CPI PPI PMI IPO ETF VIP DIY FAQ CAD BIM UI UX ID OK QQ VR AR MR XR IOT LLM GPT AIGC NLP CNN RNN LSTM
GAN TTS ASR OCR SDK IDE ATM NBA CBA CCTV BBC USA UK EU UN WHO WTO NASA MBA PHD GRE GMAT IELTS TOEFL SAT DNA RNA PCR
MRI ECG BMI LED LCD OLED PCB CNC PLC ERP CRM SAAS SEO SEM GPS SIM SMS APK EXE DLL BUG CMD PPP GNU AWS GCP RGB CMYK
DPI FPS HDR PS PR AE AM PM ABC TV DVD CD NFC PIN QR OA OTA SOP PDCA SWOT PEST MECE STEM STEAM AP IB
SUM IF IFS AND OR NOT AVERAGE COUNT COUNTA COUNTIF COUNTIFS SUMIF SUMIFS VLOOKUP HLOOKUP XLOOKUP INDEX MATCH LEFT RIGHT
MID LEN TRIM ROUND MAX MIN IFERROR TEXT DATE TODAY NOW RANK
WPS EXCEL WORD OFFICE PYTHON JAVA LINUX WINDOWS MAC MACOS ANDROID IPHONE IPAD CHATGPT DEEPSEEK MATLAB SPSS STATA
NVIDIA INTEL AMD ARM IBM RTX GTX CUDA HP DELL MOOC SPOC LMS VLOG TED
SCI SSCI CSSCI EI CNKI GPA CET HSK ACT PBL OBE CDIO BOPPPS SAS AMOS ICT ICU HIV AIDS SARS COVID UNESCO APEC NATO IMF
FBI CIA BMW KFC TCL BYD ETC ZIP RAR KTV EMBA MPA MPACC NGO UFO CPA ACCA CFA QA QC SKU KOL LOL OMG BTW ASAP
VALUE SUMPRODUCT OFFSET INDIRECT AVERAGEIF MEDIAN MODE STDEV ROUNDUP ROUNDDOWN INT ABS TRUE FALSE MONTH YEAR DAY
WEEKDAY DATEDIF TEXTJOIN FILTER SORT UNIQUE SUBTOTAL CONCATENATE
SELECT FROM WHERE JOIN NULL GROUP ORDER PHP JSP ASP AJAX REST DOS BIOS UNIX GCC MVC ORM CRUD UML OOP RAID
""".split())
_ROMAN = re.compile(r"^(?=[IVXLCDM]+$)M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
#: 夹在中文里时，多半是把中文听成了英文（户字 → whose，的 → the，是/谁 → she，说/所 → so，万 → one，好 → how）
CONFUSABLE_EN = frozenset("""whose who how she say the one way why me my no know now show sure shoe see sea tea door
low law lay lie pie pay tie die he her here high buy ma na la ha yo ya hum""".split())
#: 老师讲课时也常顺口说的英文：只算弱证据
CONFUSABLE_SOFT = frozenset("so yeah oh wow hi hey bye ah ok okay a o e uh um hmm".split())
_LATIN_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")
_FOREIGN = re.compile(r"[\u3040-\u30fa\u30fc-\u30ff\u31f0-\u31ff\uac00-\ud7af\u1100-\u11ff\u3130-\u318f"
                      r"\u0400-\u04ff\ufffd\ue000-\uf8ff]+")
#: 平时就会连说三遍的字（对对对、好好好、来来来），连续 ≤4 次不算重复错误
TRIPLE_OK = set("对好是行来走嗯哈呵嘻啦哦啊呀嘿喂快慢等哎唉谢") | {"very", "no", "yes", "go"}

#: 标红用的样式（R6 指定，网页校对表和对比面板共用）
RED_SPAN = '<span style="color:#dc2626;font-weight:700;background:#fee2e2">'
GREEN_SPAN = '<span style="color:#15803d;font-weight:700;background:#dcfce7">'
_MD_CHARS = set("\\`*_{}[]()#+-.!|~>$<=:@^")


# ============================================================================ 小工具
def _cfg_get(cfg: Any, dotted: str, default: Any = None) -> Any:
    """cfg 可以是 Config（有 get_path）或普通 dict。"""
    if cfg is None:
        return default
    getter = getattr(cfg, "get_path", None)
    if callable(getter):
        try:
            return getter(dotted, default)
        except Exception:
            pass
    node: Any = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def _report(progress: Optional[ProgressFn], frac: float, msg: str) -> None:
    """报告进度；回调自己出错不影响检查（停止按钮的 TaskCancelled 照常传出去）。"""
    if progress is None:
        return
    try:
        progress(max(0.0, min(1.0, float(frac))), msg)
    except Exception as exc:  # noqa: BLE001
        log.debug(f"进度回调出错（已忽略）：{exc}")


def _why(exc: BaseException) -> str:
    """一句中文的出错原因（有 U5 的 errors.explain 就用它）。"""
    try:
        from voicetwin.errors import explain  # U5

        title = str(explain(exc).title or "").strip()
        if title:
            return title[:120]
    except Exception:
        pass
    text = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
    return text[:120]


def _short(s: str, n: int = 12) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _has(mod: str) -> bool:
    """只查找、不导入（导入 funasr 要好几秒）。测试里会替换它。"""
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _nk(ch: str) -> str:
    return unicodedata.normalize("NFKC", ch).lower()


@lru_cache(maxsize=8192)
def _nk1(ch: str) -> str:
    """NFKC 后如果还是一个字符就用它（全角 Ａ → A），否则保持原样：保证位置不变。"""
    c = unicodedata.normalize("NFKC", ch)
    return c if len(c) == 1 else ch


def _norm_same_len(text: str) -> str:
    return "".join(_nk1(ch) for ch in text)


@lru_cache(maxsize=1)
def _t2s_converter() -> Optional[Callable[[str], str]]:
    try:
        import zhconv  # type: ignore

        return lambda s: zhconv.convert(s, "zh-cn")
    except Exception:
        pass
    try:
        import opencc  # type: ignore

        cc = opencc.OpenCC("t2s")
        return cc.convert
    except Exception:
        return None


@lru_cache(maxsize=16384)
def _simp_char(ch: str) -> str:
    conv = _t2s_converter()
    if conv is not None:
        try:
            s = conv(ch)
            if len(s) == 1:
                return s
        except Exception:
            pass
        return ch
    return _T2S.get(ch, ch)


def _simp_text(text: str) -> str:
    return "".join(_simp_char(ch) if _CJK_RE.match(ch) else ch for ch in text)


def _is_latin_letter(x: str) -> bool:
    return ("a" <= x <= "z") or ("\u00df" <= x <= "\u024f" and x.isalpha())


def _latin_part(ch: str) -> str:
    c = _nk(ch)
    return c if c and all(_is_latin_letter(x) for x in c) else ""


def _is_digit_char(ch: str) -> bool:
    c = _nk1(ch)
    return "0" <= c <= "9"


def _is_numeral(ch: str) -> bool:
    return _is_digit_char(ch) or ch in _CN_NUM


def _latin_key(k: str) -> bool:
    return bool(k) and k != "#" and _is_latin_letter(k[0])


def _han_key(k: str) -> bool:
    return bool(k) and (k == "#" or bool(_CJK_RE.match(k)))


# ============================================================================ 数字（2024 = 二零二四）
def _cn_int(s: str) -> Optional[int]:
    """"两千零二十四" → 2024，"三百五" → 350，"一万五" → 15000。看不懂时返回 None。"""
    total, section = 0, 0
    num: Optional[int] = None
    last_unit = 0
    zero_seen = False
    for ch in s:
        d = _CN_DIGITS.get(ch)
        if d is None and _is_digit_char(ch):
            d = int(_nk1(ch))
        if d is not None:
            if num is not None:
                return None  # "十二三"（十二或十三）这种约数：不比较
            if d == 0:
                zero_seen = True
                continue
            num = d
        elif ch in _CN_SMALL:
            section += (num if num is not None else 1) * _CN_SMALL[ch]
            num, last_unit, zero_seen = None, _CN_SMALL[ch], False
        elif ch in _CN_BIG:
            unit = _CN_BIG[ch]
            section += num or 0
            if section == 0 and total == 0:
                section = 1
            if unit == 10 ** 8:
                total = (total + section) * unit
            else:
                total += section * unit
            section, num, last_unit, zero_seen = 0, None, unit, False
        else:
            return None
    if num is not None:
        if not zero_seen and last_unit >= 10:  # 口语："三百五" = 350
            num *= last_unit // 10
        section += num
    return total + section


def _int_value(t: str) -> Optional[str]:
    if not t:
        return None
    if all(_is_digit_char(c) for c in t):
        return "".join(_nk1(c) for c in t)
    if all(c in _CN_DIGITS or _is_digit_char(c) for c in t):  # 逐位读："二零二四" → 2024
        return "".join(str(_CN_DIGITS[c]) if c in _CN_DIGITS else _nk1(c) for c in t)
    v = _cn_int(t)
    return None if v is None else str(v)


def _real_value(t: str) -> Optional[str]:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([十百千万亿]+)", t)
    if m:  # "3万"、"1.5亿"
        val = float(m.group(1))
        for ch in m.group(2):
            val *= (_CN_SMALL.get(ch) or _CN_BIG.get(ch) or 1)
        return str(int(val)) if abs(val - round(val)) < 1e-9 else repr(val)
    parts = re.split(r"[点.]", t, maxsplit=1)
    if len(parts) == 2:
        ip = _int_value(parts[0]) if parts[0] else "0"
        fp = parts[1]
        if ip is None or not fp or not all(c in _CN_DIGITS or _is_digit_char(c) for c in fp):
            return None
        return ip + "." + "".join(str(_CN_DIGITS[c]) if c in _CN_DIGITS else _nk1(c) for c in fp)
    return _int_value(t)


def _number_value(s: str) -> Optional[str]:
    """一段数字的标准写法："百分之五十" → "50%"，"三分之一" → "1/3"，"1,000" → "1000"。看不懂时 None。"""
    try:
        t = "".join(_nk1(c) for c in s).replace(",", "")
        pct = False
        if t.startswith("百分之"):
            pct, t = True, t[3:]
        if t.endswith("%"):
            pct, t = True, t[:-1]
        if "分之" in t:
            den, nume = t.split("分之", 1)
            a, b = _real_value(nume), _real_value(den)
            v = None if a is None or b is None else f"{a}/{b}"
        elif "/" in t:
            vals = [_real_value(p) for p in t.split("/")]
            v = None if any(x is None for x in vals) else "/".join(vals)  # type: ignore[arg-type]
        else:
            v = _real_value(t)
        if v is None:
            return None
        return v + "%" if pct else v
    except Exception:
        return None


def _num_equal(a: Optional[str], b: Optional[str]) -> bool:
    """两个数字是不是一样（看不懂的一律当作一样，不乱报）。"""
    if a is None or b is None or a == b:
        return True
    if a.endswith("%") != b.endswith("%"):
        return False
    pa, pb = a.rstrip("%").split("/"), b.rstrip("%").split("/")
    if len(pa) != len(pb):
        return False
    try:
        return all(abs(float(x) - float(y)) <= 1e-9 * max(1.0, abs(float(x))) for x, y in zip(pa, pb))
    except ValueError:
        return False


def _thousands(text: str, k: int) -> bool:
    grp = text[k:k + 3]
    more = k + 3 < len(text) and _is_digit_char(text[k + 3])
    return len(grp) == 3 and all(_is_digit_char(c) for c in grp) and not more


def _scan_number(text: str, i: int) -> Tuple[int, Optional[str]]:
    n = len(text)
    j = i + 3 if text.startswith("百分之", i) else i
    first = j
    while j < n:
        ch = text[j]
        if _is_numeral(ch):
            j += 1
            continue
        if first < j < n - 1 and _is_numeral(text[j - 1]) and _is_numeral(text[j + 1]):
            c = _nk1(ch)
            if ch == "点" or c == ".":
                j += 1
                continue
            if c == "/" and _is_digit_char(text[j - 1]) and _is_digit_char(text[j + 1]):
                j += 1
                continue
            if c == "," and _is_digit_char(text[j - 1]) and _thousands(text, j + 1):
                j += 1
                continue
        if (text.startswith("分之", j) and j > first and j + 2 < n and _is_numeral(text[j - 1])
                and _is_numeral(text[j + 2])):
            j += 2
            continue
        break
    if j == first:
        return i, None
    if j < n and _nk1(text[j]) == "%":
        j += 1
    return j, _number_value(text[i:j])


# ============================================================================ 切成可以比较的"字"
class Tok(NamedTuple):
    """key：统一写法后的内容（汉字一个字一个，英文一个词一个，数字整段是 "#"）；start/end：在原文里的位置。"""

    key: str
    start: int
    end: int
    val: Optional[str] = None  # 数字的标准写法


def tokenize(text: str) -> List[Tok]:
    """把文字切成可以比较的单位，位置始终指向原文（text[start:end]）。

    - 汉字：一个字一个（繁体转简体）；
    - 英文：一个词一个（小写、全角转半角，don't = dont），字母和数字分开（GPT4 = GPT 4）；
    - 数字（阿拉伯数字或中文数字，含 3.5 / 三点五 / 百分之五十 / 三分之一）：整段一个 "#"，标准写法放在 val；
    - + = × ÷ ≥ 这些符号按读法（加、等于……）；
    - 标点、空格、其它符号：去掉。
    """
    text = str(text or "")
    out: List[Tok] = []
    n, i = len(text), 0
    while i < n:
        ch = text[i]
        if _is_numeral(ch) or (text.startswith("百分之", i) and i + 3 < n and _is_numeral(text[i + 3])):
            j, val = _scan_number(text, i)
            if j > i:
                out.append(Tok("#", i, j, val))
                i = j
                continue
        if _latin_part(ch):
            j, parts = i, []
            while j < n:
                p = _latin_part(text[j])
                if p:
                    parts.append(p)
                    j += 1
                elif text[j] in "'’" and parts and j + 1 < n and _latin_part(text[j + 1]):
                    j += 1
                else:
                    break
            out.append(Tok("".join(parts), i, j))
            i = j
            continue
        c = _nk1(ch)
        if _CJK_RE.match(c):
            out.append(Tok(_simp_char(c), i, i + 1))
            i += 1
            continue
        reading = _SYMBOL_READINGS.get(c) or _SYMBOL_READINGS.get(ch)
        if reading:
            for k in reading:
                out.append(Tok(k, i, i + 1))
            i += 1
            continue
        if c.isalpha():  # 日文假名、韩文、希腊字母……：一个字一个
            out.append(Tok(c.lower(), i, i + 1))
        i += 1
    return out


def _keys(toks: Sequence[Tok]) -> List[str]:
    return [t.key for t in toks]


def merge_spans(spans: Any, text: Optional[str] = None) -> List[List[int]]:
    """整理位置：去掉无效的、排序、合并重叠或相邻的；给了 text 时限制在文字范围内，并把只隔着空格的合在一起。"""
    clean: List[Tuple[int, int]] = []
    limit = len(text) if text is not None else None
    for sp in spans or []:
        try:
            s, e = int(sp[0]), int(sp[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        if limit is not None:
            s, e = max(0, min(s, limit)), max(0, min(e, limit))
        else:
            s = max(0, s)
        if e > s:
            clean.append((s, e))
    out: List[List[int]] = []
    for s, e in sorted(clean):
        if out and (s <= out[-1][1] or (text is not None and not text[out[-1][1]:s].strip())):
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


# ============================================================================ 证据
@dataclass
class _Ev:
    start: int
    end: int
    reason: str
    weight: float
    kind: str = ""
    edit: Optional[Tuple[int, int, str]] = None  # 采用建议时怎么改原文：(start, end, 换成什么)
    splice: str = "no"  # yes：拼进建议；if_heur：只在规则也标了这个英文词时才拼；no：不拼
    show: bool = True


def _is_filler(s: str) -> bool:
    if not s or len(s) > 4:
        return False
    for w in FILLER_WORDS:
        s = s.replace(w, "")
    return all(c in FILLER_CHARS for c in s)


@lru_cache(maxsize=8192)
def _readings(ch: str) -> frozenset:
    """一个汉字所有可能的读音（带声调）；没装 pypinyin 时用同音字小表。"""
    try:
        from pypinyin import Style, pinyin  # type: ignore

        try:
            res = pinyin(ch, style=Style.TONE3, heteronym=True, neutral_tone_with_five=True)
        except TypeError:
            res = pinyin(ch, style=Style.TONE3, heteronym=True)
        vals = frozenset(x for x in (res[0] if res else []) if x and x != ch)
        if vals:
            return vals
    except Exception:
        pass
    return frozenset([_HOMO.get(ch, ch)])


def _same_sound(a: str, b: str) -> bool:
    if len(a) != len(b) or not a:
        return False
    return all(x == y or bool(_readings(x) & _readings(y)) for x, y in zip(a, b))


def _han_surface(toks: Sequence[Tok], text: str) -> Optional[str]:
    """这些字是不是全是汉字（含中文数字）；是的话返回简体原字，否则 None。"""
    out = []
    for t in toks:
        if t.key == "#":
            src = text[t.start:t.end]
            if not all(c in _CN_NUM for c in src):
                return None
            out.append(src)
        elif _CJK_RE.match(t.key) and t.end - t.start == 1 and _CJK_RE.match(_nk1(text[t.start])):
            out.append(t.key)
        else:
            return None
    return "".join(out)


def _classify(tag: str, at: Sequence[Tok], bt: Sequence[Tok], text: str, other: str, engine: str,
              w_diff: float, vocab: AbstractSet[str] = frozenset()) -> Tuple[str, float, str]:
    """一处不一样：返回 (类别, 权重, 能不能拼进建议 yes/if_heur/no)。权重 0 = 不算。

    vocab：这个声音的素材里本来就有的英文词（见 voice_vocab）。"""
    ak, bk = _keys(at), _keys(bt)
    aj, bj = "".join(ak), "".join(bk)
    if aj == bj:  # "VFIXED" 和 "v fixed"：只是空格或分词不同
        return "same", 0.0, "no"
    if ak and bk and all(k == "#" for k in ak + bk):
        va = [t.val for t in at]
        vb = [t.val for t in bt]
        if any(v is None for v in va + vb) or "".join(va) == "".join(vb):  # type: ignore[arg-type]
            return "same", 0.0, "no"
        return "number", W_NUMBER, "yes"
    if (not aj or _is_filler(aj)) and (not bj or _is_filler(bj)):
        return "filler", 0.0, "no"
    if tag in ("insert", "delete") and len(aj + bj) == 1 and (aj + bj) in PARTICLES:
        return "particle", W_PARTICLE, "no"
    whisper_b = engine in (ENGINE_WHISPER, ENGINE_WHISPER_WORDS)
    a_lat = bool(ak) and all(_latin_key(k) for k in ak)
    b_lat = bool(bk) and all(_latin_key(k) for k in bk)
    a_han = bool(ak) and all(_han_key(k) for k in ak)
    b_han = bool(bk) and all(_han_key(k) for k in bk)
    b_guess = b_lat and all(k in CONFUSABLE_EN or k in CONFUSABLE_SOFT for k in bk)
    if tag == "replace":
        if a_lat and b_han:
            if whisper_b:
                return "en_vs_cjk_w", 0.4, "no"
            return "en_vs_cjk", W_EN_VS_CJK, "if_heur"  # FunASR 拼不出英文：只当弱证据
        if a_han and b_lat:
            if whisper_b:
                return ("en_guess", W_EN_GUESS, "no") if b_guess else ("cjk_vs_en", W_LATIN, "yes")
            if _known_english(ak, bk, vocab):
                return "cjk_vs_en_known", W_LATIN, "yes"  # 艾子 ↔ as：老师说的英文被写成了读音相近的汉字
            return "cjk_vs_en_f", W_LATIN_WEAK, "no"
        if a_lat and b_lat:
            return ("latin", W_LATIN, "yes") if whisper_b else ("latin_f", W_LATIN_WEAK, "no")
        sa, sb = _han_surface(at, text), _han_surface(bt, other)
        if sa is not None and sb is not None and _same_sound(sa, sb):
            return "homophone", 0.0, "no"  # 他/她、的/得：读音一样，不影响训练
    elif tag == "insert" and b_lat:
        if whisper_b:
            return ("en_guess", W_EN_GUESS, "no") if b_guess else ("ins_en", W_LATIN, "yes")
        return "ins_en_f", W_LATIN_WEAK, "no"
    elif tag == "delete" and a_lat:
        return ("del_en", W_LATIN, "yes") if whisper_b else ("del_en_f", 0.4, "no")
    splice = "no" if (not whisper_b and any(_latin_key(k) for k in bk)) else "yes"
    return "diff", w_diff, splice


def _known_english(ak: Sequence[str], bk: Sequence[str], vocab: AbstractSet[str]) -> bool:
    """FunASR 听到的是英文、主识别写的是几个汉字：FunASR 的英文一般不可靠，但这几个英文词在老师自己的素材里
    （主识别引擎自己写出来过、或者老师改过的文字里）本来就常出现，而且汉字不多（像是英文的读音），就可以采用。"""
    if not vocab or not bk or len(bk) > 3:
        return False
    if not all(k in vocab and k not in CONFUSABLE_SOFT and len(k) >= 2 for k in bk):
        return False
    return 1 <= len(ak) <= 3 * len(bk)


@lru_cache(maxsize=1)
def _mother_vocab() -> FrozenSet[str]:
    """程序自带的老师母本（老师一句一句改好的讲课文字）里的英文词（小写）：都是老师真的说过的。"""
    try:
        from voicetwin.data.transcript_fix import builtin_mother

        words = set()
        for _rid, line in builtin_mother():
            words |= {k for k in _keys(tokenize(str(line or ""))) if _latin_key(k)}
        return frozenset(words)
    except Exception as exc:  # noqa: BLE001 - 读不了母本：只用素材里的词
        log.debug(f"读取母本里的英文词失败：{exc}")
        return frozenset()


def english_vocab(records: Iterable[Dict[str, Any]]) -> FrozenSet[str]:
    """老师常说的英文词：素材里出现在至少两段里的（voice_vocab）+ 程序自带的母本里的。"""
    return voice_vocab(records) | _mother_vocab()


def voice_vocab(records: Iterable[Dict[str, Any]], min_clips: int = 2) -> FrozenSet[str]:
    """这个声音的素材里出现在至少 min_clips 段里的英文词（小写）：主识别写出来的、老师改过的文字都算。"""
    counts: Dict[str, int] = {}
    for r in records:
        if r.get("deleted"):
            continue
        words = set()
        for t in (r.get("text"), r.get("orig_text")):
            words |= {k for k in _keys(tokenize(str(t or ""))) if _latin_key(k)}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
    return frozenset(w for w, c in counts.items() if c >= min_clips)


def _pad(text: str, s: int, e: int, rep: str) -> str:
    """把英文拼进中文/英文之间时补上必要的空格。"""
    if not rep:
        return rep
    before = text[s - 1:s]
    after = text[e:e + 1]
    if rep[:1].isascii() and rep[:1].isalnum() and before.isascii() and before.isalnum():
        rep = " " + rep
    if rep[-1:].isascii() and rep[-1:].isalnum() and after.isascii() and after.isalnum():
        rep = rep + " "
    return rep


def _insert_mark(toks: Sequence[Tok], i1: int) -> Tuple[int, int]:
    """另一个引擎多听到了字（这里可能漏了字）：标出缺字的位置两边的字（都是单个字时两个都标，否则标短的那个）。"""
    prev = toks[i1 - 1] if i1 > 0 else None
    nxt = toks[i1] if i1 < len(toks) else None
    if prev is not None and nxt is not None:
        if prev.end - prev.start == 1 and nxt.end - nxt.start == 1:
            return prev.start, nxt.end
        pick = prev if (prev.end - prev.start) <= (nxt.end - nxt.start) else nxt
        return pick.start, pick.end
    one = prev if prev is not None else nxt
    return (one.start, one.end) if one is not None else (0, 0)


def _partial_symbol(toks: Sequence[Tok], i1: int, i2: int) -> bool:
    """这一处只对上了某个符号读法的一部分（"≥" = 大于等于）：不拼进建议，免得把符号整个删掉。"""
    if i1 >= i2:
        return False
    first, last = toks[i1], toks[i2 - 1]
    before = i1 > 0 and (toks[i1 - 1].start, toks[i1 - 1].end) == (first.start, first.end)
    after = i2 < len(toks) and (toks[i2].start, toks[i2].end) == (last.start, last.end)
    return before or after


def _clean_other(other: str) -> str:
    """第二次识别结果：转简体、统一标点、去掉 paraformer 在汉字之间加的空格。"""
    return clean_transcript(_simp_text(str(other or "")))


def _with_final_punct(alt: str, text: str) -> str:
    t = text.rstrip()
    if not alt or not t or alt[-1:] in "。！？!?.，,；;…":
        return alt
    if t[-1] in "。！？!?.…":
        return alt + ("。" if count_cjk(alt) else ".")
    return alt


class Compared(NamedTuple):
    evidence: List[_Ev]
    total: bool  # 整句对不上
    total_alt: str  # 整句对不上时的建议（第二次识别的整句；只听清一小部分时为 ""）
    ratio: float
    other: str  # 清理后的第二次识别结果


def compare(text: str, other: str, engine: str = ENGINE_FUNASR, srt: bool = False,
            vocab: AbstractSet[str] = frozenset()) -> Compared:
    """把现在的文字（A）和第二个引擎的结果（B）逐字对比，返回证据。engine 是 B 来自哪个引擎。"""
    text = str(text or "")
    b = _clean_other(other)
    A, B = tokenize(text), tokenize(b)
    if not A:
        return Compared([], False, "", 1.0, b)
    if not B:
        if len(A) >= 4:
            ev = _Ev(A[0].start, A[-1].end, "另一个识别引擎几乎没听到说话，这段的文字可能和录音对不上", W_SILENT, "silent")
            return Compared([ev], True, "", 0.0, b)
        return Compared([], False, "", 0.0, b)
    w_diff = W_DIFF_SRT if srt else W_DIFF
    sm = difflib.SequenceMatcher(None, _keys(A), _keys(B), autojunk=False)
    evidence: List[_Ev] = []
    matched = 0.0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            matched += i2 - i1
            for k in range(i2 - i1):
                ta, tb = A[i1 + k], B[j1 + k]
                if ta.key == "#" and not _num_equal(ta.val, tb.val):
                    bo = b[tb.start:tb.end]
                    evidence.append(_Ev(ta.start, ta.end, f"数字可能不对：另一个识别引擎听到的是「{_short(bo)}」",
                                        W_NUMBER if not srt else w_diff, "number",
                                        (ta.start, ta.end, _pad(text, ta.start, ta.end, bo)), "yes"))
            continue
        at, bt = A[i1:i2], B[j1:j2]
        kind, weight, splice = _classify(tag, at, bt, text, b, engine, w_diff, vocab)
        size = j2 - j1
        if tag == "insert" and weight > 0 and (_keys(A[max(0, i1 - size):i1]) == _keys(bt)
                                              or _keys(A[i1:i1 + size]) == _keys(bt)):
            kind, weight, splice = "stutter", W_STUTTER, "no"  # "我们我们来看"：口误重复，不算错字
        if weight <= 0:
            matched += (len(at) + len(bt)) / 2.0
            continue
        if (weight < SHOW_MIN or kind in _WEAK_KINDS) and max(len(at), len(bt)) <= 6:
            matched += (len(at) + len(bt)) / 2.0  # 不可靠的那一边（FunASR 的英文、Whisper 的 the）：不算"整句对不上"
        if tag == "delete" and A[i2:i2 + (i2 - i1)] and _keys(A[i2:i2 + (i2 - i1)]) == _keys(at):
            i1, i2 = i2, i2 + (i2 - i1)  # 多出来的是紧跟着的重复："我们来看一下我们来看一下" 标第二遍
            at = A[i1:i2]
        a_orig = text[at[0].start:at[-1].end] if at else ""
        b_orig = b[bt[0].start:bt[-1].end] if bt else ""
        if tag == "insert":
            s, e = _insert_mark(A, i1)
            pos = A[i1 - 1].end if i1 > 0 else A[0].start
            edit = (pos, pos, _pad(text, pos, pos, b_orig))
            if kind == "stutter":
                reason = f"另一个识别引擎听到「{_short(b_orig)}」说了两遍（可能是口误重复）"
            else:
                reason = f"这里可能漏了「{_short(b_orig)}」（另一个识别引擎听到了）"
        elif tag == "delete":
            s, e = at[0].start, at[-1].end
            edit = (s, e, "")
            reason = f"另一个识别引擎没听到「{_short(a_orig)}」"
        else:
            s, e = at[0].start, at[-1].end
            edit = (s, e, _pad(text, s, e, b_orig))
            reason = f"另一个识别引擎听到的是「{_short(b_orig)}」"
        if _partial_symbol(A, i1, i2):
            splice = "no"
        evidence.append(_Ev(s, e, reason, weight, kind, edit, splice, weight >= SHOW_MIN))
    ratio = 2.0 * matched / float(len(A) + len(B))
    if ratio < 0.5:
        enough = len(B) >= 0.5 * len(A)
        alt = clean_transcript(_with_final_punct(b, text)) if enough else ""
        reason = ("两次识别的结果差别很大，整句可能都不对" if enough
                  else "另一个识别引擎只听清了一小部分，这段的文字可能和录音对不上")
        ev = _Ev(A[0].start, A[-1].end, reason, W_TOTAL if not srt else W_DIFF, "total")
        return Compared([ev], True, alt, ratio, b)
    return Compared(evidence, False, "", ratio, b)


def heuristics(text: str, known_terms: Iterable[str] = (), frequent: Iterable[str] = (), lang: str = "",
               vocab: AbstractSet[str] = frozenset()) -> List[_Ev]:
    """只看文字本身的规则检查（不需要模型）。

    vocab：老师本来就常说的英文词（小写；见 english_vocab）：whose、why、he、way……不再当成「把中文听成了英文」
    （老师教英语语法，这些词到处都是；以前在老师自己改好的 1005 句里标红了 50 句，还建议换成「户字」「外」「喜」）。"""
    text = str(text or "")
    ev: List[_Ev] = []
    if not text.strip():
        return ev
    norm = _norm_same_len(text)  # 全角字母 → 半角，位置不变
    cjk = count_cjk(norm)
    zh = cjk >= 3 or (cjk >= 1 and lang == "zh")
    known = {str(k).upper() for k in known_terms if k}
    freq = {str(k).upper() for k in frequent if k}
    if zh:
        for m in _LATIN_WORD.finditer(norm):
            w, s, e = m.group(0), m.start(), m.end()
            up = w.upper()
            if up in ACRONYMS or up in known or _ROMAN.match(up):
                continue
            if norm[s - 1:s].isdigit() or re.match(r"[-_]?\d", norm[e:e + 2]):
                continue  # RTX4090、GPT-4o：型号，不管
            if len(w) == 1 and w.isupper():
                continue  # A 选项、X 轴、B 点
            if w.isupper() and len(w) >= 3:
                w_ = W_CAPS_FREQ if up in freq else W_CAPS
                ev.append(_Ev(s, e, f"「{_short(w)}」像是听错的英文（不是常见的缩写）", w_, "caps"))
                continue
            low = w.lower()
            if (low in CONFUSABLE_EN or low in CONFUSABLE_SOFT) and low not in vocab:
                left = norm[:s].rstrip()[-1:]
                right = norm[e:].lstrip()[:1]
                lat_l = bool(left) and (left.isascii() and left.isalnum())
                lat_r = bool(right) and (right.isascii() and right.isalnum())
                if not lat_l and not lat_r and (_CJK_RE.match(left or " ") or _CJK_RE.match(right or " ")):
                    w_ = W_CONFUSABLE if low in CONFUSABLE_EN else W_CONFUSABLE_SOFT
                    ev.append(_Ev(s, e, f"中文里夹着「{w}」，可能是把中文听成了英文", w_, "confusable"))
                    continue
            if re.search(r"[a-z][A-Z].*[a-z][A-Z]", w) or len(w) > 15 or (
                    len(w) >= 4 and not re.search(r"[aeiouyAEIOUY]", w)):
                ev.append(_Ev(s, e, f"「{_short(w)}」像是乱码", W_GARBAGE, "garbage"))
    for m in _FOREIGN.finditer(norm):
        ev.append(_Ev(m.start(), m.end(), f"出现了不该有的外文字符「{_short(m.group(0), 6)}」", W_SCRIPT, "script"))
    ev.extend(_repeats(text))
    return ev


def _repeats(text: str) -> List[_Ev]:
    """同一个字 / 词 / 短语连着重复（"我们来看一下我们来看一下"）。标的是重复出来的那几遍，不是第一遍。"""
    toks = tokenize(text)
    keys = _keys(toks)
    # 比较是不是同样的几个字时，数字要看值（「第一种情况第二种情况」「三月三号三月四号」不是重复）；
    # 下面判断够不够标红照旧用 keys（数字都是 "#"）
    same = [k if k != "#" else "#" + str(t.val if t.val is not None else text[t.start:t.end])
            for k, t in zip(keys, toks)]
    out: List[_Ev] = []
    i, n = 0, len(keys)
    while i < n:
        hit = False
        for size in range(1, 9):
            if i + 2 * size > n:
                break
            unit = keys[i:i + size]
            cmp = same[i:i + size]
            k = 1
            while same[i + k * size:i + (k + 1) * size] == cmp:
                k += 1
            if k < 2:
                continue
            u = "".join(unit)
            if size == 1:
                strong = k >= 3 and u != "#" and not (u in TRIPLE_OK and k <= 4) and not _is_filler(u)
            elif size <= 3:
                strong = k >= 3 and "#" not in unit
            else:
                strong = True
            if not strong:
                continue
            s, e = toks[i + size].start, toks[i + k * size - 1].end
            first = text[toks[i].start:toks[i + size - 1].end]
            if size >= 4:
                gap = text[toks[i + size - 1].end:toks[i + size].start]
                weight = W_REPEAT_PUNCT if (gap.strip() and k == 2) else W_REPEAT_LONG
            else:
                weight = W_REPEAT
            out.append(_Ev(s, e, f"「{_short(first)}」连着重复了 {k} 遍", weight, "repeat"))
            i += k * size
            hit = True
            break
        if not hit:
            i += 1
    return out


def _words_list(words: Any) -> List[Tuple[str, float]]:
    """faster-whisper 的 Word 对象 / dict / (词, 概率) 统一成 [(词, 概率)]。"""
    out: List[Tuple[str, float]] = []
    for w in words or []:
        try:
            if isinstance(w, dict):
                word, p = w.get("word", ""), w.get("probability", 1.0)
            elif isinstance(w, (list, tuple)):
                word, p = w[0], w[1]
            else:
                word, p = getattr(w, "word", ""), getattr(w, "probability", 1.0)
            out.append((str(word or ""), float(p if p is not None else 1.0)))
        except (TypeError, ValueError, IndexError):
            continue
    return out


def low_prob_spans(text: str, words: Any, thr: float = LOW_PROB) -> List[Tuple[int, int, float]]:
    """把 faster-whisper 把握不大的词对到 record["text"] 上，返回 [(start, end, 最低概率)]。

    按"字"对齐（不是按位置），所以繁简体、空格、标点不一样也对得上；对不上的地方（文字本来就不同）丢掉。
    zh 模式下英文会被拆成几块（" V"、"FIX"、"ED"），合并成一处，取最低的概率。
    """
    text = str(text or "")
    items = _words_list(words)
    if not items or not text:
        return []
    raw, ranges, pos = [], [], 0
    for word, p in items:
        raw.append(word)
        ranges.append((pos, pos + len(word), p))
        pos += len(word)
    joined = "".join(raw)
    wt, tt = tokenize(joined), tokenize(text)
    if not wt or not tt:
        return []
    sm = difflib.SequenceMatcher(None, _keys(wt), _keys(tt), autojunk=False)
    w2t: Dict[int, int] = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w2t[blk.a + k] = blk.b + k
    found: List[Tuple[int, int, float]] = []
    for s, e, p in ranges:
        if p >= thr:
            continue
        idx = [i for i, t in enumerate(wt) if t.start < e and t.end > s]
        if not idx or all(_is_filler(wt[i].key) or wt[i].key in PARTICLES for i in idx):
            continue
        mapped = [w2t[i] for i in idx if i in w2t]
        if not mapped:
            continue
        found.append((tt[min(mapped)].start, tt[max(mapped)].end, p))
    merged: List[List[Any]] = []
    for s, e, p in sorted(found):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
            merged[-1][2] = min(merged[-1][2], p)
        else:
            merged.append([s, e, p])
    return [(int(s), int(e), float(p)) for s, e, p in merged]


def _apply_edits(text: str, edits: Sequence[Tuple[int, int, str]]) -> str:
    """从后往前改（前面的位置不会变）；重叠的改动只取后面那个。改完和原文读起来一样时返回 ""。"""
    out = text
    applied_from = len(text)  # 已经改过的最左边位置
    for s, e, rep in sorted(set(edits), key=lambda x: (x[0], x[1]), reverse=True):
        if not (0 <= s <= e <= len(text)) or e > applied_from:
            continue
        out = out[:s] + rep + out[e:]
        applied_from = s
    out = clean_transcript(out)
    if not out or out == text or out == clean_transcript(text):
        return ""
    a, b = tokenize(text), tokenize(out)
    if _keys(a) == _keys(b) and all(_num_equal(x.val, y.val) for x, y in zip(a, b)):
        return ""
    return out


def _overlaps(a: _Ev, b: _Ev) -> bool:
    return a.start < b.end and b.start < a.end


def _reasons(evs: Sequence[_Ev]) -> List[str]:
    order = sorted(evs, key=lambda x: (0 if x.kind in ("total", "silent") else 1, x.start, -x.weight))
    out: List[str] = []
    for x in order:
        if x.reason and x.reason not in out:
            out.append(x.reason)
    if len(out) > MAX_REASONS:
        rest = len(out) - (MAX_REASONS - 1)
        out = out[:MAX_REASONS - 1] + [f"……还有 {rest} 处"]
    return out


def build_suspect(text: str, other: Optional[str] = None, words: Any = None, *, engine: str = "",
                  known_terms: Iterable[str] = (), frequent: Iterable[str] = (), lang: str = "",
                  srt: bool = False, avg_logprob: Optional[float] = None,
                  vocab: AbstractSet[str] = frozenset()) -> Optional[Dict[str, Any]]:
    """把所有证据合起来，返回 record["suspect"]（没问题时返回 None）。

    other：第二个引擎听到的文字（None = 没有第二个引擎 / 这段没用它；"" = 它什么都没听到）。
    words：faster-whisper 的逐词结果（含 probability），可以为空。
    """
    text = str(text or "")
    if not text.strip():
        return None
    heur = heuristics(text, known_terms, frequent, lang, vocab=vocab)
    ev: List[_Ev] = list(heur)
    total_alt: Optional[str] = None
    if other is not None and engine != ENGINE_WHISPER_WORDS:
        cmp = compare(text, other, engine=engine or ENGINE_FUNASR, srt=srt, vocab=vocab)
        ev.extend(cmp.evidence)
        if cmp.total:
            total_alt = cmp.total_alt
    if words:
        for s, e, p in low_prob_spans(text, words):
            ev.append(_Ev(s, e, f"「{_short(text[s:e])}」识别时把握不大（{int(round(p * 100))}%）",
                          W_LOWP if p < VERY_LOW_PROB else W_LOWP_WEAK, "lowprob"))
    if not ev:
        return None
    weights = [x.weight for x in ev]
    if avg_logprob is not None:
        try:
            if float(avg_logprob) < -0.6:
                weights.append(W_LOGPROB)
        except (TypeError, ValueError):
            pass
    keep = 1.0
    for w in weights:
        keep *= (1.0 - max(0.0, min(1.0, w)))
    score = 1.0 - keep
    if score < FLAG_THRESHOLD - 1e-9:
        return None
    shown = [x for x in ev if x.show and x.weight >= SHOW_MIN] or ev
    spans = merge_spans([[x.start, x.end] for x in shown], text)
    if not spans:
        return None
    if total_alt is not None:
        alt = total_alt if total_alt != text else ""
    else:
        latin_heur = [h for h in heur if h.kind in _LATIN_HEUR]
        edits = [x.edit for x in ev if x.edit is not None and (
            x.splice == "yes" or (x.splice == "if_heur" and any(_overlaps(x, h) for h in latin_heur)))]
        alt = _apply_edits(text, edits) if edits else ""
    return {"spans": spans, "alt": alt, "reasons": _reasons(shown), "score": round(score, 3)}


# ============================================================================ 显示
def _esc(s: str) -> str:
    """HTML 转义 + 把 Markdown 符号换成数字实体：放进 gradio 的 markdown 列、gr.HTML、gr.Markdown 都只显示原样文字。"""
    out = []
    for ch in str(s or ""):
        if ch in _MD_CHARS:
            out.append("&#%d;" % ord(ch))
        elif ch in "&\"'":
            out.append(html.escape(ch, quote=True))
        elif ch in "\r\n\t":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def render_marked(text: Any, spans: Any) -> str:
    """把可疑的字标红：返回转义过的文字，可疑的地方包在 RED_SPAN 里（校对表的「可能有错（红色）」列）。"""
    text = str(text or "")
    out, pos = [], 0
    for s, e in merge_spans(spans, text):
        out.append(_esc(text[pos:s]))
        out.append(RED_SPAN + _esc(text[s:e]) + "</span>")
        pos = e
    out.append(_esc(text[pos:]))
    return "".join(out)


def render_plain(text: Any, spans: Any) -> str:
    """不能显示颜色的地方用：可疑的字放在【】里。"""
    text = str(text or "")
    out, pos = [], 0
    for s, e in merge_spans(spans, text):
        out += [text[pos:s], "【", text[s:e], "】"]
        pos = e
    out.append(text[pos:])
    return "".join(out)


def _diff_ranges(text: str, alt: str) -> Tuple[List[List[int]], List[List[int]]]:
    """两段文字真正不一样的地方（按"字"比较，标点、空格、全角半角、繁简体、数字写法不同不算）。"""
    A, B = tokenize(text), tokenize(alt)
    sm = difflib.SequenceMatcher(None, _keys(A), _keys(B), autojunk=False)
    ra: List[List[int]] = []
    rb: List[List[int]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                ta, tb = A[i1 + k], B[j1 + k]
                if ta.key == "#" and not _num_equal(ta.val, tb.val):
                    ra.append([ta.start, ta.end])
                    rb.append([tb.start, tb.end])
            continue
        if "".join(_keys(A[i1:i2])) == "".join(_keys(B[j1:j2])):
            continue
        if i2 > i1:
            ra.append([A[i1].start, A[i2 - 1].end])
        if j2 > j1:
            rb.append([B[j1].start, B[j2 - 1].end])
    return ra, rb


def _wrap(text: str, ranges: Sequence[Sequence[int]], open_tag: str) -> str:
    out, pos = [], 0
    for s, e in merge_spans(ranges, text):
        out += [_esc(text[pos:s]), open_tag, _esc(text[s:e]), "</span>"]
        pos = e
    out.append(_esc(text[pos:]))
    return "".join(out)


def render_diff_html(text: Any, alt: Any, spans: Any = None, label_b: str = "") -> str:
    """详情面板：两行对比。「识别 A」是现在的文字（不一样的字标红），「识别 B」是另一次识别的建议（标绿）。

    alt 为空（没有建议）时，第一行按 spans 标红（可以不给），第二行写"没有建议"。全部内容都已转义。
    label_b：建议不是来自识别引擎时（文字校正：「按逐字稿改成」），两行改成「现在的文字」「label_b」。
    """
    text, alt = str(text or ""), str(alt or "")
    if label_b:
        tag_a = '<span class="vt-diff-tag">现在的文字：</span>'
        tag_b = f'<span class="vt-diff-tag">{_esc(label_b)}：</span>'
        tag_none = f'<span class="vt-diff-tag">{_esc(label_b)}：</span>'
    else:
        tag_a = '<span class="vt-diff-tag">识别 A（现在的文字）：</span>'
        tag_b = '<span class="vt-diff-tag">识别 B（建议改成）：</span>'
        tag_none = '<span class="vt-diff-tag">识别 B：</span>'
    if not alt.strip():
        return (f'<div class="vt-diff-row">{tag_a}{_wrap(text, spans or [], RED_SPAN)}</div>'
                f'<div class="vt-diff-row vt-diff-reason">{tag_none}'
                '（没有建议。请听一听录音，有错就直接在「文字」列里改）</div>')
    ra, rb = _diff_ranges(text, alt)
    return (f'<div class="vt-diff-row">{tag_a}{_wrap(text, ra, RED_SPAN)}</div>'
            f'<div class="vt-diff-row">{tag_b}{_wrap(alt, rb, GREEN_SPAN)}</div>')


# ============================================================================ 识别引擎（用到时才加载）
def _funasr_installed() -> bool:
    return _has("funasr") and _has("modelscope") and _has("torch")


def _whisper_installed() -> bool:
    return _has("faster_whisper")


def _engine_chain(cfg: Any) -> List[str]:
    """按顺序要试的引擎（第一个加载失败就换下一个，都不行就只用规则）。"""
    primary = str(_cfg_get(cfg, "prepare.asr.engine", ENGINE_WHISPER) or ENGINE_WHISPER).strip().lower()
    force = str(_cfg_get(cfg, "prepare.proofcheck_engine", "auto") or "auto").strip().lower()
    fun, fw = _funasr_installed(), _whisper_installed()
    whisper_name = ENGINE_WHISPER_WORDS if primary == ENGINE_WHISPER else ENGINE_WHISPER
    if force in ("rules", "none", "off", "false", "规则"):
        return []
    if force == ENGINE_FUNASR:
        return [ENGINE_FUNASR] if fun else []
    if force in (ENGINE_WHISPER, "whisper", ENGINE_WHISPER_WORDS):
        return [whisper_name] if fw else []
    chain: List[str] = []
    if primary == ENGINE_FUNASR:
        if fw:
            chain.append(ENGINE_WHISPER)
    else:
        if fun:
            chain.append(ENGINE_FUNASR)
        if fw:
            chain.append(whisper_name)
    return chain


def _reason_for(engine: str, cfg: Any) -> str:
    primary = str(_cfg_get(cfg, "prepare.asr.engine", ENGINE_WHISPER) or ENGINE_WHISPER).strip().lower()
    if engine == ENGINE_FUNASR:
        return REASON_FUNASR
    if engine == ENGINE_WHISPER:
        return REASON_WHISPER_SUBS if primary in ("none", "") else REASON_WHISPER
    if engine == ENGINE_WHISPER_WORDS:
        return REASON_WORDS
    return REASON_NONE


def available_checker(cfg: Any) -> Tuple[str, str]:
    """用哪个引擎查错字：(引擎名, 中文说明)。引擎名是 'funasr' / 'faster-whisper' / 'faster-whisper-words'，
    没有可用引擎（只用规则检查）时是 ''。只检查装没装，不加载模型，很快。

    优先用和主识别引擎（prepare.asr.engine）不同的第二个引擎：主识别 faster-whisper → FunASR（中文片段）；
    主识别 FunASR → faster-whisper。没有第二个引擎时，用 faster-whisper 重新听一遍取逐字把握程度，再不行就只用规则。
    """
    try:
        chain = _engine_chain(cfg)
    except Exception as exc:  # noqa: BLE001 - 这里绝不能出错
        log.debug(f"检查识别引擎时出错：{exc}")
        chain = []
    engine = chain[0] if chain else ""
    return engine, _reason_for(engine, cfg)


def _device(cfg: Any) -> str:
    dev = str(_cfg_get(cfg, "prepare.asr.device", "auto") or "auto")
    try:
        from voicetwin.data.asr import _auto_device

        return _auto_device(dev)
    except Exception:
        return "cpu" if dev == "auto" else dev


def _gsv_root(cfg: Any) -> Optional[Path]:
    root = _cfg_get(cfg, "backends.gptsovits.root", "")
    if not root:
        return None
    p = Path(os.path.expanduser(str(root)))
    if not p.is_absolute():
        p = Path(str(_cfg_get(cfg, "_base_dir", ".") or ".")) / p
    return p


def _model_dir_ok(p: Path) -> bool:
    try:
        return (p / "configuration.json").exists() or ((p / "config.yaml").exists() and (p / "model.pt").exists())
    except OSError:
        return False


def paraformer_path(cfg: Any) -> str:
    """优先用本地已有的 paraformer（GPT-SoVITS 整合包自带的、ModelScope 缓存里的），都没有才用模型名（要联网下载）。"""
    cands: List[Path] = []
    root = _gsv_root(cfg)
    if root is not None:
        cands.append(root / PARAFORMER_LOCAL)
    ms = os.environ.get("MODELSCOPE_CACHE") or str(Path.home() / ".cache" / "modelscope" / "hub")
    for mid in (SEACO_ID, PARAFORMER_ID):
        cands += [Path(ms) / mid, Path(ms) / "models" / mid]
    for c in cands:
        if _model_dir_ok(c):
            return str(c)
    return "paraformer-zh"


def _free_gpu_memory() -> None:
    gc.collect()
    torch = sys.modules.get("torch")  # 没导入过就不导入
    if torch is not None:
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


class _FunASRChecker:
    """FunASR paraformer：不加 VAD 和标点模型（片段只有 2~12 秒，标点比较前也会去掉）。只听中文片段。"""

    name = ENGINE_FUNASR
    label = "FunASR 中文识别模型"
    diff = True

    def __init__(self, cfg: Any):
        self.cfg = cfg
        self.path = paraformer_path(cfg)
        self.model_id = self.path
        self.model: Any = None

    def applies(self, rec: Dict[str, Any]) -> bool:
        lang = str(rec.get("lang") or "")
        return lang == "zh" or (lang != "en" and count_cjk(str(rec.get("text") or "")) > 0)

    def load(self) -> None:
        from funasr import AutoModel  # 很慢（会导入所有子模块），所以只在这里导入

        device = _device(self.cfg)
        kwargs: Dict[str, Any] = {"model": self.path, "device": "cuda:0" if device == "cuda" else "cpu",
                                  "disable_update": True, "disable_pbar": True, "disable_log": True,
                                  "check_latest": False, "log_level": "ERROR"}
        if not os.path.isdir(self.path):
            kwargs["model_revision"] = "v2.0.4"  # 和 GPT-SoVITS 整合包用的版本一致
            log.info("查错字：本地没有 FunASR 模型，第一次使用会从 ModelScope 下载（大约 1 GB）……")
        threads = None
        try:
            import torch  # funasr 本来就要用；先记下线程数

            threads = int(torch.get_num_threads())
        except Exception:
            torch = None  # type: ignore[assignment]
        try:
            self.model = AutoModel(**kwargs)
        finally:
            if threads and torch is not None:  # AutoModel 会把整个程序的线程数改成 4，改回来
                try:
                    torch.set_num_threads(threads)
                except Exception:
                    pass
        log.info(f"查错字：已加载 FunASR（{device}）{self.path}")

    def recognize(self, wav16k: Any, lang: str) -> Tuple[str, Optional[List[Tuple[str, float]]]]:
        res = self.model.generate(input=wav16k)  # 一次一段；没听到声音时返回 []
        item = res[0] if isinstance(res, (list, tuple)) and res else {}
        text = item.get("text", "") if isinstance(item, dict) else ""
        return str(text or ""), None

    def close(self) -> None:
        self.model = None
        _free_gpu_memory()


def _whisper_model_name(name: Any) -> str:
    name = str(name or "").strip()
    low = name.lower()
    if not name or "paraformer" in low or "sensevoice" in low or "funasr" in low or low.startswith("iic/"):
        return "large-v3"
    return name


class _WhisperChecker:
    """faster-whisper：再听一遍，并取每个词的把握程度（word_timestamps=True → words[i].probability）。"""

    label = "faster-whisper 识别模型"

    def __init__(self, cfg: Any, words_only: bool = False):
        self.cfg = cfg
        self.name = ENGINE_WHISPER_WORDS if words_only else ENGINE_WHISPER
        self.diff = not words_only
        acfg = dict(_cfg_get(cfg, "prepare.asr", {}) or {})
        acfg["engine"] = ENGINE_WHISPER
        acfg["model"] = _whisper_model_name(acfg.get("model"))
        self.acfg = acfg
        self.model_id = acfg["model"]
        self.tr: Any = None

    def applies(self, rec: Dict[str, Any]) -> bool:
        return True

    def load(self) -> None:
        from voicetwin.data.asr import Transcriber

        tr = Transcriber(self.acfg)
        tr._load()
        self.tr = tr

    def recognize(self, wav16k: Any, lang: str) -> Tuple[str, Optional[List[Tuple[str, float]]]]:
        tr, acfg = self.tr, self.acfg
        if lang not in ("zh", "en"):
            try:
                lang = tr._detect_lang(wav16k)
            except Exception:
                lang = "zh"
        segments, _info = tr._model.transcribe(
            wav16k, language=lang, beam_size=int(acfg.get("beam_size", 5) or 5),
            initial_prompt=acfg.get("initial_prompt_zh") if lang == "zh" else None,
            condition_on_previous_text=False, vad_filter=False, temperature=0.0, word_timestamps=True)
        texts: List[str] = []
        words: List[Tuple[str, float]] = []
        for seg in segments:  # 生成器：真正的识别在这里
            texts.append(str(getattr(seg, "text", "") or ""))
            for w in (getattr(seg, "words", None) or []):
                try:
                    words.append((str(w.word), float(w.probability)))
                except Exception:
                    continue
        text = "".join(texts) if lang == "zh" else " ".join(t.strip() for t in texts)
        return text, words

    def close(self) -> None:
        self.tr = None
        _free_gpu_memory()


def _make_checker(name: str, cfg: Any) -> Any:
    """测试里会替换它（不需要真的模型）。"""
    if name == ENGINE_FUNASR:
        return _FunASRChecker(cfg)
    if name == ENGINE_WHISPER:
        return _WhisperChecker(cfg, words_only=False)
    if name == ENGINE_WHISPER_WORDS:
        return _WhisperChecker(cfg, words_only=True)
    raise ValueError(f"未知的查错字引擎：{name}")


def _load_wav16(project: Any, rec: Dict[str, Any]) -> Any:
    from voicetwin.utils.audio import load_audio

    wav, _sr = load_audio(project.abspath(rec["path"]), sr=16000)
    return wav


class _RecogCache:
    """识别结果只和录音有关（和文字无关）：存下来，改了字再查一遍时不用重新识别。"""

    def __init__(self, project: Any, engine: str, model_id: str):
        self.project = project
        self.engine = engine
        self.model_id = str(model_id or "")
        self.items: Dict[str, Any] = {}
        self.dirty = False
        self.path: Optional[Path] = None
        try:
            self.path = Path(project.cache_dir) / f"proofcheck_{re.sub(r'[^A-Za-z0-9_-]+', '_', engine)}.json"
            if self.path.exists():
                import json

                data = json.loads(self.path.read_text(encoding="utf-8"))
                same = isinstance(data, dict) and data.get("version") == CACHE_VERSION
                if same and data.get("model") == self.model_id:
                    items = data.get("items")
                    self.items = items if isinstance(items, dict) else {}
        except Exception as exc:  # noqa: BLE001
            log.debug(f"读取查错字缓存失败（已忽略）：{exc}")
            self.items = {}

    def _key(self, rec: Dict[str, Any]) -> Optional[str]:
        try:
            st = Path(self.project.abspath(rec["path"])).stat()
            return f"{rec['path']}|{st.st_size}|{int(st.st_mtime)}|{rec.get('lang') or ''}"
        except Exception:
            return None

    def get(self, rec: Dict[str, Any]) -> Optional[Tuple[str, Optional[List[Tuple[str, float]]]]]:
        item = self.items.get(str(rec.get("id")))
        key = self._key(rec)
        if not isinstance(item, dict) or key is None or item.get("key") != key:
            return None
        words = item.get("words")
        return str(item.get("text") or ""), (_words_list(words) if words is not None else None)

    def put(self, rec: Dict[str, Any], text: str, words: Optional[List[Tuple[str, float]]]) -> None:
        key = self._key(rec)
        if key is None:
            return
        self.items[str(rec.get("id"))] = {"key": key, "text": text,
                                          "words": [[w, round(p, 4)] for w, p in words] if words is not None else None}
        self.dirty = True

    def save(self) -> None:
        if not self.dirty or self.path is None:
            return
        try:
            self.project.write_json(self.path, {"version": CACHE_VERSION, "engine": self.engine,
                                                "model": self.model_id, "items": self.items})
            self.dirty = False
        except Exception as exc:  # noqa: BLE001
            log.debug(f"保存查错字缓存失败（已忽略）：{exc}")


class _EngineRunner:
    """管理"当前用哪个引擎"：用到时才加载；加载失败或一直出错就换下一个，最后退回到只用规则。"""

    def __init__(self, project: Any, cfg: Any, chain: Sequence[str], progress: Optional[ProgressFn]):
        self.project, self.cfg, self.progress = project, cfg, progress
        self.pending = list(chain)
        self.ck: Any = None
        self.loaded = False
        self.ok = 0
        self.fails = 0
        self.notes: List[str] = []
        self.caches: Dict[str, _RecogCache] = {}
        self.frac = 0.0

    def _candidate(self) -> Any:
        while self.ck is None and self.pending:
            name = self.pending.pop(0)
            try:
                self.ck = _make_checker(name, self.cfg)
            except Exception as exc:  # noqa: BLE001
                self.notes.append(f"{ENGINE_LABELS.get(name, name)}用不了（{_why(exc)}）")
                log.warning(f"查错字：{self.notes[-1]}", exc_info=exc)  # 原始报错只进 voicetwin.log
                continue
            self.loaded, self.ok, self.fails = False, 0, 0
        return self.ck

    def _drop(self, why: str, exc: Optional[BaseException] = None) -> None:
        ck = self.ck
        self.ck = None
        nxt = ENGINE_LABELS.get(self.pending[0], self.pending[0]) if self.pending else "规则检查"
        sep = " " if nxt[:1].isascii() else ""
        note = f"{getattr(ck, 'label', '识别引擎')} 没能用上（{why}），改用{sep}{nxt}"
        self.notes.append(note)
        log.warning(f"⚠️ 查错字：{note}", exc_info=exc)  # 原始报错（英文 Traceback）只进黑色窗口和 voicetwin.log
        try:
            ck.close()
        except Exception:
            pass

    def cache(self, ck: Any) -> _RecogCache:
        c = self.caches.get(ck.name)
        if c is None:
            c = self.caches[ck.name] = _RecogCache(self.project, ck.name, str(getattr(ck, "model_id", "")))
        return c

    def recognize(self, rec: Dict[str, Any], lang: str) -> Tuple[Optional[str], Any, str]:
        """返回 (用来对比的第二次识别文字或 None, 逐词结果或 None, 实际用的引擎名或 "")。"""
        while True:
            ck = self._candidate()
            if ck is None or not ck.applies(rec):
                return None, None, ""
            cache = self.cache(ck)
            hit = cache.get(rec)
            if hit is not None:
                return (hit[0] if ck.diff else None), hit[1], ck.name
            if not self.loaded:
                sep = " " if str(ck.label)[:1].isascii() else ""
                _report(self.progress, self.frac, f"正在加载{sep}{ck.label}（第一次使用可能要先下载模型，请稍等）……")
                try:
                    ck.load()
                    self.loaded = True
                except Exception as exc:  # noqa: BLE001 - 换下一种方法；停止按钮照常传出去
                    self._drop(_why(exc), exc)
                    continue
            wav = _load_wav16(self.project, rec)  # 录音读不出来：只是这一段的问题，不怪引擎
            try:
                other, words = ck.recognize(wav, lang)
            except Exception as exc:  # noqa: BLE001
                self.fails += 1
                if (self.ok == 0 and self.fails >= MAX_LOAD_FAILS_BEFORE_OK) or self.fails >= MAX_CONSECUTIVE_FAILS:
                    self._drop(_why(exc), exc)
                    continue
                raise
            self.ok += 1
            self.fails = 0
            other = str(other or "")
            words = _words_list(words) if words is not None else None
            cache.put(rec, other, words)
            return (other if ck.diff else None), words, ck.name

    def save(self) -> None:
        for c in self.caches.values():
            c.save()

    def close(self) -> None:
        self.save()
        if self.ck is not None:
            try:
                self.ck.close()
            except Exception:
                pass
            self.ck = None


# ============================================================================ 主流程
def _known_terms(project: Any, cfg: Any) -> List[str]:
    """读音词典（lexicon.txt）里的英文词和配置里的 prepare.proofcheck_terms：都当作"真的术语"。"""
    terms: List[str] = []
    try:
        for src, _dst in project.load_lexicon():
            terms += _LATIN_WORD.findall(_norm_same_len(str(src)))
    except Exception:
        pass
    extra = _cfg_get(cfg, "prepare.proofcheck_terms", None)
    if isinstance(extra, str):
        extra = re.split(r"[,，;；\s]+", extra)
    if isinstance(extra, (list, tuple)):
        for t in extra:
            terms += _LATIN_WORD.findall(_norm_same_len(str(t)))
    return terms


def _frequent_caps(records: Sequence[Dict[str, Any]], min_clips: int = 3) -> List[str]:
    """同一个大写英文词出现在好几段里：多半是老师常说的真术语（降低权重，不单独标红）。"""
    counts: Dict[str, int] = {}
    for r in records:
        if not r.get("keep", True):
            continue
        seen = {w.upper() for w in _LATIN_WORD.findall(_norm_same_len(str(r.get("text") or "")))
                if w.isupper() and len(w) >= 3}
        for w in seen:
            counts[w] = counts.get(w, 0) + 1
    return sorted(w for w, c in counts.items() if c >= min_clips)


def _is_srt_text(rec: Dict[str, Any]) -> bool:
    return rec.get("seg_mode") == "srt" and not rec.get("asr_done")


def _protect_changed(rec: Dict[str, Any], text: str, sus: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """自动查错字的结果里，碰到已经改过的字（和最初识别的不一样：老师自己改的、一键校正改好的）的标红和建议去掉：
    另一个识别引擎还是听成原来的错字时，不能把改好的字标红、更不能建议改回去（检查时发现「系 → 键」「句呀 → 剧」）。"""
    if not sus:
        return sus
    try:
        from voicetwin.data import review as _review
        from voicetwin.data.transcript_fix import _changed_chars, _touches_changed

        changed = _changed_chars(rec, text)
        if not changed[0] and not changed[1]:
            return sus
        spans = []
        for sp in sus.get("spans") or []:
            try:
                a, b = int(sp[0]), int(sp[1])
            except (TypeError, ValueError, IndexError):
                continue
            if not _touches_changed(a, b, changed):
                spans.append([a, b])
        edits = [ed for ed in _review.suggestion_edits(text, str(sus.get("alt") or ""))
                 if not _touches_changed(ed[0], ed[1], changed)]
        alt = _review.apply_edits(text, edits) if edits else ""
        if not spans and not edits:
            return None
        return dict(sus, spans=spans, alt=alt if alt and alt != text else "")
    except Exception as exc:  # noqa: BLE001 - 保护失败也不能让查错字失败：原样返回
        log.warning(f"⚠️ 查错字：去掉改过的字上的标红时出错（{_why(exc)}）", exc_info=exc)
        return sus


def _drop_rejected_auto(rec: Dict[str, Any], text: str, sus: Optional[Dict[str, Any]],
                        pairs: Any) -> Optional[Dict[str, Any]]:
    """自动查错字的结果里，老师撤销过的改法（点过「已采用」撤销、自己改回去）去掉：不再建议，那几个字也不再标红。"""
    if not sus or not pairs:
        return sus
    try:
        from voicetwin.data import review as _review

        edits = _review.suggestion_edits(text, str(sus.get("alt") or ""))
        bad = [ed for ed in edits if _review.is_rejected(pairs, text, *ed)]
        if not bad:
            return sus
        keep = [ed for ed in edits if ed not in bad]
        spans = []
        for sp in sus.get("spans") or []:
            try:
                a, b = int(sp[0]), int(sp[1])
            except (TypeError, ValueError, IndexError):
                continue
            if not any(a < max(e, s + 1) and s < b for s, e, _ in bad):
                spans.append([a, b])
        alt = _review.apply_edits(text, keep) if keep else ""
        if not spans and not keep:
            return None
        return dict(sus, spans=spans, alt=alt if alt and alt != text else "")
    except Exception as exc:  # noqa: BLE001 - 去不掉也不能让查错字失败：原样返回
        log.warning(f"⚠️ 查错字：去掉撤销过的改法时出错（{_why(exc)}）", exc_info=exc)
        return sus


def _count_flagged(project: Any, ids: Set[str]) -> int:
    """这次查过的句子里，表格上显示成「可能有错」的有几条（和校对表上方的数字一样算法：按显示的文字）。"""
    try:
        from voicetwin.data import review as _review

        draft = _review.load_draft(project)
        n = 0
        for rec in project.load_manifest():
            if str(rec.get("id")) not in ids or rec.get("deleted"):
                continue
            sus = rec.get("suspect")
            if not (isinstance(sus, dict) and (sus.get("spans") or sus.get("alt") or sus.get("reasons"))):
                continue
            shown = _review.current_values(rec, draft.get(rec.get("id")))["text"]
            if _review.analyze(rec, shown)["active"]:
                n += 1
        return n
    except Exception as exc:  # noqa: BLE001
        log.warning(f"⚠️ 查错字：统计标红的句子时出错（{_why(exc)}）", exc_info=exc)
        return 0


def find_suspects(project: Any, cfg: Any, progress: Optional[ProgressFn] = None, only_kept: bool = True,
                  limit: Optional[int] = None) -> Dict[str, Any]:
    """逐段查找可能的错字，结果写进 manifest（record["suspect"]），返回
    {"checked", "flagged", "engine", "note"}（另有 "total"、"errors"、"seconds"、"reason"）。

    - 每段都报告进度（"已检查 3 / 120 条……"），每 20 段存一次；点停止时先保存已经查完的部分再停。
    - 某一段出错只跳过那一段（改用规则检查），不会让整个任务失败。
    - 用户确认过"这句没错"（dismiss_suspect）且文字没再改过的片段，不再标红。
    """
    t0 = time.time()
    records = project.load_manifest()
    todo = [r for r in records if str(r.get("text") or "").strip() and (not only_kept or r.get("keep", True))]
    try:
        lim = int(limit) if limit is not None else 0
    except (TypeError, ValueError):
        lim = 0
    if lim > 0:
        todo = todo[:lim]
    n = len(todo)
    engine, reason = available_checker(cfg)
    if n == 0:
        _report(progress, 1.0, "没有需要检查的片段")
        return {"checked": 0, "flagged": 0, "engine": engine, "note": "没有需要检查的片段（请先准备素材）。",
                "total": 0, "errors": 0, "seconds": 0.0, "reason": reason}
    try:
        chain = _engine_chain(cfg)
    except Exception:
        chain = []
    known = _known_terms(project, cfg)
    frequent = _frequent_caps(records)
    vocab = english_vocab(records)
    runner = _EngineRunner(project, cfg, chain, progress)
    try:  # 表格里没保存的修改（「这句没错」按显示的文字记；一键校正改好、还没保存的行要能撤销）
        from voicetwin.data import review as _review

        draft = _review.load_draft(project)
        rejected = _review.load_rejected(project)  # 老师撤销过的改法：不再建议
    except Exception:  # noqa: BLE001
        _review, draft, rejected = None, {}, {}
    try:  # 用过「📝 一键全部文字校正」的句子：查完以后把新结果和一键校正的结果合在一起（不能冲掉）
        from voicetwin.data import transcript_fix as _tf

        oneclick = _tf.textfix_done_ids(project)
    except Exception:  # noqa: BLE001
        _tf, oneclick = None, set()
    remerge: List[str] = []
    used: Dict[str, int] = {}
    errors, flagged, checked, dismissed = 0, 0, 0, 0
    err_samples: List[str] = []
    how = f"用 {ENGINE_SHORT.get(engine, engine)} 再听一遍" if engine else "按规则检查"
    _report(progress, 0.0, f"开始查找可能的错字：一共 {n} 条（{how}）")
    finished = False
    try:
        for i, rec in enumerate(todo, 1):
            _check_cancel()
            runner.frac = (i - 1) / n
            text = str(rec.get("text") or "")
            lang = str(rec.get("lang") or "")
            heur_kw = {"known_terms": known, "frequent": frequent, "lang": lang, "vocab": vocab}
            eng = ""
            entry = draft.get(rec.get("id")) if draft else None
            shown = str(_review.current_values(rec, entry)["text"] or "") if (_review and entry) else text
            if rec.get("suspect_ok") and rec.get("suspect_ok") in (text, shown):
                # 用户确认过这句没错（文字也没再改过；表格里显示的那句也算）：不再标红
                dismissed += 1
                rec.pop("suspect", None)
                rec.pop("suspect_auto", None)
                checked += 1
                _report(progress, i / n, f"已检查 {i} / {n} 条")
                continue
            else:
                try:
                    other, words, eng = runner.recognize(rec, lang)
                    asr = rec.get("asr") if isinstance(rec.get("asr"), dict) else {}
                    sus = build_suspect(text, other, words, engine=eng, srt=_is_srt_text(rec),
                                        avg_logprob=asr.get("avg_logprob"), **heur_kw)
                except Exception as exc:  # noqa: BLE001 - 一段出错不影响别的段；停止按钮（TaskCancelled）照常传出去
                    errors += 1
                    eng = ""
                    if len(err_samples) < 3:
                        err_samples.append(f"{rec.get('id')}：{_why(exc)}")
                        log.warning(f"⚠️ 查错字：片段 {rec.get('id')} 出错（{_why(exc)}），这一段只用规则检查",
                                    exc_info=exc)
                    try:
                        sus = build_suspect(text, None, None, **heur_kw)
                    except Exception:  # noqa: BLE001
                        sus = None
                used[eng] = used.get(eng, 0) + 1
            sus = _protect_changed(rec, text, sus)  # 改过的字（老师改的、一键校正改好的）不标红、不建议改回去
            sus = _drop_rejected_auto(rec, text, sus, rejected.get(rec.get("id")))  # 老师撤销过的改法不再建议
            old = rec.get("suspect") if isinstance(rec.get("suspect"), dict) else None
            undo = bool(old and _review is not None and _review.analyze(rec, shown)["undo"])
            if old and old.get("src") == "transcript":
                # 一键校正的结果（保存了也算）：表格上的标记留着，这次查的结果当「自动查错字的结果」存起来，
                # 查完以后和一键校正的结果合在一起（以前直接换掉：没采用的建议没了、母本证明没错的标红又回来了，
                # 按钮是灰的，再也找不回来）
                if sus:
                    rec["suspect_auto"] = dict(sus, text=text)
                else:
                    rec.pop("suspect_auto", None)
                remerge.append(str(rec.get("id")))
            elif undo:
                # 这一行有还能撤销的修改（点过「采用」的建议，保存了也算）：标记留着，不然「已采用」的按钮没了、撤销不了
                rec.pop("suspect_auto", None)
            else:
                if sus:
                    rec["suspect"] = sus
                else:
                    rec.pop("suspect", None)
                rec.pop("suspect_auto", None)  # 重新自动查过：以前「文字校正」时存的旧结果不要了
                if str(rec.get("id")) in oneclick:
                    # 一键校正处理过、但没留下标记的行（没找到要改的、或者标红被母本证明没错去掉了）：
                    # 新查出来的也要拿母本再核对一遍（不然母本证明没错的标红又回来了）
                    remerge.append(str(rec.get("id")))
            checked += 1
            _report(progress, i / n, f"已检查 {i} / {n} 条")
            if i % SAVE_EVERY == 0 and i < n:
                project.save_manifest(records)
                runner.save()
        finished = True
    finally:
        if not finished:  # 停止或出了意外：已经查完的部分先存下来
            try:
                project.save_manifest(records)
            except Exception as exc:  # noqa: BLE001
                log.warning(f"⚠️ 查错字：保存已检查的结果失败（{_why(exc)}）", exc_info=exc)
        runner.close()
    project.save_manifest(records)
    if remerge and _tf is not None:
        _report(progress, 1.0, f"和「一键全部文字校正」的结果合在一起（{len(remerge)} 条）……")
        try:
            _tf.check_with_transcript(project, only=remerge, merge_only=True)
        except Exception as exc:  # noqa: BLE001 - 合不上：自动查错字的结果已经存好了，一键校正的标记也还在（停止照常传出去）
            log.warning(f"⚠️ 查错字：和一键全部文字校正的结果合在一起时出错（{_why(exc)}）", exc_info=exc)
    flagged = _count_flagged(project, {str(r.get("id")) for r in todo})

    real = {k: v for k, v in used.items() if k}
    main_engine = max(real, key=lambda k: real[k]) if real else ""
    rules_only = used.get("", 0)
    parts: List[str] = []
    if main_engine:
        label = ENGINE_LABELS.get(main_engine, main_engine)
        verb = "标出了识别时没把握的字" if main_engine == ENGINE_WHISPER_WORDS else "做了对比"
        gap = "" if label.endswith("）") else " "
        parts.append(f"用 {label}{gap}把 {sum(real.values())} 条再听了一遍，{verb}")
        if rules_only:
            parts.append(f"另外 {rules_only} 条只用规则检查（比如英文片段、出错的片段）")
    elif rules_only:
        parts.append(f"按规则检查了 {rules_only} 条（没有可用的第二个识别引擎，能发现的错字比较少）")
    if dismissed:
        parts.append(f"{dismissed} 条你已经确认过没错，没有再标红")
    parts += runner.notes
    if errors:
        parts.append(f"有 {errors} 条处理时出错，已改用规则检查（例如 {err_samples[0]}）" if err_samples
                     else f"有 {errors} 条处理时出错，已改用规则检查")
    note = "；".join(parts) + "。"
    secs = round(time.time() - t0, 1)
    log.info(f"查错字完成：检查了 {checked} 条，其中 {flagged} 条可能有错。{note}用时 {secs} 秒。")
    _report(progress, 1.0, f"查完了：检查了 {checked} 条，其中 {flagged} 条可能有错（已标红）")
    return {"checked": checked, "flagged": flagged, "engine": main_engine, "note": note, "total": n,
            "errors": errors, "seconds": secs, "reason": reason}


def dismiss_suspect(project: Any, clip_id: str) -> bool:
    """「这句没错」：去掉标红，并记住这句文字（表格里显示的那句，有没保存的修改就是改过的那句）；
    以后再查错字 / 文字校正时，只要文字没改，就不再标红、不再改。返回有没有找到这条。"""
    from voicetwin.data import review

    with review._LOCK:
        records = project.load_manifest()
        draft = review.load_draft(project)
        for rec in records:
            if str(rec.get("id")) == str(clip_id):
                rec.pop("suspect", None)
                rec.pop("suspect_auto", None)
                rec["suspect_ok"] = str(review.current_values(rec, draft.get(rec.get("id")))["text"] or "")
                project.save_manifest(records)
                return True
    return False


__all__ = [
    "ENGINE_FUNASR", "ENGINE_WHISPER", "ENGINE_WHISPER_WORDS", "ENGINE_LABELS", "FLAG_THRESHOLD", "RED_SPAN",
    "GREEN_SPAN", "Tok", "tokenize", "merge_spans", "compare", "heuristics", "low_prob_spans", "build_suspect",
    "render_marked", "render_plain", "render_diff_html", "available_checker", "find_suspects", "dismiss_suspect",
    "paraformer_path", "voice_vocab", "english_vocab",
]
