<template>
  <header>
    <div class="navbar-container">
      <div class="elanora-header-left">
        <router-link to="/homePage" class="elanora-header-logo-link">
          <img
            src="@logos/ELANora-logo.png"
            alt="ELANORA Logo"
            class="elanora-header-logo"
          />
        </router-link>
        <InstanceSection />
        <nav class="elanora-header-nav">
          <a href="/projects" class="elanora-header-menu-link">
            {{ t('appHeader.projects') }}
          </a>
          <a href="/upload" class="elanora-header-menu-link">
            {{ t('appHeader.upload') }}
          </a>
          <a href="/conflicts" class="elanora-header-menu-link">
            {{ t('appHeader.conflicts') }}
          </a>
          <router-link
            :to="{ name: 'TiersPage' }"
            class="elanora-header-menu-link"
          >
            {{ t('appHeader.tiers') || 'Tiers' }}
          </router-link>
        </nav>
      </div>
      <div class="elanora-header-right">
        <ProjectSection />
        <!-- User Section with Notifications -->
        <div v-if="userStore.isAuthenticated" class="elanora-header-user-section">
          <NotificationBell />           

        </div>
        <div class="elanora-header-instance-logo-container">
          <img
            src="/instance/images/logos/instance-logo.png"
            alt="Instance Logo"
            class="elanora-header-instance-logo"
          />
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import InstanceSection from '@/components/pageSpecific/appHeader/InstanceSection.vue'
import ProjectSection from '@/components/pageSpecific/appHeader/ProjectSection.vue'
import NotificationBell from '@/components/common/NotificationBell.vue'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

// User menu state
const showUserMenu = ref(false)

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const closeUserMenu = () => {
  showUserMenu.value = false
}

const logout = async () => {
  await userStore.logout()
  closeUserMenu()
  router.push('/login')
}

// Close user menu when clicking outside
const handleClickOutside = (event) => {
  if (showUserMenu.value && !event.target.closest('.elanora-header-user-menu')) {
    closeUserMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  width: 100%;
  min-width: 0;
}

.elanora-header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  min-width: 0;
}

.elanora-header-logo {
  height: 5rem;
  width: 5rem;
  box-shadow: 0 1px 4px 0 #c9dbef;
}

.elanora-header-logo-link {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.elanora-header-nav {
  display: flex;
}

.elanora-header-menu-link {
  color: #2563eb;
  font-weight: 500;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.elanora-header-menu-link:hover {
  background: #e8f0fe;
}

.elanora-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
  min-width: 0;
  max-width: 40vw;
  flex-shrink: 1;
}

.elanora-header-instance-logo-container {
  height: 5rem;
  width: 5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fbf9f6;
  box-shadow: 0 1px 4px 0 #c9dbef;
  overflow: hidden;
}

.elanora-header-instance-logo {
  max-height: 90%;
  max-width: 90%;
  object-fit: contain;
  display: block;
}

.elanora-header-project-label {
  background: #f3e8ff;
  color: #7c3aed;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 1rem;
  font-weight: 600;
}

/* User Section Styles */
.elanora-header-user-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.elanora-header-user-menu {
  position: relative;
}

.elanora-header-user-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #374151;
  font-size: 0.875rem;
}

.elanora-header-user-button:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.elanora-header-user-avatar {
  width: 2rem;
  height: 2rem;
  background: #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

.elanora-header-username {
  font-weight: 500;
  color: #374151;
}

.elanora-header-user-dropdown {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  min-width: 12rem;
  z-index: 50;
  overflow: hidden;
}

.elanora-header-user-menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  text-decoration: none;
  color: #374151;
  font-size: 0.875rem;
  transition: background-color 0.2s ease;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
}

.elanora-header-user-menu-item:hover {
  background: #f9fafb;
}

.elanora-header-logout {
  color: #dc2626;
  border-top: 1px solid #e5e7eb;
}

.elanora-header-logout:hover {
  background: #fef2f2;
}

@media (width <= 900px) {
  .navbar-container {
    flex-direction: column;
    gap: 1rem;
    padding: 0 0.5rem;
  }

  .elanora-header-left,
  .elanora-header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .elanora-header-nav {
    flex-wrap: wrap;
    gap: 0.2rem;
  }
}
</style>
