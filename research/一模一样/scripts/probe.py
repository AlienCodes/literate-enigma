import sys, math
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from voicetwin.synth.engine import QUALITY_PRESETS, RETRY_SAMPLING
from voicetwin.utils.textutil import detect_lang, syllable_count
# adaptive schedule for perfect
base=20240601; idx=5
seed0=base+idx*7919
sched=[]
tried=0;b=0;batch=4;cap=20
while tried<cap:
    sampling=None if b%3==0 else RETRY_SAMPLING[(b%3)-1]
    for k in range(min(batch,cap-tried)):
        sched.append((b,k,seed0+(b*101+k)*104729, sampling))
        tried+=1
    b+=1
for s in sched: print(s)
# language detection on mixed text
for t in ["我们看这个例子：I have a cat.","好 The quick brown fox jumps over the lazy dog and runs away fast.",
          "例如 apple 这个词。", "比如 This is a very long English example sentence used to show the rule clearly."]:
    print(t, detect_lang(t), syllable_count(t))
# ref bucket
n=syllable_count("这是一个二十个字左右的句子，用来测试参考音频的选择。")+1
for L in [10,15,20,25,30,40]:
    print(L, round(abs(math.log((L+1)/n)),1))
