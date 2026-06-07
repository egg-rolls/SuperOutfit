import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../services/api'

export const useProfileStore = defineStore('profile', () => {
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
    Object.assign(profile.value, data)
    await api.profile.update(data)
  }

  return { profile, loading, load, update }
})
