#!/usr/bin/env python3
"""Read-only, scalar-only diagnosis of the sample-exact audio reference.

This is evidence collection, not a QC gate, and never returns a pass verdict.
Private GT, cache and model bytes are read locally only. No arrays or speech
content are included in the output. Existing production/checker files are not
modified. Run after the official post-production check has created its GT.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
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


def raw_highlight_onset_scalars(tools, a, sr, no):
    """Run the unchanged pure G45 functions on actual PCM; publish levels only."""
    if no != '44':
        return None
    path = tools / '高亮同步核对.py'
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in {'是开口', '确认可收'}]
    assert len(nodes) == 2
    scope = {'np': np}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
    rows = []
    times = [tick / 1000 for tick in sorted(set(range(25600, 26001, 5)) |
                                            set(range(25770, 25831)))]
    for t in times:
        F = int(.005 * sr)
        i = int(round(t * sr))
        w = a[max(0, i - 2 * sr):i + 2 * sr]
        n = len(w) // (2 * F)
        ref = np.sqrt(np.mean(w[:n * 2 * F].reshape(n, 2 * F) ** 2, axis=1)).max() + 1e-12
        level = lambda start: float(20 * np.log10(np.sqrt(np.mean(a[start:start + F] ** 2)) / ref + 1e-12))
        pre = [level(j) for j in range(i - 6 * F, i, F)]
        post = [level(j) for j in range(i, i + 8 * F, F)]
        rows.append({'actual_pcm_time_s': round(t, 3), 'pre30ms_max_db': max(pre),
                     'post40ms_max_db': max(post), 'this5ms_db': level(i),
                     'original_G45_accepts': bool(scope['确认可收'](no, a, sr, t))})
    return {'original_checker_sha256': sha256(path), 'original_functions_executed': ['是开口', '确认可收'],
            'sentence': 'S2', 'chunk': 3, 'window_s': [25.6, 26.0],
            'fine_window_s': [25.77, 25.83], 'fine_step_s': .001,
            'purpose': 'raw actual PCM onset diagnosis only; does not approve a confirmation', 'rows': rows}


def abnormal_edit_scalars(report_path: Path, script_path: Path, wav_path: Path, sr=24000):
    """Whitelist scalar edit locations/levels from the unchanged audit report.

    Do not export waveforms, alignment maps, GT metadata/paths, arrays of PCM,
    cache bytes, or model bytes. Confirmation coverage is diagnostic only and
    does not issue or replace an official QC verdict.
    """
    if not report_path.is_file():
        return None
    data = json.loads(report_path.read_text())
    script = json.loads(script_path.read_text())
    confirmations = script.get("核对确认", {}).get("删除段", {})
    fpd = hashlib.md5(wav_path.read_bytes()).hexdigest()[:12]
    scalar_fields = (
        "raw_k1", "raw_k2", "A_k1", "A_k2", "tail_cut_ms", "onset_cut_ms",
        "tail_cut_ms_spk", "onset_cut_ms_spk", "first5_db", "last5_db",
        "lost_ms", "shift_ms", "ins_ms", "ins_nonzero", "lost_max_db",
        "lost_max_db_spk", "pre_db", "post_db", "pre_min_db", "post_min_db",
    )
    def number(value):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("non-numeric value in whitelisted official edit scalar")
        return value if math.isfinite(value) else None
    edits = []
    for text in data.get("texts", []):
        index = int(text["idx"])
        label = "标题" if index == -1 else f"S{index + 1}"
        for position, edit in enumerate(text.get("edits", [])):
            if not (edit.get("edge_bad") or edit.get("tail_cut_ms") or edit.get("onset_cut_ms")):
                continue
            row = {key: number(edit.get(key)) for key in scalar_fields if key in edit}
            row.update({"text_index": index, "sentence_label": label, "edit_index_in_text": position,
                        "edge_bad": bool(edit.get("edge_bad")),
                        "edge_sides": [side for side in edit.get("edge_sides", [])
                                       if side in {"pre", "post", "lost"}]})
            for begin, end, prefix in (("raw_k1", "raw_k2", "raw"), ("A_k1", "A_k2", "actual")):
                row[prefix + "_start_seconds"] = number(edit[begin]) / sr
                row[prefix + "_end_seconds"] = number(edit[end]) / sr
            key = f"{label} raw {edit['raw_k1'] / sr:.4f}-{edit['raw_k2'] / sr:.4f}"
            confirmation = confirmations.get(key)
            typed = isinstance(confirmation, dict)
            matches = typed and confirmation.get("配音指纹") == fpd
            supplied_kind = confirmation.get("类型") if matches else None
            kind = (supplied_kind if isinstance(supplied_kind, str)
                    and supplied_kind in {"紧贴词尾的非人声", "紧贴词头的非人声", "紧贴两头的非人声"} else None)
            legacy = key in confirmations and not typed
            allowed = ({"lost"} if legacy else {"pre", "lost"} if kind == "紧贴词尾的非人声"
                       else {"post", "lost"} if kind == "紧贴词头的非人声"
                       else {"pre", "post", "lost"} if kind == "紧贴两头的非人声" else set())
            row["source_deletion_confirmation"] = {
                "lookup_key": key, "present": key in confirmations,
                "legacy_untyped_entry": legacy, "current_pcm_fingerprint_matches": matches,
                "current_valid_type": kind,
                "covers_reported_edge_sides": set(row["edge_sides"]) <= allowed,
                "covers_reported_tail_cut": not edit.get("tail_cut_ms") or kind in {"紧贴词尾的非人声", "紧贴两头的非人声"},
                "covers_reported_onset_cut": not edit.get("onset_cut_ms") or kind in {"紧贴词头的非人声", "紧贴两头的非人声"},
            }
            edits.append(row)
    return {
        "purpose": "official abnormal edit scalar locations and existing confirmation coverage; diagnostic only",
        "official_report_sha256": sha256(report_path), "current_pcm_md5_first12": fpd,
        "sample_rate": sr, "abnormal_edits": edits,
        "extra_nonzero_runs": [{"actual_start_seconds": number(row[0]), "duration_ms": number(row[1]),
                                "absolute_peak": number(row[2])} for row in data.get("extra_runs", [])],
        "private_waveforms_GT_cache_model_bytes_exported": False,
    }


def public_timing_metadata(work: Path):
    """Read actual producer timing JSON; retain only explicit timing scalars."""
    def number(value):
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("invalid numeric producer timing metadata")
        return value
    def sentence(value):
        if value == "标题" or isinstance(value, str) and re.fullmatch(r"S[1-9]\d*", value):
            return value
        raise ValueError("invalid sentence label in producer timing metadata")
    segment_path = work / "分段.json"
    graft_path = work / "词尾除阻.json"
    result = {"purpose": "actual public timeline metadata only; no raw sample arrays",
              "segment_record_sha256": sha256(segment_path),
              "graft_record_sha256": sha256(graft_path), "segments": {}, "consonant_grafts": []}
    if segment_path.is_file():
        for key, records in json.loads(segment_path.read_text()).items():
            label = sentence(key)
            rows = []
            for record in records:
                times = record["时刻"]
                if not isinstance(times, list) or len(times) != 2:
                    raise ValueError("invalid producer segment timing pair")
                start, end = number(times[0]), number(times[1])
                if start is None or end is None or end < start:
                    raise ValueError("nonmonotonic producer segment timing pair")
                piece = number(record["段"])
                if int(piece) != piece or piece < 1:
                    raise ValueError("invalid producer segment index")
                rows.append({"段": int(piece), "增益": number(record.get("增益")),
                             "停顿": number(record.get("停顿")), "时刻": [start, end]})
            result["segments"][label] = rows
    if graft_path.is_file():
        for record in json.loads(graft_path.read_text()):
            position = record["位置"]
            if not isinstance(position, str) or not (position == "句末" or re.fullmatch(r"第[1-9]\d*个标点", position)):
                raise ValueError("invalid consonant graft position label")
            start, end = number(record["开始"]), number(record["结束"])
            if start is None or end is None or end < start:
                raise ValueError("invalid consonant graft time interval")
            result["consonant_grafts"].append({"句": sentence(record["句"]), "位置": position,
                                               "类型": "词尾辅音除阻移植", "开始": start, "结束": end})
    return result


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
        result['raw_highlight_onset_scalars'] = raw_highlight_onset_scalars(args.tools, a, sr, no)
        if no == '44':
            conf = json.loads(script.read_text()).get('核对确认', {}).get('高亮', {}).get('S2 第3块')
            current_fingerprint = hashlib.md5(wav.read_bytes()).hexdigest()[:12]
            result['raw_highlight_onset_scalars'].update({
                'current_confirmation': conf, 'actual_wav_md5_first12': current_fingerprint,
                'confirmation_fingerprint_matches': isinstance(conf, dict) and conf.get('配音指纹') == current_fingerprint})
        meta = json.loads(meta_path.read_text())
        records_path = work / "分段.json"
        records = json.loads(records_path.read_text()) if records_path.is_file() else {}
        result["segment_record_sha256"] = sha256(records_path)
        result["public_producer_timing_metadata"] = public_timing_metadata(work)
        arrays = [(it, np.load(it["file"]).astype(np.float64)) for it in meta]
        raw_peak, raw_idx, raw_sample = max(
            (float(np.abs(x).max()), it["idx"], int(np.abs(x).argmax())) for it, x in arrays)
        g_default = 0.89 / raw_peak
        result["reference_global_peak"] = {"absolute": raw_peak, "text_index": raw_idx, "time_in_reference_s": raw_sample / sr}
        result["default_audit_gain"] = g_default
        result["actual_pcm"] = {"sample_rate": sr, "samples": len(a), "duration_s": len(a) / sr,
                                "sample_peak": float(np.abs(a).max()), "peak_time_s": float(np.abs(a).argmax() / sr)}
        result["official_audit"] = summarize_official_report(args.qc_dir / f"report2_{no}.json")
        result["official_abnormal_edit_scalars"] = abnormal_edit_scalars(
            args.qc_dir / f"report2_{no}.json", script, wav, sr)
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
