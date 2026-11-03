'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';

/**
 * Plays text through Sarvam text-to-speech. While audio plays, an analyser reads the real signal so the
 * avatar's mouth follows the actual speech. `level` is a ref (0..1) updated every frame; `speaking`
 * is state and changes only when playback starts or ends.
 */
export function useSpeech(onError: () => void) {
  const [speaking, setSpeaking] = useState(false);
  const level = useRef(0);
  const audioEl = useRef<HTMLAudioElement | null>(null);
  const ctx = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const raf = useRef<number>();
  const url = useRef<string | null>(null);
  const token = useRef(0);
  const cache = useRef(new Map<string, Blob>());
  const onErr = useRef(onError);
  onErr.current = onError;

  const stop = useCallback(() => {
    token.current++;
    cancelAnimationFrame(raf.current ?? 0);
    audioEl.current?.pause();
    if (url.current) URL.revokeObjectURL(url.current);
    url.current = null;
    level.current = 0;
    setSpeaking(false);
  }, []);

  const speak = useCallback(
    async (text: string, language: string) => {
      stop();
      const mine = token.current;
      const key = `${language}:${text}`;
      let blob = cache.current.get(key);
      try {
        if (!blob) {
          blob = await api.speak(text, language);
          if (cache.current.size > 40) cache.current.clear();
          cache.current.set(key, blob);
        }
      } catch {
        if (mine === token.current) onErr.current();
        return;
      }
      if (mine !== token.current) return; // superseded by a newer request or stopped

      const el = (audioEl.current ??= new Audio());
      url.current = URL.createObjectURL(blob);
      el.src = url.current;

      if (!ctx.current) {
        const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        ctx.current = new AC();
        analyser.current = ctx.current.createAnalyser();
        analyser.current.fftSize = 512;
        ctx.current.createMediaElementSource(el).connect(analyser.current);
        analyser.current.connect(ctx.current.destination);
      }
      await ctx.current.resume();

      const data = new Uint8Array(analyser.current!.fftSize);
      const tick = () => {
        analyser.current!.getByteTimeDomainData(data);
        let sum = 0;
        for (const v of data) sum += (v - 128) * (v - 128);
        const rms = Math.sqrt(sum / data.length) / 128;
        level.current = Math.min(1, rms * 4);
        raf.current = requestAnimationFrame(tick);
      };
      el.onended = () => {
        if (mine === token.current) stop();
      };
      try {
        await el.play();
        setSpeaking(true);
        tick();
      } catch {
        if (mine === token.current) onErr.current();
        stop();
      }
    },
    [stop],
  );

  useEffect(() => () => stop(), [stop]);

  return { speak, stop, speaking, level };
}
