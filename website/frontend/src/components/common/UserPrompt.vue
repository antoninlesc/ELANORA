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
      <div v-if="warning" class="user-prompt-warning">{{ warning }}</div>
      <div class="user-prompt-actions">
        <button class="user-prompt-btn" @click="submit">OK</button>
        <button class="user-prompt-btn cancel" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: Boolean,
  message: { type: String, default: '' },
  defaultValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'number' },
  validator: { type: Function, default: null },
});
const emit = defineEmits(['update:modelValue', 'submit', 'cancel']);

const visible = ref(props.modelValue);
const inputValue = ref(props.defaultValue ?? '');
const warning = ref('');

let wasVisible = false;
watch(
  () => props.modelValue,
  (v) => {
    visible.value = v;
    if (v && !wasVisible) {
      inputValue.value = props.defaultValue ?? '';
    }
    wasVisible = v;
  }
);

// Live validation
watch(inputValue, (val) => {
  if (props.validator) {
    const msg = props.validator(val);
    warning.value = typeof msg === 'string' ? msg : '';
  } else {
    warning.value = '';
  }
});

function submit() {
  const trimmed = (inputValue.value ?? '').toString().trim();
  emit('submit', trimmed);
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
  max-width: 50vw;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 32px #0002;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  text-align: justify;
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

.user-prompt-warning {
  color: #e74c3c;
  font-size: 0.98em;
  margin-bottom: 8px;
  margin-top: -10px;
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
