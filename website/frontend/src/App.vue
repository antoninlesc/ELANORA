<template>
  <div>
    <template v-if="!isAuthLoading">
      <router-view />
      <EventMessageContainer />
    </template>
    <template v-else>
      <div class="app-loading-spinner"></div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '@stores/language';
import { useUserStore } from '@/stores/user';
import { useProjectStore } from '@/stores/project';

import EventMessageContainer from '@components/eventComponent/eventMessageContainer.vue';

const languageStore = useLanguageStore();
const { t, locale } = useI18n();
const userStore = useUserStore();
const projectStore = useProjectStore();

const updateDocumentMeta = () => {
  document.title = t('app.title');
  const metaDescription = document.querySelector('meta[name="description"]');
  if (metaDescription) {
    metaDescription.setAttribute('content', t('app.description'));
  }
  document.documentElement.lang = locale.value;
};

const isAuthLoading = computed(() => userStore.authState.loading);

onMounted(async () => {
  languageStore.initializeFromStorage();
  userStore.initializeFromStorage();
  projectStore.loadCurrentProject();

  await userStore.verifyAuthentication();

  locale.value = languageStore.language;
  updateDocumentMeta();
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
