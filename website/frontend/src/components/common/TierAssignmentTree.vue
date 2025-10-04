<template>
  <div
    :class="{ 'dragging-disable-interaction': isDragging || movingInProgress }"
  >
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
        <h1 v-if="mode === 'management'" class="tiers-page-title">
          {{ pageTitle }}
        </h1>

        <!-- Management Mode: Full sections with editing -->
        <template v-if="mode === 'management'">
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
                  <span class="section-count"
                    >({{ getTierCountForSection(section.section_id) }})</span
                  >
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
                      <span
                        v-if="element.children.length > 0"
                        class="section-count"
                        >({{ getDescendantCount(element) }})</span
                      >
                      <span v-if="element.file_name" class="tier-file"
                        >({{ element.file_name }})</span
                      >
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
                      <span v-if="child.file_name" class="tier-file"
                        >({{ child.file_name }})</span
                      >
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
            <h2>
              {{ $t('tiersPage.uncategorized') }}
              <span class="section-count"
                >({{ getUnassignedTierCount() }})</span
              >
            </h2>
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
                      <span
                        v-if="element.children.length > 0"
                        class="section-count"
                        >({{ getDescendantCount(element) }})</span
                      >
                      <span v-if="element.file_name" class="tier-file"
                        >({{ element.file_name }})</span
                      >
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
                      <span v-if="child.file_name" class="tier-file"
                        >({{ child.file_name }})</span
                      >
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
        </template>

        <!-- Assignment Mode: Tree-based drag & drop interface -->
        <template v-else-if="mode === 'assignment'">
          <div class="tiers-tree-main-block">
            <h1>{{ $t('uploadPage.step3.title') }}</h1>
            <p class="assignment-description">
              {{ $t('uploadPage.step3.description') }}
            </p>

            <!-- Production Sections Group -->
            <div class="section-group production-group">
              <h3 class="section-group-title">
                {{ $t('uploadPage.step3.existingSections') }}
              </h3>
              <!-- Production Sections (Read-only for assignment) -->
              <div
                v-for="section in productionSections"
                :key="section.section_id"
                class="tiers-section-block tiers-section-block-production"
                :data-section-id="section.section_id"
              >
                <div class="tiers-section-header">
                  <div class="tiers-section-title-container">
                    <h2>
                      {{ section.name }}
                      <span class="section-count"
                        >({{
                          getTierCountForSection(section.section_id)
                        }})</span
                      >
                      <span class="section-badge section-badge-production">{{
                        $t('tierAssignment.productionBadge')
                      }}</span>
                    </h2>
                  </div>
                </div>
                <draggable
                  :list="getAssignedTiersForSection(section.section_id)"
                  group="assignment-tiers"
                  :move="onMove"
                  item-key="tier_id"
                  class="tier-group-draggable"
                  :scroll="true"
                  :force-fallback="true"
                  :scroll-sensitivity="100"
                  :scroll-speed="20"
                  @change="(evt) => onAssignmentDrop(section.section_id, evt)"
                  @start="onDragStart"
                  @end="onDragEnd"
                >
                  <template #item="{ element }">
                    <div class="tier-tree-item">
                      <div
                        class="tier-item"
                        :class="{
                          'tier-parent': element.children.length > 0,
                        }"
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
                          <span
                            v-if="element.children.length > 0"
                            class="section-count"
                            >({{ getDescendantCount(element) }})</span
                          >
                          <span class="tier-file"
                            >({{ element.file_name }})</span
                          >
                        </div>
                      </div>
                      <template v-if="!element.collapsed">
                        <div
                          v-for="child in element.children"
                          :key="child.tier_id"
                          class="tier-item tier-child"
                          :style="{
                            marginLeft: (element.level + 1) * 20 + 'px',
                          }"
                        >
                          <span class="tier-name">{{ child.tier_name }}</span>
                          <span class="tier-file">({{ child.file_name }})</span>
                        </div>
                      </template>
                    </div>
                  </template>
                  <template #footer>
                    <div
                      v-if="
                        getAssignedTiersForSection(section.section_id)
                          .length === 0
                      "
                      class="empty-section-message"
                    >
                      {{ $t('uploadPage.step3.dropTiersHere') }}
                    </div>
                  </template>
                </draggable>
              </div>
            </div>

            <!-- Staged Sections Group -->
            <div class="section-group staged-group">
              <h3 class="section-group-title">
                {{ $t('uploadPage.step3.stagedSections') }}
              </h3>
              <!-- Staged Sections (Editable for assignment) -->
              <div
                v-for="section in stagedSections"
                :key="section.section_id"
                class="tiers-section-block tiers-section-block-staged"
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
                      <span>{{ section.name || section.section_name }}</span>
                      <span class="section-count"
                        >({{
                          getTierCountForSection(section.section_id)
                        }})</span
                      >
                      <span class="section-badge section-badge-staged">{{
                        $t('tierAssignment.stagedBadge')
                      }}</span>
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
                  :list="getAssignedTiersForSection(section.section_id)"
                  group="assignment-tiers"
                  :move="onMove"
                  item-key="tier_id"
                  class="tier-group-draggable"
                  :scroll="true"
                  :force-fallback="true"
                  :scroll-sensitivity="100"
                  :scroll-speed="20"
                  @change="(evt) => onAssignmentDrop(section.section_id, evt)"
                  @start="onDragStart"
                  @end="onDragEnd"
                >
                  <template #item="{ element }">
                    <div class="tier-tree-item">
                      <div
                        class="tier-item"
                        :class="{
                          'tier-parent': element.children.length > 0,
                        }"
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
                          <span
                            v-if="element.children.length > 0"
                            class="section-count"
                            >({{ getDescendantCount(element) }})</span
                          >
                          <span class="tier-file"
                            >({{ element.file_name }})</span
                          >
                        </div>
                      </div>
                      <template v-if="!element.collapsed">
                        <div
                          v-for="child in element.children"
                          :key="child.tier_id"
                          class="tier-item tier-child"
                          :style="{
                            marginLeft: (element.level + 1) * 20 + 'px',
                          }"
                        >
                          <span class="tier-name">{{ child.tier_name }}</span>
                          <span class="tier-file">({{ child.file_name }})</span>
                        </div>
                      </template>
                    </div>
                  </template>
                  <template #footer>
                    <div
                      v-if="
                        getAssignedTiersForSection(section.section_id)
                          .length === 0
                      "
                      class="empty-section-message"
                    >
                      {{ $t('uploadPage.step3.dropTiersHere') }}
                    </div>
                  </template>
                </draggable>
              </div>
            </div>
            <!-- New Section Creation -->
            <div
              v-if="hasNewSectionAssignments"
              class="tiers-section-block new-section-creation"
            >
              <div class="tiers-section-header">
                <div class="tiers-section-title-container">
                  <h2>{{ $t('uploadPage.step3.newSections') }}</h2>
                </div>
              </div>
              <div class="new-sections-list">
                <div
                  v-for="sectionName in uniqueNewSections"
                  :key="sectionName"
                  class="new-section-item"
                  :data-section-id="sectionName"
                >
                  <div class="new-section-header">
                    <div class="new-section-input-container">
                      <input
                        :value="newSectionNames[sectionName] || ''"
                        :placeholder="
                          $t('uploadPage.step3.sectionNamePlaceholder')
                        "
                        class="new-section-input"
                        type="text"
                        @input="
                          (event) =>
                            updateNewSectionName(
                              sectionName,
                              event.target.value
                            )
                        "
                      />
                      <span class="section-count"
                        >({{ getTierCountForSection(sectionName) }})</span
                      >
                      <div class="new-section-actions">
                        <button
                          class="tiers-section-action-btn tiers-edit-btn"
                          :title="$t('tiersPage.rename')"
                          @click.stop="startRenameNewSection(sectionName)"
                        >
                          <font-awesome-icon
                            icon="fa-regular fa-pen-to-square"
                          />
                        </button>
                        <button
                          class="tiers-section-action-btn tiers-delete-btn"
                          :title="$t('tiersPage.delete')"
                          @click.stop="handleDeleteNewSection(sectionName)"
                        >
                          <font-awesome-icon icon="fa-solid fa-trash" />
                        </button>
                      </div>
                    </div>
                  </div>
                  <draggable
                    :list="getAssignedTiersForSection(sectionName)"
                    group="assignment-tiers"
                    :move="onMove"
                    item-key="tier_id"
                    class="tier-group-draggable"
                    :scroll="true"
                    :force-fallback="true"
                    :scroll-sensitivity="100"
                    :scroll-speed="20"
                    @change="(evt) => onAssignmentDrop(sectionName, evt)"
                    @start="onDragStart"
                    @end="onDragEnd"
                  >
                    <template #item="{ element }">
                      <div class="tier-tree-item">
                        <div
                          class="tier-item"
                          :class="{
                            'tier-parent': element.children.length > 0,
                          }"
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
                            <span class="tier-name">{{
                              element.tier_name
                            }}</span>
                            <span
                              v-if="element.children.length > 0"
                              class="section-count"
                              >({{ getDescendantCount(element) }})</span
                            >
                            <span class="tier-file"
                              >({{ element.file_name }})</span
                            >
                          </div>
                        </div>
                        <template v-if="!element.collapsed">
                          <div
                            v-for="child in element.children"
                            :key="child.tier_id"
                            class="tier-item tier-child"
                            :style="{
                              marginLeft: (element.level + 1) * 20 + 'px',
                            }"
                          >
                            <span class="tier-name">{{ child.tier_name }}</span>
                            <span class="tier-file"
                              >({{ child.file_name }})</span
                            >
                          </div>
                        </template>
                      </div>
                    </template>
                    <template #footer>
                      <div
                        v-if="
                          getAssignedTiersForSection(sectionName).length === 0
                        "
                        class="empty-section-message"
                      >
                        {{ $t('uploadPage.step3.dropTiersHere') }}
                      </div>
                    </template>
                  </draggable>
                </div>
              </div>
            </div>

            <!-- Add New Section Button -->
            <div
              class="tiers-section-controls"
              style="margin: 1rem 0; text-align: center"
            >
              <button class="tiers-add-section-btn" @click="createNewSection">
                <font-awesome-icon icon="fa-solid fa-plus" />
                {{ $t('uploadPage.step3.createNewSection') }}
              </button>
            </div>

            <!-- Unassigned Tiers Section -->
            <div
              class="tiers-section-block unassigned"
              style="margin-top: 2rem"
            >
              <h2>
                {{ $t('uploadPage.step3.unassignedTiers') }}
                <span class="section-count"
                  >({{ getUnassignedTierCount() }})</span
                >
              </h2>
              <draggable
                :list="getUnassignedTiers()"
                group="assignment-tiers"
                :move="onMove"
                item-key="tier_id"
                class="tier-group-draggable unassigned"
                :scroll="true"
                :force-fallback="true"
                :scroll-sensitivity="100"
                :scroll-speed="20"
                @change="(evt) => onAssignmentDrop(null, evt)"
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
                        <span
                          v-if="element.children.length > 0"
                          class="section-count"
                          >({{ getDescendantCount(element) }})</span
                        >
                        <span class="tier-file">({{ element.file_name }})</span>
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
                        <span v-if="child.file_name" class="tier-file"
                          >({{ child.file_name }})</span
                        >
                      </div>
                    </template>
                  </div>
                </template>
                <template #footer>
                  <div
                    v-if="getUnassignedTiers().length === 0"
                    class="unassigned-empty-message"
                  >
                    {{ $t('uploadPage.step3.allTiersAssigned') }}
                  </div>
                </template>
              </draggable>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import '@/assets/css/tiers.css';
