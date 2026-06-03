<script setup>
import { ref, onMounted } from 'vue'
import { marked } from 'marked'
import { api } from './services/api'

const D = ref({ profile: {}, items: [], palettes: [], refs: [], history: [] })
const loading = ref(true)
const activeTab = ref('wardrobe')
const filter = ref('all')
const modalItem = ref(null)
const modalRef = ref(null)
const editingRef = ref(null)
const editContent = ref('')
const editMode = ref('preview') // 'preview' | 'edit'

const CM = {
  '纯白':'#f8f8f8','白色':'#f8f8f8','米白':'#f5f0e8','米白色':'#f5f0e8',
  '黑色':'#1a1a1a','炭黑':'#2a2a2a','深灰黑色':'#333','纯黑色':'#111111',
  '藏青':'#1a3a5c','藏青色':'#1a3a5c','深浅灰':'#888','灰色':'#999',
  '卡其色':'#c4a97d','卡其':'#c4a97d','复古枪黑色':'#4a4a4a'
}

async function loadAll() {
  loading.value = true
  try {
    const [profile, items, stats, palettes] = await Promise.all([
      api.profile.get().catch(() => ({})),
      api.wardrobe.list().catch(() => []),
      api.wardrobe.stats().catch(() => ({})),
      api.palettes(100).catch(() => [])
    ])
    const refList = await api.references.list().catch(() => [])
    // 逐个加载知识库内容
    const refDocs = await Promise.all(
      refList.map(name => api.references.get(name).catch(() => null))
    )
    D.value = { profile, items, stats, palettes, refs: refDocs.filter(Boolean), history: [] }
  } catch (e) {
    console.error('加载失败:', e)
  } finally {
    loading.value = false
  }
}

function switchTab(tab) {
  activeTab.value = tab
}

function getImgUrl(item) {
  return item.image ? `http://localhost:8001/api/images/${item.image}` : null
}

function getColor(item) {
  return CM[item.colors?.primary] || item.colors?.primary_hex || '#ccc'
}

function getFilteredItems() {
  if (filter.value === 'all') return D.value.items
  const [k, v] = filter.value.split(':')
  if (k === 'type') return D.value.items.filter(i => i.type === v)
  if (k === 'style') return D.value.items.filter(i => (i.style || []).includes(v))
  return D.value.items
}

function getTypes() {
  return [...new Set(D.value.items.map(i => i.type))]
}

function getStyles() {
  return [...new Set(D.value.items.flatMap(i => i.style || []))].slice(0, 8)
}

function openModal(item) {
  modalItem.value = item
}

function closeModal() {
  modalItem.value = null
  modalRef.value = null
  editingRef.value = null
  editMode.value = 'preview'
}

function openRefModal(ref) {
  modalRef.value = ref
  editMode.value = 'preview'
  editingRef.value = null
}

function startEditRef() {
  editingRef.value = modalRef.value.filename
  editContent.value = modalRef.value.content
  editMode.value = 'edit'
}

function cancelEditRef() {
  editingRef.value = null
  editContent.value = ''
  editMode.value = 'preview'
}

async function saveEditRef() {
  try {
    await api.references.update(editingRef.value, editContent.value)
    // 更新本地数据
    const idx = D.value.refs.findIndex(r => r.filename === editingRef.value)
    if (idx >= 0) D.value.refs[idx].content = editContent.value
    if (modalRef.value && modalRef.value.filename === editingRef.value) {
      modalRef.value.content = editContent.value
    }
    editingRef.value = null
    editContent.value = ''
    editMode.value = 'preview'
  } catch (e) {
    alert('保存失败: ' + e.message)
  }
}

async function deleteRef(filename) {
  if (!confirm(`确定要删除 ${filename} 吗？此操作不可恢复。`)) return
  try {
    await api.references.delete(filename)
    D.value.refs = D.value.refs.filter(r => r.filename !== filename)
  } catch (e) {
    alert('删除失败: ' + e.message)
  }
}

function renderMarkdown(content) {
  return marked(content || '')
}

