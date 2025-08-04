<template>
  <div class="project-users-manager">
    <div class="header">
      <h3>Gestion des utilisateurs du projet</h3>
      <p v-if="projectName" class="project-name">Projet: {{ projectName }}</p>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Chargement des utilisateurs...</p>
    </div>

    <!-- Error state -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="fetchUsers" class="retry-button">Réessayer</button>
    </div>

    <!-- Users list -->
    <div v-if="!loading && !error" class="users-section">
      <div class="users-header">
        <h4>Utilisateurs ({{ users.length }})</h4>
        <button 
          @click="showAddUserModal = true" 
          class="add-user-button"
          :disabled="!canManageUsers"
        >
          + Ajouter un utilisateur
        </button>
      </div>

      <div v-if="users.length === 0" class="no-users">
        <p>Aucun utilisateur associé à ce projet.</p>
      </div>

      <div v-else class="users-list">
        <div 
          v-for="user in users" 
          :key="user.user_id" 
          class="user-card"
        >
          <div class="user-info">
            <div class="user-details">
              <h5>{{ user.username }}</h5>
              <p class="user-email">{{ user.email }}</p>
            </div>
            <div class="user-permission">
              <select 
                v-model="user.permission" 
                @change="updatePermission(user)"
                :disabled="!canManageUsers || updating === user.user_id"
                class="permission-select"
                :class="`permission-${user.permission}`"
              >
                <option value="read">Lecture</option>
                <option value="write">Écriture</option>
                <option value="admin">Admin</option>
                <option value="owner">Propriétaire</option>
              </select>
            </div>
          </div>
          <div class="user-actions">
            <button 
              @click="confirmRemoveUser(user)"
              :disabled="!canManageUsers || updating === user.user_id"
              class="remove-button"
              title="Retirer du projet"
            >
              ✗
            </button>
          </div>
          <div v-if="updating === user.user_id" class="updating-overlay">
            <div class="mini-spinner"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add User Modal -->
    <div v-if="showAddUserModal" class="modal-overlay" @click="closeAddUserModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h4>Ajouter un utilisateur</h4>
          <button @click="closeAddUserModal" class="close-button">✗</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="user-id">ID Utilisateur:</label>
            <input 
              id="user-id"
              v-model="newUser.user_id" 
              type="number" 
              placeholder="Entrez l'ID de l'utilisateur"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="permission">Permission:</label>
            <select id="permission" v-model="newUser.permission" class="form-select">
              <option value="read">Lecture</option>
              <option value="write">Écriture</option>
              <option value="admin">Admin</option>
              <option value="owner">Propriétaire</option>
            </select>
          </div>
          <div v-if="addUserError" class="error-message">
            {{ addUserError }}
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeAddUserModal" class="cancel-button">Annuler</button>
          <button 
            @click="addUser" 
            :disabled="adding || !newUser.user_id"
            class="confirm-button"
          >
            <span v-if="adding">Ajout...</span>
            <span v-else>Ajouter</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm Remove Modal -->
    <div v-if="showRemoveModal" class="modal-overlay" @click="closeRemoveModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h4>Confirmer la suppression</h4>
          <button @click="closeRemoveModal" class="close-button">✗</button>
        </div>
        <div class="modal-body">
          <p>Êtes-vous sûr de vouloir retirer <strong>{{ userToRemove?.username }}</strong> du projet ?</p>
          <p class="warning">Cette action ne peut pas être annulée.</p>
        </div>
        <div class="modal-footer">
          <button @click="closeRemoveModal" class="cancel-button">Annuler</button>
          <button 
            @click="removeUser" 
            :disabled="removing"
            class="danger-button"
          >
            <span v-if="removing">Suppression...</span>
            <span v-else>Supprimer</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { getProjectUsers, addUserToProject, updateUserPermission, removeUserFromProject } from '@/api/service/projectAssociationService'

// Props
const props = defineProps({
  projectId: {
    type: [Number, String],
    required: true
  },
  projectName: {
    type: String,
    default: ''
  },
  canManageUsers: {
    type: Boolean,
    default: true
  }
})

// Reactive data
const users = ref([])
const loading = ref(false)
const error = ref('')
const updating = ref(null)
const adding = ref(false)
const removing = ref(false)

// Modal states
const showAddUserModal = ref(false)
const showRemoveModal = ref(false)
const userToRemove = ref(null)

// Form data
const newUser = ref({
  user_id: null,
  permission: 'read'
})
const addUserError = ref('')

// Computed
const projectNameToUse = computed(() => {
  return props.projectName || `project-${props.projectId}`
})

// Methods
async function fetchUsers() {
  if (!props.projectId) return

  loading.value = true
  error.value = ''
  
  try {
    const response = await getProjectUsers(projectNameToUse.value)
    users.value = response.data.users || []
  } catch (err) {
    console.error('Error fetching project users:', err)
    error.value = err.response?.data?.detail || 'Erreur lors du chargement des utilisateurs'
  } finally {
    loading.value = false
  }
}

