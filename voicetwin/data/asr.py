"""语音识别：给每个片段配上准确的文字（训练质量的关键）。

- faster-whisper（默认）：中英文都好，逐段自动识别语言，输出简体+标点。
- funasr：阿里达摩院模型，纯中文讲课更准（Paraformer / SenseVoice / Fun-ASR-Nano）。
国内网络下载模型慢时，可设置环境变量 HF_ENDPOINT=https://hf-mirror.com。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import clean_transcript, count_cjk, detect_lang, to_simplified

log = get_logger("asr")


@dataclass
class ASRResult:
    text: str
    lang: str
    avg_logprob: Optional[float] = None
    no_speech_prob: Optional[float] = None
    engine: str = ""


def _auto_device(device: str) -> str:
    if device and device != "auto":
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        pass
    try:
        import ctranslate2

        return "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    except Exception:
        return "cpu"


class Transcriber:
    """统一接口：transcribe(wav_16k_float32) -> ASRResult。"""

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = dict(cfg or {})
        self.engine = self.cfg.get("engine", "faster-whisper")
        self.language = self.cfg.get("language", "auto")
        self._model: Any = None

    # ------------------------------------------------------------------ 加载
    def _load(self) -> None:
        if self._model is not None:
            return
        if self.engine == "faster-whisper":
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError("未安装 faster-whisper：请执行 pip install \"voicetwin[asr]\"") from exc
            device = _auto_device(self.cfg.get("device", "auto"))
            compute_type = self.cfg.get("compute_type", "auto")
            if compute_type == "auto":
                compute_type = "float16" if device == "cuda" else "int8"
            model_name = self.cfg.get("model", "large-v3")
            log.info(f"加载识别模型 faster-whisper/{model_name}（{device}, {compute_type}）……首次使用会自动下载")
            self._model = WhisperModel(model_name, device=device, compute_type=compute_type)
        elif self.engine == "funasr":
            try:
                from funasr import AutoModel
            except ImportError as exc:
                raise RuntimeError("未安装 funasr：请执行 pip install \"voicetwin[funasr]\"") from exc
            model_name = self.cfg.get("model") or "paraformer-zh"
            if model_name.startswith("large") or model_name in ("medium", "small", "base"):
                model_name = "paraformer-zh"  # 用户切换引擎但没改模型名
            device = _auto_device(self.cfg.get("device", "auto"))
            kwargs: Dict[str, Any] = {"model": model_name, "device": "cuda:0" if device == "cuda" else "cpu",
                                      "disable_update": True}
            if "paraformer" in model_name:
                kwargs.update({"vad_model": "fsmn-vad", "punc_model": "ct-punc"})
            log.info(f"加载识别模型 funasr/{model_name}（{device}）……首次使用会从 ModelScope 下载")
            self._model = AutoModel(**kwargs)
        else:
            raise ValueError(f"未知的识别引擎：{self.engine}")

    # ------------------------------------------------------------------ 识别
    def transcribe(self, wav16k: np.ndarray, language: Optional[str] = None) -> ASRResult:
        self._load()
        lang = language or self.language
        if self.engine == "faster-whisper":
            return self._whisper(wav16k, lang)
        return self._funasr(wav16k)

    def _detect_lang(self, wav16k: np.ndarray) -> str:
        model = self._model
        probs: Dict[str, float] = {}
        try:
            _lang, _p, all_probs = model.detect_language(wav16k)
            probs = dict(all_probs)
        except Exception:
            try:
                _segs, info = model.transcribe(wav16k, language=None, beam_size=1)
                probs = dict(info.all_language_probs or [(info.language, info.language_probability)])
            except Exception:
                return "zh"
        # 只在中英文之间选；粤语/日语等按中文处理
        zh = probs.get("zh", 0.0) + probs.get("yue", 0.0) + 0.5 * probs.get("ja", 0.0)
        en = probs.get("en", 0.0)
        return "zh" if zh >= en else "en"

    def _whisper(self, wav16k: np.ndarray, lang: str) -> ASRResult:
        if lang not in ("zh", "en"):
            lang = self._detect_lang(wav16k)
        prompt = self.cfg.get("initial_prompt_zh") if lang == "zh" else None
        segments, _info = self._model.transcribe(
            wav16k,
            language=lang,
            beam_size=int(self.cfg.get("beam_size", 5)),
            initial_prompt=prompt,
            condition_on_previous_text=False,
            vad_filter=False,
            temperature=0.0,
        )
        texts, logprobs, weights, no_speech = [], [], [], []
        for seg in segments:
            texts.append(seg.text)
            dur = max(float(seg.end) - float(seg.start), 0.01)
            logprobs.append(float(seg.avg_logprob) * dur)
            weights.append(dur)
            no_speech.append(float(seg.no_speech_prob))
        text = "".join(texts) if lang == "zh" else " ".join(t.strip() for t in texts)
        if lang == "zh":
            text = to_simplified(text)
        text = clean_transcript(text)
        return ASRResult(
            text=text,
            lang=detect_lang(text) if text else lang,
            avg_logprob=(sum(logprobs) / sum(weights)) if weights else None,
            no_speech_prob=max(no_speech) if no_speech else None,
            engine=f"faster-whisper/{self.cfg.get('model')}",
        )

    def _funasr(self, wav16k: np.ndarray) -> ASRResult:
        res = self._model.generate(input=wav16k, language="auto", use_itn=True, batch_size_s=60)
        text = res[0].get("text", "") if res else ""
        try:
            from funasr.utils.postprocess_utils import rich_transcription_postprocess

            text = rich_transcription_postprocess(text)
        except Exception:
            pass
        text = clean_transcript(to_simplified(text))
        # 去掉 paraformer 在中文里夹的多余空格
        if count_cjk(text):
            text = clean_transcript(text)
        return ASRResult(text=text, lang=detect_lang(text) if text else "zh",
                         engine=f"funasr/{self.cfg.get('model')}")


# Whisper 在静音/音乐上常见的"幻觉"文本
HALLUCINATIONS = (
    "请不吝点赞", "订阅", "字幕由", "字幕制作", "Amara.org", "谢谢观看", "感谢观看", "明镜与点点",
    "优优独播剧场", "Thanks for watching", "Thank you for watching", "Subtitles by", "字幕志愿者",
    "中文字幕", "请订阅", "点赞", "转发", "打赏",
)


def looks_hallucinated(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    hits = sum(1 for h in HALLUCINATIONS if h.lower() in t.lower())
    if hits and len(t) < 40:
        return True
    # 同一个字连续 6 次以上，或同一个短语（2~5 字）连续重复 4 次以上
    for pattern in (r"(\D)\1{5,}", r"(\D{2,5}?)\1{3,}"):
        m = re.search(pattern, t)
        if m and m.group(1).strip(" .,，。-—_…"):
            return True
    return False


def hf_mirror_hint() -> str:
    if os.environ.get("HF_ENDPOINT"):
        return ""
    return "（如果下载模型很慢或失败，可以先设置环境变量 HF_ENDPOINT=https://hf-mirror.com 再运行）"
