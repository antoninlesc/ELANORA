<template>
  <TierAssignmentTree
    mode="management"
    @section-created="$emit('section-created', $event)"
    @section-renamed="$emit('section-renamed', $event)"
    @section-deleted="$emit('section-deleted', $event)"
    @tier-moved="$emit('tier-moved', $event)"
  />
</template>

<script setup>
import TierAssignmentTree from '@/components/common/TierAssignmentTree.vue';

// Re-export events for backward compatibility
defineEmits([
  'section-created',
  'section-renamed',
  'section-deleted',
  'tier-moved',
]);
</script>
