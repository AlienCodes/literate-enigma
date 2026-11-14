"""In-memory Git API tests only: no external I/O, media bytes or live refs."""

from copy import deepcopy
import hashlib
import json
import unittest
from unittest.mock import patch

from build_final_alias_plan import build
from final_alias_git import (FinalAliasGitError, assert_existing_final_matches,
                             create_final_tree, expected_file_identities)


def git_object(kind, raw):
    return hashlib.sha1(f"{kind} {len(raw)}\0".encode() + raw).hexdigest()


def fixture(count=3):
    rows, tree = [], {}
    for number in range(1, count + 1):
        sid = nid = f"{number:02d}"
        title = f"文章 {number}：全角（标题）"
        relative = f"归档{sid}/视频/{nid} {title}.mp4"
        blob = hashlib.sha1(("existing-public-video-" + sid).encode()).hexdigest()
        rows.append({"source_id": sid, "new_id": nid, "title_zh": title,
                     "video_repo_path": "视频修订定稿/" + relative,
                     "bytes": 100000 + number, "sha256": hashlib.sha256(sid.encode()).hexdigest(),
                     "asset_commit": hashlib.sha1(sid.encode()).hexdigest(),
                     "source_run": 43560000000 + number, "archive_prefix": f"视频修订定稿/归档{sid}",
                     "passed_per_article": True})
        tree[relative] = {"path": relative, "mode": "100644", "type": "blob", "sha": blob, "size": 100000 + number}
    inventory = {"requested_total": 70, "archived_passed_count": count,
                 "remaining_not_claimed_passed": 70 - count, "articles": rows}
    return inventory, tree, build(inventory, tree)


class MemoryGitAPI:
    """Small independent Git-data simulation supporting only allowed calls."""

    def __init__(self, initial_files):
        self.blobs = {node["sha"]: {"sha": node["sha"], "size": node["size"]}
                      for node in initial_files.values() if node["type"] == "blob"}
        self.trees, self.calls = {}, []
        self.read_transform = None

    def store_tree(self, nodes):
        children = sorted(nodes.items(), key=lambda item: (item[0] + ("/" if item[1]["type"] == "tree" else "")).encode())
        raw = b""
        for name, node in children:
            mode = "40000" if node["type"] == "tree" else node["mode"]
            raw += mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(node["sha"])
        sha = git_object("tree", raw)
        self.trees[sha] = deepcopy(nodes)
        return sha

    def __call__(self, repo, path, method="GET", data=None):
        self.calls.append({"repo": repo, "path": path, "method": method, "data": deepcopy(data)})
        if method == "POST":
            if path != "git/trees" or set(data) != {"tree"}:
                raise AssertionError("only Git tree creation is allowed")
            root = {}
            for entry in data["tree"]:
                parts = entry["path"].split("/")
                cursor = root
                for part in parts[:-1]:
                    cursor = cursor.setdefault(part, {})
                if "content" in entry:
                    if entry["path"].lower().endswith(".mp4") or not isinstance(entry["content"], str):
                        raise AssertionError("video or binary inline contents are forbidden")
                    raw = entry["content"].encode("utf-8")
                    sha = git_object("blob", raw)
                    self.blobs[sha] = {"sha": sha, "size": len(raw)}
                    cursor[parts[-1]] = {"mode": entry["mode"], "type": "blob", **self.blobs[sha]}
                elif entry["type"] == "tree":
                    if entry["sha"] not in self.trees:
                        raise AssertionError("tree reference must exist")
                    cursor[parts[-1]] = {"mode": entry["mode"], "type": "tree", "sha": entry["sha"]}
                else:
                    if entry["sha"] not in self.blobs:
                        raise AssertionError("video reference must use an existing blob")
                    cursor[parts[-1]] = {"mode": entry["mode"], "type": "blob", **self.blobs[entry["sha"]]}

            def flush(directory):
                nodes = {}
                for name, value in directory.items():
                    nodes[name] = value if "mode" in value else {"mode": "040000", "type": "tree", "sha": flush(value)}
                return self.store_tree(nodes)

            return {"sha": flush(root)}
        if method != "GET" or not path.startswith("git/trees/") or not path.endswith("?recursive=1"):
            raise AssertionError("only recursive tree readback is allowed")
        sha = path[len("git/trees/"):-len("?recursive=1")]
        result = {"sha": sha, "tree": [], "truncated": False}

        def walk(tree_sha, prefix=""):
            for name, node in self.trees[tree_sha].items():
                result["tree"].append({"path": prefix + name, **deepcopy(node)})
                if node["type"] == "tree":
                    walk(node["sha"], prefix + name + "/")

        walk(sha)
        return self.read_transform(result) if self.read_transform else result


