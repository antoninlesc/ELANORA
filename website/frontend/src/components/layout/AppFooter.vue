<template>
  <footer class="app-footer">
    <div class="footer-container">
      <div class="footer-content">
        <div class="footer-section">
          <h4>ELANORA</h4>
          <p>{{ t('footer.platform_description') }}</p>
          <div class="footer-social">
            <a href="#" class="social-link">📧</a>
            <a href="#" class="social-link">🌐</a>
            <a href="#" class="social-link">📚</a>
          </div>
        </div>

        <div class="footer-section">
          <h4>{{ t('footer.resources') }}</h4>
          <ul class="footer-links">
            <li>
              <a href="/docs">{{ t('footer.documentation') }}</a>
            </li>
            <li>
              <a href="/api">{{ t('footer.api_reference') }}</a>
            </li>
            <li>
              <a href="/tutorials">{{ t('footer.tutorials') }}</a>
            </li>
            <li>
              <a href="/support">{{ t('footer.support') }}</a>
            </li>
          </ul>
        </div>

        <div class="footer-section">
          <h4>{{ t('footer.community') }}</h4>
          <ul class="footer-links">
            <li>
              <a href="/about">{{ t('footer.about') }}</a>
            </li>
            <li>
              <a href="/research">{{ t('footer.research') }}</a>
            </li>
            <li>
              <a href="/partnerships">{{ t('footer.partnerships') }}</a>
            </li>
            <li>
              <a href="/contact">{{ t('footer.contact') }}</a>
            </li>
          </ul>
        </div>

        <div class="footer-section">
          <h4>{{ t('footer.legal') }}</h4>
          <ul class="footer-links">
            <li>
              <a href="/privacy">{{ t('footer.privacy_policy') }}</a>
            </li>
            <li>
              <a href="/terms">{{ t('footer.terms_of_service') }}</a>
            </li>
            <li>
              <a href="/cookies">{{ t('footer.cookie_policy') }}</a>
            </li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <div class="footer-copyright">
          <p>
            &copy; {{ currentYear }} ELANORA.
            {{ t('footer.all_rights_reserved') }}
          </p>
        </div>
        <div class="footer-info">
          <span class="version">v{{ version }}</span>
          <span class="separator">•</span>
          <span class="instance">{{ instanceName || 'Default Instance' }}</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue';
import { useAppInfoStore } from '@/stores/appInfo';
import { useI18n } from 'vue-i18n';

const appInfo = useAppInfoStore();
const instanceName = computed(() => appInfo.instanceName);
const version = computed(() => appInfo.version);
const currentYear = computed(() => new Date().getFullYear());
const { t } = useI18n();
</script>

<style scoped>
.app-footer {
  background: #2d3748;
  color: #e2e8f0;
  padding: 3rem 0 1rem;
  margin-top: auto;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.footer-section h4 {
  color: #1a73e8;
  font-size: 1.2rem;
  margin-bottom: 1rem;
  font-weight: 600;
}

.footer-section p {
  color: #a0aec0;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.footer-links {
  list-style: none;
  padding: 0;
}

.footer-links li {
  margin-bottom: 0.5rem;
}

.footer-links a {
  color: #a0aec0;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-links a:hover {
  color: #1a73e8;
}

.footer-social {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #4a5568;
  border-radius: 50%;
  text-decoration: none;
  font-size: 1.2rem;
  transition: all 0.2s;
}

.social-link:hover {
  background: #1a73e8;
  transform: translateY(-2px);
}

.footer-bottom {
  border-top: 1px solid #4a5568;
  padding-top: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.footer-copyright p {
  color: #a0aec0;
  font-size: 0.9rem;
  margin: 0;
}

.footer-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #a0aec0;
}

.version {
  background: #4a5568;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.separator {
  color: #718096;
}

.instance {
  color: #1a73e8;
  font-weight: 500;
}

@media (width <= 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}
</style>
