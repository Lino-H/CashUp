import { create } from 'zustand'
import { TradingService, StrategyService, MarketService } from '../utils/api'

// 用户状态接口
interface UserState {
  user: any
  isAuthenticated: boolean
  setUser: (user: any) => void
  logout: () => void
}

// 交易状态接口
interface TradingState {
  balance: any
  positions: any[]
  orders: any[]
  trades: any[]
  loading: boolean
  fetchBalance: () => Promise<void>
  fetchPositions: () => Promise<void>
  fetchOrders: () => Promise<void>
  fetchTrades: () => Promise<void>
}

// 策略状态接口
interface StrategyState {
  strategies: any[]
  loading: boolean
  fetchStrategies: () => Promise<void>
  startStrategy: (id: string) => Promise<void>
  stopStrategy: (id: string) => Promise<void>
}

// 市场数据状态接口
interface MarketState {
  marketData: any[]
  klineData: any
  loading: boolean
  fetchMarketData: () => Promise<void>
  fetchKlineData: (symbol: string, interval: string) => Promise<void>
}

// 风险管理状态接口
interface RiskState {
  metrics: any
  alerts: any[]
  loading: boolean
  fetchRiskMetrics: () => Promise<void>
  fetchRiskAlerts: () => Promise<void>
}

// 通知状态接口
interface NotificationState {
  notifications: any[]
  unreadCount: number
  loading: boolean
  fetchNotifications: () => Promise<void>
  markAsRead: (ids: string[]) => Promise<void>
}

// 用户状态存储
export const useUserStore = create<UserState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
    set({ user: null, isAuthenticated: false })
  }
}))

// 交易状态存储
export const useTradingStore = create<TradingState>((set) => ({
  balance: null,
  positions: [],
  orders: [],
  trades: [],
  loading: false,
  
  fetchBalance: async () => {
    set({ loading: true })
    try {
      const response = await TradingService.getBalance()
      set({ balance: response.data })
    } catch (error) {
      console.error('获取余额失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  fetchPositions: async () => {
    set({ loading: true })
    try {
      const response = await TradingService.getPositions()
      set({ positions: response.data || [] })
    } catch (error) {
      console.error('获取持仓失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  fetchOrders: async () => {
    set({ loading: true })
    try {
      const response = await TradingService.getOrders()
      set({ orders: response.data || [] })
    } catch (error) {
      console.error('获取订单失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  fetchTrades: async () => {
    set({ loading: true })
    try {
      const response = await TradingService.getTradeHistory()
      set({ trades: response.data || [] })
    } catch (error) {
      console.error('获取交易历史失败:', error)
    } finally {
      set({ loading: false })
    }
  }
}))

// 策略状态存储
export const useStrategyStore = create<StrategyState>((set, get) => ({
  strategies: [],
  loading: false,
  
  fetchStrategies: async () => {
    set({ loading: true })
    try {
      const response = await StrategyService.getStrategies()
      set({ strategies: response.data || [] })
    } catch (error) {
      console.error('获取策略失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  startStrategy: async (id: string) => {
    try {
      await StrategyService.startStrategy(id)
      // 重新获取策略列表
      get().fetchStrategies()
    } catch (error) {
      console.error('启动策略失败:', error)
      throw error
    }
  },
  
  stopStrategy: async (id: string) => {
    try {
      await StrategyService.stopStrategy(id)
      // 重新获取策略列表
      get().fetchStrategies()
    } catch (error) {
      console.error('停止策略失败:', error)
      throw error
    }
  }
}))

// 市场数据状态存储
export const useMarketStore = create<MarketState>((set) => ({
  marketData: [],
  klineData: null,
  loading: false,
  
  fetchMarketData: async () => {
    set({ loading: true })
    try {
      const response = await MarketService.getMarketData()
      set({ marketData: response.data || [] })
    } catch (error) {
      console.error('获取市场数据失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  fetchKlineData: async (symbol: string, interval: string) => {
    set({ loading: true })
    try {
      const response = await MarketService.getKlineData(symbol, interval)
      set({ klineData: response.data })
    } catch (error) {
      console.error('获取K线数据失败:', error)
    } finally {
      set({ loading: false })
    }
  }
}))

// 风险管理状态存储
export const useRiskStore = create<RiskState>((set) => ({
  metrics: null,
  alerts: [],
  loading: false,
  
  fetchRiskMetrics: async () => {
    set({ loading: true })
    try {
      const { RiskService } = await import('../utils/api')
      const response = await RiskService.getRiskMetrics()
      set({ metrics: response.data })
    } catch (error) {
      console.error('获取风险指标失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  fetchRiskAlerts: async () => {
    set({ loading: true })
    try {
      const { RiskService } = await import('../utils/api')
      const response = await RiskService.getRiskAlerts()
      set({ alerts: response.data || [] })
    } catch (error) {
      console.error('获取风险预警失败:', error)
    } finally {
      set({ loading: false })
    }
  }
}))

// 通知状态存储
export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,
  
  fetchNotifications: async () => {
    set({ loading: true })
    try {
      const { NotificationService } = await import('../utils/api')
      const response = await NotificationService.getNotifications()
      set({ 
        notifications: response.data || [],
        unreadCount: (response.data || []).filter((n: any) => !n.is_read).length
      })
    } catch (error) {
      console.error('获取通知失败:', error)
    } finally {
      set({ loading: false })
    }
  },
  
  markAsRead: async (ids: string[]) => {
    try {
      const { NotificationService } = await import('../utils/api')
      await NotificationService.markAsRead(ids)
      // 重新获取通知列表
      get().fetchNotifications()
    } catch (error) {
      console.error('标记已读失败:', error)
      throw error
    }
  }
}))

// 初始化用户状态
const initializeUserState = () => {
  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('user_info')
  
  if (token && userInfo) {
    try {
      const user = JSON.parse(userInfo)
      useUserStore.getState().setUser(user)
    } catch (error) {
      console.error('解析用户信息失败:', error)
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_info')
    }
  }
}

// 应用启动时初始化
initializeUserState()