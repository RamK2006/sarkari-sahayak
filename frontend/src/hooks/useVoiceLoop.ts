'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type Phase = 'off' | 'listening' | 'capturing' | 'processing' | 'speaking';

interface Options {
  /** Called with each finished utterance. The phase is 'processing' until this resolves. */
  onUtterance: (audio: Blob) => Promise<void>;
  /** Called when the citizen starts talking over the assistant. */
  onBargeIn: () => void;
  onError: (code: 'mic_denied' | 'mic_unsupported') => void;
}

// Thresholds on normalised RMS (0..1). Barge-in is higher so the assistant's own voice is not mistaken for the user.
const SPEECH = 0.035;
const BARGE = 0.1;
const ONSET_MS = 90;
const BARGE_MS = 350;
const SILENCE_MS = 1100;
const MIN_UTTERANCE_MS = 450;
const MAX_UTTERANCE_MS = 40_000;

const pickMime = () =>
  typeof MediaRecorder === 'undefined'
    ? undefined
    : ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'].find((m) => MediaRecorder.isTypeSupported(m));

export const voiceSupported = () =>
  typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined';

/**
 * Hands-free conversation: listens continuously, detects when the citizen starts and stops speaking, hands each
 * utterance over, and goes back to listening. While the assistant speaks, louder speech interrupts it.
 */
export function useVoiceLoop(opts: Options) {
  const [phase, setPhaseState] = useState<Phase>('off');
  const phaseRef = useRef<Phase>('off');
  const optsRef = useRef(opts);
  optsRef.current = opts;

  const stream = useRef<MediaStream | null>(null);
  const ctx = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const raf = useRef<number>();
  const onset = useRef(0);
  const lastVoice = useRef(0);
  const startedAt = useRef(0);

  const setPhase = useCallback((p: Phase) => {
    phaseRef.current = p;
    setPhaseState(p);
  }, []);

  const beginCapture = useCallback(() => {
    if (!stream.current) return;
    const mimeType = pickMime();
    const rec = new MediaRecorder(stream.current, mimeType ? { mimeType } : undefined);
    chunks.current = [];
    rec.ondataavailable = (e) => e.data.size > 0 && chunks.current.push(e.data);
    rec.start();
    recorder.current = rec;
    startedAt.current = performance.now();
    lastVoice.current = performance.now();
    setPhase('capturing');
  }, [setPhase]);

  const endCapture = useCallback(() => {
    const rec = recorder.current;
    if (!rec || rec.state === 'inactive') return;
    const duration = performance.now() - startedAt.current;
    rec.onstop = async () => {
      const blob = new Blob(chunks.current, { type: rec.mimeType || 'audio/webm' });
      if (phaseRef.current === 'off') return;
      if (duration < MIN_UTTERANCE_MS || blob.size < 1500) {
        setPhase('listening');
        return;
      }
      setPhase('processing');
      try {
        await optsRef.current.onUtterance(blob);
      } finally {
        if (phaseRef.current === 'processing') setPhase('listening');
      }
    };
    rec.stop();
  }, [setPhase]);

  const loop = useCallback(() => {
    const node = analyser.current;
    if (!node) return;
    const data = new Uint8Array(node.fftSize);
    node.getByteTimeDomainData(data);
    let sum = 0;
    for (const v of data) sum += (v - 128) * (v - 128);
    const rms = Math.sqrt(sum / data.length) / 128;
    const now = performance.now();
    const p = phaseRef.current;

    if (p === 'listening') {
      if (rms > SPEECH) {
        onset.current ||= now;
        if (now - onset.current > ONSET_MS) {
          onset.current = 0;
          beginCapture();
        }
      } else onset.current = 0;
    } else if (p === 'capturing') {
      if (rms > SPEECH) lastVoice.current = now;
      if (now - lastVoice.current > SILENCE_MS || now - startedAt.current > MAX_UTTERANCE_MS) endCapture();
    } else if (p === 'speaking') {
      if (rms > BARGE) {
        onset.current ||= now;
        if (now - onset.current > BARGE_MS) {
          onset.current = 0;
          optsRef.current.onBargeIn();
          beginCapture();
        }
      } else onset.current = 0;
    } else onset.current = 0;

    raf.current = requestAnimationFrame(loop);
  }, [beginCapture, endCapture]);

  const stop = useCallback(() => {
    cancelAnimationFrame(raf.current ?? 0);
    setPhase('off');
    if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop();
    stream.current?.getTracks().forEach((t) => t.stop());
    stream.current = null;
    ctx.current?.close().catch(() => undefined);
    ctx.current = null;
    analyser.current = null;
  }, [setPhase]);

  const start = useCallback(async () => {
    if (!voiceSupported()) return optsRef.current.onError('mic_unsupported');
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
    } catch {
      return optsRef.current.onError('mic_denied');
    }
    const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    ctx.current = new AC();
    analyser.current = ctx.current.createAnalyser();
    analyser.current.fftSize = 1024;
    ctx.current.createMediaStreamSource(stream.current).connect(analyser.current);
    setPhase('listening');
    raf.current = requestAnimationFrame(loop);
  }, [loop, setPhase]);

  useEffect(() => () => stop(), [stop]);

  return { phase, phaseRef, start, stop, setPhase };
}
