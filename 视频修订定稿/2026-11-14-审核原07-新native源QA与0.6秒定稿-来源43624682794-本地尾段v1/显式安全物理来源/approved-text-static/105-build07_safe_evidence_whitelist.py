from pathlib import Path
import hashlib,json
O=Path(__file__).parent;C=O/'candidate-payload';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();paths=[]
for rel in['视频/脚本/07.json','视频/工具/初稿生成/gen07.py','新版定稿/07-the-octopus-that-escaped.md','视频/制作记录/07_待改清单.md','视频/制作记录/逐句确认/07.json']:paths.append(C/rel)
paths +=[O/x for x in['draft080088-implementation-report.json','draft089-implementation-report.json','static-draft080089-report.json','original-reference-context-fixture-restoration.json','thin-validation-v1/report.json','thin-validation-v1/report-v2-context-complete.json','thin-validation-v1/report-v3-final090-table-normalized.json','actual-original-voice-input-and-DSP-invariance.json','actual-final-static-visual-review.json','source07-final090-source-freeze-and-static-approval.json','approved-video-layouts70-only07-final090.json','independent-draft080089-semantic-scope-readonly-review.json','original-sync-before-final-freeze/actual-wordtable-only-source-sync-normalization.json','original-sync-before-final-freeze/actual-original-sync.diff','original-sync-before-final-freeze/sync.log','original-sync-before-final-freeze/07-before-source-sync.md','original-sync-before-final-freeze/07-predicted-original-sync.md','actual-contact-review/contact-map.json']]
for folder in[O/'thin-validation-v1/logs',O/'thin-validation-v1/logs-v2-context-complete',O/'thin-validation-v1/logs-v3-final090-table-normalized']:
 paths.extend(p for p in folder.glob('*.log')if p.is_file())
for folder in[O/'static-1080',O/'static-4K']:paths.extend(p for p in folder.glob('after*.png')if p.is_file())
paths.extend(p for p in(O/'actual-contact-review').glob('*.jpg')if p.is_file());paths.extend(p for p in O.glob('feedback-*-actual-draft-intake.json')if p.is_file());paths.extend(p for p in O.glob('*.py')if p.is_file())
for rel in['视频/脚本/07.json','视频/工具/初稿生成/gen07.py','新版定稿/07-the-octopus-that-escaped.md']:paths.append(O/'before'/rel)
for p in(O/'history080088-v1').glob('*'):
 if p.is_file():paths.append(p)
paths.append(Path('/dev/shm/article07-review-intake-20261114/independent-user090-final-purpose-and-video-order-addendum.json'))
for n in range(80,91):paths.append(Path(f'/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-{n:03}.json'))
deny={'b9a257a23820944ee95d568b67d1cd78947b1c1814bb70dc99a45871f488f778','55026ce1b7cdb7e9c1a72da2f715e3d9e6e6f45050a8ddd575dc052b09dca872','bcb37d8930d804988c95da94b9cfeaaab2c7b026df96e6e4567f9b698ce88fbf'};seen=set();rows=[]
for p in paths:
 if str(p)in seen:continue
 seen.add(str(p));assert p.is_file(),p;h=sha(p);assert h not in deny;assert p.suffix.lower()not in['.pdf','.wav','.mp4','.m4a','.pkl','.pyc','.onnx'];assert p.name!='用户同意记录.json';rows.append(dict(path=str(p),bytes=p.stat().st_size,sha256=h))
r=dict(source_id='07',frozen_book_order='03',requested_video_order='01',kind='explicit-safe-user080-090-source-text-static-evidence-whitelist',source_JSON_sha256='b9b4ec0b90a4d1070b193fe42f5c30e1a3717560b03746a06d4b16388a83047f',GEN_sha256='63096b6215488d1534827116c2cdfd3ee20e694f38c8df66b393ef3893b38674',MD_sha256='c8a55f3a7e3e0ceccdaa047f1da6a7d58abf82ae627763bd299e86afdb53ddc7',original_GEN_fullJSON_exact_original_text000_static_and_semantic_all_completed=True,actual_new_native_quality_not_claimed=True,files=rows,count=len(rows),total_bytes=sum(x['bytes']for x in rows),denied_payload_SHA_hits=[],excluded=['all private PCM/GT/mothers/cache','all audio or MP4 files','all PDF','all live ROOT detailed status','global context/auth','blocked055/056 raw ledgers','unrelated articles'],old_first34ZIP_and_current03_alias_unchanged=True)
p=O/'safe-source07-final090-text-static-evidence-whitelist.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p),count=len(rows),bytes=r['total_bytes']),ensure_ascii=False))