async function updatePermission(user) {
  updating.value = user.user_id
  
  try {
    await updateUserPermission(projectNameToUse.value, user.user_id, {
      permission: user.permission
    })
    // Optionally show success message
  } catch (err) {
    console.error('Error updating permission:', err)
    // Revert the change
    await fetchUsers()
    error.value = err.response?.data?.detail || 'Erreur lors de la mise à jour des permissions'
  } finally {
    updating.value = null
  }
}

function confirmRemoveUser(user) {
  userToRemove.value = user
  showRemoveModal.value = true
}

async function removeUser() {
  if (!userToRemove.value) return

  removing.value = true
  
  try {
    await removeUserFromProject(projectNameToUse.value, userToRemove.value.user_id)
    await fetchUsers() // Refresh the list
    closeRemoveModal()
  } catch (err) {
    console.error('Error removing user:', err)
    error.value = err.response?.data?.detail || 'Erreur lors de la suppression de l\'utilisateur'
  } finally {
    removing.value = false
  }
}

async function addUser() {
  if (!newUser.value.user_id) return

  adding.value = true
  addUserError.value = ''
  
  try {
    await addUserToProject(projectNameToUse.value, {
      user_id: parseInt(newUser.value.user_id),
      permission: newUser.value.permission
    })
    await fetchUsers() // Refresh the list
    closeAddUserModal()
  } catch (err) {
    console.error('Error adding user:', err)
    addUserError.value = err.response?.data?.detail || 'Erreur lors de l\'ajout de l\'utilisateur'
  } finally {
    adding.value = false
  }
}

function closeAddUserModal() {
  showAddUserModal.value = false
  newUser.value = { user_id: null, permission: 'read' }
  addUserError.value = ''
}

function closeRemoveModal() {
  showRemoveModal.value = false
  userToRemove.value = null
}

// Watch for projectId changes
watch(() => props.projectId, () => {
  fetchUsers()
}, { immediate: false })

// Lifecycle
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.project-users-manager {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  margin-bottom: 24px;
}

.header h3 {
  margin: 0 0 8px 0;
  color: #2d3748;
  font-size: 1.5rem;
}

.project-name {
  color: #718096;
  font-size: 0.875rem;
  margin: 0;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #3182ce;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: #fed7d7;
  color: #c53030;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.retry-button {
  background-color: #3182ce;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 8px;
}

.retry-button:hover {
  background-color: #2c5282;
}

.users-section {
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
}

.users-header h4 {
  margin: 0;
  color: #2d3748;
}

.add-user-button {
  background-color: #38a169;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.add-user-button:hover:not(:disabled) {
  background-color: #2f855a;
}

.add-user-button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.no-users {
  padding: 40px 20px;
  text-align: center;
  color: #718096;
}

.user-card:not(:last-child) {
  border-bottom: 1px solid #e2e8f0;
}

.user-card {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  transition: background-color 0.2s;
}

.user-card:hover {
  background-color: #f7fafc;
}

.user-info {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 20px;
}

.user-details h5 {
  margin: 0 0 4px 0;
  color: #2d3748;
  font-weight: 600;
}

.user-email {
  margin: 0;
  color: #718096;
  font-size: 0.875rem;
}

.permission-select {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  background: white;
  font-size: 0.875rem;
  cursor: pointer;
}

.permission-select:disabled {
  background-color: #f7fafc;
  cursor: not-allowed;
  opacity: 0.7;
}

.permission-read { color: #3182ce; }
.permission-write { color: #38a169; }
.permission-admin { color: #d69e2e; }
.permission-owner { color: #9f7aea; }

.user-actions {
  display: flex;
  gap: 8px;
}

.remove-button {
  background-color: #e53e3e;
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
}

.remove-button:hover:not(:disabled) {
  background-color: #c53030;
}

.remove-button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.updating-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #3182ce;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  min-width: 400px;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h4 {
  margin: 0;
  color: #2d3748;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #718096;
  padding: 4px;
}

.close-button:hover {
  color: #2d3748;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  color: #2d3748;
  font-weight: 500;
}

.form-input,
.form-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
}

.cancel-button {
  background-color: #f7fafc;
  color: #2d3748;
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-button:hover {
  background-color: #edf2f7;
}

.confirm-button {
  background-color: #38a169;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.confirm-button:hover:not(:disabled) {
  background-color: #2f855a;
}

.confirm-button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.danger-button {
  background-color: #e53e3e;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.danger-button:hover:not(:disabled) {
  background-color: #c53030;
}

.danger-button:disabled {
  background-color: #a0aec0;
  cursor: not-allowed;
}

.warning {
  color: #d69e2e;
  font-size: 0.875rem;
  margin-top: 8px;
}
</style>
