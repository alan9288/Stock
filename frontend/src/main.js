import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'
import { useAuth } from './stores/auth'

// 路由設定
const routes = [
    {
        path: '/',
        name: 'dashboard',
        component: () => import('./views/Dashboard.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/settings',
        name: 'settings',
        component: () => import('./views/Settings.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/login',
        name: 'login',
        component: () => import('./views/Login.vue'),
        meta: { guest: true }
    },
    {
        path: '/register',
        name: 'register',
        component: () => import('./views/Register.vue'),
        meta: { guest: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守衛
router.beforeEach(async (to, from, next) => {
    const { isAuthenticated, init } = useAuth()

    // 確保認證狀態已初始化
    await init()

    // 需要登入的頁面
    if (to.meta.requiresAuth && !isAuthenticated.value) {
        next('/login')
    }
    // 訪客頁面（已登入就跳轉首頁）
    else if (to.meta.guest && isAuthenticated.value) {
        next('/')
    }
    else {
        next()
    }
})

const app = createApp(App)
app.use(router)
app.mount('#app')

