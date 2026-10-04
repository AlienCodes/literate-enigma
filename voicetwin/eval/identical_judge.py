"""「一模一样」档的打分（设计方案 research/一模一样/设计方案原文.md §1.8）。

每个版本分两步打分：
1. 快速打分（每个版本都做）：说话时长和你本人的语速比（不在 0.6~1.6 倍之间、句中有特别长的停顿、几乎没有声音的，
   排到最后），再只用一个声纹模型（ERes2Net-base，开发机实测 0.14 秒）打分：
   快速分 = 2.0 × min(这个模型的分数, 它给你真实录音打的 p90) / 100 − 0.4 × 时长偏差；
2. 完整打分（快速分排在前 12 名的、每种组合里最好的那个，每句最多 24 个）：全部声纹模型一起（人声检测和第一个模型的
   声纹不用再算）、音调、中英文分开查错字。

完整打分的综合分（权重来自 config.yaml 的 synth.score：像你本人 2.0、错字 1.0、语速 0.4、音调 0.2）：
- 像你本人的那一项：精准打分时，几个模型的平均最多算到你自己真实录音的 p90（再高多半是机器打分的偶然，不再加分），
  再减 0.5 × 模型之间的差别（几个模型说法不一致就保守一点）；没有精准打分时和以前完全一样；
- − 错字率；
- − 时长偏差：|ln(说话时长 / (按你本人的语速模型这句话应该说多久 / 快慢倍数))|（语速模型在 twin_profile.json 里，
  量不出来时用你整体的语速，再没有就用以前的语速标准）；
- − 音调偏差（和以前一样）；
- − 音调起伏、频谱形状和你平时差多少（权重默认 0：只有用你的录音校准过才用）；
- − 其它问题的扣分（和以前一样）；句中停顿超过你自己录音的 p97 才算异常停顿。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from voicetwin.eval.metrics import Score, Scorer
from voicetwin.style.profile import target_rate
from voicetwin.style.prosody import f0_stats
from voicetwin.utils.audio import clip_ratio, speech_activity
from voicetwin.utils.log import get_logger
from voicetwin.utils.textutil import send_lang, syllable_count

log = get_logger("identical")

#: 快速打分用的声纹模型（三个里最快的；没有它时用打分器里的最后一个）
QUICK_MEMBER = "eres2net-base-zh"
#: 说话时长 / 应该说的时长 不在这个范围里：快速打分时排到最后（多半是漏读、重复或者拖音）
GATE_RATIO = (0.6, 1.6)
#: 没过快速检查的版本快速分扣这么多（排到最后，但每种组合最好的那个照样完整打分）
GATE_PENALTY = 10.0
#: 句中停顿多长算异常（以前一直是 1.2 秒）：量出了你自己录音的 p97 就用它
LONG_PAUSE = 1.2
#: 用显卡打分的条件：显卡和处理器算出来的声纹余弦相似度至少这么高、显卡至少还空这么多显存
GPU_MIN_COSINE = 0.9999
GPU_MIN_FREE_GB = 1.5


@dataclass
class QuickScore:
    """快速打分的结果。"""
    total: float
    pct_raw: Optional[float]          # 快速打分那一个声纹模型的分数（没封顶）
    voiced: float                     # 说话时长（秒）
    expected: Optional[float]         # 按你本人的语速这句话应该说多久（已经按快慢倍数换算；没测出来是 None）
    dur_dev: Optional[float]          # |ln(说话时长 / 应该说的时长)|
    gate_ok: bool                     # 过没过快速检查
    why: str = ""                     # 没过的原因
    member: str = ""                  # 用的是哪个声纹模型
    prepared: Any = field(default=None, repr=False, compare=False)  # 人声检测和声纹（完整打分时接着用）


def _num(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


class IdenticalScorer(Scorer):
    """「一模一样」档的打分器：在原来的打分器上加你本人的说话习惯（twin_profile.json）、你自己真实录音的范围、
    每个声纹模型各自的范围和排序权重。score() 还是原来的打分（两个版本比较时用）。"""

    def __init__(self, profile: Dict[str, Any], centroid: Optional[np.ndarray], encoder: Any,
                 weights: Optional[Dict[str, float]] = None, cer_checker: Any = None, judge: Any = None,
                 twin: Optional[Dict[str, Any]] = None, rank_weights: Optional[Dict[str, Any]] = None):
        super().__init__(profile, centroid, encoder, weights, cer_checker, judge=judge)
        self._base_rate = float(self.w.get("rate", 0.4))
        self.configure(twin, rank_weights)

    def configure(self, twin: Optional[Dict[str, Any]] = None, rank_weights: Optional[Dict[str, Any]] = None) -> None:
        """换你本人的说话习惯和排序权重（「准备「一模一样」」重新校准以后，不用重新加载声纹和识别模型）。
        rank_weights（models.json 的 identical.weights，P8 用你的录音校准的）：pros 音调起伏、ltas 频谱形状、
        rate 时长偏差（不写就用 synth.score 里的）、cap（p90 = 像你本人封顶在你自己录音的 p90；none = 不封顶）。"""
        self.twin = twin if isinstance(twin, dict) else {}
        dm = self.twin.get("duration_model")
        self.duration_model = dm if isinstance(dm, dict) else None
        p97 = _num((self.twin.get("inner_pause_p97") or {}).get("value"))
        self.inner_p97 = p97 if p97 is not None and p97 > 0 else None
        rw = {"pros": 0.0, "ltas": 0.0}
        for k, v in (rank_weights or {}).items():
            if k in rw and _num(v) is not None:
                rw[k] = float(v)
        self.rank_w = rw
        rate = _num((rank_weights or {}).get("rate"))
        self.w["rate"] = float(rate) if rate is not None and rate >= 0 else self._base_rate
        self.cap_mode = "none" if str((rank_weights or {}).get("cap") or "").strip().lower() == "none" else "p90"
        self.use_judge(self.judge)

    def use_judge(self, judge: Any) -> None:
        """换打分器（例如声纹模型改到显卡上以后）：你自己录音的范围、快速打分用哪个模型跟着重新取。"""
        self.judge = judge if (judge is not None and getattr(judge, "available", False)) else None
        natural = getattr(self.judge, "natural_range", None) if self.judge is not None else None
        try:
            self.natural: Optional[Dict[str, float]] = natural() if callable(natural) else None
        except Exception:  # noqa: BLE001 - 量不出来就当没有
            self.natural = None
        self.precise = bool(self.judge is not None and getattr(self.judge, "precise", False) and self.natural)
        capped = self.precise and getattr(self, "cap_mode", "p90") != "none"
        self.cap = _num((self.natural or {}).get("p90")) if capped else None
        members = list(getattr(self.judge, "members", []) or []) if self.judge is not None else []
        finder = getattr(self.judge, "member", None)
        qm = finder(QUICK_MEMBER) if callable(finder) else None
        self.quick_member = qm if qm is not None else (members[-1] if members else None)

    # ------------------------------------------------------------------ 你本人的语速
    def expected(self, text: str, lang: str = "zh") -> Optional[float]:
        """按你本人的语速，这句话（不含停顿）应该说多少秒；没测出来是 None。
        先用 twin_profile.json 的语速模型（不 ok 时用你整体的语速），再没有就用以前说话风格里的语速。"""
        from voicetwin.style.twin_profile import expected_voiced

        val = None
        try:
            val = expected_voiced(self.duration_model, text)
        except Exception:  # noqa: BLE001
            val = None
        if val is None or val <= 0:
            syl = syllable_count(text)
            rate = target_rate(self.profile, send_lang(text, lang)) if syl else 0.0
            val = syl / rate if syl and rate and rate > 0 else None
        return float(val) if val else None

    def resid_sd(self) -> Optional[float]:
        """语速模型的残差（ln 秒）：你自己的句子平时偏离预测多少。语速模型不 ok 时是 None。"""
        dm = self.duration_model or {}
        sd = _num(dm.get("resid_sd_log"))
        return sd if dm.get("ok") and sd is not None and sd > 0 else None

    def long_pause(self) -> float:
        """完整打分时句中停顿多长算异常：你自己录音的 p97（量出来了的话），否则 1.2 秒。"""
        return float(self.inner_p97) if self.inner_p97 is not None else LONG_PAUSE

    def quick_pause_limit(self) -> float:
        """快速检查：句中停顿超过 max(1.2 秒, 你自己的 p97) 就排到后面。"""
        return max(LONG_PAUSE, self.inner_p97 or 0.0)

    # ------------------------------------------------------------------ 像你本人的那一项
    def timbre_term(self, score: Score) -> float:
        """综合分里「像你本人」那一项。精准打分：几个模型的平均先封顶在你自己录音的 p90，再减 0.5 × 模型之间的差别
        （几个模型说法不一致总要扣分，封顶以后也一样）；没有精准打分：和原来的打分一模一样。"""
        w = self.w["speaker"]
        if self.precise and score.pct_raw is not None:
            val = float(score.pct_raw)
            if self.cap is not None:
                val = min(val, self.cap)
            return w * (val - 0.5 * float(score.spread or 0.0)) / 100.0
        if score.pct_raw is not None:
            return w * float(np.clip(score.pct_raw, -50.0, 150.0)) / 100.0
        if score.pct is not None:
            return w * float(score.pct) / 100.0
        if score.speaker_sim is not None:
            return w * float(score.speaker_sim)
        return 0.0

    def non_timbre(self, score: Score) -> float:
        """综合分里除了「像你本人」以外的部分（时长、音调、读得准不准、扣分）：差不多一样高时按它挑。"""
        return float(score.total) - self.timbre_term(score)

    def member_floor_ok(self, score: Score, key: str = "g10") -> bool:
        """每个声纹模型的分数都不低于它自己给你真实录音打的那个百分位（默认 p10）；没有精准打分时不查。"""
        if not self.precise or not score.pcts:
            return True
        for m in getattr(self.judge, "members", []) or []:
            floor = m.natural_pct(key) if hasattr(m, "natural_pct") else None
            got = score.pcts.get(m.name)
            if floor is not None and got is not None and float(got) < float(floor):
                return False
        return True

    # ------------------------------------------------------------------ 第 1 步：快速打分
    def prepare(self, wav: np.ndarray, sr: int) -> Optional[Dict[str, Any]]:
        prep = getattr(self.judge, "prepare", None) if self.judge is not None else None
        return prep(wav, sr) if callable(prep) else None

    def quick(self, wav: np.ndarray, sr: int, text: str, lang: str, mult: float = 1.0) -> QuickScore:
        wav = np.asarray(wav, dtype=np.float32)
        voiced, pauses = speech_activity(wav, sr)
        exp = self.expected(text, lang)
        exp_m = exp / float(mult or 1.0) if exp else None
        why = ""
        if voiced < 0.2:
            why = "几乎没有声音"
        elif exp_m:
            ratio = voiced / exp_m
            if not GATE_RATIO[0] <= ratio <= GATE_RATIO[1]:
                why = f"说话时长是应该的 {ratio:.2f} 倍"
        if not why and pauses and max(pauses) > self.quick_pause_limit():
            why = f"句中有 {max(pauses):.1f} 秒的停顿"
        dur_dev = abs(math.log(voiced / exp_m)) if exp_m and voiced >= 0.2 else None
        prepared = self.prepare(wav, sr)
        q_pct: Optional[float] = None
        member = ""
        if wav.size > sr * 0.3:
            if prepared is not None and self.quick_member is not None:
                member = self.quick_member.name
                try:
                    q_pct = self.judge.judge_prepared(prepared, members=[member]).get("pct_raw")
                except Exception as exc:  # noqa: BLE001 - 这一个模型打不了分：只按时长排
                    log.debug(f"快速打分失败：{exc}")
            elif self.encoder is not None and self.centroid is not None:
                from voicetwin.eval.speaker import cosine

                member = getattr(self.encoder, "name", "")
                q_pct = 100.0 * cosine(self.encoder.embed(wav, sr), self.centroid)
        total = 0.0
        if q_pct is not None:
            cap = None
            if (self.precise and self.cap_mode != "none" and self.quick_member is not None
                    and hasattr(self.quick_member, "natural_pct")):
                cap = self.quick_member.natural_pct("g90")
            val = min(float(q_pct), cap) if cap is not None else float(np.clip(q_pct, -50.0, 150.0))
            total += self.w["speaker"] * val / 100.0
        if dur_dev is not None:
            total -= self.w["rate"] * dur_dev
        if why:
            total -= GATE_PENALTY
        return QuickScore(total=total, pct_raw=q_pct, voiced=float(voiced), expected=exp_m, dur_dev=dur_dev,
                          gate_ok=not why, why=why, member=member, prepared=prepared)

    # ------------------------------------------------------------------ 第 2 步：完整打分
    def full(self, wav: np.ndarray, sr: int, text: str, lang: str, mult: float = 1.0,
             prepared: Optional[Dict[str, Any]] = None, use_asr: bool = True,
             cer: Optional[Dict[str, Any]] = None, check_pauses: bool = True) -> Score:
        """完整打分。prepared：快速打分时准备好的声音（人声检测和那个模型的声纹接着用）；
        cer：以前查过的错字结果（重新排名时用，不再识别一遍）。"""
        wav = np.asarray(wav, dtype=np.float32)
        issues: List[str] = []
        sim = pct = pct_raw = spread = seconds = None
        pcts: Dict[str, float] = {}
        sims: Dict[str, float] = {}
        if wav.size > sr * 0.3:
            if self.judge is not None:
                if prepared is None:
                    prepared = self.prepare(wav, sr)
                fn = getattr(self.judge, "judge_prepared", None)
                res = fn(prepared) if (callable(fn) and prepared is not None) else self.judge.judge(wav, sr)
                sim, pct, pct_raw = res.get("sim"), res.get("pct"), res.get("pct_raw")
                pcts, sims = res.get("pcts") or {}, res.get("sims") or {}
                spread, seconds = res.get("spread"), res.get("seconds")
            elif self.encoder is not None and self.centroid is not None:
                from voicetwin.eval.speaker import cosine

                sim = cosine(self.encoder.embed(wav, sr), self.centroid)
        lcb = None
        if pct_raw is not None:
            lcb = float(pct_raw) - 0.5 * float(spread or 0.0)
        score = Score(total=0.0, speaker_sim=sim, pct=pct, pct_raw=pct_raw, pcts=pcts, sims=sims,
                      speech_seconds=seconds, lcb=lcb, spread=spread, stage="full")
        total = self.timbre_term(score)

        voiced, pauses = speech_activity(wav, sr)
        score.voiced = round(float(voiced), 3)
        if voiced < 0.2:
            issues.append("几乎没有声音")
            total -= 2.0
        syl = syllable_count(text)
        exp = self.expected(text, lang)
        exp_m = exp / float(mult or 1.0) if exp else None
        score.expected = round(exp_m, 3) if exp_m else None
        if voiced >= 0.2 and syl:
            score.rate = syl / voiced
        if exp_m and voiced >= 0.2:
            ratio = voiced / exp_m
            score.dur_dev = abs(math.log(ratio))
            score.rate_dev = score.dur_dev
            sd = self.resid_sd()
            score.dur_z = math.log(ratio) / sd if sd else None
            total -= self.w["rate"] * score.dur_dev
            if ratio > 1.0 / 0.45:  # 和以前一样：语速不到应该的 45%
                issues.append("语速过慢/可能有重复或杂音")
                total -= 0.5
            if ratio < 0.5:  # 语速超过应该的 2 倍
                issues.append("语速过快/可能漏读")
                total -= 0.5
        long_pauses = [p for p in pauses if p > self.long_pause()] if check_pauses else []
        if long_pauses:
            issues.append(f"句中有 {max(long_pauses):.1f}s 的异常停顿")
            total -= 0.3 * len(long_pauses)
        if clip_ratio(wav) > 0.002:
            issues.append("有爆音")
            total -= 0.3
        lang_p = send_lang(text, lang)
        ref_pitch = (self.profile.get("pitch") or {}).get(lang_p) or (self.profile.get("pitch") or {}).get("zh")
        if ref_pitch and self.w.get("pitch", 0) > 0:
            st = f0_stats(wav, sr)
            if st:
                score.f0 = float(st["f0_median"])
                semis = abs(12.0 * math.log2(st["f0_median"] / ref_pitch["f0_median"]))
                dev = abs(st["f0_semitone_std"] - ref_pitch.get("semitone_std", st["f0_semitone_std"]))
                score.pitch_dev = semis / 12.0 + dev / 12.0
                total -= self.w["pitch"] * score.pitch_dev
        if self.rank_w["pros"] > 0 or self.rank_w["ltas"] > 0:
            pz, ld = self._shape(wav, sr, text)
            score.prosody_z, score.ltas_d = pz, ld
            if pz is not None:
                total -= self.rank_w["pros"] * pz
            if ld is not None:
                total -= self.rank_w["ltas"] * ld
        res_cer = cer
        if res_cer is None and use_asr and self.cer_checker is not None:
            mixed = getattr(self.cer_checker, "check_mixed", None)
            res_cer = mixed(wav, sr, text) if callable(mixed) else self.cer_checker.check(wav, sr, text, lang_p)
        if res_cer is not None and res_cer.get("cer") is not None:
            score.cer, score.hyp = float(res_cer["cer"]), res_cer.get("hyp")
            score.errors, score.checker = res_cer.get("errors"), str(res_cer.get("engine") or "")
            total -= self.w["cer"] * score.cer
            if score.cer > 0.3:
                issues.append(f"识别错字率 {score.cer:.0%}")
        score.issues = issues
        score.total = float(total)
        return score

    def _shape(self, wav: np.ndarray, sr: int, text: str) -> Tuple[Optional[float], Optional[float]]:
        """音调起伏（几项各是你平时的几个标准差，取平均）和频谱形状（每个频带差几个标准差，取平均）。量不出来是 None。"""
        from voicetwin.style import twin_profile as tp

        prosody = self.twin.get("prosody") or {}
        f0_ref = _num((prosody.get("f0_median_hz") or {}).get("value"))
        try:
            feat = tp.clip_features(wav, sr, text, f0_ref)
        except Exception:  # noqa: BLE001
            return None, None
        pz = None
        group = (prosody.get("groups") or {}).get(f"{feat.get('kind')}|{tp._en_bin(feat.get('en_ratio') or 0.0)}") or {}
        zs = []
        for name, st in (group.get("features") or {}).items():
            val, mean, sd = _num(feat.get(name)), _num((st or {}).get("mean")), _num((st or {}).get("sd"))
            if val is not None and mean is not None and sd:
                zs.append(abs(val - mean) / sd)
        if zs:
            pz = float(np.mean(zs))
        ld = None
        ltas = self.twin.get("ltas") or {}
        got = feat.get("ltas")
        if isinstance(got, list) and isinstance(ltas.get("mean"), list) and isinstance(ltas.get("sd"), list):
            ds = [abs(float(g) - float(m)) / float(s) for g, m, s in zip(got, ltas["mean"], ltas["sd"])
                  if _num(g) is not None and _num(m) is not None and _num(s)]
            if ds:
                ld = float(np.mean(ds))
        return pz, ld


# ============================================================================ 用显卡打分（可选）
def judge_on_gpu(judge: Any, device: str, clips: Sequence[Tuple[np.ndarray, int]],
                 free_gb: Optional[float] = None) -> Tuple[Any, str]:
    """「一模一样」的声纹模型能不能放到显卡上（judge_device: auto）。返回 (要用的打分器, 一句中文说明)。

    条件都满足才用显卡：有显卡版的 onnxruntime（CUDA）、合成引擎加载好以后显卡还空 ≥ 1.5 GB（nvidia-smi 量的）、
    3 段参考录音上显卡和处理器算出来的声纹余弦相似度都 ≥ 0.9999。有一条不满足（或出任何错）就照旧用处理器，
    永远不会因为这个出错。free_gb：测试时直接给空闲显存，不给就用 nvidia-smi 量。"""
    try:
        if judge is None or not getattr(judge, "precise", False):
            return judge, ""
        if str(device or "auto").lower() in ("cpu", "off", "false", "no", "0"):
            return judge, "声纹打分用处理器（设置里写了 judge_device: cpu）"
        from voicetwin.eval.speaker import JudgeMember, OnnxSVEncoder, SimilarityJudge, cosine

        try:
            import onnxruntime as ort
        except Exception:  # noqa: BLE001
            return judge, "声纹打分用处理器（没有 onnxruntime）"
        if "CUDAExecutionProvider" not in ort.get_available_providers():
            return judge, "声纹打分用处理器（onnxruntime 不是显卡版的）"
        if free_gb is None:
            from voicetwin.utils.gpu import _query_smi

            smi = _query_smi()
            gpus = (smi or {}).get("gpus") or []
            free_gb = gpus[0].get("free_gb") if gpus else None
        if free_gb is None:
            return judge, "声纹打分用处理器（量不出显卡还空多少显存）"
        if float(free_gb) < GPU_MIN_FREE_GB:
            return judge, f"声纹打分用处理器（显卡只空 {float(free_gb):.1f} GB，至少要 {GPU_MIN_FREE_GB} GB）"
        if not clips:
            return judge, "声纹打分用处理器（没有可以核对的参考录音）"
        members = []
        worst = 1.0
        for m in judge.members:
            enc = m.encoder
            if not isinstance(enc, OnnxSVEncoder):
                return judge, "声纹打分用处理器（有不能放到显卡上的模型）"
            gpu = OnnxSVEncoder(enc.spec, enc.path, enc._vad, device="cuda")
            providers = gpu._model.sess.get_providers()
            if not providers or providers[0] != "CUDAExecutionProvider":
                return judge, "声纹打分用处理器（显卡版的声纹模型没能加载）"
            for wav, sr in list(clips)[:3]:
                speech = enc.prepare(wav, sr)
                c = cosine(enc.embed_prepared(speech), gpu.embed_prepared(speech))
                worst = min(worst, c)
                if not c >= GPU_MIN_COSINE:
                    return judge, (f"声纹打分用处理器（显卡算出来的和处理器的不完全一样：余弦相似度 {c:.5f}，"
                                   f"要 ≥ {GPU_MIN_COSINE}）")
            members.append(JudgeMember(gpu, m.centroid, m.calib, m.cohort))
        return SimilarityJudge(members), (f"声纹打分用显卡（实测和处理器算出来的一样：余弦相似度最低 "
                                          f"{math.floor(worst * 100000) / 100000:.5f}）")
    except Exception as exc:  # noqa: BLE001 - 用显卡只是为了快：出任何错都照旧用处理器
        return judge, f"声纹打分用处理器（{(str(exc).splitlines() or [type(exc).__name__])[0][:120]}）"
