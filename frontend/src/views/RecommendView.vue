<script setup>
defineProps({
  profile: Object,
  items: Array,
  getImgUrl: Function
})
</script>

<template>
  <div class="recommend-card">
    <h2>今日推荐穿搭</h2>
    <p style="color:var(--muted);margin-bottom:var(--space-md);font-size:14px">
      基于你的风格偏好（{{ (profile.style?.primary || profile.style_preferences || []).join('/') }}）自动搭配
    </p>
    <div v-if="items.length < 2" class="empty">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
      </div>
      衣物太少，无法生成推荐
    </div>
  </div>
</template>
