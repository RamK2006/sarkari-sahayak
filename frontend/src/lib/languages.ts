export interface Language {
  code: string;
  name: string; // written in the language itself
}

export const LANGUAGES: Language[] = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'हिन्दी' },
  { code: 'bn', name: 'বাংলা' },
  { code: 'te', name: 'తెలుగు' },
  { code: 'mr', name: 'मराठी' },
  { code: 'ta', name: 'தமிழ்' },
  { code: 'gu', name: 'ગુજરાતી' },
  { code: 'kn', name: 'ಕನ್ನಡ' },
  { code: 'ml', name: 'മലയാളം' },
  { code: 'pa', name: 'ਪੰਜਾਬੀ' },
  { code: 'od', name: 'ଓଡ଼ିଆ' },
];

export const DEFAULT_LANGUAGE = 'en';

export const isSupported = (code: string | null | undefined): code is string =>
  !!code && LANGUAGES.some((l) => l.code === code);
