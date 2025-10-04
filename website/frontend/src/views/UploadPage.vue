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
          <div class="progress-bar" :style="progressBarStyle"></div>
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
              <button class="clear-btn" @click="handleCancelUpload">
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

        <!-- Step 2: Processing (auto-advance, no back button) -->
        <div v-if="uploadStore.currentStep === 2">
          <div class="upload-progress">
            <div class="spinner"></div>
            <p>{{ $t('uploadPage.step2.processing') }}</p>
            <div class="upload-actions">
              <button class="clear-btn" @click="handleCancelUpload">
                {{ $t('uploadPage.cancel') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Step 3: Assignment -->
        <div v-if="uploadStore.currentStep === 3">
          <TierAssignmentTree
            mode="assignment"
            :extracted-tiers="uploadStore.extractedTiers"
            :existing-sections="uploadStore.existingSections"
            :tier-assignments="uploadStore.tierAssignments"
            :new-section-names="uploadStore.newSectionNames"
            :session-id="uploadStore.sessionId"
            @tier-assigned="handleTierAssignment"
            @new-section-name-updated="handleNewSectionNameUpdate"
            @section-created="handleSectionCreated"
            @section-renamed="handleSectionRenamed"
            @section-deleted="handleSectionDeleted"
          />

          <div class="upload-actions">
            <button class="clear-btn" @click="handleCancelUpload">
              {{ $t('uploadPage.cancel') }}
            </button>
            <button
              class="upload-btn"
              :disabled="!isStep3Valid"
              :title="
                !isStep3Valid
                  ? $t('uploadPage.step3.proceedDisabledTooltip', {
                      count: unassignedTiersCount,
                    })
                  : ''
              "
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

            <!-- Assignment Summary -->
            <div class="assignment-summary">
              <div class="summary-grid">
                <!-- Tiers Left to Assign -->
                <div class="summary-card">
                  <div class="card-header">
                    <div class="card-icon">
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                      </svg>
                    </div>
                    <h5 class="card-title">
                      {{ $t('uploadPage.step3.tiersLeftToAssign') }}
                    </h5>
                  </div>
                  <div class="card-value">
                    <span class="value-number">{{ unassignedTiersCount }}</span>
                    <span class="value-label">{{
                      $t('uploadPage.step3.tiers')
                    }}</span>
                  </div>
                </div>

                <!-- Production Sections Contributed -->
                <div class="summary-card">
                  <div class="card-header">
                    <div class="card-icon">
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M19 11H5M19 11C20.1046 11 21 11.8954 21 13V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V13C3 11.8954 3.89543 11 5 11M19 11V9C19 7.89543 18.1046 7 17 7M5 11V9C5 7.89543 5.89543 7 7 7M7 7V5C7 3.89543 7.89543 3 9 3H15C16.1046 3 17 3.89543 17 5V7M7 7H17"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                      </svg>
                    </div>
                    <h5 class="card-title">
                      {{ $t('uploadPage.step3.productionSections') }}
                    </h5>
                  </div>
                  <div class="card-content">
                    <div
                      v-if="productionSectionsContributed.length === 0"
                      class="empty-state"
                    >
                      <span class="empty-text">{{
                        $t('uploadPage.step3.noProductionSections')
                      }}</span>
                    </div>
                    <div v-else class="sections-list">
                      <span
                        v-for="sectionName in productionSectionsContributed"
                        :key="sectionName"
                        class="section-tag"
                      >
                        {{ sectionName }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- New Sections Created -->
                <div class="summary-card">
                  <div class="card-header">
                    <div class="card-icon">
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M12 6V12M12 12V18M12 12H18M12 12H6"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        />
                      </svg>
                    </div>
                    <h5 class="card-title">
                      {{ $t('uploadPage.step3.newSectionsCreated') }}
                    </h5>
                  </div>
                  <div class="card-content">
                    <div
                      v-if="newSectionsCreated.length === 0"
                      class="empty-state"
                    >
                      <span class="empty-text">{{
                        $t('uploadPage.step3.noNewSections')
                      }}</span>
                    </div>
                    <div v-else class="sections-list">
                      <span
                        v-for="sectionName in newSectionsCreated"
                        :key="sectionName"
                        class="section-tag new-section-tag"
                      >
                        {{ sectionName }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

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
            <button class="clear-btn" @click="handleCancelUpload">
              {{ $t('uploadPage.cancel') }}
            </button>
            <button class="clear-btn" @click="uploadStore.prevStep">
              {{ $t('uploadPage.back') }}
            </button>
            <button class="upload-btn" @click="handleConfirmUpload">
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
import UploadFolder from '@components/common/UploadFolder.vue';
import TierAssignmentTree from '@components/common/TierAssignmentTree.vue';
import '@/assets/css/upload-page.css';
import { useProjectStore } from '@/stores/project';
import { useEffectiveStandardStore } from '@/stores/effectiveStandard';
import { useNamingStandardStore } from '@/stores/namingStandard';
import { useUploadStore } from '@/stores/upload';
import { useEventMessageStore } from '@/stores/eventMessage';
import {
  isFilenameCompliant,
  clearComplianceCache,
} from '@/utils/filenameCompliance';
import {
  processUploadFiles,
  confirmUpload,
  cancelUpload,
} from '@api/service/uploadService';
import {
  fetchSectionsAndGroups,
  deleteSection,
} from '@api/service/tierService';

const loading = ref(true);
const uploadResults = ref([]);
const error = ref('');
const projectStore = useProjectStore();
const uploadStore = useUploadStore();

// Step 3: Tier Assignment

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

  // If we're already on step 3 and have extracted tiers, fetch sections
  if (
    uploadStore.currentStep === 3 &&
    uploadStore.extractedTiers.length > 0 &&
    uploadStore.selectedProject
  ) {
    await fetchExistingSections();
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

// Watch for step changes to fetch sections when entering step 3 and auto-cancel on back to step 1
// Flag to prevent duplicate cancel
const isCancelling = ref(false);

watch(
  () => uploadStore.currentStep,
  async (newStep, oldStep) => {
    // Automatically cancel if navigating back to step 1 from a higher step
    if (newStep === 1 && oldStep > 1 && !isCancelling.value) {
      await handleCancelUpload();
    }
    // Existing logic for fetching sections on step 3
    if (
      newStep === 3 &&
      uploadStore.selectedProject &&
      uploadStore.extractedTiers.length > 0
    ) {
      await fetchExistingSections();
    }
  }
);

async function fetchStandards() {
  const UPLOAD_PAGE_LOCATION_ID = 4;

  if (!uploadStore.selectedProject) {
    hasEffectiveStandard.value = false;
    return;
  }

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
    // Clear compliance cache when standard changes
    complianceCache.clear();
    clearComplianceCache();

    // Fetch media standard (location 3 = elanMedia)
    const MEDIA_LOCATION_ID = 3;
    await effectiveStandardStore.fetchEffectiveStandards(
      uploadStore.selectedProject,
      MEDIA_LOCATION_ID
    );
    const mediaStandardsObj =
      effectiveStandardStore.effectiveStandards[MEDIA_LOCATION_ID];
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
  } catch {
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
const assignedTiersCount = computed(() => {
  return Object.values(uploadStore.tierAssignments).filter(
    (assignment) => assignment && assignment !== ''
  ).length;
});

const uniqueNewSections = computed(() => {
  const newAssignments = Object.entries(uploadStore.tierAssignments)
    .filter(([, assignment]) => assignment === 'new')
    .map(([tierKey]) => tierKey);
  return [...new Set(newAssignments)];
});

// Step 3: Assignment summary computed properties
const unassignedTiersCount = computed(() => {
  return uploadStore.extractedTiers.length - assignedTiersCount.value;
});

const productionSectionsContributed = computed(() => {
  const assignedSectionIds = new Set(
    Object.values(uploadStore.tierAssignments).filter(
      (assignment) =>
        assignment &&
        typeof assignment === 'string' &&
        assignment !== '' &&
        assignment !== 'new' &&
        !assignment.startsWith('local_')
    )
  );

  return uploadStore.existingSections
    .filter((section) => assignedSectionIds.has(section.section_id))
    .map((section) => section.name)
    .sort((a, b) => a.localeCompare(b));
});

const newSectionsCreated = computed(() => {
  const localSectionIds = new Set(
    Object.values(uploadStore.tierAssignments).filter(
      (assignment) =>
        assignment &&
        typeof assignment === 'string' &&
        assignment.startsWith('local_')
    )
  );

  return uploadStore.existingSections
    .filter((section) => localSectionIds.has(section.section_id))
    .map((section) => section.name)
    .sort((a, b) => a.localeCompare(b));
});

// Step 3: Validation for proceeding to step 4
const isStep3Valid = computed(() => {
  // Check that all tiers are assigned
  const allTiersAssigned = uploadStore.extractedTiers.every((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    return (
      uploadStore.tierAssignments[tierKey] &&
      uploadStore.tierAssignments[tierKey] !== ''
    );
  });

  // Check that all new sections have names
  const allNewSectionsNamed = uniqueNewSections.value.every((sectionName) => {
    return (
      uploadStore.newSectionNames[sectionName] &&
      uploadStore.newSectionNames[sectionName].trim() !== ''
    );
  });

  return allTiersAssigned && allNewSectionsNamed;
});

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

  // Scroll to top and animate progress bar before advancing
  window.scrollTo({ top: 0, behavior: 'smooth' });
  progressBarTransitioning.value = true;
  await new Promise((resolve) => setTimeout(resolve, 1000));
  progressBarTransitioning.value = false;
  uploadStore.currentStep = 2;

  try {
    // Show processing state
    uploadStore.isProcessing = true;

    // Call the API to process files
    const response = await processUploadFiles(
      uploadStore.selectedFiles,
      uploadStore.selectedProject
    );

    // Store the results reactively
    uploadStore.extractedTiers.splice(
      0,
      uploadStore.extractedTiers.length,
      ...response.extracted_tiers
    );
    uploadStore.sessionId = response.session_id;

    // Fetch existing sections for Step 3
    await fetchExistingSections();

    // Show success message and advance to next step
    eventMessageStore.addMessage('uploadPage.step2.success', 'success', 3000, {
      count: response.extracted_tiers.length,
    });

    // Add a longer delay for user satisfaction, then scroll to top and advance
    setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      uploadStore.currentStep = 3;
    }, 900);
  } catch {
    eventMessageStore.addMessage('uploadPage.processingError', 'error');
  } finally {
    uploadStore.isProcessing = false;
  }
}
// Progress bar animation state
const progressBarTransitioning = ref(false);
const progressBarTarget = ref(null); // null = use currentStep, number = animate to this step
const progressBarStyle = computed(() => {
  let percent;
  if (progressBarTarget.value !== null) {
    percent = ((progressBarTarget.value - 1) / 3) * 100;
  } else {
    percent = ((uploadStore.currentStep - 1) / 3) * 100;
  }
  return {
    width: `${percent}%`,
    transition: progressBarTransitioning.value
      ? 'width 1s cubic-bezier(0.4,0,0.2,1)'
      : 'width 0.3s cubic-bezier(0.4,0,0.2,1)',
  };
});

// Step 3: Fetch existing tier sections
async function fetchExistingSections() {
  try {
    // Preserve local sections that were loaded from localStorage
    const preservedLocalSections = uploadStore.existingSections.filter(
      (section) =>
        section.section_id &&
        typeof section.section_id === 'string' &&
        section.section_id.startsWith('local_')
    );

    const data = await fetchSectionsAndGroups(uploadStore.selectedProject);
    const newSections = data.sections || [];

    // Ensure is_staged is boolean and set name property
    newSections.forEach((section) => {
      section.is_staged =
        section.is_staged === true ||
        section.is_staged === 'true' ||
        section.is_staged === 1 ||
        section.is_staged === '1';
      section.name = section.section_name || section.name;
      // Ensure section_id is a string for consistent comparison
      section.section_id = String(section.section_id);
    });

    // Clear assignments to sections that no longer exist or are not staged
    const validSectionIds = new Set(
      newSections.map((s) => String(s.section_id))
    );
    Object.keys(uploadStore.tierAssignments).forEach((tierKey) => {
      const assignment = uploadStore.tierAssignments[tierKey];
      if (
        assignment &&
        assignment !== 'new' &&
        !validSectionIds.has(assignment) &&
        !preservedLocalSections.some((s) => s.section_id === assignment)
      ) {
        uploadStore.tierAssignments[tierKey] = '';
      }
    });

    // Merge backend sections with preserved local sections
    uploadStore.existingSections = [...newSections, ...preservedLocalSections];
  } catch (err) {
    console.error('Error fetching existing sections:', err);
    eventMessageStore.addMessage(
      'uploadPage.step3.fetchSectionsError',
      'error'
    );
    // On error, keep the existing sections (which may include local sections from localStorage)
    // but don't modify them
  }
}

// Step 3: Handle tier assignment events
function handleTierAssignment({ tierKey, assignment }) {
  uploadStore.tierAssignments[tierKey] = assignment
    ? String(assignment)
    : assignment;
}

function handleNewSectionNameUpdate({ sectionName, newName }) {
  uploadStore.newSectionNames[sectionName] = newName;
}

function handleSectionCreated({ section }) {
  const sectionId = String(section.section_id);
  // Clear any existing assignments to this section ID to prevent conflicts from reused IDs
  Object.keys(uploadStore.tierAssignments).forEach((tierKey) => {
    if (uploadStore.tierAssignments[tierKey] === sectionId) {
      uploadStore.tierAssignments[tierKey] = '';
    }
  });
  // Add the new section to existing sections
  uploadStore.existingSections.push({ ...section, section_id: sectionId });
}

function handleSectionRenamed({ sectionId, newName }) {
  // Update the section name in existing sections
  const section = uploadStore.existingSections.find(
    (s) => s.section_id === String(sectionId)
  );
  if (section) {
    section.name = newName;
  }
}

function handleSectionDeleted({ sectionId }) {
  // Remove the section from existing sections
  const index = uploadStore.existingSections.findIndex(
    (s) => s.section_id === String(sectionId)
  );
  if (index !== -1) {
    uploadStore.existingSections.splice(index, 1);
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
  const unnamedSections = Object.entries(uploadStore.newSectionNames).filter(
    ([, name]) => {
      return !name || name.trim() === '';
    }
  );

  if (unnamedSections.length > 0) {
    eventMessageStore.addMessage(
      'uploadPage.step3.unnamedSectionsWarning',
      'warning'
    );
    return;
  }

  // Store the new section names in the assignments (already in store)
  // uploadStore.newSectionNames = { ...uploadStore.newSectionNames };

  // Scroll to top and proceed to step 4 after a short delay for satisfaction
  setTimeout(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    uploadStore.nextStep();
  }, 400);
}

async function handleConfirmUpload() {
  try {
    // Call the confirmation API using the service
    await confirmUpload(
      uploadStore.sessionId,
      uploadStore.tierAssignments,
      uploadStore.newSectionNames,
      uploadStore.description
    );

    // Show success message
    eventMessageStore.addMessage('uploadPage.step4.success', 'success', 5000);

    // Reset the upload store to clear all data
    uploadStore.reset();

    // Optionally redirect to a success page or contributions page
    // router.push('/contributions');
  } catch {
    eventMessageStore.addMessage('uploadPage.step4.error', 'error');
  }
}

async function handleCancelUpload() {
  if (isCancelling.value) return;
  isCancelling.value = true;
  // Always scroll to top and animate progress bar back to step 1
  window.scrollTo({ top: 0, behavior: 'smooth' });
  progressBarTarget.value = 1;
  progressBarTransitioning.value = true;
  // Wait for the animation
  await new Promise((resolve) => setTimeout(resolve, 1000));
  progressBarTransitioning.value = false;
  progressBarTarget.value = null;
  uploadStore.currentStep = 1;

  // Show success message after animation completes
  setTimeout(() => {
    eventMessageStore.addMessage('uploadPage.cancel.success', 'info', 3000);
    isCancelling.value = false;
  }, 0);

  if (!uploadStore.sessionId) {
    // If no session, just reset the store
    uploadStore.reset();
    return;
  }

  try {
    // Delete any staged sections created during this upload session
    const stagedSections = uploadStore.existingSections.filter(
      (section) => section.is_staged
    );
    for (const section of stagedSections) {
      try {
        await deleteSection(section.section_id, true);
      } catch {
        // Continue with other deletions even if deletion fails
      }
    }

    // Call the cancel API using the service
    await cancelUpload(uploadStore.sessionId);

    // Reset the upload store to clear all data
    uploadStore.reset();
    return;
  } catch {
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
.new-section-section h4 {
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
  margin-top: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow:
    0 4px 6px -1px rgb(0 0 0 / 10%),
    0 2px 4px -2px rgb(0 0 0 / 10%);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 8px;
}

.summary-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px -8px rgb(0 0 0 / 15%);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 10px;
  color: white;
  flex-shrink: 0;
}

.card-title {
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.card-value {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.value-number {
  font-size: 2.5rem;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}

.value-label {
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
}

.card-content {
  min-height: 60px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
}

.empty-text {
  color: #9ca3af;
  font-size: 0.875rem;
  font-style: italic;
}

.sections-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 60px;
  align-items: flex-start;
  align-content: flex-start;
}

.section-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.section-tag:hover {
  background: #e2e8f0;
  transform: translateY(-1px);
}

.new-section-tag {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #92400e;
  border-color: #f59e0b;
}

.new-section-tag:hover {
  background: linear-gradient(135deg, #fde68a, #fcd34d);
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
