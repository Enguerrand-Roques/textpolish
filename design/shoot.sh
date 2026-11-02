#!/bin/bash
# Screenshot the design preview in light and dark (needs Google Chrome).
#   design/shoot.sh            -> design/screenshots/preview-{light,dark}.png
set -e
cd "$(dirname "$0")/.."
PORT=8765
python3 -m http.server $PORT >/dev/null 2>&1 &
SERVER=$!
trap "kill $SERVER" EXIT
sleep 0.6
mkdir -p design/screenshots
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for theme in light dark; do
  "$CHROME" --headless=new --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=1700,1450 --virtual-time-budget=4000 \
    --screenshot="design/screenshots/preview-$theme.png" \
    "http://localhost:$PORT/design/preview.html?theme=$theme" 2>/dev/null
done
ls -la design/screenshots
