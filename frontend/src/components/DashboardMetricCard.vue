<template>
  <article class="metric-card" :class="`metric-card--${accent}`">
    <div class="metric-card__icon">
      <slot name="icon">{{ iconText }}</slot>
    </div>
    <div class="metric-card__content">
      <span class="metric-card__eyebrow">{{ eyebrow }}</span>
      <strong class="metric-card__value">{{ value }}</strong>
      <p v-if="description" class="metric-card__description">{{ description }}</p>
    </div>
  </article>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  eyebrow: string
  value: string | number
  description?: string
  accent?: 'blue' | 'green' | 'orange' | 'red'
}>(), {
  accent: 'blue',
})

const iconText = props.eyebrow.slice(0, 1)
</script>
