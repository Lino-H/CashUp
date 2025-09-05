/**
 * 实时交易API服务
 * Real-time Trading API Service
 */

import { message } from 'antd';

// 实时交易数据类型
export interface RealTimeTrade {
  id: string;
  strategyName: string;
  symbol: string;
  side: 'buy' | 'sell';
  price: number;
  quantity: number;
  amount: number;
  timestamp: string;
  exchange: string;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  orderId: string;
  fee: number;
  pnl?: number;
}

// 实时价格数据类型
export interface RealTimePrice {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

// 策略状态类型
export interface StrategyStatus {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error' | 'paused';
  startTime?: string;
  uptime: string;
  tradesCount: number;
  totalPnl: number;
  winRate: number;
  currentPositions: number;
  maxDrawdown: number;
  cpuUsage: number;
  memoryUsage: number;
  lastSignal?: string;
  lastError?: string;
}

// 账户余额类型
export interface AccountBalance {
  exchange: string;
  totalBalance: number;
  availableBalance: number;
  usedBalance: number;
  btcValue: number;
  change24h: number;
  currencies: Array<{
    currency: string;
    balance: number;
    available: number;
    locked: number;
    btcValue: number;
  }>;
}

// 当前持仓类型
export interface CurrentPosition {
  id: string;
  strategyName: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  margin: number;
  leverage: number;
  liquidationPrice: number;
  openTime: string;
  duration: string;
  exchange: string;
}

// 风险指标类型
export interface RiskMetrics {
  totalExposure: number;
  marginUsage: number;
  maxDrawdown: number;
  var95: number;
  sharpeRatio: number;
  beta: number;
  correlation: number;
  riskLevel: 'low' | 'medium' | 'high';
}

// 策略控制参数
export interface StrategyControl {
  strategyId: string;
  action: 'start' | 'stop' | 'pause' | 'resume';
  params?: Record<string, any>;
}

// 交易请求参数
export interface TradeRequest {
  strategyId: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  quantity: number;
  price?: number;
  leverage?: number;
  stopLoss?: number;
  takeProfit?: number;
}

// 实时数据订阅
export interface RealTimeSubscription {
  type: 'trades' | 'prices' | 'positions' | 'balances' | 'strategy_status';
  symbols?: string[];
  exchanges?: string[];
  strategies?: string[];
}

// 告警规则
export interface AlertRule {
  id: string;
  name: string;
  type: 'pnl' | 'drawdown' | 'position' | 'margin' | 'connection';
  condition: string;
  threshold: number;
  operator: 'greater' | 'less' | 'equal';
  enabled: boolean;
  notification: {
    email?: boolean;
    sms?: boolean;
    webhook?: string;
  };
}

class RealTimeTradingService {
  private baseUrl: string;
  private ws: WebSocket | null = null;
  private subscriptions: Map<string, RealTimeSubscription> = new Map();
  private eventHandlers: Map<string, Function[]> = new Map();

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8002';
  }

