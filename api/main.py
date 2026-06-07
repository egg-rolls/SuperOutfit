"""
SuperOutfit API Server
直接 import scripts/ 中的函数，不 fork 子进程
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
import json
import sys
import yaml

# --- 路径 ---
APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR / "data"
SCRIPTS_DIR = APP_DIR / "scripts"

# scripts/ 加入 sys.path，支持 from scripts.xxx import yyy
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# --- 懒加载 scripts（避免启动时加载 GP 模型） ---
_wo = None
_we = None
_wx = None
_cm = None
_sc = None

def _get_wardrobe_ops():
    global _wo
    if _wo is None:
        from scripts import wardrobe_ops
        _wo = wardrobe_ops
    return _wo

def _get_wear():
    global _we
    if _we is None:
        from scripts import wear
        _we = wear
    return _we

def _get_weather():
    global _wx
    if _wx is None:
        from scripts import weather
        _wx = weather
    return _wx

def _get_color_math():
    global _cm
    if _cm is None:
        from scripts import color_math
        _cm = color_math
    return _cm

def _get_scorer():
    global _sc
    if _sc is None:
        from scripts import scorer
        _sc = scorer
    return _sc

# --- FastAPI ---
app = FastAPI(title="SuperOutfit API", version="3.2.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic 模型 ---
class AddItemRequest(BaseModel):
    type: str
    sub_type: str = Field(..., max_length=10, description="≤10字")
    primary_color: str = Field(..., max_length=5, description="≤5字")
    primary_hex: str = ""
    material: str = ""
    fit: str = "常规"
    style: str = ""
    season: str = ""
    temp_range: str = ""
    occasion: str = ""
    brand: str = ""
    price: int = 0
    image: str = ""

class UpdateItemRequest(BaseModel):
    wear_count: int | None = None
    last_worn: str | None = None
    favorite: bool | None = None

class ColorScoreRequest(BaseModel):
    hex_colors: list[str]

class OutfitScoreRequest(BaseModel):
    item_ids: list[str]
    occasion: str = ""
    temperature: int | None = None

class WearAddRequest(BaseModel):
    items: str
    date: str = ""

class WearWashRequest(BaseModel):
    items: str

class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    gender: str | None = None
    height: int | None = None
    weight: int | None = None
    skin_tone: str | None = None
    style_preferences: list[str] | None = None
    city: str | None = None
    budget_range: dict | None = None

# --- API 路由 ---
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.2.1"}

# 衣橱 CRUD
@app.get("/api/wardrobe")
async def wardrobe_list(category: str = None, season: str = None, wishlist: bool = False):
    wo = _get_wardrobe_ops()
    result = wo.api_list(type=category, season=season, wishlist=wishlist)
    return result["items"]

@app.post("/api/wardrobe")
async def wardrobe_add(req: AddItemRequest, wishlist: bool = False):
    wo = _get_wardrobe_ops()
    item_dict = {
        "type": req.type,
        "sub_type": req.sub_type,
        "colors": {
            "primary": req.primary_color,
            "primary_hex": req.primary_hex,
            "secondary": "",
            "secondary_hex": "",
        },
        "material": req.material,
        "fit": req.fit,
        "style": [s.strip() for s in req.style.split(",") if s.strip()] if req.style else [],
        "season": [s.strip() for s in req.season.split(",") if s.strip()] if req.season else [],
        "temperature_range": req.temp_range,
        "occasion": [s.strip() for s in req.occasion.split(",") if s.strip()] if req.occasion else [],
        "brand": req.brand,
        "price": req.price,
        "image": req.image,
        "favorite": False,
    }
    return wo.api_add(item_dict, wishlist=wishlist)

@app.get("/api/wardrobe/stats")
async def wardrobe_stats(wishlist: bool = False):
    wo = _get_wardrobe_ops()
    return wo.api_stats(wishlist=wishlist)

@app.get("/api/wardrobe/{item_id}")
async def wardrobe_show(item_id: str, wishlist: bool = False):
    wo = _get_wardrobe_ops()
    item = wo.api_show(item_id, wishlist=wishlist)
    if not item:
        raise HTTPException(status_code=404, detail=f"未找到 {item_id}")
    return item

@app.put("/api/wardrobe/{item_id}")
async def wardrobe_update(item_id: str, req: UpdateItemRequest, wishlist: bool = False):
    wo = _get_wardrobe_ops()
    item = wo.api_show(item_id, wishlist=wishlist)
    if not item:
        raise HTTPException(status_code=404, detail=f"未找到 {item_id}")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    item.update(updates)
    return wo.api_update(item_id, item, wishlist=wishlist)

@app.delete("/api/wardrobe/{item_id}")
async def wardrobe_delete(item_id: str, wishlist: bool = False):
    wo = _get_wardrobe_ops()
    result = wo.api_delete(item_id, wishlist=wishlist)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

# 穿着管理
@app.post("/api/wear/add")
async def wear_add(req: WearAddRequest):
    we = _get_wear()
    item_ids = [s.strip() for s in req.items.split(",") if s.strip()]
    return we.api_record(item_ids, req.date or None)

@app.post("/api/wear/wash")
async def wear_wash(req: WearWashRequest):
    we = _get_wear()
    item_ids = [s.strip() for s in req.items.split(",") if s.strip()]
    return we.api_wash(item_ids)

@app.get("/api/wear/check")
async def wear_check(type: str = None):
    we = _get_wear()
    return we.api_check(type)

# 天气
@app.get("/api/weather")
async def weather_query(city: str = "大连", date: str = None):
    wx = _get_weather()
    return wx.query_weather(city, date)

# 色彩评分
@app.post("/api/color/score")
async def color_score(req: ColorScoreRequest):
    cm = _get_color_math()
    return cm.api_score(req.hex_colors)

# 穿搭评分
@app.post("/api/outfit/score")
async def outfit_score(req: OutfitScoreRequest):
    sc = _get_scorer()
    return sc.score_outfit(req.item_ids, req.occasion or None, req.temperature)

# 用户画像
@app.get("/api/profile")
async def profile_get():
    p = DATA_DIR / "profile.yaml"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

@app.put("/api/profile")
async def profile_update(req: ProfileUpdateRequest):
    p = DATA_DIR / "profile.yaml"
    profile = {}
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f) or {}
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    profile.update(updates)
    with open(p, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, allow_unicode=True, default_flow_style=False)
    return profile

# 色卡
@app.get("/api/palettes")
async def palettes_list(limit: int = 20):
    palettes_path = DATA_DIR / "scored_palettes.json"
    if not palettes_path.exists():
        return []
    with open(palettes_path, "r", encoding="utf-8") as f:
        palettes = json.load(f)
    top = palettes[:limit]
    return [{"colors": p["colors"], "score": p.get("score", 0)} for p in top]

@app.get("/api/palettes/debug")
async def palettes_debug():
    palettes_path = DATA_DIR / "scored_palettes.json"
    if not palettes_path.exists():
        return {"total": 0, "first_keys": [], "first_score": None}
    with open(palettes_path, "r", encoding="utf-8") as f:
        palettes = json.load(f)
    return {"total": len(palettes), "first_keys": list(palettes[0].keys()), "first_score": palettes[0].get("score")}

# 路径穿越防护
def _safe_ref_path(filename: str) -> Path:
    """校验参考文档路径，防止路径穿越"""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    fpath = (APP_DIR / "references" / filename).resolve()
    ref_dir = (APP_DIR / "references").resolve()
    if not str(fpath).startswith(str(ref_dir)):
        raise HTTPException(status_code=400, detail="非法文件路径")
    return fpath

# 知识库
@app.get("/api/references")
async def references_list():
    ref_dir = APP_DIR / "references"
    results = []
    for f in sorted(ref_dir.glob("*.md")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                content = fp.read()
                # 只返回前 200 字符作为预览
                excerpt = content[:200]
                results.append({"filename": f.name, "excerpt": excerpt, "has_more": len(content) > 200})
        except OSError:
            results.append({"filename": f.name, "excerpt": "", "has_more": False})
    return results

@app.get("/api/references/{filename}")
async def reference_get(filename: str):
    fpath = _safe_ref_path(filename)
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    with open(fpath, "r", encoding="utf-8") as f:
        return {"filename": filename, "content": f.read()}

@app.put("/api/references/{filename}")
async def reference_update(filename: str, body: dict):
    fpath = _safe_ref_path(filename)
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    content = body.get("content", "")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return {"filename": filename, "content": content}

@app.delete("/api/references/{filename}")
async def reference_delete(filename: str):
    fpath = _safe_ref_path(filename)
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    fpath.unlink()
    return {"filename": filename, "deleted": True}

# 衣物图片
images_dir = DATA_DIR / "images"
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

# 静态文件 - 前端
FRONTEND_DIR = APP_DIR / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
STATIC_DIR = DIST_DIR if DIST_DIR.exists() else FRONTEND_DIR

@app.get("/")
async def index():
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse("<h1>SuperOutfit API</h1><p>前端文件未找到</p>")

@app.get("/manifest.json")
async def manifest():
    if (STATIC_DIR / "manifest.json").exists():
        return FileResponse(STATIC_DIR / "manifest.json", media_type="application/json")
    return FileResponse(FRONTEND_DIR / "public" / "manifest.json", media_type="application/json")

@app.get("/sw.js")
async def service_worker():
    if (STATIC_DIR / "sw.js").exists():
        return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")
    return FileResponse(FRONTEND_DIR / "public" / "sw.js", media_type="application/javascript")

@app.get("/favicon.svg")
async def favicon():
    if (STATIC_DIR / "favicon.svg").exists():
        return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")
    return FileResponse(FRONTEND_DIR / "public" / "favicon.svg", media_type="image/svg+xml")

@app.get("/icon-{size}.png")
async def icon(size: str):
    if (STATIC_DIR / f"icon-{size}.png").exists():
        return FileResponse(STATIC_DIR / f"icon-{size}.png")
    return FileResponse(FRONTEND_DIR / "public" / f"icon-{size}.png")

@app.get("/assets/{filename:path}")
async def assets(filename: str):
    file_path = STATIC_DIR / "assets" / filename
    if file_path.exists():
        if filename.endswith(".js"):
            return FileResponse(file_path, media_type="application/javascript")
        if filename.endswith(".css"):
            return FileResponse(file_path, media_type="text/css")
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="资源不存在")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
