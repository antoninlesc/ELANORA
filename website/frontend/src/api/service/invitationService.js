/**
 * invitationService.js
 *
 * Provides invitation-related API calls.
 */

import axiosInstance from '@api/apiClient.js';

/**
 * Send an invitation to a specific project by email.
 * @param {Object} invitationData
 * @param {string} invitationData.receiver_email
 * @param {string} invitationData.project_name
 * @param {string} invitationData.message
 * @param {number} invitationData.expires_in_days
 * @param {string} invitationData.project_permission
 * @param {string} invitationData.language
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function sendInvitation(invitationData) {
  return await axiosInstance.post('/invitation/send', invitationData);
}

/**
 * Validate an invitation code.
 * @param {string} invitationCode
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function validateInvitation(invitationCode) {
  return await axiosInstance.get(`/invitation/validate/${invitationCode}`);
}

/**
 * Get invitations sent by the current admin user.
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getSentInvitations() {
  return await axiosInstance.get('/invitation/sent');
}

/**
 * Get invitations for a specific project.
 * @param {string} projectName
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getProjectInvitations(projectName) {
  return await axiosInstance.get(`/invitation/project/${encodeURIComponent(projectName)}`);
}

/**
 * Get invitations received by email.
 * @param {string} email
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getReceivedInvitations(email) {
  return await axiosInstance.get(`/invitation/received/${email}`);
}

/**
 * Accept an invitation (for existing users).
 * @param {number} invitationId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function acceptInvitation(invitationId) {
  return await axiosInstance.post(`/invitation/accept/${invitationId}`);
}

/**
 * Reject an invitation (for existing users).
 * @param {number} invitationId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function rejectInvitation(invitationId) {
  return await axiosInstance.post(`/invitation/reject/${invitationId}`);
}

/**
 * Resend an invitation.
 * @param {number} invitationId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function resendInvitation(invitationId) {
  // TODO: Implement endpoint in backend
  throw new Error('Resend invitation functionality not yet implemented in backend');
}

/**
 * Cancel an invitation.
 * @param {number} invitationId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function cancelInvitation(invitationId) {
  // TODO: Implement endpoint in backend
  throw new Error('Cancel invitation functionality not yet implemented in backend');
}
