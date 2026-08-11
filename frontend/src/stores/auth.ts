import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(false)
  const user = ref(null)

  const login = async (username: string, password: string) => {
    try {
      const response = await api.post('/login', { username, password })
      if (response.data.success) {
        isAuthenticated.value = true
        user.value = response.data.user
        return true
      }
      return false
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  }

  const logout = async () => {
    try {
      await api.post('/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      isAuthenticated.value = false
      user.value = null
    }
  }

  const checkAuth = async () => {
    try {
      const response = await api.get('/dashboard')
      isAuthenticated.value = response.status === 200
    } catch (error) {
      isAuthenticated.value = false
    }
  }

  return {
    isAuthenticated,
    user,
    login,
    logout,
    checkAuth
  }
})
