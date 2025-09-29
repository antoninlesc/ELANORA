import axiosInstance from '../apiClient';

const NOTIFICATION_PREFIX = '/notification';

/**
 * Get notifications for the current user
 * @param {Object} params - Query parameters
 * @param {number} params.skip - Number of notifications to skip
 * @param {number} params.limit - Maximum number of notifications to return
 * @param {boolean} params.unread_only - If true, only return unread notifications
 * @returns {Promise} Promise that resolves to the notifications
 */
export async function getNotifications(params = {}) {
  const response = await axiosInstance.get(`${NOTIFICATION_PREFIX}/`, {
    params,
  });
  return response.data;
}

/**
 * Get notification statistics for the current user
 * @returns {Promise} Promise that resolves to the notification stats
 */
export async function getNotificationStats() {
  const response = await axiosInstance.get(`${NOTIFICATION_PREFIX}/stats`);
  return response.data;
}

/**
 * Create a new notification
 * @param {Object} notificationData - The notification data
 * @param {number} notificationData.user_id - The ID of the user receiving the notification
 * @param {string} notificationData.title - The title of the notification
 * @param {string} notificationData.message - The message content of the notification
 * @param {string} notificationData.action_url - Optional URL for the notification action
 * @returns {Promise} Promise that resolves to the created notification
 */
export async function createNotification(notificationData) {
  const response = await axiosInstance.post(
    `${NOTIFICATION_PREFIX}/`,
    notificationData
  );
  return response.data;
}

/**
 * Mark a notification as read
 * @param {number} notificationId - The ID of the notification to mark as read
 * @returns {Promise} Promise that resolves to the updated notification
 */
export async function markNotificationAsRead(notificationId) {
  const response = await axiosInstance.put(
    `${NOTIFICATION_PREFIX}/${notificationId}`,
    {
      is_read: true,
    }
  );
  return response.data;
}

/**
 * Delete a notification
 * @param {number} notificationId - The ID of the notification to delete
 * @returns {Promise} Promise that resolves when the notification is deleted
 */
export async function deleteNotification(notificationId) {
  await axiosInstance.delete(`${NOTIFICATION_PREFIX}/${notificationId}`);
}

/**
 * Mark all notifications as read for the current user
 * @returns {Promise} Promise that resolves to the result
 */
export async function markAllNotificationsAsRead() {
  const response = await axiosInstance.post(
    `${NOTIFICATION_PREFIX}/mark-all-read`
  );
  return response.data;
}

/**
 * Get notification preferences for the current user
 * @returns {Promise} Promise that resolves to the notification preferences
 */
export async function getNotificationPreferences() {
  const response = await axiosInstance.get(
    `${NOTIFICATION_PREFIX}/preferences`
  );
  return response.data;
}

/**
 * Update notification preferences for the current user
 * @param {Object} preferences - The notification preferences
 * @param {boolean} preferences.email_enabled - Whether email notifications are enabled
 * @returns {Promise} Promise that resolves to the updated preferences
 */
export async function updateNotificationPreferences(preferences) {
  // Ensure email_enabled is a boolean
  const formattedPreferences = {
    email_enabled: Boolean(preferences.email_enabled),
  };

  try {
    const response = await axiosInstance.put(
      `${NOTIFICATION_PREFIX}/preferences`,
      formattedPreferences
    );
    return response.data;
  } catch (error) {
    console.error('Service: Error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
    });
    throw error;
  }
}

export const notificationService = {
  getNotifications,
  getNotificationStats,
  createNotification,
  markNotificationAsRead,
  deleteNotification,
  markAllNotificationsAsRead,
  getNotificationPreferences,
  updateNotificationPreferences,
};

export default notificationService;
