import axios from 'axios'

// 根據環境設定 API 基礎 URL
// 生產環境判斷：如果不是 localhost，則使用 Railway 後端
const isProduction = typeof window !== 'undefined' && !window.location.hostname.includes('localhost')
const API_BASE_URL = isProduction
    ? 'https://stock-production-c537.up.railway.app/api'
    : (import.meta.env.VITE_API_URL || '/api')

console.log('API Base URL:', API_BASE_URL)

const api = axios.create({
    baseURL: API_BASE_URL,
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
// 回應攔截器：處理認證錯誤、網路錯誤、驗證錯誤
// ==========================================
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // 網路錯誤（無 response）
        if (!error.response) {
            console.error('網路連線失敗:', error.message)
            error.friendlyMessage = '網路連線失敗，請檢查網路狀態'
            return Promise.reject(error)
        }

        const status = error.response.status
        const data = error.response.data

        // 401 未授權：Token 過期或無效
        if (status === 401) {
            const isAuthRequest = error.config?.url?.includes('/auth/')
            if (!isAuthRequest) {
                localStorage.removeItem('token')
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login'
                }
            }
        }

        // 422 驗證錯誤：解析 Pydantic 錯誤訊息
        if (status === 422 && data?.detail) {
            // Pydantic 驗證錯誤格式：[{loc: [...], msg: "...", type: "..."}]
            if (Array.isArray(data.detail)) {
                const messages = data.detail.map(err => {
                    const field = err.loc?.slice(1).join('.') || '欄位'
                    return `${field}: ${err.msg}`
                })
                error.response.data.detail = messages.join('\n')
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

// 取得股票歷史資料（用於走勢圖）
export async function getStockHistory(symbol, market = 'US', period = '1d') {
    const response = await api.get(`/stocks/${symbol}/history?market=${market}&period=${period}`)
    return response.data
}

// ==========================================
// 持股管理 API
// ==========================================

// 取得所有持股
export async function getHoldings() {
    const response = await api.get('/holdings')
    return response.data
}

// 新增持股
export async function createHolding(data) {
    const response = await api.post('/holdings', data)
    return response.data
}

// 新增補倉記錄
export async function addTransaction(holdingId, data) {
    const response = await api.post(`/holdings/${holdingId}/transactions`, data)
    return response.data
}

// 取得交易記錄
export async function getTransactions(holdingId) {
    const response = await api.get(`/holdings/${holdingId}/transactions`)
    return response.data
}

// 刪除持股
export async function deleteHolding(holdingId) {
    const response = await api.delete(`/holdings/${holdingId}`)
    return response.data
}

// 刪除交易記錄
export async function deleteTransaction(holdingId, transactionId) {
    const response = await api.delete(`/holdings/${holdingId}/transactions/${transactionId}`)
    return response.data
}

export default api
