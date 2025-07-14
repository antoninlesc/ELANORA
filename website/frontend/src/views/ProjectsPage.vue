<template>
  <div class="project-page-root">
    <h1 class="project-page-title">Projects</h1>

    <!-- Create Project Section -->
    <form class="project-page-create-form" @submit.prevent="createProject">
      <div class="project-page-create-fields">
        <input
          v-model="newProjectName"
          class="project-page-create-input"
          type="text"
          placeholder="Project name"
          required
        />
        <input
          v-model="newProjectDescription"
          class="project-page-create-input"
          type="text"
          placeholder="Description"
          required
        />
        <button class="project-page-create-btn" :disabled="creating">
          {{ creating ? 'Creating...' : 'Create Project' }}
        </button>
        <button
          class="project-page-create-btn"
          type="button"
          style="margin-left: 8px"
          @click="showInitDialog = true"
        >
          Init from Folder
        </button>
      </div>
      <div v-if="createError" class="project-page-create-error">
        {{ createError }}
      </div>
    </form>

    <div v-if="loading" class="project-page-loading">Loading projects...</div>
    <div v-else class="project-page-list">
      <div
        v-for="project in projects"
        :key="project"
        :class="[
          'project-page-project-box',
          { 'project-page-active': project === currentProjectName },
        ]"
        @click="selectProject(project)"
      >
        <span class="project-page-project-name">{{ project }}</span>
        <span
          v-if="project === currentProjectName"
          class="project-page-feedback"
          >Active</span
        >
      </div>
    </div>
    <div v-if="feedback" class="project-page-feedback-message">
      {{ feedback }}
    </div>

    <!-- Initialize Project from Folder Section -->
    <div class="project-page-init-section">
      <button
        v-if="!showInitDialog"
        class="project-page-init-btn"
        @click="showInitDialog = true"
      >
        Initialize Project from Folder
      </button>

      <!-- Modal for initializing from folder -->
      <div
        v-if="showInitDialog"
        class="project-page-root"
        style="
          position: fixed;
          top: 0;
          left: 0;
          width: 100vw;
          height: 100vh;
          background: rgb(0 0 0 / 25%);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
        "
      >
        <div
          style="
            background: #fff;
            padding: 32px 24px;
            border-radius: 16px;
            box-shadow: 0 2px 16px rgb(0 0 0 / 8%);
            min-width: 320px;
          "
        >
          <h2 style="margin-bottom: 18px">Init Project from Folder</h2>
          <form @submit.prevent="initFromFolder">
            <input
              v-model="initProjectName"
              class="project-page-create-input"
              type="text"
              placeholder="Project name"
              required
            />
            <input
              v-model="initProjectDescription"
              class="project-page-create-input"
              type="text"
              placeholder="Description"
              required
              style="margin-top: 8px"
            />
            <input
              ref="folderInput"
              type="file"
              webkitdirectory
              directory
              multiple
              style="margin-top: 8px"
              required
              @change="onFolderChange"
            />
            <div style="margin-top: 16px; display: flex; gap: 12px">
              <button class="project-page-create-btn" :disabled="initing">
                {{ initing ? 'Initializing...' : 'Init' }}
              </button>
              <button
                class="project-page-create-btn"
                type="button"
                style="background: #bdbdbd"
                @click="showInitDialog = false"
              >
                Cancel
              </button>
            </div>
            <div v-if="initError" class="project-page-create-error">
              {{ initError }}
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Project Files Section -->
    <div class="project-page-files-section">
      <h2 class="project-page-files-title">Project Files</h2>
      <div v-if="filesLoading" class="project-page-files-loading">
        Loading files...
      </div>
      <div
        v-else-if="!projectFiles || projectFiles.length === 0"
        class="project-page-no-files"
      >
        No files found in this project.
      </div>
      <div v-else class="project-page-files-list">
        <div
          v-for="file in projectFiles"
          :key="file.path"
          class="project-page-file-item"
        >
          <span class="project-page-file-name">{{ file.path }}</span>
          <span class="project-page-file-type">{{ file.type }}</span>
        </div>
      </div>
    </div>

    <!-- Project Files Tree -->
    <div v-if="currentProjectName" style="margin-top: 32px">
      <h2
        class="project-page-title"
        style="font-size: 1.3rem; margin-bottom: 12px"
      >
        Files in "{{ currentProjectName }}"
      </h2>
      <div v-if="filesLoading" class="project-page-loading">
        Loading files...
      </div>
      <div v-else>
        <FileTree v-if="projectFiles" :tree="projectFiles" :level="0" />
        <div v-else class="project-page-loading">No files found.</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useProjectStore } from '@/stores/project';
