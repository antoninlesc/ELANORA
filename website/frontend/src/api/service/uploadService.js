/**
 * uploadService.js
 *
 * Service for handling upload-related API calls.
 */

import apiClient from '@/api/apiClient';

/**
 * Process uploaded files for tier extraction.
 * @param {File[]} files - Array of files to process
 * @param {string} projectId - Project ID
 * @returns {Promise<Object>} - Response with sessionId and extractedTiers
 */
export const processUploadFiles = async (files, projectId) => {
  const formData = new FormData();

  // Add files to form data
  files.forEach((file) => {
    formData.append(`files`, file);
  });

  // Add project ID
  formData.append('project_id', projectId);

  const response = await apiClient.post('/upload/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Confirm and finalize the upload.
 * @param {string} sessionId - Upload session ID
 * @param {Object} tierAssignments - Tier assignments
 * @param {string} description - Upload description
 * @returns {Promise<Object>} - Confirmation response
 */
export const confirmUpload = async (
  sessionId,
  tierAssignments,
  description
) => {
  const response = await apiClient.post('/upload/confirm', {
    session_id: sessionId,
    tier_assignments: tierAssignments,
    description: description,
  });

  return response.data;
};
