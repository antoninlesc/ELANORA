<!-- filepath: e:\Github\ELANORA\website\frontend\src\components\pageSpecific\projectsPage\DownloadFilesDialog.vue -->
<template>
  <div class="download-dialog-overlay" @click="closeDialog">
    <div class="download-dialog" @click.stop>
      <div class="download-dialog-header">
        <h3>{{ $t('downloadDialog.title', { projectName }) }}</h3>
        <button class="download-dialog-close-btn" @click="closeDialog">
          <font-awesome-icon icon="fa-solid fa-times" />
        </button>
      </div>

      <div class="download-dialog-content">
        <div v-if="sortedFiles.length === 0" class="no-files-message">
          {{ t('downloadDialog.noFiles') }}
        </div>
        <div v-else class="files-section">
          <div class="files-header">
            <h4>
              {{
                t('downloadDialog.selectedFiles', {
                  count: selectedFiles.length,
                  total: sortedFiles.length,
                })
              }}
            </h4>
            <label class="select-all-label">
              <input
                v-model="selectAll"
                type="checkbox"
                @change="toggleAllFiles"
              />
              {{
                selectAll
                  ? t('downloadDialog.deselectAll')
                  : t('downloadDialog.selectAll')
              }}
            </label>
          </div>

          <div class="files-list">
            <div
              v-for="file in sortedFiles"
              :key="file.elan_id || file.name || file.filename || Math.random()"
              class="file-item"
              :class="{
                'file-selected':
                  file.elan_id && selectedFiles.includes(file.elan_id),
              }"
              @click="toggleFile(file.elan_id)"
            >
              <input
                :checked="file.elan_id && selectedFiles.includes(file.elan_id)"
                type="checkbox"
                class="file-checkbox"
                @click.stop
                @change="toggleFile(file.elan_id)"
              />
              <img
                src="/images/icons/ELAN.svg"
                alt="ELAN file"
                class="file-icon"
              />
              <div class="file-details">
                <span class="file-name" :title="file.name || file.filename">{{
                  file.name || file.filename
                }}</span>
                <span class="file-size">{{
                  formatFileSize(file.file_size || file.size)
                }}</span>
                <span
                  v-if="file.file_path"
                  class="file-path"
                  :title="file.file_path"
                  >{{ file.file_path }}</span
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="download-dialog-footer">
        <button class="cancel-btn" @click="closeDialog">
          {{ t('downloadDialog.cancel') }}
        </button>
        <button
          class="download-btn"
          :disabled="selectedFiles.length === 0"
          @click="downloadFiles"
        >
          <font-awesome-icon icon="fa-solid fa-download" />
          {{ t('downloadDialog.download') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  projectName: { type: String, required: true },
  files: { type: Array, default: () => [] },
});

const emit = defineEmits(['close', 'download']);

const { t } = useI18n();
const selectedFiles = ref([]);
const selectAll = ref(false);

// Sorting state comes from props instead of internal refs
// const sortKey = ref('name');
// const sortOrder = ref(1); // 1 for ascending, -1 for descending

// Files are already filtered and sorted by FileTree component
const sortedFiles = computed(() => {
  return props.files || [];
});

// Watch for changes in files to reset selections
watch(
  () => props.files,
  () => {
    selectedFiles.value = [];
    selectAll.value = false;
    // Trigger update of selectAll state after files change
    nextTick(() => {
      updateSelectAllState();
    });
  },
  { immediate: true }
);

// Watch for changes in selectedFiles to update selectAll state
watch(selectedFiles, () => {
  updateSelectAllState();
});

function toggleFile(fileId) {
  if (!fileId) return;

  const index = selectedFiles.value.indexOf(fileId);
  if (index > -1) {
    selectedFiles.value.splice(index, 1);
  } else {
    selectedFiles.value.push(fileId);
  }
  updateSelectAllState();
}

