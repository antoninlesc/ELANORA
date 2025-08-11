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
      <div class="profile-card personal-info-card">
        <div class="profile-card-header">
          <div class="card-title-section">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M20.5899 22C20.5899 18.13 16.7399 15 11.9999 15C7.25991 15 3.40991 18.13 3.40991 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>{{ t('profile.overview.personal_info.title') }}</h3>
          </div>
          <button class="edit-button modern-edit-btn" v-if="!editUsernameMode" @click="startEditUsername">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M18.5 2.49998C18.8978 2.10216 19.4374 1.87866 20 1.87866C20.5626 1.87866 21.1022 2.10216 21.5 2.49998C21.8978 2.89781 22.1213 3.43737 22.1213 3.99998C22.1213 4.56259 21.8978 5.10216 21.5 5.49998L12 15L8 16L9 12L18.5 2.49998Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ t('profile.overview.edit') }}
          </button>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.full_name') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 4.17157 16.1716C3.42143 16.9217 3 17.9391 3 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ userProfile.first_name }} {{ userProfile.last_name }}</span>
                </div>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.username') }}</span>
              <div class="profile-field-value">
                <template v-if="editUsernameMode">
                  <div class="edit-field-container">
                    <div class="input-container">
                      <div class="input-icon">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M12 14C8.13401 14 5 17.134 5 21H19C19 17.134 15.866 14 12 14Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                      <input 
                        v-model="editedUsername" 
                        class="modern-input" 
                        :disabled="saving"
                        placeholder="Nom d'utilisateur"
                        @keyup.enter="saveUsername"
                        @keyup.escape="cancelEditUsername"
                      />
                    </div>
                    <div class="edit-actions">
                      <button class="save-button modern-save-btn" @click="saveUsername" :disabled="saving">
                        <svg v-if="!saving" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <div v-else class="mini-spinner"></div>
                        {{ saving ? t('common.saving') : t('common.save') }}
                      </button>
                      <button class="cancel-button modern-cancel-btn" @click="cancelEditUsername" :disabled="saving">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        {{ t('common.cancel') }}
                      </button>
                    </div>
                  </div>
                </template>
                <template v-else>
                  <div class="field-content">
                    <div class="field-icon">
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M12 14C8.13401 14 5 17.134 5 21H19C19 17.134 15.866 14 12 14Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                    <span class="field-text">{{ userProfile.username }}</span>
                  </div>
                </template>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.email') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ userProfile.email }}</span>
                  <div class="verification-section">
                    <span v-if="userProfile.is_verified_account" class="verification-badge verified">
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      {{ t('profile.overview.personal_info.verified') }}
                    </span>
                    <span v-else class="verification-badge unverified">
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/>
                        <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                      {{ t('profile.overview.personal_info.unverified') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="userProfile.phone_number" class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.personal_info.phone') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 16.92V19.92C22.0011 20.1985 21.9441 20.4742 21.8325 20.7293C21.7209 20.9845 21.5573 21.2136 21.3521 21.4019C21.1468 21.5901 20.9046 21.7335 20.6407 21.8227C20.3769 21.9119 20.0974 21.9451 19.82 21.92C16.7428 21.5856 13.787 20.5341 11.19 18.85C8.77382 17.3147 6.72533 15.2662 5.18999 12.85C3.49997 10.2412 2.44824 7.27099 2.11999 4.18C2.095 3.90347 2.12787 3.62476 2.21649 3.36162C2.30512 3.09849 2.44756 2.85669 2.63476 2.65162C2.82196 2.44655 3.0498 2.28271 3.30379 2.17052C3.55777 2.05833 3.83233 2.00026 4.10999 2H7.10999C7.59344 1.99522 8.06544 2.16708 8.43945 2.48351C8.81346 2.79993 9.06681 3.23198 9.15999 3.71C9.33652 4.66443 9.61631 5.59478 9.99999 6.48C10.1018 6.74 10.1445 7.02274 10.1237 7.30405C10.1029 7.58535 10.0193 7.85678 9.87999 8.1L8.61999 9.36C10.1897 11.8135 12.2865 13.9103 14.74 15.48L16 14.22C16.2432 14.0806 16.5146 13.997 16.7959 13.9762C17.0772 13.9555 17.36 13.9982 17.62 14.1C18.5052 14.4837 19.4356 14.7635 20.39 14.94C20.8747 15.0336 21.3119 15.2904 21.6271 15.6684C21.9423 16.0464 22.1103 16.5221 22.1 17.01L22 16.92Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ userProfile.phone_number }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Professional Information Card -->
      <div class="profile-card professional-info-card">
        <div class="profile-card-header">
          <div class="card-title-section">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="2" y="3" width="20" height="14" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <line x1="8" y1="21" x2="16" y2="21" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3>{{ t('profile.overview.professional_info.title') }}</h3>
          </div>
          <button class="edit-button modern-edit-btn" @click="editProfessionalInfo">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M18.5 2.49998C18.8978 2.10216 19.4374 1.87866 20 1.87866C20.5626 1.87866 21.1022 2.10216 21.5 2.49998C21.8978 2.89781 22.1213 3.43737 22.1213 3.99998C22.1213 4.56259 21.8978 5.10216 21.5 5.49998L12 15L8 16L9 12L18.5 2.49998Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ t('profile.overview.edit') }}
          </button>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.professional_info.affiliation') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 21H21M5 21V7L13 2L21 7V21M9 9H10M14 9H15M9 13H10M14 13H15M9 17H10M14 17H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ userProfile.affiliation }}</span>
                </div>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.professional_info.department') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17 21V19C17 17.9391 16.5786 16.9217 15.8284 16.1716C15.0783 15.4214 14.0609 15 13 15H5C3.93913 15 2.92172 15.4214 2.17157 16.1716C1.42143 16.9217 1 17.9391 1 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M23 21V19C22.9993 18.1137 22.7044 17.2528 22.1614 16.5523C21.6184 15.8519 20.8581 15.3516 20 15.13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M16 3.13C16.8604 3.35031 17.623 3.85071 18.1676 4.55232C18.7122 5.25392 19.0078 6.11683 19.0078 7.005C19.0078 7.89318 18.7122 8.75608 18.1676 9.45769C17.623 10.1593 16.8604 10.6597 16 10.88" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ userProfile.department }}</span>
                </div>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.professional_info.role') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 6.253V16.64" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <path d="M18 9V21C18 21.6 17.6 22 17 22H7C6.4 22 6 21.6 6 21V9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M4 9H20L18.5 2H5.5L4 9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="role-badge modern-role-badge" :class="userProfile.role.toLowerCase()">
                    {{ t(`profile.overview.professional_info.roles.${userProfile.role.toLowerCase()}`) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Address Information Card -->
      <div v-if="userProfile.address" class="profile-card address-info-card">
        <div class="profile-card-header">
          <div class="card-title-section">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 10C21 17 12 23 12 23S3 17 3 10C3 7.61305 3.94821 5.32387 5.63604 3.63604C7.32387 1.94821 9.61305 1 12 1C14.3869 1 16.6761 1.94821 18.3639 3.63604C20.0518 5.32387 21 7.61305 21 10Z" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3>{{ t('profile.overview.address_info.title') }}</h3>
          </div>
          <button class="edit-button modern-edit-btn" @click="editAddress">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M11 4H4C3.46957 4 2.96086 4.21071 2.58579 4.58579C2.21071 4.96086 2 5.46957 2 6V20C2 20.5304 2.21071 21.0391 2.58579 21.4142C2.96086 21.7893 3.46957 22 4 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M18.5 2.49998C18.8978 2.10216 19.4374 1.87866 20 1.87866C20.5626 1.87866 21.1022 2.10216 21.5 2.49998C21.8978 2.89781 22.1213 3.43737 22.1213 3.99998C22.1213 4.56259 21.8978 5.10216 21.5 5.49998L12 15L8 16L9 12L18.5 2.49998Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            {{ t('profile.overview.edit') }}
          </button>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.address_info.street') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="9,22 9,12 15,12 15,22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">
                    <span v-if="userProfile.address.street_number">
                      {{ userProfile.address.street_number }}
                    </span>
                    {{ userProfile.address.street_name }}
                  </span>
                </div>
              </div>
            </div>
            <div v-if="userProfile.address.address_line_2" class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.address_info.address_line_2') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <line x1="7" y1="8" x2="17" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <line x1="7" y1="12" x2="17" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                      <line x1="7" y1="16" x2="11" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ userProfile.address.address_line_2 }}</span>
                </div>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.address_info.city_postal') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path d="M2 12H22" stroke="currentColor" stroke-width="2"/>
                      <path d="M12 2C14.5013 4.73835 15.9228 8.29203 16 12C15.9228 15.708 14.5013 19.2616 12 22C9.49872 19.2616 8.07725 15.708 8 12C8.07725 8.29203 9.49872 4.73835 12 2Z" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <span class="field-text">
                    {{ userProfile.address.postal_code }}
                    <span v-if="userProfile.address.city">
                      {{ userProfile.address.city.name }}, {{ userProfile.address.city.country }}
                    </span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Account Information Card -->
      <div class="profile-card account-info-card">
        <div class="profile-card-header">
          <div class="card-title-section">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 15C15.866 15 19 11.866 19 8C19 4.13401 15.866 1 12 1C8.13401 1 5 4.13401 5 8C5 11.866 8.13401 15 12 15Z" stroke="currentColor" stroke-width="2"/>
                <path d="M8.21 13.89L7 23L12 20L17 23L15.79 13.88" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>{{ t('profile.overview.account_info.title') }}</h3>
          </div>
        </div>
        <div class="profile-card-content">
          <div class="profile-field-group">
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.member_since') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                      <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/>
                      <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/>
                      <line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ formatDate(userProfile.created_at) }}</span>
                </div>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.last_updated') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M23 4V10H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M20.49 15C19.9828 16.8393 18.9228 18.4804 17.4612 19.7006C15.9996 20.9207 14.2019 21.6641 12.2856 21.8281C10.3694 21.9922 8.44444 21.5705 6.77579 20.6123C5.10714 19.6541 3.76781 18.1969 2.915 16.4281C2.06219 14.6593 1.73427 12.6519 1.97979 10.6794C2.22532 8.70689 3.03423 6.8607 4.31198 5.35635C5.58973 3.852 7.27707 2.76321 9.16584 2.22672C11.0546 1.69023 13.0607 1.72429 14.93 2.32" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="23,4 12,15 9,12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ formatDate(userProfile.updated_at) }}</span>
                </div>
              </div>
            </div>
            <div v-if="userProfile.last_login" class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.last_login') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M15 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <polyline points="10,17 15,12 10,7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <line x1="15" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                  <span class="field-text">{{ formatDate(userProfile.last_login) }}</span>
                </div>
              </div>
            </div>
            <div class="profile-field">
              <span class="profile-field-label">{{ t('profile.overview.account_info.account_status') }}</span>
              <div class="profile-field-value">
                <div class="field-content">
                  <div class="field-icon">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      <path v-if="userProfile.is_active" d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <g v-else>
                        <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </g>
                    </svg>
                  </div>
                  <span class="status-badge modern-status-badge" :class="userProfile.is_active ? 'active' : 'inactive'">
                    {{ userProfile.is_active ? t('profile.overview.account_info.active') : t('profile.overview.account_info.inactive') }}
                  </span>
                </div>
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
  // Implémentation future pour l'édition des informations professionnelles
  emit('show-message', { text: 'Édition des informations professionnelles bientôt disponible', type: 'info' });
}

