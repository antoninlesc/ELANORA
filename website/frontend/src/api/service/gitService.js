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

  // Get all branches for a project
  async getBranches(projectName) {
    const { data } = await axiosInstance.get(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/branches`
    );
    return data;
  },

  // List files in a project (recursive structure)
  async listProjectFiles(projectName, includeMedia = false) {
    const params = includeMedia ? { include_media: true } : {};
    const { data } = await axiosInstance.get(
      `/git/projects/${encodeURIComponent(projectName)}/files`,
      { params }
    );
    return data;
  },

  // Initialize a project from an existing folder with upload
  async initProjectFromFolderUpload({ project_name, description, files }) {
    const formData = new FormData();
    formData.append('project_name', project_name);
    formData.append(
      'description',
      !description || description === 'undefined' ? '' : description
    );

    files.forEach((file) => {
      formData.append('files', file, file.name);
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
  // Get detailed conflict information for a file
  async getConflictDetails(projectName, branchName, filename) {
    const { data } = await axiosInstance.get(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/branches/${encodeURIComponent(branchName)}/conflicts/${encodeURIComponent(filename)}/details`
    );
    return data;
  },

  // Rename a single file
  async renameFile(projectName, elanId, newFilename) {
    console.log('GitService renameFile called with:', {
      projectName,
      elanId,
      newFilename,
    });

    const formData = new FormData();
    formData.append('elan_id', elanId);
    formData.append('new_filename', newFilename);

    console.log('FormData entries:', Array.from(formData.entries()));

    const response = await axiosInstance.post(
      `${GIT_PREFIX}/projects/${projectName}/rename-file`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    console.log('Rename response:', response.data);
    return response.data;
  },

  // Rename multiple files
  async renameFiles(projectName, renames) {
    const response = await axiosInstance.post(
      `${GIT_PREFIX}/projects/${projectName}/rename-files`,
      {
        renames: renames,
      }
    );
    return response.data;
  },

  // Download selected files as a ZIP
  async downloadFiles(projectName, selectedFiles) {
    const elanIds = selectedFiles.map((f) => f.elan_id);
    const response = await axiosInstance.post(
      `${GIT_PREFIX}/projects/${encodeURIComponent(projectName)}/download`,
      { elan_ids: elanIds },
      { responseType: 'blob' }
    );

    // Trigger download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${projectName}_files.zip`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};

export default gitService;
