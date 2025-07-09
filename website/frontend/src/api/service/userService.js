import axiosInstance from '@api/apiClient.js';

/**
 * Fetch current user info.
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function fetchUser() {
  return await axiosInstance.get('/user/me');
}