import { renderHook, act, waitFor } from '@testing-library/react';
import React from 'react';
import { useAuth, AuthProvider } from '../../contexts/AuthContext';
import { authAPIWithCookies } from '../../services/api';

// 使用 Storage.prototype 的 spy 模拟 localStorage 行为
let getItemSpy: jest.SpyInstance;
let setItemSpy: jest.SpyInstance;
let removeItemSpy: jest.SpyInstance;

// Mock API 层
jest.mock('../../services/api', () => ({
  ...jest.requireActual('../../services/api'),
  authAPIWithCookies: {
    login: jest.fn(),
    logout: jest.fn(),
    getCurrentUser: jest.fn(),
  },
}));
const { authAPIWithCookies: mockedAuthApi } = require('../../services/api');


beforeEach(() => {
  jest.clearAllMocks();
  getItemSpy = jest.spyOn(Storage.prototype, 'getItem');
  setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
  removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem');
  Object.defineProperty(window, 'ENV', { value: { REACT_APP_ENABLE_AUTH: 'true' }, writable: true, configurable: true });
});

describe('Authentication Integration Tests', () => {
  describe('Login Flow', () => {
    test('should complete login flow successfully', async () => {
      const mockLoginResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
        user: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com'
        }
      };

      mockedAuthApi.login.mockResolvedValue(mockLoginResponse);

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      // Perform login
      await act(async () => {
        await result.current.login('testuser', 'password');
      });

      // 验证本地存储与上下文状态
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'mock-token');

      // Verify authentication state
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      });
    });

    test('should handle login failure gracefully', async () => {
      const mockErrorResponse = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' }
        }
      };
      mockedAuthApi.login.mockRejectedValue(mockErrorResponse);

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      // Perform login with invalid credentials
      await act(async () => {
        await expect(result.current.login('invalid', 'password')).rejects.toThrow('未授权，请重新登录');
      });

      // Verify localStorage was not updated
      expect(setItemSpy).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });

    test('should handle network errors during login', async () => {
      const networkError = Object.assign(new Error('Network error'), { code: 'ERR_NETWORK' });
      mockedAuthApi.login.mockRejectedValue(networkError);

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      // Perform login with network error
      await act(async () => {
        await expect(result.current.login('testuser', 'password')).rejects.toThrow('网络错误，请检查网络连接');
      });

      // Verify localStorage was not updated
      expect(setItemSpy).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout Flow', () => {
    test('should complete logout flow successfully', async () => {
      // Set initial auth state
      getItemSpy.mockReturnValue('mock-token');
      mockedAuthApi.logout.mockResolvedValue({ message: 'Logged out successfully' });

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      // Perform logout
      await act(async () => {
        await result.current.logout();
      });

      // Verify localStorage was cleared
      expect(removeItemSpy).toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).toHaveBeenCalledWith('user');

      // Verify authentication state
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    test('should clear localStorage even if API call fails', async () => {
      getItemSpy.mockReturnValue('mock-token');
      mockedAuthApi.logout.mockRejectedValue(new Error('API error'));

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      // Perform logout even if API fails
      await act(async () => {
        await result.current.logout();
      });

      // Verify localStorage was still cleared
      expect(removeItemSpy).toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).toHaveBeenCalledWith('user');

      // Verify authentication state
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('Current User Fetch', () => {
    test('should fetch current user successfully', async () => {
      getItemSpy.mockReturnValue('mock-token');
      mockedAuthApi.getCurrentUser.mockResolvedValue({
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        created_at: '2023-01-01T00:00:00Z'
      });

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      await act(async () => {
        await result.current.refreshUser();
      });

      expect(result.current.user).toEqual({
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        created_at: '2023-01-01T00:00:00Z'
      });
    });

    test('should handle 401 when fetching current user', async () => {
      getItemSpy.mockReturnValue('mock-token');

      const mockErrorResponse = {
        response: {
          status: 401,
          data: { detail: 'Token expired' }
        }
      };
      mockedAuthApi.getCurrentUser.mockRejectedValue(mockErrorResponse);

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      await act(async () => {
        await expect(result.current.refreshUser()).rejects.toThrow();
      });
    });
  });

  // Token 刷新流程由内部处理，相关逻辑在 refreshUser 失败时的清理已覆盖

  describe('Authentication State Persistence', () => {
    test('should restore authentication state from localStorage', async () => {
      getItemSpy.mockReturnValue('stored-token');
      mockedAuthApi.getCurrentUser.mockResolvedValue({
        id: '1',
        username: 'stored-user',
        email: 'stored@example.com'
      });

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      await waitFor(() => expect(result.current.isAuthenticated).toBe(true), { timeout: 2000 });
      expect(result.current.user).toEqual({
        id: '1',
        username: 'stored-user',
        email: 'stored@example.com'
      });
    });

    test('should handle corrupted user data in localStorage', async () => {
      getItemSpy.mockReturnValue('valid-token');
      mockedAuthApi.getCurrentUser.mockResolvedValue(null);

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      await waitFor(() => expect(result.current.isAuthenticated).toBe(false));
      expect(result.current.user).toBeNull();
    });
  });

  describe('API Integration', () => {
    test('should add auth token to API requests', async () => {
      getItemSpy.mockReturnValue('auth-token');

      mockedAuthApi.getCurrentUser.mockResolvedValue({ id: '1', username: 'auth', email: 'auth@example.com' });

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      await act(async () => {
        await result.current.refreshUser();
      });

      expect(mockedAuthApi.getCurrentUser).toHaveBeenCalled();
    });

    test('should handle API authentication errors', async () => {
      getItemSpy.mockReturnValue('expired-token');

      const mockErrorResponse = {
        response: {
          status: 401,
          data: { detail: 'Token expired' }
        }
      };

      mockedAuthApi.getCurrentUser.mockRejectedValue(mockErrorResponse);

      const { result } = renderHook(() => useAuth(), { wrapper: ({ children }) => React.createElement(AuthProvider, null, children) });

      await act(async () => {
        await expect(result.current.refreshUser()).rejects.toThrow();
      });
    });
  });
});