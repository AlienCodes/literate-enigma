#!/usr/bin/env python3
"""Verify and collect the 69 existing 4K videos; article 05 is a separate task.

Run after actions/download-artifact@v4 with:
  pattern: reviewed-video-*
  path: batch-artifacts/
  merge-multiple: false

This script makes no commits and never pushes. It validates the complete batch
before changing delivery files. BASE blobs are read only into temporary files.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
BASE = "c9d52b26fe981ef8e4c412189ca289716ab8bf00"
TASK_BRANCH = "codex/finish-05-and-summaries-20261112"
EXPECTED = tuple(f"{n:02}" for n in range(1, 71) if n != 5)
VIDEO_DIR = "最终版4K视频"
REPORT_DIR = "简述重制核验"
PREVIEW_DIR = "简述重制预览"
REPAIR_MIN_SNR_DB = 38
REPAIR_MIN_CORRELATION = .9999
AUTHORIZED_REPAIRS = {"67": ("S15", "and Lascaux II"),
                      "70": ("S12", "Mailings doubled")}
SUMMARY_FILES = ("01-12.json", "13-24.json", "25-36.json",
                 "37-48.json", "49-60.json", "61-70.json")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, cwd=ROOT, **kwargs)


def get(args):
    return run(args, capture_output=True, text=True).stdout


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git_paths(ref):
    raw = get(["git", "-c", "core.quotepath=off", "ls-tree", "-rz",
               "--name-only", ref, "--", VIDEO_DIR])
    return [p for p in raw.split("\0") if p]


def source_manifest():
    paths = git_paths(BASE)
    videos = {}
    for path in paths:
        match = re.fullmatch(r"最终版4K视频/(\d{2}) - [^/]+\.mp4", path)
        if not match:
            continue
        no = match.group(1)
        require(no not in videos, f"BASE has multiple source videos for {no}")
        videos[no] = path
    require(set(videos) == set(EXPECTED),
            "BASE source list must contain exactly 69 videos, excluding 05")
    return videos, set(paths)


def read_summaries():
    result = {}
    directory = ROOT / ".github/video-batch/summaries"
    for filename in SUMMARY_FILES:
        part = load_json(directory / filename)
        require(isinstance(part, dict), f"{filename}: expected a JSON object")
        for no, points in part.items():
            require(no not in result, f"Duplicate summary for {no}")
            require(isinstance(points, list) and len(points) == 5,
                    f"{no}: summary must have five points")
            for point in points:
                require(isinstance(point, list) and len(point) == 2
                        and all(isinstance(x, str) and x.strip() == x and x
                                for x in point),
                        f"{no}: invalid summary point")
            result[no] = points
    require(set(result) == {f"{n:02}" for n in range(1, 71)},
            "The six reviewed summary JSON files must cover exactly 01-70")
    return result



def current_layout_hashes():
    # Read the approved current-HEAD manifest without materializing all 4K PNGs.
    audit = json.loads(get(["git", "show",
                           "HEAD:简述重制预览/layout-audit.json"]))
    details = audit.get("articles_detail")
    require(isinstance(details, dict), "Current layout audit has no article details")
    return {
        no: normalized_hash(details.get(no, {}).get("png_sha256"),
                            f"{no} current approved summary PNG SHA256")
        for no in EXPECTED
    }


def summary_text(points):
    return "（简述：" + "".join("▸" + label + "：" + body
                              for label, body in points) + "）"


def last_chunk(data):
    return data["sentences"][-1]["chunks"][-1]


def check_script(no, candidate, original, points):
    old_last = last_chunk(original)
    old_note = old_last.get("note") or ""
    prefix = old_note.split("（简述：", 1)[0].rstrip()
    expected_note = (prefix + "\n" if prefix else "") + summary_text(points)
    require(last_chunk(candidate).get("note") == expected_note,
            f"{no}: final summary does not match the six reviewed JSON files")
    restored = copy.deepcopy(candidate)
    if "note" in old_last:
        last_chunk(restored)["note"] = old_last["note"]
    else:
        last_chunk(restored).pop("note", None)
    require(restored == original,
            f"{no}: script fields outside the final note changed")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_hash(value, description):
    require(isinstance(value, str), f"Missing {description}")
    value = value.removeprefix("SHA256=").lower()
    require(re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            f"Invalid {description}")
    return value


def probe(path):
    return json.loads(get(["ffprobe", "-v", "error", "-show_streams",
                           "-show_format", "-of", "json", path]))


def stream(info, kind):
    selected = [s for s in info["streams"] if s["codec_type"] == kind]
    require(len(selected) == 1, f"Expected exactly one {kind} stream")
    return selected[0]


def audio_hash(path):
    raw = get(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0",
               "-vn", "-c:a", "pcm_s16le", "-f", "hash", "-hash",
               "sha256", "-"]).strip()
    return normalized_hash(raw, "decoded audio SHA256")


def audio_packet_times(path):
    result = json.loads(get([
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_packets",
        "-show_entries", "packet=pts_time,dts_time,duration_time,flags", "-of",
        "json", path]))
    require(result.get("packets"), "Audio packet list is empty")
    return result["packets"]


def png_size(path):
    with path.open("rb") as stream:
        header = stream.read(24)
    require(len(header) == 24 and header[:8] == b"\x89PNG\r\n\x1a\n"
            and header[12:16] == b"IHDR", f"Invalid summary PNG: {path.name}")
    return struct.unpack(">II", header[16:24])


def finite_number(value, description):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), f"Invalid {description}")
    return float(value)



def pcm_float32_info(path, sample_rate, channels):
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-vn",
               "-ac", channels, "-ar", sample_rate, "-c:a", "pcm_f32le",
               "-f", "f32le", "-"], capture_output=True).stdout
    require(len(raw) % (4 * channels) == 0, "Invalid interleaved float32 PCM size")
    return hashlib.sha256(raw).hexdigest(), len(raw) // (4 * channels)


def video_packet_times(path):
    return json.loads(get([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_packets",
        "-show_entries", "packet=pts_time,dts_time,duration_time,flags",
        "-of", "json", path]))["packets"]


def sequence_hash(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def coded_frames_hash(path, count):
    raw = run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-an",
               "-c:v", "copy", "-frames:v", count, "-bsf:v",
               "h264_mp4toannexb,filter_units=pass_types=1-5", "-f", "h264",
               "-"], capture_output=True).stdout
    return hashlib.sha256(raw).hexdigest()


def verify_audio_audit(no, artifact, canonical_source, before_hash, after_hash, repaired):
    if int(no) < 65:
        return None
    path = artifact / f"{no}-audio-audit.json"
    require(path.is_file(), f"{no}: current MP4 audio audit is missing")
    audit = load_json(path)
    require(audit.get("article") == no and audit.get("source_commit") == BASE
            and audit.get("source_video_path") == canonical_source,
            f"{no}: audio audit does not identify the immutable BASE source")
    require(audit.get("waveform_checks_passed") is True
            and audit.get("numerical_audio_checks_passed") is True
            and audit.get("failures") == [],
            f"{no}: current numerical audio checks did not all pass")
    for name in ("current_audio_health", "canonical_mp4_loudness_check",
                 "current_within_sentence_loudness"):
        require(isinstance(audit.get(name), dict)
                and audit[name].get("failures") == [],
                f"{no}: canonical numerical audio check failed ({name})")
    require(audit["current_within_sentence_loudness"].get("suppressed_segment_candidates") == [],
            f"{no}: segment suppression candidate is unresolved")
    require(audit.get("original_audio_preserved") is (not repaired),
            f"{no}: current audit misstates whether original audio was changed")
    preservation = audit.get("preservation_failures")
    if repaired:
        require(preservation == [
            "Decoded audio or encoded AAC packets/timing changed from immutable BASE."],
            f"{no}: the intentional original-audio change must remain disclosed")
    else:
        require(preservation == [], f"{no}: original audio preservation failed")
    require(normalized_hash(audit.get("source_audio_hashes", {}).get("decoded_pcm_s16le_sha256"),
                            f"{no} audited source PCM hash") == before_hash,
            f"{no}: audio audit is not tied to the actual BASE audio")
    require(normalized_hash(audit.get("inspected_audio_hashes", {}).get("decoded_pcm_s16le_sha256"),
                            f"{no} audited final PCM hash") == after_hash,
            f"{no}: audio audit is not tied to the actual final MP4")
    return audit


def verify_authorized_repair(no, artifact, report, source, movie, canonical_source,
                             original_audio, actual_packet_match, audit):
    require(no in AUTHORIZED_REPAIRS, f"{no}: audio repair is outside the authorized scope")
    repair_path = artifact / f"{no}-audio-repair.json"
    require(repair_path.is_file(), f"{no}: audio repair evidence is missing")
    repair = load_json(repair_path)
    require(repair.get("kind") == "authorized_intentional_gain_repair"
            and repair.get("article") == no
            and repair.get("source_commit") == BASE
            and repair.get("source_video_path") == canonical_source,
            f"{no}: invalid authorization/source identity in audio repair report")
    require(repair.get("numerical_audio_checks_passed") is True
            and repair.get("no_clipped_samples") is True
            and repair.get("boundary_sensitivity", {}).get("before_finding_stable") is True
            and repair.get("boundary_sensitivity", {}).get("after_pass_stable") is True,
            f"{no}: repaired audio did not pass the established numerical/boundary checks")
    linked = report.get("audio_repair", {})
    require(linked.get("kind") == "authorized_intentional_gain_repair"
            and linked.get("report") == repair_path.name
            and normalized_hash(linked.get("report_sha256"), f"{no} linked repair SHA256")
                == sha256(repair_path)
            and linked.get("numerical_audio_checks_passed") is True
            and normalized_hash(repair.get("final_video_sha256"), f"{no} repair final video SHA256")
                == normalized_hash(report.get("video_sha256"), f"{no} final video SHA256"),
            f"{no}: verification and repair reports do not refer to the same final files")
    speech_path = artifact / f"{no}-target-speech-check.json"
    require(speech_path.is_file()
            and normalized_hash(repair.get("target_speech_check_sha256"),
                                f"{no} target speech check SHA256") == sha256(speech_path)
            and repair.get("asr_new_discrepancies") == [],
            f"{no}: repaired target sentence lacks its unchanged/new-discrepancy evidence")
    speech = load_json(speech_path)
    require(speech.get("models_verified") is True and speech.get("new_discrepancies") == [],
            f"{no}: target speech check has unresolved new discrepancies")
    require(normalized_hash(repair.get("audio_audit_report_sha256"),
                            f"{no} audio audit file SHA256")
            == sha256(artifact / f"{no}-audio-audit.json"),
            f"{no}: repair evidence refers to a different audio audit")

    sample_rate, channels = repair.get("sample_rate"), repair.get("channels")
    require(type(sample_rate) is int and type(channels) is int
            and sample_rate == int(original_audio["sample_rate"])
            and channels == original_audio["channels"],
            f"{no}: local repair must preserve source sample rate and channels")
    source_float_hash, source_frames = pcm_float32_info(source, sample_rate, channels)
    final_float_hash, final_frames = pcm_float32_info(movie, sample_rate, channels)
    require(normalized_hash(repair.get("source_decoded_float32_sha256"),
                            f"{no} repair source float32 hash") == source_float_hash,
            f"{no}: repair source PCM differs from immutable BASE")
    require(normalized_hash(repair.get("final_decoded_float32_sha256"),
                            f"{no} repair final float32 hash") == final_float_hash,
            f"{no}: repair final PCM differs from the actual MP4")
    require(repair.get("source_sample_frames") == source_frames
            and repair.get("processed_sample_frames") == source_frames
            and repair.get("final_sample_frames") == final_frames,
            f"{no}: repair PCM lengths do not match source/processing/final evidence")
    processed_hash = normalized_hash(repair.get("processed_float32_sha256"),
                                     f"{no} processed float32 hash")
    require(source_float_hash != processed_hash and source_float_hash != final_float_hash,
            f"{no}: the reported intentional repair is not reflected in PCM hashes")
    require(normalized_hash(audit["source_audio_hashes"].get("decoded_float32"),
                            f"{no} audited source float32 hash") == source_float_hash
            and normalized_hash(audit["inspected_audio_hashes"].get("decoded_float32"),
                                f"{no} audited final float32 hash") == final_float_hash,
            f"{no}: repair and audit do not inspect the same decoded PCM")
    require(repair.get("pre_encoding_outside_windows_identical") is True
            and normalized_hash(repair.get("outside_source_float32_sha256"),
                                f"{no} outside-window source hash")
            == normalized_hash(repair.get("outside_processed_float32_sha256"),
                               f"{no} outside-window processed hash"),
            f"{no}: processing-stage samples outside the authorized window changed")
    windows = repair.get("gain_windows")
    require(isinstance(windows, list) and windows,
            f"{no}: the full list of actual gain windows is missing")
    sentence, phrase = AUTHORIZED_REPAIRS[no]
    targets = [w for w in windows if w.get("sentence") == sentence and w.get("phrase") == phrase]
    require(len(targets) == 1 and (no == "70" or len(windows) == 1),
            f"{no}: the authorized target phrase is not identified unambiguously")
    target = targets[0]
    if len(windows) > 1:
        require(repair.get("outside_mask_definition")
                == "Union of every listed raised-cosine gain window, including overlaps.",
                f"{no}: unchanged samples must be measured outside all actual windows")
    for window in windows:
        require(window.get("smoothing") == "raised-cosine"
                and isinstance(window.get("sentence"), str)
                and re.fullmatch(r"S[1-9]\d*", window["sentence"])
                and isinstance(window.get("phrase"), str) and window["phrase"],
                f"{no}: an actual gain window lacks its sentence/phrase/smoothing")
        times = {key: finite_number(window.get(key), f"{no} repair {key}")
                 for key in ("start", "attack_end", "release_start", "end",
                             "core_start", "core_end")}
        require(0 <= times["start"] < times["attack_end"] <= times["release_start"]
                < times["end"] <= source_frames / sample_rate
                and times["start"] <= times["core_start"] < times["core_end"] <= times["end"]
                and finite_number(window.get("gain_db"), f"{no} gain dB") != 0,
                f"{no}: invalid actual gain envelope")
    require(0 < target["gain_db"] <= 3, f"{no}: invalid target repair gain")
    expected_gain = finite_number(
        repair.get("target_expected_net_core_gain_db", target["gain_db"] if no == "67" else None),
        f"{no} expected combined core gain")
    require(abs(finite_number(repair.get("achieved_core_gain_db"), f"{no} achieved core gain")
                - expected_gain) < .2
            and finite_number(repair.get("core_waveform_correlation"), f"{no} core correlation") > .999,
            f"{no}: repaired core waveform/net-gain evidence is incomplete")
    fade = repair.get("fade_window_peak_dbfs", {})
    require(fade and all(finite_number(v, f"{no} actual fade peak") < -70 for v in fade.values()),
            f"{no}: an actual gain ramp was not verified in quiet audio")
    require(finite_number(repair.get("final_global_peak_dbfs"), f"{no} final peak")
            <= 20 * math.log10(.99),
            f"{no}: final AAC exceeds the existing canonical 0.99 peak ceiling")
    if len(windows) > 1:
        measured = repair.get("all_windows_fade_5_10ms_measurements")
        require(isinstance(measured, list) and len(measured) == len(windows),
                f"{no}: all actual gain-window boundary measurements are required")
    for extra in repair.get("additional_speech_checks", []):
        name = extra.get("report", "")
        require(re.fullmatch(no + r"-S[1-9]\d*-speech-check\.json", name) is not None
                and extra.get("new_discrepancies") == [],
                f"{no}: invalid additional affected-sentence speech check")
        file = artifact / name
        require(file.is_file() and sha256(file) == normalized_hash(extra.get("sha256"), f"{no} extra speech SHA256"),
                f"{no}: additional affected-sentence speech evidence is missing")
        result = load_json(file)
        require(result.get("models_verified") is True and result.get("new_discrepancies") == [],
                f"{no}: an additional affected sentence has new speech discrepancies")

    aac = repair.get("aac", {})
    require(aac.get("codec") == "aac"
            and aac.get("aligned_lag_samples") == 0
            and aac.get("sample_alignment_passed") is True
            and aac.get("outside_windows_quality_passed") is True
            and aac.get("packet_timings_identical") is actual_packet_match,
            f"{no}: AAC time-alignment evidence disagrees with the actual audio")
    snr = finite_number(aac.get("outside_windows_snr_db"), f"{no} AAC outside-window SNR")
    correlation = finite_number(aac.get("outside_windows_correlation"),
                                f"{no} AAC outside-window correlation")
    require(snr >= REPAIR_MIN_SNR_DB and correlation >= REPAIR_MIN_CORRELATION
            and correlation <= 1.000000001,
            f"{no}: AAC outside-window fidelity/alignment did not meet the repair standard")
    if not actual_packet_match:
        before, after = audio_packet_times(source), audio_packet_times(movie)
        common_packets = min(len(before), len(after))
        require(before[:common_packets-1] == after[:common_packets-1]
                and abs(len(after) - len(before)) <= 1
                and abs(final_frames - source_frames) <= 1024
                and aac.get("decoded_tail_sample_delta") == final_frames - source_frames
                and min(source_frames, final_frames) / sample_rate
                    - report["source_voice_endpoint_seconds"] > .8,
                f"{no}: AAC timing differs beyond documented trailing silent padding")
    video_evidence = repair.get("video", {})
    require(video_evidence.get("all_coded_pictures_identical") is True
            and video_evidence.get("packet_timings_identical") is True,
            f"{no}: repair report does not preserve the rendered video")
    packets = video_packet_times(movie)
    actual_timing_hash = sequence_hash(packets)
    actual_picture_hash = coded_frames_hash(movie, report["output_frames"])
    for side in ("input", "final"):
        require(normalized_hash(video_evidence.get(f"{side}_packet_timing_sha256"),
                                f"{no} {side} video packet timing hash") == actual_timing_hash,
                f"{no}: video PTS/DTS changed during audio repair")
        require(normalized_hash(video_evidence.get(f"{side}_coded_sha256"),
                                f"{no} {side} coded-picture hash") == actual_picture_hash,
                f"{no}: coded video pictures changed during audio repair")
    prefix = report.get("copied_original_frames")
    require(type(prefix) is int and 0 < prefix <= report["output_frames"],
            f"{no}: missing copied-original-frame evidence")
    require(coded_frames_hash(source, prefix) == coded_frames_hash(movie, prefix)
            and video_packet_times(source)[:prefix] == packets[:prefix],
            f"{no}: untouched H264 prefix no longer matches immutable BASE")
    return repair


def verify_one(no, artifact, canonical_source, points, temporary, layout_hashes):
    script_file = artifact / f"{no}-script.json"
    report_file = artifact / f"{no}-verification.json"
    card_file = artifact / f"{no}-简述.png"
    require(all(p.is_file() for p in (script_file, report_file, card_file)),
            f"{no}: script, report or summary PNG is missing")
    movies = list(artifact.rglob("*.mp4"))
    require(len(movies) == 1, f"{no}: expected exactly one final MP4")
    movie = movies[0]
    require(not any(p.is_symlink() for p in
                    (script_file, report_file, card_file, movie)),
            f"{no}: artifact symlinks are not accepted")
    report = load_json(report_file)
    require(report.get("article") == no, f"{no}: wrong report article")
    require(report.get("source_commit") == BASE,
            f"{no}: report does not refer to the immutable BASE")
    require(report.get("source") == canonical_source,
            f"{no}: source filename differs from the canonical BASE path")
    require(report.get("end_page_frames") == 60
            and report.get("end_page_seconds") == 2,
            f"{no}: summary must be exactly 60 frames / 2 seconds")
    require(report.get("width") == 3840 and report.get("height") == 2160,
            f"{no}: report must identify native 3840x2160 output")
    repaired = no in AUTHORIZED_REPAIRS
    require(report.get("original_audio_identical") is (not repaired),
            f"{no}: original-audio identity must be reported truthfully")
    require(report.get("body_script_identical") is True,
            f"{no}: body script verification failed")
    if not repaired:
        require(report.get("original_audio_packet_timings_identical") is True,
                f"{no}: original audio timing verification failed")
        require(not (artifact / f"{no}-audio-repair.json").exists(),
                f"{no}: unexpected repair report outside the authorized two articles")
    require(report.get("layout", {}).get("items") == 5,
            f"{no}: summary layout must contain five points")
    actual_video_hash = sha256(movie)
    require(actual_video_hash == normalized_hash(report.get("video_sha256"),
                                                f"{no} video SHA256"),
            f"{no}: final MP4 does not match its verification report")
    require(png_size(card_file) == (3840, 2160),
            f"{no}: summary PNG is not native 4K")
    card_hash = sha256(card_file)
    require(card_hash == layout_hashes[no],
            f"{no}: artifact summary PNG differs from the current approved layout audit")

    original_script = json.loads(get([
        "git", "show", f"{BASE}:视频/脚本/{no}.json"]))
    candidate_script = load_json(script_file)
    check_script(no, candidate_script, original_script, points)

    info = probe(movie)
    video = stream(info, "video")
    require(video["codec_name"] == "h264"
            and (video["width"], video["height"]) == (3840, 2160),
            f"{no}: actual MP4 is not 4K H264")
    require(Fraction(video["avg_frame_rate"]) == 30,
            f"{no}: actual MP4 is not 30 fps")
    total_frames = int(video["nb_frames"])
    start_frame = report.get("summary_start_frame")
    require(type(start_frame) is int and start_frame > 0,
            f"{no}: invalid summary start frame")
    require(type(report.get("output_frames")) is int
            and report["output_frames"] == total_frames
            and total_frames == start_frame + 60,
            f"{no}: actual frame count does not give a 60-frame end page")
    start_seconds = finite_number(report.get("summary_start_seconds"),
                                  f"{no} summary start seconds")
    delay = finite_number(report.get("delay_after_voice_seconds"),
                          f"{no} delay after voice")
    require(abs(start_seconds - start_frame / 30) <= .000002,
            f"{no}: summary frame and timestamp disagree")
    require(0 <= delay <= 1 / 30 + .000002,
            f"{no}: unwanted waiting between voice and summary")
    require(abs(float(video["duration"]) - (start_seconds + 2)) <= .00001,
            f"{no}: actual video duration does not end after two summary seconds")
    if "source_voice_endpoint_seconds" in report:
        end = finite_number(report["source_voice_endpoint_seconds"],
                            f"{no} source voice endpoint")
        require(abs(start_seconds - end - delay) <= .000002,
                f"{no}: voice endpoint and transition delay disagree")

    # Materialize one immutable source blob at a time; never check it out.
    source = temporary / f"{no}-source.mp4"
    try:
        with source.open("wb") as output:
            run(["git", "show", f"{BASE}:{canonical_source}"], stdout=output,
                stderr=subprocess.PIPE)
        original_info = probe(source)
        original_video = stream(original_info, "video")
        require((original_video["width"], original_video["height"]) == (3840, 2160),
                f"{no}: BASE source is not native 4K")
        if "source_frames" in report:
            require(report["source_frames"] == int(original_video["nb_frames"]),
                    f"{no}: BASE source frame count disagrees with report")
        before_audio, after_audio = stream(original_info, "audio"), stream(info, "audio")
        for key in ("codec_name", "sample_rate", "channels", "channel_layout"):
            require(before_audio.get(key) == after_audio.get(key),
                    f"{no}: original audio stream configuration changed ({key})")
        before_hash, after_hash = audio_hash(source), audio_hash(movie)
        require(after_hash == normalized_hash(report.get("audio_sha256"), f"{no} audio SHA256"),
                f"{no}: report audio hash does not match the actual final MP4")
        packet_match = audio_packet_times(source) == audio_packet_times(movie)
        audit = verify_audio_audit(no, artifact, canonical_source,
                                   before_hash, after_hash, repaired)
        if repaired:
            require(before_hash != after_hash,
                    f"{no}: authorized audio change must remain disclosed")
            require(report.get("original_audio_packet_timings_identical") is packet_match,
                    f"{no}: report misstates source audio packet timing preservation")
            verify_authorized_repair(no, artifact, report, source, movie,
                                     canonical_source, before_audio, packet_match, audit)
        else:
            require(before_hash == after_hash, f"{no}: decoded original audio samples changed")
            require(packet_match, f"{no}: original audio packet timestamps changed")
    finally:
        source.unlink(missing_ok=True)

    return {
        "no": no, "source": canonical_source, "movie": movie,
        "script": script_file, "report": report_file, "card": card_file,
        "title_en": candidate_script["title_en"],
        "title_zh": candidate_script["title_zh"],
        "video_sha256": actual_video_hash, "audio_sha256": after_hash,
        "summary_png_sha256": card_hash,
        "source_audio_sha256": before_hash, "audio_preserved": not repaired,
        "audio_packet_timings_identical": packet_match,
        "audio_repaired": repaired,
        "audio_audit": artifact / f"{no}-audio-audit.json" if audit else None,
        "audio_repair": artifact / f"{no}-audio-repair.json" if repaired else None,
        "artifact": artifact,
        "summary_start_seconds": start_seconds, "output_frames": total_frames,
    }


def write_index(verified, duplicate_paths):
    records = [{
        "article": item["no"], "source": item["source"],
        "video_sha256": item["video_sha256"],
        "summary_png_sha256": item["summary_png_sha256"],
        "audio_sha256": item["audio_sha256"],
        "source_audio_sha256": item["source_audio_sha256"],
        "collector_audio_pcm_identical_to_BASE": item["audio_preserved"],
        "collector_audio_packet_timings_identical_to_BASE": item["audio_packet_timings_identical"],
        "audio_status": "authorized_local_gain_repair" if item["audio_repaired"] else "identical_to_BASE",
        "summary_start_seconds": item["summary_start_seconds"],
        "output_frames": item["output_frames"],
    } for item in verified]
    manifest = {
        "status": "69_existing_videos_verified_article_05_separate",
        "source_commit": BASE, "expected_total_articles": 70,
        "verified_articles": 69, "not_verified_in_this_batch": ["05"],
        "audio_identical_to_BASE_count": 67,
        "authorized_local_audio_repair_articles": ["67", "70"],
        "summary_seconds": 2, "summary_frames": 60, "width": 3840, "height": 2160,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "removed_task_branch_duplicate_paths": duplicate_paths,
        "articles": records,
    }
    directory = ROOT / REPORT_DIR
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# 简述重制：69篇已核验，第05篇独立补做", "",
        "本次已收齐并独立复核69篇已有原片，范围为01—70篇中的第05篇以外各篇。",
        "第05篇由独立流程补做，未计入本次验收。本索引不代表70篇全部完成；"
        "第05篇通过核验后，再更新70篇全量索引。", "",
        "各篇均为3840×2160、30帧/秒；正文读完后的下一帧切到独立简述页，"
        "简述显示60帧，即2秒。正文脚本除最后的简述外与基准一致。",
        "收集时独立比对了基准原片的完整解码音频及音轨时序，其中67份视频的原配音保持一致。",
        "第67、70篇根据本次实测，对已授权的实际窗口作局部增益修复及必要的句间平衡，并重新编码AAC；"
        "这两篇的原声确有改变，核验报告明确记录，不能称为全片原声相同。",
        "修声证据包含精确窗口、增益和平滑、编码前窗口外样本保全、AAC对齐和窗口外保真，"
        "以及修后数值检查和修声前后H264画面及时序一致性。",
        "第65—70篇另附本次MP4音频实测报告，范围和局限以各报告为准。", "",
        "视频沿用基准原文件名，避免同篇因冒号替换产生重复文件。"
        "核验报告原样保存；完整清单见manifest.json。", "",
        "| 篇 | 标题 | 4K视频 | 简述页 | 核验 | 音频 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in verified:
        no = item["no"]
        title = item["title_zh"].replace("|", "／")
        video_url = quote("../" + item["source"], safe="/")
        card_url = quote("../" + PREVIEW_DIR + f"/{no}.png", safe="/")
        audio_link = (f"[实测]({no}-audio-audit.json)" if item["audio_audit"] else "原样")
        if item["audio_repaired"]:
            audio_link += f" / [修声]({no}-audio-repair.json)"
        lines.append(f"| {no} | {title} | [视频]({video_url}) | "
                     f"[简述]({card_url}) | [报告]({no}.json) | {audio_link} |")
    (directory / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=ROOT / "batch-artifacts")
    parser.add_argument("--check-only", action="store_true",
                        help="Verify all 69 articles without updating delivery files")
    args = parser.parse_args()
    os.chdir(ROOT)
    branch = get(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    require(branch not in ("main", "master")
            and os.environ.get("GITHUB_REF_NAME") not in ("main", "master"),
            "Do not collect results on main/master")
    if not args.check_only:
        require(branch in ("HEAD", TASK_BRANCH),
                "Collection is limited to the isolated task branch")
    sources, base_paths = source_manifest()
    summaries = read_summaries()
    layout_hashes = current_layout_hashes()
    artifacts = args.artifacts.resolve()
    require(artifacts.is_dir(), "Artifact download directory is missing")
    missing = [no for no in EXPECTED
               if not (artifacts / f"reviewed-video-{no}").is_dir()]
    require(not missing, "Incomplete batch; missing articles: " + ", ".join(missing))

    verified = []
    temporary_parent = os.environ.get("RUNNER_TEMP")
    with tempfile.TemporaryDirectory(prefix="summary-collect-",
                                     dir=temporary_parent) as work:
        for no in EXPECTED:
            item = verify_one(no, artifacts / f"reviewed-video-{no}",
                              sources[no], summaries[no], Path(work), layout_hashes)
            verified.append(item)
            audio_state = "authorized local audio repair" if item["audio_repaired"] else "original audio"
            print(f"{no}: verified 4K, 60 summary frames, {audio_state}, final-note-only script",
                  flush=True)
    require(len(verified) == 69, "Incomplete batch; nothing will be collected")

    # Only remove task-branch name variants absent from immutable BASE.
    # Article 05 and every other directory are outside this cleanup scope.
    duplicates = []
    for path in git_paths("HEAD"):
        match = re.fullmatch(r"最终版4K视频/(\d{2}) - [^/]+\.mp4", path)
        if match and match.group(1) in sources:
            no = match.group(1)
            if path != sources[no]:
                require(path not in base_paths, "Refusing to remove a BASE source file")
                duplicates.append(path)
    if args.check_only:
        print(f"All 69 existing videos verified (67 audio-preserved, 67/70 locally repaired). "
              f"Article 05 remains separate. "
              f"Task-branch duplicate names eligible for cleanup: {len(duplicates)}")
        return

    for directory in (ROOT / VIDEO_DIR, ROOT / "视频/脚本",
                      ROOT / REPORT_DIR, ROOT / PREVIEW_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    for item in verified:
        no = item["no"]
        shutil.copyfile(item["movie"], ROOT / item["source"])
        shutil.copyfile(item["script"], ROOT / f"视频/脚本/{no}.json")
        shutil.copyfile(item["report"], ROOT / REPORT_DIR / f"{no}.json")
        shutil.copyfile(item["card"], ROOT / PREVIEW_DIR / f"{no}.png")
        for kind in ("audio-audit", "audio-repair", "target-speech-check", "candidate-comparison"):
            for suffix in (".json", ".md"):
                extra = item["artifact"] / f"{no}-{kind}{suffix}"
                if extra.is_file():
                    shutil.copyfile(extra, ROOT / REPORT_DIR / extra.name)
        for extra in item["artifact"].glob(f"{no}-S*-speech-check.json"):
            if re.fullmatch(no + r"-S[1-9]\d*-speech-check\.json", extra.name):
                shutil.copyfile(extra, ROOT / REPORT_DIR / extra.name)
    for path in duplicates:
        run(["git", "rm", "--sparse", "--ignore-unmatch", "--", path])
    write_index(verified, duplicates)
    print("Collected 69 verified 4K videos: 67 audio-preserved, articles 67/70 locally repaired. "
          "Article 05 is not counted as complete.")
    print("No commit or push was made; the workflow must stage and commit these results.")


if __name__ == "__main__":
    main()

