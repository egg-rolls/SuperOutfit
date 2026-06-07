<script setup>
import { ref, computed } from 'vue'
import { useWardrobeStore } from '../stores/wardrobe'
import WardrobeCard from '../components/WardrobeCard.vue'
import ItemModal from '../components/ItemModal.vue'

const store = useWardrobeStore()

const filter = ref('all')
const searchText = ref('')
const showSearch = ref(false)
const showAddTag = ref(false)
const newTagText = ref('')
const modalItem = ref(null)

// Custom tags (persisted to localStorage)
const STORAGE_KEY = 'superoutfit_custom_tags'
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

function setFilter(val) {
  filter.value = val
}

function toggleSearch() {
  showSearch.value = !showSearch.value
  if (!showSearch.value) searchText.value = ''
}

// Category mapping
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

// Filter logic
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

function openModal(item) {
  modalItem.value = { ...item }
}

function closeModal() {
  modalItem.value = null
}

function handleSave(itemData) {
  store.update(itemData.id, itemData)
  closeModal()
}
</script>

<template>
  <div>
    <!-- Filter bar -->
    <div class="filter-bar">
      <div class="filter-left">
        <button :class="['filter-btn', filter === 'all' && 'active']" @click="setFilter('all')">全部</button>
        <button :class="['filter-btn', filter === '上衣' && 'active']" @click="setFilter('上衣')">上衣</button>
        <button :class="['filter-btn', filter === '下装' && 'active']" @click="setFilter('下装')">下装</button>
        <button :class="['filter-btn', filter === '配饰' && 'active']" @click="setFilter('配饰')">配饰</button>

        <button
          v-for="tag in customTags"
          :key="tag"
          :class="['filter-btn', 'custom-tag', filter === 'tag:'+tag && 'active']"
          @click="setFilter('tag:'+tag)"
        >
          {{ tag }}
          <span class="tag-remove" @click.stop="removeCustomTag(tag)">×</span>
        </button>

        <button v-if="!showAddTag" class="filter-btn add-tag-btn" @click="showAddTag = true">+</button>
        <div v-else class="add-tag-input">
          <input
            v-model="newTagText"
            placeholder="标签名"
            maxlength="10"
            @keyup.enter="addCustomTag"
            @blur="addCustomTag"
            autofocus
          />
        </div>
      </div>

      <div class="filter-right">
        <div v-if="showSearch" class="search-box">
          <input
            v-model="searchText"
            placeholder="搜索名称、品牌、风格..."
            @keyup.escape="toggleSearch"
            autofocus
          />
        </div>
        <button :class="['filter-btn', 'search-btn', showSearch && 'active']" @click="toggleSearch">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Card grid -->
    <div class="grid">
      <WardrobeCard
        v-for="item in filteredItems"
        :key="item.id"
        :item="item"
        :imgUrl="store.getImgUrl(item)"
        :color="store.getColor(item)"
        @click="openModal"
        @recordWear="store.recordWear($event.id)"
        @markWash="store.markWash($event.id)"
      />
      <div v-if="!filteredItems.length" class="empty">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20.38 3.46L16 2L12 5.69L8 2L3.62 3.46L2 8L5.69 12L2 16L3.62 20.54L8 22L12 18.31L16 22L20.38 20.54L22 16L18.31 12L22 8L20.38 3.46Z"/>
          </svg>
        </div>
        衣橱为空
      </div>
    </div>

    <ItemModal
      v-if="modalItem"
      :item="modalItem"
      :imgUrl="store.getImgUrl(modalItem)"
      @close="closeModal"
      @save="handleSave"
    />
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xs);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: var(--space-xxs);
  flex-wrap: wrap;
  flex: 1;
}

.filter-right {
  display: flex;
  align-items: center;
  gap: var(--space-xxs);
}

.filter-btn {
  padding: var(--space-xs) var(--space-md);
  border: 1px solid var(--hairline);
  background: var(--canvas);
  border-radius: var(--radius-pill);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--body);
  transition: all 0.15s ease;
  white-space: nowrap;
}

.filter-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.filter-btn.active {
  background: var(--primary);
  color: var(--on-primary);
  border-color: var(--primary);
}

.custom-tag {
  position: relative;
  padding-right: 28px;
}

.tag-remove {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  line-height: 1;
  opacity: 0.5;
  cursor: pointer;
}

.tag-remove:hover {
  opacity: 1;
}

.add-tag-btn {
  min-width: 32px;
  padding: var(--space-xs) 10px;
  font-size: 16px;
  font-weight: 400;
  color: var(--muted);
  border-style: dashed;
}

.add-tag-input input {
  width: 80px;
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--primary);
  border-radius: var(--radius-pill);
  font-size: 13px;
  outline: none;
  background: var(--canvas);
  color: var(--ink);
}

.search-btn {
  min-width: 36px;
  padding: var(--space-xs) 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-box input {
  width: 180px;
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--primary);
  border-radius: var(--radius-pill);
  font-size: 13px;
  outline: none;
  background: var(--canvas);
  color: var(--ink);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; width: 0; }
  to { opacity: 1; width: 180px; }
}
</style>
