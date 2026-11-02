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
  color: string;
  cams: Cam[];
  captions: Caption[];
};

const CLIPS = {
  // demo: TextEdit window, 900×520 pt recorded at 2x
  demo: { src: "raw/demo.mp4", w: 1800, h: 1040, cropX: 0, cropW: 1800, cropH: 1040, base: 1500 / 1800 },
  // menu: right side of the menu bar; the left part is cropped out
  menu: { src: "raw/menu.mp4", w: 2040, h: 600, cropX: 300, cropW: 1740, cropH: 600, base: 1700 / 1740 },
};

const WIDE: Omit<Cam, "at"> = { z: 1, fx: 900, fy: 520 };
const PANEL: Omit<Cam, "at"> = { z: 1.5, fx: 395, fy: 590 };
const TEXT_LINE: Omit<Cam, "at"> = { z: 1.45, fx: 690, fy: 232 };

const SCENES: Scene[] = [
  {
    clip: "demo", from: 0.6, to: 11.9, color: BLUE,
    cams: [{ at: 0.6, ...WIDE }, { at: 4.1, ...PANEL }, { at: 10.7, ...TEXT_LINE }],
    captions: [
      { at: 0.6, text: "Write anywhere on your Mac." },
      { at: 4.0, text: "Select the text, press ⌥⌘G." },
      { at: 6.1, text: "One card per mistake. ↵ to accept." },
      { at: 10.65, text: "Fixed, right where you typed." },
    ],
  },
  {
    clip: "demo", from: 11.9, to: 20.2, color: INDIGO,
    cams: [{ at: 11.9, ...TEXT_LINE }, { at: 12.75, ...PANEL }],
    captions: [
      { at: 11.9, text: "Already correct?" },
      { at: 14.75, text: "Nothing to fix. Want more?" },
      { at: 16.55, text: "⌘2 · Pro rewrites it for work." },
    ],
  },
  {
    clip: "demo", from: 20.2, to: 27.9, color: PURPLE,
    cams: [{ at: 20.2, ...PANEL, fy: 605 }, { at: 26.6, ...TEXT_LINE }],
    captions: [
      { at: 20.2, text: "⌘3 · Sur mesure: ask for anything." },
      { at: 23.2, text: "Here: “en anglais” (in English)." },
      { at: 26.6, text: "Translated and pasted back." },
    ],
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
const sceneFrames = (s: Scene) => Math.round((s.to - s.from) * FPS);
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
  const t = scene.from + frame / FPS;
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
            position: "absolute", left: 110, bottom: 84, display: "flex", alignItems: "center", gap: 22,
            padding: "22px 34px", borderRadius: 26,
            background: "rgba(16,18,24,.72)", backdropFilter: "blur(24px)",
            boxShadow: "0 0 0 1px rgba(255,255,255,.1), 0 20px 60px rgba(0,0,0,.4)",
            opacity: interpolate(captionAge, [0, 8], [0, 1], { extrapolateRight: "clamp" }),
            transform: `translateY(${interpolate(captionAge, [0, 10], [16, 0], { extrapolateRight: "clamp", easing: ease })}px)`,
          }}
        >
          <span style={{ width: 16, height: 16, borderRadius: 8, background: scene.color, boxShadow: `0 0 18px ${scene.color}` }} />
          <span style={{ fontFamily: FONT, fontSize: 46, fontWeight: 600, color: "white", letterSpacing: -0.5 }}>{caption.text}</span>
        </div>
      )}

      {key && <KeyChip label={key.label} age={(t - key.t) * FPS} color={scene.color} />}
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
    ? ["Gemma 4 E2B via Ollama", "0.5–1 s per fix, model loaded", "Nothing leaves your Mac"]
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