  // WebSocket连接管理
  connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/trading';
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket连接已建立');
          this._emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this._handleWebSocketMessage(data);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭');
          this._emit('disconnected');
          // 自动重连
          setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error);
          this._emit('error', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // 事件处理
  on(event: string, handler: Function): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler: Function): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private _emit(event: string, data?: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  private _handleWebSocketMessage(data: any): void {
    const { type, payload } = data;
    
    switch (type) {
      case 'trade':
        this._emit('trade', payload);
        break;
      case 'price':
        this._emit('price', payload);
        break;
      case 'position':
        this._emit('position', payload);
        break;
      case 'balance':
        this._emit('balance', payload);
        break;
      case 'strategy_status':
        this._emit('strategy_status', payload);
        break;
      case 'alert':
        this._emit('alert', payload);
        break;
      default:
        console.warn('未知的消息类型:', type);
    }
  }

  // 订阅实时数据
  async subscribe(subscription: RealTimeSubscription): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/realtime/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const subscriptionId = await response.text();
      this.subscriptions.set(subscriptionId, subscription);
      
      // 如果WebSocket已连接，发送订阅消息
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'subscribe',
          subscriptionId,
          data: subscription
        }));
      }

      console.log('订阅成功:', subscriptionId);
    } catch (error) {
      console.error('订阅失败:', error);
      throw error;
    }
  }

  // 取消订阅
  async unsubscribe(subscriptionId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/realtime/unsubscribe/${subscriptionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      this.subscriptions.delete(subscriptionId);
      
      // 如果WebSocket已连接，发送取消订阅消息
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'unsubscribe',
          subscriptionId
        }));
      }

      console.log('取消订阅成功:', subscriptionId);
    } catch (error) {
      console.error('取消订阅失败:', error);
      throw error;
    }
  }

  // 获取实时交易数据
  async getRecentTrades(params?: {
    strategy?: string;
    symbol?: string;
    exchange?: string;
    limit?: number;
    offset?: number;
  }): Promise<RealTimeTrade[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/realtime/trades${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取实时交易数据失败:', error);
      throw error;
    }
  }

  // 获取实时价格数据
  async getRealTimePrices(symbols?: string[]): Promise<RealTimePrice[]> {
    try {
      const queryString = symbols ? `?symbols=${symbols.join(',')}` : '';
      const response = await fetch(`${this.baseUrl}/api/realtime/prices${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取实时价格数据失败:', error);
      throw error;
    }
  }

  // 获取策略状态
  async getStrategyStatus(strategyId?: string): Promise<StrategyStatus[]> {
    try {
      const queryString = strategyId ? `?strategyId=${strategyId}` : '';
      const response = await fetch(`${this.baseUrl}/api/realtime/strategy-status${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取策略状态失败:', error);
      throw error;
    }
  }

  // 获取账户余额
  async getAccountBalances(exchange?: string): Promise<AccountBalance[]> {
    try {
      const queryString = exchange ? `?exchange=${exchange}` : '';
      const response = await fetch(`${this.baseUrl}/api/realtime/balances${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取账户余额失败:', error);
      throw error;
    }
  }

  // 获取当前持仓
  async getCurrentPositions(params?: {
    strategy?: string;
    symbol?: string;
    exchange?: string;
  }): Promise<CurrentPosition[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/realtime/positions${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取当前持仓失败:', error);
      throw error;
    }
  }

  // 获取风险指标
  async getRiskMetrics(): Promise<RiskMetrics> {
    try {
      const response = await fetch(`${this.baseUrl}/api/realtime/risk-metrics`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取风险指标失败:', error);
      throw error;
    }
  }

  // 策略控制
  async controlStrategy(control: StrategyControl): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/strategies/control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(control),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const actionText = {
        start: '启动',
        stop: '停止',
        pause: '暂停',
        resume: '恢复'
      };

      message.success(`策略${actionText[control.action]}成功`);
    } catch (error) {
      console.error('策略控制失败:', error);
      message.error('策略控制失败');
      throw error;
    }
  }

  // 手动交易
  async placeTrade(request: TradeRequest): Promise<{
    orderId: string;
    status: string;
    message: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/trading/place-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('下单成功');
      return result;
    } catch (error) {
      console.error('下单失败:', error);
      message.error('下单失败');
      throw error;
    }
  }

  // 取消订单
  async cancelOrder(orderId: string, exchange: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/trading/cancel-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ orderId, exchange }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('订单取消成功');
    } catch (error) {
      console.error('取消订单失败:', error);
      message.error('取消订单失败');
      throw error;
    }
  }

  // 获取告警规则
  async getAlertRules(): Promise<AlertRule[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/alerts/rules`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取告警规则失败:', error);
      throw error;
    }
  }

  // 创建告警规则
  async createAlertRule(rule: Omit<AlertRule, 'id'>): Promise<string> {
    try {
      const response = await fetch(`${this.baseUrl}/api/alerts/rules`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rule),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('告警规则创建成功');
      return result.id;
    } catch (error) {
      console.error('创建告警规则失败:', error);
      message.error('创建告警规则失败');
      throw error;
    }
  }

  // 更新告警规则
  async updateAlertRule(id: string, rule: Partial<AlertRule>): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/alerts/rules/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rule),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('告警规则更新成功');
    } catch (error) {
      console.error('更新告警规则失败:', error);
      message.error('更新告警规则失败');
      throw error;
    }
  }

  // 删除告警规则
  async deleteAlertRule(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/alerts/rules/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('告警规则删除成功');
    } catch (error) {
      console.error('删除告警规则失败:', error);
      message.error('删除告警规则失败');
      throw error;
    }
  }

  // 获取系统状态
  async getSystemStatus(): Promise<{
    uptime: string;
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
    activeConnections: number;
    lastUpdate: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/system/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取系统状态失败:', error);
      throw error;
    }
  }

  // 获取性能指标
  async getPerformanceMetrics(): Promise<{
    ordersPerSecond: number;
    avgResponseTime: number;
    successRate: number;
    errorRate: number;
    activeStrategies: number;
    totalTrades: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/system/performance`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取性能指标失败:', error);
      throw error;
    }
  }
}

// 创建单例实例
export const realTimeTradingService = new RealTimeTradingService();

// 导出类型
export type {
  RealTimeTrade,
  RealTimePrice,
  StrategyStatus,
  AccountBalance,
  CurrentPosition,
  RiskMetrics,
  StrategyControl,
  TradeRequest,
  RealTimeSubscription,
  AlertRule
};