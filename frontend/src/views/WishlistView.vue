<script setup>
import { ref, computed } from 'vue'
import { useWishlistStore } from '../stores/wishlist'
import WishlistCard from '../components/WishlistCard.vue'

const store = useWishlistStore()

const filter = ref('all')
const searchText = ref('')
const showSearch = ref(false)
const showAddTag = ref(false)
const newTagText = ref('')

const STORAGE_KEY = 'superoutfit_wishlist_tags'
const customTags = ref(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'))

function saveCustomTags() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(customTags.value))
}

function addCustomTag() {
  const text = newTagText.value.trim()
  if (text && !customTags.value.includes(text)) {
    customTags.value.push(text)
    saveCustomTags()
  }
  newTagText.value = ''
  showAddTag.value = false
}

function removeCustomTag(tag) {
  customTags.value = customTags.value.filter(t => t !== tag)
  saveCustomTags()
  if (filter.value === 'tag:' + tag) filter.value = 'all'
}

function setFilter(val) { filter.value = val }
function toggleSearch() {
  showSearch.value = !showSearch.value
  if (!showSearch.value) searchText.value = ''
}

const CATEGORY_MAP = {
  '上衣': ['上衣'],
  '下装': ['下装', '裤', '裙', '裤子'],
}
function getCategory(item) {
  for (const [cat, types] of Object.entries(CATEGORY_MAP)) {
    if (types.some(t => (item.type || '').includes(t))) return cat
  }
  return '配饰'
}

const filteredItems = computed(() => {
  let result = store.items
  if (filter.value === '上衣' || filter.value === '下装' || filter.value === '配饰') {
    result = result.filter(i => getCategory(i) === filter.value)
  } else if (filter.value.startsWith('tag:')) {
    const tag = filter.value.slice(4).toLowerCase()
    result = result.filter(i =>
      (i.sub_type || '').toLowerCase().includes(tag) ||
      (i.brand || '').toLowerCase().includes(tag) ||
      (i.style || []).some(s => s.toLowerCase().includes(tag)) ||
      (i.type || '').toLowerCase().includes(tag) ||
      (i.colors?.primary || '').toLowerCase().includes(tag)
    )
  }
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    result = result.filter(i =>
      (i.sub_type || '').toLowerCase().includes(q) ||
      (i.brand || '').toLowerCase().includes(q) ||
      (i.type || '').toLowerCase().includes(q) ||
      (i.colors?.primary || '').toLowerCase().includes(q) ||
      (i.style || []).some(s => s.toLowerCase().includes(q))
    )
  }
  return result
})
</script>

<template>
  <div>
    <div class="filter-bar">
      <div class="filter-left">
        <button :class="['filter-btn', filter === 'all' && 'active']" @click="setFilter('all')">全部</button>
        <button :class="['filter-btn', filter === '上衣' && 'active']" @click="setFilter('上衣')">上衣</button>
        <button :class="['filter-btn', filter === '下装' && 'active']" @click="setFilter('下装')">下装</button>
        <button :class="['filter-btn', filter === '配饰' && 'active']" @click="setFilter('配饰')">配饰</button>
        <button v-for="tag in customTags" :key="tag" :class="['filter-btn', 'custom-tag', filter === 'tag:'+tag && 'active']" @click="setFilter('tag:'+tag)">
          {{ tag }}
          <span class="tag-remove" @click.stop="removeCustomTag(tag)">×</span>
        </button>
        <button v-if="!showAddTag" class="filter-btn add-tag-btn" @click="showAddTag = true">+</button>
        <div v-else class="add-tag-input">
          <input v-model="newTagText" placeholder="标签名" maxlength="10" @keyup.enter="addCustomTag" @blur="addCustomTag" autofocus />
        </div>
      </div>
      <div class="filter-right">
        <div v-if="showSearch" class="search-box">
          <input v-model="searchText" placeholder="搜索名称、品牌、风格..." @keyup.escape="toggleSearch" autofocus />
        </div>
        <button :class="['filter-btn', 'search-btn', showSearch && 'active']" @click="toggleSearch">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </button>
      </div>
    </div>

    <div class="grid">
      <WishlistCard
        v-for="item in filteredItems"
        :key="item.id"
        :item="item"
        :imgUrl="store.getImgUrl(item)"
        :color="store.getColor(item)"
        @moveToWardrobe="store.moveToWardrobe($event)"
        @remove="store.remove($event.id)"
      />
      <div v-if="!filteredItems.length" class="empty">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M6 2L3 6V20C3 20.5304 3.21071 21.0391 3.58579 21.4142C3.96086 21.7893 4.46957 22 5 22H19C19.5304 22 20.0391 21.7893 20.4142 21.4142C20.7893 21.0391 21 20.5304 21 20V6L18 2H6Z"/>
            <path d="M3 6H21"/>
            <path d="M16 10C16 11.0609 15.5786 12.0783 14.8284 12.8284C14.0783 13.5786 13.0609 14 12 14C10.9391 14 9.92172 13.5786 9.17157 12.8284C8.42143 12.0783 8 11.0609 8 10"/>
          </svg>
        </div>
        购物清单为空
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-bar { display: flex; align-items: center; justify-content: space-between; gap: var(--space-xs); margin-bottom: var(--space-lg); flex-wrap: wrap; }
.filter-left { display: flex; align-items: center; gap: var(--space-xxs); flex-wrap: wrap; flex: 1; }
.filter-right { display: flex; align-items: center; gap: var(--space-xxs); }
.filter-btn { padding: var(--space-xs) var(--space-md); border: 1px solid var(--hairline); background: var(--canvas); border-radius: var(--radius-pill); cursor: pointer; font-size: 13px; font-weight: 500; color: var(--body); transition: all 0.15s ease; white-space: nowrap; }
.filter-btn:hover { border-color: var(--primary); color: var(--primary); }
.filter-btn.active { background: var(--primary); color: var(--on-primary); border-color: var(--primary); }
.custom-tag { position: relative; padding-right: 28px; }
.tag-remove { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 14px; line-height: 1; opacity: 0.5; cursor: pointer; }
.tag-remove:hover { opacity: 1; }
.add-tag-btn { min-width: 32px; padding: var(--space-xs) 10px; font-size: 16px; font-weight: 400; color: var(--muted); border-style: dashed; }
.add-tag-input input { width: 80px; padding: var(--space-xs) var(--space-sm); border: 1px solid var(--primary); border-radius: var(--radius-pill); font-size: 13px; outline: none; background: var(--canvas); color: var(--ink); }
.search-btn { min-width: 36px; padding: var(--space-xs) 10px; display: flex; align-items: center; justify-content: center; }
.search-box input { width: 180px; padding: var(--space-xs) var(--space-sm); border: 1px solid var(--primary); border-radius: var(--radius-pill); font-size: 13px; outline: none; background: var(--canvas); color: var(--ink); animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; width: 0; } to { opacity: 1; width: 180px; } }
</style>
