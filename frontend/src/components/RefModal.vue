<script setup>
import { ref, watch, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  refData: Object
})

const emit = defineEmits(['close', 'save', 'delete'])

const showEditor = ref(false)
const editContent = ref('')

watch(() => props.refData, () => {
  showEditor.value = false
  editContent.value = ''
})

function toggleEditor() {
  if (showEditor.value) {
    showEditor.value = false
    editContent.value = ''
  } else {
    editContent.value = props.refData.content
    showEditor.value = true
  }
}

function save() {
  emit('save', props.refData.filename, editContent.value)
  showEditor.value = false
}

function handleDelete() {
  emit('delete', props.refData.filename, { stopPropagation: () => {} })
}

const previewHtml = computed(() => {
  if (showEditor.value) {
    return marked(editContent.value || '')
  }
  return marked(props.refData.content || '')
})

function getDisplayName(filename) {
  return filename.replace('.md', '').replace(/[-_]/g, ' ')
}
</script>

<template>
  <div class="modal-overlay show" @click.self="$emit('close')">
    <div class="modal" :style="{ maxWidth: showEditor ? '1200px' : '800px', maxHeight: '90vh' }">
      <!-- 顶部工具栏 -->
      <div class="modal-toolbar">
        <div class="toolbar-left">
          <h2>{{ getDisplayName(refData.filename) }}</h2>
          <span class="toolbar-meta">{{ refData.filename }} · {{ refData.content.split('\n').length }} 行</span>
        </div>
        <div class="toolbar-right">
          <button class="btn btn-secondary" @click="toggleEditor">
            {{ showEditor ? '关闭编辑器' : '编辑' }}
          </button>
          <button v-if="showEditor" class="btn btn-primary" @click="save">保存</button>
          <button class="btn btn-danger" style="padding:6px 10px" @click="handleDelete">删除</button>
          <button class="btn btn-ghost" @click="$emit('close')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- 内容区域 -->
      <div class="modal-content" :class="{ 'with-editor': showEditor }">
        <!-- 编辑器（左侧） -->
        <div v-if="showEditor" class="editor-pane">
          <div class="pane-header">源代码</div>
          <textarea 
            v-model="editContent" 
            class="editor-textarea"
            placeholder="输入 Markdown 内容..."
          ></textarea>
        </div>
        
        <!-- 预览（右侧） -->
        <div class="preview-pane">
          <div class="pane-header">{{ showEditor ? '实时预览' : '内容' }}</div>
          <div class="preview-content markdown-body" v-html="previewHtml"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--hairline);
  background: var(--surface-soft);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.toolbar-left {
  display: flex;
  align-items: baseline;
  gap: var(--space-md);
}

.toolbar-left h2 {
  font-size: 22px;
  margin: 0;
}

.toolbar-meta {
  font-size: 13px;
  color: var(--muted);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.modal-content {
  display: flex;
  height: calc(90vh - 60px);
}

.modal-content.with-editor {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.editor-pane {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--hairline);
}

.pane-header {
  padding: var(--space-sm) var(--space-md);
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
  background: var(--surface-soft);
  border-bottom: 1px solid var(--hairline);
}

.editor-textarea {
  flex: 1;
  width: 100%;
  padding: var(--space-md);
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 13px;
  line-height: 1.6;
  border: none;
  resize: none;
  background: var(--canvas);
  color: var(--ink);
  outline: none;
}

.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-content {
  flex: 1;
  padding: var(--space-lg);
  overflow-y: auto;
}
</style>
