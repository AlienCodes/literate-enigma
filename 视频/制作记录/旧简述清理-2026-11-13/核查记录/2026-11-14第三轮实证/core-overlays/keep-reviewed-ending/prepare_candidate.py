#!/usr/bin/env python3
"""Isolated ending-point preservation repair. Never write production sources."""
import hashlib
import json
import shutil
import subprocess
import difflib
from pathlib import Path

O = Path(__file__).resolve().parent
OLD = O.parent / 'keep-reviewed-gain'
REPO = Path('/workspace/work/github-publication/target')
PIN = '64621068034f8b6e09836a6d97210a0e9b2f1ed6'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


original = O / 'original-pinned'
for rel in ['视频/工具/结尾句接点.py', '视频/工具/make_video.py', '视频/工具/草稿声音.sh', '视频/工具/新管/快测.py', '视频/工具/新管/印章.py']:
    dest = original / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(subprocess.check_output(['git', 'show', f'{PIN}:{rel}'], cwd=REPO))
certified_shell = OLD / 'validated-install/视频/工具/草稿声音.sh'
assert sha(certified_shell) == '957d7eb1598698ea33ff77d83379256ecae258d84d588753d561a902284be439'
certified_before = O / 'original-certified/视频/工具/草稿声音.sh'
certified_before.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(certified_shell, certified_before)
patch = O / 'patch/视频/工具'
patch.mkdir(parents=True, exist_ok=True)
tool = (original / '视频/工具/结尾句接点.py').read_text()
tool = tool.replace('  --写入：把 结尾句 写进 scripts/NN.json（已有就覆盖这一句的设置）。',
'''  --写入：把 结尾句 写进 scripts/NN.json（已有就覆盖这一句的设置）。
  --保持已审接点：修订重制时，已有接点先通过原 _ending_parts 静音门，再原样保留整条设置与文件；
    已有坏点直接停止，不改成自动新点；没有既有接点才走原自动流程。已有整句语速模式也保持原样。''')
anchor = "def 自检():\n"
addition = '''def 保持已有接点(d, sent, parts):
    """只读验证已有末句设置；parts 必须是原出片程序 _ending_parts，任何原门失败原样向上传递。"""
    e = d.get('结尾句', {}).get(f"S{len(d['sentences'])}")
    if not isinstance(e, dict): return False
    if '整句语速' in e:
        print('  保持已审整句语速：原设置和脚本文件未写入')
        return True
    if '接点' not in e: return False
    parts(sent, e)   # 原三帧 -55 dB 接点门及原音调范围门；坏点绝不退回自动找点
    print(f"  保持已审接点样本 {e['接点']}：原静音门通过，原设置和脚本文件未写入")
    return True


def 保持自检():
    import copy
    f = []; calls = []
    d = {'sentences': [{}], '结尾句': {'S1': {'接点': [100, 200], '前段语速': .9, '最后一段语速': .78, '最后一段前停顿': .7, '前段增益dB': -2.5, '依据': '旧原话', '前段音调': {'范围': [.1, .4]}}}}
    old = copy.deepcopy(d)
    if not 保持已有接点(d, 'If so, yes.', lambda s, e: calls.append((s, copy.deepcopy(e)))) or len(calls) != 1 or d != old:
        f.append('已有设置没经过原门，或被改写')
    def bad(s, e): raise SystemExit('【停止】原门坏接点')
    try:
        保持已有接点(d, 'If so, yes.', bad); f.append('已有坏接点被放行或回退自动找点')
    except SystemExit as x:
        if '原门坏接点' not in str(x): f.append('没有保留原门错误')
    if d != old: f.append('原门拒绝后仍改了设置')
    if 保持已有接点({'sentences': [{}]}, 'If so, yes.', bad): f.append('无已有接点时没走原自动流程')
    whole = {'sentences': [{}], '结尾句': {'S1': {'整句语速': .80, '依据': '原整句'}}}
    prior = copy.deepcopy(whole)
    if not 保持已有接点(whole, 'Yes.', bad) or whole != prior: f.append('整句语速被改写或错误要求接点')
    return ['保持已审接点 自检：' + x for x in f]


'''
assert tool.count(anchor) == 1
tool = tool.replace(anchor, addition + anchor)
tool = tool.replace("e = 自检() + 前提自检()", "e = 自检() + 保持自检() + 前提自检()")
anchor = "puncts_ = 句中标点(sent_, no_)"
assert tool.count(anchor) == 1
tool = tool.replace(anchor, "if '--保持已审接点' in sys.argv and 保持已有接点(d_, sent_, _ending_parts): sys.exit(0)\n" + anchor)
(patch / '结尾句接点.py').write_text(tool)
shell = certified_shell.read_text()
anchor = 'python3 $T/结尾句接点.py $no $ea --写入 2>&1 | grep -E "接点样本|停止|没有句中标点" | cut -c1-160'
assert shell.count(anchor) == 1
shell = shell.replace(anchor, '''# 修订重制只验证并保留已有已审接点；坏点原门停止，不用自动新点替代。
if [ "${XG_KEEP_REVIEWED_ENDING:-0}" = "1" ]; then
    python3 $T/结尾句接点.py $no $ea --写入 --保持已审接点 2>&1 | grep -E "接点样本|保持已审|停止|没有句中标点" | cut -c1-160
    ending_rc=${PIPESTATUS[0]}
    if [ "$ending_rc" -ne 0 ]; then exit "$ending_rc"; fi
else
    ''' + anchor + '''
fi''')
(patch / '草稿声音.sh').write_text(shell)
diff = O / 'diff'
diff.mkdir(exist_ok=True)
for name in ['结尾句接点.py', '草稿声音.sh']:
    old = certified_before if name == '草稿声音.sh' else original / '视频/工具' / name
    new = patch / name
    (diff / (name + '.diff')).write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True), new.read_text().splitlines(True), fromfile=f'pinned/{name}', tofile=f'candidate/{name}')))
manifest = {'status': 'isolated_candidate_not_installed', 'main_pin': PIN, 'production_source_written': False,
            'mode_environment': {'XG_KEEP_REVIEWED_ENDING': '1'},
            'default_behavior': 'unchanged original automatic recomputation; new branch only under explicit ENV/CLI',
            'new_mode': 'existing full ending entry byte-preserved only after original producer _ending_parts gates; failures propagate; no prior entry uses original algorithm',
            'producer_unchanged_sha256': sha(original / '视频/工具/make_video.py'),
            'files': [{'path': f'视频/工具/{n}', 'pinned_main_sha256': sha(original / '视频/工具' / n),
                       'certified_before_sha256': sha(certified_before if n == '草稿声音.sh' else original / '视频/工具' / n),
                       'candidate_sha256': sha(patch / n)} for n in ['草稿声音.sh', '结尾句接点.py']]}
(O / 'candidate-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(manifest, ensure_ascii=False, indent=2))
