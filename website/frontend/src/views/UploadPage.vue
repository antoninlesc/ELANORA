<template>
  <div>
    <div class="upload-page-root">
      <h1 class="upload-title">{{ $t('uploadPage.title') }}</h1>

      <!-- Custom Stepper -->
      <div class="stepper">
        <div class="stepper-header">
          <div
            v-for="step in 4"
            :key="step"
            class="step"
            :class="{
              active: uploadStore.currentStep === step,
              completed: uploadStore.currentStep > step,
            }"
          >
            <div class="step-circle">{{ step }}</div>
            <div class="step-label">
              {{ $t(`uploadPage.step${step}.label`) }}
            </div>
          </div>
        </div>
        <div class="stepper-progress">
          <div
            class="progress-bar"
            :style="{ width: `${((uploadStore.currentStep - 1) / 3) * 100}%` }"
          ></div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="step-content">
        <!-- Step 1: Project Selection and Upload -->
        <div v-if="uploadStore.currentStep === 1">
          <!-- Project Selection -->
          <div class="project-selection">
            <label for="projectSelect" class="project-label">{{
              $t('uploadPage.projectSelection.label')
            }}</label>
            <select
              id="projectSelect"
              v-model="uploadStore.selectedProject"
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
          <div v-if="uploadStore.selectedProject">
            <UploadFolder
              v-model="uploadStore.selectedFiles"
              :title="$t('uploadPage.uploadZone.title')"
              :subtitle="$t('uploadPage.uploadZone.subtitle')"
              :files-with-compliance="filesWithCompliance"
              :standard="standard"
              :media-standard="mediaStandard"
              :enable-media-extraction="true"
              @rename-file="handleFileRename"
            />

            <!-- Upload Actions -->
            <div
              v-if="uploadStore.selectedFiles.length > 0"
              class="upload-actions"
            >
              <button
                class="upload-btn"
                :disabled="!uploadStore.isStepValid"
                @click="proceedToStep2"
              >
                {{ $t('uploadPage.step1.next') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Step 2: Processing -->
        <div v-if="uploadStore.currentStep === 2">
          <div v-if="uploadStore.isProcessing" class="upload-progress">
            <div class="spinner"></div>
            <p>{{ $t('uploadPage.step2.processing') }}</p>
          </div>
          <div v-else>
            <!-- Display extracted tiers (add logic later) -->
            <p>{{ $t('uploadPage.step2.completed') }}</p>
            <div class="upload-actions">
              <button class="clear-btn" @click="uploadStore.prevStep">
                {{ $t('uploadPage.back') }}
              </button>
              <button class="upload-btn" @click="uploadStore.nextStep">
                {{ $t('uploadPage.step2.next') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Step 3: Assignment -->
        <div v-if="uploadStore.currentStep === 3">
          <!-- Placeholder for tier assignment UI -->
          <p>{{ $t('uploadPage.step3.placeholder') }}</p>
          <div class="upload-actions">
            <button class="clear-btn" @click="uploadStore.prevStep">
              {{ $t('uploadPage.back') }}
            </button>
            <button
              class="upload-btn"
              :disabled="!uploadStore.isStepValid"
              @click="uploadStore.nextStep"
            >
              {{ $t('uploadPage.step3.next') }}
            </button>
          </div>
        </div>

        <!-- Step 4: Confirm -->
        <div v-if="uploadStore.currentStep === 4">
          <textarea
            v-model="uploadStore.description"
            :placeholder="$t('uploadPage.step4.placeholder')"
            class="description-textarea"
          ></textarea>
          <div class="upload-actions">
            <button class="clear-btn" @click="uploadStore.prevStep">
              {{ $t('uploadPage.back') }}
            </button>
            <button
              class="upload-btn"
              :disabled="!uploadStore.isStepValid"
              @click="confirmUpload"
            >
              {{ $t('uploadPage.step4.confirm') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Upload Results (if needed in later steps) -->
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
import UploadFolder from '@/components/common/UploadFolder.vue';
import '@/assets/css/upload-page.css';
import { useProjectStore } from '@/stores/project';
import { useEffectiveStandardStore } from '@/stores/effectiveStandard';
import { useNamingStandardStore } from '@/stores/namingStandard';
import {
  isFilenameCompliant,
  clearComplianceCache,
} from '@/utils/filenameCompliance';
import { useEventMessageStore } from '@/stores/eventMessage';
import { useUploadStore } from '@/stores/upload';
import { processUploadFiles } from '@/api/service/uploadService';

const loading = ref(true);
const uploadResults = ref([]);
const error = ref('');
const projectStore = useProjectStore();
const uploadStore = useUploadStore();

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

// Computed for Projects from Store
const projects = computed(() => projectStore.projects || []);

onMounted(async () => {
  // Ensure store is initialized (loads from localStorage if needed)
  projectStore.initializeFromStorage();

  // Sync initial project selection
  if (projectStore.currentProject) {
    uploadStore.selectedProject =
      projectStore.currentProject.project_id.toString();
  }

  // Initial fetch if a project is selected
  if (uploadStore.selectedProject) {
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
watch(
  () => uploadStore.selectedProject,
  async (newProjectId, oldProjectId) => {
    if (!isInitialLoad.value && newProjectId && newProjectId !== oldProjectId) {
      // Update project store when upload store project changes
      const project = projectStore.projects.find(
        (p) => p.project_id === parseInt(newProjectId)
      );
      if (project) {
        projectStore.setCurrentProject(project);
      }
      await fetchStandards();
    } else if (!newProjectId) {
      // Reset if no project selected
      hasEffectiveStandard.value = false;
      standard.value = null;
      mediaStandard.value = null;
    }
  }
);

// Watch for project store changes and sync to upload store
watch(
  () => projectStore.currentProject,
  (newProject) => {
    if (
      !isInitialLoad.value &&
      newProject &&
      newProject.project_id !== parseInt(uploadStore.selectedProject)
    ) {
      uploadStore.selectedProject = newProject.project_id.toString();
    }
  }
);

async function fetchStandards() {
  const UPLOAD_PAGE_LOCATION_ID = 4;

  if (!uploadStore.selectedProject) {
    console.warn('UploadPage: No project selected, skipping standards fetch');
    hasEffectiveStandard.value = false;
    return;
  }

  console.log(
    'UploadPage: Fetching standards for project:',
    uploadStore.selectedProject
  );

  try {
    await effectiveStandardStore.fetchEffectiveStandards(
      uploadStore.selectedProject,
      UPLOAD_PAGE_LOCATION_ID
    );
    await namingStandardStore.fetchStandardsAndComponentNames(
      uploadStore.selectedProject
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
      uploadStore.selectedProject,
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
    return uploadStore.selectedFiles.map((file) => ({
      ...file,
      isCompliant: true,
    }));
  }

  // Use cached compliance results if available
  return uploadStore.selectedFiles.map((file) => {
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

function handleFileRename({ file, index, newName }) {
  // Update the filename in the selectedFiles array
  if (uploadStore.selectedFiles[index]) {
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

    uploadStore.selectedFiles[index] = updatedFile;

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

async function proceedToStep2() {
  // Check for non-compliant files and show event message
  const nonCompliantFiles = filesWithCompliance.value.filter(
    (f) => !f.isCompliant
  );
  if (nonCompliantFiles.length > 0) {
    eventMessageStore.addMessage('uploadPage.complianceWarning', 'warning');
    return;
  }

  try {
    // Show processing state
    uploadStore.isProcessing = true;

    // Call the API to process files
    const response = await processUploadFiles(
      uploadStore.selectedFiles,
      uploadStore.selectedProject
    );

    // Store the results
    uploadStore.extractedTiers = response.extracted_tiers;
    uploadStore.sessionId = response.session_id;

    // Move to step 3
    uploadStore.nextStep();
  } catch (err) {
    console.error('Error processing upload files:', err);
    eventMessageStore.addMessage('uploadPage.processingError', 'error');
  } finally {
    uploadStore.isProcessing = false;
  }
}

async function confirmUpload() {
  // Implement confirmation logic (e.g., send to backend, reset store)
  uploadStore.reset();
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
