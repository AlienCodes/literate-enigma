cd /tmp/claude-0/-home-user-literate-enigma/a7bf493d-04b5-5828-bb09-9d8cecef37ad/scratchpad/hunt/ui
rm -rf "work_big/ws/我的声音"
/tmp/gsv39/bin/python setup.py ./work_big 1004 >/dev/null 2>&1
/tmp/gsv39/bin/python add_suspects.py ./work_big 2>&1 | tail -1
