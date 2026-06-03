<script setup>
defineProps({
  item: Object,
  imgUrl: String,
  color: String
})

defineEmits(['click'])
</script>

<template>
  <div class="card" @click="$emit('click', item)">
    <img v-if="imgUrl" class="card-img" :src="imgUrl" :alt="item.sub_type">
    <div v-else class="card-img placeholder">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M20.38 3.46L16 2L12 5.69L8 2L3.62 3.46L2 8L5.69 12L2 16L3.62 20.54L8 22L12 18.31L16 22L20.38 20.54L22 16L18.31 12L22 8L20.38 3.46Z"/>
      </svg>
    </div>
    <div class="card-body">
      <div class="card-type">{{ item.type }} · {{ item.sub_type }}</div>
      <div class="card-name">{{ item.colors?.primary }} {{ item.sub_type }}</div>
      <div class="card-color">
        <span class="card-color-dot" :style="{ background: color }"></span>
        {{ item.colors?.primary }}{{ item.colors?.secondary ? ' / ' + item.colors.secondary : '' }}
      </div>
      <div class="card-tags">
        <span v-for="s in (item.style || []).slice(0, 3)" :key="s" class="tag">{{ s }}</span>
      </div>
      <div class="card-meta">
        <span>{{ item.temperature_range || '?' }}°C</span>
        <span>穿着 {{ item.wear_count || 0 }} 次</span>
      </div>
    </div>
  </div>
</template>
