import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 30000
})

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

// 取得設定
export async function getConfig() {
    const response = await api.get('/config')
    return response.data
}

// 更新門檻
export async function updateThresholds(market, thresholds) {
    const response = await api.put('/config/thresholds', { market, thresholds })
    return response.data
}

// 新增群組
export async function createGroup(market, name, stocks) {
    const response = await api.post('/groups', { market, name, stocks })
    return response.data
}

// 刪除群組
export async function deleteGroup(market, name) {
    const response = await api.delete(`/groups/${market}/${name}`)
    return response.data
}

export default api
