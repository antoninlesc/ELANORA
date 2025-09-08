<template>
  <div class="upload-page">
    <div class="upload-container">
      <h1 class="upload-title">{{ $t('uploadPage.title') }}</h1>

      <!-- Project Selection -->
      <div class="project-selection">
        <label for="projectSelect" class="project-label">{{ $t('uploadPage.projectSelection.label') }}</label>
        <select
          id="projectSelect"
          v-model="selectedProject"
          class="project-select"
          :disabled="loading"
        >
          <option value="">{{ $t('uploadPage.projectSelection.placeholder') }}</option>
          <option
            v-for="project in projects"
            :key="project.project_id || project"
            :value="project.project_name || project"
          >
            {{ project.project_name || project }}
          </option>
        </select>
      </div>

      <!-- Upload Component -->
      <div v-if="selectedProject">
        <UploadFolder
          v-model="selectedFiles"
          :title="$t('uploadPage.uploadZone.title')"
          :subtitle="$t('uploadPage.uploadZone.subtitle')"
        />

        <!-- Upload Actions -->
        <div v-if="selectedFiles.length > 0" class="upload-actions">
          <button
            class="upload-btn"
            :disabled="uploading || selectedFiles.length === 0"
            @click="uploadFiles"
          >
            <span v-if="uploading" class="spinner"></span>
            {{ uploading ? $t('uploadPage.uploadingFiles', { count: selectedFiles.length }) : $t('uploadPage.uploadButton') }}
          </button>
        </div>
      </div>

      <!-- Upload Results -->
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
              {{ result.success ? $t('uploadPage.resultSuccess') : $t('uploadPage.resultFailed') }}
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
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import UploadFolder from '@/components/common/UploadFolder.vue';
import gitService from '@/api/service/gitService';
import "@/assets/css/upload-page.css";
import { useUserStore } from '@/stores/user';

const { t } = useI18n();
const projects = ref([]);
const selectedProject = ref('');
const selectedFiles = ref([]);
const uploading = ref(false);
const loading = ref(true);
const uploadResults = ref([]);
const error = ref('');
const userStore = useUserStore();

onMounted(async () => {
  await fetchProjects();
});

const username = computed(
  () => userStore.user?.username || userStore.user?.login || ''
);

async function fetchProjects() {
  try {
    loading.value = true;
    const response = await gitService.listProjects();
    projects.value = response.projects;
  } catch (e) {
    error.value = t('uploadPage.errors.failedToLoadProjects');
    console.error('Error fetching projects:', e);
  } finally {
    loading.value = false;
  }
}

async function uploadFiles() {
  if (!selectedProject.value || selectedFiles.value.length === 0) {
    error.value = t('uploadPage.errors.selectProjectAndFiles');
    return;
  }

  uploading.value = true;
  uploadResults.value = [];
  error.value = '';

  try {
    const response = await gitService.uploadElanFiles(
      selectedProject.value,
      selectedFiles.value,
      username.value
    );

    uploadResults.value = response.files || [];
    selectedFiles.value = []; // Clear files after successful upload
  } catch (e) {
    error.value = e?.response?.data?.detail || t('uploadPage.errors.uploadFailed');
    console.error('Upload error:', e);
  } finally {
    uploading.value = false;
  }
}
</script>

<style scoped>
/* All existing styles remain the same */
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

.upload-btn:hover:not(:disabled) {
  background: #1565c0;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff40;
  border-top: 2px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* ...rest of existing styles... */
</style>