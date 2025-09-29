import axiosInstance from '@api/apiClient';

/**
 * Fetch instance info (optionally by name)
 * @param {string} [name] - Optional instance name
 * @returns {Promise} Promise that resolves to the instance info
 */
export async function getInstanceInfo(name = null) {
  const params = name ? { params: { name } } : {};
  const { data } = await axiosInstance.get('/instance/info', params);
  return data;
}

export const instanceService = {
  getInstanceInfo,
};

export default instanceService;
