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

const { items, stats, loading: wardrobeLoading, load: loadWardrobe, getImgUrl, getColor, getTypes, getStyles, filterItems, update: updateWardrobeItem } = useWardrobe()
const { profile, load: loadProfile, update: updateProfile } = useProfile()
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

function handleUpdateItem(itemData) {
  updateWardrobeItem(itemData.id, itemData)
}

function handleSaveProfile(data) {
  updateProfile(data)
}

function applyTheme(theme) {
  const root = document.documentElement.style
  
  // 核心 4 色
  root.setProperty('--user-accent', theme.accent)
  root.setProperty('--canvas', theme.canvas)
  root.setProperty('--dark', theme.dark)
  root.setProperty('--user-muted', theme.muted)
  
  // 派生：深色系（基于 dark）
  root.setProperty('--surface-dark', theme.dark)
  root.setProperty('--surface-dark-elevated', theme.darkElevated)
  root.setProperty('--surface-dark-soft', theme.darkSoft)
  
  // 派生：浅色系（基于 canvas）
  root.setProperty('--surface-soft', theme.surfaceSoft)
  root.setProperty('--surface-card', theme.surface)
  root.setProperty('--surface-cream-strong', theme.creamStrong)
  root.setProperty('--hairline', theme.hairline)
  root.setProperty('--hairline-soft', theme.hairlineSoft)
  
  // 派生：文字色（确保对比度）
  root.setProperty('--ink', theme.ink)
  root.setProperty('--body', theme.body)
  root.setProperty('--body-strong', theme.bodyStrong)
  root.setProperty('--muted', theme.muted)
  root.setProperty('--muted-soft', theme.mutedSoft)
  
  // 派生：交互色
  root.setProperty('--primary', theme.accent)
  root.setProperty('--primary-active', theme.accentActive)
  root.setProperty('--primary-disabled', theme.accentDisabled)
  root.setProperty('--on-primary', theme.onPrimary)
  root.setProperty('--on-dark', theme.onDark)
  root.setProperty('--on-dark-soft', theme.onDarkSoft)
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
      :updateItem="handleUpdateItem"
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
      @applyTheme="applyTheme"
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
      @save="handleSaveProfile"
    />
  </div>
</template>

<style>
/* ===== Design System: Claude-inspired ===== */

/* 4 个可配置颜色 - 可与色卡系统联动 */
:root {
  --user-accent: #cc785c;      /* 主色调：coral */
  --user-surface: #efe9de;     /* 卡片背景：cream card */
  --user-dark: #181715;        /* 深色表面：dark navy */
  --user-muted: #6c6a64;       /* 辅助文字：muted */
}

/* 基础色彩系统 */
:root {
  --canvas: #faf9f5;
  --surface-soft: #f5f0e8;
  --surface-card: var(--user-surface);
  --surface-cream-strong: #e8e0d2;
  --surface-dark: var(--user-dark);
  --surface-dark-elevated: #252320;
  --surface-dark-soft: #1f1e1b;
  
  --ink: #141413;
  --body-strong: #252523;
  --body: #3d3d3a;
  --muted: var(--user-muted);
  --muted-soft: #8e8b82;
  
  --primary: var(--user-accent);
  --primary-active: #a9583e;
  --primary-disabled: #e6dfd8;
  
  --hairline: #e6dfd8;
  --hairline-soft: #ebe6df;
  
  --on-primary: #ffffff;
  --on-dark: #faf9f5;
  --on-dark-soft: #a09d96;
  
  --success: #5db872;
  --warning: #d4a017;
  --error: #c64545;
  
  /* 圆角系统 */
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-pill: 9999px;
  
  /* 间距系统 */
  --space-xxs: 4px;
  --space-xs: 8px;
  --space-sm: 12px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-xxl: 48px;
  --space-section: 96px;
}

/* ===== Scrollbar Hidden ===== */
* {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
*::-webkit-scrollbar {
  display: none;
}

/* ===== Animations ===== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

/* ===== Reset & Base ===== */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--canvas);
  color: var(--body);
  line-height: 1.55;
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
}

/* ===== Typography ===== */
h1, h2, h3, h4 {
  font-family: "Georgia", "Times New Roman", serif;
  font-weight: 400;
  color: var(--ink);
  letter-spacing: -0.02em;
}

h1 { font-size: 48px; line-height: 1.1; letter-spacing: -1px; }
h2 { font-size: 36px; line-height: 1.15; letter-spacing: -0.5px; }
h3 { font-size: 28px; line-height: 1.2; letter-spacing: -0.3px; }
h4 { font-size: 22px; line-height: 1.3; }

p { margin-bottom: var(--space-md); }

a {
  color: var(--primary);
  text-decoration: none;
}
a:hover { text-decoration: underline; }

/* ===== Layout ===== */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg) var(--space-lg);
}

/* ===== Header ===== */
.header {
  background: var(--surface-dark);
  color: var(--on-dark);
  padding: var(--space-xl) var(--space-xl);
}

