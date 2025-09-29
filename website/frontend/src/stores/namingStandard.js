import { defineStore } from 'pinia';
import {
  getStandardsByProject,
  getProjectStandardsFull,
  createStandardWithComponents,
  deleteStandard,
} from '@/api/service/projectStandardService.js';

export const useNamingStandardStore = defineStore('namingStandard', {
  state: () => ({
    standards: [],
    componentNames: [],
    isLoading: false,
  }),
  actions: {
    async fetchNamingStandards(projectId) {
      this.isLoading = true;
      try {
        if (!projectId) {
          this.standards = [];
          return;
        }
        const response = await getStandardsByProject(projectId);
        this.standards = [...response.data];
      } catch (err) {
        console.error('Error fetching naming standards:', err);
      } finally {
        this.isLoading = false;
      }
    },
    async fetchStandardsAndComponentNames(projectId, forceRefresh = false) {
      if (this.isLoading) {
        return;
      }
      if (
        !forceRefresh &&
        this.standards.length > 0 &&
        this.componentNames.length > 0
      ) {
        return;
      }
      this.isLoading = true;
      try {
        if (!projectId) {
          this.standards = [];
          this.componentNames = [];
          return;
        }
        const { data } = await getProjectStandardsFull(projectId);
        this.standards = Array.isArray(data.standards) ? data.standards : [];
        this.componentNames = Array.isArray(data.component_names)
          ? data.component_names
          : [];
        for (const std of this.standards) {
          if (std.components) {
            std.components = std.components.map((c) => ({
              ...c,
              accepted_values: c.accepted_values || [],
              accepted_values_str: (c.accepted_values || []).join(', '),
            }));
          }
        }
      } catch (err) {
        console.error('Error fetching standards and component names:', err);
      } finally {
        this.isLoading = false;
      }
    },
    async addNamingStandard(newStandard, projectId) {
      await createStandardWithComponents(newStandard);
      await this.fetchStandardsAndComponentNames(projectId, true);
    },
    async deleteNamingStandard(id, projectId) {
      await deleteStandard(id);
      await this.fetchStandardsAndComponentNames(projectId, true);
    },
  },
});
