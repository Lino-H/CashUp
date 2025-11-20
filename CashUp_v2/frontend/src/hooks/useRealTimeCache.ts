/**
 * 实时数据缓存Hook - 用于缓存实时更新的数据
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface RealTimeCacheOptions {
  ttl?: number; // Time to live in milliseconds
  refreshInterval?: number; // 自动刷新间隔
  staleWhileRevalidate?: boolean; // 是否在后台刷新时返回过期数据
}

export const useRealTimeCache = <T>(
  key: string,
  fetchFunction: () => Promise<T>,
  options: RealTimeCacheOptions = {}
) => {
  const {
    ttl = 30 * 1000, // 30 seconds default for real-time data
    refreshInterval = 10 * 1000, // 10 seconds default refresh interval
    staleWhileRevalidate = true
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [isStale, setIsStale] = useState(false);

  const cacheRef = useRef<Map<string, { data: T; timestamp: number }>>(new Map());
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  // 检查数据是否过期
  const isDataStale = useCallback((timestamp: number): boolean => {
    return Date.now() - timestamp > ttl;
  }, [ttl]);

  // 从缓存获取数据
  const getFromCache = useCallback((): T | null => {
    const cached = cacheRef.current.get(key);
    if (!cached) return null;

    if (isDataStale(cached.timestamp)) {
      setIsStale(true);
      return staleWhileRevalidate ? cached.data : null;
    }

    setIsStale(false);
    return cached.data;
  }, [key, isDataStale, staleWhileRevalidate]);

  // 设置缓存数据
  const setCache = useCallback((newData: T) => {
    const timestamp = Date.now();
    cacheRef.current.set(key, { data: newData, timestamp });
    setData(newData);
    setLastUpdated(timestamp);
    setIsStale(false);
  }, [key]);

  // 获取数据
  const fetchData = useCallback(async (forceRefresh: boolean = false) => {
    if (!forceRefresh) {
      const cached = getFromCache();
      if (cached && !isDataStale(cacheRef.current.get(key)?.timestamp || 0)) {
        return cached;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const result = await fetchFunction();
      if (isMountedRef.current) {
        setCache(result);
      }
      return result;
    } catch (error) {
      if (isMountedRef.current) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setError(errorMessage);
      }
      throw error;
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [fetchFunction, getFromCache, setCache, isDataStale, key]);

  // 自动刷新数据
  const startAutoRefresh = useCallback(() => {
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
    }

    refreshTimerRef.current = setInterval(async () => {
      try {
        await fetchData(true);
      } catch (error) {
        console.error('Auto refresh error:', error);
      }
    }, refreshInterval);
  }, [fetchData, refreshInterval]);

  // 停止自动刷新
  const stopAutoRefresh = useCallback(() => {
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  }, []);

  // 手动刷新数据
  const refresh = useCallback(async () => {
    return fetchData(true);
  }, [fetchData]);

  // 清除缓存
  const clearCache = useCallback(() => {
    cacheRef.current.delete(key);
    setData(null);
    setLastUpdated(null);
    setIsStale(false);
  }, [key]);

  // 初始化
  useEffect(() => {
    isMountedRef.current = true;
    
    // 初始加载数据
    fetchData();

    // 开始自动刷新
    startAutoRefresh();

    return () => {
      isMountedRef.current = false;
      stopAutoRefresh();
    };
  }, []);

  // 监听选项变化
  useEffect(() => {
    stopAutoRefresh();
    startAutoRefresh();
  }, [refreshInterval]);

  return {
    data,
    loading,
    error,
    refresh,
    clearCache,
    lastUpdated,
    isStale,
    refetch: refresh
  };
};

// 批量数据缓存Hook
export const useBatchRealTimeCache = <T>(
  keys: string[],
  fetchFunctions: { [key: string]: () => Promise<T> },
  options: RealTimeCacheOptions = {}
) => {
  const [dataMap, setDataMap] = useState<{ [key: string]: T | null }>({});
  const [loadingMap, setLoadingMap] = useState<{ [key: string]: boolean }>({});
  const [errorMap, setErrorMap] = useState<{ [key: string]: string | null }>({});

  const fetchOne = useCallback(async (key: string, forceRefresh: boolean = false) => {
    try {
      setLoadingMap(prev => ({ ...prev, [key]: true }));
      setErrorMap(prev => ({ ...prev, [key]: null }));
      const data = await fetchFunctions[key]();
      setDataMap(prev => ({ ...prev, [key]: data }));
      return data;
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      setErrorMap(prev => ({ ...prev, [key]: msg }));
      throw e;
    } finally {
      setLoadingMap(prev => ({ ...prev, [key]: false }));
    }
  }, [fetchFunctions]);

  const refreshAll = useCallback(async () => {
    const tasks = keys.map(key => fetchOne(key, true));
    await Promise.allSettled(tasks);
  }, [keys, fetchOne]);

  const clearAllCache = useCallback(() => {
    setDataMap(prev => {
      const next = { ...prev };
      keys.forEach(key => { next[key] = null; });
      return next;
    });
    setErrorMap(prev => {
      const next = { ...prev };
      keys.forEach(key => { next[key] = null; });
      return next;
    });
    setLoadingMap(prev => {
      const next = { ...prev };
      keys.forEach(key => { next[key] = false; });
      return next;
    });
  }, [keys]);

  const caches = keys.reduce((acc, key) => {
    acc[key] = {
      refresh: () => fetchOne(key, true),
      clearCache: () => {
        setDataMap(prev => ({ ...prev, [key]: null }));
        setErrorMap(prev => ({ ...prev, [key]: null }));
        setLoadingMap(prev => ({ ...prev, [key]: false }));
      },
    };
    return acc;
  }, {} as { [key: string]: { refresh: () => Promise<T>; clearCache: () => void } });

  useEffect(() => {
    keys.forEach(key => { fetchOne(key).catch(() => {}); });
  }, [keys, fetchOne]);

  return {
    dataMap,
    loadingMap,
    errorMap,
    caches,
    refreshAll,
    clearAllCache,
  };
};
