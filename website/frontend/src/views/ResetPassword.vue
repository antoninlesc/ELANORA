<template>
  <div class="reset-password-wrapper">
    <div class="reset-password-card">
      <h1 class="reset-password-title">{{ t('resetPassword.title') }}</h1>
      <form @submit.prevent="handleSubmit" class="reset-password-form">
        <div class="form-group">
          <label for="code" class="form-label">{{ t('resetPassword.code_label') }}</label>
          <input 
            id="code" 
            v-model="form.code"
            type="text" 
            class="form-input" 
            :placeholder="t('resetPassword.code_placeholder')" 
            required 
          />
        </div>
        <div class="form-group">
          <label for="new-password" class="form-label">{{ t('resetPassword.new_password_label') }}</label>
          <input 
            id="new-password" 
            v-model="form.newPassword"
            type="password" 
            class="form-input" 
            :placeholder="t('resetPassword.new_password_placeholder')" 
            required 
          />
        </div>
        <div class="form-group">
          <label for="confirm-password" class="form-label">{{ t('resetPassword.confirm_password_label') }}</label>
          <input 
            id="confirm-password" 
            v-model="form.confirmPassword"
            type="password" 
            class="form-input" 
            :placeholder="t('resetPassword.confirm_password_placeholder')" 
            required 
          />
        </div>
        <button type="submit" class="btn-primary reset-password-btn" :disabled="loading">
          <span v-if="loading">{{ t('resetPassword.submitting') }}</span>
          <span v-else>{{ t('resetPassword.submit') }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage';
import { resetPassword } from '@/api/service/authService';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const eventMessageStore = useEventMessageStore();

const form = ref({
  code: '',
  newPassword: '',
  confirmPassword: ''
});

const loading = ref(false);
const email = ref('');

onMounted(() => {
  // Get email from query parameters
  email.value = route.query.email || '';
  if (!email.value) {
    eventMessageStore.addMessage(t('resetPassword.email_required'), 'error');
    router.push({ name: 'ForgotPassword' });
  }
});

const handleSubmit = async () => {
  // Validate passwords match
  if (form.value.newPassword !== form.value.confirmPassword) {
    eventMessageStore.addMessage(t('resetPassword.passwords_no_match'), 'error');
    return;
  }

  // Validate password strength
  if (form.value.newPassword.length < 8) {
    eventMessageStore.addMessage(t('resetPassword.password_too_short'), 'error');
    return;
  }

  loading.value = true;
  try {
    await resetPassword(email.value, form.value.code, form.value.newPassword);
    eventMessageStore.addMessage(t('resetPassword.success'), 'success');
    router.push({ name: 'LoginPage' });
  } catch (error) {
    console.error('Reset password error:', error);
    eventMessageStore.addMessage(
      error?.response?.data?.detail || t('resetPassword.error'),
      'error'
    );
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.reset-password-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f5f5;
}
.reset-password-card {
  background: #fff;
  padding: 2rem 2.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  width: 100%;
  max-width: 400px;
}
.reset-password-title {
  margin-bottom: 1.5rem;
  text-align: center;
}
.reset-password-form .form-group {
  margin-bottom: 1rem;
}
.reset-password-btn {
  width: 100%;
}
</style>
