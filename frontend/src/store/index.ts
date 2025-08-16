import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  User, UserProfile, Strategy, Position, Order, AccountInfo, MarketData,
  RiskMetrics, RiskAlert, Notification, AppState, UserState, TradingState,
  RiskState, RiskSettings
} from '../types'

// 应用状态
interface AppStore extends AppState {
  // Actions
  setUser: (user: User | null) => void
  setAuthenticated: (isAuthenticated: boolean) => void
  setTheme: (theme: 'light' | 'dark') => void
  setLanguage: (language: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useAppStore = create<AppStore>()(
  persist(
    (set: any) => ({
      // Initial state
      user: null as User | null,
      isAuthenticated: false as boolean,
      theme: 'light' as 'light' | 'dark',
      language: 'zh-CN' as string,
      loading: false as boolean,
      error: null as string | null,

      // Actions
      setUser: (user: User | null) => set({ user, isAuthenticated: !!user }),
      setAuthenticated: (isAuthenticated: boolean) => set({ isAuthenticated }),
      setTheme: (theme: 'light' | 'dark') => set({ theme }),
      setLanguage: (language: string) => set({ language }),
      setLoading: (loading: boolean) => set({ loading }),
      setError: (error: string | null) => set({ error }),
      reset: () => set({
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null
      })
    }),
    {
      name: 'app-store',
      partialize: (state: any) => ({
        theme: state.theme,
        language: state.language
      })
    }
  )
)

// 用户状态
interface UserStore extends UserState {
  // Actions
  setProfile: (profile: UserProfile | null) => void
  updateProfile: (updates: Partial<UserProfile>) => void
  setPreferences: (preferences: Record<string, any>) => void
  updatePreference: (key: string, value: any) => void
  setNotifications: (notifications: Notification[]) => void
  addNotification: (notification: Notification) => void
  markNotificationAsRead: (id: string) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
  getUnreadCount: () => number
}

export const useUserStore = create<UserStore>()(
  persist(
    (set: any) => ({
      // Initial state
      profile: null as UserProfile | null,
      preferences: {} as Record<string, any>,
      notifications: [] as Notification[],
      unreadCount: 0 as number,

      // Actions
      setProfile: (profile: UserProfile | null) => set({ profile }),
      
      updateProfile: (updates: Partial<UserProfile>) => set((state: any) => ({
        profile: state.profile ? { ...state.profile, ...updates } : null
      })),
      
      setPreferences: (preferences: Record<string, any>) => set({ preferences }),
      
      updatePreference: (key: string, value: any) => set((state: any) => ({
        preferences: { ...state.preferences, [key]: value }
      })),
      
      setNotifications: (notifications: Notification[]) => {
        const unreadCount = notifications.filter((n: any) => n.status === 'unread').length
        set({ notifications, unreadCount })
      },
      
      addNotification: (notification: Notification) => set((state: any) => {
        const notifications = [notification, ...state.notifications]
        const unreadCount = notifications.filter((n: any) => n.status === 'unread').length
        return { notifications, unreadCount }
      }),
      
      markNotificationAsRead: (id: string) => set((state: any) => {
        const notifications = state.notifications.map((n: any) => 
          n.id === id ? { ...n, status: 'read' as const, read_at: new Date().toISOString() } : n
        )
        const unreadCount = notifications.filter((n: any) => n.status === 'unread').length
        return { notifications, unreadCount }
      }),
      
      removeNotification: (id: string) => set((state: any) => {
        const notifications = state.notifications.filter((n: any) => n.id !== id)
        const unreadCount = notifications.filter((n: any) => n.status === 'unread').length
        return { notifications, unreadCount }
      }),
      
      clearNotifications: () => set({ notifications: [], unreadCount: 0 }),
      
      getUnreadCount: (): number => {
        const state = useUserStore.getState()
        return state.unreadCount
      }
    }),
    {
      name: 'user-store',
      partialize: (state: any) => ({
        preferences: state.preferences
      })
    }
  )
)

// 交易状态
interface TradingStore extends TradingState {
  // Actions
  setStrategies: (strategies: Strategy[]) => void
  addStrategy: (strategy: Strategy) => void
  updateStrategy: (id: string, updates: Partial<Strategy>) => void
  removeStrategy: (id: string) => void
  
  setPositions: (positions: Position[]) => void
  addPosition: (position: Position) => void
  updatePosition: (id: string, updates: Partial<Position>) => void
  removePosition: (id: string) => void
  
  setOrders: (orders: Order[]) => void
  addOrder: (order: Order) => void
  updateOrder: (id: string, updates: Partial<Order>) => void
  removeOrder: (id: string) => void
  
  setBalance: (balance: AccountInfo | null) => void
  updateBalance: (updates: Partial<AccountInfo>) => void
  
  setMarketData: (symbol: string, data: MarketData) => void
  updateMarketData: (updates: Record<string, MarketData>) => void
  
  // Getters
  getStrategy: (id: string) => Strategy | undefined
  getPosition: (id: string) => Position | undefined
  getOrder: (id: string) => Order | undefined
  getActiveStrategies: () => Strategy[]
  getOpenPositions: () => Position[]
  getPendingOrders: () => Order[]
  getTotalPnL: () => number
}

export const useTradingStore = create<TradingStore>((set: any, get: any) => ({
  // Initial state
  strategies: [],
  positions: [],
  orders: [],
  balance: null,
  marketData: {},

  // Actions
  setStrategies: (strategies: Strategy[]) => set({ strategies }),
  
  addStrategy: (strategy: Strategy) => set((state: any) => ({
    strategies: [...state.strategies, strategy]
  })),
  
  updateStrategy: (id: string, updates: Partial<Strategy>) => set((state: any) => ({
    strategies: state.strategies.map((s: any) => s.id === id ? { ...s, ...updates } : s)
  })),
  
  removeStrategy: (id: string) => set((state: any) => ({
    strategies: state.strategies.filter((s: any) => s.id !== id)
  })),
  
  setPositions: (positions: Position[]) => set({ positions }),
  
  addPosition: (position: Position) => set((state: any) => ({
    positions: [...state.positions, position]
  })),
  
  updatePosition: (id: string, updates: Partial<Position>) => set((state: any) => ({
    positions: state.positions.map((p: any) => p.id === id ? { ...p, ...updates } : p)
  })),
  
  removePosition: (id: string) => set((state: any) => ({
    positions: state.positions.filter((p: any) => p.id !== id)
  })),
  
  setOrders: (orders: Order[]) => set({ orders }),
  
  addOrder: (order: Order) => set((state: any) => ({
    orders: [...state.orders, order]
  })),
  
  updateOrder: (id: string, updates: Partial<Order>) => set((state: any) => ({
    orders: state.orders.map((o: any) => o.id === id ? { ...o, ...updates } : o)
  })),
  
  removeOrder: (id: string) => set((state: any) => ({
    orders: state.orders.filter((o: any) => o.id !== id)
  })),
  
  setBalance: (balance: AccountInfo | null) => set({ balance }),
  
  updateBalance: (updates: Partial<AccountInfo>) => set((state: any) => ({
    balance: state.balance ? { ...state.balance, ...updates } : null
  })),
  
  setMarketData: (symbol: string, data: MarketData) => set((state: any) => ({
    marketData: { ...state.marketData, [symbol]: data }
  })),
  
  updateMarketData: (updates: Record<string, MarketData>) => set((state: any) => ({
    marketData: { ...state.marketData, ...updates }
  })),
  
  // Getters
  getStrategy: (id: string) => get().strategies.find((s: any) => s.id === id),
  
  getPosition: (id: string) => get().positions.find((p: any) => p.id === id),
  
  getOrder: (id: string) => get().orders.find((o: any) => o.id === id),
  
  getActiveStrategies: () => get().strategies.filter((s: any) => s.status === 'active'),
  
  getOpenPositions: () => get().positions.filter((p: any) => p.quantity !== 0),
  
  getPendingOrders: () => get().orders.filter((o: any) => 
    ['pending', 'open', 'partially_filled'].includes(o.status)
  ),
  
  getTotalPnL: () => {
    const positions = get().positions
    return positions.reduce((total: number, position: any) => total + position.unrealized_pnl, 0)
  }
}))

// 风险管理状态
interface RiskStore extends RiskState {
  // Actions
  setMetrics: (metrics: RiskMetrics | null) => void
  updateMetrics: (updates: Partial<RiskMetrics>) => void
  
  setAlerts: (alerts: RiskAlert[]) => void
  addAlert: (alert: RiskAlert) => void
  updateAlert: (id: string, updates: Partial<RiskAlert>) => void
  removeAlert: (id: string) => void
  resolveAlert: (id: string) => void
  
  setSettings: (settings: RiskSettings) => void
  updateSettings: (updates: Partial<RiskSettings>) => void
  
  // Getters
  getActiveAlerts: () => RiskAlert[]
  getCriticalAlerts: () => RiskAlert[]
  getAlertsByLevel: (level: string) => RiskAlert[]
}

export const useRiskStore = create<RiskStore>((set: any, get: any) => ({
  // Initial state
  metrics: null,
  alerts: [],
  settings: null,

  // Actions
  setMetrics: (metrics: RiskMetrics | null) => set({ metrics }),
  
  updateMetrics: (updates: Partial<RiskMetrics>) => set((state: any) => ({
    metrics: state.metrics ? { ...state.metrics, ...updates } : null
  })),
  
  setAlerts: (alerts: RiskAlert[]) => set({ alerts }),
  
  addAlert: (alert: RiskAlert) => set((state: any) => ({
    alerts: [alert, ...state.alerts]
  })),
  
  updateAlert: (id: string, updates: Partial<RiskAlert>) => set((state: any) => ({
    alerts: state.alerts.map((a: any) => a.id === id ? { ...a, ...updates } : a)
  })),
  
  removeAlert: (id: string) => set((state: any) => ({
    alerts: state.alerts.filter((a: any) => a.id !== id)
  })),
  
  resolveAlert: (id: string) => set((state: any) => ({
    alerts: state.alerts.map((a: any) => 
      a.id === id 
        ? { ...a, status: 'resolved' as const, resolved_at: new Date().toISOString() }
        : a
    )
  })),
  
  setSettings: (settings: RiskSettings) => set({ settings }),
  
  updateSettings: (updates: Partial<RiskSettings>) => set((state: any) => ({
    settings: state.settings ? { ...state.settings, ...updates } : updates
  })),
  
  // Getters
  getActiveAlerts: () => get().alerts.filter((a: any) => a.status === 'active'),
  
  getCriticalAlerts: () => get().alerts.filter((a: any) => 
    a.status === 'active' && a.level === 'critical'
  ),
  
  getAlertsByLevel: (level: string) => get().alerts.filter((a: any) => 
    a.status === 'active' && a.level === level
  )
}))

// WebSocket状态
interface WebSocketStore {
  connected: boolean
  reconnecting: boolean
  lastMessage: any
  subscriptions: Set<string>
  
  // Actions
  setConnected: (connected: boolean) => void
  setReconnecting: (reconnecting: boolean) => void
  setLastMessage: (message: any) => void
  addSubscription: (channel: string) => void
  removeSubscription: (channel: string) => void
  clearSubscriptions: () => void
}

export const useWebSocketStore = create<WebSocketStore>((set: any) => ({
  // Initial state
  connected: false,
  reconnecting: false,
  lastMessage: null,
  subscriptions: new Set(),

  // Actions
  setConnected: (connected: boolean) => set({ connected }),
  
  setReconnecting: (reconnecting: boolean) => set({ reconnecting }),
  
  setLastMessage: (message: any) => set({ lastMessage: message }),
  
  addSubscription: (channel: string) => set((state: any) => ({
    subscriptions: new Set([...state.subscriptions, channel])
  })),
  
  removeSubscription: (channel: string) => set((state: any) => {
    const newSubscriptions = new Set(state.subscriptions)
    newSubscriptions.delete(channel)
    return { subscriptions: newSubscriptions }
  }),
  
  clearSubscriptions: () => set({ subscriptions: new Set() })
}))

// UI状态
interface UIStore {
  sidebarCollapsed: boolean
  activeTab: string
  selectedStrategy: string | null
  selectedPosition: string | null
  selectedOrder: string | null
  modals: Record<string, boolean>
  drawers: Record<string, boolean>
  
  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void
  setActiveTab: (tab: string) => void
  setSelectedStrategy: (id: string | null) => void
  setSelectedPosition: (id: string | null) => void
  setSelectedOrder: (id: string | null) => void
  openModal: (name: string) => void
  closeModal: (name: string) => void
  toggleModal: (name: string) => void
  openDrawer: (name: string) => void
  closeDrawer: (name: string) => void
  toggleDrawer: (name: string) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set: any) => ({
      // Initial state
      sidebarCollapsed: false as boolean,
      activeTab: 'dashboard' as string,
      selectedStrategy: null as string | null,
      selectedPosition: null as string | null,
      selectedOrder: null as string | null,
      modals: {} as Record<string, boolean>,
      drawers: {} as Record<string, boolean>,

      // Actions
      setSidebarCollapsed: (collapsed: boolean) => set({ sidebarCollapsed: collapsed }),
      
      setActiveTab: (tab: string) => set({ activeTab: tab }),
      
      setSelectedStrategy: (id: string | null) => set({ selectedStrategy: id }),
      
      setSelectedPosition: (id: string | null) => set({ selectedPosition: id }),
      
      setSelectedOrder: (id: string | null) => set({ selectedOrder: id }),
      
      openModal: (name: string) => set((state: any) => ({
        modals: { ...state.modals, [name]: true }
      })),
      
      closeModal: (name: string) => set((state: any) => ({
        modals: { ...state.modals, [name]: false }
      })),
      
      toggleModal: (name: string) => set((state: any) => ({
        modals: { ...state.modals, [name]: !state.modals[name] }
      })),
      
      openDrawer: (name: string) => set((state: any) => ({
        drawers: { ...state.drawers, [name]: true }
      })),
      
      closeDrawer: (name: string) => set((state: any) => ({
        drawers: { ...state.drawers, [name]: false }
      })),
      
      toggleDrawer: (name: string) => set((state: any) => ({
        drawers: { ...state.drawers, [name]: !state.drawers[name] }
      }))
    }),
    {
      name: 'ui-store',
      partialize: (state: any) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        activeTab: state.activeTab
      })
    }
  )
)

// 导出所有stores的组合
export const useStores = () => ({
  app: useAppStore(),
  user: useUserStore(),
  trading: useTradingStore(),
  risk: useRiskStore(),
  websocket: useWebSocketStore(),
  ui: useUIStore()
})

// 重置所有stores
export const resetAllStores = () => {
  useAppStore.getState().reset?.()
  // 其他stores可以根据需要添加reset方法
}