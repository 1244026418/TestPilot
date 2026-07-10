import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('testpilot_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('testpilot_token')
      localStorage.removeItem('testpilot_user')
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) return error.response?.data?.detail || error.message
  return error instanceof Error ? error.message : '操作失败'
}

export default client
