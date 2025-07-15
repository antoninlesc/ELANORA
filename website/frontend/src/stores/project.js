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
    renameCurrentProject(newName) {
      if (this.currentProject && typeof this.currentProject === 'object') {
        this.currentProject.project_name = newName;
        localStorage.setItem(
          'currentProject',
          JSON.stringify(this.currentProject)
        );
      } else if (typeof this.currentProject === 'string') {
        this.currentProject = newName;
        localStorage.setItem('currentProject', JSON.stringify(newName));
      }
    },
  },
});
