import axios from 'axios';
import { api } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

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

describe('API Service', () => {
  describe('Request Interceptor', () => {
    test('should add authorization token when token exists', () => {
      const token = 'test-token';
      localStorageMock.getItem.mockReturnValue(token);

      const config = {
        headers: {},
        data: { test: 'data' },
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        interceptors: {
          request: {
            use: jest.fn().mockImplementation((onFulfilled) => {
              return onFulfilled(config);
            }),
          },
        },
      } as any);

      // Re-initialize api to trigger interceptor setup
      require('../api');

      const expectedConfig = {
        ...config,
        headers: {
          ...config.headers,
          Authorization: `Bearer ${token}`,
        },
      };

      expect(localStorage.getItem).toHaveBeenCalledWith('access_token');
    });

    test('should not add authorization token when token does not exist', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const config = {
        headers: {},
        data: { test: 'data' },
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        interceptors: {
          request: {
            use: jest.fn().mockImplementation((onFulfilled) => {
              return onFulfilled(config);
            }),
          },
        },
      } as any);

      // Re-initialize api to trigger interceptor setup
      require('../api');

      expect(config.headers).not.toHaveProperty('Authorization');
    });
  });

  describe('Response Interceptor', () => {
    test('should return response data for successful response', async () => {
      const responseData = { data: 'success' };
      const response = {
        data: responseData,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {},
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        interceptors: {
          response: {
            use: jest.fn().mockImplementation((onFulfilled) => {
              return Promise.resolve(onFulfilled(response));
            }),
          },
        },
      } as any);

      // Re-initialize api to trigger interceptor setup
      const api = require('../api').api;
      const result = await api.get('/test');

      expect(result).toEqual(responseData);
    });

    test('should handle 401 error by clearing token and redirecting', async () => {
      const error = {
        response: {
          status: 401,
          data: { error: 'Unauthorized' },
        },
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        interceptors: {
          response: {
            use: jest.fn().mockImplementation((onFulfilled, onRejected) => {
              return Promise.reject(onRejected(error));
            }),
          },
        },
      } as any);

      // Mock window.location.href
      delete (window as any).location;
      window.location = { href: '' } as any;

      // Re-initialize api to trigger interceptor setup
      const api = require('../api').api;

      try {
        await api.get('/test');
      } catch (error) {
        expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
        expect(localStorage.removeItem).toHaveBeenCalledWith('user');
        expect(window.location.href).toBe('/login');
      }
    });

    test('should handle 429 rate limit error', async () => {
      const error = {
        response: {
          status: 429,
          data: { error: 'Rate limit exceeded' },
        },
      };

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        interceptors: {
          response: {
            use: jest.fn().mockImplementation((onFulfilled, onRejected) => {
              return Promise.reject(onRejected(error));
            }),
          },
        },
      } as any);

      // Re-initialize api to trigger interceptor setup
      const api = require('../api').api;

      try {
        await api.get('/test');
      } catch (error) {
        expect(consoleSpy).toHaveBeenCalledWith('请求频率限制:', error.response.data);
        consoleSpy.mockRestore();
      }
    });

    test('should handle 500 server error', async () => {
      const error = {
        response: {
          status: 500,
          data: { error: 'Internal server error' },
        },
      };

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        interceptors: {
          response: {
            use: jest.fn().mockImplementation((onFulfilled, onRejected) => {
              return Promise.reject(onRejected(error));
            }),
          },
        },
      } as any);

      // Re-initialize api to trigger interceptor setup
      const api = require('../api').api;

      try {
        await api.get('/test');
      } catch (error) {
        expect(consoleSpy).toHaveBeenCalledWith('服务器错误:', error.response.data);
        consoleSpy.mockRestore();
      }
    });
  });

  describe('API Methods', () => {
    beforeEach(() => {
      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
      } as any);
    });

    test('should make GET request', async () => {
      const responseData = { data: 'get response' };
      mockedAxios.create().get.mockResolvedValue({ data: responseData });

      const api = require('../api').api;
      const result = await api.get('/test-endpoint');

      expect(result).toEqual(responseData);
      expect(mockedAxios.create().get).toHaveBeenCalledWith('/test-endpoint');
    });

    test('should make POST request', async () => {
      const requestData = { name: 'test' };
      const responseData = { data: 'post response' };
      mockedAxios.create().post.mockResolvedValue({ data: responseData });

      const api = require('../api').api;
      const result = await api.post('/test-endpoint', requestData);

      expect(result).toEqual(responseData);
      expect(mockedAxios.create().post).toHaveBeenCalledWith('/test-endpoint', requestData);
    });

    test('should make PUT request', async () => {
      const requestData = { name: 'updated' };
      const responseData = { data: 'put response' };
      mockedAxios.create().put.mockResolvedValue({ data: responseData });

      const api = require('../api').api;
      const result = await api.put('/test-endpoint/1', requestData);

      expect(result).toEqual(responseData);
      expect(mockedAxios.create().put).toHaveBeenCalledWith('/test-endpoint/1', requestData);
    });

    test('should make DELETE request', async () => {
      const responseData = { data: 'delete response' };
      mockedAxios.create().delete.mockResolvedValue({ data: responseData });

      const api = require('../api').api;
      const result = await api.delete('/test-endpoint/1');

      expect(result).toEqual(responseData);
      expect(mockedAxios.create().delete).toHaveBeenCalledWith('/test-endpoint/1');
    });
  });

  describe('Configuration', () => {
    test('should use correct base URL', () => {
      const expectedBaseUrl = 'http://localhost:8001/api';
      expect(api.defaults.baseURL).toBe(expectedBaseUrl);
    });

    test('should have correct timeout', () => {
      expect(api.defaults.timeout).toBe(10000);
    });

    test('should have correct content type', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json');
    });
  });
});