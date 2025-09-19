<template>
  <div>
    <div class="upload-page-root">
      <h1 class="upload-title">{{ $t('uploadPage.title') }}</h1>

      <!-- Project Selection -->
      <div class="project-selection">
        <label for="projectSelect" class="project-label">{{
          $t('uploadPage.projectSelection.label')
        }}</label>
        <select
          id="projectSelect"
          v-model="selectedProject"
          class="project-select"
          :disabled="loading"
        >
          <option value="">
            {{ $t('uploadPage.projectSelection.placeholder') }}
          </option>
          <option
            v-for="project in projects"
            :key="project.project_id"
            :value="project.project_id"
          >
            {{ project.project_name }}
          </option>
        </select>
      </div>

      <!-- Upload Component -->
      <div v-if="selectedProject">
        <UploadFolder
          v-model="selectedFiles"
          :title="$t('uploadPage.uploadZone.title')"
          :subtitle="$t('uploadPage.uploadZone.subtitle')"
          :files-with-compliance="filesWithCompliance"
          :standard="standard"
          :media-standard="mediaStandard"
          :enable-media-extraction="true"
          @rename-file="handleFileRename"
        />

        <!-- Upload Actions -->
        <div v-if="selectedFiles.length > 0" class="upload-actions">
          <button
            class="upload-btn"
            :disabled="uploading || selectedFiles.length === 0"
            @click="uploadFiles"
          >
            <span v-if="uploading" class="spinner"></span>
            {{
              uploading
                ? $t('uploadPage.uploadingFiles', {
                    count: selectedFiles.length,
                  })
                : $t('uploadPage.uploadButton')
            }}
          </button>
        </div>
      </div>

      <!-- Upload Results -->
      <div v-if="uploadResults.length > 0" class="upload-results">
        <h3>{{ $t('uploadPage.uploadResults') }}</h3>
        <div class="results-list">
          <div
            v-for="result in uploadResults"
            :key="result.filename"
            class="result-item"
            :class="{ success: result.success, error: !result.success }"
          >
            <span class="result-filename">{{ result.filename }}</span>
            <span class="result-status">
              {{
                result.success
                  ? $t('uploadPage.resultSuccess')
                  : $t('uploadPage.resultFailed')
              }}
            </span>
            <span v-if="result.error" class="result-error">{{
              result.error
            }}</span>
          </div>
        </div>
      </div>

      <!-- Error Messages -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import UploadFolder from '@/components/common/UploadFolder.vue';
import gitService from '@/api/service/gitService';
import '@/assets/css/upload-page.css';
import { useUserStore } from '@/stores/user';
import { useProjectStore } from '@/stores/project';
import { useEffectiveStandardStore } from '@/stores/effectiveStandard';
import { useNamingStandardStore } from '@/stores/namingStandard';
import {
  isFilenameCompliant,
  clearComplianceCache,
} from '@/utils/filenameCompliance';
import { useEventMessageStore } from '@/stores/eventMessage';

const { t } = useI18n();
const selectedProject = ref('');
const selectedFiles = ref([]);
const uploading = ref(false);
const loading = ref(true);
const uploadResults = ref([]);
const error = ref('');
const userStore = useUserStore();
const projectStore = useProjectStore();

// Stores and Composables
const effectiveStandardStore = useEffectiveStandardStore();
const namingStandardStore = useNamingStandardStore();
const eventMessageStore = useEventMessageStore();

// State for Standards
const hasEffectiveStandard = ref(false);
const standard = ref(null);
const mediaStandard = ref(null);

// Compliance cache to avoid re-computing for the same filenames
const complianceCache = new Map();

// Flag to prevent duplicate fetch on initial load
const isInitialLoad = ref(true);

// Computed for Username from User Store
const username = computed(() => userStore.user?.username || '');

// Computed for Projects from Store
const projects = computed(() => projectStore.projects || []);

onMounted(async () => {
  // Ensure store is initialized (loads from localStorage if needed)
  projectStore.initializeFromStorage();

  // Set default selected project to current active project's ID
  selectedProject.value = projectStore.currentProject?.project_id || '';

  // Initial fetch if a project is selected
  if (selectedProject.value) {
    await fetchStandards();
  }

  // Mark initial load as complete to allow watcher fetches
  isInitialLoad.value = false;

  // Set loading to false after standards are fetched
  loading.value = false;
  // Initialize Broadcast Channel for project updates
  projectStore.initBroadcastChannel();
});

// Updated: Watcher to fetch standards only after initial load
watch(selectedProject, async (newProjectId, oldProjectId) => {
  if (!isInitialLoad.value && newProjectId && newProjectId !== oldProjectId) {
    await fetchStandards();
  } else if (!newProjectId) {
    // Reset if no project selected
    hasEffectiveStandard.value = false;
    standard.value = null;
    mediaStandard.value = null;
  }
});

