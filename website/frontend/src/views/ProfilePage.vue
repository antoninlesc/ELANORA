<template>
  <div class="profile-page">
    <div class="profile-bg-gradient"></div>
    <div class="profile-container">
      <!-- Sidebar menu -->
      <aside class="profile-sidebar">
        <div class="profile-sidebar-header">
          <div class="profile-avatar">
            <span>{{ userProfile?.first_name?.[0] || '👤' }}</span>
          </div>
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
          <div class="profile-header-flex">
            
            <div>
              <h1>{{ currentMenuItem?.title }}</h1>
              <p v-if="currentMenuItem?.description" class="profile-content-subtitle">
                {{ currentMenuItem.description }}
              </p>
            </div>
          </div>
        </div>

        <div class="profile-main-card">
          <!-- Profile Overview Section -->
          <ProfileOverview
            v-if="currentSection === 'overview'"
            :user-profile="userProfile"
            :loading="loading"
            :error="error"
            @profile-updated="loadUserProfile"
            @show-message="handleMessage"
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
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '@/stores/language.js';
import { useEventMessageStore } from '@/stores/eventMessage.js';
import { fetchUserProfile } from '@/api/service/userService.js';
import ProfileOverview from '@/components/pageSpecific/profile/ProfileOverview.vue';

const { t } = useI18n();
const languageStore = useLanguageStore();
const eventMessageStore = useEventMessageStore();
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

function handleMessage(message) {
  eventMessageStore.addMessage(message.text, message.type);
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
/* Fond dégradé moderne */
.profile-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background: transparent;
}

.profile-bg-gradient {
  position: fixed;
  inset: 0;
  z-index: 0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 60%, #e2e8f0 100%);
  opacity: 0.9;
  pointer-events: none;
}

.profile-container {
  display: flex;
  flex: 1;
  max-width: 1200px;
  margin: 3rem auto 2rem auto;
  width: 100%;
  background: rgba(255,255,255,0.98);
  border-radius: 20px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0,0,0,0.03);
  overflow: hidden;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(226, 232, 240, 0.5);
}

/* Sidebar Styles */

.profile-sidebar {
  width: 260px;
  background: rgba(248,250,252,0.99);
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px 0 rgba(0, 0, 0, 0.03);
  z-index: 2;
}

.profile-sidebar-header {
  padding: 2.5rem 1.5rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.profile-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.2rem;
  color: white;
  margin-bottom: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.profile-sidebar-header h2 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.01em;
}


.profile-menu {
  flex: 1;
  padding: 1.2rem 0 1.2rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.profile-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.5rem;
  border: none;
  background: none;
  color: #64748b;
  font-size: 1.05rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px 0 0 8px;
  position: relative;
}
.profile-menu-item:hover {
  background: #f1f5f9;
  color: #475569;
  box-shadow: 2px 2px 6px 0 rgba(0, 0, 0, 0.04);
}
.profile-menu-item.active {
  background: linear-gradient(90deg, #f1f5f9 80%, #f8fafc 100%);
  color: #6366f1;
  border-right: 3px solid #6366f1;
  font-weight: 600;
  box-shadow: 2px 2px 8px 0 rgba(0, 0, 0, 0.06);
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
  padding: 1.2rem 1.5rem 1.5rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.language-toggle {
  width: 100%;
  padding: 0.85rem;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
.language-toggle:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

/* Main Content Styles */

.profile-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
}

.profile-content-header {
  padding: 2.5rem 2.5rem 1.5rem 2.5rem;
  border-bottom: none;
  background: transparent;
}

.profile-header-flex {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.profile-header-avatar {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.profile-content-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2.1rem;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.01em;
}

.profile-content-subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 1.13rem;
}

.profile-main-card {
  margin: 2.5rem 2.5rem 2.5rem 2.5rem;
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0,0,0,0.02);
  padding: 0;
  min-height: 400px;
  position: relative;
  z-index: 2;
  border: 1px solid rgba(226, 232, 240, 0.5);
  overflow: hidden;
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
@media (max-width: 900px) {
  .profile-container {
    flex-direction: column;
    border-radius: 0;
    margin: 0;
    max-width: 100vw;
    min-height: 100vh;
  }
  .profile-sidebar {
    width: 100%;
    max-height: 220px;
    flex-direction: row;
    border-radius: 0;
    box-shadow: none;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    align-items: flex-start;
    padding-bottom: 0;
  }
  .profile-sidebar-header {
    flex-direction: row;
    gap: 1rem;
    padding: 1.2rem 1rem 1.2rem 1rem;
    border-bottom: none;
    align-items: center;
    justify-content: flex-start;
  }
  .profile-avatar {
    width: 44px;
    height: 44px;
    font-size: 1.3rem;
    margin-bottom: 0;
  }
  .profile-menu {
    flex-direction: row;
    gap: 0.5rem;
    padding: 0.5rem 0.5rem 0.5rem 0.5rem;
    overflow-x: auto;
    width: 100%;
  }
  .profile-menu-item {
    min-width: 110px;
    flex-direction: column;
    gap: 0.2rem;
    padding: 0.7rem 0.5rem;
    text-align: center;
    border-radius: 8px;
    font-size: 0.98rem;
  }
  .profile-menu-item.active {
    border-right: none;
    border-bottom: 3px solid #6366f1;
    background: linear-gradient(180deg, #f1f5f9 80%, #f8fafc 100%);
  }
  .profile-sidebar-footer {
    padding: 1rem;
    border-top: none;
  }
  .profile-content-header {
    padding: 1.2rem 1rem 1rem 1rem;
  }
  .profile-header-avatar {
    width: 44px;
    height: 44px;
    font-size: 1.3rem;
  }
  .profile-main-card {
    margin: 1.2rem 0.5rem 1.2rem 0.5rem;
    padding: 0;
    border-radius: 16px;
    min-height: 300px;
  }
  .profile-section {
    padding: 1rem;
  }
}
</style>