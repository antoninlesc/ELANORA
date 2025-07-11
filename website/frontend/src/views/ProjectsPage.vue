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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useProjectStore } from '@/stores/project';
import gitService from '@/api/service/gitService';

const projectStore = useProjectStore();
const projects = ref([]);
const loading = ref(true);
const feedback = ref('');

const newProjectName = ref('');
const newProjectDescription = ref('');
const creating = ref(false);
const createError = ref('');

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

onMounted(() => {
  fetchProjects();
  projectStore.loadCurrentProject();
});
</script>

<style src="@/assets/css/project-page.css"></style>
