"""「一模一样」P5：每句话怎么找（research/一模一样/设计方案原文.md §1.5～§1.8、§2 P5，测试清单 §5.1）。

测的东西：
- 第 1 轮的组合按显卡分档；引擎不支持辅助参考时一样的组合只留一个；
- 读错太多才加更稳的设置、语速整体偏了 8% 以上才加改语速的组合；
- 请求按参考录音 / 辅助参考排在一起，每个版本的种子都不一样；
- 停下的规则（按顺序给分数）：试满至少的个数而且再试也不更好就停、一直变好就试满、不超过最多的个数、
  连着 2 次什么都没拿到就放弃；
- 生成线程：生成和打分同时进行（总时间比两样加起来短）、点停止两个线程都停、不留临时文件、生成线程里的错在主线程原样抛出；
- 两步打分：每种组合（包括第 1 轮以后加的更稳的设置）至少一个完整打分、每句最多 24 个；
- 「像你本人」那一项：几个模型说法不一致的分数排在后面、封顶在你自己录音的 p90、没有精准打分时和以前一样；
- 中英文分开查错字（假的识别模型）；没有 funasr 时和以前一样；
- 留下最好的 6 个：重新生成时最好的不会变差、标准变了时不用显卡重新排、清缓存时一起删掉；挑出来的那个一定留下；
  重新打分时人声几秒跟声纹一起沿用（真的 SimilarityJudge：短句子的分数一个数都不差）；只是排序权重变了时整篇也不启动合成引擎；
- 盲听测试当「真人」播放的录音不当参考（主参考、辅助参考）；
- 缓存键：设计里列的每一项变了都变，每次同时生成几个变了不变；
- 语速微调：真实 api_v2 上重发的请求只有 speed_factor 不一样；测试引擎上微调以后语速和目标差 3% 以内。
"""

import dataclasses
import json
import sys
import threading
import time
import zlib
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from conftest import make_cfg
from voicetwin.backends.base import SEED_STEP, SynthRequest
from voicetwin.eval import identical_judge as IJ
from voicetwin.eval.metrics import CERChecker, Score, Scorer
from voicetwin.project import Project
from voicetwin.synth import engine as eng
from voicetwin.synth import search as S
from voicetwin.synth.script import ScriptSegment
from voicetwin.utils.audio import speech_activity

SR = 16000
_REFS = [
    {"id": "r1", "path": "references/a.wav", "text": "我们今天先来看第一个例子，大家注意听。", "lang": "zh", "kind": "statement",
     "source": "v1", "duration": 6.0, "score": 2.9},
    {"id": "r2", "path": "references/b.wav", "text": "这个关系代词相对来说比较特殊，大家要注意。", "lang": "zh",
     "kind": "statement", "source": "v2", "duration": 5.5, "score": 2.8},
    {"id": "r3", "path": "references/c.wav", "text": "好，这就是今天要讲的全部内容了。", "lang": "zh", "kind": "statement",
     "source": "v3", "duration": 5.0, "score": 2.5},
    {"id": "r4", "path": "references/d.wav", "text": "接下来我们再看一个稍微复杂一点的例子。", "lang": "zh",
     "kind": "statement", "source": "v1", "duration": 6.5, "score": 2.4},
    {"id": "r5", "path": "references/e.wav", "text": "大家想一想，这道题应该怎么做呢？", "lang": "zh", "kind": "question",
     "source": "v2", "duration": 4.5, "score": 3.0},
]
TEXT = "今天我们来学习列表推导式，它可以让代码更简洁。"


# ============================================================================ 假的引擎和打分器
def _tone(seed: int, text: str, speed: float, sr: int = SR) -> np.ndarray:
    """按种子不一样的「声音」：长度按字数和语速，频率按种子（16 位整数存，读回来一个数都不差）。"""
    rng = np.random.default_rng(seed % (2 ** 32))
    dur = max(0.8, len(text) * 0.18 / max(speed, 0.1))
    t = np.arange(int(dur * sr)) / sr
    f = 120.0 + float(rng.uniform(0, 80))
    x = 0.3 * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))
    lead = np.zeros(int(0.1 * sr))
    return np.concatenate([lead, x, np.zeros(int(0.3 * sr))]).astype(np.float32)


class FakeBackend:
    """只给「一模一样」的搜索用的假引擎：记下每次请求，一次要 n 个就写 n 个文件（不同的种子）。"""

    name = "dummy"
    display_name = "测试"
    supports_aux_refs = True
    supports_batch = False
    bcfg: dict = {}

    def __init__(self, delay: float = 0.0, empty: bool = False, fail: BaseException = None, model: str = "fake-model"):
        self.calls = []
        self.delay = delay
        self.empty = empty
        self.fail = fail
        self.model = model
        self.synth_seconds = 0.0
        self.release_gpu_callback = None

    def model_id(self):
        return self.model

    def speed_calibration(self):
        return {"zh": 1.0, "en": 1.0}

    def start(self):
        pass

    def stop(self):
        pass

    def synthesize_many(self, req, n, out_dir):
        t0 = time.monotonic()
        self.calls.append((dataclasses.replace(req), int(n)))
        if self.delay:
            time.sleep(self.delay)
        if self.fail is not None:
            raise self.fail
        out = []
        if not self.empty:
            for k in range(int(n)):
                path = Path(out_dir) / f"f{len(self.calls)}_{k}.wav"
                sf.write(str(path), _tone(req.seed + k * SEED_STEP, req.text, req.speed), SR, subtype="PCM_16")
                out.append((path, k))
        self.synth_seconds += time.monotonic() - t0
        return out


def _fingerprint(wav) -> float:
    return (zlib.crc32(np.asarray(wav, dtype=np.float32).tobytes()) % 1000) / 1000.0


class FakeScorer:
    """假的打分器。totals：按顺序给每个版本的综合分（用完后一直是最后一个）；不给时按声音本身算一个固定的数
    （同一段声音存下来再读回来，分数一个数都不差）。ratio：说话时长 / 应该说的时长。"""

    def __init__(self, totals=None, cer=0.0, ratio=None, delay=0.0, expected=None):
        self.totals = list(totals) if totals is not None else None
        self.i = 0
        self.by = {}
        self.cer = cer
        self.ratio = ratio
        self.delay = delay
        self.expected_fixed = expected
        self.quick_n = 0
        self.full_n = 0
        self.score_seconds = 0.0

    def _total(self, wav):
        if self.totals is None:
            return _fingerprint(wav)
        t = self.totals[min(self.i, len(self.totals) - 1)]
        self.i += 1
        return float(t)

    def prepare(self, wav, sr):
        return None

    def quick(self, wav, sr, text, lang, mult=1.0):
        t0 = time.monotonic()
        if self.delay:
            time.sleep(self.delay)
        self.quick_n += 1
        t = self._total(wav)
        self.by[id(wav)] = t
        voiced, _ = speech_activity(wav, sr)
        self.score_seconds += time.monotonic() - t0
        return IJ.QuickScore(total=t, pct_raw=None, voiced=voiced, expected=None, dur_dev=None, gate_ok=True)

    def full(self, wav, sr, text, lang, mult=1.0, prepared=None, use_asr=True, cer=None):
        t0 = time.monotonic()
        if self.delay:
            time.sleep(self.delay)
        self.full_n += 1
        t = self.by.get(id(wav))
        if t is None:
            t = self._total(wav) if self.totals is None else float(self.totals[-1])
        voiced, _ = speech_activity(wav, sr)
        if self.expected_fixed is not None:
            exp = self.expected_fixed(voiced) if callable(self.expected_fixed) else float(self.expected_fixed)
        else:
            exp = voiced / self.ratio if self.ratio else None
        c = (cer or {}).get("cer", self.cer if use_asr else None)
        self.score_seconds += time.monotonic() - t0
        return Score(total=float(t), cer=c, errors=None if c is None else (0 if c == 0 else 5), voiced=voiced,
                     expected=exp, stage="full", checker="fake")

    def in_normal_range(self, s, lang, speed=1.0):
        return True

    def timbre_term(self, s):
        return 0.0

    def non_timbre(self, s):
        return s.total

    def resid_sd(self):
        return None


