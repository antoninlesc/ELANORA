/**
 * projectService.js
 *
 * Provides project-related API calls.
 */

import axiosInstance from '@api/apiClient.js';

/**
 * Get all projects.
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getProjects() {
  return await axiosInstance.get('/project/list');
}

/**
 * Get a specific project by ID.
 * @param {number} projectId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getProject(projectId) {
  return await axiosInstance.get(`/project/details/${projectId}`);
}