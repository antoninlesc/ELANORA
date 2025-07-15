<template>
  <div>
    <AppHeader :instance-name="instanceName" />
    <router-view />
    <AppFooter :instance-name="instanceName" :version="version" />
  </div>
</template>

<script setup>
import AppHeader from '@/components/layout/AppHeader.vue';
import AppFooter from '@/components/layout/AppFooter.vue';
</script>
