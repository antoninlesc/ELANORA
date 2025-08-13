<template>
  <div class="profile-settings">
    <!-- Language Settings Section -->
    
      <div class="settings-card-header">
        <div class="settings-icon">🌐</div>
        <div class="settings-header-content">
          <h3 class="settings-section-title">{{ t('profile.settings.language.title') }}</h3>
          <p class="settings-section-description">{{ t('profile.settings.language.description') }}</p>
        </div>
      </div>
      
      <div class="settings-card-body">
        <div class="setting-item">
          <div class="setting-header">
            <span class="setting-label">{{ t('profile.settings.language.label') }}</span>
            <div class="current-selection">
              <span class="current-flag">{{ currentLanguageInfo.flag }}</span>
              <span class="current-name">{{ currentLanguageInfo.name }}</span>
            </div>
          </div>
          <div class="language-selector">
            <button
              v-for="lang in availableLanguages"
              :key="lang.code"
              class="language-option"
              :class="{ active: currentLanguage === lang.code }"
              @click="changeLanguage(lang.code)"
              :aria-pressed="currentLanguage === lang.code"
              :disabled="currentLanguage === lang.code"
            >
              <span class="language-flag">{{ lang.flag }}</span>
              <div class="language-info">
                <span class="language-name">{{ lang.name }}</span>
                <span class="language-native">{{ lang.nativeName }}</span>
              </div>
              <div v-if="currentLanguage === lang.code" class="check-icon">✓</div>
            </button>
          </div>
        </div>
      </div>
    

  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '@/stores/language.js';
import { useEventMessageStore } from '@/stores/eventMessage.js';

const { t, availableLocales } = useI18n();
const languageStore = useLanguageStore();
const eventMessageStore = useEventMessageStore();

const currentLanguage = computed(() => languageStore.language);

// Configuration des langues avec leurs métadonnées
const languageConfig = {
  en: { 
    name: 'English', 
    nativeName: 'English',
    flag: '🇺🇸',
    region: 'United States'
  },
  fr: { 
    name: 'Français', 
    nativeName: 'Français',
    flag: '🇫🇷',
    region: 'France'
  }
};

// Génération dynamique des langues disponibles basée sur les locales disponibles
const availableLanguages = computed(() => {
  return availableLocales.filter(locale => languageConfig[locale]).map(locale => ({
    code: locale,
    ...languageConfig[locale]
  }));
});

const currentLanguageInfo = computed(() => {
  return availableLanguages.value.find(lang => lang.code === currentLanguage.value) || availableLanguages.value[0];
});

function changeLanguage(langCode) {
  if (langCode !== currentLanguage.value) {
    languageStore.setLanguage(langCode);
    const langInfo = availableLanguages.value.find(l => l.code === langCode);
    eventMessageStore.addMessage(
      t('profile.settings.language.changed', { language: langInfo?.name }),
      'success'
    );
  }
}
</script>

<style scoped>
.profile-settings {
  padding: 0;
  max-width: 900px;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Settings Card */
.settings-card {
  background: white;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.settings-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #cbd5e1;
}

.settings-card-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 2rem 2rem 1rem 2rem;
  border-bottom: 1px solid #f1f5f9;
}

.settings-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

.settings-header-content {
  flex: 1;
}

.settings-section-title {
  margin: 0 0 0.5rem 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.settings-section-description {
  margin: 0;
  color: #64748b;
  font-size: 1rem;
  line-height: 1.6;
}

.settings-card-body {
  padding: 1.5rem 2rem 2rem 2rem;
}

/* Setting Item */
.setting-item {
  margin-bottom: 0;
}

.setting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.setting-label {
  font-weight: 600;
  color: #374151;
  font-size: 1rem;
}

.current-selection {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.current-flag {
  font-size: 1.1rem;
}

.current-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: #6366f1;
}

/* Language Selector */
.language-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.language-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  border: 2px solid #f1f5f9;
  border-radius: 12px;
  background: #fafbfc;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  min-height: 80px;
}

.language-option:hover:not(:disabled) {
  border-color: #6366f1;
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.12);
}

.language-option.active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  color: #1e40af;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
}

.language-option:disabled {
  cursor: default;
  opacity: 0.8;
}

.language-flag {
  font-size: 2rem;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.language-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.language-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: inherit;
}

.language-native {
  font-size: 0.9rem;
  color: #64748b;
  font-weight: 400;
}

.language-option.active .language-native {
  color: #3b82f6;
}

.check-icon {
  font-size: 1.2rem;
  color: #10b981;
  font-weight: bold;
  background: #ecfdf5;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* Coming Soon Cards */
.coming-soon-card {
  position: relative;
}

.coming-soon-card .settings-card-header,
.coming-soon-card .settings-card-body {
  opacity: 0.6;
}

.coming-soon-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(2px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
}

.coming-soon-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  text-align: center;
  padding: 2rem;
}

.coming-soon-icon {
  font-size: 2.5rem;
  opacity: 0.7;
}

.coming-soon-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Responsive Design */
@media (max-width: 768px) {
  .profile-settings {
    gap: 1.5rem;
  }

  .settings-card-header {
    padding: 1.5rem 1.5rem 1rem 1.5rem;
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .settings-card-body {
    padding: 1rem 1.5rem 1.5rem 1.5rem;
  }

  .setting-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .current-selection {
    align-self: flex-start;
  }

  .language-selector {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .language-option {
    padding: 1rem;
    min-height: 70px;
  }

  .language-flag {
    font-size: 1.5rem;
  }

  .language-name {
    font-size: 1rem;
  }

  .language-native {
    font-size: 0.85rem;
  }

  .settings-section-title {
    font-size: 1.2rem;
  }

  .coming-soon-content {
    padding: 1.5rem;
  }

  .coming-soon-icon {
    font-size: 2rem;
  }

  .coming-soon-text {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .settings-card-header {
    padding: 1.25rem 1.25rem 0.75rem 1.25rem;
  }

  .settings-card-body {
    padding: 0.75rem 1.25rem 1.25rem 1.25rem;
  }

  .language-option {
    padding: 0.875rem;
    min-height: 60px;
    gap: 0.75rem;
  }

  .settings-icon {
    width: 40px;
    height: 40px;
    font-size: 1.25rem;
  }
}

/* Animation pour le changement de langue */
@keyframes languageChange {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.language-option.active:not(:disabled) {
  animation: languageChange 0.3s ease-out;
}
</style>
