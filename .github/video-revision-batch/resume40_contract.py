"""Exact40 original-native input/summary contract; no synthesis or acceptance shim."""
import ast,copy,hashlib,json,subprocess,tempfile
from fractions import Fraction
from pathlib import Path

REFERENCE_SHA256='531d8967e74b0ad121df3a70782a956543614aff9a97a9309f375bdafaeebdd0'
ROOT_AUTH='b75a9e72816b032faca17cb40fd1e98ad71d3b37def12931e03cc174d3f8877a'
def require(ok,message):
 if not ok:raise ValueError(message)
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  while chunk:=f.read(1048576):h.update(chunk)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def command(args):return subprocess.run(args,check=True,capture_output=True,text=True).stdout.strip()
def checked(p,s):
 p=Path(p);require(p.is_file()and p.stat().st_size==s['bytes']and digest(p)==s['sha256'],'Exact original input differs: '+p.name);return p

def exact_summary_pair(article,request_sha,gen_sha,actual_sha,expected,actual,ref):
 return (article=='40'and ref['root_exact_summary_decision_sha256']==ROOT_AUTH and request_sha=='66f6b6206d38e4cbcb5fd92faf9e3c5118b8749962eb52e68121204070ddb7ec'and gen_sha=='9334ab505726068c08e7dd9c6f673bd2c0b0e5403d8ae9a119d89ab1087bcf1c'and actual_sha=='362e802d79a67364da0392f0af44b855688210cbb3b7393478faad91c877809d'and expected==ref['request_summary']and actual==ref['actual_summary'])

def prepare_tail(original_source):
 """Original outer statements AST-exact except two unavailable-private-WAV reads."""
 tree=ast.parse(original_source);body=next(n.body for n in tree.body if isinstance(n,ast.Try));start=next(i for i,n in enumerate(body)if isinstance(n,ast.Assign)and n.lineno>1000 and any(isinstance(t,ast.Name)and t.id=='current'for t in n.targets));tail=copy.deepcopy(body[start:]);changed=[]
 class PCM(ast.NodeTransformer):
  def visit_Call(self,node):
   self.generic_visit(node)
   if isinstance(node.func,ast.Name)and node.func.id=='sha'and len(node.args)==1 and ast.unparse(node.args[0])in ["W / 'work_40/a.wav'","W / f'work_{NO}/a.wav'"]:
    changed.append(dict(line=node.lineno,original=ast.unparse(node)));return ast.copy_location(ast.Call(func=ast.Name(id='inherited_pcm_sha',ctx=ast.Load()),args=[],keywords=[]),node)
   return node
 patched=PCM().visit(ast.Module(body=tail,type_ignores=[]));ast.fix_missing_locations(patched);require(len(changed)==2,'Original tail private-PCM callsites differ')
 require(not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='official'for n in ast.walk(patched)),'No original draft/final voice/body pipeline may run')
 return patched,dict(original_outer_start_line=body[start].lineno,original_outer_statement_count=len(tail),private_PCM_reads_replaced_by_explicit_inherited_proof=changed,all_other_original_outer_statement_AST_unchanged=True,original_same_summary_content_AST_unchanged=True,no_original_draft_or_final_or_TTS_call_in_suffix=True)

