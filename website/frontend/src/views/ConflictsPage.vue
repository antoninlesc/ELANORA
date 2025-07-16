<template>
  <div class="conflicts-page">
    <div class="conflicts-container">
      <h1 class="conflicts-title">Manage Conflicts</h1>
      
      <!-- Project Selection -->
      <div class="project-selection">
        <label for="projectSelect" class="project-label">Select Project:</label>
        <select 
          id="projectSelect" 
          v-model="selectedProject" 
          class="project-select"
          :disabled="loading"
          @change="fetchBranches"
        >
          <option value="">Choose a project...</option>
          <option v-for="project in projects" :key="project" :value="project">
            {{ project }}
          </option>
        </select>
      </div>

      <!-- Branch Selection -->
      <div v-if="selectedProject" class="branch-selection">
        <label for="branchSelect" class="branch-label">Select Branch:</label>
        <select 
          id="branchSelect" 
          v-model="selectedBranch" 
          class="branch-select"
          :disabled="branchesLoading"
          @change="fetchConflicts"
        >
          <option value="">Choose a branch...</option>
          <option v-for="branch in branches" :key="branch" :value="branch">
            {{ branch.name }}
          </option>
        </select>
      </div>

      <!-- Conflicts List -->
      <div v-if="selectedProject && selectedBranch" class="conflicts-section">
        <div class="conflicts-header">
          <h2>Conflicts in "{{ selectedBranch.name }}"</h2>
          <div class="conflicts-actions">
            <button 
              @click="refreshConflicts" 
              class="refresh-btn"
              :disabled="conflictsLoading || refreshing"
            >
              {{ refreshing ? '🔄 Refreshing...' : '🔄 Refresh' }}
            </button>
            <button 
              v-if="conflicts.length > 0"
              @click="showBatchResolution = true" 
              class="batch-btn"
            >
              Resolve All
            </button>
          </div>
        </div>

        <div v-if="conflictsLoading" class="loading">
          Loading conflicts...
        </div>

        <div v-else-if="conflicts.length === 0" class="no-conflicts">
          <div class="no-conflicts-icon">✅</div>
          <h3>No conflicts found</h3>
          <p>All files are in sync for this branch.</p>
        </div>

        <div v-else class="conflicts-list">
          <div 
            v-for="conflict in conflicts" 
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
        <div v-if="conflicts.length > 0" class="cache-info">
          <small class="cache-status">
            Source: {{ conflicts.source || 'unknown' }}
            <span v-if="conflicts.cache_age_hours">
              (cached {{ conflicts.cache_age_hours }}h ago)
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
            <p>Resolve all {{ conflicts.length }} conflicts using the same strategy:</p>
            
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
import "@/assets/css/conflicts-page.css";

const projects = ref([]);
const branches = ref([]);
const conflicts = ref([]);
const selectedProject = ref('');
const selectedBranch = ref('');
const loading = ref(true);
const branchesLoading = ref(false);
const conflictsLoading = ref(false);
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

// Add a refresh indicator
const refreshing = ref(false);

onMounted(async () => {
  await fetchProjects();
});

async function fetchProjects() {
  try {
    loading.value = true;
    const response = await gitService.listProjects();
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
    conflicts.value = [];
    
    const response = await gitService.getBranches(selectedProject.value);
    branches.value = response.branches || [];
  } catch (e) {
    error.value = 'Failed to load branches';
    console.error('Error fetching branches:', e);
  } finally {
    branchesLoading.value = false;
  }
}

async function fetchConflicts() {
  if (!selectedProject.value || !selectedBranch.value) return;
  
  try {
    conflictsLoading.value = true;
    const response = await gitService.getConflicts(
      selectedProject.value, 
      selectedBranch.value.name || selectedBranch.value
    );
    conflicts.value = response.conflicts || [];
    
    // Show cache info if available
    if (response.source === 'database' && response.cache_age_hours !== undefined) {
      console.log(`Loaded conflicts from cache (${response.cache_age_hours}h old)`);
    }
  } catch (e) {
    error.value = 'Failed to load conflicts';
    console.error('Error fetching conflicts:', e);
    conflicts.value = [];
  } finally {
    conflictsLoading.value = false;
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
    conflicts.value = response.conflicts || [];
  } catch (e) {
    error.value = 'Failed to refresh conflicts';
    console.error('Error refreshing conflicts:', e);
  } finally {
    refreshing.value = false;
  }
}

function viewConflictDetails(conflict) {
  // This would open a detailed view of the conflict
  alert(`Viewing details for ${conflict.filename}:\n\n${conflict.details}\n\nIn a real implementation, this would show a side-by-side comparison of the conflicting content.`);
}

function resolveConflict(conflict) {
  currentConflict.value = conflict;
  resolutionStrategy.value = '';
  showResolutionModal.value = true;
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
    const index = conflicts.value.findIndex(c => c.filename === currentConflict.value.filename);
    if (index !== -1) {
      conflicts.value.splice(index, 1);
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
      // No filename = resolve all conflicts
    );
    
    // Clear all conflicts
    conflicts.value = [];
    showBatchResolution.value = false;
    batchResolutionStrategy.value = '';
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Failed to resolve conflicts';
    console.error('Batch resolution error:', e);
  } finally {
    batchResolving.value = false;
  }
}

function formatConflictType(type) {
  const types = {
    'content_conflict': 'Content Conflict',
    'merge_conflict': 'Merge Conflict',
    'annotation_conflict': 'Annotation Conflict',
    'tier_conflict': 'Tier Conflict'
  };
  return types[type] || 'Unknown Conflict';
}
</script>

<style></style>