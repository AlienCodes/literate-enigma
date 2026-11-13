import json,hashlib,re
from pathlib import Path
from booklet_utils import ROOT,validate_article
from publication_payloads import payload

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cell(t):return t.replace('|','\\|').replace('\n',' ')

def build():
    order=json.loads(Path('/workspace/work/order70-recommended.json').read_text())['order']
    assert len(order)==len(set(order))==70
    chapters={}
    for n in order:
        p=payload(n);j=p['previous']
        assert j['status']=='complete' and j['pdf_sha256']==p['pdf_sha256'] and j['content_sha256']==p['content_sha256'],n
        assert j['user_preview_matches_download'] and len(j['previews'])==p['pages'],n
        chapters[n]={**p,'url':j['url']}
    volumes=[]
    for v in range(1,8):
        q=json.loads((ROOT/f'volumes/{v:02}/qc.json').read_text())
        j=json.loads((ROOT/f'publication/volume-{v:02}.json').read_text())
        review=json.loads((ROOT/f'reviews/volumes-{v:02}.json').read_text())
        assert q['passed'] and sha(q['pdf'])==q['pdf_sha256']==j['pdf_sha256'],v
        assert review.get('passed') and review.get('pdf_sha256')==q['pdf_sha256'],v
        assert j['pdf_attachment']['file_access_confirmed'] and j['pdf_attachment']['sha256']==q['pdf_sha256'],v
        assert [a['id'] for a in q['articles']]==order[(v-1)*10:v*10],v
        assert all(a['pdf_sha256']==chapters[a['id']]['pdf_sha256'] for a in q['articles']),v
        volumes.append({**q,'attachment':j['pdf_attachment']['markdown']})
    blocks=['70篇小册子均采用已确认的插图阅读版式。每篇包含专属插图、纯净英文原文、完整中文译文、22项核心词汇、其余文中词汇、4道回想练习及五点文章主线。',
    '下载请点击PDF附件。每篇页面展示对应最终PDF的逐页预览；页面菜单中的“导出”会另外排版整个网页。',
    '# 七册合订PDF',
    '按推荐阅读顺序编排，每册10篇，保留原篇号。合订PDF内的目录可以点击跳转到对应文章。']
    for v in volumes:
        i=v['volume'];blocks.append(f'## 第{i}册 · 阅读顺序{(i-1)*10+1:02d}–{i*10:02d} · {v["pages"]}页')
        blocks.append(v['attachment'])
    blocks.extend(['# 70篇逐篇预览与下载','点击篇目查看完整逐页预览，并下载该篇独立PDF。下列顺序为编辑推荐，原篇号不变。'])
    for v in range(1,8):
        blocks.append(f'## 第{v}册 · 阅读顺序{(v-1)*10+1:02d}–{v*10:02d}')
        rows=['| 顺序 | 原篇号 | 篇目 | 页数 |','| ---: | --- | --- | ---: |']
        for pos,n in enumerate(order[(v-1)*10:v*10],(v-1)*10+1):
            p=chapters[n];rows.append(f'| {pos:02d} | 第{n}篇 | [{cell(p["title_zh"])}]({p["url"]}) | {p["pages"]}页 |')
        blocks.append('\n'.join(rows))
    blocks.extend(['# 原文资料','英文原文依据[仓库固定版本](https://github.com/AlienCodes/literate-enigma/tree/9374187e740fcefef39e42259a2f057ae504ebc9/视频/脚本)，保留原篇号。中文阅读说明会澄清原文中需要辨明的史实或概念。',
    '第36篇授勋日期的阅读说明依据[白宫2010年11月17日典礼记录](https://obamawhitehouse.archives.gov/the-press-office/2010/11/17/remarks-president-presenting-national-medals-science-and-national-medals/)，区分2009年度奖项与2010年实际授勋。'])
    out={'title':'70篇插图英语阅读小册','blocks':blocks,'articles':70,'total_individual_pages':sum(p['pages'] for p in chapters.values()),'volumes':7,'total_volume_pages':sum(v['pages'] for v in volumes),'unique_article_urls':len({p['url'] for p in chapters.values()})}
    assert out['unique_article_urls']==70
    (ROOT/'publication/catalog-final-payload.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='blocks'},ensure_ascii=False))

if __name__=='__main__':build()
