<script setup>
import { ref } from 'vue'
import { useRefsStore } from '../stores/refs'
import RefModal from '../components/RefModal.vue'

const store = useRefsStore()
const modalRef = ref(null)

function openModal(r) {
  modalRef.value = r
}

function closeModal() {
  modalRef.value = null
}

function handleSave(filename, content) {
  store.update(filename, content)
  if (modalRef.value && modalRef.value.filename === filename) {
    modalRef.value.content = content
  }
}

function handleDelete(filename, event) {
  if (event && event.stopPropagation) event.stopPropagation()
  if (confirm(`确定要删除 ${filename} 吗？此操作不可恢复。`)) {
    store.remove(filename)
    if (modalRef.value && modalRef.value.filename === filename) {
      closeModal()
    }
  }
}

function getDisplayName(filename) {
  return filename.replace('.md', '').replace(/[-_]/g, ' ')
}
</script>

<template>
  <div>
    <div class="refs-grid">
      <div v-for="r in store.refs" :key="r.filename" class="ref-card" @click="openModal(r)">
        <h3>{{ getDisplayName(r.filename) }}</h3>
        <div style="margin-top:var(--space-sm);font-size:14px;color:var(--muted);line-height:1.6">
          {{ r.content.substring(0, 100) }}{{ r.content.length > 100 ? '...' : '' }}
        </div>
      </div>
      <div v-if="!store.refs.length" class="empty">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        </div>
        暂无知识文档
      </div>
    </div>
    <RefModal v-if="modalRef" :refData="modalRef" @close="closeModal" @save="handleSave" @delete="handleDelete" />
  </div>
</template>
