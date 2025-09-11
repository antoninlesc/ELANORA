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
        >
          <td 
            class="filename-cell"
            @mouseenter="onFilenameMouseEnter(file)"
            @mouseleave="onFilenameMouseLeave"
          >
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
      :key="hoveredFile"
      :suggestion="getRenameSuggestion(filteredFiles.find(f => f.name === hoveredFile))"
      :current-filename="hoveredFile"
      :project-name="projectName"
      :elan-id="filteredFiles.find(f => f.name === hoveredFile)?.elan_id"
      :standard="projectStandard"
      :media-files="filteredFiles.find(f => f.name === hoveredFile)?.media_filenames || []"
      :style="popoverStyle"
      @mouseenter="onPopoverMouseEnter"
      @mouseleave="onPopoverMouseLeave"
      @accept="newName => handleRename(filteredFiles.find(f => f.name === hoveredFile), newName)"
      @close="closePopover"
      @conflict="handleRenameConflict"
      @error="handleRenameError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import FileRenameSuggestion from '@components/common/FileRenameSuggestion.vue';
import { extractComponentsFromMedia, generateSuggestedFilename } from '@/utils/filenameFromMediaFile';
import { useEventMessageStore } from '@/stores/eventMessage';

const props = defineProps({
  files: { type: Array, required: true },
  showCompliance: { type: Boolean, default: false },
  showFilters: { type: Boolean, default: false },
  projectId: { type: Number, default: null },
  projectName: { type: String, default: null },
  mediaStandard: { type: Object, default: null },
  projectStandard: { type: Object, default: null }
});

const emit = defineEmits(['rename']);
const eventMessageStore = useEventMessageStore();

const hoveredFile = ref(null);
const sortKey = ref('name');
const sortOrder = ref(1);
const filterType = ref('');
const filterDate = ref('');
const popoverHovered = ref(false);
const popoverCloseTimer = ref(null);
const currentPopoverStyle = ref({});

