import sys,os; sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import title_logo as T
from PIL import Image
W=os.path.dirname(os.path.abspath(__file__))
s,c=T.make_seal(400)
bg=Image.new('RGBA',(c,c),(16,44,36,255)); bg.alpha_composite(s); big=bg.convert('RGB')
s2,c2=T.make_seal(154)
bg2=Image.new('RGBA',(c2,c2),(16,44,36,255)); bg2.alpha_composite(s2); sm=bg2.convert('RGB')
ph=sm.resize((c2*45//100,c2*45//100),Image.LANCZOS).resize((c2,c2),Image.NEAREST)  # phone-ish scale
out=Image.new('RGB',(c+c2+20,c),(0,0,0)); out.paste(big,(0,0)); out.paste(sm,(c+20,0)); out.paste(ph,(c+20,c2+20))
out.save(os.path.join(W,'seal_test.png'))
