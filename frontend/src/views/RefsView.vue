<script setup>
import { ref } from 'vue'
import RefModal from '../components/RefModal.vue'

const props = defineProps({
  refs: Array
})

const emit = defineEmits(['delete', 'save'])

const modalRef = ref(null)

function openModal(r) {
  modalRef.value = r
}

function closeModal() {
  modalRef.value = null
}

function handleSave(filename, content) {
  emit('save', filename, content)
  if (modalRef.value && modalRef.value.filename === filename) {
    modalRef.value.content = content
  }
}

function handleDelete(filename) {
  if (confirm(`确定要删除 ${filename} 吗？此操作不可恢复。`)) {
    emit('delete', filename)
  }
}
</script>

<template>
  <div>
    <div class="refs-grid">
      <div v-for="r in refs" :key="r.filename" class="ref-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <h3 style="font-size:18px;margin-bottom:10px">📄 {{ r.filename.replace('.md', '') }}</h3>
          <button class="filter-btn" style="color:#c44;border-color:#c44" @click.stop="handleDelete(r.filename)">🗑️</button>
        </div>
        <div class="ref-meta">{{ r.filename }} · {{ r.content.split('\n').length }} 行</div>
        <div class="ref-summary" style="margin-top:8px;font-size:13px;color:var(--dim);line-height:1.6">
          {{ r.content.substring(0, 100) }}{{ r.content.length > 100 ? '...' : '' }}
        </div>
        <button class="filter-btn" style="margin-top:12px" @click="openModal(r)">📖 查看完整内容</button>
      </div>
      <div v-if="!refs.length" class="empty">
        <div class="empty-icon">📚</div>暂无知识文档
      </div>
    </div>
    <RefModal v-if="modalRef" :refData="modalRef" @close="closeModal" @save="handleSave" />
  </div>
</template>
