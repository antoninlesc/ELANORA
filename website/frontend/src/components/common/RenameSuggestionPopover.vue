<template>
  <div
    class="rename-suggestion-popover"
    :style="style"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <div class="suggestion-header">
      <div class="suggestion-title">
        <i class="fas fa-lightbulb"></i>
        {{ t('renameSuggestionPopover.title') }}
      </div>
      <button class="close-btn" @click="emit('close')">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="suggestion-content">
      <div v-if="isProcessing" class="processing-state">
        <i class="fas fa-spinner fa-spin"></i>
        {{ t('renameSuggestionPopover.processing') }}
      </div>

      <div v-else-if="mediaFiles.length > 0" class="media-files-info">
        <i class="fas fa-film"></i>
        <span class="media-info-text">{{
          t('renameSuggestionPopover.basedOnMediaFile')
        }}</span>
        <span class="media-file-name">{{ mediaFiles[0] }}</span>
      </div>

      <div class="suggestion-input-container">
        <input
          v-model="renameValue"
          class="suggestion-input"
          :class="{ 'non-compliant': !isValidRename }"
          :placeholder="t('renameSuggestionPopover.placeholder')"
          @input="handleInputChange"
          @keydown.enter="confirmRename"
          @keydown.escape="emit('close')"
        />

        <div
          v-if="!isValidRename && renameValue.trim()"
          class="compliance-warning"
        >
          <i class="fas fa-exclamation-triangle"></i>
          {{ t('renameSuggestionPopover.notCompliant') }}
        </div>
      </div>

      <div class="suggestion-actions">
        <button class="suggestion-btn cancel-btn" @click="emit('close')">
          {{ t('common.cancel') }}
        </button>
        <button
          class="suggestion-btn confirm-btn"
          :disabled="!isValidRename || isRenaming"
          @click="confirmRename"
        >
          <span v-if="isRenaming" class="spinner"></span>
          {{
            isRenaming
              ? t('renameSuggestionPopover.renaming')
              : t('renameSuggestionPopover.rename')
          }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { isElanFilenameCompliant } from '@/utils/elanFilenameCompliance';

const { t } = useI18n();

const props = defineProps({
  // Core props
  suggestion: { type: String, required: true },
  currentFilename: { type: String, required: true },
  standard: { type: Object, default: null },
  mediaFiles: { type: Array, default: () => [] },

  // Context-specific props
  isUploadContext: { type: Boolean, default: false }, // true for upload, false for existing files
  projectName: { type: String, default: '' },
  elanId: { type: Number, default: null },
  isProcessing: { type: Boolean, default: false },

  // Positioning and attachment
  style: { type: Object, default: () => ({}) },

  // Configurable selectors for trigger and attachment elements
  triggerSelector: { type: String, default: '' }, // CSS selector for hover trigger element
  attachmentSelector: { type: String, default: '' }, // CSS selector for visual attachment element
});

const emit = defineEmits([
  'accept',
  'close',
  'mouseenter',
  'mouseleave',
  'conflict',
  'error',
]);

const renameValue = ref('');
const isRenaming = ref(false);

// Computed properties
const isValidRename = computed(() => {
  const trimmedValue = renameValue.value.trim();
  if (!trimmedValue || trimmedValue === props.currentFilename) return false;
  if (!props.standard) return false;

  return isElanFilenameCompliant(props.standard, trimmedValue);
});

// Calculate simple popover position - always to the right with left arrow
function calculatePopoverStyle(hoveredFile, attachmentSelector) {
  if (!hoveredFile || !attachmentSelector) {
    return {};
  }

  // Find the attachment element
  const attachmentElement =
    document.querySelector(
      `${attachmentSelector}[data-file="${hoveredFile}"]`
    ) || document.querySelector(attachmentSelector);

  if (!attachmentElement) {
    console.warn(
      'RenameSuggestionPopover: Could not find attachment element with selector:',
      attachmentSelector,
      'for file:',
      hoveredFile
    );
    return { position: 'fixed', top: '100px', left: '100px', zIndex: 10 };
  }

  const rect = attachmentElement.getBoundingClientRect();
  const popoverWidth = 320; // max-width from CSS

  // Try to get actual popover height if it exists, otherwise use estimate
  const popoverElement = document.querySelector('.rename-suggestion-popover');
  const popoverHeight = popoverElement ? popoverElement.offsetHeight : 180;

  const arrowSize = 8; // Size of the arrow
  const gap = 8; // Gap between attachment element and popover

  // Position popover so arrow tip (at 50% of popover height) aligns with center of attachment element
  let left = rect.right + gap + arrowSize;
  let top = rect.top + rect.height / 2 - popoverHeight / 2;

  // Ensure popover doesn't go off-screen horizontally
  if (left + popoverWidth > window.innerWidth - 20) {
    left = window.innerWidth - popoverWidth - 20;
  }

  // Ensure popover doesn't go off-screen vertically
  if (top < 20) {
    top = 20;
  } else if (top + popoverHeight > window.innerHeight - 20) {
    top = window.innerHeight - popoverHeight - 20;
  }

  return {
    position: 'fixed',
    top: `${top}px`,
    left: `${left}px`,
    zIndex: 999999,
  };
}

// Expose methods for parent components
defineExpose({
  calculatePopoverStyle,
});

// Watchers
onMounted(() => {
  renameValue.value = props.suggestion;
});

watch(
  () => props.suggestion,
  (newSuggestion) => {
    if (newSuggestion) {
      renameValue.value = newSuggestion;
    }
  }
);

watch(
  () => props.style,
  () => {
    // Style updated - popover will re-position automatically
  },
  { deep: true }
);

// Event handlers
function handleMouseEnter() {
  emit('mouseenter');
}

function handleMouseLeave() {
  emit('mouseleave');
}

function handleInputChange() {
  // Could add debounced validation here if needed
}

async function confirmRename() {
  if (!isValidRename.value || isRenaming.value) return;

  const newName = renameValue.value.trim();
  isRenaming.value = true;

  try {
    if (props.isUploadContext) {
      // For upload context, just emit the new name
      emit('accept', newName);
      emit('close');
    } else {
      // For existing files context, make API call
      if (!props.projectName || !props.elanId) {
        throw new Error('Missing project information for rename operation');
      }

      // Import gitService dynamically to avoid circular dependencies
      const gitService = (await import('@api/service/gitService')).default;

      console.log('RenameSuggestionPopover props:', {
        projectName: props.projectName,
        elanId: props.elanId,
        currentFilename: props.currentFilename,
        newName,
      });

      const result = await gitService.renameFile(
        props.projectName,
        props.elanId,
        newName
      );

      // Check the result for success/failure
      if (result && result.success) {
        // Only emit accept if the rename was successful
        emit('accept', newName);
        emit('close');
      } else if (result && result.message_key === 'rename_file_conflict') {
        // Handle conflict response from backend
        emit('conflict', {
          newName,
          currentFilename: props.currentFilename,
          conflictElanId: result.conflict_elan_id,
          message: result.message || 'A file with this name already exists',
        });
      } else {
        // Handle other unsuccessful responses
        emit('error', new Error(result?.message || 'Rename operation failed'));
      }
    }
  } catch (error) {
    console.error('Rename error:', error);

    // Check for specific backend error responses
    const responseData = error.response?.data;

    if (
      responseData?.message_key === 'rename_file_conflict' ||
      error.response?.status === 409
    ) {
      // File name conflict - emit conflict event
      emit('conflict', {
        newName,
        currentFilename: props.currentFilename,
        conflictElanId: responseData?.conflict_elan_id,
        message:
          responseData?.message || 'A file with this name already exists',
      });
    } else {
      // General error
      emit('error', error);
    }
  } finally {
    isRenaming.value = false;
  }
}
</script>

<style scoped>
.rename-suggestion-popover {
  background: #fff;
  border: 1px solid #ffe082;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 15%);
  padding: 0;
  min-width: 320px;
  max-width: 400px;
  z-index: 999999 !important;
  font-size: 0.98rem;
  position: fixed !important;
  transform: none !important;
  overflow: visible; /* Allow arrow to show outside bounds */
  pointer-events: auto !important; /* Ensure popover can be interacted with */
}

/* Simple left-pointing arrow always centered on left edge */
.rename-suggestion-popover::before,
.rename-suggestion-popover::after {
  content: '';
  position: absolute;
  border: solid transparent;
  z-index: 100001;
  pointer-events: none; /* Ensure arrow doesn't interfere with mouse events */
}

/* Main arrow (outer border) - points left towards filename */
.rename-suggestion-popover::before {
  content: '';
  position: absolute;
  border-style: solid;
  border-color: transparent #ffe082 transparent transparent;
  border-width: 8px 8px 8px 0;
  top: calc(50% - 8px) !important; /* Keep important for positioning */
  left: -8px !important; /* Keep important for positioning */
  width: 0;
  height: 0;
  z-index: 1000000;
  pointer-events: none;
}

/* Inner arrow (white fill) - points left towards filename */
.rename-suggestion-popover::after {
  content: '';
  position: absolute;
  border-style: solid;
  border-color: transparent #fff transparent transparent;
  border-width: 7px 7px 7px 0;
  top: calc(50% - 7px) !important; /* Keep important for positioning */
  left: -7px !important; /* Keep important for positioning */
  width: 0;
  height: 0;
  z-index: 1000001;
  pointer-events: none;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px 8px;
  border-bottom: 1px solid #f0f0f0;
}

.suggestion-title {
  font-weight: 600;
  color: #d32f2f;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
}

.suggestion-content {
  padding: 12px 16px;
}

.processing-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-style: italic;
  margin-bottom: 12px;
}

