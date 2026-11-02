import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import events from "../public/raw/events.json";

// Raw clips come from design/record_video.py. Event times are logged from the
// moment screencapture is launched; the video starts ~0.15 s later.
const OFFSET = 0.15;
const FPS = 30;
const FONT = '-apple-system, "SF Pro Display", "Helvetica Neue", sans-serif';

const BLUE = "#0a84ff";
const INDIGO = "#5e5ce6";
const PURPLE = "#bf5af2";
const TEAL = "#30b0c7";

type Cam = { at: number; z: number; fx: number; fy: number };
type Caption = { at: number; text: string };
type Scene = {
  clip: "demo" | "menu";
  from: number; // source seconds
  to: number;
  rate?: number; // playback speed, only for typing
  color: string;
  cams: Cam[];
  captions: Caption[];
  waits?: { start: number; end: number }[]; // model at work: show a stopwatch
};

const CLIPS = {
  // demo: TextEdit window, 980×760 pt recorded at 2x; the empty bottom is cropped
  demo: { src: "raw/demo.mp4", w: 1960, h: 1520, cropX: 0, cropW: 1960, cropH: 1360, base: 1000 / 1360 },
  // menu: right side of the menu bar; the left part is cropped out
  menu: { src: "raw/menu.mp4", w: 2040, h: 600, cropX: 300, cropW: 1740, cropH: 600, base: 1700 / 1740 },
};

const WIDE: Omit<Cam, "at"> = { z: 1, fx: 980, fy: 680 };
// Panel on the right half, so captions on the left never cover it.
const PANEL: Omit<Cam, "at"> = { z: 1.35, fx: 62, fy: 880 };
const TEXT_LINE: Omit<Cam, "at"> = { z: 1.26, fx: 980, fy: 305 };

// Source times are events.json times minus OFFSET (see design/record_video.py).
const SCENES: Scene[] = [
  {
    clip: "demo", from: 0.6, to: 8.7, rate: 3, color: BLUE,
    cams: [{ at: 0.6, ...WIDE }],
    captions: [{ at: 0.6, text: "Write anywhere on your Mac." }],
  },
  {
    clip: "demo", from: 8.7, to: 21.0, color: BLUE,
    cams: [{ at: 8.7, ...WIDE }, { at: 9.4, ...PANEL }, { at: 19.8, ...TEXT_LINE }],
    captions: [
      { at: 8.7, text: "Select a whole message, press ⌥⌘G." },
      { at: 13.8, text: "13 mistakes found, each one labelled." },
      { at: 16.2, text: "Conjugation, agreement, homophones, spelling…" },
      { at: 19.8, text: "⌘↵ fixes them all in place." },
    ],
    waits: [{ start: 9.32, end: 13.78 }],
  },
  {
    clip: "demo", from: 25.9, to: 34.2, color: INDIGO,
    cams: [{ at: 25.9, ...PANEL }],
    captions: [
      { at: 25.9, text: "Already correct? It tells you." },
      { at: 28.15, text: "⌘2 · Pro rewrites it for work." },
    ],
    waits: [{ start: 28.16, end: 32.1 }],
  },
  {
    clip: "demo", from: 34.2, to: 45.0, color: PURPLE,
    cams: [{ at: 34.2, ...PANEL }, { at: 43.2, ...TEXT_LINE }],
    captions: [
      { at: 34.2, text: "⌘3 · Sur mesure: ask for anything." },
      { at: 36.6, text: "Here: “en anglais” (in English)." },
      { at: 43.2, text: "Translated and pasted back." },
    ],
    waits: [{ start: 36.62, end: 39.82 }],
  },
  {
    clip: "menu", from: 0.6, to: 8.6, color: TEAL,
    cams: [{ at: 0.6, z: 1, fx: 870, fy: 300 }, { at: 3.0, z: 1.2, fx: 930, fy: 300 }],
    captions: [
      { at: 0.6, text: "Recent corrections live in the menu bar." },
      { at: 5.5, text: "Click one to copy it again." },
    ],
  },
];

const KEYS = new Set(["⌘A", "⌥⌘G", "↵", "⌘2", "⌘3", "⌘↵"]);
const INTRO = 90;
const OUTRO = 120;
const sceneFrames = (s: Scene) => Math.round(((s.to - s.from) / (s.rate ?? 1)) * FPS);
export const TOTAL_FRAMES = INTRO + SCENES.reduce((n, s) => n + sceneFrames(s), 0) + OUTRO;

const ease = Easing.bezier(0.45, 0, 0.2, 1);
const MOVE = 0.8; // seconds per camera move

function camAt(cams: Cam[], t: number): Omit<Cam, "at"> {
  let cur = { z: cams[0].z, fx: cams[0].fx, fy: cams[0].fy };
  for (const k of cams.slice(1)) {
    const p = ease(Math.min(1, Math.max(0, (t - k.at) / MOVE)));
    cur = { z: cur.z + (k.z - cur.z) * p, fx: cur.fx + (k.fx - cur.fx) * p, fy: cur.fy + (k.fy - cur.fy) * p };
  }
  return cur;
}

