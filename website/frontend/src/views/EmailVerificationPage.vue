<template>
  <div class="email-verification-container">
    <!-- Header -->
    <div class="verification-header">
      <div class="header-content">
        <div class="icon-container">
          <svg class="verification-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1>{{ $t('emailVerification.title') }}</h1>
        <p class="subtitle">{{ $t('emailVerification.subtitle') }}</p>
        <div class="email-display">
          <span class="email-text">{{ userEmail }}</span>
        </div>
      </div>
    </div>

    <!-- Verification Form -->
    <div class="verification-form">
      <form @submit.prevent="handleVerification">
        <div class="form-group">
          <label for="verificationCode" class="form-label">
            {{ $t('emailVerification.codeLabel') }}
          </label>
          <div class="code-input-container">
            <input
              id="verificationCode"
              v-model="verificationCode"
              type="text"
              class="code-input"
              :class="{ 'error': validationMessage }"
              :placeholder="$t('emailVerification.codePlaceholder')"
              maxlength="6"
              autocomplete="off"
              @input="onCodeInput"
              @keypress="onKeyPress"
            />
            <div v-if="isLoading" class="loading-spinner">
              <div class="spinner"></div>
            </div>
          </div>
          
          <!-- Validation Message -->
          <div v-if="validationMessage" class="validation-message error">
            <svg class="message-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" 
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" 
                    clip-rule="evenodd" />
            </svg>
            {{ validationMessage }}
          </div>

          <!-- Success Message -->
          <div v-if="successMessage" class="validation-message success">
            <svg class="message-icon" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" 
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                    clip-rule="evenodd" />
            </svg>
            {{ successMessage }}
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="button-group">
          <button
            type="submit"
            class="verify-button"
            :disabled="!verificationCode || verificationCode.length !== 6 || isLoading"
          >
            <span v-if="!isLoading">{{ $t('emailVerification.verifyButton') }}</span>
            <span v-else>{{ $t('emailVerification.verifying') }}</span>
          </button>
        </div>
      </form>

      <!-- Resend Section -->
      <div class="resend-section">
        <p class="resend-text">{{ $t('emailVerification.noCodeReceived') }}</p>
        <button
          type="button"
          class="resend-button"
          :disabled="resendCooldown > 0 || isResending"
          @click="resendVerificationCode"
        >
          <span v-if="!isResending && resendCooldown === 0">
            {{ $t('emailVerification.resendButton') }}
          </span>
          <span v-else-if="isResending">
            {{ $t('emailVerification.resending') }}
          </span>
          <span v-else>
            {{ $t('emailVerification.resendCooldown', { seconds: resendCooldown }) }}
          </span>
        </button>
      </div>

      <!-- Help Section -->
      <div class="help-section">
        <div class="help-content">
          <h3>{{ $t('emailVerification.helpTitle') }}</h3>
          <ul class="help-list">
            <li>{{ $t('emailVerification.helpCheck1') }}</li>
            <li>{{ $t('emailVerification.helpCheck2') }}</li>
            <li>{{ $t('emailVerification.helpCheck3') }}</li>
          </ul>
          <p class="help-contact">
            {{ $t('emailVerification.helpContact') }}
            <router-link to="/contact" class="contact-link">
              {{ $t('emailVerification.contactSupport') }}
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { sendVerificationEmail, verifyEmail } from '@api/service/authService.js'

