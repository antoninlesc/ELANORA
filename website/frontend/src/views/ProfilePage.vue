<template>
  <div class="profile-page">
    <h2>Profile</h2>
    <button @click="toggleLanguage">
      {{ language === 'en' ? 'Passer en français' : 'Switch to English' }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useLanguageStore } from '@/stores/language.js';

const languageStore = useLanguageStore();
const language = computed(() => languageStore.language);

function toggleLanguage() {
  languageStore.setLanguage(language.value === 'en' ? 'fr' : 'en');
}
</script>

<style scoped>
.profile-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

h2 {
  text-align: center;
  margin-bottom: 1.5rem;
}

button {
  display: block;
  width: 100%;
  padding: 0.75rem;
  font-size: 1rem;
  color: #fff;
  background-color: #007bff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}
</style>