import { createRouter, createWebHistory } from 'vue-router';
import { useEventMessageStore } from '@stores/eventMessage.js';
import { useUserStore } from '@stores/user.js';

import DefaultLayout from '@/layouts/DefaultLayout.vue';
import HomePage from '@views/HomePage.vue';
import LoginPage from '@views/LoginPage.vue';
import RegisterPage from '@views/RegisterPage.vue';
import ForgotPassword from '@views/ForgotPassword.vue';
import ResetPassword from '@views/ResetPassword.vue';
import EmailVerificationPage from '@views/EmailVerificationPage.vue';
import HTTPStatus from '@views/HTTPStatus.vue';
import ProjectsPage from '@views/ProjectsPage.vue';
import UploadPage from '@views/UploadPage.vue';
import ConflictsPage from '@views/ConflictsPage.vue';
import AdminInvitationsPage from '@views/AdminInvitationsPage.vue';
import TiersPage from '@views/TiersPage.vue';

// Define routes
const routes = [
  // Public routes
  {
    path: '/',
    name: 'LoginPage',
    component: LoginPage,
  },
  {
    path: '/register',
    name: 'RegisterPage',
    component: RegisterPage,
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
    path: '/verify-email',
    name: 'EmailVerificationPage',
    component: EmailVerificationPage,
  },
  // Authenticated routes with layout
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: 'homePage',
        name: 'HomePage',
        component: HomePage,
        meta: { requiresAuth: true },
      },
      {
        path: 'projects',
        name: 'ProjectsPage',
        component: ProjectsPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'admin/invitations',
        name: 'AdminInvitationsPage',
        component: AdminInvitationsPage,
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'upload',
        name: 'UploadPage',
        component: UploadPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'conflicts',
        name: 'Conflicts',
        component: ConflictsPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'tiers',
        name: 'TiersPage',
        component: TiersPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'error/:statusCode',
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
    ],
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
router.beforeEach(async (to, from, next) => {
  const eventMessageStore = useEventMessageStore();
  const userStore = useUserStore();

  // Check if authentication verification is needed for this route
  const needsAuthCheck =
    to.meta.requiresAuth || to.meta.requiresAdmin || to.name === 'LoginPage';

  // Only verify authentication if we need it for this route
  if (needsAuthCheck && !userStore.authState.initialized) {
    console.log('Authentication verification needed, verifying...');
    await userStore.verifyAuthentication();
  }

  // Handle login route: redirect if already authenticated
  if (to.name === 'LoginPage' && userStore.isAuthenticated) {
    eventMessageStore.addMessage('event_messages.already_logged_in', 'info');
    if (from.name) return next(false);
    return next({ name: 'HomePage' });
  }

  // Check auth for protected routes
  if (to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      return handleNotAuthenticated(eventMessageStore, to, next);
    }
  }

  // Check admin role for admin routes
  if (to.meta.requiresAdmin) {
    if (!userStore.user?.role || userStore.user.role !== 'admin') {
      eventMessageStore.addMessage('http_status.403', 'error');
      return next({ name: 'HomePage' });
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
