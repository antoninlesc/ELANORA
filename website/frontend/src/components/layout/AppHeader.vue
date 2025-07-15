<template>
  <header>
    <div class="navbar-container">
      <div class="elanora-header-left">
        <img
          src="@images/ELANora-logo.png"
          alt="ELANORA Logo"
          class="elanora-header-logo"
        />
      </div>
      <div class="elanora-header-right">
        <a href="/projects" class="elanora-header-menu-link">
          {{ t('navigation.projects') }}
        </a>
        <a href="/upload" class="elanora-header-menu-link">
          {{ t('navigation.upload') }}
        </a>
        <a href="/conflicts" class="elanora-header-menu-link">
          {{ t('navigation.conflicts') }}
        </a>
        <span v-if="instanceName" class="elanora-header-instance-label">{{
          instanceName
        }}</span>
        <button
          v-if="user"
          class="elanora-header-btn-logout"
          @click="handleLogout"
        >
          {{ t('common.logout') }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useAppInfoStore } from '@/stores/appInfo';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUserStore } from '@/stores/user';

const appInfo = useAppInfoStore();
const instanceName = computed(() => appInfo.instanceName);

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();
const user = computed(() => userStore.user);

const handleLogout = async () => {
  try {
    await userStore.logout();
    localStorage.setItem('logoutMessage', t('auth.logout_success'));
  } catch (error) {
    console.error('Logout failed:', error);
    localStorage.setItem('logoutMessage', t('auth.logout_error'));
  }
  router.push('/');
};
</script>

<style scoped>
.elanora-header-left {
  display: flex;
  align-items: center;
}

.elanora-header-logo {
  height: 80px;
  width: auto;
}

.elanora-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.elanora-header-instance-label {
  background: #e8f0fe;
  color: #1a73e8;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.elanora-header-btn-logout {
  background: none;
  border: 1px solid #dadce0;
  color: #5f6368;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-block;
}

.elanora-header-btn-logout:hover {
  background-color: #f8f9fa;
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

@media (width <= 768px) {
  .elanora-header-container {
    flex-direction: column;
    gap: 1rem;
  }

  .elanora-header-right {
    margin-left: 0;
  }
}
</style>
