import axiosInstance from '@api/apiClient';

const UPLOAD_PREFIX = '/upload';

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

  const response = await axiosInstance.post(
    `${UPLOAD_PREFIX}/process`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

/**
 * Confirm and finalize the upload.
 * @param {string} sessionId - Upload session ID
 * @param {Object} tierAssignments - Tier assignments (tierKey -> assignment)
 * @param {Object} newSectionNames - New section names (sectionName -> displayName)
 * @param {string} description - Upload description
 * @returns {Promise<Object>} - Confirmation response
 */
export const confirmUpload = async (
  sessionId,
  tierAssignments,
  newSectionNames,
  description
) => {
  // Transform tierAssignments object into array format expected by backend
  const assignmentsArray = Object.entries(tierAssignments).map(
    ([tierKey, assignment]) => {
      let section_name = null;
      if (assignment === 'new') {
        // For new sections, use the display name from newSectionNames
        section_name = newSectionNames[tierKey] || tierKey;
      } else if (assignment && assignment !== '') {
        // For existing sections, assignment is the section ID, but backend expects section name
        // For now, we'll pass the section ID and let backend handle it
        section_name = assignment;
      }

      return {
        tier_id: tierKey,
        tier_name: tierKey,
        section_name: section_name,
      };
    }
  );

  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('tier_assignments', JSON.stringify(assignmentsArray));
  formData.append(
    'new_section_names',
    JSON.stringify(Object.values(newSectionNames))
  );
  formData.append('description', description);

  const response = await axiosInstance.post(
    `${UPLOAD_PREFIX}/confirm`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

/**
 * Cancel an upload session.
 * @param {string} sessionId - Upload session ID
 * @returns {Promise<Object>} - Cancellation response
 */
export const cancelUpload = async (sessionId) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);

  const response = await axiosInstance.post(
    `${UPLOAD_PREFIX}/cancel`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
};

export const uploadService = {
  processUploadFiles,
  confirmUpload,
  cancelUpload,
};

export default uploadService;
