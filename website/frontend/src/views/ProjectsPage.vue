<template>
  <div>
    <div class="project-page-root">
      <h1 class="project-page-title">
        {{ t('projectsPage.title', { instanceName: instanceName }) }}
      </h1>

      <!-- Section 1: Project List as Card Grid -->
      <div class="project-page-section project-page-section-card">
        <div class="project-list-header">
          <span class="project-list-title">{{
            t('projectsPage.projectListTitle')
          }}</span>
          <button
            class="project-page-create-btn"
            @click="showCreateDialog = true"
          >
            <font-awesome-icon icon="fa-solid fa-plus" />
            {{ t('projectsPage.createProject') }}
          </button>
        </div>
        <template v-if="(projectStore.projects?.length || 0) === 0">
          <div class="project-page-no-projects">
            {{ t('projectsPage.noProjects') }}
          </div>
        </template>
        <template v-else>
          <div class="project-page-card-grid">
            <div
              v-for="project in paginatedProjects"
              :key="project.project_id"
              :class="[
                'project-card',
                {
                  'project-card-active':
                    project.project_id === currentProjectId,
                },
              ]"
              @click="selectProject(project)"
            >
              <!-- Row 1: Name + Actions -->
              <div class="project-card-row project-card-row-header">
                <div class="project-card-title-container">
                  <span
                    class="project-card-title"
                    :title="project.project_name"
                  >
                    <font-awesome-icon
                      icon="fa-diagram-project"
                      class="project-card-title-icon"
                    />
                    {{ project.project_name }}
                  </span>
                </div>
                <div class="project-card-actions">
                  <button
                    class="project-card-action-btn edit"
                    :title="t('projectsPage.project.buttons.rename')"
                    @click.stop="openEditDialog(project)"
                  >
                    <font-awesome-icon icon="fa-regular fa-pen-to-square" />
                  </button>
                  <button
                    v-if="isAdmin"
                    class="project-card-action-btn share"
                    :title="t('projectsPage.project.buttons.share')"
                    @click.stop="openShareModal(project)"
                  >
                    <font-awesome-icon icon="fa-regular fa-share-from-square" />
                  </button>
                  <button
                    class="project-card-action-btn config"
                    :title="t('projectsPage.project.buttons.settings')"
                    @click.stop="goToStandardsPage(project)"
                  >
                    <font-awesome-icon icon="fa-solid fa-gears" />
                  </button>
                  <button
                    class="project-card-action-btn project-card-delete-btn"
                    :title="t('projectsPage.project.buttons.delete')"
                    @click.stop="deleteProject(project.project_name)"
                  >
                    <font-awesome-icon icon="trash" />
                  </button>
                </div>
              </div>
              <!-- Row 2: Description -->
              <div class="project-card-row project-card-row-desc">
                <div class="project-card-desc-icon-section">
                  <font-awesome-icon
                    icon="fa-regular fa-comment-dots"
                    class="project-card-desc-icon-white"
                  />
                </div>
                <div
                  class="project-card-desc-container project-card-desc-container-contrast"
                >
                  <div class="project-card-desc-scroll">
                    <span class="project-card-desc-text">
                      {{
                        project.project_description ||
                        t('projectsPage.noDescription')
                      }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- Pagination Controls -->
          <div v-if="totalPages > 1" class="project-page-pagination">
            <button
              :disabled="currentPage === 1"
              class="pagination-arrow-btn"
              @click="prevPage"
            >
              <font-awesome-icon icon="fa-solid fa-angles-left" />
            </button>
            <input
              v-model.number="currentPage"
              type="number"
              min="1"
              :max="totalPages"
              class="project-page-pagination-input"
              @change="goToPage(currentPage)"
            />
            <span>/ {{ totalPages }}</span>
            <button
              class="pagination-arrow-btn"
              :disabled="currentPage === totalPages"
              @click="nextPage"
            >
              <font-awesome-icon icon="fa-solid fa-angles-right" />
            </button>
          </div>
        </template>
      </div>

      <!-- Section Divider: only show if there are projects and a project is selected -->
      <div
        v-if="(projectStore.projects?.length || 0) > 0 && currentProjectName"
        class="project-page-section-divider"
      ></div>

      <!-- Section 2: Project Details (only if selected) -->
      <div
        v-if="currentProjectName"
        class="project-page-section project-page-section-card"
      >
        <div class="project-page-files-tree-section">
          <div class="project-page-files-tree-title-row">
            <div class="project-page-files-tree-title">
              {{
                t('projectsPage.filesInProject', {
                  projectName: currentProjectName,
                })
              }}
            </div>
            <button
              class="project-page-create-btn"
              :disabled="syncing"
              @click="openSyncDialog"
            >
              <font-awesome-icon
                icon="fa-solid fa-retweet"
                class="project-page-sync-icon"
              />
              {{
                syncing
                  ? t('projectsPage.synchronizing')
                  : t('projectsPage.synchronize')
              }}
            </button>
          </div>
          <div v-if="filesLoading" class="project-page-loading">
            {{ t('projectsPage.loadingFiles') }}
          </div>
          <div v-else>
            <FileTree v-if="projectFiles" :files="projectFiles.files"/>
            <div v-else class="project-page-loading">
              {{ t('projectsPage.noFilesFound') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Project Create Modal -->
      <ProjectCreateDialog
        v-if="showCreateDialog"
        @close="showCreateDialog = false"
        @created="onProjectCreated"
      />

      <!-- Edit Project Section -->
      <ProjectEditDialog
        v-if="editDialogVisible"
        :project="editingProject"
        @close="closeEditDialog"
        @edited="onProjectEdited"
      />

      <!-- Project Share Modal -->
      <ProjectShareModal
        :show="showShareModal"
        :project-name="shareProjectName"
        @close="closeShareModal"
        @success="onShareSuccess"
      />

      <!-- Sync Dialog -->
      <ProjectSyncDialog
        v-model:visible="syncDialogVisible"
        :project-name="currentProjectName"
        :is-admin="isAdmin"
        @sync-completed="handleSyncCompleted"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useProjectStore } from '@stores/project';
import { useUserStore } from '@stores/user';
import { useAppInfoStore } from '@stores/appInfo';
import gitService from '@api/service/gitService';
import FileTree from '@components/common/FileTree.vue';
import ProjectCreateDialog from '@/components/pageSpecific/projectsPage/ProjectCreateDialog.vue';
import ProjectShareModal from '@components/common/ProjectShareModal.vue';
import ProjectSyncDialog from '@/components/pageSpecific/projectsPage/ProjectSyncDialog.vue';
import ProjectEditDialog from '@/components/pageSpecific/projectsPage/ProjectEditDialog.vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUserConfirm } from '@/composables/useUserConfirm';
import { useHead } from '@unhead/vue';

const projectStore = useProjectStore();
const userStore = useUserStore();
const appInfoStore = useAppInfoStore();
const router = useRouter();
const projects = ref([]);
const loading = ref(true);
const { t } = useI18n();

useHead({
  title: computed(() => t('projectsPage.pageTitle')),
  meta: [
    {
      name: 'description',
      content: computed(() => t('projectsPage.pageDescription')),
    },
  ],
});

const instanceName = computed(
  () => appInfoStore.instance?.instance_name || 'ELANORA'
);

const showCreateDialog = ref(false);

const projectFiles = ref(null);
const filesLoading = ref(false);

const currentProjectId = computed(
  () => projectStore.currentProject?.project_id
);
const currentProjectName = computed(
  () => projectStore.currentProject?.project_name
);

const syncing = ref(false);
const syncDialogVisible = ref(false);

// Share modal state
const showShareModal = ref(false);
const shareProjectName = ref('');

// Check if user is admin
const isAdmin = computed(() => userStore.user?.role === 'admin');

// Pagination state
const pageSize = 6;
const currentPage = ref(1);

const totalPages = computed(() =>
  Math.max(1, Math.ceil((projectStore.projects?.length || 0) / pageSize))
);

const paginatedProjects = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return projectStore.projects.slice(start, start + pageSize);
});

