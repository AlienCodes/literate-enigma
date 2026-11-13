from group_01_12 import *
from PIL import Image

fixes={
 '02':{'restraint':'restraint at four was glorified'},
 '04':{'innate':'an innate flair for spatial tasks','spatial':'spatial tasks','expansion':'an expansion of rear grey matter'},
 '05':{'confessed':'confessed to the second killing','investigation':'the perplexing investigation','geneticist':'a geneticist','molecular':'molecular markers','varied':'layout varied considerably'},
 '06':{'gesture':'Every gesture and motion','subconscious':'motion was subconscious'},
 '07':{'reconstructed':'reconstructed that route','neurons':'neurons lie in the limbs'},
 '08':{'convinced':'convinced since 1849','crucial':'The crucial evidence','inquiry':'a government inquiry','sceptical':'the sceptical curate Henry Whitehead','refute':'set out to refute Snow'},
 '09':{'veterans':'First World War veterans','delegation':'a delegation of ex-soldiers','detachment':'not a battalion but a detachment','ammunition':'10,000 rounds of ammunition.','ambush':'approached an ambush','withdrawal':'an embarrassing withdrawal','reinforcements':'pleas for reinforcements','intervention':'intervention gave way to a bounty','bounty':'a bounty sanctioned by the government.','compensation':'gave farmers compensation'},
 '10':{'discreetly':'discreetly plucked from its wall.','burglary':'involvement in the burglary.','apprehended':'Peruggia was apprehended','tribunal':'a tribunal imposed a penalty','heist':'the heist elevated one esteemed gem'},
 '11':{'bizarre':'found the unexpected placement bizarre','invincible':'an invincible entity'},
}
reports=[];images=[]
for no in ASSIGNED:
 path=ROOT/'content/articles'/f'{no}.json';d=json.loads(path.read_text())
 for v in d['vocabulary']:
  if v['source_term'] in fixes.get(no,{}):
   assert v['core'];v['context_phrase']=fixes[no][v['source_term']]
 from booklet_utils import validate_article
 result=validate_article(d)
 assert all('{{' not in t and '}}' not in t for t in d['english_paragraphs'])
 assert all('{{' not in t and '}}' not in t for t in d['chinese_paragraphs'])
 atomic_json(path,d)
 meta=json.loads((ROOT/'illustrations'/f'{no}.json').read_text())
 png=ROOT/'illustrations'/f'{no}.png'
 sha=hashlib.sha256(png.read_bytes()).hexdigest();assert sha==meta['sha256']
 assert meta['review_passed'] is True and meta['prompt']==d['illustration_prompt']
 assert Path(meta['original_generation_path']).read_bytes()==png.read_bytes()
 with Image.open(png) as im:
  im.verify()
 with Image.open(png) as im:
  wh=list(im.size);assert wh[0]*2==wh[1]*3
 assert sha not in images;images.append(sha)
 result.update({'content_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'illustration_sha256':sha,'illustration_pixels':wh,'original_generation_retained':True,'visual_review_passed':True})
 reports.append(result)
atomic_json(ROOT/'progress/group_01_12_selfcheck.json',{'group':'01_12','scope':'02–12; approved 01 untouched','source_commit':SOURCE_COMMIT if 'SOURCE_COMMIT' in globals() else '9374187e740fcefef39e42259a2f057ae504ebc9','articles':reports,'unique_illustrations':len(set(images)),'unresolved_blockers':[],'review_notes':['02：统计不显著不等于证明完全没有关联。','03：自行感染得到胃炎，未声称患上溃疡。','04：保留样本小且全男性与表观记忆权衡限定。','05：少年只认第二案，筛查漏网后靠举报找到真凶。','06：未发现欺骗不等于证实马能算术。','07：出逃路线为依黏液重建，宣言和法律不等于主观体验证据。','08：每日新发致死病例、死亡人数与未患重症分别处理。','09：1934年为申领赏金笔数，不冒充独立确认击杀数。','10：爱国是当事人自述，盗窃推动名气是带限定的历史学家判断。','11：两次万分之一都是选出着法概率估计，并非胜率。','12：庆祝的是对手改换配方，盲测未测品牌依恋。']})
progress()
print(json.dumps({'articles':len(reports),'target_words':sum(x['vocabulary'] for x in reports),'core_words':22*len(reports),'questions':4*len(reports),'unique_illustrations':len(set(images)),'valid':True},ensure_ascii=False))
