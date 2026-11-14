# 试算：与 make_video.py 完全相同的配音与时间表，只是不画图、不压视频；写到 dry_NN/list.txt、dry_NN/a.wav
import sys
src=open('make_video.py').read().split("if __name__")[0]
for a,b in [("work=f'work_{no}'","work=f'dry_{no}'"),("R.frame_interlinear(","(lambda *a,**k:None)("),
            ("af=TA.render_frames(","af=(lambda *a,**k:[('title.png',0.0)])("),("subprocess.run([FF,","(lambda *a,**k:None)([FF,")]:
    assert src.count(a)==1,a; src=src.replace(a,b)
exec(src)
build(sys.argv[1],'none.mp4')
