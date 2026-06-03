<script setup>
defineProps({
  palettes: Array
})
</script>

<template>
  <div class="palette-grid">
    <div v-for="(p, i) in palettes" :key="i" class="palette-card">
      <div class="palette-swatches">
        <div v-for="c in p.colors" :key="c" class="swatch" :style="{ background: c }" :title="c"></div>
      </div>
      <div class="palette-info">
        <div class="palette-hex"><span v-for="c in p.colors" :key="c">{{ c }}</span></div>
        <div class="palette-meta">{{ p.source || '' }}{{ p.likes ? ' · ❤️ ' + p.likes : '' }}</div>
      </div>
    </div>
  </div>
</template>
