<script setup>
import { ref, watch } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  refData: Object
})

const emit = defineEmits(['close', 'save'])

const editMode = ref('preview')
const editContent = ref('')

watch(() => props.refData, () => {
  editMode.value = 'preview'
  editContent.value = ''
})

function startEdit() {
  editContent.value = props.refData.content
  editMode.value = 'edit'
}

function cancelEdit() {
  editMode.value = 'preview'
  editContent.value = ''
}

function save() {
  emit('save', props.refData.filename, editContent.value)
  editMode.value = 'preview'
}

function renderMarkdown(content) {
  return marked(content || '')
}
</script>

<template>
  <div class="modal-overlay show" @click.self="$emit('close')">
    <div class="modal" style="max-width:900px;max-height:90vh">
      <button class="modal-close" @click="$emit('close')">&times;</button>
      <div class="modal-body">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h2 style="font-size:24px">📄 {{ refData.filename.replace('.md', '') }}</h2>
          <div style="display:flex;gap:8px">
            <button v-if="editMode === 'preview'" class="filter-btn" @click="startEdit">✏️ 编辑</button>
            <button v-if="editMode === 'edit'" class="filter-btn" @click="cancelEdit">取消</button>
            <button v-if="editMode === 'edit'" class="filter-btn active" @click="save">💾 保存</button>
          </div>
        </div>
        <div class="ref-meta" style="margin-bottom:16px">{{ refData.filename }} · {{ refData.content.split('\n').length }} 行</div>
        
        <div v-if="editMode === 'edit'">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <button class="filter-btn active">源代码</button>
          </div>
          <textarea v-model="editContent" style="width:100%;height:60vh;padding:12px;font-family:monospace;font-size:13px;border:1px solid var(--border);border-radius:8px;resize:vertical"></textarea>
        </div>
        <div v-else>
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <button class="filter-btn active">MD 预览</button>
            <button class="filter-btn" @click="startEdit">源代码</button>
          </div>
          <div class="markdown-body" v-html="renderMarkdown(refData.content)"></div>
        </div>
      </div>
    </div>
  </div>
</template>
