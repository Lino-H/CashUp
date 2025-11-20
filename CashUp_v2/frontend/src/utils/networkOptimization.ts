/**
 * 网络优化管理器
 * Network Optimization Manager
 * 整合缓存和请求去重功能
 */

import { cacheManager } from './cacheManager';
import { requestDeduplicationManager } from './requestDeduplication';

export interface NetworkOptimizationConfig {
  /** 缓存配置 */
  cache: {
    enabled: boolean;
    defaultTTL: number;
    maxSize: number;
    maxEntries: number;
    compression: boolean;
  };
  /** 请求去重配置 */
  deduplication: {
    enabled: boolean;
    timeout: number;
    maxConcurrent: number;
    deduplicationWindow: number;
    maxRetries: number;
  };
  /** 是否启用缓存优先 */
  cacheFirst: boolean;
  /** 是否启用网络优先 */
  networkFirst: boolean;
  /** 是否启用stale-while-revalidate */
  staleWhileRevalidate: boolean;
  /** 是否启用离线支持 */
  offlineSupport: boolean;
}

export interface NetworkRequestOptions {
  /** 缓存选项 */
  cacheOptions?: {
    ttl?: number;
    tags?: string[];
    version?: string;
    compress?: boolean;
    backgroundRefresh?: boolean;
    staleWhileRevalidate?: number;
  };
  /** 请求去重选项 */
  deduplicationOptions?: {
    timeout?: number;
    retryCount?: number;
    enableCancellation?: boolean;
  };
  /** 网络选项 */
  networkOptions?: {
    timeout?: number;
    retries?: number;
    headers?: Record<string, string>;
  };
}

export interface NetworkOptimizationMetrics {
  cache: {
    hits: number;
    misses: number;
    hitRate: number;
    totalSize: number;
    evictionCount: number;
  };
  deduplication: {
    totalRequests: number;
    deduplicatedRequests: number;
    concurrentRequests: number;
    timeoutRequests: number;
    cancelledRequests: number;
    retryRequests: number;
    successRate: number;
  };
  performance: {
    averageResponseTime: number;
    cacheLoadTime: number;
    networkLoadTime: number;
    totalRequests: number;
  };
}

export class NetworkOptimizationManager {
  private config: NetworkOptimizationConfig;
  private metrics: NetworkOptimizationMetrics;

  constructor(config: Partial<NetworkOptimizationConfig> = {}) {
    this.config = {
      cache: {
        enabled: true,
        defaultTTL: 5 * 60 * 1000, // 5分钟
        maxSize: 50 * 1024 * 1024, // 50MB
        maxEntries: 1000,
        compression: true,
        ...config.cache,
      },
      deduplication: {
        enabled: true,
        timeout: 30 * 1000, // 30秒
        maxConcurrent: 10,
        deduplicationWindow: 5 * 60 * 1000, // 5分钟
        maxRetries: 3,
        ...config.deduplication,
      },
      cacheFirst: config.cacheFirst ?? true,
      networkFirst: config.networkFirst ?? false,
      staleWhileRevalidate: config.staleWhileRevalidate ?? true,
      offlineSupport: config.offlineSupport ?? false,
    };

    this.metrics = this.initMetrics();

    // 更新缓存管理器配置
    cacheManager.updateConfig({
      defaultTTL: this.config.cache.defaultTTL,
      maxSize: this.config.cache.maxSize,
      maxEntries: this.config.cache.maxEntries,
      compression: this.config.cache.compression,
    });

    // 更新请求去重管理器配置
    requestDeduplicationManager.updateConfig({
      timeout: this.config.deduplication.timeout,
      maxConcurrent: this.config.deduplication.maxConcurrent,
      deduplicationWindow: this.config.deduplication.deduplicationWindow,
      maxRetries: this.config.deduplication.maxRetries,
    });
  }

  /**
   * 初始化性能指标
   */
  private initMetrics(): NetworkOptimizationMetrics {
    return {
      cache: {
        hits: 0,
        misses: 0,
        hitRate: 0,
        totalSize: 0,
        evictionCount: 0,
      },
      deduplication: {
        totalRequests: 0,
        deduplicatedRequests: 0,
        concurrentRequests: 0,
        timeoutRequests: 0,
        cancelledRequests: 0,
        retryRequests: 0,
        successRate: 0,
      },
      performance: {
        averageResponseTime: 0,
        cacheLoadTime: 0,
        networkLoadTime: 0,
        totalRequests: 0,
      },
    };
  }

