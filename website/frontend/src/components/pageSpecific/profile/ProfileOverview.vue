<template>
  <div class="profile-overview">
    <!-- Loading State -->
    <div v-if="loading" class="profile-loading">
      <div class="loading-spinner"></div>
      <p>{{ t('profile.overview.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="profile-error">
      <div class="error-icon">⚠️</div>
      <h3>{{ t('profile.overview.error_title') }}</h3>
      <p>{{ error }}</p>
    </div>

    <!-- Profile Content -->
    <div v-else-if="userProfile" class="profile-content-grid">
      <!-- Personal Information Card -->
      <div class="profile-card">
        <div class="profile-card-header">
          <h3>{{ t('profile.overview.personal_info.title') }}</h3>
          <button class="edit-button" v-if="!editUsernameMode" @click="startEditUsername">
            {{ t('profile.overview.edit') }}
          </button>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.full_name') }}</span>
              <div class="profile-field-value">
                {{ userProfile.first_name }} {{ userProfile.last_name }}
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.username') }}</span>
              <div class="profile-field-value">
                <template v-if="editUsernameMode">
                  <input v-model="editedUsername" class="username-input" :disabled="saving" />
                  <button class="save-button" @click="saveUsername" :disabled="saving">
                    {{ saving ? t('common.saving') : t('common.save') }}
                  </button>
                  <button class="cancel-button" @click="cancelEditUsername" :disabled="saving">
                    {{ t('common.cancel') }}
                  </button>
                </template>
                <template v-else>
                  {{ userProfile.username }}
                </template>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.email') }}</span>
              <div class="profile-field-value">
                {{ userProfile.email }}
                <span v-if="userProfile.is_verified_account" class="verification-badge verified">
                  ✓ {{ t('profile.overview.personal_info.verified') }}
                </span>
                <span v-else class="verification-badge unverified">
                  ⚠ {{ t('profile.overview.personal_info.unverified') }}
                </span>
              </div>
            </div>
            <div v-if="userProfile.phone_number" class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.phone') }}</span>
              <div class="profile-field-value">
                {{ userProfile.phone_number }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Professional Information Card -->
      <div class="profile-card">
        <div class="profile-card-header">
          <h3>{{ t('profile.overview.professional_info.title') }}</h3>
          <button class="edit-button" @click="editProfessionalInfo">
            {{ t('profile.overview.edit') }}
          </button>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.professional_info.affiliation') }}</span>
              <div class="profile-field-value">
                {{ userProfile.affiliation }}
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.professional_info.department') }}</span>
              <div class="profile-field-value">
                {{ userProfile.department }}
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.professional_info.role') }}</span>
              <div class="profile-field-value">
                <span class="role-badge" :class="userProfile.role.toLowerCase()">
                  {{ t(`profile.overview.professional_info.roles.${userProfile.role.toLowerCase()}`) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Address Information Card -->
      <div v-if="userProfile.address" class="profile-card">
        <div class="profile-card-header">
          <h3>{{ t('profile.overview.address_info.title') }}</h3>
          <button class="edit-button" @click="editAddress">
            {{ t('profile.overview.edit') }}
          </button>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.address_info.street') }}</span>
              <div class="profile-field-value">
                <span v-if="userProfile.address.street_number">
                  {{ userProfile.address.street_number }}
                </span>
                {{ userProfile.address.street_name }}
              </div>
            </div>
            <div v-if="userProfile.address.address_line_2" class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.address_info.address_line_2') }}</span>
              <div class="profile-field-value">
                {{ userProfile.address.address_line_2 }}
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.address_info.city_postal') }}</span>
              <div class="profile-field-value">
                {{ userProfile.address.postal_code }}
                <span v-if="userProfile.address.city">
                  {{ userProfile.address.city.name }}, {{ userProfile.address.city.country }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Account Information Card -->
      <div class="profile-card">
        <div class="profile-card-header">
          <h3>{{ t('profile.overview.account_info.title') }}</h3>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.member_since') }}</span>
              <div class="profile-field-value">
                {{ formatDate(userProfile.created_at) }}
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.last_updated') }}</span>
              <div class="profile-field-value">
                {{ formatDate(userProfile.updated_at) }}
              </div>
            </div>
            <div v-if="userProfile.last_login" class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.last_login') }}</span>
              <div class="profile-field-value">
                {{ formatDate(userProfile.last_login) }}
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.account_status') }}</span>
              <div class="profile-field-value">
                <span class="status-badge" :class="userProfile.is_active ? 'active' : 'inactive'">
                  {{ userProfile.is_active ? t('profile.overview.account_info.active') : t('profile.overview.account_info.inactive') }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="profile-empty">
      <div class="empty-icon">👤</div>
      <h3>{{ t('profile.overview.empty_title') }}</h3>
      <p>{{ t('profile.overview.empty_message') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { updateUserProfile } from '@/api/service/userService.js';

const { t } = useI18n();

const props = defineProps({
  userProfile: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['profile-updated', 'show-message']);

const editUsernameMode = ref(false);
const editedUsername = ref('');
const saving = ref(false);

watch(
  () => props.userProfile,
  (newVal) => {
    if (newVal && !editUsernameMode.value) {
      editedUsername.value = newVal.username;
    }
  },
  { immediate: true }
);

function startEditUsername() {
  editUsernameMode.value = true;
  editedUsername.value = props.userProfile?.username || '';
}

function cancelEditUsername() {
  editUsernameMode.value = false;
  editedUsername.value = props.userProfile?.username || '';
}

async function saveUsername() {
  if (saving.value) return;
  
  // Validate username
  if (!editedUsername.value.trim()) {
    emit('show-message', { text: 'Le nom d\'utilisateur ne peut pas être vide', type: 'error' });
    return;
  }
  
  if (editedUsername.value === props.userProfile?.username) {
    // No change, just exit edit mode
    editUsernameMode.value = false;
    return;
  }
  
  try {
    saving.value = true;
    
    const response = await updateUserProfile({
      username: editedUsername.value
    });
    
    if (response.data) {
      emit('show-message', { text: 'Nom d\'utilisateur mis à jour avec succès', type: 'success' });
      emit('profile-updated'); // Tell parent to reload profile
      editUsernameMode.value = false;
    }
  } catch (error) {
    console.error('Error updating username:', error);
    let errorMessage = 'Erreur lors de la mise à jour du nom d\'utilisateur';
    
    if (error.response?.data?.detail) {
      if (error.response.data.detail.includes('already taken')) {
        errorMessage = 'Ce nom d\'utilisateur est déjà pris';
      } else {
        errorMessage = error.response.data.detail;
      }
    }
    
    emit('show-message', { text: errorMessage, type: 'error' });
    // Reset to original value on error
    editedUsername.value = props.userProfile?.username || '';
  } finally {
    saving.value = false;
  }
}

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function editProfessionalInfo() {
  // TODO: Implement edit professional info
  console.log('Edit professional info');
}

function editAddress() {
  // TODO: Implement edit address
  console.log('Edit address');
}
</script>
/* Username edit styles */
.username-input {
  font-size: 1rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  margin-right: 0.5rem;
}
.save-button {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  margin-right: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.save-button:hover {
  background: #1d4ed8;
}
.save-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
.cancel-button {
  background: #f3f4f6;
  color: #6b7280;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.2s;
}
.cancel-button:hover {
  background: #e5e7eb;
  color: #374151;
}
.cancel-button:disabled {
  background: #f9fafb;
  color: #d1d5db;
  cursor: not-allowed;
}

<style scoped>
.profile-overview {
  padding: 0;
}

/* Loading State */
.profile-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.loading-spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error State */
.profile-error {
  text-align: center;
  padding: 4rem 2rem;
  color: #dc2626;
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.profile-error h3 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  color: #374151;
}

.profile-error p {
  margin: 0;
  color: #6b7280;
}

/* Content Grid */
.profile-content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
  padding: 0;
}

/* Profile Cards */
.profile-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.profile-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.profile-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.profile-card-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.edit-button {
  padding: 0.5rem 1rem;
  background: #f3f4f6;
  color: #6b7280;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-button:hover {
  background: #e5e7eb;
  color: #374151;
}

.profile-card-content {
  padding: 1rem 1.5rem 1.5rem;
}

/* Profile Fields */
.profile-field-group {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.profile-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.profile-field-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.profile-field-value {
  font-size: 1rem;
  color: #1f2937;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* Badges */
.verification-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.verification-badge.verified {
  background: #d1fae5;
  color: #065f46;
}

.verification-badge.unverified {
  background: #fef3c7;
  color: #92400e;
}

.role-badge {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  text-transform: capitalize;
}

.role-badge.admin {
  background: #fecaca;
  color: #991b1b;
}

.role-badge.public {
  background: #e0e7ff;
  color: #3730a3;
}

.status-badge {
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

/* Empty State */
.profile-empty {
  text-align: center;
  padding: 4rem 2rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.profile-empty h3 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  color: #374151;
}

.profile-empty p {
  margin: 0;
  font-size: 1.1rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .profile-content-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .profile-card-header {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .edit-button {
    align-self: flex-end;
  }

  .profile-card-content {
    padding: 0 1rem 1rem;
  }
}
</style>
