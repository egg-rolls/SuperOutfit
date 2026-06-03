<script setup>
defineProps({
  item: Object,
  imgUrl: String
})

defineEmits(['close'])
</script>

<template>
  <div class="modal-overlay show" @click.self="$emit('close')">
    <div class="modal">
      <button class="modal-close" @click="$emit('close')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
      <img v-if="imgUrl" class="modal-img" :src="imgUrl" :alt="item.sub_type">
      <div v-else class="modal-img" style="display:flex;align-items:center;justify-content:center;color:var(--hairline);background:var(--surface-soft)">
        <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M20.38 3.46L16 2L12 5.69L8 2L3.62 3.46L2 8L5.69 12L2 16L3.62 20.54L8 22L12 18.31L16 22L20.38 20.54L22 16L18.31 12L22 8L20.38 3.46Z"/>
        </svg>
      </div>
      <div class="modal-body">
        <h2>{{ item.colors?.primary }} {{ item.sub_type }}</h2>
        <div class="meta">{{ item.type }} · {{ item.material || '?' }} · {{ item.fit || '?' }}</div>
        <div v-if="item.colors?.primary_hex" style="margin-top:8px;font-size:13px;font-family:monospace;color:var(--muted)">
          HEX: {{ item.colors.primary_hex }}{{ item.colors?.secondary_hex ? ' / ' + item.colors.secondary_hex : '' }}
        </div>
        <div class="section">
          <div class="section-title">风格</div>
          <div class="card-tags"><span v-for="s in (item.style || [])" :key="s" class="tag">{{ s }}</span></div>
        </div>
        <div class="section">
          <div class="section-title">季节 · 场合</div>
          <div class="card-tags">
            <span v-for="s in (item.season || [])" :key="s" class="tag">{{ s }}</span>
            <span v-for="o in (item.occasion || [])" :key="o" class="tag">{{ o }}</span>
          </div>
        </div>
        <div class="section">
          <div class="section-title">适穿温度</div>
          <div>{{ item.temperature_range || '?' }}°C</div>
        </div>
        <div class="section">
          <div class="section-title">推荐搭配</div>
          <div class="pair-list">
            <span v-for="p in (item.pair_with || [])" :key="p" class="pair-item">{{ p }}</span>
            <span v-if="!item.pair_with?.length" style="color:var(--muted)">暂无</span>
          </div>
        </div>
        <div v-if="item.restrict?.length" class="section">
          <div class="section-title">搭配禁忌</div>
          <div v-for="r in item.restrict" :key="r" class="restrict">{{ r }}</div>
        </div>
        <div class="section">
          <div class="section-title">穿着记录</div>
          <div>穿着 {{ item.wear_count || 0 }} 次 · {{ item.last_worn || '未穿过' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