import { ref, onMounted, computed, nextTick, watch } from 'vue';
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
} from '@api/service/tierService';
import draggable from 'vuedraggable';

const props = defineProps({
  mode: {
    type: String,
    default: 'management',
    validator: (value) => ['management', 'assignment'].includes(value),
  },
  extractedTiers: {
    type: Array,
    default: () => [],
  },
  existingSections: {
    type: Array,
    default: () => [],
  },
  tierAssignments: {
    type: Object,
    default: () => ({}),
  },
  newSectionNames: {
    type: Object,
    default: () => ({}),
  },
  sessionId: {
    type: String,
    default: null,
  },
});

const emit = defineEmits([
  'tier-assigned',
  'new-section-name-updated',
  'section-created',
  'section-renamed',
  'section-deleted',
  'tier-moved',
  'proceed',
]);

const projectStore = useProjectStore();
const { t } = useI18n();
const userConfirm = useUserConfirm();
const eventMessageStore = useEventMessageStore();

const currentProject = computed(() => projectStore.currentProject);

const pageTitle = computed(() => {
  if (currentProject.value?.project_name) {
    return t('tiersPage.pageTitleWithProject', {
      projectName: currentProject.value.project_name,
    });
  } else {
    return t('tiersPage.pageTitle');
  }
});

