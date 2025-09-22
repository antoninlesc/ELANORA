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
              <button class="clear-btn" @click="cancelUpload">
                {{ $t('uploadPage.cancel') }}
              </button>
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
              <button class="clear-btn" @click="cancelUpload">
                {{ $t('uploadPage.cancel') }}
              </button>
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
          <div class="assignment-section">
            <h3>{{ $t('uploadPage.step3.title') }}</h3>
            <p class="assignment-description">
              {{ $t('uploadPage.step3.description') }}
            </p>

            <!-- Extracted Tiers List -->
            <div class="tiers-section">
              <h4>{{ $t('uploadPage.step3.extractedTiers') }}</h4>
              <div class="tiers-list">
                <div
                  v-for="tier in uploadStore.extractedTiers"
                  :key="tier.tier_id || tier.tier_name"
                  class="tier-item"
                >
                  <div class="tier-info">
                    <span class="tier-name">{{ tier.tier_name }}</span>
                    <span v-if="tier.parent_tier_name" class="tier-parent">
                      ({{ $t('uploadPage.step3.parentTier') }}:
                      {{ tier.parent_tier_name }})
                    </span>
                    <span class="tier-file">{{ tier.file_name }}</span>
                  </div>

                  <!-- Assignment Dropdown -->
                  <select
                    v-model="
                      uploadStore.tierAssignments[
                        tier.tier_id || tier.tier_name
                      ]
                    "
                    class="tier-assignment-select"
                  >
                    <option value="">
                      {{ $t('uploadPage.step3.selectSection') }}
                    </option>
                    <option
                      v-for="section in existingSections"
                      :key="section.section_id"
                      :value="section.section_id"
                    >
                      {{ section.name }}
                    </option>
                    <option value="new">
                      {{ $t('uploadPage.step3.createNewSection') }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- New Section Creation -->
            <div v-if="hasNewSectionAssignments" class="new-section-section">
              <h4>{{ $t('uploadPage.step3.newSections') }}</h4>
              <div class="new-sections-list">
                <div
                  v-for="sectionName in uniqueNewSections"
                  :key="sectionName"
                  class="new-section-item"
                >
                  <label class="new-section-label">
                    {{ $t('uploadPage.step3.sectionName') }}:
                    <input
                      v-model="newSectionNames[sectionName]"
                      :placeholder="
                        $t('uploadPage.step3.sectionNamePlaceholder')
                      "
                      class="new-section-input"
                      type="text"
                    />
                  </label>
                  <div class="assigned-tiers">
                    <span class="assigned-tiers-label">
                      {{ $t('uploadPage.step3.assignedTiersLabel') }}:
                    </span>
                    <span class="assigned-tiers-list">
                      {{
                        getTiersForNewSection(sectionName)
                          .map((t) => t.tier_name)
                          .join(', ')
                      }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Assignment Summary -->
            <div class="assignment-summary">
              <h4>{{ $t('uploadPage.step3.summary') }}</h4>
              <div class="summary-stats">
                <div class="stat-item">
                  <span class="stat-label"
                    >{{ $t('uploadPage.step3.totalTiers') }}:</span
                  >
                  <span class="stat-value">{{
                    uploadStore.extractedTiers.length
                  }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label"
                    >{{ $t('uploadPage.step3.assignedTiersCount') }}:</span
                  >
                  <span class="stat-value">{{ assignedTiersCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label"
                    >{{ $t('uploadPage.step3.newSectionsCount') }}:</span
                  >
                  <span class="stat-value">{{ uniqueNewSections.length }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="upload-actions">
            <button class="clear-btn" @click="cancelUpload">
              {{ $t('uploadPage.cancel') }}
            </button>
            <button class="clear-btn" @click="uploadStore.prevStep">
              {{ $t('uploadPage.back') }}
            </button>
            <button
              class="upload-btn"
              :disabled="!uploadStore.isStepValid"
              @click="proceedToStep4"
            >
              {{ $t('uploadPage.step3.next') }}
            </button>
          </div>
        </div>

        <!-- Step 4: Confirm -->
        <div v-if="uploadStore.currentStep === 4">
          <div class="confirmation-section">
            <h3>{{ $t('uploadPage.step4.title') }}</h3>
            <p class="confirmation-description">
              {{ $t('uploadPage.step4.description') }}
            </p>

            <div class="upload-summary">
              <h4>{{ $t('uploadPage.step4.summary') }}</h4>
              <div class="summary-details">
                <div class="summary-item">
                  <span class="summary-label"
                    >{{ $t('uploadPage.projectSelection.label') }}:</span
                  >
                  <span class="summary-value">{{
                    getProjectName(uploadStore.selectedProject)
                  }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label"
                    >{{ $t('uploadPage.step2.completed') }}:</span
                  >
                  <span class="summary-value"
                    >{{ uploadStore.extractedTiers.length }}
                    {{ $t('uploadPage.step3.extractedTiers') }}</span
                  >
                </div>
                <div class="summary-item">
                  <span class="summary-label"
                    >{{ $t('uploadPage.step3.assignedTiersCount') }}:</span
                  >
                  <span class="summary-value">{{ assignedTiersCount }}</span>
                </div>
                <div v-if="uniqueNewSections.length > 0" class="summary-item">
                  <span class="summary-label"
                    >{{ $t('uploadPage.step3.newSectionsCount') }}:</span
                  >
                  <span class="summary-value">{{
                    uniqueNewSections.length
                  }}</span>
                </div>
              </div>
            </div>

            <textarea
              v-model="uploadStore.description"
              :placeholder="$t('uploadPage.step4.placeholder')"
              class="description-textarea"
            ></textarea>
          </div>

          <div class="upload-actions">
            <button class="clear-btn" @click="cancelUpload">
              {{ $t('uploadPage.cancel') }}
            </button>
            <button class="clear-btn" @click="uploadStore.prevStep">
              {{ $t('uploadPage.back') }}
            </button>
            <button class="upload-btn" @click="confirmUpload">
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

// Step 3: Tier Assignment
const existingSections = ref([]);
const newSectionNames = ref({});

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

// Step 3: Computed properties for tier assignment
const hasNewSectionAssignments = computed(() => {
  return Object.values(uploadStore.tierAssignments).some(
    (assignment) => assignment === 'new'
  );
});

const uniqueNewSections = computed(() => {
  const newAssignments = Object.entries(uploadStore.tierAssignments)
    .filter(([, assignment]) => assignment === 'new')
    .map(([tierKey]) => tierKey);
  return [...new Set(newAssignments)];
});

const assignedTiersCount = computed(() => {
  return Object.values(uploadStore.tierAssignments).filter(
    (assignment) => assignment && assignment !== ''
  ).length;
});

const getTiersForNewSection = (sectionName) => {
  return uploadStore.extractedTiers.filter((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    return (
      uploadStore.tierAssignments[tierKey] === 'new' && tierKey === sectionName
    );
  });
};

// Helper function to get project name
const getProjectName = (projectId) => {
  if (!projectId) return '';
  const project = projects.value.find(
    (p) => p.project_id === parseInt(projectId)
  );
  return project ? project.project_name : projectId;
};

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

    // Fetch existing sections for Step 3
    await fetchExistingSections();

    // Move to step 3
    uploadStore.nextStep();
  } catch (err) {
    console.error('Error processing upload files:', err);
    eventMessageStore.addMessage('uploadPage.processingError', 'error');
  } finally {
    uploadStore.isProcessing = false;
  }
}

// Step 3: Fetch existing tier sections
async function fetchExistingSections() {
  try {
    const response = await fetch(
      `/api/v1/tier/${uploadStore.selectedProject}/sections`
    );
    if (!response.ok) {
      throw new Error('Failed to fetch sections');
    }
    const data = await response.json();
    existingSections.value = data.sections || [];
  } catch (err) {
    console.error('Error fetching existing sections:', err);
    eventMessageStore.addMessage(
      'uploadPage.step3.fetchSectionsError',
      'error'
    );
    existingSections.value = [];
  }
}

// Step 3: Proceed to Step 4
async function proceedToStep4() {
  // Validate that all tiers are assigned
  const unassignedTiers = uploadStore.extractedTiers.filter((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    return (
      !uploadStore.tierAssignments[tierKey] ||
      uploadStore.tierAssignments[tierKey] === ''
    );
  });

  if (unassignedTiers.length > 0) {
    eventMessageStore.addMessage(
      'uploadPage.step3.unassignedTiersWarning',
      'warning'
    );
    return;
  }

  // Validate that new sections have names
  const unnamedSections = uniqueNewSections.value.filter((sectionName) => {
    return (
      !newSectionNames.value[sectionName] ||
      newSectionNames.value[sectionName].trim() === ''
    );
  });

  if (unnamedSections.length > 0) {
    eventMessageStore.addMessage(
      'uploadPage.step3.unnamedSectionsWarning',
      'warning'
    );
    return;
  }

  // Store the new section names in the assignments
  uploadStore.newSectionNames = { ...newSectionNames.value };

  // Proceed to step 4
  uploadStore.nextStep();
}

async function confirmUpload() {
  try {
    // Prepare form data for the API call
    const formData = new FormData();
    formData.append('session_id', uploadStore.sessionId);
    formData.append(
      'tier_assignments',
      JSON.stringify(uploadStore.tierAssignments)
    );
    formData.append(
      'new_section_names',
      JSON.stringify(uploadStore.newSectionNames)
    );
    formData.append('description', uploadStore.description);

    // Call the confirmation API
    const response = await fetch('/api/v1/upload/confirm', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to confirm upload');
    }

    // Parse response (not used currently but good practice)
    await response.json();

    // Show success message
    eventMessageStore.addMessage('uploadPage.step4.success', 'success', 5000);

    // Reset the upload store to clear all data
    uploadStore.reset();

    // Optionally redirect to a success page or contributions page
    // router.push('/contributions');
  } catch (err) {
    console.error('Error confirming upload:', err);
    eventMessageStore.addMessage('uploadPage.step4.error', 'error');
  }
}

async function cancelUpload() {
  if (!uploadStore.sessionId) {
    // If no session, just reset the store
    uploadStore.reset();
    eventMessageStore.addMessage('uploadPage.cancel.success', 'info', 3000);
    return;
  }

  try {
    // Prepare form data for the cancel API call
    const formData = new FormData();
    formData.append('session_id', uploadStore.sessionId);

    // Call the cancel API
    const response = await fetch('/api/v1/upload/cancel', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to cancel upload');
    }

    // Show success message
    eventMessageStore.addMessage('uploadPage.cancel.success', 'info', 3000);

    // Reset the upload store to clear all data
    uploadStore.reset();
  } catch (err) {
    console.error('Error cancelling upload:', err);
    eventMessageStore.addMessage('uploadPage.cancel.error', 'error');
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

/* Step 3: Assignment Styles */
.assignment-section {
  max-width: 800px;
  margin: 0 auto;
}

.assignment-description {
  color: #666;
  margin-bottom: 24px;
  line-height: 1.5;
}

.tiers-section h4,
.new-section-section h4,
.assignment-summary h4 {
  color: #333;
  margin-bottom: 16px;
  font-size: 1.1rem;
}

.tiers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.tier-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.tier-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tier-name {
  font-weight: 600;
  color: #333;
}

.tier-parent {
  font-size: 0.9rem;
  color: #666;
}

.tier-file {
  font-size: 0.8rem;
  color: #999;
}

.tier-assignment-select {
  min-width: 200px;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}

.new-sections-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.new-section-item {
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.new-section-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.new-section-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  margin-bottom: 12px;
}

.assigned-tiers {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.assigned-tiers-label {
  font-weight: 600;
  color: #555;
}

.assigned-tiers-list {
  color: #666;
  font-size: 0.9rem;
}

.assignment-summary {
  margin-top: 24px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-weight: 600;
  color: #555;
}

.stat-value {
  font-weight: 700;
  color: #1976d2;
}

/* Step 4: Confirmation Styles */
.confirmation-section {
  max-width: 600px;
  margin: 0 auto;
}

.confirmation-description {
  color: #666;
  margin-bottom: 24px;
  line-height: 1.5;
}

.upload-summary {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.upload-summary h4 {
  color: #333;
  margin-bottom: 16px;
  font-size: 1.1rem;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.summary-label {
  font-weight: 600;
  color: #555;
}

.summary-value {
  color: #333;
}

.description-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.4;
}

.description-textarea:focus {
  outline: none;
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgb(25 118 210 / 20%);
}
</style>
