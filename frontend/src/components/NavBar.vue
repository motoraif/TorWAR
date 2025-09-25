<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/" class="nav-brand">
        <i class="fas fa-shield-alt"></i>
        TorWAR
      </router-link>
      
      <div class="nav-menu" :class="{ active: isMenuOpen }">
        <router-link to="/" class="nav-link">Dashboard</router-link>
        <router-link to="/workloads" class="nav-link" v-if="isAuthenticated">Workloads</router-link>
        <router-link to="/reports" class="nav-link" v-if="isAuthenticated">Reports</router-link>
        <router-link to="/recommendations" class="nav-link" v-if="isAuthenticated">Recommendations</router-link>
        <router-link to="/ai-dashboard" class="nav-link" v-if="isAuthenticated">AI Dashboard</router-link>
        
        <div class="nav-auth">
          <button v-if="!isAuthenticated" @click="$router.push('/login')" class="btn-login">
            Login
          </button>
          <div v-else class="user-menu">
            <span class="user-info">{{ userInfo }}</span>
            <button @click="logout" class="btn-logout">
              <i class="fas fa-sign-out-alt"></i>
            </button>
          </div>
        </div>
      </div>
      
      <button class="nav-toggle" @click="toggleMenu">
        <i class="fas fa-bars"></i>
      </button>
    </div>
  </nav>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'NavBar',
  setup() {
    const authStore = useAuthStore()
    const isMenuOpen = ref(false)
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const userInfo = computed(() => {
      return authStore.user?.user_id || 'User'
    })
    
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value
    }
    
    const logout = () => {
      authStore.logout()
      isMenuOpen.value = false
    }
    
    return {
      isMenuOpen,
      isAuthenticated,
      userInfo,
      toggleMenu,
      logout
    }
  }
}
</script>

<style lang="scss" scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
  
  &:hover, &.router-link-active {
    background-color: rgba(255,255,255,0.2);
  }
}

.nav-auth {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-login, .btn-logout {
  background: rgba(255,255,255,0.2);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  
  &:hover {
    background: rgba(255,255,255,0.3);
  }
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-info {
  font-size: 0.9rem;
  opacity: 0.9;
}

.nav-toggle {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
}

@media (max-width: 768px) {
  .nav-toggle {
    display: block;
  }
  
  .nav-menu {
    position: absolute;
    top: 60px;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    flex-direction: column;
    padding: 20px;
    transform: translateY(-100%);
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s;
    
    &.active {
      transform: translateY(0);
      opacity: 1;
      visibility: visible;
    }
  }
  
  .nav-link {
    width: 100%;
    text-align: center;
    padding: 12px;
  }
}
</style>
