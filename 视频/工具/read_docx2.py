import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
def uniq(row):
    seen=[];out=[]
    for c in row.cells:
        if c._tc in seen: continue
        seen.append(c._tc); out.append(c)
    return out
def runs(c):
    return [(r.text.replace('\u2005',''),bool(r.bold)) for p in c.paragraphs for r in p.runs]
def segs(path):
    d=Document(path); res=[]
    for el in d.element.body.iterchildren():
        tag=el.tag.split('}')[1]
        if tag=='tbl':
            rows=Table(el,d).rows
            for i in range(0,len(rows)-1,2):
                E=uniq(rows[i]); Z=uniq(rows[i+1])
                res.append(('T',[(''.join(t for t,_ in runs(e)),runs(z)) for e,z in zip(E,Z)]))
        elif tag=='p':
            t=Paragraph(el,d).text
            if t.strip(): res.append(('P',t))
    return res
if __name__=='__main__':
    for k,v in segs(sys.argv[1]):
        print(k+'|', v if k=='P' else ' ‖ '.join(f"{e} => {''.join(t for t,_ in z)}" for e,z in v))
