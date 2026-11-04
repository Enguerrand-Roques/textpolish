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
type ClipName = "demo" | "menu" | "langMenu" | "langWin";
type Scene = {
  clip: ClipName;
  from: number; // source seconds
  to: number;
  rate?: number; // playback speed, only for typing (with a badge)
  color: string;
  cams: Cam[];
  captions: Caption[];
  waits?: { start: number; end: number }[]; // model at work: show a stopwatch
};

type Clip = {
  src: string; w: number; h: number; cropX: number; cropW: number; cropH: number; base: number;
  events: "demo" | "menu" | "lang";
  patches?: { left: number; width: number; height: number; top?: number; color?: string }[]; // areas to paint over
};
const BAR = "linear-gradient(rgb(32,109,167), rgb(34,111,170))";
const TITLE_BAR = "#25292b";
const CLIPS: Record<ClipName, Clip> = {
  // demo: TextEdit window, 980×760 pt recorded at 2x; the empty bottom is cropped
  // TextEdit says "— Modifié" (French system) after the file name: painted over
  demo: { src: "raw/demo.mp4", w: 1960, h: 1520, cropX: 0, cropW: 1960, cropH: 1360, base: 1000 / 1360, events: "demo",
          patches: [{ left: 366, top: 10, width: 150, height: 46, color: TITLE_BAR }] },
  // menu: right side of the menu bar; hide TextEdit's (French) menus and the recording indicator
  menu: { src: "raw/menu.mp4", w: 2040, h: 600, cropX: 300, cropW: 1740, cropH: 600, base: 1700 / 1740, events: "menu",
          patches: [{ left: 0, width: 1612 - 300, height: 62 },
                    { left: 0, top: 204, width: 110, height: 56, color: "#1f2325" }] }, // "…ge.txt" title
  // lang: screen from the TextEdit window's left edge to the right edge, menu bar included
  langMenu: { src: "raw/lang.mp4", w: 2640, h: 1520, cropX: 1480, cropW: 680, cropH: 320, base: 1.4, events: "lang",
              patches: [{ left: 20, width: 100, height: 62 }] }, // recording indicator
  langWin: { src: "raw/lang.mp4", w: 2640, h: 1520, cropX: 0, cropW: 1960, cropH: 1520, base: 1000 / 1360, events: "lang",
             patches: [{ left: 366, top: 210, width: 150, height: 46, color: TITLE_BAR }] },
};

const WIDE: Omit<Cam, "at"> = { z: 1, fx: 980, fy: 680 };
// Panel on the right half, so captions on the left never cover it.
const PANEL: Omit<Cam, "at"> = { z: 1.35, fx: 62, fy: 880 };
const TEXT_LINE: Omit<Cam, "at"> = { z: 1.26, fx: 980, fy: 305 };

// Source times are events.json times minus OFFSET (see design/record_video.py).
const SCENES: Scene[] = [
  {
    clip: "demo", from: 0.6, to: 8.35, rate: 3, color: BLUE,
    cams: [{ at: 0.6, ...WIDE }],
    captions: [{ at: 0.6, text: "Write anywhere on your Mac." }],
  },
  {
    // the stopwatch starts when the text reaches the model (log: 3,516 ms)
    clip: "demo", from: 8.35, to: 20.3, color: BLUE,
    cams: [{ at: 8.35, ...WIDE }, { at: 9.0, ...PANEL }, { at: 18.6, ...TEXT_LINE }],
    captions: [
      { at: 8.35, text: "Select the text, press ⌥⌘G." },
      { at: 13.15, text: "11 mistakes found and labeled." },
      { at: 15.4, text: "Grammar, agreement, conjugation, spelling…" },
      { at: 18.1, text: "⌘↵ fixes them all in place." },
    ],
    waits: [{ start: 9.64, end: 13.155 }],
  },
  {
    clip: "demo", from: 26.3, to: 33.9, color: INDIGO,
    cams: [{ at: 26.3, ...PANEL }],
    captions: [
      { at: 26.3, text: "Already correct? It tells you." },
      { at: 28.2, text: "⌘2 · Pro rewrites it for work." },
    ],
    waits: [{ start: 28.25, end: 31.45 }],
  },
  {
    clip: "demo", from: 33.9, to: 45.0, color: PURPLE,
    cams: [{ at: 33.9, ...PANEL }, { at: 42.6, ...TEXT_LINE }],
    captions: [
      { at: 33.9, text: "⌘3 · Custom: ask for anything." },
      { at: 36.19, text: "Here: “translate into French”." },
      { at: 42.4, text: "Translated and pasted back." },
    ],
    waits: [{ start: 36.22, end: 39.99 }],
  },
  {
    clip: "menu", from: 0.6, to: 7.0, color: TEAL,
    cams: [{ at: 0.6, z: 1, fx: 870, fy: 300 }, { at: 3.0, z: 1.2, fx: 930, fy: 300 }],
    captions: [
      { at: 0.6, text: "Recent results live in the menu bar." },
      { at: 5.4, text: "Click one to copy it again." },
    ],
  },
  {
    clip: "langMenu", from: 0.6, to: 5.6, color: TEAL,
    cams: [{ at: 0.6, z: 1, fx: 390, fy: 160 }],
    captions: [
      { at: 0.6, text: "Prefer French? Switch from the menu bar." },
      { at: 4.2, text: "English or Français, remembered next time." },
    ],
  },
  {
    // the stopwatch starts when the text reaches the model (log: 3,287 ms)
    clip: "langWin", from: 6.4, to: 16.0, color: BLUE,
    cams: [{ at: 6.4, z: 1.55, fx: 820, fy: 690 }, { at: 8.3, ...PANEL, fy: 900 }],
    captions: [
      { at: 6.4, text: "Now a message in French." },
      { at: 11.77, text: "Same app in French: 13 fixes, each labeled." },
    ],
    waits: [{ start: 8.48, end: 11.77 }],
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
  const keyEvents = events[c.events]
    .map((e) => ({ ...e, t: e.t - OFFSET }))
    .filter((e) => KEYS.has(e.label) && e.t >= scene.from && e.t < scene.to);
  const key = [...keyEvents].reverse().find((e) => t >= e.t && t < e.t + 1.1);

  return (
    <AbsoluteFill style={{ opacity: fade }}>
      <Backdrop color={scene.color} drift={(t / 40) % 1} />
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
        {(c.patches ?? []).map((p, i) => (
          <div key={i} style={{ position: "absolute", left: p.left, top: p.top ?? 0, width: p.width, height: p.height, background: p.color ?? BAR }} />
        ))}
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
      {rate !== 1 && <Badge text={`Typing sped up ${rate}×`} under={!!scene.waits} />}
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

// Under the stopwatch when there is one, else bottom right (clear of the window).
const Badge: React.FC<{ text: string; under: boolean }> = ({ text, under }) => (
  <div style={{ position: "absolute", ...(under ? { left: 110, top: 176 } : { right: 110, bottom: 96 }), padding: "14px 26px", borderRadius: 20, fontFamily: FONT,
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
