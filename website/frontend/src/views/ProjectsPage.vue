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
            v-if="isAdmin"
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
                <div v-if="isAdmin" class="project-card-actions">
                  <button
                    class="project-card-action-btn edit"
                    :title="t('projectsPage.project.buttons.rename')"
                    @click.stop="openEditDialog(project)"
                  >
                    <font-awesome-icon icon="fa-regular fa-pen-to-square" />
                  </button>
                  <button
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
              v-if="isAdmin"
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
            <!-- INFO BANNER containing the status row (only for admins) -->
            <div
              v-if="isAdmin"
              class="project-page-files-info-banner"
              :class="{
                'info-banner-compliant': hasEffectiveStandard && nonCompliantCount === 0,
                'info-banner-noncompliant': hasEffectiveStandard && nonCompliantCount > 0,
                'info-banner-no-standard': !hasEffectiveStandard
              }"
            >
              <font-awesome-icon
                :icon="getBannerIcon"
                :class="['info-banner-icon', getBannerIconClass]"
              />
              <span class="info-banner-text">
                <template v-if="!hasEffectiveStandard">
                  {{ t('projectsPage.infoBanner.noEffectiveStandard1') }}
                  <button
                    class="info-banner-link"
                    @click="goToStandardsPage(projectStore.currentProject)"
                  >
                    {{ t('projectsPage.infoBanner.noEffectiveStandard2') }}
                  </button>
                  {{ t('projectsPage.infoBanner.noEffectiveStandard3') }}
                </template>
                <template v-else-if="nonCompliantCount > 0">
                  {{ t('projectsPage.infoBanner.nonCompliant', { count: nonCompliantCount }) }} 
                  <button
                    class="info-banner-bulk-rename-link"
                    tabindex="0"
                    @click="openBulkRenameDialog"
                    @keydown.enter="openBulkRenameDialog"
                  >
                    {{ t('projectsPage.infoBanner.bulkRename') }}
                  </button>
                </template>
                <template v-else>
                  {{ t('projectsPage.infoBanner.allCompliant') }}
                </template>
              </span>
            </div>
            <div v-if="projectFiles && projectFiles.files && projectFiles.files.length > 0">
              <FileTree 
                :files="projectFiles.files" 
                :show-compliance="isAdmin && hasEffectiveStandard"
                :project-id="currentProjectId"
                :project-name="currentProjectName"
                :media-standard="mediaStandard"
                :project-standard="projectStandard"
              />
            </div>
            <div v-else class="project-page-loading">
              {{ t('projectsPage.noFilesFound') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Project Create Modal (admin only) -->
      <ProjectCreateDialog
        v-if="showCreateDialog && isAdmin"
        @close="showCreateDialog = false"
        @created="onProjectCreated"
      />

      <!-- Edit Project Section (admin only) -->
      <ProjectEditDialog
        v-if="editDialogVisible && isAdmin"
        :project="editingProject"
        @close="closeEditDialog"
        @edited="onProjectEdited"
      />

      <!-- Project Share Modal (admin only) -->
      <ProjectShareModal
        v-if="isAdmin"
        :show="showShareModal"
        :project-name="shareProjectName"
        @close="closeShareModal"
        @success="onShareSuccess"
      />

      <!-- Sync Dialog (admin only) -->
      <ProjectSyncDialog
        v-if="isAdmin"
        v-model:visible="syncDialogVisible"
        :project-name="currentProjectName"
        :is-admin="isAdmin"
        @sync-completed="handleSyncCompleted"
      />

      <!-- BulkRenameDialog (admin only) -->
      <BulkRenameDialog
        v-if="bulkRenameDialogVisible && isAdmin"
        :files="nonCompliantFiles"
        :all-files="projectFiles?.files || []"
        :project-id="currentProjectId"
        @close="bulkRenameDialogVisible = false"
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
import BulkRenameDialog from '@/components/pageSpecific/projectsPage/BulkRenameDialog.vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useUserConfirm } from '@/composables/useUserConfirm';
import { useHead } from '@unhead/vue';
import { useEffectiveStandardStore } from '@/stores/effectiveStandard';
import { useNamingStandardStore } from '@/stores/namingStandard';
import { isFilenameCompliant } from '@/utils/filenameCompliance';
import { getMediaStandardForProject } from '@/utils/filenameFromMediaFile';

const projectStore = useProjectStore();
const userStore = useUserStore();
const appInfoStore = useAppInfoStore();
const router = useRouter();
const projects = ref([]);
const loading = ref(true);
const { t } = useI18n();
const standardName = ref('');

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

// Standard state
const hasEffectiveStandard = ref(false);
const projectStandard = ref(null);
const mediaStandard = ref(null);

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

// Banner computed properties
const getBannerIcon = computed(() => {
  if (!hasEffectiveStandard.value) return 'fa-solid fa-circle-info';
  return nonCompliantCount.value > 0 ? 'fa-solid fa-square-xmark' : 'fa-solid fa-square-check';
});

const getBannerIconClass = computed(() => {
  if (!hasEffectiveStandard.value) return 'icon-no-standard';
  return nonCompliantCount.value > 0 ? 'icon-noncompliant' : 'icon-compliant';
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
    hasEffectiveStandard.value = false;
    return;
  }
  
  // Prevent duplicate calls
  if (filesLoading.value) {
    return;
  }
  
  filesLoading.value = true;
  try {
    const res = await gitService.listProjectFiles(currentProjectName.value, true); // Always include media info

    const PROJECT_FILES_LOCATION_ID = 1;

    // Fetch standards for this project/location
    const effectiveStandardStore = useEffectiveStandardStore();
    await effectiveStandardStore.fetchEffectiveStandards(
      projectStore.currentProject.project_id,
      PROJECT_FILES_LOCATION_ID
    );

    // Fetch naming standards
    const namingStandardStore = useNamingStandardStore();
    await namingStandardStore.fetchStandardsAndComponentNames(currentProjectId.value);

    // Get the first naming standard ID assigned for this location
    let standardId;
    const standardsObj = effectiveStandardStore.effectiveStandards[PROJECT_FILES_LOCATION_ID];
    if (standardsObj && typeof standardsObj === 'object') {
      // Get the first available naming_standard_id
      const ids = Object.values(standardsObj).filter(id => !!id);
      standardId = ids.length > 0 ? ids[0] : undefined;
    } else if (typeof standardsObj === 'string' || typeof standardsObj === 'number') {
      standardId = standardsObj;
    }

    // Check if there's an effective standard
    hasEffectiveStandard.value = !!standardId;

    // Check compliance for each file and add isCompliant property
    const standard = namingStandardStore.standards.find(std => std.id === standardId);
    standardName.value = standard ? standard.name : '';
    
    // Store the project standard for use in FileTree suggestions
    projectStandard.value = standard;
    
    // Get media standard for suggestions
    mediaStandard.value = await getMediaStandardForProject(
      currentProjectId.value, 
      effectiveStandardStore, 
      namingStandardStore
    );
    
    // Only check compliance if there's a standard and user is admin
    res.files = res.files.map(file => {
      const isCompliant = (standard && isAdmin.value) ? isFilenameCompliant(standard, file.name) : true;
      return {
        ...file,
        isCompliant,
      };
    });
    
    projectFiles.value = res;
  } finally {
    filesLoading.value = false;
  }
}

async function openSyncDialog() {
  if (!currentProjectName.value || !isAdmin.value) return;
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
  if (!isAdmin.value) return;
  
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
  if (!isAdmin.value) return;
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
  if (!isAdmin.value) return;
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
  projectStore.initBroadcastChannel();
  projectStore.loadCurrentProject();
});

function goToStandardsPage(project) {
  if (!isAdmin.value) return;
  router.push({
    name: 'ProjectConfigurationPage',
    params: { projectId: project.project_id },
  });
}

function onProjectCreated() {
  showCreateDialog.value = false;
  fetchProjects();
}

const nonCompliantFiles = computed(() =>
  (isAdmin.value && hasEffectiveStandard.value) 
    ? (projectFiles.value?.files?.filter(f => f.isCompliant === false) || [])
    : []
);
const nonCompliantCount = computed(() => nonCompliantFiles.value.length);

const bulkRenameDialogVisible = ref(false);
function openBulkRenameDialog() {
  if (!isAdmin.value) return;
  bulkRenameDialogVisible.value = true;
}
</script>

<style src="@/assets/css/projects-page.css"></style>
