export interface Language {
  code: string;
  name: string; // written in the language itself
  /** Sarvam can speak this language (text-to-speech). All languages support text and speech recognition. */
  tts: boolean;
}

export const LANGUAGES: Language[] = [
  { code: 'en', name: 'English', tts: true },
  { code: 'hi', name: 'हिन्दी', tts: true },
  { code: 'bn', name: 'বাংলা', tts: true },
  { code: 'te', name: 'తెలుగు', tts: true },
  { code: 'mr', name: 'मराठी', tts: true },
  { code: 'ta', name: 'தமிழ்', tts: true },
  { code: 'gu', name: 'ગુજરાતી', tts: true },
  { code: 'kn', name: 'ಕನ್ನಡ', tts: true },
  { code: 'ml', name: 'മലയാളം', tts: true },
  { code: 'pa', name: 'ਪੰਜਾਬੀ', tts: true },
  { code: 'od', name: 'ଓଡ଼ିଆ', tts: true },
  { code: 'as', name: 'অসমীয়া', tts: false },
  { code: 'ur', name: 'اردو', tts: false },
  { code: 'ne', name: 'नेपाली', tts: false },
  { code: 'kok', name: 'कोंकणी', tts: false },
  { code: 'mai', name: 'मैथिली', tts: false },
  { code: 'doi', name: 'डोगरी', tts: false },
  { code: 'sd', name: 'سنڌي', tts: false },
  { code: 'ks', name: 'کٲشُر', tts: false },
  { code: 'sa', name: 'संस्कृतम्', tts: false },
  { code: 'sat', name: 'ᱥᱟᱱᱛᱟᱲᱤ', tts: false },
  { code: 'mni', name: 'মৈতৈলোন্', tts: false },
  { code: 'brx', name: "बर'", tts: false },
];

export const DEFAULT_LANGUAGE = 'en';
export const RTL_LANGUAGES = new Set(['ur', 'sd', 'ks']);

export const isSupported = (code: string | null | undefined): code is string =>
  !!code && LANGUAGES.some((l) => l.code === code);

export const hasSpeech = (code: string) => LANGUAGES.find((l) => l.code === code)?.tts ?? false;
