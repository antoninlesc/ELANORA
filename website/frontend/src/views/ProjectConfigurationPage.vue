<template>
  <div>
    <div class="project-standards-page">
      <h1 class="project-standards-title">
        <span v-if="projectName" class="project-standards-title-project-name">
          {{ projectName }}
        </span>
        <span class="project-standards-title-text">
          {{ t('projectSettings.title') }}
        </span>
      </h1>

      <div
        v-for="group in sectionGroups"
        :key="group.key"
        :class="['settings-section', { open: openGroup === group.key }]"
      >
        <div
          class="settings-section-header group-header"
          @click="toggleGroup(group.key)"
        >
          <span>{{ group.title }}</span>
          <span :class="{ open: openGroup === group.key }">&#9660;</span>
        </div>
        <transition name="main-section-height">
          <div v-show="openGroup === group.key">
            <div
              v-for="section in group.sections"
              :key="section.key"
              class="inner-section"
            >
              <div
                class="settings-section-header inner-header"
                @click="toggleSection(section.key)"
              >
                <span>{{ section.title }}</span>
                <span :class="{ open: openSections.includes(section.key) }">&#9660;</span>
              </div>
              <transition name="accordion">
                <div
                  v-show="openSections.includes(section.key)"
                  class="settings-section-body"
                >
                  <component
                    :is="section.component"
                  />
                </div>
              </transition>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import ConfigureNamingStandards from '@components/pageSpecific/projectConfiguration/ConfigureNamingStandards.vue';
import ConfigureFileTypes from '@components/pageSpecific/projectConfiguration/ConfigureFileTypes.vue';
// Stub components for demo
const ConfigureProjectMembers = { template: '<div>Members & Access</div>' };
const ConfigurePendingInvitations = { template: '<div>Invitations</div>' };

import { ref, computed } from 'vue';
import { useProjectStore } from '@stores/project.js';
import { useI18n } from 'vue-i18n';

import '@/assets/css/ProjectConfigurationPage.css';

const openGroup = ref(null);
// Change to array for multiple open subsections
const openSections = ref([]);

function toggleGroup(group) {
  openGroup.value = openGroup.value === group ? null : group;
  // Optionally clear openSections when switching group
  openSections.value = [];
}
function toggleSection(section) {
  const idx = openSections.value.indexOf(section);
  if (idx === -1) {
    openSections.value.push(section);
  } else {
    openSections.value.splice(idx, 1);
  }
}

const { t } = useI18n();
const projectStore = useProjectStore();
const projectName = computed(() => projectStore.projectName);

const sectionGroups = [
  {
    key: 'technical',
    title: 'Technical Settings',
    sections: [
      {
        key: 'filetypes',
        title: 'File Types',
        component: ConfigureFileTypes,
      },
      {
        key: 'naming',
        title: 'Naming Standards',
        component: ConfigureNamingStandards,
      },
    ],
  },
  {
    key: 'collaborators',
    title: 'Collaborators',
    sections: [
      {
        key: 'members',
        title: 'Members & Access',
        component: ConfigureProjectMembers,
      },
      {
        key: 'invitations',
        title: 'Invitations',
        component: ConfigurePendingInvitations,
      },
    ],
  },
];
</script>
