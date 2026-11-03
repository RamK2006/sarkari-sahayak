/**
 * Avatar looks, one per language, as data. The component draws whatever the look describes, so adding or
 * changing a region means editing this table only. Looks are regional suggestions (attire, adornment,
 * greeting), not a claim that everyone who speaks a language dresses this way.
 */
export type Greeting = 'palms' | 'salaam';
export type Headwear = 'none' | 'turban' | 'cap';
export type HairStyle = 'long' | 'bun' | 'braid' | 'short';

export interface AvatarLook {
  skin: string;
  hair: string;
  hairStyle: HairStyle;
  top: string; // main garment
  trim: string; // border, scarf or collar
  scarf?: string; // dupatta / shawl worn over the shoulders
  bindi?: string;
  headwear: Headwear;
  headwearColor?: string;
  mustache?: boolean;
  greeting: Greeting;
  backdrop: string;
}

const L = (look: Partial<AvatarLook> & Pick<AvatarLook, 'skin' | 'top' | 'trim' | 'backdrop'>): AvatarLook => ({
  hair: '#1d1815',
  hairStyle: 'long',
  headwear: 'none',
  greeting: 'palms',
  ...look,
});

export const AVATAR_LOOKS: Record<string, AvatarLook> = {
  en: L({ skin: '#c99572', top: '#2f4a73', trim: '#eef2f7', hairStyle: 'bun', backdrop: '#dfe9f5' }),
  hi: L({ skin: '#d1a07c', top: '#c2562b', trim: '#f0c36b', scarf: '#e8a33d', bindi: '#b3201f', backdrop: '#fbe8cf' }),
  bn: L({ skin: '#bd8a66', top: '#f4efe6', trim: '#b3201f', bindi: '#b3201f', hairStyle: 'bun', backdrop: '#fde7e2' }),
  te: L({ skin: '#a9714d', top: '#2f7d5b', trim: '#e0b13c', bindi: '#8f1d1d', hairStyle: 'braid', backdrop: '#e1f1e6' }),
  mr: L({ skin: '#c28a65', top: '#6c3f8f', trim: '#e0b13c', bindi: '#8f1d1d', hairStyle: 'bun', backdrop: '#eee3f6' }),
  ta: L({ skin: '#9a6340', top: '#7a1f3d', trim: '#e0b13c', bindi: '#8f1d1d', hairStyle: 'braid', backdrop: '#f8e1e6' }),
  gu: L({ skin: '#cf9d77', top: '#d4472f', trim: '#2c7fb8', scarf: '#2c7fb8', bindi: '#b3201f', backdrop: '#fde4d6' }),
  kn: L({ skin: '#a87450', top: '#c0392b', trim: '#e0b13c', bindi: '#8f1d1d', hairStyle: 'braid', backdrop: '#fbe3dd' }),
  ml: L({ skin: '#9c6a46', top: '#f5efdf', trim: '#d9a62e', bindi: '#2b2b2b', hairStyle: 'bun', backdrop: '#f4efd8' }),
  pa: L({ skin: '#c9966f', top: '#2b6cb0', trim: '#e8a33d', hair: '#161212', hairStyle: 'short', headwear: 'turban', headwearColor: '#e87a1e', mustache: true, backdrop: '#fdebd0' }),
  od: L({ skin: '#ad7954', top: '#c0392b', trim: '#f4efe6', bindi: '#b3201f', hairStyle: 'bun', backdrop: '#fbe5dd' }),
  as: L({ skin: '#c79a74', top: '#f4efe6', trim: '#c0392b', bindi: '#b3201f', hairStyle: 'bun', backdrop: '#f9e6e0' }),
  ur: L({ skin: '#c89873', top: '#2f6f5e', trim: '#f4efe6', hair: '#161212', hairStyle: 'short', headwear: 'cap', headwearColor: '#f4efe6', mustache: true, greeting: 'salaam', backdrop: '#e1f1ea' }),
  ne: L({ skin: '#d3a883', top: '#b3201f', trim: '#e0b13c', bindi: '#b3201f', backdrop: '#fbe4e0' }),
  kok: L({ skin: '#b78260', top: '#1f7a8c', trim: '#e0b13c', bindi: '#8f1d1d', hairStyle: 'bun', backdrop: '#dff0f3' }),
  mai: L({ skin: '#b88660', top: '#e4a11b', trim: '#b3201f', scarf: '#b3201f', bindi: '#b3201f', backdrop: '#fdeecf' }),
  doi: L({ skin: '#d5a782', top: '#5b3f8c', trim: '#e0b13c', scarf: '#e0b13c', bindi: '#b3201f', backdrop: '#ece3f6' }),
  sd: L({ skin: '#c99a76', top: '#8e3b6b', trim: '#e0b13c', scarf: '#e0b13c', greeting: 'salaam', backdrop: '#f4e3ee' }),
  ks: L({ skin: '#dcb592', top: '#8b2e2e', trim: '#d9a62e', hair: '#161212', hairStyle: 'short', headwear: 'cap', headwearColor: '#8b2e2e', greeting: 'salaam', mustache: true, backdrop: '#f5e1de' }),
  sa: L({ skin: '#c28f68', top: '#e8a33d', trim: '#f4efe6', bindi: '#b3201f', hairStyle: 'bun', backdrop: '#fdeccc' }),
  sat: L({ skin: '#8f5a3a', top: '#c0392b', trim: '#f4efe6', scarf: '#f4efe6', hairStyle: 'bun', backdrop: '#f8e1da' }),
  mni: L({ skin: '#d3a780', top: '#f4efe6', trim: '#7a1f3d', hairStyle: 'bun', backdrop: '#f3e2e8' }),
  brx: L({ skin: '#cfa27c', top: '#e4a11b', trim: '#7a1f3d', scarf: '#7a1f3d', hairStyle: 'bun', backdrop: '#fdeecf' }),
};

export const lookFor = (language: string): AvatarLook => AVATAR_LOOKS[language] ?? AVATAR_LOOKS.en;
