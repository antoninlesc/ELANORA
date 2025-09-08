import { defineStore } from 'pinia';
import effectiveNamingStandardApi from '@/api/service/effectiveNamingStandard.js';

export const useEffectiveStandardStore = defineStore('effectiveStandard', {
  state: () => ({
    locations: [],
    effectiveStandards: {},
    isLoading: false,
    error: '',
  }),
  actions: {
    async fetchLocations() {
      this.isLoading = true;
      try {
        const { data } = await effectiveNamingStandardApi.getEffectiveStandardsLocations();
        this.locations = data.locations || [];
      } catch (err) {
        console.error('Error fetching locations:', err);
        this.error = 'Failed to load locations.';
      } finally {
        this.isLoading = false;
      }
    },
    async fetchEffectiveStandards(projectId, locationId, fileTypeIds = []) {
      if (!locationId) return;
      this.isLoading = true;
      try {
        const { data } = await effectiveNamingStandardApi.getEffectiveStandards(projectId, locationId);
        const standardsMap = {};
        // Always map all returned standards for this location
        for (const eff of data.effective_standards) {
          standardsMap[eff.project_file_type_id] = eff.naming_standard_id;
        }
        // Optionally, if fileTypeIds is provided, ensure those keys exist (for UI consistency)
        for (const fileTypeId of fileTypeIds) {
          if (!(fileTypeId in standardsMap)) {
            standardsMap[fileTypeId] = "";
          }
        }
        this.effectiveStandards[locationId] = standardsMap;
        this.error = '';
      } catch (err) {
        console.error('Error fetching effective standards:', err);
        this.error = 'Failed to load effective standards.';
      } finally {
        this.isLoading = false;
      }
    },
    async assignEffectiveStandard(projectId, fileTypeId, standardId, locationId) {
      await effectiveNamingStandardApi.assignEffectiveStandard(projectId, fileTypeId, standardId, locationId);
      if (!this.effectiveStandards[locationId]) this.effectiveStandards[locationId] = {};
      this.effectiveStandards[locationId][fileTypeId] = standardId;
    },
    async unassignEffectiveStandard(projectId, fileTypeId, locationId) {
      await effectiveNamingStandardApi.unassignEffectiveStandard(projectId, fileTypeId, locationId);
      if (!this.effectiveStandards[locationId]) this.effectiveStandards[locationId] = {};
      this.effectiveStandards[locationId][fileTypeId] = "";
    },
  },
});