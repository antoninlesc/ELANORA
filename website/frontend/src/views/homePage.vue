<template>
  <div class="home-page home-page-bg">
    <div class="home-page-card">
      <h1 class="home-title">{{ $t('homePage.welcomeMessage') }}</h1>
      <p class="home-desc">{{ $t('homePage.description') }}</p>
      <p class="home-instructions">{{ $t('homePage.instructions') }}</p>
      <router-link to="/login">
        <button class="home-btn">
          {{ $t('homePage.getStarted') }}
        </button>
      </router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped src="@/assets/css/homePage.css"></style>