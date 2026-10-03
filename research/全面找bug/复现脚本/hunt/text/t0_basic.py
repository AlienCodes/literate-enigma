import time
from h import *
t=time.time()
cfg, p = voice(["这个借词是一个定语从剧。", "我们今天看看看这个关系带词。", "Hello world,这是英文。"])
r = wf.run_transcript_fix(cfg, "v", once=True)
print("secs", time.time()-t, r.get("fixes"), r["adopted"])
for k,v in table(p).items(): print(k, v)
print(tf.textfix_used(p), tf.textfix_new_ids(p))
try:
    wf.run_transcript_fix(cfg, "v", once=True)
except ValueError as e: print("2nd click:", str(e)[:40])
