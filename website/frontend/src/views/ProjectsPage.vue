<template>
  <div>
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
        <!-- Replace your project list loop with this -->
        <div
          v-for="project in projectStore.projects"
          :key="project"
          :class="[
            'project-page-project-box',
            { 'project-page-active': project === currentProjectName },
          ]"
          @click="selectProject(project)"
        >
          <div style="display: flex; align-items: center">
            <span class="project-page-project-name">{{ project }}</span>
            <span
              v-if="project === currentProjectName"
              class="project-page-feedback"
              >Active</span
            >
          </div>
          <div class="project-page-actions">
            <button
              class="project-page-edit-btn"
              title="Rename Project"
              @click.stop="openRenameDialog(project)"
            >
              <font-awesome-icon icon="fa-regular fa-pen-to-square" />
            </button>
            <button
              v-if="isAdmin"
              class="project-page-share-btn"
              title="Share Project"
              @click.stop="openShareModal(project)"
            >
              <font-awesome-icon icon="share" />
            </button>
            <button
              class="project-page-delete-btn"
              title="Delete Project"
              @click.stop="deleteProject(project)"
            >
              <font-awesome-icon icon="trash" />
            </button>
          </div>
        </div>
      </div>

      <!-- Initialize Project from Folder Section -->
      <div class="project-page-init-section">
        <!-- Modal for initializing from folder -->
        <div v-if="showInitDialog" class="project-page-modal-overlay">
          <div class="project-page-modal-content">
            <h2 class="project-page-modal-title">Init Project from Folder</h2>
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
              <UploadFolder v-model="selectedFiles" />
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

      <!-- Rename Project Section -->
      <div v-if="renameDialogVisible" class="project-page-modal-overlay">
        <div class="project-page-modal-content">
          <h2 class="project-page-modal-title">Rename Project</h2>
          <form @submit.prevent="renameProject">
            <input
              v-model="renameInput"
              class="project-page-create-input"
              type="text"
              placeholder="New project name"
              required
            />
            <div style="margin-top: 16px; display: flex; gap: 12px">
              <button class="project-page-create-btn" :disabled="renaming">
                {{ renaming ? 'Renaming...' : 'Rename' }}
              </button>
              <button
                class="project-page-create-btn"
                type="button"
                style="background: #bdbdbd"
                @click="closeRenameDialog"
              >
                Cancel
              </button>
            </div>
            <div v-if="renameError" class="project-page-create-error">
              {{ renameError }}
            </div>
          </form>
        </div>
      </div>

      <!-- Project Files Section -->
      <!-- Project Files Tree -->
      <div v-if="currentProjectName" class="project-page-files-tree-section">
        <div class="project-page-files-tree-title">
          Files in "{{ currentProjectName }}"
          <button
            class="project-page-create-btn"
            style="float: right; margin-left: 16px"
            :disabled="syncing"
            @click="synchronizeProject"
          >
            {{ syncing ? 'Synchronizing...' : 'Synchronize' }}
          </button>
        </div>
        <div v-if="filesLoading" class="project-page-loading">
          Loading files...
        </div>
        <div v-else>
          <FileTree v-if="projectFiles" :tree="projectFiles" :level="0" />
          <div v-else class="project-page-loading">No files found.</div>
        </div>
      </div>

      <!-- Project Share Modal -->
      <ProjectShareModal
        :show="showShareModal"
        :project-name="shareProjectName"
        @close="closeShareModal"
        @success="onShareSuccess"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useProjectStore } from '@stores/project';
import { useUserStore } from '@stores/user';
import gitService from '@api/service/gitService';
import FileTree from '@components/common/FileTree.vue';
import UploadFolder from '@components/common/UploadFolder.vue';
import ProjectShareModal from '@components/common/ProjectShareModal.vue';

const projectStore = useProjectStore();
const userStore = useUserStore();
const projects = ref([]);
const loading = ref(true);

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

const selectedFiles = ref([]);

const currentProjectName = computed(
  () =>
    projectStore.currentProject?.project_name ||
    projectStore.currentProject?.name ||
    projectStore.currentProject
);

const syncing = ref(false);

const renameDialogVisible = ref(false);
const renameInput = ref('');
const renaming = ref(false);
const renameError = ref('');
const renamingProject = ref(null);

// Share modal state
const showShareModal = ref(false);
const shareProjectName = ref('');

// Check if user is admin
const isAdmin = computed(() => userStore.user?.role === 'admin');

async function fetchProjects() {
  loading.value = true;
  try {
    const res = await gitService.listProjects();
    projects.value = res.projects;
    projectStore.setProjects(res.projects);
  } finally {
    loading.value = false;
  }
}

function selectProject(project) {
  projectStore.setCurrentProject(project);
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

async function synchronizeProject() {
  if (!currentProjectName.value) return;
  syncing.value = true;
  try {
    await gitService.synchronizeProject(currentProjectName.value);
    await fetchProjectFiles();
    await fetchProjects();
  } catch {
    syncing.value = false;
    console.error('Failed to synchronize project:', currentProjectName.value);
  } finally {
    syncing.value = false;
  }
}

async function deleteProject(projectName) {
  if (
    !confirm(
      `Are you sure you want to delete project "${projectName}"? This cannot be undone.`
    )
  )
    return;
  try {
    await gitService.deleteProject(projectName);
    await fetchProjects();
    if (currentProjectName.value === projectName) {
      projectStore.clearCurrentProject();
      projectFiles.value = null;
    }
  } catch {
    console.error('Failed to delete project:', projectName);
  } finally {
    await fetchProjects();
  }
}

function openRenameDialog(project) {
  renamingProject.value = project;
  renameInput.value = project;
  renameError.value = '';
  renameDialogVisible.value = true;
}

function closeRenameDialog() {
  renamingProject.value = null;
  renameInput.value = '';
  renameError.value = '';
  renameDialogVisible.value = false;
}

async function renameProject() {
  renameError.value = '';
  if (!renameInput.value.trim()) {
    renameError.value = 'Please enter a new project name.';
    return;
  }
  renaming.value = true;
  try {
    await gitService.renameProject(
      renamingProject.value,
      renameInput.value.trim()
    );
    // Update project list and current project reactively
    await fetchProjects();
    if (currentProjectName.value === renamingProject.value) {
      projectStore.renameCurrentProject(renameInput.value.trim());
    }
    closeRenameDialog();
  } catch (e) {
    renameError.value =
      e?.response?.data?.detail || 'Failed to rename project.';
  } finally {
    renaming.value = false;
  }
}

// Share modal functions
function openShareModal(project) {
  shareProjectName.value = project;
  showShareModal.value = true;
}

function closeShareModal() {
  showShareModal.value = false;
  shareProjectName.value = '';
}

function onShareSuccess() {
  // Optionally reload projects or show a success message
  console.log('Project shared successfully');
}

// Fetch files when current project changes
watch(
  [projects, currentProjectName],
  ([projectsVal, currentProjectVal]) => {
    if (
      projectsVal.length > 0 &&
      currentProjectVal &&
      projectsVal.includes(currentProjectVal)
    ) {
      fetchProjectFiles();
    }
  },
  { immediate: true }
);

onMounted(() => {
  fetchProjects();
  projectStore.loadCurrentProject();
});
</script>

<style src="@/assets/css/project-page.css"></style>
