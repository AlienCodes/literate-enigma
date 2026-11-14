#!/usr/bin/env python3
"""Exercise the two actual dispatch functions with the real native tokenizer.

The capture callback records producer inputs; it does not synthesize or stand
in for audio acceptance. All other tests and the original full run stay real.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('--tools', type=Path, required=True)
p.add_argument('--original-maker', type=Path, required=True)
p.add_argument('--expected', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
sha = lambda data: hashlib.sha256(data).hexdigest()
old = a.original_maker.read_text()
actual_feature = (a.tools / 'make_video.py').read_text()
new = (Path(__file__).parent / 'baseline-six/make_video.py').read_text()
assert sha(actual_feature.encode()) == '23d886be9cf999eabc682159e1ab2fc2cf6c4ccb0597f32d60d5e90a34606c0e'
assert sha(old.encode()) == '4c85e1fbdd2e82c5646d5f58df63c85eca60af4ef521f1d36f765575a568d6f3'
assert sha(new.encode()) == '6945e9bee6db143029bace6c04b4f4df7110c41ba647eee7236b0d0e5ed75203'
old_nodes, new_nodes = ast.parse(old).body, ast.parse(new).body
assert len(old_nodes) == len(new_nodes)
different = [(x, y) for x, y in zip(old_nodes, new_nodes)
             if ast.dump(x, include_attributes=False) != ast.dump(y, include_attributes=False)]
assert len(different) == 1 and different[0][0].name == '_pron'
old_func, new_func = different[0]
fixed = old_func
for node in ast.walk(fixed):
    if isinstance(node, ast.keyword) and node.arg == 'flags':
        assert ast.dump(node.value) == "Attribute(value=Name(id='re', ctx=Load()), attr='I', ctx=Load())"
        node.value = ast.Call(func=ast.Name(id='_wf', ctx=ast.Load()),
                              args=[ast.Name(id='w_', ctx=ast.Load())], keywords=[])
assert ast.dump(fixed, include_attributes=False) == ast.dump(new_func, include_attributes=False)
dicts = {str(x.relative_to(a.tools)): sha(x.read_bytes()) for x in (a.tools / '发音词典').glob('*') if x.is_file()}
ns = {'__name__': 'real_dispatch_native_namespace', '__file__': str(a.tools / 'make_video.py')}
sys.path.insert(0, str(Path.cwd()))
exec(compile(actual_feature.split("if __name__")[0], str(a.tools / 'make_video.py'), 'exec'), ns)
actual_wrapper = ns['_pron']
feature_tree=ast.parse(actual_feature); feature_fun=next(n for n in feature_tree.body if isinstance(n,ast.FunctionDef) and n.name=='_pron')
expected_fun=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='_pron')
normalized=__import__('copy').deepcopy(feature_fun)
for node in ast.walk(normalized):
    if isinstance(node,ast.BoolOp) and isinstance(node.op,ast.Or) and [ast.dump(v) for v in node.values]==["Name(id='SYNTH_PUNCT', ctx=Load())","Name(id='SPOKEN_COMMA', ctx=Load())"]:
        node.values=[ast.Name(id='SYNTH_PUNCT',ctx=ast.Load())]
# Canonicalize the one-value Or back to its original name.
class SingleOr(ast.NodeTransformer):
    def visit_BoolOp(self,node):
        self.generic_visit(node);return node.values[0] if isinstance(node.op,ast.Or)and len(node.values)==1 else node
normalized=SingleOr().visit(normalized)
assert ast.dump(normalized,include_attributes=False)==ast.dump(expected_fun,include_attributes=False)
base_functions={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
actual_functions={n.name:ast.dump(n,include_attributes=False)for n in feature_tree.body if isinstance(n,ast.FunctionDef)}
feature_changed=[k for k in base_functions if base_functions[k]!=actual_functions[k]]
assert set(feature_changed)=={'_synth_punct','_pron','chunk_token_starts','sentence_audio','build'}
new_wrapper = actual_wrapper
# Reload only the original function definition into the same genuine producer
# namespace. The models, tokenizer, dictionaries and phonemes_of are identical.
original_node = next(n for n in ast.parse(old).body if isinstance(n, ast.FunctionDef) and n.name == '_pron')
exec(compile(ast.Module(body=[original_node], type_ignores=[]), '<actual-original-_pron>', 'exec'), ns)
old_wrapper = ns['_pron']
ns['_pron'] = new_wrapper
expected = json.loads(a.expected.read_text())['actual_original_wrapper_vs_in_memory_candidate_callback_traces']
rows = []
for case in expected:
    trace = {}
    for label, wrapper in [('original_actual_dispatch', old_wrapper), ('candidate_dispatch', new_wrapper)]:
        events = []
        def capture(text, voice, speed=1., lang='en-us', **kw):
            events.append({'input_text': text, 'input_text_SHA256': sha(text.encode()),
                           'speed': speed, 'lang': lang, 'kw': kw})
        wrapper(capture)(case['source_text'], ns['V'], speed=.95, lang='en-us')
        assert len(events) == 1
        assert events[0] == case[label], case['case'] + ':' + label
        trace[label] = events[0]
    rows.append({'case': case['case'], 'source_text': case['source_text'], **trace})
assert rows[0]['candidate_dispatch']['input_text'] == rows[0]['source_text']
assert rows[0]['candidate_dispatch']['kw'] == {}
assert all(x['candidate_dispatch'] == x['original_actual_dispatch'] for x in rows[1:])
# The exact prior buggy function is a real negative control for the desired
# ordinary-word dispatch rule; the brand still requires corrected phonemes.
assert rows[0]['original_actual_dispatch']['kw'].get('is_phonemes') is True
assert next(x for x in rows if x['case'] == 'literal-company-NeXT')['candidate_dispatch']['kw']['is_phonemes'] is True
assert all(sha((a.tools / name).read_bytes()) == h for name, h in dicts.items())
report = {'status': 'passed_actual_native_case_consistent_producer_dispatch',
          'original_maker_SHA256': sha(old.encode()), 'candidate_maker_SHA256': sha(actual_feature.encode()),
          'casefix_baseline_all_other_AST_exact': True, 'all_nonfeature_function_AST_exact': True, 'declared_feature_function_changes': feature_changed, 'only_AST_keyword_change_re_I_to_existing_wf': True,
          'real_native_model_namespace_and_tokenizer': True,
          'four_actual_callback_traces': rows, 'ordinary_next_restored_to_original_text_input': True,
          'proper_NeXT_and_correct_Origin_Haber_and_BASF_inputs_exact': True,
          'prior_bug_actual_negative_control_rejected_by_new_requirement': True,
          'all_dictionary_files_byte_exact': dicts, 'private_PCM_exported': False,
          'audio_inference_in_this_dispatch_test': False, 'article_quality_accepted': False}
a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k != 'all_dictionary_files_byte_exact'}, ensure_ascii=False))
