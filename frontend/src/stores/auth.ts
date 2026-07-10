import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import client from '../api/client'
import type { User } from '../types'

interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('testpilot_token') || '')
  const savedUser = localStorage.getItem('testpilot_user')
  const user = ref<User | null>(savedUser ? JSON.parse(savedUser) : null)
  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const isAdmin = computed(() => user.value?.role === 'admin')

  function saveAuth(data: AuthResponse) {
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('testpilot_token', data.access_token)
    localStorage.setItem('testpilot_user', JSON.stringify(data.user))
  }

  async function login(username: string, password: string) {
    const { data } = await client.post<AuthResponse>('/auth/login', { username, password })
    saveAuth(data)
  }

  async function register(username: string, password: string) {
    const { data } = await client.post<AuthResponse>('/auth/register', { username, password })
    saveAuth(data)
  }

  async function refreshUser() {
    if (!token.value) return
    const { data } = await client.get<User>('/auth/me')
    user.value = data
    localStorage.setItem('testpilot_user', JSON.stringify(data))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('testpilot_token')
    localStorage.removeItem('testpilot_user')
  }

  return { token, user, isAuthenticated, isAdmin, login, register, refreshUser, logout }
})
