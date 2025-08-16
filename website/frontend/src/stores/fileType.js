import { defineStore } from 'pinia';
import fileTypeService from '@/api/service/fileTypeService.js';

export const useFileTypeStore = defineStore('fileType', {
  state: () => ({
    fileTypes: [],
    isLoading: false,
  }),
  actions: {
    async fetchFileTypes(projectId) {
      if (this.isLoading) {
        return;
      }
      if (this.fileTypes.length > 0) {
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
    async addFileType(newFileType, projectId) {
      await fileTypeService.addProjectFileType(projectId, newFileType);
      await this.fetchFileTypes(projectId);
    },
    async deleteFileType(id, projectId) {
      await fileTypeService.deleteProjectFileType(projectId, id);
      await this.fetchFileTypes(projectId);
    },
    async updateFileType(id, update, projectId) {
      await fileTypeService.updateProjectFileType(projectId, id, update);
      await this.fetchFileTypes(projectId);
    },
  },
});
