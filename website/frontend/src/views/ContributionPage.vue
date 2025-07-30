<template>
  <div class="pendingUploads-page">
    <div class="pendingUploads-container">
      <!-- TODO Add a locale for the title -->
      <h1 class="pendingUploads-title">Manage Pending Uploads</h1>

      <div v-if="selectedProject">
        <div v-if="pendingUploadsLoading" class="loading">
          Loading pendingUploads...
        </div>

        <div v-else-if="pendingUploads.length === 0" class="no-pendingUploads">
          <div class="no-pendingUploads-icon">✅</div>
          <h3>No pendingUploads found</h3>
          <p>All files are in sync for this branch.</p>
        </div>

        <div v-else class="pendingUploads-list">
          <div 
            v-for="conflict in pendingUploads" 
            :key="conflict.filename"
            class="conflict-item"
          >
            <div class="conflict-header">
              <div class="conflict-info">
                <h3 class="conflict-filename">{{ conflict.filename }}</h3>
                <span class="conflict-type">{{ formatConflictType(conflict.type) }}</span>
              </div>
              <div class="conflict-actions">
                <button 
                  @click="viewConflictDetails(conflict)"
                  class="view-btn"
                >
                  View Details
                </button>
                <button 
                  @click="resolveConflict(conflict)"
                  class="resolve-btn"
                >
                  Resolve
                </button>
              </div>
            </div>
            
            <div v-if="conflict.details" class="conflict-details">
              <p>{{ conflict.details }}</p>
            </div>
          </div>
        </div>

        <!-- Cache Info Display -->
        <div v-if="pendingUploads.length > 0" class="cache-info">
          <small class="cache-status">
            Source: {{ pendingUploads.source || 'unknown' }}
            <span v-if="pendingUploads.cache_age_hours">
              (cached {{ pendingUploads.cache_age_hours }}h ago)
            </span>
          </small>
        </div>
      </div>

      <!-- Conflict Resolution Modal -->
      <div v-if="showResolutionModal" class="modal-overlay" @click="closeResolutionModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>Resolve Conflict: {{ currentConflict?.filename }}</h2>
            <button @click="closeResolutionModal" class="close-btn">×</button>
          </div>
          
          <div class="resolution-options">
            <h3>Choose Resolution Strategy:</h3>
            <div class="strategy-options">
              <label class="strategy-option">
                <input 
                  type="radio" 
                  v-model="resolutionStrategy" 
                  value="accept_incoming"
                >
                <div class="strategy-content">
                  <strong>Accept Incoming Changes</strong>
                  <p>Keep the changes from the branch being merged</p>
                </div>
              </label>
              
              <label class="strategy-option">
                <input 
                  type="radio" 
                  v-model="resolutionStrategy" 
                  value="accept_current"
                >
                <div class="strategy-content">
                  <strong>Accept Current Changes</strong>
                  <p>Keep the current version (discard incoming changes)</p>
                </div>
              </label>
              
              <label class="strategy-option">
                <input 
                  type="radio" 
                  v-model="resolutionStrategy" 
                  value="manual"
                >
                <div class="strategy-content">
                  <strong>Manual Resolution</strong>
                  <p>Manually merge the changes (advanced)</p>
                </div>
              </label>
            </div>
          </div>
          
          <div class="modal-actions">
            <button 
              @click="applyResolution"
              class="apply-btn"
              :disabled="!resolutionStrategy || resolving"
            >
              {{ resolving ? 'Resolving...' : 'Apply Resolution' }}
            </button>
            <button @click="closeResolutionModal" class="cancel-btn">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Batch Resolution Modal -->
      <div v-if="showBatchResolution" class="modal-overlay" @click="showBatchResolution = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>Batch Conflict Resolution</h2>
            <button @click="showBatchResolution = false" class="close-btn">×</button>
          </div>
          
          <div class="batch-content">
            <p>Resolve all {{ pendingUploads.length }} pendingUploads using the same strategy:</p>
            
            <div class="strategy-options">
              <label class="strategy-option">
                <input 
                  type="radio" 
                  v-model="batchResolutionStrategy" 
                  value="accept_incoming"
                >
                <div class="strategy-content">
                  <strong>Accept All Incoming Changes</strong>
                </div>
              </label>
              
              <label class="strategy-option">
                <input 
                  type="radio" 
                  v-model="batchResolutionStrategy" 
                  value="accept_current"
                >
                <div class="strategy-content">
                  <strong>Accept All Current Changes</strong>
                </div>
              </label>
            </div>
          </div>
          
          <div class="modal-actions">
            <button 
              @click="applyBatchResolution"
              class="apply-btn"
              :disabled="!batchResolutionStrategy || batchResolving"
            >
              {{ batchResolving ? 'Resolving All...' : 'Resolve All Conflicts' }}
            </button>
            <button @click="showBatchResolution = false" class="cancel-btn">
              Cancel
            </button>
          </div>
        </div>
      </div>

      <!-- Merge View Modal -->
      <div v-if="showMergeView" class="modal-overlay large" @click="onMergeViewCancelled">
        <div class="modal-content large" @click.stop>
          <div class="modal-header">
            <h2>Resolve Merge Conflict</h2>
            <button @click="onMergeViewCancelled" class="close-btn">×</button>
          </div>
          
          <div class="modal-body">
            <ConflictMergeView
              v-if="selectedConflictFile"
              :project-name="selectedProject"
              :branch-name="selectedBranch.name || selectedBranch"
              :filename="selectedConflictFile.filename"
              @resolved="onConflictResolved"
              @cancelled="onMergeViewCancelled"
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
import { ref, onMounted } from 'vue';
import gitService from '@/api/service/gitService';
import "@/assets/css/pendingUploads-page.css";
import ConflictMergeView from '@/components/common/ConflictMergeView.vue';

