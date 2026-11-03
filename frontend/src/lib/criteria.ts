'use client';

import { useI18n } from './i18n';
import type { CriterionItem, Status } from './types';

// Which option group labels a criterion's enum parameters.
const OPTION_GROUP: Record<string, string> = {
  gender: 'gender',
  area: 'area',
  occupation_in: 'occupation',
  category_in: 'category',
};

/** Renders a criterion outcome as a sentence in the selected language. */
export function useCriterionText() {
  const { t, formatNumber } = useI18n();
  return (item: CriterionItem): string => {
    if (item.criterion === 'verify') return t(`verify.${String(item.params.code)}`);

    const group = OPTION_GROUP[item.criterion];
    const params: Record<string, string | number> = {};
    for (const [k, v] of Object.entries(item.params)) {
      if (Array.isArray(v)) params[k] = v.map((x) => t(`opt.${group}.${x}`)).join(', ');
      else if (typeof v === 'number') params[k] = formatNumber(v);
      else if (k === 'value' && group) params[k] = t(`opt.${group}.${String(v)}`);
      else if (k === 'category') params[k] = t(`opt.category.${String(v)}`);
      else params[k] = String(v);
    }
    return t(`criteria.${item.criterion}.${item.outcome}`, params);
  };
}

export const STATUS_ORDER: Status[] = ['eligible', 'potentially_eligible', 'insufficient_info', 'not_eligible'];
