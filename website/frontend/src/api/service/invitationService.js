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
 * @param {number} invitationData.project_id
 * @param {string} invitationData.message
 * @param {number} invitationData.expires_in_days
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function sendInvitation(invitationData) {
  return await axiosInstance.post('/invitation/send', invitationData);
}

/**
 * Validate an invitation code.
 * @param {string} invitationId
 * @returns {Promise<import('axios').AxiosResponse>}
 */
export async function validateInvitation(invitationId) {
  return await axiosInstance.get(`/invitation/validate/${invitationId}`);
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
