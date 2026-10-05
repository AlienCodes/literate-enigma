import sys,os
VID='/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/video'
sys.path.insert(0,VID); sys.path.insert(0,VID+'/logo/D_wordmark'); os.chdir(VID)
from PIL import Image,ImageDraw,ImageFont
import render as R, title_logo as T
BOLT2=[(38,0),(80,0),(66,38),(86,38),(30,100),(44,54),(18,54)]
def lock(fontsel='zc',stroke=0.0,bolt='feather',sub_sz=13,sub_w=800,size=58,SS=4,u=1):
    k=u*SS
    if fontsel=='zc': zf=ImageFont.truetype(T.LOGO_FONT,int(size*k))
    else: zf=R.ZH(int(size*k),900)
    sw=int(round(stroke*size*k))
    track=int(3*k)+sw
    cw=[zf.getlength(c) for c in T.BRAND]; tw=int(sum(cw)+track*3+2*sw)
    bb=zf.getbbox(T.BRAND,stroke_width=sw); th=bb[3]-bb[1]
    sf=R.EN(int(sub_sz*k),sub_w); sub='PUNK ENGLISH'; sbb=sf.getbbox(sub); sh=sbb[3]-sbb[1]
    sg=int(10*k); ht=th+sg+sh; ic=ht; gap=int(16*k); pad=int(20*k)
    im=Image.new('RGBA',(ic+gap+tw+2*pad,ht+2*pad),(0,0,0,0)); d=ImageDraw.Draw(im); ox=oy=pad
    m=Image.new('L',(ic,ic),0); ImageDraw.Draw(m).rounded_rectangle([0,0,ic-1,ic-1],radius=int(ic*0.26),fill=255)
    im.paste(T._diag_grad(ic,ic,T.YEL,T.ORA),(ox,oy),m)
    if bolt=='feather':
        bs=ic*0.74; pts=[(ox+(ic-bs)/2+px/24*bs,oy+(ic-bs)/2+py/24*bs) for px,py in T._BOLT]
    else:
        bs=ic*0.66; pts=[(ox+(ic-bs*0.68)/2+(px-18)/100*bs,oy+(ic-bs)/2+py/100*bs) for px,py in BOLT2]
    d.polygon(pts,fill=T.INK+(255,))
    x=ox+ic+gap+sw
    for c,w in zip(T.BRAND,cw):
        d.text((x,oy-bb[1]),c,font=zf,fill=T.WHITE+(255,),stroke_width=sw,stroke_fill=T.WHITE+(255,)); x+=w+track
    lw=sum(sf.getlength(c) for c in sub); st=(tw-lw)/11; x=ox+ic+gap; sy=oy+th+sg-sbb[1]
    for c in sub: d.text((x,sy),c,font=sf,fill=T.TEAL+(255,)); x+=sf.getlength(c)+st
    return im.resize((im.width//SS,im.height//SS),Image.LANCZOS)
bg=T.base(1).crop((560,240,1360,840))
y=10
for kw in [dict(),dict(stroke=0.03,bolt='chunky',sub_sz=14,sub_w=700),dict(stroke=0.045,bolt='chunky',sub_sz=15,sub_w=700),dict(fontsel='noto',bolt='chunky',sub_sz=15,sub_w=700,size=54)]:
    L=lock(**kw); bg.paste(L,((bg.width-L.width)//2,y),L); y+=L.height+10
bg=bg.resize((bg.width*2,bg.height*2),Image.LANCZOS); bg.save(VID+'/logo/D_wordmark/work/explore2.png')
