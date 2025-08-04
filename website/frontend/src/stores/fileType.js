import { defineStore } from 'pinia';
import fileTypeService from '@/api/service/fileTypeService.js';

export const useFileTypeStore = defineStore('fileType', {
  state: () => ({
    fileTypes: [],
    isLoading: false,
  }),
  actions: {
    async fetchFileTypes(projectId) {
      this.isLoading = true;
      try {
        if (!projectId) {
          this.fileTypes = [];
          return;
        }
        const response = await fileTypeService.getProjectFileTypes(projectId);
        this.fileTypes = [...response.data];
      } catch (err) {
        console.error('[fileTypeStore] fetchFileTypes error:', err);
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
