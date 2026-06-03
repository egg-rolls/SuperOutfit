import { ref } from 'vue'
import { api } from '../services/api'

export function useProfile() {
  const profile = ref({})
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      profile.value = await api.profile.get().catch(() => ({}))
    } finally {
      loading.value = false
    }
  }

  async function update(data) {
    profile.value = await api.profile.update(data)
  }

  return { profile, loading, load, update }
}
