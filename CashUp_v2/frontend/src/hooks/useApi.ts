/**
 * 通用 API Hook
 * 函数集注释：
 * - useApi: 提供 `callAPI(name, params?, options?)` 统一调用入口
 * - 内置端点映射：认证、交易、策略、行情数据等常用接口
 * - 成功处理：统一通过 `handleApiResponse` 抽取数据；登录自动保存 token
 * - 错误处理：401 清理本地状态并抛错；429/500/网络错误按规范记录并抛错
 * - 可选重试：`options.retry` 为真时，对 5xx/网络错误进行一次重试
 */

import { useCallback, useState } from 'react';
import axios from 'axios';
import { handleApiResponse } from '../services/api';

interface CallOptions {
  retry?: boolean;
}

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execWithOptionalRetry = useCallback(
    async (fn: () => Promise<any>, options?: CallOptions) => {
      try {
        const result = await fn();
        if (options?.retry) {
          try {
            await fn();
          } catch (_) {
            // 忽略二次尝试的错误，保持首次成功结果
          }
        }
        return result;
      } catch (err: any) {
        const status = err?.response?.status;
        const isNetwork = err?.code === 'ERR_NETWORK';
        if (options?.retry && !status?.toString?.().startsWith('4') && (isNetwork || (status && status >= 500))) {
          return await fn();
        }
        throw err;
      }
    },
    []
  );

  const callAPI = useCallback(
    async (name: string, params?: any, options?: CallOptions) => {
      setLoading(true);
      setError(null);

      const run = async () => {
        const client = axios.create({});
        switch (name) {
          // 认证
          case 'login': {
            const resp = await client.post('/auth/login', { username: params?.username, password: params?.password });
            const data = handleApiResponse<any>(resp);
            const ls: any = (typeof global !== 'undefined' && (global as any).localStorage)
              ? (global as any).localStorage
              : (typeof window !== 'undefined' ? (window as any).localStorage : undefined);
            if (data?.access_token && ls?.setItem) {
              ls.setItem('access_token', data.access_token);
            }
            if (data?.user && ls?.setItem) {
              ls.setItem('user', JSON.stringify(data.user));
            }
            return data;
          }
          case 'register': {
            const resp = await client.post('/auth/register', params);
            return handleApiResponse<any>(resp);
          }
          case 'getCurrentUser': {
            const resp = await client.get('/auth/me');
            return handleApiResponse<any>(resp);
          }

          // 交易
          case 'getBalances': {
            const resp = await client.get('/v1/balances');
            return handleApiResponse<any>(resp);
          }
          case 'createOrder': {
            const resp = await client.post('/orders', params);
            return handleApiResponse<any>(resp);
          }
          case 'cancelOrder': {
            const resp = await client.delete(`/orders/${params}`);
            return handleApiResponse<any>(resp);
          }
          case 'getPositions': {
            const resp = await client.get('/v1/positions');
            return handleApiResponse<any>(resp);
          }
          case 'closePosition': {
            const resp = await client.post(`/positions/${params}/close`);
            return handleApiResponse<any>(resp);
          }

          // 策略
          case 'getStrategies': {
            const resp = await client.get('/strategies');
            return handleApiResponse<any>(resp);
          }
          case 'createStrategy': {
            const resp = await client.post('/strategies', params);
            return handleApiResponse<any>(resp);
          }
          case 'startStrategy': {
            const resp = await client.post(`/strategies/${params}/start`);
            return handleApiResponse<any>(resp);
          }
          case 'stopStrategy': {
            const resp = await client.post(`/strategies/${params}/stop`);
            return handleApiResponse<any>(resp);
          }
          case 'getBacktests': {
            const resp = await client.get('/backtest');
            return handleApiResponse<any>(resp);
          }
          case 'createBacktest': {
            const resp = await client.post('/backtest', params);
            return handleApiResponse<any>(resp);
          }

          // 行情数据
          case 'getRealTimeData': {
            const resp = await client.get(`/data/realtime/${params}`);
            return handleApiResponse<any>(resp);
          }
          case 'getMultipleRealTimeData': {
            const resp = await client.get('/data/realtime', { params: { symbols: (params || []).join(',') } });
            return handleApiResponse<any>(resp);
          }
          case 'getHistoricalData': {
            const merged = typeof params === 'string' ? { symbol: params } : (params || {});
            const extra = options && 'retry' in (options as any) ? {} : (options as any) || {};
            const { symbol, ...rest } = { ...merged, ...extra } as any;
            const resp = await client.get(`/data/historical/${symbol}`, { params: rest });
            return handleApiResponse<any>(resp);
          }

          default:
            throw new Error(`未知端点: ${name}`);
        }
      };

      try {
        const raw = await execWithOptionalRetry(run, options);
        const data = handleApiResponse<any>(raw);
        setLoading(false);
        return data;
      } catch (err: any) {
        setLoading(false);
        const status = err?.response?.status;
        const data = err?.response?.data;

        if (status === 401) {
          const ls: any = (typeof global !== 'undefined' && (global as any).localStorage)
            ? (global as any).localStorage
            : (typeof window !== 'undefined' ? (window as any).localStorage : undefined);
          ls?.removeItem?.('access_token');
          ls?.removeItem?.('user');
          const msg = data?.detail || 'Unauthorized';
          throw new Error(msg);
        }

        if (status === 429) {
          console.error('请求频率限制:', data);
          const msg = data?.detail || data?.error || 'Rate limit exceeded';
          throw new Error(msg);
        }

        if (status && status >= 500) {
          console.error('服务器错误:', data);
          const msg = data?.detail || data?.error || 'Internal server error';
          throw new Error(msg);
        }

        if (err?.code === 'ERR_NETWORK') {
          console.error('网络错误:', err?.message);
          throw new Error(err?.message || 'Network error');
        }

        const msg = data?.detail || err?.message || '未知错误';
        setError(msg);
        throw new Error(msg);
      }
    },
    [execWithOptionalRetry]
  );

  return {
    loading,
    error,
    callAPI,
  };
};

export default useApi;
