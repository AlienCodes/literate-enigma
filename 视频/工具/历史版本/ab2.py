import numpy as np,soundfile as sf,subprocess,imageio_ffmpeg
from kokoro_onnx import Kokoro
from clean import clean_tail
k=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin'); FF=imageio_ffmpeg.get_ffmpeg_exe()
T="Yet the foundation was precarious. Only a few dozen children entered the SAT analysis, predominantly the sons and daughters of Stanford faculty and postgraduate students. The raw link was roughly half as strong as the original finding."
m=k.get_voice_style('am_michael'); f=k.get_voice_style('am_fenrir')
B=open('AF.txt').read().strip()
NEW="highpass=f=70,afftdn=nf=-32:nr=8,bandreject=f=4800:t=h:w=40,bandreject=f=4800:t=h:w=40,bandreject=f=9600:t=h:w=60,bandreject=f=9600:t=h:w=60,equalizer=f=200:t=q:w=1:g=1.5,equalizer=f=3500:t=q:w=1.5:g=-2,equalizer=f=7000:t=q:w=1.5:g=-3,lowpass=f=10000,aresample=48000:resampler=soxr"
cfg={'B_现在':(0.75*m+0.25*f,0.95,B),'D_更柔和':(0.9*m+0.1*f,0.95,NEW),'E_纯Michael柔和':(m,0.95,NEW)}
for name,(v,sp,af) in cfg.items():
    w,sr=k.create(T,voice=v,speed=sp,lang='en-us'); w=clean_tail(w); w=w/np.abs(w).max()*0.89
    sf.write('/tmp/ab.wav',w,sr)
    subprocess.run([FF,'-y','-loglevel','error','-i','/tmp/ab.wav','-af',af,'-c:a','libmp3lame','-b:a','256k',f'samples/{name}.mp3'],check=True)
print('ok')
