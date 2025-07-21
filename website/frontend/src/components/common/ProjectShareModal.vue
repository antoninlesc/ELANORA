<template>
  <div v-if="show" class="modal-overlay" @click="closeModal">
    <div class="modal-content share-modal" @click.stop>
      <div class="modal-header">
        <h2>{{ t('project.share.title', { projectName }) }}</h2>
        <button @click="closeModal" class="close-btn">×</button>
      </div>
      
      <div class="share-options">
        <div class="share-tabs">
          <button 
            :class="['tab-btn', { active: activeTab === 'email' }]"
            @click="activeTab = 'email'"
          >
            <span class="tab-icon">📧</span>
            {{ t('project.share.send_by_email') }}
          </button>
          <button 
            :class="['tab-btn', { active: activeTab === 'copy' }]"
            @click="activeTab = 'copy'"
          >
            <span class="tab-icon">🔗</span>
            {{ t('project.share.get_code') }}
          </button>
        </div>

                <!-- Send by Email Tab -->
        <div v-if="activeTab === 'email'" class="tab-content">
          <form @submit.prevent="sendProjectInvitation" class="invitation-form">
            <div class="form-group">
              <label for="share-email" class="form-label">
                {{ t('project.share.email_label') }}
                <span class="required">*</span>
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
              <div v-if="emailError" class="error-message">{{ emailError }}</div>
            </div>

            <div class="form-group">
              <label for="share-message" class="form-label">
                {{ t('project.share.message_label') }}
              </label>
              <textarea
                id="share-message"
                v-model="form.message"
                class="form-textarea"
                :placeholder="t('project.share.message_placeholder')"
                rows="3"
              ></textarea>
            </div>

            <div class="form-group">
              <label for="share-language" class="form-label">
                {{ t('project.share.language_label') }}
              </label>
              <select id="share-language" v-model="form.language" class="form-select">
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

        <!-- Copy Code Tab -->
        <div v-if="activeTab === 'copy'" class="tab-content">
          <div v-if="!invitationCode" class="generate-code-section">
            <p class="info-message">{{ t('project.share.generate_code_info') }}</p>
            <button 
              @click="generateInvitationCode" 
              class="btn-secondary generate-btn"
              :disabled="generating"
            >
              <span v-if="generating">{{ t('project.share.generating') }}</span>
              <span v-else>{{ t('project.share.generate_code') }}</span>
            </button>
          </div>
          
          <div v-else class="code-display-section">
            <p class="info-message">{{ t('project.share.code_ready_info') }}</p>
            <div class="code-container">
              <input 
                ref="codeInput"
                v-model="invitationCode" 
                class="code-input" 
                readonly
              />
              <button @click="copyToClipboard" class="copy-btn" :class="{ copied: copied }">
                <span v-if="copied">✓</span>
                <span v-else>📋</span>
              </button>
            </div>
            <p class="code-instructions">{{ t('project.share.code_instructions') }}</p>
            <button 
              @click="generateNewCode" 
              class="btn-secondary refresh-btn"
            >
              {{ t('project.share.generate_new_code') }}
            </button>
          </div>
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="success-message">
          {{ successMessage }}
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { sendInvitation as sendInvitationAPI, generateInvitationCode as generateInvitationCodeAPI } from '@/api/service/invitationService';

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

// Tab management
const activeTab = ref('email');

// Form data
const form = ref({
  email: '',
  message: '',
  language: 'fr'
});

// States
const sending = ref(false);
const generating = ref(false);
const copied = ref(false);
const emailError = ref('');
const successMessage = ref('');
const errorMessage = ref('');

// Invitation code
const invitationCode = ref('');
const codeInput = ref(null);

const projectName = computed(() => props.projectName);

const closeModal = () => {
  // Reset form and states
  form.value = {
    email: '',
    message: '',
    language: 'fr'
  };
  activeTab.value = 'email';
  emailError.value = '';
  successMessage.value = '';
  errorMessage.value = '';
  invitationCode.value = '';
  copied.value = false;
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
      project_permission: 'write',  // Utiliser 'write' au lieu de 'READ_WRITE'
      send_email: true  // Explicitement indiquer qu'on veut envoyer un email
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

const generateInvitationCode = async () => {
  errorMessage.value = '';
  generating.value = true;
  
  try {
    // Utiliser l'endpoint spécialisé pour générer un code sans email
    const invitationData = {
      project_name: projectName.value,
      expires_in_days: 7,
      project_permission: 'write'  // Utiliser 'write' au lieu de 'READ_WRITE'
    };

    const response = await generateInvitationCodeAPI(invitationData);
    
    if (response.data.success && response.data.invitation_code) {
      invitationCode.value = response.data.invitation_code;
    } else {
      errorMessage.value = response.data.message || t('project.share.code_generation_error');
    }
  } catch (error) {
    console.error('Error generating invitation code:', error);
    errorMessage.value = t('project.share.code_generation_error');
  } finally {
    generating.value = false;
  }
};

const generateNewCode = () => {
  invitationCode.value = '';
  generateInvitationCode();
};

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(invitationCode.value);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    // Fallback pour les anciens navigateurs
    console.warn('Could not copy to clipboard:', err);
    if (codeInput.value) {
      codeInput.value.select();
      document.execCommand('copy');
      copied.value = true;
      setTimeout(() => {
        copied.value = false;
      }, 2000);
    }
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.share-modal {
  background: white;
  border-radius: 12px;
  padding: 0;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #374151;
  background: #f3f4f6;
  border-radius: 6px;
}

.share-options {
  padding: 24px;
}

.share-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  flex: 1;
  padding: 12px 16px;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  color: #6b7280;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab-btn:hover:not(.active) {
  color: #374151;
  background: #f9fafb;
}

.tab-icon {
  font-size: 18px;
}

.tab-content {
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #374151;
}

.required {
  color: #ef4444;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input.error {
  border-color: #ef4444;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.send-btn {
  width: 100%;
  margin-top: 8px;
}

.generate-code-section,
.code-display-section {
  text-align: center;
}

.info-message {
  margin-bottom: 16px;
  color: #6b7280;
  line-height: 1.5;
}

.generate-btn,
.refresh-btn {
  margin-top: 8px;
}

.code-container {
  display: flex;
  gap: 8px;
  margin: 16px 0;
  align-items: center;
}

.code-input {
  flex: 1;
  padding: 12px;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  text-align: center;
  font-size: 16px;
  color: #1f2937;
}

.copy-btn {
  padding: 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: #2563eb;
}

.copy-btn.copied {
  background: #10b981;
}

.code-instructions {
  margin-top: 12px;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.4;
}

.success-message {
  margin-top: 16px;
  padding: 12px;
  background: #dcfce7;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  color: #166534;
  font-weight: 500;
}

.error-message {
  margin-top: 8px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  color: #dc2626;
  font-weight: 500;
}
</style>