.header h1 {
  font-size: 28px;
  color: var(--on-dark);
  letter-spacing: -0.3px;
}

.header .subtitle {
  color: var(--on-dark-soft);
  font-size: 14px;
  margin-top: var(--space-xs);
}

.header .stats-bar {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-md);
  flex-wrap: wrap;
}

.header .stat {
  background: var(--surface-dark-elevated);
  padding: var(--space-xs) var(--space-md);
  border-radius: var(--radius-md);
}

.header .stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--on-dark);
}

.header .stat-label {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--on-dark-soft);
}

/* ===== Tabs ===== */
.tabs {
  display: flex;
  gap: var(--space-xxs);
  margin-bottom: var(--space-lg);
  background: var(--surface-card);
  padding: var(--space-xxs);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}

.tab {
  padding: var(--space-xs) var(--space-md);
  border: none;
  background: none;
  cursor: pointer;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--muted);
  transition: all 0.15s ease;
}

.tab:hover {
  background: var(--surface-soft);
  color: var(--ink);
}

.tab.active {
  background: var(--surface-cream-strong);
  color: var(--ink);
}

/* ===== Filters ===== */
.filters {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
}

.filter-btn {
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--hairline);
  background: var(--canvas);
  border-radius: var(--radius-pill);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--body);
  transition: all 0.15s ease;
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

/* ===== Grid ===== */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-md);
}

/* ===== Card ===== */
.card {
  background: var(--canvas);
  border: 1px solid var(--hairline-soft);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.2s ease;
  cursor: pointer;
  animation: fadeIn 0.3s ease forwards;
}

.card:hover {
  border-color: var(--hairline);
  box-shadow: 0 2px 8px rgba(20, 20, 19, 0.06);
  transform: translateY(-2px);
}

.card-img {
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
  background: var(--surface-soft);
}

.card-img.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: var(--hairline);
}

.card-body {
  padding: var(--space-md);
}

.card-type {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
}

.card-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--ink);
  margin-top: var(--space-xxs);
}

.card-color {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  font-size: 13px;
  color: var(--muted);
}

.card-color-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid var(--hairline);
}

.card-tags {
  display: flex;
  gap: var(--space-xxs);
  margin-top: var(--space-sm);
  flex-wrap: wrap;
}

.tag {
  padding: var(--space-xxs) var(--space-sm);
  background: var(--surface-card);
  color: var(--body);
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 500;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-sm);
  font-size: 12px;
  color: var(--muted-soft);
}

/* ===== Modal ===== */
.modal-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(20, 20, 19, 0.6);
  z-index: 100;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
  backdrop-filter: blur(4px);
}

.modal-overlay.show {
  display: flex;
  animation: fadeIn 0.2s ease forwards;
}

.modal {
  background: var(--canvas);
  border-radius: var(--radius-xl);
  max-width: 600px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
  position: relative;
  animation: scaleIn 0.2s ease forwards;
}

.modal-img {
  width: 100%;
  aspect-ratio: 4/5;
  object-fit: cover;
  background: var(--surface-soft);
}

.modal-close {
  position: absolute;
  top: var(--space-sm);
  right: var(--space-sm);
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--surface-dark);
  color: var(--on-dark);
  border: none;
  cursor: pointer;
  font-size: 18px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease;
}

.modal-close:hover {
  background: var(--surface-dark-elevated);
}

.modal-body {
  padding: var(--space-xl);
}

.modal-body h2 {
  font-size: 28px;
  margin-bottom: var(--space-xxs);
}

.modal-body .meta {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: var(--space-md);
}

.modal-body .section {
  margin-bottom: var(--space-md);
}

.modal-body .section-title {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
  margin-bottom: var(--space-xs);
}

.modal-body .pair-list {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.modal-body .pair-item {
  padding: var(--space-xxs) var(--space-sm);
  background: var(--surface-card);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--body);
}

.modal-body .restrict {
  color: var(--error);
  font-size: 13px;
}

/* ===== Profile ===== */
.profile-card {
  background: var(--canvas);
  border: 1px solid var(--hairline-soft);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
}

.profile-card h2 {
  font-size: 28px;
  margin-bottom: var(--space-md);
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-md);
}

.profile-item {
  padding: var(--space-sm);
  background: var(--surface-soft);
  border-radius: var(--radius-md);
}

.profile-item .label {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
}

.profile-item .value {
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
  margin-top: var(--space-xxs);
}

/* ===== Recommend ===== */
.recommend-card {
  background: var(--canvas);
  border: 1px solid var(--hairline-soft);
  border-radius: var(--radius-lg);
  padding: var(--space-xl);
  margin-bottom: var(--space-lg);
}

.recommend-card h2 {
  font-size: 28px;
  margin-bottom: var(--space-sm);
}

/* ===== Palettes ===== */
.palette-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-sm);
}

