const API_BASE = '/api'

// GET 请求缓存（TTL 30s）+ 请求去重
const _cache = new Map()
const _inflight = new Map()
const CACHE_TTL = 30_000

async function request(url, options = {}) {
  const isGet = !options.method || options.method === 'GET'
  const cacheKey = url

  // GET 请求：检查缓存
  if (isGet) {
    const cached = _cache.get(cacheKey)
    if (cached && Date.now() - cached.time < CACHE_TTL) {
      return cached.data
    }
    // 检查是否有进行中的相同请求（去重）
    if (_inflight.has(cacheKey)) {
      return _inflight.get(cacheKey)
    }
  }

  const doFetch = (async () => {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    const data = await response.json()

    // GET 请求写入缓存
    if (isGet) {
      _cache.set(cacheKey, { data, time: Date.now() })
      _inflight.delete(cacheKey)
    }

    return data
  })()

  // GET 请求：注册 in-flight
  if (isGet) {
    _inflight.set(cacheKey, doFetch)
    // 失败时清理 in-flight
    doFetch.catch(() => _inflight.delete(cacheKey))
  }

  return doFetch
}

// 清除缓存（写操作后调用）
function bustCache(pattern) {
  if (pattern) {
    for (const key of _cache.keys()) {
      if (key.includes(pattern)) _cache.delete(key)
    }
  } else {
    _cache.clear()
  }
}

export const api = {
  // Health
  health: () => request('/health'),

  // Wardrobe
  wardrobe: {
    list: (params = {}) => {
      const query = new URLSearchParams(params).toString()
      return request(`/wardrobe${query ? `?${query}` : ''}`)
    },
    add: (data) => {
      bustCache('/wardrobe')
      return request('/wardrobe', { method: 'POST', body: JSON.stringify(data) })
    },
    show: (id) => request(`/wardrobe/${id}`),
    update: (id, data) => {
      bustCache('/wardrobe')
      return request(`/wardrobe/${id}`, { method: 'PUT', body: JSON.stringify(data) })
    },
    delete: (id) => {
      bustCache('/wardrobe')
      return request(`/wardrobe/${id}`, { method: 'DELETE' })
    },
    stats: () => request('/wardrobe/stats'),
  },

  // Wishlist
  wishlist: {
    list: (params = {}) => {
      const query = new URLSearchParams({ ...params, wishlist: true }).toString()
      return request(`/wardrobe?${query}`)
    },
    add: (data) => {
      bustCache('/wardrobe')
      return request('/wardrobe?wishlist=true', { method: 'POST', body: JSON.stringify(data) })
    },
    show: (id) => request(`/wardrobe/${id}?wishlist=true`),
    update: (id, data) => {
      bustCache('/wardrobe')
      return request(`/wardrobe/${id}?wishlist=true`, { method: 'PUT', body: JSON.stringify(data) })
    },
    delete: (id) => {
      bustCache('/wardrobe')
      return request(`/wardrobe/${id}?wishlist=true`, { method: 'DELETE' })
    },
    stats: () => request('/wardrobe/stats?wishlist=true'),
  },

  // Wear management
  wear: {
    add: (items, date = '') => {
      bustCache('/wardrobe')
      return request('/wear/add', { method: 'POST', body: JSON.stringify({ items, date }) })
    },
    wash: (items) => {
      bustCache('/wardrobe')
      return request('/wear/wash', { method: 'POST', body: JSON.stringify({ items }) })
    },
    check: (type = null) => request(`/wear/check${type ? `?type=${encodeURIComponent(type)}` : ''}`)
  },

  // Weather
  weather: (city = '大连') => request(`/weather?city=${encodeURIComponent(city)}`),

  // Color
  color: {
    score: (hexColors) => request('/color/score', { method: 'POST', body: JSON.stringify({ hex_colors: hexColors }) })
  },

  // Outfit
  outfit: {
    score: (itemIds, occasion = '', temperature = null) => {
      const data = { item_ids: itemIds }
      if (occasion) data.occasion = occasion
      if (temperature) data.temperature = temperature
      return request('/outfit/score', { method: 'POST', body: JSON.stringify(data) })
    }
  },

  // Profile
  profile: {
    get: () => request('/profile'),
    update: (data) => {
      bustCache('/profile')
      return request('/profile', { method: 'PUT', body: JSON.stringify(data) })
    }
  },

  // Palettes
  palettes: (limit = 20) => request(`/palettes?limit=${limit}`),

  // References
  references: {
    list: () => request('/references'),
    get: (filename) => request(`/references/${filename}`),
    update: (filename, content) => {
      bustCache('/references')
      return request(`/references/${filename}`, { method: 'PUT', body: JSON.stringify({ content }) })
    },
    delete: (filename) => {
      bustCache('/references')
      return request(`/references/${filename}`, { method: 'DELETE' })
    }
  }
}
