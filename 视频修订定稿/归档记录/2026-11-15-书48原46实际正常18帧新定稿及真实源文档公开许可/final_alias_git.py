"""Build and verify final-alias Git trees through an injected Git-data API.

There is no network, authentication, ref, filesystem or media-processing code
here. ``api(repo, path, method='GET', data=None)`` is supplied by the owner of
the final canonical commit. Only ``git/trees`` POST and GET calls are made.
"""

from collections.abc import Mapping
import hashlib
import json
import re
import unicodedata

from build_final_alias_plan import build


KIND = "validated-video-final-alias-plan-v1"
FINAL = "最终定稿"
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")


class FinalAliasGitError(ValueError):
    """A plan or existing final directory differs from the exact managed tree."""


def _require(condition, message):
    if not condition:
        raise FinalAliasGitError(message)


def _path(value):
    _require(isinstance(value, str) and bool(value), "managed path must be nonempty text")
    _require(not any(unicodedata.category(c) in {"Cc", "Cf", "Cs"}
                     or c in "\u2028\u2029" for c in value), "managed path contains controls")
    _require("\\" not in value and all(p and p not in {".", ".."} for p in value.split("/")),
             "managed path is absolute, traversing, or contains a separator error")
    _require(unicodedata.normalize("NFC", value) == value, "managed path must already be NFC")
    return value


def _git_hash(kind, data):
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(data)).encode("ascii")
                        + b"\0" + data).hexdigest()


def _text_bytes(content):
    _require(isinstance(content, str), "inline Git-tree content must be UTF-8 text, never bytes")
    _require("\0" not in content, "inline Git-tree content must not contain a NUL byte")
    try:
        return content.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise FinalAliasGitError("inline Git-tree content is not valid UTF-8 text") from error


def expected_file_identities(plan):
    """Return final-root-relative files with exact mode/type/Git-SHA1/size.

    Video SHA and size come from matching plan entries and accepted manifest
    rows. Text identity is computed from its literal UTF-8 Git blob bytes.
    """
    _require(isinstance(plan, Mapping), "plan must be a mapping")
    manifest, entries, texts = plan.get("manifest"), plan.get("video_entries"), plan.get("text_files")
    _require(isinstance(manifest, Mapping) and manifest.get("kind") == KIND, "unrecognized final-alias plan kind")
    _require(isinstance(entries, list) and isinstance(texts, Mapping), "plan must contain video entries and text files")
    rows = manifest.get("videos")
    _require(isinstance(rows, list) and type(manifest.get("current_count")) is int
             and manifest["current_count"] == len(rows) == len(entries), "plan video count disagrees")
    managed = manifest.get("managed_text_files")
    _require(isinstance(managed, list) and len(set(managed)) == len(managed)
             and set(managed) == set(texts), "managed text paths disagree with the manifest")
    _require("README.md" in texts and "当前清单.json" in texts, "managed README/current manifest are missing")
    try:
        literal_manifest = json.loads(texts["当前清单.json"])
    except (TypeError, ValueError) as error:
        raise FinalAliasGitError("current manifest is not JSON text") from error
    _require(literal_manifest == manifest, "inline current manifest differs from the plan manifest")
    by_basename = {}
    for row in rows:
        _require(isinstance(row, Mapping), "manifest video row must be a mapping")
        alias = row.get("alias_path")
        _require(isinstance(alias, str) and alias.startswith(FINAL + "/视频/"), "video alias is outside the final video directory")
        name = _path(alias[len(FINAL + "/视频/"):])
        _require("/" not in name and name.endswith(".mp4"), "video alias must be an MP4 basename")
        _require(name not in by_basename, "duplicate video basename")
        _require(type(row.get("bytes")) is int and row["bytes"] > 0, "video byte count is invalid")
        _require(isinstance(row.get("git_blob_sha"), str) and _SHA1.fullmatch(row["git_blob_sha"]), "video Git blob SHA is invalid")
        by_basename[name] = row
    expected, selected = {}, set()
    for entry in entries:
        _require(isinstance(entry, Mapping) and set(entry) == {"path", "mode", "type", "sha"},
                 "video tree entries may contain only path/mode/type/existing SHA, never content")
        name = _path(entry.get("path"))
        _require("/" not in name and name.endswith(".mp4") and name in by_basename and name not in selected,
                 "video entries do not exactly match the manifest basenames")
        row = by_basename[name]
        _require(entry["mode"] == "100644" and entry["type"] == "blob"
                 and entry["sha"] == row["git_blob_sha"], "video entry differs from its existing accepted blob")
        selected.add(name)
        expected["视频/" + name] = {"mode": "100644", "type": "blob", "sha": entry["sha"], "size": row["bytes"]}
    _require(selected == set(by_basename), "a manifest video has no existing-blob tree entry")
    for path, content in texts.items():
        _path(path)
        _require(not path.lower().endswith(".mp4"), "MP4 cannot be an inline text file")
        _require(path.split("/", 1)[0] != "视频", "inline text cannot enter or replace the video subtree")
        _require(path not in expected, "video/text file path collision")
        raw = _text_bytes(content)
        expected[path] = {"mode": "100644", "type": "blob", "sha": _git_hash("blob", raw), "size": len(raw)}
    for path in expected:
        parents = path.split("/")[:-1]
        _require(not any("/".join(parents[:n]) in expected for n in range(1, len(parents) + 1)),
                 "managed file conflicts with a required parent directory")
    return {path: expected[path] for path in sorted(expected)}


