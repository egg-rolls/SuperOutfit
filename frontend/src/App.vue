<script setup>
import { ref, onMounted, computed } from 'vue'
import { useWardrobe } from './composables/useWardrobe'
import { useProfile } from './composables/useProfile'
import { usePalettes } from './composables/usePalettes'
import { useRefs } from './composables/useRefs'
import AppHeader from './components/AppHeader.vue'
import TabNav from './components/TabNav.vue'
import WardrobeView from './views/WardrobeView.vue'
import PalettesView from './views/PalettesView.vue'
import RefsView from './views/RefsView.vue'
import ProfileView from './views/ProfileView.vue'
import RecommendView from './views/RecommendView.vue'

const activeTab = ref('wardrobe')

const { items, stats, loading: wardrobeLoading, load: loadWardrobe, getImgUrl, getColor, getTypes, getStyles, filterItems } = useWardrobe()
const { profile, load: loadProfile } = useProfile()
const { palettes, load: loadPalettes } = usePalettes()
const { refs, load: loadRefs, update: updateRef, remove: removeRef } = useRefs()

const computedStats = computed(() => ({
  total: items.value.length,
  types: getTypes().length,
  palettes: palettes.value.length,
  refs: refs.value.length,
  favorites: items.value.filter(i => i.favorite).length
}))

async function loadAll() {
  await Promise.all([
    loadWardrobe(),
    loadProfile(),
    loadPalettes(),
    loadRefs()
  ])
}

function handleDeleteRef(filename) {
  removeRef(filename)
}

function handleSaveRef(filename, content) {
  updateRef(filename, content)
}

onMounted(loadAll)
</script>