function goToPage(page) {
  let num = Number(page);
  if (isNaN(num) || num < 1) num = 1;
  if (num > totalPages.value) num = totalPages.value;
  currentPage.value = num;
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++;
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value--;
}

// Reset to page 1 if projects change and current page is out of bounds
watch(
  () => projectStore.projects?.length,
  () => {
    if (currentPage.value > totalPages.value) currentPage.value = 1;
  }
);

watch(currentPage, (val) => {
  if (val < 1) currentPage.value = 1;
  if (val > totalPages.value) currentPage.value = totalPages.value;
});

async function fetchProjects() {
  loading.value = true;
  try {
    const res = await gitService.listUserProjects();
    projects.value = res.projects;
    projectStore.setProjects(res.projects);
    if (res.projects.length === 0) {
      projectStore.clearCurrentProject();
      projectFiles.value = null;
    }
  } finally {
    loading.value = false;
  }
}

function selectProject(project) {
  projectStore.setCurrentProject(project);
}

async function fetchProjectFiles() {
  if (!currentProjectName.value) {
    projectFiles.value = null;
    return;
  }
  filesLoading.value = true;
  try {
    const res = await gitService.listProjectFiles(currentProjectName.value);
    projectFiles.value = res;
  } finally {
    filesLoading.value = false;
  }
}

async function openSyncDialog() {
  if (!currentProjectName.value) return;
  syncing.value = true;
  syncDialogVisible.value = true;
  syncing.value = false;
}

function handleSyncCompleted() {
  fetchProjectFiles();
  fetchProjects();
}

const userConfirm = useUserConfirm();

async function deleteProject(projectName) {
  const confirmed = await userConfirm({
    title: t('projectsPage.deleteTitle'),
    message: t('projectsPage.deleteMessage', { projectName }),
    confirmText: t('projectsPage.deleteConfirm'),
    cancelText: t('projectsPage.deleteCancel'),
  });
  if (!confirmed) return;

  try {
    await gitService.deleteProject(projectName);
    await fetchProjects();
    if (currentProjectName.value === projectName) {
      projectStore.clearCurrentProject();
      projectFiles.value = null;
    }
  } catch {
    console.error('Failed to delete project:', projectName);
  }
}

const editDialogVisible = ref(false);
const editingProject = ref(null);

function openEditDialog(project) {
  editingProject.value = project;
  editDialogVisible.value = true;
}

function closeEditDialog() {
  editingProject.value = null;
  editDialogVisible.value = false;
}

async function onProjectEdited() {
  closeEditDialog();
  await fetchProjects();
}

function openShareModal(project) {
  shareProjectName.value = project.project_name;
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

watch(
  [() => projectStore.projects, currentProjectName],
  ([projectsVal, currentProjectVal]) => {
    if (
      projectsVal.length > 0 &&
      currentProjectVal &&
      projectsVal.some((p) => p.project_name === currentProjectVal)
    ) {
      fetchProjectFiles();
    }
  },
  { immediate: true }
);

onMounted(() => {
  if (projectStore.projects.length === 0) {
    fetchProjects();
  }
  projectStore.loadCurrentProject();
});

function goToStandardsPage(project) {
  router.push({
    name: 'ProjectConfigurationPage',
    params: { projectId: project.project_id },
  });
}

function onProjectCreated() {
  showCreateDialog.value = false;
  fetchProjects();
}
</script>

<style src="@/assets/css/projects-page.css"></style>
