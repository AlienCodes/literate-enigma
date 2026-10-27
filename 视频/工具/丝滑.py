#!/usr/bin/env python3
"""丝滑记录（K，用户 2026-10-27 丝滑主义：“一定要确保这个流程的运行，中间非常的丝滑，没有任何的bug，没有任何的问题，也没有任何程序上之间的冲突”）。
正式入口（会话开工、草稿声音.sh、交付核查、定稿流水线、推送两仓库）每次停下记一条到 制作记录/丝滑/NN.jsonl（没篇号记 会话.jsonl）：
  内容问题 = 门在干活（稿子、声音、画面有毛病被挡下，正常）；
  不丝滑   = 程序毛病、环境缺东西、会话间冲突、要重读重跑、手工绕过（目标 0，每条都要报坑 G54）。
方法进化表 每篇加“不丝滑次数”，比前三篇中位数变差沿用 G65（方法复盘要写查得到的进化落地）。
用法：python3 视频/工具/丝滑.py 记 <入口> <NN|-> "<停下的原因>" [不丝滑|内容问题]
      python3 视频/工具/丝滑.py --次数 NN      python3 视频/工具/丝滑.py --自检"""
import os, sys, re, json, datetime, tempfile, shutil
T = os.path.dirname(os.path.abspath(__file__)); V = os.path.dirname(T)
目录 = [f'{V}/制作记录/丝滑']
不丝滑式 = re.compile(r'Traceback|ModuleNotFound|ImportError|No such file|NoSuchFile|找不到|缺包|缺 ffmpeg|环境|bad substitution|syntax error|'
                    r'锁|冲突|超时|timeout|Timeout|网络|连接|重读|印章|过期|没开工|会话开工|角色闸门|打不上|409|403|Permission|权限|'
                    r'一致（G2|白名单外|镜像|推送|失灵|崩|出错|异常|工作目录|work_\d\d/a\.wav')


接线 = {'定稿流水线.sh': 'python3 "$T/丝滑.py" 记 定稿流水线', '草稿声音.sh': 'python3 $T/丝滑.py 记 草稿声音', '推送两仓库.sh': '丝滑.py" 记 推送两仓库',
        '交付核查.py': "_SH.记('交付核查'", '会话开工.py': "丝滑.记('会话开工'"}


def 分类(说明):
    return '不丝滑' if 不丝滑式.search(说明 or '') else '内容问题'


def 记(入口, 篇, 说明, 类=None):
    类 = 类 or 分类(说明); 篇 = 篇 if re.fullmatch(r'\d\d', 篇 or '') else '会话'
    os.makedirs(目录[0], exist_ok=True)
    r = {'时刻': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), '入口': 入口, '类': 类, '说明': (说明 or '')[:300]}
    with open(f'{目录[0]}/{篇}.jsonl', 'a') as f: f.write(json.dumps(r, ensure_ascii=False) + '\n')
    if 类 == '不丝滑':
        print(f'【不丝滑（丝滑主义 K）】{入口} 停下不是稿子的问题：{r["说明"][:120]}\n  当场报坑：python3 视频/工具/报坑.py "{篇 if 篇 != "会话" else ""} {入口}：{r["说明"][:60]}"（G54）')
    return r


def 次数(篇, 类='不丝滑'):
    f = f'{目录[0]}/{篇}.jsonl'
    if not os.path.exists(f): return 0
    n = 0
    for l in open(f):
        try: n += json.loads(l).get('类') == 类
        except Exception: pass
    return n


def 自检():
    f = []; old = 目录[0]; d = tempfile.mkdtemp(prefix='丝滑自检_'); 目录[0] = d
    try:
        for s in ("ModuleNotFoundError: No module named 'soundfile'", "bad substitution", '改门锁：别人持锁', '开工必读 更新了，--重读',
                  '两仓库 视频/ 不一致（G2）', '新容器没有 work_25/a.wav', '慢自检的印章对不上'):
            if 分类(s) != '不丝滑': f.append(f'没抓到：“{s}”该算不丝滑（K）')
        for s in ('[T36] S3 有破折号', 'S4 词尾辅音 /t/ 听不清', '[L19] 说明比正文宽', '读音核对 问题数 2'):
            if 分类(s) != '内容问题': f.append(f'误判：“{s}”是门在干活，不是不丝滑（K）')
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            记('定稿流水线', '28', 'ModuleNotFoundError: soundfile'); 记('交付核查', '28', '[T36] 破折号'); 记('推送两仓库', '-', '两仓库 视频/ 不一致（G2）')
        if buf.getvalue().count('当场报坑') != 2: f.append('不丝滑没提示报坑（K/G54）')
        if 次数('28') != 1 or 次数('28', '内容问题') != 1 or 次数('会话') != 1: f.append(f'计数不对（K）：28 不丝滑 {次数("28")}、内容 {次数("28", "内容问题")}、会话 {次数("会话")}')
        for prog, anc in 接线.items():   # 五个正式入口都接上（拆掉任何一处必须发现）
            if anc not in open(f'{T}/{prog}').read(): f.append(f'没接上：{prog} 停下不记丝滑（K）')
    finally:
        目录[0] = old; shutil.rmtree(d, ignore_errors=True)
    return f


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--自检' in a:
        e = 自检(); print('丝滑记录 自检：' + ('通过（程序/环境/冲突/重读重跑算不丝滑，稿子内容问题不算；按篇计数）' if not e else '失灵！' + '；'.join(e))); sys.exit(1 if e else 0)
    if '--次数' in a: print(次数(a[a.index('--次数') + 1])); sys.exit(0)
    if a and a[0] == '记' and len(a) >= 4: 记(a[1], a[2], a[3], a[4] if len(a) > 4 else None); sys.exit(0)
    sys.exit(__doc__)
