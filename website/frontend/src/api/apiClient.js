/**
 * apiClient.js
 *
 * Configures and exports a shared axios instance for API requests.
 * - Sets base URL and default headers.
 * - Automatically attaches CSRF tokens for unsafe HTTP methods.
 * - Handles token refresh logic on 401 responses.
 * - Redirects to login after repeated failed refresh attempts.
 */

import axios from 'axios';

// Create axios instance with custom configuration
const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true, // Important for sending/receiving cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor:
 * Adds CSRF token from cookies to headers for unsafe HTTP methods (POST, PUT, DELETE, PATCH).
 */
axiosInstance.interceptors.request.use((config) => {
  // Only add CSRF token for methods that modify data
  if (
    ['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase())
  ) {
    // Get CSRF token from cookies
    const csrfToken = document.cookie
      .split('; ')
      .find((row) => row.startsWith('elanora_csrf='))
      ?.split('=')[1];

    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
  }
  return config;
});

// --- Begin token refresh logic ---

/**
 * Response interceptor:
 * Handles 401 Unauthorized errors by attempting to refresh the session token.
 * Retries failed requests after a successful refresh.
 * Redirects to login after repeated failures.
 */
let isRefreshing = false;
let failedRefreshAttempts = 0;
const MAX_REFRESH_ATTEMPTS = 3;
const waitingRequests = [];

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle CSRF token expiration (403)
    if (
      error.response?.status === 403 &&
      error.response?.data?.detail === "CSRF token missing or invalid." &&
      !originalRequest._csrfRetry
    ) {
      originalRequest._csrfRetry = true;
      try {
        // Attempt to refresh session (which should set a new CSRF token)
        await axiosInstance.post('/auth/refresh');
        // Retry the original request
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login or handle as needed
        localStorage.setItem('redirectTo', window.location.pathname);
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      failedRefreshAttempts < MAX_REFRESH_ATTEMPTS
    ) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          waitingRequests.push({
            resolve,
            reject,
            config: originalRequest,
          });
        });
      }

      isRefreshing = true;

      try {
        await axiosInstance.post('/auth/refresh');
        waitingRequests.forEach((request) => {
          axiosInstance(request.config)
            .then((response) => request.resolve(response))
            .catch((err) => request.reject(err));
        });
        waitingRequests.length = 0;
        failedRefreshAttempts = 0;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        failedRefreshAttempts++;
        if (failedRefreshAttempts >= MAX_REFRESH_ATTEMPTS) {
          localStorage.setItem('redirectTo', window.location.pathname);
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }
        waitingRequests.forEach((request) => {
          request.reject(refreshError);
        });
        waitingRequests.length = 0;
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// --- End token refresh logic ---

export default axiosInstance;
