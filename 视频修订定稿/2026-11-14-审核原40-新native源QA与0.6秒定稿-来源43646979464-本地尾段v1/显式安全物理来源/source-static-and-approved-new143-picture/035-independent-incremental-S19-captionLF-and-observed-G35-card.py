from pathlib import Path
import copy
HEADER=Path('/dev/shm/article40-user139140-draft-20261114/independent-render40-static139140142.py').read_text().split('target=[',1)[0]
exec(HEADER,globals())
import sys
sys.path.insert(0,'/dev/shm/native-inline-engine-reviewed60-v20-077-layout');import delivery as D
before=H/'before/视频/脚本/40.json';after=H/'candidate-payload/视频/脚本/40.json';variant=H/'independent-thin-validation/40-actual-original-mechanical-result-v2.json';final_data=json.loads(after.read_text());assert sha(after)=='66f6b6206d38e4cbcb5fd92faf9e3c5118b8749962eb52e68121204070ddb7ec';virtual=copy.deepcopy(final_data);virtual['sentences'][18]['chunks'][0]['note']=virtual['sentences'][18]['chunks'][0]['note'].replace('后来，\n黄色','后来，黄色');assert hashlib.sha256((json.dumps(virtual,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()=='44d850a163dd06814282c9728b62aa79d069c912b3f91bdfab69945fc9392ba7'
oldreport=json.loads((H/'actual-static139140142-independent-report.json').read_text());variant_data=json.loads(variant.read_text());assert D.changed_json_paths(final_data,variant_data)==['/sentences/18/chunks/0/note'];assert D.visible_tokens(final_data['sentences'][18]['chunks'][0]['note'],True)==D.visible_tokens(variant_data['sentences'][18]['chunks'][0]['note'],True)
result={'kind':'source40-caption-oneLF-incremental-actual-static-and-original-G35-card-observation','source_id':'40','book_order':'46','source_sha256':sha(after),'GEN_sha256':sha(H/'candidate-payload/视频/工具/初稿生成/gen40.py'),'MD_sha256':sha(H/'candidate-payload/新版定稿/40-the-glue-that-failed.md'),'previous_full_static_report':{'path':str(H/'actual-static139140142-independent-report.json'),'sha256':sha(H/'actual-static139140142-independent-report.json')},'root_caption_oneLF_only_since_previous_source':True,'other18_sentence_data_deep_identical_to_previous_source':True,'actual_original_G35_variant':{'path':str(variant),'sha256':sha(variant),'applied_to_request':False,'difference_paths':D.changed_json_paths(final_data,variant_data)},'no_audio_source_native_or_PDF_mutation':True,'resolutions':[]}
for scale in [1,2]:
 os.environ['VIDEO_S']=str(scale);R=load('source40_incremental_actual_renderer_'+str(scale),renderer);R.F=str(OLD/'fonts')+'/'
 for k in theme_node.keywords:setattr(R,k.arg,ast.literal_eval(k.value))
 for name,default in [('EN',600),('ZH',500)]:
  original=getattr(R,name)
  def wrap(original,default):
   @functools.lru_cache(maxsize=256)
   def cached(size,weight=None):
    f=original(size,default if weight is None else weight);f.getlength=functools.lru_cache(maxsize=1024)(f.getlength);return f
   return cached
  setattr(R,name,wrap(original,default))
 folder=H/('incremental-captionLF-'+('1080'if scale==1 else'4K'));folder.mkdir(exist_ok=True);row={'scale':scale,'width':R.W,'height':R.H,'variants':[]}
 for label,path in [('before',before),('after-root-oneLF',after),('observed-original-G35-only',variant)]:
  d=json.loads(path.read_text());summary=R.拆出简述页(d);R.apply_script(d);colors=R.分色(d);R.unify_colors(colors,d['sentences']);s=d['sentences'][18];chunks=[[tuple(x)for x in c['align']]for c in s['chunks']];notes=[c.get('note')for c in s['chunks']];cs=R.sent_colors(colors,s);natural=R.max_es(chunks,cs,notes);cap=d.get('字号上限',{}).get('S19');size=min(natural,100*scale,float(cap)*scale if cap is not None else 100*scale);size=int(size)if size==int(size)else size;_,height,width,_=R._measure(chunks,cs,notes,size,R._grouping(chunks,cs));orphan=R.orphan_lines(chunks,cs,notes,size);assert width<=R.MAXW2 and height<=R.MAXH2 and not orphan
  p=folder/(label+'-actual-S19-body-tail.png');R.ES_FIXED=size;R.frame_interlinear(chunks,cs,'',1,str(p),active=0,notes=notes);tail={'path':str(p),'PNG_sha256':sha(p),'RGB_sha256':rgb(p),'font_px':size,'width_px':width,'height_px':height,'within_bounds':True,'orphans':orphan}
  ss,lines,first=R.简述排(summary);assert len(first)==5;p=folder/(label+'-summary.png');R.frame_简述(summary,1,str(p));card={'path':str(p),'PNG_sha256':sha(p),'RGB_sha256':rgb(p),'font_px':ss,'point_count':len(first),'raw_text_sha256':hashlib.sha256(summary.encode()).hexdigest(),'canonical_text_sha256':hashlib.sha256(summary.replace('\n','').replace('▹','').encode()).hexdigest(),'rows':[''.join(ch for ch,_ in l)for l in lines]};row['variants'].append({'label':label,'tail':tail,'summary':card})
 a,b,c=row['variants'];assert all(a['summary'][k]==b['summary'][k]for k in ['PNG_sha256','RGB_sha256','font_px','raw_text_sha256','canonical_text_sha256','rows']);assert a['summary']['canonical_text_sha256']==c['summary']['canonical_text_sha256'];row.update(request_summary_raw_text_font_rows_and_pixels_exact=True,observed_G35_summary_RGB_equals_approved_request=c['summary']['RGB_sha256']==a['summary']['RGB_sha256'],observed_G35_summary_font_equals_request=c['summary']['font_px']==a['summary']['font_px'])
 if scale==2:assert b['summary']['RGB_sha256']==approved['summary_rgb_sha256'] and b['summary']['font_px']==approved['summary_font_4k_px']
 result['resolutions'].append(row)
result.update(passed=True,all_new_S19_actual_static_within_bounds_no_orphans=True,original_request_summary_preserved=True,observed_G35_variant_not_applied_to_request=True);out=H/'independent-incremental-captionLF-and-observed-G35-card-report.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(out),'sha256':sha(out),'G35observations':[{'scale':x['scale'],'RGB_same':x['observed_G35_summary_RGB_equals_approved_request'],'request_font':x['variants'][1]['summary']['font_px'],'G35_font':x['variants'][2]['summary']['font_px']}for x in result['resolutions']]},ensure_ascii=False))
