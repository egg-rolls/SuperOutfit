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
    <div v-else class="card-img placeholder">👕</div>
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
        <span>🌡️ {{ item.temperature_range || '?' }}</span>
        <span>穿 {{ item.wear_count || 0 }} 次</span>
      </div>
    </div>
  </div>
</template>
