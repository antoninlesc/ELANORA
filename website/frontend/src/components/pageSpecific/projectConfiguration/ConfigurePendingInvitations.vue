<template>
  <div class="configure-pending-invitations">
    <div class="invitations-header">
      <h3>{{ t('projectSettings.invitations.title') }}</h3>
      <button
        v-if="canManageInvitations"
        class="btn-send-invitation"
        @click="showInviteModal = true"
      >
        <span class="invite-icon">✉</span>
        {{ t('projectSettings.invitations.send_invitation') }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>{{ t('common.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button class="btn-retry" @click="loadInvitations">
        {{ t('common.retry') }}
      </button>
    </div>

    <!-- Invitations List -->
    <div v-else class="invitations-content">
      <div v-if="invitations.length === 0" class="empty-state">
        <div class="empty-icon">📧</div>
        <p>{{ t('projectSettings.invitations.no_invitations') }}</p>
        <small>{{ t('projectSettings.invitations.no_invitations_desc') }}</small>
      </div>
      
      <div v-else class="invitations-list">
        <div
          v-for="invitation in invitations"
          :key="invitation.invitation_id"
          class="invitation-card"
        >
          <div class="invitation-info">
            <div class="invitation-email">
              <span class="email-icon">📧</span>
              <div class="email-details">
                <div class="email-address">{{ invitation.receiver_email }}</div>
                <div class="invitation-date">
                  {{ t('projectSettings.invitations.sent_on') }} 
                  {{ formatDate(invitation.created_at) }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="invitation-permission">
            <span class="permission-badge" :class="invitation.project_permission">
              {{ t(`projectSettings.permissions.${invitation.project_permission}`) }}
            </span>
          </div>
          
          <div class="invitation-status">
            <span class="status-badge" :class="invitation.status">
              {{ t(`projectSettings.invitations.status.${invitation.status}`) }}
            </span>
          </div>
          
          <div class="invitation-actions">
            <button
              v-if="canCancelInvitation(invitation)"
              class="btn-resend"
              :disabled="processingInvitations.has(invitation.invitation_id)"
              @click="resendInvitation(invitation)"
              :title="t('projectSettings.invitations.resend')"
            >
              🔄
            </button>
            <button
              v-if="canCancelInvitation(invitation)"
              class="btn-cancel"
              :disabled="processingInvitations.has(invitation.invitation_id)"
              @click="confirmCancelInvitation(invitation)"
              :title="t('projectSettings.invitations.cancel')"
            >
              ×
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Send Invitation Modal -->
    <div v-if="showInviteModal" class="modal-overlay" @click="closeInviteModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>{{ t('projectSettings.invitations.send_modal.title') }}</h4>
          <button class="modal-close" @click="closeInviteModal">×</button>
        </div>
        
        <form @submit.prevent="sendInvitation" class="invite-form">
          <div class="form-group">
            <label for="inviteEmail">{{ t('projectSettings.invitations.send_modal.email') }}</label>
            <input
              id="inviteEmail"
              v-model="newInvitation.email"
              type="email"
              class="form-input"
              required
              :placeholder="t('projectSettings.invitations.send_modal.email_placeholder')"
            />
          </div>
          
          <div class="form-group">
            <label for="invitePermission">{{ t('projectSettings.invitations.send_modal.permission') }}</label>
            <select id="invitePermission" v-model="newInvitation.permission" class="form-select" required>
              <option value="read">{{ t('projectSettings.permissions.read') }}</option>
              <option value="write">{{ t('projectSettings.permissions.write') }}</option>
              <option value="admin">{{ t('projectSettings.permissions.admin') }}</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="inviteMessage">{{ t('projectSettings.invitations.send_modal.message') }}</label>
            <textarea
              id="inviteMessage"
              v-model="newInvitation.message"
              class="form-textarea"
              rows="3"
              :placeholder="t('projectSettings.invitations.send_modal.message_placeholder')"
            ></textarea>
          </div>
          
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="closeInviteModal">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-submit" :disabled="sendingInvitation">
              <span v-if="sendingInvitation" class="loading-text">{{ t('common.sending') }}...</span>
              <span v-else>{{ t('projectSettings.invitations.send') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Cancel Invitation Modal -->
    <div v-if="showCancelModal" class="modal-overlay" @click="closeCancelModal">
      <div class="modal-content confirm-modal" @click.stop>
        <div class="modal-header">
          <h4>{{ t('projectSettings.invitations.cancel_modal.title') }}</h4>
        </div>
        
        <div class="modal-body">
          <p>{{ t('projectSettings.invitations.cancel_modal.message', { email: invitationToCancel?.receiver_email }) }}</p>
          <p class="warning-text">{{ t('projectSettings.invitations.cancel_modal.warning') }}</p>
        </div>
        
        <div class="modal-actions">
          <button class="btn-cancel" @click="closeCancelModal">
            {{ t('common.no') }}
          </button>
          <button class="btn-danger" :disabled="cancelingInvitation" @click="cancelInvitation">
            <span v-if="cancelingInvitation" class="loading-text">{{ t('common.canceling') }}...</span>
            <span v-else>{{ t('common.yes_cancel') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useEventMessageStore } from '@/stores/eventMessage';
import { useProjectStore } from '@/stores/project';
import { 
  getProjectInvitations, 
  sendInvitation as sendInvitationAPI, 
  resendInvitation as resendInvitationAPI, 
  cancelInvitation as cancelInvitationAPI 
} from '@/api/service/invitationService';

const { t } = useI18n();
const route = useRoute();
const eventMessageStore = useEventMessageStore();
const projectStore = useProjectStore();

const projectId = computed(() => Number(route.params.projectId));
const projectName = computed(() => projectStore.projectName);

// Props - in a real implementation, you'd get the current user role from a store
const currentUserRole = ref('admin'); // This should come from props or store

// Reactive state
const invitations = ref([]);
const loading = ref(false);
const error = ref('');

// Modal states
const showInviteModal = ref(false);
const showCancelModal = ref(false);
const invitationToCancel = ref(null);

// Operation states
const processingInvitations = ref(new Set());
const sendingInvitation = ref(false);
const cancelingInvitation = ref(false);

// Form data
const newInvitation = reactive({
  email: '',
  permission: 'read',
  message: ''
});

// Computed properties
const canManageInvitations = computed(() => {
  return ['admin', 'owner'].includes(currentUserRole.value);
});

// Methods
const loadInvitations = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    if (!projectName.value) {
      console.warn('No project name available');
      invitations.value = [];
      return;
    }
    
    const response = await getProjectInvitations(projectName.value);
    // La réponse du backend est une InvitationListResponse avec { invitations: [], total: number }
    invitations.value = response.data.invitations || [];
    
  } catch (err) {
    console.error('Error loading invitations:', err);
    error.value = err.response?.data?.detail || t('projectSettings.invitations.load_error');
    invitations.value = [];
  } finally {
    loading.value = false;
  }
};

const canCancelInvitation = (invitation) => {
  return ['admin', 'owner'].includes(currentUserRole.value) && 
         ['pending'].includes(invitation.status);
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

const closeInviteModal = () => {
  showInviteModal.value = false;
  newInvitation.email = '';
  newInvitation.permission = 'read';
  newInvitation.message = '';
};

const sendInvitation = async () => {
  sendingInvitation.value = true;
  
  try {
    if (!projectName.value) {
      eventMessageStore.addMessage('projectSettings.invitations.no_project_error', 'error');
      return;
    }

    const invitationData = {
      receiver_email: newInvitation.email,
      project_name: projectName.value,
      message: newInvitation.message,
      language: 'fr', // You might want to get this from i18n or user preferences
      expires_in_days: 7,
      project_permission: newInvitation.permission
    };

    const response = await sendInvitationAPI(invitationData);
    
    if (response.data.success !== false) {
      eventMessageStore.addMessage('projectSettings.invitations.invitation_sent', 'success');
      closeInviteModal();
      await loadInvitations(); // Refresh the list
    } else {
      eventMessageStore.addMessage('projectSettings.invitations.send_error', 'error');
    }
  } catch (err) {
    console.error('Error sending invitation:', err);
    eventMessageStore.addMessage(
      err.response?.data?.detail || 'projectSettings.invitations.send_error',
      'error'
    );
  } finally {
    sendingInvitation.value = false;
  }
};

const resendInvitation = async (invitation) => {
  processingInvitations.value.add(invitation.invitation_id);
  
  try {
    await resendInvitationAPI(invitation.invitation_id);
    eventMessageStore.addMessage('projectSettings.invitations.invitation_resent', 'success');
    await loadInvitations();
  } catch (err) {
    console.error('Error resending invitation:', err);
    eventMessageStore.addMessage(
      err.response?.data?.detail || 'projectSettings.invitations.resend_error', 
      'error'
    );
  } finally {
    processingInvitations.value.delete(invitation.invitation_id);
  }
};

const confirmCancelInvitation = (invitation) => {
  invitationToCancel.value = invitation;
  showCancelModal.value = true;
};

const closeCancelModal = () => {
  showCancelModal.value = false;
  invitationToCancel.value = null;
};

const cancelInvitation = async () => {
  if (!invitationToCancel.value) return;
  
  cancelingInvitation.value = true;
  
  try {
    await cancelInvitationAPI(invitationToCancel.value.invitation_id);
    eventMessageStore.addMessage('projectSettings.invitations.invitation_canceled', 'success');
    closeCancelModal();
    await loadInvitations(); // Refresh the list
  } catch (err) {
    console.error('Error canceling invitation:', err);
    eventMessageStore.addMessage(
      err.response?.data?.detail || 'projectSettings.invitations.cancel_error', 
      'error'
    );
  } finally {
    cancelingInvitation.value = false;
  }
};

watch(
  projectName,
  async () => {
    await loadInvitations();
  },
  { immediate: true }
);

// Lifecycle
onMounted(async () => {
  // Ensure project is loaded before loading invitations
  if (!projectStore.currentProject && !projectStore.isLoading) {
    projectStore.initializeFromStorage();
  }
  
  // Wait a bit for project to be loaded if needed
  if (!projectName.value && projectStore.isLoading) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  loadInvitations();
});

// Expose methods for parent components if needed
defineExpose({
  loadInvitations,
  invitations
});
</script>

<style scoped>
.configure-pending-invitations {
  padding: 0;
}

.invitations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.invitations-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
}

.btn-send-invitation {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-send-invitation:hover {
  background: #059669;
  transform: translateY(-1px);
}

.invite-icon {
  font-size: 1rem;
}

.loading-state, .error-state {
  text-align: center;
  padding: 2rem 1rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid #10b981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #dc2626;
  margin-bottom: 1rem;
}

.btn-retry {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.btn-retry:hover {
  background: #e5e7eb;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state p {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.empty-state small {
  font-size: 0.875rem;
  color: #9ca3af;
}

.invitations-list {
  display: grid;
  gap: 1rem;
}

.invitation-card {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  align-items: center;
  gap: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.2s ease;
}

.invitation-card:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.invitation-email {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.email-icon {
  font-size: 1.25rem;
}

.email-details {
  flex: 1;
}

.email-address {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.125rem;
}

.invitation-date {
  font-size: 0.875rem;
  color: #6b7280;
}

.permission-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.permission-badge.read {
  background: #dbeafe;
  color: #1e40af;
}

.permission-badge.write {
  background: #d1fae5;
  color: #047857;
}

.permission-badge.admin {
  background: #fef3c7;
  color: #92400e;
}

.status-badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.accepted {
  background: #d1fae5;
  color: #047857;
}

.status-badge.declined {
  background: #fee2e2;
  color: #dc2626;
}

.status-badge.expired {
  background: #f3f4f6;
  color: #6b7280;
}

.invitation-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-resend, .btn-cancel {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-resend {
  background: #dbeafe;
  color: #1e40af;
}

.btn-resend:hover:not(:disabled) {
  background: #bfdbfe;
  transform: scale(1.1);
}

.btn-cancel {
  background: #fee2e2;
  color: #dc2626;
  font-weight: bold;
}

.btn-cancel:hover:not(:disabled) {
  background: #fecaca;
  transform: scale(1.1);
}

.btn-resend:disabled, .btn-cancel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal Styles */
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
  backdrop-filter: blur(2px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 1.5rem;
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.modal-header h4 {
  margin: 0;
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.modal-close:hover {
  color: #374151;
  background: #f3f4f6;
}

.invite-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-input, .form-select, .form-textarea {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions, .modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.confirm-modal .modal-body {
  margin-bottom: 1.5rem;
}

.confirm-modal .modal-body p {
  margin: 0 0 0.75rem 0;
  color: #374151;
  line-height: 1.5;
}

.warning-text {
  font-size: 0.875rem;
  color: #dc2626;
  font-weight: 500;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-text::after {
  content: '';
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
