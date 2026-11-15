"""Exact source35 additional parser tests; no model/audio or native certificate."""
from pathlib import Path
import argparse
import ast
import copy
import json
import re
import unittest

DISPLAY = 'In 2014 came an eerie, man-made twist.'
PROJECTED = 'In 2014 came an eerie man-made twist.'


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


def data35():
    sentences = [{'chunks': [{'en': 'Unchanged context sentence.'}]} for _ in range(15)]
    sentences[-1] = {'chunks': [{'en': DISPLAY}]}
    return {'no': '35', 'sentences': sentences,
            '朗读删逗号': {'S15': {'篇号': 35, '原文': DISPLAY, '逗号序号': [1]}}}


def data68():
    text = 'Its amenities included a lounge and, that year, a grand piano.'
    return {'no': '68', 'sentences': [{'chunks': [{'en': 'Context.'}]}, {'chunks': [{'en': text}]}],
            '朗读删逗号': {'S2': {'篇号': 68, '原文': text, '逗号序号': [1]}}}


class Source35Tests(unittest.TestCase):
    def test_prior19_rejects35(self):
        with self.assertRaises(SystemExit):
            pure(A.prior19)['_speech_comma_spec'](data35(), 'S15')

    def test_exact_single_comma_removed_hyphen_and_display_retained(self):
        d = data35()
        before = copy.deepcopy(d)
        p = pure(A.candidate)['_speech_comma_spec'](d, 'S15')
        self.assertEqual(p['projected'], PROJECTED)
        self.assertIn('man-made', p['projected'])
        self.assertEqual(p['projected'].replace(',', ''), DISPLAY.replace(',', ''))
        self.assertFalse(p['needs_mother_binding'])
        self.assertEqual(d, before)

    def test_all_prior_five_case_outputs_exact_to19(self):
        cases = [(json.loads(A.fixture43.read_bytes()), ['S16']),
                 (json.loads(A.fixture52.read_bytes()), ['S4', 'S18']),
                 (json.loads(A.fixture24.read_bytes()), ['S18']), (data68(), ['S2'])]
        for data, labels in cases:
            for label in labels:
                with self.subTest(no=data['no'], label=label):
                    self.assertEqual(pure(A.prior19)['_speech_comma_spec'](data, label),
                                     pure(A.candidate)['_speech_comma_spec'](data, label))

    def test_wrong_source_sentence_and_ordinal_rejected(self):
        for no, label, ordinals in [('34', 'S15', [1]), ('36', 'S15', [1]),
                                    ('35', 'S14', [1]), ('35', 'S15', [2]),
                                    ('35', 'S15', [1, 2]), ('35', 'S15', [])]:
            d = data35()
            spec = d['朗读删逗号'].pop('S15')
            d['no'] = no
            spec.update({'篇号': int(no), '逗号序号': ordinals})
            d['朗读删逗号'][label] = spec
            with self.subTest(no=no, label=label, ordinals=ordinals), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, label)

    def test_changed_full_display_or_hyphen_is_rejected_even_if_spec_matches(self):
        for text in [DISPLAY.replace('2014', '2015'), DISPLAY.replace('man-made', 'man made'),
                     DISPLAY.replace('eerie', 'strange'), DISPLAY.replace(',', ';')]:
            d = data35()
            d['sentences'][-1]['chunks'][0]['en'] = text
            d['朗读删逗号']['S15']['原文'] = text
            with self.subTest(text=text), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, 'S15')

    def test_old_ending_or_synth_and_wrong_typed_spec_rejected(self):
        for kind in ['ending', 'synth', 'extra', 'typed']:
            d = data35()
            if kind in ['ending', 'synth']:
                d['结尾句' if kind == 'ending' else '合成标点'] = {'S15': {'old': True}}
            elif kind == 'extra':
                d['朗读删逗号']['S15']['extra'] = True
            else:
                d['朗读删逗号']['S15']['篇号'] = '35'
            with self.subTest(kind=kind), self.assertRaises(SystemExit):
                pure(A.candidate)['_speech_comma_spec'](d, 'S15')

    def test_stale_mother_and_absent_source_context_still_block(self):
        d = data35()
        d['非人声区间'] = {'S15': [[.1, .2]]}
        env = pure(A.candidate)
        spec = env['_speech_comma_spec'](d, 'S15')
        self.assertTrue(spec['needs_mother_binding'])
        env['SPOKEN_COMMA'] = {('35', 'S15'): spec}
        with self.assertRaises(SystemExit):
            env['_speech_rule'](DISPLAY)
        env['_SPOKEN_SOURCE_NO'] = '35'
        for old in [{}, {DISPLAY: 'test-only-old-mother'}]:
            env['VFP'] = old
            with self.subTest(old=old), self.assertRaises(SystemExit):
                env['_speech_mother_guard'](DISPLAY, 'test-only-new-mother')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ['candidate', 'prior19', 'fixture24', 'fixture43', 'fixture52']:
        p.add_argument('--' + name, type=Path, required=True)
    A, rest = p.parse_known_args()
    unittest.main(argv=[__file__] + rest, verbosity=2)
