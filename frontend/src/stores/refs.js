import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../services/api'

export const useRefsStore = defineStore('refs', () => {
  const refs = ref([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      const refList = await api.references.list().catch(() => [])
      const refDocs = await Promise.all(
        refList.map(name => api.references.get(name).catch(() => null))
      )
      refs.value = refDocs.filter(Boolean)
    } finally {
      loading.value = false
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

  return { refs, loading, load, update, remove }
})
