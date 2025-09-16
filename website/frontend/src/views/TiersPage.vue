<template>
  <div :class="{ 'dragging-disable-interaction': isDragging }">
    <div v-if="loading" class="tiers-page-loading">
      {{ $t('tiersPage.loading') }}
    </div>
    <div v-else-if="error" class="tiers-page-error">
      {{ $t('tiersPage.error') }}
      <button class="tiers-retry-btn" @click="loadData">
        {{ $t('tiersPage.retry') }}
      </button>
    </div>
    <div v-else>
      <div class="tiers-tree-main-block">
        <h1 class="tiers-page-title">{{ $t('tiersPage.pageTitle') }}</h1>
        <div
          v-for="section in sections"
          :key="section.section_id"
          class="tiers-section-block"
          :data-section-id="section.section_id"
        >
          <div class="tiers-section-header">
            <div class="tiers-section-title-container">
              <div
                v-if="editingSectionId === section.section_id"
                class="tiers-edit-container"
              >
                <input
                  v-model="renameSectionName"
                  required
                  class="tiers-edit-input"
                  @keyup.enter="handleRenameSection(section.section_id)"
                  @keyup.escape="cancelEdit"
                />
              </div>
              <h2 v-else>
                <span>{{ section.name }}</span>
              </h2>
            </div>
            <div class="tiers-section-actions">
              <button
                class="tiers-section-action-btn tiers-edit-btn"
                :title="$t('tiersPage.rename')"
                @click.stop="
                  startRenameSection(section.section_id, section.name)
                "
              >
                <font-awesome-icon icon="fa-regular fa-pen-to-square" />
              </button>
              <button
                class="tiers-section-action-btn tiers-delete-btn"
                :title="$t('tiersPage.delete')"
                @click.stop="handleDeleteSection(section.section_id)"
              >
                <font-awesome-icon icon="fa-solid fa-trash" />
              </button>
            </div>
          </div>
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

        <!-- Add Section Button at bottom of sections -->
        <div
          class="tiers-section-controls"
          style="margin: 1rem 0; text-align: center"
        >
          <button
            class="tiers-add-section-btn"
            :title="$t('tiersPage.addSection')"
            @click="handleAddSection"
          >
            <font-awesome-icon icon="fa-solid fa-plus" />
            {{ $t('tiersPage.addSection') }}
          </button>
        </div>

        <!-- Always show Unsectioned at the bottom -->
        <div class="tiers-section-block unsectioned" style="margin-top: 2rem">
          <h2>{{ $t('tiersPage.uncategorized') }}</h2>
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
                class="unsectioned-empty-message"
              >
                {{ $t('tiersPage.noTiers') }}
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
import { ref, onMounted, computed, nextTick } from 'vue';
import { useProjectStore } from '@/stores/project';
import { useHead } from '@unhead/vue';
import { useI18n } from 'vue-i18n';
import { useUserConfirm } from '@/composables/useUserConfirm';
import { useEventMessageStore } from '@/stores/eventMessage';
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
const userConfirm = useUserConfirm();
const eventMessageStore = useEventMessageStore();

useHead({
  title: t('tiersPage.pageTitle'),
  meta: [{ name: 'description', content: t('tiersPage.pageDescription') }],
});

const currentProject = computed(() => projectStore.currentProject);

const sections = ref([]);
const tierGroups = ref([]);
const loading = ref(true);
const error = ref('');
const renameSectionName = ref('');
const editingSectionId = ref(null);
const isDragging = ref(false);
const dragInProgress = ref(false);
const collapsedStates = ref(new Map());
const newSectionId = ref(null);

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
      error.value = t('tiersPage.noSections');
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
  } catch (err) {
    console.error('Error loading data:', err);
    error.value = t('tiersPage.error');
  } finally {
    if (!silent) loading.value = false;
  }
}

async function handleAddSection() {
  try {
    const response = await createSection(
      currentProject.value.project_id,
      'New Section'
    );
    const newSection = response.data;
    // Use the correct property name from API response
    newSectionId.value = newSection.tier_section_id || newSection.section_id;

    // Load data silently to avoid loading flash
    await loadData({ silent: true });

    // Verify the new section is in the array
    const sectionExists = sections.value.some(
      (s) => s.section_id === newSectionId.value
    );

    if (!sectionExists) {
      console.warn('New section not found in sections array!');
      newSectionId.value = null;
      eventMessageStore.addMessage(
        'tiersPage.eventMessages.sectionCreateFailed',
        'error'
      );
      return;
    }

    // Put the new section in edit mode
    startRenameSection(newSection.section_id, 'New Section');

    // Wait for multiple nextTicks to ensure DOM is fully updated
    await nextTick();
    await nextTick();
    await nextTick();

    // Add a small delay to ensure rendering is complete
    setTimeout(() => {
      scrollToNewSection();
    }, 100);

    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionCreated',
      'success'
    );
  } catch (error) {
    console.error('Failed to create section:', error);
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionCreateFailed',
      'error'
    );
  }
}