def _project(tmp_path, name="搜索", cfg=None):
    cfg = cfg or make_cfg(tmp_path / "ws")
    project = Project(cfg, name)
    project.root.mkdir(parents=True, exist_ok=True)
    project.refs_dir.mkdir(parents=True, exist_ok=True)
    for r in _REFS:
        sf.write(str(project.abspath(r["path"])), _tone(len(r["id"]), r["text"], 1.0), SR, subtype="PCM_16")
    project.references_path.write_text(json.dumps(_REFS, ensure_ascii=False), encoding="utf-8")
    return cfg, project


def _ctx(project, block=None, twin=None):
    pool = S.pool_from_refs(project.load_references())
    block = block or {}
    return {"twin": twin or {}, "bank": None, "pool": pool, "bank_sig": S.pool_signature(pool),
            "prior": S.prior_scores(pool, block.get("ref_prior")),
            "prior_version": str(block.get("ref_prior_version") or "") if block.get("ref_prior") else "",
            "weights": block.get("weights") or {}, "weights_version": str(block.get("weights_version") or "default"),
            "block": block, "profile_sig": "twin-a"}


def _narrator(tmp_path, tier="none", scorer=None, backend=None, cfg=None, use_asr=False, name="搜索", **kw):
    cfg, project = _project(tmp_path, name=name, cfg=cfg)
    backend = backend or FakeBackend()
    n = eng.Narrator(cfg, project, backend, quality="identical", tier=tier, **kw)
    n._identical = _ctx(project)
    n._scorer = scorer or FakeScorer()
    n._judge = None
    n.use_asr = use_asr
    n._started = True
    return n, backend


def _seg(text=TEXT, index=0, lang="zh", kind="statement", pause_after="sentence"):
    return ScriptSegment(text=text, display=text, lang=lang, kind=kind, index=index, pause_after=pause_after)


def _limits(**kw):
    """synth.tiers.identical 里改每句至少 / 最多试几个、每批几个（测试用小一点的数）。"""
    return {"tiers": {"identical": kw}}


# ============================================================================ 组合
def test_arm_planning_per_tier():
    refs = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    aux = {"a": [{"id": 1}, {"id": 2}, {"id": 3}], "b": [{"id": 1}, {"id": 2}, {"id": 3}],
           "c": [{"id": 1}, {"id": 2}, {"id": 3}]}
    want_mid = [S.Arm("a", 0, 3), S.Arm("a", 1, 3), S.Arm("a", 0, 0), S.Arm("b", 0, 3), S.Arm("b", 1, 3),
                S.Arm("c", 0, 3)]
    assert S.plan_arms("high", refs, aux) == want_mid and S.plan_arms("mid", refs, aux) == want_mid
    assert S.plan_arms("low", refs[:2], aux) == want_mid[:5]
    assert S.plan_arms("none", refs[:2], aux) == [S.Arm("a", 0, 3), S.Arm("a", 1, 3), S.Arm("b", 0, 3)]
    # 小显存只配 2 条辅助参考：组合里就写 2
    aux2 = {k: v[:2] for k, v in aux.items()}
    assert S.plan_arms("low", refs[:2], aux2)[0] == S.Arm("a", 0, 2)
    # 引擎不支持辅助参考（没有辅助参考）：A1 和 A3 一样，只留一个
    none = {"a": [], "b": [], "c": []}
    assert S.plan_arms("mid", refs, none) == [S.Arm("a", 0, 0), S.Arm("a", 1, 0), S.Arm("b", 0, 0), S.Arm("b", 1, 0),
                                              S.Arm("c", 0, 0)]


def test_dummy_backend_plan_dedups_aux_arms(prepared, tmp_path):
    """真的测试引擎（不支持辅助参考）：第 1 轮没有重复的组合，参考录音来自参考录音库。"""
    from voicetwin.backends.base import get_backend

    cfg, project, _ = prepared
    n = eng.Narrator(cfg, project, get_backend("dummy", cfg, project), quality="identical", tier="mid")
    plan = n._plan(_seg("今天我们讲第一课的第一个例子，大家注意看。"))
    assert len(plan.refs) == 3 and all(a.aux_n == 0 for a in plan.arms)
    assert len(plan.arms) == len(set(plan.arms)) == 5
    assert plan.ref["id"] == plan.refs[0]["id"] and plan.pool_key and plan.pool_key != plan.key
    assert any(e.get("_bank") for e in n._identical_ctx()["pool"])  # 用的是参考录音库


def test_shortlist_rules():
    pool = S.pool_from_refs(_REFS)
    prior = S.prior_scores(pool)
    seg = _seg()
    picks = S.shortlist_refs(seg, pool, prior, 3)
    assert len(picks) == 3 and len({p["id"] for p in picks}) == 3
    assert picks[1]["source"] != picks[0]["source"]  # 第二条来自别的视频
    # 和这句话文字一样的录音不用
    same = _seg(_REFS[0]["text"])
    assert all(p["id"] != "r1" for p in S.shortlist_refs(same, pool, prior, 3))
    # 问句：最后一段用问句的参考；一句长话前面几段（pause_after = clause）按陈述句
    q = _seg("大家觉得这个例子应该怎么改呢？", kind="question")
    assert S.shortlist_refs(q, pool, prior, 2)[0]["id"] == "r5"
    q_mid = _seg("大家觉得这个例子应该怎么改呢？", kind="question", pause_after="clause")
    assert S.shortlist_refs(q_mid, pool, prior, 2)[0]["id"] != "r5"
    # 英文占 15% 以上：至少一条参考里英文也占 15% 以上
    en_ref = {"id": "r6", "path": "references/f.wav", "text": "比如 This is an example sentence 就是这样。", "lang": "zh",
              "kind": "statement", "source": "v9", "score": -5.0}
    pool2 = S.pool_from_refs(_REFS + [en_ref])
    mixed = _seg("比如 This is a very long English example sentence used here.")
    got = S.shortlist_refs(mixed, pool2, S.prior_scores(pool2), 2)
    assert any(p["id"] == "r6" for p in got)
    # 老师自己指定的参考：只用它
    assert S.shortlist_refs(seg, pool, prior, 3, forced=pool[3]) == [pool[3]]
    # 辅助参考：同语言、陈述句、别的视频、不是主参考
    aux = S.aux_set(pool[0], pool, prior, 3)
    assert aux and all(a["id"] != "r1" and a["source"] != "v1" and a["kind"] == "statement" for a in aux)


# ============================================================================ 加组合
def test_rescue_arms_only_after_cer_failures(tmp_path):
    n, b = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0], cer=0.5), use_asr=True)
    seg = _seg()
    plan = n._plan(seg)
    out = n._search_obj().run(seg, plan)
    presets = [c.arm.preset_idx for c in out.cands]
    assert S.RESCUE in presets
    rescue_calls = [r for r, _ in b.calls if r.temperature == 0.6 and r.top_p == 0.8]
    assert rescue_calls and {Path(r.ref_audio).name for r in rescue_calls} <= {"a.wav", "b.wav", "c.wav", "d.wav",
                                                                               "e.wav"}
    # 读对了：不加更稳的设置
    n2, b2 = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0], cer=0.0), use_asr=True, name="搜索2")
    out2 = n2._search_obj().run(seg, n2._plan(seg))
    assert S.RESCUE not in [c.arm.preset_idx for c in out2.cands]
    assert not [r for r, _ in b2.calls if r.temperature == 0.6]


def test_speed_arm_only_when_durations_are_off(tmp_path):
    n, b = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0], ratio=1.15))
    seg = _seg()
    out = n._search_obj().run(seg, n._plan(seg))
    mults = {c.arm.speed_mult for c in out.cands}
    assert 1.1 in mults  # 说得慢了 15%：语速 × 1.1（最多改 10%）
    assert any(abs(r.speed - 1.1) < 1e-9 for r, _ in b.calls)
    n2, b2 = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0], ratio=1.05), name="搜索2")
    out2 = n2._search_obj().run(seg, n2._plan(seg))
    assert {c.arm.speed_mult for c in out2.cands} == {1.0}  # 差 5%：不加


