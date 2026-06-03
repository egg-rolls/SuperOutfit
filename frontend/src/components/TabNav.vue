<script setup>
defineProps({
  activeTab: String
})

defineEmits(['update:activeTab'])

const tabs = [
  { key: 'wardrobe', label: '🧥 衣橱' },
  { key: 'recommend', label: '✨ 推荐' },
  { key: 'palettes', label: '🎨 色卡库' },
  { key: 'refs', label: '📚 知识库' },
  { key: 'profile', label: '👤 画像' }
]
</script>

<template>
  <div class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      :class="['tab', activeTab === tab.key && 'active']"
      @click="$emit('update:activeTab', tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
