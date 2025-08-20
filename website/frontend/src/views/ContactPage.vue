<template>
  <div class="contact-container-wrapper">
    <div class="contact-container">
      <div class="contact-card">
        <div class="contact-header">
          <h1 class="contact-title">{{ t('contact.title') }}</h1>
          <p class="contact-subtitle">{{ t('contact.subtitle') }}</p>
        </div>

        <form class="contact-form" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="email">{{ t('contact.email') }} *</label>
            <input
              id="email"
              v-model="contactForm.email"
              type="email"
              required
              :placeholder="t('contact.email_placeholder')"
              :disabled="isSubmitting || isAuthenticated"
              :readonly="isAuthenticated"
            />
          </div>

          <div class="form-group">
            <label for="request_type">{{ t('contact.request_type') }} *</label>
            <select
              id="request_type"
              v-model="contactForm.request_type"
              required
              :disabled="isSubmitting"
            >
              <option value="">{{ t('contact.select_request_type') }}</option>
              <option value="bug_report">{{ t('contact.bug_report') }}</option>
              <option value="feature_request">{{ t('contact.feature_request') }}</option>
              <option value="technical_support">{{ t('contact.technical_support') }}</option>
              <option value="account_issue">{{ t('contact.account_issue') }}</option>
              <option value="general_inquiry">{{ t('contact.general_inquiry') }}</option>
              <option value="other">{{ t('contact.other') }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="message">{{ t('contact.message') }} *</label>
            <textarea
              id="message"
              v-model="contactForm.message"
              required
              rows="6"
              :placeholder="t('contact.message_placeholder')"
              :disabled="isSubmitting"
            ></textarea>
          </div>

          <button
            type="submit"
            class="btn-primary contact-btn"
            :disabled="isSubmitting"
          >
            <span v-if="isSubmitting">{{ t('contact.sending') }}</span>
            <span v-else>{{ t('contact.send') }}</span>
          </button>
        </form>

        <div class="contact-info">
          <p class="contact-note">{{ t('contact.response_note') }}</p>
        </div>

        <div class="back-to-site">
          <router-link to="/" class="back-link">
            ← {{ t('contact.back_to_site') }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage.js';
import { useUserStore } from '@stores/user.js';
import { contactService } from '@api/service/contactService.js';
import '@assets/css/contact-page.css';

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();
const userStore = useUserStore();

const isSubmitting = ref(false);

const contactForm = reactive({
  email: '',
  request_type: '',
  message: '',
});

// Computed property to check if user is authenticated
const isAuthenticated = computed(() => userStore.user && userStore.user.user_id);

// Computed property to get user email
const userEmail = computed(() => userStore.user?.email || '');

// Initialize form with user email if authenticated
onMounted(async () => {
  // Ensure authentication is verified first
  if (!userStore.authState.initialized) {
    await userStore.verifyAuthentication();
  }
  
  if (isAuthenticated.value && userEmail.value) {
    contactForm.email = userEmail.value;
  }
});

// Watch for authentication state changes
watch([isAuthenticated, userEmail], ([isAuth, email]) => {
  if (isAuth && email && !contactForm.email) {
    contactForm.email = email;
  }
});

const handleSubmit = async () => {
  if (isSubmitting.value) return;

  try {
    isSubmitting.value = true;

    await contactService.sendContactMessage(contactForm);

    eventMessageStore.addMessage('contact.success_message', 'success');
    
    // Reset form, but keep email if user is authenticated
    if (!isAuthenticated.value) {
      contactForm.email = '';
    }
    contactForm.request_type = '';
    contactForm.message = '';
  } catch (error) {
    console.error('Error sending contact message:', error);
    eventMessageStore.addMessage(
      'contact.error_message',
      'error'
    );
  } finally {
    isSubmitting.value = false;
  }
};
</script>


