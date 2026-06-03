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
      <button class="modal-close" @click="$emit('close')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
      <div class="modal-body">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md)">
          <h2 style="font-size:28px">{{ refData.filename.replace('.md', '') }}</h2>
          <div style="display:flex;gap:var(--space-xs)">
            <button v-if="editMode === 'preview'" class="btn btn-secondary" @click="startEdit">编辑</button>
            <button v-if="editMode === 'edit'" class="btn btn-ghost" @click="cancelEdit">取消</button>
            <button v-if="editMode === 'edit'" class="btn btn-primary" @click="save">保存</button>
          </div>
        </div>
        <div class="ref-meta" style="margin-bottom:var(--space-md)">{{ refData.filename }} · {{ refData.content.split('\n').length }} 行</div>
        
        <div v-if="editMode === 'edit'">
          <div style="display:flex;gap:var(--space-xs);margin-bottom:var(--space-sm)">
            <span class="tag" style="background:var(--primary);color:var(--on-primary)">源代码</span>
          </div>
          <textarea v-model="editContent" style="width:100%;height:60vh;padding:var(--space-md);font-family:'JetBrains Mono',monospace;font-size:13px;border:1px solid var(--hairline);border-radius:var(--radius-md);resize:vertical;background:var(--canvas);color:var(--ink)"></textarea>
        </div>
        <div v-else>
          <div style="display:flex;gap:var(--space-xs);margin-bottom:var(--space-sm)">
            <span class="tag" style="background:var(--primary);color:var(--on-primary)">MD 预览</span>
            <button class="btn btn-ghost" @click="startEdit" style="font-size:12px">切换源代码</button>
          </div>
          <div class="markdown-body" v-html="renderMarkdown(refData.content)"></div>
        </div>
      </div>
    </div>
  </div>
</template>
