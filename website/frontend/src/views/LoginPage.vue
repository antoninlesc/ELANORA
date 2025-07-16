<template>
  <div class="login-container-wrapper">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1 class="login-logo">ELANORA</h1>
          <p class="login-subtitle">{{ t('login.platform_subtitle') }}</p>
          <div class="instance-info">
            <span class="instance-badge"
              >{{ userStore.user?.instance_name || 'Default' }} Instance</span
            >
            <p class="instance-desc">
              {{
                t('login.connect_to_access', {
                  instanceName: userStore.user?.instance_name || 'Default',
                })
              }}
            </p>
          </div>
        </div>

        <form class="login-form" @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="email">{{ t('login.login') }}</label>
            <input
              id="login"
              v-model="loginForm.login"
              type="text"
              required
              :placeholder="t('login.login_placeholder')"
              :disabled="userStore.authState.loading"
            />
          </div>

          <div class="form-group">
            <label for="password">{{ t('login.password') }}</label>
            <input
              id="password"
              v-model="loginForm.password"
              type="password"
              required
              :placeholder="t('login.password_placeholder')"
              :disabled="userStore.authState.loading"
            />
          </div>

          <div class="login-options">
            <label class="checkbox-label">
              <input v-model="loginForm.remember" type="checkbox" />
              {{ t('login.remember_me') }}
            </label>
            <router-link to="/forgot-password" class="forgot-link">
              {{ t('login.forgot_password') }}
            </router-link>
          </div>

          <button
            type="submit"
            class="btn-primary login-btn"
            :disabled="userStore.authState.loading"
          >
            <span v-if="userStore.authState.loading">{{
              t('login.logging_in')
            }}</span>
            <span v-else>{{ t('login.login') }}</span>
          </button>
        </form>

        <div class="login-divider">
          <span>{{ t('common.or') }}</span>
        </div>

        <div class="institution-login">
          <button
            class="btn-secondary login-btn"
            :disabled="userStore.authState.loading"
            @click="handleSSOLogin"
          >
            🏛️
            <span>{{
              t('login.login_with_sso', { provider: ssoProvider })
            }}</span>
          </button>
        </div>

        <div class="login-footer">
          <p>
            {{ t('login.no_account') }}
            <a href="#" @click="requestAccess">{{
              t('login.request_access')
            }}</a>
          </p>
          <p class="invitation-text">
            {{ t('login.have_invitation') }}
            <router-link to="/register">{{
              t('login.join_project')
            }}</router-link>
          </p>
        </div>
      </div>

      <div class="login-info">
        <h3>{{ t('login.welcome_to_elanora') }}</h3>
        <div class="lab-info">
          <h4>🏛️ {{ userStore.user?.instance_name || 'Default' }}</h4>
          <p>{{ userStore.user?.institution_name || 'Institution' }}</p>
        </div>
        <ul>
          <li>✓ {{ t('login.features.collaborative_elan') }}</li>
          <li>✓ {{ t('login.features.conflict_detection') }}</li>
          <li>✓ {{ t('login.features.annotation_workflows') }}</li>
          <li>✓ {{ t('login.features.project_repositories') }}</li>
          <li>✓ {{ t('login.features.secure_instance') }}</li>
        </ul>
        <!-- Statistiques hidden if not available -->
        <div class="instance-stats loading">
          <div class="stat">
            <strong>-</strong> {{ t('login.stats.active_projects') }}
          </div>
          <div class="stat">
            <strong>-</strong> {{ t('login.stats.researchers') }}
          </div>
          <div class="stat">
            <strong>-</strong> {{ t('login.stats.elan_files') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useEventMessageStore } from '@stores/eventMessage';
import { useUserStore } from '@stores/user';

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();
const eventMessageStore = useEventMessageStore();

const loginForm = ref({
  login: '',
  password: '',
  remember: false,
});

const ssoProvider = computed(() => {
  return userStore.user?.instance_name
    ? `${userStore.user.instance_name} SSO`
    : 'SSO';
});

onMounted(() => {
  const msg = localStorage.getItem('logoutMessage');
  if (msg) {
    eventMessageStore.addMessage(msg, 'success');
    localStorage.removeItem('logoutMessage');
  }
});

const handleLogin = async () => {
  try {
    const response = await userStore.login({
      login: loginForm.value.login,
      password: loginForm.value.password,
    });

    if (response.needs_verification) {
      eventMessageStore.addMessage(
        response.message || 'Vérifiez votre email avant de vous connecter.',
        'warning'
      );
      
      // Redirect to email verification page
      router.push({
        name: 'EmailVerificationPage',
        query: { 
          email: response.email,
          freshCode: 'true'
        }
      });
      return;
    }
    if (!userStore.user) {
      eventMessageStore.addMessage('Erreur de connexion', 'error');
      return;
    }
    eventMessageStore.addMessage('Connexion réussie', 'success');
    router.push({ name: 'HomePage' });
  } catch (error) {
    console.error('Login error:', error);
    let msg = 'Erreur de connexion';
    if (error.response && error.response.data && error.response.data.detail) {
      msg = error.response.data.detail;
    }
    eventMessageStore.addMessage(msg, 'error');
  }
};

const handleSSOLogin = async () => {
  try {
    // Check if SSO is enabled
    await userStore.initiateSSOLogin();
  } catch (error) {
    console.error('SSO login error:', error);
    eventMessageStore.addMessage(t('auth.sso_error'), 'error');
  }
};

const requestAccess = async () => {
  if (!loginForm.value.login) {
    eventMessageStore.addMessage(t('auth.enter_login_first'), 'warning');
    document.getElementById('login').focus();
    return;
  }
  try {
    await userStore.requestAccess({
      login: loginForm.value.login,
    });
    eventMessageStore.addMessage(
      t('auth.access_request_sent', { login: loginForm.value.login }),
      'success'
    );
  } catch (error) {
    console.error('Access request error:', error);
    eventMessageStore.addMessage(t('auth.access_request_error'), 'error');
  }
};
</script>

<style scoped src="@/assets/css/login.css"></style>
