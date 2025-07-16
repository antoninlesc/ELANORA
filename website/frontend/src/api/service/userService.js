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