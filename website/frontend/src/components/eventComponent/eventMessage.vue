<template>
  <transition name="slide-fade">
    <div
      v-if="visible"
      :class="['event-message', typeClasses[type]]"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
    >
      <div class="event-message-icon">
        <font-awesome-icon
          v-if="type === 'error'"
          :icon="faExclamationCircle"
        />
        <font-awesome-icon
          v-if="type === 'warning'"
          :icon="faExclamationTriangle"
        />
        <font-awesome-icon v-if="type === 'info'" :icon="faInfoCircle" />
        <font-awesome-icon v-if="type === 'success'" :icon="faCheckCircle" />
      </div>
      <div class="event-message-text">
        {{ t(translationKey) }}
      </div>
      <button
        class="event-message-close"
        aria-label="Close notification"
        @click="closeMessage"
      >
        <font-awesome-icon :icon="faTimes" />
      </button>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { useI18n } from 'vue-i18n';
import {
  faExclamationCircle,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faTimes,
} from '@fortawesome/free-solid-svg-icons';

const props = defineProps({
  translationKey: {
    type: String,
    required: true,
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) =>
      ['info', 'warning', 'error', 'success'].includes(value),
  },
  duration: {
    type: Number,
    default: 6000, // 6 seconds
  },
  show: {
    type: Boolean,
    default: true,
  },
  id: {
    type: Number,
    required: true,
  },
});

const { t } = useI18n();
const emit = defineEmits(['close']);
const visible = ref(props.show);
const timer = ref(null);
const hover = ref(false);
let fadeOutTimer = null;

const typeClasses = computed(() => ({
  error: 'event-message-error',
  warning: 'event-message-warning',
  info: 'event-message-info',
  success: 'event-message-success',
}));

const closeMessage = () => {
  visible.value = false;
  if (timer.value) {
    clearTimeout(timer.value);
  }
  if (fadeOutTimer) {
    clearTimeout(fadeOutTimer);
  }
  // Allow time for animation to complete before emitting close event
  setTimeout(() => {
    emit('close', props.id);
  }, 500);
};

const setupAutoClose = () => {
  if (timer.value) {
    clearTimeout(timer.value);
  }

  if (props.duration > 0) {
    timer.value = setTimeout(() => {
      if (!hover.value) {
        closeMessage();
      }
      // If hovering, do not close; will close on mouseleave
    }, props.duration);
  }
};

function onMouseEnter() {
  hover.value = true;
  if (timer.value) {
    clearTimeout(timer.value);
  }
  if (fadeOutTimer) {
    clearTimeout(fadeOutTimer);
  }
}

function onMouseLeave() {
  hover.value = false;
  // Start fade out after 2 seconds if not already closed
  fadeOutTimer = setTimeout(() => {
    closeMessage();
  }, 2000);
}

watch(
  () => props.show,
  (newValue) => {
    visible.value = newValue;
    if (newValue && props.duration > 0) {
      setupAutoClose();
    }
  }
);

onMounted(() => {
  if (visible.value && props.duration > 0) {
    setupAutoClose();
  }
});

onBeforeUnmount(() => {
  if (timer.value) {
    clearTimeout(timer.value);
  }
  if (fadeOutTimer) {
    clearTimeout(fadeOutTimer);
  }
});
</script>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.slide-fade-leave-active {
  transition: all 0.5s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.slide-fade-enter-from {
  transform: translateY(40px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(40px);
  opacity: 0;
}

.event-message {
  min-width: 300px;
  max-width: 450px;
  display: flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgb(0 0 0 / 10%);
  gap: 1rem;
}

.event-message-icon {
  flex-shrink: 0;
  margin-right: 0.75rem;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
}

.event-message-text {
  flex-grow: 1;
  font-size: 1rem;
  text-align: left;
}

.event-message-close {
  margin-left: 1rem;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1.2rem;
  transition: color 0.15s;
}

.event-message-close:hover {
  color: #374151;
}

.event-message-error {
  background: #ffe1e1;
  color: #b91c1c;
  border-left: 4px solid #ef4444;
}

.event-message-warning {
  background: #fffbe6;
  color: #b45309;
  border-left: 4px solid #f59e42;
}

.event-message-info {
  background: var(--very-light-main, #d4fff7);
  color: var(--color-main, #077a7d);
  border-left: 4px solid var(--color-main, #077a7d);
}

.event-message-success {
  background: #e6fffa;
  color: #047857;
  border-left: 4px solid #34d399;
}
</style>