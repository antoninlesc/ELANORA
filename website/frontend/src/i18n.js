import { createI18n } from 'vue-i18n';
import en from '@locales/en.json';
import fr from '@locales/fr.json';

// Define available languages
const messages = { en, fr };

// Function to set up i18n
export const setupI18n = () => {
  // Retrieve the language from localStorage or default to 'en'
  const storedLanguage = localStorage.getItem('language') || 'en';

  return createI18n({
    legacy: false,
    locale: storedLanguage,
    fallbackLanguage: 'en',
    messages,
  });
};
