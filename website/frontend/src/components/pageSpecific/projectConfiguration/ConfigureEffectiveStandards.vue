<template>
  <div class="configure-effective-standards-container">
    <h2 class="configure-effective-standards-title">{{ t('configureEffectiveStandards.title') }}</h2>
    <table class="configure-effective-standards-table">
      <thead>
        <tr>
          <th class="configure-effective-standards-th">{{ t('configureEffectiveStandards.fileType') }}</th>
          <th class="configure-effective-standards-th">{{ t('configureEffectiveStandards.effectiveStandard') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="fileType in requiredFileTypes"
          :key="fileType.id"
          class="configure-effective-standards-row"
        >
          <td class="configure-effective-standards-td">
            {{ fileType.name }} ({{ fileType.extension }})
          </td>
          <td class="configure-effective-standards-td">
            <select
              v-model="effectiveStandards[fileType.id]"
              class="configure-effective-standards-select"
              @change="saveEffectiveStandard(fileType.id)"
            >
              <option
                v-for="standard in standardsByFileType[fileType.id]"
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useNamingStandardStore } from '@stores/namingStandard';
import { useFileTypeStore } from '@stores/fileType';
import effectiveNamingStandardApi from '@/api/service/effectiveNamingStandard.js';
import { useEventMessageStore } from '@stores/eventMessage';
import { useRoute } from 'vue-router';

const { t } = useI18n();
const eventMessageStore = useEventMessageStore();
const namingStandardStore = useNamingStandardStore();
const fileTypeStore = useFileTypeStore();
const route = useRoute();

const projectId = Number(route.params.projectId);
const effectiveStandards = ref({});

const fileTypes = computed(() => fileTypeStore.fileTypes);
const requiredFileTypes = computed(() =>
  fileTypes.value.filter(ft => ft.is_required)
);

const standardsByFileType = computed(() => {
  const result = {};
  for (const fileType of fileTypes.value) {
    result[fileType.id] = namingStandardStore.standards.filter(
      s => s.project_file_type_id === fileType.id
    );
  }
  return result;
});

async function fetchEffectiveStandards() {
  try {
    const { data: effectiveData } = await effectiveNamingStandardApi.getEffectiveStandards(projectId);
    effectiveStandards.value = {};
    for (const eff of effectiveData.effective_standards) {
      effectiveStandards.value[eff.project_file_type_id] = eff.naming_standard_id;
    }
  } catch {
    eventMessageStore.addMessage(
      t('configureEffectiveStandards.eventMessages.loadFailed'),
      'error'
    );
  }
}

async function saveEffectiveStandard(fileTypeId) {
  try {
    await effectiveNamingStandardApi.assignEffectiveStandard(
      projectId,
      fileTypeId,
      effectiveStandards.value[fileTypeId]
    );
    eventMessageStore.addMessage(
      t('configureEffectiveStandards.eventMessages.updateSuccess'),
      'success'
    );
  } catch {
    eventMessageStore.addMessage(
      t('configureEffectiveStandards.eventMessages.updateFailed'),
      'error'
    );
  }
}

onMounted(async () => {
  await fileTypeStore.fetchFileTypes(projectId);
  await namingStandardStore.fetchStandardsAndComponentNames(projectId);
  await fetchEffectiveStandards();
});
</script>

<style scoped>
.configure-effective-standards-container {
  margin: 0 auto;
}

.configure-effective-standards-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 2rem;
  text-align: center;
  color: #2d3748;
}
.configure-effective-standards-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  overflow: hidden;
}
.configure-effective-standards-th {
  background: #e2e8f0;
  color: #2d3748;
  font-weight: 500;
  padding: 0.8rem 1rem;
  text-align: left;
  border-bottom: 2px solid #cbd5e0;
}
.configure-effective-standards-row {
  border-bottom: 1px solid #e2e8f0;
}
.configure-effective-standards-td {
  padding: 0.7rem 1rem;
  font-size: 1rem;
  color: #4a5568;
}
.configure-effective-standards-select {
  width: 100%;
  padding: 0.4rem 0.7rem;
  border-radius: 5px;
  border: 1px solid #cbd5e0;
  font-size: 1rem;
  background: #f1f5f9;
}
.configure-effective-standards-success {
  margin-top: 1.5rem;
  color: #38a169;
  background: #f0fff4;
  padding: 0.7rem 1rem;
  border-radius: 6px;
  text-align: center;
}
.configure-effective-standards-error {
  margin-top: 1.5rem;
  color: #e53e3e;
  background: #fff5f5;
  padding: 0.7rem 1rem;
  border-radius: 6px;
  text-align: center;
}
</style>