<template>
  <AppHeader :profile="profile" :stats="computedStats" />
  
  <div class="container">
    <TabNav v-model:activeTab="activeTab" />
    
    <WardrobeView
      v-show="activeTab === 'wardrobe'"
      :items="items"
      :getImgUrl="getImgUrl"
      :getColor="getColor"
      :getTypes="getTypes"
      :getStyles="getStyles"
      :filterItems="filterItems"
    />
    
    <RecommendView
      v-show="activeTab === 'recommend'"
      :profile="profile"
      :items="items"
      :getImgUrl="getImgUrl"
    />
    
    <PalettesView
      v-show="activeTab === 'palettes'"
      :palettes="palettes"
    />
    
    <RefsView
      v-show="activeTab === 'refs'"
      :refs="refs"
      @delete="handleDeleteRef"
      @save="handleSaveRef"
    />
    
    <ProfileView
      v-show="activeTab === 'profile'"
      :profile="profile"
    />
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #f5f5f0; --card: #fff; --text: #1a1a1a; --dim: #666;
  --accent: #2d5a27; --accent-light: #e8f0e6; --border: #e0ddd8;
  --shadow: 0 2px 8px rgba(0,0,0,.06); --radius: 12px;
}
body {
  font-family: -apple-system, "SF Pro SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
}
.header { background: linear-gradient(135deg, #2d3a2e, #3d4a3e); color: #fff; padding: 32px 40px; }
.header h1 { font-size: 28px; font-weight: 700; letter-spacing: -.5px; }
.header .subtitle { color: rgba(255,255,255,.7); font-size: 14px; margin-top: 4px; }
.header .stats-bar { display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap; }
.header .stat { background: rgba(255,255,255,.12); padding: 8px 16px; border-radius: 8px; }
.header .stat-value { font-size: 20px; font-weight: 700; }
.header .stat-label { font-size: 11px; opacity: .7; text-transform: uppercase; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px 20px; }
.tabs { display: flex; gap: 4px; margin-bottom: 24px; background: var(--card); padding: 4px; border-radius: var(--radius); box-shadow: var(--shadow); flex-wrap: wrap; }
.tab { padding: 10px 16px; border: none; background: none; cursor: pointer; border-radius: 8px; font-size: 13px; font-weight: 500; color: var(--dim); transition: .2s; }
.tab:hover { background: var(--accent-light); color: var(--accent); }
.tab.active { background: var(--accent); color: #fff; }
.filters { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-btn { padding: 6px 14px; border: 1px solid var(--border); background: var(--card); border-radius: 20px; cursor: pointer; font-size: 12px; transition: .2s; }
.filter-btn:hover, .filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.card { background: var(--card); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); transition: transform .2s, box-shadow .2s; cursor: pointer; }
.card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.1); }
.card-img { width: 100%; aspect-ratio: 3/4; object-fit: cover; background: #f0efe9; }
.card-img.placeholder { display: flex; align-items: center; justify-content: center; font-size: 48px; color: var(--border); }
.card-body { padding: 14px; }
.card-type { font-size: 11px; color: var(--dim); text-transform: uppercase; letter-spacing: .5px; }
.card-name { font-size: 15px; font-weight: 600; margin-top: 2px; }
.card-color { display: flex; align-items: center; gap: 6px; margin-top: 6px; font-size: 12px; color: var(--dim); }
.card-color-dot { width: 14px; height: 14px; border-radius: 50%; border: 1px solid var(--border); }
.card-tags { display: flex; gap: 4px; margin-top: 8px; flex-wrap: wrap; }
.tag { padding: 2px 8px; background: var(--accent-light); color: var(--accent); border-radius: 10px; font-size: 11px; }
.card-meta { display: flex; justify-content: space-between; margin-top: 8px; font-size: 11px; color: var(--dim); }
.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
.modal-overlay.show { display: flex; }
.modal { background: var(--card); border-radius: 16px; max-width: 600px; width: 100%; max-height: 85vh; overflow-y: auto; position: relative; }
.modal-img { width: 100%; aspect-ratio: 4/5; object-fit: cover; background: #f0efe9; }
.modal-close { position: absolute; top: 12px; right: 12px; width: 36px; height: 36px; border-radius: 50%; background: rgba(0,0,0,.5); color: #fff; border: none; cursor: pointer; font-size: 18px; z-index: 10; }
.modal-body { padding: 24px; }
.modal-body h2 { font-size: 22px; margin-bottom: 4px; }
.modal-body .meta { color: var(--dim); font-size: 13px; margin-bottom: 16px; }
.modal-body .section { margin-bottom: 16px; }
.modal-body .section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--dim); letter-spacing: .5px; margin-bottom: 6px; }
.modal-body .pair-list { display: flex; gap: 6px; flex-wrap: wrap; }
.modal-body .pair-item { padding: 4px 10px; background: #f5f5f0; border-radius: 6px; font-size: 12px; }
.modal-body .restrict { color: #c44; font-size: 12px; }
.profile-card { background: var(--card); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow); }
.profile-card h2 { font-size: 20px; margin-bottom: 16px; }
.profile-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.profile-item { padding: 12px; background: var(--bg); border-radius: 8px; }
.profile-item .label { font-size: 11px; color: var(--dim); text-transform: uppercase; }
.profile-item .value { font-size: 15px; font-weight: 500; margin-top: 2px; }
.recommend-card { background: var(--card); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow); margin-bottom: 24px; }
.recommend-card h2 { font-size: 20px; margin-bottom: 12px; }
.palette-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.palette-card { background: var(--card); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow); transition: transform .2s; }
.palette-card:hover { transform: translateY(-2px); }
.palette-swatches { display: flex; height: 60px; }
.palette-swatches .swatch { flex: 1; }
.palette-info { padding: 10px 12px; }
.palette-meta { font-size: 11px; color: var(--dim); margin-top: 2px; }
.palette-hex { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
.palette-hex span { font-size: 10px; padding: 2px 6px; background: var(--bg); border-radius: 4px; font-family: monospace; }
.refs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 16px; }
.ref-card { background: var(--card); border-radius: var(--radius); padding: 20px; box-shadow: var(--shadow); transition: transform .2s; cursor: pointer; }
.ref-card:hover { transform: translateY(-2px); }
.ref-card h3 { font-size: 16px; margin-bottom: 8px; color: var(--accent); }
.ref-card .ref-meta { font-size: 11px; color: var(--dim); margin-bottom: 8px; }
.empty { text-align: center; padding: 60px 20px; color: var(--dim); }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.markdown-body { line-height: 1.8; font-size: 14px; }
.markdown-body h1, .markdown-body h2, .markdown-body h3 { margin: 20px 0 10px; font-weight: 600; }
.markdown-body h1 { font-size: 22px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.markdown-body h2 { font-size: 18px; }
.markdown-body h3 { font-size: 16px; }
.markdown-body p { margin: 8px 0; }
.markdown-body ul, .markdown-body ol { padding-left: 24px; margin: 8px 0; }
.markdown-body li { margin: 4px 0; }
.markdown-body code { background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 13px; font-family: monospace; }
.markdown-body pre { background: #1a1a1a; color: #f0f0f0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; }
.markdown-body pre code { background: none; color: inherit; padding: 0; }
.markdown-body blockquote { border-left: 4px solid var(--accent); padding-left: 16px; color: var(--dim); margin: 12px 0; }
.markdown-body table { border-collapse: collapse; width: 100%; margin: 12px 0; }
.markdown-body th, .markdown-body td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
.markdown-body th { background: var(--bg); font-weight: 600; }
.markdown-body strong { font-weight: 600; }
.markdown-body a { color: var(--accent); text-decoration: underline; }
@media(max-width: 600px) {
  .header { padding: 20px; }
  .header h1 { font-size: 22px; }
  .grid, .palette-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .refs-grid { grid-template-columns: 1fr; }
  .card-body { padding: 10px; }
  .card-name { font-size: 13px; }
}
</style>
