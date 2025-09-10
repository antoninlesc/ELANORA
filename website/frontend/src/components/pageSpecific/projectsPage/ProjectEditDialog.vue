<template>
  <div class="project-edit-modal-overlay">
    <div class="project-edit-modal-content">
      <template v-if="props.project && props.project.project_name">
        <h2 class="project-edit-modal-title">Edit Project</h2>
        <form @submit.prevent="handleEdit">
          <input
            v-model="name"
            class="project-edit-input"
            type="text"
            placeholder="Project name"
            maxlength="100"
            required
            @input="validateName"
          />
          <div class="project-edit-error" style="min-height: 20px">
            <span v-if="nameError">{{ nameError }}</span>
          </div>
          <textarea
            v-model="description"
            class="project-edit-textarea"
            placeholder="Description (optional)"
            maxlength="5000"
            rows="5"
            @input="validateDescription"
          ></textarea>
          <div class="project-edit-desc-info">
            <span>{{ description.length }}/5000</span>
          </div>
          <div class="project-edit-error" style="min-height: 20px">
            <span v-if="descError">{{ descError }}</span>
          </div>
          <div class="project-edit-actions">
            <button
              type="submit"
              class="project-page-create-btn"
              :disabled="editing || !canEdit"
            >
              {{ editing ? 'Saving...' : 'Save' }}
            </button>
            <button
              type="button"
              class="project-page-create-btn"
              @click="emit('close')"
            >
              Cancel
            </button>
          </div>
          <div class="project-edit-error" style="min-height: 20px">
            <span v-if="error">{{ error }}</span>
          </div>
        </form>
      </template>
      <template v-else>
        <div>Loading...</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import gitService from '@api/service/gitService';
import { useProjectStore } from '@stores/project';

const props = defineProps({
  project: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['close', 'edited']);
const projectStore = useProjectStore();

const name = ref('');
const description = ref('');
const editing = ref(false);
const error = ref('');
const nameError = ref('');
const descError = ref('');

watch(
  () => props.project,
  (project) => {
    name.value = project?.project_name || '';
    description.value = project?.project_description || '';
  },
  { immediate: true }
);

const allProjectNames = computed(() =>
  (projectStore.projects || [])
    .filter((p) => p.project_id !== props.project?.project_id)
    .map((p) => p.project_name?.toLowerCase())
);

function validateName() {
  const trimmed = name.value.trim();
  if (!trimmed) {
    nameError.value = 'Project name is required.';
  } else if (trimmed.length > 100) {
    nameError.value = 'Project name must be at most 100 characters.';
  } else if (allProjectNames.value.includes(trimmed.toLowerCase())) {
    nameError.value = 'A project with this name already exists.';
  } else {
    nameError.value = '';
  }
}

function validateDescription() {
  if (description.value && !description.value.trim()) {
    description.value = '';
  }
  if (description.value.length > 5000) {
    descError.value = 'Description must be at most 5000 characters.';
  } else {
    descError.value = '';
  }
}

const canEdit = computed(() => {
  validateName();
  validateDescription();
  return !nameError.value && !descError.value && name.value.trim();
});

async function handleEdit() {
  validateName();
  validateDescription();
  if (!canEdit.value) {
    error.value = 'Please fix the errors above.';
    return;
  }
  editing.value = true;
  try {
    await gitService.editProject(
      props.project.project_name,
      name.value.trim(),
      description.value.trim()
    );
    error.value = '';
    emit('edited');
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Failed to edit project.';
  } finally {
    editing.value = false;
  }
}

onMounted(() => {
  projectStore.initBroadcastChannel();
});
</script>

<style scoped>
.project-edit-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 50%);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.project-edit-modal-content {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  min-width: 340px;
  max-width: 95vw;
  box-shadow: 0 2px 16px rgb(0 0 0 / 8%);
}

.project-edit-modal-title {
  margin-bottom: 18px;
  font-size: 1.3rem;
  font-weight: 600;
  text-align: center;
}

.project-edit-input {
  width: 100%;
  margin-bottom: 10px;
  padding: 8px 12px;
  border: 1.5px solid #bdbdbd;
  border-radius: 6px;
  font-size: 1rem;
}

.project-edit-textarea {
  width: 100%;
  min-height: 90px;
  max-height: 180px;
  margin-bottom: 4px;
  padding: 10px 12px;
  border: 1.5px solid #bdbdbd;
  border-radius: 6px;
  font-size: 1rem;
  resize: vertical;
  overflow-y: auto;
  background: #f8f9fa;
  box-sizing: border-box;
}

.project-edit-desc-info {
  text-align: right;
  font-size: 0.95rem;
  color: #888;
  margin-bottom: 8px;
}

.project-edit-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 18px;
}

.project-edit-error {
  color: #d32f2f;
  margin-bottom: 8px;
  font-size: 0.98rem;
  text-align: left;
  margin-top: -2px;
  min-height: 20px;
}
</style>
