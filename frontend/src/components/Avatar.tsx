'use client';

import { useEffect, useRef, useState, type CSSProperties, type MutableRefObject } from 'react';
import { lookFor, type AvatarLook } from '@/lib/avatars';
import { useI18n } from '@/lib/i18n';
import type { Gesture, Mood } from '@/lib/types';

export type AvatarState = 'idle' | 'listening' | 'processing' | 'speaking';

interface Props {
  language: string;
  state: AvatarState;
  mood: Mood;
  /** A new `key` replays the gesture for a few seconds. */
  gesture: { value: Gesture; key: number };
  /** Live audio level (0..1) while speaking, written every frame by the speech player. */
  level: MutableRefObject<number>;
  className?: string;
}

interface Pose {
  tilt: number;
  browY: number;
  browRot: number; // inner ends up (+) or down (-)
  browRaiseRight: number;
  smile: number;
  squint: number;
  gaze: [number, number];
}

/** Expression from what is really happening (listening, waiting, speaking) and the mood the assistant chose. */
function poseFor(state: AvatarState, mood: Mood): Pose {
  const base: Pose = { tilt: 0, browY: 0, browRot: 0, browRaiseRight: 0, smile: 4, squint: 1, gaze: [0, 0] };
  const byMood: Record<Mood, Partial<Pose>> = {
    neutral: {},
    happy: { smile: 9, squint: 0.8, browY: -1.5 },
    empathetic: { smile: 1, browRot: 9, browY: -1, tilt: -4 },
    serious: { smile: -1, browRot: -8, browY: 2.5 },
    thinking: { smile: 0, gaze: [3, -3], browRaiseRight: -4, tilt: 3 },
  };
  const pose = { ...base, ...byMood[mood] };
  if (state === 'listening') return { ...pose, tilt: -4.5, browY: Math.min(pose.browY, -2.5), gaze: [0, 0.5] };
  if (state === 'processing') return { ...pose, ...byMood.thinking, tilt: 3 };
  return pose;
}

const mouthClosed = (smile: number) => `M107 147 Q120 ${147 + smile} 133 147`;
const mouthOpen = (smile: number, level: number) => {
  const open = Math.min(1, level) * 11;
  return `M107 146 Q120 ${144 - smile * 0.15} 133 146 Q120 ${147 + open * 1.6} 107 146 Z`;
};

function Hands({ look, gesture }: { look: AvatarLook; gesture: Gesture }) {
  const skin = look.skin;
  const shade = 'rgba(0,0,0,0.12)';
  const hand = (visible: boolean): CSSProperties => ({
    opacity: visible ? 1 : 0,
    transform: visible ? 'translateY(0)' : 'translateY(14px)',
    transition: 'opacity 350ms ease, transform 350ms ease',
  });
  const greeting = gesture === 'namaste' ? look.greeting : null;
  return (
    <g aria-hidden>
      {/* palms together */}
      <g style={hand(greeting === 'palms')}>
        <path d="M120 200C109 211 108 232 115 248L125 248C132 232 131 211 120 200Z" fill={skin} />
        <path d="M120 204L120 246" stroke={shade} strokeWidth="1.6" />
        <rect x="108" y="244" width="24" height="9" rx="3" fill={look.trim} />
      </g>
      {/* right hand raised to the forehead */}
      <g style={hand(greeting === 'salaam')}>
        <ellipse cx="168" cy="104" rx="8" ry="15" transform="rotate(-22 168 104)" fill={skin} />
        <path d="M164 92L170 116M168 90L174 114" stroke={shade} strokeWidth="1.3" />
        <rect x="160" y="124" width="20" height="40" rx="9" transform="rotate(-8 170 144)" fill={look.top} />
      </g>
      {/* open palms offering help */}
      <g style={hand(gesture === 'open')}>
        <ellipse cx="56" cy="238" rx="13" ry="9" transform="rotate(-18 56 238)" fill={skin} />
        <ellipse cx="184" cy="238" rx="13" ry="9" transform="rotate(18 184 238)" fill={skin} />
        <rect x="38" y="246" width="14" height="44" rx="7" fill={look.top} />
        <rect x="188" y="246" width="14" height="44" rx="7" fill={look.top} />
      </g>
      {/* pointing to what is on screen */}
      <g style={hand(gesture === 'point')}>
        <rect x="176" y="168" width="9" height="32" rx="4.5" fill={skin} />
        <ellipse cx="183" cy="206" rx="13" ry="11" fill={skin} />
        <rect x="171" y="214" width="24" height="60" rx="11" fill={look.top} />
      </g>
    </g>
  );
}

