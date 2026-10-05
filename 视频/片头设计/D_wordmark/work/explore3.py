import sys,os
VID='/tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/video'
sys.path.insert(0,VID+'/logo/D_wordmark'); os.chdir(VID)
from PIL import Image
import title_logo as T
bg=T.base(1).crop((660,300,1260,900))
y=10
for kw in [dict(size=58,bold=0.025),dict(size=60,bold=0.018),dict(size=60,bold=0.018,glow=0.45),dict(size=62,bold=0.012)]:
    L,b=T.brand_lockup(1,**kw); bg.paste(L,((bg.width-L.width)//2,y),L); y+=L.height
bg=bg.resize((bg.width*2,bg.height*2),Image.LANCZOS); bg.save(VID+'/logo/D_wordmark/work/explore3.png')