function getStats() {
  const items = D.value.items
  const byT = {}
  items.forEach(i => { byT[i.type] = (byT[i.type] || 0) + 1 })
  return {
    total: items.length,
    types: Object.keys(byT).length,
    palettes: D.value.palettes?.length || 0,
    refs: D.value.refs?.length || 0,
    favorites: items.filter(i => i.favorite).length
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="header">
    <h1>🧥 SuperOutfit</h1>
    <div class="subtitle">
      {{ D.profile.body?.height || '?' }}cm / {{ D.profile.body?.weight || '?' }}kg ·
      {{ D.profile.location || D.profile.city || '?' }} ·
      {{ D.profile.lifestyle?.occupation || '' }}
    </div>
    <div class="stats-bar">
      <div class="stat"><div class="stat-value">{{ getStats().total }}</div><div class="stat-label">衣物</div></div>
      <div class="stat"><div class="stat-value">{{ getStats().types }}</div><div class="stat-label">类别</div></div>
      <div class="stat"><div class="stat-value">{{ getStats().palettes }}</div><div class="stat-label">色卡</div></div>
      <div class="stat"><div class="stat-value">{{ getStats().refs }}</div><div class="stat-label">知识</div></div>
      <div class="stat"><div class="stat-value">{{ getStats().favorites }}</div><div class="stat-label">收藏</div></div>
    </div>
  </div>

  <div class="container">
    <div class="tabs">
      <button :class="['tab', activeTab === 'wardrobe' && 'active']" @click="switchTab('wardrobe')">🧥 衣橱</button>
      <button :class="['tab', activeTab === 'recommend' && 'active']" @click="switchTab('recommend')">✨ 推荐</button>
      <button :class="['tab', activeTab === 'palettes' && 'active']" @click="switchTab('palettes')">🎨 色卡库</button>
      <button :class="['tab', activeTab === 'refs' && 'active']" @click="switchTab('refs')">📚 知识库</button>
      <button :class="['tab', activeTab === 'profile' && 'active']" @click="switchTab('profile')">👤 画像</button>
    </div>

    <!-- 衣橱 -->
    <div v-show="activeTab === 'wardrobe'">
      <div class="filters">
        <button :class="['filter-btn', filter === 'all' && 'active']" @click="filter = 'all'">全部</button>
        <button v-for="t in getTypes()" :key="t" :class="['filter-btn', filter === 'type:'+t && 'active']" @click="filter = 'type:'+t">{{ t }}</button>
        <button v-for="s in getStyles()" :key="s" :class="['filter-btn', filter === 'style:'+s && 'active']" @click="filter = 'style:'+s">{{ s }}</button>
      </div>
      <div class="grid">
        <div v-for="item in getFilteredItems()" :key="item.id" class="card" @click="openModal(item)">
          <img v-if="getImgUrl(item)" class="card-img" :src="getImgUrl(item)" :alt="item.sub_type">
          <div v-else class="card-img placeholder">👕</div>
          <div class="card-body">
            <div class="card-type">{{ item.type }} · {{ item.sub_type }}</div>
            <div class="card-name">{{ item.colors?.primary }} {{ item.sub_type }}</div>
            <div class="card-color">
              <span class="card-color-dot" :style="{ background: getColor(item) }"></span>
              {{ item.colors?.primary }}{{ item.colors?.secondary ? ' / ' + item.colors.secondary : '' }}
            </div>
            <div class="card-tags">
              <span v-for="s in (item.style || []).slice(0, 3)" :key="s" class="tag">{{ s }}</span>
            </div>
            <div class="card-meta">
              <span>🌡️ {{ item.temperature_range || '?' }}</span>
              <span>穿 {{ item.wear_count || 0 }} 次</span>
            </div>
          </div>
        </div>
        <div v-if="!getFilteredItems().length" class="empty">
          <div class="empty-icon">👔</div>衣橱为空
        </div>
      </div>
    </div>

    <!-- 推荐 -->
    <div v-show="activeTab === 'recommend'" class="recommend-card">
      <h2>✨ 今日推荐穿搭</h2>
      <p style="color:var(--dim);margin-bottom:16px;font-size:13px">
        基于你的风格偏好（{{ (D.profile.style?.primary || D.profile.style_preferences || []).join('/') }}）自动搭配
      </p>
      <div v-if="D.items.length < 2" class="empty">
        <div class="empty-icon">✨</div>衣物太少，无法生成推荐
      </div>
    </div>

    <!-- 色卡库 -->
    <div v-show="activeTab === 'palettes'">
      <div class="palette-grid">
        <div v-for="(p, i) in D.palettes" :key="i" class="palette-card">
          <div class="palette-swatches">
            <div v-for="c in p.colors" :key="c" class="swatch" :style="{ background: c }" :title="c"></div>
          </div>
          <div class="palette-info">
            <div class="palette-hex"><span v-for="c in p.colors" :key="c">{{ c }}</span></div>
            <div class="palette-meta">{{ p.source || '' }}{{ p.likes ? ' · ❤️ ' + p.likes : '' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库 -->
    <div v-show="activeTab === 'refs'" class="refs-grid">
      <div v-for="r in D.refs" :key="r.filename" class="ref-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <h3 style="font-size:18px;margin-bottom:10px">📄 {{ r.filename.replace('.md', '') }}</h3>
          <button class="filter-btn" style="color:#c44;border-color:#c44" @click.stop="deleteRef(r.filename)">🗑️</button>
        </div>
        <div class="ref-meta">{{ r.filename }} · {{ r.content.split('\n').length }} 行</div>
        <div class="ref-summary" style="margin-top:8px;font-size:13px;color:var(--dim);line-height:1.6">
          {{ r.content.substring(0, 100) }}{{ r.content.length > 100 ? '...' : '' }}
        </div>
        <button class="filter-btn" style="margin-top:12px" @click="openRefModal(r)">📖 查看完整内容</button>
      </div>
      <div v-if="!D.refs.length" class="empty">
        <div class="empty-icon">📚</div>暂无知识文档
      </div>
    </div>

    <!-- 画像 -->
    <div v-show="activeTab === 'profile'" class="profile-card">
      <h2>👤 个人画像</h2>
      <div class="profile-grid">
        <div class="profile-item"><div class="label">身材</div><div class="value">{{ D.profile.body?.height || '?' }}cm / {{ D.profile.body?.weight || '?' }}kg · {{ D.profile.body?.build || '?' }}</div></div>
        <div class="profile-item"><div class="label">肩宽</div><div class="value">{{ D.profile.body?.shoulder || '?' }}cm</div></div>
        <div class="profile-item"><div class="label">三围</div><div class="value">胸{{ D.profile.measurements?.chest || '?' }} / 腰{{ D.profile.measurements?.waist || '?' }} / 臀{{ D.profile.measurements?.hip || '?' }}</div></div>
        <div class="profile-item"><div class="label">城市</div><div class="value">{{ D.profile.location || D.profile.city || '?' }}</div></div>
        <div class="profile-item"><div class="label">职业</div><div class="value">{{ D.profile.lifestyle?.occupation || '?' }}</div></div>
        <div class="profile-item"><div class="label">主要风格</div><div class="value">{{ (D.profile.style?.primary || D.profile.style_preferences || []).join('、') }}</div></div>
        <div class="profile-item"><div class="label">喜爱颜色</div><div class="value">{{ (D.profile.colors?.love || D.profile.favorite_colors || []).join('、') }}</div></div>
        <div class="profile-item"><div class="label">预算（上/下/外套）</div><div class="value">¥{{ D.profile.budget?.top || '?' }} / ¥{{ D.profile.budget?.bottom || '?' }} / ¥{{ D.profile.budget?.outerwear || '?' }}</div></div>
      </div>
    </div>
  </div>

  <!-- 知识库详情弹窗 -->
  <div v-if="modalRef" class="modal-overlay show" @click.self="closeModal">
    <div class="modal" style="max-width:900px;max-height:90vh">
      <button class="modal-close" @click="closeModal">&times;</button>
      <div class="modal-body">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h2 style="font-size:24px">📄 {{ modalRef.filename.replace('.md', '') }}</h2>
          <div style="display:flex;gap:8px">
            <button v-if="editMode === 'preview'" class="filter-btn" @click="startEditRef">✏️ 编辑</button>
            <button v-if="editMode === 'edit'" class="filter-btn" @click="cancelEditRef">取消</button>
            <button v-if="editMode === 'edit'" class="filter-btn active" @click="saveEditRef">💾 保存</button>
          </div>
        </div>
        <div class="ref-meta" style="margin-bottom:16px">{{ modalRef.filename }} · {{ modalRef.content.split('\n').length }} 行</div>
        
        <!-- 编辑模式 -->
        <div v-if="editMode === 'edit'">
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <button :class="['filter-btn', editMode === 'edit' && 'active']">源代码</button>
          </div>
          <textarea v-model="editContent" style="width:100%;height:60vh;padding:12px;font-family:monospace;font-size:13px;border:1px solid var(--border);border-radius:8px;resize:vertical"></textarea>
        </div>
        <!-- 预览模式 -->
        <div v-else>
          <div style="display:flex;gap:8px;margin-bottom:12px">
            <button class="filter-btn active">MD 预览</button>
            <button class="filter-btn" @click="startEditRef">源代码</button>
          </div>
          <div class="markdown-body" v-html="renderMarkdown(modalRef.content)"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- 衣物详情弹窗 -->
  <div v-if="modalItem" class="modal-overlay show" @click.self="closeModal">
    <div class="modal">
      <button class="modal-close" @click="closeModal">&times;</button>
      <img v-if="getImgUrl(modalItem)" class="modal-img" :src="getImgUrl(modalItem)" :alt="modalItem.sub_type">
      <div v-else class="modal-img" style="display:flex;align-items:center;justify-content:center;font-size:72px;color:#ccc;background:#f0efe9">👕</div>
      <div class="modal-body">
        <h2>{{ modalItem.colors?.primary }} {{ modalItem.sub_type }}</h2>
        <div class="meta">{{ modalItem.type }} · {{ modalItem.material || '?' }} · {{ modalItem.fit || '?' }}</div>
        <div v-if="modalItem.colors?.primary_hex" style="margin-top:8px;font-size:12px;font-family:monospace;color:var(--dim)">
          HEX: {{ modalItem.colors.primary_hex }}{{ modalItem.colors?.secondary_hex ? ' / ' + modalItem.colors.secondary_hex : '' }}
        </div>
        <div class="section">
          <div class="section-title">风格</div>
          <div class="card-tags"><span v-for="s in (modalItem.style || [])" :key="s" class="tag">{{ s }}</span></div>
        </div>
        <div class="section">
          <div class="section-title">季节 · 场合</div>
          <div class="card-tags">
            <span v-for="s in (modalItem.season || [])" :key="s" class="tag">{{ s }}</span>
            <span v-for="o in (modalItem.occasion || [])" :key="o" class="tag">{{ o }}</span>
          </div>
        </div>
        <div class="section">
          <div class="section-title">适穿温度</div>
          <div>🌡️ {{ modalItem.temperature_range || '?' }} ℃</div>
        </div>
        <div class="section">
          <div class="section-title">推荐搭配</div>
          <div class="pair-list">
            <span v-for="p in (modalItem.pair_with || [])" :key="p" class="pair-item">{{ p }}</span>
            <span v-if="!modalItem.pair_with?.length" style="color:#999">暂无</span>
          </div>
        </div>
        <div v-if="modalItem.restrict?.length" class="section">
          <div class="section-title">搭配禁忌</div>
          <div v-for="r in modalItem.restrict" :key="r" class="restrict">⚠️ {{ r }}</div>
        </div>
        <div class="section">
          <div class="section-title">穿着记录</div>
          <div>穿 {{ modalItem.wear_count || 0 }} 次 · {{ modalItem.last_worn || '未穿过' }}</div>
        </div>
      </div>
    </div>
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

/* Markdown body */
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
