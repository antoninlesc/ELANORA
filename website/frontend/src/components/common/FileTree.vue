<template>
  <div class="filetree-container">
    <div v-if="showFilters" class="filetree-filters">
      <input v-model="filterType" placeholder="Filter by extension (e.g., .eaf)" />
      <input v-model="filterDate" type="date" placeholder="Filter by modified date" />
    </div>

    <table class="filetree-table">
      <thead>
        <tr>
          <th class="sortable-header" @click="sortBy('name')">
            <span class="header-text">Filename</span>
            <span class="sort-icon-placeholder">
              <font-awesome-icon
                v-if="sortKey === 'name'"
                :icon="sortOrder === 1 ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down'"
                class="sort-icon"
              />
            </span>
          </th>
          <th class="sortable-header" @click="sortBy('extension')">
            <span class="header-text">Extension</span>
            <span class="sort-icon-placeholder">
              <font-awesome-icon
                v-if="sortKey === 'extension'"
                :icon="sortOrder === 1 ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down'"
                class="sort-icon"
              />
            </span>
          </th>
          <th class="sortable-header" @click="sortBy('size')">
            <span class="header-text">Size</span>
            <span class="sort-icon-placeholder">
              <font-awesome-icon
                v-if="sortKey === 'size'"
                :icon="sortOrder === 1 ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down'"
                class="sort-icon"
              />
            </span>
          </th>
          <th class="sortable-header" @click="sortBy('lastModified')">
            <span class="header-text">Last Modified</span>
            <span class="sort-icon-placeholder">
              <font-awesome-icon
                v-if="sortKey === 'lastModified'"
                :icon="sortOrder === 1 ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down'"
                class="sort-icon"
              />
            </span>
          </th>
          <th class="sortable-header" @click="sortBy('lastUpdatedBy')">
            <span class="header-text">Updated By</span>
            <span class="sort-icon-placeholder">
              <font-awesome-icon
                v-if="sortKey === 'lastUpdatedBy'"
                :icon="sortOrder === 1 ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down'"
                class="sort-icon"
              />
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="file in filteredFiles"
          :key="file.name"
          :data-file="file.name"
          :class="[
            'filetree-row',
            { 'filetree-noncompliant': showCompliance && file.isCompliant === false }
          ]"
          @mouseenter="showCompliance && file.isCompliant === false ? hoveredFile = file.name : null"
          @mouseleave="!popoverHovered ? hoveredFile = null : null"
        >
          <td class="filename-cell">
            <div class="filename-content">
              <img
                v-if="isEafFile(file.name)"
                src="/images/icons/ELAN.svg"
                alt="ELAN file"
                class="file-icon"
              />
              <span 
                :title="file.name" 
                :class="{ 'filename-noncompliant': showCompliance && file.isCompliant === false }"
              >{{ file.name }}</span>
            </div>
          </td>
          <td>{{ getExtension(file.name) }}</td>
          <td>{{ formatSize(file.size) }}</td>
          <td>{{ formatDate(file.lastModified) }}</td>
          <td>{{ file.lastUpdatedBy || 'N/A' }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Compliance popover as context bubble -->
    <FileRenameSuggestion
      v-if="showCompliance && hoveredFile"
      :suggestion="getRenameSuggestion(filteredFiles.find(f => f.name === hoveredFile))"
      :style="popoverStyle"
      @mouseenter="popoverHovered = true"
      @mouseleave="popoverHovered = false"
      @accept="newName => handleRename(filteredFiles.find(f => f.name === hoveredFile), newName)"
      @close="closePopover"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import FileRenameSuggestion from '@components/common/FileRenameSuggestion.vue';
import { extractComponentsFromMedia, generateSuggestedFilename } from '@/utils/filenameFromMediaFile';

const props = defineProps({
  files: { type: Array, required: true },
  showCompliance: { type: Boolean, default: false },
  showFilters: { type: Boolean, default: false },
  projectId: { type: Number, default: null },
  mediaStandard: { type: Object, default: null },
  projectStandard: { type: Object, default: null }
});

const emit = defineEmits(['rename']);

const hoveredFile = ref(null);
const sortKey = ref('name');
const sortOrder = ref(1);
const filterType = ref('');
const filterDate = ref('');
const popoverHovered = ref(false);

const filteredFiles = computed(() => {
  let filtered = props.files.filter(file => {
    const matchesType = !filterType.value || getExtension(file.name).toLowerCase().includes(filterType.value.toLowerCase());
    const matchesDate = !filterDate.value || new Date(file.lastModified).toDateString() === new Date(filterDate.value).toDateString();
    return matchesType && matchesDate;
  });
  return filtered.sort((a, b) => {
    const aVal = a[sortKey.value];
    const bVal = b[sortKey.value];
    if (aVal < bVal) return -sortOrder.value;
    if (aVal > bVal) return sortOrder.value;
    return 0;
  });
});

function sortBy(key) {
  if (sortKey.value === key) {
    sortOrder.value = -sortOrder.value;
  } else {
    sortKey.value = key;
    sortOrder.value = 1;
  }
}

function isEafFile(name) {
  return name.toLowerCase().endsWith('.eaf');
}

function getExtension(name) {
  return name.split('.').pop() || '';
}

function formatSize(bytes) {
  if (!bytes) return 'N/A';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${day}/${month}/${year}, ${hours}:${minutes}`;
}

function getRenameSuggestion(file) {
  // If file already has a suggestion, use it
  if (file?.suggestedName) {
    return file.suggestedName;
  }
  
  // Try to generate media-based suggestion if we have the required data
  if (file?.media_filenames && file.media_filenames.length > 0 && props.mediaStandard && props.projectStandard) {
    const extractedComponents = extractComponentsFromMedia(file.media_filenames, props.mediaStandard);
    if (extractedComponents) {
      const suggestion = generateSuggestedFilename(extractedComponents, props.projectStandard);
      if (suggestion) {
        return suggestion;
      }
    }
  }
  
  // Fallback suggestion
  return 'suggested_filename.eaf';
}

function handleRename(file, newName) {
  emit('rename', { file, newName });
}

function closePopover() {
  hoveredFile.value = null;
  popoverHovered.value = false;
}

const popoverStyle = computed(() => {
  if (!hoveredFile.value) return {};
  const filenameSpan = document.querySelector(`[data-file="${hoveredFile.value}"] .filename-content span`);
  if (!filenameSpan) return { position: 'fixed', top: '100px', left: '100px', zIndex: 10 };
  const rect = filenameSpan.getBoundingClientRect();
  const popoverHeightEstimate = 120;
  return {
    position: 'fixed',
    top: `${rect.top - popoverHeightEstimate}px`, // Position above the filename
    left: `${rect.right}px`,                      // Start to the right of the filename
    zIndex: 10,
  };
});
</script>

<style scoped>
.filetree-container {
  width: 100%;
  overflow-x: auto;
}
.filetree-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.filetree-table th, .filetree-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #ccc;
  border-right: 0.5px solid #e0e0e0;
}
.filetree-table th:last-child, .filetree-table td:last-child {
  border-right: none;
}
.filetree-table th {
  background: #f4f4f4;
  cursor: pointer;
}
.filetree-table th:hover {
  background: #e0e0e0;
}
.filetree-row:nth-child(even) {
  background: #f9f9f9;
}
.filetree-row:hover {
  background: #e8f4fd;
}
.filetree-noncompliant {
  background: #ffe5e5 !important;
}
.filetree-filters {
  margin-bottom: 10px;
}
.filetree-filters input {
  margin-right: 10px;
  padding: 4px;
}
.filename-cell {
  display: flex;
  align-items: center;
}
.filename-content {
  display: flex;
  align-items: center;
}
.file-icon {
  width: 18px;
  height: 18px;
  margin-right: 4px;
  vertical-align: middle;
}
.sort-icon {
  margin-left: 4px;
  font-size: 12px;
}
.sortable-header {
  position: relative;
  cursor: pointer;
}
.header-text {
  display: inline-block;
  margin-right: 4px;
}
.sort-icon-placeholder {
  display: inline-block;
  width: 16px;
  height: 16px;
  vertical-align: middle;
  line-height: 16px;
}
.filename-noncompliant {
  font-weight: bold;
  color: #d9534f;
}
</style>
