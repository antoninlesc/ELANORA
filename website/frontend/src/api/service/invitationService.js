/**
 * invitationService.js
 *
 * Provides invitation-related API calls.
 */

import axiosInstance from '@api/apiClient.js';

/**
 * Send an invitation to a specific project.
 * @param {Object} invitationData
 * @param {string} invitationData.receiver_email
 * @param {string} invitationData.project_name
 * @param {string} invitationData.message
 * @param {number} invitationData.expires_in_days
 * @param {string} invitationData.project_permission
 * @param {string} invitationData.language
 * @param {boolean} invitationData.send_email
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function sendInvitation(invitationData) {
  return await axiosInstance.post('/invitation/send', invitationData);
}

/**
 * Generate an invitation code without sending email.
 * @param {Object} invitationData
 * @param {string} invitationData.project_name
 * @param {string} invitationData.project_permission
 * @param {number} invitationData.expires_in_days
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function generateInvitationCode(invitationData) {
  return await axiosInstance.post('/invitation/generate-code', invitationData);
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
 * Get invitations received by email.
 * @param {string} email
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function getReceivedInvitations(email) {
  return await axiosInstance.get(`/invitation/received/${email}`);
}
