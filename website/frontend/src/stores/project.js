import { defineStore } from 'pinia';

export const useProjectStore = defineStore('project', {
  state: () => ({
    currentProject: null,
    projects: [],
    isLoading: false,
  }),

  getters: {
    projectId: (state) => state.currentProject?.project_id ?? null,
    projectName: (state) => state.currentProject?.project_name ?? '',
    projectDescription: (state) =>
      state.currentProject?.project_description ?? '',
    projectList: (state) => state.projects ?? [],
  },

  actions: {
    sortProjects() {
      this.projects = this.projects.slice().sort((a, b) =>
        a.project_name.localeCompare(b.project_name)
      );
    },
    initializeFromStorage() {
      this.isLoading = true;
      const savedProjects = localStorage.getItem('projects');
      if (savedProjects) {
        this.projects = JSON.parse(savedProjects);
        this.sortProjects();
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
      this.projects = projects.slice();
      this.sortProjects();
      localStorage.setItem('projects', JSON.stringify(this.projects));
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
  },
});
