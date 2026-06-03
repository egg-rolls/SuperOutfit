<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  item: Object,
  imgUrl: String
})

const emit = defineEmits(['close', 'save'])

const editing = ref(false)
const editData = ref({})

watch(() => props.item, (newItem) => {
  editing.value = false
  editData.value = {}
}, { immediate: true })

function startEdit() {
  editData.value = { ...props.item }
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editData.value = {}
}

function save() {
  emit('save', editData.value)
}

function addToArray(field) {
  if (!editData.value[field]) editData.value[field] = []
  editData.value[field].push('')
}

function removeFromArray(field, index) {
  editData.value[field].splice(index, 1)
}
</script>

<template>
  <div class="modal-overlay show" @click.self="$emit('close')">
    <div class="modal">
      <!-- 工具栏 -->
      <div class="modal-toolbar">
        <div class="toolbar-left">
          <h2>{{ editing ? '编辑衣物' : (item.colors?.primary + ' ' + item.sub_type) }}</h2>
        </div>
        <div class="toolbar-right">
          <button v-if="!editing" class="btn btn-secondary" @click="startEdit">编辑</button>
          <button v-if="editing" class="btn btn-ghost" @click="cancelEdit">取消</button>
          <button v-if="editing" class="btn btn-primary" @click="save">保存</button>
          <button class="btn btn-ghost" @click="$emit('close')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      <!-- 预览模式 -->
      <div v-if="!editing">
        <img v-if="imgUrl" class="modal-img" :src="imgUrl" :alt="item.sub_type">
        <div v-else class="modal-img" style="display:flex;align-items:center;justify-content:center;color:var(--hairline);background:var(--surface-soft)">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M20.38 3.46L16 2L12 5.69L8 2L3.62 3.46L2 8L5.69 12L2 16L3.62 20.54L8 22L12 18.31L16 22L20.38 20.54L22 16L18.31 12L22 8L20.38 3.46Z"/>
          </svg>
        </div>
        <div class="modal-body">
          <div class="meta">{{ item.type }} · {{ item.material || '?' }} · {{ item.fit || '?' }}</div>
          <div v-if="item.colors?.primary_hex" style="margin-top:8px;font-size:13px;font-family:monospace;color:var(--muted)">
            HEX: {{ item.colors.primary_hex }}{{ item.colors?.secondary_hex ? ' / ' + item.colors.secondary_hex : '' }}
          </div>
          <div class="section">
            <div class="section-title">风格</div>
            <div class="card-tags"><span v-for="s in (item.style || [])" :key="s" class="tag">{{ s }}</span></div>
          </div>
          <div class="section">
            <div class="section-title">季节 · 场合</div>
            <div class="card-tags">
              <span v-for="s in (item.season || [])" :key="s" class="tag">{{ s }}</span>
              <span v-for="o in (item.occasion || [])" :key="o" class="tag">{{ o }}</span>
            </div>
          </div>
          <div class="section">
            <div class="section-title">适穿温度</div>
            <div>{{ item.temperature_range || '?' }}°C</div>
          </div>
          <div class="section">
            <div class="section-title">推荐搭配</div>
            <div class="pair-list">
              <span v-for="p in (item.pair_with || [])" :key="p" class="pair-item">{{ p }}</span>
              <span v-if="!item.pair_with?.length" style="color:var(--muted)">暂无</span>
            </div>
          </div>
          <div v-if="item.restrict?.length" class="section">
            <div class="section-title">搭配禁忌</div>
            <div v-for="r in item.restrict" :key="r" class="restrict">{{ r }}</div>
          </div>
          <div class="section">
            <div class="section-title">穿着记录</div>
            <div>穿着 {{ item.wear_count || 0 }} 次 · {{ item.last_worn || '未穿过' }}</div>
          </div>
        </div>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="modal-body" style="max-height:70vh;overflow-y:auto">
        <div class="edit-grid">
          <div class="edit-field">
            <label>类型</label>
            <select v-model="editData.type">
              <option value="上衣">上衣</option>
              <option value="下装">下装</option>
              <option value="外套">外套</option>
              <option value="鞋子">鞋子</option>
              <option value="配饰">配饰</option>
            </select>
          </div>
          <div class="edit-field">
            <label>子类型</label>
            <input v-model="editData.sub_type" placeholder="如：T恤、牛仔裤">
          </div>
          <div class="edit-field">
            <label>主色</label>
            <input v-model="editData.colors.primary" placeholder="颜色名称">
          </div>
          <div class="edit-field">
            <label>HEX 色值</label>
            <input v-model="editData.colors.primary_hex" placeholder="#F5F0E8">
          </div>
          <div class="edit-field">
            <label>材质</label>
            <input v-model="editData.material" placeholder="如：纯棉">
          </div>
          <div class="edit-field">
            <label>版型</label>
            <select v-model="editData.fit">
              <option value="修身">修身</option>
              <option value="常规">常规</option>
              <option value="宽松">宽松</option>
              <option value="宽松落肩">宽松落肩</option>
            </select>
          </div>
          <div class="edit-field">
            <label>品牌</label>
            <input v-model="editData.brand" placeholder="品牌名称">
          </div>
          <div class="edit-field">
            <label>适穿温度</label>
            <input v-model="editData.temperature_range" placeholder="18~32">
          </div>
        </div>
        
        <div class="edit-section">
          <label>风格标签</label>
          <div class="edit-tags">
            <div v-for="(s, i) in (editData.style || [])" :key="i" class="edit-tag">
              <input v-model="editData.style[i]">
              <button @click="removeFromArray('style', i)">×</button>
            </div>
            <button class="btn btn-ghost btn-sm" @click="addToArray('style')">+ 添加</button>
          </div>
        </div>

        <div class="edit-section">
          <label>季节</label>
          <div class="edit-tags">
            <div v-for="(s, i) in (editData.season || [])" :key="i" class="edit-tag">
              <input v-model="editData.season[i]">
              <button @click="removeFromArray('season', i)">×</button>
            </div>
            <button class="btn btn-ghost btn-sm" @click="addToArray('season')">+ 添加</button>
          </div>
        </div>

        <div class="edit-section">
          <label>场合</label>
          <div class="edit-tags">
            <div v-for="(o, i) in (editData.occasion || [])" :key="i" class="edit-tag">
              <input v-model="editData.occasion[i]">
              <button @click="removeFromArray('occasion', i)">×</button>
            </div>
            <button class="btn btn-ghost btn-sm" @click="addToArray('occasion')">+ 添加</button>
          </div>
        </div>

        <div class="edit-section">
          <label>推荐搭配</label>
          <div class="edit-tags">
            <div v-for="(p, i) in (editData.pair_with || [])" :key="i" class="edit-tag">
              <input v-model="editData.pair_with[i]">
              <button @click="removeFromArray('pair_with', i)">×</button>
            </div>
            <button class="btn btn-ghost btn-sm" @click="addToArray('pair_with')">+ 添加</button>
          </div>
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

.toolbar-left h2 {
  font-size: 22px;
  margin: 0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.edit-field label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
  margin-bottom: var(--space-xs);
}

.edit-field input,
.edit-field select {
  width: 100%;
  padding: var(--space-sm);
  border: 1px solid var(--hairline);
  border-radius: var(--radius-md);
  font-size: 14px;
  background: var(--canvas);
  color: var(--ink);
}

.edit-field input:focus,
.edit-field select:focus {
  outline: none;
  border-color: var(--primary);
}

.edit-section {
  margin-bottom: var(--space-md);
}

.edit-section label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--muted);
  margin-bottom: var(--space-xs);
}

.edit-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.edit-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--surface-card);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
}

.edit-tag input {
  border: none;
  background: transparent;
  font-size: 13px;
  width: 80px;
  padding: 2px;
}

.edit-tag button {
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.edit-tag button:hover {
  color: var(--error);
}
</style>
