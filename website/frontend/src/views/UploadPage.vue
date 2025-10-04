<template>
  <div>
    <div class="upload-page-root">
      <h1 class="upload-title">{{ $t('uploadPage.title') }}</h1>

      <!-- Custom Stepper -->
      <div class="upload-page-stepper">
        <div class="upload-page-stepper-header">
          <div
            v-for="step in 4"
            :key="step"
            class="upload-page-step"
            :class="{
              'upload-page-active': uploadStore.currentStep === step,
              'upload-page-completed': uploadStore.currentStep > step,
            }"
          >
            <div class="upload-page-step-circle">{{ step }}</div>
            <div class="upload-page-step-label">
              {{ $t(`uploadPage.step${step}.label`) }}
            </div>
          </div>
        </div>
        <div class="upload-page-stepper-progress">
          <div class="upload-page-progress-bar" :style="progressBarStyle"></div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="step-content">
        <!-- Step 1: Project Selection and Upload -->
        <div v-if="uploadStore.currentStep === 1">
          <!-- Project Selection -->
          <div class="upload-page-project-selection">
            <label for="projectSelect" class="upload-page-project-label">{{
              $t('uploadPage.projectSelection.label')
            }}</label>
            <select
              id="projectSelect"
              v-model="uploadStore.selectedProject"
              class="upload-page-project-select"
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
                class="upload-page-btn-cancel"
                @click="handleCancelUpload"
              >
                <font-awesome-icon icon="fa-solid fa-xmark" />
                {{ $t('uploadPage.cancelButton') }}
              </button>
              <button
                class="upload-page-btn-primary"
                :disabled="!uploadStore.isStepValid"
                @click="proceedToStep2"
              >
                {{ $t('uploadPage.step1.next') }}
                <font-awesome-icon icon="fa-solid fa-arrow-right" />
              </button>
            </div>
          </div>
        </div>

        <!-- Step 2: Processing (auto-advance, no back button) -->
        <div v-if="uploadStore.currentStep === 2">
          <div class="upload-progress">
            <div class="upload-page-spinner"></div>
            <p>{{ $t('uploadPage.step2.processing') }}</p>
            <div class="upload-actions">
              <button
                class="upload-page-btn-cancel"
                @click="handleCancelUpload"
              >
                <font-awesome-icon icon="fa-solid fa-xmark" />
                {{ $t('uploadPage.cancelButton') }}
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
            <button class="upload-page-btn-cancel" @click="handleCancelUpload">
              <font-awesome-icon icon="fa-solid fa-xmark" />
              {{ $t('uploadPage.cancelButton') }}
            </button>
            <button
              class="upload-page-btn-primary"
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
              <font-awesome-icon icon="fa-solid fa-arrow-right" />
            </button>
          </div>
        </div>

        <!-- Step 4: Confirm -->
        <div v-if="uploadStore.currentStep === 4">
          <div class="upload-page-step4-container">
            <!-- Header -->
            <div class="upload-page-step4-header">
              <h2 class="upload-page-step4-title">
                {{ $t('uploadPage.step4.title') }}
              </h2>
              <p class="upload-page-step4-subtitle">
                {{ $t('uploadPage.step4.description') }}
              </p>
            </div>

            <!-- Project Info Card -->
            <div class="upload-page-recap-card upload-page-project-card">
              <div class="upload-page-card-icon-large">
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M3 7C3 5.89543 3.89543 5 5 5H9.58579C9.851 5 10.1054 5.10536 10.2929 5.29289L12 7H19C20.1046 7 21 7.89543 21 9V17C21 18.1046 20.1046 19 19 19H5C3.89543 19 3 18.1046 3 17V7Z"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
              <div class="upload-page-project-info">
                <span class="upload-page-project-label">{{
                  $t('uploadPage.step4.contributingTo')
                }}</span>
                <h3 class="upload-page-project-name">
                  {{ getProjectName(uploadStore.selectedProject) }}
                </h3>
              </div>
            </div>

            <!-- Stats Overview -->
            <div class="upload-page-stats-overview">
              <div class="upload-page-stat-box upload-page-stat-total">
                <div class="upload-page-stat-icon">
                  <svg
                    width="24"
                    height="24"
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
                <div class="upload-page-stat-content">
                  <div class="upload-page-stat-value">
                    {{ assignedTiersCount }}
                  </div>
                  <div class="upload-page-stat-label">
                    {{ $t('uploadPage.step4.totalTiersUploaded') }}
                  </div>
                </div>
              </div>

              <div class="upload-page-stat-box upload-page-stat-production">
                <div class="upload-page-stat-icon">
                  <svg
                    width="24"
                    height="24"
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
                <div class="upload-page-stat-content">
                  <div class="upload-page-stat-value">
                    {{ productionSectionsWithCounts.length }}
                  </div>
                  <div class="upload-page-stat-label">
                    {{ $t('uploadPage.step4.productionSections') }}
                  </div>
                </div>
              </div>

              <div class="upload-page-stat-box upload-page-stat-staged">
                <div class="upload-page-stat-icon">
                  <font-awesome-icon icon="fa-solid fa-square-plus" size="lg" />
                </div>
                <div class="upload-page-stat-content">
                  <div class="upload-page-stat-value">
                    {{ stagedSectionsWithCounts.length }}
                  </div>
                  <div class="upload-page-stat-label">
                    {{ $t('uploadPage.step4.stagedSections') }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Sections Breakdown -->
            <div class="upload-page-sections-breakdown">
              <!-- Production Sections -->
              <div
                v-if="productionSectionsWithCounts.length > 0"
                class="upload-page-section-group"
              >
                <h4
                  class="upload-page-section-group-title upload-page-production-title"
                >
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
                  {{ $t('uploadPage.step4.contributingToProduction') }}
                </h4>
                <div class="upload-page-section-list">
                  <div
                    v-for="section in productionSectionsWithCounts"
                    :key="section.section_id"
                    class="upload-page-section-item upload-page-production-section"
                  >
                    <span class="upload-page-section-name">{{
                      section.name
                    }}</span>
                    <span
                      class="upload-page-section-badge upload-page-production-badge"
                    >
                      <span class="upload-page-badge-count">{{
                        section.count
                      }}</span>
                      <span class="upload-page-badge-label">{{
                        section.count === 1
                          ? $t('uploadPage.step4.tier')
                          : $t('uploadPage.step4.tiers')
                      }}</span>
                    </span>
                  </div>
                </div>
              </div>

              <!-- Staged Sections -->
              <div
                v-if="stagedSectionsWithCounts.length > 0"
                class="upload-page-section-group"
              >
                <h4
                  class="upload-page-section-group-title upload-page-staged-title"
                >
                  <font-awesome-icon icon="fa-solid fa-square-plus" />
                  {{ $t('uploadPage.step4.suggestingNewSections') }}
                </h4>
                <div class="upload-page-section-list">
                  <div
                    v-for="section in stagedSectionsWithCounts"
                    :key="section.section_id"
                    class="upload-page-section-item upload-page-staged-section"
                  >
                    <span class="upload-page-section-name">{{
                      section.name
                    }}</span>
                    <span
                      class="upload-page-section-badge upload-page-staged-badge"
                    >
                      <span class="upload-page-badge-count">{{
                        section.count
                      }}</span>
                      <span class="upload-page-badge-label">{{
                        section.count === 1
                          ? $t('uploadPage.step4.tier')
                          : $t('uploadPage.step4.tiers')
                      }}</span>
                    </span>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div
                v-if="
                  productionSectionsWithCounts.length === 0 &&
                  stagedSectionsWithCounts.length === 0
                "
                class="upload-page-empty-sections-state"
              >
                <svg
                  width="48"
                  height="48"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                    stroke="#9ca3af"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                <p>{{ $t('uploadPage.step4.noSectionsAssigned') }}</p>
              </div>
            </div>

            <!-- Description -->
            <div class="upload-page-description-section">
              <label class="upload-page-description-label">
                {{ $t('uploadPage.step4.addDescription') }}
                <span class="upload-page-optional-label"
                  >({{ $t('uploadPage.step4.optional') }})</span
                >
              </label>
              <textarea
                v-model="uploadStore.description"
                :placeholder="$t('uploadPage.step4.placeholder')"
                class="upload-page-description-textarea"
                rows="4"
              ></textarea>
            </div>

            <!-- Actions -->
            <div class="upload-page-step4-actions">
              <button
                class="upload-page-btn-secondary"
                @click="uploadStore.prevStep"
              >
                <font-awesome-icon icon="fa-solid fa-arrow-left" />
                {{ $t('uploadPage.back') }}
              </button>
              <button
                class="upload-page-btn-cancel"
                @click="handleCancelUpload"
              >
                <font-awesome-icon icon="fa-solid fa-xmark" />
                {{ $t('uploadPage.cancelButton') }}
              </button>
              <button
                class="upload-page-btn-primary"
                @click="handleConfirmUpload"
              >
                <font-awesome-icon icon="fa-solid fa-circle-check" />
                {{ $t('uploadPage.step4.confirm') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Upload Results (if needed in later steps) -->
      <div v-if="uploadResults.length > 0" class="upload-results">
        <h3>{{ $t('uploadPage.uploadResults') }}</h3>
        <div class="upload-page-results-list">
          <div
            v-for="result in uploadResults"
            :key="result.filename"
            class="upload-page-result-item"
            :class="{
              'upload-page-success': result.success,
              'upload-page-error': !result.success,
            }"
          >
            <span class="upload-page-result-filename">{{
              result.filename
            }}</span>
            <span class="upload-page-result-status">
              {{
                result.success
                  ? $t('uploadPage.resultSuccess')
                  : $t('uploadPage.resultFailed')
              }}
            </span>
            <span v-if="result.error" class="upload-page-result-error">{{
              result.error
            }}</span>
          </div>
        </div>
      </div>

      <!-- Error Messages -->
      <div v-if="error" class="upload-page-error-message">
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

  // Pre-select current project ONLY if uploadStore has no selection yet
  if (!uploadStore.selectedProject && projectStore.currentProject) {
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
// This watcher does NOT sync back to projectStore - dropdown is independent
watch(
  () => uploadStore.selectedProject,
  async (newProjectId, oldProjectId) => {
    if (!isInitialLoad.value && newProjectId && newProjectId !== oldProjectId) {
      // Only fetch standards, do NOT update projectStore
      await fetchStandards();
    } else if (!newProjectId) {
      // Reset if no project selected
      hasEffectiveStandard.value = false;
      standard.value = null;
      mediaStandard.value = null;
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

// Step 4: Sections with tier counts for recap
const productionSectionsWithCounts = computed(() => {
  const sectionCounts = new Map();

  // Count tiers assigned to each production section
  uploadStore.extractedTiers.forEach((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    const assignment = uploadStore.tierAssignments[tierKey];

    if (
      assignment &&
      assignment !== '' &&
      assignment !== 'new' &&
      !assignment.startsWith('local_')
    ) {
      const section = uploadStore.existingSections.find(
        (s) => s.section_id === assignment && !s.is_staged
      );

      if (section) {
        const currentCount = sectionCounts.get(section.section_id) || 0;
        sectionCounts.set(section.section_id, currentCount + 1);
      }
    }
  });

  // Convert to array with section details
  return Array.from(sectionCounts.entries())
    .map(([sectionId, count]) => {
      const section = uploadStore.existingSections.find(
        (s) => s.section_id === sectionId
      );
      return {
        section_id: sectionId,
        name: section?.name || sectionId,
        count,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
});

const stagedSectionsWithCounts = computed(() => {
  const sectionCounts = new Map();

  // Count tiers assigned to each staged section
  uploadStore.extractedTiers.forEach((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    const assignment = uploadStore.tierAssignments[tierKey];

    if (assignment && assignment.startsWith('local_')) {
      const section = uploadStore.existingSections.find(
        (s) => s.section_id === assignment && s.is_staged
      );

      if (section) {
        const currentCount = sectionCounts.get(section.section_id) || 0;
        sectionCounts.set(section.section_id, currentCount + 1);
      }
    }
  });

  // Convert to array with section details
  return Array.from(sectionCounts.entries())
    .map(([sectionId, count]) => {
      const section = uploadStore.existingSections.find(
        (s) => s.section_id === sectionId
      );
      return {
        section_id: sectionId,
        name: section?.name || section?.section_name || sectionId,
        count,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));
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
