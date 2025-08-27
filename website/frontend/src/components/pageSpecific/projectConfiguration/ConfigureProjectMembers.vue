<template>
  <div class="configure-project-members">
    <div class="members-header">
      <h3>{{ t('projectSettings.members.title') }}</h3>
      <button
        v-if="canAddUsers"
        class="btn-add-member"
        @click="showAddUserModal = true"
      >
        <span class="add-icon">+</span>
        {{ t('projectSettings.members.add_member') }}
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
      <button class="btn-retry" @click="loadUsers">
        {{ t('common.retry') }}
      </button>
    </div>

    <!-- Members List -->
    <div v-else class="members-content">
      <div v-if="users.length === 0" class="empty-state">
        <div class="empty-icon">👥</div>
        <p>{{ t('projectSettings.members.no_members') }}</p>
        <small>{{ t('projectSettings.members.no_members_desc') }}</small>
      </div>
      
      <div v-else class="members-grid">
        <div
          v-for="user in users"
          :key="user.user_id"
          class="member-card"
        >
          <div class="member-info">
            <div class="member-avatar">
              {{ user.username.charAt(0).toUpperCase() }}
            </div>
            <div class="member-details">
              <div class="member-name">{{ user.username }}</div>
              <div class="member-email">{{ user.email }}</div>
            </div>
          </div>
          
          <div class="member-permission">
            <div v-if="canEditUser(user)" class="permission-selector">
              <select
                :value="user.permission"
                :disabled="updatingUsers.has(user.user_id)"
                class="permission-select"
                :class="{ updating: updatingUsers.has(user.user_id) }"
                @change="handlePermissionChange(user, $event.target.value)"
              >
                <option
                  v-for="permission in getAvailablePermissions(user)"
                  :key="permission"
                  :value="permission"
                  :class="permission"
                >
                  {{ t(`projectSettings.permissions.${permission}`) }}
                </option>
              </select>
              <div v-if="updatingUsers.has(user.user_id)" class="update-spinner">
                <div class="spinner-small"></div>
              </div>
            </div>
            <span v-else class="permission-badge" :class="user.permission">
              {{ t(`projectSettings.permissions.${user.permission}`) }}
            </span>
          </div>
          
          <div class="member-actions">
            <button
              v-if="canRemoveUser(user)"
              class="btn-remove"
              :disabled="updatingUsers.has(user.user_id) || removingUser"
              @click="confirmRemoveUser(user)"
              :title="t('common.remove')"
            >
              ×
            </button>
            <div v-else class="no-actions">
              <span class="owner-badge" v-if="user.permission === 'owner'">
                {{ t('projectSettings.permissions.owner') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add User Modal -->
    <div v-if="showAddUserModal" class="modal-overlay" @click="closeAddUserModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>{{ t('projectSettings.members.add_modal.title') }}</h4>
          <button class="modal-close" @click="closeAddUserModal">×</button>
        </div>
        
        <form @submit.prevent="addUser" class="add-member-form">
          <div class="form-group">
            <label for="userId">{{ t('project.share.select_user') }} <span class="share-required">*</span></label>
            <select
              id="userId"
              v-model="newUser.user_id"
              class="form-select"
              :disabled="loadingAvailableUsers"
              required
            >
              <option value="" disabled>
                {{ loadingAvailableUsers ? t('common.loading') : t('project.share.choose_user') }}
              </option>
              <option
                v-for="user in filteredAvailableUsers"
                :key="user.user_id"
                :value="user.user_id"
              >
                {{ user.first_name }} {{ user.last_name }} ({{ user.username }}) - {{ user.email }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="permission">{{ t('projectSettings.members.add_modal.permission') }}</label>
            <select id="permission" v-model="newUser.permission" class="form-select" required>
              <option value="read">{{ t('projectSettings.permissions.read') }}</option>
              <option value="write">{{ t('projectSettings.permissions.write') }}</option>
              <option value="admin">{{ t('projectSettings.permissions.admin') }}</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="closeAddUserModal">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn-submit" :disabled="addingUser">
              <span v-if="addingUser" class="loading-text">{{ t('common.adding') }}...</span>
              <span v-else>{{ t('common.add') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useProjectStore } from '@/stores/project';
import { useUserStore } from '@/stores/user';
import { useEventMessageStore } from '@/stores/eventMessage';
import { useUserConfirm } from '@/composables/useUserConfirm';
import {
  getProjectUsers,
  addUserToProject,
  updateUserPermission,
  removeUserFromProject
} from '@/api/service/projectAssociationService';
import { fetchActiveUsers } from '@/api/service/userService';

const { t } = useI18n();
const projectStore = useProjectStore();
const userStore = useUserStore();
const eventMessageStore = useEventMessageStore();
const userConfirm = useUserConfirm();

const projectName = computed(() => projectStore.projectName);

// Reactive state
const users = ref([]);
const loading = ref(false);
const error = ref('');

// Modal states
const showAddUserModal = ref(false);

// Operation states
const updatingUsers = ref(new Set());
const addingUser = ref(false);
const removingUser = ref(false);
const loadingAvailableUsers = ref(false);

// Form data
const newUser = reactive({
  user_id: '',
  permission: 'read'
});

// Available users list for Add Member modal
const availableUsers = ref([]);
const filteredAvailableUsers = computed(() => {
  const existingIds = new Set(users.value.map((u) => u.user_id));
  return availableUsers.value.filter((u) => !existingIds.has(u.user_id));
});

// Computed properties
const currentUserRole = computed(() => {
  if (!userStore.user || !users.value.length) return null;
  
  const currentUser = users.value.find(user => user.user_id === userStore.user.user_id);
  console.log('currentUser from project:', currentUser);
  console.log('currentUserRole:', currentUser?.permission);
  
  return currentUser?.permission || null;
});

const canAddUsers = computed(() => {
  return ['admin', 'owner'].includes(currentUserRole.value);
});

// Methods
const loadUsers = async () => {
  if (!projectName.value) {
    error.value = t('projectSettings.members.no_project_selected');
    return;
  }

  loading.value = true;
  error.value = '';
  
  try {
    const response = await getProjectUsers(projectName.value);
    if (response.data) {
      users.value = response.data.users || [];
    }
  } catch (err) {
    console.error('Error loading users:', err);
    error.value = err.response?.data?.detail || t('projectSettings.members.load_error');
  } finally {
    loading.value = false;
  }
};

// Load active users for the Add Member modal (similar to ProjectShareModal)
const loadActiveUsers = async () => {
  if (loadingAvailableUsers.value) return;
  loadingAvailableUsers.value = true;
  try {
    const response = await fetchActiveUsers();
    if (response.data && response.data.users) {
      availableUsers.value = response.data.users;
    }
  } catch (err) {
    console.error('Error loading available users:', err);
    eventMessageStore.addMessage('project.share.error_loading_users', 'error');
  } finally {
    loadingAvailableUsers.value = false;
  }
};

const canEditUser = (user) => {
  // Only admin and owner can edit permissions
  if (!['admin', 'owner'].includes(currentUserRole.value)) return false;
  
  // Owner cannot be edited
  if (user.permission === 'owner') return false;
  
  // Admin cannot edit other admins (only owner can)
  return !(user.permission === 'admin' && currentUserRole.value !== 'owner');
};

const canRemoveUser = (user) => {
  // Only admin and owner can remove users
  if (!['admin', 'owner'].includes(currentUserRole.value)) return false;
  
  // Owner cannot be removed
  if (user.permission === 'owner') return false;
  
  // Admins can remove read/write users, but only owner can remove admins
  if (user.permission === 'admin') {
    return currentUserRole.value === 'owner';
  }
  
  return true;
};

const getAvailablePermissions = (user) => {
  const allPermissions = ['read', 'write', 'admin'];

  // Filter permissions based on current user role
  if (currentUserRole.value === 'owner') {
    return allPermissions;
  } else if (currentUserRole.value === 'admin') {
    // Admins can only set read/write permissions
    return ['read', 'write'];
  }
  
  return [];
};

const handlePermissionChange = async (user, newPermission) => {
  if (user.permission === newPermission) return;
  
  const oldPermission = user.permission;
  const confirmed = await userConfirm({
    title: t('projectSettings.members.confirm_permission_change.title'),
    message: t('projectSettings.members.confirm_permission_change.message', {
      username: user.username,
      oldPermission: t(`projectSettings.permissions.${oldPermission}`),
      newPermission: t(`projectSettings.permissions.${newPermission}`)
    }),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel')
  });
  
  if (confirmed) {
    await updateUserPermissionHandler(user, newPermission);
  } else {
    // Force re-render to reset select value
    nextTick(() => {
      const selectElement = event.target;
      if (selectElement) {
        selectElement.value = oldPermission;
      }
    });
  }
};

const confirmPermissionChange = async (user, newPermission) => {
  return handlePermissionChange(user, newPermission);
};

const updateUserPermissionHandler = async (user, newPermission = null) => {
  const permission = newPermission || user.permission;
  const oldPermission = user.permission;
  
  // Optimistically update the UI
  user.permission = permission;
  updatingUsers.value.add(user.user_id);
  
  try {
    const response = await updateUserPermission(
      projectName.value,
      user.user_id,
      { permission }
    );
    
    if (response.data) {
      eventMessageStore.addMessage('projectSettings.members.permission_updated', 'success');
    }
  } catch (err) {
    console.error('Error updating user permission:', err);
    // Revert the change
    user.permission = oldPermission;
    eventMessageStore.addMessage('projectSettings.members.permission_update_error', 'error');
  } finally {
    updatingUsers.value.delete(user.user_id);
  }
};

const confirmRemoveUser = async (user) => {
  const confirmed = await userConfirm({
    title: t('projectSettings.members.confirm_remove.title'),
    message: t('projectSettings.members.confirm_remove.message', { username: user.username }),
    confirmText: t('common.remove'),
    cancelText: t('common.cancel')
  });
  
  if (confirmed) {
    await removeUser(user);
  }
};

const closeAddUserModal = () => {
  showAddUserModal.value = false;
  newUser.user_id = '';
  newUser.permission = 'read';
};

const addUser = async () => {
  addingUser.value = true;
  
  try {
    const response = await addUserToProject(projectName.value, {
  user_id: parseInt(newUser.user_id, 10),
      permission: newUser.permission
    });
    
    if (response.data) {
      eventMessageStore.addMessage('projectSettings.members.user_added', 'success');
      closeAddUserModal();
      await loadUsers(); // Refresh the list
    }
  } catch (err) {
    console.error('Error adding user:', err);
    eventMessageStore.addMessage(
      err.response?.data?.detail || 'projectSettings.members.add_error',
      'error'
    );
  } finally {
    addingUser.value = false;
  }
};

const removeUser = async (user) => {
  if (!user) return;
  
  removingUser.value = true;
  
  try {
    const response = await removeUserFromProject(
      projectName.value,
      user.user_id
    );
    
    if (response.data) {
      eventMessageStore.addMessage('projectSettings.members.user_removed', 'success');
      await loadUsers(); // Refresh the list
    }
  } catch (err) {
    console.error('Error removing user:', err);
    eventMessageStore.addMessage('projectSettings.members.remove_error', 'error');
  } finally {
    removingUser.value = false;
  }
};

// Lifecycle
onMounted(() => {
  // Only load users if we have a project name
  if (projectName.value) {
    loadUsers();
  }
});

// When opening the Add Member modal, load available users
watch(showAddUserModal, (open) => {
  if (open) {
    loadActiveUsers();
  }
});

// Watch for project changes
watch(projectName, (newProjectName) => {
  if (newProjectName) {
    loadUsers();
  } else {
    users.value = [];
    error.value = '';
  }
});

// Expose methods for parent components if needed
defineExpose({
  loadUsers,
  users
});
</script>

<style scoped>
.configure-project-members {
  padding: 0;
}

.members-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.members-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
}

.btn-add-member {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-add-member:hover {
  background: #4f46e5;
  transform: translateY(-1px);
}

.add-icon {
  font-size: 1rem;
  font-weight: bold;
}

.loading-state, .error-state {
  text-align: center;
  padding: 2rem 1rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid #6366f1;
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

.members-grid {
  display: grid;
  gap: 1rem;
}

.member-card {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.2s ease;
}

.member-card:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
}

.member-details {
  flex: 1;
}

.member-name {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.125rem;
}

.member-email {
  font-size: 0.875rem;
  color: #6b7280;
}



.permission-select {
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  font-size: 0.875rem;
  min-width: 120px;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
}

.permission-select:hover:not(:disabled) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.permission-select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.permission-select:disabled {
  background: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
  border-color: #e5e7eb;
}

.permission-select.updating {
  background: #f3f4f6;
  color: #6b7280;
  cursor: wait;
}

.update-spinner {
  display: flex;
  align-items: center;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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

.permission-badge.owner {
  background: #ede9fe;
  color: #6b21a8;
}

/* Styles pour les options du select */
.permission-select option.read {
  background-color: #dbeafe;
  color: #1e40af;
}

.permission-select option.write {
  background-color: #d1fae5;
  color: #047857;
}

.permission-select option.admin {
  background-color: #fef3c7;
  color: #92400e;
}

.permission-select option.owner {
  background-color: #ede9fe;
  color: #6b21a8;
}

.btn-remove {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: #fee2e2;
  color: #dc2626;
  cursor: pointer;
  font-size: 1.125rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-remove:hover:not(:disabled) {
  background: #fecaca;
  transform: scale(1.1);
}

.btn-remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-actions {
  width: 32px;
  text-align: center;
}

.owner-badge {
  font-size: 0.75rem;
  color: #6b21a8;
  font-weight: 500;
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

.add-member-form {
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

.form-input, .form-select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
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

.btn-cancel, .btn-submit, .btn-danger {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-cancel:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-submit {
  background: #6366f1;
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: #4f46e5;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

.btn-cancel:disabled,
.btn-submit:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
