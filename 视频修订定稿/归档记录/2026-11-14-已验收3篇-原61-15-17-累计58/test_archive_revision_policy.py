"""Inventory-only fixtures. These fixtures never assert new media acceptance."""
from copy import deepcopy
from pathlib import Path
import json
import unittest
import archive_revision_policy as policy

B = Path(__file__).resolve().parent


class RevisionMetadataSafety(unittest.TestCase):
    def setUp(self):
        self.previous = json.loads((B/'operations-native43556226408-49/final-remote-cumulative-inventory.json').read_text())
        self.auth = policy.authorization(B/'user-review-revisions-14-27-13-authorization.json')
        self.old = next(r for r in self.previous['articles'] if r['source_id'] == '14')
        self.current = deepcopy(self.old)
        # Deliberate metadata fixture, never a native handoff or delivery claim.
        self.current.update(source_run='fixture-new-native-run-not-produced', archive_prefix='fixture-revision14-not-produced', video_repo_path='fixture-revision14-not-produced/21.mp4', asset_commit='fixture-not-an-actual-Git-commit')
        self.batch = {'prefix': self.current['archive_prefix'], 'asset_commit': self.current['asset_commit'], 'source_ids': ['14']}

    def merged(self):
        return policy.merge_inventory(self.previous, [self.current], self.batch, self.auth)

    def test_revision_preserves_unique_count_and_full_original_row(self):
        merged = self.merged()
        self.assertEqual(merged['archived_passed_count'], 55)
        row = next(r for r in merged['articles'] if r['source_id'] == '14')
        self.assertEqual(row['previous_versions'][-1], self.old)
        self.assertEqual(policy.validate_transition(self.previous, merged, [self.current], self.auth), ([], ['14']))

    def test_no_authorization_rejected(self):
        with self.assertRaises(AssertionError):
            policy.expected_rows(self.previous, [self.current])

    def test_prior_approval_row_tampering_rejected(self):
        previous = deepcopy(self.previous)
        next(r for r in previous['articles'] if r['source_id'] == '14')['sha256'] = 'wrong'
        with self.assertRaises(AssertionError):
            policy.expected_rows(previous, [self.current], self.auth)

    def test_unreviewed_source_rejected(self):
        current = deepcopy(next(r for r in self.previous['articles'] if r['source_id'] == '26'))
        current.update(source_run='fixture-unapproved', archive_prefix='fixture26', video_repo_path='fixture26/27.mp4', asset_commit='fixture26')
        with self.assertRaises(AssertionError):
            policy.expected_rows(self.previous, [current], self.auth)

    def test_same_run_or_prefix_or_commit_or_path_rejected(self):
        for field in ['source_run', 'archive_prefix', 'asset_commit', 'video_repo_path']:
            with self.subTest(field=field):
                current = deepcopy(self.current)
                current[field] = self.old[field]
                with self.assertRaises(AssertionError):
                    policy.expected_rows(self.previous, [current], self.auth)

    def test_changed_book_order_rejected(self):
        current = deepcopy(self.current)
        current['new_id'] = '99'
        with self.assertRaises(AssertionError):
            policy.expected_rows(self.previous, [current], self.auth)

    def test_erased_old_history_rejected(self):
        merged = self.merged()
        next(r for r in merged['articles'] if r['source_id'] == '14')['previous_versions'] = []
        with self.assertRaises(AssertionError):
            policy.validate_transition(self.previous, merged, [self.current], self.auth)

    def test_unrelated_row_changes_rejected(self):
        merged = self.merged()
        next(r for r in merged['articles'] if r['source_id'] != '14')['bytes'] += 1
        with self.assertRaises(AssertionError):
            policy.validate_transition(self.previous, merged, [self.current], self.auth)

    def test_duplicate_count_and_duplicate_source_rejected(self):
        merged = self.merged()
        merged['archived_passed_count'] = 56
        with self.assertRaises(AssertionError):
            policy.validate_transition(self.previous, merged, [self.current], self.auth)
        with self.assertRaises(AssertionError):
            policy.expected_rows(self.previous, [self.current, self.current], self.auth)

    def test_failed_handoff_metadata_rejected(self):
        current = deepcopy(self.current)
        current['passed_per_article'] = False
        with self.assertRaises(AssertionError):
            policy.expected_rows(self.previous, [current], self.auth)

    def test_extra_batch_or_lost_old_batch_rejected(self):
        for extra in [True, False]:
            merged = self.merged()
            if extra:
                merged['batches'].append({'prefix': 'unrelated-fixture', 'asset_commit': 'fake', 'source_ids': []})
            else:
                del merged['batches'][0]
            with self.assertRaises(AssertionError):
                policy.validate_transition(self.previous, merged, [self.current], self.auth)

    def test_existing_addition_path_remains_valid(self):
        current = deepcopy(self.current)
        current.update(source_id='61', new_id='24')
        merged = policy.merge_inventory(self.previous, [current], {**self.batch, 'source_ids': ['61']})
        self.assertEqual(policy.validate_transition(self.previous, merged, [current]), (['61'], []))
        self.assertEqual(merged['archived_passed_count'], 56)


if __name__ == '__main__':
    unittest.main(verbosity=2)
