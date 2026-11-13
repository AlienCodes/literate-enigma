#!/usr/bin/env python3
"""Download only pinned final media/public QC from the existing backup work branches.

Source and destination are the same AlienCodes/literate-enigma repository used
under original CLAUDE rule 3 and by the user-approved Article03 sample. This is
not a new third-party mirror. Never download GT, ASR models, private a.wav or caches.
The GitHub token is sent only to api.github.com. Signed download redirects use a
new request without Authorization, and every redirect host is checked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile

REPOSITORY = "AlienCodes/literate-enigma"
TARGET_BRANCH = "codex/finish-05-and-summaries-20261112"
REPAIR_BRANCH = "codex/audio-fix67-70-20261112"
RULES = {
    "ordinary": (TARGET_BRANCH, ".github/workflows/summary70-videos.yml"),
    "repair": (REPAIR_BRANCH, ".github/workflows/audio-fix67-70.yml"),
    "article05": (TARGET_BRANCH, ".github/workflows/produce05-canonical4K.yml"),
}
EXPECTED = {f"{n:02}" for n in range(1, 71) if n != 5}
MAX_ZIP_BYTES = 256 * 1024 * 1024
MAX_EXPANDED_BYTES = 512 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def file_sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def cdn_url_allowed(url):
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if p.scheme != "https" or p.username or p.password or p.port not in (None, 443):
        return False
    return (host in {"github.com", "api.github.com", "objects.githubusercontent.com",
                     "objects-origin.githubusercontent.com", "release-assets.githubusercontent.com"}
            or host.endswith(".actions.githubusercontent.com")
            or host.endswith(".blob.core.windows.net"))


class GitHub:
    def __init__(self):
        self.token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        require(self.token, "GitHub Actions token is unavailable")
        self.api_opener = build_opener(NoRedirect())
        self.download_opener = build_opener(NoRedirect())

    def api_request(self, path):
        # The caller supplies generated numeric endpoints, never a redirect URL.
        require(path.startswith(f"/repos/{REPOSITORY}/actions/"), "Unexpected GitHub API path")
        return Request("https://api.github.com" + path, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "approved-vocabulary-final-media-collector",
        })

    def api_json(self, path):
        try:
            with self.api_opener.open(self.api_request(path), timeout=60) as r:
                data = r.read(10 * 1024 * 1024 + 1)
            require(len(data) <= 10 * 1024 * 1024, "Oversized GitHub metadata response")
            return json.loads(data)
        except HTTPError as exc:
            raise RuntimeError(f"GitHub metadata request failed (HTTP {exc.code})") from None
        except URLError:
            raise RuntimeError("GitHub metadata transport failed") from None

    def download(self, artifact_id, destination):
        path = f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
        try:
            response = self.api_opener.open(self.api_request(path), timeout=60)
        except HTTPError as exc:
            require(exc.code in (301, 302, 303, 307, 308),
                    f"GitHub artifact request failed (HTTP {exc.code})")
            location = exc.headers.get("Location")
            require(location, "GitHub artifact redirect has no location")
            response = None
        except URLError:
            raise RuntimeError("GitHub artifact transport failed") from None
        else:
            # Authenticated bytes are accepted only from the original API request.
            with response:
                return self._save_response(response, destination)
        for _ in range(5):
            require(cdn_url_allowed(location), "Rejected artifact download redirect host")
            # Deliberately no Authorization, Cookie or inherited API headers here.
            request = Request(location, headers={"User-Agent": "approved-vocabulary-final-media-collector"})
            try:
                with self.download_opener.open(request, timeout=60) as response:
                    return self._save_response(response, destination)
            except HTTPError as exc:
                if exc.code in (301, 302, 303, 307, 308):
                    target = exc.headers.get("Location")
                    require(target, "Artifact CDN redirect has no location")
                    location = urljoin(location, target)
                    continue
                raise RuntimeError(f"Artifact CDN request failed (HTTP {exc.code})") from None
            except URLError:
                raise RuntimeError("Artifact CDN transport failed") from None
        raise RuntimeError("Too many artifact download redirects")

    @staticmethod
    def _save_response(response, destination):
        total = 0
        with destination.open("xb") as out:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                require(total <= MAX_ZIP_BYTES, "Artifact ZIP exceeds the media-only size limit")
                out.write(block)
        return total


def validate_source(source, role):
    require(isinstance(source, dict), f"Missing pinned {role} run")
    require(type(source.get("run_id")) is int and source["run_id"] > 0,
            f"Fill a successful explicit {role} run ID before collection")
    require(isinstance(source.get("commit"), str)
            and re.fullmatch(r"[0-9a-f]{40}", source["commit"]), f"Invalid pinned {role} commit")
    branch, workflow = RULES[role]
    require(source.get("branch") == branch and source.get("workflow_path") == workflow,
            f"Unexpected {role} branch/workflow; only the approved backup work branches are allowed")
    if role != "article05":
        numbers = source.get("articles")
        require(isinstance(numbers, list) and numbers and len(set(numbers)) == len(numbers)
                and all(isinstance(n, str) and n in EXPECTED for n in numbers),
                f"Invalid {role} article allowlist")
        if role == "repair":
            require(set(numbers) <= {"67", "70"}, "Only 67/70 may be repair overrides")
    return source


def checked_run(api, source, role):
    data = api.api_json(f"/repos/{REPOSITORY}/actions/runs/{source['run_id']}")
    require(data.get("id") == source["run_id"] and data.get("status") == "completed",
            "Pinned workflow run is not complete")
    for key in ("repository", "head_repository"):
        require(str(data.get(key, {}).get("full_name", "")).lower() == REPOSITORY.lower(),
                "Pinned run comes from an unexpected repository/fork")
    require(data.get("head_sha") == source["commit"]
            and data.get("head_branch") == source["branch"]
            and str(data.get("path", "")).split("@", 1)[0] == source["workflow_path"],
            "Pinned run commit/branch/workflow differs from collection.json")
    require(data.get("event") in ("push", "workflow_dispatch"), "Unapproved workflow event")
    # The ordinary full matrix can be red only because 67/70 need the separate
    # repair artifacts. Every selected final file is independently verified later.
    conclusions = ("success", "failure") if role == "ordinary" else ("success",)
    require(data.get("conclusion") in conclusions, "Pinned workflow run has no usable final result")
    found = []
    for page in range(1, 11):
        result = api.api_json(f"/repos/{REPOSITORY}/actions/runs/{source['run_id']}/artifacts?per_page=100&page={page}")
        rows = result.get("artifacts", [])
        found.extend(rows)
        if len(rows) < 100:
            break
    return data, found


def allowed_file(name, role, no):
    if role == "article05":
        return name in {"05-status.json", "05-summary-verification.json",
                        "05-4K-读完即转简述2秒.mp4"}
    if not (name.startswith(no + "-") or name.startswith(no + " - ")):
        return False
    if name.endswith((".mp4", ".png")):
        return True  # Final video and public card/transition screenshots only.
    if name in {f"{no}-script.json", f"{no}-verification.json", f"{no}-body-matching.json"}:
        return True
    if any(name == f"{no}-{kind}{suffix}"
           for kind in ("audio-audit", "before-audio-audit", "audio-repair", "target-speech-check", "candidate-comparison")
           for suffix in (".json", ".md")):
        return True
    if re.fullmatch(no + r"-S[1-9]\d*-speech-check\.json", name):
        return True
    return name.endswith(".txt") and "ssim" in name.lower()


def extract_media_only(archive, directory, role, no):
    entries = []
    names = set()
    total = 0
    prefixes = {(), ("article05-delivery",)} if role == "article05" else {
        (), ("completion-output",), ("audio-repair-final", no), (no,)}
    with zipfile.ZipFile(archive) as z:
        require(len(z.infolist()) <= 500, "Too many files in a final-media artifact")
        for info in z.infolist():
            raw = getattr(info, "orig_filename", info.filename)
            require("\0" not in raw and "\\" not in raw, "Invalid ZIP member path")
            path = PurePosixPath(raw)
            require(not path.is_absolute() and all(x not in (".", "..") for x in path.parts)
                    and not re.match(r"^[A-Za-z]:", raw), "ZIP path traversal is forbidden")
            mode = (info.external_attr >> 16) & 0xffff
            require(not stat.S_ISLNK(mode) and stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR),
                    "ZIP symlinks and special files are forbidden")
            if info.is_dir():
                continue
            require(tuple(path.parts[:-1]) in prefixes and allowed_file(path.name, role, no),
                    "Artifact contains a file outside the final-media/public-QC allowlist")
            require(path.name not in names, "Duplicate ZIP basename is forbidden")
            names.add(path.name)
            total += info.file_size
            require(total <= MAX_EXPANDED_BYTES, "Expanded final-media artifact is too large")
            entries.append((info, path.name))
        require(sum(name.endswith(".mp4") for _, name in entries) == 1,
                "Final artifact must contain exactly one MP4")
        required = ({"05-status.json", "05-summary-verification.json"} if role == "article05"
                    else {f"{no}-script.json", f"{no}-verification.json", f"{no}-简述.png"})
        require(required <= names, "Final artifact is missing its public verification files")
        directory.mkdir()
        for info, name in entries:
            with z.open(info) as source, (directory / name).open("xb") as out:
                shutil.copyfileobj(source, out, 1024 * 1024)


def one_artifact(api, rows, source, run, role, no, root, scratch):
    name = "article05-canonical-4K-final" if role == "article05" else f"reviewed-video-{no}"
    candidates = [a for a in rows if a.get("name") == name and not a.get("expired")]
    explicit = source.get("artifact_ids", {}).get(name)
    if explicit is not None:
        candidates = [a for a in candidates if a.get("id") == explicit]
    require(len(candidates) == 1, f"Expected one pinned final artifact named {name}")
    artifact = candidates[0]
    digest = artifact.get("digest", "")
    require(re.fullmatch(r"sha256:[0-9a-f]{64}", digest), "Artifact has no verifiable ZIP digest")
    archive = scratch / f"{artifact['id']}.zip"
    api.download(artifact["id"], archive)
    require(file_sha(archive) == digest.split(":", 1)[1], "Downloaded artifact ZIP digest mismatch")
    extracted = scratch / f"{artifact['id']}-files"
    extract_media_only(archive, extracted, role, no)
    target = root / name
    require(not target.is_symlink(), "Artifact destination must not be a symlink")
    if target.exists():
        shutil.rmtree(target)  # Explicit later run / repair override, never merge stale files.
    shutil.move(str(extracted), str(target))
    archive.unlink()
    print(f"Downloaded {name} from pinned run {source['run_id']} (artifact {artifact['id']})", flush=True)
    return {"role": role, "article": no, "run_id": source["run_id"],
            "commit": source["commit"], "branch": source["branch"],
            "workflow_path": source["workflow_path"], "run_conclusion": run["conclusion"],
            "artifact_id": artifact["id"], "artifact_name": name, "zip_digest": digest}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".github/video-batch/collection.json"))
    parser.add_argument("--out", type=Path, default=Path("batch-artifacts"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    require(config.get("schema") == 1 and config.get("repository") == REPOSITORY
            and config.get("destination_branch") == TARGET_BRANCH, "Unexpected collection destination")
    normal = [validate_source(x, "ordinary") for x in config.get("ordinary_runs", [])]
    repairs = [validate_source(x, "repair") for x in config.get("repair_runs", [])]
    fifth = validate_source(config.get("article05_run"), "article05")
    require(normal and repairs, "Fill all successful pinned run selections before collection")
    require(set().union(*(set(x["articles"]) for x in repairs)) == {"67", "70"},
            "Final repair overrides must cover exactly 67 and 70")
    require(set().union(*(set(x["articles"]) for x in normal + repairs)) == EXPECTED,
            "Pinned ordinary and repair artifacts do not cover all 69 existing videos")
    args.out.mkdir(parents=True, exist_ok=True)
    require(not any(args.out.iterdir()), "Artifact output must be empty before pinned collection")
    api = GitHub()
    receipt = {"schema": 1, "repository": REPOSITORY, "destination_branch": TARGET_BRANCH,
               "config_sha256": file_sha(args.config), "downloads": [], "final_sources": {}}
    with tempfile.TemporaryDirectory(prefix="approved-media-", dir=os.environ.get("RUNNER_TEMP")) as tmp:
        scratch = Path(tmp)
        # Ordinary sources first; explicit later ordinary sources replace corrected
        # card renders. Then the two measured audio repairs always win.
        for role, sources in (("ordinary", normal), ("repair", repairs), ("article05", [fifth])):
            for source in sources:
                run, rows = checked_run(api, source, role)
                for no in (["05"] if role == "article05" else source["articles"]):
                    row = one_artifact(api, rows, source, run, role, no, args.out, scratch)
                    receipt["downloads"].append(row)
                    receipt["final_sources"][no] = row
    require(set(receipt["final_sources"]) == {f"{n:02}" for n in range(1, 71)},
            "Pinned download did not finish all 70 final selections")
    (args.out / "collection-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("All pinned final media downloaded. This is not yet an ALL70 verification pass.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never dump response bodies, tokens or signed redirect URLs in logs.
        print(f"Final-media download stopped: {type(exc).__name__}: {exc}")
        raise SystemExit(1)