function startRenameSection(sectionId, currentName) {
  editingSectionId.value = sectionId;
  renameSectionName.value = currentName;

  // Auto-focus the input after DOM update
  nextTick(() => {
    const input = document.querySelector(
      `[data-section-id="${sectionId}"] .tiers-edit-input`
    );
    if (input) {
      input.focus();
      input.select(); // Select all text for easy replacement
    }
  });
}

async function handleRenameSection(sectionId) {
  const trimmedName = renameSectionName.value.trim();
  if (!trimmedName) {
    cancelEdit();
    return;
  }

  try {
    await renameSection(sectionId, trimmedName);
    editingSectionId.value = null;
    renameSectionName.value = '';
    await loadData({ silent: true });
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionRenamed',
      'success',
      3000,
      { sectionName: trimmedName }
    );
  } catch (error) {
    console.error('Failed to rename section:', error);
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionRenameFailed',
      'error'
    );
  }
}

function cancelEdit() {
  editingSectionId.value = null;
  renameSectionName.value = '';
}

async function handleDeleteSection(sectionId) {
  const section = sections.value.find((s) => s.section_id === sectionId);
  const sectionName = section ? section.name : 'this section';

  // Check if section has tiers
  const sectionTiers = tierGroups.value.filter(
    (tg) => tg.section_id === sectionId
  );
  const hasTiers = sectionTiers.length > 0;

  const confirmed = await userConfirm({
    title: t('tiersPage.confirmDelete'),
    message: t('tiersPage.deleteSectionMessage', { sectionName }),
    confirmText: t('tiersPage.yesDelete'),
    cancelText: t('tiersPage.noCancel'),
  });

  if (!confirmed) return;

  try {
    await deleteSection(sectionId);
    await loadData({ silent: true });

    if (hasTiers) {
      eventMessageStore.addMessage(
        'tiersPage.eventMessages.sectionDeletedWithTiers',
        'success',
        5000,
        {
          sectionName: sectionName,
          tierCount: sectionTiers.length,
        }
      );
    } else {
      eventMessageStore.addMessage(
        'tiersPage.eventMessages.sectionDeleted',
        'success',
        3000,
        { sectionName: sectionName }
      );
    }
  } catch (error) {
    console.error('Failed to delete section:', error);
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionDeleteFailed',
      'error'
    );
  }
}

function onMove() {
  return true;
}

async function onDrop(newSectionId, evt) {
  if (!evt || !evt.added) return;
  const movedGroup = evt.added.element;
  if (!movedGroup) return;

  try {
    await moveTierGroup(
      movedGroup.tier_group_id,
      newSectionId,
      currentProject.value.project_id,
      movedGroup.tier_id,
      movedGroup.tier_name
    );
    await loadData({ silent: true });

    // Determine destination section name
    let destinationName;
    if (newSectionId === null) {
      destinationName = t('tiersPage.uncategorized');
    } else {
      const destinationSection = sections.value.find(
        (s) => s.section_id === newSectionId
      );
      destinationName = destinationSection
        ? destinationSection.name
        : 'Unknown Section';
    }

    // Determine the appropriate message based on tier type
    let messageKey;
    if (movedGroup.children && movedGroup.children.length > 0) {
      // This is a parent tier with children (tier group)
      messageKey = 'tiersPage.eventMessages.tierGroupMoved';
    } else if (movedGroup.parent_tier_id) {
      // This is a child tier of a group
      messageKey = 'tiersPage.eventMessages.tierGroupChildMoved';
    } else {
      // This is a standalone tier
      messageKey = 'tiersPage.eventMessages.tierMoved';
    }

    eventMessageStore.addMessage(messageKey, 'success', 3000, {
      tierName: movedGroup.tier_name,
      destination: destinationName,
    });
  } catch (error) {
    console.error('Failed to move tier group:', error);
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.tierMoveFailed',
      'error'
    );
  }
}

function onDragStart() {
  isDragging.value = true;
  dragInProgress.value = true;
}

function onDragEnd() {
  isDragging.value = false;
  dragInProgress.value = false;
}
function scrollToNewSection() {
  if (!newSectionId.value) {
    return;
  }

  const maxAttempts = 20;
  let attempts = 0;

  const tryScroll = () => {
    attempts++;
    const selector = `[data-section-id="${newSectionId.value}"]`;
    const element = document.querySelector(selector);

    if (element) {
      try {
        element.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
          inline: 'nearest',
        });
      } catch {
        try {
          const elementTop = element.offsetTop;
          const elementHeight = element.offsetHeight;
          const windowHeight = window.innerHeight;
          const scrollTo = elementTop - windowHeight / 2 + elementHeight / 2;

          window.scrollTo({
            top: scrollTo,
            behavior: 'smooth',
          });
        } catch {
          element.scrollIntoView({ block: 'center' });
        }
      }

      newSectionId.value = null;
      return;
    }

    if (attempts < maxAttempts) {
      setTimeout(tryScroll, 100);
    } else {
      newSectionId.value = null;
    }
  };

  tryScroll();
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
