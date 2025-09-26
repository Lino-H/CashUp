/**
 * API服务层 - 连接后端接口
 * API Service Layer - Connect to Backend Endpoints
 */

import axios from 'axios';

// API基础配置 - 使用webpack DefinePlugin注入环境变量
declare global {
  interface Window {
    ENV: {
      REACT_APP_API_URL?: string;
      REACT_APP_TRADING_URL?: string;
      REACT_APP_STRATEGY_URL?: string;
      REACT_APP_NOTIFICATION_URL?: string;
    };
  }
}

// API基础配置 - 开发环境使用相对路径，生产环境使用绝对路径
const API_BASE_URL = process.env.NODE_ENV === 'development' ? '/api' : (window.ENV?.REACT_APP_API_URL || 'http://localhost:8001/api');

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Cookie认证API - 直接发送请求不添加Authorization头，但允许发送cookies
const cookieApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // 允许发送cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Cookie认证API响应拦截器
cookieApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 统一错误处理
    if (error.response?.status === 401) {
      // 未授权，清除token并跳转到登录页
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      // 请求频率限制
      console.error('请求频率限制:', error.response.data);
    } else if (error.response?.status >= 500) {
      // 服务器错误
      console.error('服务器错误:', error.response.data);
    } else if (error.response?.status >= 400) {
      // 客户端错误
      console.error('客户端错误:', error.response.data);
    } else if (error.code === 'ECONNABORTED') {
      // 请求超时
      console.error('请求超时:', error.message);
    } else if (!error.response) {
      // 网络错误
      console.error('网络错误:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 统一错误处理
    if (error.response?.status === 401) {
      // 未授权，清除token并跳转到登录页
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      // 请求频率限制
      console.error('请求频率限制:', error.response.data);
    } else if (error.response?.status >= 500) {
      // 服务器错误
      console.error('服务器错误:', error.response.data);
    } else if (error.response?.status >= 400) {
      // 客户端错误
      console.error('客户端错误:', error.response.data);
    } else if (error.code === 'ECONNABORTED') {
      // 请求超时
      console.error('请求超时:', error.message);
    } else if (!error.response) {
      // 网络错误
      console.error('网络错误:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// 认证相关API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  register: (userData: any) =>
    api.post('/auth/register', userData),
  
  logout: () =>
    api.post('/auth/logout'),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
    
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
};

export const authAPIWithCookies = {
  login: (username: string, password: string) =>
    cookieApi.post('/auth/login', { username, password }),
  
  logout: () =>
    cookieApi.post('/auth/logout'),
  
  getCurrentUser: () =>
    cookieApi.get('/auth/me'),
};

// 用户相关API
export const userAPI = {
  getUsers: (params?: any) =>
    cookieApi.get('/users', { params }),
  
  getUserById: (userId: string) =>
    cookieApi.get(`/users/${userId}`),
  
  getCurrentUser: () =>
    cookieApi.get('/users/me'),
  
  updateUser: (userId: string, userData: any) =>
    cookieApi.put(`/users/${userId}`, userData),
  
  updateCurrentUser: (userData: any) =>
    cookieApi.put('/users/me', userData),
  
  changePassword: (passwordData: any) =>
    cookieApi.post('/users/me/change-password', passwordData),
};

// 配置相关API
export const configAPI = {
  getConfigs: (params?: any) =>
    cookieApi.get('/config', { params }),
  
  getConfigById: (configId: string) =>
    cookieApi.get(`/config/${configId}`),
  
  getConfigByKey: (key: string) =>
    cookieApi.get(`/config/by-key/${key}`),
  
  getConfigsByCategory: (category: string) =>
    cookieApi.get(`/config/category/${category}`),
  
  createConfig: (configData: any) =>
    cookieApi.post('/config', configData),
  
  updateConfig: (configId: string, configData: any) =>
    cookieApi.put(`/config/${configId}`, configData),
  
  updateConfigByKey: (key: string, value: any) =>
    cookieApi.put(`/config/key/${key}`, { value }),
  
  deleteConfig: (configId: string) =>
    cookieApi.delete(`/config/${configId}`),
  
  batchUpdateConfigs: (configs: any[]) =>
    cookieApi.post('/config/batch', configs),
  
  getMyConfigs: () =>
    cookieApi.get('/config/my'),
};

  // 策略平台API (端口8003)
const strategyApi = axios.create({
  baseURL: (window.ENV?.REACT_APP_STRATEGY_URL) || 'http://localhost:8003/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 允许跨域请求携带cookies
});

// 策略平台API响应拦截器
strategyApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 统一错误处理
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      console.error('请求频率限制:', error.response.data);
    } else if (error.response?.status >= 500) {
      console.error('服务器错误:', error.response.data);
    } else if (error.response?.status >= 400) {
      console.error('客户端错误:', error.response.data);
    } else if (error.code === 'ECONNABORTED') {
      console.error('请求超时:', error.message);
    } else if (!error.response) {
      console.error('网络错误:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export const strategyAPI = {
  getStrategies: (params?: any) =>
    strategyApi.get('/strategies', { params }),
  
  getStrategyById: (strategyId: string) =>
    strategyApi.get(`/strategies/${strategyId}`),
  
  createStrategy: (strategyData: any) =>
    strategyApi.post('/strategies', strategyData),
  
  updateStrategy: (strategyId: string, strategyData: any) =>
    strategyApi.put(`/strategies/${strategyId}`, strategyData),
  
  deleteStrategy: (strategyId: string) =>
    strategyApi.delete(`/strategies/${strategyId}`),
  
  startStrategy: (strategyId: string) =>
    strategyApi.post(`/strategies/${strategyId}/start`),
  
  stopStrategy: (strategyId: string) =>
    strategyApi.post(`/strategies/${strategyId}/stop`),
  
  reloadStrategy: (strategyId: string) =>
    strategyApi.post(`/strategies/${strategyId}/reload`),
  
  getStrategyPerformance: (strategyId: string) =>
    strategyApi.get(`/strategies/${strategyId}/performance`),
  
  getBacktests: (params?: any) =>
    strategyApi.get('/backtest', { params }),
  
  getBacktestById: (backtestId: string) =>
    strategyApi.get(`/backtest/${backtestId}`),
  
  createBacktest: (backtestData: any) =>
    strategyApi.post('/backtest', backtestData),
  
  getMarketData: (symbol: string, params?: any) =>
    strategyApi.get(`/data/historical/${symbol}`, { params }),
  
  getRealTimeData: (symbol: string) =>
    strategyApi.get(`/data/realtime/${symbol}`),
  
  getMultipleRealTimeData: (symbols: string[]) =>
    strategyApi.get('/data/realtime', { params: { symbols: symbols.join(',') } }),
  
  getMarketOverview: () =>
    strategyApi.get('/data/market/overview'),
  
  getSymbols: () =>
    strategyApi.get('/data/symbols'),
  
  getTimeframes: () =>
    strategyApi.get('/data/timeframes'),
};

// API响应基础类型
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  detail?: string;
  error?: string;
}

// 策略响应类型
export interface StrategyResponse {
  strategies: Strategy[];
  total?: number;
  page?: number;
}

// 市场数据响应类型
export interface MarketDataResponse {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

// 策略类型
export interface Strategy {
  id: string;
  name: string;
  description: string;
  type: string;
  symbol: string;
  timeframe: string;
  status: 'running' | 'stopped' | 'error' | 'paused';
  config: any;
  performance: {
    totalPnl: number;
    winRate: number;
    tradesCount: number;
    maxDrawdown: number;
    sharpeRatio: number;
  };
  createdAt: string;
  updatedAt: string;
}

// 交易订单类型
export interface Order {
  id: string;
  strategyId: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  price: number;
  quantity: number;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  filledQuantity: number;
  averagePrice: number;
  fee: number;
  pnl?: number;
  timestamp: string;
}

// 持仓类型
export interface Position {
  id: string;
  strategyId: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  margin: number;
  leverage: number;
  timestamp: string;
}

// 交易服务API (端口8002)
const tradingApi = axios.create({
  baseURL: (window.ENV?.REACT_APP_TRADING_URL) || 'http://localhost:8002/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 允许跨域请求携带cookies
});

// 交易API响应拦截器
tradingApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 统一错误处理
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status === 429) {
      console.error('请求频率限制:', error.response.data);
    } else if (error.response?.status >= 500) {
      console.error('服务器错误:', error.response.data);
    } else if (error.response?.status >= 400) {
      console.error('客户端错误:', error.response.data);
    } else if (error.code === 'ECONNABORTED') {
      console.error('请求超时:', error.message);
    } else if (!error.response) {
      console.error('网络错误:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export const tradingAPI = {
  // 临时API，因为交易引擎还没有这些具体端点
  // 订单管理
  getOrders: (params?: any) =>
    tradingApi.get('/v1/orders', { params }),
  
  getOrderById: (orderId: string) =>
    tradingApi.get(`/orders/${orderId}`),
  
  createOrder: (orderData: any) =>
    tradingApi.post('/orders', orderData),
  
  updateOrder: (orderId: string, orderData: any) =>
    tradingApi.put(`/orders/${orderId}`, orderData),
  
  cancelOrder: (orderId: string) =>
    tradingApi.delete(`/orders/${orderId}`),
  
  getOrdersSummary: () =>
    tradingApi.get('/orders/summary'),
  
  getOrdersBySymbol: (symbol: string) =>
    tradingApi.get(`/orders/by-symbol/${symbol}`),
  
  getOrdersByStrategy: (strategyId: string) =>
    tradingApi.get(`/orders/by-strategy/${strategyId}`),
  
  // 持仓管理
  getPositions: (params?: any) =>
    tradingApi.get('/v1/positions', { params }),
  
  getPositionById: (positionId: string) =>
    tradingApi.get(`/positions/${positionId}`),
  
  createPosition: (positionData: any) =>
    tradingApi.post('/positions', positionData),
  
  updatePosition: (positionId: string, positionData: any) =>
    tradingApi.put(`/positions/${positionId}`, positionData),
  
  closePosition: (positionId: string) =>
    tradingApi.post(`/positions/${positionId}/close`),
  
  getPositionsSummary: () =>
    tradingApi.get('/positions/summary'),
  
  getPositionsBySymbol: (symbol: string) =>
    tradingApi.get(`/positions/by-symbol/${symbol}`),
  
  getPositionsByStrategy: (strategyId: string) =>
    tradingApi.get(`/positions/by-strategy/${strategyId}`),
  
  // 交易记录
  getTrades: (params?: any) =>
    tradingApi.get('/v1/trades', { params }),
  
  getTradeById: (tradeId: string) =>
    tradingApi.get(`/v1/trades/${tradeId}`),
  
  createTrade: (tradeData: any) =>
    tradingApi.post('/v1/trades', tradeData),
  
  getTradesSummary: () =>
    tradingApi.get('/v1/trades/summary'),
  
  getTradesStatistics: () =>
    tradingApi.get('/v1/trades/statistics'),
  
  // 账户信息
  getBalances: () =>
    tradingApi.get('/v1/balances'),
  
  getAccountInfo: () =>
    tradingApi.get('/v1/account/info'),
};

// 统一API响应处理函数
export const handleApiResponse = <T>(response: any): T | null => {
  if (!response) {
    return null;
  }
  
  // 处理不同的响应结构
  if (response.data) {
    return response.data;
  }
  
  if (response.strategies) {
    return response;
  }
  
  if (response.orders) {
    return response;
  }
  
  if (response.positions) {
    return response;
  }
  
  return response;
};

// API缓存接口
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

// API缓存管理器
class APICache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  
  // 生成缓存键
  private generateKey(url: string, params?: any): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${url}_${paramString}`;
  }
  
  // 设置缓存
  set<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  // 获取缓存
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }
  
  // 清除缓存
  clear(): void {
    this.cache.clear();
  }
  
  // 清除特定URL的缓存
  clearByUrl(url: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(url)) {
        this.cache.delete(key);
      }
    }
  }
}

// 创建全局API缓存实例
const apiCache = new APICache();

// 请求去重管理器
class RequestDeduplication {
  private pendingRequests: Map<string, Promise<any>> = new Map();
  
  // 生成请求键
  private generateKey(url: string, method: string, params?: any): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${method}_${url}_${paramString}`;
  }
  
  // 添加或获取待处理的请求
  addOrGet<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key);
    }
    
    const promise = requestFn()
      .finally(() => {
        this.pendingRequests.delete(key);
      });
    
    this.pendingRequests.set(key, promise);
    return promise;
  }
  
  // 清除所有待处理的请求
  clear(): void {
    this.pendingRequests.clear();
  }
}