def _directory_identities(files):
    directories = {"", "视频"}
    for path in files:
        parts = path.split("/")[:-1]
        directories.update("/".join(parts[:n]) for n in range(1, len(parts) + 1))
    _require(not set(files).intersection(directories), "managed file conflicts with a required directory")
    nodes = {}
    for directory in sorted(directories, key=lambda p: (p.count("/"), len(p)), reverse=True):
        prefix = directory + "/" if directory else ""
        children = []
        for path, node in files.items():
            if path.startswith(prefix) and "/" not in path[len(prefix):]:
                children.append((path[len(prefix):], "100644", node["sha"], False))
        for path, node in nodes.items():
            if path.startswith(prefix) and "/" not in path[len(prefix):]:
                children.append((path[len(prefix):], "40000", node["sha"], True))
        children.sort(key=lambda x: x[0].encode("utf-8") + (b"/" if x[3] else b""))
        data = b"".join(mode.encode("ascii") + b" " + name.encode("utf-8") + b"\0" + bytes.fromhex(sha)
                        for name, mode, sha, _ in children)
        nodes[directory] = {"mode": "040000", "type": "tree", "sha": _git_hash("tree", data)}
    return nodes


def _verify_tree(files, actual, root_sha):
    directories = _directory_identities(files)
    expected = {**files, **{path: node for path, node in directories.items() if path}}
    _require(set(actual) == set(expected), "final directory has missing, unexpected, or custom file/directory paths")
    for path, wanted in expected.items():
        found = actual[path]
        _require(isinstance(found, Mapping), f"invalid Git tree entry: {path}")
        _require(all(found.get(key) == wanted[key] for key in ("mode", "type", "sha")),
                 f"final file/directory mode, type or Git SHA differs: {path}")
        if wanted["type"] == "blob":
            _require(type(found.get("size")) is int and found["size"] == wanted["size"],
                     f"final file byte size differs: {path}")
    _require(root_sha == directories[""]["sha"], "final root Git tree SHA differs from its exact managed contents")
    return directories


def assert_existing_final_matches(inventory, canonical_video_tree, catalog=None, latest_requests=None):
    """Reject an absent, partial or custom-edited final folder, without I/O."""
    plan = build(inventory, canonical_video_tree, catalog, latest_requests=latest_requests)
    files = expected_file_identities(plan)
    root = canonical_video_tree.get(FINAL)
    _require(isinstance(root, Mapping) and root.get("type") == "tree" and root.get("mode") == "040000",
             "existing 最终定稿 root must be a 040000 tree")
    actual = {path[len(FINAL) + 1:]: node for path, node in canonical_video_tree.items()
              if isinstance(path, str) and path.startswith(FINAL + "/")}
    directories = _verify_tree(files, actual, root.get("sha"))
    return {"final_tree_sha": directories[""]["sha"], "video_tree_sha": directories["视频"]["sha"],
            "video_count": len(plan["video_entries"]), "text_file_count": len(plan["text_files"]),
            "expected_file_count": len(files), "all_file_modes_sizes_gitSHA_verified": True}


def _post_expected_tree(api,repo,entries,expected_sha):
    try:
        return api(repo,'git/trees',method='POST',data={'tree':entries})
    except Exception as error:
        # GitHub can create the exact tree and still return a 422 timeout.
        # Only an actual GET of the exact predicted object can recover it.
        if getattr(error,'code',None)!=422:
            raise
        observed=api(repo,'git/trees/'+expected_sha,method='GET')
        _require(isinstance(observed,Mapping) and observed.get('sha')==expected_sha,'Timed-out tree object was not actually created')
        return observed


def create_final_tree(api, repo, plan):
    """POST two trees, reference existing video blobs, and verify a recursive GET.

    The injected callback alone owns transport. No blobs containing video bytes,
    commits, branch refs, Releases or authentication are created by this helper.
    """
    _require(callable(api) and isinstance(repo, str) and bool(repo), "API callback and repository are required")
    files = expected_file_identities(plan)
    directories = _directory_identities(files)
    videos = _post_expected_tree(api,repo,[dict(e) for e in plan["video_entries"]],directories["视频"]["sha"])
    _require(isinstance(videos, Mapping) and videos.get("sha") == directories["视频"]["sha"],
             "created video subtree does not match its existing-blob references")
    entries = [{"path": "视频", "mode": "040000", "type": "tree", "sha": videos["sha"]}]
    entries.extend({"path": path, "mode": "100644", "type": "blob", "content": content}
                   for path, content in sorted(plan["text_files"].items()))
    final = _post_expected_tree(api,repo,entries,directories[""]["sha"])
    _require(isinstance(final, Mapping) and final.get("sha") == directories[""]["sha"],
             "created final root tree does not match its planned contents")
    observed = api(repo, "git/trees/" + final["sha"] + "?recursive=1", method="GET")
    _require(isinstance(observed, Mapping) and observed.get("sha") == final["sha"]
             and not observed.get("truncated") and isinstance(observed.get("tree"), list),
             "recursive final tree readback is missing, truncated or unpinned")
    actual = {}
    for entry in observed["tree"]:
        _require(isinstance(entry, Mapping) and isinstance(entry.get("path"), str)
                 and entry["path"] not in actual, "recursive final tree has invalid or duplicate paths")
        actual[entry["path"]] = entry
    _verify_tree(files, actual, final["sha"])
    return {"final_tree_sha": final["sha"], "video_tree_sha": videos["sha"],
            "video_count": len(plan["video_entries"]), "text_file_count": len(plan["text_files"]),
            "expected_file_count": len(files), "all_file_modes_sizes_gitSHA_verified": True}
