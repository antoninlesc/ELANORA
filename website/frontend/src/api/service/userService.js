import axiosInstance from '@api/apiClient.js';

/**
 * Fetch current user info.
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function fetchUser() {
  return await axiosInstance.get('/user/me');
}

/**
 * Check if a username is available for registration.
 * @param {string} username
 * @returns {Promise<{ available: boolean, message: string }>}
 */
export async function checkUsernameAvailability(username) {
  const response = await axiosInstance.get(`/auth/check-username/${encodeURIComponent(username)}`);
  return response.data;
}

/**
 * Check if an email is available for registration.
 * @param {string} email
 * @returns {Promise<{ available: boolean, message: string }>}
 */
export async function checkEmailAvailability(email) {
  const response = await axiosInstance.get(`/auth/check-email/${encodeURIComponent(email)}`);
  return response.data;
}