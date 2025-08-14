<template>
  <div class="profile-security">
    <div class="security-section">
      <h3 class="security-title">{{ t('profile.security.change_password.title') }}</h3>
      <p class="security-description">{{ t('profile.security.change_password.description') }}</p>
      
      <form @submit.prevent="handlePasswordChange" class="password-form">
        <div class="form-group">
          <label for="current-password" class="form-label">
            {{ t('profile.security.change_password.current_password') }}
          </label>
          <input
            id="current-password"
            v-model="form.currentPassword"
            type="password"
            class="form-input"
            :placeholder="t('profile.security.change_password.current_password_placeholder')"
            required
            autocomplete="current-password"
          />
        </div>

        <div class="form-group">
          <label for="new-password" class="form-label">
            {{ t('profile.security.change_password.new_password') }}
          </label>
          <input
            id="new-password"
            v-model="form.newPassword"
            type="password"
            class="form-input"
            :placeholder="t('profile.security.change_password.new_password_placeholder')"
            required
            autocomplete="new-password"
            @input="validatePassword"
          />
          <div v-if="passwordValidation.show" class="password-requirements">
            <div class="requirements-title">{{ t('profile.security.change_password.requirements.title') }}</div>
            <div 
              v-for="requirement in passwordRequirements" 
              :key="requirement.key"
              class="requirement-item"
              :class="{ valid: requirement.valid }"
            >
              <span class="requirement-icon">{{ requirement.valid ? '✓' : '✗' }}</span>
              <span class="requirement-text">{{ requirement.text }}</span>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label for="confirm-password" class="form-label">
            {{ t('profile.security.change_password.confirm_password') }}
          </label>
          <input
            id="confirm-password"
            v-model="form.confirmPassword"
            type="password"
            class="form-input"
            :placeholder="t('profile.security.change_password.confirm_password_placeholder')"
            required
            autocomplete="new-password"
          />
          <div v-if="form.confirmPassword && !passwordsMatch" class="error-message">
            {{ t('profile.security.change_password.passwords_no_match') }}
          </div>
        </div>

        <div class="form-actions">
          <button 
            type="submit" 
            class="btn-primary"
            :disabled="!isFormValid || loading"
          >
            <span v-if="loading">{{ t('profile.security.change_password.updating') }}</span>
            <span v-else>{{ t('profile.security.change_password.update') }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { changePassword } from '@/api/service/userService.js';

const { t } = useI18n();
const emit = defineEmits(['show-message']);

// State
const form = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const loading = ref(false);
const passwordValidation = ref({
  show: false
});

// Password validation
const passwordRequirements = computed(() => [
  {
    key: 'length',
    text: t('profile.security.change_password.requirements.length'),
    valid: form.value.newPassword.length >= 8
  },
  {
    key: 'uppercase',
    text: t('profile.security.change_password.requirements.uppercase'),
    valid: /[A-Z]/.test(form.value.newPassword)
  },
  {
    key: 'lowercase',
    text: t('profile.security.change_password.requirements.lowercase'),
    valid: /[a-z]/.test(form.value.newPassword)
  },
  {
    key: 'number',
    text: t('profile.security.change_password.requirements.number'),
    valid: /\d/.test(form.value.newPassword)
  },
  {
    key: 'special',
    text: t('profile.security.change_password.requirements.special'),
    valid: /[!@#$%^&*(),.?":{}|<>]/.test(form.value.newPassword)
  }
]);

const passwordsMatch = computed(() => {
  return form.value.newPassword === form.value.confirmPassword;
});

const isPasswordValid = computed(() => {
  return passwordRequirements.value.every(req => req.valid);
});

const isFormValid = computed(() => {
  return form.value.currentPassword &&
         form.value.newPassword &&
         form.value.confirmPassword &&
         isPasswordValid.value &&
         passwordsMatch.value;
});

// Methods
function validatePassword() {
  passwordValidation.value.show = form.value.newPassword.length > 0;
}

async function handlePasswordChange() {
  if (!isFormValid.value) {
    emit('show-message', {
      text: t('profile.security.change_password.form_invalid'),
      type: 'error'
    });
    return;
  }

  loading.value = true;
  try {
    await changePassword({
      current_password: form.value.currentPassword,
      new_password: form.value.newPassword
    });

    emit('show-message', {
      text: t('profile.security.change_password.success'),
      type: 'success'
    });

    // Reset form
    form.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    };
    passwordValidation.value.show = false;

  } catch (error) {
    console.error('Password change error:', error);
    emit('show-message', {
      text: error?.response?.data?.detail || t('profile.security.change_password.error'),
      type: 'error'
    });
  } finally {
    loading.value = false;
  }
}

// Watch for password field focus loss
watch(() => form.value.newPassword, (newVal) => {
  if (!newVal) {
    passwordValidation.value.show = false;
  }
});
</script>

<style scoped>
.profile-security {
  padding: 2rem;
}

.security-section {
  max-width: 500px;
}

.security-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.security-description {
  color: #6b7280;
  margin: 0 0 2rem 0;
  line-height: 1.6;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-weight: 500;
  color: #374151;
  font-size: 0.95rem;
}

.form-input {
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.password-requirements {
  margin-top: 0.75rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.requirements-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.75rem;
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #6b7280;
  transition: color 0.2s;
}

.requirement-item.valid {
  color: #059669;
}

.requirement-item:last-child {
  margin-bottom: 0;
}

.requirement-icon {
  font-weight: bold;
  width: 1rem;
  text-align: center;
}

.requirement-text {
  flex: 1;
}

.error-message {
  color: #dc2626;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.form-actions {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-start;
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1rem;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

@media (max-width: 640px) {
  .profile-security {
    padding: 1rem;
  }
  
  .security-section {
    max-width: 100%;
  }
}
</style>