function updateSelectAllState() {
  if (!sortedFiles.value || !Array.isArray(sortedFiles.value)) {
    selectAll.value = false;
    return;
  }
  selectAll.value =
    selectedFiles.value.length === sortedFiles.value.length &&
    sortedFiles.value.length > 0;
}

function toggleAllFiles() {
  if (!sortedFiles.value || !Array.isArray(sortedFiles.value)) {
    selectedFiles.value = [];
    return;
  }

  if (selectAll.value) {
    selectedFiles.value = sortedFiles.value
      .map((f) => f.elan_id)
      .filter((id) => id != null && id !== undefined);
  } else {
    selectedFiles.value = [];
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return t('downloadDialog.unknownSize');
  const k = 1024;
  const sizes = [
    t('downloadDialog.bytes'),
    t('downloadDialog.kb'),
    t('downloadDialog.mb'),
    t('downloadDialog.gb'),
  ];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function closeDialog() {
  emit('close');
}

function downloadFiles() {
  if (selectedFiles.value.length === 0) return;

  if (!sortedFiles.value || !Array.isArray(sortedFiles.value)) {
    return;
  }

  const selectedFileObjects = sortedFiles.value.filter(
    (f) => f && f.elan_id && selectedFiles.value.includes(f.elan_id)
  );

  if (selectedFileObjects.length === 0) return;

  emit('download', selectedFileObjects);
}
</script>

<style scoped>
.download-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgb(0 0 0 / 50%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.download-dialog {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 550px;
  max-height: 80%;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 16px rgb(0 0 0 / 20%);
}

.download-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.download-dialog-header h3 {
  margin: 0;
  color: #333;
}

.download-dialog-close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
}

.download-dialog-content {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
}

.no-files-message {
  text-align: center;
  color: #666;
  font-size: 1rem;
  padding: 40px 20px;
}

.files-section {
  display: flex;
  flex-direction: column;
}

.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e0e0e0;
}

.files-header h4 {
  margin: 0;
  color: #333;
  font-size: 1rem;
  font-weight: 600;
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.85rem;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.select-all-label:hover {
  background: #e3f2fd;
}

.files-list {
  max-height: 300px;
  overflow-y: auto;
  border-radius: 6px;
  background: #fafafa;
}

.files-list::-webkit-scrollbar {
  width: 6px;
}

.files-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.files-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.files-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}

.file-item:hover {
  background: #e3f2fd;
  box-shadow: inset 0 0 0 1px rgb(25 118 210 / 10%);
}

.file-item:nth-child(even) {
  background: #fafafa;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:nth-child(even):hover {
  background: #e3f2fd;
}

.file-selected {
  background: #e3f2fd !important;
  border-left: 3px solid #1976d2;
}

.file-selected:hover {
  background: #bbdefb !important;
}

.file-checkbox {
  margin: 0;
  cursor: pointer;
}

.file-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  opacity: 0.8;
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
  font-size: 0.9rem;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.75rem;
  color: #666;
  font-weight: 400;
  background: #f5f5f5;
  padding: 1px 4px;
  border-radius: 3px;
  display: inline-block;
  white-space: nowrap;
}

.file-path {
  font-size: 0.7rem;
  color: #888;
  font-family: 'SF Mono', Monaco, Inconsolata, 'Roboto Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  opacity: 0.7;
}

.download-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}

.cancel-btn {
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  color: #666;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease;
}

.cancel-btn:hover {
  background: #e8e8e8;
  border-color: #ccc;
}

.download-btn {
  padding: 8px 16px;
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition:
    background 0.2s,
    box-shadow 0.2s;
  box-shadow: 0 1px 4px rgb(25 118 210 / 8%);
}

.download-btn:disabled {
  background: #90caf9;
  cursor: not-allowed;
  box-shadow: none;
}

.download-btn:hover:not(:disabled),
.download-btn:focus-visible:not(:disabled) {
  background: #1565c0;
  box-shadow: 0 2px 8px rgb(25 118 210 / 16%);
}
</style>
