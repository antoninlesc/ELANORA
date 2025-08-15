<template>
  <div v-if="visible" class="user-confirm-backdrop">
    <dialog class="user-confirm-modal" open @keydown.esc="cancel">
      <div v-if="title" class="user-confirm-title">{{ title }}</div>
      <div class="user-confirm-message">{{ message }}</div>
      <div class="user-confirm-actions">
        <button class="user-confirm-btn confirm" @click="confirm">
          {{ confirmText }}
        </button>
        <button class="user-confirm-btn cancel" @click="cancel">
          {{ cancelText }}
        </button>
      </div>
    </dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';

const props = defineProps({
  modelValue: Boolean,
  message: { type: String, required: true },
  title: { type: String, default: '' },
  confirmText: { type: String, default: 'Confirm' },
  cancelText: { type: String, default: 'Cancel' },
});
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel']);

const visible = ref(props.modelValue);

watch(
  () => props.modelValue,
  (v) => (visible.value = v)
);

function confirm() {
  emit('confirm');
  emit('update:modelValue', false);
}
function cancel() {
  emit('cancel');
  emit('update:modelValue', false);
}

// Focus modal for accessibility
onMounted(() => {
  if (visible.value) {
    setTimeout(() => {
      const el = document.querySelector('.user-confirm-modal');
      if (el) el.focus();
    }, 10);
  }
});

defineExpose({ confirm, cancel });
</script>

<style scoped>
.user-confirm-backdrop {
  position: fixed;
  z-index: 10000;
  inset: 0;
  background: rgb(0 0 0 / 25%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-confirm-modal {
  background: #fff;
  border-radius: 10px;
  padding: 28px 32px 22px;
  min-width: 320px;
  max-width: 80vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 32px #0002;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  outline: none;
  margin: 0 auto;
  position: static;
}

.user-confirm-title {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 10px;
  color: #222;
}

.user-confirm-message {
  font-size: 1.08rem;
  margin-bottom: 18px;
  color: #222;
}

.user-confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.user-confirm-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 7px 18px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.18s;
}

.user-confirm-btn.cancel {
  background: #d32f2f;
  color: #fff;
}

.user-confirm-btn:hover {
  filter: brightness(1.08);
}
</style>
