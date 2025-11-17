/**
 * 高级缓存管理系统
 * Advanced Cache Management System
 */

export interface CacheEntry<T = any> {
  data: T;
  timestamp: number;
  ttl: number;
  key: string;
  version: string;
  tags: string[];
  hitCount: number;
  size: number;
}

export interface CacheConfig {
  defaultTTL: number;
  maxSize: number;
  maxEntries: number;
  compression: boolean;
  version: string;
  enableLogging: boolean;
  enableMetrics: boolean;
}

export interface CacheMetrics {
  totalHits: number;
  totalMisses: number;
  totalEvictions: number;
  totalSize: number;
  hitRate: number;
  evictionCount: number;
  loadTime: number;
  memoryUsage: number;
}

export interface CacheOptions {
  ttl?: number;
  tags?: string[];
  version?: string;
  compress?: boolean;
  backgroundRefresh?: boolean;
  staleWhileRevalidate?: number;
}

export class CacheManager {
  private cache: Map<string, CacheEntry>;
  private config: CacheConfig;
  private metrics: CacheMetrics;
  private cleanupInterval: number;
  private cleanupTimer: NodeJS.Timeout | null;

  constructor(config: Partial<CacheConfig> = {}) {
    this.config = {
      defaultTTL: 5 * 60 * 1000, // 5分钟
      maxSize: 50 * 1024 * 1024, // 50MB
      maxEntries: 1000,
      compression: true,
      version: '1.0.0',
      enableLogging: false,
      enableMetrics: true,
      ...config,
    };

    this.cache = new Map();
    this.metrics = this.initMetrics();
    this.cleanupInterval = 60 * 1000; // 1分钟清理一次
    this.cleanupTimer = null;

    this.startCleanup();
  }

  /**
   * 初始化性能指标
   */
  private initMetrics(): CacheMetrics {
    return {
      totalHits: 0,
      totalMisses: 0,
      totalEvictions: 0,
      totalSize: 0,
      hitRate: 0,
      evictionCount: 0,
      loadTime: 0,
      memoryUsage: 0,
    };
  }

  /**
   * 生成缓存键
   */
  private generateKey(namespace: string, key: string): string {
    return `${namespace}:${key}`;
  }

  /**
   * 检查缓存项是否过期
   */
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  /**
   * 计算缓存项大小
   */
  private calculateSize(data: any): number {
    return JSON.stringify(data).length * 2; // 粗略估算
  }

  /**
   * 压缩数据
   */
  private compressData(data: any): any {
    if (!this.config.compression) return data;
    
    // 这里可以实现实际的压缩算法
    // 目前返回原始数据
    return data;
  }

  /**
   * 解压缩数据
   */
  private decompressData(data: any): any {
    if (!this.config.compression) return data;
    
    // 这里可以实现实际的解压缩算法
    // 目前返回原始数据
    return data;
  }

  /**
   * 检查缓存大小限制
   */
  private checkSizeLimit(): void {
    let totalSize = 0;
    
    for (const entry of this.cache.values()) {
      totalSize += entry.size;
      
      if (totalSize > this.config.maxSize) {
        this.evictOldest();
      }
    }
  }

