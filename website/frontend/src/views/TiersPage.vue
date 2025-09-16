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
                  class="tier-item"
                  :class="{ 'tier-parent': element.children.length > 0 }"
                  :style="{ marginLeft: element.level * 20 + 'px' }"
                  @click="handleTierClick(element)"
                >
                  <div class="tier-content">
                    <button
                      v-if="element.children.length > 0"
                      class="collapse-button"
                    >
                      <font-awesome-icon
                        :icon="
                          element.collapsed
                            ? 'fa-solid fa-chevron-right'
                            : 'fa-solid fa-chevron-down'
                        "
                        size="sm"
                      />
                    </button>
                    <span class="tier-name">{{ element.tier_name }}</span>
                  </div>
                </div>
                <template v-if="!element.collapsed">
                  <div
                    v-for="child in element.children"
                    :key="child.tier_id"
                    class="tier-item tier-child"
                    :style="{ marginLeft: (element.level + 1) * 20 + 'px' }"
                  >
                    <span class="tier-name">{{ child.tier_name }}</span>
                  </div>
                </template>
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
                  class="tier-item"
                  :class="{ 'tier-parent': element.children.length > 0 }"
                  :style="{ marginLeft: element.level * 20 + 'px' }"
                  @click="handleTierClick(element)"
                >
                  <div class="tier-content">
                    <button
                      v-if="element.children.length > 0"
                      class="collapse-button"
                    >
                      <font-awesome-icon
                        :icon="
                          element.collapsed
                            ? 'fa-solid fa-chevron-right'
                            : 'fa-solid fa-chevron-down'
                        "
                        size="sm"
                      />
                    </button>
                    <span class="tier-name">{{ element.tier_name }}</span>
                  </div>
                </div>
                <template v-if="!element.collapsed">
                  <div
                    v-for="child in element.children"
                    :key="child.tier_id"
                    class="tier-item tier-child"
                    :style="{ marginLeft: (element.level + 1) * 20 + 'px' }"
                  >
                    <span class="tier-name">{{ child.tier_name }}</span>
                  </div>
                </template>
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
const dragInProgress = ref(false);
const collapsedStates = ref(new Map());

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
    tierMap[tier.tier_id] = {
      ...tier,
      children: [],
      level: 0,
      collapsed: collapsedStates.value.get(tier.tier_id) ?? true,
    };
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

  // Sort roots and children alphabetically
  function sortAlphabetically(nodes) {
    nodes.sort((a, b) => a.tier_name.localeCompare(b.tier_name));
    nodes.forEach((node) => {
      if (node.children && node.children.length > 0) {
        sortAlphabetically(node.children);
      }
    });
  }
  sortAlphabetically(roots);

  return roots;
}

function toggleCollapsed(element) {
  const currentState = collapsedStates.value.get(element.tier_id) ?? true;
  collapsedStates.value.set(element.tier_id, !currentState);
}

function handleTierClick(element) {
  if (dragInProgress.value) return;
  if (element.children.length > 0) {
    toggleCollapsed(element);
  }
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
    // Clear collapsed states for tiers that no longer exist
    const currentTierIds = new Set(tierGroups.value.map((tg) => tg.tier_id));
    for (const [tierId] of collapsedStates.value) {
      if (!currentTierIds.has(tierId)) {
        collapsedStates.value.delete(tierId);
      }
    }
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
  dragInProgress.value = true;
}
function onDragEnd() {
  isDragging.value = false;
  setTimeout(() => (dragInProgress.value = false), 10);
}

onMounted(() => {
  loadData();
  projectStore.initBroadcastChannel();
});
</script>

<script>
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';

export default {
  components: {
    FontAwesomeIcon,
  },
};
</script>
