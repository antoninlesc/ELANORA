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

/**
 * Reset password with verification code.
 * @param {string} email
 * @param {string} code
 * @param {string} newPassword
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function resetPassword(email, code, newPassword) {
  const payload = { email, code, new_password: newPassword };
  console.log('Sending reset password request for:', email);
  return await axiosInstance.post('/auth/reset-password', payload);
}

/**
 * Register a user with an invitation code.
 * @param {Object} data - Registration data
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function registerWithInvitation(data) {
  return await axiosInstance.post('/auth/register', data);
}
