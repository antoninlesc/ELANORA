<template>
  <div v-if="visible" class="user-prompt-backdrop">
    <div class="user-prompt-modal">
      <div class="user-prompt-message">{{ message }}</div>
      <input
        v-model="inputValue"
        :type="type"
        class="user-prompt-input"
        autofocus
        @keyup.enter="submit"
      />
      <div class="user-prompt-actions">
        <button class="user-prompt-btn" @click="submit">OK</button>
        <button class="user-prompt-btn cancel" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineExpose } from 'vue';

const props = defineProps({
  modelValue: Boolean,
  message: { type: String, default: '' },
  defaultValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'number' },
});
const emit = defineEmits(['update:modelValue', 'submit', 'cancel']);

const visible = ref(props.modelValue);
const inputValue = ref(props.defaultValue ?? '');

watch(
  () => props.modelValue,
  (v) => (visible.value = v)
);
watch(
  () => props.defaultValue,
  (v) => (inputValue.value = v)
);

function submit() {
  emit('submit', inputValue.value);
  emit('update:modelValue', false);
}
function cancel() {
  emit('cancel');
  emit('update:modelValue', false);
}

defineExpose({ inputValue });
</script>

<style scoped>
.user-prompt-backdrop {
  position: fixed;
  z-index: 10000;
  inset: 0;
  background: rgb(0 0 0 / 25%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-prompt-modal {
  background: #fff;
  border-radius: 10px;
  padding: 28px 32px 22px;
  min-width: 320px;
  box-shadow: 0 4px 32px #0002;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.user-prompt-message {
  font-size: 1.08rem;
  margin-bottom: 16px;
  color: #222;
}

.user-prompt-input {
  font-size: 1.1rem;
  padding: 7px 10px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  margin-bottom: 18px;
}

.user-prompt-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.user-prompt-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 5px;
  padding: 7px 18px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.18s;
}

.user-prompt-btn.cancel {
  background: #e5e7eb;
  color: #333;
}

.user-prompt-btn:hover {
  filter: brightness(1.08);
}
</style>
