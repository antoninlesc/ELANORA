<template>
  <div :class="{ 'dragging-disable-interaction': isDragging }">
    <h1 class="tiers-page-title">Tier Hierarchy</h1>
    <div v-if="loading" class="tiers-page-loading">Loading...</div>
    <div v-else-if="error" class="tiers-page-error">{{ error }}</div>
    <div v-else>
      <div class="tiers-tree-main-block">
        <div class="tiers-section-controls">
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
            :list="getTierTreesForSection(section.section_id)"
            group="tier-groups"
            :move="onMove"
            item-key="tier_id"
            class="tier-group-draggable"
            :scroll="true"
            :force-fallback="true"
            :scroll-sensitivity="100"
            :scroll-speed="20"
            @change="(evt) => onDrop(section.section_id, evt)"
            @start="onDragStart"
            @end="onDragEnd"
          >
            <template #item="{ element }">
              <div class="tier-tree-item">
                <div
                  class="tier-item tier-parent"
                  :style="{ marginLeft: element.level * 20 + 'px' }"
                >
                  <span class="tier-name">{{ element.tier_name }}</span>
                  <span class="tier-id">(ID: {{ element.tier_id }})</span>
                </div>
                <div
                  v-for="child in element.children"
                  :key="child.tier_id"
                  class="tier-item tier-child"
                  :style="{ marginLeft: (element.level + 1) * 20 + 'px' }"
                >
                  <span class="tier-name">{{ child.tier_name }}</span>
                  <span class="tier-id">(ID: {{ child.tier_id }})</span>
                </div>
              </div>
            </template>
          </draggable>
        </div>
        <!-- Always show Unsectioned at the bottom -->
        <div style="margin-top: 2rem">
          <h2>Unsectioned</h2>
          <draggable
            :list="getTierTreesForSection(null)"
            group="tier-groups"
            :move="onMove"
            item-key="tier_id"
            class="tier-group-draggable unsectioned"
            :scroll="true"
            :force-fallback="true"
            :scroll-sensitivity="100"
            :scroll-speed="20"
            @change="(evt) => onDrop(null, evt)"
            @start="onDragStart"
            @end="onDragEnd"
          >
            <template #item="{ element }">
              <div class="tier-tree-item">
                <div
                  class="tier-item tier-parent"
                  :style="{ marginLeft: element.level * 20 + 'px' }"
                >
                  <span class="tier-name">{{ element.tier_name }}</span>
                  <span class="tier-id">(ID: {{ element.tier_id }})</span>
                </div>
                <div
                  v-for="child in element.children"
                  :key="child.tier_id"
                  class="tier-item tier-child"
                  :style="{ marginLeft: (element.level + 1) * 20 + 'px' }"
                >
                  <span class="tier-name">{{ child.tier_name }}</span>
                  <span class="tier-id">(ID: {{ child.tier_id }})</span>
                </div>
              </div>
            </template>
            <template #footer>
              <div
                v-if="getTierTreesForSection(null).length === 0"
                style="color: #888; text-align: center; padding: 1rem"
              >
                No unsectioned tier groups.
              </div>
            </template>
          </draggable>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import '@/assets/css/tiers.css';
import { ref, onMounted, computed } from 'vue';
import { useProjectStore } from '@/stores/project';
import { useHead } from '@unhead/vue';
import { useI18n } from 'vue-i18n';
import {
  fetchSectionsAndGroups,
  createSection,
  renameSection,
  deleteSection,
  moveTierGroup,
} from '@/api/service/tierService';
import draggable from 'vuedraggable';

const projectStore = useProjectStore();
const { t } = useI18n();

useHead({
  title: t('tiersPage.pageTitle'),
  meta: [{ name: 'description', content: t('tiersPage.pageDescription') }],
});

const currentProject = computed(() => projectStore.currentProject);

const sections = ref([]);
const tierGroups = ref([]);
const loading = ref(true);
const error = ref('');
const newSectionName = ref('');
const renameSectionName = ref('');
const editingSectionId = ref(null);
const isDragging = ref(false);

function getTierTreesForSection(sectionId) {
  const sectionTiers = tierGroups.value.filter(
    (g) => g.section_id === sectionId
  );
  return buildTierTrees(sectionTiers);
}

function buildTierTrees(tiers) {
  // Build a map of tier_id to tier
  const tierMap = {};
  tiers.forEach((tier) => {
    tierMap[tier.tier_id] = { ...tier, children: [], level: 0 };
  });

  const roots = [];
  const processed = new Set();

  // First pass: identify roots (tiers without parents or whose parents aren't in our list)
  tiers.forEach((tier) => {
    if (!tier.parent_tier_id || !tierMap[tier.parent_tier_id]) {
      roots.push(tierMap[tier.tier_id]);
      processed.add(tier.tier_id);
    }
  });

  // Second pass: build hierarchy by assigning children to parents
  tiers.forEach((tier) => {
    if (
      tier.parent_tier_id &&
      tierMap[tier.parent_tier_id] &&
      !processed.has(tier.tier_id)
    ) {
      tierMap[tier.parent_tier_id].children.push(tierMap[tier.tier_id]);
      processed.add(tier.tier_id);
    }
  });

  // Set levels for proper indentation
  function setLevels(nodes, level) {
    nodes.forEach((node) => {
      node.level = level;
      if (node.children && node.children.length > 0) {
        setLevels(node.children, level + 1);
      }
    });
  }
  setLevels(roots, 0);

  return roots;
}

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
  await moveTierGroup(
    movedGroup.tier_group_id,
    newSectionId,
    currentProject.value.project_id,
    movedGroup.tier_id,
    movedGroup.tier_name
  );
  await loadData({ silent: true });
}

function onDragStart() {
  isDragging.value = true;
}
function onDragEnd() {
  isDragging.value = false;
}

onMounted(() => {
  loadData();
  projectStore.initBroadcastChannel();
});
</script>
