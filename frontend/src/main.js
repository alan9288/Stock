import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

// 路由設定
const routes = [
    { path: '/', name: 'dashboard', component: () => import('./views/Dashboard.vue') },
    { path: '/settings', name: 'settings', component: () => import('./views/Settings.vue') }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
