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
        v-for="item in filterItems(filter)"
        :key="item.id"
        :item="item"
        :imgUrl="getImgUrl(item)"
        :color="getColor(item)"
        @click="openModal"
      />
      <div v-if="!filterItems(filter).length" class="empty">
        <div class="empty-icon">👔</div>衣橱为空
      </div>
    </div>
    <ItemModal v-if="modalItem" :item="modalItem" :imgUrl="getImgUrl(modalItem)" @close="closeModal" />
  </div>
</template>
