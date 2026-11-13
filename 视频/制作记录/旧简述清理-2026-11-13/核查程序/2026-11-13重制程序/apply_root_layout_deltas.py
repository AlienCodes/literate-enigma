"""Apply reviewed source-data changes only; no producer/checker modifications."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PAY = BASE / 'payload'
def module(name, filename):
    spec=importlib.util.spec_from_file_location(name,BASE/filename)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result
pre=module('data_preflight','generator_text_preflight.py')
summ=module('apply_reviewed_summary','apply_summary_revisions.py')
before={n:json.loads((PAY/f'视频/脚本/{n}.json').read_text()) for n in ['01','13','43','44']}
changes=copy.deepcopy(before)
bracket=json.loads((BASE/'preflight-note01-bracket-overlay.json').read_text())
note=changes['01']['sentences'][13]['chunks'][1]
assert note['note'] in [bracket['before'],bracket['after']]
note['note']=bracket['after']

c=changes['13']['sentences'][16]['chunks'][0]
for key in ['zh']:
    assert '长觉，就能' in c[key] or '长觉，\n就能' in c[key]
    c[key]=c[key].replace('长觉，就能','长觉，\n就能')
c['align'][0][1]=c['align'][0][1].replace('长觉，就能','长觉，\n就能')
assert c['zh']==''.join(p[1] for p in c['align'])
changes['43'].setdefault('字号上限',{})['S21']=99
c=changes['44']['sentences'][3]['chunks'][0]
if c['align'][0][0]=='**Norway** and **Finland**':
    assert c['align'][0][1]=='**挪威**(Norway)和**芬兰**(Finland)'
    c['align'][:1]=[['**Norway**','**挪威**(Norway)'],['and','和'],['**Finland**','**芬兰**(Finland)']]
assert c['en']==' '.join(p[0] for p in c['align'] if p[0]!='\n')
assert c['zh']==''.join(p[1] for p in c['align'])
report=[]
for n,d in changes.items():
    gen,issues=pre.pure_generator(d);assert not issues,(n,issues)
    diffs=pre.differences(before[n],d)
    (BASE/f'root-layout-before-{n}.json').write_text(json.dumps(before[n],ensure_ascii=False,indent=1)+'\n')
    (PAY/f'视频/脚本/{n}.json').write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n')
    (PAY/f'视频/工具/初稿生成/gen{n}.py').write_text(gen)
    # Preserve Markdown wording; mirror the explicit Chinese visual newline.
    if n=='13':
        md=next((PAY/'新版定稿').glob('13-*.md'))
        text=md.read_text();assert '长觉，就能' in text or '长觉，\n就能' in text
        md.write_text(text.replace('长觉，就能','长觉，\n就能'))
    record=PAY/f'视频/制作记录/{n}_待改清单.md'
    text=record.read_text()
    marker='## 2026-11-13 原版排版核验后的最小数据修正'
    reasons={'01':'仅在既有例子外加全角括号，例子文字原样，满足既有注释格式。',
             '13':'仅将“长觉，就能”换行为“长觉，\\n就能”，保留中文全部字符及英文原文，避免少年被拆成孤字；不缩小字号。',
             '43':'S21 字号上限99是1080与4K两档不把末词him.孤立的最大共同整数值；不改英文或中文。',
             '44':'将已有Norway/挪威、and/和、Finland/芬兰拆为独立对齐格，保证两个国家中文各在其英文下方；显示文字及音轨原样。'}
    if marker not in text:
        record.write_text(text.rstrip()+'\n\n'+marker+'\n\n'+reasons[n]+'\n')
    report.append({'id':n,'source_changes':diffs,'data_only':True,'actual_video_generated':False})
(BASE/'root-layout-data-deltas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

# Add priority prose to the independently reviewed summary composition, retaining
# immutable writer/crossreview files and the previous exact candidate in history.
approved={r['id']:r for r in json.loads((BASE/'summary-approved-70.json').read_text())}
adjustpath=BASE/'summary-root-adjustments.json'
adjustments=json.loads(adjustpath.read_text())
for n in ['01','50']:
    previous=approved[n]['after']
    after=(previous.replace('不能直接代表真实水平','未必代表真实水平') if n=='01'
           else json.loads((BASE/'summary-revision-50-priority.json').read_text())['after'])
    if previous==after:
        continue
    reason=('Keep the same cautious meaning and remove the final isolated Chinese character without reducing font size.' if n=='01'
            else 'User requested a detailed, plain explanation of what detection, association, the spoonful estimate, and limited evidence do and do not establish; reviewed against the complete source.')
    adjustments.append({'id':n,'reviewed_after_sha256':hashlib.sha256(previous.encode()).hexdigest(),
                        'reviewed_after':previous,'after':after,'reason':reason})
adjustpath.write_text(json.dumps(adjustments,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_articles':list(changes),'summary_composition_updated':['01','50'],'no_actual_video_pass_claimed':True}))
