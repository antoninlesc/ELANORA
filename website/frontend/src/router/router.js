import { createRouter, createWebHistory } from 'vue-router';
import { useEventMessageStore } from '@stores/eventMessage.js';
import { useUserStore } from '@stores/user.js';

// TODO: Import views
// import HomePage from '@views/HomePage.vue';
// import HTTPStatus from '@views/HTTPStatus.vue';
// ... add other view imports

// Define routes
const routes = [
  {
    path: '/',
    name: 'homePage',
    component: () => import('@views/homePage.vue'), // Lazy load for now
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@views/login.vue'),
    meta: { requiresGuest: true }
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
  next({ name: 'Login' }); 
}

// Helper: handle role denied
function handleRoleDenied(
  eventMessageStore,
  from,
  next,
  attempts,
  statusCode = 403
) {
  const newAttempts = attempts + 1;
  localStorage.setItem('permissionDeniedAttempts', newAttempts.toString());
  if (newAttempts <= 2) {
    eventMessageStore.addMessage('event_messages.permission_denied', 'warning');
    if (from.name) next(false);
    else next({ name: 'HomePage' });
  } else {
    next({ name: 'HTTPStatus', params: { statusCode } });
  }
}

// Global route guard
router.beforeEach((to, from, next) => {
  const eventMessageStore = useEventMessageStore();
  const userStore = useUserStore();

  // Vérifie si la route nécessite d'être non authentifié
  if (to.meta.requiresGuest && userStore.authState.isAuthenticated) {
    next({ name: 'homePage' });
    return;
  }
  // Vérifie si la route nécessite d'être authentifié
  if (to.meta.requiresAuth && !userStore.authState.isAuthenticated) {
    handleNotAuthenticated(eventMessageStore, to, next);
    return;
  }
  next();
});

// Add afterEach to track last successful route for redirectTo
router.afterEach((to, from) => {
  // TODO: Add after navigation logic
});

export default router;
