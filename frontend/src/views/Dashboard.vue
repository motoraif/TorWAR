<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
      <div class="space-x-2">
        <button 
          v-if="stats.recommendations > 0"
          class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md"
        >
          Generate Report
        </button>
        <router-link 
          to="/aws-connect"
          class="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md"
        >
          Add AWS Connection
        </router-link>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">AWS Connections</dt>
                <dd class="text-lg font-medium text-gray-900">{{ stats.connections }}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 01-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15 13.586V12a1 1 0 011-1z" clip-rule="evenodd"/>
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Recommendations</dt>
                <dd class="text-lg font-medium text-gray-900">{{ stats.recommendations }}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">Actions Needed</dt>
                <dd class="text-lg font-medium text-gray-900">{{ stats.warnings }}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">AWS Connections</h3>
          <div v-if="connections.length > 0" class="space-y-3">
            <div 
              v-for="conn in connections" 
              :key="conn.id"
              class="flex justify-between items-center p-3 border rounded-lg"
            >
              <div>
                <p class="font-medium">{{ conn.profile_name }}</p>
                <p class="text-sm text-gray-500">{{ conn.region }} • {{ conn.auth_type }}</p>
              </div>
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Active
              </span>
            </div>
          </div>
          <div v-else class="text-center py-4">
            <p class="text-gray-500">No AWS connections configured.</p>
            <router-link 
              to="/aws-connect"
              class="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200"
            >
              Add Connection
            </router-link>
          </div>
        </div>
      </div>

      <div class="bg-white shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg leading-6 font-medium text-gray-900">Recent Recommendations</h3>
            <button 
              v-if="connections.length > 0"
              @click="syncRecommendations"
              :disabled="syncing"
              class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 disabled:opacity-50"
            >
              {{ syncing ? 'Syncing...' : 'Sync' }}
            </button>
          </div>
          
          <div v-if="recommendations.length > 0" class="space-y-3">
            <div 
              v-for="rec in recommendations.slice(0, 5)" 
              :key="rec.id"
              class="flex justify-between items-center p-3 border rounded-lg"
            >
              <div>
                <p class="font-medium">{{ rec.name.substring(0, 30) }}...</p>
                <p class="text-sm text-gray-500">{{ rec.category }}</p>
              </div>
              <span 
                :class="getStatusClass(rec.status)"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              >
                {{ rec.status.toUpperCase() }}
              </span>
            </div>
            <router-link 
              to="/recommendations"
              class="block text-center text-sm text-primary-600 hover:text-primary-500"
            >
              View All Recommendations
            </router-link>
          </div>
          <div v-else class="text-center py-4">
            <p class="text-gray-500">No recommendations available.</p>
            <button 
              v-if="connections.length > 0"
              @click="syncRecommendations"
              :disabled="syncing"
              class="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-primary-700 bg-primary-100 hover:bg-primary-200 disabled:opacity-50"
            >
              {{ syncing ? 'Syncing...' : 'Sync Recommendations' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../services/api'

const stats = ref({
  connections: 0,
  recommendations: 0,
  warnings: 0
})

const connections = ref([])
const recommendations = ref([])
const syncing = ref(false)

const loadDashboardData = async () => {
  try {
    const response = await api.get('/dashboard')
    // Parse HTML response to extract data (temporary until API is updated)
    stats.value.connections = response.data.connections?.length || 0
    stats.value.recommendations = response.data.recommendations?.length || 0
    stats.value.warnings = response.data.recommendations?.filter((r: any) => r.status === 'warning').length || 0
    
    connections.value = response.data.connections || []
    recommendations.value = response.data.recommendations || []
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

const syncRecommendations = async () => {
  syncing.value = true
  try {
    const response = await api.post('/sync-recommendations')
    if (response.data.success) {
      await loadDashboardData()
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

onMounted(() => {
  loadDashboardData()
})
</script>
