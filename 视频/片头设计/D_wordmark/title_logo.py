# D_wordmark: drop-in replacement for title2.frame_title2 with the 「朋克英语」 brand lockup.
# - no article number anywhere (kicker + watermark removed); layout re-centred
# - brand lockup (gradient app-icon with lightning bolt + 朋克英语 wordmark + justified PUNK ENGLISH)
#   sits under the Chinese title badge, centred, clearly subordinate to the title.
# Must run with cwd = video dir (render.py loads fonts from relative 'fonts/').
import os,sys,math,random
_VID=os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
if _VID not in sys.path: sys.path.insert(0,_VID)
from PIL import Image,ImageDraw,ImageFilter,ImageChops,ImageFont
import render as R
S=R.S
W,H=1920*S,1080*S
HERE=os.path.dirname(os.path.abspath(__file__))
LOGO_FONT=os.path.join(HERE,'ZCOOLQingKeHuangYou-Regular.ttf')   # OFL 1.1, google/fonts ofl/zcoolqingkehuangyou
BRAND='朋克英语'
YEL,ORA,TEAL,WHITE,INK=(255,214,64),(255,120,80),(94,234,212),(248,250,246),(14,36,29)

def grad(w,h,c1,c2):
    g=Image.new('RGB',(w,h))
    for x in range(w):
        t=x/max(1,w-1); ImageDraw.Draw(g).line([(x,0),(x,h)],fill=tuple(int(a+(b-a)*t) for a,b in zip(c1,c2)))
    return g
def base(variant):
    im=Image.new('RGB',(W,H))
    top,bot=(10,30,24),(16,44,36)
    d=ImageDraw.Draw(im)
    for y in range(H): d.line([(0,y),(W,y)],fill=tuple(int(a+(b-a)*y/H) for a,b in zip(top,bot)))
    glow=Image.new('L',(W,H),0); ImageDraw.Draw(glow).ellipse([W/2-700*S,H/2-380*S,W/2+700*S,H/2+380*S],fill=90)
    glow=glow.filter(ImageFilter.GaussianBlur(160*S))
    col=(40,120,90) if variant!=2 else (120,90,20)
    im=Image.composite(Image.new('RGB',(W,H),col),im,glow)
    return im
def wrap(words,font,maxw):
    lines=[[]]
    for w in words:
        t=' '.join(x for x,_ in lines[-1]+[w])
        if lines[-1] and font.getlength(t)>maxw: lines.append([w])
        else: lines[-1].append(w)
    return lines

# ---------------------------------------------------------------- brand lockup
def _diag_grad(w,h,c1,c2):
    """small diagonal (top-left -> bottom-right) gradient, upscaled smoothly"""
    n=64; g=Image.new('RGB',(n,n)); px=g.load()
    for y in range(n):
        for x in range(n):
            t=(x+y)/(2*n-2); px[x,y]=tuple(int(a+(b-a)*t) for a,b in zip(c1,c2))
    return g.resize((max(1,w),max(1,h)),Image.BILINEAR)
# chunky lightning bolt, 100-unit box (flat top, hard step, sharp tip)
_BOLT=[(38,0),(80,0),(66,38),(86,38),(30,100),(44,54),(18,54)]
_BOLT_X=(18,86)
def check_brand_glyphs(path=LOGO_FONT,text=BRAND):
    """every brand char must exist in the cmap AND render differently from .notdef"""
    from fontTools.ttLib import TTFont
    cmap=TTFont(path,lazy=True).getBestCmap()
    f=ImageFont.truetype(path,64)
    def ink(c):
        m=Image.new('L',(96,96),0); ImageDraw.Draw(m).text((8,8),c,font=f,fill=255); return m
    nd=ink('\U000F0000')
    for c in text:
        assert ord(c) in cmap, f'{c} missing from cmap of {path}'
        assert ImageChops.difference(ink(c),nd).getbbox(), f'{c} renders as .notdef'
    return True
