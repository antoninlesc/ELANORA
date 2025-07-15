<template>
  <div id="app">
    <AppHeader class="navbar" />
    <router-view class="content" />
    <AppFooter class="footer" />
  </div>
</template>

<script setup>
import AppHeader from '@/components/layout/AppHeader.vue';
import AppFooter from '@/components/layout/AppFooter.vue';

import '@css/default-layout.css';
</script>
