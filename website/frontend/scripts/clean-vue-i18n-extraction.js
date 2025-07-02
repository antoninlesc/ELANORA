import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import process from 'process';

// Path to the locales folder (relative to this script)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const localesPath = path.resolve(__dirname, '../src/locales');

// Function to remove empty translations from a JSON file
export async function cleanEmptyEntries(filePath) {
  const file = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  const cleanedFile = removeEmptyEntries(file);

  fs.writeFileSync(filePath, JSON.stringify(cleanedFile, null, 2));
  console.log(`Cleaned up empty entries in: ${filePath}`);
}

// Recursive function to clean empty keys
export function removeEmptyEntries(obj) {
  if (Array.isArray(obj)) {
    return obj.map(removeEmptyEntries);
  }
  if (typeof obj === 'object' && obj !== null) {
    const newObj = {};
    for (const key in obj) {
      if (key === '' && obj[key] === '') continue;
      newObj[key] = removeEmptyEntries(obj[key]);
    }
    return newObj;
  }
  return obj;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  fs.readdirSync(localesPath).forEach(async (file) => {
    if (file.endsWith('.json')) {
      const filePath = path.join(localesPath, file);
      await cleanEmptyEntries(filePath);
    }
  });
}
