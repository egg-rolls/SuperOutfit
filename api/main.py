"""
SuperOutfit API Server
FastAPI 后端，通过 subprocess 调用 scripts/ 中的 CLI 工具
与 MCP server.py 共享同一套脚本，不重复实现
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json
import subprocess
import sys
import yaml

# --- 路径 ---
APP_DIR = Path(__file__).parent.parent
DATA_DIR = APP_DIR / "data"
SCRIPTS_DIR = APP_DIR / "scripts"
VENV_DIR = APP_DIR / ".venv"
PYTHON = str(VENV_DIR / "Scripts" / "python.exe")

# --- FastAPI ---
app = FastAPI(title="SuperOutfit API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 工具函数 ---
def run_script(name: str, args: list[str] = None, timeout: int = 30) -> str:
    """运行 scripts/ 下的 Python 脚本"""
    cmd = [PYTHON, str(SCRIPTS_DIR / name)]
    if args:
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"脚本执行失败: {result.stderr}")
    return result.stdout.strip()

def run_script_json(name: str, args: list[str] = None) -> dict:
    """运行脚本并解析 JSON 输出"""
    output = run_script(name, args)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw": output}

# --- Pydantic 模型 ---
class AddItemRequest(BaseModel):
    type: str
    sub_type: str
    primary_color: str
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

class WardrobeRecordRequest(BaseModel):
    items: str
    occasion: str = ""
    notes: str = ""

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
    return {"status": "ok", "version": "2.0.0"}

# 衣橱 CRUD
@app.get("/api/wardrobe")
async def wardrobe_list(category: str = None, style: str = None, season: str = None):
    args = ["list", "--json"]
    if category: args.extend(["--type", category])
    if style: args.extend(["--style", style])
    if season: args.extend(["--season", season])
    result = run_script_json("wardrobe_ops.py", args)
    # 前端期望数组，兼容 {target, items, total} 和直接数组
    if isinstance(result, dict) and "items" in result:
        return result["items"]
    return result

@app.post("/api/wardrobe")
async def wardrobe_add(req: AddItemRequest):
    args = ["add"]
    for key, val in req.model_dump().items():
        if val is not None and val != "" and val != 0:
            args.extend([f"--{key.replace('_', '-')}", str(val)])
    return run_script_json("wardrobe_ops.py", args)

@app.get("/api/wardrobe/stats")
async def wardrobe_stats():
    # 从列表数据计算统计
    items = run_script_json("wardrobe_ops.py", ["list", "--json"])
    if isinstance(items, dict) and "items" in items:
        items = items["items"]
    if not isinstance(items, list):
        return {"total": 0, "by_type": {}, "by_season": {}, "total_wears": 0}
    from collections import Counter
    type_counts = Counter(i.get("type", "未知") for i in items)
    season_counts = Counter(s for i in items for s in (i.get("season") or []))
    total_wears = sum(i.get("wear_count", 0) for i in items)
    return {
        "total": len(items),
        "by_type": dict(type_counts),
        "by_season": dict(season_counts),
        "total_wears": total_wears,
    }

@app.get("/api/wardrobe/{item_id}")
async def wardrobe_show(item_id: str):
    return run_script_json("wardrobe_ops.py", ["show", item_id])

@app.put("/api/wardrobe/{item_id}")
async def wardrobe_update(item_id: str, req: UpdateItemRequest):
    args = ["update", item_id]
    if req.wear_count is not None: args.extend(["--wear-count", str(req.wear_count)])
    if req.last_worn is not None: args.extend(["--last-worn", req.last_worn])
    if req.favorite is not None: args.extend(["--favorite", str(req.favorite)])
    return run_script_json("wardrobe_ops.py", args)

@app.delete("/api/wardrobe/{item_id}")
async def wardrobe_delete(item_id: str):
    return run_script_json("wardrobe_ops.py", ["delete", item_id])

@app.post("/api/wardrobe/record")
async def wardrobe_record(req: WardrobeRecordRequest):
    args = ["record", "--items", req.items]
    if req.occasion: args.extend(["--occasion", req.occasion])
    if req.notes: args.extend(["--notes", req.notes])
    return run_script_json("wardrobe_ops.py", args)

# 穿着管理
@app.post("/api/wear/add")
async def wear_add(req: WearAddRequest):
    args = ["add", "--items", req.items]
    if req.date: args.extend(["--date", req.date])
    return run_script_json("wear.py", args)

@app.post("/api/wear/wash")
async def wear_wash(req: WearWashRequest):
    return run_script_json("wear.py", ["wash", "--items", req.items])

@app.get("/api/wear/check")
async def wear_check(type: str = None):
    args = ["check", "--json"]
    if type: args.extend(["--type", type])
    return run_script_json("wear.py", args)

# 天气
@app.get("/api/weather")
async def weather_query(city: str = "大连", date: str = None):
    args = ["--city", city]
    if date: args.extend(["--date", date])
    return run_script_json("weather.py", args)

# 色彩评分
@app.post("/api/color/score")
async def color_score(req: ColorScoreRequest):
    return run_script_json("color_math.py", ["--colors", ",".join(req.hex_colors)])

# 穿搭评分
@app.post("/api/outfit/score")
async def outfit_score(req: OutfitScoreRequest):
    args = ["--items", ",".join(req.item_ids)]
    if req.occasion: args.extend(["--occasion", req.occasion])
    if req.temperature: args.extend(["--temp", str(req.temperature)])
    return run_script_json("scorer.py", args)

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
    with open(DATA_DIR / "scored_palettes.json", "r", encoding="utf-8") as f:
        palettes = json.load(f)
    top = palettes[:limit]
    return [{"colors": p["colors"], "score": p.get("score", 0)} for p in top]

@app.get("/api/palettes/debug")
async def palettes_debug():
    with open(DATA_DIR / "scored_palettes.json", "r", encoding="utf-8") as f:
        palettes = json.load(f)
    return {"total": len(palettes), "first_keys": list(palettes[0].keys()), "first_score": palettes[0].get("score")}

# 知识库
@app.get("/api/references")
async def references_list():
    ref_dir = APP_DIR / "references"
    return [f.name for f in ref_dir.glob("*.md")]

@app.get("/api/references/{filename}")
async def reference_get(filename: str):
    fpath = APP_DIR / "references" / filename
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    with open(fpath, "r", encoding="utf-8") as f:
        return {"filename": filename, "content": f.read()}

@app.put("/api/references/{filename}")
async def reference_update(filename: str, body: dict):
    fpath = APP_DIR / "references" / filename
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    content = body.get("content", "")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return {"filename": filename, "content": content}

@app.delete("/api/references/{filename}")
async def reference_delete(filename: str):
    fpath = APP_DIR / "references" / filename
    if not fpath.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    fpath.unlink()
    return {"filename": filename, "deleted": True}

# 衣物图片 - 直接挂载静态目录，不经过 Python 代码
images_dir = DATA_DIR / "images"
if images_dir.exists():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

# AI 推荐 WebSocket
@app.websocket("/ws/recommend")
async def ws_recommend(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event", "")
            body = data.get("body", "")

            if event == "chat":
                profile = {}
                p = DATA_DIR / "profile.yaml"
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        profile = yaml.safe_load(f) or {}

                # 获取天气
                try:
                    weather_info = run_script_json("weather.py", ["--city", profile.get("city", "大连"), "--json"])
                    temp = weather_info.get("current", {}).get("temp", "N/A")
                    desc = weather_info.get("current", {}).get("weather_desc", "未知")
                except:
                    temp, desc = "N/A", "未知"

                # 获取衣橱
                try:
                    items = run_script_json("wardrobe_ops.py", ["list", "--json"])
                    wardrobe_summary = "\n".join([
                        f"- {i.get('name', i.get('type', ''))} ({i.get('type','')}, {i.get('colors', {}).get('primary', '')})"
                        for i in items[:20]
                    ])
                except:
                    wardrobe_summary = "衣橱为空"

                prompt = f"""你是穿搭推荐助手。用户问：{body}

