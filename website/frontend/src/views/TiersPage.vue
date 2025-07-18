<template>
  <div :class="{ 'dragging-disable-interaction': isDragging }">
    <h1 class="tiers-page-title">Tier Hierarchy</h1>
    <div v-if="loading" class="tiers-page-loading">Loading...</div>
    <div v-else-if="error" class="tiers-page-error">{{ error }}</div>
    <div v-else>
      <div class="tiers-tree-main-block">
        <div v-if="useCustomSections" class="tiers-section-controls">
          <!-- Create Section -->
          <form
            class="tiers-section-create-form"
            @submit.prevent="handleCreateSection"
          >
            <input
              v-model="newSectionName"
              placeholder="New section name"
              required
            />
            <button type="submit">Create Section</button>
          </form>
        </div>
        <template v-if="useCustomSections">
          <div
            v-for="section in sections"
            :key="section.section_id"
            class="tiers-section-block"
          >
            <h2>
              <span v-if="editingSectionId !== section.section_id">{{
                section.name
              }}</span>
              <input
                v-else
                v-model="renameSectionName"
                required
                @keyup.enter="handleRenameSection(section.section_id)"
                @blur="editingSectionId = null"
              />
              <button
                @click="startRenameSection(section.section_id, section.name)"
              >
                Rename
              </button>
              <button @click="handleDeleteSection(section.section_id)">
                Delete
              </button>
            </h2>
            <draggable
              :list="
                tierGroups.filter((g) => g.section_id === section.section_id)
              "
              group="tier-groups"
              :move="onMove"
              item-key="tier_group_id"
              class="tier-group-draggable"
              :scroll="true"
              :force-fallback="true"
              :scroll-sensitivity="100"
              :scroll-speed="20"
              @change="(evt) => onDrop(section.section_id, evt)"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element, index }">
                <TierTree
                  :tiers="element.tiers"
                  :group-label="element.elan_file_name"
                  :group-index="index"
                />
              </template>
            </draggable>
          </div>
          <!-- Always show Unsectioned at the bottom -->
          <div style="margin-top: 2rem">
            <h2>Unsectioned</h2>
            <draggable
              :list="tierGroups.filter((g) => !g.section_id)"
              group="tier-groups"
              :move="onMove"
              item-key="tier_group_id"
              class="tier-group-draggable unsectioned"
              :scroll="true"
              :force-fallback="true"
              :scroll-sensitivity="100"
              :scroll-speed="20"
              @change="(evt) => onDrop(null, evt)"
              @start="onDragStart"
              @end="onDragEnd"
            >
              <template #item="{ element, index }">
                <TierTree
                  :tiers="element.tiers"
                  :group-label="element.elan_file_name"
                  :group-index="index"
                />
              </template>
              <template #footer>
                <div
                  v-if="tierGroups.filter((g) => !g.section_id).length === 0"
                  style="color: #888; text-align: center; padding: 1rem"
                >
                  No unsectioned tier groups.
                </div>
              </template>
            </draggable>
          </div>
        </template>
        <template v-else>
          <TierTree
            v-for="(group, idx) in tierTree"
            :key="group.fileName"
            :tiers="group.tiers"
            :group-index="idx"
            :group-label="group.fileName"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import '@/assets/css/tiers.css';
import { ref, onMounted, computed } from 'vue';
import { useProjectStore } from '@/stores/project';
import {
  fetchSectionsAndGroups,
  createSection,
  renameSection,
  deleteSection,
  moveTierGroup,
} from '@/api/service/tierService';
import TierTree from '@/components/common/tierTree.vue';
import draggable from 'vuedraggable';

const projectStore = useProjectStore();
const currentProject = computed(() => projectStore.currentProject);

const tierTree = ref([]);
const sections = ref([]);
const tierGroups = ref([]);
const loading = ref(true);
const error = ref('');
const useCustomSections = ref(false);
const newSectionName = ref('');
const renameSectionName = ref('');
const editingSectionId = ref(null);
const isDragging = ref(false);

async function loadData({ silent = false } = {}) {
  if (!silent) loading.value = true;
  error.value = '';
  try {
    if (!currentProject.value) {
      error.value = 'No active project selected.';
      return;
    }
    const custom = await fetchSectionsAndGroups(
      currentProject.value.project_id
    );
    sections.value = custom.sections;
    tierGroups.value = custom.tier_groups;
    useCustomSections.value = true;
  } catch {
    error.value = 'Failed to load tiers.';
  } finally {
    if (!silent) loading.value = false;
  }
}

async function handleCreateSection() {
  if (!newSectionName.value) return;
  await createSection(currentProject.value.project_id, newSectionName.value);
  newSectionName.value = '';
  await loadData();
}

function startRenameSection(sectionId, currentName) {
  editingSectionId.value = sectionId;
  renameSectionName.value = currentName;
}

async function handleRenameSection(sectionId) {
  if (!renameSectionName.value) return;
  await renameSection(sectionId, renameSectionName.value);
  editingSectionId.value = null;
  renameSectionName.value = '';
  await loadData();
}

async function handleDeleteSection(sectionId) {
  if (confirm('Are you sure you want to delete this section?')) {
    await deleteSection(sectionId);
    await loadData();
  }
}

function onMove() {
  return true;
}

async function onDrop(newSectionId, evt) {
  if (!evt || !evt.added) return;
  const movedGroup = evt.added.element;
  if (!movedGroup) return;
  await moveTierGroup(movedGroup.tier_group_id, newSectionId);
  await loadData({ silent: true });
}

function onDragStart() {
  isDragging.value = true;
}
function onDragEnd() {
  isDragging.value = false;
}

onMounted(loadData);
</script>
