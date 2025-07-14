<template>
  <div class="admin-invitation-page">
    <AppHeader instance-name="ELANORA Admin" />
    
    <div class="admin-container">
      <div class="admin-header">
        <h1 class="admin-title">{{ t('invitation.send_title') }}</h1>
        <p class="admin-description">{{ t('invitation.send_description') }}</p>
      </div>

      <!-- Send Invitation Form -->
      <div class="invitation-form-card">
        <form        @submit.prevent="handleSendInvitation" class="invitation-form">
          <div class="form-group">
            <label for="email" class="form-label">
              {{ t('invitation.email_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="email"
              v-model="form.email"
              type="email"
              class="form-input"
              :class="{ 'error': emailError }"
              :placeholder="t('invitation.email_placeholder')"
              required
            />
            <div v-if="emailError" class="error-message">{{ emailError }}</div>
          </div>

          <div class="form-group">
            <label for="project" class="form-label">
              {{ t('invitation.project_label') }}
              <span class="required">*</span>
            </label>
            <select 
              id="project"
              v-model="form.projectId"
              class="form-select"
              :class="{ 'error': projectError }"
              required
            >
              <option value="">{{ t('invitation.select_project') }}</option>
              <option 
                v-for="project in projects" 
                :key="project.project_id" 
                :value="project.project_id"
              >
                {{ project.project_name }}
              </option>
            </select>
            <div v-if="projectError" class="error-message">{{ projectError }}</div>
          </div>

          <div class="form-group">
            <label for="message" class="form-label">
              {{ t('invitation.message_label') }}
            </label>
            <textarea 
              id="message"
              v-model="form.message"
              class="form-textarea"
              :placeholder="t('invitation.message_placeholder')"
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="language" class="form-label">
              {{ t('invitation.language_label') }}
            </label>
            <select 
              id="language"
              v-model="form.language"
              class="form-select"
            >
              <option value="en">English</option>
              <option value="fr">Français</option>
            </select>
          </div>

          <button 
            type="submit" 
            class="btn-primary send-btn" 
            :disabled="sending || !form.email || !form.projectId"
          >
            <span v-if="sending">{{ t('invitation.sending') }}</span>
            <span v-else>{{ t('invitation.send_button') }}</span>
          </button>
        </form>
      </div>

      <!-- Sent Invitations List -->
      <div class="sent-invitations-card">
        <h2 class="section-title">Recently Sent Invitations</h2>
        
        <div v-if="loadingInvitations" class="loading-message">
          Loading invitations...
        </div>
        
        <div v-else-if="sentInvitations.length === 0" class="empty-message">
          No invitations sent yet.
        </div>
        
        <div v-else class="invitations-list">
          <div 
            v-for="invitation in sentInvitations" 
            :key="invitation.invitation_id"
            class="invitation-item"
          >
            <div class="invitation-details">
              <div class="invitation-email">{{ invitation.receiver_email }}</div>
              <div class="invitation-meta">
                <span class="invitation-status" :class="invitation.status">
                  {{ invitation.status }}
                </span>
                <span class="invitation-date">
                  {{ formatDate(invitation.created_at) }}
                </span>
              </div>
            </div>
            <div class="invitation-code">
              <code>{{ invitation.invitation_id }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage';
import { sendInvitation, getSentInvitations } from '@/api/service/invitationService';
import { getProjects } from '@/api/service/projectService';
import AppHeader from '@components/layout/AppHeader.vue';

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();

// Reactive data
const form = ref({
  email: '',
  projectId: '',
  message: '',
  language: 'en'
});

const sending = ref(false);
const emailError = ref('');
const projectError = ref('');
const sentInvitations = ref([]);
const loadingInvitations = ref(false);
const projects = ref([]);

// Load data on mount
onMounted(async () => {
  await Promise.all([
    loadSentInvitations(),
    loadProjects()
  ]);
});

const loadProjects = async () => {
  try {
    const response = await getProjects();
    projects.value = response.data || [];
  } catch (error) {
    console.error('Failed to load projects:', error);
    eventMessageStore.addMessage(t('project.load_error'), 'error');
  }
};

const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const handleSendInvitation = async () => {
  emailError.value = '';
  projectError.value = '';

  // Validate email
  if (!validateEmail(form.value.email)) {
    emailError.value = t('invitation.invalid_email');
    return;
  }

  // Validate project selection
  if (!form.value.projectId) {
    projectError.value = t('invitation.project_required');
    return;
  }

  sending.value = true;

  try {
    const response = await sendInvitation({
      receiver_email: form.value.email,
      project_id: parseInt(form.value.projectId),
      message: form.value.message || null,
      expires_in_days: 7
    });

    if (response.data.success) {
      eventMessageStore.addMessage(t('invitation.success'), 'success');
      
      // Reset form
      form.value.email = '';
      form.value.projectId = '';
      form.value.message = '';
      
      // Reload sent invitations
      await loadSentInvitations();
    } else {
      eventMessageStore.addMessage(
        response.data.message || t('invitation.error'),
        'error'
      );
    }
  } catch (error) {
    console.error('Failed to send invitation:', error);
    eventMessageStore.addMessage(
      error.response?.data?.detail || t('invitation.error'),
      'error'
    );
  } finally {
    sending.value = false;
  }
};

const loadSentInvitations = async () => {
  loadingInvitations.value = true;
  
  try {
    const response = await getSentInvitations();
    sentInvitations.value = response.data.invitations || [];
  } catch (error) {
    console.error('Failed to load sent invitations:', error);
    sentInvitations.value = [];
  } finally {
    loadingInvitations.value = false;
  }
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
};
</script>

<style scoped>
.admin-invitation-page {
  min-height: 100vh;
  background: #f8fafc;
}

.admin-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.admin-header {
  text-align: center;
  margin-bottom: 3rem;
}

.admin-title {
  color: #1f2937;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.admin-description {
  color: #6b7280;
  font-size: 1.125rem;
  margin: 0;
}

.invitation-form-card,
.sent-invitations-card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  padding: 2rem;
  margin-bottom: 2rem;
}

.section-title {
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.invitation-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-label {
  color: #374151;
  font-weight: 500;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.required {
  color: #ef4444;
  margin-left: 0.25rem;
}

.form-input,
.form-textarea,
.form-select {
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.2s;
  background: white;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.btn-primary {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  padding: 0.875rem 2rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.send-btn {
  align-self: flex-start;
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.loading-message,
.empty-message {
  text-align: center;
  color: #6b7280;
  padding: 2rem;
  font-style: italic;
}

.invitations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.invitation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #f9fafb;
}

.invitation-details {
  flex: 1;
}

.invitation-email {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.invitation-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
}

.invitation-status {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.invitation-status.pending {
  background: #fef3c7;
  color: #92400e;
}

.invitation-status.accepted {
  background: #d1fae5;
  color: #065f46;
}

.invitation-status.expired {
  background: #fee2e2;
  color: #991b1b;
}

.invitation-date {
  color: #6b7280;
}

.invitation-code {
  font-family: 'Courier New', monospace;
  background: #f3f4f6;
  padding: 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .admin-container {
    padding: 1rem;
  }

  .invitation-form-card,
  .sent-invitations-card {
    padding: 1.5rem;
  }

  .invitation-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .invitation-code {
    align-self: stretch;
    text-align: center;
  }
}
</style>
