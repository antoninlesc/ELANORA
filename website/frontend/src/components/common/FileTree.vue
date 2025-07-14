<template>
  <div>
    <template v-if="tree">
      <div
        v-if="tree.type === 'file'"
        :style="{ marginLeft: `${level * 18}px` }"
        class="filetree-file"
      >
        <span style="color: #1976d2">📄</span>
        <span>{{ tree.name }}</span>
      </div>
      <div
        v-else
        :style="{ marginLeft: `${level * 18}px` }"
        class="filetree-folder"
      >
        <div class="filetree-folder-header" @click="toggle">
          <span style="color: #388e3c">{{ open ? '📂' : '📁' }}</span>
          <span style="font-weight: 600">{{ tree.name }}</span>
        </div>
        <div v-show="open">
          <FileTree
            v-for="child in tree.children"
            :key="child.name + child.type"
            :tree="child"
            :level="level + 1"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  tree: { type: Object, required: true },
  level: { type: Number, default: 0 },
});

const open = ref(props.level === 0); // root open by default

function toggle() {
  open.value = !open.value;
}
</script>

<style scoped>
.filetree-file {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: default;
  padding: 2px 0;
}

.filetree-folder {
  margin-bottom: 2px;
}

.filetree-folder-header {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
}
</style>
