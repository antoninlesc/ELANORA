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
import "@/assets/css/upload-page.css";

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
  //TODO : use env variable

  if (eafFiles.length !== files.length) {
    error.value = 'Only .eaf files are allowed';
    setTimeout(() => error.value = '', 3000);
  }
  //TODO : use env variable
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

<style></style>