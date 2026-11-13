#!/usr/bin/env python3
"""Read-only, scalar-only diagnosis of the sample-exact audio reference.

This is evidence collection, not a QC gate, and never returns a pass verdict.
Private GT, cache and model bytes are read locally only. No arrays or speech
content are included in the output. Existing production/checker files are not
modified. Run after the official post-production check has created its GT.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path

import numpy as np
import soundfile as sf


def sha256(path: Path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def ncc_search(a, x, lo, hi):
    """Amplitude-independent alignment; no thresholds or gates are changed."""
    size = len(x)
    lo = max(0, int(lo))
    hi = min(len(a) - size, int(hi))
    if hi < lo or np.dot(x, x) < 1e-20:
        return None, None
    seg = a[lo:hi + size]
    nfft = 1 << max(1, (len(seg) + size - 1).bit_length())
    corr = np.fft.irfft(np.fft.rfft(seg, nfft) * np.conj(np.fft.rfft(x, nfft)), nfft)[:hi - lo + 1]
    cs = np.r_[0.0, np.cumsum(seg * seg)]
    energy = cs[size:size + hi - lo + 1] - cs[:hi - lo + 1]
    norm = corr / (np.linalg.norm(x) * np.sqrt(np.maximum(energy, 1e-20)) + 1e-20)
    j = int(np.argmax(norm))
    return lo + j, float(norm[j])


def anchor_offsets(x, sr, limit=16):
    size = int(sr * 0.1)
    hop = int(sr * 0.05)
    starts = np.arange(0, max(0, len(x) - size + 1), hop, dtype=int)
    if not len(starts):
        return []
    cs = np.r_[0.0, np.cumsum(x * x)]
    energies = (cs[starts + size] - cs[starts]) / size
    # One energetic, 100 ms copy per temporal stratum. Both quiet and voiced
    # regions may exist; publish only correlations/gains/residuals, never audio.
    candidates = []
    for group in np.array_split(np.arange(len(starts)), min(limit, len(starts))):
        j = int(group[np.argmax(energies[group])])
        if energies[j] > max(float(energies.max()) * 1e-4, 1e-16):
            candidates.append(int(starts[j]))
    return candidates


def summarize_official_report(path: Path):
    if not path.is_file():
        return None
    data = json.loads(path.read_text())
    texts = data.get("texts", [])
    edits = [e for t in texts for e in t.get("edits", [])]
    return {
        "report_sha256": sha256(path),
        "fixed_gain": data.get("g"),
        "text_count": len(texts),
        "unmatched_blocks": sum(t.get("n_unmatched_blocks", 0) for t in texts),
        "edit_count": len(edits),
        "edits_with_nonzero_tail_or_onset_cut": sum(bool(e.get("tail_cut_ms") or e.get("onset_cut_ms")) for e in edits),
        "a10_edge_violations": sum(bool(e.get("edge_bad")) for e in edits),
        "extra_nonzero_run_count": len(data.get("extra_runs", [])),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video-root", required=True, type=Path, help="Private root containing video/ and tts/.")
    p.add_argument("--qc-dir", required=True, type=Path)
    p.add_argument("--no", required=True)
    p.add_argument("--tools", required=True, type=Path)
    p.add_argument("--post-log", type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    no = args.no.zfill(2)
    work = args.video_root / "video" / f"work_{no}"
    wav = work / "a.wav"
    script = args.video_root / "video" / "scripts" / f"{no}.json"
    meta_path = args.qc_dir / "gt" / f"{no}_meta.json"
    result = {
        "purpose": "diagnostic scalar evidence only; no QC pass verdict",
        "article": no,
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "source_sha256": sha256(script),
        "wav_sha256": sha256(wav),
        "gt_meta_sha256": sha256(meta_path),
        "tool_sha256": {name: sha256(args.tools / name) for name in (
            "make_video.py", "clean.py", "独立复核/audit.py", "独立复核/synth.py", "交付核查.py")},
        "model_sha256": {name: sha256(args.video_root / "tts" / name) for name in (
            "kokoro-v1.0.onnx", "voices-v1.0.bin", "voice_mb.npy")},
        "versions": {},
        "execution": {"python": platform.python_version(), "machine_architecture": platform.machine(),
                      "strict_cache": os.environ.get("STRICT_CACHE"),
                      "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                      "mkl_num_threads": os.environ.get("MKL_NUM_THREADS")},
        "notes": [
            "audit.py default gain is 0.89 divided by the peak of all complete GT arrays; it is not LS-estimated despite its docstring.",
            "make_video.py normalizes the concatenated, already trimmed/cleaned/processed audio to a 0.89 sample peak.",
            "Anchor least-squares gains are diagnostic estimates at independently aligned 100 ms regions; a high NCC alone does not prove sample equality.",
            "The kept-input peak is inferred from an anchor gain, not an instrumented pre-normalization producer buffer.",
        ],
    }
    cpu_info = Path("/proc/cpuinfo")
    if cpu_info.is_file():
        fields = {}
        for line in cpu_info.read_text().splitlines():
            if ":" in line:
                key, value = (s.strip() for s in line.split(":", 1))
                if key in ("vendor_id", "model name", "flags") and key not in fields:
                    fields[key] = value if key != "flags" else hashlib.sha256(value.encode()).hexdigest()
        result["execution"]["cpu"] = fields
    for name in ("numpy", "soundfile", "onnxruntime", "kokoro-onnx", "phonemizer", "scipy"):
        try:
            result["versions"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result["versions"][name] = None
    try:
        a, sr = sf.read(wav, dtype="float64")
        if a.ndim != 1 or sr != 24000:
            raise ValueError(f"expected mono 24000 Hz; got channels={a.ndim}, sample_rate={sr}")
        meta = json.loads(meta_path.read_text())
        records_path = work / "分段.json"
        records = json.loads(records_path.read_text()) if records_path.is_file() else {}
        result["segment_record_sha256"] = sha256(records_path)
        arrays = [(it, np.load(it["file"]).astype(np.float64)) for it in meta]
        raw_peak, raw_idx, raw_sample = max(
            (float(np.abs(x).max()), it["idx"], int(np.abs(x).argmax())) for it, x in arrays)
        g_default = 0.89 / raw_peak
        result["reference_global_peak"] = {"absolute": raw_peak, "text_index": raw_idx, "time_in_reference_s": raw_sample / sr}
        result["default_audit_gain"] = g_default
        result["actual_pcm"] = {"sample_rate": sr, "samples": len(a), "duration_s": len(a) / sr,
                                "sample_peak": float(np.abs(a).max()), "peak_time_s": float(np.abs(a).argmax() / sr)}
        result["official_audit"] = summarize_official_report(args.qc_dir / f"report2_{no}.json")
        rows = []
        all_anchors = []
        for it, x in arrays:
            idx = it["idx"]
            rec = records.get(f"S{idx + 1}") if idx >= 0 else None
            if idx < 0:
                body_starts = [r[0]["时刻"][0] for r in records.values() if r and "时刻" in r[0]]
                lo, hi = 0.0, min(body_starts) if body_starts else min(10.0, len(a) / sr)
            elif rec:
                lo = float(rec[0]["时刻"][0]) - 0.35
                hi = float(rec[-1]["时刻"][1]) + 0.35
            else:
                rows.append({"text_index": idx, "error": "missing actual-time segment records"})
                continue
            anchors = []
            for start in anchor_offsets(x, sr):
                ref = x[start:start + int(sr * 0.1)]
                at, ncc = ncc_search(a, ref, lo * sr, hi * sr)
                if at is None:
                    continue
                observed = a[at:at + len(ref)]
                g_ls = float(np.dot(observed, ref) / np.dot(ref, ref))
                ls_error = observed - g_ls * ref
                fixed_error = observed - g_default * ref
                anchor = {
                    "text_index": idx,
                    "reference_time_s": start / sr,
                    "actual_time_s": at / sr,
                    "ncc": ncc,
                    "least_squares_gain": g_ls,
                    "least_squares_to_default_gain": g_ls / g_default,
                    "max_abs_error_lsb_default_gain": float(np.abs(fixed_error).max() * 32768),
                    "max_abs_error_lsb_least_squares_gain": float(np.abs(ls_error).max() * 32768),
                    "rms_error_lsb_default_gain": float(np.sqrt(np.mean(fixed_error * fixed_error)) * 32768),
                    "rms_error_lsb_least_squares_gain": float(np.sqrt(np.mean(ls_error * ls_error)) * 32768),
                }
                anchors.append(anchor)
                all_anchors.append(anchor)
            rows.append({"text_index": idx, "gt_sha256": sha256(Path(it["file"])),
                         "gt_mtime_ns": Path(it["file"]).stat().st_mtime_ns,
                         "reference_sample_peak": float(np.abs(x).max()), "anchors": anchors})
        result["texts"] = rows
        # Exact-copy candidates require high NCC AND residual below the existing
        # checker's original 2.2 LSB limit after fitting one scalar. This does
        # not waive any check and never invokes audit.py with a fitted gain.
        same_waveform = [r for r in all_anchors if r["ncc"] >= 0.99999 and r["max_abs_error_lsb_least_squares_gain"] <= 2.2]
        result["anchor_summary"] = {"count": len(all_anchors), "same_waveform_candidates": len(same_waveform)}
        if same_waveform:
            gains = np.array([r["least_squares_gain"] for r in same_waveform])
            g_median = float(np.median(gains))
            result["anchor_summary"].update({
                "median_fitted_gain": g_median,
                "median_fitted_to_default_gain": g_median / g_default,
                "fitted_gain_min": float(gains.min()),
                "fitted_gain_max": float(gains.max()),
                "inferred_kept_input_peak": 0.89 / g_median,
                "default_gain_fails_original_2_2_lsb_limit_count": sum(r["max_abs_error_lsb_default_gain"] > 2.2 for r in same_waveform),
            })
        if args.post_log and args.post_log.is_file():
            lines = args.post_log.read_text(errors="replace").splitlines()
            result["official_selftest_status_lines"] = [l.strip() for l in lines if "核查程序自检：词尾轻切" in l or "【核查程序失灵，下面的独立复核" in l]
            result["post_log_sha256"] = sha256(args.post_log)
    except Exception as exc:
        # Report exception class and message; never traceback private paths/data.
        result["diagnostic_error"] = {"type": type(exc).__name__, "message": str(exc).replace(str(args.video_root), "<private-root>").replace(str(args.qc_dir), "<private-qc>")}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"article": no, "diagnostic_error": result.get("diagnostic_error"), "anchor_summary": result.get("anchor_summary")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
