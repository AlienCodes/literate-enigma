# 全面核对（标题和所有句子）：clean_tail 在句首、句尾修剪掉的部分有没有剪到词。（停顿位置改由 停顿位置精确核对.py 负责）
# 2026-10-09 修正两处错误（A10b 复犯）：① 基准改成本句最响的 5 ms 帧（原来用单个采样点的峰值，比 5 ms 帧高约 10 dB，等于把门槛放宽了 10 dB）；
# ② 合成前先经过数字读法 spoken()、去掉粗体和中文说明（与出片程序 say()/sentence_audio 完全相同；原来直接合成原文，数字处与成片不是同一段声音）。
# 判定（电平都相对本句最响的 5 ms 帧，能听见 = ≥-55 dB，A13）：
#   句首：剪点前紧挨着的 20 ms 里有能听见的帧 = 剪到了第一个词的起音 → BAD；离剪点 20 ms 以外、与词之间隔着听不见部分的，是开口前的杂音（纯人声要删），列出不报错。
#   句尾：剪掉的部分里有任何能听见的帧 → BAD（可能是词尾塞音的除阻，要用实际声音核实）。
#   淡出：句尾最后 50 ms 淡出处，原来的声音有 ≥-40 dB 的帧 → BAD（淡出改动了词尾，独立复核 A10 的同一口径）。
import re,json,sys
sys.path.insert(0,".")
exec(open('make_video.py').read().split("if __name__")[0])
F5=int(0.005*SR); GUARD=int(0.02*SR)
def db5(x,ref):
    m=len(x)//F5
    return 20*np.log10(np.sqrt(np.mean(x[:m*F5].reshape(m,F5)**2,axis=1))/ref+1e-9) if m else np.zeros(0)
bad=0
for no in sys.argv[1:]:
    d=json.load(open(f'scripts/{no}.json'))
    texts=[d['title_en']]+[' '.join(re.sub(r'\*\*','',R.strip_gloss(c['en'])).strip() for c in s['chunks']) for s in d['sentences']]
    for si,sent in enumerate(texts):
        raw,_=k.create(spoken(re.sub(r'\*\*','',R.strip_gloss(sent))),voice=V,speed=SPEED,lang='en-us'); raw=np.asarray(raw,np.float32); w=clean_tail(raw)
        st=_head_offset(raw,w); en=st+len(w)
        m=len(raw)//F5; ref=np.sqrt(np.mean(raw[:m*F5].reshape(m,F5)**2,axis=1)).max()
        near=db5(raw[max(0,st-GUARD):st],ref); far=db5(raw[:max(0,st-GUARD)],ref); tail=db5(raw[en:],ref); fade=db5(raw[en-int(0.05*SR):en],ref)
        mx=lambda x: float(x.max()) if len(x) else -99.0
        hn,hf,tl,fd=mx(near),mx(far),mx(tail),mx(fade)
        flag=(hn>=AUD_DB) or (tl>=AUD_DB) or (fd>=-40)
        if flag: bad+=1
        note=f'（剪点 20 ms 以外删掉了开口前的杂音，最响 {hf:.0f}dB，不是词）' if hf>=AUD_DB else ''
        print(f"{no} {'标题' if si==0 else 'S%d'%si} {'BAD' if flag else 'OK '} 句首删掉 {st/SR:.3f}s（剪点前 20 ms 最响 {hn:.0f}dB）{note}｜句尾删掉 {(len(raw)-en)/SR:.3f}s 最响 {tl:.0f}dB｜淡出段原响度 {fd:.0f}dB")
print('问题数',bad)
