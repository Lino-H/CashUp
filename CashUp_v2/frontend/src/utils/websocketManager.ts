/**
 * WebSocket连接管理与URL解析
 * WebSocket Connection Manager & URL Resolution
 * 函数集注释：
 * - WebSocketManager: 管理连接、重连、心跳、订阅与消息收发
 * - createWebSocketManager/getGlobalWebSocketManager/destroyGlobalWebSocketManager: 全局实例管理
 * - resolveWebSocketUrl/getWebSocketUrl: 统一动态解析WS地址（优先使用 window.ENV，回退同源）
 */

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
  source?: string;
  correlationId?: string;
  expectResponse?: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  enableHeartbeat: boolean;
  heartbeatInterval: number;
  enableLogging: boolean;
  protocols?: string[];
}

export interface WebSocketEventHandlers {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onReconnect?: (attempt: number) => void;
  onMaxReconnectReached?: () => void;
}

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private eventHandlers: WebSocketEventHandlers;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectAttempts = 0;
  private isConnected = false;
  private messageQueue: WebSocketMessage[] = [];
  private pendingMessages: Map<string, { resolve: (value: any) => void; reject: (reason?: any) => void }> = new Map();
  private subscriptionTopics: Set<string> = new Set();
  private metrics: {
    totalMessages: number;
    sentMessages: number;
    receivedMessages: number;
    connectionTime: number;
    disconnections: number;
    reconnects: number;
    errors: number;
  };

  constructor(config: WebSocketConfig, eventHandlers: WebSocketEventHandlers = {}) {
    const cfg: Partial<WebSocketConfig> = { ...(config || {}) };
    this.config = {
      url: cfg.url ?? '',
      reconnectInterval: cfg.reconnectInterval ?? 5000,
      maxReconnectAttempts: cfg.maxReconnectAttempts ?? 10,
      enableHeartbeat: cfg.enableHeartbeat ?? true,
      heartbeatInterval: cfg.heartbeatInterval ?? 30000,
      enableLogging: cfg.enableLogging ?? false,
      protocols: cfg.protocols,
    };

    this.eventHandlers = eventHandlers;
    this.metrics = {
      totalMessages: 0,
      sentMessages: 0,
      receivedMessages: 0,
      connectionTime: 0,
      disconnections: 0,
      reconnects: 0,
      errors: 0,
    };

    this.connect();
  }

  /**
   * 连接WebSocket
   */
  public connect(): void {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.log('WebSocket already connected');
      return;
    }

    try {
      this.log(`Connecting to ${this.config.url}...`);
      
      this.ws = new WebSocket(this.config.url, this.config.protocols);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);

      this.metrics.connectionTime = Date.now();
    } catch (error) {
      this.log('Connection error:', error);
      this.metrics.errors++;
      this.handleReconnect();
    }
  }

  /**
   * 断开WebSocket连接
   */
  public disconnect(): void {
    this.log('Disconnecting WebSocket...');
    
    this.clearTimers();
    this.isConnected = false;
    this.reconnectAttempts = 0;
    
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onmessage = null;
      
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close();
      }
      
      this.ws = null;
    }

    this.eventHandlers.onClose?.(new CloseEvent('close'));
  }

  /**
   * 发送消息
   */
  public send(message: WebSocketMessage | string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket is not connected'));
        return;
      }

      try {
        if (typeof message === 'string') {
          this.ws.send(message);
          this.log('Sent message:', message);
        } else {
          const messageString = JSON.stringify(message);
          this.ws.send(messageString);
          this.log('Sent message:', message);
        }

        this.metrics.sentMessages++;
        this.metrics.totalMessages++;
        resolve();
      } catch (error) {
        this.log('Send error:', error);
        this.metrics.errors++;
        reject(error);
      }
    });
  }

  /**
   * 发送消息并等待响应
   */
  public sendWithResponse(message: WebSocketMessage, expectedResponseType: string, timeout: number = 10000): Promise<any> {
    const correlationId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const enhancedMessage: WebSocketMessage = {
      ...message,
      correlationId,
      expectResponse: expectedResponseType,
    };

    return new Promise((resolve, reject) => {
      this.pendingMessages.set(correlationId, { resolve, reject });
      
      const timeoutId = setTimeout(() => {
        this.pendingMessages.delete(correlationId);
        reject(new Error(`Request timeout for ${expectedResponseType}`));
      }, timeout);

      this.send(enhancedMessage).catch(error => {
        clearTimeout(timeoutId);
        this.pendingMessages.delete(correlationId);
        reject(error);
      });
    });
  }

  /**
   * 订阅主题
   */
  public subscribe(topic: string): void {
    this.subscriptionTopics.add(topic);
    this.log(`Subscribed to topic: ${topic}`);
    
    // 发送订阅消息
    this.send({
      type: 'subscribe',
      data: { topic },
      timestamp: Date.now(),
    }).catch(error => {
      this.log('Subscription error:', error);
    });
  }

  /**
   * 取消订阅
   */
  public unsubscribe(topic: string): void {
    this.subscriptionTopics.delete(topic);
    this.log(`Unsubscribed from topic: ${topic}`);
    
    // 发送取消订阅消息
    this.send({
      type: 'unsubscribe',
      data: { topic },
      timestamp: Date.now(),
    }).catch(error => {
      this.log('Unsubscription error:', error);
    });
  }

  /**
   * 获取连接状态
   */
  public getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * 获取连接状态信息
   */
  public getConnectionState(): string {
    const state = this.getReadyState();
    switch (state) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'open';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'closed';
      default:
        return 'unknown';
    }
  }

  /**
   * 获取统计信息
   */
  public getMetrics(): typeof this.metrics {
    return { ...this.metrics };
  }

  /**
   * 获取已订阅的主题
   */
  public getSubscriptions(): string[] {
    return Array.from(this.subscriptionTopics);
  }

  /**
   * 处理连接打开
   */
  private handleOpen(event: Event): void {
    this.log('WebSocket connected');
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.metrics.totalMessages = 0;
    this.metrics.sentMessages = 0;
    this.metrics.receivedMessages = 0;
    
    this.eventHandlers.onOpen?.(event);
    
    // 发送队列中的消息
    this.flushMessageQueue();
    
    // 启动心跳
    if (this.config.enableHeartbeat) {
      this.startHeartbeat();
    }
  }

  /**
   * 处理连接关闭
   */
  private handleClose(event: CloseEvent): void {
    this.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnected = false;
    this.metrics.disconnections++;
    
    this.clearTimers();
    this.eventHandlers.onClose?.(event);
    
    // 尝试重连
    this.handleReconnect();
  }

  /**
   * 处理连接错误
   */
  private handleError(event: Event): void {
    this.log('WebSocket error:', event);
    this.metrics.errors++;
    this.eventHandlers.onError?.(event);
  }

  /**
   * 处理消息
   */
  private handleMessage(event: MessageEvent): void {
    try {
      let message: WebSocketMessage;
      
      if (typeof event.data === 'string') {
        try {
          message = JSON.parse(event.data);
        } catch (error) {
          message = {
            type: 'raw',
            data: event.data,
            timestamp: Date.now(),
          };
        }
      } else {
        message = {
          type: 'binary',
          data: event.data,
          timestamp: Date.now(),
        };
      }

      this.metrics.receivedMessages++;
      this.metrics.totalMessages++;
      this.log('Received message:', message);

      // 处理响应消息
      if (message.correlationId && this.pendingMessages.has(message.correlationId)) {
        const pending = this.pendingMessages.get(message.correlationId);
        if (pending) {
          this.pendingMessages.delete(message.correlationId);
          if (message.type === message.expectResponse) {
            pending.resolve(message.data);
          } else {
            pending.reject(new Error(`Unexpected response type: ${message.type}`));
          }
        }
        return;
      }

      // 处理订阅消息
      if (message.type === 'subscription_ack') {
        this.log('Subscription acknowledged:', message.data);
        return;
      }

      // 调用消息处理器
      this.eventHandlers.onMessage?.(message);
      
    } catch (error) {
      this.log('Message handling error:', error);
      this.metrics.errors++;
    }
  }

  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnect attempts reached');
      this.metrics.reconnects++;
      this.eventHandlers.onMaxReconnectReached?.();
      return;
    }

    if (this.reconnectTimer) {
      return;
    }

    this.reconnectAttempts++;
    this.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
    
    this.eventHandlers.onReconnect?.(this.reconnectAttempts);
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.config.reconnectInterval);
  }

  /**
   * 发送队列中的消息
   */
  private flushMessageQueue(): void {
    if (this.messageQueue.length === 0) {
      return;
    }

    const queue = [...this.messageQueue];
    this.messageQueue = [];
    
    queue.forEach(message => {
      this.send(message).catch(error => {
        this.log('Failed to send queued message:', error);
        this.messageQueue.push(message);
      });
    });
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
        this.send({
          type: 'heartbeat',
          data: { timestamp: Date.now() },
          timestamp: Date.now(),
        }).catch(error => {
          this.log('Heartbeat error:', error);
        });
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * 清除定时器
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 日志记录
   */
  private log(...args: any[]): void {
    if (this.config.enableLogging) {
      console.log('[WebSocket Manager]', ...args);
    }
  }
}

