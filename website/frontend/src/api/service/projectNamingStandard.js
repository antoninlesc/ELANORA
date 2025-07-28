import axiosInstance from '@api/apiClient.js';

export default {
  async getStandardsByProject(projectId) {
    return axiosInstance.get(`/project-naming-standard/project/${projectId}`);
  },
  async getStandardWithComponents(standardId) {
    return axiosInstance.get(`/project-naming-standard/${standardId}`);
  },
  async createStandardWithComponents(payload) {
    return axiosInstance.post('/project-naming-standard/create', payload);
  },
  async updateStandardAndComponents(standardId, updateFields, components) {
    return axiosInstance.put(`/project-naming-standard/${standardId}/update`, {
      update_fields: updateFields,
      components,
    });
  },
  async deleteStandard(standardId) {
    return axiosInstance.delete(`/project-naming-standard/${standardId}`);
  },
  async getComponentNames(projectId) {
    return axiosInstance.get(
      `/project-naming-standard/project/${projectId}/component-names`
    );
  },
};
