#!/bin/bash
# usage: run_bg.sh <viewerDir> <outDir> <camsFile> [w h]
cd /home/claude/aoki && harness/serve.sh > /dev/null
mkdir -p "$2"
nohup setsid node harness/shoot.mjs "$1" "$2" "$3" ${4:-1280} ${5:-800} > "$2/log.txt" 2>&1 < /dev/null &
echo "started pid $!"
