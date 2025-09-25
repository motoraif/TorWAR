<template>
  <div id="app">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
    <LoadingSpinner v-if="isLoading" />
    <NotificationToast />
  </div>
</template>

<script>
import { computed } from 'vue'
import { useAppStore } from './stores/app'
import NavBar from './components/NavBar.vue'
import LoadingSpinner from './components/LoadingSpinner.vue'
import NotificationToast from './components/NotificationToast.vue'

export default {
  name: 'App',
  components: {
    NavBar,
    LoadingSpinner,
    NotificationToast
  },
  setup() {
    const appStore = useAppStore()
    
    const isLoading = computed(() => appStore.isLoading)
    
    return {
      isLoading
    }
  }
}
</script>

<style lang="scss">
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

@media (max-width: 768px) {
  .main-content {
    padding: 10px;
  }
}
</style>