useHead({
  title: t('tiersPage.pageTitle'),
  meta: [{ name: 'description', content: t('tiersPage.pageDescription') }],
});

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
const movingInProgress = ref(false);
const localSectionCounter = ref(0);

// Assignment mode computed properties
const hasNewSectionAssignments = computed(() => {
  console.log(
    'TierAssignmentTree: Computing hasNewSectionAssignments from tierAssignments:',
    props.tierAssignments
  );
  const result = Object.values(props.tierAssignments).some(
    (assignment) => assignment === 'new'
  );
  console.log('TierAssignmentTree: hasNewSectionAssignments result:', result);
  return result;
});

const uniqueNewSections = computed(() => {
  console.log(
    'TierAssignmentTree: Computing uniqueNewSections from tierAssignments:',
    props.tierAssignments
  );
  const newAssignments = Object.entries(props.tierAssignments)
    .filter(([, assignment]) => {
      console.log(
        'TierAssignmentTree: Checking assignment:',
        assignment,
        'is new?',
        assignment === 'new'
      );
      return assignment === 'new';
    })
    .map(([tierKey]) => tierKey);
  console.log('TierAssignmentTree: uniqueNewSections result:', [
    ...new Set(newAssignments),
  ]);
  return [...new Set(newAssignments)].sort();
});