.media-files-info {
  color: #666;
  font-size: 0.85rem;
  margin-bottom: 8px;
  padding: 6px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  border-left: 3px solid #1565c0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.media-info-text {
  font-weight: 500;
}

.media-file-name {
  font-family: monospace;
  font-size: 0.8rem;
  color: #555;
  background: rgb(255 255 255 / 70%);
  padding: 2px 6px;
  border-radius: 3px;
}

.suggestion-input-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.suggestion-input {
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 6px 8px;
  font-size: 0.95rem;
  font-family: monospace;
  width: 100%;
  transition: border-color 0.2s;
}

.suggestion-input:focus {
  outline: none;
  border-color: #2196f3;
}

.suggestion-input.non-compliant {
  border-color: #f44336;
  background-color: #fff8f8;
}

.compliance-warning,
.compliance-success {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8rem;
  margin-top: 4px;
}

.compliance-warning {
  color: #f44336;
}

.compliance-success {
  color: #4caf50;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.suggestion-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.95rem;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: background 0.2s;
}

.cancel-btn {
  background: #f5f5f5;
  color: #666;
}

.cancel-btn:hover {
  background: #e0e0e0;
}

.confirm-btn {
  background: #1976d2;
  color: #fff;
}

.confirm-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.confirm-btn:hover:not(:disabled) {
  background: #1565c0;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid #ffffff40;
  border-top: 2px solid #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>
