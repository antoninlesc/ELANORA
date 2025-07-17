<template>
  <div v-if="!loading">
    <router-view />
    <EventMessageContainer />
  </div>
  <div v-else>Loading...</div>
</template>

<script setup>
import { onMounted, watch, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '@stores/language';
import { useUserStore } from '@/stores/user';
import { useProjectStore } from '@/stores/project';
import { useAppInfoStore } from '@/stores/appInfo';
import gitService from '@/api/service/gitService'; // <-- Import your service
import instanceService from '@/api/service/instanceService'; // <-- If you have this

import EventMessageContainer from '@components/eventComponent/eventMessageContainer.vue';

const languageStore = useLanguageStore();
const { t, locale } = useI18n();
const userStore = useUserStore();
const projectStore = useProjectStore();
const appInfoStore = useAppInfoStore();
const loading = ref(true);

const updateDocumentMeta = () => {
  document.title = t('app.title');
  const metaDescription = document.querySelector('meta[name="description"]');
  if (metaDescription) {
    metaDescription.setAttribute('content', t('app.description'));
  }
  document.documentElement.lang = locale.value;
};

onMounted(async () => {
  languageStore.initializeFromStorage();
  userStore.initializeFromStorage();
  projectStore.initializeFromStorage();

  await userStore.verifyAuthentication();

  // Fetch instance info (if needed)
  try {
    const response = await instanceService.getInstanceInfo();
    if (response) {
      appInfoStore.setInstance(response);
      localStorage.setItem('instance', JSON.stringify(response));
    }
  } catch {
    const cached = localStorage.getItem('instance');
    if (cached) {
      appInfoStore.setInstance(JSON.parse(cached));
    }
  }

  // Fetch projects from backend and save to store
  try {
    const res = await gitService.listProjects();
    if (res && res.projects) {
      projectStore.setProjects(res.projects);
      // Set the first project as current if none is set
      if (!projectStore.currentProject && res.projects.length > 0) {
        projectStore.setCurrentProject(res.projects[0]);
      }
    }
  } catch (e) {
    // Optionally handle error or fallback
    console.error('Failed to fetch projects:', e);
  }

  locale.value = languageStore.language;
  updateDocumentMeta();
  loading.value = false;
});

watch(
  () => languageStore.language,
  (newLang) => {
    locale.value = newLang;
    updateDocumentMeta();
  }
);

watch(locale, updateDocumentMeta);
</script>
