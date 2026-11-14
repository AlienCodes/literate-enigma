"""Join actual new native source QA to its already-produced normal18 tail.

The producer's raw inheritance record remains immutable. Its no-prior-V3
statement describes production time; the separate, real local source/GEN/MD
validation is added only now. This command generates no media or native run.
"""
import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import validate_first34_post_only as V


def spec(path):
    return V.spec(path)


def main(a):
    raw_path = Path(a.upstream_record)
    raw = V.D.load(raw_path)
    n = raw['article']
    V.require(n in {'05', '67'} and raw['prior_full_delivery_V3_claimed'] is False,
              'Only an actually new approved source with an honest raw inheritance record')
    quality_path = Path(a.source_validation_handoff)
    quality = V.D.load(quality_path)
    article = next(r for r in quality['articles'] if r['source_id'] == n)
    V.require(article['passed_per_article'] is True and quality['source_run'] == raw['source_native_run'],
              'Current source validation must belong to the actual new native run')
    V.require(spec(article['canonical_source_mp4']['path']) == article['canonical_source_mp4'] and
              article['canonical_source_mp4']['sha256'] == raw['source_video_sha256'],
              'Current source validation must inspect this exact new canonical body')
    native_inheritance = Path(raw['inherited_actual_native_QA_record'])
    V.require(V.D.digest(native_inheritance) == raw['inherited_actual_native_QA_record_sha256'],
              'Original actual native QA inheritance record changed')
    original = V.D.load(native_inheritance)
    V.require(original['actual_native_run'] == quality['source_run'] and
              original['actual_native_HEAD'] == raw['actual_native_HEAD'] and
              original['original_native_all_quality_passed'] is True and
              original['full_delivery_V3_prior_to_this_new_tail_claimed'] is False,
              'Do not invent prior delivery V3 or a new native quality run')
    adapter = copy.deepcopy(raw)
    adapter.update(inherited_passed_handoff=str(quality_path),
                   inherited_passed_handoff_sha256=V.D.digest(quality_path),
                   original_raw_upstream_record=spec(raw_path),
                   actual_current_source_validation_completed_locally=True,
                   original_raw_record_and_production_time_claim_preserved=True)
    adapter_path = raw_path.with_name(n+'-normal18-upstream-with-actual-local-source-validation.json')
    V.D.write(adapter_path, adapter)
    out = Path(a.output)
    # The reusable verifier prints an intermediate serialization. Do not expose
    # it as a handoff before the original raw inheritance evidence is attached.
    with contextlib.redirect_stdout(io.StringIO()):
        V.validate(SimpleNamespace(upstream_record=str(adapter_path),
                                  tail_report=a.tail_report, mp4=a.mp4,
                                  boundary_review=a.boundary_review, output=str(out)))
    hpath = out/'archive-handoff.json'
    hand = V.D.load(hpath)
    evidence = [raw_path, native_inheritance, Path(__file__)]
    hand.update(kind='actual-new-native-source-QA-then-authorized-normal18-local-tail',
                current_source_validation_handoff=spec(quality_path),
                original_producer_claimed_prior_delivery_V3=False,
                actual_new_source_QA_then_final_normal18_verified=True)
    item = hand['articles'][0]['section']
    item['evidence'].extend(spec(p) for p in evidence)
    inp = V.D.load(out/'actual-sample-input.json')
    inp['kind'] = hand['kind']
    inp['articles'] = [item]
    V.D.write(out/'actual-sample-input.json', inp)
    report = V.D.load(out/'report.json')
    report.update(current_source_QA_validation=spec(quality_path),
                  original_upstream_record=spec(raw_path),
                  original_native_QA_inheritance=spec(native_inheritance),
                  original_producer_claimed_prior_delivery_V3=False)
    V.D.write(out/'report.json', report)
    snapshot = out/'code-snapshot'/Path(__file__).name
    shutil.copyfile(__file__, snapshot)
    hand['tool_source_sha256'][snapshot.name] = V.D.digest(snapshot)
    # Refresh only newly constructed, not-yet-handed-off files once. Original
    # native QA, raw tail evidence, historical handoffs and media are untouched.
    for row in hand['validation_files']:
        p = Path(row['path'])
        if p in {out/'actual-sample-input.json', out/'report.json'}:
            row.update(bytes=p.stat().st_size, sha256=V.D.digest(p))
    hand['validation_files'].extend(
        {**spec(p), 'relative_validation_path':'actual-new-source-inheritance/'+str(i)+'-'+p.name}
        for i,p in enumerate(evidence))
    hand['validation_files'].append({**spec(snapshot), 'relative_validation_path':'code-snapshot/'+snapshot.name})
    for row in hand['validation_files']:
        V.checked(row)
    V.D.write(hpath, hand)
    print(json.dumps({'handoff':spec(hpath), 'record':spec(out/'validated-article-record.json'),
                      'actual_current_source_QA':spec(quality_path),
                      'original_raw_native_QA_inheritance_preserved':True}, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('upstream-record','source-validation-handoff','tail-report','mp4','boundary-review','output'):
        p.add_argument('--'+k, required=True)
    main(p.parse_args())
