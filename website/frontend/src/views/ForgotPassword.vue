<template>
  <div class="forgot-password-wrapper">
    <div class="forgot-password-card">
      <h1 class="forgot-password-title">{{ t('forgotPassword.title') }}</h1>
      <form class="forgot-password-form" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="email" class="form-label">{{
            t('forgotPassword.email_label')
          }}</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            class="form-input"
            :placeholder="t('forgotPassword.email_placeholder')"
            autocomplete="email"
          />
        </div>
        <button
          type="submit"
          class="btn-primary forgot-password-btn"
          :disabled="loading"
        >
          <span v-if="loading">{{ t('forgotPassword.sending') }}</span>
          <span v-else>{{ t('forgotPassword.send_code') }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { forgotPassword } from '@/api/service/authService';
import { useEventMessageStore } from '@stores/eventMessage';

const { t, locale } = useI18n();
const router = useRouter();
const eventMessageStore = useEventMessageStore();

const email = ref('');
const loading = ref(false);

const handleSubmit = async () => {
  loading.value = true;
  try {
    await forgotPassword(email.value, locale.value);
    eventMessageStore.addMessage(t('forgotPassword.code_sent'), 'success');
    router.push({ name: 'ResetPassword', query: { email: email.value } });
  } catch (error) {
    console.error(error);
    eventMessageStore.addMessage(
      error?.response?.data?.detail || t('forgotPassword.error'),
      'error'
    );
  } finally {
    loading.value = false;
  }
};
</script>

<style src="@/assets/css/forgot-password.css" scoped></style>
