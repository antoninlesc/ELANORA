import axiosInstance from '@api/apiClient.js';

export default {
  async getEffectiveStandards(projectId) {
    return axiosInstance.get(`/effective-naming-standard/project/${projectId}/effective-standards`);
  },
  async assignEffectiveStandard(projectId, projectFileTypeId, namingStandardId) {
    return axiosInstance.post(
      `/effective-naming-standard/project/${projectId}/filetype/${projectFileTypeId}/assign`,
      { naming_standard_id: namingStandardId }
    );
  },
  async unassignEffectiveStandard(projectId, projectFileTypeId) {
    return axiosInstance.delete(
      `/effective-naming-standard/project/${projectId}/filetype/${projectFileTypeId}/unassign`
    );
  },
};