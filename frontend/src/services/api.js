import axios from 'axios'

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add loading state
        return config
      },
      (error) => Promise.reject(error)
    )
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('torwar_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }
  
  setAuthToken(token) {
    if (token) {
      this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete this.client.defaults.headers.common['Authorization']
    }
  }
  
  // Generic methods
  get(url, config = {}) {
    return this.client.get(url, config)
  }
  
  post(url, data = {}, config = {}) {
    return this.client.post(url, data, config)
  }
  
  put(url, data = {}, config = {}) {
    return this.client.put(url, data, config)
  }
  
  delete(url, config = {}) {
    return this.client.delete(url, config)
  }
  
  // TorWAR specific methods
  async getWorkloads() {
    const response = await this.get('/workloads')
    return response.data
  }
  
  async getWorkload(id) {
    const response = await this.get(`/workloads/${id}`)
    return response.data
  }
  
  async getReports(workloadId = null) {
    const url = workloadId ? `/reports?workload_id=${workloadId}` : '/reports'
    const response = await this.get(url)
    return response.data
  }
  
  async getReport(id) {
    const response = await this.get(`/reports/${id}`)
    return response.data
  }
  
  async deleteReport(id) {
    const response = await this.delete(`/reports/${id}`)
    return response.data
  }
  
  async compareReports(id1, id2) {
    const response = await this.get(`/reports/compare/${id1}/${id2}`)
    return response.data
  }
  
  async getRecommendations() {
    const response = await this.get('/recommendations')
    return response.data
  }
  
  async getPerformanceMetrics() {
    const response = await this.get('/performance/metrics')
    return response.data
  }
  
  async getSecurityStats() {
    const response = await this.get('/security/stats')
    return response.data
  }
}

export default new ApiService()
