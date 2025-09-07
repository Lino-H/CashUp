/**
 * 数据缓存Hook - 提供本地数据缓存功能
 */

import { useState, useEffect, useCallback } from 'react';

interface CacheOptions {
  ttl?: number; // Time to live in milliseconds
  storage?: 'localStorage' | 'sessionStorage' | 'memory';
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export const useDataCache = <T>(
  key: string,
  options: CacheOptions = {}
) => {
  const {
    ttl = 5 * 60 * 1000, // 5 minutes default
    storage = 'localStorage'
  } = options;

  const [cachedData, setCachedData] = useState<CacheEntry<T> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 获取存储实例
  const getStorage = () => {
    if (storage === 'localStorage') {
      return localStorage;
    } else if (storage === 'sessionStorage') {
      return sessionStorage;
    }
    return null;
  };

  // 从缓存获取数据
  const getFromCache = useCallback((): T | null => {
    try {
      if (storage === 'memory') {
        const entry = cachedData as CacheEntry<T>;
        if (entry && Date.now() - entry.timestamp < entry.ttl) {
          return entry.data;
        }
        return null;
      }

      const storageInstance = getStorage();
      if (!storageInstance) return null;

      const cached = storageInstance.getItem(key);
      if (!cached) return null;

      const entry: CacheEntry<T> = JSON.parse(cached);
      if (Date.now() - entry.timestamp > entry.ttl) {
        storageInstance.removeItem(key);
        return null;
      }

      return entry.data;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }, [key, storage, cachedData]);

  // 设置缓存数据
  const setCache = useCallback((data: T) => {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        ttl
      };

      if (storage === 'memory') {
        setCachedData(entry);
        return;
      }

      const storageInstance = getStorage();
      if (!storageInstance) return;

      storageInstance.setItem(key, JSON.stringify(entry));
    } catch (error) {
      console.error('Cache write error:', error);
    }
  }, [key, storage, ttl]);

  // 清除缓存
  const clearCache = useCallback(() => {
    try {
      if (storage === 'memory') {
        setCachedData(null);
        return;
      }

      const storageInstance = getStorage();
      if (storageInstance) {
        storageInstance.removeItem(key);
      }
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }, [key, storage]);

  // 获取数据（优先从缓存，如果没有则调用fetch函数）
  const getData = useCallback(async (
    fetchFunction: () => Promise<T>,
    forceRefresh: boolean = false
  ): Promise<T> => {
    setLoading(true);
    setError(null);

    try {
      // 如果不是强制刷新，先尝试从缓存获取
      if (!forceRefresh) {
        const cached = getFromCache();
        if (cached) {
          return cached;
        }
      }

      // 从API获取数据
      const data = await fetchFunction();
      
      // 缓存数据
      setCache(data);
      
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [getFromCache, setCache]);

  // 预加载数据
  const preloadData = useCallback(async (fetchFunction: () => Promise<T>) => {
    try {
      const data = await fetchFunction();
      setCache(data);
    } catch (error) {
      console.error('Preload error:', error);
    }
  }, [setCache]);

  return {
    data: cachedData?.data || null,
    loading,
    error,
    getData,
    preloadData,
    clearCache,
    hasCache: getFromCache() !== null
  };
};

// 全局缓存管理器
export class CacheManager {
  private static instance: CacheManager;
  private memoryCache: Map<string, CacheEntry<any>> = new Map();

  static getInstance(): CacheManager {
    if (!CacheManager.instance) {
      CacheManager.instance = new CacheManager();
    }
    return CacheManager.instance;
  }

  clearAll() {
    this.memoryCache.clear();
    localStorage.clear();
    sessionStorage.clear();
  }

  clearByKey(key: string) {
    this.memoryCache.delete(key);
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  }

  clearByPattern(pattern: string) {
    const regex = new RegExp(pattern);
    
    // 清除内存缓存
    for (const key of Array.from(this.memoryCache.keys())) {
      if (regex.test(key)) {
        this.memoryCache.delete(key);
      }
    }

    // 清除localStorage
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && regex.test(key)) {
        localStorage.removeItem(key);
      }
    }

    // 清除sessionStorage
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && regex.test(key)) {
        sessionStorage.removeItem(key);
      }
    }
  }

  getStats() {
    return {
      memoryCache: this.memoryCache.size,
      localStorage: localStorage.length,
      sessionStorage: sessionStorage.length
    };
  }
}

export const cacheManager = CacheManager.getInstance();