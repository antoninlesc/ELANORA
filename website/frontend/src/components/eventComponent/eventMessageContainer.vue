<template>
  <div class="event-message-container">
    <EventMessage
      v-for="msg in messages"
      :id="msg.id"
      :key="msg.id"
      :translation-key="msg.translationKey"
      :type="msg.type"
      :duration="msg.duration"
      :show="msg.show"
      @close="handleClose"
    />
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import { useEventMessageStore } from '@stores/eventMessage';
import { onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import EventMessage from './eventMessage.vue';

const eventMessageStore = useEventMessageStore();
const { messages } = storeToRefs(eventMessageStore);
const router = useRouter();

const handleClose = (id) => {
  eventMessageStore.removeMessage(id);
};

// Process messages from localStorage
const checkLocalStorageForMessages = () => {
  // Check login success message
  if (localStorage.getItem('loginMessage') === 'success') {
    eventMessageStore.addMessage('event_messages.login.success', 'success');
    localStorage.removeItem('loginMessage');
  }

  // Check logout success message
  if (localStorage.getItem('logoutMessage') === 'success') {
    eventMessageStore.addMessage('event_messages.logout.success', 'success');
    localStorage.removeItem('logoutMessage');
  }

  // Check permission denied message
  if (localStorage.getItem('loginPermissionDeniedMessage') === 'true') {
    eventMessageStore.addMessage('event_messages.permission_denied', 'warning');
    localStorage.removeItem('loginPermissionDeniedMessage');
  }
};

onMounted(() => {
  // Initial check
  checkLocalStorageForMessages();

  // Use router's afterEach hook to detect navigation
  const unregisterHook = router.afterEach(() => {
    checkLocalStorageForMessages();
  });

  // Clean up
  onBeforeUnmount(() => {
    unregisterHook();
  });
});
</script>

<style scoped>
.event-message-container {
  position: fixed;
  bottom: 1.5rem;
  left: 1.5rem;
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>