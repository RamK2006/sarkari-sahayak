'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type RecorderState = 'idle' | 'recording';

const MAX_MS = 60_000;

const pickMime = () => {
  if (typeof MediaRecorder === 'undefined') return undefined;
  return ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'].find((m) =>
    MediaRecorder.isTypeSupported(m),
  );
};

export const recordingSupported = () =>
  typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined';

/** Records microphone audio. `onFinish` receives the recording when the user stops (or after 60 s). */
export function useRecorder(onFinish: (audio: Blob) => void, onError: (code: 'mic_denied' | 'mic_unsupported') => void) {
  const [state, setState] = useState<RecorderState>('idle');
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const finish = useRef(onFinish);
  finish.current = onFinish;

  const stop = useCallback(() => {
    clearTimeout(timer.current);
    if (recorder.current && recorder.current.state !== 'inactive') recorder.current.stop();
  }, []);

  const start = useCallback(async () => {
    if (!recordingSupported()) return onError('mic_unsupported');
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      return onError('mic_denied');
    }
    const mimeType = pickMime();
    const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    chunks.current = [];
    rec.ondataavailable = (e) => e.data.size > 0 && chunks.current.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      setState('idle');
      const blob = new Blob(chunks.current, { type: rec.mimeType || mimeType || 'audio/webm' });
      if (blob.size > 0) finish.current(blob);
    };
    recorder.current = rec;
    rec.start();
    setState('recording');
    timer.current = setTimeout(stop, MAX_MS);
  }, [onError, stop]);

  useEffect(() => () => stop(), [stop]);

  return { state, start, stop };
}
