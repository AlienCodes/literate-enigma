"""Record actual word/POS/translation review through the unchanged original entrypoint."""
import datetime,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).parent;B=H.parent;M=B/'article14-user-review-20261114/gen-text-validation/mirror';W=M/'_text-preflight-work26';C=H/'candidate-payload';rel=Path('视频/制作记录/逐句确认/26.json');p=M/rel
sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
candidate=json.loads((C/'视频/脚本/26.json').read_text());actual=json.loads((W/'scripts/26.json').read_text());assert candidate==actual
base=B/'payload'/rel;assert base.exists()and sha(base)==sha(p)
q=H/'before'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base,q);before=json.loads(p.read_text())
conclusions={
 'S4':'T1没加信息：只按用户点名给gestures及手势加重点，原英中文字符及信息保留。T3词性：secluded为形容词与世隔绝的，homemade为形容词自制的，repertoire为名词一整套/全部，gestures为gesture的复数名词手势，siblings为复数名词兄弟姐妹。T6不生硬：of为普通结构，手势沿用原译，不额外添词。T7通顺：描述与父母和兄弟姐妹共用自创的一套手势，原句完整保留。T8看得懂：手势与聋人家庭交流语境清楚，原说明保留。T21贴合语境：gestures指交流用手势，不是抽象姿态。T2/T4/T5/T9：词义方向不变，gestures与手势在同一对齐格内单独标粗，不横跨其他词。T13整句读通：本句说明此前聋人生活隔绝，只在家庭中分享自创手势。',
 'S16':'T1没加信息：只按用户点名给Linguists及语言学家加重点，复数大小写与原语序均保留。T3词性：Linguists为linguist的复数名词，指语言学家；infancy与maturity为名词，原译婴儿期和成熟期保留。T6不生硬：沿用语言成长的原比喻和原中文，不增修辞。T7通顺：语言学家难得有机会观察语言从初生到成熟，原句信息完整。T8看得懂：语言学家身份和语言成长过程前文已有交代，原结构说明保留。T21贴合语境：Linguists指研究语言的学者，不是泛指会多种语言的人。T2/T4/T5/T9：词义方向不变，完整Linguists与完整语言学家一格对应，不拆、不跨其他词。T13整句读通：本句概括语言学家亲眼观察这门语言成长的难得机会。'
}
env={**os.environ,'XG_P':str(M),'XG_TOOLS':str(M/'视频/工具'),'XG_WORK':str(W),'PYTHONDONTWRITEBYTECODE':'1'};logs=[]
for which,why in conclusions.items():
 result=subprocess.run([sys.executable,str(M/'视频/工具/逐句确认.py'),'26',which,why],cwd=W,env=env,capture_output=True,text=True);logs.append({'sentence':which,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'conclusion':why});assert result.returncode==0
after=json.loads(p.read_text());assert set(before)==set(after)
for k in before:
 if k not in conclusions:assert before[k]==after[k]
q=C/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
report={'article':'26','kind':'two-actual-text-only-reviews-recorded-by-original-sentence-confirmation-program','only_updated_sentence_keys':['S4','S16'],'source_sha256':sha(C/'视频/脚本/26.json'),'original_program_sha256':sha(M/'视频/工具/逐句确认.py'),'record_before_sha256':sha(H/'before'/rel),'record_after_sha256':sha(q),'unchanged_other_sentence_confirmations':True,'no_audio_confirmation_or_core_change':True,'official_entrypoint_runs':logs,'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};(H/'actual-text-two-sentence-confirmations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'new_record_sha256':sha(q)},ensure_ascii=False))
