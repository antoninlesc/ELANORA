<template>
  <div class="upload-folder-container">
    <!-- File input for browsing individual files -->
    <input
      ref="fileInput"
      type="file"
      multiple
      accept=".eaf"
      style="display: none"
      @change="handleFileInput"
    />

    <!-- Upload Zone -->
    <div
      class="upload-zone"
      :class="{
        dragover: isDragOver,
        'has-files': selectedFiles.length > 0,
        compact: compact,
      }"
      @drop="handleDrop"
      @dragover.prevent="isDragOver = true"
      @dragleave="isDragOver = false"
      @click="selectedFiles.length === 0 ? triggerBrowse() : null"
    >
      <div v-if="selectedFiles.length === 0" class="upload-content">
        <div class="upload-icon">📁</div>
        <h3>{{ title || $t('upload.zone.title') }}</h3>
        <p>{{ subtitle || $t('upload.zone.subtitle') }}</p>
      </div>

      <div v-else class="files-preview">
        <div class="preview-header">
          <h4>
            {{ $t('upload.selectedFiles', { count: selectedFiles.length }) }}
          </h4>
          <div class="preview-actions">
            <button
              type="button"
              class="action-btn add"
              :title="$t('upload.addMoreFiles')"
              @click.stop="triggerBrowse"
            >
              <font-awesome-icon icon="plus" />
            </button>
            <button
              type="button"
              class="action-btn clear"
              :title="$t('upload.clearAllFiles')"
              @click.stop="clearFiles"
            >
              <font-awesome-icon icon="trash" />
            </button>
          </div>
        </div>

        <div class="files-list" :class="{ 'compact-list': compact }">
          <div
            v-for="(file, index) in selectedFiles"
            :key="getFileKey(file, index)"
            class="file-item"
            :class="{
              'file-noncompliant':
                filesWithCompliance?.[index]?.isCompliant === false,
            }"
            :data-file="file.name"
            @mouseenter="
              enableMediaExtraction &&
              standard &&
              mediaStandard &&
              filesWithCompliance?.[index]?.isCompliant === false
                ? handleFileMouseEnter(file, index)
                : null
            "
            @mouseleave="
              enableMediaExtraction &&
              standard &&
              mediaStandard &&
              filesWithCompliance?.[index]?.isCompliant === false
                ? handleFileMouseLeave()
                : null
            "
          >
            <img
              src="/images/icons/ELAN.svg"
              alt="ELAN file"
              class="file-icon"
            />
            <div class="file-details">
              <span
                class="upload-folder-file-name"
                :title="file.name"
                :data-file="file.name"
                :class="{ processing: isFileProcessing(file.name) }"
              >
                {{ file.name }}
                <span
                  v-if="isFileProcessing(file.name)"
                  class="processing-indicator"
                  >⏳</span
                >
              </span>
              <span class="upload-folder-file-size">{{
                formatFileSize(file.size)
              }}</span>
              <span
                v-if="file.webkitRelativePath"
                class="file-path"
                :title="file.webkitRelativePath"
              >
                {{ getFileDirectory(file.webkitRelativePath) }}
              </span>
            </div>
            <button
              class="remove-btn"
              :title="$t('upload.removeFile')"
              @click.stop="removeFile(index)"
            >
              ×
            </button>
          </div>
        </div>

        <RenameSuggestionPopover
          v-if="
            enableMediaExtraction &&
            standard &&
            mediaStandard &&
            showRenameSuggestion &&
            hoveredFile &&
            renameSuggestion
          "
          ref="renamePopoverRef"
          :key="hoveredFile.name"
          :suggestion="renameSuggestion"
          :current-filename="hoveredFile.name"
          :standard="standard"
          :media-files="hoveredFileMedia"
          :is-upload-context="true"
          :is-processing="isFileProcessing(hoveredFile.name)"
          :style="popoverStyle"
          :trigger-selector="'.file-item.file-noncompliant'"
          :attachment-selector="'.upload-folder-file-name'"
          @accept="handleRenameAccept"
          @close="closeRenameSuggestion"
          @mouseenter="handlePopoverMouseEnter"
          @mouseleave="handlePopoverMouseLeave"
        />

        <div class="files-summary">
          <span class="total-size">
            {{ $t('upload.totalSize', { size: formatFileSize(totalSize) }) }}
          </span>
          <span v-if="maxFileSize && hasOversizedFiles" class="size-warning">
            ⚠️
            {{
              $t('upload.filesExceedLimit', {
                maxSize: formatFileSize(maxFileSize),
              })
            }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, onMounted } from 'vue';