/**
 * 解析WebSocket地址（支持绝对与相对路径）
 */
export function resolveWebSocketUrl(pathOrUrl: string): string {
  const isAbsolute = /^wss?:\/\//i.test(pathOrUrl);
  if (isAbsolute) return pathOrUrl;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const path = pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`;
  return `${protocol}//${host}${path}`;
}

/**
 * 根据类型获取WebSocket地址，优先读取构建注入的 window.ENV
 */
export function getWebSocketUrl(kind: 'trading' | 'news' | 'strategy' | 'notification', fallbackPath?: string): string {
  const env = (window as any).ENV || {};
  const keyMap: Record<string, string | undefined> = {
    trading: env.REACT_APP_WS_TRADING_URL,
    news: env.REACT_APP_WS_NEWS_URL,
    strategy: env.REACT_APP_WS_STRATEGY_URL,
    notification: env.REACT_APP_WS_NOTIFICATION_URL,
  };
  const value = keyMap[kind];
  const defaultPath = fallbackPath || `/ws/${kind}`;
  return resolveWebSocketUrl(value || defaultPath);
}

/**
 * 全局WebSocket实例
 */
let globalWebSocketManager: WebSocketManager | null = null;

/**
 * 创建WebSocket管理器
 */
export function createWebSocketManager(
  url: string,
  eventHandlers?: WebSocketEventHandlers,
  config?: Partial<WebSocketConfig>
): WebSocketManager {
  const defaultConfig: WebSocketConfig = {
    url,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
    enableHeartbeat: true,
    heartbeatInterval: 30000,
    enableLogging: process.env.NODE_ENV === 'development',
  };

  globalWebSocketManager = new WebSocketManager(
    { ...defaultConfig, ...config },
    eventHandlers
  );

  return globalWebSocketManager;
}

/**
 * 获取全局WebSocket管理器
 */
export function getGlobalWebSocketManager(): WebSocketManager | null {
  return globalWebSocketManager;
}

/**
 * 销毁全局WebSocket管理器
 */
export function destroyGlobalWebSocketManager(): void {
  if (globalWebSocketManager) {
    globalWebSocketManager.disconnect();
    globalWebSocketManager = null;
  }
}