// 创建全局请求去重实例
const requestDeduplication = new RequestDeduplication();

// 带缓存的API调用包装器
export const cachedApiCall = async <T>(
  apiFunction: () => Promise<T>,
  cacheKey: string,
  ttl: number = 5 * 60 * 1000
): Promise<T> => {
  // 首先检查缓存
  const cachedData = apiCache.get<T>(cacheKey);
  if (cachedData) {
    return cachedData;
  }
  
  // 如果没有缓存，发起请求
  const data = await apiFunction();
  
  // 缓存结果
  apiCache.set(cacheKey, data, ttl);
  
  return data;
};

// 带去重的API调用包装器
export const deduplicatedApiCall = async <T>(
  apiFunction: () => Promise<T>,
  dedupKey: string
): Promise<T> => {
  return requestDeduplication.addOrGet(dedupKey, apiFunction);
};

// 错误日志记录
export const logError = (error: any, context?: string) => {
  const errorInfo = {
    timestamp: new Date().toISOString(),
    context: context || 'API_ERROR',
    message: error?.message || 'Unknown error',
    code: error?.code,
    status: error?.response?.status,
    url: error?.config?.url,
    method: error?.config?.method,
    stack: error?.stack,
  };
  
  console.error('API Error:', errorInfo);
  
  // 可以在这里添加错误上报逻辑
  // 例如发送到错误监控服务
};