import FontAwesomeIcon from '@/plugins/fontawesome';
import { useEventMessageStore } from '@stores/eventMessage';
import { useI18n } from 'vue-i18n';
import RenameSuggestionPopover from '@/components/common/RenameSuggestionPopover.vue';
import {
  processElanFileForMedia,
  clearElanFileCache,
} from '@/utils/elanFileParser';
import { generateSuggestedFilename } from '@/utils/filenameFromMediaFile';
import { extractComponentsFromFilename } from '@/utils/filenameCompliance';
import { clearComplianceCache } from '@/utils/filenameCompliance';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  maxFileSize: { type: Number, default: 50 * 1024 * 1024 },
  compact: { type: Boolean, default: false },
  allowDuplicates: { type: Boolean, default: false },
  filesWithCompliance: { type: Array, default: () => [] }, // New: Array of compliance statuses
  standard: { type: Object, default: null }, // New: Naming standard for suggestions
  mediaStandard: { type: Object, default: null }, // New: Media naming standard
  enableMediaExtraction: { type: Boolean, default: true }, // New: Explicit control for media extraction
});

const emit = defineEmits([
  'update:modelValue',
  'error',
  'files-changed',
  'rename-file',
]);

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();
const selectedFiles = ref([]);
const isDragOver = ref(false);
const fileInput = ref(null);

// Hover functionality state
const hoveredFile = ref(null);
const hoveredFileIndex = ref(-1);
const showRenameSuggestion = ref(false);
const renameSuggestion = ref('');
const hoveredFileMedia = ref([]);
const popoverStyle = ref({});
const hoverTimeout = ref(null);
const isProcessingHover = ref(false); // Prevent multiple simultaneous processing
const renamePopoverRef = ref(null);

// Media extraction cache for pre-processing
const mediaCache = ref(new Map()); // file.name -> { mediaInfo, isProcessing, error }
const processingQueue = ref(new Set()); // Track files currently being processed

// Cleanup on unmount
onUnmounted(() => {
  // Clear any pending timeouts
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value);
  }

  // Clear caches to prevent memory leaks
  clearElanFileCache();
  clearComplianceCache();
  clearMediaCache();

  // Remove scroll event listener
  window.removeEventListener('scroll', handleScroll);
});

// Setup on mount
onMounted(() => {
  // Add scroll event listener to update popover position on scroll
  window.addEventListener('scroll', handleScroll, { passive: true });
});

// Computed properties
const totalSize = computed(() =>
  selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
);

const hasOversizedFiles = computed(
  () =>
    props.maxFileSize &&
    selectedFiles.value.some((file) => file.size > props.maxFileSize)
);

// Computed property to check if a file is being processed
const isFileProcessing = computed(() => (fileName) => {
  const cached = mediaCache.value.get(fileName);
  return cached?.isProcessing || false;
});

// Helper functions
function getFileKey(file, index) {
  return `${file.name}-${file.size}-${file.lastModified || index}`;
}

