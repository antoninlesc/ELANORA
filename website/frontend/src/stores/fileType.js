import { defineStore } from 'pinia';
import fileTypeService from '@/api/service/fileTypeService.js';

export const useFileTypeStore = defineStore('fileType', {
  state: () => ({
    fileTypes: [],
    isLoading: false,
  }),
  actions: {
    async fetchFileTypes() {
      this.isLoading = true;
      try {
        const { data } = await fileTypeService.getAllFileTypes();
        this.fileTypes = Array.isArray(data) ? data : [];
      } finally {
        this.isLoading = false;
      }
    },
    async addFileType(newFileType) {
      await fileTypeService.createFileType(newFileType);
      await this.fetchFileTypes();
    },
    async deleteFileType(id) {
      await fileTypeService.deleteFileType(id);
      await this.fetchFileTypes();
    },
    async updateFileType(id, update) {
      await fileTypeService.updateFileType(id, update);
      await this.fetchFileTypes();
    },
  },
});
