import numpy as np,soundfile as sf,subprocess,imageio_ffmpeg
from kokoro_onnx import Kokoro
from clean import clean_tail
k=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin'); FF=imageio_ffmpeg.get_ffmpeg_exe()
T="Yet the foundation was precarious. Only a few dozen children entered the SAT analysis, predominantly the sons and daughters of Stanford faculty and postgraduate students. The raw link was roughly half as strong as the original finding."
m=k.get_voice_style('am_michael'); f=k.get_voice_style('am_fenrir')
B=open('AF.txt').read().strip()
F=B.replace('highpass=f=70,','highpass=f=70,afftdn=nf=-40:nr=4,')
G="highpass=f=70,afftdn=nf=-40:nr=4,bandreject=f=4800:t=h:w=40,bandreject=f=4800:t=h:w=40,bandreject=f=9600:t=h:w=60,bandreject=f=9600:t=h:w=60,equalizer=f=180:t=q:w=1:g=1.5,equalizer=f=2500:t=q:w=1.2:g=1.5,equalizer=f=5500:t=q:w=2:g=-1.5,lowpass=f=11500,aresample=48000:resampler=soxr"
cfg={'B_现在':(0.75*m+0.25*f,B),'F_原声去底噪':(0.75*m+0.25*f,F),'G_清亮不沙':(0.85*m+0.15*f,G)}
for name,(v,af) in cfg.items():
    w,sr=k.create(T,voice=v,speed=0.95,lang='en-us'); w=clean_tail(w); w=w/np.abs(w).max()*0.89
    sf.write('/tmp/ab.wav',w,sr)
    subprocess.run([FF,'-y','-loglevel','error','-i','/tmp/ab.wav','-af',af,'-c:a','libmp3lame','-b:a','256k',f'samples/{name}.mp3'],check=True)
open('AF_F.txt','w').write(F); open('AF_G.txt','w').write(G)
print('ok')
