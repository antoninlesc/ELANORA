<template>
  <div class="pending-uploads-page">
    <div class="pending-uploads-container">
      <h1 class="pending-uploads-title">
        {{ t('pendingUploads.title') }} 
        <span v-if="currentProjectName" class="project-name">{{ currentProjectName }}</span>
      </h1>

      <!-- No Project Selected -->
      <div v-if="!currentProject" class="no-selection">
        <div class="no-selection-icon">📁</div>
        <h3>{{ t('pendingUploads.noProjectSelected.title') }}</h3>
        <p>{{ t('pendingUploads.noProjectSelected.message') }}</p>
        <router-link to="/projects" class="select-project-btn">
          {{ t('pendingUploads.noProjectSelected.selectProject') }}
        </router-link>
      </div>

      <!-- Loading State -->
      <div v-else-if="uploadsLoading" class="loading">
        <div class="loading-spinner"></div>
        <p>{{ t('pendingUploads.loading') }}</p>
      </div>

      <!-- No Pending Uploads -->
      <div v-else-if="pendingUploads.length === 0" class="no-uploads">
        <div class="no-uploads-icon">✅</div>
        <h3>{{ t('pendingUploads.noUploads.title') }}</h3>
        <p>{{ t('pendingUploads.noUploads.message') }}</p>
      </div>

      <!-- Pending Uploads List -->
      <div v-else class="uploads-section">
        <!-- Summary Stats -->
        <div class="uploads-summary">
          <div class="summary-card">
            <h3>{{ totalPending }}</h3>
            <p>{{ t('pendingUploads.summary.totalPending') }}</p>
          </div>
          <div class="summary-card ready">
            <h3>{{ readyCount }}</h3>
            <p>{{ t('pendingUploads.summary.readyToMerge') }}</p>
          </div>
          <div class="summary-card conflicts">
            <h3>{{ conflictsCount }}</h3>
            <p>{{ t('pendingUploads.summary.needResolution') }}</p>
          </div>
        </div>

        <!-- Upload List -->
        <div class="uploads-list">
          <div 
            v-for="upload in pendingUploads" 
            :key="upload.upload_id"
            class="upload-item"
            :class="getUploadStatusClass(upload)"
          >
            <div class="upload-header">
              <div class="upload-info">
                <h3 class="upload-branch">{{ upload.original_branch }}</h3>
                <div class="upload-meta">
                  <span class="upload-type">{{ formatUploadType(upload.upload_type) }}</span>
                  <span class="upload-date">{{ formatDate(upload.uploaded_at) }}</span>
                  <span class="upload-user">{{ t('pendingUploads.uploadedBy', { user: upload.uploaded_by }) }}</span>
                </div>
              </div>
              
              <div class="upload-status-section">
                <div class="upload-status">
                  <span class="status-badge" :class="getStatusClass(upload.merge_status)">
                    {{ formatStatus(upload.merge_status) }}
                  </span>
                </div>
                
                <!-- Actions -->
                <div class="upload-actions">
                  <button 
                    @click="viewUploadDetails(upload)"
                    class="action-btn view-btn"
                  >
                    {{ t('pendingUploads.actions.viewDetails') }}
                  </button>
                  
                  <button 
                    v-if="upload.merge_status === 'ready_to_merge'"
                    @click="mergeUpload(upload)"
                    class="action-btn merge-btn"
                    :disabled="merging"
                  >
                    {{ merging === upload.upload_id ? t('pendingUploads.actions.merging') : t('pendingUploads.actions.mergeNow') }}
                  </button>
                  
                  <button 
                    v-if="upload.merge_status === 'needs_resolution'"
                    @click="resolveUpload(upload)"
                    class="action-btn resolve-btn"
                  >
                    {{ t('pendingUploads.actions.resolveConflicts') }}
                  </button>
                  
                  <button 
                    @click="testMerge(upload)"
                    class="action-btn test-btn"
                    :disabled="testing === upload.upload_id"
                  >
                    {{ testing === upload.upload_id ? t('pendingUploads.actions.testing') : t('pendingUploads.actions.testMerge') }}
                  </button>
                </div>
              </div>
            </div>

            <!-- File Summary -->
            <div class="upload-summary">
              <div class="file-counts">
                <span v-if="upload.file_counts?.new > 0" class="file-count new">
                  +{{ upload.file_counts.new }} {{ t('pendingUploads.fileTypes.new') }}
                </span>
                <span v-if="upload.file_counts?.modified > 0" class="file-count modified">
                  ~{{ upload.file_counts.modified }} {{ t('pendingUploads.fileTypes.modified') }}
                </span>
                <span v-if="upload.file_counts?.deleted > 0" class="file-count deleted">
                  -{{ upload.file_counts.deleted }} {{ t('pendingUploads.fileTypes.deleted') }}
                </span>
              </div>
              
              <p class="upload-description">{{ upload.description }}</p>
            </div>

            <!-- Conflicts (if any) -->
            <div v-if="upload.conflicted_files?.length > 0" class="conflicts-section">
              <h4>{{ t('pendingUploads.conflictedFiles') }}:</h4>
              <ul class="conflict-files">
                <li v-for="file in upload.conflicted_files" :key="file" class="conflict-file">
                  {{ file }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Upload Details Modal -->
      <div v-if="showDetailsModal" class="modal-overlay" @click="closeDetailsModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>{{ t('pendingUploads.modal.uploadDetails') }}: {{ selectedUpload?.original_branch }}</h2>
            <button @click="closeDetailsModal" class="close-btn">×</button>
          </div>
          
          <div class="modal-body">
            <UploadDetailsView 
              v-if="selectedUpload"
              :upload="selectedUpload"
            />
          </div>
        </div>
      </div>

      <!-- Conflict Resolution Modal -->
      <div v-if="showResolutionModal" class="modal-overlay large" @click="closeResolutionModal">
        <div class="modal-content large" @click.stop>
          <div class="modal-header">
            <h2>{{ t('pendingUploads.modal.resolveConflicts') }}: {{ selectedUpload?.original_branch }}</h2>
            <button @click="closeResolutionModal" class="close-btn">×</button>
          </div>
          
          <div class="modal-body">
            <UploadResolutionView
              v-if="selectedUpload"
              :project-name="currentProjectName"
              :upload="selectedUpload"
              @resolved="onUploadResolved"
              @cancelled="closeResolutionModal"
            />
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
import { ref, onMounted, computed, onUnmounted, watch } from 'vue';
import gitService from '@/api/service/gitService';
import "@/assets/css/pending-uploads-page.css";
import UploadDetailsView from '@/components/common/UploadDetailsView.vue';
import UploadResolutionView from '@/components/common/UploadResolutionView.vue';
import { useProjectStore } from '@/stores/project.js';
import { useI18n } from 'vue-i18n';

// State
const { t } = useI18n();
const pendingUploads = ref([]);
const loading = ref(true);
const uploadsLoading = ref(false);
const error = ref('');

// Modal state
const showDetailsModal = ref(false);
const showResolutionModal = ref(false);
const selectedUpload = ref(null);

// Action state
const merging = ref(null); // upload_id being merged
const testing = ref(null); // upload_id being tested
const batchMerging = ref(false);

// Project store
const projectStore = useProjectStore();

// Computed properties from project store
const currentProject = computed(() => projectStore.currentProject);
const currentProjectName = computed(() => {
  if (!currentProject.value) return '';
  
  return typeof currentProject.value === 'object'
    ? currentProject.value.project_name
    : currentProject.value;
});

// Upload computed properties
const totalPending = computed(() => pendingUploads.value.length);
const readyCount = computed(() => 
  pendingUploads.value.filter(u => u.merge_status === 'ready_to_merge').length
);
const conflictsCount = computed(() => 
  pendingUploads.value.filter(u => u.merge_status === 'needs_resolution').length
);

// Auto-refresh interval
let refreshInterval = null;

// Watch for project changes
watch(currentProject, async (newProject, oldProject) => {
  if (newProject && newProject !== oldProject) {
    await fetchPendingUploads();
  }
}, { immediate: true });

onMounted(async () => {
  // Load pending uploads if project is already selected
  if (currentProject.value) {
    await fetchPendingUploads();
  }
  
  // Set up auto-refresh every 30 seconds
  refreshInterval = setInterval(() => {
    if (currentProject.value) {
      fetchPendingUploads(false); // Silent refresh
    }
  }, 30000);
});

// Cleanup interval on unmount
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});

