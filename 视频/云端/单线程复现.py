"""单线程复现（G72 证明）：用出片程序同一种单线程会话，逐句合成一篇的全部句子，打印每句和总的声音指纹；两台机器输出逐行相同 = 跨机器逐样本可复现。
用法：python3 单线程复现.py <tts目录> <脚本.json>"""
import sys, json, re, hashlib, numpy as np, onnxruntime as ort
from kokoro_onnx import Kokoro
D, js = sys.argv[1:3]
so = ort.SessionOptions(); so.intra_op_num_threads = 1; so.inter_op_num_threads = 1
k = Kokoro.from_session(ort.InferenceSession(f'{D}/kokoro-v1.0.onnx', so, providers=['CPUExecutionProvider']), f'{D}/voices-v1.0.bin')
V = np.load(f'{D}/voice_mb.npy'); d = json.load(open(js)); tot = hashlib.md5()
for i, s in enumerate(d['sentences']):
    t = ' '.join(re.sub(r'\*\*|\{\{.*?\}\}', '', c['en']).strip() for c in s['chunks'])
    a = np.asarray(k.create(t, voice=V, speed=0.95, lang='en-us')[0], np.float32); h = hashlib.md5(a.tobytes()).hexdigest()[:12]; tot.update(a.tobytes())
    print(f'S{i+1} {len(a)} {h}', flush=True)
print('总', tot.hexdigest()[:16])
