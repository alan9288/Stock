/**
 * 認證狀態管理
 * 使用 Vue Composition API 實現簡單的狀態管理
 */

import { ref, computed } from 'vue'
import api from '../api'

// 狀態
const user = ref(null)
const token = ref(localStorage.getItem('token') || null)
const loading = ref(false)
const error = ref(null)

// 計算屬性
const isAuthenticated = computed(() => !!token.value && !!user.value)

/**
 * 設定認證 Token
 */
function setToken(newToken) {
    token.value = newToken
    if (newToken) {
        localStorage.setItem('token', newToken)
        api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
    } else {
        localStorage.removeItem('token')
        delete api.defaults.headers.common['Authorization']
    }
}

/**
 * 註冊
 */
async function register(email, password, name = null) {
    loading.value = true
    error.value = null

    try {
        const response = await api.post('/auth/register', { email, password, name })
        const data = response.data

        setToken(data.access_token)
        user.value = data.user

        return { success: true }
    } catch (err) {
        error.value = err.response?.data?.detail || '註冊失敗'
        return { success: false, error: error.value }
    } finally {
        loading.value = false
    }
}

/**
 * 登入
 */
async function login(email, password) {
    loading.value = true
    error.value = null

    try {
        // 使用 URLSearchParams 符合 OAuth2 規範
        const params = new URLSearchParams()
        params.append('username', email)
        params.append('password', password)

        const response = await api.post('/auth/login', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
        const data = response.data

        setToken(data.access_token)
        user.value = data.user

        return { success: true }
    } catch (err) {
        error.value = err.response?.data?.detail || '登入失敗'
        return { success: false, error: error.value }
    } finally {
        loading.value = false
    }
}

/**
 * 登出
 */
function logout() {
    setToken(null)
    user.value = null
}

/**
 * 取得當前使用者
 */
async function fetchUser() {
    if (!token.value) return

    loading.value = true
    try {
        // 確保 Token 有設定到 Header
        api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`

        const response = await api.get('/auth/me')
        user.value = response.data
    } catch (err) {
        // Token 無效，清除
        logout()
    } finally {
        loading.value = false
    }
}

/**
 * 初始化認證狀態（應用程式啟動時呼叫）
 */
async function init() {
    if (token.value) {
        await fetchUser()
    }
}

// 導出
export function useAuth() {
    return {
        user,
        token,
        loading,
        error,
        isAuthenticated,
        register,
        login,
        logout,
        fetchUser,
        init
    }
}
