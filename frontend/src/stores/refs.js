import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../services/api'

export const useRefsStore = defineStore('refs', () => {
  const refs = ref([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const filenames = await api.references.list().catch(() => [])
      // 只加载文件名列表，内容延迟加载
      refs.value = filenames.map(name => ({ filename: name, content: '' }))
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
      refs.value[idx] = { ...refs.value[idx], content }
    }
  }

  async function remove(filename) {
    await api.references.delete(filename)
    refs.value = refs.value.filter(r => r.filename !== filename)
  }

  return { refs, loading, load, loadContent, update, remove }
})
