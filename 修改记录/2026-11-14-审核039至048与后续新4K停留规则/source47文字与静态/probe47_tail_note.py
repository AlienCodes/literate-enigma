exec((__import__('pathlib').Path(__file__).parent/'probe47_note_options.py').read_text().split('d=json.loads')[0])
d=json.loads((B/'payload/视频/脚本/47.json').read_text());R.拆出简述页(d);R.apply_script(d);colors=R.分色(d);R.unify_colors(colors,d['sentences']);s=d['sentences'][12];text='（“狼的影子”比喻狼对生态系统的影响。作者认为，流行故事可能夸大了狼的作用；柳树恢复、河岸变稳等变化还受其他因素影响，现有研究尚无定论，真实情况比故事复杂。）';results=[]
for k in [0,2,3,4,5]:
 ss=copy.deepcopy(s)
 if k:
  lines=R.折成(text,k,R.ZH(30,400),R.断点(text))
  if lines is None:continue
  ss['chunks'][1].pop('note');ss['chunks'][2]['note']='\n'.join(lines)
 chunks=[[tuple(p)for p in c['align']]for c in ss['chunks']];notes=[c.get('note')for c in ss['chunks']];cs=R.sent_colors(colors,ss);size=min(R.max_es(chunks,cs,notes),100);_,height,width,params=R._measure(chunks,cs,notes,size,R._grouping(chunks,cs));results.append({'rows':k,'notes':notes,'main_font_1080_px':size,'note_font_1080_px':int(int(size*R.ZR)*.9),'height':height,'width':width,'wide_notes':R.wide_notes(chunks,cs,notes,size),'orphans':R.orphan_lines(chunks,cs,notes,size)})
p=H/'actual-S13-accepted-note-linewrap-options.json';p.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results,ensure_ascii=False))
