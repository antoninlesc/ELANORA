<template>
  <div class="project-users-manager">
    <div class="header">
      <h3>{{ $t('project.users.title', { projectName }) }}</h3>
      <button
        v-if="canAddUsers"
        class="btn-primary add-user-btn"
        @click="showAddUserModal = true"
      >
        <i class="icon-plus"></i>
        {{ $t('project.users.add_user') }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>{{ $t('common.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button class="btn-secondary" @click="loadUsers">
        {{ $t('common.retry') }}
      </button>
    </div>

    <!-- Users List -->
    <div v-else class="users-list">
      <div v-if="users.length === 0" class="empty-state">
        <p>{{ $t('project.users.no_users') }}</p>
      </div>

      <div v-else class="users-table">
        <div class="table-header">
          <div class="column user-info">{{ $t('project.users.user') }}</div>
          <div class="column permission">
            {{ $t('project.users.permission') }}
          </div>
          <div class="column actions">{{ $t('common.actions') }}</div>
        </div>

        <div v-for="user in users" :key="user.user_id" class="user-row">
          <div class="column user-info">
            <div class="user-avatar">
              {{ user.username.charAt(0).toUpperCase() }}
            </div>
            <div class="user-details">
              <div class="username">{{ user.username }}</div>
              <div class="email">{{ user.email }}</div>
            </div>
          </div>

          <div class="column permission">
            <select
              v-if="canEditUser(user)"
              v-model="user.permission"
              class="permission-select"
              :disabled="updatingUsers.has(user.user_id)"
              @change="updateUserPermissionHandler(user)"
            >
              <option value="read">{{ $t('project.permissions.read') }}</option>
              <option value="write">
                {{ $t('project.permissions.write') }}
              </option>
              <option value="admin">
                {{ $t('project.permissions.admin') }}
              </option>
              <option v-if="user.permission === 'owner'" value="owner">
                {{ $t('project.permissions.owner') }}
              </option>
            </select>
            <span v-else class="permission-badge" :class="user.permission">
              {{ $t(`project.permissions.${user.permission}`) }}
            </span>
          </div>

          <div class="column actions">
            <button
              v-if="canRemoveUser(user)"
              class="btn-danger btn-small"
              :disabled="updatingUsers.has(user.user_id)"
              @click="confirmRemoveUser(user)"
            >
              <i class="icon-trash"></i>
              {{ $t('common.remove') }}
            </button>
            <span v-else class="no-actions">-</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add User Modal -->
    <div
      v-if="showAddUserModal"
      class="modal-overlay"
      @click="closeAddUserModal"
    >
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>{{ $t('project.users.add_user_modal.title') }}</h4>
          <button class="modal-close" @click="closeAddUserModal">×</button>
        </div>

        <form class="add-user-form" @submit.prevent="addUser">
          <div class="form-group">
            <label for="userId">{{
              $t('project.users.add_user_modal.user_id')
            }}</label>
            <input
              id="userId"
              v-model="newUser.user_id"
              type="number"
              class="form-input"
              required
              min="1"
            />
          </div>

          <div class="form-group">
            <label for="permission">{{
              $t('project.users.add_user_modal.permission')
            }}</label>
            <select
              id="permission"
              v-model="newUser.permission"
              class="form-select"
              required
            >
              <option value="read">{{ $t('project.permissions.read') }}</option>
              <option value="write">
                {{ $t('project.permissions.write') }}
              </option>
              <option value="admin">
                {{ $t('project.permissions.admin') }}
              </option>
            </select>
          </div>

          <div class="form-actions">
            <button
              type="button"
              class="btn-secondary"
              @click="closeAddUserModal"
            >
              {{ $t('common.cancel') }}
            </button>
            <button type="submit" class="btn-primary" :disabled="addingUser">
              {{ addingUser ? $t('common.adding') : $t('common.add') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Confirm Remove Modal -->
    <div v-if="showRemoveModal" class="modal-overlay" @click="closeRemoveModal">
      <div class="modal-content confirm-modal" @click.stop>
        <div class="modal-header">
          <h4>{{ $t('project.users.remove_modal.title') }}</h4>
        </div>

        <div class="modal-body">
          <p>
            {{
              $t('project.users.remove_modal.message', {
                username: userToRemove?.username,
              })
            }}
          </p>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="closeRemoveModal">
            {{ $t('common.cancel') }}
          </button>
          <button
            class="btn-danger"
            :disabled="removingUser"
            @click="removeUser"
          >
            {{ removingUser ? $t('common.removing') : $t('common.remove') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@/stores/eventMessage';
import {
  getProjectUsers,
  addUserToProject,
  updateUserPermission,
  removeUserFromProject,
} from '@/api/service/projectAssociationService';

const props = defineProps({
  projectName: {
    type: String,
    required: true,
  },
  currentUserRole: {
    type: String,
    default: 'read',
  },
});

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();

// Reactive state
const users = ref([]);
const loading = ref(false);
const error = ref('');

// Modal states
const showAddUserModal = ref(false);
const showRemoveModal = ref(false);
const userToRemove = ref(null);

// Operation states
const updatingUsers = ref(new Set());
const addingUser = ref(false);
const removingUser = ref(false);

// Form data
const newUser = reactive({
  user_id: '',
  permission: 'read',
});

// Computed properties
const canAddUsers = computed(() => {
  return ['admin', 'owner'].includes(props.currentUserRole);
});

// Methods
const loadUsers = async () => {
  loading.value = true;
  error.value = '';

  try {
    const response = await getProjectUsers(props.projectName);
    if (response.data) {
      users.value = response.data.users || [];
    }
  } catch (err) {
    console.error('Error loading users:', err);
    error.value = err.response?.data?.detail || t('project.users.load_error');
  } finally {
    loading.value = false;
  }
};

const canEditUser = (user) => {
  // Only admin and owner can edit permissions
  if (!['admin', 'owner'].includes(props.currentUserRole)) return false;

  // Owner cannot be edited
  if (user.permission === 'owner') return false;

  // Admin cannot edit other admins (only owner can)
  return !(user.permission === 'admin' && props.currentUserRole !== 'owner');
};

const canRemoveUser = (user) => {
  // Only admin and owner can remove users
  if (!['admin', 'owner'].includes(props.currentUserRole)) return false;

  // Owner cannot be removed
  if (user.permission === 'owner') return false;

  // Admins can remove read/write users, but only owner can remove admins
  if (user.permission === 'admin') {
    return props.currentUserRole === 'owner';
  }

  return true;
};

const updateUserPermissionHandler = async (user) => {
  updatingUsers.value.add(user.user_id);

  try {
    const response = await updateUserPermission(
      props.projectName,
      user.user_id,
      { permission: user.permission }
    );

    if (response.data) {
      eventMessageStore.addMessage(
        'project.users.permission_updated',
        'success'
      );
    }
  } catch (err) {
    console.error('Error updating user permission:', err);
    eventMessageStore.addMessage(
      'project.users.permission_update_error',
      'error'
    );
    // Reload users to reset the select value
    await loadUsers();
  } finally {
    updatingUsers.value.delete(user.user_id);
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
    const response = await addUserToProject(props.projectName, {
      user_id: parseInt(newUser.user_id),
      permission: newUser.permission,
    });

    if (response.data) {
      eventMessageStore.addMessage('project.users.user_added', 'success');
      closeAddUserModal();
      await loadUsers(); // Refresh the list
    }
  } catch (err) {
    console.error('Error adding user:', err);
    eventMessageStore.addMessage(
      err.response?.data?.detail || 'project.users.add_error',
      'error'
    );
  } finally {
    addingUser.value = false;
  }
};

const confirmRemoveUser = (user) => {
  userToRemove.value = user;
  showRemoveModal.value = true;
};

const closeRemoveModal = () => {
  showRemoveModal.value = false;
  userToRemove.value = null;
};

const removeUser = async () => {
  if (!userToRemove.value) return;

  removingUser.value = true;

  try {
    const response = await removeUserFromProject(
      props.projectName,
      userToRemove.value.user_id
    );

    if (response.data) {
      eventMessageStore.addMessage('project.users.user_removed', 'success');
      closeRemoveModal();
      await loadUsers(); // Refresh the list
    }
  } catch (err) {
    console.error('Error removing user:', err);
    eventMessageStore.addMessage('project.users.remove_error', 'error');
  } finally {
    removingUser.value = false;
  }
};

// Lifecycle
onMounted(() => {
  loadUsers();
});

// Expose methods for parent components if needed
defineExpose({
  loadUsers,
  users,
});
</script>

<style scoped>
.project-users-manager {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 10%);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.add-user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-container,
.error-container {
  text-align: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.error-message {
  color: #dc2626;
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.users-table {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 16px;
  background: #f9fafb;
  padding: 16px;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.user-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  align-items: center;
}

.user-row:last-child {
  border-bottom: none;
}

.user-row:hover {
  background: #f9fafb;
}

.column.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-details {
  flex: 1;
}

.username {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 2px;
}

.email {
  font-size: 0.875rem;
  color: #6b7280;
}

.permission-select {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: white;
  font-size: 0.875rem;
  min-width: 100px;
}

.permission-select:disabled {
  background: #f3f4f6;
  color: #6b7280;
}

.permission-badge {
  display: inline-block;
  padding: 4px 12px;
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

.btn-small {
  padding: 6px 12px;
  font-size: 0.875rem;
}

.no-actions {
  color: #9ca3af;
  font-size: 0.875rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 50%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #374151;
}

.add-user-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-input,
.form-select {
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgb(59 130 246 / 10%);
}

.form-actions,
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.confirm-modal .modal-body {
  margin-bottom: 24px;
}

.confirm-modal .modal-body p {
  margin: 0;
  color: #374151;
  line-height: 1.5;
}

/* Button Styles */
.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-primary:disabled,
.btn-secondary:disabled,
.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

/* Icon placeholder - you can replace with your actual icon library */
.icon-plus::before {
  content: '+';
}

.icon-trash::before {
  content: '🗑️';
}
</style>