async function fetchPendingUploads(showLoading = true) {
  if (!currentProjectName.value) {
    pendingUploads.value = [];
    return;
  }
  
  try {
    if (showLoading) uploadsLoading.value = true;
    error.value = '';
    
    const response = await gitService.getPendingUploadsWithStatus(currentProjectName.value);
    pendingUploads.value = response.pending_uploads || [];
    
    console.log(`Loaded ${pendingUploads.value.length} pending uploads for project: ${currentProjectName.value}`);
  } catch (e) {
    if (showLoading) {
      error.value = t('pendingUploads.errors.loadFailed');
      console.error('Error fetching pending uploads:', e);
    }
    pendingUploads.value = [];
  } finally {
    if (showLoading) uploadsLoading.value = false;
  }
}

async function testMerge(upload) {
  try {
    testing.value = upload.upload_id;
    error.value = '';
    
    const response = await gitService.adminTestMerge(
      currentProjectName.value, 
      upload.branch_name
    );
    
    // Update the upload status in the list
    const index = pendingUploads.value.findIndex(u => u.upload_id === upload.upload_id);
    if (index !== -1) {
      pendingUploads.value[index] = {
        ...pendingUploads.value[index],
        merge_status: response.status,
        conflicted_files: response.conflicted_files || [],
        conflicts_count: response.conflicts_count || 0,
        can_auto_merge: response.can_auto_merge,
        tested_at: response.tested_at
      };
    }
    
  } catch (e) {
    error.value = e?.response?.data?.detail || t('pendingUploads.errors.testMergeFailed');
    console.error('Test merge error:', e);
  } finally {
    testing.value = null;
  }
}

