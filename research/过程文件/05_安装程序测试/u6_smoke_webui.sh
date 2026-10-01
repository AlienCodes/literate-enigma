#!/bin/bash
# Smoke test: real gradio 4.24 launch via launcher, then a second launch must detect the running instance.
WT=<仓库>/.claude/worktrees/wf_08725f86-d54-6
PY=<草稿目录>/gsv39/bin/python
D=<草稿目录>/u6smoke
rm -rf "$D"; mkdir -p "$D"; cd "$D" || exit 1
export PYTHONPATH="$WT"
export BROWSER=true
printf 'workspace: ./ws\nbackend: dummy\n' > config.yaml
# occupy 7941 with a non-gradio listener so the launcher must move to 7942
$PY -c "import socket,time;s=socket.socket();s.bind(('127.0.0.1',7941));s.listen();time.sleep(60)" &
BLOCK=$!
sleep 1
timeout 60 $PY -m voicetwin webui --port 7941 > first.log 2>&1 &
FIRST=$!
for i in $(seq 1 40); do
  if grep -q "Running on local URL" first.log 2>/dev/null; then break; fi
  sleep 1
done
echo "----- first.log"; cat first.log
echo "----- /config title"
$PY -c "import json,urllib.request;o=urllib.request.build_opener(urllib.request.ProxyHandler({}));print(json.loads(o.open('http://127.0.0.1:7942/config',timeout=5).read())['title'])"
echo "----- second launch"
timeout 30 $PY -m voicetwin webui --port 7941; echo "second exit=$?"
kill $FIRST $BLOCK 2>/dev/null
wait 2>/dev/null
echo done
