<template>
  <div>
    <h1 class="tiers-page-title">Tier Hierarchy</h1>
    <div v-if="loading" class="tiers-page-loading">Loading...</div>
    <div v-else-if="error" class="tiers-page-error">{{ error }}</div>
    <div v-else>
      <div class="tiers-tree-main-block">
        <TierTree
          v-for="(group, idx) in tierTree"
          :key="idx"
          :tiers="group"
          :group-index="idx"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import '@/assets/css/tiers.css';
import { ref, onMounted, computed } from 'vue';
import { useProjectStore } from '@/stores/project';
import { fetchProjectTiers } from '@/api/service/tierService';
import TierTree from '@/components/common/TierTree.vue';

const projectStore = useProjectStore();
const currentProject = computed(() => projectStore.currentProject);

const tierTree = ref([]);
const loading = ref(true);
const error = ref('');

onMounted(async () => {
  loading.value = true;
  error.value = '';
  try {
    if (!currentProject.value) {
      error.value = 'No active project selected.';
      return;
    }
    const data = await fetchProjectTiers(currentProject.value);
    tierTree.value = data;
  } catch {
    error.value = 'Failed to load tiers.';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.tiers-page-title {
  font-size: 2.2rem;
  font-weight: 700;
  color: #4f46e5;
  margin-bottom: 2rem;
  text-align: center;
  letter-spacing: 0.03em;
}

.tiers-page-loading,
.tiers-page-error {
  text-align: center;
  font-size: 1.2rem;
  margin-top: 2rem;
}

.tiers-page-error {
  color: #dc2626;
}
</style>
