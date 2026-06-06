const API_BASE = 'http://localhost:32201/api'
const WS_BASE = 'ws://localhost:32201/ws'

async function request(url, options = {}) {
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
  
  return response.json()
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
    add: (data) => request('/wardrobe', { method: 'POST', body: JSON.stringify(data) }),
    show: (id) => request(`/wardrobe/${id}`),
    update: (id, data) => request(`/wardrobe/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => request(`/wardrobe/${id}`, { method: 'DELETE' }),
    stats: () => request('/wardrobe/stats'),
    record: (data) => request('/wardrobe/record', { method: 'POST', body: JSON.stringify(data) })
  },
  
  // Wear management
  wear: {
    add: (items, date = '') => request('/wear/add', { method: 'POST', body: JSON.stringify({ items, date }) }),
    wash: (items) => request('/wear/wash', { method: 'POST', body: JSON.stringify({ items }) }),
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
    update: (data) => request('/profile', { method: 'PUT', body: JSON.stringify(data) })
  },
  
  // Palettes
  palettes: (limit = 20) => request(`/palettes?limit=${limit}`),
  
  // References
  references: {
    list: () => request('/references'),
    get: (filename) => request(`/references/${filename}`),
    update: (filename, content) => request(`/references/${filename}`, { method: 'PUT', body: JSON.stringify({ content }) }),
    delete: (filename) => request(`/references/${filename}`, { method: 'DELETE' })
  }
}

export function connectRecommendWS(onMessage, onEnd) {
  const ws = new WebSocket(`${WS_BASE}/recommend`)
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.event === 'chat') {
      onMessage(data.body)
    } else if (data.event === 'end') {
      onEnd?.()
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    onEnd?.()
  }
  
  return {
    send: (message) => {
      ws.send(JSON.stringify({ event: 'chat', body: message }))
    },
    close: () => ws.close()
  }
}
