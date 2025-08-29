<template>
  <div class="space-y-6">
    <!-- Header with actions -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Notifications</h2>
        <p class="mt-1 text-sm text-gray-500">
          Gérez vos notifications et préférences
        </p>
      </div>
      <div class="mt-4 sm:mt-0 flex space-x-3">
        <button
          v-if="unreadCount > 0"
          @click="markAllAsRead"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          :disabled="loading"
        >
          <template v-if="loading">
            <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Chargement...
          </template>
          <template v-else>
            Tout marquer comme lu
          </template>
        </button>
        <button
          @click="refreshNotifications"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          :disabled="loading"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Actualiser
        </button>
      </div>
    </div>

    <!-- Notification Statistics -->
    <div class="bg-white overflow-hidden shadow rounded-lg">
      <div class="p-5">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <svg class="h-8 w-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <div class="ml-5 w-0 flex-1">
            <dl class="grid grid-cols-1 gap-x-4 gap-y-2 sm:grid-cols-3">
              <div>
                <dt class="text-sm font-medium text-gray-500 truncate">Total</dt>
                <dd class="text-lg font-semibold text-gray-900">{{ stats.total_notifications }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 truncate">Non lues</dt>
                <dd class="text-lg font-semibold text-red-600">{{ stats.unread_notifications }}</dd>
              </div>
              <div>
                <dt class="text-sm font-medium text-gray-500 truncate">Lues</dt>
                <dd class="text-lg font-semibold text-green-600">{{ stats.read_notifications }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="border-b border-gray-200">
      <nav class="-mb-px flex space-x-8">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          @click="currentFilter = tab.key"
          class="py-2 px-1 border-b-2 font-medium text-sm"
          :class="currentFilter === tab.key 
            ? 'border-blue-500 text-blue-600' 
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
        >
          {{ tab.label }}
          <span 
            v-if="tab.count !== undefined" 
            class="ml-2 py-0.5 px-2 rounded-full text-xs"
            :class="currentFilter === tab.key 
              ? 'bg-blue-100 text-blue-600' 
              : 'bg-gray-100 text-gray-600'"
          >
            {{ tab.count }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Notifications List -->
    <div class="space-y-4">
      <div v-if="loading && notifications.length === 0" class="text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-sm text-gray-500 mt-2">Chargement des notifications...</p>
      </div>

      <div v-else-if="filteredNotifications.length === 0" class="text-center py-8">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Aucune notification</h3>
        <p class="mt-1 text-sm text-gray-500">
          {{ currentFilter === 'unread' ? 'Vous n\'avez aucune notification non lue.' : 'Aucune notification à afficher.' }}
        </p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="notification in filteredNotifications"
          :key="notification.notification_id"
          class="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow duration-200"
          :class="{ 'ring-2 ring-blue-200 bg-blue-50': !notification.is_read }"
        >
          <div class="p-6">
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center">
                  <h3 class="text-lg font-medium text-gray-900 truncate">
                    {{ notification.title }}
                  </h3>
                  <div v-if="!notification.is_read" class="ml-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Nouveau
                    </span>
                  </div>
                </div>
                <p class="mt-2 text-sm text-gray-600">
                  {{ notification.message }}
                </p>
                <div class="mt-4 flex items-center text-sm text-gray-500">
                  <svg class="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {{ formatDate(notification.created_at) }}
                </div>
              </div>
              
              <!-- Actions -->
              <div class="ml-4 flex-shrink-0 flex space-x-2">
                <button
                  v-if="notification.action_url"
                  @click="handleNotificationAction(notification)"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Voir
                </button>
                <button
                  v-if="!notification.is_read"
                  @click="markAsRead(notification.notification_id)"
                  class="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Marquer comme lu
                </button>
                <button
                  @click="deleteNotification(notification.notification_id)"
                  class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Supprimer
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Load More Button -->
      <div v-if="hasMoreNotifications" class="text-center">
        <button
          @click="loadMoreNotifications"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          :disabled="loading"
        >
          <template v-if="loading">
            <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Chargement...
          </template>
          <template v-else>
            Charger plus
          </template>
        </button>
      </div>
    </div>

    <!-- Notification Preferences -->
    <div class="bg-white overflow-hidden shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900">
          Préférences de notification
        </h3>
        <div class="mt-2 max-w-xl text-sm text-gray-500">
          <p>Configurez vos préférences de notification.</p>
        </div>
        <div class="mt-5">
          <div class="flex items-center">
            <input
              id="email-notifications"
              v-model="preferences.email_enabled"
              @change="updatePreferences"
              type="checkbox"
              class="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
            >
            <label for="email-notifications" class="ml-2 block text-sm text-gray-900">
              Recevoir les notifications par email
            </label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import { formatDistanceToNow } from 'date-fns'
import { fr } from 'date-fns/locale'

const router = useRouter()
const notificationStore = useNotificationStore()

// Local state
const currentFilter = ref('all')
const currentPage = ref(0)
const pageSize = 20

// Computed properties
const notifications = computed(() => notificationStore.notifications)
const stats = computed(() => notificationStore.stats)
const preferences = computed(() => notificationStore.preferences)
const loading = computed(() => notificationStore.loading)
const unreadCount = computed(() => notificationStore.unreadCount)

const filterTabs = computed(() => [
  { key: 'all', label: 'Toutes', count: stats.value.total_notifications },
  { key: 'unread', label: 'Non lues', count: stats.value.unread_notifications },
  { key: 'read', label: 'Lues', count: stats.value.read_notifications }
])

const filteredNotifications = computed(() => {
  if (currentFilter.value === 'unread') {
    return notifications.value.filter(n => !n.is_read)
  }
  if (currentFilter.value === 'read') {
    return notifications.value.filter(n => n.is_read)
  }
  return notifications.value
})

const hasMoreNotifications = computed(() => {
  const currentCount = notifications.value.length
  return currentCount > 0 && currentCount % pageSize === 0 && currentCount < stats.value.total_notifications
})

// Methods
const refreshNotifications = async () => {
  currentPage.value = 0
  await Promise.all([
    notificationStore.fetchNotifications({ skip: 0, limit: pageSize }),
    notificationStore.fetchNotificationStats()
  ])
}

const loadMoreNotifications = async () => {
  currentPage.value += 1
  const skip = currentPage.value * pageSize
  const newNotifications = await notificationStore.fetchNotifications({ 
    skip, 
    limit: pageSize 
  })
  
  // Add new notifications to existing ones
  if (newNotifications && newNotifications.length > 0) {
    notificationStore.notifications.push(...newNotifications)
  }
}

const markAsRead = async (notificationId) => {
  await notificationStore.markNotificationAsRead(notificationId)
}

const markAllAsRead = async () => {
  await notificationStore.markAllNotificationsAsRead()
}

const deleteNotification = async (notificationId) => {
  await notificationStore.deleteNotification(notificationId)
}

const handleNotificationAction = async (notification) => {
  // Mark as read if not already read
  if (!notification.is_read) {
    await markAsRead(notification.notification_id)
  }
  
  // Navigate to action URL
  if (notification.action_url) {
    router.push(notification.action_url)
  }
}

const updatePreferences = async () => {
  try {
    const preferencesData = {
      email_enabled: Boolean(preferences.value.email_enabled)
    }
    console.log('Updating preferences with data:', preferencesData)
    await notificationStore.updateNotificationPreferences(preferencesData)
  } catch (error) {
    console.error('Error updating notification preferences:', error)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return formatDistanceToNow(date, { 
    addSuffix: true, 
    locale: fr 
  })
}

// Watchers
watch(currentFilter, () => {
  // Reset pagination when filter changes
  currentPage.value = 0
})

// Lifecycle
onMounted(async () => {
  await Promise.all([
    refreshNotifications(),
    notificationStore.fetchNotificationPreferences()
  ])
})
</script>