function getFileDirectory(relativePath) {
  const parts = relativePath.split('/');
  return parts.length > 1 ? parts.slice(0, -1).join('/') + '/' : '';
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// File input handling
function triggerBrowse() {
  fileInput.value?.click();
}

function handleFileInput(event) {
  const files = Array.from(event.target.files);
  addFiles(files);
  event.target.value = '';
}

// Drag and drop handling
async function handleDrop(event) {
  event.preventDefault();
  isDragOver.value = false;

  const files = await extractFilesFromDrop(event);
  if (files.length > 0) {
    addFiles(files);
  }
}

async function extractFilesFromDrop(event) {
  const items = event.dataTransfer.items;

  if (items && items.length > 0) {
    // Modern browsers - handle files and folders
    const promises = Array.from(items)
      .filter((item) => item.kind === 'file')
      .map((item) => {
        const entry = item.webkitGetAsEntry();
        return entry ? processEntry(entry) : [];
      });

    const results = await Promise.all(promises);
    return results.flat();
  } else {
    // Fallback - handle files only
    return Array.from(event.dataTransfer.files);
  }
}

// Recursively process directory entries
async function processEntry(entry) {
  if (entry.isFile) {
    return new Promise((resolve) => {
      entry.file(
        (file) => {
          // Add relative path for folder structure
          if (entry.fullPath !== '/' + file.name) {
            Object.defineProperty(file, 'webkitRelativePath', {
              value: entry.fullPath.slice(1),
              writable: false,
            });
          }
          resolve([file]);
        },
        () => resolve([])
      );
    });
  }

  if (entry.isDirectory) {
    const dirReader = entry.createReader();
    const allFiles = [];

    // Read all entries from directory
    let entries;
    do {
      entries = await new Promise((resolve) =>
        dirReader.readEntries(resolve, () => resolve([]))
      );

      const filePromises = entries.map(processEntry);
      const fileResults = await Promise.all(filePromises);
      allFiles.push(...fileResults.flat());
    } while (entries.length > 0);

    return allFiles;
  }

  return [];
}

// File processing
function addFiles(files) {
  if (!files?.length) {
    eventMessageStore.addMessage('upload.noFilesSelected', 'error', 4000);
    emit('error', t('upload.noFilesSelected'));
    return;
  }

  // Filter for .eaf files
  const eafFiles = files.filter((file) =>
    file.name.toLowerCase().endsWith('.eaf')
  );

  // Report skipped files
  const skippedCount = files.length - eafFiles.length;
  if (skippedCount > 0) {
    eventMessageStore.addMessage('upload.filesSkipped', 'warning', 4000, {
      count: skippedCount,
    });
  }

  if (!eafFiles.length) {
    eventMessageStore.addMessage('upload.noEafFiles', 'error', 4000);
    emit('error', t('upload.noEafFiles'));
    return;
  }

  // Check file sizes
  if (props.maxFileSize) {
    const oversizedFiles = eafFiles.filter(
      (file) => file.size > props.maxFileSize
    );
    if (oversizedFiles.length > 0) {
      const fileNames = oversizedFiles.map((f) => f.name).join(', ');
      eventMessageStore.addMessage('upload.filesTooLarge', 'error', 6000, {
        files: fileNames,
        maxSize: formatFileSize(props.maxFileSize),
      });
      emit(
        'error',
        t('upload.filesTooLarge', {
          files: fileNames,
          maxSize: formatFileSize(props.maxFileSize),
        })
      );
      return;
    }
  }

  // Handle duplicates
  let filesToAdd = eafFiles;
  if (!props.allowDuplicates) {
    const existingNames = new Set(selectedFiles.value.map((f) => f.name));
    filesToAdd = eafFiles.filter((file) => !existingNames.has(file.name));

    const duplicateCount = eafFiles.length - filesToAdd.length;
    if (duplicateCount > 0) {
      eventMessageStore.addMessage(
        'upload.duplicatesSkipped',
        'warning',
        4000,
        { count: duplicateCount }
      );
    }
  }

  if (!filesToAdd.length) {
    eventMessageStore.addMessage('upload.noNewFiles', 'warning', 4000);
    emit('error', t('upload.noNewFiles'));
    return;
  }

  // Add files
  selectedFiles.value.push(...filesToAdd);

  // Sort alphabetically by file name (case-insensitive)
  selectedFiles.value.sort((a, b) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
  );

  // Start pre-processing files for media extraction (background task)
  if (props.enableMediaExtraction && props.standard && props.mediaStandard) {
    preProcessFilesForMedia(filesToAdd);
  }

  updateModelValue();

  const hasFolder = filesToAdd.some((f) => f.webkitRelativePath);

  if (hasFolder) {
    eventMessageStore.addMessage(
      'upload.filesAddedFromFolder',
      'success',
      3000,
      { count: filesToAdd.length }
    );
  } else if (filesToAdd.length === 1) {
    eventMessageStore.addMessage('upload.fileAdded', 'success', 3000, {
      fileName: filesToAdd[0].name,
    });
  } else {
    eventMessageStore.addMessage('upload.filesAdded', 'success', 3000, {
      count: filesToAdd.length,
    });
  }
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1);
  selectedFiles.value.sort((a, b) =>
    a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
  );

  updateModelValue();
}

