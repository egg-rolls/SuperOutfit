<script setup>
import { ref } from 'vue'
import WardrobeCard from '../components/WardrobeCard.vue'
import ItemModal from '../components/ItemModal.vue'

const props = defineProps({
  items: Array,
  getImgUrl: Function,
  getColor: Function,
  getTypes: Function,
  getStyles: Function,
  filterItems: Function
})

const filter = ref('all')
const modalItem = ref(null)

function openModal(item) {
  modalItem.value = item
}

function closeModal() {
  modalItem.value = null
}
</script>

<template>
  <div>
    <div class="filters">
      <button :class="['filter-btn', filter === 'all' && 'active']" @click="filter = 'all'">全部</button>
      <button v-for="t in getTypes()" :key="t" :class="['filter-btn', filter === 'type:'+t && 'active']" @click="filter = 'type:'+t">{{ t }}</button>
      <button v-for="s in getStyles()" :key="s" :class="['filter-btn', filter === 'style:'+s && 'active']" @click="filter = 'style:'+s">{{ s }}</button>
    </div>
    <div class="grid">
      <WardrobeCard
        v-for="(item, i) in filterItems(filter)"
        :key="item.id"
        :item="item"
        :imgUrl="getImgUrl(item)"
        :color="getColor(item)"
        :style="{ animationDelay: i * 0.05 + 's' }"
        @click="openModal"
      />
      <div v-if="!filterItems(filter).length" class="empty">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20.38 3.46L16 2L12 5.69L8 2L3.62 3.46L2 8L5.69 12L2 16L3.62 20.54L8 22L12 18.31L16 22L20.38 20.54L22 16L18.31 12L22 8L20.38 3.46Z"/>
          </svg>
        </div>
        衣橱为空
      </div>
    </div>
    <ItemModal v-if="modalItem" :item="modalItem" :imgUrl="getImgUrl(modalItem)" @close="closeModal" />
  </div>
</template>
