import { defineStore } from 'pinia';

// Define a consistent event name for sign language changes
export const SIGN_LANGUAGE_CHANGE_EVENT = 'signLanguageChanged';

export const useLanguageStore = defineStore('language', {
  state: () => ({
    language: localStorage.getItem('language') || 'en',
    signLanguage: localStorage.getItem('signLanguage') || 'IS',
  }),
  actions: {
    setLanguage(language) {
      this.language = language;
      localStorage.setItem('language', language);

      // Dispatch custom event for language change
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('languageChanged', {
            detail: { language },
          })
        );
      }
    },
    setSignLanguage(signLanguage) {
      const previousSignLanguage = this.signLanguage;
      this.signLanguage = signLanguage;
      localStorage.setItem('signLanguage', signLanguage);
      if (
        previousSignLanguage !== signLanguage &&
        typeof window !== 'undefined'
      ) {
        window.dispatchEvent(
          new CustomEvent(SIGN_LANGUAGE_CHANGE_EVENT, {
            detail: { signLanguage },
          })
        );
      }
    },
    initializeFromStorage() {
      // Ensure language is set from localStorage or default
      const lang = localStorage.getItem('language') || 'en';
      this.language = lang;
      localStorage.setItem('language', lang);

      // Ensure signLanguage is set from localStorage or default
      const signLang = localStorage.getItem('signLanguage') || 'IS';
      this.signLanguage = signLang;
      localStorage.setItem('signLanguage', signLang);
    },
  },
});