export default {
  name: 'EmailVerificationPage',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const { t } = useI18n()

    // Reactive data
    const verificationCode = ref('')
    const userEmail = ref('')
    const isLoading = ref(false)
    const isResending = ref(false)
    const validationMessage = ref('')
    const successMessage = ref('')
    const resendCooldown = ref(0)
    
    let cooldownInterval = null

    // Get email from route query or localStorage
    onMounted(() => {
      userEmail.value = route.query.email || localStorage.getItem('pendingVerificationEmail') || ''
      
      if (!userEmail.value) {
        router.push('/login')
      }
      
      // Start initial cooldown if this is a fresh verification request
      if (route.query.freshCode) {
        startResendCooldown()
      }
    })

    onUnmounted(() => {
      if (cooldownInterval) {
        clearInterval(cooldownInterval)
      }
    })

    // Handle code input
    const onCodeInput = () => {
      // Clear validation messages when user types
      validationMessage.value = ''
      successMessage.value = ''
      
      // Auto-format to digits only and limit to 6 characters
      verificationCode.value = verificationCode.value.replace(/\D/g, '').slice(0, 6)
    }

    // Handle key press
    const onKeyPress = (event) => {
      // Only allow digits
      if (!/\d/.test(event.key) && !['Backspace', 'Delete', 'Tab', 'Enter'].includes(event.key)) {
        event.preventDefault()
      }
    }

    // Handle verification
    const handleVerification = async () => {
      if (!verificationCode.value || verificationCode.value.length !== 6) {
        validationMessage.value = t('emailVerification.errors.invalidCodeLength')
        return
      }

      isLoading.value = true
      validationMessage.value = ''
      successMessage.value = ''

      try {
        const response = await verifyEmail(userEmail.value, verificationCode.value)

        if (response.data.success) {
          successMessage.value = t('emailVerification.success')
          
          // Clear pending verification email
          localStorage.removeItem('pendingVerificationEmail')
          
          // Redirect to login after a short delay
          setTimeout(() => {
            router.push('/login?verified=true')
          }, 2000)
        } else {
          validationMessage.value = response.data.message || t('emailVerification.errors.invalidCode')
        }
      } catch (error) {
        console.error('Email verification error:', error)
        validationMessage.value = error.response?.data?.detail || t('emailVerification.errors.verificationFailed')
      } finally {
        isLoading.value = false
      }
    }

    // Resend verification code
    const resendVerificationCode = async () => {
      if (resendCooldown.value > 0 || isResending.value) {
        return
      }

      isResending.value = true
      validationMessage.value = ''
      successMessage.value = ''

      try {
        const response = await sendVerificationEmail(userEmail.value, localStorage.getItem('language') || 'en')

        if (response.data.success) {
          successMessage.value = t('emailVerification.resendSuccess')
          startResendCooldown()
        } else {
          validationMessage.value = response.data.message || t('emailVerification.errors.resendFailed')
        }
      } catch (error) {
        console.error('Resend verification error:', error)
        validationMessage.value = error.response?.data?.detail || t('emailVerification.errors.resendFailed')
      } finally {
        isResending.value = false
      }
    }

    // Start resend cooldown
    const startResendCooldown = () => {
      resendCooldown.value = 60 // 60 seconds cooldown
      
      cooldownInterval = setInterval(() => {
        resendCooldown.value--
        if (resendCooldown.value <= 0) {
          clearInterval(cooldownInterval)
          cooldownInterval = null
        }
      }, 1000)
    }

    return {
      verificationCode,
      userEmail,
      isLoading,
      isResending,
      validationMessage,
      successMessage,
      resendCooldown,
      handleVerification,
      resendVerificationCode,
      onCodeInput,
      onKeyPress
    }
  }
}
</script>

<style scoped>
.email-verification-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  padding: 2rem 1rem;
}

.verification-header {
  text-align: center;
  margin-bottom: 3rem;
}

.header-content {
  max-width: 500px;
  margin: 0 auto;
}

.icon-container {
  margin-bottom: 1.5rem;
}

.verification-icon {
  width: 4rem;
  height: 4rem;
  color: white;
  background: rgba(255, 255, 255, 0.2);
  padding: 1rem;
  border-radius: 50%;
  backdrop-filter: blur(10px);
}

.verification-header h1 {
  color: white;
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
  margin: 0 0 1.5rem 0;
  line-height: 1.6;
}

.email-display {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2rem;
  padding: 0.75rem 1.5rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.email-text {
  color: white;
  font-weight: 600;
  font-size: 1rem;
}

.verification-form {
  max-width: 500px;
  margin: 0 auto;
  background: white;
  border-radius: 1rem;
  padding: 2.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.form-group {
  margin-bottom: 2rem;
}

.form-label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

.code-input-container {
  position: relative;
}

.code-input {
  width: 100%;
  padding: 1rem 1.25rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.5rem;
  font-family: 'Courier New', monospace;
  transition: all 0.2s ease;
  background: #f9fafb;
}

.code-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  background: white;
}

.code-input.error {
  border-color: #dc2626;
  background: #fef2f2;
}

.loading-spinner {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
}

.spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 2px solid #e5e7eb;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.validation-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.validation-message.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.validation-message.success {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.message-icon {
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
}

.button-group {
  margin-bottom: 2rem;
}

.verify-button {
  width: 100%;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 0.75rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.verify-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  transform: translateY(-1px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.verify-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.resend-section {
  text-align: center;
  padding: 1.5rem 0;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 2rem;
}

.resend-text {
  color: #6b7280;
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
}

.resend-button {
  background: none;
  border: 2px solid #2563eb;
  color: #2563eb;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.resend-button:hover:not(:disabled) {
  background: #2563eb;
  color: white;
}

.resend-button:disabled {
  border-color: #9ca3af;
  color: #9ca3af;
  cursor: not-allowed;
}

.help-section {
  background: #f8fafc;
  border-radius: 0.75rem;
  padding: 1.5rem;
}

.help-content h3 {
  color: #374151;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.help-list {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.6;
  margin: 0 0 1rem 0;
  padding-left: 1.25rem;
}

.help-list li {
  margin-bottom: 0.5rem;
}

.help-contact {
  color: #6b7280;
  font-size: 0.875rem;
  margin: 0;
}

.contact-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.contact-link:hover {
  text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 640px) {
  .email-verification-container {
    padding: 1rem 0.5rem;
  }
  
  .verification-header h1 {
    font-size: 2rem;
  }
  
  .verification-form {
    padding: 1.5rem;
    margin: 0 0.5rem;
  }
  
  .code-input {
    font-size: 1.25rem;
    letter-spacing: 0.25rem;
  }
}
</style>
