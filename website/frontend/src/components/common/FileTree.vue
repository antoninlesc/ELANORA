<template>
  <div>
    <div v-for="file in files" :key="file.name" class="filetree-file">
      <img
        v-if="isEafFile(file.name)"
        src="/images/icons/ELAN.svg"
        alt="ELAN file"
        style="width: 18px; height: 18px; margin-right: 4px; vertical-align: middle;"
      />
      <span :title="file.name" class="filetree-name">{{ file.name }}</span>
    </div>
  </div>
</template>

<script setup>
const { files } = defineProps({
  files: { type: Array, required: true }
});

function isEafFile(name) {
  return name.toLowerCase().endsWith('.eaf');
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
.filetree-name {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  vertical-align: middle;
}
</style>
