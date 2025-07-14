import { createRouter, createWebHistory } from 'vue-router';
import { useEventMessageStore } from '@stores/eventMessage.js';
import { useUserStore } from '@stores/user.js';

import HomePage from '@views/HomePage.vue';
import LoginPage from '@views/LoginPage.vue';
import RegisterPage from '@views/RegisterPage.vue';
import ForgotPassword from '@views/ForgotPassword.vue';
import ResetPassword from '@views/ResetPassword.vue';
import HTTPStatus from '@views/HTTPStatus.vue';

// Define routes
const routes = [
  {
    path: '/',
    name: 'LoginPage',
    component: LoginPage,
  },
  {
    path: '/homePage',
    name: 'HomePage',
    component: HomePage,
    meta: { requiresAuth: true },
  },
  {
    path: '/register',
    name: 'RegisterPage',
    component: RegisterPage,
  },
  {
    path: '/projects',
    name: 'ProjectsPage',
    component: () => import('@views/ProjectsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/invitations',
    name: 'AdminInvitationsPage',
    component: () => import('@views/AdminInvitationsPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPassword,

  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPassword,
    
  },
  {
    path: '/error/:statusCode',
    name: 'HTTPStatus',
    props: (route) => ({
      statusCode: String(route.params.statusCode),
      message: getErrorMessage(route.params.statusCode),
    }),
    component: HTTPStatus,
  },
  {
    // Catch-all to redirect to 404 page when no route matches
    path: '/:catchAll(.*)',
    redirect: '/error/404',
  },
];

// Function to map status codes to messages
function getErrorMessage(status) {
  const messages = {
    400: '400',
    401: '401',
    403: '403',
    404: '404',
    405: '405',
    408: '408',
    500: '500',
    502: '502',
    503: '503',
  };
  return messages[status] || 'An unknown error occurred.';
}

// Create the router instance
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Helper: handle not authenticated
function handleNotAuthenticated(eventMessageStore, to, next) {
  localStorage.setItem('redirectAfterLogin', to.fullPath);
  eventMessageStore.addMessage('http_status.401', 'warning');
  next({ name: 'LoginPage' });
}

// Global route guard
router.beforeEach((to, from, next) => {
  const eventMessageStore = useEventMessageStore();
  const userStore = useUserStore();
  console.log('userStore', userStore);
  console.log(
    'userStore.authState.initialized',
    userStore.authState.initialized
  );
  console.log('userStore.isAuthenticated', userStore.isAuthenticated);
  // Handle login route: redirect if already authenticated
  if (to.name === 'LoginPage' && userStore.isAuthenticated) {
    eventMessageStore.addMessage('event_messages.already_logged_in', 'warning');
    if (from.name) return next(false);
    return next({ name: 'HomePage' });
  }

  // Only check auth if required
  if (to.meta.requiresAuth) {
    if (!userStore.authState.initialized) {
      // Let App.vue handle the loading spinner, just allow navigation to continue
      return next();
    }
    if (!userStore.isAuthenticated) {
      return handleNotAuthenticated(eventMessageStore, to, next);
    }
  }
  next();
});

// Add afterEach to track last successful route for redirectTo
router.afterEach((to, from) => {
  // Don't update redirectTo if navigating to or coming from the HTTPStatus error page
  if (to.name !== 'HTTPStatus' && from.name !== 'HTTPStatus') {
    localStorage.setItem('redirectTo', from.fullPath || '/');
  }
  // If user navigates from LoginPage to HomePage, update redirectAfterLogin to homepage
  if (from.name === 'LoginPage' && to.name === 'HomePage') {
    localStorage.setItem('redirectAfterLogin', '/');
  }
});

export default router;
