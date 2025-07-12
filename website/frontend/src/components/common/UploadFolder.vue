<template>
  <div class="upload-folder-root">
    <input
      ref="folderInput"
      type="file"
      webkitdirectory
      directory
      multiple
      style="display: none"
      @change="onFolderChange"
    />
    <button class="upload-folder-btn" type="button" @click="openPicker">
      <span>📁</span> <span>Browse...</span>
    </button>
    <span v-if="files.length" class="upload-folder-summary">
      {{ files.length }} file{{ files.length > 1 ? 's' : '' }} selected
    </span>
    <div v-if="files.length" class="upload-folder-tree">
      <FolderTree :tree="fileTree" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

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
  files.value = Array.from(e.target.files);
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
      if (i === parts.length - 1) {
        // file
        node[part] = { type: 'file', file };
      } else {
        if (!node[part]) node[part] = { type: 'folder', children: {} };
        node = node[part].children;
      }
    }
  }
  return root;
}

// Recursive folder tree as a component using <template>
import { defineComponent, reactive } from 'vue';

const FolderTree = defineComponent({
  name: 'FolderTree',
  props: {
    tree: { type: Object, required: true },
    level: { type: Number, default: 0 },
  },
  setup(props) {
    const open = reactive({});
    const toggle = (folder) => {
      open[folder] = !open[folder];
    };
    return { open, toggle, props };
  },
  template: `
    <ul class="upload-folder-list" :style="{ marginLeft: (props.level * 14) + 'px' }">
      <template v-for="(node, name) in props.tree" :key="name">
        <li v-if="node.type === 'file'" class="upload-folder-file">
          <span class="upload-folder-file-name">{{ name }}</span>
        </li>
        <li v-else>
          <div
            class="upload-folder-folder"
            style="cursor:pointer;display:inline-flex;align-items:center;gap:4px;"
            @click="toggle(name)"
          >
            <span style="color:#388e3c;">{{ open[name] ? '📂' : '📁' }}</span>
            <span style="font-weight:600;">{{ name }}</span>
          </div>
          <FolderTree v-if="open[name]" :tree="node.children" :level="props.level + 1" />
        </li>
      </template>
    </ul>
  `,
});
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
