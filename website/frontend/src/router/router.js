import { createRouter, createWebHistory } from 'vue-router';
import { useEventMessageStore } from '@stores/eventMessage.js';
import { useUserStore } from '@stores/user.js';
import { useProjectStore } from '@stores/project.js';
import gitService from '@/api/service/gitService';

import DefaultLayout from '@/layouts/DefaultLayout.vue';
import HomePage from '@views/HomePage.vue';
import LoginPage from '@views/LoginPage.vue';
import RegisterPage from '@views/RegisterPage.vue';
import ForgotPassword from '@views/ForgotPassword.vue';
import ResetPassword from '@views/ResetPassword.vue';
import EmailVerificationPage from '@views/EmailVerificationPage.vue';
import ContactPage from '@views/ContactPage.vue';
import HTTPStatusPage from '@views/HTTPStatusPage.vue';
import ProjectsPage from '@views/ProjectsPage.vue';
import UploadPage from '@views/UploadPage.vue';
import AdminInvitationsPage from '@views/AdminInvitationsPage.vue';
import InvitationResponsePage from '@views/InvitationResponsePage.vue';
import InvitationDecisionPage from '@views/InvitationDecisionPage.vue';
import TiersPage from '@views/TiersPage.vue';
import TestProjectUsersPage from '@views/TestProjectUsersPage.vue';
import ProjectConfigurationPage from '@views/ProjectConfigurationPage.vue';
import ProfilePage from '@views/ProfilePage.vue';
import ContributionPage from '@views/ContributionPage.vue';

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
  {
    path: '/contact',
    name: 'ContactPage',
    component: ContactPage,
  },
  // Invitation response routes (public, for email links)
  {
    path: '/invitation/:action/:invitationId',
    name: 'InvitationResponse',
    component: InvitationResponsePage,
    props: true,
    meta: { requiresAuth: true },
  },
  // Invitation decision page (for notifications)
  {
    path: '/invitation/respond/:invitationId',
    name: 'InvitationDecision',
    component: InvitationDecisionPage,
    props: true,
    meta: { requiresAuth: true },
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
        path: 'contribution',
        name: 'ContributionPage',
        component: ContributionPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'tiers',
        name: 'TiersPage',
        component: TiersPage,
        meta: { requiresAuth: true },
      },
      {
        path: 'test/project-users',
        name: 'TestProjectUsersPage',
        component: TestProjectUsersPage,
        meta: { requiresAuth: true },
      },
      {
        path: '/projects/:projectId/configuration',
        name: 'ProjectConfigurationPage',
        component: ProjectConfigurationPage,
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'profile',
        name: 'ProfilePage',
        component: ProfilePage,
        meta: { requiresAuth: true },
      },
      {
        path: 'error/:statusCode',
        name: 'HTTPStatusPage',
        props: (route) => ({
          statusCode: Number(route.params.statusCode),
          message: getErrorMessage(route.params.statusCode),
        }),
        component: HTTPStatusPage,
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

  // Always wait for authentication to be initialized before allowing navigation to public auth pages
  const publicAuthPages = [
    'LoginPage',
    'RegisterPage',
    'ForgotPassword',
    'ResetPassword',
    'EmailVerificationPage',
  ];
  if (publicAuthPages.includes(to.name)) {
    // If auth state is not initialized, verify authentication first
    if (!userStore.authState.initialized) {
      await userStore.verifyAuthentication();
    }
    // If authenticated, block access
    if (userStore.isAuthenticated) {
      eventMessageStore.addMessage('event_messages.already_logged_in', 'info');
      if (from.name) return next(false);
      return next({ name: 'HomePage' });
    }
  }

  // Check if authentication verification is needed for this route
  const needsAuthCheck =
    to.meta.requiresAuth || to.meta.requiresAdmin || to.name === 'LoginPage';

  // Only verify authentication if we need it for this route
  if (needsAuthCheck && !userStore.authState.initialized) {
    await userStore.verifyAuthentication();
  }

  // Check auth for protected routes
  if (to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      return handleNotAuthenticated(eventMessageStore, to, next);
    } else {
      const projectStore = useProjectStore();
      if (!projectStore.projects.length) {
        try {
          const res = await gitService.listUserProjects();
          if (res?.projects) {
            projectStore.setProjects(res.projects);
            if (res.projects.length === 0) {
              projectStore.clearCurrentProject();
            } else {
              // Load saved currentProject from localStorage if it exists
              const savedCurrentProject =
                localStorage.getItem('currentProject');
              if (savedCurrentProject) {
                projectStore.currentProject = JSON.parse(savedCurrentProject);
              } else if (!projectStore.currentProject) {
                // Fallback: set to the first project (sorted by setProjects)
                projectStore.setCurrentProject(res.projects[0]);
              }
            }
          }
        } catch (e) {
          // Optionally handle error
          console.error('Failed to fetch projects:', e);
        }
      }
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
  if (to.name !== 'HTTPStatusPage' && from.name !== 'HTTPStatusPage') {
    localStorage.setItem('redirectTo', from.fullPath || '/');
  }
  // If user navigates from LoginPage to HomePage, update redirectAfterLogin to homepage
  if (from.name === 'LoginPage' && to.name === 'HomePage') {
    localStorage.setItem('redirectAfterLogin', '/');
  }
});

export default router;