// Separate existing sections into production and staged
const productionSections = computed(() => {
  const filtered = props.existingSections
    .filter((section) => {
      return !section.session_id;
    })
    .sort((a, b) =>
      (a.name || a.section_name).localeCompare(b.name || b.section_name)
    );
  return filtered;
});

const stagedSections = computed(() => {
  const filtered = props.existingSections
    .filter((section) => {
      return section.session_id === props.sessionId;
    })
    .sort((a, b) =>
      (a.name || a.section_name).localeCompare(b.name || b.section_name)
    );
  return filtered;
});

// Assignment mode functions
function getAssignedTiersForSection(sectionId) {
  const assignedTiers = props.extractedTiers.filter((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    const assignment = props.tierAssignments[tierKey];
    return assignment === sectionId;
  });
  return buildTierTrees(assignedTiers);
}

function getUnassignedTiers() {
  const unassignedTiers = props.extractedTiers.filter((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    const assignment = props.tierAssignments[tierKey];
    return !assignment || assignment === '';
  });
  return buildTierTrees(unassignedTiers);
}

// Functions to count tiers in sections
function getTierCountForSection(sectionId) {
  if (props.mode === 'management') {
    // Management mode: count tier groups in the section
    return tierGroups.value.filter((tg) => tg.section_id === sectionId).length;
  } else {
    // Assignment mode: count assigned tiers in the section
    return props.extractedTiers.filter((tier) => {
      const tierKey = tier.tier_id || tier.tier_name;
      return props.tierAssignments[tierKey] === sectionId;
    }).length;
  }
}

function getUnassignedTierCount() {
  if (props.mode === 'management') {
    // Management mode: count tier groups with null section_id
    return tierGroups.value.filter((tg) => tg.section_id === null).length;
  } else {
    // Assignment mode: count tiers with no assignment
    return props.extractedTiers.filter((tier) => {
      const tierKey = tier.tier_id || tier.tier_name;
      const assignment = props.tierAssignments[tierKey];
      return !assignment || assignment === '';
    }).length;
  }
}

// Function to count all descendants of a tier (recursive)
function getDescendantCount(tier) {
  if (!tier.children || tier.children.length === 0) {
    return 0;
  }

  let count = tier.children.length;
  tier.children.forEach((child) => {
    count += getDescendantCount(child);
  });

  return count;
}