# ============================================================================ 请求的顺序和种子
def test_requests_grouped_and_seeds_unique(tmp_path):
    cfg = make_cfg(tmp_path / "ws", synth=_limits(batch=2, min_candidates=12, max_candidates=20))
    n, b = _narrator(tmp_path, tier="mid", cfg=cfg, scorer=FakeScorer(totals=[1.0]))
    seg = _seg(index=3)
    plan = n._plan(seg)
    out = n._search_obj().run(seg, plan)
    first = [(Path(r.ref_audio).name, len(r.aux_refs)) for r, _ in b.calls[:len(plan.arms)]]
    groups = [g for k, g in enumerate(first) if k == 0 or g != first[k - 1]]
    assert len(groups) == len(set(groups))  # 同一条参考、同样的辅助参考的请求都排在一起
    runs = [g[0] for k, g in enumerate(groups) if k == 0 or g[0] != groups[k - 1][0]]
    assert len(runs) == len(set(runs)) == len(plan.refs)  # 每条参考录音的请求连在一起
    seeds = [c.seed for c in out.cands]
    assert len(seeds) == len(set(seeds)) == out.tries
    # 第 j 次请求的种子 = 基础种子 + 第几句 × 7919 + j × 每批最多几个 × 104729
    base = n.base_seed + 3 * 7919
    assert [r.seed for r, _ in b.calls] == [base + j * n.n_candidates * SEED_STEP for j in range(len(b.calls))]


# ============================================================================ 停下的规则
def test_stops_exactly_at_min_with_plateau(tmp_path):
    n, b = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0]))  # 没有 N 卡：每批 1 个、至少 6 个、最多 12 个
    seg = _seg()
    out = n._search_obj().run(seg, n._plan(seg))
    assert out.tries == 6 and len(b.calls) == 6 and out.met and out.stats["stop"] == "target"


def test_continues_while_improving_and_respects_cap(tmp_path):
    n, b = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0 + 0.05 * i for i in range(40)]))
    seg = _seg()
    out = n._search_obj().run(seg, n._plan(seg))
    assert out.tries == 12 and out.stats["stop"] == "max"
    # 前 3 个越来越好、之后不变：第 3 个之后再试 8 个才算「再试也不更好」
    n2, _ = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0, 1.1, 1.2]), name="搜索2")
    assert n2._search_obj().run(seg, n2._plan(seg)).tries == 11
    # 命令行 -n 5：一共只试 5 个（第 1 轮每种组合至少 1 个）
    n3, b3 = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0 + 0.1 * i for i in range(40)]), name="搜索3",
                       candidates=5)
    out3 = n3._search_obj().run(seg, n3._plan(seg))
    assert out3.tries == 5 and sum(k for _, k in b3.calls) == 5


def test_gives_up_after_two_empty_requests(tmp_path):
    n, b = _narrator(tmp_path, backend=FakeBackend(empty=True))
    seg = _seg()
    with pytest.raises(RuntimeError, match="第 1 句没能生成"):
        n._search_obj().run(seg, n._plan(seg))
    assert len(b.calls) == 2
    # 生成出错（不是「重试也没用」的那种）：也是 2 次就放弃
    n2, b2 = _narrator(tmp_path, backend=FakeBackend(fail=RuntimeError("偶然的错误 abc")), name="搜索2")
    with pytest.raises(RuntimeError, match="没能生成") as ei:
        n2._search_obj().run(seg, n2._plan(seg))
    assert len(b2.calls) == 2 and "偶然的错误 abc" in str(ei.value.__cause__)
    # 「重试也没用」的错误（显存不够减到 1 个也不够）：马上停
    n3, b3 = _narrator(tmp_path, backend=FakeBackend(fail=RuntimeError("CUDA out of memory. Tried to allocate")),
                       name="搜索3")
    with pytest.raises(RuntimeError, match="没能生成"):
        n3._search_obj().run(seg, n3._plan(seg))
    assert len(b3.calls) == 1


class FlakyBackend(FakeBackend):
    """前 ok 次请求正常，之后一直出错（不是「重试也没用」的那种）。"""

    def __init__(self, ok, **kw):
        super().__init__(**kw)
        self.ok = ok

    def synthesize_many(self, req, n, out_dir):
        if len(self.calls) >= self.ok:
            self.calls.append((dataclasses.replace(req), int(n)))
            raise RuntimeError("偶然的错误")
        return super().synthesize_many(req, n, out_dir)


def test_keeps_the_best_when_later_requests_keep_failing(tmp_path):
    """已经有版本了、后面的请求却一直出错：不会一直试下去，连着 4 次以后用已经有的里面最好的。"""
    n, b = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0 + 0.1 * i for i in range(10)]),
                     backend=FlakyBackend(ok=3))
    seg = _seg()
    out = n._search_obj().run(seg, n._plan(seg))
    assert out.tries == 3 and out.stats["stop"] == "errors" and len(b.calls) == 3 + 4
    assert out.best.total == pytest.approx(1.2)


def test_stop_needs_the_search_target_on_the_best(tmp_path):
    """挑出来的那个读错了（错字检查没通过）：没达到继续找的目标，一直试到最多。"""
    n, b = _narrator(tmp_path, scorer=FakeScorer(totals=[1.0], cer=0.5), use_asr=True)
    seg = _seg()
    out = n._search_obj().run(seg, n._plan(seg))
    assert out.tries == 12 and not out.met


# ============================================================================ 生成线程
def test_pipeline_overlaps_synthesis_and_scoring(tmp_path):
    cfg = make_cfg(tmp_path / "ws", synth=_limits(batch=2, min_candidates=12, max_candidates=12))
    sc = FakeScorer(totals=[1.0], delay=0.04)
    n, b = _narrator(tmp_path, tier="mid", cfg=cfg, scorer=sc, backend=FakeBackend(delay=0.25))
    seg = _seg()
    search = n._search_obj()
    assert search.pipeline_on()
    t0 = time.monotonic()
    out = search.run(seg, n._plan(seg))
    wall = time.monotonic() - t0
    assert out.stats["pipeline"] is True and out.tries == 12
    assert wall < 0.9 * (b.synth_seconds + sc.score_seconds), (wall, b.synth_seconds, sc.score_seconds)
    # 没有 N 卡：不开生成线程
    n2, _ = _narrator(tmp_path, tier="none", name="搜索2")
    assert not n2._search_obj().pipeline_on()


def test_cancel_stops_both_threads_and_leaves_no_tmp_files(tmp_path):
    from voicetwin.utils.progress import TaskCancelled, clear_cancel, request_cancel

    cfg = make_cfg(tmp_path / "ws", synth=_limits(batch=2, min_candidates=40, max_candidates=64))
    n, b = _narrator(tmp_path, tier="mid", cfg=cfg, backend=FakeBackend(delay=0.15))
    seg = _seg()
    plan = n._plan(seg)
    clear_cancel()
    timer = threading.Timer(0.4, request_cancel)
    timer.start()
    try:
        with pytest.raises(TaskCancelled):
            n._search_obj().run(seg, plan)
    finally:
        timer.cancel()
        clear_cancel()
    assert not any(t.name == "vt-identical-gen" and t.is_alive() for t in threading.enumerate())
    tmp = n.project.cache_dir / "tmp"
    assert not tmp.exists() or not any(tmp.iterdir())
    n_calls = len(b.calls)
    time.sleep(0.3)
    assert len(b.calls) == n_calls  # 停了以后不再发请求


def test_producer_exception_is_reraised_with_the_same_message():
    def work(job):
        raise ValueError(f"生成线程里的错 {job}")

    p = S._Producer(work)
    p.start()
    p.submit(7)
    with pytest.raises(ValueError, match="^生成线程里的错 7$"):
        p.get()
    p.close()
    assert not p.is_alive()


def test_producer_cancel_inside_the_thread_reaches_the_main_thread(tmp_path):
    from voicetwin.utils.progress import TaskCancelled

    cfg = make_cfg(tmp_path / "ws", synth=_limits(batch=2, min_candidates=12, max_candidates=12))
    n, b = _narrator(tmp_path, tier="mid", cfg=cfg, backend=FakeBackend(fail=TaskCancelled("已按你的要求停止")))
    seg = _seg()
    with pytest.raises(TaskCancelled, match="已按你的要求停止"):
        n._search_obj().run(seg, n._plan(seg))
    assert len(b.calls) == 1


