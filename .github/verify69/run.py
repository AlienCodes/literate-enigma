#!/usr/bin/env python3
"""One read-only integration of pinned existing69 media with the unchanged collector.

Uses only the established AlienCodes/literate-enigma backup work branches.
Downloads final media/public QC on this GitHub runner, never GT/models/caches.
No rendering, media upload, commits, pushes or updates to the root work branch.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / ".github/verify69"
REPORT = ROOT / "verify69-report"
ARTIFACTS = ROOT / "verify69-artifacts"
EXPECTED = {f"{n:02}" for n in range(1, 71) if n != 5}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def main():
    os.chdir(ROOT)
    REPORT.mkdir(exist_ok=True)
    report = {"kind": "read-only-existing69-collector-integration", "passed": False,
              "source_root_commit": "bd8e8fcd38877d407fa4284fc9088e7325307f12",
              "source_base_commit": "c9d52b26fe981ef8e4c412189ca289716ab8bf00",
              "article05_excluded": True, "rendering_performed": False,
              "media_uploaded": False, "root_ref_changed": False,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "stage": "start"}
    result_path = REPORT / "summary.json"

    def save():
        result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    try:
        D = module("pinned_public_media_download", ROOT / ".github/video-batch/download_reviewed.py")
        config_path = TASK / "collection.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        D.require(config.get("repository") == D.REPOSITORY
                  and config.get("destination_branch") == D.TARGET_BRANCH,
                  "Unexpected source repository/work branch")
        normal = [D.validate_source(x, "ordinary") for x in config["ordinary_runs"]]
        repairs = [D.validate_source(x, "repair") for x in config["repair_runs"]]
        selected = set().union(*(set(x["articles"]) for x in normal + repairs))
        D.require(selected == EXPECTED, "Pinned artifacts must cover exactly the existing69")
        D.require(set().union(*(set(x["articles"]) for x in repairs)) == {"67", "70"},
                  "Pinned repair outputs must be exactly 67 and 70")
        D.require(not ARTIFACTS.exists(), "Use a fresh read-only integration workspace")
        ARTIFACTS.mkdir()
        report.update(config_sha256=digest(config_path), selected_articles=sorted(selected),
                      collector_sha256=digest(ROOT / ".github/video-batch/collect.py"),
                      downloader_sha256=digest(ROOT / ".github/video-batch/download_reviewed.py"),
                      downloaded_artifacts=[])
        report["verification_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        save()
        api = D.GitHub()
        # Deliberately call only the reusable helpers, not D.main(), since 05 is
        # still pending and this test must not claim to finalize ALL70.
        with tempfile.TemporaryDirectory(prefix="verify69-download-", dir=os.environ.get("RUNNER_TEMP")) as tmp:
            for role, sources in (("ordinary", normal), ("repair", repairs)):
                for source in sources:
                    report["stage"] = f"source-run-{source['run_id']}"
                    save()
                    run, rows = D.checked_run(api, source, role)
                    for no in source["articles"]:
                        report["stage"] = f"download-{no}"
                        save()
                        entry = D.one_artifact(api, rows, source, run, role, no, ARTIFACTS, Path(tmp))
                        report["downloaded_artifacts"].append(entry)
                        save()
        D.require(len(report["downloaded_artifacts"]) == 69,
                  "The fixed selection must produce 69 unique artifact directories")
        # Metadata only: measure any container tail beyond the new 60-frame card.
        # This observation adds no gate and never changes audio/video or standards.
        report["stage"] = "read-final-duration-metadata"
        report["duration_metadata"] = []
        report["duration_metadata_errors"] = []
        for no in sorted(selected):
            try:
                movies = list((ARTIFACTS / f"reviewed-video-{no}").glob("*.mp4"))
                if len(movies) != 1:
                    raise RuntimeError("Expected one already-downloaded final MP4")
                raw = subprocess.check_output([
                    "ffprobe", "-v", "error", "-show_entries",
                    "format=duration:stream=codec_type,duration", "-of", "json", str(movies[0])], text=True)
                info = json.loads(raw)
                def seconds(value):
                    try:
                        n = float(value)
                        return n if math.isfinite(n) else None
                    except (TypeError, ValueError):
                        return None
                fmt = seconds(info.get("format", {}).get("duration"))
                video = seconds(next((s.get("duration") for s in info.get("streams", [])
                                      if s.get("codec_type") == "video"), None))
                audio = seconds(next((s.get("duration") for s in info.get("streams", [])
                                      if s.get("codec_type") == "audio"), None))
                report["duration_metadata"].append({
                    "article": no, "format_duration": fmt, "video_duration": video, "audio_duration": audio,
                    "format_minus_video_seconds": None if fmt is None or video is None else fmt - video})
            except Exception as exc:
                report["duration_metadata_errors"].append(f"{no}: {type(exc).__name__}: {exc}")
        measured = [x for x in report["duration_metadata"] if x["format_minus_video_seconds"] is not None]
        report["max_format_minus_video"] = max(measured, key=lambda x: x["format_minus_video_seconds"]) if measured else None
        print("Maximum format.duration - video.duration:", json.dumps(report["max_format_minus_video"]), flush=True)
        save()
        report["stage"] = "unchanged-collector-check-only"
        save()
        log_path = REPORT / "collector.log"
        with log_path.open("w", encoding="utf-8") as log:
            completed = subprocess.run([
                sys.executable, "-u", ".github/video-batch/collect.py",
                "--artifacts", str(ARTIFACTS), "--check-only"], cwd=ROOT,
                stdout=log, stderr=subprocess.STDOUT)
        report["collector_returncode"] = completed.returncode
        report["collector_log_tail"] = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-45:]
        print("\n".join(report["collector_log_tail"]), flush=True)
        D.require(completed.returncode == 0, "Existing69 collector returned a nonzero result; inspect collector.log")
        report.update(passed=True, stage="read-only-existing69-integration-passed")
        print("The existing69 real artifacts passed the unchanged collector. Article05 and ALL70 publication remain separate.")
    except Exception as exc:
        report["first_error"] = f"{type(exc).__name__}: {exc}"
        print(report["first_error"], flush=True)
        # No HTTP bodies or signed URLs are printed; downloader errors are sanitized.
        if report["stage"] == "unchanged-collector-check-only":
            print("Collector schema/interface failure is retained in the compact report.")
        raise
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        save()


if __name__ == "__main__":
    main()
