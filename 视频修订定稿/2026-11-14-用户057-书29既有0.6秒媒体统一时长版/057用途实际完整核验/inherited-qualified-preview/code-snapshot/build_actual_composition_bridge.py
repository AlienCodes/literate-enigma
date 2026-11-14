"""Record exact old/new helper function equality for a real frozen candidate.

Only bridges unchanged existing art pixels/source binding/packet readers. This
does not approve a helper's new hold logic or any actual video.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ORIGINAL_SHA = 'dc204b91415e28297b844e9666087b0e23e67194944b359cb5fb5ddbca0f1208'
FUNCTIONS = ('run', 'digest_bytes', 'sha', 'probe', 'packets', 'packet_timing',
             'coded_pictures_sha', 'boundary_is_idr', 'aac_sha', 'rgb_sha',
             'source_layout_digest', 'source_layout_binding', 'approved_inputs',
             'compose_illustration', 'verify_static_pages')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def functions(path):
    return {v.name: ast.dump(v, include_attributes=False)
            for v in ast.parse(Path(path).read_text()).body
            if isinstance(v, (ast.FunctionDef, ast.AsyncFunctionDef))}


def build(original, candidate, candidate_sha256, output):
    assert digest(original) == ORIGINAL_SHA, 'Use the real originally approved composition program'
    assert digest(candidate) == candidate_sha256, 'Actual frozen candidate bytes differ'
    old, new = functions(original), functions(candidate)
    rows = []
    for name in FUNCTIONS:
        assert old[name] == new[name], 'Composition/source/packet algorithm actually changed: ' + name
        rows.append({'function': name, 'AST_identical': True,
                     'AST_sha256': hashlib.sha256(old[name].encode()).hexdigest()})
    report = {'kind': 'actual_frozen_helper_existing_composition_source_and_packet_function_bridge',
              'original_composition_program_sha256': ORIGINAL_SHA,
              'new_actual_preparer_sha256': candidate_sha256,
              'actual_function_comparisons': rows,
              'old_composition_records_modified': False,
              'existing_pixels_and_full120_frame_checks_still_required': True,
              'new_hold18_logic_or_actual_media_pass_claimed': False}
    target = Path(output)
    assert not target.exists(), 'Preserve previously frozen bridge reports'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('original', 'candidate', 'candidate-sha256', 'output'):
        p.add_argument('--' + k, required=True)
    a = p.parse_args()
    build(a.original, a.candidate, a.candidate_sha256, a.output)
