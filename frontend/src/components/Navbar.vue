<template>
  <nav class="bg-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <router-link to="/dashboard" class="text-xl font-bold text-primary-600">
            TorWAR
          </router-link>
        </div>
        
        <div class="flex items-center space-x-4">
          <router-link 
            to="/dashboard" 
            class="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md"
          >
            Dashboard
          </router-link>
          <router-link 
            to="/recommendations" 
            class="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md"
          >
            Recommendations
          </router-link>
          <router-link 
            to="/aws-connect" 
            class="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md"
          >
            AWS Connect
          </router-link>
          <button 
            @click="handleLogout"
            class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