# ============================================================================ 两步打分
def test_cascade_limits(tmp_path):
    # 一般的显卡：每批 8 个，第 1 轮 6 种组合 × 8 = 48 个，再第 2 轮 → 一共 64 个（分数一直变好：试满）
    sc = FakeScorer(totals=list(np.linspace(0.0, 1.0, 64)))
    n, b = _narrator(tmp_path, tier="mid", scorer=sc)
    seg = _seg()
    plan = n._plan(seg)
    search = n._search_obj()
    out = search.run(seg, plan)
    assert out.tries == 64 and len(plan.arms) == 6
    full = [c for c in search.cands if c.score is not None]
    assert len(full) == 24 and sc.full_n == 24  # 名额用满，不超过
    for arm in {c.arm for c in search.cands}:  # 每种组合（后出场的也一样）至少一个完整打分
        assert any(c.score is not None for c in search.cands if c.arm == arm), arm
    # 前几次请求时快速分前 12 名都完整打了分
    first = [c for c in search.cands if c.req_no == 0]
    assert all(c.score is not None for c in first)
    # 每个版本都读错 → 第 1 轮以后加 2 种更稳的设置：后出场的那种也要有完整打分的名额（审查发现：
    # 以前决定加组合时就不再给它们留名额，第一种加的把 24 个用完，第二种一个都没有，读对的版本也挑不出来）
    sc2 = FakeScorer(totals=list(np.linspace(0.0, 1.0, 64)), cer=0.5)
    n2, _ = _narrator(tmp_path, tier="mid", scorer=sc2, use_asr=True, name="搜索2")
    plan2 = n2._plan(seg)
    s2 = n2._search_obj()
    s2.run(seg, plan2)
    arms2 = list(dict.fromkeys(c.arm for c in s2.cands))
    assert len([a for a in arms2 if a.preset_idx == S.RESCUE]) == 2
    for arm in arms2:
        assert any(c.score is not None for c in s2.cands if c.arm == arm), arm.label(plan2.refs)
    assert s2.n_full <= 24 and sc2.full_n == s2.n_full


# ============================================================================ 「像你本人」那一项
class _Member:
    def __init__(self, name, g10, g90):
        self.name = name
        self._g = {"g10": g10, "g90": g90}

    def natural_pct(self, key):
        return self._g.get(key)


class _PreciseJudge:
    available = reliable = calibrated = precise = True

    def __init__(self):
        self.members = [_Member("a", 85.0, 110.0), _Member("eres2net-base-zh", 84.0, 111.0)]

    def natural_range(self):
        return {"p10": 85.0, "p25": 92.0, "p50": 100.0, "p90": 110.0}

    def member(self, name):
        return next((m for m in self.members if m.name == name), None)


class _PlainJudge:
    available = reliable = calibrated = True
    precise = False
    members: list = []

    def __init__(self, res):
        self.res = res

    def natural_range(self):
        return None

    def judge(self, wav, sr):
        return dict(self.res)


def test_timbre_term_ranking_cap_and_fallback():
    w = {"speaker": 2.0, "cer": 1.0, "rate": 0.4, "pitch": 0.2}
    sc = IJ.IdenticalScorer({}, None, None, w, judge=_PreciseJudge())
    assert sc.precise and sc.cap == 110.0
    shaky = sc.timbre_term(Score(total=0, pct_raw=130.0, spread=20.0))
    steady = sc.timbre_term(Score(total=0, pct_raw=105.0, spread=2.0))
    assert shaky < steady  # 几个模型说法差很多的 130% 排在一致的 105% 后面
    # 封顶在你自己录音的 p90（110%）：再高也不加分
    assert sc.timbre_term(Score(total=0, pct_raw=200.0, spread=0.0)) == sc.timbre_term(
        Score(total=0, pct_raw=110.0, spread=0.0)) == pytest.approx(2.2)
    # 每个模型都不低于它自己给你真实录音打的 p10
    assert sc.member_floor_ok(Score(total=0, pcts={"a": 90.0, "eres2net-base-zh": 86.0}))
    assert not sc.member_floor_ok(Score(total=0, pcts={"a": 90.0, "eres2net-base-zh": 80.0}))
    # 没有精准打分：和以前（Scorer.score）加的那一项完全一样
    x = (0.3 * np.sin(2 * np.pi * 150 * np.arange(2 * SR) / SR)).astype(np.float32)
    for res in ({"pct": 97.0, "pct_raw": 97.0}, {"pct": 100.0, "pct_raw": 160.0}, {"pct": 88.0}, {"sim": 0.83}):
        full = {"pct": None, "pct_raw": None, "pcts": {}, "sims": {}, "sim": None, "seconds": None, **res}
        empty = {"pct": None, "pct_raw": None, "pcts": {}, "sims": {}, "sim": None, "seconds": None}
        today = Scorer({}, None, None, w, judge=_PlainJudge(full)).score(x, SR, "你好你好", "zh", use_asr=False).total \
            - Scorer({}, None, None, w, judge=_PlainJudge(empty)).score(x, SR, "你好你好", "zh", use_asr=False).total
        plain = IJ.IdenticalScorer({}, None, None, w, judge=_PlainJudge(full))
        s = Score(total=0, pct=full["pct"], pct_raw=full["pct_raw"], speaker_sim=full["sim"])
        assert not plain.precise and plain.timbre_term(s) == pytest.approx(today), res


