<script setup>
defineProps({
  profile: Object,
  items: Array,
  getImgUrl: Function
})
</script>

<template>
  <div class="recommend-card">
    <h2>✨ 今日推荐穿搭</h2>
    <p style="color:var(--dim);margin-bottom:16px;font-size:13px">
      基于你的风格偏好（{{ (profile.style?.primary || profile.style_preferences || []).join('/') }}）自动搭配
    </p>
    <div v-if="items.length < 2" class="empty">
      <div class="empty-icon">✨</div>衣物太少，无法生成推荐
    </div>
  </div>
</template>
