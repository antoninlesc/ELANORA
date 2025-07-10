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

/**
 * Request password reset.
 * @param {string} email
 * @param {string} [language]
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function forgotPassword(email, language) {
  const payload = { email };
  if (language) payload.language = language;
  console.log('Sending forgot password request for:', email, 'with language:', language);
  return await axiosInstance.post('/auth/forgot-password', payload);
}