function editAddress() {
  // Implémentation future pour l'édition de l'adresse
  emit('show-message', { text: 'Édition de l\'adresse bientôt disponible', type: 'info' });
}
</script>
<style scoped>
.profile-overview {
  padding: 0;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

/* Loading State */
.profile-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 6rem 2rem;
  color: #64748b;
  background: white;
  border-radius: 16px;
  margin: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 3rem;
  height: 3rem;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error State */
.profile-error {
  text-align: center;
  padding: 6rem 2rem;
  color: #dc2626;
  background: white;
  border-radius: 16px;
  margin: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #fecaca;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  opacity: 0.8;
}

.profile-error h3 {
  margin: 0 0 1rem 0;
  font-size: 1.75rem;
  font-weight: 600;
  color: #374151;
}

.profile-error p {
  margin: 0;
  color: #6b7280;
  font-size: 1.1rem;
}

/* Content Grid */
.profile-content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 2rem;
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Profile Cards */
.profile-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  transition: all 0.3s ease;
  position: relative;
}

.profile-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Card Types with Subtle Headers */
.personal-info-card .profile-card-header {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
}

.professional-info-card .profile-card-header {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
}

.address-info-card .profile-card-header {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: white;
}

.account-info-card .profile-card-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.profile-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 2rem 1.5rem;
  border-bottom: none;
  position: relative;
}

