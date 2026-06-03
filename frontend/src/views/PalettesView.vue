<script setup>
import { ref } from 'vue'

const props = defineProps({
  palettes: Array
})

const emit = defineEmits(['applyTheme'])

const showPicker = ref(false)
const selectedPalette = ref(null)
const selectedColors = ref([])

const themeSlots = [
  { key: 'accent', label: '主色调', desc: '按钮、链接、强调色' },
  { key: 'surface', label: '卡片背景', desc: '浅色卡片、输入框背景' },
  { key: 'dark', label: '深色表面', desc: '头部、深色卡片' },
  { key: 'muted', label: '辅助文字', desc: '次要文字、标签' }
]

function handlePaletteClick(palette) {
  const colors = palette.colors || []
  
  if (colors.length === 4) {
    // 正好4个颜色，直接应用
    applyTheme(colors)
  } else if (colors.length < 4) {
    // 少于4个，复制填充
    const filled = fillColors(colors)
    applyTheme(filled)
  } else {
    // 大于4个，弹出选择界面
    selectedPalette.value = palette
    selectedColors.value = []
    showPicker.value = true
  }
}

function fillColors(colors) {
  if (colors.length === 0) return ['#cc785c', '#efe9de', '#181715', '#6c6a64']
  if (colors.length === 1) return [colors[0], colors[0], colors[0], colors[0]]
  if (colors.length === 2) return [colors[0], colors[1], colors[0], colors[1]]
  if (colors.length === 3) return [colors[0], colors[1], colors[2], colors[1]]
  return colors.slice(0, 4)
}

function selectColor(color) {
  if (selectedColors.value.length < 4) {
    selectedColors.value.push(color)
  }
}

function removeColor(index) {
  selectedColors.value.splice(index, 1)
}

function applyFromPicker() {
  if (selectedColors.value.length === 4) {
    applyTheme(selectedColors.value)
    showPicker.value = false
  }
}

function applyTheme(colors) {
  emit('applyTheme', {
    accent: colors[0],
    surface: colors[1],
    dark: colors[2],
    muted: colors[3]
  })
}

function resetTheme() {
  emit('applyTheme', {
    accent: '#cc785c',
    surface: '#efe9de',
    dark: '#181715',
    muted: '#6c6a64'
  })
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
      <div 
        v-for="(p, i) in palettes" 
        :key="i" 
        class="palette-card"
        @click="handlePaletteClick(p)"
      >
        <div class="palette-swatches">
          <div v-for="c in p.colors" :key="c" class="swatch" :style="{ background: c }" :title="c"></div>
        </div>
        <div class="palette-info">
          <div class="palette-hex"><span v-for="c in p.colors" :key="c">{{ c }}</span></div>
          <div class="palette-meta">
            {{ p.source || '' }}{{ p.likes ? ' · ' + p.likes + ' likes' : '' }}
            <span v-if="p.colors.length > 4" style="color:var(--primary)"> · 点击选择颜色</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 颜色选择弹窗 -->
    <div v-if="showPicker" class="modal-overlay show" @click.self="showPicker = false">
      <div class="modal" style="max-width:500px">
        <div class="modal-toolbar">
          <h2>选择 4 个主题颜色</h2>
          <button class="btn btn-ghost" @click="showPicker = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <div style="padding:var(--space-lg)">
          <!-- 已选颜色 -->
          <div style="margin-bottom:var(--space-lg)">
            <div style="font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:var(--space-sm)">
              已选择 {{ selectedColors.length }}/4
            </div>
            <div style="display:flex;gap:var(--space-sm)">
              <div 
                v-for="(slot, idx) in themeSlots" 
                :key="slot.key"
                style="flex:1;text-align:center"
              >
                <div 
                  style="width:100%;aspect-ratio:1;border-radius:var(--radius-md);border:2px dashed var(--hairline);margin-bottom:var(--space-xs);display:flex;align-items:center;justify-content:center;cursor:pointer"
                  :style="{ 
                    background: selectedColors[idx] || 'var(--surface-soft)',
                    borderColor: selectedColors[idx] ? 'var(--primary)' : 'var(--hairline)'
                  }"
                  @click="selectedColors[idx] && removeColor(idx)"
                >
                  <span v-if="!selectedColors[idx]" style="font-size:11px;color:var(--muted)">{{ idx + 1 }}</span>
                  <span v-else style="font-size:11px;color:white;text-shadow:0 1px 2px rgba(0,0,0,0.5)">×</span>
                </div>
                <div style="font-size:11px;font-weight:500;color:var(--ink)">{{ slot.label }}</div>
                <div style="font-size:10px;color:var(--muted)">{{ slot.desc }}</div>
              </div>
            </div>
          </div>

          <!-- 可选颜色 -->
          <div>
            <div style="font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:var(--space-sm)">
              从色卡中选择
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:var(--space-xs)">
              <div 
                v-for="c in selectedPalette?.colors" 
                :key="c"
                style="width:48px;height:48px;border-radius:var(--radius-md);cursor:pointer;border:2px solid transparent;transition:all 0.15s ease"
                :style="{ 
                  background: c,
                  borderColor: selectedColors.includes(c) ? 'var(--primary)' : 'transparent',
                  opacity: selectedColors.includes(c) ? 0.5 : 1
                }"
                :title="c"
                @click="!selectedColors.includes(c) && selectColor(c)"
              />
            </div>
          </div>

          <!-- 应用按钮 -->
          <button 
            class="btn btn-primary" 
            style="width:100%;margin-top:var(--space-lg)"
            :style="{ opacity: selectedColors.length === 4 ? 1 : 0.5 }"
            :disabled="selectedColors.length !== 4"
            @click="applyFromPicker"
          >
            应用主题
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  border-bottom: 1px solid var(--hairline);
  background: var(--surface-soft);
}

.modal-toolbar h2 {
  font-size: 20px;
  margin: 0;
}
</style>
