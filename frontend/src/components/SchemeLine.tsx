'use client';

import Link from 'next/link';
import { ChevronRight } from 'lucide-react';
import { StatusIcon } from '@/components/StatusMark';
import { useI18n } from '@/lib/i18n';
import type { SchemeBrief, Status } from '@/lib/types';

/** One scheme as a list row: name, issuer, benefit, and (optionally) its status and missing information. */
export function SchemeLine({ scheme, status, missing }: { scheme: SchemeBrief; status?: Status; missing?: string[] }) {
  const { t } = useI18n();
  return (
    <Link href={`/schemes/${scheme.id}`} className="group flex items-start justify-between gap-4 py-4 hover:bg-brand-soft/60 sm:px-2">
      <div className="min-w-0">
        <h3 className="text-base font-semibold text-brand group-hover:underline">{scheme.name}</h3>
        <p className="mt-0.5 text-sm text-ink-faint">{scheme.ministry}</p>
        <p className="mt-2 text-ink-muted">{scheme.benefits}</p>
        {status && (
          <p className="mt-2 flex items-center gap-2 text-sm font-medium">
            <StatusIcon status={status} className="h-4 w-4" />
            {t(`status.${status}`)}
          </p>
        )}
        {missing && missing.length > 0 && (
          <p className="mt-1 text-sm text-ink-muted">{t('results.needs', { fields: missing.map((f) => t(`field.${f}`)).join(', ') })}</p>
        )}
      </div>
      <span className="mt-1 flex shrink-0 items-center gap-1 text-sm font-medium text-brand">
        <span className="hidden sm:inline">{t('results.view')}</span>
        <ChevronRight aria-hidden className="h-5 w-5" />
      </span>
    </Link>
  );
}
