/**
 * API服务层 - 连接后端接口
 * API Service Layer - Connect to Backend Endpoints
 */

import axios from 'axios';

// API基础配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001/api';

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
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 未授权，清除token并跳转到登录页
      localStorage.removeItem('token');
      window.location.href = '/login';
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
};

// 用户相关API
export const userAPI = {
  getUsers: (params?: any) =>
    api.get('/users', { params }),
  
  getUserById: (userId: string) =>
    api.get(`/users/${userId}`),
  
  getCurrentUser: () =>
    api.get('/users/me'),
  
  updateUser: (userId: string, userData: any) =>
    api.put(`/users/${userId}`, userData),
  
  updateCurrentUser: (userData: any) =>
    api.put('/users/me', userData),
  
  changePassword: (passwordData: any) =>
    api.post('/users/me/change-password', passwordData),
};

// 配置相关API
export const configAPI = {
  getConfigs: (params?: any) =>
    api.get('/config', { params }),
  
  getConfigById: (configId: string) =>
    api.get(`/config/${configId}`),
  
  getConfigByKey: (key: string) =>
    api.get(`/config/by-key/${key}`),
  
  getConfigsByCategory: (category: string) =>
    api.get(`/config/category/${category}`),
  
  createConfig: (configData: any) =>
    api.post('/config', configData),
  
  updateConfig: (configId: string, configData: any) =>
    api.put(`/config/${configId}`, configData),
  
  updateConfigByKey: (key: string, value: any) =>
    api.put(`/config/key/${key}`, { value }),
  
  deleteConfig: (configId: string) =>
    api.delete(`/config/${configId}`),
  
  batchUpdateConfigs: (configs: any[]) =>
    api.post('/config/batch', configs),
  
  getMyConfigs: () =>
    api.get('/config/my'),
};

// 策略平台API (端口8003)
const strategyApi = axios.create({
  baseURL: process.env.REACT_APP_STRATEGY_URL || 'http://localhost:8003/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加相同的拦截器
strategyApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

strategyApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
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

// 市场数据类型
export interface MarketData {
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
  baseURL: process.env.REACT_APP_TRADING_URL || 'http://localhost:8002/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加相同的拦截器
tradingApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

tradingApi.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const tradingAPI = {
  // 订单管理
  getOrders: (params?: any) =>
    tradingApi.get('/orders', { params }),
  
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
    tradingApi.get('/positions', { params }),
  
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
    tradingApi.get('/trades', { params }),
  
  getTradeById: (tradeId: string) =>
    tradingApi.get(`/trades/${tradeId}`),
  
  createTrade: (tradeData: any) =>
    tradingApi.post('/trades', tradeData),
  
  getTradesSummary: () =>
    tradingApi.get('/trades/summary'),
  
  getTradesStatistics: () =>
    tradingApi.get('/trades/statistics'),
  
  // 账户信息
  getBalances: () =>
    tradingApi.get('/balances'),
  
  getAccountInfo: () =>
    tradingApi.get('/account/info'),
};

export default api;