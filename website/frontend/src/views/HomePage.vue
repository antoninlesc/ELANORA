<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-container">
        <div class="hero-content">
          <div class="hero-text">
            <h1 class="hero-title">{{ t('homePage.welcomeMessage') }}</h1>
            <p class="hero-subtitle">{{ t('homePage.description') }}</p>
            <p class="hero-instructions">{{ t('homePage.instructions') }}</p>
            <div class="hero-actions">
              <router-link to="/" class="btn-primary">
                {{ t('homePage.getStarted') }}
              </router-link>
              <button class="btn-secondary" @click="showDemo">
                {{ t('homePage.viewDemo') }}
              </button>
            </div>
          </div>
          <div class="hero-visual">
            <div class="demo-preview">
              <div class="demo-header">
                <div class="demo-dots">
                  <span></span><span></span><span></span>
                </div>
                <span class="demo-title">ELANORA Platform</span>
              </div>
              <div class="demo-content">
                <div class="demo-file">📁 session_001_discourse.eaf</div>
                <div class="demo-file">📁 session_002_fluence.eaf</div>
                <div class="demo-file conflict">⚠️ session_003_markers.eaf</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="container">
        <h2 class="section-title">{{ t('homePage.features.title') }}</h2>
        <div class="features-grid">
          <div
            v-for="feature in features"
            :key="feature.key"
            class="feature-card"
          >
            <div class="feature-icon">{{ feature.icon }}</div>
            <h3>{{ t(`homePage.features.${feature.key}.title`) }}</h3>
            <p>{{ t(`homePage.features.${feature.key}.description`) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="stats-section">
      <div class="container">
        <h2 class="section-title">{{ t('homePage.platform_stats') }}</h2>
        <div class="stats-grid">
          <StatCard
            v-for="stat in platformStats"
            :key="stat.key"
            :icon="stat.icon"
            :value="stat.value"
            :label="t(`homePage.stats.${stat.key}`)"
            :trend="stat.trend"
            :trend-type="stat.trendType"
            :variant="stat.variant"
          />
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-content">
          <h2>{{ t('homePage.cta.title') }}</h2>
          <p>{{ t('homePage.cta.description') }}</p>
          <div class="cta-actions">
            <router-link to="/" class="btn-primary">
              {{ t('homePage.cta.get_started') }}
            </router-link>
            <a href="/contact" class="btn-secondary">
              {{ t('homePage.cta.contact_us') }}
            </a>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useHead } from '@unhead/vue';
import StatCard from '@/components/common/StatCard.vue';

const { t } = useI18n();

useHead({
  title: t('homePage.pageTitle'),
  meta: [
    { name: 'description', content: t('homePage.pageDescription') },
  ],
});

// Features data
const features = ref([
  {
    key: 'collaborative_elan',
    icon: '🤝',
  },
  {
    key: 'conflict_detection',
    icon: '⚠️',
  },
  {
    key: 'annotation_workflows',
    icon: '📋',
  },
  {
    key: 'project_repositories',
    icon: '📚',
  },
  {
    key: 'secure_instance',
    icon: '🔒',
  },
  {
    key: 'export_tools',
    icon: '📄',
  },
]);

// Platform statistics
const platformStats = ref([
  {
    key: 'total_projects',
    icon: '📚',
    value: '-',
    trend: '',
    trendType: 'neutral',
    variant: 'primary',
  },
  {
    key: 'active_users',
    icon: '👥',
    value: '-',
    trend: '',
    trendType: 'neutral',
    variant: 'success',
  },
  {
    key: 'elan_files',
    icon: '📁',
    value: '-',
    trend: '',
    trendType: 'neutral',
    variant: 'primary',
  },
  {
    key: 'institutions',
    icon: '🏛️',
    value: '-',
    trend: '',
    trendType: 'neutral',
    variant: 'default',
  },
]);

const showDemo = () => {
  // Implementation for demo modal or redirect
  console.log('Show demo clicked');
};
</script>

<style scoped src="@/assets/css/home-page.css"></style>