async function onAssignmentDrop(targetSectionId, evt) {
  if (!evt || !evt.added) {
    return;
  }
  const movedTier = evt.added.element;
  if (!movedTier) {
    return;
  }

  if (movingInProgress.value) return; // Prevent double-submit

  movingInProgress.value = true;

  // If dropping on a new section that doesn't exist yet, mark as 'new' (only in management mode)
  let assignment = targetSectionId;
  if (
    props.mode === 'management' &&
    targetSectionId &&
    targetSectionId !== 'new' &&
    !props.existingSections.find((s) => s.section_id === targetSectionId)
  ) {
    console.log(
      'TierAssignmentTree: Section not found in existing sections, marking as new'
    );
    assignment = 'new';
  }

  // For assignment mode, keep everything local - no DB calls
  // Handle tier groups: when moving a parent tier, move all its children too
  const tiersToAssign = [movedTier];
  if (movedTier.children && movedTier.children.length > 0) {
    // Add all children of this tier group
    tiersToAssign.push(...movedTier.children);
  }

  console.log(
    'TierAssignmentTree: Assigning tiers:',
    tiersToAssign.map((t) => t.tier_name),
    'to assignment:',
    assignment
  );

  // Assign all tiers in the group
  tiersToAssign.forEach((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    console.log(
      'TierAssignmentTree: Emitting tier-assigned for tier:',
      tierKey,
      'assignment:',
      assignment
    );
    emit('tier-assigned', { tierKey, assignment });
  });

  // Add success message for assignment (using existing key for consistency)
  let destinationName;
  if (assignment === null) {
    destinationName = t('uploadPage.step3.unassignedTiers');
  } else {
    const section = props.existingSections.find(
      (s) => s.section_id === assignment
    );
    destinationName = section ? section.name : assignment;
  }

  // Use the same message key as in management mode for moving tiers
  eventMessageStore.addMessage(
    'tiersPage.eventMessages.tierMoved',
    'success',
    3000,
    {
      tierName: movedTier.tier_name,
      destination: destinationName,
    }
  );

  movingInProgress.value = false;
}

function startRenameNewSection(sectionName) {
  // Focus the input for the new section
  nextTick(() => {
    const input = document.querySelector(
      `[data-section-id="${sectionName}"] .new-section-input`
    );
    if (input) {
      input.focus();
      input.select();
    }
  });
}

async function handleDeleteNewSection(sectionName) {
  const sectionNameDisplay = props.newSectionNames[sectionName] || sectionName;

  // Check if section has tiers
  const sectionTiers = props.extractedTiers.filter((tier) => {
    const tierKey = tier.tier_id || tier.tier_name;
    return props.tierAssignments[tierKey] === sectionName;
  });

  const confirmed = await userConfirm({
    title: t('tiersPage.confirmDelete'),
    message: t('tiersPage.deleteSectionMessage', {
      sectionName: sectionNameDisplay,
    }),
    confirmText: t('tiersPage.yesDelete'),
    cancelText: t('tiersPage.noCancel'),
  });

  if (!confirmed) return;

  try {
    // Move all tiers from this section back to unassigned
    sectionTiers.forEach((tier) => {
      const tierKey = tier.tier_id || tier.tier_name;
      emit('tier-assigned', { tierKey, assignment: '' });
    });

    // Remove the section name
    emit('new-section-name-updated', { sectionName, newName: '' });

    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionDeleted',
      'success',
      3000,
      { sectionName: sectionNameDisplay }
    );
  } catch (error) {
    console.error('Failed to delete new section:', error);
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionDeleteFailed',
      'error'
    );
  }
}

async function createNewSection() {
  console.log('TierAssignmentTree: Creating new section in mode:', props.mode);
  console.log(
    'TierAssignmentTree: Current tierAssignments:',
    props.tierAssignments
  );
  console.log(
    'TierAssignmentTree: Current existingSections:',
    props.existingSections
  );
  try {
    if (props.mode === 'assignment') {
      // For assignment mode, create a local section object
      console.log(
        'TierAssignmentTree: Creating local section for project:',
        currentProject.value?.project_id
      );
      const newSection = {
        section_id: `local_${++localSectionCounter.value}`,
        name: 'New Section',
        is_staged: true,
        session_id: props.sessionId,
        project_id: currentProject.value.project_id,
      };

      console.log(
        'TierAssignmentTree: Created local section with ID:',
        newSection.section_id
      );

      // Emit event to parent to update existing sections
      console.log(
        'TierAssignmentTree: Emitting section-created event with section:',
        newSection
      );
      emit('section-created', { section: newSection });

      // Set the new section ID for scrolling
      newSectionId.value = newSection.section_id;

      // Wait for DOM update and scroll to new section
      nextTick(() => {
        setTimeout(() => {
          scrollToNewSection();
        }, 100);
      });

      eventMessageStore.addMessage(
        'tiersPage.eventMessages.sectionCreated',
        'success'
      );
    } else {
      // For management mode, use existing logic
      const response = await createSection(
        currentProject.value.project_id,
        'New Section'
      );
      const newSection = response.data;
      newSectionId.value = newSection.tier_section_id || newSection.section_id;

      await loadData({ silent: true });

      startRenameSection(newSection.section_id, 'New Section');

      await nextTick();
      await nextTick();
      await nextTick();

      setTimeout(() => {
        scrollToNewSection();
      }, 100);

      eventMessageStore.addMessage(
        'tiersPage.eventMessages.sectionCreated',
        'success'
      );
    }
  } catch (error) {
    console.error('Failed to create section:', error);
    eventMessageStore.addMessage(
      'tiersPage.eventMessages.sectionCreateFailed',
      'error'
    );
  }
}