// ── Background ─────────────────────────────────────────────────────────────
const Backdrop: React.FC<{ color: string; drift: number }> = ({ color, drift }) => (
  <AbsoluteFill style={{ background: "#07080c" }}>
    <AbsoluteFill
      style={{
        background: `radial-gradient(60% 70% at ${20 + drift * 10}% 15%, ${color}55, transparent 70%),
                     radial-gradient(50% 60% at ${85 - drift * 8}% 90%, ${color}33, transparent 70%)`,
      }}
    />
  </AbsoluteFill>
);

// ── Scene: a real clip with camera moves, captions and keys ────────────────
const ClipScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const dur = sceneFrames(scene);
  const rate = scene.rate ?? 1;
  const t = scene.from + (frame / FPS) * rate;
  const c = CLIPS[scene.clip];
  const cam = camAt(scene.cams, t);
  const s = c.base * cam.z;
  const fade = interpolate(frame, [0, 12, dur - 12, dur], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const enter = interpolate(frame, [0, 18], [0.96, 1], { extrapolateRight: "clamp", easing: ease });

  const caption = [...scene.captions].reverse().find((x) => t >= x.at);
  const captionAge = caption ? (t - caption.at) * FPS : 0;
  const keyEvents = events[scene.clip]
    .map((e) => ({ ...e, t: e.t - OFFSET }))
    .filter((e) => KEYS.has(e.label) && e.t >= scene.from && e.t < scene.to);
  const key = [...keyEvents].reverse().find((e) => t >= e.t && t < e.t + 1.1);

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Backdrop color={scene.color} drift={frame / dur} />
      <div
        style={{
          position: "absolute", left: 0, top: 0, width: c.cropW, height: c.cropH,
          transformOrigin: "0 0",
          transform: `translate(${960 - cam.fx * s * enter}px, ${520 - cam.fy * s * enter}px) scale(${s * enter})`,
          borderRadius: 26, overflow: "hidden",
          boxShadow: "0 50px 140px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.08)",
        }}
      >
        <OffthreadVideo
          src={staticFile(c.src)}
          trimBefore={Math.round(scene.from * FPS)}
          playbackRate={rate}
          muted
          style={{ position: "absolute", left: -c.cropX, top: 0, width: c.w, height: c.h }}
        />
        {scene.clip === "menu" && (
          // hide macOS's screen-recording indicator in the menu bar
          <div style={{ position: "absolute", left: 1508 - c.cropX, top: 4, width: 106, height: 58,
            background: "linear-gradient(rgb(32,109,167), rgb(34,111,170))" }} />
        )}
      </div>

      {caption && (
        <div
          style={{
            position: "absolute", left: 110, bottom: 84, maxWidth: 760, display: "flex", alignItems: "center", gap: 22,
            padding: "22px 34px", borderRadius: 26,
            background: "rgba(16,18,24,.72)", backdropFilter: "blur(24px)",
            boxShadow: "0 0 0 1px rgba(255,255,255,.1), 0 20px 60px rgba(0,0,0,.4)",
            opacity: interpolate(captionAge, [0, 8], [0, 1], { extrapolateRight: "clamp" }),
            transform: `translateY(${interpolate(captionAge, [0, 10], [16, 0], { extrapolateRight: "clamp", easing: ease })}px)`,
          }}
        >
          <span style={{ width: 16, height: 16, flexShrink: 0, borderRadius: 8, background: scene.color, boxShadow: `0 0 18px ${scene.color}` }} />
          <span style={{ fontFamily: FONT, fontSize: 44, fontWeight: 600, lineHeight: 1.2, color: "white", letterSpacing: -0.5 }}>{caption.text}</span>
        </div>
      )}

      {key && <KeyChip label={key.label} age={((t - key.t) * FPS) / rate} color={scene.color} />}
      {rate !== 1 && <Badge text={`Typing sped up ${rate}×`} />}
      {(scene.waits ?? []).map((w) =>
        t >= w.start && t < w.end + 1.6 ? (
          <Stopwatch key={w.start} seconds={Math.min(t, w.end) - w.start} done={t >= w.end}
            age={(t - w.start) * FPS} color={scene.color} />
        ) : null,
      )}
    </AbsoluteFill>
  );
};

const KeyChip: React.FC<{ label: string; age: number; color: string }> = ({ label, age, color }) => {
  const { fps } = useVideoConfig();
  const pop = spring({ frame: age, fps, config: { damping: 14, stiffness: 180 } });
  const out = interpolate(age, [24, 33], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute", right: 110, bottom: 84, minWidth: 140, padding: "18px 34px", borderRadius: 24,
        textAlign: "center", fontFamily: FONT, fontSize: 64, fontWeight: 600, color: "white",
        background: "rgba(255,255,255,.12)", backdropFilter: "blur(24px)",
        boxShadow: `0 0 0 2px ${color}, 0 0 50px ${color}88`,
        transform: `scale(${0.6 + 0.4 * pop})`, opacity: out,
      }}
    >
      {label}
    </div>
  );
};

