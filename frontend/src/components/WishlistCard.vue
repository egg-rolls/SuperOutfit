<script setup>
const props = defineProps({
  item: Object,
  imgUrl: String,
  color: String
})

const emit = defineEmits(['click', 'moveToWardrobe', 'remove'])

function handleMoveToWardrobe(e) {
  e.stopPropagation()
  emit('moveToWardrobe', props.item)
}

function handleRemove(e) {
  e.stopPropagation()
  emit('remove', props.item)
}
</script>

<template>
  <div class="card" @click="$emit('click', item)">
    <img v-if="imgUrl" class="card-img" :src="imgUrl" :alt="item.sub_type" loading="lazy" decoding="async">
    <div v-else class="card-img placeholder">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M20.38 3.46L16 2L12 5.69L8 2L3.62 3.46L2 8L5.69 12L2 16L3.62 20.54L8 22L12 18.31L16 22L20.38 20.54L22 16L18.31 12L22 8L20.38 3.46Z"/>
      </svg>
    </div>
    <div class="card-body">
      <div class="card-type">{{ item.type }}</div>
      <div class="card-name">{{ item.sub_type }}</div>
      <div class="card-color">
        <span class="card-color-dot" :style="{ background: color }"></span>
        {{ item.colors?.primary }}{{ item.colors?.secondary ? ' / ' + item.colors.secondary : '' }}
      </div>
      <div class="card-tags">
        <span v-for="s in (item.style || []).slice(0, 3)" :key="s" class="tag">{{ s }}</span>
      </div>
      <div class="card-meta">
        <span v-if="item.brand">{{ item.brand }}</span>
        <span v-if="item.price" class="price">¥{{ item.price }}</span>
      </div>
      <div class="card-actions">
        <button class="action-btn move-btn" @click="handleMoveToWardrobe">
          <span class="btn-icon">👕</span>
          <span>移入衣橱</span>
        </button>
        <button class="action-btn remove-btn" @click="handleRemove">
          <span class="btn-icon">✕</span>
          <span>删除</span>
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

.price {
  font-weight: 600;
  color: var(--primary);
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

.move-btn:hover {
  background: #e8f5e9;
  border-color: var(--success);
  color: var(--success);
}

.remove-btn:hover {
  background: #fce4ec;
  border-color: var(--error);
  color: var(--error);
}

.btn-icon {
  font-size: 14px;
}
</style>