// Watcher to reload data when current project changes (only for management mode)
watch(currentProject, (newProject, oldProject) => {
  if (props.mode === 'management') {
    if (
      newProject &&
      newProject.project_id !== (oldProject?.project_id || null)
    ) {
      // Reload data silently when the project changes
      loadData({ silent: true });
    } else if (!newProject) {
      // Handle case where no project is selected
      error.value = t('tiersPage.noSections');
      sections.value = [];
      tierGroups.value = [];
    }
  }
});

// Watchers for debugging prop changes
watch(
  () => props.existingSections,
  (newVal) => {
    // Update the local section counter based on existing local sections
    const localIds = newVal
      .filter(
        (section) =>
          section.section_id &&
          typeof section.section_id === 'string' &&
          section.section_id.startsWith('local_')
      )
      .map((section) => parseInt(section.section_id.split('_')[1]) || 0);
    if (localIds.length > 0) {
      localSectionCounter.value = Math.max(...localIds);
    }
  },
  { deep: true }
);

watch(
  () => props.tierAssignments,
  () => {},
  { deep: true }
);

function getTierTreesForSection(sectionId) {
  const sectionTiers = tierGroups.value.filter(
    (g) => g.section_id === sectionId
  );
  return buildTierTrees(sectionTiers);
}

