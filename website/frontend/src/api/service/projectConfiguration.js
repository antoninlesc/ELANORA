import axiosInstance from '@api/apiClient.js';

export default {
  async getProjectConfiguration(projectId) {
    return axiosInstance.get(`/project-configuration/project/${projectId}`);
  },
};
