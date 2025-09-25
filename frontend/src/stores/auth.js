import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('torwar_token'))
  
  const isAuthenticated = computed(() => !!token.value)
  
  const login = async (credentials) => {
    try {
      const response = await api.post('/auth/token', credentials)
      token.value = response.data.token
      user.value = response.data.user_data
      
      localStorage.setItem('torwar_token', token.value)
      api.setAuthToken(token.value)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      }
    }
  }
  
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('torwar_token')
    api.setAuthToken(null)
  }
  
  const checkAuth = async () => {
    if (!token.value) return false
    
    try {
      api.setAuthToken(token.value)
      const response = await api.get('/auth/sessions')
      return true
    } catch (error) {
      logout()
      return false
    }
  }
  
  // Initialize auth on store creation
  if (token.value) {
    api.setAuthToken(token.value)
  }
  
  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    checkAuth
  }
})
