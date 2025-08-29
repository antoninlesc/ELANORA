<template>
  <div class="relative notification-bell">
    <!-- Notification Bell Button -->
    <button
      @click="toggleDropdown"
      class="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-full"
      :class="{ 'text-blue-600': hasUnreadNotifications }"
      :title="unreadCount > 0 ? `${unreadCount} notifications non lues` : 'Notifications'"
    >
      <!-- Bell Icon -->
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
      
      <!-- Unread Count Badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown Panel -->
    <div
      v-if="showDropdown"
      class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50"
      @click.stop
    >
      <!-- Dropdown Header -->
      <div class="px-4 py-3 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900">Notifications</h3>
          <button
            v-if="unreadCount > 0"
            @click="markAllAsRead"
            class="text-sm text-blue-600 hover:text-blue-800 font-medium"
            :disabled="loading"
          >
            Tout marquer comme lu
          </button>
        </div>
        <p class="text-sm text-gray-500 mt-1">
          {{ unreadCount }} non lue{{ unreadCount !== 1 ? 's' : '' }}
        </p>
      </div>

      <!-- Notifications List -->
      <div class="max-h-96 overflow-y-auto">
        <div v-if="loading" class="p-4 text-center">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
          <p class="text-sm text-gray-500 mt-2">Chargement...</p>
        </div>

        <div v-else-if="notifications.length === 0" class="p-4 text-center">
          <p class="text-gray-500">Aucune notification</p>
        </div>

        <div v-else>
          <div
            v-for="notification in notifications.slice(0, 10)"
            :key="notification.notification_id"
            class="px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
            :class="{ 'bg-blue-50': !notification.is_read }"
            @click="handleNotificationClick(notification)"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-medium text-gray-900 truncate">
                  {{ notification.title }}
                </h4>
                <p class="text-sm text-gray-600 mt-1 line-clamp-2">
                  {{ notification.message }}
                </p>
                <p class="text-xs text-gray-400 mt-1">
                  {{ formatDate(notification.created_at) }}
                </p>
              </div>
              
              <!-- Unread indicator -->
              <div v-if="!notification.is_read" class="ml-2 mt-1">
                <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
              </div>
              
              <!-- Actions -->
              <div class="ml-2 flex flex-col space-y-1">
                <button
                  v-if="!notification.is_read"
                  @click.stop="markAsRead(notification.notification_id)"
                  class="text-xs text-blue-600 hover:text-blue-800"
                  title="Marquer comme lu"
                >
                  ✓
                </button>
                <button
                  @click.stop="deleteNotification(notification.notification_id)"
                  class="text-xs text-red-600 hover:text-red-800"
                  title="Supprimer"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Dropdown Footer -->
      <div class="px-4 py-3 border-t border-gray-200">
        <router-link
          to="/profile?tab=notifications"
          class="block text-sm text-blue-600 hover:text-blue-800 font-medium text-center"
          @click="closeDropdown"
        >
          Voir toutes les notifications
        </router-link>
      </div>
    </div>

    <!-- Overlay to close dropdown -->
    <div
      v-if="showDropdown"
      class="fixed inset-0 z-40"
      @click="closeDropdown"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'

const router = useRouter()
const notificationStore = useNotificationStore()

// Local state
const showDropdown = ref(false)

// Computed properties
const notifications = computed(() => notificationStore.notifications)
const unreadCount = computed(() => notificationStore.unreadCount)
const hasUnreadNotifications = computed(() => notificationStore.hasUnreadNotifications)
const loading = computed(() => notificationStore.loading)

// Methods
const toggleDropdown = async () => {
  showDropdown.value = !showDropdown.value
  
  if (showDropdown.value) {
    try {
      // Fetch latest notifications when opening dropdown
      await notificationStore.fetchUnreadNotifications({ limit: 10 })
      await notificationStore.fetchNotificationStats()
    } catch (error) {
      console.error('Failed to fetch notifications for dropdown:', error)
    }
  }
}

const closeDropdown = () => {
  showDropdown.value = false
}

const markAsRead = async (notificationId) => {
  try {
    await notificationStore.markNotificationAsRead(notificationId)
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
  }
}

const markAllAsRead = async () => {
  try {
    await notificationStore.markAllNotificationsAsRead()
  } catch (error) {
    console.error('Failed to mark all notifications as read:', error)
  }
}

const deleteNotification = async (notificationId) => {
  try {
    await notificationStore.deleteNotification(notificationId)
  } catch (error) {
    console.error('Failed to delete notification:', error)
  }
}

const handleNotificationClick = async (notification) => {
  try {
    // Mark as read if not already read
    if (!notification.is_read) {
      await markAsRead(notification.notification_id)
    }
    
    // Navigate to action URL if available
    if (notification.action_url) {
      closeDropdown()
      router.push(notification.action_url)
    }
  } catch (error) {
    console.error('Failed to handle notification click:', error)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return formatDistanceToNow(date, { 
    addSuffix: true, 
    locale: fr 
  })
}

// Lifecycle
onMounted(async () => {
  try {
    // Fetch initial notification stats
    await notificationStore.fetchNotificationStats()
    
    // Set up polling for new notifications every 60 seconds
    const interval = setInterval(async () => {
      try {
        await notificationStore.fetchNotificationStats()
      } catch (error) {
        console.warn('Failed to fetch notification stats in interval:', error)
      }
    }, 60000)
    
    // Store interval ID for cleanup
    window.notificationInterval = interval
  } catch (error) {
    console.error('Failed to initialize notification bell:', error)
  }
})

onUnmounted(() => {
  if (window.notificationInterval) {
    clearInterval(window.notificationInterval)
    delete window.notificationInterval
  }
})

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (showDropdown.value && !event.target.closest('.notification-bell')) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
