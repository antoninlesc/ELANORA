/**
 * authService.js
 *
 * Provides authentication-related API calls (login, logout, register, verification, password reset).
 */

import axiosInstance from '@api/apiClient.js';

/**
 * Login with user credentials.
 * @param {object} credentials
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function login(credentials) {
  return await axiosInstance.post('/auth/login', credentials);
}

/**
 * Logout the current user.
 * @param {string} [csrfToken]
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function logout(csrfToken) {
  return await axiosInstance.post(
    '/auth/logout',
    {},
    csrfToken ? { headers: { 'X-CSRF-Token': csrfToken } } : undefined
  );
}