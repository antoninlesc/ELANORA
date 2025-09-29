import axiosInstance from '@api/apiClient';

const PROJECT_PREFIX = '/project';

/**
 * List all projects for the instance
 * @returns {Promise} Promise that resolves to the list of projects
 */
export async function listProjects() {
  const { data } = await axiosInstance.get(`${PROJECT_PREFIX}`);
  return data;
}

/**
 * List projects accessible to the current user
 * @returns {Promise} Promise that resolves to the list of user projects
 */
export async function listUserProjects() {
  const { data } = await axiosInstance.get(`${PROJECT_PREFIX}/user-projects`);
  return data;
}

/**
 * Create a new project
 * @param {Object} projectData - The project data
 * @returns {Promise} Promise that resolves to the created project
 */
export async function createProject(projectData) {
  const { data } = await axiosInstance.post(
    `${PROJECT_PREFIX}/create`,
    projectData
  );
  return data;
}

/**
 * List files in a project (recursive structure)
 * @param {string} projectName - The name of the project
 * @param {boolean} includeMedia - Whether to include media files
 * @returns {Promise} Promise that resolves to the project files
 */
export async function listProjectFiles(projectName, includeMedia = false) {
  const params = includeMedia ? { include_media: true } : {};
  const { data } = await axiosInstance.get(
    `${PROJECT_PREFIX}/${encodeURIComponent(projectName)}/files`,
    { params }
  );
  return data;
}

/**
 * Initialize a project from an existing folder with upload
 * @param {Object} params - The upload parameters
 * @param {string} params.project_name - The project name
 * @param {string} params.description - The project description
 * @param {File[]} params.files - The files to upload
 * @returns {Promise} Promise that resolves to the upload result
 */
export async function initProjectFromFolderUpload({
  project_name,
  description,
  files,
}) {
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
    `${PROJECT_PREFIX}/init-from-folder-upload`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return data;
}

/**
 * Delete a project
 * @param {string} projectName - The name of the project to delete
 * @returns {Promise} Promise that resolves to the deletion result
 */
export async function deleteProject(projectName) {
  const { data } = await axiosInstance.delete(
    `${PROJECT_PREFIX}/${encodeURIComponent(projectName)}`
  );
  return data;
}

/**
 * Edit a project
 * @param {string} oldProjectName - The current project name
 * @param {string} newProjectName - The new project name
 * @param {string} newProjectDescription - The new project description
 * @returns {Promise} Promise that resolves to the updated project
 */
export async function editProject(
  oldProjectName,
  newProjectName,
  newProjectDescription
) {
  const { data } = await axiosInstance.post(
    `${PROJECT_PREFIX}/${encodeURIComponent(oldProjectName)}/edit`,
    {
      new_project_name: newProjectName,
      new_project_description: newProjectDescription,
    }
  );
  return data;
}

/**
 * Get project users
 * @param {number} projectId - The project ID
 * @returns {Promise} Promise that resolves to the project users
 */
export async function getProjectUsers(projectId) {
  const response = await axiosInstance.get(
    `${PROJECT_PREFIX}/${projectId}/users`
  );
  return response;
}

/**
 * Add a user to a project
 * @param {number} projectId - The project ID
 * @param {Object} userData - The user data
 * @returns {Promise} Promise that resolves to the result
 */
export async function addUserToProject(projectId, userData) {
  const response = await axiosInstance.post(
    `${PROJECT_PREFIX}/${projectId}/users`,
    userData
  );
  return response;
}

/**
 * Update user permission in a project
 * @param {number} projectId - The project ID
 * @param {number} userId - The user ID
 * @param {Object} permissionData - The permission data
 * @returns {Promise} Promise that resolves to the result
 */
export async function updateUserPermission(projectId, userId, permissionData) {
  const response = await axiosInstance.put(
    `${PROJECT_PREFIX}/${projectId}/users/${userId}`,
    permissionData
  );
  return response;
}

/**
 * Remove a user from a project
 * @param {number} projectId - The project ID
 * @param {number} userId - The user ID
 * @returns {Promise} Promise that resolves to the result
 */
export async function removeUserFromProject(projectId, userId) {
  const response = await axiosInstance.delete(
    `${PROJECT_PREFIX}/${projectId}/users/${userId}`
  );
  return response;
}

/**
 * Get project files with media
 * @param {number} projectId - The project ID
 * @returns {Promise} Promise that resolves to the project files with media
 */
export async function getProjectFilesWithMedia(projectId) {
  const { data } = await axiosInstance.get(
    `${PROJECT_PREFIX}/${projectId}/files-with-media`
  );
  return data;
}

export const projectService = {
  listProjects,
  listUserProjects,
  createProject,
  listProjectFiles,
  initProjectFromFolderUpload,
  deleteProject,
  editProject,
  getProjectUsers,
  addUserToProject,
  updateUserPermission,
  removeUserFromProject,
  getProjectFilesWithMedia,
};

export default projectService;
