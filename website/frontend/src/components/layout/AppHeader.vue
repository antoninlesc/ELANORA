<template>
  <header class="app-header">
    <div class="header-container">
      <div class="header-left">
        <h1 class="logo">ELANORA</h1>
        <span v-if="instanceName" class="instance-label">{{
          instanceName
        }}</span>
        <span v-if="breadcrumb" class="breadcrumb"> / </span>
        <span v-if="repoName" class="repo-name">{{ repoName }}</span>
      </div>
      <nav v-if="showNavigation" class="nav">
        <router-link to="/projects" class="nav-link">{{
          t('navigation.projects')
        }}</router-link>
        <router-link to="/dashboard" class="nav-link">{{
          t('navigation.dashboard')
        }}</router-link>
        <router-link to="/conflicts" class="nav-link">
          {{ t('navigation.conflicts') }}
          <span v-if="conflictCount > 0" class="badge">{{
            conflictCount
          }}</span>
        </router-link>
        <router-link to="/tiers" class="nav-link">{{
          t('navigation.tier_management')
        }}</router-link>
        <router-link to="/export" class="nav-link">{{
          t('navigation.export')
        }}</router-link>
        <div v-if="user" class="user-menu">
          <span>{{ user.name }}</span>
          <button class="btn-logout" @click="handleLogout">
            {{ t('common.logout') }}
          </button>
        </div>
      </nav>
      <div v-else class="header-actions">
        <router-link to="/" class="btn-secondary">{{
          t('auth.login')
        }}</router-link>
        <button class="btn-primary" @click="requestAccess">
          {{ t('auth.request_access') }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUserStore } from '@/stores/user';

defineProps({
  instanceName: {
    type: String,
    default: 'elanora',
  },
  repoName: {
    type: String,
    default: 'elanora-repo',
  },
  breadcrumb: {
    type: Boolean,
    default: false,
  },
  showNavigation: {
    type: Boolean,
    default: false,
  },
  conflictCount: {
    type: Number,
    default: 0,
  },
});

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();

const user = computed(() => userStore.user);

const handleLogout = () => {
  userStore.logout();
  router.push('/');
};

const requestAccess = () => {
  router.push('/request-access');
};
</script>

<style scoped>
.app-header {
  background: white;
  border-bottom: 1px solid #e1e8ed;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgb(0 0 0 / 10%);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo {
  color: #1a73e8;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0;
}

.instance-label {
  background: #e8f0fe;
  color: #1a73e8;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}

.breadcrumb {
  color: #5f6368;
  font-size: 1.2rem;
}

.repo-name {
  color: #5f6368;
  font-weight: 500;
}

.nav {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-link {
  text-decoration: none;
  color: #5f6368;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s;
  position: relative;
}

.nav-link.router-link-active,
.nav-link:hover {
  background-color: #e8f0fe;
  color: #1a73e8;
}

.badge {
  background: #ea4335;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 0.75rem;
  margin-left: 4px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: #5f6368;
}

.btn-logout,
.btn-secondary,
.btn-primary {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-block;
  border: none;
}

.btn-logout {
  background: none;
  border: 1px solid #dadce0;
  color: #5f6368;
}

.btn-logout:hover {
  background-color: #f8f9fa;
}

.btn-secondary {
  background-color: #f8f9fa;
  color: #3c4043;
  border: 1px solid #dadce0;
}

.btn-secondary:hover {
  background-color: #e8eaed;
}

.btn-primary {
  background-color: #1a73e8;
  color: white;
}

.btn-primary:hover {
  background-color: #1557b0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

@media (width <= 768px) {
  .header-container {
    flex-direction: column;
    gap: 1rem;
  }

  .nav {
    flex-wrap: wrap;
    gap: 1rem;
  }
}
</style>
