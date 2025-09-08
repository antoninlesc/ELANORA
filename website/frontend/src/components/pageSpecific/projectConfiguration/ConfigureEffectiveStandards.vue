<template>
  <div>
    <div class="configure-effective-standards-header">
      <h2 class="configure-effective-standards-title">{{ t('configureEffectiveStandards.title') }}</h2>
    </div>
    <!-- Location Selection -->
    <div class="configure-effective-standards-section">
      <label for="location-select" class="configure-effective-standards-label">{{ t('configureEffectiveStandards.standardLocation') }}</label>
      <select
        id="location-select"
        v-model="selectedLocationId"
        class="configure-effective-standards-select"
        @change="onLocationChange"
      >
        <option v-for="loc in locations" :key="loc.id" :value="loc.id">
          {{ t('configureEffectiveStandards.standardLocations.' + loc.label) }}
        </option>
      </select>
    </div>
    <!-- Drag & Drop File Type Association -->
    <div class="configure-effective-standards-dnd-row">
      <div class="configure-effective-standards-dnd-box">
        <div class="configure-effective-standards-chips-label">{{ t('configureEffectiveStandards.availableFileTypes') }}</div>
        <draggable
          :list="availableFileTypesDraggable"
          :group="{ name: 'fileTypes', pull: true, put: true }"
          item-key="id"
          class="configure-effective-standards-chips-list"
          @change="onFileTypeChange"
        >
          <template #item="{ element }">
            <div class="configure-effective-standards-chip">
              {{ element.name }} ({{ element.extension }})
            </div>
          </template>
        </draggable>
      </div>
      <div class="configure-effective-standards-dnd-box">
        <div class="configure-effective-standards-chips-label">{{ t('configureEffectiveStandards.associatedFileTypes') }}</div>
        <draggable
          :list="associatedFileTypesDraggable"
          :group="{ name: 'fileTypes', pull: true, put: true }"
          item-key="id"
          class="configure-effective-standards-chips-list"
          @change="onFileTypeChange"
        >
          <template #item="{ element }">
            <div class="configure-effective-standards-chip configure-effective-standards-chip--active">
              {{ element.name }} ({{ element.extension }})
            </div>
          </template>
        </draggable>
      </div>
    </div>
    <!-- Standards Table -->
    <div v-if="activeFileTypes.length" class="configure-effective-standards-assign-standards-section">
      <h3 class="configure-effective-standards-section-title">{{ t('configureEffectiveStandards.assignStandardsTitle') }}</h3>
      <table class="configure-effective-standards-table">
        <thead>
          <tr>
            <th class="configure-effective-standards-th">{{ t('configureEffectiveStandards.fileType') }}</th>
            <th class="configure-effective-standards-th">{{ t('configureEffectiveStandards.effectiveStandard') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="fileTypeId in activeFileTypes"
            :key="fileTypeId"
            class="configure-effective-standards-row"
          >
            <td class="configure-effective-standards-td">
              {{ fileTypes.find(ft => ft.id === fileTypeId)?.name }}
            </td>
            <td class="configure-effective-standards-td">
              <select
                v-model="effectiveStandards[fileTypeId]"
                :class="['configure-effective-standards-select', { 'configure-effective-standards-select--unassigned': !effectiveStandards[fileTypeId] }]"
                @change="onEffectiveStandardChange(fileTypeId)"
              >
                <option value="">{{ t('configureEffectiveStandards.selectStandard') }}</option>
                <option
                  v-for="standard in standardsByFileType[fileTypeId]"
                  :key="standard.id"
                  :value="standard.id"
                >
                  {{ standard.name }}
                </option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="errorMessage" class="configure-effective-standards-error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="configure-effective-standards-success">{{ successMessage }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useNamingStandardStore } from '@stores/namingStandard';
import { useFileTypeStore } from '@stores/fileType';
import { useEffectiveStandardStore } from '@stores/effectiveStandard';
import { useEventMessageStore } from '@stores/eventMessage';
import { useRoute } from 'vue-router';
import draggable from 'vuedraggable';

const { t } = useI18n();
const namingStandardStore = useNamingStandardStore();
const fileTypeStore = useFileTypeStore();
const effectiveStandardStore = useEffectiveStandardStore();
const eventMessageStore = useEventMessageStore();
const route = useRoute();

const projectId = Number(route.params.projectId);
const selectedLocationId = ref(null);
const errorMessage = ref("");
const successMessage = ref("");
const dragZone = ref(null);

const locations = computed(() => effectiveStandardStore.locations);
const fileTypes = computed(() => fileTypeStore.fileTypes);
const activeFileTypes = computed(() => {
  if (!selectedLocationId.value) return [];
  return fileTypeStore.fileTypesByLocation[selectedLocationId.value] || [];
});
const effectiveStandards = computed({
  get() {
    if (!selectedLocationId.value) return {};
    return effectiveStandardStore.effectiveStandards[selectedLocationId.value] || {};
  },
  set(val) {
    if (!selectedLocationId.value) return;
    effectiveStandardStore.effectiveStandards[selectedLocationId.value] = val;
  }
});
const standardsByFileType = computed(() => {
  const result = {};
  for (const fileType of fileTypes.value) {
    result[fileType.id] = namingStandardStore.standards.filter(
      s => s.project_file_type_id === fileType.id
    );
  }
  return result;
});
const availableFileTypesDraggable = computed(() =>
  fileTypes.value.filter(ft => !activeFileTypes.value.includes(ft.id))
);
const associatedFileTypesDraggable = computed(() =>
  fileTypes.value.filter(ft => activeFileTypes.value.includes(ft.id))
);

async function loadInitialData() {
  await fileTypeStore.fetchFileTypes(projectId);
  await namingStandardStore.fetchStandardsAndComponentNames(projectId);
  await effectiveStandardStore.fetchLocations();
  if (locations.value.length > 0) {
    selectedLocationId.value = locations.value[0].id;
    await fileTypeStore.fetchFileTypesForLocation(projectId, selectedLocationId.value);
    await effectiveStandardStore.fetchEffectiveStandards(projectId, selectedLocationId.value, activeFileTypes.value);
  }
}

async function onLocationChange() {
  await fileTypeStore.fetchFileTypesForLocation(projectId, selectedLocationId.value);
  await effectiveStandardStore.fetchEffectiveStandards(projectId, selectedLocationId.value, activeFileTypes.value);
  errorMessage.value = "";
  successMessage.value = "";
}

async function onFileTypeChange(evt) {
  if (!selectedLocationId.value) return;
  const location = locations.value.find(loc => loc.id === selectedLocationId.value);
  // Handle add (drag from available to associated)
  if (evt.added && evt.added.element) {
    const added = evt.added.element;
    if (added && added.id && !activeFileTypes.value.includes(added.id)) {
      await fileTypeStore.addFileTypeToLocation(projectId, selectedLocationId.value, added.id);
      eventMessageStore.addMessage(
        t('configureEffectiveStandards.eventMessages.fileTypeAdded', {
          fileType: added.name,
          location: location?.label || ''
        }),
        'success'
      );
      await effectiveStandardStore.fetchEffectiveStandards(projectId, selectedLocationId.value, activeFileTypes.value);
    }
  }
  // Handle remove (drag from associated to available)
  if (evt.removed && evt.removed.element) {
    const removed = evt.removed.element;
    if (removed && removed.id && activeFileTypes.value.includes(removed.id)) {
      await fileTypeStore.removeFileTypeFromLocation(projectId, selectedLocationId.value, removed.id);
      // Unassign effective standard for this file type at this location
      await effectiveStandardStore.unassignEffectiveStandard(projectId, removed.id, selectedLocationId.value);
      eventMessageStore.addMessage(
        t('configureEffectiveStandards.eventMessages.fileTypeRemoved', {
          fileType: removed.name,
          location: location?.label || ''
        }),
        'success'
      );
      await effectiveStandardStore.fetchEffectiveStandards(projectId, selectedLocationId.value, activeFileTypes.value);
    }
  }
  dragZone.value = null;
}

async function onEffectiveStandardChange(fileTypeId) {
  const selected = effectiveStandards.value[fileTypeId];
  if (selected === "") {
    await effectiveStandardStore.unassignEffectiveStandard(projectId, fileTypeId, selectedLocationId.value);
    eventMessageStore.addMessage(
      t('configureEffectiveStandards.eventMessages.removeSuccess'),
      'success'
    );
  } else if (!isNaN(Number(selected))) {
    await effectiveStandardStore.assignEffectiveStandard(projectId, fileTypeId, selected, selectedLocationId.value);
    eventMessageStore.addMessage(
      t('configureEffectiveStandards.eventMessages.updateSuccess'),
      'success'
    );
  }
  await effectiveStandardStore.fetchEffectiveStandards(projectId, selectedLocationId.value, activeFileTypes.value);
}

onMounted(loadInitialData);

watch(selectedLocationId, async (newVal, oldVal) => {
  if (newVal !== oldVal) {
    await onLocationChange();
  }
});
</script>

<style scoped>
.configure-effective-standards-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
}
.configure-effective-standards-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: #1f2937;
}
.configure-effective-standards-section {
  margin-bottom: 2rem;
}
.configure-effective-standards-section-title {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #2563eb;
}
.configure-effective-standards-label {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.7rem;
  color: #2d3748;
  display: block;
}
.configure-effective-standards-dnd-row {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
}
.configure-effective-standards-dnd-box {
  flex: 1;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.07);
  padding: 1.2rem;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  border: 2px solid #e2e8f0;
  transition: border-color 0.2s, background 0.2s;
}
.configure-effective-standards-chips-label {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.7rem;
  color: #2d3748;
}
.configure-effective-standards-chips-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  min-height: 40px;
}
.configure-effective-standards-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 1rem;
  background: #e2e8f0;
  color: #2d3748;
  border: 2px solid #e2e8f0;
  cursor: grab;
  transition: background 0.2s, border-color 0.2s;
  margin-bottom: 0.3rem;
}
.configure-effective-standards-chip:hover {
  background: #cbd5e0;
  border-color: #2563eb;
}
.configure-effective-standards-chip--active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
.configure-effective-standards-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  overflow: hidden;
  margin-top: 1.5rem;
}
.configure-effective-standards-th {
  background: #e2e8f0;
  color: #2d3748;
  font-weight: 500;
  padding: 1rem 1.2rem;
  text-align: left;
  border-bottom: 2px solid #cbd5e0;
}
.configure-effective-standards-row {
  border-bottom: 1px solid #e2e8f0;
}
.configure-effective-standards-td {
  padding: 1rem 1.2rem;
  font-size: 1rem;
  color: #4a5568;
}
.configure-effective-standards-select {
  width: 100%;
  padding: 0.5rem 0.9rem;
  border-radius: 6px;
  border: 1px solid #cbd5e0;
  font-size: 1rem;
  background: #f1f5f9;
  margin-bottom: 0.5rem;
}
.configure-effective-standards-select--unassigned {
  border: 1px solid #e53e3e;
  background: #fff5f5;
}
.configure-effective-standards-success {
  margin-top: 2rem;
  color: #38a169;
  background: #f0fff4;
  padding: 1rem 1.2rem;
  border-radius: 8px;
  text-align: center;
  font-size: 1.1rem;
}
.configure-effective-standards-error {
  margin-top: 2rem;
  color: #e53e3e;
  background: #fff5f5;
  padding: 1rem 1.2rem;
  border-radius: 8px;
  text-align: center;
  font-size: 1.1rem;
}
.configure-effective-standards-assign-standards-section {
  margin-bottom: 2rem;
}
</style>