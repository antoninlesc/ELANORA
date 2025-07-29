<template>
  <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-content share-modal" @click.stop>
      <div class="modal-header">
        <h2>{{ t('project.share.title', { projectName }) }}</h2>
        <button @click="closeModal" class="close-btn">×</button>
      </div>
      
      <div class="share-options">
        <!-- Send by Email Form -->
        <div class="tab-content">
          <form @submit.prevent="sendProjectInvitation" class="invitation-form">
            <div class="share-form-group">
              <label for="share-email" class="form-label">
                {{ t('project.share.email_label') }}
                <span class="share-required">*</span>
              </label>
              <input
                id="share-email"
                v-model="form.email"
                type="email"
                class="form-input"
                :class="{ error: emailError }"
                :placeholder="t('project.share.email_placeholder')"
                required
              />
              <div v-if="emailError" class="share-error-message">{{ emailError }}</div>
            </div>

            <div class="share-form-group">
              <label for="share-message" class="form-label">
                {{ t('project.share.message_label') }}
              </label>
              <textarea
                id="share-message"
                v-model="form.message"
                class="form-textarea share-form-textarea"
                :placeholder="t('project.share.message_placeholder')"
                rows="3"
              ></textarea>
            </div>

            <div class="share-form-group">
              <label for="share-language" class="form-label">
                {{ t('project.share.language_label') }}
              </label>
              <select id="share-language" v-model="form.language" class="share-form-select">
                <option value="en">English</option>
                <option value="fr">Français</option>
              </select>
            </div>

            <button 
              type="submit" 
              class="btn-primary send-btn" 
              :disabled="sending || !form.email"
            >
              <span v-if="sending">{{ t('project.share.sending') }}</span>
              <span v-else>{{ t('project.share.send_invitation') }}</span>
            </button>
          </form>
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="share-success-message">
          {{ successMessage }}
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="share-error-message">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { sendInvitation as sendInvitationAPI } from '@/api/service/invitationService';
import '@/assets/css/ProjectShareModal.css';

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  projectName: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['close', 'success']);

const { t } = useI18n();

// Form data
const form = ref({
  email: '',
  message: '',
  language: 'fr'
});

// States
const sending = ref(false);
const emailError = ref('');
const successMessage = ref('');
const errorMessage = ref('');

const projectName = computed(() => props.projectName);

const closeModal = () => {
  // Reset form and states
  form.value = {
    email: '',
    message: '',
    language: 'fr'
  };
  emailError.value = '';
  successMessage.value = '';
  errorMessage.value = '';
  emit('close');
};

const sendProjectInvitation = async () => {
  emailError.value = '';
  errorMessage.value = '';
  successMessage.value = '';
  
  if (!form.value.email) {
    emailError.value = t('project.share.email_required');
    return;
  }

  sending.value = true;
  
  try {
    const invitationData = {
      receiver_email: form.value.email,
      project_name: projectName.value,
      message: form.value.message,
      language: form.value.language,
      expires_in_days: 7,
      project_permission: 'read'
    };

    const response = await sendInvitationAPI(invitationData);
    
    if (response.data.success) {
      successMessage.value = t('project.share.invitation_sent_success', { email: form.value.email });
      form.value.email = '';
      form.value.message = '';
      emit('success');
    } else {
      errorMessage.value = response.data.message || t('project.share.invitation_send_error');
    }
  } catch (error) {
    console.error('Error sending invitation:', error);
    errorMessage.value = t('project.share.invitation_send_error');
  } finally {
    sending.value = false;
  }
};
</script>
