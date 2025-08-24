import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
const USER_API_URL = import.meta.env.VITE_USER_API_URL || 'http://localhost:8001'
const TRADING_API_URL = import.meta.env.VITE_TRADING_API_URL || 'http://localhost:8002'
const EXCHANGE_API_URL = import.meta.env.VITE_EXCHANGE_API_URL || 'http://localhost:8003'
const ORDER_API_URL = import.meta.env.VITE_ORDER_API_URL || 'http://localhost:8006'
const MONITORING_API_URL = import.meta.env.VITE_MONITORING_API_URL || 'http://localhost:8009'
const API_TIMEOUT = 30000

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求ID用于追踪
    config.headers['X-Request-ID'] = generateRequestId()
    
    console.log('API Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      data: config.data,
      params: config.params
    })
    
    return config
  },
  (error) => {
    console.error('Request Error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('API Response:', {
      status: response.status,
      url: response.config.url,
      data: response.data
    })
    
    return response
  },
  (error) => {
    console.error('Response Error:', error)
    
    // 处理不同的错误状态
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          message.error('登录已过期，请重新登录')
          break
          
        case 403:
          message.error('权限不足，无法访问该资源')
          break
          
        case 404:
          message.error('请求的资源不存在')
          break
          
        case 422:
          // 验证错误
          if (data.detail && Array.isArray(data.detail)) {
            const errorMessages = data.detail.map((err: any) => err.msg).join(', ')
            message.error(`参数验证失败: ${errorMessages}`)
          } else {
            message.error(data.message || '参数验证失败')
          }
          break
          
        case 429:
          message.error('请求过于频繁，请稍后再试')
          break
          
        case 500:
          message.error('服务器内部错误，请稍后再试')
          break
          
        case 502:
        case 503:
        case 504:
          message.error('服务暂时不可用，请稍后再试')
          break
          
        default:
          message.error(data.message || `请求失败 (${status})`)
      }
    } else if (error.request) {
      // 网络错误
      message.error('网络连接失败，请检查网络设置')
    } else {
      // 其他错误
      message.error('请求发生未知错误')
    }
    
    return Promise.reject(error)
  }
)

// 生成请求ID
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
  request_id: string
}

// 分页响应类型
export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// 通用API方法
export class ApiService {
  // GET请求
  static async get<T = any>(
    url: string, 
    params?: Record<string, any>, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await api.get(url, { params, ...config })
    return response.data
  }
  
  // POST请求
  static async post<T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await api.post(url, data, config)
    return response.data
  }
  
  // PUT请求
  static async put<T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await api.put(url, data, config)
    return response.data
  }
  
  // PATCH请求
  static async patch<T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await api.patch(url, data, config)
    return response.data
  }
  
  // DELETE请求
  static async delete<T = any>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await api.delete(url, config)
    return response.data
  }
  
  // 文件上传
  static async upload<T = any>(
    url: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
    
    return response.data
  }
  
  // 文件下载
  static async download(
    url: string, 
    filename?: string, 
    params?: Record<string, any>
  ): Promise<void> {
    const response = await api.get(url, {
      params,
      responseType: 'blob'
    })
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    
    // 设置文件名
    if (filename) {
      link.download = filename
    } else {
      // 从响应头获取文件名
      const contentDisposition = response.headers['content-disposition']
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch) {
          link.download = filenameMatch[1]
        }
      }
    }
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
}