import gitService from '@/api/service/gitService';
import FileTree from '@/components/common/FileTree.vue';

const projectStore = useProjectStore();
const projects = ref([]);
const loading = ref(true);
const feedback = ref('');

const newProjectName = ref('');
const newProjectDescription = ref('');
const creating = ref(false);
const createError = ref('');

const showInitDialog = ref(false);
const initProjectName = ref('');
const initProjectDescription = ref('');
const initing = ref(false);
const initError = ref('');

const projectFiles = ref(null);
const filesLoading = ref(false);

const folderInput = ref(null);
const selectedFiles = ref([]);

const currentProjectName = computed(
  () =>
    projectStore.currentProject?.project_name ||
    projectStore.currentProject?.name ||
    projectStore.currentProject
);

async function fetchProjects() {
  loading.value = true;
  try {
    const res = await gitService.listProjects();
    projects.value = res.projects;
  } catch {
    feedback.value = 'Failed to load projects.';
  } finally {
    loading.value = false;
  }
}

function selectProject(project) {
  projectStore.setCurrentProject(project);
  feedback.value = `Switched to project: ${project}`;
}

async function createProject() {
  createError.value = '';
  if (!newProjectName.value.trim() || !newProjectDescription.value.trim()) {
    createError.value = 'Please enter a name and description.';
    return;
  }
  creating.value = true;
  try {
    await gitService.createProject({
      project_name: newProjectName.value.trim(),
      description: newProjectDescription.value.trim(),
    });
    feedback.value = `Project "${newProjectName.value}" created!`;
    newProjectName.value = '';
    newProjectDescription.value = '';
    await fetchProjects();
  } catch (e) {
    createError.value =
      e?.response?.data?.detail || 'Failed to create project.';
  } finally {
    creating.value = false;
  }
}

async function fetchProjectFiles() {
  if (!currentProjectName.value) {
    projectFiles.value = null;
    return;
  }
  filesLoading.value = true;
  try {
    const res = await gitService.listProjectFiles(currentProjectName.value);
    projectFiles.value = res.tree || null;
  } catch {
    projectFiles.value = null;
  } finally {
    filesLoading.value = false;
  }
}

async function initFromFolder() {
  initError.value = '';
  if (!initProjectName.value.trim() || !initProjectDescription.value.trim()) {
    initError.value = 'Please fill in all fields.';
    return;
  }
  if (!selectedFiles.value.length) {
    initError.value = 'Please select a folder with .eaf files.';
    return;
  }
  initing.value = true;
  try {
    await gitService.initProjectFromFolderUpload({
      project_name: initProjectName.value.trim(),
      description: initProjectDescription.value.trim(),
      files: selectedFiles.value,
    });
    feedback.value = `Project "${initProjectName.value}" initialized from folder!`;
    showInitDialog.value = false;
    initProjectName.value = '';
    initProjectDescription.value = '';
    await fetchProjects();
  } catch (e) {
    initError.value =
      e?.response?.data?.detail || 'Failed to initialize project.';
  } finally {
    initing.value = false;
  }
}

function onFolderChange(e) {
  selectedFiles.value = Array.from(e.target.files);
}

// Fetch files when current project changes
watch(currentProjectName, fetchProjectFiles);

onMounted(() => {
  fetchProjects();
  projectStore.loadCurrentProject();
});
</script>

<style src="@/assets/css/project-page.css"></style>
