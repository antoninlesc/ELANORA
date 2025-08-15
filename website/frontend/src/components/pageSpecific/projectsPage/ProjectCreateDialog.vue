<template>
  <div class="project-create-modal-overlay">
    <div class="project-create-modal-content">
      <h2 class="project-create-modal-title">
        {{ t('projectsPage.createProject') }}
      </h2>
      <form @submit.prevent="handleCreate">
        <!-- Project Name -->
        <input
          v-model="name"
          class="project-create-input"
          type="text"
          :placeholder="t('projectsPage.createDialog.projectNamePlaceholder')"
          maxlength="100"
          required
          @input="validateName"
        />
        <div class="project-create-error" style="min-height: 20px">
          <span v-if="nameError">{{ nameError }}</span>
        </div>
        <!-- Description -->
        <textarea
          v-model="description"
          class="project-create-textarea"
          :placeholder="
            t('projectsPage.createDialog.projectDescriptionPlaceholder')
          "
          maxlength="5000"
          rows="5"
          @input="validateDescription"
        ></textarea>
        <div class="project-create-desc-info">
          <span>{{ description.length }}/5000</span>
        </div>
        <div class="project-create-error" style="min-height: 20px">
          <span v-if="descError">{{ descError }}</span>
        </div>
        <!-- Upload Area -->
        <div
          class="project-create-upload-zone"
          :class="{ dragover: isDragOver }"
          @drop="handleDrop"
          @dragover.prevent="onDragOver"
          @dragleave="isDragOver = false"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            webkitdirectory
            directory
            multiple
            accept=".eaf"
            style="display: none"
            @change="handleFileSelect"
          />
          <div v-if="!fileTree" class="upload-content">
            <div class="upload-icon">📁</div>
            <h3>{{ t('projectsPage.createDialog.dropFolder') }}</h3>
            <p>{{ t('projectsPage.createDialog.onlyEafFiles') }}</p>
          </div>
          <div v-else class="files-preview">
            <h4>{{ t('projectsPage.folderPreview') }}</h4>
            <FileTree :files="flatFiles"/>
          </div>
        </div>
        <div class="project-create-error" style="min-height: 20px">
          <span v-if="error">{{ error }}</span>
        </div>
        <div class="project-create-actions">
          <button
            type="submit"
            class="project-page-create-btn"
            :disabled="creating || !canCreate"
          >
            {{
              creating
                ? t('projectsPage.createDialog.creating')
                : t('projectsPage.createDialog.create')
            }}
          </button>
          <button
            type="button"
            class="project-page-create-btn"
            @click="emit('close')"
          >
            {{ t('common.cancel') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import FileTree from '@components/common/FileTree.vue';
import gitService from '@api/service/gitService';
import { useProjectStore } from '@stores/project';

const { t } = useI18n();
const emit = defineEmits(['close', 'created']);
const projectStore = useProjectStore();

const name = ref('');
const description = ref('');
const selectedFiles = ref([]);
const fileTree = ref(null);
const isDragOver = ref(false);
const creating = ref(false);
const error = ref('');
const fileInput = ref(null);

const nameError = ref('');
const descError = ref('');

const allProjectNames = computed(() =>
  (projectStore.projects || []).map((p) => p.project_name.toLowerCase())
);

function validateName() {
  const trimmed = name.value.trim();
  if (!trimmed) {
    nameError.value = t('projectsPage.createDialog.errors.nameRequired');
  } else if (trimmed.length > 100) {
    nameError.value = t('projectsPage.createDialog.errors.nameTooLong');
  } else if (allProjectNames.value.includes(trimmed.toLowerCase())) {
    nameError.value = t('projectsPage.createDialog.errors.nameExists');
  } else {
    nameError.value = '';
  }
}

function validateDescription() {
  if (description.value && !description.value.trim()) {
    description.value = '';
  }
  if (description.value.length > 5000) {
    descError.value = t('projectsPage.createDialog.errors.descTooLong');
  } else {
    descError.value = '';
  }
}

const canCreate = computed(() => {
  validateName();
  validateDescription();
  return !nameError.value && !descError.value && name.value.trim();
});

function triggerFileInput() {
  fileInput.value?.click();
}

function traverseFileTree(item, path, files) {
  return new Promise((resolve) => {
    if (item.isFile) {
      item.file((file) => {
        file.customRelativePath = path + file.name;
        files.push(file);
        resolve();
      });
    } else if (item.isDirectory) {
      const dirReader = item.createReader();
      dirReader.readEntries((entries) => {
        Promise.all(
          entries.map((entry) =>
            traverseFileTree(entry, path + item.name + '/', files)
          )
        ).then(resolve);
      });
    } else {
      resolve();
    }
  });
}

function buildTree(files) {
  const root = { name: 'root', type: 'folder', children: [] };
  for (const file of files) {
    if (!file.name.toLowerCase().endsWith('.eaf')) continue;
    const relPath =
      file.customRelativePath || file.webkitRelativePath || file.name;
    const parts = relPath.split('/');
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        node.children.push({ name: part, type: 'file' });
      } else {
        let folder = node.children.find(
          (c) => c.type === 'folder' && c.name === part
        );
        if (!folder) {
          folder = { name: part, type: 'folder', children: [] };
          node.children.push(folder);
        }
        node = folder;
      }
    }
  }
  if (root.children.length === 1 && root.children[0].type === 'folder') {
    return root.children[0];
  }
  return root;
}