function clearFiles() {
  selectedFiles.value = [];
  if (fileInput.value) fileInput.value.value = '';

  // Clear the ELAN file cache when files are cleared
  clearElanFileCache();

  // Clear compliance cache
  clearComplianceCache();

  // Clear media cache
  clearMediaCache();

  updateModelValue();
}

function updateModelValue() {
  emit('update:modelValue', selectedFiles.value);
  emit('files-changed', selectedFiles.value);
}

// Media pre-processing functions
function preProcessFilesForMedia(files) {
  files.forEach((file) => {
    // Skip if already processed or processing
    if (
      mediaCache.value.has(file.name) ||
      processingQueue.value.has(file.name)
    ) {
      return;
    }

    // Mark as processing
    processingQueue.value.add(file.name);
    mediaCache.value.set(file.name, { isProcessing: true });

    // Process in background
    processElanFileForMedia(file)
      .then((mediaInfo) => {
        mediaCache.value.set(file.name, {
          mediaInfo,
          isProcessing: false,
          processedAt: Date.now(),
        });
        processingQueue.value.delete(file.name);
      })
      .catch((error) => {
        console.error(
          'UploadFolder: Error pre-processing media for file:',
          file.name,
          error
        );
        mediaCache.value.set(file.name, {
          error: error.message,
          isProcessing: false,
          processedAt: Date.now(),
        });
        processingQueue.value.delete(file.name);
      });
  });
}

function clearMediaCache() {
  mediaCache.value.clear();
  processingQueue.value.clear();
}

// Helper functions for processing media info
function processCachedMediaInfo(mediaInfo, file) {
  return processMediaInfo(mediaInfo, file);
}

function processMediaInfo(mediaInfo, file) {
  if (mediaInfo.hasMedia && mediaInfo.mediaFilenames.length > 0) {
    hoveredFileMedia.value = mediaInfo.mediaFilenames;

    // Extract components from the first media file using the media standard
    const baseFilename = mediaInfo.mediaFilenames[0].replace(/\.[^/.]+$/, '');
    const extractedComponents = extractComponentsFromFilename(
      props.mediaStandard,
      baseFilename
    );

    if (extractedComponents) {
      // Generate suggested filename
      const suggestion = generateSuggestedFilename(
        extractedComponents,
        props.standard,
        '.eaf'
      );

      if (suggestion && suggestion !== file.name) {
        renameSuggestion.value = suggestion;
        showRenameSuggestion.value = true;
      } else {
        showRenameSuggestion.value = false;
      }
    } else {
      showRenameSuggestion.value = false;
    }
  } else {
    showRenameSuggestion.value = false;
  }
}

// Hover functionality handlers
const popoverHovered = ref(false); // Track if popover is being hovered