.card-title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon {
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.card-icon svg {
  width: 1.5rem;
  height: 1.5rem;
  color: white;
}

.profile-card-header h3 {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

/* Modern Edit Button */
.modern-edit-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.modern-edit-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.modern-edit-btn svg {
  width: 1rem;
  height: 1rem;
}

.profile-card-content {
  padding: 2rem;
  background: white;
}

/* Profile Fields */
.profile-field-group {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.profile-field {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.profile-field-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.profile-field-value {
  font-size: 1rem;
  color: #1f2937;
  font-weight: 500;
}

.field-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.field-content:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.field-icon {
  width: 2.5rem;
  height: 2.5rem;
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.field-icon svg {
  width: 1.25rem;
  height: 1.25rem;
  color: white;
}

.field-text {
  flex: 1;
  font-size: 1rem;
  font-weight: 500;
  color: #1f2937;
}

/* Edit Field Container */
.edit-field-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 16px;
  border: 2px solid #e2e8f0;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  width: 1.25rem;
  height: 1.25rem;
  color: #6b7280;
  z-index: 1;
}

.input-icon svg {
  width: 100%;
  height: 100%;
}

.modern-input {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  font-size: 1rem;
  font-weight: 500;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  background: white;
  color: #1f2937;
  transition: all 0.2s ease;
  outline: none;
}

.modern-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.modern-input:disabled {
  background: #f1f5f9;
  color: #6b7280;
  cursor: not-allowed;
}

.edit-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.modern-save-btn, .modern-cancel-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 120px;
  justify-content: center;
}

.modern-save-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
}

.modern-save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.modern-save-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.modern-cancel-btn {
  background: #f1f5f9;
  color: #6b7280;
  border: 1px solid #e2e8f0;
}

.modern-cancel-btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #374151;
  transform: translateY(-1px);
}

.modern-save-btn svg, .modern-cancel-btn svg {
  width: 1rem;
  height: 1rem;
}

.mini-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Verification Section */
.verification-section {
  margin-left: auto;
}

/* Modern Badges */
.verification-badge {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.verification-badge svg {
  width: 1rem;
  height: 1rem;
}

.verification-badge.verified {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  border: 1px solid #34d399;
}

.verification-badge.unverified {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border: 1px solid #f59e0b;
}

.modern-role-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 700;
  padding: 0.625rem 1rem;
  border-radius: 12px;
  text-transform: capitalize;
  letter-spacing: 0.025em;
  border: 2px solid transparent;
}

.modern-role-badge.admin {
  background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
  color: #991b1b;
  border-color: #ef4444;
}

.modern-role-badge.public {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border-color: #3b82f6;
}

.modern-status-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.875rem;
  font-weight: 700;
  padding: 0.625rem 1rem;
  border-radius: 12px;
  letter-spacing: 0.025em;
  border: 2px solid transparent;
}

