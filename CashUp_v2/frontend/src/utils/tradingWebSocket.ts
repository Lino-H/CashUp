/**
 * 实时交易WebSocket客户端
 * Real-time Trading WebSocket Client
 */

import { WebSocketManager, WebSocketMessage, createWebSocketManager } from './websocketManager';

export interface MarketData {
  symbol: string;
  price: number;
  timestamp: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  change24h: number;
  changePercent24h: number;
}

export interface TradeData {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  price: number;
  quantity: number;
  timestamp: number;
  maker: boolean;
  fee: number;
}

export interface OrderBookData {
  symbol: string;
  timestamp: number;
  bids: [number, number][]; // [price, quantity]
  asks: [number, number][]; // [price, quantity]
  spread: number;
}

export interface PositionUpdate {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercentage: number;
  timestamp: number;
}

export interface OrderUpdate {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  quantity: number;
  price: number;
  status: 'pending' | 'open' | 'filled' | 'canceled' | 'rejected';
  filledQuantity: number;
  remainingQuantity: number;
  timestamp: number;
}

export interface TradingWebSocketConfig {
  url: string;
  enableReconnect: boolean;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  enableHeartbeat: boolean;
  heartbeatInterval: number;
  enableLogging: boolean;
  symbols: string[];
}

export interface TradingEventHandlers {
  onMarketData?: (data: MarketData) => void;
  onTrade?: (data: TradeData) => void;
  onOrderBook?: (data: OrderBookData) => void;
  onPositionUpdate?: (data: PositionUpdate) => void;
  onOrderUpdate?: (data: OrderUpdate) => void;
  onConnectionStatus?: (status: 'connected' | 'disconnected' | 'reconnecting') => void;
  onError?: (error: Error) => void;
}

export class TradingWebSocketClient {
  private wsManager: WebSocketManager | null = null;
  private config: TradingWebSocketConfig;
  private eventHandlers: TradingEventHandlers;
  private subscriptions: Set<string> = new Set();
  private isInitialized = false;

  constructor(config: TradingWebSocketConfig, eventHandlers: TradingEventHandlers = {}) {
    this.config = {
      enableReconnect: true,
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      enableHeartbeat: true,
      heartbeatInterval: 30000,
      enableLogging: false,
      ...config,
    };

    this.eventHandlers = eventHandlers;
  }

  /**
   * 初始化WebSocket连接
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.warn('TradingWebSocketClient is already initialized');
      return;
    }

    try {
      this.log('Initializing TradingWebSocketClient...');
      
      this.wsManager = createWebSocketManager(
        this.config.url,
        {
          onOpen: this.handleOpen.bind(this),
          onClose: this.handleClose.bind(this),
          onError: this.handleError.bind(this),
          onMessage: this.handleMessage.bind(this),
          onReconnect: this.handleReconnect.bind(this),
          onMaxReconnectReached: this.handleMaxReconnectReached.bind(this),
        },
        {
          reconnectInterval: this.config.reconnectInterval,
          maxReconnectAttempts: this.config.maxReconnectAttempts,
          enableHeartbeat: this.config.enableHeartbeat,
          heartbeatInterval: this.config.heartbeatInterval,
          enableLogging: this.config.enableLogging,
        }
      );

      this.isInitialized = true;
      this.log('TradingWebSocketClient initialized successfully');
    } catch (error) {
      this.log('Initialization error:', error);
      this.eventHandlers.onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * 连接WebSocket
   */
  public connect(): void {
    if (!this.wsManager) {
      this.log('WebSocket manager not initialized');
      return;
    }

    this.wsManager.connect();
  }

  /**
   * 断开连接
   */
  public disconnect(): void {
    if (this.wsManager) {
      this.wsManager.disconnect();
    }
    this.isInitialized = false;
    this.subscriptions.clear();
  }

  /**
   * 订阅市场数据
   */
  public subscribeMarketData(symbols: string[]): void {
    const symbolsToSubscribe = symbols.filter(symbol => !this.subscriptions.has(symbol));
    
    if (symbolsToSubscribe.length === 0) {
      return;
    }

    this.subscriptions.add('market_data');
    this.sendSubscriptionRequest('market_data', { symbols: symbolsToSubscribe });
    this.log(`Subscribed to market data for: ${symbolsToSubscribe.join(', ')}`);
  }

  /**
   * 订阅交易数据
   */
  public subscribeTrades(symbols: string[]): void {
    const symbolsToSubscribe = symbols.filter(symbol => !this.subscriptions.has(`trades_${symbol}`));
    
    if (symbolsToSubscribe.length === 0) {
      return;
    }

    symbolsToSubscribe.forEach(symbol => {
      this.subscriptions.add(`trades_${symbol}`);
    });
    
    this.sendSubscriptionRequest('trades', { symbols: symbolsToSubscribe });
    this.log(`Subscribed to trades for: ${symbolsToSubscribe.join(', ')}`);
  }

