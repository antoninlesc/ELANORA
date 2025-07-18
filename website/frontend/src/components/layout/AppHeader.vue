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
            {{ t('navigation.projects') }}
          </a>
          <a href="/upload" class="elanora-header-menu-link">
            {{ t('navigation.upload') }}
          </a>
          <a href="/conflicts" class="elanora-header-menu-link">
            {{ t('navigation.conflicts') }}
          </a>
          <router-link
            :to="{ name: 'TiersPage' }"
            class="elanora-header-menu-link"
          >
            {{ t('navigation.tiers') || 'Tiers' }}
          </router-link>
        </nav>
      </div>
      <div class="elanora-header-right">
        <ProjectSection />
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
import { useI18n } from 'vue-i18n';
import InstanceSection from '@/components/common/InstanceSection.vue';
import ProjectSection from '@/components/common/ProjectSection.vue';

const { t } = useI18n();
</script>

<style scoped>
.elanora-header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
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
}

.elanora-header-insdtance-logo-container {
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