  /**
   * 生成缓存键
   */
  private generateCacheKey(method: string, url: string, params?: any): string {
    const paramString = params ? JSON.stringify(params, Object.keys(params).sort()) : '';
    return `${method}:${url}:${paramString}`;
  }

  /**
   * 执行网络请求
   */
  private async executeNetworkRequest<T>(
    requestFn: () => Promise<T>,
    options: NetworkRequestOptions = {}
  ): Promise<T> {
    const startTime = Date.now();

    try {
      const result = await requestFn();
      const responseTime = Date.now() - startTime;
      
      // 更新性能指标
      this.metrics.performance.networkLoadTime = responseTime;
      this.metrics.performance.averageResponseTime = 
        (this.metrics.performance.averageResponseTime * this.metrics.performance.totalRequests + responseTime) / 
        (this.metrics.performance.totalRequests + 1);
      
      return result;
    } catch (error) {
      const responseTime = Date.now() - startTime;
      
      // 更新性能指标
      this.metrics.performance.networkLoadTime = responseTime;
      this.metrics.performance.averageResponseTime = 
        (this.metrics.performance.averageResponseTime * this.metrics.performance.totalRequests + responseTime) / 
        (this.metrics.performance.totalRequests + 1);
      
      throw error;
    }
  }

  /**
   * 优化的网络请求方法
   */
  public async optimizedRequest<T>(
    method: string,
    url: string,
    requestFn: () => Promise<T>,
    params?: any,
    options: NetworkRequestOptions = {}
  ): Promise<T> {
    const deduplicationOptions = options.deduplicationOptions || {};

    // 更新指标
    this.metrics.performance.totalRequests++;
    this.metrics.deduplication.totalRequests++;

    // 请求去重
    if (this.config.deduplication.enabled) {
      return requestDeduplicationManager.deduplicateRequest(
        method,
        url,
        () => this.handleRequestWithCache(method, url, requestFn, params, options),
        params,
        deduplicationOptions.retryCount || 0
      );
    }

    return this.handleRequestWithCache(method, url, requestFn, params, options);
  }

  /**
   * 处理带有缓存的请求
   */
  private async handleRequestWithCache<T>(
    method: string,
    url: string,
    requestFn: () => Promise<T>,
    params?: any,
    options: NetworkRequestOptions = {}
  ): Promise<T> {
    const requestKey = this.generateCacheKey(method, url, params);
    const cacheOptions = options.cacheOptions || {};

    // 缓存优先策略
    if (this.config.cache.enabled && this.config.cacheFirst) {
      const cachedData = await cacheManager.get<T>('api', requestKey);
      if (cachedData) {
        this.metrics.cache.hits++;
        this.metrics.cache.hitRate = (this.metrics.cache.hits / (this.metrics.cache.hits + this.metrics.cache.misses)) * 100;
        
        if (this.config.staleWhileRevalidate && cacheOptions.staleWhileRevalidate) {
          // 后台刷新
          this.backgroundRefresh(method, url, requestFn, params, options);
          return cachedData;
        }
        
        return cachedData;
      }
      this.metrics.cache.misses++;
    }

    // 网络优先策略
    if (!this.config.cacheFirst) {
      const result = await this.executeNetworkRequest(requestFn, options);
      
      if (this.config.cache.enabled) {
        await cacheManager.set('api', requestKey, result, cacheOptions);
      }
      
      return result;
    }

    // 缓存未命中，执行网络请求
    const result = await this.executeNetworkRequest(requestFn, options);
    
    if (this.config.cache.enabled) {
      await cacheManager.set('api', requestKey, result, cacheOptions);
    }

    return result;
  }

  /**
   * 背景刷新
   */
  private async backgroundRefresh<T>(
    method: string,
    url: string,
    requestFn: () => Promise<T>,
    params?: any,
    options: NetworkRequestOptions = {}
  ): Promise<void> {
    const requestKey = this.generateCacheKey(method, url, params);
    
    try {
      const result = await requestFn();
      await cacheManager.set('api', requestKey, result, options.cacheOptions);
    } catch (error) {
      console.error('[NetworkOptimization] Background refresh failed:', error);
    }
  }

