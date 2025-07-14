<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <img src="/images/ELANora-logo.png" alt="ELANORA Logo" class="register-logo" />
        <h1 class="register-title">{{ t('register.title') }}</h1>
        <p v-if="invitationValid" class="register-subtitle invitation-welcome">
          {{ t('register.invitation_welcome', { senderName: invitationInfo?.sender_username || 'Un administrateur' }) }}
        </p>
        <p v-else class="register-subtitle">
          {{ t('register.subtitle') }}
        </p>
      </div>

      <!-- Invitation Code Section -->
      <div v-if="!invitationValid" class="invitation-section">
        <div class="form-group">
          <label for="invitation-code" class="form-label">
            {{ t('register.invitation_code_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="invitation-code"
            v-model="invitationCode"
            type="text"
            class="form-input"
            :class="{ 'error': invitationError }"
            :placeholder="t('register.invitation_code_placeholder')"
            @input="validateInvitationCode"
          />
          <div v-if="invitationError" class="error-message">{{ invitationError }}</div>
          <div v-if="invitationValidating" class="info-message">
            {{ t('register.validating_invitation') }}
          </div>
          <div v-if="invitationValid" class="success-message">
            {{ t('register.invitation_valid') }}
          </div>
        </div>
      </div>

      <!-- Registration Form -->
      <form v-if="invitationValid" @submit.prevent="handleRegister" class="register-form">
        <div class="form-row">
          <div class="form-group">
            <label for="first-name" class="form-label">
              {{ t('register.first_name_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="first-name"
              v-model="form.firstName"
              type="text"
              class="form-input"
              :placeholder="t('register.first_name_placeholder')"
              required
            />
          </div>
          <div class="form-group">
            <label for="last-name" class="form-label">
              {{ t('register.last_name_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="last-name"
              v-model="form.lastName"
              type="text"
              class="form-input"
              :placeholder="t('register.last_name_placeholder')"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label for="username" class="form-label">
            {{ t('register.username_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="username"
            v-model="form.username"
            type="text"
            class="form-input"
            :placeholder="t('register.username_placeholder')"
            required
          />
        </div>

        <div class="form-group">
          <label for="email" class="form-label">
            {{ t('register.email_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="email"
            v-model="form.email"
            type="email"
            class="form-input"
            :placeholder="t('register.email_placeholder')"
            :value="invitationInfo?.receiver_email || ''"
            :readonly="!!invitationInfo?.receiver_email"
            required
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="password" class="form-label">
              {{ t('register.password_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              :placeholder="t('register.password_placeholder')"
              required
            />
          </div>
          <div class="form-group">
            <label for="confirm-password" class="form-label">
              {{ t('register.confirm_password_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="confirm-password"
              v-model="form.confirmPassword"
              type="password"
              class="form-input"
              :placeholder="t('register.confirm_password_placeholder')"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label for="affiliation" class="form-label">
            {{ t('register.affiliation_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="affiliation"
            v-model="form.affiliation"
            type="text"
            class="form-input"
            :placeholder="t('register.affiliation_placeholder')"
            required
          />
        </div>

        <div class="form-group">
          <label for="department" class="form-label">
            {{ t('register.department_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="department"
            v-model="form.department"
            type="text"
            class="form-input"
            :placeholder="t('register.department_placeholder')"
            required
          />
        </div>

        <button 
          type="submit" 
          class="btn-primary register-btn" 
          :disabled="loading || !invitationValid"
        >
          <span v-if="loading">{{ t('register.registering') }}</span>
          <span v-else>{{ t('register.submit') }}</span>
        </button>
      </form>

      <div class="register-footer">
        <p>
          {{ t('register.already_have_account') }}
          <router-link to="/" class="link">{{ t('register.login_here') }}</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage';
import { validateInvitation } from '@/api/service/invitationService';
import { registerWithInvitation } from '@/api/service/authService';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const eventMessageStore = useEventMessageStore();

// Reactive data
const invitationCode = ref('');
const invitationValid = ref(false);
const invitationValidating = ref(false);
const invitationError = ref('');
const invitationInfo = ref(null);
const loading = ref(false);

const form = ref({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  affiliation: '',
  department: ''
});

// Check for invitation code in URL params
onMounted(() => {
  const invitationParam = route.query.invitation;
  if (invitationParam) {
    invitationCode.value = invitationParam;
    validateInvitationCode();
  }
});

// Watch for changes in invitation code
watch(invitationCode, (newValue) => {
  if (newValue && newValue.length > 0) {
    invitationError.value = '';
  }
});

const validateInvitationCode = async () => {
  if (!invitationCode.value || invitationCode.value.length === 0) {
    invitationError.value = t('register.invitation_code_required');
    invitationValid.value = false;
    return;
  }

  invitationValidating.value = true;
  invitationError.value = '';

  try {
    const response = await validateInvitation(invitationCode.value);
    if (response.data.valid) {
      invitationValid.value = true;
      invitationInfo.value = response.data.invitation;
      
      // Pre-fill email if available
      if (invitationInfo.value?.receiver_email) {
        form.value.email = invitationInfo.value.receiver_email;
      }
      
      eventMessageStore.addMessage(t('register.invitation_valid'), 'success');
    } else {
      invitationValid.value = false;
      invitationError.value = response.data.message || t('register.invitation_invalid');
    }
  } catch (error) {
    invitationValid.value = false;
    invitationError.value = error.response?.data?.detail || t('register.invitation_validation_error');
  } finally {
    invitationValidating.value = false;
  }
};

const handleRegister = async () => {
  // Validate form
  if (form.value.password !== form.value.confirmPassword) {
    eventMessageStore.addMessage(t('register.passwords_no_match'), 'error');
    return;
  }

  if (form.value.password.length < 8) {
    eventMessageStore.addMessage(t('register.password_too_short'), 'error');
    return;
  }

  loading.value = true;

  try {
    // API call for registration with invitation
    const payload = {
      invitation_code: invitationCode.value,
      first_name: form.value.firstName,
      last_name: form.value.lastName,
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
      affiliation: form.value.affiliation,
      department: form.value.department,
    };
    await registerWithInvitation(payload);
    eventMessageStore.addMessage(t('register.success'), 'success');
    router.push({ name: 'LoginPage' });
  } catch (error) {
    console.error('Registration error:', error);
    eventMessageStore.addMessage(
      error?.response?.data?.detail || t('register.error'),
      'error'
    );
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped src="@/assets/css/register.css"></style>
