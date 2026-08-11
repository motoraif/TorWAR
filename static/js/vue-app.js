
// TorWAR Vue 3 App (Simple Build)
const { createApp, ref, reactive, computed, onMounted } = Vue;

// Main App Component
const App = {
  setup() {
    const user = ref(null);
    const recommendations = ref([]);
    const loading = ref(false);
    
    const login = async (credentials) => {
      loading.value = true;
      try {
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(credentials)
        });
        const data = await response.json();
        if (data.success) {
          user.value = data.user;
          window.showNotification('Login successful!', 'success');
        }
      } catch (error) {
        window.showNotification('Login failed!', 'error');
      } finally {
        loading.value = false;
      }
    };
    
    const fetchRecommendations = async () => {
      loading.value = true;
      try {
        const response = await fetch('/api/recommendations');
        const data = await response.json();
        recommendations.value = data.recommendations || [];
      } catch (error) {
        window.showNotification('Failed to load recommendations', 'error');
      } finally {
        loading.value = false;
      }
    };
    
    onMounted(() => {
      if (user.value) {
        fetchRecommendations();
      }
    });
    
    return {
      user,
      recommendations,
      loading,
      login,
      fetchRecommendations
    };
  },
  
  template: `
    <div id="app">
      <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
          <a class="navbar-brand" href="#">TorWAR</a>
          <button id="theme-toggle" class="theme-toggle">
            <i class="fas fa-moon"></i>
          </button>
        </div>
      </nav>
      
      <div class="container-fluid mt-4">
        <div v-if="loading" class="text-center">
          <div class="loading-spinner"></div>
          <p>Loading...</p>
        </div>
        
        <div v-else-if="!user" class="row justify-content-center">
          <div class="col-md-6">
            <div class="card">
              <div class="card-body">
                <h5 class="card-title">Login to TorWAR</h5>
                <form @submit.prevent="login({username: $refs.username.value, password: $refs.password.value})">
                  <div class="mb-3">
                    <input type="text" class="form-control" placeholder="Username" ref="username" required>
                  </div>
                  <div class="mb-3">
                    <input type="password" class="form-control" placeholder="Password" ref="password" required>
                  </div>
                  <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else>
          <div class="row">
            <div class="col-12">
              <h2>Welcome, {{ user.username }}!</h2>
              <div class="row">
                <div class="col-md-4" v-for="rec in recommendations" :key="rec._id">
                  <div class="card mb-3">
                    <div class="card-body">
                      <h6 class="card-title">{{ rec.check_name }}</h6>
                      <span :class="'badge risk-' + rec.status.toLowerCase()">{{ rec.status }}</span>
                      <p class="card-text mt-2">{{ rec.description }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
};

// Initialize Vue app
createApp(App).mount('#app');
