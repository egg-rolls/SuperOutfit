import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../services/api'

export const usePalettesStore = defineStore('palettes', () => {
  const palettes = ref([])
  const loading = ref(false)

  async function load(limit = 20) {
    loading.value = true
    try {
      palettes.value = await api.palettes(limit).catch(() => [])
    } finally {
      loading.value = false
    }
  }

  return { palettes, loading, load }
})
