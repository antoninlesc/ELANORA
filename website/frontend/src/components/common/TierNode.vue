<template>
  <li class="tiers-tree-node">
    <div class="tiers-tree-label" @click="toggle">
      <span v-if="hasChildren" class="tiers-tree-toggle">
        <span v-if="open">▼</span>
        <span v-else>▶</span>
      </span>
      <span v-else class="tiers-tree-toggle" style="opacity: 0">▶</span>
      <span v-if="hasChildren" class="tiers-tree-icon">📁</span>
      <span v-else class="tiers-tree-icon">📄</span>
      <span class="tiers-tree-tiername">{{ tier.tier_name }}</span>
      <span v-if="hasChildren" class="tiers-tree-children-count">
        ({{ tier.children.length }})
      </span>
    </div>
    <transition name="fade">
      <ul v-if="hasChildren && open" class="tiers-tree-children">
        <TierNode
          v-for="child in sortedChildren"
          :key="child.tier_id"
          :tier="child"
        />
      </ul>
    </transition>
  </li>
</template>

<script setup>
import { ref, computed } from 'vue';
import TierNode from './TierNode.vue';

const props = defineProps({
  tier: { type: Object, required: true },
});

const open = ref(false);

const hasChildren = computed(
  () => props.tier.children && props.tier.children.length > 0
);

// Sort children: folders first (alphabetical), then files (alphabetical)
const sortedChildren = computed(() => {
  if (!props.tier.children) return [];
  const folders = props.tier.children
    .filter(
      (child) => Array.isArray(child.children) && child.children.length > 0
    )
    .sort((a, b) => a.tier_name.localeCompare(b.tier_name));
  const files = props.tier.children
    .filter(
      (child) => !Array.isArray(child.children) || child.children.length === 0
    )
    .sort((a, b) => a.tier_name.localeCompare(b.tier_name));
  return [...folders, ...files];
});

function toggle() {
  open.value = !open.value;
}
</script>

<style scoped>
.tiers-tree-node {
  margin-bottom: 0.2rem;
}

.tiers-tree-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0.3rem 0.7rem;
  border-radius: 5px;
  transition: background 0.15s;
  font-size: 1rem;
  font-weight: 500;
}

.tiers-tree-label:hover {
  background: #f3f4f6;
}

.tiers-tree-toggle {
  margin-right: 0.4rem;
  font-size: 1.1rem;
  user-select: none;
  width: 1.2em;
  display: inline-block;
  text-align: center;
}

.tiers-tree-icon {
  margin-right: 0.3em;
}

.tiers-tree-tiername {
  margin-left: 0.1rem;
}

.tiers-tree-children-count {
  font-size: 0.9rem;
  color: #a78bfa;
  margin-left: 0.5rem;
}

.tiers-tree-children {
  margin-left: 1.3em;
  border-left: 1.5px solid #e0e7ef;
  padding-left: 0.7em;
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
