import { defineStore } from 'pinia';

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    currentProject: null,
  }),
  actions: {
    setCurrentProject(project) {
      this.currentProject = project;
      // Save to localStorage
      localStorage.setItem('currentProject', JSON.stringify(project));
    },
    loadCurrentProject() {
      const saved = localStorage.getItem('currentProject');
      if (saved) {
        this.currentProject = JSON.parse(saved);
      }
    },
    clearCurrentProject() {
      this.currentProject = null;
      localStorage.removeItem('currentProject');
    },
  },
});
