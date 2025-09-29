import axiosInstance from '@api/apiClient';

const GIT_PREFIX = '/git';

/**
 * Check if Git is available
 * @returns {Promise} Promise that resolves to Git availability status
 */
export async function checkGit() {
  const { data } = await axiosInstance.get(`${GIT_PREFIX}/check`);
  return data;
}

/**
 * Synchronize the project (apply changes to DB)
 * @param {string} projectName - The project name
 * @returns {Promise} Promise that resolves to the synchronization result
 */
export async function synchronizeProject(projectName) {
  const { data } = await axiosInstance.post(
    `/git/projects/${encodeURIComponent(projectName)}/synchronize`
  );
  return data;
}

/**
 * Check if the project is in sync (preview changes)
 * @param {string} projectName - The project name
 * @returns {Promise} Promise that resolves to the sync status
 */
export async function checkSyncStatus(projectName) {
  const { data } = await axiosInstance.get(
    `/git/projects/${encodeURIComponent(projectName)}/synchronize/check`
  );
  return data;
}

/**
 * Discard all local changes and reset to remote master
 * @param {string} projectName - The project name
 * @returns {Promise} Promise that resolves to the discard result
 */
export async function discardLocalChanges(projectName) {
  const { data } = await axiosInstance.post(
    `/git/projects/${encodeURIComponent(projectName)}/discard-local-changes`
  );
  return data;
}

/**
 * Restore the project from backup
 * @param {string} projectName - The project name
 * @returns {Promise} Promise that resolves to the restore result
 */
export async function restoreFromBackup(projectName) {
  const { data } = await axiosInstance.post(
    `/git/projects/${encodeURIComponent(projectName)}/restore-from-backup`
  );
  return data;
}

/**
 * Decline the backup for a project
 * @param {string} projectName - The project name
 * @returns {Promise} Promise that resolves to the decline result
 */
export async function declineBackup(projectName) {
  const { data } = await axiosInstance.post(
    `/git/projects/${encodeURIComponent(projectName)}/decline-backup`
  );
  return data;
}

/**
 * Rename a single file
 * @param {string} projectName - The project name
 * @param {string} elanId - The ELAN ID
 * @param {string} newFilename - The new filename
 * @returns {Promise} Promise that resolves to the rename result
 */
export async function renameFile(projectName, elanId, newFilename) {
  const formData = new FormData();
  formData.append('elan_id', elanId);
  formData.append('new_filename', newFilename);

  const response = await axiosInstance.post(
    `${GIT_PREFIX}/projects/${projectName}/rename-file`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

/**
 * Rename multiple files
 * @param {string} projectName - The project name
 * @param {Array} renames - Array of rename objects
 * @returns {Promise} Promise that resolves to the rename result
 */
export async function renameFiles(projectName, renames) {
  const response = await axiosInstance.post(
    `${GIT_PREFIX}/projects/${projectName}/rename-files`,
    {
      renames: renames,
    }
  );
  return response.data;
}

/**
 * Download selected files as a ZIP
 * @param {string} projectName - The project name
 * @param {Array} selectedFiles - Array of selected files
 * @returns {Promise} Promise that resolves when download is initiated
 */
export async function downloadFiles(projectName, selectedFiles) {
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
}

export const gitService = {
  checkGit,
  synchronizeProject,
  checkSyncStatus,
  discardLocalChanges,
  restoreFromBackup,
  declineBackup,
  renameFile,
  renameFiles,
  downloadFiles,
};

export default gitService;
