<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>TorWAR Dashboard</h1>
      <p class="subtitle">AWS Well-Architected Review Tool</p>
    </div>
    
    <div class="stats-grid" v-if="isAuthenticated">
      <StatCard 
        title="Workloads" 
        :value="stats.workloads" 
        icon="fas fa-building"
        color="primary"
      />
      <StatCard 
        title="Reports" 
        :value="stats.reports" 
        icon="fas fa-file-alt"
        color="success"
      />
      <StatCard 
        title="Recommendations" 
        :value="stats.recommendations" 
        icon="fas fa-lightbulb"
        color="warning"
      />
      <StatCard 
        title="High Priority Issues" 
        :value="stats.highPriority" 
        icon="fas fa-exclamation-triangle"
        color="danger"
      />
    </div>
    
    <div class="dashboard-content">
      <div class="welcome-card" v-if="!isAuthenticated">
        <h2>Welcome to TorWAR</h2>
        <p>Your comprehensive AWS Well-Architected Review Tool</p>
        <router-link to="/login" class="btn btn-primary">
          Get Started
        </router-link>
      </div>
      
      <div class="dashboard-widgets" v-else>
        <div class="widget">
          <h3>Recent Reports</h3>
          <ReportList :reports="recentReports" :limit="5" />
        </div>
        
        <div class="widget">
          <h3>System Performance</h3>
          <PerformanceChart :data="performanceData" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'
import StatCard from '../components/StatCard.vue'
import ReportList from '../components/ReportList.vue'
import PerformanceChart from '../components/PerformanceChart.vue'

export default {
  name: 'Dashboard',
  components: {
    StatCard,
    ReportList,
    PerformanceChart
  },
  setup() {
    const authStore = useAuthStore()
    const stats = ref({
      workloads: 0,
      reports: 0,
      recommendations: 0,
      highPriority: 0
    })
    const recentReports = ref([])
    const performanceData = ref({})
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    
    const loadDashboardData = async () => {
      if (!isAuthenticated.value) return
      
      try {
        // Load stats
        const [workloads, reports, performance] = await Promise.all([
          api.getWorkloads(),
          api.getReports(),
          api.getPerformanceMetrics()
        ])
        
        stats.value = {
          workloads: workloads.length,
          reports: reports.length,
          recommendations: 0, // Will be loaded from recommendations API
          highPriority: reports.filter(r => r.risk_summary?.HIGH > 0).length
        }
        
        recentReports.value = reports.slice(0, 5)
        performanceData.value = performance
        
      } catch (error) {
        console.error('Error loading dashboard data:', error)
      }
    }
    
    onMounted(() => {
      loadDashboardData()
    })
    
    return {
      isAuthenticated,
      stats,
      recentReports,
      performanceData
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 40px;
  
  h1 {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 10px;
  }
  
  .subtitle {
    font-size: 1.2rem;
    color: #666;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 60px 40px;
  border-radius: 12px;
  text-align: center;
  
  h2 {
    font-size: 2rem;
    margin-bottom: 15px;
  }
  
  p {
    font-size: 1.1rem;
    margin-bottom: 30px;
    opacity: 0.9;
  }
}

.dashboard-widgets {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.widget {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  
  h3 {
    margin-bottom: 20px;
    color: #333;
  }
}

.btn {
  display: inline-block;
  padding: 12px 24px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
  
  &.btn-primary {
    background: white;
    color: #667eea;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
  }
}

@media (max-width: 768px) {
  .dashboard-widgets {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
