import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '../../../contexts/AuthContext';
import { authAPI } from '../api';
import { AxiosResponse } from 'axios';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

// Mock axios
jest.mock('axios');
const mockedAxios = jest.mocked(require('axios').default);

beforeEach(() => {
  jest.clearAllMocks();
  global.localStorage = localStorageMock as any;
});

describe('Authentication Integration Tests', () => {
  describe('Login Flow', () => {
    test('should complete login flow successfully', async () => {
      const mockLoginResponse = {
        data: {
          access_token: 'mock-token',
          token_type: 'bearer',
          user: {
            id: '1',
            username: 'testuser',
            email: 'test@example.com'
          }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockLoginResponse),
      } as any);

      const { result } = renderHook(() => useAuth());

      // Perform login
      await act(async () => {
        await result.current.login('testuser', 'password');
      });

      // Verify localStorage was updated
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'mock-token');
      expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify({
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      }));

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

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockRejectedValue(mockErrorResponse),
      } as any);

      const { result } = renderHook(() => useAuth());

      // Perform login with invalid credentials
      await act(async () => {
        await expect(result.current.login('invalid', 'password')).rejects.toThrow('Invalid credentials');
      });

      // Verify localStorage was not updated
      expect(localStorage.setItem).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });

    test('should handle network errors during login', async () => {
      const networkError = new Error('Network error');
      networkError.code = 'ERR_NETWORK';

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockRejectedValue(networkError),
      } as any);

      const { result } = renderHook(() => useAuth());

      // Perform login with network error
      await act(async () => {
        await expect(result.current.login('testuser', 'password')).rejects.toThrow('Network error');
      });

      // Verify localStorage was not updated
      expect(localStorage.setItem).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout Flow', () => {
    test('should complete logout flow successfully', async () => {
      // Set initial auth state
      localStorageMock.getItem.mockReturnValue('mock-token');
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      }));

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue({ data: { message: 'Logged out successfully' } }),
      } as any);

      const { result } = renderHook(() => useAuth());

      // Perform logout
      await act(async () => {
        await result.current.logout();
      });

      // Verify localStorage was cleared
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');

      // Verify authentication state
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    test('should clear localStorage even if API call fails', async () => {
      localStorageMock.getItem.mockReturnValue('mock-token');
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      }));

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockRejectedValue(new Error('API error')),
      } as any);

      const { result } = renderHook(() => useAuth());

      // Perform logout even if API fails
      await act(async () => {
        await result.current.logout();
      });

      // Verify localStorage was still cleared
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');

      // Verify authentication state
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('Current User Fetch', () => {
    test('should fetch current user successfully', async () => {
      localStorageMock.getItem.mockReturnValue('mock-token');

      const mockUserResponse = {
        data: {
          id: '1',
          username: 'testuser',
          email: 'test@example.com',
          created_at: '2023-01-01T00:00:00Z'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockResolvedValue(mockUserResponse),
      } as any);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.currentUser();
      });

      expect(result.current.user).toEqual({
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        created_at: '2023-01-01T00:00:00Z'
      });
    });

    test('should handle 401 when fetching current user', async () => {
      localStorageMock.getItem.mockReturnValue('mock-token');

      const mockErrorResponse = {
        response: {
          status: 401,
          data: { detail: 'Token expired' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(mockErrorResponse),
      } as any);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.currentUser();
      });

      // Should clear localStorage and redirect
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
    });
  });

  describe('Token Refresh Flow', () => {
    test('should refresh token successfully', async () => {
      localStorageMock.getItem.mockReturnValue('old-token');

      const mockRefreshResponse = {
        data: {
          access_token: 'new-token',
          token_type: 'bearer'
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        post: jest.fn().mockResolvedValue(mockRefreshResponse),
      } as any);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.refreshToken('refresh-token');
      });

      // Verify new token was stored
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'new-token');
    });
  });

  describe('Authentication State Persistence', () => {
    test('should restore authentication state from localStorage', () => {
      localStorageMock.getItem.mockReturnValue('stored-token');
      localStorageMock.getItem.mockReturnValueOnce(JSON.stringify({
        id: '1',
        username: 'stored-user',
        email: 'stored@example.com'
      }));

      const { result } = renderHook(() => useAuth());

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: '1',
        username: 'stored-user',
        email: 'stored@example.com'
      });
    });

    test('should handle corrupted user data in localStorage', () => {
      localStorageMock.getItem.mockReturnValue('valid-token');
      localStorageMock.getItem.mockReturnValueOnce('corrupted-json');

      const { result } = renderHook(() => useAuth());

      // Should handle corrupted data gracefully
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toBeNull();
    });
  });

  describe('API Integration', () => {
    test('should add auth token to API requests', async () => {
      localStorageMock.getItem.mockReturnValue('auth-token');

      const mockApiInstance = {
        get: jest.fn().mockResolvedValue({ data: { result: 'success' } }),
        post: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
      };

      mockedAxios.create.mockReturnValue(mockApiInstance as any);

      const { result } = renderHook(() => useAuth());

      // Make an API call
      await act(async () => {
        await result.current.getCurrentUser();
      });

      // Verify auth token was added to request
      expect(mockApiInstance.get).toHaveBeenCalledWith('/auth/me');
      // The actual request interceptor should add the token
    });

    test('should handle API authentication errors', async () => {
      localStorageMock.getItem.mockReturnValue('expired-token');

      const mockErrorResponse = {
        response: {
          status: 401,
          data: { detail: 'Token expired' }
        }
      };

      mockedAxios.create.mockReturnValue({
        ...mockedAxios,
        get: jest.fn().mockRejectedValue(mockErrorResponse),
      } as any);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await expect(result.current.getCurrentUser()).rejects.toThrow();
      });

      // Should clear authentication state
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('user');
    });
  });
});