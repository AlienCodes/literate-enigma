import sys,json
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
def cell_runs(c):
    out=[]
    for p in c.paragraphs:
        for r in p.runs:
            col=r.font.color.rgb if r.font.color and r.font.color.type else None
            out.append((r.text,bool(r.bold),str(col) if col else None))
    return out
def items(path):
    d=Document(path); res=[]
    for el in d.element.body.iterchildren():
        tag=el.tag.split('}')[1]
        if tag=='tbl':
            t=Table(el,d); rows=t.rows
            res.append(('T',[[cell_runs(c) for c in r.cells] for r in rows]))
        elif tag=='p':
            p=Paragraph(el,d); res.append(('P',p.text))
    return res
if __name__=='__main__':
    for k,v in items(sys.argv[1]):
        if k=='P': print('P|',v)
        else:
            en=[''.join(t for t,_,_ in c) for c in v[0]]; zh=[''.join(t for t,_,_ in c) for c in v[1]] if len(v)>1 else []
            print('T|',' ‖ '.join(f'{a} => {b}' for a,b in zip(en,zh)), '' if len(v)==2 else f'[rows={len(v)}]')
