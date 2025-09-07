/**
 * 优化的加载状态管理Hook
 */

import { useState, useCallback, useEffect } from 'react';

interface LoadingState {
  loading: boolean;
  error: string | null;
  data: any;
}

interface UseLoadingOptions {
  initialLoading?: boolean;
  timeout?: number;
  retryCount?: number;
  onSuccess?: (data: any) => void;
  onError?: (error: string) => void;
}

export const useLoading = (options: UseLoadingOptions = {}) => {
  const {
    initialLoading = false,
    timeout = 30000, // 30 seconds default timeout
    retryCount = 0,
    onSuccess,
    onError
  } = options;

  const [state, setState] = useState<LoadingState>({
    loading: initialLoading,
    error: null,
    data: null
  });

  const [retryAttempts, setRetryAttempts] = useState(0);

  const execute = useCallback(async (
    asyncFunction: () => Promise<any>,
    customOptions?: Partial<UseLoadingOptions>
  ): Promise<any> => {
    const finalOptions = { ...options, ...customOptions };
    let timeoutId: NodeJS.Timeout | null = null;

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));

      // 设置超时
      const timeoutPromise = new Promise((_, reject) => {
        timeoutId = setTimeout(() => {
          reject(new Error('Operation timeout'));
        }, finalOptions.timeout);
      });

      // 执行异步函数
      const result = await Promise.race([asyncFunction(), timeoutPromise]);

      setState(prev => ({ ...prev, loading: false, data: result }));
      setRetryAttempts(0);

      if (finalOptions.onSuccess) {
        finalOptions.onSuccess(result);
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      // 重试逻辑
      if (finalOptions.retryCount && retryAttempts < finalOptions.retryCount) {
        setRetryAttempts(prev => prev + 1);
        return execute(asyncFunction, customOptions);
      }

      setState(prev => ({ 
        ...prev, 
        loading: false, 
        error: errorMessage 
      }));

      if (finalOptions.onError) {
        finalOptions.onError(errorMessage);
      }

      throw error;
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  }, [options, retryAttempts]);

  const reset = useCallback(() => {
    setState({
      loading: false,
      error: null,
      data: null
    });
    setRetryAttempts(0);
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
  }, []);

  const setData = useCallback((data: any) => {
    setState(prev => ({ ...prev, data }));
  }, []);

  return {
    ...state,
    execute,
    reset,
    setLoading,
    setError,
    setData,
    retryAttempts
  };
};

// 批量加载状态管理
export const useBatchLoading = (keys: string[], options: UseLoadingOptions = {}) => {
  const [states, setStates] = useState<{ [key: string]: LoadingState }>(() => {
    const initialStates: { [key: string]: LoadingState } = {};
    keys.forEach(key => {
      initialStates[key] = {
        loading: options.initialLoading || false,
        error: null,
        data: null
      };
    });
    return initialStates;
  });

  const execute = useCallback(async (
    key: string,
    asyncFunction: () => Promise<any>,
    customOptions?: Partial<UseLoadingOptions>
  ): Promise<any> => {
    if (!keys.includes(key)) {
      throw new Error(`Key "${key}" not found in batch loading keys`);
    }

    const finalOptions = { ...options, ...customOptions };

    try {
      setStates(prev => ({
        ...prev,
        [key]: { ...prev[key], loading: true, error: null }
      }));

      const result = await asyncFunction();

      setStates(prev => ({
        ...prev,
        [key]: { ...prev[key], loading: false, data: result }
      }));

      if (finalOptions.onSuccess) {
        finalOptions.onSuccess(result);
      }

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';

      setStates(prev => ({
        ...prev,
        [key]: { ...prev[key], loading: false, error: errorMessage }
      }));

      if (finalOptions.onError) {
        finalOptions.onError(errorMessage);
      }

      throw error;
    }
  }, [keys, options]);

  const executeAll = useCallback(async (
    asyncFunctions: { [key: string]: () => Promise<any> },
    customOptions?: Partial<UseLoadingOptions>
  ): Promise<{ [key: string]: any }> => {
    const promises = keys.map(key => {
      if (asyncFunctions[key]) {
        return execute(key, asyncFunctions[key], customOptions);
      }
      return Promise.resolve();
    });

    return Promise.allSettled(promises);
  }, [keys, execute]);

  const reset = useCallback((key?: string) => {
    if (key) {
      setStates(prev => ({
        ...prev,
        [key]: { loading: false, error: null, data: null }
      }));
    } else {
      const resetStates: { [key: string]: LoadingState } = {};
      keys.forEach(k => {
        resetStates[k] = { loading: false, error: null, data: null };
      });
      setStates(resetStates);
    }
  }, [keys]);

  const getLoadingStates = useCallback(() => {
    return {
      anyLoading: Object.values(states).some(state => state.loading),
      allLoading: Object.values(states).every(state => state.loading),
      loadingCount: Object.values(states).filter(state => state.loading).length,
      hasErrors: Object.values(states).some(state => state.error),
      errors: Object.entries(states)
        .filter(([, state]) => state.error)
        .reduce((acc, [key, state]) => {
          acc[key] = state.error;
          return acc;
        }, {} as { [key: string]: string | null })
    };
  }, [states]);

  return {
    states,
    execute,
    executeAll,
    reset,
    ...getLoadingStates()
  };
};

// 延迟加载Hook
export const useLazyLoad = <T>(
  asyncFunction: () => Promise<T>,
  options: UseLoadingOptions = {}
) => {
  const [loaded, setLoaded] = useState(false);
  const loadingState = useLoading(options);

  const load = useCallback(async (forceReload = false) => {
    if (!loaded || forceReload) {
      const result = await loadingState.execute(asyncFunction);
      setLoaded(true);
      return result;
    }
    return loadingState.data;
  }, [asyncFunction, loadingState, loaded]);

  const reload = useCallback(async () => {
    return load(true);
  }, [load]);

  return {
    ...loadingState,
    load,
    reload,
    loaded
  };
};