.palette-card {
  background: var(--canvas);
  border: 1px solid var(--hairline-soft);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.2s ease;
  animation: fadeIn 0.3s ease forwards;
}

.palette-card:hover {
  border-color: var(--hairline);
  transform: translateY(-2px);
}

.palette-swatches {
  display: flex;
  height: 60px;
}

.palette-swatches .swatch {
  flex: 1;
}

.palette-info {
  padding: var(--space-sm) var(--space-md);
}

.palette-meta {
  font-size: 12px;
  color: var(--muted);
  margin-top: var(--space-xxs);
}

.palette-hex {
  display: flex;
  gap: var(--space-xxs);
  margin-top: var(--space-xs);
  flex-wrap: wrap;
}

.palette-hex span {
  font-size: 11px;
  padding: 2px var(--space-xs);
  background: var(--surface-soft);
  border-radius: var(--radius-xs);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  color: var(--muted);
}

/* ===== Refs ===== */
.refs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--space-md);
}

.ref-card {
  background: var(--canvas);
  border: 1px solid var(--hairline-soft);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  transition: all 0.2s ease;
  cursor: pointer;
  animation: fadeIn 0.3s ease forwards;
}

.ref-card:hover {
  border-color: var(--hairline);
  box-shadow: 0 2px 8px rgba(20, 20, 19, 0.06);
  transform: translateY(-2px);
}

.ref-card h3 {
  font-size: 22px;
  margin-bottom: var(--space-sm);
  color: var(--ink);
}

.ref-card .ref-meta {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: var(--space-sm);
}

/* ===== Empty State ===== */
.empty {
  text-align: center;
  padding: var(--space-section) var(--space-lg);
  color: var(--muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-sm);
}

/* ===== Markdown Body ===== */
.markdown-body {
  line-height: 1.7;
  font-size: 15px;
  color: var(--body);
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin: var(--space-lg) 0 var(--space-sm);
  font-weight: 400;
}

.markdown-body h1 {
  font-size: 28px;
  border-bottom: 1px solid var(--hairline);
  padding-bottom: var(--space-sm);
}

.markdown-body h2 { font-size: 22px; }
.markdown-body h3 { font-size: 18px; }

.markdown-body p { margin: var(--space-sm) 0; }

.markdown-body ul,
.markdown-body ol {
  padding-left: var(--space-lg);
  margin: var(--space-sm) 0;
}

.markdown-body li { margin: var(--space-xxs) 0; }

.markdown-body code {
  background: var(--surface-soft);
  padding: 2px var(--space-xs);
  border-radius: var(--radius-xs);
  font-size: 13px;
  font-family: "JetBrains Mono", ui-monospace, monospace;
}

.markdown-body pre {
  background: var(--surface-dark);
  color: var(--on-dark);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-sm) 0;
}

.markdown-body pre code {
  background: none;
  color: inherit;
  padding: 0;
}

.markdown-body blockquote {
  border-left: 3px solid var(--primary);
  padding-left: var(--space-md);
  color: var(--muted);
  margin: var(--space-sm) 0;
}

.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: var(--space-sm) 0;
}

.markdown-body th,
.markdown-body td {
  border: 1px solid var(--hairline);
  padding: var(--space-sm) var(--space-md);
  text-align: left;
}

.markdown-body th {
  background: var(--surface-soft);
  font-weight: 500;
}

.markdown-body strong { font-weight: 600; }

.markdown-body a {
  color: var(--primary);
  text-decoration: underline;
}

/* ===== Button ===== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  padding: 8px 16px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  line-height: 1.4;
  white-space: nowrap;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn:active {
  transform: translateY(0);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-primary {
  background: var(--primary);
  color: var(--on-primary);
  border-color: var(--primary);
}

.btn-primary:hover {
  background: var(--primary-active);
  border-color: var(--primary-active);
}

.btn-secondary {
  background: var(--canvas);
  color: var(--ink);
  border-color: var(--hairline);
}

.btn-secondary:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-danger {
  background: transparent;
  color: var(--error);
  border-color: var(--error);
}

.btn-danger:hover {
  background: var(--error);
  color: white;
}

.btn-ghost {
  background: transparent;
  color: var(--muted);
  border-color: transparent;
}

.btn-ghost:hover {
  color: var(--ink);
  background: var(--surface-soft);
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  h1 { font-size: 32px; }
  h2 { font-size: 28px; }
  h3 { font-size: 22px; }
  
  .header { padding: var(--space-lg); }
  
  .grid,
  .palette-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
  }
  
  .refs-grid { grid-template-columns: 1fr; }
  
  .card-body { padding: var(--space-sm); }
  .card-name { font-size: 14px; }
  
  .modal-body { padding: var(--space-lg); }
  .modal-body h2 { font-size: 22px; }
}

@media (max-width: 480px) {
  .grid {
    grid-template-columns: 1fr;
  }
  
  .tabs {
    overflow-x: auto;
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
  }
  
  .tab { white-space: nowrap; }
}
</style>
