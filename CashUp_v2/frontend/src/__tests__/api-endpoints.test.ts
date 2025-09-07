import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi } from '../hooks/useApi';
import { authAPI, tradingAPI, strategyAPI } from '../services/api';

// Mock axios
jest.mock('axios');
const mockedAxios = jest.mocked(require('axios').default);

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
  global.localStorage = localStorageMock as any;
});

describe('API Endpoints Integration Tests', () => {
  describe('Authentication API', () => {
    test('should login successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'mock-token',
          token_type: 'bearer',
          user: {
            id: '1',
            username: 'testuser',
            email: 'testuser@example.com'
          }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('login', {
          username: 'testuser',
          password: 'password123'
        });
        
        expect(response).toEqual(mockResponse.data);
        expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'mock-token');
      });
    });

    test('should handle login failure', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockRejectedValue(mockError),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        await expect(result.current.callAPI('login', {
          username: 'invalid',
          password: 'wrongpass'
        })).rejects.toThrow('Invalid credentials');
      });
    });

    test('should register new user', async () => {
      const mockResponse = {
        data: {
          message: 'User registered successfully',
          user: {
            id: '1',
            username: 'newuser',
            email: 'newuser@example.com'
          }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('register', {
          username: 'newuser',
          email: 'newuser@example.com',
          password: 'password123'
        });
        
        expect(response).toEqual(mockResponse.data);
      });
    });
  });

  describe('Trading API', () => {
    beforeEach(() => {
      localStorageMock.getItem.mockReturnValue('mock-token');
    });

    test('should fetch account balances', async () => {
      const mockResponse = {
        data: {
          total_balance: 10000,
          available_balance: 8000,
            margin_balance: 2000,
          positions: [
            {
              symbol: 'BTCUSDT',
              quantity: 0.1,
              pnl: 100
            }
          ]
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getBalances');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/v1/balances');
      });
    });

    test('should place order', async () => {
      const mockResponse = {
        data: {
          order_id: '12345',
          symbol: 'BTCUSDT',
          side: 'buy',
          type: 'limit',
          quantity: 0.1,
          price: 50000,
          status: 'pending'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('createOrder', {
          symbol: 'BTCUSDT',
          side: 'buy',
          type: 'limit',
          quantity: 0.1,
          price: 50000
        });
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().post).toHaveBeenCalledWith('/orders', {
          symbol: 'BTCUSDT',
          side: 'buy',
          type: 'limit',
          quantity: 0.1,
          price: 50000
        });
      });
    });

    test('should cancel order', async () => {
      const mockResponse = {
        data: {
          message: 'Order cancelled successfully'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        delete: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('cancelOrder', '12345');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().delete).toHaveBeenCalledWith('/orders/12345');
      });
    });

    test('should fetch positions', async () => {
      const mockResponse = {
        data: [
          {
            id: '1',
            symbol: 'BTCUSDT',
            side: 'long',
            quantity: 0.1,
            entry_price: 50000,
            current_price: 51000,
            pnl: 100
          }
        ]
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getPositions');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/v1/positions');
      });
    });

    test('should close position', async () => {
      const mockResponse = {
        data: {
          message: 'Position closed successfully'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('closePosition', '1');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().post).toHaveBeenCalledWith('/positions/1/close');
      });
    });
  });

  describe('Strategy API', () => {
    beforeEach(() => {
      localStorageMock.getItem.mockReturnValue('mock-token');
    });

    test('should fetch strategies', async () => {
      const mockResponse = {
        data: [
          {
            id: '1',
            name: 'Moving Average Strategy',
            status: 'running',
            symbol: 'BTCUSDT',
            timeframe: '1h',
            pnl: 1000
          }
        ]
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getStrategies');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/strategies');
      });
    });

    test('should create strategy', async () => {
      const mockResponse = {
        data: {
          id: '1',
          name: 'New Strategy',
          status: 'created',
          config: {
            indicators: [
              { type: 'sma', period: 20 }
            ]
          }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('createStrategy', {
          name: 'New Strategy',
          symbol: 'BTCUSDT',
          config: {
            indicators: [
              { type: 'sma', period: 20 }
            ]
          }
        });
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().post).toHaveBeenCalledWith('/strategies', {
          name: 'New Strategy',
          symbol: 'BTCUSDT',
          config: {
            indicators: [
              { type: 'sma', period: 20 }
            ]
          }
        });
      });
    });

    test('should start strategy', async () => {
      const mockResponse = {
        data: {
          message: 'Strategy started successfully'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('startStrategy', '1');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().post).toHaveBeenCalledWith('/strategies/1/start');
      });
    });

    test('should stop strategy', async () => {
      const mockResponse = {
        data: {
          message: 'Strategy stopped successfully'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('stopStrategy', '1');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().post).toHaveBeenCalledWith('/strategies/1/stop');
      });
    });

    test('should fetch backtests', async () => {
      const mockResponse = {
        data: [
          {
            id: '1',
            name: 'Backtest 1',
            status: 'completed',
            pnl: 1000,
            win_rate: 65
          }
        ]
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getBacktests');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/backtest');
      });
    });

    test('should create backtest', async () => {
      const mockResponse = {
        data: {
          id: '1',
          name: 'New Backtest',
          status: 'running'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('createBacktest', {
          name: 'New Backtest',
          symbol: 'BTCUSDT',
          timeframe: '1h',
          start_date: '2023-01-01',
          end_date: '2023-12-31'
        });
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().post).toHaveBeenCalledWith('/backtest', {
          name: 'New Backtest',
          symbol: 'BTCUSDT',
          timeframe: '1h',
          start_date: '2023-01-01',
          end_date: '2023-12-31'
        });
      });
    });
  });

  describe('Market Data API', () => {
    beforeEach(() => {
      localStorageMock.getItem.mockReturnValue('mock-token');
    });

    test('should fetch real-time data', async () => {
      const mockResponse = {
        data: {
          symbol: 'BTCUSDT',
          price: 50000,
          change24h: 2.5,
          volume24h: 1000000,
          timestamp: '2023-12-31T00:00:00Z'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getRealTimeData', 'BTCUSDT');
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/data/realtime/BTCUSDT');
      });
    });

    test('should fetch multiple symbols data', async () => {
      const mockResponse = {
        data: [
          {
            symbol: 'BTCUSDT',
            price: 50000,
            change24h: 2.5
          },
          {
            symbol: 'ETHUSDT',
            price: 3000,
            change24h: 1.8
          }
        ]
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getMultipleRealTimeData', ['BTCUSDT', 'ETHUSDT']);
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/data/realtime', {
          params: { symbols: 'BTCUSDT,ETHUSDT' }
        });
      });
    });

    test('should fetch historical data', async () => {
      const mockResponse = {
        data: [
          {
            timestamp: '2023-12-31T00:00:00Z',
            open: 49500,
            high: 50500,
            low: 49000,
            close: 50000,
            volume: 100000
          }
        ]
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getHistoricalData', 'BTCUSDT', {
          timeframe: '1h',
          limit: 100
        });
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledWith('/data/historical/BTCUSDT', {
          params: { timeframe: '1h', limit: 100 }
        });
      });
    });
  });

  describe('Error Handling', () => {
    test('should handle 401 errors', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Unauthorized' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(mockError),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        await expect(result.current.callAPI('getCurrentUser')).rejects.toThrow('Unauthorized');
      });

      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
    });

    test('should handle 429 rate limit errors', async () => {
      const mockError = {
        response: {
          status: 429,
          data: { error: 'Rate limit exceeded' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(mockError),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        await expect(result.current.callAPI('getBalances')).rejects.toThrow('Rate limit exceeded');
      });

      expect(console.error).toHaveBeenCalledWith('请求频率限制:', mockError.response.data);
    });

    test('should handle 500 server errors', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal server error' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(mockError),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        await expect(result.current.callAPI('getBalances')).rejects.toThrow('Internal server error');
      });

      expect(console.error).toHaveBeenCalledWith('服务器错误:', mockError.response.data);
    });

    test('should handle network errors', async () => {
      const networkError = new Error('Network error');
      networkError.code = 'ERR_NETWORK';

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(networkError),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        await expect(result.current.callAPI('getBalances')).rejects.toThrow('Network error');
      });

      expect(console.error).toHaveBeenCalledWith('网络错误:', networkError.message);
    });
  });

  describe('Request Retry', () => {
    test('should retry failed requests', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { error: 'Internal server error' }
        }
      };

      const mockResponse = {
        data: {
          total_balance: 10000
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn()
          .mockRejectedValue(mockError)
          .mockResolvedValueOnce(mockResponse),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        const response = await result.current.callAPI('getBalances', {}, { retry: true });
        
        expect(response).toEqual(mockResponse.data);
        expect(mockedAxios.create().get).toHaveBeenCalledTimes(2);
      });
    });

    test('should not retry non-retryable errors', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Unauthorized' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(mockError),
      } as any);

      const { result } = renderHook(() => useApi());

      await act(async () => {
        await expect(result.current.callAPI('getBalances', {}, { retry: true })).rejects.toThrow('Unauthorized');
      });

      expect(mockedAxios.create().get).toHaveBeenCalledTimes(1);
    });
  });
});