function Hair({ look }: { look: AvatarLook }) {
  const c = look.hair;
  return (
    <>
      {look.hairStyle === 'long' && <path d="M76 124C70 52 170 52 164 124C168 164 178 196 170 224L146 218L146 134L94 134L94 218L70 224C62 196 72 164 76 124Z" fill={c} />}
      {look.hairStyle === 'braid' && (
        <>
          <path d="M78 122C74 56 166 56 162 122C164 150 160 170 156 186L84 186C80 170 76 150 78 122Z" fill={c} />
          <path d="M150 180C158 200 160 220 154 246C150 258 160 262 158 276" stroke={c} strokeWidth="13" strokeLinecap="round" fill="none" />
        </>
      )}
      {look.hairStyle === 'bun' && (
        <>
          <circle cx="120" cy="52" r="19" fill={c} />
          <path d="M78 124C74 60 166 60 162 124C164 146 158 160 152 168L88 168C82 160 76 146 78 124Z" fill={c} />
        </>
      )}
      {look.hairStyle === 'short' && <path d="M79 118C76 62 164 62 161 118L150 104L90 104Z" fill={c} />}
    </>
  );
}

function HairFront({ look }: { look: AvatarLook }) {
  if (look.headwear === 'turban') return null;
  return <path d="M80 116C76 58 164 56 160 116C156 98 144 84 126 79C112 94 92 102 80 116Z" fill={look.hair} />;
}

function Headwear({ look }: { look: AvatarLook }) {
  const c = look.headwearColor ?? '#e87a1e';
  if (look.headwear === 'turban')
    return (
      <g>
        <path d="M78 112C70 60 170 56 162 112C150 94 90 94 78 112Z" fill={c} />
        <path d="M82 100C108 82 134 82 158 100M80 90C106 70 138 70 160 90M86 80C110 64 134 64 154 80" stroke="rgba(0,0,0,0.18)" strokeWidth="2.2" fill="none" />
        <path d="M156 86C176 90 184 106 176 124C170 112 162 104 152 98Z" fill={c} />
      </g>
    );
  if (look.headwear === 'cap')
    return (
      <g>
        <path d="M82 96C84 66 156 66 158 96Z" fill={c} />
        <rect x="80" y="92" width="80" height="9" rx="4" fill="rgba(0,0,0,0.15)" />
      </g>
    );
  return null;
}

/**
 * Illustrated seated figure. Look (skin, attire, adornment, greeting) comes from the language's entry in
 * lib/avatars.ts. Motion maps to real activity: listening, waiting for a reply, speaking (mouth follows the
 * audio signal), plus the mood and gesture the assistant selected for its reply.
 */