  /**
   * 订阅订单簿数据
   */
  public subscribeOrderBook(symbols: string[], depth: number = 20): void {
    const symbolsToSubscribe = symbols.filter(symbol => !this.subscriptions.has(`orderbook_${symbol}`));
    
    if (symbolsToSubscribe.length === 0) {
      return;
    }

    symbolsToSubscribe.forEach(symbol => {
      this.subscriptions.add(`orderbook_${symbol}`);
    });
    
    this.sendSubscriptionRequest('orderbook', { symbols: symbolsToSubscribe, depth });
    this.log(`Subscribed to order book for: ${symbolsToSubscribe.join(', ')}, depth: ${depth}`);
  }

  /**
   * 订阅持仓更新
   */
  public subscribePositions(): void {
    if (this.subscriptions.has('positions')) {
      return;
    }

    this.subscriptions.add('positions');
    this.sendSubscriptionRequest('positions', {});
    this.log('Subscribed to position updates');
  }

  /**
   * 订阅订单更新
   */
  public subscribeOrders(): void {
    if (this.subscriptions.has('orders')) {
      return;
    }

    this.subscriptions.add('orders');
    this.sendSubscriptionRequest('orders', {});
    this.log('Subscribed to order updates');
  }

  /**
   * 取消订阅
   */
  public unsubscribe(topic: string): void {
    if (!this.subscriptions.has(topic)) {
      return;
    }

    this.subscriptions.delete(topic);
    this.sendUnsubscriptionRequest(topic);
    this.log(`Unsubscribed from: ${topic}`);
  }

  /**
   * 取消所有订阅
   */
  public unsubscribeAll(): void {
    const topics = Array.from(this.subscriptions);
    topics.forEach(topic => this.unsubscribe(topic));
  }

  /**
   * 发送订单
   */
  public async sendOrder(order: {
    symbol: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit' | 'stop' | 'stop_limit';
    quantity: number;
    price?: number;
    stopPrice?: number;
  }): Promise<{ orderId: string; status: string }> {
    if (!this.wsManager || !this.isConnected()) {
      throw new Error('WebSocket not connected');
    }

    try {
      const response = await this.wsManager.sendWithResponse(
        {
          type: 'create_order',
          data: order,
          timestamp: Date.now(),
        },
        'order_created',
        10000
      );

      return response;
    } catch (error) {
      this.log('Order creation error:', error);
      throw error;
    }
  }

  /**
   * 取消订单
   */
  public async cancelOrder(orderId: string): Promise<{ success: boolean; message: string }> {
    if (!this.wsManager || !this.isConnected()) {
      throw new Error('WebSocket not connected');
    }

    try {
      const response = await this.wsManager.sendWithResponse(
        {
          type: 'cancel_order',
          data: { orderId },
          timestamp: Date.now(),
        },
        'order_canceled',
        10000
      );

      return response;
    } catch (error) {
      this.log('Order cancellation error:', error);
      throw error;
    }
  }

  /**
   * 修改订单
   */
  public async modifyOrder(orderId: string, modifications: {
    quantity?: number;
    price?: number;
  }): Promise<{ success: boolean; message: string }> {
    if (!this.wsManager || !this.isConnected()) {
      throw new Error('WebSocket not connected');
    }

    try {
      const response = await this.wsManager.sendWithResponse(
        {
          type: 'modify_order',
          data: { orderId, modifications },
          timestamp: Date.now(),
        },
        'order_modified',
        10000
      );

      return response;
    } catch (error) {
      this.log('Order modification error:', error);
      throw error;
    }
  }

  /**
   * 获取连接状态
   */
  public isConnected(): boolean {
    return this.wsManager?.getReadyState() === WebSocket.OPEN;
  }

  /**
   * 获取连接状态信息
   */
  public getConnectionStatus(): string {
    return this.wsManager?.getConnectionState() ?? 'unknown';
  }

  /**
   * 获取订阅列表
   */
  public getSubscriptions(): string[] {
    return Array.from(this.subscriptions);
  }

  /**
   * 获取统计信息
   */
  public getMetrics() {
    return this.wsManager?.getMetrics() || {
      totalMessages: 0,
      sentMessages: 0,
      receivedMessages: 0,
      connectionTime: 0,
      disconnections: 0,
      reconnects: 0,
      errors: 0,
    };
  }

  /**
   * 处理连接打开
   */
  private handleOpen(event: Event): void {
    this.log('WebSocket connected');
    this.eventHandlers.onConnectionStatus?.('connected');
    
    // 重新订阅之前的主题
    this.resubscribeTopics();
  }

  /**
   * 处理连接关闭
   */
  private handleClose(event: CloseEvent): void {
    this.log('WebSocket disconnected:', event.code, event.reason);
    this.eventHandlers.onConnectionStatus?.('disconnected');
  }

  /**
   * 处理连接错误
   */
  private handleError(event: Event): void {
    this.log('WebSocket error:', event);
    this.eventHandlers.onError?.(new Error('WebSocket connection error'));
  }

