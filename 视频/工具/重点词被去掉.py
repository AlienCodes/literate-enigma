"""重点词被去掉的提醒（用户 2026-10-17：“之后我们要去做的时候，你要专门……提醒我……告诉我他去除了哪些重点词汇……你要给我做一个提醒机制”）。
记录在 制作记录/重点词被去掉.json（篇号 → 被去掉的词、句子、原因）。程序执行，不靠记忆：
  开工提醒.sh（每次开会话）、初稿生成/核对.py（生成这一篇的稿子时）都打印；踩坑核查 [T32]：这一篇有被去掉的词而脚本里没有
  核对确认.已告诉用户被去掉的重点词 就停，先把下面的话原样告诉用户。
用法：python3 重点词被去掉.py NN            打印第 NN 篇的提醒（没有就不打印）"""
import json, os, sys
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '制作记录', '重点词被去掉.json')
def 记录(no):
    try: return json.load(open(F)).get(str(no).zfill(2), [])
    except FileNotFoundError: return []
def 提醒(no):
    r = 记录(no)
    if not r: return ''
    out = [f'【重点词被去掉（要告诉用户）】第{str(no).zfill(2)}篇有 {len(r)} 个重点词因撞词被去掉了，做这一篇时先跟用户说清楚，用户可能要另加别的重点词：']
    for x in r:
        out.append(f'  · {x["词"]}（{x["中文"]}），{x["日期"]}：在这一句——{x["英文句"]} ／ {x["中文句"]}；原因：{x["原因"]}')
    return '\n'.join(out)
if __name__ == '__main__':
    t = 提醒(sys.argv[1]) if len(sys.argv) > 1 else ''
    if t: print(t)
