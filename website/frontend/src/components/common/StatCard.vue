<template>
  <div class="stat-card" :class="cardClass">
    <div v-if="icon" class="stat-icon">{{ icon }}</div>
    <div class="stat-content">
      <h3 class="stat-number">{{ value }}</h3>
      <p class="stat-label">{{ label }}</p>
      <span v-if="trend" class="stat-trend" :class="trendClass">{{
        trend
      }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  icon: {
    type: String,
    default: '',
  },
  value: {
    type: [String, Number],
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  trend: {
    type: String,
    default: '',
  },
  trendType: {
    type: String,
    default: 'neutral',
    validator: (value) => ['positive', 'negative', 'neutral'].includes(value),
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) =>
      ['default', 'primary', 'warning', 'success'].includes(value),
  },
});

const cardClass = computed(() => ({
  [`stat-card--${props.variant}`]: props.variant !== 'default',
}));

const trendClass = computed(() => ({
  [`trend--${props.trendType}`]: true,
}));
</script>

<style scoped>
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgb(0 0 0 / 8%);
  border-left: 4px solid #1a73e8;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgb(0 0 0 / 12%);
}

.stat-card-primary {
  border-left-color: #1a73e8;
}

.stat-card-warning {
  border-left-color: #f9ab00;
}

.stat-card-success {
  border-left-color: #137333;
}

.stat-icon {
  font-size: 2.5rem;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 2rem;
  color: #1a73e8;
  margin: 0 0 0.25rem;
  font-weight: 700;
}

.stat-label {
  color: #5f6368;
  margin: 0 0 0.5rem;
  font-weight: 500;
}

.stat-trend {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.trend-positive {
  background-color: #e6f4ea;
  color: #137333;
}

.trend-negative {
  background-color: #fce8e6;
  color: #d93025;
}

.trend-neutral {
  background-color: #f0f4f8;
  color: #5f6368;
}
</style>
