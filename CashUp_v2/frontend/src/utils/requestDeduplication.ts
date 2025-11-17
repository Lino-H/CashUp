/**
 * 请求去重管理器
 * Request Deduplication Manager
 */

export interface DeduplicationEntry {
  requestId: string;
  timestamp: number;
  promise: Promise<any>;
  cancelToken?: AbortController;
}

export interface DeduplicationConfig {
  /** 请求超时时间（毫秒） */
  timeout: number;
  /** 最大并发请求数 */
  maxConcurrent: number;
  /** 去重时间窗口（毫秒） */
  deduplicationWindow: number;
  /** 重试次数 */
  maxRetries: number;
  /** 是否启用请求去重 */
  enabled: boolean;
  /** 是否启用取消机制 */
  enableCancellation: boolean;
}

export interface DeduplicationMetrics {
  totalRequests: number;
  deduplicatedRequests: number;
  concurrentRequests: number;
  timeoutRequests: number;
  cancelledRequests: number;
  retryRequests: number;
  successRate: number;
  averageResponseTime: number;
}

export class RequestDeduplicationManager {
  private activeRequests: Map<string, DeduplicationEntry>;
  private config: DeduplicationConfig;
  private metrics: DeduplicationMetrics;
  private cleanupTimer: NodeJS.Timeout | null;

  constructor(config: Partial<DeduplicationConfig> = {}) {
    this.config = {
      timeout: 30 * 1000, // 30秒
      maxConcurrent: 10,
      deduplicationWindow: 5 * 60 * 1000, // 5分钟
      maxRetries: 3,
      enabled: true,
      enableCancellation: true,
      ...config,
    };

    this.activeRequests = new Map();
    this.metrics = this.initMetrics();
    this.cleanupTimer = null;

    this.startCleanup();
  }

  /**
   * 初始化性能指标
   */
  private initMetrics(): DeduplicationMetrics {
    return {
      totalRequests: 0,
      deduplicatedRequests: 0,
      concurrentRequests: 0,
      timeoutRequests: 0,
      cancelledRequests: 0,
      retryRequests: 0,
      successRate: 0,
      averageResponseTime: 0,
    };
  }

  /**
   * 生成请求唯一标识
   */
  private generateRequestKey(method: string, url: string, params?: any): string {
    const paramString = params ? JSON.stringify(params, Object.keys(params).sort()) : '';
    return `${method}:${url}:${paramString}`;
  }

  /**
   * 检查是否超时
   */
  private isExpired(entry: DeduplicationEntry): boolean {
    return Date.now() - entry.timestamp > this.config.deduplicationWindow;
  }

  /**
   * 清理过期请求
   */
  private cleanupExpired(): void {
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.activeRequests.entries()) {
      if (this.isExpired(entry)) {
        expiredKeys.push(key);
        this.metrics.cancelledRequests++;
        
        // 取消请求
        if (entry.cancelToken) {
          entry.cancelToken.abort();
        }
      }
    }

    expiredKeys.forEach(key => {
      this.activeRequests.delete(key);
      this.metrics.concurrentRequests--;
    });