async function handleFileMouseEnter(file, index) {
  // Clear any pending close timer
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value);
    hoverTimeout.value = null;
  }

  // If hovering over a different file, close any existing popover first
  if (hoveredFile.value && hoveredFile.value.name !== file.name) {
    closeRenameSuggestion();
  }

  // Only show suggestions for non-compliant files
  if (props.filesWithCompliance?.[index]?.isCompliant !== false) {
    return;
  }

  // Show suggestions if we have standards and media extraction is enabled
  if (!props.enableMediaExtraction || !props.standard || !props.mediaStandard) {
    return;
  }

  hoveredFile.value = file;
  hoveredFileIndex.value = index;

  // Set timeout to show suggestion after 1 second
  hoverTimeout.value = setTimeout(async () => {
    // Prevent multiple simultaneous processing
    if (isProcessingHover.value) {
      return;
    }

    isProcessingHover.value = true;

    try {
      await generateRenameSuggestion(file);
      if (renameSuggestion.value) {
        // Calculate style BEFORE showing the popover
        if (renamePopoverRef.value) {
          const style = renamePopoverRef.value.calculatePopoverStyle(
            file.name,
            '.upload-folder-file-name'
          );
          popoverStyle.value = style;
        }
        showRenameSuggestion.value = true;
      }
    } catch (error) {
      console.error('UploadFolder: Error in hover processing:', error);
    } finally {
      isProcessingHover.value = false;
    }
  }, 1000);
}

function handleFileMouseLeave() {
  // Only handle mouse leave for non-compliant files
  if (
    hoveredFile.value &&
    props.filesWithCompliance?.[hoveredFileIndex.value]?.isCompliant !== false
  ) {
    return;
  }

  // Clear any existing timeout
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value);
    hoverTimeout.value = null;
  }

  // Start a timer to close the popover, but allow time to move to the popover
  hoverTimeout.value = setTimeout(() => {
    if (!popoverHovered.value) {
      closeRenameSuggestion();
    }
  }, 200); // Reduced to match FileTree's timing
}

function handlePopoverMouseEnter() {
  popoverHovered.value = true;
  // Clear any pending close timers
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value);
    hoverTimeout.value = null;
  }
}

function handlePopoverMouseLeave() {
  popoverHovered.value = false;
  // Start a timer to close, similar to file mouse leave
  hoverTimeout.value = setTimeout(() => {
    if (!popoverHovered.value) {
      closeRenameSuggestion();
    }
  }, 200); // Match the file mouse leave timing
}

async function generateRenameSuggestion(file) {
  if (
    !file ||
    !props.enableMediaExtraction ||
    !props.standard ||
    !props.mediaStandard
  ) {
    return;
  }

  // Check if we have cached media info
  const cachedData = mediaCache.value.get(file.name);
  if (cachedData) {
    if (cachedData.isProcessing) {
      // Show processing state
      renameSuggestion.value = 'Processing...';
      showRenameSuggestion.value = true;
      if (renamePopoverRef.value) {
        popoverStyle.value = renamePopoverRef.value.calculatePopoverStyle(
          file.name,
          '.upload-folder-file-name'
        );
      }
      return;
    }

    if (cachedData.error) {
      showRenameSuggestion.value = false;
      return;
    }

    if (cachedData.mediaInfo) {
      return processCachedMediaInfo(cachedData.mediaInfo, file);
    }
  }

  // No cache available, process normally
  try {
    const mediaInfo = await processElanFileForMedia(file);

    // Cache the result for future use
    mediaCache.value.set(file.name, {
      mediaInfo,
      isProcessing: false,
      processedAt: Date.now(),
    });

    return processMediaInfo(mediaInfo, file);
  } catch (error) {
    console.error('UploadFolder: Error generating rename suggestion:', error);
    // Cache the error
    mediaCache.value.set(file.name, {
      error: error.message,
      isProcessing: false,
      processedAt: Date.now(),
    });
    showRenameSuggestion.value = false;
    renameSuggestion.value = '';
  }
}

function handleRenameAccept(newName) {
  // Emit rename event to parent
  emit('rename-file', {
    file: hoveredFile.value,
    index: hoveredFileIndex.value,
    newName: newName,
  });

  closeRenameSuggestion();
}

