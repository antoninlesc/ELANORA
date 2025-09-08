<template>
  <div
    class="file-rename-suggestion-popover"
    tabindex="-1"
    @mouseenter="clearCloseTimer"
    @mouseleave="startCloseTimer"
  >
    <div class="suggestion-title">{{ t('fileRenameSuggestion.title') }}</div>
    <div class="suggestion-new-name">{{ suggestion }}</div>
    <button class="suggestion-accept-btn" @click="acceptSuggestion">
      {{ t('fileRenameSuggestion.accept') }}
    </button>
    <div class="suggestion-manual">
      <input
        v-model="manualName"
        class="suggestion-input"
        :placeholder="t('fileRenameSuggestion.manualPlaceholder')"
        @keydown.enter="acceptManual"
      />
      <button class="suggestion-accept-btn" @click="acceptManual">
        {{ t('fileRenameSuggestion.acceptManual') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps({
  suggestion: { type: String, required: true }
});
const emit = defineEmits(['accept', 'close']);

const manualName = ref('');

let closeTimer = null;
function startCloseTimer() {
  closeTimer = setTimeout(() => emit('close'), 1000);
}
function clearCloseTimer() {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}
function acceptSuggestion() {
  emit('accept', props.suggestion);
  emit('close');
}
function acceptManual() {
  if (manualName.value.trim()) {
    emit('accept', manualName.value.trim());
    emit('close');
  }
}
</script>

<style scoped>
.file-rename-suggestion-popover {
  background: #fff;
  border: 1px solid #ffe082;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 10%);
  padding: 10px 16px;
  min-width: 220px;
  z-index: 100;
  font-size: 0.98rem;
  position: absolute;
}
.suggestion-title {
  font-weight: 600;
  color: #d32f2f;
  margin-bottom: 4px;
}
.suggestion-new-name {
  color: #333;
  font-family: monospace;
  background: #fffde7;
  border-radius: 4px;
  padding: 2px 6px;
  margin-bottom: 8px;
}
.suggestion-accept-btn {
  background: #388e3c;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 4px 10px;
  margin-right: 6px;
  cursor: pointer;
  font-size: 0.95rem;
}
.suggestion-manual {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  align-items: center;
}
.suggestion-input {
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.95rem;
}
</style>