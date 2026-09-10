#!/bin/bash
# (re)start the local static server if it is not answering
if ! curl -s -o /dev/null -m 2 http://127.0.0.1:8000/; then
  cd /home/claude/aoki && nohup setsid python3 -m http.server 8000 --bind 127.0.0.1 > /tmp/http.log 2>&1 < /dev/null &
  sleep 1.5
fi
curl -s -o /dev/null -w "server %{http_code}\n" http://127.0.0.1:8000/
