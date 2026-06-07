<script setup>
import { ref } from 'vue'
import { usePalettesStore } from '../stores/palettes'

const store = usePalettesStore()
const emit = defineEmits(['applyTheme'])

const showPicker = ref(false)
const selectedPalette = ref(null)
const selectedColors = ref([])

const themeSlots = [
  { key: 'accent', label: '主色调', desc: '按钮、强调色' },
  { key: 'canvas', label: '页面背景', desc: '整体背景' },
  { key: 'dark', label: '深色表面', desc: '头部、深色卡片' },
  { key: 'muted', label: '辅助文字', desc: '次要文字' }
]

// === 颜色工具 ===
function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return { r, g, b }
}

function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(c => Math.max(0, Math.min(255, Math.round(c))).toString(16).padStart(2, '0')).join('')
}

function getLuminance(hex) {
  const { r, g, b } = hexToRgb(hex)
  const toLinear = (c) => {
    c = c / 255
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
  }
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b)
}

function adjustColor(hex, amount) {
  const { r, g, b } = hexToRgb(hex)
  if (amount > 0) {
    return rgbToHex(r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount)
  } else {
    const f = 1 + amount
    return rgbToHex(r * f, g * f, b * f)
  }
}

function pickTextColor(bg) {
  const lum = getLuminance(bg)
  return lum > 0.4 ? '#1a1a1a' : '#f5f0e8'
}

function pickMutedColor(bg) {
  const lum = getLuminance(bg)
  return lum > 0.4 ? '#6c6a64' : '#a09d96'
}

// === 主题生成 ===
function generateTheme(colors) {
  const [accent, canvas, dark, muted] = colors
  const darkElevated = adjustColor(dark, 0.15)
  const darkSoft = adjustColor(dark, 0.08)
  const surfaceSoft = adjustColor(canvas, -0.04)
  const surface = adjustColor(canvas, -0.06)
  const creamStrong = adjustColor(canvas, -0.1)
  const hairline = adjustColor(canvas, -0.12)
  const hairlineSoft = adjustColor(canvas, -0.06)
  const ink = pickTextColor(canvas)
  const body = adjustColor(ink, 0.15)
  const bodyStrong = adjustColor(ink, 0.05)
  const mutedSoft = pickMutedColor(canvas)
  const accentActive = adjustColor(accent, -0.2)
  const accentDisabled = adjustColor(accent, 0.5)
  const onPrimary = pickTextColor(accent)
  const onDark = pickTextColor(dark)
  const onDarkSoft = pickMutedColor(dark)

  return {
    accent, canvas, dark, muted,
    darkElevated, darkSoft,
    surfaceSoft, surface, creamStrong, hairline, hairlineSoft,
    ink, body, bodyStrong, mutedSoft,
    accentActive, accentDisabled,
    onPrimary, onDark, onDarkSoft
  }
}

// === 交互 ===
function handlePaletteClick(palette) {
  const colors = palette.colors || []
  if (colors.length === 4) {
    emit('applyTheme', generateTheme(colors))
  } else if (colors.length > 4) {
    selectedPalette.value = palette
    selectedColors.value = []
    showPicker.value = true
  } else {
    emit('applyTheme', generateTheme(fillColors(colors)))
  }
}

function fillColors(colors) {
  if (colors.length === 0) return ['#cc785c', '#faf9f5', '#181715', '#6c6a64']
  if (colors.length === 1) return [colors[0], '#faf9f5', '#181715', colors[0]]
  if (colors.length === 2) return [colors[0], colors[1], '#181715', colors[0]]
  if (colors.length === 3) return [colors[0], colors[1], colors[2], colors[0]]
  return colors.slice(0, 4)
}

function selectColor(color) {
  if (selectedColors.value.length < 4) selectedColors.value.push(color)
}

function removeColor(index) {
  selectedColors.value.splice(index, 1)
}

function applyFromPicker() {
  if (selectedColors.value.length === 4) {
    emit('applyTheme', generateTheme(selectedColors.value))
    showPicker.value = false
  }
}