async function fetchStandards() {
  const UPLOAD_PAGE_LOCATION_ID = 4;

  if (!selectedProject.value) {
    console.warn('UploadPage: No project selected, skipping standards fetch');
    hasEffectiveStandard.value = false;
    return;
  }

  console.log(
    'UploadPage: Fetching standards for project:',
    selectedProject.value
  );

  try {
    await effectiveStandardStore.fetchEffectiveStandards(
      selectedProject.value,
      UPLOAD_PAGE_LOCATION_ID
    );
    await namingStandardStore.fetchStandardsAndComponentNames(
      selectedProject.value
    );

    // Get the standard ID
    let standardId;
    const standardsObj =
      effectiveStandardStore.effectiveStandards[UPLOAD_PAGE_LOCATION_ID];
    console.log(
      'UploadPage: Effective standards for location 4:',
      standardsObj
    );

    if (standardsObj && typeof standardsObj === 'object') {
      const ids = Object.values(standardsObj).filter((id) => !!id);
      standardId = ids.length > 0 ? ids[0] : undefined;
    } else if (
      typeof standardsObj === 'string' ||
      typeof standardsObj === 'number'
    ) {
      standardId = standardsObj;
    }

    hasEffectiveStandard.value = !!standardId;
    standard.value = namingStandardStore.standards.find(
      (std) => std.id === standardId
    );
    console.log('UploadPage: Found standard:', standard.value);

    // Clear compliance cache when standard changes
    complianceCache.clear();
    clearComplianceCache();

    // Fetch media standard (location 3 = elanMedia)
    const MEDIA_LOCATION_ID = 3;
    console.log('UploadPage: Fetching media standards for location 3');
    await effectiveStandardStore.fetchEffectiveStandards(
      selectedProject.value,
      MEDIA_LOCATION_ID
    );
    const mediaStandardsObj =
      effectiveStandardStore.effectiveStandards[MEDIA_LOCATION_ID];
    console.log(
      'UploadPage: Effective standards for location 3:',
      mediaStandardsObj
    );

    let mediaStandardId;
    if (mediaStandardsObj && typeof mediaStandardsObj === 'object') {
      const ids = Object.values(mediaStandardsObj).filter((id) => !!id);
      mediaStandardId = ids.length > 0 ? ids[0] : undefined;
    } else if (
      typeof mediaStandardsObj === 'string' ||
      typeof mediaStandardsObj === 'number'
    ) {
      mediaStandardId = mediaStandardsObj;
    }

    mediaStandard.value = namingStandardStore.standards.find(
      (std) => std.id === mediaStandardId
    );
    console.log('UploadPage: Found media standard:', mediaStandard.value);
  } catch (e) {
    console.error('UploadPage: Error fetching standards:', e);
    hasEffectiveStandard.value = false;
  }
}

// Computed for Files with Compliance
const filesWithCompliance = computed(() => {
  if (!hasEffectiveStandard.value || !standard.value) {
    return selectedFiles.value.map((file) => ({ ...file, isCompliant: true }));
  }

  // Use cached compliance results if available
  return selectedFiles.value.map((file) => {
    const cached = complianceCache.get(file.name);
    if (cached !== undefined) {
      return { ...file, isCompliant: cached };
    }

    // Compute compliance and cache it
    const isCompliant = isFilenameCompliant(standard.value, file.name);
    complianceCache.set(file.name, isCompliant);
    return { ...file, isCompliant };
  });
});

// UploadFiles to show event message and prevent upload for non-compliant files
async function uploadFiles() {
  if (!selectedProject.value || selectedFiles.value.length === 0) {
    error.value = t('uploadPage.errors.selectProjectAndFiles');
    return;
  }

  // Check for non-compliant files and show event message
  const nonCompliantFiles = filesWithCompliance.value.filter(
    (f) => !f.isCompliant
  );
  if (nonCompliantFiles.length > 0) {
    eventMessageStore.addMessage('uploadPage.complianceWarning', 'warning');
    return;
  }

  uploading.value = true;
  uploadResults.value = [];
  error.value = '';

  try {
    const response = await gitService.uploadElanFiles(
      selectedProject.value,
      selectedFiles.value,
      username.value
    );

    uploadResults.value = response.files || [];
    selectedFiles.value = [];
  } catch (e) {
    error.value =
      e?.response?.data?.detail || t('uploadPage.errors.uploadFailed');
    console.error('Upload error:', e);
  } finally {
    uploading.value = false;
  }
}

function handleFileRename({ file, index, newName }) {
  // Update the filename in the selectedFiles array
  if (selectedFiles.value[index]) {
    // Create a new File object with the updated name
    const updatedFile = new File([file], newName, {
      type: file.type,
      lastModified: file.lastModified,
    });

    // Preserve webkitRelativePath if it exists
    if (file.webkitRelativePath) {
      Object.defineProperty(updatedFile, 'webkitRelativePath', {
        value: file.webkitRelativePath.replace(file.name, newName),
        writable: false,
      });
    }

    selectedFiles.value[index] = updatedFile;

    // Clear cache for the old filename and add cache for new filename
    complianceCache.delete(file.name);
    complianceCache.set(newName, isFilenameCompliant(standard.value, newName));

    // Show success message
    eventMessageStore.addMessage('uploadPage.fileRenamed', 'success', 3000, {
      oldName: file.name,
      newName: newName,
    });
  }
}
</script>

<style scoped>
.upload-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.upload-btn {
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-btn:hover:not(:disabled) {
  background: #1565c0;
}

.spinner {
  width: 16px;
  height: 16px;
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
