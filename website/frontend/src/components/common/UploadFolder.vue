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
        'dragover': isDragOver, 
        'has-files': selectedFiles.length > 0,
        'compact': compact 
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
          <h4>{{ $t('upload.selectedFiles', { count: selectedFiles.length }) }}</h4>
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
          >
            <img
              src="/images/icons/ELAN.svg"
              alt="ELAN file"
              class="file-icon"
            />
            <div class="file-details">
              <span class="file-name" :title="file.name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
              <span v-if="file.webkitRelativePath" class="file-path" :title="file.webkitRelativePath">
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

        <div class="files-summary">
          <span class="total-size">
            {{ $t('upload.totalSize', { size: formatFileSize(totalSize) }) }}
          </span>
          <span v-if="maxFileSize && hasOversizedFiles" class="size-warning">
            ⚠️ {{ $t('upload.filesExceedLimit', { maxSize: formatFileSize(maxFileSize) }) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import FontAwesomeIcon from '@/plugins/fontawesome';
import { useEventMessageStore } from '@stores/eventMessage';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  maxFileSize: { type: Number, default: 50 * 1024 * 1024 },
  compact: { type: Boolean, default: false },
  allowDuplicates: { type: Boolean, default: false }
});

const emit = defineEmits(['update:modelValue', 'error', 'files-changed']);

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();
const selectedFiles = ref([]);
const isDragOver = ref(false);
const fileInput = ref(null);

// Initialize from modelValue
watch(() => props.modelValue, (newValue) => {
  if (newValue && Array.isArray(newValue)) {
    selectedFiles.value = [...newValue];
  }
}, { immediate: true });

// Computed properties
const totalSize = computed(() => 
  selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
);

const hasOversizedFiles = computed(() =>
  props.maxFileSize && selectedFiles.value.some(file => file.size > props.maxFileSize)
);

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
      .filter(item => item.kind === 'file')
      .map(item => {
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
      entry.file((file) => {
        // Add relative path for folder structure
        if (entry.fullPath !== '/' + file.name) {
          Object.defineProperty(file, 'webkitRelativePath', {
            value: entry.fullPath.slice(1),
            writable: false
          });
        }
        resolve([file]);
      }, () => resolve([]));
    });
  } 
  
  if (entry.isDirectory) {
    const dirReader = entry.createReader();
    const allFiles = [];
    
    // Read all entries from directory
    let entries;
    do {
      entries = await new Promise(resolve => 
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
  const eafFiles = files.filter(file => 
    file.name.toLowerCase().endsWith('.eaf')
  );
  
  // Report skipped files
  const skippedCount = files.length - eafFiles.length;
  if (skippedCount > 0) {
    eventMessageStore.addMessage('upload.filesSkipped', 'warning', 4000, { count: skippedCount });
  }
  
  if (!eafFiles.length) {
    eventMessageStore.addMessage('upload.noEafFiles', 'error', 4000);
    emit('error', t('upload.noEafFiles'));
    return;
  }
  
  // Check file sizes
  if (props.maxFileSize) {
    const oversizedFiles = eafFiles.filter(file => file.size > props.maxFileSize);
    if (oversizedFiles.length > 0) {
      const fileNames = oversizedFiles.map(f => f.name).join(', ');
      eventMessageStore.addMessage('upload.filesTooLarge', 'error', 6000, { 
        files: fileNames,
        maxSize: formatFileSize(props.maxFileSize)
      });
      emit('error', t('upload.filesTooLarge', { files: fileNames, maxSize: formatFileSize(props.maxFileSize) }));
      return;
    }
  }
  
  // Handle duplicates
  let filesToAdd = eafFiles;
  if (!props.allowDuplicates) {
    const existingNames = new Set(selectedFiles.value.map(f => f.name));
    filesToAdd = eafFiles.filter(file => !existingNames.has(file.name));
    
    const duplicateCount = eafFiles.length - filesToAdd.length;
    if (duplicateCount > 0) {
      eventMessageStore.addMessage('upload.duplicatesSkipped', 'warning', 4000, { count: duplicateCount });
    }
  }
  
  if (!filesToAdd.length) {
    eventMessageStore.addMessage('upload.noNewFiles', 'warning', 4000);
    emit('error', t('upload.noNewFiles'));
    return;
  }
  
  // Add files and show success
  selectedFiles.value.push(...filesToAdd);
  updateModelValue();
  
  const hasFolder = filesToAdd.some(f => f.webkitRelativePath);
  
  if (hasFolder) {
    eventMessageStore.addMessage('upload.filesAddedFromFolder', 'success', 3000, { count: filesToAdd.length });
  } else if (filesToAdd.length === 1) {
    eventMessageStore.addMessage('upload.fileAdded', 'success', 3000, { fileName: filesToAdd[0].name });
  } else {
    eventMessageStore.addMessage('upload.filesAdded', 'success', 3000, { count: filesToAdd.length });
  }
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1);
  updateModelValue();
}

function clearFiles() {
  selectedFiles.value = [];
  if (fileInput.value) fileInput.value.value = '';
  updateModelValue();
}

function updateModelValue() {
  emit('update:modelValue', selectedFiles.value);
  emit('files-changed', selectedFiles.value);
}

// Expose methods
defineExpose({
  clearFiles,
  addFiles
});
</script>

<style scoped>
.upload-folder-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.upload-zone {
  border: 2px dashed #1976d2;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
  min-height: 140px;
  position: relative;
}

.upload-zone:hover {
  border-color: #1565c0;
  background: #f5f5f5;
}

.upload-zone.compact {
  padding: 24px 16px;
  min-height: 100px;
}

.upload-zone.dragover {
  border-color: #388e3c;
  background: #e8f5e9;
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(56, 142, 60, 0.2);
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

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
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

.files-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 12px;
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

.file-name {
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.85rem;
  color: #666;
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

.files-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #e0e0e0;
  font-size: 0.9rem;
}

.total-size {
  color: #666;
  font-weight: 500;
}

.size-warning {
  color: #f57c00;
  font-weight: 500;
}

@media (max-width: 768px) {
  .preview-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .files-summary {
    flex-direction: column;
    gap: 4px;
    align-items: flex-start;
  }
}
</style>