  /**
   * 驱逐最旧的缓存项
   */
  private evictOldest(): void {
    if (this.cache.size === 0) return;

    let oldestKey = '';
    let oldestTimestamp = Infinity;

    for (const [key, entry] of this.cache.entries()) {
      if (entry.timestamp < oldestTimestamp) {
        oldestTimestamp = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.metrics.totalEvictions++;
      this.metrics.evictionCount++;
      
      if (this.config.enableLogging) {
        console.log(`[Cache] Evicted item: ${oldestKey}`);
      }
    }
  }

  /**
   * 检查条目限制
   */
  private checkEntryLimit(): void {
    if (this.cache.size >= this.config.maxEntries) {
      this.evictOldest();
    }
  }

  /**
   * 开始清理过期缓存
   */
  private startCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.cleanupTimer = setInterval(() => {
      this.cleanupExpired();
    }, this.cleanupInterval);

    if (this.config.enableLogging) {
      console.log(`[Cache] Cleanup started with interval: ${this.cleanupInterval}ms`);
    }
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
   * 清理过期缓存
   */
  private cleanupExpired(): void {
    const keysToDelete: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (this.isExpired(entry)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => {
      this.cache.delete(key);
      this.metrics.totalEvictions++;
    });

    if (keysToDelete.length > 0 && this.config.enableLogging) {
      console.log(`[Cache] Cleaned up ${keysToDelete.length} expired items`);
    }
  }

  /**
   * 获取缓存项
   */
  public async get<T = any>(namespace: string, key: string): Promise<T | null> {
    const fullKey = this.generateKey(namespace, key);
    const entry = this.cache.get(fullKey);

    if (!entry) {
      this.metrics.totalMisses++;
      return null;
    }

    if (this.isExpired(entry)) {
      this.cache.delete(fullKey);
      this.metrics.totalMisses++;
      this.metrics.totalEvictions++;
      return null;
    }

    // 更新命中次数
    entry.hitCount++;
    this.metrics.totalHits++;

    // 计算命中率
    const totalRequests = this.metrics.totalHits + this.metrics.totalMisses;
    this.metrics.hitRate = totalRequests > 0 ? (this.metrics.totalHits / totalRequests) * 100 : 0;

    if (this.config.enableLogging) {
      console.log(`[Cache] Hit: ${fullKey}, count: ${entry.hitCount}`);
    }

    return this.decompressData(entry.data);
  }

  /**
   * 设置缓存项
   */
  public async set<T = any>(
    namespace: string,
    key: string,
    data: T,
    options: CacheOptions = {}
  ): Promise<void> {
    const fullKey = this.generateKey(namespace, key);
    const now = Date.now();

    const entry: CacheEntry<T> = {
      data: this.compressData(data),
      timestamp: now,
      ttl: options.ttl || this.config.defaultTTL,
      key: fullKey,
      version: options.version || this.config.version,
      tags: options.tags || [],
      hitCount: 0,
      size: this.calculateSize(data),
    };

    // 检查条目限制
    this.checkEntryLimit();

    // 检查大小限制
    this.checkSizeLimit();

    this.cache.set(fullKey, entry);
    this.metrics.totalSize += entry.size;

    if (this.config.enableLogging) {
      console.log(`[Cache] Set: ${fullKey}, size: ${entry.size} bytes`);
    }
  }

  /**
   * 删除缓存项
   */
  public async delete(namespace: string, key: string): Promise<boolean> {
    const fullKey = this.generateKey(namespace, key);
    const entry = this.cache.get(fullKey);

    if (entry) {
      this.cache.delete(fullKey);
      this.metrics.totalSize -= entry.size;
      this.metrics.totalEvictions++;
      
      if (this.config.enableLogging) {
        console.log(`[Cache] Deleted: ${fullKey}`);
      }
      
      return true;
    }

    return false;
  }

  /**
   * 批量删除
   */
  public async deleteByTag(tag: string): Promise<number> {
    let deletedCount = 0;
    const keysToDelete: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (entry.tags.includes(tag)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => {
      const entry = this.cache.get(key);
      if (entry) {
        this.metrics.totalSize -= entry.size;
        this.cache.delete(key);
        deletedCount++;
      }
    });

    if (deletedCount > 0 && this.config.enableLogging) {
      console.log(`[Cache] Deleted ${deletedCount} items with tag: ${tag}`);
    }

    return deletedCount;
  }

  /**
   * 清空缓存
   */
  public async clear(): Promise<void> {
    const size = this.cache.size;
    this.cache.clear();
    this.metrics.totalSize = 0;
    this.metrics.totalEvictions += size;

    if (this.config.enableLogging) {
      console.log(`[Cache] Cleared all items`);
    }
  }

  /**
   * 获取缓存项统计信息
   */
  public async getStats(namespace?: string): Promise<{
    count: number;
    totalSize: number;
    hitRate: number;
    topKeys: Array<{ key: string; hits: number; size: number }>;
  }> {
    let relevantCache = this.cache;
    
    if (namespace) {
      const namespacePrefix = `${namespace}:`;
      const filtered = new Map<string, CacheEntry>();
      
      for (const [key, entry] of this.cache.entries()) {
        if (key.startsWith(namespacePrefix)) {
          filtered.set(key, entry);
        }
      }
      
      relevantCache = filtered;
    }

    const stats = {
      count: relevantCache.size,
      totalSize: 0,
      hitRate: this.metrics.hitRate,
      topKeys: [] as Array<{ key: string; hits: number; size: number }>,
    };

    // 按命中次数排序
    const sortedEntries = Array.from(relevantCache.entries())
      .sort(([, a], [, b]) => b.hitCount - a.hitCount)
      .slice(0, 10); // 只取前10个

    sortedEntries.forEach(([key, entry]) => {
      stats.totalSize += entry.size;
      stats.topKeys.push({
        key,
        hits: entry.hitCount,
        size: entry.size,
      });
    });

    return stats;
  }

  /**
   * 获取性能指标
   */
  public getMetrics(): CacheMetrics {
    return { ...this.metrics };
  }

  /**
   * 更新配置
   */
  public updateConfig(newConfig: Partial<CacheConfig>): void {
    this.config = { ...this.config, ...newConfig };
    
    // 重新启动清理器
    this.stopCleanup();
    this.startCleanup();
  }

  /**
   * 获取缓存项列表
   */
  public async list(namespace?: string): Promise<Array<{
    key: string;
    size: number;
    hits: number;
    ttl: number;
    expired: boolean;
  }>> {
    let relevantCache = this.cache;
    
    if (namespace) {
      const namespacePrefix = `${namespace}:`;
      const filtered = new Map<string, CacheEntry>();
      
      for (const [key, entry] of this.cache.entries()) {
        if (key.startsWith(namespacePrefix)) {
          filtered.set(key, entry);
        }
      }
      
      relevantCache = filtered;
    }

    const items = [];

    for (const [key, entry] of relevantCache.entries()) {
      items.push({
        key,
        size: entry.size,
        hits: entry.hitCount,
        ttl: entry.ttl,
        expired: this.isExpired(entry),
      });
    }

    return items;
  }

  /**
   * 预热缓存
   */
  public async warmup<T>(
    namespace: string,
    items: Array<{ key: string; data: T; options?: CacheOptions }>
  ): Promise<void> {
    const startTime = performance.now();
    
    for (const item of items) {
      await this.set(namespace, item.key, item.data, item.options);
    }
    
    const endTime = performance.now();
    this.metrics.loadTime += endTime - startTime;

    if (this.config.enableLogging) {
      console.log(`[Cache] Warmed up ${items.length} items in ${endTime - startTime}ms`);
    }
  }

  /**
   * 背景刷新
   */
  public async backgroundRefresh<T>(
    namespace: string,
    key: string,
    fetchFn: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    // 如果启用了stale-while-revalidate，先返回旧数据
    if (options.staleWhileRevalidate) {
      const cachedData = await this.get<T>(namespace, key);
      if (cachedData) {
        // 异步刷新
        this.set(namespace, key, await fetchFn(), options)
          .catch(error => {
            if (this.config.enableLogging) {
              console.error(`[Cache] Background refresh failed for ${key}:`, error);
            }
          });
        
        return cachedData;
      }
    }

    // 获取新数据
    const newData = await fetchFn();
    await this.set(namespace, key, newData, options);
    
    return newData;
  }

  /**
   * 检查缓存项是否存在
   */
  public async has(namespace: string, key: string): Promise<boolean> {
    const fullKey = this.generateKey(namespace, key);
    const entry = this.cache.get(fullKey);

    if (!entry) {
      return false;
    }

    if (this.isExpired(entry)) {
      this.cache.delete(fullKey);
      this.metrics.totalEvictions++;
      return false;
    }

    return true;
  }

  /**
   * 获取缓存项TTL
   */
  public async getTTL(namespace: string, key: string): Promise<number | null> {
    const fullKey = this.generateKey(namespace, key);
    const entry = this.cache.get(fullKey);

    if (!entry) {
      return null;
    }

    const remainingTime = entry.ttl - (Date.now() - entry.timestamp);
    return Math.max(0, remainingTime);
  }

  /**
   * 更新缓存项TTL
   */
  public async touch(namespace: string, key: string, ttl?: number): Promise<boolean> {
    const fullKey = this.generateKey(namespace, key);
    const entry = this.cache.get(fullKey);

    if (!entry) {
      return false;
    }

    entry.timestamp = Date.now();
    entry.ttl = ttl || entry.ttl;

    return true;
  }

  /**
   * 销毁缓存管理器
   */
  public destroy(): void {
    this.stopCleanup();
    this.cache.clear();
    this.metrics = this.initMetrics();
  }
}

// 创建默认缓存管理器实例
export const cacheManager = new CacheManager({
  defaultTTL: 5 * 60 * 1000, // 5分钟
  maxSize: 50 * 1024 * 1024, // 50MB
  maxEntries: 1000,
  compression: true,
  version: '1.0.0',
  enableLogging: process.env.NODE_ENV === 'development',
  enableMetrics: true,
});

export default CacheManager;