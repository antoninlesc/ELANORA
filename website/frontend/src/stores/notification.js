import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {
  getNotifications,
  getNotificationStats,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  deleteNotification,
  getNotificationPreferences,
  updateNotificationPreferences,
} from '@api/service/notificationService.js';

export const useNotificationStore = defineStore('notification', () => {
  // State
  const notifications = ref([]);
  const stats = ref({
    total_notifications: 0,
    unread_notifications: 0,
    read_notifications: 0,
  });
  const preferences = ref({
    email_enabled: true,
  });
  const loading = ref(false);
  const error = ref(null);

  // Getters
  const unreadNotifications = computed(() =>
    notifications.value.filter((notification) => !notification.is_read)
  );

  const unreadCount = computed(() => stats.value.unread_notifications || 0);

  const hasUnreadNotifications = computed(() => unreadCount.value > 0);

  // Actions
  const fetchNotifications = async (params = {}) => {
    loading.value = true;
    error.value = null;
    try {
      const data = await getNotifications(params);
      notifications.value = data;
    } catch (err) {
      error.value = err.message || 'Failed to fetch notifications';
      console.error('Error fetching notifications:', err);
    } finally {
      loading.value = false;
    }
  };

  const fetchUnreadNotifications = async (params = {}) => {
    loading.value = true;
    error.value = null;
    try {
      const data = await getNotifications({
        ...params,
        unread_only: true,
      });
      // Update existing notifications with unread ones
      const existingIds = new Set(
        notifications.value.map((n) => n.notification_id)
      );
      const newNotifications = data.filter(
        (n) => !existingIds.has(n.notification_id)
      );
      notifications.value = [...notifications.value, ...newNotifications];
    } catch (err) {
      error.value = err.message || 'Failed to fetch unread notifications';
      console.error('Error fetching unread notifications:', err);
    } finally {
      loading.value = false;
    }
  };

  const fetchNotificationStats = async () => {
    try {
      const data = await getNotificationStats();
      stats.value = data;
    } catch (err) {
      error.value = err.message || 'Failed to fetch notification stats';
      console.error('Error fetching notification stats:', err);
    }
  };

  const handleMarkNotificationAsRead = async (notificationId) => {
    try {
      const updatedNotification = await markNotificationAsRead(notificationId);
      const index = notifications.value.findIndex(
        (n) => n.notification_id === notificationId
      );
      if (index !== -1) {
        notifications.value[index] = updatedNotification;
      }
      // Update stats
      await fetchNotificationStats();
    } catch (err) {
      error.value = err.message || 'Failed to mark notification as read';
      console.error('Error marking notification as read:', err);
    }
  };

  const handleMarkAllNotificationsAsRead = async () => {
    try {
      await markAllNotificationsAsRead();
      // Mark all notifications as read in the store
      notifications.value.forEach((notification) => {
        notification.is_read = true;
      });
      // Update stats
      await fetchNotificationStats();
    } catch (err) {
      error.value = err.message || 'Failed to mark all notifications as read';
      console.error('Error marking all notifications as read:', err);
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      await deleteNotification(notificationId);
      notifications.value = notifications.value.filter(
        (n) => n.notification_id !== notificationId
      );
      // Update stats
      await fetchNotificationStats();
    } catch (err) {
      error.value = err.message || 'Failed to delete notification';
      console.error('Error deleting notification:', err);
    }
  };

  const fetchNotificationPreferences = async () => {
    try {
      const data = await getNotificationPreferences();
      preferences.value = data;
    } catch (err) {
      error.value = err.message || 'Failed to fetch notification preferences';
      console.error('Error fetching notification preferences:', err);
    }
  };

  const handleUpdateNotificationPreferences = async (newPreferences) => {
    try {
      const data = await updateNotificationPreferences(newPreferences);
      preferences.value = data;
      error.value = null; // Clear any previous errors
    } catch (err) {
      error.value = err.message || 'Failed to update notification preferences';
      console.error('Error updating notification preferences:', err);
      throw err;
    }
  };

  const addNotification = (notification) => {
    // Add a new notification to the beginning of the list
    notifications.value.unshift(notification);
    // Update stats (increment unread count)
    stats.value.unread_notifications += 1;
    stats.value.total_notifications += 1;
  };

  const clearError = () => {
    error.value = null;
  };

  const clearNotifications = () => {
    notifications.value = [];
    stats.value = {
      total_notifications: 0,
      unread_notifications: 0,
      read_notifications: 0,
    };
  };

  return {
    // State
    notifications,
    stats,
    preferences,
    loading,
    error,

    // Getters
    unreadNotifications,
    unreadCount,
    hasUnreadNotifications,

    // Actions
    fetchNotifications,
    fetchUnreadNotifications,
    fetchNotificationStats,
    markNotificationAsRead: handleMarkNotificationAsRead,
    markAllNotificationsAsRead: handleMarkAllNotificationsAsRead,
    deleteNotification: handleDeleteNotification,
    fetchNotificationPreferences,
    updateNotificationPreferences: handleUpdateNotificationPreferences,
    addNotification,
    clearError,
    clearNotifications,
  };
});
