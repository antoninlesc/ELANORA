<template>
  <div>
    <div class="project-standards-page">
      <h1 class="project-standards-title">Project Settings</h1>
      <!-- File Types Section -->
      <div class="settings-section">
        <div
          class="settings-section-header"
          @click="toggleSection('filetypes')"
        >
          <span>File Types</span>
          <span :class="{ open: openSection === 'filetypes' }">&#9660;</span>
        </div>
        <transition name="accordion">
          <div
            v-show="openSection === 'filetypes'"
            class="settings-section-body"
          >
            <ConfigureFileTypes
              :file-types="fileTypeStore.fileTypes"
              :is-loading="fileTypeStore.isLoading"
            />
          </div>
        </transition>
      </div>
      <!-- Naming Standards Section -->
      <div class="settings-section">
        <div class="settings-section-header" @click="toggleSection('naming')">
          <span>Naming Standards</span>
          <span :class="{ open: openSection === 'naming' }">&#9660;</span>
        </div>
        <transition name="accordion">
          <div v-show="openSection === 'naming'" class="settings-section-body">
            <ConfigureNamingStandards
              :standards="standards"
              :file-types="fileTypeStore.fileTypes"
              :component-names="componentNames"
              :loading="loading"
              @refresh="fetchProjectConfiguration"
            />
          </div>
        </transition>
      </div>
      <!-- Add more sections as needed -->
    </div>
  </div>
</template>

<script setup>
import ConfigureNamingStandards from '@components/common/ConfigureNamingStandards.vue';
import ConfigureFileTypes from '@components/common/ConfigureFileTypes.vue';
import { ref, onMounted, watch } from 'vue';
import projectConfigurationApi from '@/api/service/projectConfiguration.js';
import { useFileTypeStore } from '@stores/fileType.js';
import { useProjectStore } from '@stores/project.js';

import '@/assets/css/ProjectConfigurationPage.css';

const openSection = ref(null);
function toggleSection(section) {
  openSection.value = openSection.value === section ? null : section;
}

const fileTypeStore = useFileTypeStore();
const projectStore = useProjectStore();
const standards = ref([]);
const componentNames = ref([]);
const loading = ref(true);

async function fetchProjectConfiguration() {
  loading.value = true;
  try {
    const { data } = await projectConfigurationApi.getProjectConfiguration(
      projectStore.projectId
    );
    fileTypeStore.fileTypes = data.file_types;
    standards.value = data.standards;
    componentNames.value = data.component_names;
  } finally {
    loading.value = false;
  }
}

onMounted(fetchProjectConfiguration);

watch(
  () => projectStore.currentProject,
  (val) => {
    console.log('Current project changed:', val);
  },
  { immediate: true }
);
</script>
