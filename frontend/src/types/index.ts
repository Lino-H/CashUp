// 用户相关类型
export interface User {
  id: string
  username: string
  email: string
  phone?: string
  avatar?: string
  nickname?: string
  timezone: string
  language: string
  theme: 'light' | 'dark' | 'auto'
  created_at: string
  updated_at: string
  is_active: boolean
  is_verified: boolean
}

export interface UserProfile extends User {
  first_name?: string
  last_name?: string
  bio?: string
  location?: string
  website?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  username: string
  invite_code?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

// 策略相关类型
export interface Strategy {
  id: string
  name: string
  description: string
  type: StrategyType
  status: StrategyStatus
  parameters: Record<string, any>
  symbols: string[]
  timeframe: string
  risk_level: RiskLevel
  max_positions: number
  initial_capital: number
  created_at: string
  updated_at: string
  created_by: string
  performance?: StrategyPerformance
}

export type StrategyType = 
  | 'trend_following'
  | 'mean_reversion'
  | 'momentum'
  | 'arbitrage'
  | 'market_making'
  | 'grid_trading'
  | 'dca'
  | 'custom'

export type StrategyStatus = 
  | 'draft'
  | 'active'
  | 'paused'
  | 'stopped'
  | 'error'

export type RiskLevel = 'low' | 'medium' | 'high'

export interface StrategyPerformance {
  total_return: number
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  profit_factor: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  avg_win: number
  avg_loss: number
  largest_win: number
  largest_loss: number
}

export interface BacktestRequest {
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  commission?: number
  slippage?: number
}

export interface BacktestResult {
  id: string
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  performance: StrategyPerformance
  equity_curve: EquityPoint[]
  trades: Trade[]
  created_at: string
}

export interface EquityPoint {
  timestamp: string
  equity: number
  drawdown: number
}

// 交易相关类型
export interface Order {
  id: string
  strategy_id?: string
  symbol: string
  side: OrderSide
  type: OrderType
  status: OrderStatus
  quantity: number
  price?: number
  filled_quantity: number
  avg_fill_price?: number
  commission: number
  created_at: string
  updated_at: string
  filled_at?: string
  cancelled_at?: string
}

export type OrderSide = 'buy' | 'sell'
export type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit'
export type OrderStatus = 
  | 'pending'
  | 'open'
  | 'partially_filled'
  | 'filled'
  | 'cancelled'
  | 'rejected'
  | 'expired'

export interface Position {
  id: string
  strategy_id?: string
  symbol: string
  side: 'long' | 'short'
  quantity: number
  avg_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
  commission: number
  margin_used: number
  leverage: number
  created_at: string
  updated_at: string
}

export interface Trade {
  id: string
  strategy_id?: string
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  commission: number
  pnl: number
  executed_at: string
  order_id: string
}

export interface Balance {
  currency: string
  total: number
  available: number
  frozen: number
  margin_used: number
  unrealized_pnl: number
}

export interface AccountInfo {
  balances: Balance[]
  total_equity: number
  margin_level: number
  free_margin: number
  margin_call_level: number
  stop_out_level: number
}

// 市场数据相关类型
export interface MarketData {
  symbol: string
  price: number
  change: number
  change_percent: number
  volume: number
  high_24h: number
  low_24h: number
  market_cap?: number
  updated_at: string
}

export interface Kline {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TechnicalIndicator {
  name: string
  value: number
  signal: 'buy' | 'sell' | 'neutral'
  description: string
}

export interface MarketOverview {
  total_market_cap: number
  total_volume: number
  btc_dominance: number
  fear_greed_index: number
  trending_coins: string[]
}

// 风险管理相关类型
export interface RiskMetrics {
  portfolio_value: number
  total_exposure: number
  margin_usage: number
  max_drawdown: number
  var_1d: number
  var_7d: number
  sharpe_ratio: number
  sortino_ratio: number
  beta: number
  alpha: number
}

export interface RiskAlert {
  id: string
  type: RiskAlertType
  level: AlertLevel
  title: string
  message: string
  threshold: number
  current_value: number
  strategy_id?: string
  symbol?: string
  status: 'active' | 'resolved' | 'ignored'
  created_at: string
  resolved_at?: string
}

export type RiskAlertType = 
  | 'margin_call'
  | 'max_drawdown'
  | 'position_size'
  | 'concentration'
  | 'volatility'
  | 'correlation'
  | 'liquidity'

export type AlertLevel = 'info' | 'warning' | 'error' | 'critical'

export interface RiskSettings {
  max_portfolio_risk: number
  max_position_size: number
  max_daily_loss: number
  max_drawdown: number
  margin_call_level: number
  stop_out_level: number
  concentration_limit: number
  correlation_limit: number
}

// 通知相关类型
export interface Notification {
  id: string
  type: NotificationType
  level: AlertLevel
  title: string
  content: string
  source: string
  recipient_id: string
  status: 'unread' | 'read'
  created_at: string
  read_at?: string
  metadata?: Record<string, any>
}

export type NotificationType = 
  | 'trade_execution'
  | 'order_update'
  | 'position_update'
  | 'risk_alert'
  | 'system_update'
  | 'strategy_update'
  | 'market_alert'
  | 'account_update'

export interface NotificationSettings {
  email_enabled: boolean
  push_enabled: boolean
  sms_enabled: boolean
  in_app_enabled: boolean
  quiet_hours_start?: string
  quiet_hours_end?: string
  frequency_limit: number
  types: Record<NotificationType, boolean>
}

// API相关类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
  request_id: string
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ApiError {
  code: number
  message: string
  details?: any
  timestamp: string
  request_id: string
}

// 系统配置相关类型
export interface SystemConfig {
  max_positions: number
  max_order_size: number
  default_leverage: number
  risk_level: RiskLevel
  auto_backup: boolean
  data_retention: number
  session_timeout: number
}

export interface ApiKey {
  id: string
  name: string
  key: string
  permissions: ApiPermission[]
  created_at: string
  last_used?: string
  status: 'active' | 'disabled'
  expires_at?: string
}

export type ApiPermission = 'trading' | 'market_data' | 'account' | 'admin'

// 图表相关类型
export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartDataset {
  label: string
  data: number[]
  backgroundColor?: string | string[]
  borderColor?: string
  borderWidth?: number
  fill?: boolean
}

export interface ChartOptions {
  responsive: boolean
  maintainAspectRatio: boolean
  scales?: any
  plugins?: any
  interaction?: any
}

// 表格相关类型
export interface TableColumn<T = any> {
  title: string
  dataIndex: keyof T
  key: string
  width?: number
  align?: 'left' | 'center' | 'right'
  sorter?: boolean | ((a: T, b: T) => number)
  render?: (value: any, record: T, index: number) => React.ReactNode
  filters?: { text: string; value: any }[]
  onFilter?: (value: any, record: T) => boolean
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[]
  dataSource: T[]
  loading?: boolean
  pagination?: any
  rowKey: string | ((record: T) => string)
  rowSelection?: any
  scroll?: { x?: number; y?: number }
  size?: 'small' | 'middle' | 'large'
}

// 表单相关类型
export interface FormField {
  name: string
  label: string
  type: 'input' | 'select' | 'number' | 'date' | 'switch' | 'textarea'
  required?: boolean
  placeholder?: string
  options?: { label: string; value: any }[]
  rules?: any[]
  disabled?: boolean
  tooltip?: string
}

export interface FormProps {
  fields: FormField[]
  initialValues?: Record<string, any>
  onSubmit: (values: any) => void
  loading?: boolean
  layout?: 'horizontal' | 'vertical' | 'inline'
}

// WebSocket相关类型
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface WebSocketConfig {
  url: string
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval: number
}

// 主题相关类型
export interface ThemeConfig {
  primaryColor: string
  backgroundColor: string
  textColor: string
  borderColor: string
  successColor: string
  warningColor: string
  errorColor: string
  infoColor: string
}

// 路由相关类型
export interface RouteConfig {
  path: string
  component: React.ComponentType
  exact?: boolean
  title: string
  icon?: React.ReactNode
  children?: RouteConfig[]
  permissions?: string[]
  hidden?: boolean
}

// 菜单相关类型
export interface MenuItem {
  key: string
  label: string
  icon?: React.ReactNode
  children?: MenuItem[]
  path?: string
  permissions?: string[]
  hidden?: boolean
}

// 状态管理相关类型
export interface AppState {
  user: User | null
  isAuthenticated: boolean
  theme: 'light' | 'dark'
  language: string
  loading: boolean
  error: string | null
}

export interface UserState {
  profile: UserProfile | null
  preferences: Record<string, any>
  notifications: Notification[]
  unreadCount: number
}

export interface TradingState {
  strategies: Strategy[]
  positions: Position[]
  orders: Order[]
  balance: AccountInfo | null
  marketData: Record<string, MarketData>
}

export interface RiskState {
  metrics: RiskMetrics | null
  alerts: RiskAlert[]
  settings: RiskSettings | null
}

// 事件相关类型
export interface AppEvent {
  type: string
  payload: any
  timestamp: string
}

export type EventHandler<T = any> = (event: AppEvent & { payload: T }) => void

// 工具类型
export type Nullable<T> = T | null
export type Optional<T> = T | undefined
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type KeyOf<T> = keyof T
export type ValueOf<T> = T[keyof T]

export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

// 常量类型
export const ORDER_SIDES = ['buy', 'sell'] as const
export const ORDER_TYPES = ['market', 'limit', 'stop', 'stop_limit'] as const
export const ORDER_STATUSES = [
  'pending', 'open', 'partially_filled', 'filled', 
  'cancelled', 'rejected', 'expired'
] as const

export const STRATEGY_TYPES = [
  'trend_following', 'mean_reversion', 'momentum', 
  'arbitrage', 'market_making', 'grid_trading', 'dca', 'custom'
] as const

export const STRATEGY_STATUSES = [
  'draft', 'active', 'paused', 'stopped', 'error'
] as const

export const RISK_LEVELS = ['low', 'medium', 'high'] as const
export const ALERT_LEVELS = ['info', 'warning', 'error', 'critical'] as const

export const NOTIFICATION_TYPES = [
  'trade_execution', 'order_update', 'position_update', 
  'risk_alert', 'system_update', 'strategy_update', 
  'market_alert', 'account_update'
] as const

export const API_PERMISSIONS = ['trading', 'market_data', 'account', 'admin'] as const

// 默认值
export const DEFAULT_PAGE_SIZE = 20
export const DEFAULT_CHART_COLORS = [
  '#1890ff', '#52c41a', '#faad14', '#f5222d', 
  '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'
]

export const DEFAULT_TIMEFRAMES = [
  { label: '1分钟', value: '1m' },
  { label: '5分钟', value: '5m' },
  { label: '15分钟', value: '15m' },
  { label: '30分钟', value: '30m' },
  { label: '1小时', value: '1h' },
  { label: '4小时', value: '4h' },
  { label: '1天', value: '1d' },
  { label: '1周', value: '1w' }
]

export const DEFAULT_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 
  'DOTUSDT', 'XRPUSDT', 'LTCUSDT', 'LINKUSDT'
]