当前天气：{profile.get('city', '大连')} {temp}°C {desc}
用户：{profile.get('height','N/A')}cm {profile.get('weight','N/A')}kg
风格偏好：{', '.join(profile.get('style_preferences', []))}
衣橱：
{wardrobe_summary}

请推荐 1-2 套穿搭方案。格式：方案名 + 搭配 + 推荐理由（简洁）"""

                import http.client
                try:
                    conn = http.client.HTTPConnection("127.0.0.1", 11434, timeout=60)
                    payload = json.dumps({
                        "model": "qwen3:32b",
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": True
                    })
                    conn.request("POST", "/api/chat", payload, {"Content-Type": "application/json"})
                    resp = conn.getresponse()

                    for line in resp:
                        line = line.strip()
                        if line:
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    await websocket.send_json({"event": "chat", "body": content})
                            except json.JSONDecodeError:
                                continue

                    await websocket.send_json({"event": "end", "body": ""})
                except Exception as e:
                    await websocket.send_json({"event": "chat", "body": f"AI 服务不可用: {str(e)}"})
                    await websocket.send_json({"event": "end", "body": ""})

    except WebSocketDisconnect:
        pass

# 静态文件 - 前端（优先 dist/，开发模式回退到 frontend/）
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
    # dist 模式下 manifest 在 dist/ 根目录；开发模式在 public/
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