.modern-status-badge.active {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  border-color: #34d399;
}

.modern-status-badge.inactive {
  background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
  color: #991b1b;
  border-color: #ef4444;
}

/* Empty State */
.profile-empty {
  text-align: center;
  padding: 6rem 2rem;
  color: #6b7280;
  background: white;
  border-radius: 20px;
  margin: 2rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 5rem;
  margin-bottom: 2rem;
  opacity: 0.4;
}

.profile-empty h3 {
  margin: 0 0 1rem 0;
  font-size: 1.75rem;
  font-weight: 600;
  color: #374151;
}

.profile-empty p {
  margin: 0;
  font-size: 1.125rem;
  color: #6b7280;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .profile-content-grid {
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 1.5rem;
    padding: 1.5rem;
  }
}

@media (max-width: 768px) {
  .profile-content-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    padding: 1rem;
  }

  .profile-card-header {
    padding: 1.5rem 1.5rem 1rem;
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .card-title-section {
    width: 100%;
  }

  .modern-edit-btn {
    align-self: flex-end;
    width: auto;
  }

  .profile-card-content {
    padding: 1.5rem;
  }

  .field-content {
    padding: 0.75rem;
  }

  .field-icon {
    width: 2rem;
    height: 2rem;
  }

  .field-icon svg {
    width: 1rem;
    height: 1rem;
  }

  .card-icon {
    width: 2rem;
    height: 2rem;
  }

  .card-icon svg {
    width: 1.25rem;
    height: 1.25rem;
  }

  .edit-actions {
    flex-direction: column;
  }

  .modern-save-btn, .modern-cancel-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .profile-content-grid {
    padding: 0.5rem;
  }

  .profile-card {
    border-radius: 16px;
  }

  .profile-card-header {
    padding: 1rem;
  }

  .profile-card-content {
    padding: 1rem;
  }

  .profile-field-group {
    gap: 1.5rem;
  }

  .field-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    text-align: center;
  }

  .field-icon {
    align-self: center;
  }

  .verification-section {
    margin-left: 0;
    margin-top: 0.5rem;
  }
}

/* Smooth transitions for all interactive elements */
* {
  transition: all 0.2s ease;
}

/* Focus styles for accessibility */
.modern-edit-btn:focus,
.modern-save-btn:focus,
.modern-cancel-btn:focus,
.modern-input:focus {
  outline: 2px solid #6366f1;
  outline-offset: 2px;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .profile-card {
    border: 2px solid #000;
  }
  
  .field-content {
    border: 2px solid #000;
  }
  
  .modern-input {
    border: 2px solid #000;
  }
}

/* Reduced motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  .profile-card:hover {
    transform: none;
  }
  
  .modern-edit-btn:hover,
  .modern-save-btn:hover,
  .modern-cancel-btn:hover {
    transform: none;
  }
}
</style>