const projects = ref([]);
const branches = ref([]);
const pendingUploads = ref([]);
const selectedProject = ref('');
const selectedBranch = ref('');
const loading = ref(true);
const branchesLoading = ref(false);
const pendingUploadsLoading = ref(false);
const error = ref('');

// Resolution modal state
const showResolutionModal = ref(false);
const currentConflict = ref(null);
const resolutionStrategy = ref('');
const resolving = ref(false);

// Batch resolution state
const showBatchResolution = ref(false);
const batchResolutionStrategy = ref('');
const batchResolving = ref(false);

// Merge view state
const showMergeView = ref(false);
const selectedConflictFile = ref(null);

// Add a refresh indicator
const refreshing = ref(false);

onMounted(async () => {
  await fetchProjects();
});

async function fetchProjects() {
  try {
    loading.value = true;
    const response = await gitService.listUserProjects();
    projects.value = response.projects;
  } catch (e) {
    error.value = 'Failed to load projects';
    console.error('Error fetching projects:', e);
  } finally {
    loading.value = false;
  }
}

async function fetchBranches() {
  if (!selectedProject.value) return;
  
  try {
    branchesLoading.value = true;
    branches.value = [];
    selectedBranch.value = '';
    pendingUploads.value = [];
    
    const response = await gitService.getBranches(selectedProject.value);
    branches.value = response.branches || [];
  } catch (e) {
    error.value = 'Failed to load branches';
    console.error('Error fetching branches:', e);
  } finally {
    branchesLoading.value = false;
  }
}

async function fetchPendingUploads() {
  if (!selectedProject.value || !selectedBranch.value) return;
  
  try {
    pendingUploadsLoading.value = true;
    const response = await gitService.getPendingUploads(
      selectedProject.value
    );
    pendingUploads.value = response.pendingUploads || [];
    
    // Show cache info if available
    if (response.source === 'database' && response.cache_age_hours !== undefined) {
      console.log(`Loaded pendingUploads from cache (${response.cache_age_hours}h old)`);
    }
  } catch (e) {
    error.value = 'Failed to load pendingUploads';
    console.error('Error fetching pendingUploads:', e);
    pendingUploads.value = [];
  } finally {
    pendingUploadsLoading.value = false;
  }
}

async function refreshConflicts() {
  if (!selectedProject.value || !selectedBranch.value) return;
  
  try {
    refreshing.value = true;
    const response = await gitService.refreshConflicts(
      selectedProject.value, 
      selectedBranch.value.name || selectedBranch.value
    );
    pendingUploads.value = response.pendingUploads || [];
  } catch (e) {
    error.value = 'Failed to refresh pendingUploads';
    console.error('Error refreshing pendingUploads:', e);
  } finally {
    refreshing.value = false;
  }
}