class FinalAliasGitTests(unittest.TestCase):
    def setUp(self):
        self.inventory, self.canonical, self.plan = fixture()
        self.api = MemoryGitAPI(self.canonical)

    def materialized(self):
        result = create_final_tree(self.api, "owner/repository", self.plan)
        observed = self.api("owner/repository", "git/trees/" + result["final_tree_sha"] + "?recursive=1")
        tree = deepcopy(self.canonical)
        tree["最终定稿"] = {"path": "最终定稿", "mode": "040000", "type": "tree", "sha": result["final_tree_sha"]}
        tree.update({"最终定稿/" + row["path"]: {**row, "path": "最终定稿/" + row["path"]} for row in observed["tree"]})
        return result, tree

    def test_known_git_blob_hash_utf8_size_and_deterministic_identities(self):
        self.assertEqual(git_object("blob", b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")
        before = deepcopy(self.plan)
        with patch("builtins.open", side_effect=AssertionError("no file I/O")):
            expected = expected_file_identities(self.plan)
        self.assertEqual(self.plan, before)
        self.assertEqual(expected, expected_file_identities(self.plan))
        raw = self.plan["text_files"]["README.md"].encode()
        self.assertEqual(expected["README.md"]["size"], len(raw))
        self.assertEqual(expected["README.md"]["sha"], git_object("blob", raw))
        self.assertEqual(set(expected["README.md"]), {"mode", "type", "sha", "size"})

    def test_create_two_trees_no_media_content_or_ref_calls(self):
        with patch("builtins.open", side_effect=AssertionError("no file I/O")):
            result = create_final_tree(self.api, "owner/repository", self.plan)
        self.assertEqual([call["method"] for call in self.api.calls], ["POST", "POST", "GET"])
        self.assertTrue(all(call["path"].startswith("git/trees") for call in self.api.calls))
        for entry in self.api.calls[0]["data"]["tree"]:
            self.assertEqual(set(entry), {"path", "mode", "type", "sha"})
            self.assertTrue(entry["path"].endswith(".mp4"))
        for entry in self.api.calls[1]["data"]["tree"]:
            if entry["type"] == "blob":
                self.assertIsInstance(entry["content"], str)
                self.assertNotIn("sha", entry)
                self.assertFalse(entry["path"].lower().endswith(".mp4"))
        self.assertEqual(result["video_count"], 3)
        self.assertEqual(result["text_file_count"], 5)
        self.assertTrue(result["all_file_modes_sizes_gitSHA_verified"])

    def test_existing_exact_directory_passes_and_inputs_are_unchanged(self):
        created, canonical = self.materialized()
        before = deepcopy((self.inventory, canonical))
        result = assert_existing_final_matches(self.inventory, canonical)
        self.assertEqual(result, created)
        self.assertEqual((self.inventory, canonical), before)

    def test_missing_root_bad_root_and_unknown_custom_directory_rejected(self):
        _, canonical = self.materialized()
        cases = []
        missing = deepcopy(canonical); del missing["最终定稿"]; cases.append(missing)
        wrong_mode = deepcopy(canonical); wrong_mode["最终定稿"]["mode"] = "100644"; cases.append(wrong_mode)
        custom = deepcopy(canonical); custom["最终定稿/私人目录"] = {"mode": "040000", "type": "tree", "sha": "0" * 40}; cases.append(custom)
        for value in cases:
            with self.subTest(), self.assertRaises(FinalAliasGitError):
                assert_existing_final_matches(self.inventory, value)

    def test_unknown_changed_renamed_missing_or_wrong_size_file_rejected(self):
        _, original = self.materialized()
        for change in ["unknown", "changed", "renamed", "missing", "size", "mode"]:
            canonical = deepcopy(original)
            node = canonical["最终定稿/README.md"]
            if change == "unknown":
                canonical["最终定稿/人工补充.md"] = deepcopy(node)
            elif change == "changed":
                node["sha"] = git_object("blob", b"same kind of real edited text")
            elif change == "renamed":
                canonical["最终定稿/新名字.md"] = canonical.pop("最终定稿/README.md")
            elif change == "missing":
                del canonical["最终定稿/README.md"]
            elif change == "size":
                node["size"] += 1
            else:
                node["mode"] = "100755"
            with self.subTest(change=change), self.assertRaises(FinalAliasGitError):
                assert_existing_final_matches(self.inventory, canonical)

    def test_unknown_edited_directory_sha_rejected(self):
        _, canonical = self.materialized()
        canonical["最终定稿/修改记录"]["sha"] = "0" * 40
        with self.assertRaisesRegex(FinalAliasGitError, "Git SHA differs"):
            assert_existing_final_matches(self.inventory, canonical)

    def test_no_inline_mp4_binary_or_video_namespace_collision(self):
        for path, content in [("evil.mp4", "text"), ("evil.MP4", "text"), ("视频/extra.md", "text"),
                              ("extra.md", b"binary"), ("extra.md", "NUL\0content"),
                              ("../escape.md", "text"), ("修改记录", "file-vs-directory")]:
            plan = deepcopy(self.plan)
            plan["text_files"][path] = content
            plan["manifest"]["managed_text_files"].append(path)
            # Bytes cannot be represented in the JSON manifest, so the literal
            # manifest contains only its path list and never the binary content.
            plan["text_files"]["当前清单.json"] = json.dumps(plan["manifest"], ensure_ascii=False)
            with self.subTest(path=path, content=repr(content)), self.assertRaises(FinalAliasGitError):
                create_final_tree(self.api, "owner/repository", plan)
        self.assertEqual(self.api.calls, [])

    def test_existing_video_sha_only_no_inline_video_or_mismatch(self):
        for mutation in ["inline", "sha", "duplicate", "traversal"]:
            plan = deepcopy(self.plan)
            if mutation == "inline":
                plan["video_entries"][0]["content"] = "forbidden"
            elif mutation == "sha":
                plan["video_entries"][0]["sha"] = "0" * 40
            elif mutation == "duplicate":
                plan["video_entries"][1] = deepcopy(plan["video_entries"][0])
            else:
                plan["video_entries"][0]["path"] = "../x.mp4"
            with self.subTest(mutation=mutation), self.assertRaises(FinalAliasGitError):
                create_final_tree(self.api, "owner/repository", plan)
        self.assertEqual(self.api.calls, [])

    def test_recursive_readback_truncation_missing_duplicate_and_corruption_rejected(self):
        for kind in ["truncated", "missing", "duplicate", "wrong-size", "wrong-mode", "custom-dir"]:
            api = MemoryGitAPI(self.canonical)
            def transform(response, kind=kind):
                if kind == "truncated": response["truncated"] = True
                elif kind == "missing": response["tree"].pop()
                elif kind == "duplicate": response["tree"].append(deepcopy(response["tree"][0]))
                elif kind == "custom-dir": response["tree"].append({"path": "unknown", "mode": "040000", "type": "tree", "sha": "0" * 40})
                else:
                    blob = next(r for r in response["tree"] if r["type"] == "blob")
                    if kind == "wrong-size": blob["size"] += 1
                    else: blob["mode"] = "100755"
                return response
            api.read_transform = transform
            with self.subTest(kind=kind), self.assertRaises(FinalAliasGitError):
                create_final_tree(api, "owner/repository", self.plan)

    def test_58_fixture_creates_only_58_existing_video_references(self):
        inventory, canonical, plan = fixture(58)
        api = MemoryGitAPI(canonical)
        result = create_final_tree(api, "owner/repository", plan)
        self.assertEqual(result["video_count"], 58)
        self.assertEqual(result["text_file_count"], 60)
        self.assertEqual(result["expected_file_count"], 118)
        self.assertEqual(len(api.calls[0]["data"]["tree"]), 58)
        self.assertIn("58/70", plan["text_files"]["README.md"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
