"""测试用的"假"合成引擎：生成有音高、共振峰和节奏的类语音信号。

用途：在没有显卡 / 没下载模型时验证整条流水线（切片、打分、拼接、字幕）。
这个文件不依赖 voicetwin 包，可以被任意 Python 环境作为 worker 运行。
"""

from __future__ import annotations

import json
import os
import re
import sys

import numpy as np

CJK = re.compile(r"[一-鿿]")
WORD = re.compile(r"[A-Za-z]+")
VOWELS = [(730, 1090, 2440), (270, 2290, 3010), (300, 870, 2240), (530, 1840, 2480), (570, 840, 2410)]


def _syllables(text: str):
    units = []
    for token in re.findall(r"[一-鿿]|[A-Za-z]+|\d|[，,、；;：:]|[。！？!?.…]", text):
        if token in "，,、；;：:":
            units.append(("pause", 0.22))
        elif token in "。！？!?.…":
            units.append(("pause", 0.45))
        elif WORD.fullmatch(token):
            n = max(1, len(re.findall(r"[aeiouy]+", token.lower())))
            units += [("syl", 1.0)] * n
        else:
            units.append(("syl", 1.0))
    return units


def _resonate(x: np.ndarray, sr: int, formants) -> np.ndarray:
    from scipy import signal

    y = np.zeros_like(x)
    for i, f in enumerate(formants):
        bw = 80 + 40 * i
        r = np.exp(-np.pi * bw / sr)
        theta = 2 * np.pi * f / sr
        b, a = [1 - r], [1, -2 * r * np.cos(theta), r * r]
        y += signal.lfilter(b, a, x) / (i + 1)
    return y


def synth_speech(text: str, sr: int = 24000, seed: int = 0, f0: float = 150.0, rate: float = 4.6,
                 speed: float = 1.0, noise: float = 0.002) -> np.ndarray:
    rng = np.random.default_rng(seed)
    units = _syllables(text) or [("syl", 1.0)]
    out = [np.zeros(int(0.05 * sr))]
    n_syl = sum(1 for u in units if u[0] == "syl")
    k = 0
    question = text.strip().endswith(("?", "？"))
    for kind, val in units:
        if kind == "pause":
            out.append(np.zeros(int(val / speed * sr * rng.uniform(0.85, 1.15))))
            continue
        dur = rng.uniform(0.8, 1.2) / rate / speed
        n = int(dur * sr)
        t = np.arange(n) / sr
        # 语调：整句缓慢下降，疑问句末尾上扬
        pos = k / max(n_syl - 1, 1)
        contour = f0 * (1.08 - 0.16 * pos) * (1.25 if question and pos > 0.85 else 1.0)
        pitch = contour * (1 + 0.03 * np.sin(2 * np.pi * rng.uniform(3, 6) * t))
        phase = 2 * np.pi * np.cumsum(pitch) / sr
        src = np.sign(np.sin(phase)) * 0.5 + 0.5 * np.sin(phase)
        voiced = _resonate(src, sr, VOWELS[rng.integers(len(VOWELS))])
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.6
        out.append(voiced * env)
        k += 1
    out.append(np.zeros(int(0.08 * sr)))
    wav = np.concatenate(out)
    wav = wav / (np.max(np.abs(wav)) + 1e-9) * 0.5
    wav += rng.normal(0, noise, len(wav))
    return wav.astype(np.float32)


def main() -> None:
    import argparse

    import soundfile as sf

    ap = argparse.ArgumentParser()
    ap.add_argument("--f0", type=float, default=150.0)
    ap.add_argument("--rate", type=float, default=4.6)
    ap.add_argument("--sr", type=int, default=24000)
    args = ap.parse_args()

    proto = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
    os.dup2(2, 1)
    sys.stdout = sys.stderr

    def reply(obj):
        proto.write(json.dumps(obj, ensure_ascii=False) + "\n")
        proto.flush()

    reply({"event": "ready", "sr": args.sr, "backend": "dummy"})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        rid = req.get("id")
        try:
            if req.get("cmd") == "shutdown":
                reply({"id": rid, "ok": True})
                break
            if req.get("cmd") == "ping":
                reply({"id": rid, "ok": True})
                continue
            params = req.get("params") or {}
            wav = synth_speech(req["text"], sr=args.sr, seed=int(req.get("seed") or 0), f0=args.f0,
                               rate=args.rate, speed=float(params.get("speed", 1.0) or 1.0))
            sf.write(req["out"], wav, args.sr)
            reply({"id": rid, "ok": True, "out": req["out"], "sr": args.sr})
        except Exception as exc:  # pragma: no cover
            reply({"id": rid, "ok": False, "error": f"{type(exc).__name__}: {exc}"})


if __name__ == "__main__":
    main()