function resetTheme() {
  emit('applyTheme', generateTheme(['#cc785c', '#faf9f5', '#181715', '#6c6a64']))
}
</script>

<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md)">
      <div>
        <h3 style="font-size:18px;margin-bottom:var(--space-xxs)">色卡库</h3>
        <p style="font-size:13px;color:var(--muted)">点击色卡切换主题配色</p>
      </div>
      <button class="btn btn-secondary" @click="resetTheme">重置默认</button>
    </div>

    <div class="palette-grid">
      <div v-for="(p, i) in store.palettes" :key="i" class="palette-card" @click="handlePaletteClick(p)">
        <div class="palette-swatches">
          <div v-for="c in p.colors" :key="c" class="swatch" :style="{ background: c }" :title="c"></div>
        </div>
        <div class="palette-info">
          <div class="palette-hex"><span v-for="c in p.colors" :key="c">{{ c }}</span></div>
          <div class="palette-meta">
            {{ p.source || '' }}{{ p.likes ? ' · ' + p.likes + ' likes' : '' }}
            <span style="color:var(--primary)"> · 点击应用</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 颜色选择弹窗 (>4色时) -->
    <div v-if="showPicker" class="modal-overlay show" @click.self="showPicker = false">
      <div class="modal" style="max-width:500px">
        <div class="modal-toolbar">
          <h2>选择 4 个主题颜色</h2>
          <button class="btn btn-ghost" @click="showPicker = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div style="padding:var(--space-lg)">
          <div style="margin-bottom:var(--space-lg)">
            <div style="font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:var(--space-sm)">已选择 {{ selectedColors.length }}/4</div>
            <div style="display:flex;gap:var(--space-sm)">
              <div v-for="(slot, idx) in themeSlots" :key="slot.key" style="flex:1;text-align:center">
                <div style="width:100%;aspect-ratio:1;border-radius:var(--radius-md);border:2px dashed var(--hairline);margin-bottom:var(--space-xs);display:flex;align-items:center;justify-content:center;cursor:pointer"
                  :style="{ background: selectedColors[idx] || 'var(--surface-soft)', borderColor: selectedColors[idx] ? 'var(--primary)' : 'var(--hairline)' }"
                  @click="selectedColors[idx] && removeColor(idx)">
                  <span v-if="!selectedColors[idx]" style="font-size:11px;color:var(--muted)">{{ idx + 1 }}</span>
                  <span v-else style="font-size:11px;color:white;text-shadow:0 1px 2px rgba(0,0,0,0.5)">×</span>
                </div>
                <div style="font-size:11px;font-weight:500;color:var(--ink)">{{ slot.label }}</div>
                <div style="font-size:10px;color:var(--muted)">{{ slot.desc }}</div>
              </div>
            </div>
          </div>
          <div>
            <div style="font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:var(--space-sm)">从色卡中选择</div>
            <div style="display:flex;flex-wrap:wrap;gap:var(--space-xs)">
              <div v-for="c in selectedPalette?.colors" :key="c" style="width:48px;height:48px;border-radius:var(--radius-md);cursor:pointer;border:2px solid transparent;transition:all 0.15s ease"
                :style="{ background: c, borderColor: selectedColors.includes(c) ? 'var(--primary)' : 'transparent', opacity: selectedColors.includes(c) ? 0.5 : 1 }"
                :title="c" @click="!selectedColors.includes(c) && selectColor(c)" />
            </div>
          </div>
          <button class="btn btn-primary" style="width:100%;margin-top:var(--space-lg)" :style="{ opacity: selectedColors.length === 4 ? 1 : 0.5 }" :disabled="selectedColors.length !== 4" @click="applyFromPicker">应用主题</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-toolbar { display: flex; justify-content: space-between; align-items: center; padding: var(--space-md) var(--space-lg); border-bottom: 1px solid var(--hairline); background: var(--surface-soft); }
.modal-toolbar h2 { font-size: 20px; margin: 0; }
</style>
