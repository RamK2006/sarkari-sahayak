'use client';

import { useEffect, useRef, type MutableRefObject } from 'react';
import { useI18n } from '@/lib/i18n';

export type AvatarState = 'idle' | 'listening' | 'processing' | 'speaking';

interface Props {
  state: AvatarState;
  /** Live audio level (0..1) while speaking, written every frame by the speech player. */
  level: MutableRefObject<number>;
  className?: string;
}

const TILT: Record<AvatarState, number> = { idle: 0, listening: -3, processing: 2.5, speaking: 0 };
const GAZE: Record<AvatarState, [number, number]> = {
  idle: [0, 0],
  listening: [0, 0.4],
  processing: [-1.6, -1.8],
  speaking: [0, 0],
};
const BROW_LIFT: Record<AvatarState, number> = { idle: 0, listening: -2.5, processing: -1.5, speaking: -0.5 };

const CLOSED_MOUTH = 'M91 143 Q100 147.5 109 143';

/** Mouth shape for an audio level: upper lip stays, lower lip drops with the signal. */
function mouthPath(level: number): string {
  const open = Math.min(1, level) * 9;
  if (open < 0.6) return CLOSED_MOUTH;
  return `M91 142.5 Q100 140.5 109 142.5 Q100 ${143 + open * 1.5} 91 142.5 Z`;
}

/**
 * Seated figure anchored to the bottom edge of the conversation. Every motion maps to real activity:
 * recording (listening), a pending request (processing), or audio playing (speaking, with the mouth
 * driven by the actual audio signal).
 */
export function Avatar({ state, level, className }: Props) {
  const { t } = useI18n();
  const mouth = useRef<SVGPathElement>(null);
  const raf = useRef<number>();

  useEffect(() => {
    const el = mouth.current;
    if (!el) return;
    if (state !== 'speaking') {
      el.setAttribute('d', CLOSED_MOUTH);
      el.setAttribute('fill', 'none');
      return;
    }
    const tick = () => {
      const d = mouthPath(level.current);
      el.setAttribute('d', d);
      el.setAttribute('fill', d === CLOSED_MOUTH ? 'none' : '#4a2323');
      raf.current = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(raf.current ?? 0);
  }, [state, level]);

  const [gx, gy] = GAZE[state];
  const label = t(`avatar.${state}`);

  return (
    <figure className={className} aria-label={label}>
      <svg viewBox="0 0 200 260" role="img" aria-hidden="true" className="block h-auto w-full">
        <defs>
          <linearGradient id="av-skin" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#d6a583" />
            <stop offset="1" stopColor="#b9825f" />
          </linearGradient>
          <linearGradient id="av-blazer" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#2d4366" />
            <stop offset="1" stopColor="#1b2b47" />
          </linearGradient>
        </defs>

        <g className="sa-breathe">
          {/* hair behind the shoulders */}
          <path d="M52 112C50 56 150 56 148 112C150 152 160 186 152 212L128 206L128 124L72 124L72 206L48 212C40 186 50 152 52 112Z" fill="#1d1815" />

          {/* blazer */}
          <path d="M6 262C6 218 34 198 76 190L124 190C166 198 194 218 194 262Z" fill="url(#av-blazer)" />
          {/* shirt */}
          <path d="M76 190L100 238L124 190Z" fill="#eef2f7" />
          {/* lapels */}
          <path d="M76 190L98 232L82 246L54 206Z" fill="#243858" />
          <path d="M124 190L102 232L118 246L146 206Z" fill="#243858" />

          {/* neck */}
          <path d="M86 150L114 150L116 194C108 202 92 202 84 194Z" fill="#b98462" />
          <path d="M86 150L114 150L114 168C106 174 94 174 86 168Z" fill="#a67352" opacity="0.55" />

          {/* head, tilting with state */}
          <g
            style={{
              transform: `rotate(${TILT[state]}deg)`,
              transformOrigin: '100px 192px',
              transition: 'transform 500ms ease',
            }}
          >
            <ellipse cx="62.5" cy="114" rx="5" ry="9" fill="#b98462" />
            <ellipse cx="137.5" cy="114" rx="5" ry="9" fill="#b98462" />
            <path d="M63 106C63 70 137 70 137 106C137 139 120 160 100 160C80 160 63 139 63 106Z" fill="url(#av-skin)" />
            <circle cx="79" cy="127" r="7" fill="#d98c7a" opacity="0.13" />
            <circle cx="121" cy="127" r="7" fill="#d98c7a" opacity="0.13" />

            {/* brows */}
            <g style={{ transform: `translateY(${BROW_LIFT[state]}px)`, transition: 'transform 400ms ease' }}>
              <path d="M77 98Q86 93 95 97" stroke="#1d1815" strokeWidth="2.6" strokeLinecap="round" fill="none" />
              <path d="M105 97Q114 93 123 98" stroke="#1d1815" strokeWidth="2.6" strokeLinecap="round" fill="none" />
            </g>

            {/* eyes */}
            <g className="sa-blink">
              {[86, 114].map((cx) => (
                <g key={cx}>
                  <ellipse cx={cx} cy="108" rx="6.6" ry="4.3" fill="#fbfbfb" />
                  <g style={{ transform: `translate(${gx}px, ${gy}px)`, transition: 'transform 400ms ease' }}>
                    <circle cx={cx} cy="108" r="3.3" fill="#3b2a20" />
                    <circle cx={cx} cy="108" r="1.5" fill="#0d0a09" />
                    <circle cx={cx + 1.1} cy="106.8" r="0.8" fill="#ffffff" />
                  </g>
                  <path d={`M${cx - 6.8} 107.6Q${cx} 102.8 ${cx + 6.8} 107.6`} stroke="#1d1815" strokeWidth="1.7" fill="none" strokeLinecap="round" />
                </g>
              ))}
            </g>

            {/* nose */}
            <path d="M100 112Q96 126 99 129Q101.5 131 105 129" stroke="#9a6747" strokeWidth="1.6" fill="none" strokeLinecap="round" opacity="0.65" />

            {/* mouth */}
            <path ref={mouth} d={CLOSED_MOUTH} stroke="#7e4337" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" fill="none" />

            {/* hair in front, side parted */}
            <path d="M60 110C55 58 145 54 140 110C136 93 126 80 106 75C92 90 72 99 60 110Z" fill="#1d1815" />
          </g>
        </g>
      </svg>
      <figcaption className="sr-only text-center text-sm text-ink-muted md:not-sr-only md:mt-2" aria-live="polite">
        {label}
      </figcaption>
    </figure>
  );
}