    if (expiredKeys.length > 0) {
      console.log(`[RequestDeduplication] Cleaned up ${expiredKeys.length} expired requests`);
    }
  }

  /**
   * 开始清理
   */
  private startCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.cleanupTimer = setInterval(() => {
      this.cleanupExpired();
    }, this.config.deduplicationWindow / 2);

    console.log(`[RequestDeduplication] Cleanup started with interval: ${this.config.deduplicationWindow / 2}ms`);
  }

  /**
   * 停止清理
   */
  private stopCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  /**
   * 执行请求
   */
  private async executeRequest<T>(
    requestKey: string,
    requestFn: () => Promise<T>,
    cancelToken?: AbortController
  ): Promise<T> {
    const startTime = Date.now();
    
    try {
      const result = await Promise.race([
        requestFn(),
        new Promise<never>((_, reject) => {
          setTimeout(() => reject(new Error('Request timeout')), this.config.timeout);
        })
      ]);

      const responseTime = Date.now() - startTime;
      this.metrics.totalRequests++;
      this.metrics.successRate = (this.metrics.totalRequests > 0 ? 
        ((this.metrics.totalRequests - this.metrics.timeoutRequests) / this.metrics.totalRequests) * 100 : 0);

      // 更新平均响应时间
      this.metrics.averageResponseTime = 
        (this.metrics.averageResponseTime * (this.metrics.totalRequests - 1) + responseTime) / this.metrics.totalRequests;

      // 清理已完成请求
      this.activeRequests.delete(requestKey);
      this.metrics.concurrentRequests--;

      return result;
    } catch (error) {
      this.metrics.totalRequests++;
      
      if (error instanceof Error && error.message === 'Request timeout') {
        this.metrics.timeoutRequests++;
      } else {
        this.metrics.concurrentRequests--;
        this.activeRequests.delete(requestKey);
      }

      throw error;
    }
  }

  /**
   * 执行去重请求
   */
  public async deduplicateRequest<T>(
    method: string,
    url: string,
    requestFn: () => Promise<T>,
    params?: any,
    retryCount: number = 0
  ): Promise<T> {
    if (!this.config.enabled) {
      return requestFn();
    }

    const requestKey = this.generateRequestKey(method, url, params);
    const now = Date.now();

    // 检查是否有相同的请求正在进行
    const existingEntry = this.activeRequests.get(requestKey);
    
    if (existingEntry && !this.isExpired(existingEntry)) {
      this.metrics.deduplicatedRequests++;
      console.log(`[RequestDeduplication] Deduplicated request: ${requestKey}`);
      return existingEntry.promise;
    }

    // 检查并发请求数限制
    if (this.metrics.concurrentRequests >= this.config.maxConcurrent) {
      console.log(`[RequestDeduplication] Max concurrent requests reached: ${this.config.maxConcurrent}`);
      return requestFn();
    }

    // 创建取消控制器
    const cancelToken = this.config.enableCancellation ? new AbortController() : undefined;

    // 创建新的请求条目
    const entry: DeduplicationEntry = {
      requestId: requestKey,
      timestamp: now,
      promise: this.executeRequest(requestKey, requestFn, cancelToken),
      cancelToken,
    };

    this.activeRequests.set(requestKey, entry);
    this.metrics.concurrentRequests++;

    try {
      const result = await entry.promise;
      return result;
    } catch (error) {
      // 重试逻辑
      if (retryCount < this.config.maxRetries) {
        this.metrics.retryRequests++;
        console.log(`[RequestDeduplication] Retrying request (${retryCount + 1}/${this.config.maxRetries}): ${requestKey}`);
        
        // 等待一段时间后重试
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
        
        return this.deduplicateRequest(method, url, requestFn, params, retryCount + 1);
      }
      
      throw error;
    }
  }

  /**
   * 取消请求
   */
  public cancelRequest(method: string, url: string, params?: any): boolean {
    if (!this.config.enableCancellation) {
      return false;
    }

    const requestKey = this.generateRequestKey(method, url, params);
    const entry = this.activeRequests.get(requestKey);

    if (entry && !this.isExpired(entry)) {
      if (entry.cancelToken) {
        entry.cancelToken.abort();
      }
      
      this.activeRequests.delete(requestKey);
      this.metrics.concurrentRequests--;
      this.metrics.cancelledRequests++;
      
      console.log(`[RequestDeduplication] Cancelled request: ${requestKey}`);
      return true;
    }

    return false;
  }

  /**
   * 获取性能指标
   */
  public getMetrics(): DeduplicationMetrics {
    return { ...this.metrics };
  }

  /**
   * 获取当前请求数量
   */
  public getActiveRequestCount(): number {
    return this.metrics.concurrentRequests;
  }

  /**
   * 检查请求是否正在执行
   */
  public isRequestActive(method: string, url: string, params?: any): boolean {
    const requestKey = this.generateRequestKey(method, url, params);
    const entry = this.activeRequests.get(requestKey);
    return !!entry && !this.isExpired(entry);
  }

  /**
   * 更新配置
   */
  public updateConfig(newConfig: Partial<DeduplicationConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // 重新启动清理器
    this.stopCleanup();
    this.startCleanup();
  }

  /**
   * 清空所有请求
   */
  public clear(): void {
    this.activeRequests.clear();
    this.metrics.concurrentRequests = 0;
    this.metrics.cancelledRequests += this.activeRequests.size;
    
    // 取消所有请求
    for (const entry of this.activeRequests.values()) {
      if (entry.cancelToken) {
        entry.cancelToken.abort();
      }
    }
  }

  /**
   * 销毁请求去重管理器
   */
  public destroy(): void {
    this.stopCleanup();
    this.clear();
    this.metrics = this.initMetrics();
  }
}

// 创建默认请求去重管理器实例
export const requestDeduplicationManager = new RequestDeduplicationManager({
  timeout: 30 * 1000,
  maxConcurrent: 10,
  deduplicationWindow: 5 * 60 * 1000,
  maxRetries: 3,
  enabled: true,
  enableCancellation: true,
});

export default RequestDeduplicationManager;