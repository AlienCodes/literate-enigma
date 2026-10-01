import sys, pypdfium2 as pdfium
from PIL import Image
out = sys.argv[1]; pdf = pdfium.PdfDocument("<仓库>/docs/声音分身VoiceTwin使用手册.pdf")
n=len(pdf); print(n)
imgs=[pdf[i].render(scale=0.55).to_pil().convert("RGB") for i in range(n)]
w,h = imgs[0].size; per=12
import os; os.makedirs(out, exist_ok=True)
for f in os.listdir(out): os.remove(os.path.join(out,f))
for s in range(0,n,per):
    sheet = Image.new("RGB",(w*4+50, h*3+40),"#888")
    for k,im in enumerate(imgs[s:s+per]):
        sheet.paste(im,(10+(k%4)*(w+10), 10+(k//4)*(h+10)))
    sheet.save(f"{out}/sheet_{s//per+1:02d}.png")
for i in [int(x) for x in sys.argv[2:]]:
    pdf[i-1].render(scale=1.4).to_pil().save(f"{out}/p{i:02d}.png")