  /**
   * 批量请求优化
   */
  public async batchRequest<T>(
    requests: Array<{
      method: string;
      url: string;
      requestFn: () => Promise<T>;
      params?: any;
      options?: NetworkRequestOptions;
    }>
  ): Promise<Array<{ success: boolean; data?: T; error?: Error }>> {
    const results = [];

    for (const request of requests) {
      try {
        const result = await this.optimizedRequest(
          request.method,
          request.url,
          request.requestFn,
          request.params,
          request.options
        );
        results.push({ success: true, data: result });
      } catch (error) {
        results.push({ success: false, error: error as Error });
      }
    }

    return results;
  }

  /**
   * 预加载缓存
   */
  public async preloadCache<T>(
    items: Array<{
      method: string;
      url: string;
      requestFn: () => Promise<T>;
      params?: any;
      options?: NetworkRequestOptions;
    }>
  ): Promise<void> {
    const preloadPromises = items.map(async (item) => {
      try {
        const requestKey = this.generateCacheKey(item.method, item.url, item.params);
        const cacheOptions = item.options?.cacheOptions || {};
        
        // 检查是否已缓存
        const cached = await cacheManager.has('api', requestKey);
        if (!cached) {
          const result = await item.requestFn();
          await cacheManager.set('api', requestKey, result, cacheOptions);
        }
      } catch (error) {
        console.error('[NetworkOptimization] Preload failed:', error);
      }
    });

    await Promise.all(preloadPromises);
  }

  /**
   * 获取性能指标
   */
  public getMetrics(): NetworkOptimizationMetrics {
    const cacheMetrics = cacheManager.getMetrics();
    const deduplicationMetrics = requestDeduplicationManager.getMetrics();

    return {
      cache: {
        hits: cacheMetrics.totalHits,
        misses: cacheMetrics.totalMisses,
        hitRate: cacheMetrics.hitRate,
        totalSize: cacheMetrics.totalSize,
        evictionCount: cacheMetrics.totalEvictions,
      },
      deduplication: {
        totalRequests: deduplicationMetrics.totalRequests,
        deduplicatedRequests: deduplicationMetrics.deduplicatedRequests,
        concurrentRequests: deduplicationMetrics.concurrentRequests,
        timeoutRequests: deduplicationMetrics.timeoutRequests,
        cancelledRequests: deduplicationMetrics.cancelledRequests,
        retryRequests: deduplicationMetrics.retryRequests,
        successRate: deduplicationMetrics.successRate,
      },
      performance: this.metrics.performance,
    };
  }

  /**
   * 更新配置
   */
  public updateConfig(newConfig: Partial<NetworkOptimizationConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // 更新子组件配置
    cacheManager.updateConfig({
      defaultTTL: this.config.cache.defaultTTL,
      maxSize: this.config.cache.maxSize,
      maxEntries: this.config.cache.maxEntries,
      compression: this.config.cache.compression,
    });

    requestDeduplicationManager.updateConfig({
      timeout: this.config.deduplication.timeout,
      maxConcurrent: this.config.deduplication.maxConcurrent,
      deduplicationWindow: this.config.deduplication.deduplicationWindow,
      maxRetries: this.config.deduplication.maxRetries,
    });
  }

  /**
   * 清空缓存
   */
  public async clearCache(): Promise<void> {
    await cacheManager.clear();
  }

  /**
   * 取消请求
   */
  public cancelRequest(method: string, url: string, params?: any): boolean {
    return requestDeduplicationManager.cancelRequest(method, url, params);
  }

  /**
   * 检查请求是否活跃
   */
  public isRequestActive(method: string, url: string, params?: any): boolean {
    return requestDeduplicationManager.isRequestActive(method, url, params);
  }

  /**
   * 销毁网络优化管理器
   */
  public destroy(): void {
    cacheManager.destroy();
    requestDeduplicationManager.destroy();
  }
}

// 创建默认网络优化管理器实例
export const networkOptimizationManager = new NetworkOptimizationManager({
  cache: {
    enabled: true,
    defaultTTL: 5 * 60 * 1000,
    maxSize: 50 * 1024 * 1024,
    maxEntries: 1000,
    compression: true,
  },
  deduplication: {
    enabled: true,
    timeout: 30 * 1000,
    maxConcurrent: 10,
    deduplicationWindow: 5 * 60 * 1000,
    maxRetries: 3,
  },
  cacheFirst: true,
  networkFirst: false,
  staleWhileRevalidate: true,
  offlineSupport: false,
});

export default NetworkOptimizationManager;