export function Avatar({ language, state, mood, gesture, level, className }: Props) {
  const { t } = useI18n();
  const look = lookFor(language);
  const pose = poseFor(state, mood);
  const mouth = useRef<SVGPathElement>(null);
  const raf = useRef<number>();
  const [shown, setShown] = useState<Gesture>('none');

  // Show each requested gesture briefly, then lower the hands.
  useEffect(() => {
    if (gesture.value === 'none') return setShown('none');
    setShown(gesture.value);
    const timer = setTimeout(() => setShown('none'), 3800);
    return () => clearTimeout(timer);
  }, [gesture.key, gesture.value]);

  useEffect(() => {
    const el = mouth.current;
    if (!el) return;
    const closed = mouthClosed(pose.smile);
    if (state !== 'speaking') {
      el.setAttribute('d', closed);
      el.setAttribute('fill', 'none');
      return;
    }
    const tick = () => {
      const open = level.current > 0.06;
      el.setAttribute('d', open ? mouthOpen(pose.smile, level.current) : closed);
      el.setAttribute('fill', open ? '#5a2424' : 'none');
      raf.current = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(raf.current ?? 0);
  }, [state, level, pose.smile]);

  const move = (x: number, y: number): CSSProperties => ({ transform: `translate(${x}px, ${y}px)`, transition: 'transform 400ms ease' });
  const brow = (rot: number, raise: number): CSSProperties => ({
    transformBox: 'fill-box',
    transformOrigin: 'center',
    transform: `translateY(${pose.browY + raise}px) rotate(${rot}deg)`,
    transition: 'transform 400ms ease',
  });
  const label = t(`avatar.${state}`);

  return (
    <figure className={className} aria-label={label}>
      <svg viewBox="0 0 240 300" role="img" aria-hidden="true" className="block h-auto w-full">
        <circle cx="120" cy="150" r="116" fill={look.backdrop} opacity="0.9" />

        <g className="sa-breathe">
          <Hair look={look} />

          {/* shoulders and garment */}
          <path d="M14 300C14 246 46 214 96 200L144 200C194 214 226 246 226 300Z" fill={look.top} />
          <path d="M96 200L120 236L144 200" stroke={look.trim} strokeWidth="7" strokeLinejoin="round" fill="none" />
          <path d="M20 280C40 262 70 252 96 250" stroke={look.trim} strokeWidth="5" strokeLinecap="round" fill="none" opacity="0.7" />
          {look.scarf && <path d="M62 214C84 232 108 244 130 238C150 250 176 252 200 238L218 262C186 276 150 270 124 256C96 262 64 246 44 232Z" fill={look.scarf} opacity="0.95" />}

          <path d="M106 160L134 160L136 204C128 212 112 212 104 204Z" fill={look.skin} />
          <path d="M106 160L134 160L134 180C126 186 114 186 106 180Z" fill="rgba(0,0,0,0.12)" />

          <g style={{ transform: `rotate(${pose.tilt + (state === 'speaking' ? level.current * 1.5 : 0)}deg)`, transformOrigin: '120px 204px', transition: 'transform 450ms ease' }}>
            <ellipse cx="80" cy="124" rx="6" ry="10" fill={look.skin} />
            <ellipse cx="160" cy="124" rx="6" ry="10" fill={look.skin} />
            <ellipse cx="120" cy="120" rx="41" ry="46" fill={look.skin} />
            <ellipse cx="102" cy="140" rx="9" ry="6" fill="#e0866f" opacity="0.18" />
            <ellipse cx="138" cy="140" rx="9" ry="6" fill="#e0866f" opacity="0.18" />

            {/* brows */}
            <g style={brow(pose.browRot, 0)}>
              <path d="M92 106Q103 100 114 105" stroke={look.hair} strokeWidth="3.4" strokeLinecap="round" fill="none" />
            </g>
            <g style={brow(-pose.browRot, pose.browRaiseRight)}>
              <path d="M126 105Q137 100 148 106" stroke={look.hair} strokeWidth="3.4" strokeLinecap="round" fill="none" />
            </g>

            {/* eyes */}
            <g className="sa-blink" style={{ transform: `scaleY(${pose.squint})`, transformBox: 'fill-box', transformOrigin: 'center' }}>
              {[104, 136].map((cx) => (
                <g key={cx}>
                  <ellipse cx={cx} cy="123" rx="8.5" ry="9.5" fill="#ffffff" />
                  <g style={move(pose.gaze[0], pose.gaze[1])}>
                    <circle cx={cx} cy="123.5" r="5.6" fill="#3a2a22" />
                    <circle cx={cx} cy="123.5" r="2.7" fill="#0e0a09" />
                    <circle cx={cx + 2} cy="121" r="1.7" fill="#ffffff" />
                  </g>
                  <path d={`M${cx - 9} 121Q${cx} 112 ${cx + 9} 121`} stroke={look.hair} strokeWidth="2.4" fill="none" strokeLinecap="round" />
                </g>
              ))}
            </g>

            <path d="M120 128Q116 140 119 143Q122 145 125 143" stroke="rgba(0,0,0,0.28)" strokeWidth="1.8" fill="none" strokeLinecap="round" />
            {look.bindi && <circle cx="120" cy="100" r="3.2" fill={look.bindi} />}
            {look.mustache && <path d="M104 142Q112 137 120 141Q128 137 136 142Q128 147 120 144Q112 147 104 142Z" fill={look.hair} />}
            <path ref={mouth} d={mouthClosed(pose.smile)} stroke="#7e3f35" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" fill="none" />

            <HairFront look={look} />
            <Headwear look={look} />
          </g>

          <Hands look={look} gesture={shown} />
        </g>
      </svg>
      <figcaption className="sr-only" aria-live="polite">
        {label}
      </figcaption>
    </figure>
  );
}