def verify_inputs(capsule,request,original_program,decision,ref,accepted_video=None,inspect_media=True):
 require(digest(Path(__file__).with_name('resume40-reference.json'))==REFERENCE_SHA256 and ref==load(Path(__file__).with_name('resume40-reference.json')),'Only the frozen actual source40 reference document')
 capsule=Path(capsule);request=Path(request);require(ref['source_id']=='40'and ref['quality_book_order']=='46'and ref['source_native_run']==43640848824 and ref['source_native_HEAD']=='a2c0aa473654d24448ec9077aa1af75ee5fb81e3','Only exact failed native40 completion')
 checked(original_program,ref['original_wrapper']);require(digest(decision)==ref['root_exact_summary_decision_sha256']==ROOT_AUTH,'Exact root summary authority required');checked(capsule/'artifact.zip',ref['original_artifact_zip'])
 for name,s in ref['input_files'].items():checked(capsule/'files'/name,s)
 for rel,h in ref['request_files'].items():require(digest(request/rel)==h,'Exact immutable requested JSON/GEN/MD differs')
 s=load(capsule/'files/40-status.json');proof=load(capsule/'files/40-failed-draft-proof.json');fingerprint=load(capsule/'files/40-failed-draft-fingerprint.json');actual=capsule/'files/40-failed-working-source.json';movie=capsule/'files/40-failed-draft.mp4'
 require(s['article']=='40'and s['passed']is False and s['error']=='Canonical summary changed words, punctuation or the five main points.'and s['stage']=='original-stamp-after-production.log','Do not relabel or broaden the old actual outer failure')
 require(proof['passed']is False and proof['acceptance']is False and proof['official_fingerprint_matches_current_video_source_and_pcm']is True and proof['source_sha256']==digest(actual)==ref['actual_source_sha256']and proof['video_sha256']==digest(movie)==ref['canonical_video_sha256']and proof['internal_pcm_sha256']==ref['expected_RAW_PCM_sha256']and proof['official_fingerprint_sha256']==digest(capsule/'files/40-failed-draft-fingerprint.json'),'Actual canonical/source/fingerprint/PCM provenance differs')
 require(fingerprint['视频']==ref['canonical_video_sha256'][:16]and fingerprint['配音']==ref['expected_RAW_PCM_sha256'][:16],'Original official fingerprint does not bind video and inherited PCM')
 require(s['actual_native_fastcheck_stamp']==ref['original_stamp']and s['actual_native_core_certification']==ref['original_gate_certification']and s['real_restored_stamp_validated']is True,'Actual original full certification/stamp differs')
 rows=s['check_summaries'];require('original-stamp-after-production.log'in rows and any('⑤ 出片后核查：全部通过'in x for x in rows['canonical-draft-00.log'])and any('用户定稿原话：有'in x for x in rows['canonical-final4K-00.log']),'Original successful voice/text/4K/stamp control-flow evidence missing')
 require(exact_summary_pair('40',digest(request/'视频/脚本/40.json'),digest(request/'视频/工具/初稿生成/gen40.py'),digest(actual),ref['request_summary'],ref['actual_summary'],ref),'Only exact40 approved summary-role pair')
 require(proof['production_started_ns']<proof['video_mtime_ns']and proof['production_started_ns']<proof['fingerprint_mtime_ns'],'Original production freshness proof differs')
 result=dict(input_contract_passed=True,source_id='40',original_source_run_remains_failed=True,original_gate_exit_zero_inherited_from_pinned_control_flow=True,inherited_PCM_sha256=proof['internal_pcm_sha256'],new_private_PCM_recomputed=False,source_and_canonical=ref['canonical_video_sha256'],formal_completion_or_final_media_pass_claimed=False)
 if inspect_media:
  p=json.loads(command(['ffprobe','-v','error','-show_streams','-of','json',str(movie)]));v=next(x for x in p['streams']if x['codec_type']=='video');require((v['width'],v['height'],v['avg_frame_rate'])==(3840,2160,'30/1'),'Original actual4K/30fps differs');audio=actual_aac(movie);require(audio['aac_adts_sha256']==ref['expected_current_AAC_ADTS_sha256']and audio['packet_count']==ref['expected_packet_count'],'Actual whole current AAC/packet count differs')
  if accepted_video is not None:require(digest(accepted_video)==s['accepted_source']['sha256']and actual_aac(accepted_video)==audio,'Actual inherited current/accepted whole AAC codec/side-data/absolute timing differs')
  if 'expected_absolute_packet_projection_sha256'in ref:require(audio['packet_projection_sha256']==ref['expected_absolute_packet_projection_sha256'],'Actual original absolute packet projection differs')
  result['actual_audio']={k:v for k,v in audio.items()if k!='projection'}
 return result


def actual_aac(path):
    """Hash copied ADTS plus exact rational timestamp/payload/priming projection. Never rebase PTS."""
    raw = json.loads(command(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_streams', '-show_packets', '-show_data_hash', 'sha256', '-of', 'json', str(path)]))
    require(len(raw.get('streams', [])) == 1, f'No unique actual audio stream: {path}')
    stream = raw['streams'][0]; require(stream['codec_name'] == 'aac', f'Expected copied AAC: {path}')
    timebase = Fraction(stream['time_base']); packets = []
    for pkt in raw['packets']:
        timing = []
        for key in ('pts', 'dts', 'duration'):
            require(key in pkt, f'Cannot prove exact packet {key}: {path}')
            value = int(pkt[key]) * timebase
            timing.append([value.numerator, value.denominator])
        side = [{k: s[k] for k in sorted(s) if k != 'side_data_size'} for s in pkt.get('side_data_list', [])]
        require(pkt.get('data_hash'), f'No actual packet payload hash: {path}')
        packets.append({'timing_rationals': timing, 'size': int(pkt['size']), 'payload_sha256': pkt['data_hash'], 'side_data': side})
    codec = {k: stream.get(k) for k in ('codec_name', 'profile', 'sample_rate', 'channels', 'channel_layout')}
    projection = {'codec': codec, 'packets': packets}
    encoded = json.dumps(projection, sort_keys=True, separators=(',', ':')).encode()
    with tempfile.TemporaryDirectory(prefix='actual-aac-') as td:
        adts = Path(td) / 'audio.aac'
        command(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-vn', '-c:a', 'copy', '-f', 'adts', str(adts)])
        return {'aac_adts_sha256': digest(adts), 'packet_projection_sha256': hashlib.sha256(encoded).hexdigest(),
                'packet_count': len(packets), 'projection': projection}
