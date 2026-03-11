import { defineStore } from 'pinia'
import axios from 'axios'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:9500/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const pendingAlarmCount = ref(0)

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const username = computed(() => user.value?.username || '')

  const http = axios.create({
    baseURL: API_BASE,
    timeout: 30000
  })

  http.interceptors.request.use(config => {
    if (token.value) {
      config.headers.Authorization = `Bearer ${token.value}`
    }
    return config
  })

  http.interceptors.response.use(
    response => response,
    error => {
      console.error('[API Error]', {
        method: error.config?.method,
        url: error.config?.url,
        status: error.response?.status,
        message: error.message,
        data: error.response?.data
      })

      if (error.response?.status === 401) {
        logout()
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  // 不能直接把 axios instance 返回给 Pinia：
  // axios instance 是 callable function，会被 Pinia 当作 action 包装，导致 .post/.get 丢失。
  const api = {
    request: http.request.bind(http),
    get: http.get.bind(http),
    post: http.post.bind(http),
    put: http.put.bind(http),
    delete: http.delete.bind(http),
    patch: http.patch.bind(http),
  }

  async function login(username: string, password: string) {
    const res = await api.post('/auth/login', { username, password })
    if (res.data.success) {
      token.value = res.data.access_token
      user.value = res.data.user
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      return res.data
    }
    throw new Error(res.data.message || '登录失败')
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchPendingAlarms() {
    try {
      const res = await api.get('/alarms/pending/count')
      pendingAlarmCount.value = res.data.count
    } catch (e) {
      console.error('获取待处理报警失败', e)
    }
  }

  return {
    token,
    user,
    pendingAlarmCount,
    isLoggedIn,
    userRole,
    username,
    api,
    login,
    logout,
    fetchPendingAlarms
  }
})

export default useAuthStore
