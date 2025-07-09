<template>
  <div class="http-status-error-container">
    <h1 class="http-status-error-code" :class="errorColor">
      {{ statusCode }}
    </h1>
    <p class="http-status-error-message">
      {{ t('http_status.' + message) }}
    </p>
    <router-link :to="getRedirect()" class="http-status-error-link">
      {{ t('http_status.back') }}
    </router-link>
  </div>
</template>

<script setup>
// Imports
import '@css/http-status.css';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// Define props
const props = defineProps({
  statusCode: {
    type: Number,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
});

// Computed properties
const errorColor = computed(() => {
  const colors = {
    400: 'error-purple',
    401: 'error-yellow',
    403: 'error-orange',
    404: 'error-red',
    405: 'error-blue',
    408: 'error-red',
    500: 'error-red',
    502: 'error-gray',
    503: 'error-gray',
  };
  return colors[props.statusCode] || 'error-gray';
});

// Methods
const getRedirect = () => {
  const redirectTo = localStorage.getItem('redirectTo') || '/';
  return redirectTo;
};
</script>
