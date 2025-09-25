import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/workloads',
    name: 'Workloads',
    component: () => import('../views/Workloads.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/workloads/:id',
    name: 'WorkloadDetail',
    component: () => import('../views/WorkloadDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/Reports.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reports/:id',
    name: 'ReportDetail',
    component: () => import('../views/ReportDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/recommendations',
    name: 'Recommendations',
    component: () => import('../views/Recommendations.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ai-dashboard',
    name: 'AIDashboard',
    component: () => import('../views/AIDashboard.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
