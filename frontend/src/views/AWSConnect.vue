<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-3xl font-bold text-gray-900">Connect AWS Account</h1>
    
    <div class="bg-white shadow rounded-lg p-6">
      <form @submit.prevent="handleConnect" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Profile Name</label>
          <input
            v-model="form.profile_name"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="My AWS Account"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Authentication Type</label>
          <select
            v-model="form.auth_type"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="access_key">Access Key</option>
            <option value="iam_role">IAM Role</option>
            <option value="cross_account">Cross-Account Role</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Region</label>
          <select
            v-model="form.region"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="us-east-1">US East (N. Virginia)</option>
            <option value="us-west-2">US West (Oregon)</option>
            <option value="eu-west-1">Europe (Ireland)</option>
            <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
          </select>
        </div>

        <!-- Access Key Fields -->
        <div v-if="form.auth_type === 'access_key' || form.auth_type === 'cross_account'" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Access Key ID</label>
            <input
              v-model="form.access_key"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Secret Access Key</label>
            <input
              v-model="form.secret_key"
              type="password"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        <!-- Role ARN for IAM Role and Cross-Account -->
        <div v-if="form.auth_type === 'iam_role' || form.auth_type === 'cross_account'">
          <label class="block text-sm font-medium text-gray-700 mb-2">Role ARN</label>
          <input
            v-model="form.role_arn"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            placeholder="arn:aws:iam::123456789012:role/MyRole"
          />
        </div>

        <div v-if="error" class="text-red-600 text-sm">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 rounded-md font-medium disabled:opacity-50"
        >
          {{ loading ? 'Testing Connection...' : 'Connect AWS Account' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()

const form = ref({
  profile_name: '',
  auth_type: 'access_key',
  region: 'us-east-1',
  access_key: '',
  secret_key: '',
  role_arn: ''
})

const loading = ref(false)
const error = ref('')

const handleConnect = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await api.post('/aws-connect', form.value)
    if (response.data.success) {
      router.push('/dashboard')
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Connection failed'
  } finally {
    loading.value = false
  }
}
</script>
