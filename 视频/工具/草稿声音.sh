#!/bin/bash
# 草稿声音（2026-10-16 方法升级，11 方法复盘定的：把 自动切点 → 重建 → 确认迁移 → 核查 串成一条命令）。在视频工作目录下运行：bash <工具目录>/草稿声音.sh NN
# 结尾句接点 → 三轮（重建 → 疑点清单 → 自动切点 --写入）→ 词尾辅音 --写入 → 重建 → 确认按位置迁移 → 只打印问题行：
# 三项声音核查的问题数、程序交人看的疑点、读音待核实。人只看这些。
no=$1; T=/home/user/postgraduate-vocabulary/视频/工具
# A45（2026-10-24）：改了读音或语速，这一句旧的非人声区间、词尾除阻、停顿删除、插入点和对应确认自动作废：出片程序跳过它们（OLD_IV_VOID=1），区间作废.py 从脚本删掉，下面重找
export OLD_IV_VOID=1
# 已定过结尾句语速的（20 前段 0.96，A27）照原语速重找接点，不改回默认值
ea=$(python3 -c "import json;e=list(json.load(open('scripts/$no.json')).get('结尾句',{}).values());e=e[0] if e else {};ks=('前段语速','最后一段语速','最后一段前停顿');print(*(e[k] for k in ks) if all(k in e for k in ks) else '')")
python3 $T/结尾句接点.py $no $ea --写入 2>&1 | grep -E "接点样本|停止|没有句中标点" | cut -c1-160
for i in 1 2 3; do bash $T/快速重建核查.sh $no >/dev/null 2>&1; python3 $T/区间作废.py $no 2>&1 | grep -v "没有读音"; python3 $T/疑点清单.py $no >/dev/null 2>&1; python3 $T/自动切点.py $no --写入 2>&1 | grep -E "^$no 疑点|停止"; done
python3 $T/词尾辅音核对.py $no --写入 2>&1 | grep -E "写入|问题数" | tail -3
bash $T/快速重建核查.sh $no 2>&1 | grep -E "问题数|停止|指纹"
python3 $T/区间作废.py $no --记指纹
python3 $T/疑点清单.py $no >/dev/null 2>&1; python3 $T/确认按位置迁移.py $no
python3 $T/自动切点.py $no 2>&1 | grep "人看" | cut -c1-120
python3 $T/读音核对.py $no 2>&1 | grep -E "待核实 \[|BAD|问题数" | cut -c1-170
