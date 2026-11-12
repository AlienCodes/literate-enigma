#!/usr/bin/env python3
"""Assemble ALL70 only after collector69 and the independent canonical05 both pass.

All source/destination branches belong to the already-used backup repository
AlienCodes/literate-enigma (original CLAUDE rule 3 and the approved Article03
sample). No new mirror, GT, original a.wav, models or private caches are exported.
This script never commits or pushes; the supplied workflow makes one final commit.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / ".github/video-batch"
REPOSITORY = "AlienCodes/literate-enigma"
BRANCH = "codex/finish-05-and-summaries-20261112"
ARTICLE05_PATH = "最终版4K视频/05 - The Fingerprint in the Blood - 血里的指纹.mp4"
NUMBERS = tuple(f"{n:02}" for n in range(1, 71))
PACKAGE = ROOT / "complete-70-delivery"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def get(args):
    return subprocess.run([str(x) for x in args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def collector():
    spec = importlib.util.spec_from_file_location("existing69_collector", TASK / "collect.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_repository():
    remote = get(["git", "remote", "get-url", "origin"]).strip()
    if remote.startswith("git@github.com:"):
        name = remote.removeprefix("git@github.com:").removesuffix(".git")
    else:
        parsed = urlsplit(remote)
        require(parsed.scheme == "https" and parsed.hostname == "github.com",
                "Only the approved existing GitHub backup repository is permitted")
        name = parsed.path.strip("/").removesuffix(".git")
    require(name.lower() == REPOSITORY.lower(), "Unexpected collection repository")
    branch = get(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    require(branch in ("HEAD", BRANCH)
            and os.environ.get("GITHUB_REF_NAME", BRANCH) == BRANCH,
            "Final collection is limited to the isolated backup work branch")


def load_inputs(config_path, artifact_root):
    config = read(config_path)
    receipt = read(artifact_root / "collection-receipt.json")
    require(config.get("repository") == receipt.get("repository") == REPOSITORY
            and config.get("destination_branch") == receipt.get("destination_branch") == BRANCH,
            "Download provenance identifies a different source/destination")
    require(receipt.get("config_sha256") == sha(config_path),
            "Download receipt does not match the pinned collection configuration")
    require(set(receipt.get("final_sources", {})) == set(NUMBERS),
            "Not all 70 final source selections were downloaded")
    fifth = config.get("article05_run")
    require(isinstance(fifth, dict) and isinstance(fifth.get("commit"), str)
            and re.fullmatch(r"[0-9a-f]{40}", fifth["commit"]),
            "Article05 successful producer commit is not pinned")
    selected = receipt["final_sources"]["05"]
    require(selected.get("role") == "article05"
            and selected.get("run_conclusion") == "success"
            and selected.get("run_id") == fifth.get("run_id")
            and selected.get("commit") == fifth["commit"]
            and selected.get("branch") == fifth.get("branch") == BRANCH
            and selected.get("workflow_path") == fifth.get("workflow_path")
                == ".github/workflows/produce05-canonical4K.yml"
            and selected.get("artifact_name") == "article05-canonical-4K-final",
            "Article05 artifact is not the pinned successful official producer result")
    return config, receipt, fifth


def layout_details():
    layout = json.loads(get(["git", "show", "HEAD:简述重制预览/layout-audit.json"]))
    details = layout.get("articles_detail")
    require(isinstance(details, dict) and set(NUMBERS) <= set(details),
            "The current HEAD layout audit must include all 70 cards")
    return details


def validate05(C, directory, fifth, summaries, details):
    require(directory.is_dir(), "Canonical05 final artifact is missing")
    allowed = {"05-status.json", "05-summary-verification.json",
               "05-4K-读完即转简述2秒.mp4"}
    require({p.name for p in directory.iterdir() if p.is_file()} == allowed,
            "Canonical05 artifact must contain only the final MP4 and two public reports")
    require(not any(p.is_symlink() for p in directory.iterdir()), "Canonical05 symlinks are forbidden")
    status_path = directory / "05-status.json"
    summary_path = directory / "05-summary-verification.json"
    movie = directory / "05-4K-读完即转简述2秒.mp4"
    status, verification = read(status_path), read(summary_path)
    require(status.get("article") == verification.get("article") == "05"
            and status.get("passed") is True
            and status.get("canonical_pipeline_passed") is True
            and status.get("checks_unchanged") is True
            and verification.get("canonical_pipeline_passed") is True,
            "Canonical05 did not pass the unchanged official full production pipeline")
    require(status.get("source_kind") == verification.get("source_kind") == "new-canonical-4K",
            "Article05 must identify a newly made canonical 4K source, never a BASE source")
    require(status.get("canonical_source_commit") == verification.get("source_commit") == fifth["commit"],
            "Canonical05 reports do not match the pinned successful producer commit")
    require(status.get("voice_unchanged") is True
            and verification.get("original_audio_identical") is True
            and verification.get("original_audio_packet_timings_identical") is True,
            "Article05 summary processing did not preserve its newly verified canonical voice")
    canonical_hash = C.normalized_hash(status.get("canonical_video_sha256"), "05 canonical source SHA256")
    require(canonical_hash == C.normalized_hash(verification.get("canonical_source_video_sha256"),
                                              "05 canonical source verification SHA256"),
            "Canonical05 source hashes disagree between official reports")
    movie_hash = sha(movie)
    require(movie_hash == C.normalized_hash(status.get("video_sha256"), "05 status final video SHA256")
            == C.normalized_hash(verification.get("video_sha256"), "05 final video SHA256"),
            "Canonical05 final MP4 does not match both official reports")
    video = C.stream(C.probe(movie), "video")
    require(video.get("codec_name") == "h264"
            and (video.get("width"), video.get("height")) == (3840, 2160)
            and Fraction(video["avg_frame_rate"]) == 30,
            "Canonical05 final MP4 is not native 4K H264 at 30 fps")
    require(verification.get("end_page_frames") == 60
            and verification.get("end_page_seconds") == status.get("summary_seconds") == 2,
            "Canonical05 summary must contain exactly 60 frames / 2 seconds")
    start_frame = verification.get("summary_start_frame")
    total = int(video["nb_frames"])
    require(type(start_frame) is int and start_frame > 0
            and total == start_frame + 60
            and verification.get("output_frames") == status.get("video_frames") == total,
            "Canonical05 actual frame count disagrees with summary timing")
    start = C.finite_number(verification.get("summary_start_seconds"), "05 summary start")
    delay = C.finite_number(verification.get("delay_after_voice_seconds"), "05 summary delay")
    endpoint = C.finite_number(verification.get("source_voice_endpoint_seconds"), "05 voice endpoint")
    require(0 <= delay <= 1 / 30 + .000002
            and abs(start - start_frame / 30) <= .000002
            and abs(start - endpoint - delay) <= .000002
            and abs(float(video["duration"]) - start - 2) <= .00001
            and abs(float(status.get("summary_start_seconds")) - start) <= .000002
            and abs(float(status.get("delay_after_voice_seconds")) - delay) <= .000002,
            "Canonical05 does not switch immediately and end after two summary seconds")
    audio_hash = C.audio_hash(movie)
    require(audio_hash == C.normalized_hash(verification.get("audio_sha256"), "05 actual decoded PCM SHA256"),
            "Canonical05 final decoded audio does not match its official summary verification")
    text_hash = hashlib.sha256(C.summary_text(summaries["05"]).encode("utf-8")).hexdigest()
    png_hash = C.normalized_hash(details["05"].get("png_sha256"), "05 current approved card SHA256")
    require(C.normalized_hash(verification.get("summary_text_sha256"), "05 summary text SHA256") == text_hash
            and C.normalized_hash(verification.get("summary_png_sha256"), "05 source summary PNG SHA256") == png_hash,
            "Canonical05 uses a stale summary text/card rather than the current reviewed ALL70 version")
    return {"article": "05", "source_kind": "new-canonical-4K", "source_commit": fifth["commit"],
            "video_path": ARTICLE05_PATH, "video_sha256": movie_hash,
            "audio_sha256": audio_hash, "audio_status": "new_canonical_audio_full_pipeline_passed",
            "summary_png_sha256": png_hash, "summary_text_sha256": text_hash,
            "summary_start_seconds": start, "output_frames": total,
            "movie": movie, "status_file": status_path, "summary_file": summary_path}


def canonical_paths(C):
    paths, _ = C.source_manifest()
    return {**paths, "05": ARTICLE05_PATH}


def unique_videos(C, expected):
    physical = {p.relative_to(ROOT).as_posix() for p in (ROOT / C.VIDEO_DIR).rglob("*.mp4")}
    tracked = set(get(["git", "ls-files", "-z", "--", C.VIDEO_DIR]).split("\0"))
    tracked = {p for p in tracked if p.endswith(".mp4")}
    require(physical == set(expected.values()) and tracked <= set(expected.values()),
            "The final directory/index does not contain exactly one canonical video per article")


def report_files(C, no):
    names = [f"{no}.json", f"{no}-status.json"]
    names += [f"{no}-{kind}{suffix}" for kind in
              ("audio-audit", "audio-repair", "target-speech-check", "candidate-comparison")
              for suffix in (".json", ".md")]
    files = [ROOT / C.REPORT_DIR / name for name in names if (ROOT / C.REPORT_DIR / name).is_file()]
    files += [p for p in (ROOT / C.REPORT_DIR).glob(f"{no}-S*-speech-check.json")
              if re.fullmatch(no + r"-S[1-9]\d*-speech-check\.json", p.name)]
    return files


def update_all70(C, fifth, details, receipt, config_path, artifact_root):
    destination = ROOT / ARTICLE05_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fifth["movie"], destination)
    report_dir = ROOT / C.REPORT_DIR
    shutil.copyfile(fifth["summary_file"], report_dir / "05.json")
    shutil.copyfile(fifth["status_file"], report_dir / "05-status.json")
    card = ROOT / C.PREVIEW_DIR / "05.png"
    with card.open("wb") as stream:
        subprocess.run(["git", "show", "HEAD:简述重制预览/05.png"], cwd=ROOT, check=True, stdout=stream)
    require(sha(card) == fifth["summary_png_sha256"] and C.png_size(card) == (3840, 2160),
            "Current HEAD Article05 card differs from its approved layout hash")
    manifest = read(report_dir / "manifest.json")
    require(manifest.get("verified_articles") == 69
            and {x["article"] for x in manifest["articles"]} == set(C.EXPECTED),
            "Existing69 collection has not passed before ALL70 finalization")
    fifth_public = {k: v for k, v in fifth.items() if k not in ("movie", "status_file", "summary_file")}
    # This is the existing public repository script, updated only in its final
    # summary note. The canonical05 producer's private working script is not read
    # or exported; its independent status/verification still governs the video.
    public_commit = get(["git", "rev-parse", "HEAD"]).strip()
    public_original = json.loads(get(["git", "show", f"{public_commit}:视频/脚本/05.json"]))
    public_updated = copy.deepcopy(public_original)
    points = C.read_summaries()["05"]
    prefix = (C.last_chunk(public_original).get("note") or "").split("（简述：", 1)[0].rstrip()
    C.last_chunk(public_updated)["note"] = (prefix + "\n" if prefix else "") + C.summary_text(points)
    C.check_script("05", public_updated, public_original, points)
    public_path = ROOT / "视频/脚本/05.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(public_updated, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fifth_public["public_script_source_commit"] = public_commit
    fifth_public["public_script_scope"] = "public-repository-final-summary-note-only"
    rows = manifest["articles"] + [fifth_public]
    rows.sort(key=lambda x: x["article"])
    paths = canonical_paths(C)
    unique_videos(C, paths)
    for row in rows:
        no = row["article"]
        row["video_path"] = paths[no]
        require(sha(ROOT / paths[no]) == row["video_sha256"], f"{no}: copied final video hash changed")
        card = ROOT / C.PREVIEW_DIR / f"{no}.png"
        require(sha(card) == details[no]["png_sha256"], f"{no}: final card differs from current HEAD layout")
        row["summary_png_sha256"] = sha(card)
        row["public_qc_sha256"] = {p.name: sha(p) for p in report_files(C, no)}
    receipt_target = report_dir / "collection-receipt.json"
    shutil.copyfile(artifact_root / "collection-receipt.json", receipt_target)
    manifest.update(status="all_70_verified_completed", expected_total_articles=70,
                    verified_articles=70, not_verified_in_this_batch=[],
                    audio_identical_to_BASE_count=67,
                    authorized_local_audio_repair_articles=["67", "70"],
                    newly_produced_canonical_articles=["05"], articles=rows,
                    collection_config_sha256=sha(config_path), collection_receipt_sha256=sha(receipt_target),
                    finalized_at_utc=datetime.now(timezone.utc).isoformat())
    manifest["existing_69_source_commit"] = manifest.pop("source_commit", C.BASE)
    (report_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 70篇4K视频：简述重制完成", "",
             "70篇已全部收齐并通过最终核验，逐篇只保留一个采用原始规范文件名的4K视频。",
             "全部为3840×2160、30帧/秒；正文读完立即切到独立简述页，显示60帧，即2秒。",
             "简述文字与六份审校JSON一致，全部卡片与当前排版核验图像哈希一致。", "",
             "67份旧视频的原配音保持一致；第67、70篇根据实测证据作局部修声，真实范围和增益曲线见修声报告。",
             "第05篇为新制作的canonical 4K成片，原生产job的完整音频门和4K流程均已通过，"
             "没有把它假称为原基准中已有的成片。",
             "第65—70篇附本次MP4音频实测；各项复核范围、局限和源run信息均保留在报告中。", "",
             "| 篇 | 标题 | 4K视频 | 简述页 | 核验 |",
             "| --- | --- | --- | --- | --- |"]
    for row in rows:
        no = row["article"]
        title = ("血里的指纹" if no == "05" else read(ROOT / f"视频/脚本/{no}.json")["title_zh"]).replace("|", "／")
        lines.append(f"| {no} | {title} | [视频]({quote('../'+paths[no], safe='/')}) | "
                     f"[简述]({quote('../'+C.PREVIEW_DIR+'/'+no+'.png', safe='/')}) | [报告]({no}.json) |")
    (report_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def verify_final(C, manifest, summaries, details, config_path):
    require(manifest.get("status") == "all_70_verified_completed"
            and manifest.get("verified_articles") == 70
            and manifest.get("not_verified_in_this_batch") == []
            and manifest.get("audio_identical_to_BASE_count") == 67
            and manifest.get("authorized_local_audio_repair_articles") == ["67", "70"]
            and manifest.get("newly_produced_canonical_articles") == ["05"],
            "Final manifest does not identify all 70 verified results truthfully")
    rows = {r["article"]: r for r in manifest["articles"]}
    require(set(rows) == set(NUMBERS) and len(manifest["articles"]) == 70, "Final manifest article set is incomplete")
    paths = canonical_paths(C)
    unique_videos(C, paths)
    require(manifest.get("collection_config_sha256") == sha(config_path)
            and manifest.get("collection_receipt_sha256") == sha(ROOT / C.REPORT_DIR / "collection-receipt.json"),
            "Pinned collection provenance changed during finalization/rebase")
    for no, row in rows.items():
        require(row["video_path"] == paths[no] and sha(ROOT / paths[no]) == row["video_sha256"],
                f"{no}: final MP4 changed after its verified collection")
        require(sha(ROOT / C.PREVIEW_DIR / f"{no}.png") == row["summary_png_sha256"] == details[no]["png_sha256"],
                f"{no}: final PNG no longer matches current HEAD layout")
        for name, digest in row["public_qc_sha256"].items():
            require(Path(name).name == name and sha(ROOT / C.REPORT_DIR / name) == digest,
                    f"{no}: verified public QC changed after collection")
        if no != "05":
            base_script = json.loads(get(["git", "show", f"{C.BASE}:视频/脚本/{no}.json"]))
            C.check_script(no, read(ROOT / f"视频/脚本/{no}.json"), base_script, summaries[no])
        else:
            require(row["summary_text_sha256"] == hashlib.sha256(C.summary_text(summaries[no]).encode()).hexdigest(),
                    "05: reviewed summary text changed during finalization/rebase")
            public_commit = row.get("public_script_source_commit", "")
            require(re.fullmatch(r"[0-9a-f]{40}", public_commit) is not None,
                    "05: public script summary update has no recorded public source commit")
            public_original = json.loads(get(["git", "show", f"{public_commit}:视频/脚本/05.json"]))
            C.check_script("05", read(ROOT / "视频/脚本/05.json"), public_original, summaries[no])


def package(C, manifest):
    require(not PACKAGE.is_symlink(), "Final package directory must not be a symlink")
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    for row in manifest["articles"]:
        for relative in [row["video_path"], f'{C.PREVIEW_DIR}/{row["article"]}.png']:
            target = PACKAGE / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
            require(sha(target) == sha(ROOT / relative), "Final package media copy failed its hash check")
        for name in row["public_qc_sha256"]:
            target = PACKAGE / C.REPORT_DIR / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / C.REPORT_DIR / name, target)
    for name in ("manifest.json", "README.md", "collection-receipt.json"):
        shutil.copyfile(ROOT / C.REPORT_DIR / name, PACKAGE / C.REPORT_DIR / name)
    require(len(list((PACKAGE / C.VIDEO_DIR).glob("*.mp4"))) == 70,
            "Final downloadable package does not contain exactly 70 videos")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=ROOT / "batch-artifacts")
    parser.add_argument("--config", type=Path, default=TASK / "collection.json")
    parser.add_argument("--verify-final-only", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    check_repository()
    C = collector()
    config, receipt, fifth = load_inputs(args.config, args.artifacts)
    summaries, details = C.read_summaries(), layout_details()
    if args.verify_final_only:
        verify_final(C, read(ROOT / C.REPORT_DIR / "manifest.json"), summaries, details, args.config)
        print("ALL70 files, current summaries/layout and pinned provenance remain verified after rebase.")
        return
    previous = sys.argv
    try:
        sys.argv = [str(TASK / "collect.py"), "--artifacts", str(args.artifacts)]
        C.main()  # Existing strict collector69, including only the two authorized repairs.
    finally:
        sys.argv = previous
    fifth_result = validate05(C, args.artifacts / "article05-canonical-4K-final", fifth, summaries, details)
    manifest = update_all70(C, fifth_result, details, receipt, args.config, args.artifacts)
    verify_final(C, manifest, summaries, details, args.config)
    package(C, manifest)
    print("ALL70 verified and packaged locally in this GitHub job. Workflow publication remains to run.")


if __name__ == "__main__":
    main()
