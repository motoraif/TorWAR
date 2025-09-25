<template>
  <div class="toast-container">
    <div 
      v-for="notification in notifications" 
      :key="notification.id"
      :class="['toast', `toast-${notification.type}`]"
    >
      <i :class="getIcon(notification.type)"></i>
      <span>{{ notification.message }}</span>
      <button @click="removeNotification(notification.id)" class="toast-close">
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useAppStore } from '../stores/app'

export default {
  name: 'NotificationToast',
  setup() {
    const appStore = useAppStore()
    
    const notifications = computed(() => appStore.notifications)
    
    const getIcon = (type) => {
      const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
      }
      return icons[type] || icons.info
    }
    
    const removeNotification = (id) => {
      appStore.removeNotification(id)
    }
    
    return {
      notifications,
      getIcon,
      removeNotification
    }
  }
}
</script>

<style lang="scss" scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease-out;
  min-width: 300px;
  
  &.toast-success {
    background: #28a745;
  }
  
  &.toast-error {
    background: #dc3545;
  }
  
  &.toast-warning {
    background: #ffc107;
    color: #333;
  }
  
  &.toast-info {
    background: #17a2b8;
  }
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 4px;
  margin-left: auto;
  
  &:hover {
    opacity: 0.8;
  }
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
