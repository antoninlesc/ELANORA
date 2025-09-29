<template>
  <router-view />
  <EventMessageContainer />
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useLanguageStore } from '@stores/language';
import { useAppInfoStore } from '@/stores/appInfo';
import instanceService from '@api/service/instanceService';

import EventMessageContainer from '@components/eventComponent/eventMessageContainer.vue';

const languageStore = useLanguageStore();
const { locale } = useI18n();
const appInfoStore = useAppInfoStore();

onMounted(async () => {
  languageStore.initializeFromStorage();

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

  locale.value = languageStore.language;
});

watch(
  () => languageStore.language,
  (newLang) => {
    locale.value = newLang;
  }
);
</script>
