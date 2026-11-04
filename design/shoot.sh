#!/bin/bash
# Screenshot the design preview in light and dark (needs Google Chrome).
#   design/shoot.sh [en|fr]    -> design/screenshots/preview-{light,dark}[-fr].png
set -e
cd "$(dirname "$0")/.."
PORT=8765
# Bound to localhost: the repo root holds config.py, which must not be served
# to the network.
python3 -m http.server --bind 127.0.0.1 $PORT >/dev/null 2>&1 &
SERVER=$!
trap "kill $SERVER" EXIT
sleep 0.6
mkdir -p design/screenshots
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LANG=${1:-en}
SUFFIX=$([ "$LANG" = en ] && echo "" || echo "-$LANG")
for theme in light dark; do
  "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=1700,1200 --virtual-time-budget=20000 \
    --screenshot="design/screenshots/preview-$theme$SUFFIX.png" \
    "http://localhost:$PORT/design/preview.html?theme=$theme&lang=$LANG" 2>/dev/null
done
ls -la design/screenshots