  /**
   * 处理重连
   */
  private handleReconnect(attempt: number): void {
    this.log(`Reconnecting... (attempt ${attempt})`);
    this.eventHandlers.onConnectionStatus?.('reconnecting');
  }

  /**
   * 处理最大重连次数达到
   */
  private handleMaxReconnectReached(): void {
    this.log('Max reconnect attempts reached');
    this.eventHandlers.onError?.(new Error('Max reconnect attempts reached'));
  }

  /**
   * 处理消息
   */
  private handleMessage(message: WebSocketMessage): void {
    try {
      switch (message.type) {
        case 'market_data':
          this.handleMarketData(message.data);
          break;
        case 'trade':
          this.handleTrade(message.data);
          break;
        case 'orderbook':
          this.handleOrderBook(message.data);
          break;
        case 'position_update':
          this.handlePositionUpdate(message.data);
          break;
        case 'order_update':
          this.handleOrderUpdate(message.data);
          break;
        case 'subscription_ack':
          this.log('Subscription acknowledged:', message.data);
          break;
        case 'error':
          this.log('Server error:', message.data);
          this.eventHandlers.onError?.(new Error(message.data.message || 'Server error'));
          break;
        default:
          this.log('Unknown message type:', message.type);
      }
    } catch (error) {
      this.log('Message handling error:', error);
      this.eventHandlers.onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  }

  /**
   * 处理市场数据
   */
  private handleMarketData(data: MarketData): void {
    this.eventHandlers.onMarketData?.(data);
  }

  /**
   * 处理交易数据
   */
  private handleTrade(data: TradeData): void {
    this.eventHandlers.onTrade?.(data);
  }

  /**
   * 处理订单簿数据
   */
  private handleOrderBook(data: OrderBookData): void {
    this.eventHandlers.onOrderBook?.(data);
  }

  /**
   * 处理持仓更新
   */
  private handlePositionUpdate(data: PositionUpdate): void {
    this.eventHandlers.onPositionUpdate?.(data);
  }

  /**
   * 处理订单更新
   */
  private handleOrderUpdate(data: OrderUpdate): void {
    this.eventHandlers.onOrderUpdate?.(data);
  }

  /**
   * 发送订阅请求
   */
  private sendSubscriptionRequest(topic: string, data: any): void {
    if (!this.wsManager || !this.isConnected()) {
      this.log('Cannot send subscription request - not connected');
      return;
    }

    this.wsManager.send({
      type: 'subscribe',
      data: { topic, ...data },
      timestamp: Date.now(),
    }).catch(error => {
      this.log('Subscription request error:', error);
    });
  }

  /**
   * 发送取消订阅请求
   */
  private sendUnsubscriptionRequest(topic: string): void {
    if (!this.wsManager || !this.isConnected()) {
      this.log('Cannot send unsubscription request - not connected');
      return;
    }

    this.wsManager.send({
      type: 'unsubscribe',
      data: { topic },
      timestamp: Date.now(),
    }).catch(error => {
      this.log('Unsubscription request error:', error);
    });
  }

  /**
   * 重新订阅主题
   */
  private resubscribeTopics(): void {
    const topics = Array.from(this.subscriptions);
    topics.forEach(topic => {
      if (topic.startsWith('market_data')) {
        this.sendSubscriptionRequest('market_data', { symbols: this.config.symbols });
      } else if (topic.startsWith('trades_')) {
        const symbol = topic.replace('trades_', '');
        this.sendSubscriptionRequest('trades', { symbols: [symbol] });
      } else if (topic.startsWith('orderbook_')) {
        const symbol = topic.replace('orderbook_', '');
        this.sendSubscriptionRequest('orderbook', { symbols: [symbol] });
      } else if (topic === 'positions') {
        this.sendSubscriptionRequest('positions', {});
      } else if (topic === 'orders') {
        this.sendSubscriptionRequest('orders', {});
      }
    });
  }

  /**
   * 日志记录
   */
  private log(...args: any[]): void {
    if (this.config.enableLogging) {
      console.log('[TradingWebSocket]', ...args);
    }
  }
}

/**
 * 全局交易WebSocket客户端实例
 */
let globalTradingWebSocketClient: TradingWebSocketClient | null = null;

/**
 * 创建交易WebSocket客户端
 */
export function createTradingWebSocketClient(
  config: TradingWebSocketConfig,
  eventHandlers?: TradingEventHandlers
): TradingWebSocketClient {
  globalTradingWebSocketClient = new TradingWebSocketClient(config, eventHandlers);
  return globalTradingWebSocketClient;
}

/**
 * 获取全局交易WebSocket客户端
 */
export function getGlobalTradingWebSocketClient(): TradingWebSocketClient | null {
  return globalTradingWebSocketClient;
}

/**
 * 销毁全局交易WebSocket客户端
 */
export function destroyGlobalTradingWebSocketClient(): void {
  if (globalTradingWebSocketClient) {
    globalTradingWebSocketClient.disconnect();
    globalTradingWebSocketClient = null;
  }
}