// Real elapsed time while the local model works (the clips are not sped up).
const Stopwatch: React.FC<{ seconds: number; done: boolean; age: number; color: string }> = ({ seconds, done, age, color }) => {
  const appear = interpolate(age, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute", left: 110, top: 84, display: "flex", alignItems: "center", gap: 18,
        padding: "16px 28px", borderRadius: 24, fontFamily: FONT, color: "white",
        background: "rgba(16,18,24,.72)", backdropFilter: "blur(24px)",
        boxShadow: `0 0 0 1px rgba(255,255,255,.1), 0 0 40px ${done ? "#30d15855" : color + "44"}`,
        opacity: appear, transform: `translateY(${(1 - appear) * -12}px)`,
      }}
    >
      <span style={{ fontSize: 26, fontWeight: 500, color: "rgba(255,255,255,.7)" }}>
        {done ? "Done on this Mac" : "Gemma 4, on this Mac"}
      </span>
      <span style={{ fontSize: 44, fontWeight: 700, fontVariantNumeric: "tabular-nums", color: done ? "#30d158" : "white" }}>
        {seconds.toFixed(1)} s
      </span>
    </div>
  );
};

const Badge: React.FC<{ text: string }> = ({ text }) => (
  <div style={{ position: "absolute", right: 110, top: 84, padding: "14px 26px", borderRadius: 20, fontFamily: FONT,
    fontSize: 30, fontWeight: 600, color: "rgba(255,255,255,.85)", background: "rgba(16,18,24,.72)",
    boxShadow: "0 0 0 1px rgba(255,255,255,.12)" }}>
    ⏩ {text}
  </div>
);

// ── Title cards ────────────────────────────────────────────────────────────
const Glyph: React.FC<{ size: number }> = ({ size }) => (
  <div
    style={{
      width: size, height: size, borderRadius: size * 0.24, display: "grid", placeItems: "center",
      background: `linear-gradient(145deg, #3b9bff, ${BLUE} 55%, ${INDIGO})`,
      boxShadow: `0 20px 60px ${BLUE}66, inset 0 1px 0 rgba(255,255,255,.35)`,
    }}
  >
    <svg width={size * 0.5} height={size * 0.5} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20l4.2-1L19 8.2a2.1 2.1 0 0 0-3-3L5.2 16 4 20z" />
    </svg>
  </div>
);

const Title: React.FC<{ outro?: boolean }> = ({ outro }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const at = (d: number) => spring({ frame: frame - d, fps, config: { damping: 18, stiffness: 120 } });
  const fadeOut = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const fadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const rise = (d: number) => ({ opacity: at(d), transform: `translateY(${(1 - at(d)) * 30}px)` });
  const chips = outro
    ? ["Gemma 4 E2B via Ollama", "Runs offline", "Nothing leaves your Mac"]
    : ["Runs on your Mac", "Private by design", "Open source"];

  return (
    <AbsoluteFill style={{ opacity: outro ? fadeIn : fadeOut }}>
      <Backdrop color={outro ? PURPLE : BLUE} drift={frame / durationInFrames} />
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 34, fontFamily: FONT, color: "white" }}>
        <div style={{ ...rise(0), transform: `scale(${0.7 + 0.3 * at(0)})` }}><Glyph size={150} /></div>
        <div style={{ ...rise(6), fontSize: 120, fontWeight: 700, letterSpacing: -3 }}>TextPolish</div>
        <div style={{ ...rise(12), fontSize: 46, fontWeight: 500, color: "rgba(255,255,255,.75)" }}>
          {outro ? "Fix, rewrite or translate, in any Mac app." : "A writing assistant for every Mac app."}
        </div>
        <div style={{ ...rise(20), display: "flex", gap: 18, marginTop: 10 }}>
          {chips.map((c) => (
            <span key={c} style={{ fontSize: 30, fontWeight: 500, padding: "12px 26px", borderRadius: 999,
              background: "rgba(255,255,255,.08)", boxShadow: "0 0 0 1px rgba(255,255,255,.14)" }}>{c}</span>
          ))}
        </div>
        {outro && (
          <div style={{ ...rise(30), marginTop: 26, fontSize: 36, fontWeight: 500, color: "#9cc9ff" }}>
            github.com/Enguerrand-Roques/textpolish
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const TextPolishVideo: React.FC = () => {
  let start = INTRO;
  return (
    <AbsoluteFill style={{ background: "#07080c" }}>
      <Sequence durationInFrames={INTRO}><Title /></Sequence>
      {SCENES.map((scene, i) => {
        const from = start;
        start += sceneFrames(scene);
        return (
          <Sequence key={i} from={from} durationInFrames={sceneFrames(scene)}>
            <ClipScene scene={scene} />
          </Sequence>
        );
      })}
      <Sequence from={start} durationInFrames={OUTRO}><Title outro /></Sequence>
    </AbsoluteFill>
  );
};
