<template>
  <div :class="['stat-card', `stat-card-${color}`]">
    <div class="stat-icon">
      <i :class="icon"></i>
    </div>
    <div class="stat-content">
      <div class="stat-value">{{ formattedValue }}</div>
      <div class="stat-title">{{ title }}</div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'StatCard',
  props: {
    title: {
      type: String,
      required: true
    },
    value: {
      type: [Number, String],
      default: 0
    },
    icon: {
      type: String,
      default: 'fas fa-chart-bar'
    },
    color: {
      type: String,
      default: 'primary',
      validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
    }
  },
  setup(props) {
    const formattedValue = computed(() => {
      if (typeof props.value === 'number') {
        return props.value.toLocaleString()
      }
      return props.value
    })
    
    return {
      formattedValue
    }
  }
}
</script>

<style lang="scss" scoped>
.stat-card {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  }
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #333;
  line-height: 1;
  margin-bottom: 5px;
}

.stat-title {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

// Color variants
.stat-card-primary .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card-success .stat-icon {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
}

.stat-card-warning .stat-icon {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
}

.stat-card-danger .stat-icon {
  background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
}

.stat-card-info .stat-icon {
  background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%);
}

@media (max-width: 768px) {
  .stat-card {
    padding: 20px;
    gap: 15px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
    font-size: 1.2rem;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
}
</style>
