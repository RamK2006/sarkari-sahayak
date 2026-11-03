import { CircleAlert, CircleCheck, CircleHelp, CircleX } from 'lucide-react';
import type { Status } from '@/lib/types';

const STYLE: Record<Status, { Icon: typeof CircleCheck; color: string }> = {
  eligible: { Icon: CircleCheck, color: 'text-ok' },
  potentially_eligible: { Icon: CircleAlert, color: 'text-warn' },
  insufficient_info: { Icon: CircleHelp, color: 'text-brand' },
  not_eligible: { Icon: CircleX, color: 'text-ink-faint' },
};

/** Status icon. Always rendered next to the status text, never as the only signal. */
export function StatusIcon({ status, className = 'h-5 w-5' }: { status: Status; className?: string }) {
  const { Icon, color } = STYLE[status];
  return <Icon aria-hidden className={`${className} shrink-0 ${color}`} />;
}
