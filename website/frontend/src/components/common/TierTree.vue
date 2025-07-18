<template>
  <div class="tiers-tree-container">
    <div class="tiers-tree-scroll-area">
      <div class="tiers-tree-group-label" @click="toggleGroup">
        <span class="tiers-tree-toggle">
          <span v-if="open">▼</span>
          <span v-else>▶</span>
        </span>
        <span class="tiers-tree-group-name">{{ groupLabel }}</span>
      </div>
      <transition name="fade">
        <ul v-if="open" class="tiers-tree-root">
          <li
            v-for="rootTier in sortedRootTiers"
            :key="rootTier.tier_id"
            class="tiers-tree-root-group"
          >
            <TierNode :tier="rootTier" />
          </li>
        </ul>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { defineProps, ref, computed } from 'vue';
import TierNode from './TierNode.vue';

const props = defineProps({
  tiers: { type: Array, required: true },
  groupIndex: { type: Number, required: true },
  groupLabel: { type: String, required: false, default: '' },
});

const open = ref(false);

const sortedRootTiers = computed(() => {
  if (!props.tiers) return [];
  const folders = props.tiers
    .filter((tier) => Array.isArray(tier.children) && tier.children.length > 0)
    .sort((a, b) => a.tier_name.localeCompare(b.tier_name));
  const files = props.tiers
    .filter(
      (tier) => !Array.isArray(tier.children) || tier.children.length === 0
    )
    .sort((a, b) => a.tier_name.localeCompare(b.tier_name));
  return [...folders, ...files];
});

function toggleGroup() {
  open.value = !open.value;
}
</script>

<style scoped>
.tiers-tree-scroll-area {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.tiers-tree-group-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 600;
  font-size: 1.1rem;
  background: #ede9fe;
  color: #5b21b6;
  border-radius: 8px;
  padding: 0.7rem 1.2rem;
  box-shadow: 0 1px 4px 0 #e0e7ef;
  transition: background 0.2s;
  margin-bottom: 0.7rem;
}

.tiers-tree-group-label:hover {
  background: #c7d2fe;
}

.tiers-tree-toggle {
  margin-right: 0.6rem;
  font-size: 1.1rem;
  user-select: none;
  width: 1.2em;
  display: inline-block;
  text-align: center;
}

.tiers-tree-group-name {
  margin-right: 0.7em;
}

.tiers-tree-root {
  list-style: none;
  padding-left: 0;
  margin: 0;
}

.tiers-tree-root-group {
  margin-bottom: 1.2rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  max-height: 0;
}
</style>
