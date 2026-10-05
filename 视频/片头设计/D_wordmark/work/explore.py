import sys,os,math
VID='/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/video'
sys.path.insert(0,VID); os.chdir(VID)
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
import render as R
HERE=VID+'/logo/D_wordmark/'
ZC=HERE+'ZCOOLQingKeHuangYou-Regular.ttf'
YEL,ORA,TEAL,WHITE,DARK=(255,214,64),(255,120,80),(94,234,212),(248,250,246),(14,36,29)
def lin_grad(w,h,c1,c2,ang=35):
    g=Image.new('RGB',(w,h)); px=g.load()
    a=math.radians(ang); dx,dy=math.cos(a),math.sin(a)
    L=abs(w*dx)+abs(h*dy)
    for y in range(h):
        for x in range(w):
            t=((x*dx+y*dy)-min(0,w*dx)-min(0,h*dy))/L
            px[x,y]=tuple(int(p+(q-p)*t) for p,q in zip(c1,c2))
    return g
BOLT=[(13,2),(3,14),(12,14),(11,22),(21,10),(12,10)]
def bolt_pts(x,y,s): return [(x+px/24*s,y+py/24*s) for px,py in BOLT]
def star_pts(cx,cy,ro,ri,n=12,rot=0):
    pts=[]
    for i in range(2*n):
        r=ro if i%2==0 else ri; a=math.pi*i/n+rot
        pts.append((cx+r*math.sin(a),cy-r*math.cos(a)))
    return pts
def lockup(style,unit=1,SS=4):
    k=unit*SS
    zsz=int(68*k); zf=ImageFont.truetype(ZC,zsz)
    track=int(4*k)
    txt='朋克英语'
    cw=[zf.getlength(c) for c in txt]
    tw=sum(cw)+track*3
    bb=zf.getbbox('朋'); th=bb[3]-bb[1]
    ic=int(th*1.0) if style!='stack' else 0
    sub='PUNK ENGLISH'; sf=R.EN(int(15*k),800); st=int(5.2*k)
    sw=sum(sf.getlength(c) for c in sub)+st*(len(sub)-1)
    sbb=sf.getbbox('PUNK')
    gap=int(20*k)
    if style in('sq','star','bolt'):
        Wd=ic+gap+int(tw); Ht=th
    elif style=='sq2':  # icon + stacked text
        sub_h=sbb[3]-sbb[1]; ht=th+int(12*k)+sub_h
        ic=ht; Wd=ic+gap+int(max(tw,sw)); Ht=ht
    pad=int(30*k)
    im=Image.new('RGBA',(Wd+2*pad,Ht+2*pad),(0,0,0,0)); d=ImageDraw.Draw(im)
    ox,oy=pad,pad
    # icon
    if style in('sq','sq2'):
        m=Image.new('L',(ic,ic),0); ImageDraw.Draw(m).rounded_rectangle([0,0,ic-1,ic-1],radius=int(ic*0.24),fill=255)
        g=lin_grad(ic//4+1,ic//4+1,YEL,ORA,45).resize((ic,ic),Image.BILINEAR)
        im.paste(g,(ox,oy),m)
        bs=ic*0.78; d.polygon(bolt_pts(ox+(ic-bs)/2+ic*0.01,oy+(ic-bs)/2,bs),fill=DARK+(255,))
    elif style=='star':
        cx,cy=ox+ic/2,oy+ic/2
        m=Image.new('L',im.size,0); ImageDraw.Draw(m).polygon(star_pts(cx,cy,ic*0.56,ic*0.44,14),fill=255)
        g=lin_grad(im.size[0]//8+1,im.size[1]//8+1,YEL,ORA,45).resize(im.size,Image.BILINEAR)
        im.paste(g,(0,0),m)
        bs=ic*0.62; d.polygon(bolt_pts(cx-bs/2,cy-bs/2,bs),fill=DARK+(255,))
    elif style=='bolt':
        m=Image.new('L',im.size,0); ImageDraw.Draw(m).polygon(bolt_pts(ox-ic*0.1,oy-ic*0.08,ic*1.16),fill=255)
        g=lin_grad(im.size[0]//8+1,im.size[1]//8+1,YEL,ORA,60).resize(im.size,Image.BILINEAR)
        im.paste(g,(0,0),m); ic=int(ic*0.8)
    # text
    x=ox+ic+gap; ty=oy-bb[1]
    for c,w in zip(txt,cw):
        d.text((x,ty),c,font=zf,fill=WHITE+(255,)); x+=w+track
    if style=='sq2':
        x=ox+ic+gap; sy=oy+th+int(12*k)-sbb[1]
        for c in sub:
            d.text((x,sy),c,font=sf,fill=TEAL+(255,)); x+=sf.getlength(c)+st
    return im.resize((im.width//SS,im.height//SS),Image.LANCZOS)
if __name__=='__main__':
    import title2 as T
    bg=T.base(1).crop((360,200,1560,1000))
    y=20
    for st in ['sq','sq2','star','bolt']:
        L=lockup(st); bg.paste(L,((bg.width-L.width)//2,y),L); y+=L.height+20
    bg.save(HERE+'work/explore1.png')
