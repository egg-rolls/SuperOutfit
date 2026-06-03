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

function handleDelete(filename, event) {
  event.stopPropagation()
  if (confirm(`确定要删除 ${filename} 吗？此操作不可恢复。`)) {
    emit('delete', filename)
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
      <div v-for="r in refs" :key="r.filename" class="ref-card" @click="openModal(r)">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <h3>{{ getDisplayName(r.filename) }}</h3>
          <button class="btn btn-danger" style="padding:4px 8px;font-size:12px" @click="handleDelete(r.filename, $event)">删除</button>
        </div>
        <div style="margin-top:var(--space-sm);font-size:14px;color:var(--muted);line-height:1.6">
          {{ r.content.substring(0, 100) }}{{ r.content.length > 100 ? '...' : '' }}
        </div>
      </div>
      <div v-if="!refs.length" class="empty">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        </div>
        暂无知识文档
      </div>
    </div>
    <RefModal 
      v-if="modalRef" 
      :refData="modalRef" 
      @close="closeModal" 
      @save="handleSave"
      @delete="handleDelete"
    />
  </div>
</template>
