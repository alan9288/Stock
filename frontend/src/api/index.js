import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 30000
})

// ==========================================
// 請求攔截器：自動附帶 Authorization Token
// ==========================================
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// ==========================================
// 回應攔截器：處理認證錯誤
// ==========================================
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // 401 未授權：Token 過期或無效
        if (error.response?.status === 401) {
            const isAuthRequest = error.config?.url?.includes('/auth/')
            if (!isAuthRequest) {
                localStorage.removeItem('token')
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login'
                }
            }
        }
        return Promise.reject(error)
    }
)

// ==========================================
// API 函式
// ==========================================

// 取得市場狀態
export async function getMarketStatus() {
    const response = await api.get('/market-status')
    return response.data
}

// 取得所有股票數據
export async function getStocks() {
    const response = await api.get('/stocks')
    return response.data
}

// 驗證股票代號是否有效
export async function validateStock(symbol, market = 'US') {
    const response = await api.get(`/validate-stock/${symbol}?market=${market}`)
    return response.data
}

// 取得股票歷史資料（用於走勢圖）
export async function getStockHistory(symbol, market = 'US', period = '1d') {
    const response = await api.get(`/stocks/${symbol}/history?market=${market}&period=${period}`)
    return response.data
}

export default api
