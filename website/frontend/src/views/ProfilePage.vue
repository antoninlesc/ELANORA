<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- Sidebar menu -->
      <aside class="profile-sidebar">
        <div class="profile-sidebar-header">
          <h2>{{ t('profile.title') }}</h2>
        </div>
        <nav class="profile-menu">
          <button
            v-for="item in menuItems"
            :key="item.id"
            class="profile-menu-item"
            :class="{ active: currentSection === item.id }"
            @click="currentSection = item.id"
          >
            <span class="profile-menu-icon">{{ item.icon }}</span>
            <span class="profile-menu-label">{{ item.label }}</span>
          </button>
        </nav>
        <div class="profile-sidebar-footer">
          <button @click="toggleLanguage" class="language-toggle">
            {{ language === 'en' ? 'Passer en français' : 'Switch to English' }}
          </button>
        </div>
      </aside>

      <!-- Main content area -->
      <main class="profile-content">
        <div class="profile-content-header">
          <h1>{{ currentMenuItem?.title }}</h1>
          <p v-if="currentMenuItem?.description" class="profile-content-subtitle">
            {{ currentMenuItem.description }}
          </p>
        </div>

        <!-- Profile Overview Section -->
        <ProfileOverview
          v-if="currentSection === 'overview'"
          :user-profile="userProfile"
          :loading="loading"
          :error="error"
        />

        <!-- Settings Section (placeholder) -->
        <div v-else-if="currentSection === 'settings'" class="profile-section">
          <div class="profile-placeholder">
            <h3>{{ t('profile.settings.title') }}</h3>
            <p>{{ t('profile.settings.coming_soon') }}</p>
          </div>
        </div>

        <!-- Security Section (placeholder) -->
        <div v-else-if="currentSection === 'security'" class="profile-section">
          <div class="profile-placeholder">
            <h3>{{ t('profile.security.title') }}</h3>
            <p>{{ t('profile.security.coming_soon') }}</p>
          </div>
        </div>

        <!-- Notifications Section (placeholder) -->
        <div v-else-if="currentSection === 'notifications'" class="profile-section">
          <div class="profile-placeholder">
            <h3>{{ t('profile.notifications.title') }}</h3>
            <p>{{ t('profile.notifications.coming_soon') }}</p>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '@/stores/language.js';
import { fetchUserProfile } from '@/api/service/userService.js';
import ProfileOverview from '@/components/pageSpecific/profile/ProfileOverview.vue';

const { t } = useI18n();
const languageStore = useLanguageStore();
const language = computed(() => languageStore.language);

// State
const currentSection = ref('overview');
const userProfile = ref(null);
const loading = ref(true);
const error = ref('');

// Menu configuration
const menuItems = computed(() => [
  {
    id: 'overview',
    label: t('profile.menu.overview'),
    title: t('profile.overview.title'),
    description: t('profile.overview.description'),
    icon: '👤',
  },
  {
    id: 'settings',
    label: t('profile.menu.settings'),
    title: t('profile.settings.title'),
    description: t('profile.settings.description'),
    icon: '⚙️',
  },
  {
    id: 'security',
    label: t('profile.menu.security'),
    title: t('profile.security.title'),
    description: t('profile.security.description'),
    icon: '🔒',
  },
  {
    id: 'notifications',
    label: t('profile.menu.notifications'),
    title: t('profile.notifications.title'),
    description: t('profile.notifications.description'),
    icon: '🔔',
  },
]);

const currentMenuItem = computed(() => 
  menuItems.value.find(item => item.id === currentSection.value)
);

// Methods
function toggleLanguage() {
  languageStore.setLanguage(language.value === 'en' ? 'fr' : 'en');
}

async function loadUserProfile() {
  try {
    loading.value = true;
    error.value = '';
    const response = await fetchUserProfile();
    userProfile.value = response.data;
  } catch (err) {
    console.error('Error loading user profile:', err);
    error.value = t('profile.errors.load_failed');
  } finally {
    loading.value = false;
  }
}

// Lifecycle
onMounted(() => {
  loadUserProfile();
});
</script>

<style scoped>
.profile-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.profile-container {
  display: flex;
  flex: 1;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* Sidebar Styles */
.profile-sidebar {
  width: 280px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.profile-sidebar-header {
  padding: 2rem 1.5rem 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.profile-sidebar-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a202c;
}

.profile-menu {
  flex: 1;
  padding: 1rem 0;
}

.profile-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  border: none;
  background: none;
  color: #4a5568;
  font-size: 1rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 0;
}

.profile-menu-item:hover {
  background: #edf2f7;
  color: #2d3748;
}

.profile-menu-item.active {
  background: #e6f3ff;
  color: #2563eb;
  border-right: 3px solid #2563eb;
}

.profile-menu-icon {
  font-size: 1.1rem;
  width: 1.5rem;
  text-align: center;
}

.profile-menu-label {
  font-weight: 500;
}

.profile-sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.language-toggle {
  width: 100%;
  padding: 0.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.language-toggle:hover {
  background: #1d4ed8;
}

/* Main Content Styles */
.profile-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.profile-content-header {
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  background: white;
}

.profile-content-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: #1a202c;
}

.profile-content-subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 1.1rem;
}

.profile-section {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

.profile-placeholder {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.profile-placeholder h3 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  color: #374151;
}

.profile-placeholder p {
  margin: 0;
  font-size: 1.1rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .profile-container {
    flex-direction: column;
    border-radius: 0;
    height: 100vh;
  }

  .profile-sidebar {
    width: 100%;
    max-height: 200px;
    overflow-y: auto;
  }

  .profile-menu {
    display: flex;
    overflow-x: auto;
    padding: 1rem;
  }

  .profile-menu-item {
    min-width: 120px;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.75rem;
    text-align: center;
    border-radius: 8px;
  }

  .profile-menu-item.active {
    border-right: none;
    border-bottom: 3px solid #2563eb;
  }

  .profile-content-header {
    padding: 1.5rem 1rem 1rem;
  }

  .profile-content-header h1 {
    font-size: 1.5rem;
  }

  .profile-section {
    padding: 1rem;
  }
}
</style>