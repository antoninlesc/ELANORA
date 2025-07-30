<template>
  <div class="conflict-merge-view">
    <div class="merge-header">
      <h3>Resolve Conflict: {{ filename }}</h3>
      <div class="merge-actions">
        <button 
          @click="acceptCurrent" 
          class="btn-accept current"
          :disabled="resolving"
        >
          Accept Current (Master)
        </button>
        <button 
          @click="acceptIncoming" 
          class="btn-accept incoming"
          :disabled="resolving"
        >
          Accept Incoming ({{ branchName }})
        </button>
        <button 
          @click="toggleManualMode" 
          class="btn-manual"
          :disabled="resolving"
        >
          {{ isManualMode ? 'Exit Manual' : 'Manual Resolve' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      Loading conflict details...
    </div>

    <div v-else-if="conflictData" class="merge-content">
      <!-- Automatic Resolution Preview -->
      <div v-if="!isManualMode" class="auto-resolve-view">
        <div class="conflict-sections">
          <div 
            v-for="(section, index) in conflictData.conflict_content.merge_data.conflict_sections" 
            :key="index"
            class="conflict-section"
          >
            <div class="section-header">
              <h4>Conflict {{ index + 1 }}</h4>
              <div class="section-actions">
                <button 
                  @click="selectSectionContent(index, 'current')"
                  class="btn-select current"
                  :class="{ active: sectionSelections[index] === 'current' }"
                >
                  Use Current
                </button>
                <button 
                  @click="selectSectionContent(index, 'incoming')"
                  class="btn-select incoming"
                  :class="{ active: sectionSelections[index] === 'incoming' }"
                >
                  Use Incoming
                </button>
                <button 
                  @click="selectSectionContent(index, 'both')"
                  class="btn-select both"
                  :class="{ active: sectionSelections[index] === 'both' }"
                >
                  Use Both
                </button>
              </div>
            </div>

            <div class="diff-view">
              <!-- Current Content -->
              <div class="diff-side current">
                <div class="diff-header">
                  <span class="diff-label">Current (Master)</span>
                  <span class="line-count">{{ section.current_content.split('\n').length }} lines</span>
                </div>
                <pre class="diff-content current"><code>{{ section.current_content }}</code></pre>
              </div>

              <!-- Incoming Content -->
              <div class="diff-side incoming">
                <div class="diff-header">
                  <span class="diff-label">Incoming ({{ section.branch_name }})</span>
                  <span class="line-count">{{ section.incoming_content.split('\n').length }} lines</span>
                </div>
                <pre class="diff-content incoming"><code>{{ section.incoming_content }}</code></pre>
              </div>
            </div>

            <!-- Base Content (if 3-way merge) -->
            <div v-if="section.base_content" class="diff-side base">
              <div class="diff-header">
                <span class="diff-label">Base (Common Ancestor)</span>
                <span class="line-count">{{ section.base_content.split('\n').length }} lines</span>
              </div>
              <pre class="diff-content base"><code>{{ section.base_content }}</code></pre>
            </div>
          </div>
        </div>

        <!-- Resolution Preview -->
        <div class="resolution-preview">
          <h4>Resolution Preview</h4>
          <pre class="preview-content"><code>{{ generateResolutionPreview() }}</code></pre>
          <button 
            @click="applyAutoResolution" 
            class="btn-apply"
            :disabled="!hasSelections || resolving"
          >
            {{ resolving ? 'Applying...' : 'Apply Resolution' }}
          </button>
        </div>
      </div>

      <!-- Manual Resolution Editor -->
      <div v-else class="manual-resolve-view">
        <div class="editor-header">
          <h4>Manual Resolution Editor</h4>
          <p>Edit the content below to resolve the conflict manually:</p>
        </div>
        
        <div class="editor-content">
          <textarea 
            v-model="manualContent"
            class="manual-editor"
            rows="20"
            placeholder="Enter your resolved content here..."
          ></textarea>
        </div>

        <div class="editor-actions">
          <button 
            @click="applyManualResolution" 
            class="btn-apply"
            :disabled="!manualContent.trim() || resolving"
          >
            {{ resolving ? 'Applying...' : 'Apply Manual Resolution' }}
          </button>
          <button @click="resetManualContent" class="btn-reset">
            Reset to Original
          </button>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import gitService from '@/api/service/gitService';

const props = defineProps({
  projectName: String,
  branchName: String,
  filename: String,
});

const emit = defineEmits(['resolved', 'cancelled']);

const loading = ref(true);
const resolving = ref(false);
const error = ref('');
const conflictData = ref(null);
const isManualMode = ref(false);
const sectionSelections = ref({});
const manualContent = ref('');

const hasSelections = computed(() => {
  return Object.keys(sectionSelections.value).length > 0;
});

onMounted(async () => {
  await loadConflictDetails();
});

async function loadConflictDetails() {
  try {
    loading.value = true;
    const response = await gitService.getConflictDetails(
      props.projectName,
      props.branchName,
      props.filename
    );
    
    conflictData.value = response;
    
    // Initialize manual content with original file content
    if (response.conflict_content.full_content) {
      manualContent.value = response.conflict_content.full_content;
    }
    
  } catch (e) {
    error.value = 'Failed to load conflict details';
    console.error('Error loading conflict details:', e);
  } finally {
    loading.value = false;
  }
}

function selectSectionContent(sectionIndex, choice) {
  sectionSelections.value[sectionIndex] = choice;
}

function generateResolutionPreview() {
  if (!conflictData.value?.conflict_content?.merge_data?.conflict_sections) {
    return '';
  }

  let resolvedContent = '';
  const sections = conflictData.value.conflict_content.merge_data.conflict_sections;
  
  sections.forEach((section, index) => {
    const selection = sectionSelections.value[index];
    
    switch (selection) {
      case 'current':
        resolvedContent += section.current_content + '\n';
        break;
      case 'incoming':
        resolvedContent += section.incoming_content + '\n';
        break;
      case 'both':
        resolvedContent += section.current_content + '\n' + section.incoming_content + '\n';
        break;
      default:
        resolvedContent += `// UNRESOLVED CONFLICT ${index + 1}\n`;
        resolvedContent += section.current_content + '\n';
        resolvedContent += '// END CONFLICT\n';
    }
  });
  
  return resolvedContent;
}

async function acceptCurrent() {
  try {
    resolving.value = true;
    await gitService.resolveConflicts(
      props.projectName,
      props.branchName,
      'accept_current',
      props.filename
    );
    emit('resolved');
  } catch (e) {
    error.value = 'Failed to accept current version';
    console.error('Error accepting current:', e);
  } finally {
    resolving.value = false;
  }
}

async function acceptIncoming() {
  try {
    resolving.value = true;
    await gitService.resolveConflicts(
      props.projectName,
      props.branchName,
      'accept_incoming',
      props.filename
    );
    emit('resolved');
  } catch (e) {
    error.value = 'Failed to accept incoming version';
    console.error('Error accepting incoming:', e);
  } finally {
    resolving.value = false;
  }
}

async function applyAutoResolution() {
  try {
    resolving.value = true;
    const resolvedContent = generateResolutionPreview();
    
    await gitService.resolveConflictManually(
      props.projectName,
      props.branchName,
      props.filename,
      resolvedContent
    );
    
    emit('resolved');
  } catch (e) {
    error.value = 'Failed to apply resolution';
    console.error('Error applying resolution:', e);
  } finally {
    resolving.value = false;
  }
}

async function applyManualResolution() {
  try {
    resolving.value = true;
    
    await gitService.resolveConflictManually(
      props.projectName,
      props.branchName,
      props.filename,
      manualContent.value
    );
    
    emit('resolved');
  } catch (e) {
    error.value = 'Failed to apply manual resolution';
    console.error('Error applying manual resolution:', e);
  } finally {
    resolving.value = false;
  }
}

function toggleManualMode() {
  isManualMode.value = !isManualMode.value;
  if (isManualMode.value && hasSelections.value) {
    // Pre-fill with current selection preview
    manualContent.value = generateResolutionPreview();
  }
}

function resetManualContent() {
  if (conflictData.value?.conflict_content?.full_content) {
    manualContent.value = conflictData.value.conflict_content.full_content;
  }
}
</script>

<style scoped>
.conflict-merge-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.merge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.merge-actions {
  display: flex;
  gap: 10px;
}

.btn-accept, .btn-manual, .btn-apply, .btn-reset {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-accept.current {
  background: #2196f3;
  color: white;
}

.btn-accept.incoming {
  background: #4caf50;
  color: white;
}

.btn-manual {
  background: #ff9800;
  color: white;
}

.btn-apply {
  background: #4caf50;
  color: white;
}

.btn-reset {
  background: #666;
  color: white;
}

.conflict-section {
  margin-bottom: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f5f5;
  padding: 10px 15px;
}

.section-actions {
  display: flex;
  gap: 5px;
}

.btn-select {
  padding: 4px 8px;
  border: 1px solid #ccc;
  border-radius: 3px;
  background: white;
  cursor: pointer;
  font-size: 12px;
}

.btn-select.active {
  background: #2196f3;
  color: white;
  border-color: #2196f3;
}

.diff-view {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: #ddd;
}

.diff-side {
  background: white;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  font-size: 14px;
}

.diff-label {
  font-weight: 600;
}

.line-count {
  color: #666;
  font-size: 12px;
}

.diff-content {
  margin: 0;
  padding: 15px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.diff-content.current {
  background: #fff5f5;
  border-left: 4px solid #f56565;
}

.diff-content.incoming {
  background: #f0fff4;
  border-left: 4px solid #48bb78;
}

.diff-content.base {
  background: #fffbf0;
  border-left: 4px solid #ed8936;
}

.resolution-preview {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.preview-content {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  margin: 10px 0;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  max-height: 200px;
  overflow-y: auto;
}

.manual-editor {
  width: 100%;
  min-height: 400px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
}

.editor-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.loading, .error-message {
  text-align: center;
  padding: 20px;
}

.error-message {
  background: #fee;
  color: #c33;
  border: 1px solid #fcc;
  border-radius: 4px;
}
</style>