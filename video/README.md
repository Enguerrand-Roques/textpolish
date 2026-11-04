# TextPolish video

The 1-minute montage in `docs/textpolish-demo.mp4`, built with [Remotion](https://www.remotion.dev/) from real recordings of the app: the English interface, the history menu, then the switch to French.

1. Film the raw clips (the app must be running, log in `design/app.log`; don't touch the keyboard or mouse for ~1 min 30):

   ```bash
   venv/bin/python3 design/record_video.py video/public/raw
   (cd video/public/raw && for f in demo menu lang; do ffmpeg -i $f.mov -r 30 -c:v libx264 -crf 14 -pix_fmt yuv420p -an $f.mp4; done)
   ```

2. Preview and render:

   ```bash
   cd video && npm install
   npm run studio   # live preview
   npm run render   # out/textpolish.mp4
   ```

3. Encode the web copy (about 5 MB) and the short loop used by the case study:

   ```bash
   ffmpeg -i video/out/textpolish.mp4 -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -movflags +faststart -an docs/textpolish-demo.mp4
   ```

Scene timings, captions and camera moves are in `src/Video.tsx`; key presses come from `public/raw/events.json`, written by the recorder. The raw clips are not committed (they show the desktop).
