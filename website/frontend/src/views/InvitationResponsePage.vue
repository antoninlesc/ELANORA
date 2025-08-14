<template>
  <div class="invitation-response-page">
    <div class="container">
      <div class="response-card">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>{{ t('invitation.processing') }}</p>
        </div>

        <!-- Success State -->
        <div v-else-if="success" class="success-state">
          <div class="icon success-icon">✓</div>
          <h1>{{ successTitle }}</h1>
          <p>{{ successMessage }}</p>
          <router-link to="/projects" class="btn-primary">
            {{ t('invitation.go_to_projects') }}
          </router-link>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <div class="icon error-icon">✗</div>
          <h1>{{ t('invitation.error_title') }}</h1>
          <p>{{ errorMessage }}</p>
          <router-link to="/homePage" class="btn-secondary">
            {{ t('invitation.back_to_home') }}
          </router-link>
        </div>

        <!-- Default State (shouldn't appear) -->
        <div v-else class="loading-state">
          <p>{{ t('invitation.processing') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import {
  acceptInvitation,
  rejectInvitation,
} from '@/api/service/invitationService';

const route = useRoute();
const { t } = useI18n();

const loading = ref(true);
const success = ref(false);
const error = ref(false);
const errorMessage = ref('');
const action = ref('');

const successTitle = computed(() => {
  return action.value === 'accept'
    ? t('invitation.accept_success_title')
    : t('invitation.reject_success_title');
});

const successMessage = computed(() => {
  return action.value === 'accept'
    ? t('invitation.accept_success_message')
    : t('invitation.reject_success_message');
});

const processInvitation = async () => {
  try {
    const invitationId = route.params.invitationId;
    action.value = route.params.action;

    if (!invitationId || !['accept', 'reject'].includes(action.value)) {
      throw new Error('Invalid invitation parameters');
    }

    let response;
    if (action.value === 'accept') {
      response = await acceptInvitation(invitationId);
    } else {
      response = await rejectInvitation(invitationId);
    }

    if (response.data.success) {
      success.value = true;
    } else {
      throw new Error(response.data.message || 'Unknown error');
    }
  } catch (err) {
    console.error('Error processing invitation:', err);
    error.value = true;
    errorMessage.value =
      err.response?.data?.detail ||
      err.message ||
      t('invitation.general_error');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  processInvitation();
});
</script>

<style scoped>
.invitation-response-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.container {
  max-width: 500px;
  width: 100%;
}

.response-card {
  background: white;
  border-radius: 1rem;
  padding: 3rem;
  box-shadow: 0 20px 60px rgb(0 0 0 / 10%);
  text-align: center;
}

.loading-state,
.success-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.icon {
  width: 4rem;
  height: 4rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
  color: white;
}

.success-icon {
  background: #10b981;
}

.error-icon {
  background: #ef4444;
}

.spinner {
  width: 3rem;
  height: 3rem;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

p {
  font-size: 1rem;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
}

.btn-primary,
.btn-secondary {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background: #4b5563;
}
</style>
