import axiosInstance from '@api/apiClient.js';

const PROJECT_STANDARD_PREFIX = '/project-standard';

/**
 * Get standards by project
 * @param {number} projectId - The project ID
 * @returns {Promise} Promise that resolves to the project standards
 */
export async function getStandardsByProject(projectId) {
  return axiosInstance.get(`${PROJECT_STANDARD_PREFIX}/project/${projectId}`);
}

/**
 * Get standard with components
 * @param {number} standardId - The standard ID
 * @returns {Promise} Promise that resolves to the standard with components
 */
export async function getStandardWithComponents(standardId) {
  return axiosInstance.get(`${PROJECT_STANDARD_PREFIX}/${standardId}`);
}

/**
 * Create standard with components
 * @param {Object} payload - The standard creation payload
 * @returns {Promise} Promise that resolves to the created standard
 */
export async function createStandardWithComponents(payload) {
  return axiosInstance.post(`${PROJECT_STANDARD_PREFIX}/create`, payload);
}

/**
 * Delete a standard
 * @param {number} standardId - The standard ID
 * @returns {Promise} Promise that resolves when the standard is deleted
 */
export async function deleteStandard(standardId) {
  return axiosInstance.delete(`${PROJECT_STANDARD_PREFIX}/${standardId}`);
}

/**
 * Get component names for a project
 * @param {number} projectId - The project ID
 * @returns {Promise} Promise that resolves to the component names
 */
export async function getComponentNames(projectId) {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/component-names`
  );
}

/**
 * Get project naming standards full
 * @param {number} projectId - The project ID
 * @returns {Promise} Promise that resolves to the full naming standards
 */
export async function getProjectNamingStandardsFull(projectId) {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/full`
  );
}

/**
 * Get projects with standards
 * @returns {Promise} Promise that resolves to projects with standards
 */
export async function getProjectsWithStandards() {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/projects-with-standards`
  );
}

/**
 * Import selected standards
 * @param {Object} payload - The import payload
 * @returns {Promise} Promise that resolves to the import result
 */
export async function importSelectedStandards(payload) {
  return axiosInstance.post(`${PROJECT_STANDARD_PREFIX}/import`, payload);
}

/**
 * Get file types for location
 * @param {number} projectId - The project ID
 * @param {number} locationId - The location ID
 * @returns {Promise} Promise that resolves to the file types
 */
export async function getFileTypesForLocation(projectId, locationId) {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/location/${locationId}/filetypes`
  );
}

/**
 * Add file type to location
 * @param {number} projectId - The project ID
 * @param {number} locationId - The location ID
 * @param {number} fileTypeId - The file type ID
 * @returns {Promise} Promise that resolves to the result
 */
export async function addFileTypeToLocation(projectId, locationId, fileTypeId) {
  return axiosInstance.post(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/location/${locationId}/filetype/${fileTypeId}/add`
  );
}

/**
 * Remove file type from location
 * @param {number} projectId - The project ID
 * @param {number} locationId - The location ID
 * @param {number} fileTypeId - The file type ID
 * @returns {Promise} Promise that resolves to the result
 */
export async function removeFileTypeFromLocation(
  projectId,
  locationId,
  fileTypeId
) {
  return axiosInstance.delete(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/location/${locationId}/filetype/${fileTypeId}/remove`
  );
}

/**
 * Get effective standards locations
 * @returns {Promise} Promise that resolves to the locations
 */
export async function getEffectiveStandardsLocations() {
  return axiosInstance.get(`${PROJECT_STANDARD_PREFIX}/locations`);
}

/**
 * Get effective standards
 * @param {number} projectId - The project ID
 * @param {number} locationId - The location ID
 * @returns {Promise} Promise that resolves to the effective standards
 */
