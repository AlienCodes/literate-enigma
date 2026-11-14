"""Meaningful pure-plan checks; no repository, state or media writes."""

from copy import deepcopy
import hashlib
import json
import unittest
from unittest.mock import patch

from build_final_alias_plan import build, PlanError


def digest(value, algorithm="sha256"):
    return hashlib.new(algorithm, value.encode()).hexdigest()


def article(sid, nid, title, marker="accepted", with_run=True):
    row = {"source_id": sid, "new_id": nid, "title_zh": title,
           "title_en": "Observed title " + sid, "bytes": 1000 + int(sid),
           "sha256": digest(sid + marker), "asset_commit": digest(sid + marker, "sha1"),
           "video_repo_path": f"视频修订定稿/归档{sid}-{marker}/视频/{nid} {title}.mp4",
           "archive_prefix": f"视频修订定稿/归档{sid}-{marker}",
           "passed_per_article": True}
    if with_run:
        row["source_run"] = 43560000000 + int(sid)
    return row


def inputs(rows):
    inventory = {"requested_total": 70, "archived_passed_count": len(rows),
                 "remaining_not_claimed_passed": 70 - len(rows), "articles": rows}
    tree = {}
    for row in rows:
        path = row["video_repo_path"].removeprefix("视频修订定稿/")
        tree[path] = {"path": path, "mode": "100644", "type": "blob",
                      "sha": digest(row["sha256"], "sha1"), "size": row["bytes"]}
        proof = row["archive_prefix"].removeprefix("视频修订定稿/") + "/archive-manifest.json"
        tree[proof] = {"path": proof, "mode": "100644", "type": "blob",
                       "sha": digest(proof, "sha1"), "size": 20}
    return inventory, tree


