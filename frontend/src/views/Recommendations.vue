<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900">Trusted Advisor Recommendations</h1>
      <button 
        @click="syncRecommendations"
        :disabled="syncing"
        class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md disabled:opacity-50"
      >
        {{ syncing ? 'Syncing...' : 'Sync Recommendations' }}
      </button>
    </div>

    <!-- Filters -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <input
        v-model="filters.search"
        type="text"
        placeholder="Search recommendations..."
        class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
      />
      <select
        v-model="filters.category"
        class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
      >
        <option value="">All Categories</option>
        <option value="cost_optimizing">Cost Optimization</option>
        <option value="security">Security</option>
        <option value="performance">Performance</option>
        <option value="fault_tolerance">Fault Tolerance</option>
      </select>
      <select
        v-model="filters.status"
        class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
      >
        <option value="">All Status</option>
        <option value="ok">OK</option>
        <option value="warning">Warning</option>
        <option value="error">Error</option>
      </select>
    </div>

    <!-- Recommendations Grid -->
    <div v-if="filteredRecommendations.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="rec in filteredRecommendations" 
        :key="rec.id"
        class="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
      >
        <div class="p-4">
          <div class="flex justify-between items-start mb-2">
            <h3 class="text-sm font-medium text-gray-500">{{ rec.category.replace('_', ' ').toUpperCase() }}</h3>
            <span 
              :class="getStatusClass(rec.status)"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
            >
              {{ rec.status.toUpperCase() }}
            </span>
          </div>
          <h4 class="text-lg font-semibold text-gray-900 mb-2">{{ rec.name }}</h4>
          <p class="text-gray-600 text-sm mb-4">{{ rec.description?.substring(0, 100) }}...</p>
          <div class="flex justify-between items-center">
            <span class="text-xs text-gray-500">
              {{ formatDate(rec.created_at) }}
            </span>
            <button class="text-primary-600 hover:text-primary-500 text-sm font-medium">
              View Details
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="text-center py-12">
      <div class="text-gray-400 mb-4">
        <svg class="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No Recommendations Available</h3>
      <p class="text-gray-500 mb-4">Connect to AWS and sync your Trusted Advisor recommendations to get started.</p>
      <div class="space-x-2">
        <router-link 
          to="/aws-connect"
          class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md"
        >
          Connect AWS
        </router-link>
        <button 
          @click="syncRecommendations"
          :disabled="syncing"
          class="bg-gray-200 hover:bg-gray-300 text-gray-900 px-4 py-2 rounded-md disabled:opacity-50"
        >
          {{ syncing ? 'Syncing...' : 'Sync Now' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
      <p class="mt-4 text-gray-500">Loading recommendations...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

const recommendations = ref([])
const loading = ref(false)
const syncing = ref(false)

const filters = ref({
  search: '',
  category: '',
  status: ''
})

const filteredRecommendations = computed(() => {
  return recommendations.value.filter((rec: any) => {
    const matchesSearch = !filters.value.search || 
      rec.name.toLowerCase().includes(filters.value.search.toLowerCase())
    const matchesCategory = !filters.value.category || rec.category === filters.value.category
    const matchesStatus = !filters.value.status || rec.status === filters.value.status
    
    return matchesSearch && matchesCategory && matchesStatus
  })
})

const loadRecommendations = async () => {
  loading.value = true
  try {
    const response = await api.get('/recommendations')
    recommendations.value = response.data.recommendations || []
  } catch (error) {
    console.error('Failed to load recommendations:', error)
  } finally {
    loading.value = false
  }
}

const syncRecommendations = async () => {
  syncing.value = true
  try {
    const response = await api.post('/sync-recommendations')
    if (response.data.success) {
      await loadRecommendations()
    }
  } catch (error) {
    console.error('Sync failed:', error)
  } finally {
    syncing.value = false
  }
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'ok': return 'bg-green-100 text-green-800'
    case 'warning': return 'bg-yellow-100 text-yellow-800'
    case 'error': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

onMounted(() => {
  loadRecommendations()
})
</script>
