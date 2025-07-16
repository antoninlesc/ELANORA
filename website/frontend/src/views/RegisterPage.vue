<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <img src="/images/ELANora-logo.png" alt="ELANORA Logo" class="register-logo" />
        <h1 class="register-title">{{ t('register.title') }}</h1>
        <p v-if="invitationValid" class="register-subtitle invitation-welcome">
          {{ t('register.invitation_welcome', { senderName: invitationInfo?.sender_username || 'Un administrateur' }) }}
        </p>
        <p v-else class="register-subtitle">
          {{ t('register.subtitle') }}
        </p>
      </div>

      <!-- Invitation Code Section -->
      <div v-if="!invitationValid" class="invitation-section">
        <div class="form-group">
          <label for="invitation-code" class="form-label">
            {{ t('register.invitation_code_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="invitation-code"
            v-model="invitationCode"
            type="text"
            class="form-input"
            :class="{ 'error': invitationError }"
            :placeholder="t('register.invitation_code_placeholder')"
            @input="validateInvitationCode"
          />
          <div v-if="invitationError" class="error-message">{{ invitationError }}</div>
          <div v-if="invitationValidating" class="info-message">
            {{ t('register.validating_invitation') }}
          </div>
          <div v-if="invitationValid" class="success-message">
            {{ t('register.invitation_valid') }}
          </div>
        </div>
      </div>

      <!-- Registration Form -->
      <form v-if="invitationValid" @submit.prevent="handleRegister" class="register-form">
        <div class="form-row">
          <div class="form-group">
            <label for="first-name" class="form-label">
              {{ t('register.first_name_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="first-name"
              v-model="form.firstName"
              type="text"
              class="form-input"
              :placeholder="t('register.first_name_placeholder')"
              required
            />
          </div>
          <div class="form-group">
            <label for="last-name" class="form-label">
              {{ t('register.last_name_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="last-name"
              v-model="form.lastName"
              type="text"
              class="form-input"
              :placeholder="t('register.last_name_placeholder')"
              required
            />
          </div>
        </div>

        <div class="form-group">
          <label for="username" class="form-label">
            {{ t('register.username_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="username"
            v-model="form.username"
            type="text"
            class="form-input"
            :class="{ 'error': usernameAvailable === false }"
            :placeholder="t('register.username_placeholder')"
            required
            autocomplete="username"
          />
          <div v-if="usernameCheckLoading" class="info-message">{{ t('register.checking_username') }}</div>
          <div v-if="usernameAvailable === true" class="success-message">{{ usernameCheckMessage }}</div>
          <div v-if="usernameAvailable === false" class="error-message">{{ usernameCheckMessage }}</div>
        </div>

        <!-- Email field -->

        <div class="form-row">
          <div class="form-group">
            <label for="password" class="form-label">
              {{ t('register.password_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              :placeholder="t('register.password_placeholder')"
              required
              autocomplete="new-password"
            />
          </div>
          <div class="form-group">
            <label for="confirm-password" class="form-label">
              {{ t('register.confirm_password_label') }}
              <span class="required">*</span>
            </label>
            <input 
              id="confirm-password"
              v-model="form.confirmPassword"
              type="password"
              class="form-input"
              :placeholder="t('register.confirm_password_placeholder')"
              required
              autocomplete="new-password"
            />
          </div>
        </div>
        <div class="form-group">
          <label for="email" class="form-label">
            {{ t('register.email_label') }}
            <span class="required">*</span>
          </label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="form-input"
            :placeholder="t('register.email_placeholder')"
            required
            :disabled="!!invitationInfo?.receiver_email"
          />
        </div>
        <div class="form-group">
          <label for="confirm-email" class="form-label">
            {{ t('register.confirm_email_label') }}
            <span class="required">*</span>
          </label>
          <input
            id="confirm-email"
            v-model="form.confirmEmail"
            type="email"
            class="form-input"
            :placeholder="t('register.confirm_email_placeholder')"
            required
            :disabled="!!invitationInfo?.receiver_email"
          />
        </div>

        <div class="form-group">
          <label for="phone" class="form-label">
            {{ t('register.phone_label') }}
          </label>
          <input 
            id="phone"
            v-model="form.phoneNumber"
            type="tel"
            class="form-input"
            :placeholder="t('register.phone_placeholder')"
          />
        </div>

        <div class="form-group">
          <label for="affiliation" class="form-label">
            {{ t('register.affiliation_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="affiliation"
            v-model="form.affiliation"
            type="text"
            class="form-input"
            :placeholder="t('register.affiliation_placeholder')"
            required
          />
        </div>
        <div class="form-group">
          <label for="department" class="form-label">
            {{ t('register.department_label') }}
            <span class="required">*</span>
          </label>
          <input 
            id="department"
            v-model="form.department"
            type="text"
            class="form-input"
            :placeholder="t('register.department_placeholder')"
            required
          />
        </div>

        <!-- Address Section -->
        <div class="address-section">
          <h3 class="section-title">{{ t('register.address_section') }}</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label for="country" class="form-label">
                {{ t('register.country_label') }}
                <span class="required">*</span>
              </label>
              <select 
                id="country"
                v-model="form.address.countryId"
                class="form-select"
                @change="onCountryChange"
                required
              >
                <option value="">{{ t('register.country_placeholder') }}</option>
                <option 
                  v-for="country in countries" 
                  :key="country.country_id" 
                  :value="country.country_id"
                >
                  {{ country.country_name }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label for="city" class="form-label">
                {{ t('register.city_label') }}
                <span class="required">*</span>
              </label>
              <input 
                id="city"
                v-model="form.address.cityName"
                type="text"
                class="form-input"
                :placeholder="t('register.city_placeholder')"
                required
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="streetName" class="form-label">
                {{ t('register.street_name_label') }}
                <span class="required">*</span>
              </label>
              <input 
                id="streetName"
                v-model="form.address.streetName"
                type="text"
                class="form-input"
                :placeholder="t('register.street_name_placeholder')"
                required
              />
            </div>

            <div class="form-group">
              <label for="streetNumber" class="form-label">
                {{ t('register.street_number_label') }}
              </label>
              <input 
                id="streetNumber"
                v-model="form.address.streetNumber"
                type="text"
                class="form-input"
                :placeholder="t('register.street_number_placeholder')"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="postalCode" class="form-label">
                {{ t('register.postal_code_label') }}
                <span class="required">*</span>
              </label>
              <input 
                id="postalCode"
                v-model="form.address.postalCode"
                type="text"
                class="form-input"
                :placeholder="t('register.postal_code_placeholder')"
                required
              />
            </div>

            <div class="form-group">
              <label for="addressLine2" class="form-label">
                {{ t('register.address_line2_label') }}
              </label>
              <input 
                id="addressLine2"
                v-model="form.address.addressLine2"
                type="text"
                class="form-input"
                :placeholder="t('register.address_line2_placeholder')"
              />
            </div>
          </div>
        </div>

        <button 
          type="submit" 
          class="btn-primary register-btn" 
          :disabled="loading || !invitationValid"
        >
          <span v-if="loading">{{ t('register.registering') }}</span>
          <span v-else>{{ t('register.submit') }}</span>
        </button>
      </form>

      <div class="register-footer">
        <p>
          {{ t('register.already_have_account') }}
          <router-link to="/" class="link">{{ t('register.login_here') }}</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage';
import { validateInvitation } from '@/api/service/invitationService';
import { registerWithInvitation } from '@/api/service/authService';
import { getCountries } from '@/api/service/locationService';
import { checkUsernameAvailability } from '@/api/service/userService';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const eventMessageStore = useEventMessageStore();

// Reactive data
const invitationCode = ref('');
const invitationValid = ref(false);
const invitationValidating = ref(false);
const invitationError = ref('');
const invitationInfo = ref(null);
const loading = ref(false);
const countries = ref([]);

const form = ref({
  firstName: '',
  lastName: '',
  username: '',
  email: '',
  confirmEmail: '',
  password: '',
  confirmPassword: '',
  phoneNumber: '',
  affiliation: '',
  department: '',
  address: {
    countryId: '',
    cityName: '',
    streetName: '',
    streetNumber: '',
    postalCode: '',
    addressLine2: ''
  }
});

// Username availability check
const usernameAvailable = ref(null);
const usernameCheckLoading = ref(false);
const usernameCheckMessage = ref('');
let usernameCheckTimeout = null;

// Check for invitation code in URL params
onMounted(async () => {
  const invitationParam = route.query.invitation;
  if (invitationParam) {
    invitationCode.value = invitationParam;
    validateInvitationCode();
  }
  
  // Load countries
  await loadCountries();
});

// Watch for changes in invitation code
watch(invitationCode, (newValue) => {
  if (newValue && newValue.length > 0) {
    invitationError.value = '';
  }
});

const validateInvitationCode = async () => {
  if (!invitationCode.value || invitationCode.value.length === 0) {
    invitationError.value = t('register.invitation_code_required');
    invitationValid.value = false;
    return;
  }

  invitationValidating.value = true;
  invitationError.value = '';

  try {
    const response = await validateInvitation(invitationCode.value);
    if (response.data.valid) {
      invitationValid.value = true;
      invitationInfo.value = response.data.invitation;
      
      // Pre-fill email if available and disable editing
      if (invitationInfo.value?.receiver_email) {
        form.value.email = invitationInfo.value.receiver_email;
        form.value.confirmEmail = invitationInfo.value.receiver_email;
      } else {
        form.value.email = '';
        form.value.confirmEmail = '';
      }
      
      eventMessageStore.addMessage(t('register.invitation_valid'), 'success');
    } else {
      invitationValid.value = false;
      invitationError.value = response.data.message || t('register.invitation_invalid');
    }
  } catch (error) {
    invitationValid.value = false;
    invitationError.value = error.response?.data?.detail || t('register.invitation_validation_error');
  } finally {
    invitationValidating.value = false;
  }
};

// Load countries from API
const loadCountries = async () => {
  try {
    const response = await getCountries();
    if (response.success) {
      countries.value = response.data;
    } else {
      eventMessageStore.addMessage(t('register.error_loading_countries'), 'error');
    }
  } catch (error) {
    console.error('Error loading countries:', error);
    eventMessageStore.addMessage(t('register.error_loading_countries'), 'error');
  }
};

const handleRegister = async () => {
  // Validate form

  if (form.value.password !== form.value.confirmPassword) {
    eventMessageStore.addMessage(t('register.passwords_no_match'), 'error');
    return;
  }

  if (form.value.email !== form.value.confirmEmail) {
    eventMessageStore.addMessage(t('register.emails_no_match'), 'error');
    return;
  }

  if (form.value.password.length < 8) {
    eventMessageStore.addMessage(t('register.password_too_short'), 'error');
    return;
  }

  loading.value = true;

  try {
    // Prepare address object if fields are filled
    let address = null;
    if (form.value.address.streetName && form.value.address.cityName && form.value.address.postalCode && form.value.address.countryId) {
      address = {
        street_name: form.value.address.streetName,
        street_number: form.value.address.streetNumber || null,
        city_name: form.value.address.cityName,
        country_id: parseInt(form.value.address.countryId),
        postal_code: form.value.address.postalCode,
        address_line_2: form.value.address.addressLine2 || null
      };
    }

    // API call for registration with invitation
    const payload = {
      invitation_code: invitationCode.value,
      first_name: form.value.firstName,
      last_name: form.value.lastName,
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
      phone_number: form.value.phoneNumber || null,
      affiliation: form.value.affiliation,
      department: form.value.department,
      address: address
    };
    await registerWithInvitation(payload);
    eventMessageStore.addMessage(t('register.success'), 'success');
    router.push({ name: 'LoginPage' });
  } catch (error) {
    console.error('Registration error:', error);
    eventMessageStore.addMessage(
      error?.response?.data?.detail || t('register.error'),
      'error'
    );
  } finally {
    loading.value = false;
  }
};

// Username availability check
watch(() => form.value.username, (newUsername) => {
  usernameAvailable.value = null;
  usernameCheckMessage.value = '';
  if (usernameCheckTimeout) clearTimeout(usernameCheckTimeout);
  if (!newUsername || newUsername.length < 3) return;
  usernameCheckLoading.value = true;
  usernameCheckTimeout = setTimeout(async () => {
    try {
      const res = await checkUsernameAvailability(newUsername);
      usernameAvailable.value = res.available;
      usernameCheckMessage.value = res.message;
    } catch (e) {
      console.error('Username check error:', e);
      usernameAvailable.value = null;
      usernameCheckMessage.value = t('register.username_check_error');
    } finally {
      usernameCheckLoading.value = false;
    }
  }, 500);
});
</script>

<style scoped src="@/assets/css/register.css"></style>
