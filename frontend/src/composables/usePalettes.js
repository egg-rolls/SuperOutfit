import { ref } from 'vue'
import { api } from '../services/api'

export function usePalettes() {
  const palettes = ref([])
  const loading = ref(false)

  async function load(limit = 100) {
    loading.value = true
    try {
      palettes.value = await api.palettes(limit).catch(() => [])
    } finally {
      loading.value = false
    }
  }

  return { palettes, loading, load }
}
