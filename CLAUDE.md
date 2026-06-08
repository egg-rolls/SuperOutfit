# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperOutfit is an AI-powered wardrobe management and outfit recommendation system (AI 智能穿搭顾问). It manages clothing items as individual YAML files, scores color coordination using a Gaussian Process model trained on 5,462 human-rated color palettes, and recommends outfits based on weather, occasion, and user preferences.

**Version:** 3.3.0 | **License:** MIT | **Python:** 3.11+ | **Language:** Chinese (UI, docs, data)

## Build & Run Commands

```bash
# Install Python dependencies
uv sync

# Frontend dev (hot-reload, separate port)
cd frontend && npm install && npm run dev

# Frontend build (output served by FastAPI at :32200)
cd frontend && npm run build

# Gateway — starts API + frontend + MCP server
spof gateway
spof gateway --dev              # dev mode: frontend hot-reload on separate port
spof gateway --no-frontend      # API + MCP only
spof gateway --no-mcp           # API + frontend only

# Manual backend (debug only)
uv run uvicorn api.main:app --host 0.0.0.0 --port 32200 --reload

# PyInstaller packaging
python build.py                 # portable exe
python build.py --installer     # Windows installer (needs Inno Setup)
python build.py --clean

# CLI commands (unified entry point)
spof --help
spof list --json
spof color score --colors '#F5F0E8,#111111'
```

No test suite exists. `pytest` is listed as a dev dependency but no test files are present.

## Architecture

Four entry points share a common Python backend in `scripts/`:

```
Gateway (gateway.py) ─── orchestrates all services
├── CLI (superoutfit.py / spof)     ── command-line interface
├── MCP Server (server.py)          ── stdio protocol, 12 tools for AI agents
├── FastAPI Backend (api/main.py)   ── REST API on port 32200 + static file serving
└── Vue Frontend (frontend/dist/)   ── served by FastAPI in production
```

### Key Backend Modules (`scripts/`)

- **wardrobe_ops.py** — Clothing CRUD (add/list/show/edit/delete)
- **wear.py** — Wear tracking (add/wash/check/report)
- **scorer.py** — 6-dimension outfit scoring (calls color_math.py)
- **color_math.py** — Color harmony via GP model + HSL + OKLab
- **like_based_scoring.py** — 42-dim feature extraction + like-transfer + 7-grade scoring
- **weather.py** — Weather via Open-Meteo API
- **config.py** — User config loader from `data/profile.yaml`
- **train_color_model.py** — Color model training pipeline

### Frontend (`frontend/src/`)

Vue 3 Composition API + Pinia state management + Vite 8. Views: WardrobeView, WishlistView, PalettesView, ProfileView, RefsView. Theme system in `App.vue` (`applyTheme()`) derives 20+ CSS variables from 4 base colors.

### Data Layer

File-based YAML storage — no database. Each clothing item is a separate YAML file:
- `data/items/` — wardrobe items
- `data/wishlist/` — shopping list (same format)
- `data/profile.yaml` — user profile (city, measurements, preferences)
- `data/color_model_gp.pkl` — trained GP model
- `data/` is gitignored (personal data)

## Critical Design Decisions

1. **YAML is the only data entry point (v3.2).** AI generates YAML → `spof add --file item.yaml`. No `--field` parameters for clothing attributes. This allows data schema to evolve without CLI changes.

2. **`--wishlist` flag switches target directory** from `data/items/` to `data/wishlist/`. Same CRUD commands, independent storage.

3. **This app does NOT call any LLM internally.** It's an AI *tool* (called by AI via MCP), not an AI chat app. All AI recommendations happen through external agents calling MCP tools.

4. **Feature extraction has a single source of truth.** `like_based_scoring.py::extract_features()` is the only implementation. `color_math.py` imports from it. Never re-implement feature extraction elsewhere — it caused a 15-point scoring drift when OKLab a,b channels were accidentally scaled by 5x.

5. **Gateway subprocess output must go to files, not PIPE.** Windows pipe buffer is ~4KB; uvicorn logs fill it and deadlock the event loop. Logs go to `.logs/{name}.log`.

6. **Theme `applyTheme()` must set ALL 20+ CSS variables.** Missing variables keep hardcoded values, breaking theme consistency. Text colors must be computed dynamically via `pickTextColor()` — never hardcoded, or dark theme text becomes invisible.

## Git Conventions

```
<type>(<scope>): <subject>
```

Types: `feat`, `fix`, `refactor`, `ui`, `data`, `model`, `docs`, `chore`

GitHub remote requires proxy on port 7892 to push.
