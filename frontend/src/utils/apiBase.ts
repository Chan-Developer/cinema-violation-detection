const DEFAULT_API_BASE = 'http://localhost:9500/api'

export const getApiBase = () => {
  const configured = import.meta.env.VITE_API_BASE
  if (configured) return configured

  if (typeof window !== 'undefined' && window.location.origin) {
    return `${window.location.origin}/api`
  }

  return DEFAULT_API_BASE
}

export const getApiOrigin = () => getApiBase().replace(/\/api\/?$/, '')