class FinalAliasPlanTests(unittest.TestCase):
    def setUp(self):
        self.rows = [article("12", "37", "仍保留  空格：全角（标点）"),
                     article("61", "24", "集装箱：重塑世界的铁盒子"),
                     article("15", "25", "永不沉没的神话")]
        self.inventory, self.tree = inputs(self.rows)

    def test_sort_gaps_alias_shape_and_two_independent_number_spaces(self):
        result = build(self.inventory, self.tree)
        self.assertEqual([r["path"] for r in result["video_entries"]],
                         ["24 集装箱：重塑世界的铁盒子.mp4", "25 永不沉没的神话.mp4",
                          "37 仍保留  空格：全角（标点）.mp4"])
        self.assertTrue(all(set(row) == {"path", "mode", "type", "sha"}
                            for row in result["video_entries"]))
        self.assertNotIn("12", result["manifest"]["missing_source_ids"])
        self.assertIn("12", result["manifest"]["missing_new_ids"])
        self.assertEqual(len(result["video_entries"]), 3)
        self.assertIn("3/70", result["text_files"]["README.md"])
        self.assertTrue(all(not p.startswith("最终定稿/") for p in result["text_files"]))
        self.assertEqual(result["manifest"]["kind"], "validated-video-final-alias-plan-v1")
        self.assertEqual(result["manifest"], json.loads(result["text_files"]["当前清单.json"]))
        self.assertEqual(set(result["manifest"]["managed_text_files"]), set(result["text_files"]))

    def test_actual_58_count_not_fake_70(self):
        excluded = {"05", "16", "18", "30", "48", "54", "65", "66", "67", "68", "69", "70"}
        rows = [article(f"{n:02d}", f"{n:02d}", f"文章{n}")
                for n in range(1, 71) if f"{n:02d}" not in excluded]
        inv, tree = inputs(rows)
        result = build(inv, tree)
        self.assertEqual(len(result["video_entries"]), 58)
        self.assertEqual(result["manifest"]["current_count"], 58)
        self.assertFalse(result["manifest"]["complete"])
        self.assertEqual(set(result["manifest"]["missing_source_ids"]), excluded)
        self.assertIn("58/70", result["text_files"]["README.md"])

    def test_top_level_current_only_retains_full_nested_history_without_mutation(self):
        current = article("13", "23", "十一天不睡觉的少年", "approved-current")
        previous = article("13", "23", "十一天不睡觉的少年", "old")
        previous["previous_versions"] = [{"marker": "full nested original fact", "extra": [1, 2]}]
        current["previous_versions"] = [previous]
        inv, tree = inputs([current])
        inv["pending_articles"] = [article("26", "27", "孩子们发明的语言", "not-yet-grafted")]
        before = deepcopy((inv, tree))
        with patch("builtins.open", side_effect=AssertionError("pure build must not open files")):
            result = build(inv, tree)
        self.assertEqual((inv, tree), before)
        self.assertEqual(len(result["video_entries"]), 1)
        self.assertEqual(result["manifest"]["videos"][0]["previous_versions"], [previous])
        self.assertEqual(result["manifest"]["videos"][0]["sha256"], current["sha256"])
        text = result["text_files"]["修改记录/23 十一天不睡觉的少年.md"]
        self.assertIn(previous["sha256"], text)
        self.assertIn(current["sha256"], text)
        self.assertIn("archive-manifest.json", text)
        self.assertNotIn("not-yet-grafted", json.dumps(result, ensure_ascii=False))
        result["manifest"]["videos"][0]["previous_versions"][0]["previous_versions"][0]["extra"].append(3)
        self.assertEqual((inv, tree), before)

    def test_current_source26_is_not_replaced_by_pending_version(self):
        old = article("26", "27", "孩子们发明的语言", "canonical-old")
        candidate = article("26", "27", "孩子们发明的语言", "unintegrated-new")
        inv, tree = inputs([old])
        inv["pending_revisions"] = [candidate]
        result = build(inv, tree)
        self.assertEqual(result["manifest"]["videos"][0]["sha256"], old["sha256"])
        self.assertNotEqual(result["manifest"]["videos"][0]["sha256"], candidate["sha256"])

    def test_canceled61_and_unapproved15_reviews_do_not_change_existing_selection(self):
        self.inventory["review018_019_unapproved"] = [article("15", "25", "永不沉没的神话", "unapproved")]
        self.inventory["source61_canceled_edits"] = {"candidate_sha256": digest("canceled")}
        result = build(self.inventory, self.tree)
        current = {r["source_id"]: r for r in result["manifest"]["videos"]}
        self.assertEqual(current["61"]["sha256"], self.rows[1]["sha256"])
        self.assertEqual(current["15"]["sha256"], self.rows[2]["sha256"])

    def test_missing_run_stays_null_without_path_guess(self):
        row = article("53", "53", "已有验收视频", with_run=False)
        inv, tree = inputs([row])
        result = build(inv, tree)["manifest"]["videos"][0]
        self.assertIsNone(result["source_run"])
        self.assertEqual(result["missing_metadata_fields"], ["source_run"])

    def test_duplicate_source_or_order_rejected(self):
        for field in ["source_id", "new_id"]:
            inv, tree = deepcopy((self.inventory, self.tree))
            inv["articles"][1][field] = inv["articles"][0][field]
            with self.subTest(field=field), self.assertRaisesRegex(PlanError, "duplicate"):
                build(inv, tree)

    def test_noncanonical_zero_padding_and_numeric_ids_rejected(self):
        for field in ["source_id", "new_id"]:
            for value in ["1", 1, "001", "00", "71"]:
                inv = deepcopy(self.inventory)
                inv["articles"][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaisesRegex(PlanError, "two-digit"):
                    build(inv, self.tree)

    def test_count_and_unpassed_negatives(self):
        for key, value in [("archived_passed_count", 4), ("archived_passed_count", True),
                           ("remaining_not_claimed_passed", 0), ("requested_total", 69)]:
            inv = deepcopy(self.inventory)
            inv[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(PlanError):
                build(inv, self.tree)
        for value in [False, 1, None, "true"]:
            inv = deepcopy(self.inventory)
            inv["articles"][0]["passed_per_article"] = value
            with self.subTest(passed=value), self.assertRaisesRegex(PlanError, "explicitly passed"):
                build(inv, self.tree)

    def test_unsafe_titles_and_non_nfc_rejected_without_rewriting(self):
        for title in ["bad/name", "bad\\name", "bad\nname", "bad\0name", "bad\u202ename", "Cafe\u0301", "..", "  "]:
            inv = deepcopy(self.inventory)
            inv["articles"][0]["title_zh"] = title
            with self.subTest(title=repr(title)), self.assertRaises(PlanError):
                build(inv, self.tree)

    def test_unsafe_original_paths_rejected(self):
        for path in ["../video.mp4", "视频修订定稿/a/../b.mp4", "视频修订定稿//x.mp4",
                     "视频修订定稿/x\\b.mp4", "视频修订定稿/x\nb.mp4"]:
            inv = deepcopy(self.inventory)
            inv["articles"][0]["video_repo_path"] = path
            with self.subTest(path=repr(path)), self.assertRaises(PlanError):
                build(inv, self.tree)

    def test_final_alias_cannot_be_its_own_original_even_with_valid_blob(self):
        inv, tree = deepcopy((self.inventory, self.tree))
        row = inv["articles"][0]
        original = row["video_repo_path"].removeprefix("视频修订定稿/")
        relative = f"最终定稿/视频/{row['new_id']} {row['title_zh']}.mp4"
        row["video_repo_path"] = "视频修订定稿/" + relative
        tree[relative] = {**tree[original], "path": relative}
        self.assertEqual(tree[relative]["size"], row["bytes"])
        self.assertEqual(tree[relative]["sha"], tree[original]["sha"])
        with self.assertRaisesRegex(PlanError, "original archive, not a final alias"):
            build(inv, tree)

    def test_missing_blob_wrong_size_type_and_mode_rejected(self):
        key = self.rows[0]["video_repo_path"].removeprefix("视频修订定稿/")
        for change in [None, {"mode": "100755"}, {"mode": "120000"}, {"type": "tree"},
                       {"size": 1}, {"size": True}, {"sha": "not-git-sha"}]:
            tree = deepcopy(self.tree)
            if change is None:
                del tree[key]
            else:
                tree[key].update(change)
            with self.subTest(change=change), self.assertRaises(PlanError):
                build(self.inventory, tree)

    def test_optional_catalog_is_full_bijection_and_validates_mapping(self):
        rows = [{"source_id": f"{n:02d}", "new_id": f"{n:02d}", "title_zh": f"文章{n}"}
                for n in range(1, 71)]
        selected = article("12", "12", "文章12")
        inv, tree = inputs([selected])
        self.assertTrue(build(inv, tree, {"count": 70, "illustrations": rows})["manifest"]["catalog_validated"])
        for catalog in [rows[:-1], rows + [rows[0]], rows[:1] * 70]:
            with self.subTest(length=len(catalog)), self.assertRaises(PlanError):
                build(inv, tree, catalog)
        swapped = deepcopy(rows)
        swapped[11]["new_id"], swapped[36]["new_id"] = "37", "12"
        with self.assertRaisesRegex(PlanError, "disagrees"):
            build(inv, tree, swapped)
        changed_title = deepcopy(rows)
        changed_title[11]["title_zh"] = "另一个标题"
        with self.assertRaisesRegex(PlanError, "disagrees"):
            build(inv, tree, changed_title)

    def test_deterministic_and_empty_inventory_are_honest(self):
        self.assertEqual(build(self.inventory, self.tree), build(self.inventory, self.tree))
        inv, tree = inputs([])
        result = build(inv, tree)
        self.assertEqual(result["video_entries"], [])
        self.assertEqual(len(result["manifest"]["missing_source_ids"]), 70)
        self.assertIn("0/70", result["text_files"]["README.md"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
