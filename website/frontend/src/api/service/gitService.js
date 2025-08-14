import axiosInstance from '@/api/apiClient';

const GIT_PREFIX = '/git';
const gitService = {
  // Check if Git is available
  async checkGit() {
    const { data } = await axiosInstance.get(`${GIT_PREFIX}/check`);
    return data;
  },
  // List all projects for the instance
  async listProjects() {
    const { data } = await axiosInstance.get(`${GIT_PREFIX}/projects`);
    return data;
  },

  // List projects accessible to the current user
  async listUserProjects() {
    const { data } = await axiosInstance.get(`${GIT_PREFIX}/user-projects`);
    return data;
  },

  // Create a new project
  async createProject(projectData) {
    const { data } = await axiosInstance.post(
      `${GIT_PREFIX}/projects/create`,
      projectData
    );
    return data;
  },

  // Commit changes to a project
  async commitChanges(projectName, commitMessage, userName) {
    const payload = {
      commit_message: commitMessage,
      user_name: userName,
    };
    const { data } = await axiosInstance.post(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/commit`,
      payload
    );
    return data;
  },

  // Upload ELAN files to a project
  async uploadElanFiles(projectName, files, userName = 'user') {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('user_name', userName);

    const { data } = await axiosInstance.post(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },

  // Get all branches for a project
  async getBranches(projectName) {
    const { data } = await axiosInstance.get(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/branches`
    );
    return data;
  },

  // Resolve conflicts and merge a branch
  async resolveConflicts(
    projectName,
    branchName,
    resolutionStrategy = 'accept_incoming'
  ) {
    const params = new URLSearchParams({
      branch_name: branchName,
      resolution_strategy: resolutionStrategy,
    });
    const { data } = await axiosInstance.post(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/resolve-conflicts?${params.toString()}`
    );
    return data;
  },

  // List files in a project (recursive structure)
  async listProjectFiles(projectName) {
    const { data } = await axiosInstance.get(
      `/git/projects/${encodeURIComponent(projectName)}/files`
    );
    return data;
  },

  // Initialize a project from an existing folder with upload
  async initProjectFromFolderUpload({ project_name, description, files }) {
    const formData = new FormData();
    formData.append('project_name', project_name);
    formData.append('description', description);
    files.forEach((file) => {
      // webkitRelativePath preserves folder structure
      formData.append('files', file, file.webkitRelativePath);
    });
    const { data } = await axiosInstance.post(
      `/git/projects/init-from-folder-upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  // Synchronize the project (apply changes to DB)
  async synchronizeProject(projectName) {
    const { data } = await axiosInstance.post(
      `/git/projects/${encodeURIComponent(projectName)}/synchronize`
    );
    return data;
  },

  // Check if the project is in sync (preview changes)
  async checkSyncStatus(projectName) {
    const { data } = await axiosInstance.get(
      `/git/projects/${encodeURIComponent(projectName)}/synchronize/check`
    );
    return data;
  },

  // Delete a project
  async deleteProject(projectName) {
    const { data } = await axiosInstance.delete(
      `/git/projects/${encodeURIComponent(projectName)}`
    );
    return data;
  },

  // Edit a project
  async editProject(oldProjectName, newProjectName, newProjectDescription) {
    const { data } = await axiosInstance.post(
      `/git/projects/${encodeURIComponent(oldProjectName)}/edit`,
      {
        new_project_name: newProjectName,
        new_project_description: newProjectDescription,
      }
    );
    return data;
  },

  // Discard all local changes and reset to remote master
  async discardLocalChanges(projectName) {
    const { data } = await axiosInstance.post(
      `/git/projects/${encodeURIComponent(projectName)}/discard-local-changes`
    );
    return data;
  },

  // Restore the project from backup
  async restoreFromBackup(projectName) {
    const { data } = await axiosInstance.post(
      `/git/projects/${encodeURIComponent(projectName)}/restore-from-backup`
    );
    return data;
  },

  // Decline the backup for a project
  async declineBackup(projectName) {
    const { data } = await axiosInstance.post(
      `/git/projects/${encodeURIComponent(projectName)}/decline-backup`
    );
    return data;
  },
};

export default gitService;
