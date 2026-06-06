<script setup>
const props = defineProps({
  item: Object,
  imgUrl: String,
  color: String
})

const emit = defineEmits(['click', 'recordWear', 'markWash'])

function handleRecordWear(e) {
  e.stopPropagation()
  emit('recordWear', props.item)
}

function handleMarkWash(e) {
  e.stopPropagation()
  emit('markWash', props.item)
}
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
        <span>
          <span class="season-icon">🌡</span>
          {{ item.temperature_range || '?' }}°C
        </span>
        <span>
          <span class="wear-icon">👕</span>
          穿过 {{ item.wear_count || 0 }} 次
        </span>
      </div>
      <div v-if="item.needs_wash" class="wash-alert">
        <span class="wash-icon">⚠️</span>
        <span>需清洗 (已穿{{ (item.wear_count || 0) - (item.wash_count || 0) }}次)</span>
      </div>
      <div class="card-actions">
        <button class="action-btn wear-btn" @click="handleRecordWear">
          <span class="btn-icon">👟</span>
          <span>记录穿着</span>
        </button>
        <button 
          class="action-btn wash-btn" 
          :class="{ 'wash-needed': item.needs_wash }"
          @click="handleMarkWash"
        >
          <span class="btn-icon">🧺</span>
          <span>标记清洗</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-meta {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-sm);
  font-size: 12px;
  color: var(--muted-soft);
}

.card-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.season-icon,
.wear-icon {
  font-size: 14px;
}

.wash-alert {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: var(--space-xs);
  padding: 6px 10px;
  background: #fff3cd;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: #856404;
}

.wash-icon {
  font-size: 14px;
}

.card-actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--hairline-soft);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  border: 1px solid var(--hairline);
  border-radius: var(--radius-md);
  background: var(--canvas);
  color: var(--body);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--surface-soft);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-icon {
  font-size: 14px;
}

.wash-needed {
  border-color: #ffc107;
  background: #fff8e1;
}

.wash-needed:hover {
  background: #ffecb3;
  border-color: #ff9800;
}
</style>
