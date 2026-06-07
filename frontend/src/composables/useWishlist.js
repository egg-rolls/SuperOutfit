import { ref } from 'vue'
import { api } from '../services/api'

const CM = {
  '纯白':'#f8f8f8','白色':'#f8f8f8','米白':'#f5f0e8','米白色':'#f5f0e8',
  '黑色':'#1a1a1a','炭黑':'#2a2a2a','深灰黑色':'#333','纯黑色':'#111111',
  '藏青':'#1a3a5c','藏青色':'#1a3a5c','深浅灰':'#888','灰色':'#999',
  '卡其色':'#c4a97d','卡其':'#c4a97d','复古枪黑色':'#4a4a4a'
}

export function useWishlist() {
  const items = ref([])
  const loading = ref(false)

  async function load() {
    loading.value = true
    try {
      items.value = await api.wishlist.list().catch(() => [])
    } finally {
      loading.value = false
    }
  }

  async function add(data) {
    const result = await api.wishlist.add(data)
    await load()
    return result
  }

  async function remove(id) {
    await api.wishlist.delete(id)
    items.value = items.value.filter(i => i.id !== id)
  }

  async function moveToWardrobe(item) {
    // 1. 创建到正式衣橱
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
    // 2. 从购物清单删除
    await remove(item.id)
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

  function filterItems(filter, searchText = '') {
    let result = items.value

    // 分类过滤
    if (filter !== 'all') {
      const [k, v] = filter.split(':')
      if (k === 'type') result = result.filter(i => i.type === v)
      else if (k === 'style') result = result.filter(i => (i.style || []).includes(v))
      else if (k === 'search') {
        const q = v.toLowerCase()
        result = result.filter(i =>
          (i.sub_type || '').toLowerCase().includes(q) ||
          (i.brand || '').toLowerCase().includes(q) ||
          (i.style || []).some(s => s.toLowerCase().includes(q))
        )
      }
    }

    // 搜索文本过滤
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
    items, loading, load, add, remove, moveToWardrobe,
    getImgUrl, getColor, getTypes, getStyles, filterItems
  }
}