// 创建不同服务的API实例
const userApi = axios.create({
  baseURL: USER_API_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

const tradingApi = axios.create({
  baseURL: TRADING_API_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

const exchangeApi = axios.create({
  baseURL: EXCHANGE_API_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

const orderApi = axios.create({
  baseURL: ORDER_API_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

const monitoringApi = axios.create({
  baseURL: MONITORING_API_URL,
  timeout: API_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

// 拦截器配置函数
const setupInterceptors = (apiInstance: any) => {
  // 请求拦截器
  apiInstance.interceptors.request.use(
    (config: any) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      config.headers['X-Request-ID'] = generateRequestId()
      return config
    },
    (error: any) => Promise.reject(error)
  )

  // 响应拦截器
  apiInstance.interceptors.response.use(
    (response: any) => response,
    (error: any) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        message.error('登录已过期，请重新登录')
      }
      return Promise.reject(error)
    }
  )
}

// 为所有API实例添加拦截器
setupInterceptors(userApi)
setupInterceptors(tradingApi)
setupInterceptors(exchangeApi)
setupInterceptors(orderApi)
setupInterceptors(monitoringApi)

// 具体业务API服务

// 用户服务
export class UserService {
  // 登录
  static async login(email: string, password: string) {
    const response = await userApi.post('/auth/login', { email, password })
    return response.data
  }
  
  // 注册
  static async register(userData: {
    email: string
    password: string
    username: string
    invite_code?: string
  }) {
    const response = await userApi.post('/auth/register', userData)
    return response.data
  }
  
  // 获取用户信息
  static async getUserProfile() {
    const response = await userApi.get('/users/profile')
    return response.data
  }
  
  // 更新用户信息
  static async updateUserProfile(userData: any) {
    const response = await userApi.put('/users/profile', userData)
    return response.data
  }
  
  // 修改密码
  static async changePassword(oldPassword: string, newPassword: string) {
    const response = await userApi.post('/users/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  }
}

// 策略服务
export class StrategyService {
  // 获取策略列表
  static async getStrategies(params?: {
    page?: number
    size?: number
    status?: string
    type?: string
  }) {
    const response = await tradingApi.get('/strategies', { params })
    return response.data
  }
  
  // 获取策略详情
  static async getStrategy(id: string) {
    const response = await tradingApi.get(`/strategies/${id}`)
    return response.data
  }
  
  // 创建策略
  static async createStrategy(strategyData: any) {
    const response = await tradingApi.post('/strategies', strategyData)
    return response.data
  }
  
  // 更新策略
  static async updateStrategy(id: string, strategyData: any) {
    const response = await tradingApi.put(`/strategies/${id}`, strategyData)
    return response.data
  }
  
  // 删除策略
  static async deleteStrategy(id: string) {
    const response = await tradingApi.delete(`/strategies/${id}`)
    return response.data
  }
  
  // 启动策略
  static async startStrategy(id: string) {
    const response = await tradingApi.post(`/strategies/${id}/start`)
    return response.data
  }
  
  // 停止策略
  static async stopStrategy(id: string) {
    const response = await tradingApi.post(`/strategies/${id}/stop`)
    return response.data
  }
  
  // 回测策略
  static async backtestStrategy(id: string, params: {
    start_date: string
    end_date: string
    initial_capital: number
  }) {
    const response = await tradingApi.post(`/strategies/${id}/backtest`, params)
    return response.data
  }
}

// 交易服务
export class TradingService {
  // 获取账户余额
  static async getBalance() {
    const response = await tradingApi.get('/balance')
    return response.data
  }
  
  // 获取持仓
  static async getPositions() {
    const response = await tradingApi.get('/positions')
    return response.data
  }
  
  // 获取订单
  static async getOrders(params?: {
    status?: string
    symbol?: string
    page?: number
    size?: number
  }) {
    const response = await orderApi.get('/orders', { params })
    return response.data
  }
  
  // 创建订单
  static async createOrder(orderData: {
    symbol: string
    side: 'buy' | 'sell'
    type: 'market' | 'limit'
    quantity: number
    price?: number
  }) {
    const response = await orderApi.post('/orders', orderData)
    return response.data
  }
  
  // 取消订单
  static async cancelOrder(orderId: string) {
    const response = await orderApi.delete(`/orders/${orderId}`)
    return response.data
  }
  
  // 平仓
  static async closePosition(positionId: string) {
    const response = await tradingApi.post(`/positions/${positionId}/close`)
    return response.data
  }
  
  // 获取交易历史
  static async getTradeHistory(params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    size?: number
  }) {
    const response = await tradingApi.get('/trades', { params })
    return response.data
  }
}

// 市场数据服务
export class MarketService {
  // 获取市场数据
  static async getMarketData(params?: {
    symbols?: string[]
    interval?: string
  }) {
    const response = await exchangeApi.get('/market/data', { params })
    return response.data
  }
  
  // 获取K线数据
  static async getKlineData(symbol: string, interval: string, limit?: number) {
    const response = await exchangeApi.get(`/market/klines/${symbol}`, {
      params: { interval, limit }
    })
    return response.data
  }
  
  // 获取技术指标
  static async getIndicators(symbol: string, indicator: string, params?: any) {
    const response = await exchangeApi.get(`/market/indicators/${symbol}/${indicator}`, { params })
    return response.data
  }
}

// 风险管理服务
export class RiskService {
  // 获取风险指标
  static async getRiskMetrics() {
    const response = await monitoringApi.get('/risk/metrics')
    return response.data
  }
  
  // 获取风险预警
  static async getRiskAlerts(params?: {
    level?: string
    status?: string
    page?: number
    size?: number
  }) {
    const response = await monitoringApi.get('/risk/alerts', { params })
    return response.data
  }
  
  // 更新风险设置
  static async updateRiskSettings(settings: any) {
    const response = await monitoringApi.put('/risk/settings', settings)
    return response.data
  }
}

// 通知服务
export class NotificationService {
  // 获取通知列表
  static async getNotifications(params?: {
    type?: string
    status?: string
    page?: number
    size?: number
  }) {
    const response = await monitoringApi.get('/notifications', { params })
    return response.data
  }
  
  // 标记通知为已读
  static async markAsRead(notificationIds: string[]) {
    const response = await monitoringApi.post('/notifications/mark-read', {
      notification_ids: notificationIds
    })
    return response.data
  }
  
  // 删除通知
  static async deleteNotifications(notificationIds: string[]) {
    const response = await monitoringApi.post('/notifications/delete', {
      notification_ids: notificationIds
    })
    return response.data
  }
  
  // 发送自定义通知
  static async sendNotification(notificationData: {
    title: string
    content: string
    type: string
    recipients?: string[]
  }) {
    const response = await monitoringApi.post('/notifications/send', notificationData)
    return response.data
  }
}

export default api