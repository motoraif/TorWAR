import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/styles.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// Global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err, info)
}

app.mount('#app')
