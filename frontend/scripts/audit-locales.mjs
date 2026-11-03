// Verifies every locale has exactly the keys of en.json and the same {placeholders} per key.
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const dir = join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'locales');
const load = (f) => JSON.parse(readFileSync(join(dir, f), 'utf8'));
const placeholders = (s) => (s.match(/\{\w+\}/g) ?? []).sort().join(',');

const en = load('en.json');
let problems = 0;
for (const file of readdirSync(dir).filter((f) => f.endsWith('.json') && f !== 'en.json')) {
  const messages = load(file);
  for (const key of Object.keys(en)) {
    if (!(key in messages)) {
      console.error(`${file}: missing ${key}`);
      problems++;
    } else if (placeholders(messages[key]) !== placeholders(en[key])) {
      console.error(`${file}: placeholder mismatch in ${key}`);
      problems++;
    } else if (!messages[key].trim()) {
      console.error(`${file}: empty ${key}`);
      problems++;
    }
  }
  for (const key of Object.keys(messages)) {
    if (!(key in en)) {
      console.error(`${file}: unknown key ${key}`);
      problems++;
    }
  }
}
console.log(problems ? `${problems} problem(s)` : 'All locales are complete.');
process.exit(problems ? 1 : 0);