function viewConflictDetails(conflict) {
  const details = [];
  
  details.push(`File: ${conflict.filename}`);
  details.push(`Type: ${formatConflictType(conflict.type)}`);
  details.push(`Status: ${conflict.status.toUpperCase()}`);
  details.push(`Detected: ${new Date(conflict.detected_at).toLocaleString()}`);
  
  if (conflict.git_info) {
    details.push(`\nGit Information:`);
    details.push(`- Change Type: ${conflict.git_info.change_type}`);
    
    if (conflict.git_info.conflict_branch) {
      details.push(`- Isolated in Branch: ${conflict.git_info.conflict_branch}`);
    }
    
    if (conflict.git_info.file_size) {
      details.push(`- File Size: ${(conflict.git_info.file_size / 1024).toFixed(1)} KB`);
    }
    
    if (conflict.git_info.conflict_markers > 0) {
      details.push(`- Conflict Markers: ${conflict.git_info.conflict_markers}`);
    }
    
    if (conflict.git_info.additions > 0 || conflict.git_info.deletions > 0) {
      details.push(`- Changes: +${conflict.git_info.additions || 0} -${conflict.git_info.deletions || 0}`);
    }
  }
  
  if (conflict.resolution_info) {
    details.push(`\nResolution Information:`);
    details.push(`- Can Auto-Resolve: ${conflict.resolution_info.can_auto_resolve ? 'Yes' : 'No'}`);
    details.push(`- Suggested Action: ${conflict.resolution_info.suggested_action}`);
    details.push(`- Requires Manual Review: ${conflict.resolution_info.requires_manual_review ? 'Yes' : 'No'}`);
  }
  
  alert(details.join('\n'));
}

function resolveConflict(conflict) {
  selectedConflictFile.value = conflict;
  showMergeView.value = true;
}

function closeResolutionModal() {
  showResolutionModal.value = false;
  currentConflict.value = null;
  resolutionStrategy.value = '';
}

async function applyResolution() {
  if (!currentConflict.value || !resolutionStrategy.value) return;
  
  try {
    resolving.value = true;
    
    await gitService.resolveConflicts(
      selectedProject.value,
      selectedBranch.value.name || selectedBranch.value,
      resolutionStrategy.value,
      currentConflict.value.filename  // Resolve specific file
    );
    
    // Remove resolved conflict from list
    const index = pendingUploads.value.findIndex(c => c.filename === currentConflict.value.filename);
    if (index !== -1) {
      pendingUploads.value.splice(index, 1);
    }
    
    closeResolutionModal();
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Failed to resolve conflict';
    console.error('Resolution error:', e);
  } finally {
    resolving.value = false;
  }
}

async function applyBatchResolution() {
  if (!batchResolutionStrategy.value) return;
  
  try {
    batchResolving.value = true;
    
    await gitService.resolveConflicts(
      selectedProject.value,
      selectedBranch.value.name || selectedBranch.value,
      batchResolutionStrategy.value
      // No filename = resolve all pendingUploads
    );
    
    // Clear all pendingUploads
    pendingUploads.value = [];
    showBatchResolution.value = false;
    batchResolutionStrategy.value = '';
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Failed to resolve pendingUploads';
    console.error('Batch resolution error:', e);
  } finally {
    batchResolving.value = false;
  }
}

function onConflictResolved() {
  showMergeView.value = false;
  selectedConflictFile.value = null;
  // Refresh pendingUploads list
  fetchConflicts();
}

function onMergeViewCancelled() {
  showMergeView.value = false;
  selectedConflictFile.value = null;
}

function formatConflictType(type) {
  const types = {
    'GIT_CONTENT_CONFLICT': 'Content Conflict',
    'GIT_MERGE_CONFLICT': 'Merge Conflict',
    'GIT_FILE_CONFLICT': 'File Conflict',
    'content_conflict': 'Content Conflict',
    'merge_conflict': 'Merge Conflict',
    'annotation_conflict': 'Annotation Conflict',
    'tier_conflict': 'Tier Conflict'
  };
  return types[type] || 'Unknown Conflict';
}
</script>

<style></style>