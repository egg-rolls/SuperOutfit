<script setup>
defineProps({
  profile: Object,
  stats: Object
})
</script>

<template>
  <div class="header">
    <h1>SuperOutfit</h1>
    <div class="subtitle">
      {{ profile.body?.height || '?' }}cm / {{ profile.body?.weight || '?' }}kg ·
      {{ profile.location || profile.city || '?' }} ·
      {{ profile.lifestyle?.occupation || '' }}
    </div>
    <div class="stats-bar">
      <div class="stat"><div class="stat-value">{{ stats.total || 0 }}</div><div class="stat-label">衣物</div></div>
      <div class="stat"><div class="stat-value">{{ stats.types || 0 }}</div><div class="stat-label">类别</div></div>
      <div class="stat"><div class="stat-value">{{ stats.palettes || 0 }}</div><div class="stat-label">色卡</div></div>
      <div class="stat"><div class="stat-value">{{ stats.refs || 0 }}</div><div class="stat-label">知识</div></div>
      <div class="stat"><div class="stat-value">{{ stats.favorites || 0 }}</div><div class="stat-label">收藏</div></div>
    </div>
  </div>
</template>
