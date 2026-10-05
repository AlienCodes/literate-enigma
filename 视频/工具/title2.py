from PIL import Image,ImageDraw,ImageFilter,ImageChops
import render as R
S=R.S
W,H=1920*S,1080*S
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
def frame_title2(no,en,zh,hl,ghost,out,variant=1):
    im=base(variant); d=ImageDraw.Draw(im)
    AC1,AC2=(255,214,64),(255,120,80)
    # watermark number
    nf=R.EN(620*S,900); txt=no
    wm=Image.new('L',(W,H),0); ImageDraw.Draw(wm).text((W-nf.getlength(txt)-40*S,H-700*S),txt,font=nf,fill=22)
    im=Image.composite(Image.new('RGB',(W,H),(140,220,180)),im,wm); d=ImageDraw.Draw(im)
    words=[(w,('h' if w.strip(',.') in hl else 'g' if w.strip(',.') in ghost else 'n')) for w in en.split()]
    for es in range(168*S,60,-4):
        ef=R.EN(es,900); lines=wrap(words,ef,1680*S)
        if len(lines)<=3: break
    kf=R.ZH(36*S,700); zf=R.ZH(int(es*0.57),900)
    kick=f"考研英语精读 · No.{no}"
    lhE=int(es*1.08); total=70*S+len(lines)*lhE+50*S+int(es*0.57*1.55)
    y=(H-total)/2
    # kicker with lines
    kw=kf.getlength(kick); kx=(W-kw)/2
    d.text((kx,y),kick,font=kf,fill=(94,234,212))
    d.line([(kx-120*S,y+24*S),(kx-30*S,y+24*S)],fill=(94,234,212),width=3*S); d.line([(kx+kw+30*S,y+24*S),(kx+kw+120*S,y+24*S)],fill=(94,234,212),width=3*S)
    y+=80*S
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
                # ghost: faded fill + outline shimmer
                fade=Image.new('L',(W,H),0)
                for i in range(int(ww)+1):
                    pass
                gm=Image.new('L',(int(ww)+2,int(es*1.3)))
                gd=ImageDraw.Draw(gm)
                for i in range(gm.width): gd.line([(i,0),(i,gm.height)],fill=int(255-230*(i/gm.width)**1.3))
                fm=Image.new('L',(W,H),0); fm.paste(gm,(int(x),int(y)))
                im=Image.composite(Image.new('RGB',(W,H),(248,250,246)),im,ImageChops.multiply(m,fm))
                dots=Image.new('L',(W,H),0); dd=ImageDraw.Draw(dots)
                import random; random.seed(3)
                for _ in range(260*S):
                    px=x+ww*0.45+random.random()*ww*0.75; py=y+es*0.15+random.random()*es*0.95
                    rr=(random.random()*4+1)*S; dd.ellipse([px-rr,py-rr,px+rr,py+rr],fill=int(60+120*random.random()))
                im=Image.composite(Image.new('RGB',(W,H),(200,255,230)),im,ImageChops.multiply(dots,m.filter(ImageFilter.MaxFilter(15*S+1))))
            else:
                ImageDraw.Draw(im).text((x,y),w,font=ef,fill=(248,250,246))
            x+=ww+ef.getlength(' ')
        y+=lhE
    d=ImageDraw.Draw(im)
    y+=48*S
    zw=zf.getlength(zh); pad=48*S; ph=int(es*0.57*1.55)
    d.rounded_rectangle([(W-zw)/2-pad,y,(W+zw)/2+pad,y+ph],radius=18*S,fill=AC1)
    bb=d.textbbox((0,0),zh,font=zf); d.text(((W-(bb[2]-bb[0]))/2-bb[0],y+(ph-(bb[3]-bb[1]))/2-bb[1]),zh,font=zf,fill=(20,40,32))
    im.save(out)
if __name__=='__main__':
    frame_title2('01','The Robber Who Thought Lemon Juice Made Him Invisible','以为柠檬汁能隐身的劫匪',['Lemon','Juice'],['Invisible'],'t1.png')