async function mergeUpload(upload) {
  if (upload.merge_status !== 'ready_to_merge') {
    error.value = t('pendingUploads.errors.notReadyToMerge');
    return;
  }
  
  try {
    merging.value = upload.upload_id;
    error.value = '';
    
    await gitService.adminCompleteMerge(
      currentProjectName.value,
      upload.branch_name,
      'auto' // Auto-merge since it's ready
    );
    
    // Remove the merged upload from the list
    const index = pendingUploads.value.findIndex(u => u.upload_id === upload.upload_id);
    if (index !== -1) {
      pendingUploads.value.splice(index, 1);
    }
    
    // Refresh all uploads to update status of remaining ones
    await fetchPendingUploads(false);
    
  } catch (e) {
    error.value = e?.response?.data?.detail || t('pendingUploads.errors.mergeFailed');
    console.error('Merge error:', e);
  } finally {
    merging.value = null;
  }
}

async function mergeAllReady() {
  const readyUploads = pendingUploads.value.filter(u => u.merge_status === 'ready_to_merge');
  
  if (readyUploads.length === 0) {
    error.value = t('pendingUploads.errors.noReadyUploads');
    return;
  }
  
  try {
    batchMerging.value = true;
    error.value = '';
    
    // Merge all ready uploads sequentially
    for (const upload of readyUploads) {
      await gitService.adminCompleteMerge(
        currentProjectName.value,
        upload.branch_name,
        'auto'
      );
    }
    
    // Refresh the entire list
    await fetchPendingUploads();
    
  } catch (e) {
    error.value = e?.response?.data?.detail || t('pendingUploads.errors.batchMergeFailed');
    console.error('Batch merge error:', e);
  } finally {
    batchMerging.value = false;
  }
}

function resolveUpload(upload) {
  selectedUpload.value = upload;
  showResolutionModal.value = true;
}

function viewUploadDetails(upload) {
  selectedUpload.value = upload;
  showDetailsModal.value = true;
}

function closeDetailsModal() {
  showDetailsModal.value = false;
  selectedUpload.value = null;
}

function closeResolutionModal() {
  showResolutionModal.value = false;
  selectedUpload.value = null;
}

async function onUploadResolved() {
  closeResolutionModal();
  // Refresh the list to show updated status
  await fetchPendingUploads();
}

// Utility functions
function getUploadStatusClass(upload) {
  return {
    'status-ready': upload.merge_status === 'ready_to_merge',
    'status-conflicts': upload.merge_status === 'needs_resolution',
    'status-error': upload.merge_status === 'error',
    'status-pending': upload.merge_status === 'pending_admin_approval'
  };
}

function getStatusClass(status) {
  const classes = {
    'ready_to_merge': 'ready',
    'needs_resolution': 'conflicts', 
    'error': 'error',
    'pending_admin_approval': 'pending'
  };
  return classes[status] || 'pending';
}

function formatStatus(status) {
  const statuses = {
    'ready_to_merge': t('pendingUploads.status.readyToMerge'),
    'needs_resolution': t('pendingUploads.status.needsResolution'),
    'error': t('pendingUploads.status.error'),
    'pending_admin_approval': t('pendingUploads.status.pendingReview')
  };
  return statuses[status] || status;
}

function formatUploadType(type) {
  const types = {
    'pending_upload': t('pendingUploads.uploadTypes.newFiles'),
    'upload_with_modifications': t('pendingUploads.uploadTypes.withModifications'),
    'upload_with_deletions': t('pendingUploads.uploadTypes.withDeletions')
  };
  return types[type] || type;
}

function formatDate(dateString) {
  if (!dateString) return t('pendingUploads.unknown');
  return new Date(dateString).toLocaleDateString();
}
</script>

<style scoped>
.project-name {
  color: #1976d2;
  font-weight: 600;
}

.select-project-btn {
  display: inline-block;
  margin-top: 16px;
  padding: 12px 24px;
  background: #1976d2;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: background 0.3s;
}

.select-project-btn:hover {
  background: #1565c0;
}
</style>