_LOCK={}
LAST_LOGO_BOX=None
def brand_lockup(u=S,SS=4,size=60,bold=0.018,glow=0.35,tilt=-6.0):
    """RGBA lockup at scale u (1 -> 1080p). Returns (img, (x0,y0,x1,y1) content box inside img)."""
    key=(u,SS,size,bold,glow,tilt)
    if key in _LOCK: return _LOCK[key]
    k=u*SS
    zf=ImageFont.truetype(LOGO_FONT,int(size*k))
    sw=int(round(bold*size*k))          # faux-bold: heavier, blockier wordmark
    track=int(3*k)+sw
    cw=[zf.getlength(c) for c in BRAND]; tw=int(sum(cw)+track*(len(BRAND)-1)+2*sw)
    bb=zf.getbbox(BRAND,stroke_width=sw); th=bb[3]-bb[1]
    sub='PUNK ENGLISH'; sf=R.EN(int(15*k),800)
    sbb=sf.getbbox(sub); sh=sbb[3]-sbb[1]
    sgap=int(10*k)
    ht=th+sgap+sh            # total lockup height
    ic=ht                    # icon is as tall as the two-line text block
    gap=int(16*k)
    Wd=ic+gap+tw
    pad=int(24*k)
    im=Image.new('RGBA',(Wd+2*pad,ht+2*pad),(0,0,0,0)); d=ImageDraw.Draw(im)
    ox,oy=pad,pad
    # icon: rounded square, yellow->orange (same ramp as the highlighted title words), ink bolt
    ic_im=Image.new('RGBA',(ic,ic),(0,0,0,0))
    m=Image.new('L',(ic,ic),0); ImageDraw.Draw(m).rounded_rectangle([0,0,ic-1,ic-1],radius=int(ic*0.26),fill=255)
    ic_im.paste(_diag_grad(ic,ic,YEL,ORA),(0,0),m)
    bs=ic*0.66; bw=(_BOLT_X[1]-_BOLT_X[0])/100*bs
    ImageDraw.Draw(ic_im).polygon([((ic-bw)/2+(px-_BOLT_X[0])/100*bs,(ic-bs)/2+py/100*bs) for px,py in _BOLT],fill=INK+(255,))
    if tilt: ic_im=ic_im.rotate(tilt,resample=Image.BICUBIC,expand=True)
    ix=ox+(ic-ic_im.width)//2; iy=oy+(ic-ic_im.height)//2
    if glow>0:
        gm=Image.new('L',im.size,0); gm.paste(ic_im.getchannel('A').point(lambda v:int(v*glow)),(ix,iy))
        gm=gm.filter(ImageFilter.GaussianBlur(10*k))
        gl=Image.new('RGBA',im.size,ORA+(0,)); gl.putalpha(gm); im=Image.alpha_composite(im,gl)
    im.alpha_composite(ic_im,(ix,iy)); d=ImageDraw.Draw(im)
    # wordmark
    x=ox+ic+gap+sw
    for c,w in zip(BRAND,cw):
        d.text((x,oy-bb[1]),c,font=zf,fill=WHITE+(255,),stroke_width=sw,stroke_fill=WHITE+(255,)); x+=w+track
    # PUNK ENGLISH justified to the wordmark width
    lw=sum(sf.getlength(c) for c in sub)
    st=(tw-lw)/(len(sub)-1); x=ox+ic+gap; sy=oy+th+sgap-sbb[1]
    for c in sub:
        d.text((x,sy),c,font=sf,fill=TEAL+(255,)); x+=sf.getlength(c)+st
    out=im.resize((im.width//SS,im.height//SS),Image.LANCZOS)
    box=(pad//SS,pad//SS,(pad+Wd)//SS,(pad+ht)//SS)
    _LOCK[key]=(out,box); return out,box

# ---------------------------------------------------------------- title page
def frame_title2(no,en,zh,hl,ghost,out,variant=1):
    # `no` is accepted for API compatibility but deliberately NOT displayed.
    im=base(variant); d=ImageDraw.Draw(im)
    AC1,AC2=(255,214,64),(255,120,80)
    words=[(w,('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168*S,60,-4):
        ef=R.EN(es,900); lines=wrap(words,ef,1680*S)
        if len(lines)<=3: break
    zf=R.ZH(int(es*0.57),900)
    lhE=int(es*1.08); ph=int(es*0.57*1.55)
    logo,lbox=brand_lockup(S); lh=lbox[3]-lbox[1]
    cap=ef.getbbox('H'); cap_top=cap[1]          # ink top of first title line
    g_badge=48*S; g_logo=64*S
    # visual stack: cap-top of line 1 .. bottom of lockup
    total=len(lines)*lhE-cap_top+g_badge+ph+g_logo+lh
    y=(H-total)/2-cap_top-6*S
    for ln in lines:
        lw=ef.getlength(' '.join(w for w,_ in ln)); x=(W-lw)/2
        for w,k in ln:
            ww=ef.getlength(w)
            if k=='h':
                m=Image.new('L',(W,H),0); ImageDraw.Draw(m).text((x,y),w,font=ef,fill=255)
                gl=m.filter(ImageFilter.GaussianBlur(18*S)).point(lambda v:int(v*0.7))
                im=Image.composite(Image.new('RGB',(W,H),AC2),im,gl)
                g=Image.new('RGB',(W,H)); g.paste(grad(int(ww)+2,int(es*1.3),AC1,AC2),(int(x),int(y)))
                im=Image.composite(g,im,m)
            elif k=='g':
                m=Image.new('L',(W,H),0); ImageDraw.Draw(m).text((x,y),w,font=ef,fill=255)
                gm=Image.new('L',(int(ww)+2,int(es*1.3)))
                gd=ImageDraw.Draw(gm)
                for i in range(gm.width): gd.line([(i,0),(i,gm.height)],fill=int(255-230*(i/gm.width)**1.3))
                fm=Image.new('L',(W,H),0); fm.paste(gm,(int(x),int(y)))
                im=Image.composite(Image.new('RGB',(W,H),(248,250,246)),im,ImageChops.multiply(m,fm))
                dots=Image.new('L',(W,H),0); dd=ImageDraw.Draw(dots)
                rnd=random.Random(3)
                for _ in range(260*S):
                    px=x+ww*0.45+rnd.random()*ww*0.75; py=y+es*0.15+rnd.random()*es*0.95
                    rr=(rnd.random()*4+1)*S; dd.ellipse([px-rr,py-rr,px+rr,py+rr],fill=int(60+120*rnd.random()))
                im=Image.composite(Image.new('RGB',(W,H),(200,255,230)),im,ImageChops.multiply(dots,m.filter(ImageFilter.MaxFilter(15*S+(S+1)%2))))
            else:
                ImageDraw.Draw(im).text((x,y),w,font=ef,fill=(248,250,246))
            x+=ww+ef.getlength(' ')
        y+=lhE
    d=ImageDraw.Draw(im)
    y+=g_badge
    zw=zf.getlength(zh); pad=48*S
    d.rounded_rectangle([(W-zw)/2-pad,y,(W+zw)/2+pad,y+ph],radius=18*S,fill=AC1)
    bb=d.textbbox((0,0),zh,font=zf); d.text(((W-(bb[2]-bb[0]))/2-bb[0],y+(ph-(bb[3]-bb[1]))/2-bb[1]),zh,font=zf,fill=(20,40,32))
    y+=ph+g_logo
    lw=lbox[2]-lbox[0]
    lx=int(round((W-lw)/2))-lbox[0]; ly=int(round(y))-lbox[1]
    im=im.convert('RGBA'); im.alpha_composite(logo,(lx,ly)); im=im.convert('RGB')
    global LAST_LOGO_BOX; LAST_LOGO_BOX=(lx+lbox[0],ly+lbox[1],lx+lbox[2],ly+lbox[3])   # for crops/QA
    im.save(out)
    return im

if __name__=='__main__':
    check_brand_glyphs()
    o=sys.argv[1] if len(sys.argv)>1 else HERE
    frame_title2('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible'],os.path.join(o,'t01.png'))
    frame_title2('02','The Truth About One Marshmallow','一颗棉花糖的真相',['Marshmallow'],[],os.path.join(o,'t02.png'))
    frame_title2('03','The Doctor Who Drank Bacteria to Win an Argument','喝下细菌的医生',['Drank','Bacteria'],['Argument'],os.path.join(o,'t03.png'))
