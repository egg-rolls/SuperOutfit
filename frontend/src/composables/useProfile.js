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
    // 更新本地数据
    Object.assign(profile.value, data)
    // TODO: 调用 API 更新后端
  }

  return { profile, loading, load, update }
}
