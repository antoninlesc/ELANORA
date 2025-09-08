import { defineStore } from 'pinia';
import fileTypeService from '@/api/service/fileTypeService.js';
import projectLocationFileTypeService from '@/api/service/projectLocationFileTypeService.js';

export const useFileTypeStore = defineStore('fileType', {
  state: () => ({
    fileTypes: [],
    fileTypesByLocation: {},
    isLoading: false,
  }),
  actions: {
    async fetchFileTypes(projectId) {
      if (this.isLoading) {
        return;
      }
      this.isLoading = true;
      try {
        if (!projectId) {
          this.fileTypes = [];
          return;
        }
        const response = await fileTypeService.getProjectFileTypes(projectId);
        this.fileTypes = [...response.data];
      } catch (err) {
        console.error('Error fetching file types:', err);
      } finally {
        this.isLoading = false;
      }
    },
    async fetchFileTypesForLocation(projectId, locationId) {
      if (!locationId) return;
      const { data } = await projectLocationFileTypeService.getFileTypesForLocation(projectId, locationId);
      this.fileTypesByLocation[locationId] = data.file_types.map(ft => ft.project_file_type_id);
    },
    async addFileTypeToLocation(projectId, locationId, fileTypeId) {
      await projectLocationFileTypeService.addFileTypeToLocation(projectId, locationId, fileTypeId);
      await this.fetchFileTypesForLocation(projectId, locationId);
    },
    async removeFileTypeFromLocation(projectId, locationId, fileTypeId) {
      await projectLocationFileTypeService.removeFileTypeFromLocation(projectId, locationId, fileTypeId);
      await this.fetchFileTypesForLocation(projectId, locationId);
    },
    async addFileType(newFileType, projectId) {
      await fileTypeService.addProjectFileType(projectId, newFileType);
      await this.fetchFileTypes(projectId);
    },
    async deleteFileType(id, projectId) {
      await fileTypeService.deleteProjectFileType(projectId, id);
      await this.fetchFileTypes(projectId);
      // Remove from all location associations
      Object.keys(this.fileTypesByLocation).forEach(locationId => {
        this.fileTypesByLocation[locationId] = this.fileTypesByLocation[locationId].filter(ftId => ftId !== id);
      });
    },
    async updateFileType(id, update, projectId) {
      await fileTypeService.updateProjectFileType(projectId, id, update);
      await this.fetchFileTypes(projectId);
    },
  },
});
