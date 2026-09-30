"""合成引擎：讲稿 → 完整的讲课音频（+ 字幕）。

为了"像你"做的事情：
1. 每句话生成多个候选（不同随机种子），用声纹相似度、语速/音高偏差、（可选）识别错字率打分，挑最像的；
2. 错字率太高（漏字/多字/读错）自动重试；
3. 疑问句用你的疑问语气参考音频，陈述句用陈述参考；
4. 句间/段间停顿按你本人的停顿习惯（含自然波动）；
5. 语速用验证集自动校准，响度匹配你原来的录音；
6. 每句结果都缓存：改了讲稿的某一句，重新生成只会重做那一句。
"""

from __future__ import annotations

import json
import random
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

from voicetwin.backends.base import Backend, SynthRequest
from voicetwin.data.references import aux_references, pick_reference
from voicetwin.eval.metrics import CERChecker, Score, Scorer
from voicetwin.eval.speaker import get_speaker_encoder, voice_centroid
from voicetwin.project import Project
from voicetwin.style.profile import pause_range, pause_seconds
from voicetwin.synth.script import ScriptSegment, parse_script
from voicetwin.utils.audio import (
    fade,
    load_audio,
    measure_lufs,
    normalize_lufs,
    resample,
    save_audio,
    silence,
    trim_silence,
)
from voicetwin.utils.ffmpeg import encode
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import short_hash

log = get_logger("synth")
CACHE_VERSION = "v1"
QUALITY_PRESETS = {
    "fast": {"candidates": 1, "asr": False},
    "balanced": {"candidates": 3, "asr": False},
    "best": {"candidates": 5, "asr": True},
}
ProgressFn = Callable[[float, str], None]


@dataclass
class SegmentResult:
    segment: ScriptSegment
    wav: np.ndarray
    sr: int
    score: Dict[str, Any]
    ref_id: str
    cached: bool
    seed: int
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    start: float = 0.0
    end: float = 0.0


@dataclass
class NarrationResult:
    audio_path: Path
    srt_path: Optional[Path]
    report_path: Path
    duration: float
    segments: List[Dict[str, Any]]
    warnings: List[str]