function closeRenameSuggestion() {
  showRenameSuggestion.value = false;
  hoveredFile.value = null;
  hoveredFileIndex.value = -1;
  hoveredFileMedia.value = [];
  renameSuggestion.value = '';
}

function handleScroll() {
  if (
    hoveredFile.value &&
    showRenameSuggestion.value &&
    renamePopoverRef.value
  ) {
    popoverStyle.value = renamePopoverRef.value.calculatePopoverStyle(
      hoveredFile.value.name,
      '.upload-folder-file-name'
    );
  }
}

// Expose methods
defineExpose({
  clearFiles,
  addFiles,
});
</script>

<style scoped>
.upload-folder-container {
  display: flex;
  flex-direction: column;
  gap: 12px;

  /* Ensure popover can appear above all content */
  position: relative;
  z-index: 1;
  overflow: visible;
}

.upload-zone {
  border: 2px dashed #1976d2;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
  min-height: 140px;
  position: relative;

  /* Ensure popover can appear above */
  overflow: visible;
  z-index: 1;
}

.upload-zone:hover {
  border-color: #1565c0;
  background: #eee;
}

.upload-zone.compact {
  padding: 24px 16px;
  min-height: 100px;
}

.upload-zone.dragover {
  border-color: #388e3c;
  background: #e8f5e9;
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgb(56 142 60 / 20%);
}

.upload-zone.has-files {
  cursor: default;
  text-align: left;
  padding: 16px;
  min-height: auto;
  pointer-events: none;
}

.upload-zone.has-files:hover {
  border-color: #1976d2;
  background: #fafafa;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
}

.files-list {
  max-height: 300px;
  overflow: visible auto;
  margin-bottom: 12px;

  /* Allow popover to appear above */
  position: relative;
  z-index: 1;
}

.files-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #e0e0e0;
  font-size: 0.9rem;
}

.upload-zone.has-files .preview-header,
.upload-zone.has-files .files-list,
.upload-zone.has-files .files-summary {
  pointer-events: auto;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-content h3 {
  margin: 0;
  color: #333;
  font-weight: 600;
  font-size: 1.1rem;
}

.upload-content p {
  margin: 0;
  color: #666;
  font-size: 0.95rem;
}

.upload-icon {
  font-size: 3.5rem;
  opacity: 0.7;
  margin-bottom: 4px;
}

.preview-header h4 {
  margin: 0;
  color: #333;
  font-weight: 600;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
}

.action-btn:hover {
  background: #f5f5f5;
  border-color: #1976d2;
  color: #1976d2;
}

.action-btn.clear:hover {
  border-color: #d32f2f;
  color: #d32f2f;
}

.files-list.compact-list {
  max-height: 200px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.file-item:hover {
  background: rgb(25 118 210 / 4%);
  border-radius: 6px;
  transition: background 0.2s ease;
}

.file-item:last-child {
  border-bottom: none;
}

.file-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.upload-folder-file-name {
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: fit-content;
}

.upload-folder-file-size {
  font-size: 0.85rem;
  color: #666;
  max-width: fit-content;
}

.file-path {
  font-size: 0.8rem;
  color: #999;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  width: 24px;
  height: 24px;
  background: #fff;
  color: #999;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  transition: all 0.2s;
  flex-shrink: 0;
  border: 1px solid #e0e0e0;
}

.remove-btn:hover {
  background: #f44336;
  color: white;
  border-color: #f44336;
}

.total-size {
  color: #666;
  font-weight: 500;
}

.size-warning {
  color: #f57c00;
  font-weight: 500;
}

/* New: Highlight non-compliant files in red */
.file-noncompliant {
  background: #ffe5e5;
  border-left: 4px solid #d9534f;
}

.file-noncompliant .upload-folder-file-name {
  color: #d9534f;
  font-weight: bold;
  max-width: fit-content;
}

.upload-folder-file-name.processing {
  opacity: 0.8;
}

.processing-indicator {
  margin-left: 4px;
  font-size: 0.8em;
  opacity: 0.7;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}
</style>
