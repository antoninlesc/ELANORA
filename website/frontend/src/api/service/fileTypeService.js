import axiosInstance from '@api/apiClient.js';

export default {
  async getAllFileTypes() {
    return axiosInstance.get('/file-type/all');
  },
  async createFileType(payload) {
    return axiosInstance.post('/file-type/', payload);
  },
  async updateFileType(id, payload) {
    return axiosInstance.put(`/file-type/${id}`, payload);
  },
  async deleteFileType(id) {
    return axiosInstance.delete(`/file-type/${id}`);
  },
};
