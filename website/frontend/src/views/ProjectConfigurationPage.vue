<template>
  <div>
    <div class="project-standards-page">
      <h1 class="project-standards-title">
        <span class="project-standards-title-text">
          {{ titleParts.before }}
          <span class="project-standards-title-project-name">{{
            projectName
          }}</span>
          {{ titleParts.after }}
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
          <span>{{ t(group.titleKey) }}</span>
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
                <span>{{ t(section.titleKey) }}</span>
                <span :class="{ open: openSections.includes(section.key) }"
                  >&#9660;</span
                >
              </div>
              <transition name="accordion">
                <div
                  v-show="openSections.includes(section.key)"
                  class="settings-section-body"
                >
                  <component :is="section.component" />
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
import ConfigureProjectMembers from '@components/pageSpecific/projectConfiguration/ConfigureProjectMembers.vue';
import ConfigurePendingInvitations from '@components/pageSpecific/projectConfiguration/ConfigurePendingInvitations.vue';

import { ref, computed } from 'vue';
import { useProjectStore } from '@stores/project.js';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

import '@/assets/css/ProjectConfigurationPage.css';

const openGroup = ref(null);
const openSections = ref([]);

function toggleGroup(group) {
  openGroup.value = openGroup.value === group ? null : group;
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
const route = useRoute();
const { t } = useI18n();
const projectStore = useProjectStore();
const projectId = computed(() => Number(route.params.projectId));
const projectName = computed(() => {
  const project = projectStore.projects.find(
    (p) => p.project_id === projectId.value
  );
  return project ? project.project_name : '';
});

const titleParts = computed(() => {
  // Get the translation with a unique placeholder
  const raw = t('projectSettings.title', { projectName: '___PROJECT___' });
  const [before, after] = raw.split('___PROJECT___');
  return { before, after };
});

const sectionGroups = [
  {
    key: 'technical',
    titleKey: 'projectSettings.sectionNames.sections.technical',
    sections: [
      {
        key: 'filetypes',
        titleKey: 'projectSettings.sectionNames.sections.subsections.fileTypes',
        component: ConfigureFileTypes,
      },
      {
        key: 'naming',
        titleKey:
          'projectSettings.sectionNames.sections.subsections.namingStandards',
        component: ConfigureNamingStandards,
      },
    ],
  },
  {
    key: 'collaborators',
    titleKey: 'projectSettings.sectionNames.sections.collaborators',
    sections: [
      {
        key: 'members',
        titleKey: 'projectSettings.sectionNames.sections.subsections.members',
        component: ConfigureProjectMembers,
      },
      {
        key: 'invitations',
        titleKey:
          'projectSettings.sectionNames.sections.subsections.invitations',
        component: ConfigurePendingInvitations,
      },
    ],
  },
];
</script>
