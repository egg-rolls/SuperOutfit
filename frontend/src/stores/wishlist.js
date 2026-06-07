import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../services/api'
import { getImgUrl, getColor, getTypes, getStyles } from '../utils/itemHelpers'
import { useWardrobeStore } from './wardrobe'

export const useWishlistStore = defineStore('wishlist', () => {
  const items = ref([])
  const loading = ref(false)

  // Getters
  const types = computed(() => getTypes(items.value))
  const styles = computed(() => getStyles(items.value))
  const total = computed(() => items.value.length)

  // Actions
  async function load() {
    loading.value = true
    try {
      items.value = await api.wishlist.list().catch(() => [])
    } finally {
      loading.value = false
    }
  }

  async function add(data) {
    await api.wishlist.add(data)
    await load()
  }

  async function remove(id) {
    await api.wishlist.delete(id)
    items.value = items.value.filter(i => i.id !== id)
  }

  async function moveToWardrobe(item) {
    // 1. Create in wardrobe
    await api.wardrobe.add({
      type: item.type,
      sub_type: item.sub_type,
      primary_color: item.colors?.primary || '',
      primary_hex: item.colors?.primary_hex || '',
      material: item.material || '',
      fit: item.fit || '',
      style: (item.style || []).join(','),
      season: (item.season || []).join(','),
      temp_range: item.temperature_range || '',
      occasion: (item.occasion || []).join(','),
      brand: item.brand || '',
      price: item.price || 0,
      image: item.image || ''
    })
    // 2. Delete from wishlist
    await remove(item.id)
    // 3. Refresh wardrobe store
    const wardrobeStore = useWardrobeStore()
    await wardrobeStore.load()
  }

  function filterItems(filter, searchText = '') {
    let result = items.value

    if (filter !== 'all') {
      const [k, v] = filter.split(':')
      if (k === 'type') result = result.filter(i => i.type === v)
      else if (k === 'style') result = result.filter(i => (i.style || []).includes(v))
      else if (k === 'tag') {
        const tag = v.toLowerCase()
        result = result.filter(i =>
          (i.sub_type || '').toLowerCase().includes(tag) ||
          (i.brand || '').toLowerCase().includes(tag) ||
          (i.style || []).some(s => s.toLowerCase().includes(tag)) ||
          (i.type || '').toLowerCase().includes(tag) ||
          (i.colors?.primary || '').toLowerCase().includes(tag)
        )
      }
    }

    if (searchText) {
      const q = searchText.toLowerCase()
      result = result.filter(i =>
        (i.sub_type || '').toLowerCase().includes(q) ||
        (i.brand || '').toLowerCase().includes(q) ||
        (i.type || '').toLowerCase().includes(q) ||
        (i.colors?.primary || '').toLowerCase().includes(q) ||
        (i.style || []).some(s => s.toLowerCase().includes(q))
      )
    }

    return result
  }

  return {
    items, loading,
    types, styles, total,
    load, add, remove, moveToWardrobe,
    getImgUrl, getColor, filterItems
  }
})
