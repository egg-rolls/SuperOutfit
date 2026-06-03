#!/usr/bin/env python3
"""
SuperOutfit UI 构建脚本 v2
用法：python build_ui.py

读取 data/ 和 references/ 生成自包含 HTML，包含：
  - 衣橱管理（衣物卡片 + 图片）
  - 穿搭推荐
  - 色卡库（6400 组真实色卡可视化）
  - 知识库（references/ 文档预览）
  - 用户画像
  - 穿搭历史
"""

import base64
import json
import os
import re
import yaml
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parent
DATA_DIR = SKILL_DIR / "data"
REFS_DIR = SKILL_DIR / "references"
UI_DIR = SKILL_DIR / "ui"
OUTPUT = UI_DIR / "outfit.html"

def load_yaml(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_all_items():
    items_dir = DATA_DIR / "items"
    if not items_dir.exists():
        return []
    items = []
    for f in sorted(items_dir.glob("*.yaml")):
        item = load_yaml(f)
        if item:
            items.append(item)
    return items

def load_images(items):
    images_dir = DATA_DIR / "images"
    result = {}
    for item in items:
        img_name = item.get("image", "")
        if img_name:
            img_path = images_dir / img_name
            if img_path.exists():
                with open(img_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                ext = img_path.suffix.lower()
                mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
                result[item["id"]] = f"data:{mime};base64,{b64}"
    return result

def load_palettes(max_count=200):
    """加载色卡数据（取前 max_count 组）"""
    palette_file = DATA_DIR / "raw_palettes.json"
    if not palette_file.exists():
        return []
    with open(palette_file, "r", encoding="utf-8") as f:
        palettes = json.load(f)
    # 按 likes 排序，取前 N 组
    palettes.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return palettes[:max_count]

def load_references():
    """加载 references/ 目录下的文档摘要"""
    if not REFS_DIR.exists():
        return []
    refs = []
    for f in sorted(REFS_DIR.glob("*.md")):
        if f.name == "SOURCES.md":
            continue
        content = f.read_text(encoding="utf-8")
        # 提取标题和前几行
        lines = content.strip().split("\n")
        title = lines[0].lstrip("#").strip() if lines else f.stem
        # 提取前 5 行非空内容作为摘要
        body_lines = [l for l in lines[1:] if l.strip() and not l.strip().startswith("---")]
        summary = "\n".join(body_lines[:8])
        refs.append({
            "name": f.name,
            "title": title,
            "summary": summary,
            "lines": len(lines),
            "size": f.stat().st_size,
        })
    return refs

def build():
    UI_DIR.mkdir(parents=True, exist_ok=True)
    profile = load_yaml(DATA_DIR / "profile.yaml") or {}
    items = load_all_items()
    history = load_yaml(DATA_DIR / "history.yaml") or {"records": []}
    index = load_yaml(DATA_DIR / "wardrobe_index.yaml") or {}
    images = load_images(items)
    palettes = load_palettes(200)
    refs = load_references()

    data = {
        "profile": profile,
        "items": items,
        "history": history.get("records", []),
        "index": index,
        "images": images,
        "palettes": palettes,
        "refs": refs,
        "generated_at": datetime.now().isoformat(),
    }

    data_json = json.dumps(data, ensure_ascii=False, indent=None)
    html = HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json)

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"UI 已生成：{OUTPUT}")
    print(f"  衣物：{len(items)} 件")
    print(f"  图片：{len(images)} 张")
    print(f"  色卡：{len(palettes)} 组（共 {len(palettes)} 组展示）")
    print(f"  知识：{len(refs)} 篇")
    print(f"  大小：{OUTPUT.stat().st_size / 1024:.1f} KB")
    print(f"\n用浏览器打开：{OUTPUT}")


HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SuperOutfit - 穿搭仪表盘</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f5f5f0;--card:#fff;--text:#1a1a1a;--dim:#666;--accent:#2d5a27;--accent-light:#e8f0e6;--border:#e0ddd8;--shadow:0 2px 8px rgba(0,0,0,.06);--radius:12px}
body{font-family:-apple-system,"SF Pro SC","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.6}
.header{background:linear-gradient(135deg,#2d3a2e,#3d4a3e);color:#fff;padding:32px 40px}
.header h1{font-size:28px;font-weight:700;letter-spacing:-.5px}
.header .subtitle{color:rgba(255,255,255,.7);font-size:14px;margin-top:4px}
.header .stats-bar{display:flex;gap:16px;margin-top:16px;flex-wrap:wrap}
.header .stat{background:rgba(255,255,255,.12);padding:8px 16px;border-radius:8px}
.header .stat-value{font-size:20px;font-weight:700}
.header .stat-label{font-size:11px;opacity:.7;text-transform:uppercase}
.container{max-width:1400px;margin:0 auto;padding:24px 20px}
.tabs{display:flex;gap:4px;margin-bottom:24px;background:var(--card);padding:4px;border-radius:var(--radius);box-shadow:var(--shadow);flex-wrap:wrap}
.tab{padding:10px 16px;border:none;background:none;cursor:pointer;border-radius:8px;font-size:13px;font-weight:500;color:var(--dim);transition:.2s}
.tab:hover{background:var(--accent-light);color:var(--accent)}
.tab.active{background:var(--accent);color:#fff}
.filters{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.filter-btn{padding:6px 14px;border:1px solid var(--border);background:var(--card);border-radius:20px;cursor:pointer;font-size:12px;transition:.2s}
.filter-btn:hover,.filter-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.card{background:var(--card);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:transform .2s,box-shadow .2s;cursor:pointer}
.card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,.1)}
.card-img{width:100%;aspect-ratio:3/4;object-fit:cover;background:#f0efe9}
.card-img.placeholder{display:flex;align-items:center;justify-content:center;font-size:48px;color:var(--border)}
.card-body{padding:14px}
.card-type{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px}
.card-name{font-size:15px;font-weight:600;margin-top:2px}
.card-color{display:flex;align-items:center;gap:6px;margin-top:6px;font-size:12px;color:var(--dim)}
.card-color-dot{width:14px;height:14px;border-radius:50%;border:1px solid var(--border)}
.card-tags{display:flex;gap:4px;margin-top:8px;flex-wrap:wrap}
.tag{padding:2px 8px;background:var(--accent-light);color:var(--accent);border-radius:10px;font-size:11px}
.card-meta{display:flex;justify-content:space-between;margin-top:8px;font-size:11px;color:var(--dim)}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:100;align-items:center;justify-content:center;padding:20px}
.modal-overlay.show{display:flex}
.modal{background:var(--card);border-radius:16px;max-width:600px;width:100%;max-height:85vh;overflow-y:auto;position:relative}
.modal-img{width:100%;aspect-ratio:4/5;object-fit:cover;background:#f0efe9}
.modal-close{position:absolute;top:12px;right:12px;width:36px;height:36px;border-radius:50%;background:rgba(0,0,0,.5);color:#fff;border:none;cursor:pointer;font-size:18px;z-index:10}
.modal-body{padding:24px}
.modal-body h2{font-size:22px;margin-bottom:4px}
.modal-body .meta{color:var(--dim);font-size:13px;margin-bottom:16px}
.modal-body .section{margin-bottom:16px}
.modal-body .section-title{font-size:12px;font-weight:600;text-transform:uppercase;color:var(--dim);letter-spacing:.5px;margin-bottom:6px}
.modal-body .pair-list{display:flex;gap:6px;flex-wrap:wrap}
.modal-body .pair-item{padding:4px 10px;background:#f5f5f0;border-radius:6px;font-size:12px}
.modal-body .restrict{color:#c44;font-size:12px}
.profile-card{background:var(--card);border-radius:var(--radius);padding:24px;box-shadow:var(--shadow)}
.profile-card h2{font-size:20px;margin-bottom:16px}
.profile-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.profile-item{padding:12px;background:var(--bg);border-radius:8px}
.profile-item .label{font-size:11px;color:var(--dim);text-transform:uppercase}
.profile-item .value{font-size:15px;font-weight:500;margin-top:2px}
.recommend-card{background:var(--card);border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);margin-bottom:24px}
.recommend-card h2{font-size:20px;margin-bottom:12px}
.combo{display:flex;gap:12px;margin-bottom:16px;align-items:center;padding:12px;background:var(--bg);border-radius:8px}
.combo-items{display:flex;gap:8px}
.combo-thumb{width:56px;height:56px;border-radius:8px;object-fit:cover;background:#e0ddd8}
.combo-info{flex:1}
.combo-score{font-size:24px;font-weight:700;color:var(--accent);min-width:56px;text-align:center}
.empty{text-align:center;padding:60px 20px;color:var(--dim)}
.empty-icon{font-size:48px;margin-bottom:12px}

/* Palette grid */
.palette-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.palette-card{background:var(--card);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow);transition:transform .2s}
.palette-card:hover{transform:translateY(-2px)}
.palette-swatches{display:flex;height:60px}
.palette-swatches .swatch{flex:1}
.palette-info{padding:10px 12px}
.palette-name{font-size:13px;font-weight:600}
.palette-meta{font-size:11px;color:var(--dim);margin-top:2px}
.palette-hex{display:flex;gap:4px;margin-top:6px;flex-wrap:wrap}
.palette-hex span{font-size:10px;padding:2px 6px;background:var(--bg);border-radius:4px;font-family:monospace}

/* Refs */
.refs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:16px}
.ref-card{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);transition:transform .2s;cursor:pointer}
.ref-card:hover{transform:translateY(-2px)}
.ref-card h3{font-size:16px;margin-bottom:8px;color:var(--accent)}
.ref-card .ref-meta{font-size:11px;color:var(--dim);margin-bottom:8px}
.ref-card .ref-summary{font-size:13px;color:var(--dim);line-height:1.5;max-height:120px;overflow:hidden;position:relative}
.ref-card .ref-summary::after{content:'';position:absolute;bottom:0;left:0;right:0;height:30px;background:linear-gradient(transparent,var(--card))}

@media(max-width:600px){.header{padding:20px}.header h1{font-size:22px}.grid,.palette-grid{grid-template-columns:repeat(2,1fr);gap:10px}.refs-grid{grid-template-columns:1fr}.card-body{padding:10px}.card-name{font-size:13px}}
</style>
</head>
<body>
<div class="header">
  <h1>🧥 SuperOutfit</h1>
  <div class="subtitle" id="profile-summary"></div>
  <div class="stats-bar" id="stats-bar"></div>
</div>
<div class="container">
  <div class="tabs">
    <button class="tab active" onclick="switchTab('wardrobe',this)">🧥 衣橱</button>
    <button class="tab" onclick="switchTab('recommend',this)">✨ 推荐</button>
    <button class="tab" onclick="switchTab('palettes',this)">🎨 色卡库</button>
    <button class="tab" onclick="switchTab('refs',this)">📚 知识库</button>
    <button class="tab" onclick="switchTab('profile',this)">👤 画像</button>
    <button class="tab" onclick="switchTab('history',this)">📅 历史</button>
  </div>

  <div id="tab-wardrobe">
    <div class="filters" id="filters"></div>
    <div class="grid" id="wardrobe-grid"></div>
  </div>
  <div id="tab-recommend" style="display:none"></div>
  <div id="tab-palettes" style="display:none">
    <div class="filters" id="palette-filters"></div>
    <div class="palette-grid" id="palette-grid"></div>
  </div>
  <div id="tab-refs" style="display:none">
    <div class="refs-grid" id="refs-grid"></div>
  </div>
  <div id="tab-profile" style="display:none"></div>
  <div id="tab-history" style="display:none"></div>
</div>

<div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div id="modal-content"></div>
  </div>
</div>

<script>
const D = __DATA_PLACEHOLDER__;
const CM = {'纯白':'#f8f8f8','白色':'#f8f8f8','米白':'#f5f0e8','米白色':'#f5f0e8','黑色':'#1a1a1a','炭黑':'#2a2a2a','深灰黑色':'#333','纯黑色':'#111111','藏青':'#1a3a5c','藏青色':'#1a3a5c','深浅灰':'#888','灰色':'#999','卡其色':'#c4a97d','卡其':'#c4a97d','复古枪黑色':'#4a4a4a','杂色多宝（棕/红/黄/黑/白）':'#8b6914'};

function switchTab(n,btn){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('[id^="tab-"]').forEach(t=>t.style.display='none');btn.classList.add('active');document.getElementById('tab-'+n).style.display='block';if(n==='palettes')renderPalettes();if(n==='refs')renderRefs();if(n==='recommend')renderRecommend();if(n==='profile')renderProfile();if(n==='history')renderHistory()}

function renderStats(){
  const p=D.profile,items=D.items,byT={};
  items.forEach(i=>{byT[i.type]=(byT[i.type]||0)+1});
  document.getElementById('profile-summary').textContent=(p.body?.height||'?')+'cm / '+(p.body?.weight||'?')+'kg · '+(p.location||'')+' · '+(p.lifestyle?.occupation||'');
  document.getElementById('stats-bar').innerHTML=
    '<div class="stat"><div class="stat-value">'+items.length+'</div><div class="stat-label">衣物</div></div>'+
    '<div class="stat"><div class="stat-value">'+Object.keys(byT).length+'</div><div class="stat-label">类别</div></div>'+
    '<div class="stat"><div class="stat-value">'+(D.palettes?.length||0)+'</div><div class="stat-label">色卡</div></div>'+
    '<div class="stat"><div class="stat-value">'+(D.refs?.length||0)+'</div><div class="stat-label">知识</div></div>'+
    '<div class="stat"><div class="stat-value">'+items.filter(i=>i.favorite).length+'</div><div class="stat-label">收藏</div></div>';
}

// ===== Wardrobe =====
function renderFilters(){
  const types=[...new Set(D.items.map(i=>i.type))];
  const styles=[...new Set(D.items.flatMap(i=>i.style||[]))];
  let h='<button class="filter-btn active" onclick="filterItems(this,\'all\')">全部</button>';
  types.forEach(t=>h+='<button class="filter-btn" onclick="filterItems(this,\'type:'+t+'\')">'+t+'</button>');
  styles.slice(0,8).forEach(s=>h+='<button class="filter-btn" onclick="filterItems(this,\'style:'+s+'\')">'+s+'</button>');
  document.getElementById('filters').innerHTML=h;
}
function filterItems(btn,f){document.querySelectorAll('#filters .filter-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');renderGrid(f)}
function renderGrid(filter){
  let items=D.items;
  if(filter&&filter!=='all'){const[k,v]=filter.split(':');if(k==='type')items=items.filter(i=>i.type===v);else if(k==='style')items=items.filter(i=>(i.style||[]).includes(v))}
  if(!items.length){document.getElementById('wardrobe-grid').innerHTML='<div class="empty"><div class="empty-icon">👔</div>衣橱为空</div>';return}
  document.getElementById('wardrobe-grid').innerHTML=items.map(item=>{
    const img=D.images[item.id];const ch=CM[item.colors?.primary]||'#ccc';
    const imgH=img?'<img class="card-img" src="'+img+'" alt="'+item.sub_type+'">':'<div class="card-img placeholder">👕</div>';
    const tags=(item.style||[]).slice(0,3).map(s=>'<span class="tag">'+s+'</span>').join('');
    return '<div class="card" onclick="showDetail(\''+item.id+'\')">'+imgH+'<div class="card-body"><div class="card-type">'+item.type+' · '+item.sub_type+'</div><div class="card-name">'+(item.colors?.primary||'')+' '+item.sub_type+'</div><div class="card-color"><span class="card-color-dot" style="background:'+ch+'"></span>'+(item.colors?.primary||'')+(item.colors?.secondary?' / '+item.colors.secondary:'')+'</div><div class="card-tags">'+tags+'</div><div class="card-meta"><span>🌡️ '+(item.temperature_range||'?')+'</span><span>穿 '+(item.wear_count||0)+' 次</span></div></div></div>';
  }).join('');
}
function showDetail(id){
  const item=D.items.find(i=>i.id===id);if(!item)return;
  const img=D.images[id];
  const imgH=img?'<img class="modal-img" src="'+img+'" alt="'+item.sub_type+'">':'<div class="modal-img" style="display:flex;align-items:center;justify-content:center;font-size:72px;color:#ccc;background:#f0efe9">👕</div>';
  const pair=(item.pair_with||[]).map(p=>'<span class="pair-item">'+p+'</span>').join('');
  const rst=(item.restrict||[]).map(r=>'<div class="restrict">⚠️ '+r+'</div>').join('');
  const occ=(item.occasion||[]).map(o=>'<span class="tag">'+o+'</span>').join('');
  const sea=(item.season||[]).map(s=>'<span class="tag">'+s+'</span>').join('');
  const sty=(item.style||[]).map(s=>'<span class="tag">'+s+'</span>').join('');
  const hexInfo=item.colors?.primary_hex?'<div style="margin-top:8px;font-size:12px;font-family:monospace;color:var(--dim)">HEX: '+item.colors.primary_hex+(item.colors?.secondary_hex?' / '+item.colors.secondary_hex:'')+'</div>':'';
  document.getElementById('modal-content').innerHTML=imgH+'<div class="modal-body"><h2>'+(item.colors?.primary||'')+' '+item.sub_type+'</h2><div class="meta">'+item.type+' · '+(item.material||'?')+' · '+(item.fit||'?')+'</div>'+hexInfo+'<div class="section"><div class="section-title">风格</div><div class="card-tags">'+sty+'</div></div><div class="section"><div class="section-title">季节 · 场合</div><div class="card-tags">'+sea+' '+occ+'</div></div><div class="section"><div class="section-title">适穿温度</div><div>🌡️ '+(item.temperature_range||'?')+' ℃</div></div><div class="section"><div class="section-title">推荐搭配</div><div class="pair-list">'+(pair||'<span style="color:#999">暂无</span>')+'</div></div>'+(rst?'<div class="section"><div class="section-title">搭配禁忌</div>'+rst+'</div>':'')+'<div class="section"><div class="section-title">穿着记录</div><div>穿 '+(item.wear_count||0)+' 次 · '+(item.last_worn||'未穿过')+'</div></div></div>';
  document.getElementById('modal').classList.add('show');
}
function closeModal(){document.getElementById('modal').classList.remove('show')}

// ===== Palettes =====
function renderPalettes(){
  const palettes=D.palettes||[];
  if(!palettes.length){document.getElementById('palette-grid').innerHTML='<div class="empty"><div class="empty-icon">🎨</div>暂无色卡数据</div>';return}
  // Source filter
  const sources=[...new Set(palettes.map(p=>p.source||'unknown'))];
  let fh='<button class="filter-btn active" onclick="filterPalettes(this,\'all\')">全部 ('+palettes.length+')</button>';
  sources.forEach(s=>{const c=palettes.filter(p=>(p.source||'unknown')===s).length;fh+='<button class="filter-btn" onclick="filterPalettes(this,\''+s+'\')">'+s+' ('+c+')</button>'});
  document.getElementById('palette-filters').innerHTML=fh;
  renderPaletteGrid(palettes);
}
function filterPalettes(btn,src){document.querySelectorAll('#palette-filters .filter-btn').forEach(b=>b.classList.remove('active'));btn.classList.add('active');const all=D.palettes||[];renderPaletteGrid(src==='all'?all:all.filter(p=>(p.source||'unknown')===src))}
function renderPaletteGrid(palettes){
  document.getElementById('palette-grid').innerHTML=palettes.slice(0,100).map(p=>{
    const swatches=p.colors.map(c=>'<div class="swatch" style="background:'+c+'" title="'+c+'"></div>').join('');
    const hexes=p.colors.map(c=>'<span>'+c+'</span>').join('');
    const meta=(p.source||'')+(p.likes?' · ❤️ '+p.likes:'')+(p.name?' · '+p.name:'');
    return '<div class="palette-card"><div class="palette-swatches">'+swatches+'</div><div class="palette-info"><div class="palette-hex">'+hexes+'</div><div class="palette-meta">'+meta+'</div></div></div>';
  }).join('');
}

// ===== References =====
function renderRefs(){
  const refs=D.refs||[];
  if(!refs.length){document.getElementById('refs-grid').innerHTML='<div class="empty"><div class="empty-icon">📚</div>暂无知识文档</div>';return}
  document.getElementById('refs-grid').innerHTML=refs.map(r=>{
    const summary=r.summary.replace(/\n/g,'<br>').replace(/\|.*\|/g,'').replace(/#{1,6}\s/g,'').substring(0,300);
    return '<div class="ref-card"><h3>📄 '+r.title+'</h3><div class="ref-meta">'+r.name+' · '+r.lines+' 行 · '+(r.size/1024).toFixed(1)+' KB</div><div class="ref-summary">'+summary+'</div></div>';
  }).join('');
}

// ===== Profile =====
function renderProfile(){
  const p=D.profile,b=p.body||{},s=p.style||{},c=p.colors||{},l=p.lifestyle||{},bg=p.budget||{};
  document.getElementById('tab-profile').innerHTML='<div class="profile-card"><h2>👤 个人画像</h2><div class="profile-grid">'+
    '<div class="profile-item"><div class="label">身材</div><div class="value">'+(b.height||'?')+'cm / '+(b.weight||'?')+'kg · '+(b.build||'?')+'</div></div>'+
    '<div class="profile-item"><div class="label">肩宽</div><div class="value">'+(b.shoulder||'?')+'cm</div></div>'+
    '<div class="profile-item"><div class="label">三围</div><div class="value">胸'+(p.measurements?.chest||'?')+' / 腰'+(p.measurements?.waist||'?')+' / 臀'+(p.measurements?.hip||'?')+'</div></div>'+
    '<div class="profile-item"><div class="label">城市</div><div class="value">'+(p.location||'?')+'</div></div>'+
    '<div class="profile-item"><div class="label">职业</div><div class="value">'+(l.occupation||'?')+'</div></div>'+
    '<div class="profile-item"><div class="label">通勤</div><div class="value">'+(l.commute||'?')+'</div></div>'+
    '<div class="profile-item"><div class="label">主要风格</div><div class="value">'+(s.primary||[]).join('、')+'</div></div>'+
    '<div class="profile-item"><div class="label">次要风格</div><div class="value">'+(s.secondary||[]).join('、')+'</div></div>'+
    '<div class="profile-item"><div class="label">避免风格</div><div class="value">'+(s.avoid||[]).join('、')+'</div></div>'+
    '<div class="profile-item"><div class="label">喜爱颜色</div><div class="value">'+(c.love||[]).join('、')+'</div></div>'+
    '<div class="profile-item"><div class="label">中性颜色</div><div class="value">'+(c.neutral||[]).join('、')+'</div></div>'+
    '<div class="profile-item"><div class="label">避免颜色</div><div class="value">'+(c.avoid||[]).join('、')+'</div></div>'+
    '<div class="profile-item"><div class="label">预算（上/下/外套）</div><div class="value">¥'+(bg.top||'?')+' / ¥'+(bg.bottom||'?')+' / ¥'+(bg.outerwear||'?')+'</div></div>'+
    '<div class="profile-item"><div class="label">周末</div><div class="value">'+(l.weekend||[]).join('、')+'</div></div>'+
    '</div></div>';
}

// ===== Recommend =====
function renderRecommend(){
  const items=D.items;
  if(items.length<2){document.getElementById('tab-recommend').innerHTML='<div class="empty"><div class="empty-icon">✨</div>衣物太少，无法生成推荐</div>';return}
  const tops=items.filter(i=>i.type==='上衣'),bottoms=items.filter(i=>i.type==='下装'),accs=items.filter(i=>i.type==='配饰');
  const combos=[];
  for(const t of tops)for(const b of bottoms){const c=[t,b];const a=accs.find(a=>(a.occasion||[]).some(o=>(t.occasion||[]).includes(o)||(b.occasion||[]).includes(o)));if(a)c.push(a);let sc=60;const safe=['纯白','白色','米白','米白色','黑色','炭黑','深浅灰','灰色','藏青','藏青色','卡其色'];if(safe.includes(t.colors?.primary))sc+=10;if(safe.includes(b.colors?.primary))sc+=10;const so=[...new Set(t.season||[])].filter(s=>(b.season||[]).includes(s));if(so.length)sc+=8;const st=[...new Set(t.style||[])].filter(s=>(b.style||[]).includes(s));if(st.length)sc+=7;if(((t.wear_count||0)+(b.wear_count||0))/2<3)sc+=5;combos.push({items:c,score:Math.min(sc,100)})}
  combos.sort((a,b)=>b.score-a.score);const top3=combos.slice(0,3);const gc=s=>s>=85?'#2d5a27':s>=70?'#5a8a27':s>=55?'#aa8a27':'#aa4427';
  document.getElementById('tab-recommend').innerHTML='<div class="recommend-card"><h2>✨ 今日推荐穿搭</h2><p style="color:var(--dim);margin-bottom:16px;font-size:13px">基于你的风格偏好（'+(D.profile.style?.primary||[]).join('/')+'）自动搭配</p>'+top3.map((c,idx)=>'<div class="combo"><div class="combo-score" style="color:'+gc(c.score)+'">'+c.score+'<div style="font-size:12px;font-weight:400">方案'+(idx+1)+'</div></div><div class="combo-items">'+c.items.map(item=>{const img=D.images[item.id];return img?'<img class="combo-thumb" src="'+img+'" title="'+item.sub_type+'">':'<div class="combo-thumb" style="display:flex;align-items:center;justify-content:center;font-size:20px">👕</div>'}).join('')+'</div><div class="combo-info"><div style="font-weight:600">'+c.items.map(i=>i.sub_type).join(' + ')+'</div><div style="font-size:12px;color:var(--dim)">'+c.items.map(i=>i.colors?.primary).join(' · ')+'</div></div></div>').join('')+'</div>';
}

// ===== History =====
function renderHistory(){
  const r=D.history||[];
  if(!r.length){document.getElementById('tab-history').innerHTML='<div class="empty"><div class="empty-icon">📅</div>暂无穿搭记录</div>';return}
  document.getElementById('tab-history').innerHTML='<div class="profile-card"><h2>📅 穿搭历史</h2>'+r.map(rec=>'<div style="padding:12px;border-bottom:1px solid var(--border)"><div style="font-weight:600">'+rec.date+'</div><div style="font-size:13px;color:var(--dim)">'+(rec.items||[]).join(', ')+(rec.occasion?' · '+rec.occasion:'')+'</div></div>').join('')+'</div>';
}

renderStats();renderFilters();renderGrid('all');
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});
</script>
</body>
</html>
'''.strip()


if __name__ == "__main__":
    build()
