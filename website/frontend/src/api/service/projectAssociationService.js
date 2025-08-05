/**
 * Service for managing project-user associations
 */
import axiosInstance from '@/api/apiClient';

/**
 * Get all users associated with a project
 * @param {string} projectName - The project name
 * @returns {Promise} API response with project users
 */
export const getProjectUsers = async (projectName) => {
  try {
    const response = await axiosInstance.get(`/project-associations/projects/${projectName}/users`);
    return response;
  } catch (error) {
    console.error('Error fetching project users:', error);
    throw error;
  }
};

/**
 * Add a user to a project with specified permission
 * @param {string} projectName - The project name
 * @param {Object} userData - User data with user_id and permission
 * @returns {Promise} API response
 */
export const addUserToProject = async (projectName, userData) => {
  try {
    const response = await axiosInstance.post(`/project-associations/projects/${projectName}/users`, userData);
    return response;
  } catch (error) {
    console.error('Error adding user to project:', error);
    throw error;
  }
};

/**
 * Update a user's permission in a project
 * @param {string} projectName - The project name
 * @param {number} userId - The user ID
 * @param {Object} permissionData - Object with permission field
 * @returns {Promise} API response
 */
export const updateUserPermission = async (projectName, userId, permissionData) => {
  try {
    const response = await axiosInstance.put(`/project-associations/projects/${projectName}/users/${userId}`, permissionData);
    return response;
  } catch (error) {
    console.error('Error updating user permission:', error);
    throw error;
  }
};

/**
 * Remove a user from a project
 * @param {string} projectName - The project name
 * @param {number} userId - The user ID
 * @returns {Promise} API response
 */
export const removeUserFromProject = async (projectName, userId) => {
  try {
    const response = await axiosInstance.delete(`/project-associations/projects/${projectName}/users/${userId}`);
    return response;
  } catch (error) {
    console.error('Error removing user from project:', error);
    throw error;
  }
};