def test_full_score_terms():
    """完整打分：时长偏差按语速模型、句中停顿超过你自己的 p97 才算异常。"""
    twin = {"duration_model": {"ok": True, "coef": {"const": 0.0, "n_cjk": 0.25, "en_syllables": 0.2, "n_digits": 0.3,
                                                     "n_clause_punct": 0.0}, "resid_sd_log": 0.1},
            "inner_pause_p97": {"value": 0.6, "n": 30}}
    sc = IJ.IdenticalScorer({}, None, None, {"speaker": 2.0, "cer": 1.0, "rate": 0.4, "pitch": 0.2}, twin=twin)
    text = "今天我们学习列表推导式"  # 11 个汉字 → 应该说 2.75 秒
    assert sc.expected(text) == pytest.approx(2.75)
    sr = SR
    t = np.arange(int(2.75 * sr)) / sr
    voice = (0.3 * np.sin(2 * np.pi * 150 * t)).astype(np.float32)
    gap = np.zeros(int(0.8 * sr), np.float32)
    wav = np.concatenate([np.zeros(int(0.2 * sr), np.float32), voice[: len(voice) // 2], gap,
                          voice[len(voice) // 2:], np.zeros(int(0.3 * sr), np.float32)])
    s = sc.full(wav, sr, text, "zh", use_asr=False)
    assert s.expected == pytest.approx(2.75) and s.dur_dev < 0.05 and abs(s.dur_z) < 0.5
    assert any("异常停顿" in x for x in s.issues)  # 0.8 秒 > 你自己的 p97（0.6 秒）
    q = sc.quick(wav, sr, text, "zh")
    assert q.gate_ok  # 快速检查按 max(1.2, p97)
    # 说得太快（只有应该的一半）：快速检查不过
    q2 = sc.quick(np.concatenate([voice[: len(voice) // 2], np.zeros(int(0.3 * sr), np.float32)]), sr, text, "zh")
    assert not q2.gate_ok and q2.total < -5
    # 快慢倍数 1.25：应该说的时长按倍数缩短
    assert sc.full(wav, sr, text, "zh", mult=1.25, use_asr=False).expected == pytest.approx(2.2)


def test_gpu_judge_never_fails_without_cuda(monkeypatch):
    judge = _PreciseJudge()
    clips = [(np.zeros(SR, np.float32), SR)]
    got, note = IJ.judge_on_gpu(judge, "auto", clips)
    assert got is judge and "处理器" in note
    assert IJ.judge_on_gpu(judge, "cpu", clips)[0] is judge
    assert IJ.judge_on_gpu(None, "auto", clips) == (None, "")
    import types

    ort = types.ModuleType("onnxruntime")  # 假装有显卡版的 onnxruntime（这台机器上没有显卡）
    ort.get_available_providers = lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"]
    monkeypatch.setitem(sys.modules, "onnxruntime", ort)
    got, note = IJ.judge_on_gpu(judge, "auto", clips, free_gb=1.0)
    assert got is judge and "1.0 GB" in note

    class Sess:
        def __init__(self, providers):
            self._p = providers

        def get_providers(self):
            return self._p

    class FakeEnc:
        def __init__(self, spec, path, vad, device="cpu"):
            self.spec, self.path, self._vad, self.device = spec, path, vad, device
            self.name = "fake-sv"
            self._model = type("M", (), {"sess": Sess(["CUDAExecutionProvider" if device == "cuda" else "CPU"])})()

        def prepare(self, wav, sr):
            return wav

        def embed_prepared(self, speech):
            v = np.ones(8, np.float32)
            if self.device == "cuda" and FakeEnc.drift:
                v[0] += 0.5
            return v / np.linalg.norm(v)

    from voicetwin.eval import speaker as SP

    monkeypatch.setattr(SP, "OnnxSVEncoder", FakeEnc)
    cen = np.ones(8, np.float32)
    real = SP.SimilarityJudge([SP.JudgeMember(FakeEnc("s", "p", None), cen, {"g50": 2.0, "i0": 0.0, "norm": "asnorm"},
                                              {"emb": np.ones((2, 8), np.float32)})])
    FakeEnc.drift = True
    got, note = IJ.judge_on_gpu(real, "auto", clips, free_gb=4.0)
    assert got is real and "不完全一样" in note
    FakeEnc.drift = False
    got, note = IJ.judge_on_gpu(real, "auto", clips, free_gb=4.0)
    assert got is not real and got.members[0].encoder.device == "cuda" and "声纹打分用显卡" in note
    assert real.precise and got.precise and got.signature() == real.signature()  # 打分标准不变


# ============================================================================ 中英文分开查错字
class _FakePara:
    pass


def _mixed_checker(monkeypatch, para_text, whisper_text, funasr=True):
    from voicetwin.eval import metrics

    c = CERChecker("auto")
    monkeypatch.setattr(metrics, "_has_module", lambda mod: funasr if mod == "funasr" else True)
    c._para = _FakePara()
    c._model = type("W", (), {"transcribe": lambda self, wav, language="zh": type("R", (), {"text": whisper_text})()})()
    monkeypatch.setattr(CERChecker, "_paraformer_text", lambda self, wav16: para_text)
    return c


def test_mixed_cer_with_fake_transcribers(monkeypatch):
    wav = np.zeros(SR, np.float32)
    text = "我们用Python写一个小程序。"
    # Paraformer 把 Python 写成「派森」（多出来的字不算错），Whisper 听出了 Python
    c = _mixed_checker(monkeypatch, "我们用派森写一个小程序", "我们用Python写一个小程序")
    r = c.check_mixed(wav, SR, text)
    assert r["errors"] == 0 and r["cer"] == 0.0 and r["engine"] == "paraformer+whisper" and r["strong"]
    from voicetwin.eval.metrics import engine_is_strong

    assert engine_is_strong(r["engine"])
    # 漏了英文单词：错 1 个
    c = _mixed_checker(monkeypatch, "我们用写一个小程序", "我们用写一个小程序")
    r = c.check_mixed(wav, SR, text)
    assert r["errors"] == 1 and r["errors_en"] == 1 and r["errors_cjk"] == 0
    assert r["cer"] == pytest.approx(1 / (9 + 1))
    # 漏了一个汉字：错 1 个
    c = _mixed_checker(monkeypatch, "我们用派森写一个程序", "我们用Python写一个程序")
    r = c.check_mixed(wav, SR, text)
    assert r["errors"] == 1 and r["errors_cjk"] == 1
    # 没有 funasr：和以前一样（check）
    c = _mixed_checker(monkeypatch, "x", "y", funasr=False)
    seen = []
    monkeypatch.setattr(CERChecker, "check", lambda self, w, s, t, lang: seen.append(lang) or {"cer": 0.0})
    assert c.check_mixed(wav, SR, text) == {"cer": 0.0} and seen == ["zh"]
    # 纯中文 / 纯英文：和 check 一样
    c = _mixed_checker(monkeypatch, "x", "y")
    seen.clear()
    c.check_mixed(wav, SR, "我们今天上课。")
    c.check_mixed(wav, SR, "We can add a condition.")
    assert seen == ["zh", "en"]


# ============================================================================ 留下来的版本
def test_top_k_store_redo_and_rerank_without_synthesis(tmp_path):
    from voicetwin.synth.search import load_candidates, store_dir

    n, b = _narrator(tmp_path, scorer=FakeScorer())
    seg = _seg()
    res = n.synthesize_segment(seg)
    plan = n._plan(seg)
    folder = store_dir(n.project.cache_dir, plan.pool_key)
    files = sorted(p.name for p in folder.glob("*.flac"))
    assert 1 <= len(files) <= 6 and (folder / "cands.json").exists()
    stored = load_candidates(folder)
    best_total = max(it["score"]["total"] for it in stored)
    assert res.score["total"] == pytest.approx(best_total)
    # 重新生成（换了种子）：以前留下的一起比，最好的不会变差
    for _ in range(3):
        n._scorer = FakeScorer()
        r2 = n.synthesize_segment(seg, force=True)
        assert r2.score["total"] >= best_total - 1e-9
        best_total = max(best_total, r2.score["total"])
        assert len(list(folder.glob("*.flac"))) <= 6
    # 打分标准、说话习惯、排序权重变了：不用生成，按新标准从留下的里面重新挑
    calls = len(b.calls)
    n._scorer = FakeScorer()
    n._identical["profile_sig"] = "twin-b"
    r3 = n.synthesize_segment(seg)
    assert len(b.calls) == calls and r3.cached
    n._scorer = FakeScorer()
    orig = n._judge_sig
    n._judge_sig = lambda: "another-judge"
    r4 = n.synthesize_segment(seg)
    n._judge_sig = orig
    assert len(b.calls) == calls and r4.cached
    n._scorer = FakeScorer()
    n._identical["weights_version"] = "w2"  # 权重变了：缓存键也变了，但同样的设置留下的版本还在
    plan2 = n._plan(seg)
    assert plan2.key != plan.key and plan2.pool_key == plan.pool_key
    r5 = n.synthesize_segment(seg)
    assert len(b.calls) == calls and r5.cached and plan2.meta_path.exists()
    meta = json.loads(plan2.meta_path.read_text(encoding="utf-8"))
    assert meta["weights_version"] == "w2" and meta["profile_sig"] == "twin-b"
    # 清缓存：留下来的版本一起删掉
    eng.clear_cache(n.project)
    assert not folder.exists()


_DIM = 16
_CEN = np.ones(_DIM, np.float32) / np.sqrt(_DIM)


class _VadEncoder:
    """假的精准声纹模型：和 OnnxSVEncoder 一样先做人声检测（这里是去掉静音）、再算声纹；同一段人声永远同一个声纹。"""
    name = "eres2net-base-zh"
    reliable = True
    prep_key = ("speech16k", 1)

    def __init__(self):
        self.prepares = 0

    def prepare(self, wav, sr):
        from voicetwin.utils.audio import resample

        self.prepares += 1
        w = resample(np.asarray(wav, np.float32), sr, 16000)
        return w[np.abs(w) > 1e-4]

    def embed_prepared(self, speech):
        rng = np.random.default_rng(zlib.crc32(np.asarray(speech, np.float32).tobytes()))
        v = _CEN + 0.15 * rng.normal(size=_DIM).astype(np.float32)
        return (v / np.linalg.norm(v)).astype(np.float32)

    def embed(self, wav, sr):
        return self.embed_prepared(self.prepare(wav, sr))


def _vad_judge():
    """真的 SimilarityJudge（两头校准、陌生人声纹库）；校准里有短句子的标准（g50_short：人声 1.5 秒时「100%」低一些）。"""
    from voicetwin.eval import speaker as SP

    cohort = {"emb": np.random.default_rng(0).normal(size=(50, _DIM)).astype(np.float32)}
    calib = {"norm": "asnorm", "g10": 2.2, "g25": 2.6, "g50": 3.0, "g90": 3.6, "i0": 0.5, "sig": "x",
             "g50_short": {"1.5": 2.0, "3": 2.5}, "full_seconds": 5.0}
    judge = SP.SimilarityJudge([SP.JudgeMember(_VadEncoder(), _CEN, calib, cohort)])
    assert judge.precise
    return judge


def test_stored_versions_keep_their_speech_seconds(tmp_path):
    """留下来的版本重新打分时声纹沿用存下来的，人声有几秒也要一起沿用（短句子「100%」的标准按人声长短定）。
    审查发现：以前沿用声纹就不再做人声检测、人声秒数变成「不知道」，按整句的标准算——短句子重新排名时
    从 100% ✅ 掉到 84% 🔴，重新生成时留下来的最好版本也被算低、换成了更差的新版本。"""
    judge = _vad_judge()
    w = {"speaker": 2.0, "cer": 1.0, "rate": 0.4, "pitch": 0.2}
    n, b = _narrator(tmp_path, scorer=IJ.IdenticalScorer({}, None, None, w, judge=judge))
    n._judge = judge
    seg = _seg("好的，我们开始。")  # 短句：人声不到 1.5 秒
    first = n.synthesize_segment(seg)
    assert first.score["speech_seconds"] is not None and first.score["speech_seconds"] < 1.5
    plan = n._plan(seg)
    items = S.load_candidates(S.store_dir(n.project.cache_dir, plan.pool_key))
    keys = ("pct", "pct_raw", "pcts", "total", "speech_seconds")
    saved = {(it["seed"], it["row"]): {k: it["score"].get(k) for k in keys} for it in items}
    assert len(saved) == len(items) >= 2
    # 按现在的标准重新排名（不生成）：每个留下的版本分数一个数都不差，而且没有再做人声检测（声纹沿用存下来的）
    enc = judge.members[0].encoder
    before = enc.prepares
    again = n._search_obj().rerank(seg, plan, 0)
    assert enc.prepares == before
    assert {(c.seed, c.row): {k: c.score.to_dict().get(k) for k in keys} for c in again.cands} == saved
    # 老师能看到的：只是说话习惯的指纹变了（例如改了素材里别的一句话的文字）→ 重新排名后百分比、状态、提示都不变
    calls = len(b.calls)
    n._identical["profile_sig"] = "twin-after-text-edit"
    r2 = n.synthesize_segment(seg)
    assert len(b.calls) == calls and r2.cached
    assert (r2.pct, r2.status, r2.hint, r2.seed) == (first.pct, first.status, first.hint, first.seed)
    assert r2.score["speech_seconds"] == first.score["speech_seconds"]
    # 重新生成：留下来的版本和当时的分数一样，最好的不会变差
    out = n._search_obj().run(seg, plan, force=True)
    stored = {(c.seed, c.row): round(c.total, 4) for c in out.cands if c.stored}
    assert stored == {k: v["total"] for k, v in saved.items()}
    assert out.best.total >= max(stored.values()) - S.TIE_EPS


class _TieScorer(FakeScorer):
    """同一段声音永远同一个分数；综合分都差不到 0.02（差不多一样高）；「非音色部分」正好和综合分反过来
    （综合分低一点的那个时长、音调更好）——挑出来的那个按综合分排在后面。"""

    def _total(self, wav):
        return 1.0 + 0.0025 * (zlib.crc32(np.asarray(wav, np.float32).tobytes()) % 8)

    def non_timbre(self, s):
        return -s.total


def test_chosen_version_is_always_stored(tmp_path):
    """挑出来的那个（差不多一样高时按时长、音调挑的，按综合分排不进前 6）也一定留下来：分数不变时重新排名还是它，
    重新生成时它也一起比（审查发现：以前只留综合分前 6 个，重新排名换成了另一个版本）。"""
    cfg = make_cfg(tmp_path / "ws", synth=_limits(min_candidates=10, max_candidates=10))
    n, b = _narrator(tmp_path, scorer=_TieScorer(), cfg=cfg)
    seg = _seg()
    res = n.synthesize_segment(seg)
    plan = n._plan(seg)
    search = n._search_obj()
    stored = S.load_candidates(S.store_dir(n.project.cache_dir, plan.pool_key))
    ranked = sorted(search.pool, key=search._value, reverse=True)
    assert res.tries == 10 and len(stored) == 6
    assert [c.seed for c in ranked].index(res.seed) >= 6  # 按综合分排不进前 6（不然测不出来）
    assert stored[0]["seed"] == res.seed and len({it["seed"] for it in stored}) == 6
    # 只是说话习惯的指纹变了（每个版本的分数完全一样）：重新排名还是同一个版本
    calls = len(b.calls)
    n._scorer = _TieScorer()
    n._identical["profile_sig"] = "twin-b"
    r2 = n.synthesize_segment(seg)
    assert len(b.calls) == calls and r2.cached and r2.seed == res.seed
    # 重新生成：它也一起比
    n._scorer = _TieScorer()
    out = n._search_obj().run(seg, plan, force=True)
    assert res.seed in {c.seed for c in out.cands if c.stored}


class _CountingBackend(FakeBackend):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.starts = 0

    def start(self):
        self.starts += 1


def test_weights_change_reranks_without_starting_the_engine(tmp_path):
    """只是排序权重变了（缓存键跟着变）：留下的版本都在、一个请求都不用发，整篇生成时也不启动合成引擎
    （真的 GPT-SoVITS 启动要占显卡、几十秒）。留下的版本读不了时才启动、重新生成这一句。"""
    n1, b1 = _narrator(tmp_path, backend=_CountingBackend())
    n1._started = False
    seg = _seg()
    n1.synthesize_all([seg])
    assert b1.starts == 1 and b1.calls

    def again(version):
        models = n1.project.load_models()
        models.setdefault(b1.name, {})["identical"] = {"weights_version": version, "weights": {}}
        n1.project.models_path.write_text(json.dumps(models), encoding="utf-8")
        b = _CountingBackend()
        nn = eng.Narrator(n1.cfg, n1.project, b, quality="identical", tier="none")
        nn._scorer, nn._judge, nn.use_asr = FakeScorer(), None, False
        rec = []
        nn.progress = lambda f, m: rec.append(m)
        return b, nn.synthesize_all([seg]), rec

    b2, r2, rec2 = again("w2")
    assert (b2.starts, len(b2.calls), r2[0].cached) == (0, 0, True)
    assert not any("启动合成引擎" in m for m in rec2)
    # 留下的版本读不了（声音文件坏了）：这时才启动合成引擎、重新生成
    folder = S.store_dir(n1.project.cache_dir, n1._plan(seg).pool_key)
    for f in folder.glob("*.flac"):
        f.write_bytes(b"broken")
    b3, r3, _ = again("w3")
    assert b3.starts == 1 and b3.calls and not r3[0].cached


class _AsrFailScorer(FakeScorer):
    """识别校验一用就出错（例如识别模型显存不够）；不识别时和 FakeScorer 一样。"""

    def full(self, wav, sr, text, lang, mult=1.0, prepared=None, use_asr=True, cer=None):
        if use_asr and cer is None:
            raise RuntimeError("CUDA failed with error out of memory")
        return super().full(wav, sr, text, lang, mult, prepared=prepared, use_asr=use_asr, cer=cer)


def test_identical_asr_failure_is_unchecked_and_rechecked_later(tmp_path):
    """「一模一样」识别校验出错（第四轮找 bug g5 合并进「一模一样」）：搜索时关掉识别校验接着挑，但这一句不能说
    达到了严格标准、不能当成检查过的存进缓存，只告诉老师一次，小结里列出来；下次识别校验能用时重新生成并检查——
    不从留下的版本里重新挑（留下的也没检查过），排序权重变了（缓存键变了）时也一样。识别校验还是不能用时直接用。"""
    n, b = _narrator(tmp_path, scorer=_AsrFailScorer(), use_asr=True)
    assert n._asr_requested
    seg = _seg()
    res = n.synthesize_segment(seg)
    meta = json.loads(n._plan(seg).meta_path.read_text(encoding="utf-8"))
    assert res.unchecked and res.met is None and res.score.get("cer") is None
    assert meta["asr_checked"] is False and meta["met"] is None and not n.use_asr
    told = [w for w in n.warnings if "识别校验出错了" in w]
    assert len(told) == 1 and "第 1 句起" in told[0] and not told[0].startswith("第")
    lines = n._summary_lines([res], [], None, {"pauses": {}, "loudness": {}})
    assert any("其中 1 句没有做识别校验" in x and "第 1 句" in x for x in lines)
    # 识别校验还是不能用：直接用，不重新生成
    n_off, b_off = _narrator(tmp_path, scorer=FakeScorer(), use_asr=False)
    r_off = n_off.synthesize_segment(seg)
    assert r_off.cached and r_off.unchecked and not b_off.calls
    # 排序权重变了（缓存键变了、留下的版本还在）：留下的没检查过，识别校验又能用了——重新生成并检查，不重新挑
    n_w, b_w = _narrator(tmp_path, scorer=FakeScorer(), use_asr=True)
    n_w._identical["weights_version"] = "w2"
    r_w = n_w.synthesize_segment(seg)
    assert b_w.calls and not r_w.cached and not r_w.unchecked and r_w.met is True
    assert json.loads(n_w._plan(seg).meta_path.read_text(encoding="utf-8"))["asr_checked"] is True
    # 原来的缓存键：缓存里是没检查过的那个 → 重新生成并检查（不从留下的版本里重新挑）
    n2, b2 = _narrator(tmp_path, scorer=FakeScorer(), use_asr=True)
    r2 = n2.synthesize_segment(seg)
    assert b2.calls and not r2.cached and not r2.unchecked and r2.met is True and r2.score["cer"] == 0.0
    assert json.loads(n2._plan(seg).meta_path.read_text(encoding="utf-8"))["asr_checked"] is True
    assert not any("识别校验" in w for w in n2.warnings)
    # 再下一次：直接用
    n3, b3 = _narrator(tmp_path, scorer=FakeScorer(), use_asr=True)
    r3 = n3.synthesize_segment(seg)
    assert r3.cached and not r3.unchecked and r3.met is True and not b3.calls


def test_blind_test_never_uses_its_real_clips_as_references(prepared, tmp_path, monkeypatch):
    """盲听测试当「真人」播放的录音，不能拿来当生成那一段的参考（主参考、辅助参考都不行）：「一模一样」从参考录音库
    挑参考，以前只从 references.json 里去掉了它们（审查发现：验证集不够、要用训练集的录音时，它们还在库里能被挑上）。"""
    from voicetwin import workflows as wf

    _constant_scores(monkeypatch)
    cfg, project, _ = prepared
    n_val = sum(1 for r in project.load_manifest(only_kept=True) if r.get("text") and r.get("split") == "val")
    real_ids = {r["id"] for r in wf._blind_pool(project, n_val + 6)}
    seen = {"pool": set(), "used": set()}
    orig = eng.Narrator._plan_identical

    def spy(self, seg):
        plan = orig(self, seg)
        seen["pool"] |= {e["id"] for e in self._identical_ctx()["pool"]}
        seen["used"] |= {r["id"] for r in plan.refs} | {a["id"] for v in plan.aux_by_ref.values() for a in v}
        return plan

    monkeypatch.setattr(eng.Narrator, "_plan_identical", spy)
    res = wf.build_blind_test(cfg, project.voice, n=n_val + 6, quality="identical", seed=3)
    ans = json.loads(Path(res["answer_path"]).read_text(encoding="utf-8"))
    import shutil  # 共用的测试声音：这次的盲听测试不留着（别的测试看「最新的盲听测试」）

    shutil.rmtree(res["dir"], ignore_errors=True)
    Path(res["answer_path"]).unlink()
    assert {it["clip"] for it in ans["items"] if it["truth"] == "真人"} == real_ids
    bank = json.loads((project.root / "refs_bank.json").read_text(encoding="utf-8"))
    assert real_ids & {e["id"] for e in bank["entries"]}  # 库里本来有盲听测试的录音（不然测不出来）
    assert seen["pool"] and not seen["pool"] & real_ids and not seen["used"] & real_ids


def test_excluded_refs_never_planned_as_main_or_aux(tmp_path):
    """不能用的参考录音（exclude_refs，盲听测试的「真人」录音）：不当主参考、不当辅助参考（测试引擎不支持辅助参考，
    这里用支持的假引擎），缓存键跟着变（以前用它们当参考生成好的不能拿来用）；全都不能用时照旧用 references.json。"""
    n, b = _narrator(tmp_path, tier="mid")
    seg = _seg()
    n._identical = None
    plan = n._plan(seg)
    used = {r["id"] for r in plan.refs} | {a["id"] for v in plan.aux_by_ref.values() for a in v}
    assert {"r1", "r2"} <= used
    n.exclude_refs = {"r1", "r2"}
    n._identical = None
    plan2 = n._plan(seg)
    used2 = {r["id"] for r in plan2.refs} | {a["id"] for v in plan2.aux_by_ref.values() for a in v}
    assert used2 and not used2 & {"r1", "r2"} and plan2.key != plan.key
    assert not {"r1", "r2"} & {e["id"] for e in n._identical_ctx()["pool"]}
    n.exclude_refs = {r["id"] for r in _REFS}
    n._identical = None
    assert n._plan(seg).refs  # 全都不能用：照旧有参考（和 build_blind_test 里 refs 的兜底一样）


# ============================================================================ 缓存键
def test_cache_key_knobs_and_batch_size(tmp_path):
    cfg = make_cfg(tmp_path / "ws")
    n, b = _narrator(tmp_path, tier="mid", cfg=cfg)
    seg = _seg()
    base = n._plan(seg)
    keys = {"base": base.key}

    def key_of(nn, s=seg):
        return nn._plan(s).key

    # 每批几个（B）：不在缓存键里
    c_b = make_cfg(tmp_path / "ws", synth=_limits(batch=3))
    nb, _ = _narrator(tmp_path, tier="mid", cfg=c_b)
    assert nb.n_candidates == 3 and key_of(nb) == base.key
    # 每一项变了都变
    nm, _ = _narrator(tmp_path, tier="mid", backend=FakeBackend(model="other-model"))
    keys["model"] = key_of(nm)
    keys["text"] = key_of(n, _seg(TEXT + "啊"))
    en = "We can add a condition at the end of the expression."
    keys["lang_zh"], keys["lang_en"] = key_of(n, _seg(en, lang="zh")), key_of(n, _seg(en, lang="en"))
    ctx = dict(n._identical)
    n._identical = dict(ctx, bank_sig="other-bank")
    keys["bank"] = key_of(n)
    n._identical = dict(ctx, prior_version="audition-2")
    keys["prior"] = key_of(n)
    n._identical = dict(ctx, weights_version="w9")
    keys["weights"] = key_of(n)
    n._identical = dict(ctx, block={"speed": {"zh": 1.07}})
    keys["speed"] = key_of(n)
    n._identical = ctx
    for name, synth in (("min", _limits(min_candidates=30)), ("max", _limits(max_candidates=50)),
                        ("plateau", _limits(plateau=6)), ("eps", _limits(plateau_eps=0.05)),
                        ("presets", _limits(presets=[{"temperature": 0.9, "top_k": 15, "top_p": 1.0}])),
                        ("seed", {"seed": 7})):
        nn, _ = _narrator(tmp_path, tier="mid", cfg=make_cfg(tmp_path / "ws", synth=synth))
        keys[name] = key_of(nn)
    nr, _ = _narrator(tmp_path, tier="mid", reference="r4")
    keys["forced_ref"] = key_of(nr)
    ns, _ = _narrator(tmp_path, tier="mid", speed=1.2)
    keys["mult"] = key_of(ns)
    assert keys["lang_zh"] != keys["lang_en"]
    vals = list(keys.values())
    assert len(set(vals)) == len(vals), keys
    # 其它档位的缓存键不受影响（test_identical_tier.py 的金标准照样通过）
    assert eng.Narrator(cfg, n.project, b, quality="perfect", tier="mid")._plan(seg).key != base.key


# ============================================================================ 语速微调
def test_tempo_refinement_on_dummy_backend_hits_the_target(prepared, tmp_path):
    from voicetwin.backends.base import get_backend

    cfg, project, _ = prepared
    c2 = make_cfg(project.root.parent, synth=_limits(min_candidates=3, max_candidates=3))
    backend = get_backend("dummy", c2, project)
    try:
        n = eng.Narrator(c2, project, backend, quality="identical", tier="none")
        state = {}

        def expected(voiced):  # 第一个版本说得比应该的长 8%（其它版本按同一个目标比）
            state.setdefault("e", voiced / 1.08)
            return state["e"]

        n._scorer = FakeScorer(totals=[2.0, 1.0, 1.0], expected=expected)
        n._judge = None
        n.use_asr = False
        seg = _seg("今天我们来学习列表推导式，它可以让代码变得更加简洁。", index=5)
        plan = n._plan(seg)
        search = n._search_obj()
        out = search.run(seg, plan)
        ref = [c for c in search.refined]
        assert len(ref) == 1 and ref[0].refined and ref[0].refine_of is search.cands[0]
        r = ref[0]
        assert r.seed == search.cands[0].seed and r.speed == pytest.approx(search.cands[0].speed * 1.08, rel=1e-3)
        assert abs(r.score.voiced / state["e"] - 1.0) < 0.03
        assert out.stats["refine_requests"] == 1 and out.tries == 3  # 微调的不算在试了几个里
    finally:
        backend.stop()


def test_tempo_refinement_real_api_request_differs_only_in_speed(prepared, tmp_path, monkeypatch):
    """真实 api_v2（假模型）：同时生成 2 个，挑出来的那个语速偏了 → 同一个请求只改 speed_factor 再发一次。"""
    import os
    import socket
    import sysconfig

    from fake_gptsovits import REAL_API_V2, build_fake_root
    from voicetwin import workflows as wf
    from voicetwin.backends.base import get_backend
    from voicetwin.backends.gptsovits import GPTSoVITSBackend

    monkeypatch.setattr(GPTSoVITSBackend, "ensure_users_pth", lambda self: None)
    monkeypatch.setattr(GPTSoVITSBackend, "_gpu_memory", lambda self, quick=False: (11.99, 11.2, "test"))
    monkeypatch.setattr(GPTSoVITSBackend, "STARTUP_NOTE_SECONDS", 0.4)
    paths = [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"], os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(p for p in dict.fromkeys(paths) if p))
    for k in ("FAKE_GSV_MAX_BATCH", "FAKE_GSV_SPEED_TRICK_BROKEN", "FAKE_GSV_INNER_ZERO"):
        monkeypatch.delenv(k, raising=False)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    cfg, project, _ = prepared
    root = build_fake_root(tmp_path / "GPT-SoVITS", real_api=REAL_API_V2)
    gcfg = make_cfg(project.root.parent, backends={"gptsovits": {
        "root": str(root), "python": sys.executable, "port": port, "startup_timeout": 60}},
        synth=_limits(batch=2, min_candidates=2, max_candidates=2))
    p2 = wf.open_project(gcfg, project.voice, must_exist=True)
    b = get_backend("gptsovits", gcfg, p2)
    try:
        n = eng.Narrator(gcfg, p2, b, quality="identical", tier="low")
        n._scorer = FakeScorer(totals=[2.0, 1.0], ratio=1.1)
        n._judge = None
        n.use_asr = False
        n._identical = None
        rec = []
        n.progress = lambda f, m: rec.append(m)
        seg = _seg("大家好，今天我们讲第一课的第一个例子。", index=2)
        plan = n._plan(seg)
        plan.arms = plan.arms[:1]  # 第 1 轮只留一种组合：一次请求同时生成 2 个
        search = n._search_obj()
        search.run(seg, plan, force=True)
        runs = [json.loads(x)["req"] for x in (root / "_real_api_calls.jsonl").read_text(encoding="utf-8").splitlines()
                if x.strip() and json.loads(x)["kind"] == "run"]
        big = [r for r in runs if r["batch_size"] == 2 and "\n" in r["text"]]
        assert len(big) >= 2
        first, again = big[0], big[-1]
        diff = {k for k in set(first) | set(again) if first.get(k) != again.get(k)}
        assert diff == {"speed_factor"}, diff
        assert first["speed_factor"] == 1.0001 and again["speed_factor"] == pytest.approx(1.1, rel=1e-3)
        assert search.refined and search.refined[0].row == search.cands[0].row
        assert any("已试 2 个版本（显卡一次同时生成 2 个）" in m for m in rec)  # 真的同时生成了才这样说
    finally:
        b.stop()


# ============================================================================ 给老师看的字、进度
def test_texts_describe_what_p5_built():
    """说明写上这一步做好了的（每句几条参考、几种设置、引擎自检通过时同时生成好几个、三个声纹模型、中英文分开查错字；
    第 6 步做好以后：整篇再挑一遍、按你本人的停顿长短和音量拼接），没实测的（用满显卡）不写。
    「新模型先做一次准备」第 8 步做好了（prepare_identical），可以写（test_identical_tier 按功能把关）。"""
    help_ = eng.QUALITY_HELP["identical"]
    for ph in ("换几条", "几种生成设置", "同时生成好几个版本", "三个模型", "中英文分开", "自检通过",
               "整篇再挑一遍", "按你本人的停顿长短和音量拼接"):
        assert ph in help_, ph
    label = eng.QUALITY_LABELS["identical"]
    assert "换几条" in label and "几十" not in label and "整篇按你的停顿和音量拼接" in label
    assert "减少同时生成的个数" in eng.recommended_quality("low")[1]
    for t in (label, help_, *eng.QUALITY_TIER_NOTES.values()):
        for ph in ("用满显卡", "不会因为显存不够而停下"):
            assert ph not in t, (ph, t)


def _constant_scores(monkeypatch, total=1.0, pct=100.0):
    from voicetwin.eval import metrics

    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")

    def quick(self, wav, sr, text, lang, mult=1.0):
        return IJ.QuickScore(total=total, pct_raw=pct, voiced=1.0, expected=None, dur_dev=None, gate_ok=True)

    def full(self, wav, sr, text, lang, mult=1.0, prepared=None, use_asr=True, cer=None, check_pauses=True):
        return Score(total=total, pct=pct, pct_raw=pct, cer=0.0, errors=0, stage="full")

    monkeypatch.setattr(IJ.IdenticalScorer, "quick", quick)
    monkeypatch.setattr(IJ.IdenticalScorer, "full", full)
    monkeypatch.setattr(metrics.Scorer, "in_normal_range", lambda self, s, lang, speed=1.0: True)


def test_eta_line_only_after_three_fresh_sentences(prepared, tmp_path, monkeypatch):
    import uuid

    from voicetwin import workflows as wf

    _constant_scores(monkeypatch)
    cfg, project, _ = prepared
    tag = uuid.uuid4().hex[:6]
    lines = [f"预计时间测试第{k}句，编号{tag}。" for k in "一二三四"]
    rec = []
    res = wf.run_narrate(cfg, project.voice, "\n".join(lines), out=str(tmp_path / "eta.wav"), variants=False,
                         progress=lambda f, m: rec.append(m))
    assert res.quality == "identical" and len(res.segments) == 4
    eta = [k for k, m in enumerate(rec) if m.startswith("按刚才实测的速度估算，生成还要")]
    third = next(k for k, m in enumerate(rec) if m.startswith("[3/4] 生成："))
    assert len(eta) == 1 and eta[0] > third and "还有 1 句" in rec[eta[0]]
    # 再来一次：都已经生成过（直接用），不说还要多久；只有 3 句新的时最后一句之后也不说
    rec.clear()
    wf.run_narrate(cfg, project.voice, "\n".join(lines), out=str(tmp_path / "eta2.wav"), variants=False,
                   progress=lambda f, m: rec.append(m))
    assert not any(m.startswith("按刚才实测的速度估算") for m in rec)
    rec.clear()
    wf.run_narrate(cfg, project.voice, "\n".join(x.replace(tag, tag + "b") for x in lines[:3]),
                   out=str(tmp_path / "eta3.wav"), variants=False, progress=lambda f, m: rec.append(m))
    assert not any(m.startswith("按刚才实测的速度估算") for m in rec)


def test_identical_narration_end_to_end_on_dummy(prepared, tmp_path, monkeypatch):
    """测试引擎整篇走一遍（真的打分器，没有精准声纹模型）：每句的记录里有用了哪种组合、试了几次请求，
    报告里的参考录音来自参考录音库，第 1 轮的进度不说「显卡一次同时生成」（测试引擎是一个一个生成的）。"""
    import uuid

    from voicetwin import workflows as wf

    monkeypatch.setattr(eng, "_vram_tier", lambda: "none")
    cfg, project, _ = prepared
    rec = []
    text = f"整篇测试的一句话，它稍微长一点，编号{uuid.uuid4().hex[:6]}。"
    res = wf.run_narrate(cfg, project.voice, text, out=str(tmp_path / "e2e.wav"), variants=False,
                         progress=lambda f, m: rec.append((f, m)))
    seg = res.segments[0]
    assert 6 <= seg["tries"] <= 12 and seg["candidates"]
    assert all("arm" in c for c in seg["candidates"])
    meta = json.loads(Path(project.abspath(seg["clip"])).with_suffix(".json").read_text(encoding="utf-8"))
    assert meta["search"]["candidates"] == seg["tries"] and meta["search"]["requests"] >= 5
    assert meta["arm"]["ref_id"] == seg["ref"] and meta["profile_sig"]
    bank_ids = {e["id"] for e in json.loads((project.root / "refs_bank.json").read_text(encoding="utf-8"))["entries"]}
    assert seg["ref"] in bank_ids
    assert not any("同时生成" in m for _, m in rec)
    fr = [f for f, _ in rec]
    assert fr == sorted(fr)
