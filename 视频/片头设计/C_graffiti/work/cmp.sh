cd /tmp/claude-0/-home-user-literate-enigma/df763388-3805-5b4c-bf94-30b7788b9986/scratchpad/video
D=logo/C_graffiti/work
python3 $D/tagone.py $D/v_none.png
KEYLINE=255,214,64 python3 $D/tagone.py $D/v_yel.png
KEYLINE=255,240,245 python3 $D/tagone.py $D/v_wht.png
KEYLINE=255,214,64 KL_W=3.2 python3 $D/tagone.py $D/v_yel3.png
python3 -c "
from PIL import Image
ims=[Image.open('$D/v_%s.png'%k) for k in ['none','yel','wht','yel3']]
w=max(i.width for i in ims); h=sum(i.height for i in ims)
c=Image.new('RGB',(w,h)); y=0
for i in ims: c.paste(i,(0,y)); y+=i.height
c=c.resize((c.width*2,c.height*2),Image.LANCZOS); c.save('$D/cmp_keyline.png'); print(c.size)
"