function handleFileSelect(event) {
  const files = Array.from(event.target.files).filter((f) =>
    f.name.toLowerCase().endsWith('.eaf')
  );
  selectedFiles.value = files;
  fileTree.value = files.length ? buildTree(files) : null;
}

function onDragOver(event) {
  event.preventDefault();
  if (
    event.dataTransfer.items &&
    Array.from(event.dataTransfer.items).some((item) => item.kind === 'file')
  ) {
    isDragOver.value = true;
  }
}

async function handleDrop(event) {
  event.preventDefault();
  isDragOver.value = false;
  const items = event.dataTransfer.items;
  if (items && items.length && items[0].webkitGetAsEntry) {
    const entries = [];
    for (const item of items) {
      const entry = item.webkitGetAsEntry();
      if (entry) entries.push(entry);
    }
    const files = [];
    await Promise.all(
      entries.map((entry) => traverseFileTree(entry, '', files))
    );
    const eafFiles = files.filter((f) => f.name.toLowerCase().endsWith('.eaf'));
    selectedFiles.value = eafFiles;
    fileTree.value = eafFiles.length ? buildTree(eafFiles) : null;
  } else if (event.dataTransfer.files && event.dataTransfer.files.length) {
    const files = Array.from(event.dataTransfer.files).filter((f) =>
      f.name.toLowerCase().endsWith('.eaf')
    );
    selectedFiles.value = files;
    fileTree.value = files.length ? buildTree(files) : null;
  } else {
    error.value = t('projectsPage.createDialog.errors.folderDropNotSupported');
  }
}

const flatFiles = computed(() =>
  selectedFiles.value
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(f => ({ name: f.name, type: 'file' }))
);

async function handleCreate() {
  validateName();
  validateDescription();
  if (!canCreate.value) {
    error.value = t('projectsPage.createDialog.errors.fixAbove');
    return;
  }
  creating.value = true;
  try {
    if (selectedFiles.value.length > 0) {
      await gitService.initProjectFromFolderUpload({
        project_name: name.value.trim(),
        description: description.value.trim() || undefined,
        files: selectedFiles.value,
      });
    } else {
      await gitService.createProject({
        project_name: name.value.trim(),
        description: description.value.trim() || undefined,
      });
    }
    error.value = '';
    creating.value = false;
    selectedFiles.value = [];
    fileTree.value = null;
    name.value = '';
    description.value = '';
    if (fileInput.value) fileInput.value.value = '';
    emit('created');
  } catch (e) {
    error.value =
      e?.response?.data?.detail ||
      t('projectsPage.createDialog.errors.createFailed');
  } finally {
    creating.value = false;
  }
}
</script>

<style scoped>
.project-create-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 50%);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.project-create-modal-content {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  min-width: 600px;
  max-width: 95vw;
  box-shadow: 0 2px 16px rgb(0 0 0 / 8%);
}

.project-create-modal-title {
  margin-bottom: 18px;
  font-size: 1.3rem;
  font-weight: 600;
  text-align: center;
}

.project-create-input {
  width: 100%;
  margin-bottom: 10px;
  padding: 8px 12px;
  border: 1.5px solid #bdbdbd;
  border-radius: 6px;
  font-size: 1rem;
}

.project-create-textarea {
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

.project-create-desc-info {
  text-align: right;
  font-size: 0.95rem;
  color: #888;
  margin-bottom: 8px;
}

.project-create-upload-zone {
  border: 2px dashed #1976d2;
  border-radius: 10px;
  padding: 24px;
  text-align: center;
  margin-bottom: 16px;
  cursor: pointer;
  transition:
    border 0.2s,
    background 0.2s;
  min-height: 120px;
}

.project-create-upload-zone.dragover {
  border-color: #388e3c;
  background: #e8f5e9;
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.files-preview {
  text-align: left;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px 10px;
  margin-top: 8px;
}

.project-create-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 18px;
}

.project-create-error {
  color: #d32f2f;
  margin-bottom: 8px;
  font-size: 0.98rem;
  text-align: left;
  margin-top: -2px;
  min-height: 20px;
}
</style>
