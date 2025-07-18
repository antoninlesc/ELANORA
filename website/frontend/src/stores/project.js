import { defineStore } from 'pinia';

export const useProjectStore = defineStore('project', {
  state: () => ({
    currentProject: null,
    projects: [],
    isLoading: false,
  }),
  actions: {
    initializeFromStorage() {
      this.isLoading = true;
      const savedProjects = localStorage.getItem('projects');
      if (savedProjects) {
        this.projects = JSON.parse(savedProjects);
      }
      const savedCurrentProject = localStorage.getItem('currentProject');
      if (savedCurrentProject) {
        this.currentProject = JSON.parse(savedCurrentProject);
      }
      this.isLoading = false;
    },
    setCurrentProject(project) {
      this.currentProject = project;
      // Save to localStorage
      localStorage.setItem('currentProject', JSON.stringify(project));
    },
    setProjects(projects) {
      this.projects = projects;
      // Save to localStorage
      localStorage.setItem('projects', JSON.stringify(projects));
    },
    loadCurrentProject() {
      this.isLoading = true;
      const saved = localStorage.getItem('currentProject');
      if (saved) {
        this.currentProject = JSON.parse(saved);
      }
      this.isLoading = false;
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
      }
    },
  },
});
