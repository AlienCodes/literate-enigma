"""合成对照（2026-10-26 GitHub 化）：同一句在不同机器上合成是否逐样本相同。按几种 onnxruntime 设置各合成一次，打印声音指纹。
用法：python3 合成对照.py <tts目录>   两台机器的输出逐行比，指纹相同的设置就能跨机器逐样本复现。"""
import sys, hashlib, numpy as np, onnxruntime as ort, platform, os
from kokoro_onnx import Kokoro
D = sys.argv[1]; V = 'af_heart'
TXT = ['In all the major economies, scientists raise this question.', 'Whether that is a good thing remains to be seen.']
cpu = next((l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')), '?')
flags = next((l for l in open('/proc/cpuinfo') if l.startswith('flags')), '')
print('机器', cpu, '| avx512' if 'avx512f' in flags else '| 无avx512', '| ort', ort.__version__)
def k_of(opt, thr):
    so = ort.SessionOptions(); so.graph_optimization_level = opt; so.intra_op_num_threads = thr; so.inter_op_num_threads = 1
    return Kokoro.from_session(ort.InferenceSession(f'{D}/kokoro-v1.0.onnx', so, providers=['CPUExecutionProvider']), f'{D}/voices-v1.0.bin')
for name, opt, thr in [('默认', ort.GraphOptimizationLevel.ORT_ENABLE_ALL, 0), ('单线程', ort.GraphOptimizationLevel.ORT_ENABLE_ALL, 1),
                       ('单线程+不优化', ort.GraphOptimizationLevel.ORT_DISABLE_ALL, 1)]:
    k = k_of(opt, thr)
    h = [hashlib.md5(np.asarray(k.create(t, voice=V, speed=0.95, lang='en-us')[0], np.float32).tobytes()).hexdigest()[:12] for t in TXT]
    print(name, *h, flush=True)