class Narrator:
    def __init__(self, cfg: Dict[str, Any], project: Project, backend: Backend, quality: Optional[str] = None,
                 candidates: Optional[int] = None, speed: Union[str, float, None] = None, reference: str = "",
                 asr_check: Optional[bool] = None, progress: Optional[ProgressFn] = None):
        self.cfg = cfg
        self.scfg: Dict[str, Any] = dict(cfg.get("synth", {}) or {})
        self.project = project
        self.backend = backend
        self.quality = quality or self.scfg.get("quality", "balanced")
        preset = QUALITY_PRESETS.get(self.quality, QUALITY_PRESETS["balanced"])
        cand_cfg = candidates if candidates is not None else self.scfg.get("candidates", "auto")
        self.n_candidates = int(preset["candidates"] if cand_cfg in (None, "auto") else cand_cfg)
        asr_cfg = asr_check if asr_check is not None else self.scfg.get("asr_check", "auto")
        self.use_asr = bool(preset["asr"]) if asr_cfg in (None, "auto") else bool(asr_cfg)
        self.speed_opt = speed if speed is not None else self.scfg.get("speed", "auto")
        self.reference = reference
        self.progress = progress
        self.profile = project.load_profile()
        self.refs = project.load_references()
        self.warnings: List[str] = []
        self._scorer: Optional[Scorer] = None
        self.base_seed = int(self.scfg.get("seed", 20240601))

    # ------------------------------------------------------------------ 打分器
    @property
    def scorer(self) -> Scorer:
        if self._scorer is None:
            try:
                encoder = get_speaker_encoder(self.cfg.get("speaker_encoder", "auto"))
                cen = voice_centroid(self.project, encoder)
            except Exception as exc:
                log.warning(f"声纹打分不可用：{exc}")
                encoder, cen = None, None
            checker = CERChecker(self.scfg.get("asr_check_model", "small")) if self.use_asr else None
            self._scorer = Scorer(self.profile, cen, encoder, self.scfg.get("score"), checker)
        return self._scorer

    # ------------------------------------------------------------------ 工具
    def _speed_multiplier(self) -> float:
        """用户额外指定的快慢倍数（auto = 1.0，即完全按你本人的语速）。"""
        opt = self.speed_opt
        return 1.0 if opt in (None, "auto", "") else float(opt)

    def _speed_for(self, lang: str) -> float:
        """最终传给引擎的语速 = 自动校准系数 × 用户倍数。"""
        cal = self.backend.speed_calibration()
        return float(cal.get(lang, cal.get("zh", 1.0)) or 1.0) * self._speed_multiplier()

    def _progress(self, frac: float, msg: str) -> None:
        if self.progress:
            try:
                self.progress(max(0.0, min(1.0, frac)), msg)
            except Exception:
                pass

    def _cache_paths(self, key: str) -> Tuple[Path, Path]:
        d = self.project.cache_dir / "segments" / key[:2]
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{key}.wav", d / f"{key}.json"

    # ------------------------------------------------------------------ 单句
    def synthesize_segment(self, seg: ScriptSegment, force: bool = False) -> SegmentResult:
        ref = pick_reference(self.refs, seg.lang, seg.kind, self.reference)
        aux = aux_references(self.refs, ref, int((self.backend.bcfg.get("infer") or {}).get("aux_refs", 0)))
        if not self.backend.supports_aux_refs:
            aux = []
        speed = self._speed_for(seg.lang)
        key = short_hash(CACHE_VERSION, self.backend.model_id(), seg.text, seg.lang, ref["id"], [a["id"] for a in aux],
                         round(speed, 3), self.n_candidates, self.use_asr, self.base_seed, n=16)
        wav_path, meta_path = self._cache_paths(key)
        if wav_path.exists() and meta_path.exists() and not force:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            wav, sr = load_audio(wav_path)
            return SegmentResult(seg, wav, sr, meta.get("score", {}), ref["id"], True, meta.get("seed", 0),
                                 meta.get("candidates", []))

        seed0 = self.base_seed + seg.index * 7919
        if force:
            seed0 += random.randint(1, 10_000_000)
        tmp_dir = self.project.cache_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        candidates: List[Tuple[Score, int, np.ndarray, int]] = []
        cand_info: List[Dict[str, Any]] = []
        max_retries = int(self.scfg.get("max_retries", 2))
        cer_thr = float(self.scfg.get("cer_retry_threshold", 0.15))
        rounds = [(self.n_candidates, None)] + [(2, 0.7)] * max_retries
        for r_i, (n, temperature) in enumerate(rounds):
            for k in range(n):
                seed = seed0 + (r_i * 101 + k) * 104729
                req = SynthRequest(
                    text=seg.text, lang=seg.lang, ref_audio=self.project.abspath(ref["path"]), ref_text=ref["text"],
                    ref_lang=ref["lang"], aux_refs=[self.project.abspath(a["path"]) for a in aux], seed=seed,
                    speed=speed, temperature=temperature, top_k=10 if temperature else None,
                )
                out = tmp_dir / f"{key}_{r_i}_{k}.wav"
                try:
                    self.backend.synthesize(req, out)
                    wav, sr = load_audio(out)
                except Exception as exc:
                    log.warning(f"  第 {seg.index + 1} 句候选 {k + 1} 失败：{exc}")
                    continue
                finally:
                    out.unlink(missing_ok=True)
                if wav.size == 0:
                    continue
                need_score = self.n_candidates > 1 or self.use_asr or r_i > 0
                # 在裁剪前打分（语速测量需要首尾的静音作为底噪参考）
                score = self.scorer.score(wav, sr, seg.text, seg.lang, speed=self._speed_multiplier(), use_asr=self.use_asr) \
                    if need_score else Score(total=0.0)
                wav, _, _ = trim_silence(wav, sr, pad_ms=40)
                if wav.size == 0:
                    continue
                candidates.append((score, seed, wav, sr))
                cand_info.append({"seed": seed, **score.to_dict()})
            if not candidates:
                continue
            best = max(candidates, key=lambda c: c[0].total)
            if not self.use_asr or best[0].cer is None or best[0].cer <= cer_thr:
                break
            log.info(f"  第 {seg.index + 1} 句错字率 {best[0].cer:.0%}（识别为：{best[0].hyp}），重新生成……")
        if not candidates:
            raise RuntimeError(f"第 {seg.index + 1} 句合成失败：{seg.text}")
        best_score, best_seed, best_wav, sr = max(candidates, key=lambda c: c[0].total)
        if self.n_candidates == 1 and not self.use_asr:  # 单候选时也给出一份打分，方便查看
            best_score = self.scorer.score(best_wav, sr, seg.text, seg.lang, speed=self._speed_multiplier(), use_asr=False)
        save_audio(wav_path, best_wav, sr)
        meta = {"text": seg.text, "lang": seg.lang, "ref": ref["id"], "seed": best_seed, "score": best_score.to_dict(),
                "candidates": cand_info, "model": self.backend.model_id(), "created": time.strftime("%Y-%m-%d %H:%M:%S")}
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        return SegmentResult(seg, best_wav, sr, meta["score"], ref["id"], False, best_seed, cand_info)

    # ------------------------------------------------------------------ 整篇
    def narrate(self, source: Union[str, Path, Sequence[ScriptSegment]], out_path: Union[str, Path],
                redo: Iterable[int] = (), subtitles: Optional[bool] = None) -> NarrationResult:
        if isinstance(source, (list, tuple)):
            segments = list(source)
        else:
            segments = parse_script(
                source, lexicon=self.project.load_lexicon(),
                max_units_zh=int(self.scfg.get("max_units_zh", 50)), max_units_en=int(self.scfg.get("max_units_en", 45)),
                min_units=int(self.scfg.get("min_units", 6)), skip_code_blocks=bool(self.scfg.get("skip_code_blocks", True)),
            )
        if not segments:
            raise ValueError("讲稿里没有可以朗读的内容")
        if not self.refs:
            raise RuntimeError("这个声音还没有参考音频，请先完成素材准备（voicetwin prepare）")
        redo_set = {int(i) - 1 for i in redo}  # 用户看到的编号从 1 开始
        out_path = Path(out_path)
        log.info(f"共 {len(segments)} 句，引擎 {self.backend.display_name}，质量 {self.quality}"
                 f"（每句 {self.n_candidates} 个候选{'，识别校验' if self.use_asr else ''}）")
        self.backend.start()
        results: List[SegmentResult] = []
        t0 = time.time()
        for i, seg in enumerate(segments):
            res = self.synthesize_segment(seg, force=i in redo_set)
            results.append(res)
            sim = res.score.get("speaker_sim")
            tag = "缓存" if res.cached else "生成"
            msg = f"[{i + 1}/{len(segments)}] {tag} {seg.display[:28]}" + (f"（相似度 {sim:.2f}）" if sim is not None else "")
            log.info(msg)
            self._progress((i + 1) / len(segments) * 0.95, msg)
            for issue in res.score.get("issues") or []:
                self.warnings.append(f"第 {i + 1} 句：{issue}（可用 --redo {i + 1} 重新生成）")
        audio, sr = self._assemble(results)
        final = self._write_audio(audio, sr, out_path)
        srt_path = None
        if subtitles if subtitles is not None else self.scfg.get("subtitles", True):
            srt_path = self._write_srt(results, final.with_suffix(".srt"))
        seg_report = [{
            "index": r.segment.index + 1, "text": r.segment.display, "tts_text": r.segment.text, "lang": r.segment.lang,
            "start": round(r.start, 3), "end": round(r.end, 3), "ref": r.ref_id, "cached": r.cached, "seed": r.seed,
            **{k: v for k, v in r.score.items() if k in ("speaker_sim", "cer", "rate", "issues")},
        } for r in results]
        sims = [s["speaker_sim"] for s in seg_report if s.get("speaker_sim") is not None]
        report = {"audio": str(final), "backend": self.backend.name, "model": self.backend.model_id(),
                  "quality": self.quality, "duration": round(len(audio) / sr, 2),
                  "mean_speaker_sim": round(float(np.mean(sims)), 4) if sims else None,
                  "elapsed_sec": round(time.time() - t0, 1), "warnings": self.warnings, "segments": seg_report}
        report_path = final.with_suffix(".report.json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        self._progress(1.0, f"完成：{final}")
        return NarrationResult(final, srt_path, report_path, len(audio) / sr, seg_report, self.warnings)

    def say(self, text: str, out_path: Union[str, Path]) -> NarrationResult:
        return self.narrate(text, out_path, subtitles=False)

    # ------------------------------------------------------------------ 拼接
    def _pause(self, seg: ScriptSegment, i: int) -> float:
        kind = seg.pause_after
        if isinstance(kind, (int, float)):
            return float(kind)
        if self.scfg.get("pauses", "profile") == "fixed":
            return pause_seconds(self.profile, kind, self.scfg.get("fixed_pauses") or {})
        lo, hi = pause_range(self.profile, kind)
        base = pause_seconds(self.profile, kind)
        rng = random.Random(self.base_seed + i)
        # 在你的常见停顿范围内轻微波动（偏向中位数），避免机械感
        val = base + (rng.random() - 0.5) * (hi - lo) * 0.6
        return float(max(0.08, val))

    def _assemble(self, results: List[SegmentResult]) -> Tuple[np.ndarray, int]:
        sr = max(r.sr for r in results)
        timed = any(r.segment.cue_start is not None for r in results)
        pieces: List[Tuple[float, np.ndarray]] = []
        cursor = 0.35
        for i, r in enumerate(results):
            wav = fade(resample(r.wav, r.sr, sr), sr)
            if timed and r.segment.cue_start is not None:
                start = r.segment.cue_start
                if start < cursor - 0.02:
                    if start + 0.5 < cursor:
                        self.warnings.append(f"第 {i + 1} 句比字幕时间轴晚了 {cursor - start:.1f} 秒（上一句太长）")
                    start = cursor
            else:
                start = cursor
            r.start, r.end = start, start + len(wav) / sr
            pieces.append((start, wav))
            if timed:
                cursor = r.end + (0.08 if r.segment.pause_after == "clause" else 0.0)
            else:
                cursor = r.end + self._pause(r.segment, i)
        total = max(s + len(w) / sr for s, w in pieces) + 0.4
        out = np.zeros(int(total * sr) + 1, dtype=np.float32)
        for start, wav in pieces:
            a = int(round(start * sr))
            out[a:a + len(wav)] += wav
        return out, sr

    def _target_lufs(self) -> Optional[float]:
        opt = self.scfg.get("loudness", "profile")
        if opt in (None, "off", False):
            return None
        if opt == "profile":
            loud = self.profile.get("loudness") or {}
            val = loud.get("source_lufs") or loud.get("clip_lufs")
            return float(val) if val is not None else -18.0
        return float(opt)

    def _write_audio(self, audio: np.ndarray, sr: int, out_path: Path) -> Path:
        target = self._target_lufs()
        if target is not None:
            audio = normalize_lufs(audio, sr, target, ceiling_db=-1.0)
        fmt = (out_path.suffix.lower().lstrip(".") or self.scfg.get("output_format", "wav"))
        wav_path = out_path.with_suffix(".wav")
        save_audio(wav_path, audio, sr)
        log.info(f"输出响度 {measure_lufs(audio, sr):.1f} LUFS，时长 {len(audio) / sr:.1f} 秒")
        if fmt in ("mp3", "m4a", "flac"):
            final = encode(wav_path, out_path.with_suffix("." + fmt))
            wav_path.unlink(missing_ok=True)
            return final
        return wav_path

    def _write_srt(self, results: List[SegmentResult], path: Path) -> Path:
        from voicetwin.data.subtitles import Cue, write_srt

        cues = [Cue(r.start, r.end, r.segment.display) for r in results]
        return write_srt(cues, path)


def clear_cache(project: Project) -> int:
    seg_dir = project.cache_dir / "segments"
    n = sum(1 for _ in seg_dir.rglob("*.wav")) if seg_dir.exists() else 0
    shutil.rmtree(seg_dir, ignore_errors=True)
    return n
