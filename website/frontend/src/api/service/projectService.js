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
  return await axiosInstance.get('/project');
}

/**
 * Get a specific project by ID.
 * @param {number} projectId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getProject(projectId) {
  return await axiosInstance.get(`/project/${projectId}`);
}

/**
 * Create a new project.
 * @param {Object} projectData
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function createProject(projectData) {
  return await axiosInstance.post('/project', projectData);
}

/**
 * Update a project.
 * @param {number} projectId
 * @param {Object} projectData
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function updateProject(projectId, projectData) {
  return await axiosInstance.put(`/project/${projectId}`, projectData);
}

/**
 * Delete a project.
 * @param {number} projectId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function deleteProject(projectId) {
  return await axiosInstance.delete(`/project/${projectId}`);
}