// 统一API错误处理
export const handleApiError = (error: any): string => {
  // 记录错误日志
  logError(error);
  
  if (error.response) {
    const { status, data } = error.response;
    switch (status) {
      case 400:
        return data?.detail || data?.message || '请求参数错误';
      case 401:
        return '未授权，请重新登录';
      case 403:
        return data?.detail || '权限不足';
      case 404:
        return data?.detail || '资源不存在';
      case 422:
        return data?.detail || '数据验证失败';
      case 429:
        return data?.detail || '请求频率限制，请稍后再试';
      case 500:
        return data?.detail || '服务器内部错误';
      case 502:
        return '网关错误，请稍后再试';
      case 503:
        return '服务暂时不可用，请稍后再试';
      case 504:
        return '网关超时，请稍后再试';
      default:
        return data?.detail || data?.message || `未知错误 (${status})`;
    }
  } else if (error.code === 'ECONNABORTED') {
    return '请求超时，请检查网络连接';
  } else if (error.code === 'ERR_NETWORK') {
    return '网络错误，请检查网络连接';
  } else if (error.request) {
    return '服务器无响应，请稍后再试';
  } else {
    return error?.message || '未知错误';
  }
};

// 缓存管理工具
export const cacheManager = {
  clear: () => apiCache.clear(),
  clearByUrl: (url: string) => apiCache.clearByUrl(url),
  getStats: () => ({
    size: apiCache.cache.size,
    keys: Array.from(apiCache.cache.keys())
  })
};

// 请求去重管理工具
export const dedupeManager = {
  clear: () => requestDeduplication.clear(),
  getPendingRequests: () => Array.from(requestDeduplication.pendingRequests.keys())
};

// 请求重试函数
export const apiCallWithRetry = async <T extends any>(
  apiFunction: () => Promise<T>,
  maxRetries: number = 1
): Promise<T> => {
  try {
    const result = await apiFunction();
    return result;
  } catch (error: any) {
    // 如果是401错误且还有重试次数，尝试刷新token
    if (error.response?.status === 401 && maxRetries > 0) {
      // 这里需要从AuthContext获取刷新token的逻辑
      // 为了简化，我们直接抛出错误
      console.warn('API call failed with 401, retry logic would go here');
    }
    throw error;
  }
};

export default api;