const filteredFiles = computed(() => {
  let filtered = props.files.filter(file => {
    const matchesType = !filterType.value || getExtension(file.name).toLowerCase().includes(filterType.value.toLowerCase());
    
    // Handle date filtering with proper null/invalid date checking
    let matchesDate = true;
    if (filterDate.value && file.lastModified && file.lastModified !== 'N/A' && file.lastModified !== null) {
      const fileDate = new Date(file.lastModified);
      const filterDateObj = new Date(filterDate.value);
      if (!isNaN(fileDate.getTime()) && !isNaN(filterDateObj.getTime())) {
        matchesDate = fileDate.toDateString() === filterDateObj.toDateString();
      }
    }
    
    return matchesType && matchesDate;
  });
  return filtered.sort((a, b) => {
    let aVal = a[sortKey.value];
    let bVal = b[sortKey.value];
    
    // Special handling for lastModified to handle null/invalid dates
    if (sortKey.value === 'lastModified') {
      // Treat null, undefined, 'N/A', or null as earliest date
      if (!aVal || aVal === 'N/A' || aVal === null) aVal = '1970-01-01T00:00:00.000Z';
      if (!bVal || bVal === 'N/A' || bVal === null) bVal = '1970-01-01T00:00:00.000Z';
    }
    
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
  if (!dateStr || dateStr === 'N/A' || dateStr === null) return 'N/A';
  const date = new Date(dateStr);
  // Check if the date is valid
  if (isNaN(date.getTime())) return 'N/A';
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

function handleRenameConflict(conflictData) {
  // Handle individual rename conflicts
  console.log('Individual rename conflict detected:', conflictData);
  
  // Show conflict notification to user
  eventMessageStore.addMessage('rename.conflict', 'warning', 6000);
  
  // TODO: When merge tool is implemented, collect conflicts for resolution
  // For now, just close the popover since the operation couldn't be completed
  closePopover();
}

function handleRenameError(error) {
  // Handle individual rename errors
  console.error('Individual rename error:', error);
  
  // Show error notification to user
  eventMessageStore.addMessage('rename.error', 'error', 5000);
  
  // Close the popover and could show an error notification
  closePopover();
}

function closePopover() {
  hoveredFile.value = null;
  currentPopoverStyle.value = {};
  popoverHovered.value = false;
  // Clear any pending timers
  if (popoverCloseTimer.value) {
    clearTimeout(popoverCloseTimer.value);
    popoverCloseTimer.value = null;
  }
}

function onFilenameMouseEnter(file) {
  // Clear any pending close timer
  if (popoverCloseTimer.value) {
    clearTimeout(popoverCloseTimer.value);
    popoverCloseTimer.value = null;
  }
  
  // Only show popover for non-compliant files when compliance checking is enabled
  if (props.showCompliance && file.isCompliant === false) {
    hoveredFile.value = file.name;
    currentPopoverStyle.value = calculatePopoverStyle();
  }
}

function onFilenameMouseLeave() {
  // Start a timer to close the popover, but allow time to move to the popover
  popoverCloseTimer.value = setTimeout(() => {
    if (!popoverHovered.value) {
      hoveredFile.value = null;
    }
  }, 200); // Reduced to 200ms for better responsiveness
}

function onPopoverMouseEnter() {
  // Clear the close timer when mouse enters popover
  if (popoverCloseTimer.value) {
    clearTimeout(popoverCloseTimer.value);
    popoverCloseTimer.value = null;
  }
  popoverHovered.value = true;
}

function onPopoverMouseLeave() {
  popoverHovered.value = false;
  // Small delay when leaving popover to avoid flickering
  popoverCloseTimer.value = setTimeout(() => {
    hoveredFile.value = null;
  }, 100);
}

function calculatePopoverStyle() {
  if (!hoveredFile.value) return {};
  
  const filenameSpan = document.querySelector(`[data-file="${hoveredFile.value}"] .filename-content span`);
  if (!filenameSpan) return { position: 'fixed', top: '100px', left: '100px', zIndex: 10 };
  
  const rect = filenameSpan.getBoundingClientRect();
  const popoverWidth = 280; // Estimated popover width
  const popoverHeight = 140; // Estimated popover height
  const arrowSize = 10; // Size of the arrow
  const gap = 8; // Gap between filename and popover for breathing room
  
  // Calculate viewport dimensions
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  
  // Default position: right of the filename span, vertically centered
  let left = rect.right + gap + arrowSize;
  let top = rect.top + (rect.height / 2) - (popoverHeight / 2);
  let placement = 'right';
  
  // Check if popover would go off-screen to the right
  if (left + popoverWidth > viewportWidth - 20) {
    // Position to the left of the filename span
    left = rect.left - popoverWidth - gap - arrowSize;
    placement = 'left';
  }
  
  // Check if popover would go off-screen to the left
  if (left < 20) {
    // Position above the filename span, centered horizontally
    left = rect.left + (rect.width / 2) - (popoverWidth / 2);
    top = rect.top - popoverHeight - gap - arrowSize;
    placement = 'top';
  }
  
  // Check if popover would go off-screen at the top
  if (top < 20) {
    // Position below the filename span, centered horizontally
    left = rect.left + (rect.width / 2) - (popoverWidth / 2);
    top = rect.bottom + gap + arrowSize;
    placement = 'bottom';
  }
  
  // Ensure popover doesn't go off-screen vertically when positioned left/right
  if (placement === 'left' || placement === 'right') {
    if (top < 20) {
      top = 20;
    } else if (top + popoverHeight > viewportHeight - 20) {
      top = viewportHeight - popoverHeight - 20;
    }
  }
  
  // Ensure popover doesn't go off-screen horizontally when positioned top/bottom
  if (placement === 'top' || placement === 'bottom') {
    if (left < 20) {
      left = 20;
    } else if (left + popoverWidth > viewportWidth - 20) {
      left = viewportWidth - popoverWidth - 20;
    }
  }
  
  // Calculate arrow offset for proper pointing - use span position for precision
  let arrowOffset;
  if (placement === 'top' || placement === 'bottom') {
    // For top/bottom placement, arrow should point to center of filename span
    arrowOffset = `${rect.left + (rect.width / 2) - left}px`;
  } else {
    // For left/right placement, arrow should point to vertical center of filename span
    arrowOffset = `${rect.top + (rect.height / 2) - top}px`;
  }
  
  return {
    position: 'fixed',
    top: `${top}px`,
    left: `${left}px`,
    zIndex: 1000,
    '--arrow-placement': placement,
    '--arrow-offset': arrowOffset
  };
}

const popoverStyle = computed(() => {
  return currentPopoverStyle.value;
});

function handleScroll() {
  if (hoveredFile.value) {
    currentPopoverStyle.value = calculatePopoverStyle();
  }
}

// Cleanup timers on component unmount
onUnmounted(() => {
  if (popoverCloseTimer.value) {
    clearTimeout(popoverCloseTimer.value);
  }
  // Remove scroll event listener
  window.removeEventListener('scroll', handleScroll);
});

onMounted(() => {
  // Add scroll event listener to update popover position on scroll
  window.addEventListener('scroll', handleScroll, { passive: true });
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
