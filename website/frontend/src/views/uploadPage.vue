<template>
  <div class="upload-page">
    <div class="upload-container">
      <h1 class="upload-title">Upload ELAN Files</h1>
      
      <!-- Project Selection -->
      <div class="project-selection">
        <label for="projectSelect" class="project-label">Select Project:</label>
        <select 
          id="projectSelect" 
          v-model="selectedProject" 
          class="project-select"
          :disabled="loading"
        >
          <option value="">Choose a project...</option>
          <option v-for="project in projects" :key="project" :value="project">
            {{ project }}
          </option>
        </select>
      </div>

      <!-- Upload Zone -->
      <div 
        v-if="selectedProject"
        class="upload-zone"
        :class="{ 'dragover': isDragOver, 'uploading': uploading }"
        @drop="handleDrop"
        @dragover.prevent="isDragOver = true"
        @dragleave="isDragOver = false"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".eaf"
          style="display: none"
          @change="handleFileSelect"
        />
        
        <div v-if="!uploading" class="upload-content">
          <div class="upload-icon">📁</div>
          <h3>Drop ELAN files here or click to browse</h3>
          <p>Only .eaf files are accepted (max 50MB per file)</p>
        </div>
        
        <div v-else class="upload-progress">
          <div class="spinner"></div>
          <p>Uploading {{ selectedFiles.length }} file(s)...</p>
        </div>
      </div>

      <!-- Selected Files Preview -->
      <div v-if="selectedFiles.length > 0 && !uploading" class="files-preview">
        <h3>Selected Files ({{ selectedFiles.length }})</h3>
        <div class="files-list">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
            <button @click="removeFile(index)" class="remove-btn">×</button>
          </div>
        </div>
        
        <div class="upload-actions">
          <button 
            @click="uploadFiles" 
            class="upload-btn"
            :disabled="uploading || selectedFiles.length === 0"
          >
            Upload Files
          </button>
          <button @click="clearFiles" class="clear-btn">Clear All</button>
        </div>
      </div>

      <!-- Upload Results -->
      <div v-if="uploadResults.length > 0" class="upload-results">
        <h3>Upload Results</h3>
        <div class="results-list">
          <div 
            v-for="result in uploadResults" 
            :key="result.filename"
            class="result-item"
            :class="{ 'success': result.success, 'error': !result.success }"
          >
            <span class="result-filename">{{ result.filename }}</span>
            <span class="result-status">
              {{ result.success ? '✓ Success' : '✗ Failed' }}
            </span>
            <span v-if="result.error" class="result-error">{{ result.error }}</span>
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
const selectedProject = ref('');
const selectedFiles = ref([]);
const uploading = ref(false);
const loading = ref(true);
const isDragOver = ref(false);
const uploadResults = ref([]);
const error = ref('');
const fileInput = ref(null);

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

function triggerFileInput() {
  if (!uploading.value) {
    fileInput.value?.click();
  }
}

function handleFileSelect(event) {
  const files = Array.from(event.target.files);
  addFiles(files);
}

function handleDrop(event) {
  event.preventDefault();
  isDragOver.value = false;
  const files = Array.from(event.dataTransfer.files);
  addFiles(files);
}

function addFiles(files) {
  const eafFiles = files.filter(file => file.name.toLowerCase().endsWith('.eaf'));
  
  if (eafFiles.length !== files.length) {
    error.value = 'Only .eaf files are allowed';
    setTimeout(() => error.value = '', 3000);
  }
  
  // Check file sizes
  const oversizedFiles = eafFiles.filter(file => file.size > 50 * 1024 * 1024);
  if (oversizedFiles.length > 0) {
    error.value = `Some files are too large (max 50MB): ${oversizedFiles.map(f => f.name).join(', ')}`;
    return;
  }
  
  selectedFiles.value = [...selectedFiles.value, ...eafFiles];
  error.value = '';
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1);
}

function clearFiles() {
  selectedFiles.value = [];
  uploadResults.value = [];
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

async function uploadFiles() {
  if (!selectedProject.value || selectedFiles.value.length === 0) {
    error.value = 'Please select a project and files';
    return;
  }
  
  uploading.value = true;
  uploadResults.value = [];
  error.value = '';
  
  try {
    const response = await gitService.uploadElanFiles(
      selectedProject.value, 
      selectedFiles.value, 
      'user'
    );
    
    uploadResults.value = response.files || [];
    
    // Clear selected files on successful upload
    selectedFiles.value = [];
    if (fileInput.value) {
      fileInput.value.value = '';
    }
    
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Upload failed';
    console.error('Upload error:', e);
  } finally {
    uploading.value = false;
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
</script>

<style scoped>
.upload-page {
  max-width: 800px;
  margin: 40px auto;
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
}

.upload-container {
  width: 100%;
}

.upload-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 32px;
  color: #2c3e50;
  text-align: center;
}

.project-selection {
  margin-bottom: 32px;
}

.project-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.project-select {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
}

.project-select:focus {
  outline: none;
  border-color: #1976d2;
}

.upload-zone {
  border: 3px dashed #ddd;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 24px;
}

.upload-zone:hover {
  border-color: #1976d2;
  background: #f8f9fa;
}

.upload-zone.dragover {
  border-color: #1976d2;
  background: #e3f2fd;
}

.upload-zone.uploading {
  cursor: not-allowed;
  opacity: 0.7;
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1976d2;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.files-preview {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.files-list {
  margin: 16px 0;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: white;
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid #e0e0e0;
}

.file-name {
  flex: 1;
  font-weight: 500;
}

.file-size {
  color: #666;
  margin-right: 16px;
}

.remove-btn {
  background: #ff4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.upload-btn, .clear-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}

.upload-btn {
  background: #1976d2;
  color: white;
}

.upload-btn:hover:not(:disabled) {
  background: #1565c0;
}

.upload-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.clear-btn {
  background: #666;
  color: white;
}

.clear-btn:hover {
  background: #555;
}

.upload-results {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
}

.result-item.success {
  background: #e8f5e9;
  border: 1px solid #4caf50;
}

.result-item.error {
  background: #ffebee;
  border: 1px solid #f44336;
}

.result-error {
  color: #f44336;
  font-size: 0.9rem;
}

.error-message {
  background: #ffebee;
  border: 1px solid #f44336;
  color: #d32f2f;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
}
</style>