import axiosInstance from '@/api/apiClient';

const instanceService = {
  // Fetch instance info (optionally by name)
  async getInstanceInfo(name = null) {
    const params = name ? { params: { name } } : {};
    const { data } = await axiosInstance.get('/instance/info', params);
    return data;
  },
};

export default instanceService;