function buildTierTrees(tiers) {
  // Build maps for both tier_id and tier_name lookups
  const tierMapById = {};
  const tierMapByName = {};
  tiers.forEach((tier) => {
    const tierObj = {
      ...tier,
      children: [],
      level: 0,
      collapsed: collapsedStates.value.get(tier.tier_id) ?? true,
    };
    tierMapById[tier.tier_id] = tierObj;
    tierMapByName[tier.tier_name] = tierObj;
  });

  const roots = [];
  const processed = new Set();

  // First pass: identify roots (tiers without parents or whose parents aren't in our list)
  tiers.forEach((tier) => {
    const hasParentId = tier.parent_tier_id && tierMapById[tier.parent_tier_id];
    const hasParentName =
      tier.parent_tier_name && tierMapByName[tier.parent_tier_name];
    if (!hasParentId && !hasParentName) {
      roots.push(tierMapById[tier.tier_id]);
      processed.add(tier.tier_id);
    }
  });

  // Second pass: build hierarchy by assigning children to parents
  tiers.forEach((tier) => {
    if (processed.has(tier.tier_id)) return;

    let parent = null;
    if (tier.parent_tier_id && tierMapById[tier.parent_tier_id]) {
      parent = tierMapById[tier.parent_tier_id];
    } else if (tier.parent_tier_name && tierMapByName[tier.parent_tier_name]) {
      parent = tierMapByName[tier.parent_tier_name];
    }

    if (parent) {
      parent.children.push(tierMapById[tier.tier_id]);
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
  if (props.mode !== 'management') return;

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
    sections.value = custom.sections.sort((a, b) =>
      a.name.localeCompare(b.name)
    );
    tierGroups.value = custom.tier_groups;
    // Clear collapsed states for tiers that no longer exist
    const currentTierIds = new Set(tierGroups.value.map((tg) => tg.tier_id));
    for (const [tierId] of collapsedStates.value) {
      if (!currentTierIds.has(tierId)) {
        collapsedStates.value.delete(tierId);
      }
    }
  } catch {
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
    if (props.mode === 'assignment') {
      // For assignment mode, just update the local state
      emit('section-renamed', { sectionId, newName: trimmedName });
    } else {
      // For management mode, call the backend
      await renameSection(sectionId, trimmedName);
      await loadData({ silent: true });
    }

    editingSectionId.value = null;
    renameSectionName.value = '';

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
  const section =
    sections.value.find((s) => s.section_id === sectionId) ||
    props.existingSections.find((s) => s.section_id === sectionId);
  const sectionName = section ? section.name : 'this section';

  // Check if section has tiers
  const sectionTiers =
    props.mode === 'management'
      ? tierGroups.value.filter((tg) => tg.section_id === sectionId)
      : props.extractedTiers.filter((tier) => {
          const tierKey = tier.tier_id || tier.tier_name;
          return props.tierAssignments[tierKey] === sectionId;
        });

  const hasTiers = sectionTiers.length > 0;

  const confirmed = await userConfirm({
    title: t('tiersPage.confirmDelete'),
    message: t('tiersPage.deleteSectionMessage', { sectionName }),
    confirmText: t('tiersPage.yesDelete'),
    cancelText: t('tiersPage.noCancel'),
  });

  if (!confirmed) return;

  try {
    if (props.mode === 'assignment') {
      // For assignment mode, emit event to parent
      emit('section-deleted', { sectionId });
    } else {
      // For management mode, call the backend
      await deleteSection(sectionId);
      await loadData({ silent: true });
    }

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

  if (movingInProgress.value) return; // Prevent double-submit

  movingInProgress.value = true;
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
  } finally {
    movingInProgress.value = false;
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

      // Focus the section name input for assignment mode
      if (props.mode === 'assignment') {
        const input = element.querySelector('.new-section-input');
        if (input) {
          input.focus();
          input.select();
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
  if (props.mode === 'management') {
    loadData();
    projectStore.initBroadcastChannel();
  } else {
    loading.value = false; // No loading needed for assignment mode
  }
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

<style scoped>
/* Assignment mode styles */
.assignment-section {
  max-width: 800px;
  margin: 0 auto;
}

.assignment-description {
  color: #666;
  margin-bottom: 24px;
  line-height: 1.5;
}

.tiers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.assignment-tier-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
}

.tier-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tier-name {
  font-weight: 600;
  color: #333;
}

.tier-parent {
  font-size: 0.9rem;
  color: #666;
}

.tier-file {
  font-size: 0.8rem;
  color: #999;
}

.tier-assignment-select {
  min-width: 200px;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}

.new-section-section h4,
.assignment-summary h4 {
  color: #333;
  margin-bottom: 16px;
  font-size: 1.1rem;
}

.new-sections-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.new-section-item {
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.new-section-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.assigned-tiers {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.assigned-tiers-label {
  font-weight: 600;
  color: #555;
}

.assigned-tiers-list {
  color: #666;
  font-size: 0.9rem;
}

.assignment-summary {
  margin-top: 24px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-weight: 600;
  color: #555;
}

.stat-value {
  font-weight: 700;
  color: #1976d2;
}

.assignment-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.assignment-proceed-btn {
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.assignment-proceed-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.assignment-proceed-btn:hover:not(:disabled) {
  background: #1565c0;
}

.no-tiers-message {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.empty-section-message {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 10px;
  margin: 5px 0;
}

.unassigned-empty-message {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}

.new-section-creation .new-section-item {
  margin-bottom: 16px;
}

.new-section-header {
  margin-bottom: 12px;
}

.new-section-input-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-section-input {
  flex: 1;
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.new-section-actions {
  display: flex;
  gap: 4px;
}

/* Visual distinction between production and staged sections */
.tiers-section-block-production {
  border: 1px solid #d1d5db;
}

.tiers-section-block-production h2::before {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
}

.tiers-section-block-staged {
  border: 1px solid #d1d5db;
}

.tiers-section-block-staged h2::before {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

/* Section badges */
.section-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 8px;
}

.section-badge-production {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.section-count {
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 500;
}

.unassigned h2::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  background: linear-gradient(135deg, #9ca3af, #6b7280);
  border-radius: 2px;
}

/* Section Group Containers */
.section-group {
  margin-bottom: 2rem;
  padding: 1rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}

.production-group {
  border-color: #d1d5db;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
}

.staged-group {
  border-color: #1976d2;
  background: linear-gradient(135deg, #f0f9ff 0%, #e3f2fd 100%);
}

.section-group-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 0.5rem;
}

.production-group .section-group-title {
  color: #6b7280;
  border-bottom-color: #d1d5db;
}

.staged-group .section-group-title {
  color: #1976d2;
  border-bottom-color: #1976d2;
}
</style>
