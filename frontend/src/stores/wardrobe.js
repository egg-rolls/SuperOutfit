import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../services/api'
import { getImgUrl, getColor, getTypes, getStyles } from '../utils/itemHelpers'

export const useWardrobeStore = defineStore('wardrobe', () => {
  const items = ref([])
  const stats = ref({})
  const loading = ref(false)

  // Getters
  const types = computed(() => getTypes(items.value))
  const styles = computed(() => getStyles(items.value))
  const total = computed(() => items.value.length)
  const favorites = computed(() => items.value.filter(i => i.favorite).length)

  // Actions
  async function load() {
    loading.value = true
    try {
      const [itemsData, statsData] = await Promise.all([
        api.wardrobe.list().catch(() => []),
        api.wardrobe.stats().catch(() => ({}))
      ])
      items.value = itemsData
      stats.value = statsData
    } finally {
      loading.value = false
    }
  }

  async function update(id, data) {
    const idx = items.value.findIndex(i => i.id === id)
    if (idx >= 0) {
      Object.assign(items.value[idx], data)
    }
    await api.wardrobe.update(id, data)
  }

  async function remove(id) {
    await api.wardrobe.delete(id)
    items.value = items.value.filter(i => i.id !== id)
  }

  async function recordWear(id) {
    await api.wear.add(id)
    // 局部更新，不全量 reload
    const idx = items.value.findIndex(i => i.id === id)
    if (idx >= 0) {
      items.value[idx].wear_count = (items.value[idx].wear_count || 0) + 1
      items.value[idx].last_worn = new Date().toISOString().split('T')[0]
      items.value[idx].needs_wash = true
    }
  }

  async function markWash(id) {
    await api.wear.wash(id)
    // 局部更新
    const idx = items.value.findIndex(i => i.id === id)
    if (idx >= 0) {
      items.value[idx].needs_wash = false
    }
  }

  function filterItems(filter) {
    if (filter === 'all') return items.value
    const [k, v] = filter.split(':')
    if (k === 'type') return items.value.filter(i => i.type === v)
    if (k === 'style') return items.value.filter(i => (i.style || []).includes(v))
    return items.value
  }

  return {
    items, stats, loading,
    types, styles, total, favorites,
    load, update, remove, recordWear, markWash,
    getImgUrl, getColor, filterItems
  }
})
