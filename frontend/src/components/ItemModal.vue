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
      <button class="modal-close" @click="$emit('close')">&times;</button>
      <img v-if="imgUrl" class="modal-img" :src="imgUrl" :alt="item.sub_type">
      <div v-else class="modal-img" style="display:flex;align-items:center;justify-content:center;font-size:72px;color:#ccc;background:#f0efe9">👕</div>
      <div class="modal-body">
        <h2>{{ item.colors?.primary }} {{ item.sub_type }}</h2>
        <div class="meta">{{ item.type }} · {{ item.material || '?' }} · {{ item.fit || '?' }}</div>
        <div v-if="item.colors?.primary_hex" style="margin-top:8px;font-size:12px;font-family:monospace;color:var(--dim)">
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
          <div>🌡️ {{ item.temperature_range || '?' }} ℃</div>
        </div>
        <div class="section">
          <div class="section-title">推荐搭配</div>
          <div class="pair-list">
            <span v-for="p in (item.pair_with || [])" :key="p" class="pair-item">{{ p }}</span>
            <span v-if="!item.pair_with?.length" style="color:#999">暂无</span>
          </div>
        </div>
        <div v-if="item.restrict?.length" class="section">
          <div class="section-title">搭配禁忌</div>
          <div v-for="r in item.restrict" :key="r" class="restrict">⚠️ {{ r }}</div>
        </div>
        <div class="section">
          <div class="section-title">穿着记录</div>
          <div>穿 {{ item.wear_count || 0 }} 次 · {{ item.last_worn || '未穿过' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
