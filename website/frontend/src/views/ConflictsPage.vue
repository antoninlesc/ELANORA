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
          <h2>Conflicts in "{{ selectedBranch }}"</h2>
          <div class="conflicts-actions">
            <button 
              @click="refreshConflicts" 
              class="refresh-btn"
              :disabled="conflictsLoading"
            >
              🔄 Refresh
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
    // This would need to be implemented in your git service
    // For now, we'll simulate some conflicts
    const response = await gitService.getConflicts?.(selectedProject.value, selectedBranch.value) || 
                     { conflicts: [] };
    conflicts.value = response.conflicts || [];
  } catch (e) {
    error.value = 'Failed to load conflicts';
    console.error('Error fetching conflicts:', e);
    // Simulate some conflicts for demo
    conflicts.value = [
      {
        filename: 'example1.eaf',
        type: 'content_conflict',
        details: 'Conflicting annotations in tier T1'
      },
      {
        filename: 'example2.eaf',
        type: 'merge_conflict',
        details: 'Different time slot values'
      }
    ];
  } finally {
    conflictsLoading.value = false;
  }
}

function refreshConflicts() {
  fetchConflicts();
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
      selectedBranch.value,
      resolutionStrategy.value
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
      selectedBranch.value,
      batchResolutionStrategy.value
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

<style scoped>
.conflicts-page {
  max-width: 1000px;
  margin: 40px auto;
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
}

.conflicts-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 32px;
  color: #2c3e50;
  text-align: center;
}

.project-selection, .branch-selection {
  margin-bottom: 24px;
}

.project-label, .branch-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.project-select, .branch-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
}

.project-select:focus, .branch-select:focus {
  outline: none;
  border-color: #1976d2;
}

.conflicts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e0e0e0;
}

.conflicts-actions {
  display: flex;
  gap: 12px;
}

.refresh-btn, .batch-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.refresh-btn {
  background: #666;
  color: white;
}

.batch-btn {
  background: #ff9800;
  color: white;
}

.refresh-btn:hover, .batch-btn:hover {
  opacity: 0.9;
}

.loading {
  text-align: center;
  color: #666;
  padding: 48px;
}

.no-conflicts {
  text-align: center;
  padding: 48px;
  color: #666;
}

.no-conflicts-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.conflict-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.conflict-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
}

.conflict-info {
  flex: 1;
}

.conflict-filename {
  margin: 0 0 4px 0;
  color: #2c3e50;
}

.conflict-type {
  background: #ff5722;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.conflict-actions {
  display: flex;
  gap: 8px;
}

.view-btn, .resolve-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.3s;
}

.view-btn {
  background: #2196f3;
  color: white;
}

.resolve-btn {
  background: #4caf50;
  color: white;
}

.view-btn:hover, .resolve-btn:hover {
  opacity: 0.9;
}

.conflict-details {
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  background: white;
  color: #666;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e0e0e0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.resolution-options, .batch-content {
  padding: 24px;
}

.strategy-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.strategy-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.3s;
}

.strategy-option:hover {
  border-color: #1976d2;
}

.strategy-option input[type="radio"] {
  margin-top: 2px;
}

.strategy-content {
  flex: 1;
}

.strategy-content strong {
  display: block;
  margin-bottom: 4px;
  color: #2c3e50;
}

.strategy-content p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid #e0e0e0;
}

.apply-btn, .cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.apply-btn {
  background: #4caf50;
  color: white;
}

.apply-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.cancel-btn {
  background: #666;
  color: white;
}

.error-message {
  background: #ffebee;
  border: 1px solid #f44336;
  color: #d32f2f;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  margin-top: 24px;
}
</style>