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
              :disabled="isSubmitting"
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
import { ref, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage.js';
import { contactService } from '@api/service/contactService.js';

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();

const isSubmitting = ref(false);

const contactForm = reactive({
  email: '',
  request_type: '',
  message: '',
});

const handleSubmit = async () => {
  if (isSubmitting.value) return;

  try {
    isSubmitting.value = true;

    await contactService.sendContactMessage(contactForm);

    eventMessageStore.addMessage('contact.success_message', 'success');
    
    // Reset form
    contactForm.email = '';
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

<style scoped>
.contact-container-wrapper {
  min-height: 100vh;
  background: linear-gradient(to bottom right, #eff6ff, #e0e7ff);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.contact-container {
  width: 100%;
  max-width: 32rem;
}

.contact-card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  padding: 2rem;
}

.contact-header {
  text-align: center;
  margin-bottom: 2rem;
}

.contact-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.5rem;
}

.contact-subtitle {
  color: #4b5563;
  font-size: 1rem;
  line-height: 1.625;
}

.contact-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  font-size: 1rem;
}

.form-group input::placeholder,
.form-group textarea::placeholder {
  color: #9ca3af;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input:disabled,
.form-group select:disabled,
.form-group textarea:disabled {
  background-color: #f9fafb;
  color: #6b7280;
}

.form-group textarea {
  resize: vertical;
  min-height: 120px;
}

.contact-btn {
  width: 100%;
  background-color: #2563eb;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.contact-btn:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.contact-btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.5);
}

.contact-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.contact-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #eff6ff;
  border-radius: 0.375rem;
}

.contact-note {
  font-size: 0.875rem;
  color: #1d4ed8;
  text-align: center;
}

.back-to-site {
  margin-top: 1.5rem;
  text-align: center;
}

.back-link {
  color: #2563eb;
  font-weight: 500;
  font-size: 0.875rem;
  text-decoration: none;
}

.back-link:hover {
  color: #1d4ed8;
}
</style>
