<script setup>
import { ref, watch } from 'vue'
import { useProfileStore } from '../stores/profile'

const store = useProfileStore()
const editing = ref(false)
const editData = ref({})

watch(() => store.profile, () => {
  editing.value = false
  editData.value = {}
}, { immediate: true })

function startEdit() {
  editData.value = JSON.parse(JSON.stringify(store.profile))
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editData.value = {}
}

function save() {
  store.update(editData.value)
  editing.value = false
}
</script>

<template>
  <div class="profile-card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-md)">
      <h2>个人画像</h2>
      <div style="display:flex;gap:var(--space-xs)">
        <button v-if="!editing" class="btn btn-secondary" @click="startEdit">编辑</button>
        <button v-if="editing" class="btn btn-ghost" @click="cancelEdit">取消</button>
        <button v-if="editing" class="btn btn-primary" @click="save">保存</button>
      </div>
    </div>

    <!-- 预览模式 -->
    <div v-if="!editing" class="profile-grid">
      <div class="profile-item"><div class="label">姓名</div><div class="value">{{ store.profile.name || '未设置' }}</div></div>
      <div class="profile-item"><div class="label">性别</div><div class="value">{{ store.profile.gender || '未设置' }}</div></div>
      <div class="profile-item"><div class="label">身高</div><div class="value">{{ store.profile.body?.height || '?' }}cm</div></div>
      <div class="profile-item"><div class="label">体重</div><div class="value">{{ store.profile.body?.weight || '?' }}kg</div></div>
      <div class="profile-item"><div class="label">体型</div><div class="value">{{ store.profile.body?.build || '?' }}</div></div>
      <div class="profile-item"><div class="label">肩宽</div><div class="value">{{ store.profile.body?.shoulder || '?' }}cm</div></div>
      <div class="profile-item"><div class="label">胸围</div><div class="value">{{ store.profile.measurements?.chest || '?' }}cm</div></div>
      <div class="profile-item"><div class="label">腰围</div><div class="value">{{ store.profile.measurements?.waist || '?' }}cm</div></div>
      <div class="profile-item"><div class="label">臀围</div><div class="value">{{ store.profile.measurements?.hip || '?' }}cm</div></div>
      <div class="profile-item"><div class="label">肤色</div><div class="value">{{ store.profile.body?.skin_tone || '?' }}</div></div>
      <div class="profile-item"><div class="label">城市</div><div class="value">{{ store.profile.location || store.profile.city || '?' }}</div></div>
      <div class="profile-item"><div class="label">职业</div><div class="value">{{ store.profile.lifestyle?.occupation || '?' }}</div></div>
      <div class="profile-item"><div class="label">通勤方式</div><div class="value">{{ store.profile.lifestyle?.commute || '?' }}</div></div>
      <div class="profile-item"><div class="label">主要风格</div><div class="value">{{ (store.profile.style?.primary || store.profile.style_preferences || []).join('、') || '未设置' }}</div></div>
      <div class="profile-item"><div class="label">次要风格</div><div class="value">{{ (store.profile.style?.secondary || []).join('、') || '未设置' }}</div></div>
      <div class="profile-item"><div class="label">避免风格</div><div class="value">{{ (store.profile.style?.avoid || []).join('、') || '无' }}</div></div>
      <div class="profile-item"><div class="label">喜爱颜色</div><div class="value">{{ (store.profile.colors?.love || store.profile.favorite_colors || []).join('、') || '未设置' }}</div></div>
      <div class="profile-item"><div class="label">中性颜色</div><div class="value">{{ (store.profile.colors?.neutral || []).join('、') || '未设置' }}</div></div>
      <div class="profile-item"><div class="label">避免颜色</div><div class="value">{{ (store.profile.colors?.avoid || store.profile.avoided_colors || []).join('、') || '无' }}</div></div>
      <div class="profile-item"><div class="label">上衣预算</div><div class="value">¥{{ store.profile.budget?.top || '?' }}</div></div>
      <div class="profile-item"><div class="label">下装预算</div><div class="value">¥{{ store.profile.budget?.bottom || '?' }}</div></div>
      <div class="profile-item"><div class="label">外套预算</div><div class="value">¥{{ store.profile.budget?.outerwear || '?' }}</div></div>
      <div class="profile-item"><div class="label">周末活动</div><div class="value">{{ (store.profile.lifestyle?.weekend || []).join('、') || '未设置' }}</div></div>
    </div>

    <!-- 编辑模式 -->
    <div v-else style="max-height:70vh;overflow-y:auto">
      <div class="edit-grid">
        <div class="edit-field"><label>姓名</label><input v-model="editData.name"></div>
        <div class="edit-field"><label>性别</label><select v-model="editData.gender"><option value="male">男</option><option value="female">女</option></select></div>
        <div class="edit-field"><label>身高 (cm)</label><input v-model.number="editData.body.height" type="number"></div>
        <div class="edit-field"><label>体重 (kg)</label><input v-model.number="editData.body.weight" type="number"></div>
        <div class="edit-field"><label>肩宽 (cm)</label><input v-model.number="editData.body.shoulder" type="number"></div>
        <div class="edit-field"><label>体型</label><select v-model="editData.body.build"><option value="slim">偏瘦</option><option value="normal">标准</option><option value="athletic">健壮</option><option value="heavy">偏胖</option></select></div>
        <div class="edit-field"><label>胸围 (cm)</label><input v-model.number="editData.measurements.chest" type="number"></div>
        <div class="edit-field"><label>腰围 (cm)</label><input v-model.number="editData.measurements.waist" type="number"></div>
        <div class="edit-field"><label>臀围 (cm)</label><input v-model.number="editData.measurements.hip" type="number"></div>
        <div class="edit-field"><label>肤色</label><select v-model="editData.body.skin_tone"><option value="light">偏白</option><option value="medium">自然色</option><option value="warm">暖色</option><option value="dark">偏黑</option></select></div>
        <div class="edit-field"><label>城市</label><input v-model="editData.location"></div>
        <div class="edit-field"><label>职业</label><input v-model="editData.lifestyle.occupation"></div>
      </div>
      <div class="edit-section"><label>上衣预算 (¥)</label><input v-model.number="editData.budget.top" type="number" style="width:120px"></div>
      <div class="edit-section"><label>下装预算 (¥)</label><input v-model.number="editData.budget.bottom" type="number" style="width:120px"></div>
      <div class="edit-section"><label>外套预算 (¥)</label><input v-model.number="editData.budget.outerwear" type="number" style="width:120px"></div>
    </div>
  </div>
</template>

<style scoped>
.edit-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-md); margin-bottom: var(--space-lg); }
.edit-field label { display: block; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); margin-bottom: var(--space-xs); }
.edit-field input, .edit-field select { width: 100%; padding: var(--space-sm); border: 1px solid var(--hairline); border-radius: var(--radius-md); font-size: 14px; background: var(--canvas); color: var(--ink); }
.edit-field input:focus, .edit-field select:focus { outline: none; border-color: var(--primary); }
.edit-section { margin-bottom: var(--space-md); }
.edit-section label { display: block; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 1.5px; color: var(--muted); margin-bottom: var(--space-xs); }
.edit-section input { padding: var(--space-sm); border: 1px solid var(--hairline); border-radius: var(--radius-md); font-size: 14px; background: var(--canvas); color: var(--ink); }
.edit-section input:focus { outline: none; border-color: var(--primary); }
</style>
