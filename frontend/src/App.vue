<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <Navbar v-if="authStore.isAuthenticated" />
    <main class="container mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import Navbar from './components/Navbar.vue'

const authStore = useAuthStore()

onMounted(() => {
  authStore.checkAuth()
})
</script>
