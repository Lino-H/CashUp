import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// API基础配置
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'
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

// 具体业务API服务

// 用户服务
export class UserService {
  // 登录
  static async login(email: string, password: string) {
    return ApiService.post('/api/v1/auth/login', { email, password })
  }
  
  // 注册
  static async register(userData: {
    email: string
    password: string
    username: string
    invite_code?: string
  }) {
    return ApiService.post('/api/v1/auth/register', userData)
  }
  
  // 获取用户信息
  static async getUserProfile() {
    return ApiService.get('/api/v1/users/profile')
  }
  
  // 更新用户信息
  static async updateUserProfile(userData: any) {
    return ApiService.put('/api/v1/users/profile', userData)
  }
  
  // 修改密码
  static async changePassword(oldPassword: string, newPassword: string) {
    return ApiService.post('/api/v1/users/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
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
    return ApiService.get('/api/v1/strategies', params)
  }
  
  // 获取策略详情
  static async getStrategy(id: string) {
    return ApiService.get(`/api/v1/strategies/${id}`)
  }
  
  // 创建策略
  static async createStrategy(strategyData: any) {
    return ApiService.post('/api/v1/strategies', strategyData)
  }
  
  // 更新策略
  static async updateStrategy(id: string, strategyData: any) {
    return ApiService.put(`/api/v1/strategies/${id}`, strategyData)
  }
  
  // 删除策略
  static async deleteStrategy(id: string) {
    return ApiService.delete(`/api/v1/strategies/${id}`)
  }
  
  // 启动策略
  static async startStrategy(id: string) {
    return ApiService.post(`/api/v1/strategies/${id}/start`)
  }
  
  // 停止策略
  static async stopStrategy(id: string) {
    return ApiService.post(`/api/v1/strategies/${id}/stop`)
  }
  
  // 回测策略
  static async backtestStrategy(id: string, params: {
    start_date: string
    end_date: string
    initial_capital: number
  }) {
    return ApiService.post(`/api/v1/strategies/${id}/backtest`, params)
  }
}

// 交易服务
export class TradingService {
  // 获取账户余额
  static async getBalance() {
    return ApiService.get('/api/v1/trading/balance')
  }
  
  // 获取持仓
  static async getPositions() {
    return ApiService.get('/api/v1/trading/positions')
  }
  
  // 获取订单
  static async getOrders(params?: {
    status?: string
    symbol?: string
    page?: number
    size?: number
  }) {
    return ApiService.get('/api/v1/trading/orders', params)
  }
  
  // 创建订单
  static async createOrder(orderData: {
    symbol: string
    side: 'buy' | 'sell'
    type: 'market' | 'limit'
    quantity: number
    price?: number
  }) {
    return ApiService.post('/api/v1/trading/orders', orderData)
  }
  
  // 取消订单
  static async cancelOrder(orderId: string) {
    return ApiService.delete(`/api/v1/trading/orders/${orderId}`)
  }
  
  // 平仓
  static async closePosition(positionId: string) {
    return ApiService.post(`/api/v1/trading/positions/${positionId}/close`)
  }
  
  // 获取交易历史
  static async getTradeHistory(params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    size?: number
  }) {
    return ApiService.get('/api/v1/trading/trades', params)
  }
}

// 市场数据服务
export class MarketService {
  // 获取市场数据
  static async getMarketData(params?: {
    symbols?: string[]
    interval?: string
  }) {
    return ApiService.get('/api/v1/market/data', params)
  }
  
  // 获取K线数据
  static async getKlineData(symbol: string, interval: string, limit?: number) {
    return ApiService.get(`/api/v1/market/klines/${symbol}`, {
      interval,
      limit
    })
  }
  
  // 获取技术指标
  static async getIndicators(symbol: string, indicator: string, params?: any) {
    return ApiService.get(`/api/v1/market/indicators/${symbol}/${indicator}`, params)
  }
}

// 风险管理服务
export class RiskService {
  // 获取风险指标
  static async getRiskMetrics() {
    return ApiService.get('/api/v1/risk/metrics')
  }
  
  // 获取风险预警
  static async getRiskAlerts(params?: {
    level?: string
    status?: string
    page?: number
    size?: number
  }) {
    return ApiService.get('/api/v1/risk/alerts', params)
  }
  
  // 更新风险设置
  static async updateRiskSettings(settings: any) {
    return ApiService.put('/api/v1/risk/settings', settings)
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
    return ApiService.get('/api/v1/notifications', params)
  }
  
  // 标记通知为已读
  static async markAsRead(notificationIds: string[]) {
    return ApiService.post('/api/v1/notifications/mark-read', {
      notification_ids: notificationIds
    })
  }
  
  // 删除通知
  static async deleteNotifications(notificationIds: string[]) {
    return ApiService.post('/api/v1/notifications/delete', {
      notification_ids: notificationIds
    })
  }
  
  // 发送自定义通知
  static async sendNotification(notificationData: {
    title: string
    content: string
    type: string
    recipients?: string[]
  }) {
    return ApiService.post('/api/v1/notifications/send', notificationData)
  }
}

export default api