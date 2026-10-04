#!/bin/bash
# 用法：run_all.sh <仓库> <端口> <结果文件>：重新建工作文件夹、启动网页（pid 文件）、跑 check.py、关掉网页
B=$(dirname "$0"); REPO=$1; PORT=$2; OUT=$3
if [ -f $B/webui.pid ]; then kill $(cat $B/webui.pid) 2>/dev/null; while kill -0 $(cat $B/webui.pid) 2>/dev/null; do sleep 0.3; done; rm -f $B/webui.pid; fi
rm -rf $B/work && /tmp/gsv39/bin/python $B/browser_setup.py $REPO $B/work > /dev/null 2>&1
# 只让 python 本身在后台运行，$! 才是它的 pid（写成「cd && python &」时 $! 是外面那个 shell，kill 它网页还开着）
GRADIO_ANALYTICS_ENABLED=False BROWSER=none nohup /tmp/gsv39/bin/python $B/browser_run_webui.py $REPO $B/work $PORT > $B/webui.log 2>&1 &
echo $! > $B/webui.pid
for i in $(seq 1 120); do grep -q "Running on local URL" $B/webui.log && break; sleep 0.5; done
URL=$(grep -o "Running on local URL: *http://[0-9.:]*" $B/webui.log | grep -o "http://[0-9.:]*")
echo "URL=$URL"
timeout 600 python3 $B/browser_check.py $REPO $B/work $URL/ 2>&1 | grep -v "^[0-9][0-9]:[0-9][0-9]:[0-9][0-9] |" > $OUT
kill $(cat $B/webui.pid); while kill -0 $(cat $B/webui.pid) 2>/dev/null; do sleep 0.3; done; rm -f $B/webui.pid