export async function getEffectiveStandards(projectId, locationId) {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/location/${locationId}/effective-standards`
  );
}

/**
 * Assign effective standard
 * @param {number} projectId - The project ID
 * @param {number} projectFileTypeId - The project file type ID
 * @param {number} namingStandardId - The naming standard ID
 * @param {number} locationId - The location ID
 * @returns {Promise} Promise that resolves to the assignment result
 */
export async function assignEffectiveStandard(
  projectId,
  projectFileTypeId,
  namingStandardId,
  locationId
) {
  return axiosInstance.post(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/filetype/${projectFileTypeId}/assign`,
    { naming_standard_id: namingStandardId, location_id: locationId }
  );
}

/**
 * Unassign effective standard
 * @param {number} projectId - The project ID
 * @param {number} projectFileTypeId - The project file type ID
 * @param {number} locationId - The location ID
 * @returns {Promise} Promise that resolves to the unassignment result
 */
export async function unassignEffectiveStandard(
  projectId,
  projectFileTypeId,
  locationId
) {
  return axiosInstance.delete(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/filetype/${projectFileTypeId}/location/${locationId}/unassign`
  );
}

/**
 * Add project file type
 * @param {number} projectId - The project ID
 * @param {Object} payload - The file type payload
 * @returns {Promise} Promise that resolves to the added file type
 */
export async function addProjectFileType(projectId, payload) {
  return axiosInstance.post(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/file_types/add`,
    payload
  );
}

/**
 * Get project file types
 * @param {number} projectId - The project ID
 * @returns {Promise} Promise that resolves to the project file types
 */
export async function getProjectFileTypes(projectId) {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/file_types`
  );
}

/**
 * Delete project file type
 * @param {number} projectId - The project ID
 * @param {number} fileTypeId - The file type ID
 * @returns {Promise} Promise that resolves to the deletion result
 */
export async function deleteProjectFileType(projectId, fileTypeId) {
  return axiosInstance.delete(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/file_type/${fileTypeId}`
  );
}

/**
 * Import preview
 * @param {number} sourceProjectId - The source project ID
 * @param {number} targetProjectId - The target project ID
 * @returns {Promise} Promise that resolves to the import preview
 */
export async function importPreview(sourceProjectId, targetProjectId) {
  return axiosInstance.get(
    `${PROJECT_STANDARD_PREFIX}/file_types/import_preview/`,
    {
      params: {
        source_project_id: sourceProjectId,
        target_project_id: targetProjectId,
      },
    }
  );
}

/**
 * Import selected
 * @param {number} sourceProjectId - The source project ID
 * @param {number} targetProjectId - The target project ID
 * @param {Array} fileTypeNames - The file type names
 * @returns {Promise} Promise that resolves to the import result
 */
export async function importSelected(
  sourceProjectId,
  targetProjectId,
  fileTypeNames
) {
  return axiosInstance.post(
    `${PROJECT_STANDARD_PREFIX}/file_types/import_selected/?source_project_id=${sourceProjectId}&target_project_id=${targetProjectId}`,
    { file_type_names: fileTypeNames }
  );
}

/**
 * Update project file type
 * @param {number} projectId - The project ID
 * @param {number} fileTypeId - The file type ID
 * @param {Object} payload - The update payload
 * @returns {Promise} Promise that resolves to the updated file type
 */
export async function updateProjectFileType(projectId, fileTypeId, payload) {
  return axiosInstance.put(
    `${PROJECT_STANDARD_PREFIX}/project/${projectId}/file_type/${fileTypeId}`,
    payload
  );
}

export const projectStandardService = {
  getStandardsByProject,
  getStandardWithComponents,
  createStandardWithComponents,
  deleteStandard,
  getComponentNames,
  getProjectNamingStandardsFull,
  getProjectsWithStandards,
  importSelectedStandards,
  getFileTypesForLocation,
  addFileTypeToLocation,
  removeFileTypeFromLocation,
  getEffectiveStandardsLocations,
  getEffectiveStandards,
  assignEffectiveStandard,
  unassignEffectiveStandard,
  addProjectFileType,
  getProjectFileTypes,
  deleteProjectFileType,
  importPreview,
  importSelected,
  updateProjectFileType,
};

export default projectStandardService;
