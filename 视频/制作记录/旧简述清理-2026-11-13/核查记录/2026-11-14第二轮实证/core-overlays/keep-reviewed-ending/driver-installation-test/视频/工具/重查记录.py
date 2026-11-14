#!/usr/bin/env python3
"""重查记录（铁4/G9/G22）：存的视频是不是还和现行程序、现行脚本一致。按篇记在 工具/全篇重查通过.json：
键 = 程序指纹 + 这一篇存的视频 + 现行脚本，三样都没变，上次的重查结论就还算数；任何一样变了就“欠着”。
全篇核查.py --视频 逐篇重查并记；踩坑核查 文本阶段对已有定稿 4K 的篇目欠着时提醒（G22）。"""
import os, re, json, hashlib
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
STAMP = f'{T}/全篇重查通过.json'
def 程序指纹(t=T):   # 铁4：出片程序、排版程序（配音处理、停顿规则都在 make_video.py 里）；G27：make_video 递归 import 的全部模块（对正量、片头等）
    import sys; sys.path.insert(0, T); import 出片指纹 as Z
    return hashlib.sha256(b''.join(open(p, 'rb').read() for _, p in sorted(Z.清单([t]).items()))).hexdigest()[:16]
def _sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def 已出片():
    P = os.path.dirname(V); out = {}
    for f in sorted(os.listdir(f'{P}/最终版4K视频')):
        if f.endswith('.mp4') and f[:2].isdigit(): out[f[:2]] = f'{P}/最终版4K视频/{f}'
    return out
def 键(no, mp4, fp=None):   # 程序 + 这一篇存的视频 + 现行脚本：三样都没变，上次的重查结论就还算数
    js = f"{V}/脚本/{no}.json"; return f'{fp or 程序指纹()}-{_sha(mp4)}-{_sha(js) if os.path.exists(js) else "无"}'   # 演练镜像里冻结样本没有新归档篇目的脚本：按“无”算（和 演练镜像.仓库底稿 一致）
def 用户免重查():
    """用户 2026-11-04（45 会话）：“已经定稿的之前已经定稿的不要再乱动”：出片程序改过后，已定稿篇不再全篇重查、也不再提醒"""
    try: return any(r.get('用于', '').startswith('已定稿不重查') for r in json.load(open(os.path.join(T, '用户同意记录.json')))['记录'])
    except Exception: return False
def 定稿提醒(no, 已, 欠):
    """G22：已有定稿 4K 的篇目，现行脚本或程序和存的视频对不上 → 提醒必须重出 4K（2026-10-23 我改了已定稿的 21 没重出，全篇重查才查出来）"""
    if no in 已 and no in 欠:
        return f'★ [G22] 第{no}篇已有定稿 4K，现行脚本或程序和存的视频对不上（或还没重查过）：改完必须 bash 视频/工具/新管/定稿.sh {no} 重出 4K、归档（G9）'
def 读记录(stamp=STAMP):
    """{篇: {键,…}}。K158（2026-11-03 11:58 两个会话同时记、merge=union 把两边的行拼在一起，JSON 缺逗号读不出，全部篇目被当成没查过、
    每次定稿都把 36 篇从头重查）：读不出就逐行把 "篇": "键" 捞回来，两边的键都认"""
    try: return {k: {v} for k, v in json.load(open(stamp)).get('篇', {}).items()}
    except Exception: pass
    try: t = open(stamp).read()
    except Exception: return {}
    out = {}
    for no, k in re.findall(r'"(\d\d)"\s*:\s*"([0-9a-f]{16}-[0-9a-f]{16}-(?:[0-9a-f]{16}|无))"', t): out.setdefault(no, set()).add(k)
    return out
def 记(updates, stamp=STAMP, fp=None):
    """把这次查过的 {篇: 键} 并进记录，总写成合法 JSON；别的篇每篇留一个键（有现行程序指纹的优先）"""
    import datetime
    fp = fp or 程序指纹(); out = {}
    for no, ks in 读记录(stamp).items():
        ks = sorted(ks); out[no] = next((k for k in ks if k.startswith(fp)), ks[-1])
    out.update(updates)
    json.dump({'篇': dict(sorted(out.items())), '时间': f'{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%dT%H:%M}（UTC）'}, open(stamp, 'w'), ensure_ascii=False, indent=0)
def 欠着(stamp=STAMP, keys=None):
    """还没用现行程序重查过的已出片篇目（铁4/音29/画21：改一处，全部重查）；按篇记，查一篇记一篇，中途停了不白查"""
    if keys is None: fp = 程序指纹(); keys = {no: 键(no, p, fp) for no, p in 已出片().items()}
    st = 读记录(stamp)
    return [no for no, k in sorted(keys.items()) if k not in st.get(no, set())]


if __name__ == '__main__' and '--自检' in __import__('sys').argv:   # K158：merge=union 拼坏的记录照样读出两边的键；记() 写回合法 JSON
    import tempfile, sys
    fp_ = 'a' * 16; k1 = f'{fp_}-{"1" * 16}-{"2" * 16}'; k2 = f'{"b" * 16}-{"3" * 16}-{"4" * 16}'; k3 = f'{fp_}-{"5" * 16}-{"6" * 16}'
    坏 = '{\n"篇": {\n"01": "%s",\n"02": "%s"\n"01": "%s"\n},\n"时间": "x"\n}' % (k2, k3, k1)   # 两边都留、缺逗号
    td = tempfile.mkdtemp(); sp = f'{td}/s.json'; open(sp, 'w').write(坏); f = []
    st = 读记录(sp)
    if st.get('01') != {k1, k2} or st.get('02') != {k3}: f.append(f'没捞全：{st}')
    if 欠着(sp, {'01': k1, '02': k3}): f.append('误报：拼坏的记录里有的键也算欠着')
    if 欠着(sp, {'01': f'{fp_}-{"9" * 16}-{"9" * 16}', '02': k3}) != ['01']: f.append('没抓到：键变了还不算欠着')
    记({'03': k1}, sp, fp_); d_ = json.load(open(sp))['篇']
    if d_ != {'01': k1, '02': k3, '03': k1}: f.append(f'记() 写回不对：{d_}')
    print('重查记录 自检：' + ('通过（拼坏的记录照读、两边的键都认、键变了算欠着、写回合法 JSON）' if not f else '失灵！' + '；'.join(f))); sys.exit(1 if f else 0)
