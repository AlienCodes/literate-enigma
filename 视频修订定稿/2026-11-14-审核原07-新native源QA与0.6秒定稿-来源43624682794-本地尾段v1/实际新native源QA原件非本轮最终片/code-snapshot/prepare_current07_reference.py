"""Compare the REAL new source07 AAC object to the current first34 accepted one.

Requires an actual successful native already prepared by the unchanged intake.
Writes no reference registration until the complete measured objects are equal.
No media generation, audio repair, remote write, legacy catalog edit or old-H edit.
"""
import argparse,json,hashlib
from pathlib import Path
import delivery as D

CURRENT_H=Path('/dev/shm/first34-hold06-intake/validated/book03-source07/archive-handoff.json')
CURRENT_H_SHA='dd30a02b3d58569717599d643a9c3f0400ebea26fb70f9691cfb11666e90bcf3'
CURRENT_MOVIE_SHA='3ba931446468d28e2d1eea2fa57ddf1c79b24bad52be4fbd697a828c7865dede'
REQUEST_SHA='b9b4ec0b90a4d1070b193fe42f5c30e1a3717560b03746a06d4b16388a83047f'
GEN_SHA='63096b6215488d1534827116c2cdfd3ee20e694f38c8df66b393ef3893b38674'
RUN=43624682794
HEAD='de032df394223d16268ef0448ed5eaf11e649765'
AAC='16b6293adfc7a3c35224408ae39d831317e1932f8d47876824e129129c9115d8'
PROJECTION='dde0cc8aeda5d9f505270c9d4b1444542ee65e5d7c53cfd7741383447af4c897'

def spec(p):
 p=Path(p).resolve();return {'path':str(p),'bytes':p.stat().st_size,'sha256':D.digest(p)}

def main(a):
 root=Path(a.native_root).resolve();out=Path(a.source_output).resolve();folder=out/'07';folder.mkdir(parents=True,exist_ok=True)
 run=D.load(out/'actual-native-run.json');job=D.load(folder/'actual-native-job.json');context=D.load(root/'inline-adapter-context.json')
 D.require(run['id']==RUN and run['head_sha']==HEAD and job['run_id']==RUN and job['status']=='completed'and job['conclusion']=='success','Only the actually successful immutable user090 native output')
 status=D.load(root/'files/07-status.json');request=status['request_source_sha256']
 D.require(status['article']=='07'and status['passed']is True and status['canonical_pipeline_passed']is True and request['视频/脚本/07.json']==REQUEST_SHA and request['视频/工具/初稿生成/gen07.py']==GEN_SHA,'Actual new native source/full-QA request differs')
 D.require(status['accepted_source']['sha256']==CURRENT_MOVIE_SHA and status['canonical_aac_adts_sha256']==status['accepted_source']['aac_adts_sha256']==AAC,'Native actual accepted/current voice differs')
 D.require(D.digest(CURRENT_H)==CURRENT_H_SHA,'Existing current07 H bytes changed')
 h=D.load(CURRENT_H);row=next(x for x in h['articles']if x['source_id']=='07');record_path=Path(row['validated_record']);record=D.load(record_path);accepted=D.checked_file(row['final_mp4'])
 D.require(row['passed_per_article']is True and row['new_id']==record['new_id']=='03'and record['sha256']==CURRENT_MOVIE_SHA and record['bytes']==14781446,'Existing current07 accepted lineage differs')
 new=root/'files/07-4K-读完即转简述2秒.mp4';new_audio=D.actual_aac(new);old_audio=D.actual_aac(accepted)
 D.require(new_audio==old_audio,'Actual complete new/current AAC, codec, payload, side-data or absolute packet timing differs')
 D.require(new_audio['aac_adts_sha256']==AAC and new_audio['packet_projection_sha256']==PROJECTION and new_audio['packet_count']==6443,'Actual source07 full packet reference differs')
 compact=lambda value:{k:v for k,v in value.items()if k!='projection'}
 identity={'kind':'actual-measured-current07-to-user090-new-selected-canonical-entire-AAC-object-identity','actual_comparison_passed':True,'codec_AAC_payload_side_data_and_absolute_packet_projection_entire_objects_equal':True,'source_id':'07','quality_book_order':'03','requested_video_order':'01','actual_native_run':RUN,'actual_native_head':HEAD,'accepted_MP4_sha256':D.digest(accepted),'new_canonical_MP4_sha256':D.digest(new),'new_audio':compact(new_audio),'accepted_audio':compact(old_audio),'all6443_packet_objects_and_codec_compared_in_memory':True,'projection_lists_not_duplicated_full_MP4_permanently_preserved':True,'audio_or_video_generated_or_changed':False}
 ip=folder/'actual-current07-accepted-voice-identity.json'
 if ip.exists():D.require(D.load(ip)==identity,'Existing actual comparison belongs to different data')
 else:D.write(ip,identity)
 legacy=D.load(out/'frozen-primary/来源视频清单.json') if(out/'frozen-primary/来源视频清单.json').exists()else D.load(Path(__file__).parent/'actual53-64-validation/frozen-primary/来源视频清单.json')
 entries=legacy['videos'] if isinstance(legacy,dict)and'videos'in legacy else legacy
 if isinstance(entries,dict):old=entries['07']
 else:old=next(x for x in entries if str(x.get('id',x.get('no',''))).zfill(2)=='07')
 registry={'kind':'exact-user090-current-source07-accepted-reference-registration','source_id':'07','quality_book_order':'03','requested_video_order':'01','actual_new_native_run':RUN,'actual_new_native_head':HEAD,'request_source_sha256':REQUEST_SHA,'request_generator_sha256':GEN_SHA,'current_accepted_prior_handoff':spec(CURRENT_H),'current_accepted_prior_record':spec(record_path),'current_accepted_MP4':spec(accepted),'actual_entire_oldcurrent_to_newcanonical_audio_identity':spec(ip),'actual_new_canonical_SHA256':D.digest(new),'legacy_catalog_identity_preserved':old,'user090_authority':spec('/dev/shm/archive-writer-user-review-20261114/USER-REVIEW-2026-11-14-090.json'),'old_H_legacy_catalog_and_media_unchanged':True,'no_new_native_or_TTS_in_this_comparison':True}
 rp=folder/'exact07-current-accepted-reference-registration.json'
 if rp.exists():D.require(D.load(rp)==registry,'Existing reference registration belongs to different data')
 else:D.write(rp,registry)
 print(json.dumps({'identity':spec(ip),'registry':spec(rp),'new_canonical':spec(new)},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-root',required=True);p.add_argument('--source-output',required=True);main(p.parse_args())
