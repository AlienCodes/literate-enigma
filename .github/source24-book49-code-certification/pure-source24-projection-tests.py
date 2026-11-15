"""Run original pure parser/guards only; no model, audio, video or network."""
from pathlib import Path
import ast
import copy
import json
import re
import unittest

R = Path(__file__).resolve().parent
ORIGINAL = R / 'prior17-make_video.py'
DRAFT = R / 'request24-original-display.json'
DISPLAY = 'Precision put six ashore within reach of help and, a century on, brought their ship back into view.'
PROJECTED = 'Precision put six ashore within reach of help and a century on, brought their ship back into view.'


def pure(path):
    names = {'_speech_comma_spec', '_speech_comma_display_for_data',
             '_speech_source_context', '_speech_rule', '_speech_mother_guard'}
    body = []
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            body.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_SPOKEN_COMMA_ALLOWED' for t in node.targets):
            body.append(node)
    env = {'re': re, 'SPOKEN_COMMA': {}, '_SPOKEN_SOURCE_NO': None}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), env)
    return env


def candidate_data():
    d = json.loads(DRAFT.read_bytes())
    d['朗读删逗号'] = {'S18': {'篇号': 24, '原文': DISPLAY, '逗号序号': [1]}}
    return d


class ProjectionTests(unittest.TestCase):
    def test_unmodified17_actually_rejects_new_source24(self):
        with self.assertRaises(SystemExit):
            pure(ORIGINAL)['_speech_comma_spec'](candidate_data(), 'S18')

    def test_only_first_and_comma_removed_display_both_commas_unchanged(self):
        d = candidate_data()
        before = copy.deepcopy(d['sentences'])
        parsed = pure(R / 'make_video.py')['_speech_comma_spec'](d, 'S18')
        self.assertEqual(parsed['original'], DISPLAY)
        self.assertEqual(parsed['projected'], PROJECTED)
        self.assertEqual(parsed['projected'].count(','), 1)
        self.assertIn('on, brought', parsed['projected'])
        self.assertEqual(d['sentences'], before)

    def test_old_three_cases_produce_exact_same_pure_parser_outputs(self):
        files = [(R / 'feature-sources/43.json', ['S16']),
                 (R / 'feature-sources/52.json', ['S4', 'S18'])]
        a, b = pure(ORIGINAL), pure(R / 'make_video.py')
        for path, labels in files:
            data = json.loads(path.read_bytes())
            for label in labels:
                with self.subTest(path=path.name, label=label):
                    self.assertEqual(a['_speech_comma_spec'](data, label), b['_speech_comma_spec'](data, label))

    def test_wrong_comma_selection_rejected(self):
        for selection in [[2], [1, 2], [], [1, 1], [0]]:
            data = candidate_data()
            data['朗读删逗号']['S18']['逗号序号'] = selection
            with self.subTest(selection=selection), self.assertRaises(SystemExit):
                pure(R / 'make_video.py')['_speech_comma_spec'](data, 'S18')

    def test_other_source_or_sentence_rejected(self):
        data = candidate_data()
        data['no'] = '25'
        data['朗读删逗号']['S18']['篇号'] = 25
        with self.assertRaises(SystemExit):
            pure(R / 'make_video.py')['_speech_comma_spec'](data, 'S18')
        data = candidate_data()
        data['朗读删逗号']['S17'] = data['朗读删逗号'].pop('S18')
        with self.assertRaises(SystemExit):
            pure(R / 'make_video.py')['_speech_comma_spec'](data, 'S17')

    def test_new_tuple_cannot_authorize_changed_full_display_even_if_spec_matches(self):
        data = candidate_data()
        data['sentences'][17]['chunks'][1]['en'] = data['sentences'][17]['chunks'][1]['en'].replace('a century on,', 'two centuries on,')
        data['朗读删逗号']['S18']['原文'] = DISPLAY.replace('a century on,', 'two centuries on,')
        with self.assertRaises(SystemExit):
            pure(R / 'make_video.py')['_speech_comma_spec'](data, 'S18')

    def test_stale_target_controls_and_fingerprint_still_block_new_mother(self):
        env = pure(R / 'make_video.py')
        parsed = env['_speech_comma_spec'](candidate_data(), 'S18')
        self.assertTrue(parsed['needs_mother_binding'])
        env['SPOKEN_COMMA'] = {('24', 'S18'): parsed}
        env['_SPOKEN_SOURCE_NO'] = '24'
        env['VFP'] = {DISPLAY: '44b73ada53b6'}
        with self.assertRaises(SystemExit):
            env['_speech_mother_guard'](DISPLAY, 'test-only-new-fingerprint-not-real-audio')
        env['VFP'] = {}
        with self.assertRaises(SystemExit):
            env['_speech_mother_guard'](DISPLAY, 'test-only-new-fingerprint-not-real-audio')


if __name__ == '__main__':
    unittest.main(verbosity=2)
