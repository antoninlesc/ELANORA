import { defineStore } from 'pinia';

export const useLanguageStore = defineStore('language', {
  state: () => ({
    language: localStorage.getItem('language') || 'en',
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
    initializeFromStorage() {
      // Ensure language is set from localStorage or default
      const lang = localStorage.getItem('language') || 'en';
      this.language = lang;
      localStorage.setItem('language', lang);
    },
  },
});
