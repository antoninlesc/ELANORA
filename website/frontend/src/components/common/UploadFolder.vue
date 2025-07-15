<template>
  <div class="upload-folder-root">
    <input
      ref="folderInput"
      type="file"
      webkitdirectory
      directory
      style="display: none"
      accept=".eaf"
      @change="onFolderChange"
    />
    <button class="upload-folder-btn" type="button" @click="openPicker">
      <font-awesome-icon icon="folder-open" style="margin-right: 6px" />
      <span>Browse...</span>
    </button>
    <span v-if="files.length" class="upload-folder-summary">
      {{ files.length }} file{{ files.length > 1 ? 's' : '' }} selected
    </span>
    <div v-if="files.length" class="upload-folder-tree">
      <FileTree v-if="files.length" :tree="fileTree" :level="0" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import FileTree from './FileTree.vue';
import FontAwesomeIcon from '@/plugins/fontawesome';

defineProps({
  modelValue: { type: Array, default: () => [] },
});
const emit = defineEmits(['update:modelValue']);

const files = ref([]);
const fileTree = ref({});

function openPicker() {
  files.value = [];
  fileTree.value = {};
  emit('update:modelValue', []);
  folderInput.value.value = null;
  folderInput.value.click();
}

function onFolderChange(e) {
  // Only keep .eaf files
  const allFiles = Array.from(e.target.files);
  const eafFiles = allFiles.filter((f) =>
    f.name.toLowerCase().endsWith('.eaf')
  );
  files.value = eafFiles;
  emit('update:modelValue', files.value);
  fileTree.value = buildTree(files.value);
}

const folderInput = ref(null);

// Build a tree from the flat file list
function buildTree(files) {
  const root = {};
  for (const file of files) {
    const parts = file.webkitRelativePath.split('/');
    let node = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (!node[part]) {
        node[part] = {
          name: part,
          type: i === parts.length - 1 ? 'file' : 'folder',
          children: i === parts.length - 1 ? undefined : {},
        };
      }
      node = node[part].children || node[part];
    }
  }
  // Recursively convert children objects to arrays
  function toArray(node) {
    if (node.type === 'folder') {
      node.children = Object.values(node.children).map(toArray);
    }
    return node;
  }
  const roots = Object.values(root).map(toArray);
  // If only one root, return it; else wrap in a virtual root
  return roots.length === 1
    ? roots[0]
    : { name: '', type: 'folder', children: roots };
}
</script>

<style scoped>
.upload-folder-root {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.upload-folder-btn {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 18px;
  font-size: 1rem;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}

.upload-folder-btn:hover {
  background: #1565c0;
}

.upload-folder-summary {
  color: #1976d2;
  font-weight: 500;
  margin-left: 2px;
}

.upload-folder-list {
  margin: 0;
  padding: 0 0 0 12px;
  list-style: none;
  max-height: 180px;
  overflow-y: auto;
  border-left: 2px solid #e3e3e3;
}

.upload-folder-file {
  font-size: 0.97rem;
  color: #333;
  padding: 2px 0;
  white-space: pre;
}

.upload-folder-file-name {
  font-family: 'Fira Mono', Consolas, monospace;
}

.upload-folder-folder {
  user-select: none;
}
</style>
