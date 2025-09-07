/**
 * 数据缓存工具 - 避免重复API调用
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

interface CacheOptions {
  ttl?: number; // Default: 5 minutes
  key?: string;
}

class DataCache {
  private cache = new Map<string, CacheEntry<any>>();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  // 生成缓存键
  private generateKey(endpoint: string, params?: any): string {
    if (!params) {
      return endpoint;
    }
    return `${endpoint}_${JSON.stringify(params)}`;
  }

  // 检查缓存是否过期
  private isExpired(entry: CacheEntry<any>): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  // 获取数据
  public get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) {
      return null;
    }
    
    if (this.isExpired(entry)) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }

  // 设置数据
  public set<T>(key: string, data: T, ttl: number = this.defaultTTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  // 删除数据
  public delete(key: string): void {
    this.cache.delete(key);
  }

  // 清空缓存
  public clear(): void {
    this.cache.clear();
  }

  // 获取缓存大小
  public size(): number {
    return this.cache.size;
  }

  // 带缓存的API调用
  public async fetchWithCache<T>(
    endpoint: string,
    apiCall: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    const { ttl = this.defaultTTL, key } = options;
    const cacheKey = key || this.generateKey(endpoint);
    
    // 先从缓存获取
    const cachedData = this.get<T>(cacheKey);
    if (cachedData) {
      return cachedData;
    }
    
    // 调用API
    const data = await apiCall();
    
    // 存入缓存
    this.set(cacheKey, data, ttl);
    
    return data;
  }

  // 批量获取数据（避免重复请求）
  public async batchFetch<T>(
    requests: Array<{
      key: string;
      apiCall: () => Promise<T>;
      ttl?: number;
    }>
  ): Promise<Map<string, T>> {
    const results = new Map<string, T>();
    const pendingRequests: Array<{ key: string; promise: Promise<T> }> = [];

    // 检查缓存
    requests.forEach(({ key }) => {
      const cachedData = this.get<T>(key);
      if (cachedData) {
        results.set(key, cachedData);
      } else {
        pendingRequests.push({
          key,
          promise: requests.find(r => r.key === key)!.apiCall()
        });
      }
    });

    // 执行未缓存的请求
    if (pendingRequests.length > 0) {
      const promises = pendingRequests.map(async ({ key, promise }) => {
        const data = await promise;
        results.set(key, data);
        this.set(key, data);
        return { key, data };
      });

      await Promise.all(promises);
    }

    return results;
  }

  // 预加载热门数据
  public async preload<T>(
    endpoints: Array<{
      key: string;
      apiCall: () => Promise<T>;
      ttl?: number;
    }>
  ): Promise<void> {
    const promises = endpoints.map(({ key, apiCall, ttl }) => 
      this.fetchWithCache(key, apiCall, { ttl })
    );
    
    await Promise.all(promises);
  }
}

// 创建全局缓存实例
export const dataCache = new DataCache();

// 导出缓存Hook供React组件使用
export const useCache = () => {
  const get = <T>(key: string): T | null => dataCache.get<T>(key);
  
  const set = <T>(key: string, data: T, ttl?: number): void => {
    dataCache.set(key, data, ttl);
  };
  
  const clear = (): void => dataCache.clear();
  
  return { get, set, clear };
};

export default dataCache;