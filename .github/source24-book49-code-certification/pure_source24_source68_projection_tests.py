"""Only AST-extracted original parser/source/mother guards; no model or audio."""
from pathlib import Path
import argparse
import ast
import copy
import json
import re
import unittest

DISPLAY = 'Its amenities included a lounge and, that year, a grand piano.'
PROJECTED = 'Its amenities included a lounge and that year, a grand piano.'


def pure(path):
    names = {'_speech_comma_spec', '_speech_comma_display_for_data',
             '_speech_source_context', '_speech_rule', '_speech_mother_guard'}
    nodes = []
    for n in ast.parse(Path(path).read_text()).body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            nodes.append(n)
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_SPOKEN_COMMA_ALLOWED' for t in n.targets):
            nodes.append(n)
    env = {'re': re, 'SPOKEN_COMMA': {}, '_SPOKEN_SOURCE_NO': None}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return env


def data68():
    return {'no': '68', 'sentences': [
        {'chunks': [{'en': 'The first sentence.'}]},
        {'chunks': [{'en': DISPLAY}]}],
        '朗读删逗号': {'S2': {'篇号': 68, '原文': DISPLAY, '逗号序号': [1]}}}


class ProjectionTests(unittest.TestCase):
    def test_prior18_rejects68(self):
        with self.assertRaises(SystemExit):
            pure(A.prior18)['_speech_comma_spec'](data68(), 'S2')

    def test_exact_first_comma_only_display_retained(self):
        d = data68()
        before = copy.deepcopy(d)
        got = pure(A.candidate)['_speech_comma_spec'](d, 'S2')
        self.assertEqual(got['projected'], PROJECTED)
        self.assertIn('year, a grand piano.', got['projected'])
        self.assertEqual(got['projected'].count(','), 1)
        self.assertFalse(got['needs_mother_binding'])
        self.assertEqual(d, before)

    def test_all_prior_four_cases_parser_outputs_identical(self):
        for path, labels in [(A.fixture43, ['S16']), (A.fixture52, ['S4', 'S18']),
                             (A.fixture24, ['S18'])]:
            d = json.loads(Path(path).read_bytes())
            for label in labels:
                with self.subTest(path=str(path), label=label):
                    self.assertEqual(pure(A.prior18)['_speech_comma_spec'](d, label),
                                     pure(A.candidate)['_speech_comma_spec'](d, label))

    def test_original_three_cases_identical_to_certified17(self):
        for path, labels in [(A.fixture43, ['S16']), (A.fixture52, ['S4', 'S18'])]:
            d = json.loads(Path(path).read_bytes())
            for label in labels:
                self.assertEqual(pure(A.prior17)['_speech_comma_spec'](d, label),
                                 pure(A.candidate)['_speech_comma_spec'](d, label))

    def test_wrong_source_and_wrong_sentence_rejected(self):
        for no, label in [('67', 'S2'), ('69', 'S2'), ('68', 'S1')]:
            d = data68()
            spec = d['朗读删逗号'].pop('S2')
            d['no'] = no
            spec['篇号'] = int(no)
            d['朗读删逗号'][label] = spec
            with self.subTest(no=no, label=label), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, label)

    def test_wrong_ordinal_rejected(self):
        for value in [[2], [1, 2], [0], [], [1, 1], [True]]:
            d = data68()
            d['朗读删逗号']['S2']['逗号序号'] = value
            with self.subTest(value=value), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, 'S2')

    def test_changed_full_display_even_with_matching_spec_rejected(self):
        for changed in [DISPLAY.replace('amenities', 'facilities'),
                        DISPLAY.replace('grand piano', 'piano'), DISPLAY + ' ',
                        DISPLAY.replace('year,', 'year;')]:
            d = data68()
            d['sentences'][1]['chunks'][0]['en'] = changed
            d['朗读删逗号']['S2']['原文'] = changed
            with self.subTest(changed=changed), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, 'S2')

    def test_extra_field_wrong_typed_source_rejected(self):
        for key, value in [('extra', True), ('篇号', '68')]:
            d = data68()
            d['朗读删逗号']['S2'][key] = value
            with self.subTest(key=key), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, 'S2')

    def test_old_ending_or_synth_punctuation_rejected(self):
        for key in ['结尾句', '合成标点']:
            d = data68()
            d[key] = {'S2': {'old': True}}
            with self.subTest(key=key), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, 'S2')

    def test_stale_physical_controls_need_binding_and_reject_unknown_mother(self):
        d = data68()
        d['非人声区间'] = {'S2': [[.2, .3]]}
        env = pure(A.candidate)
        spec = env['_speech_comma_spec'](d, 'S2')
        self.assertTrue(spec['needs_mother_binding'])
        env['SPOKEN_COMMA'] = {('68', 'S2'): spec}
        env['_SPOKEN_SOURCE_NO'] = '68'
        for old in ({}, {DISPLAY: 'old-mother-not-real-test-only'}):
            env['VFP'] = old
            with self.subTest(old=old), self.assertRaises(SystemExit):
                env['_speech_mother_guard'](DISPLAY, 'new-mother-not-real-test-only')

    def test_context_absence_is_still_hard_failure(self):
        env = pure(A.candidate)
        env['SPOKEN_COMMA'] = {('68', 'S2'): env['_speech_comma_spec'](data68(), 'S2')}
        with self.assertRaises(SystemExit):
            env['_speech_rule'](DISPLAY)

    def test_source24_full_display_guard_retained(self):
        d = json.loads(A.fixture24.read_bytes())
        label = 'S18'
        d['sentences'][17]['chunks'][0]['en'] = d['sentences'][17]['chunks'][0]['en'].replace('Precision', 'Accuracy')
        d['朗读删逗号'][label]['原文'] = d['朗读删逗号'][label]['原文'].replace('Precision', 'Accuracy')
        with self.assertRaises(SystemExit):
            pure(A.candidate)['_speech_comma_spec'](d, label)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for key in ('candidate', 'prior18', 'prior17', 'fixture43', 'fixture52', 'fixture24'):
        p.add_argument('--' + key, type=Path, required=True)
    A, rest = p.parse_known_args()
    unittest.main(argv=[__file__] + rest, verbosity=2)
