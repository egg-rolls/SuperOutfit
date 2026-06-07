import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../services/api'

export const useRefsStore = defineStore('refs', () => {
  const refs = ref([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      // 后端返回 filename + excerpt（前 200 字符）
      const data = await api.references.list().catch(() => [])
      refs.value = data.map(r => ({
        filename: r.filename,
        excerpt: r.excerpt || '',
        has_more: r.has_more || false,
        content: '',  // 完整内容延迟加载
      }))
    } finally {
      loading.value = false
    }
  }

  async function loadContent(filename) {
    const idx = refs.value.findIndex(r => r.filename === filename)
    if (idx >= 0 && !refs.value[idx].content) {
      const data = await api.references.get(filename)
      refs.value[idx] = { ...refs.value[idx], content: data.content }
    }
  }

  async function update(filename, content) {
    await api.references.update(filename, content)
    const idx = refs.value.findIndex(r => r.filename === filename)
    if (idx >= 0) {
      refs.value[idx] = {
        ...refs.value[idx],
        content,
        excerpt: content.substring(0, 200),
        has_more: content.length > 200,
      }
    }
  }

  async function remove(filename) {
    await api.references.delete(filename)
    refs.value = refs.value.filter(r => r.filename !== filename)
  }

  return { refs, loading, load, loadContent, update, remove }
})
