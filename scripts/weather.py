#!/usr/bin/env python3
"""
SuperOutfit 天气查询工具
用法：python weather.py --city 北京 [--date 2026-06-03]

返回 JSON 格式的天气信息，供穿搭推荐使用。
使用 Open-Meteo 免费 API（无需 API Key）。
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, date

# 主要城市坐标
CITY_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "南京": (32.0603, 118.7969),
    "西安": (34.3416, 108.9398),
    "重庆": (29.5630, 106.5516),
    "天津": (39.3434, 117.3616),
    "苏州": (31.2990, 120.5853),
    "长沙": (28.2282, 112.9388),
    "大连": (38.9140, 121.6147),
    "厦门": (24.4798, 118.0894),
    "昆明": (25.0389, 102.7183),
    "郑州": (34.7466, 113.6254),
    "济南": (36.6512, 117.1201),
    "哈尔滨": (45.8038, 126.5350),
    "沈阳": (41.8057, 123.4315),
    "东京": (35.6762, 139.6503),
    "首尔": (37.5665, 126.9780),
    "纽约": (40.7128, -74.0060),
    "伦敦": (51.5074, -0.1278),
    "巴黎": (48.8566, 2.3522),
}

WMO_CODES = {
    0: "晴天",
    1: "大部晴朗",
    2: "多云",
    3: "阴天",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "中阵雨",
    82: "大阵雨",
    95: "雷暴",
    96: "雷暴+小冰雹",
    99: "雷暴+大冰雹",
}

def get_temp_feel(temp, wind_speed=0):
    """体感温度描述"""
    if temp < 0:
        return "严寒"
    elif temp < 5:
        return "寒冷"
    elif temp < 10:
        return "冷"
    elif temp < 15:
        return "凉爽"
    elif temp < 20:
        return "舒适偏凉"
    elif temp < 25:
        return "舒适"
    elif temp < 30:
        return "温暖"
    elif temp < 35:
        return "热"
    else:
        return "酷热"

def get_clothing_advice(temp):
    """基于温度给出穿衣建议"""
    if temp < 0:
        return "厚羽绒服、保暖内衣、围巾手套帽子"
    elif temp < 5:
        return "厚外套/羽绒服、毛衣、保暖裤"
    elif temp < 10:
        return "外套、毛衣/卫衣、长裤"
    elif temp < 15:
        return "薄外套/风衣、长袖、长裤"
    elif temp < 20:
        return "薄外套或长袖衬衫、长裤"
    elif temp < 25:
        return "短袖/薄长袖、长裤/薄裤"
    elif temp < 30:
        return "短袖、薄裤/短裤"
    elif temp < 35:
        return "轻薄短袖、短裤、注意防晒"
    else:
        return "尽可能轻薄、注意防暑降温"

def query_weather(city, target_date=None):
    """查询天气"""
    if city not in CITY_COORDS:
        return {"error": f"未知城市: {city}", "available_cities": list(CITY_COORDS.keys())}
    
    lat, lon = CITY_COORDS[city]
    today = date.today()
    is_forecast = target_date is None or target_date >= today.isoformat()
    
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "Asia/Shanghai",
        "forecast_days": 7,
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SuperOutfit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"error": f"天气 API 请求失败: {str(e)}"}
    
    # 当前天气
    current = data.get("current", {})
    current_temp = current.get("temperature_2m", 0)
    current_feel = current.get("apparent_temperature", 0)
    current_code = current.get("weather_code", 0)
    
    # 找到目标日期的天气
    daily = data.get("daily", {})
    dates = daily.get("temperature_2m_max", [])
    
    target_idx = 0
    if target_date:
        daily_dates = daily.get("time", [])
        if target_date in daily_dates:
            target_idx = daily_dates.index(target_date)
        else:
            return {"error": f"无法获取 {target_date} 的天气（仅支持未来7天）"}
    
    temp_max = daily.get("temperature_2m_max", [0])[target_idx] if daily.get("temperature_2m_max") else 0
    temp_min = daily.get("temperature_2m_min", [0])[target_idx] if daily.get("temperature_2m_min") else 0
    weather_code = daily.get("weather_code", [0])[target_idx] if daily.get("weather_code") else 0
    precip_prob = daily.get("precipitation_probability_max", [0])[target_idx] if daily.get("precipitation_probability_max") else 0
    
    avg_temp = (temp_max + temp_min) / 2
    condition = WMO_CODES.get(weather_code, "未知")
    
    result = {
        "city": city,
        "date": target_date or today.isoformat(),
        "temperature": {
            "current": current_temp,
            "max": temp_max,
            "min": temp_min,
            "avg": round(avg_temp, 1),
            "unit": "°C",
        },
        "apparent_temperature": current_feel,
        "condition": condition,
        "weather_code": weather_code,
        "humidity": current.get("relative_humidity_2m", 0),
        "wind_speed": current.get("wind_speed_10m", 0),
        "precipitation_probability": precip_prob,
        "feel": get_temp_feel(avg_temp),
        "clothing_advice": get_clothing_advice(avg_temp),
        # 简化字段，方便 AI 直接引用
        "simple": {
            "temp": round(avg_temp),
            "condition": condition,
            "feel": get_temp_feel(avg_temp),
            "advice": get_clothing_advice(avg_temp),
        },
    }
    
    return result

def main():
    parser = argparse.ArgumentParser(description="SuperOutfit 天气查询")
    parser.add_argument("--city", default=None, help="城市名称（默认从配置读取）")
    parser.add_argument("--date", help="日期 YYYY-MM-DD（默认今天）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--list-cities", action="store_true", help="列出支持的城市")

    args = parser.parse_args()

    if args.list_cities:
        try:
            from output import console
            from rich.table import Table
            from rich import box
            t = Table(box=box.SIMPLE_HEAD, border_style="#e6dfd8", title="支持的城市", title_style="bold #cc785c")
            t.add_column("城市")
            for city in sorted(CITY_COORDS.keys()):
                t.add_row(city)
            console.print(t)
        except ImportError:
            print("支持的城市：")
            for city in sorted(CITY_COORDS.keys()):
                print(f"  {city}")
        return

    # 从配置获取默认城市
    city = args.city
    if not city:
        try:
            from config import get_city
            city = get_city()
        except ImportError:
            city = "大连"

    result = query_weather(city, args.date)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        try:
            from output import console, kv_pairs
            from rich.panel import Panel
            from rich.table import Table
            from rich import box

            temp = result.get("temperature", "N/A")
            condition = result.get("condition", "未知")
            humidity = result.get("humidity", "N/A")
            wind = result.get("wind_speed", "N/A")
            high = result.get("high", "N/A")
            low = result.get("low", "N/A")
            city_name = result.get("city", city)
            date = result.get("date", "today")

            # 天气图标
            icons = {"晴": "☀", "多云": "⛅", "阴": "☁", "雨": "🌧", "雪": "❄", "雾": "🌫", "风": "💨"}
            icon = icons.get(condition, "🌤")

            t = Table(box=None, show_header=False, padding=(0, 2))
            t.add_column(style="dim", min_width=10)
            t.add_column()
            t.add_row("天气", f"{icon} {condition}")
            t.add_row("温度", f"{temp}°C")
            if high != "N/A" and low != "N/A":
                t.add_row("范围", f"{low}°C ~ {high}°C")
            if humidity != "N/A":
                t.add_row("湿度", f"{humidity}%")
            if wind != "N/A":
                t.add_row("风速", f"{wind} km/h")

            console.print()
            console.print(Panel(t, title=f"天气 · {city_name} · {date}", border_style="#cc785c", box=box.ROUNDED, expand=False))
            console.print()
        except ImportError:
            print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
