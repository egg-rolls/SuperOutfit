<script setup>
defineProps({
  profile: Object
})
</script>

<template>
  <div class="profile-card">
    <h2>👤 个人画像</h2>
    <div class="profile-grid">
      <div class="profile-item"><div class="label">身材</div><div class="value">{{ profile.body?.height || '?' }}cm / {{ profile.body?.weight || '?' }}kg · {{ profile.body?.build || '?' }}</div></div>
      <div class="profile-item"><div class="label">肩宽</div><div class="value">{{ profile.body?.shoulder || '?' }}cm</div></div>
      <div class="profile-item"><div class="label">三围</div><div class="value">胸{{ profile.measurements?.chest || '?' }} / 腰{{ profile.measurements?.waist || '?' }} / 臀{{ profile.measurements?.hip || '?' }}</div></div>
      <div class="profile-item"><div class="label">城市</div><div class="value">{{ profile.location || profile.city || '?' }}</div></div>
      <div class="profile-item"><div class="label">职业</div><div class="value">{{ profile.lifestyle?.occupation || '?' }}</div></div>
      <div class="profile-item"><div class="label">主要风格</div><div class="value">{{ (profile.style?.primary || profile.style_preferences || []).join('、') }}</div></div>
      <div class="profile-item"><div class="label">喜爱颜色</div><div class="value">{{ (profile.colors?.love || profile.favorite_colors || []).join('、') }}</div></div>
      <div class="profile-item"><div class="label">预算（上/下/外套）</div><div class="value">¥{{ profile.budget?.top || '?' }} / ¥{{ profile.budget?.bottom || '?' }} / ¥{{ profile.budget?.outerwear || '?' }}</div></div>
    </div>
  </div>
</template>
