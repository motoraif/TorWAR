import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const isLoading = ref(false)
  const notifications = ref([])
  
  const setLoading = (loading) => {
    isLoading.value = loading
  }
  
  const addNotification = (notification) => {
    const id = Date.now()
    notifications.value.push({
      id,
      type: notification.type || 'info',
      message: notification.message,
      duration: notification.duration || 5000
    })
    
    // Auto remove notification
    setTimeout(() => {
      removeNotification(id)
    }, notification.duration || 5000)
  }
  
  const removeNotification = (id) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  return {
    isLoading,
    notifications,
    setLoading,
    addNotification,
    removeNotification
  }
})
