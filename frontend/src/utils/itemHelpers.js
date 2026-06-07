// Shared color name → hex map
const COLOR_MAP = {
  '纯白':'#f8f8f8','白色':'#f8f8f8','米白':'#f5f0e8','米白色':'#f5f0e8',
  '黑色':'#1a1a1a','炭黑':'#2a2a2a','深灰黑色':'#333','纯黑色':'#111111',
  '藏青':'#1a3a5c','藏青色':'#1a3a5c','深浅灰':'#888','灰色':'#999',
  '卡其色':'#c4a97d','卡其':'#c4a97d','复古枪黑色':'#4a4a4a'
}

export function getImgUrl(item) {
  return item.image ? `/images/${item.image}` : null
}

export function getColor(item) {
  return COLOR_MAP[item.colors?.primary] || item.colors?.primary_hex || '#ccc'
}

export function getTypes(items) {
  return [...new Set(items.map(i => i.type))]
}

export function getStyles(items) {
  return [...new Set(items.flatMap(i => i.style || []))].slice(0, 8)
}
