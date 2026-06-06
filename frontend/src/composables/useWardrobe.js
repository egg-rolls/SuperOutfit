import { ref } from 'vue'
import { api } from '../services/api'

const CM = {
  '纯白':'#f8f8f8','白色':'#f8f8f8','米白':'#f5f0e8','米白色':'#f5f0e8',
  '黑色':'#1a1a1a','炭黑':'#2a2a2a','深灰黑色':'#333','纯黑色':'#111111',
  '藏青':'#1a3a5c','藏青色':'#1a3a5c','深浅灰':'#888','灰色':'#999',
  '卡其色':'#c4a97d','卡其':'#c4a97d','复古枪黑色':'#4a4a4a'
}

export function useWardrobe() {
  const items = ref([])
  const stats = ref({})
  const loading = ref(false)

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
    // 更新本地数据
    const idx = items.value.findIndex(i => i.id === id)
    if (idx >= 0) {
      Object.assign(items.value[idx], data)
    }
    // TODO: 调用 API 更新后端
  }

  async function remove(id) {
    await api.wardrobe.delete(id)
    items.value = items.value.filter(i => i.id !== id)
  }

  async function recordWear(id) {
    const result = await api.wear.add(id)
    // 重新加载后端数据，获取 needs_wash 等计算字段
    await load()
    return result
  }

  async function markWash(id) {
    const result = await api.wear.wash(id)
    // 重新加载后端数据，获取 needs_wash 等计算字段
    await load()
    return result
  }

  function getImgUrl(item) {
    return item.image ? `/images/${item.image}` : null
  }

  function getColor(item) {
    return CM[item.colors?.primary] || item.colors?.primary_hex || '#ccc'
  }

  function getTypes() {
    return [...new Set(items.value.map(i => i.type))]
  }

  function getStyles() {
    return [...new Set(items.value.flatMap(i => i.style || []))].slice(0, 8)
  }

  function filterItems(filter) {
    if (filter === 'all') return items.value
    const [k, v] = filter.split(':')
    if (k === 'type') return items.value.filter(i => i.type === v)
    if (k === 'style') return items.value.filter(i => (i.style || []).includes(v))
    return items.value
  }

  return { items, stats, loading, load, update, remove, recordWear, markWash, getImgUrl, getColor, getTypes, getStyles, filterItems }
}
