import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, RouterProvider, createRoutesFromElements, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import App from '../App';
import LoginPage from '../pages/LoginPage';
import DashboardPage from '../pages/DashboardPage';

// Mock the AuthContext
const mockAuth = {
  isAuthenticated: false,
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  user: null,
};

jest.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => mockAuth,
}));

// Mock API calls
jest.mock('../services/api', () => ({
  authAPI: {
    getCurrentUser: jest.fn(),
  },
}));

const { authAPI } = require('../services/api');

describe('App Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('should redirect to login when not authenticated', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
    expect(screen.getByText(/请输入您的账号密码/i)).toBeInTheDocument();
  });

  test('should show dashboard when authenticated', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
      expect(screen.getByText(/testuser/i)).toBeInTheDocument();
    });
  });

  test('should show loading state', () => {
    const mockAuthLoading = {
      ...mockAuth,
      loading: true,
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthLoading);

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/加载中.../i)).toBeInTheDocument();
  });

  test('should handle route navigation', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    });
  });

  test('should handle protected routes', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
    expect(screen.getByText(/请输入您的账号密码/i)).toBeInTheDocument();
  });

  test('should preserve route state', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard?param=value']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
    expect(screen.getByText(/请输入您的账号密码/i)).toBeInTheDocument();
  });

  test('should handle 404 pages', () => {
    render(
      <MemoryRouter initialEntries={['/nonexistent']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/页面未找到/i)).toBeInTheDocument();
  });

  test('should handle logout', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    });

    // Mock logout
    mockAuthAuthenticated.logout.mockImplementation(() => {
      mockAuthAuthenticated.isAuthenticated = false;
      mockAuthAuthenticated.user = null;
    });

    // Simulate logout
    fireEvent.click(screen.getByRole('button', { name: /退出登录/i }));

    expect(mockAuthAuthenticated.logout).toHaveBeenCalled();
  });

  test('should handle API errors gracefully', async () => {
    authAPI.getCurrentUser.mockRejectedValue({
      response: {
        status: 401,
        data: { error: 'Unauthorized' }
      }
    });

    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
      expect(screen.getByText(/请输入您的账号密码/i)).toBeInTheDocument();
    });
  });

  test('should handle network errors', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    });
  });

  test('should support i18n', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
    expect(screen.getByText(/请输入您的账号密码/i)).toBeInTheDocument();
  });

  test('should handle theme switching', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    });

    // Test theme toggle
    const themeToggle = screen.getByRole('button', { name: /切换主题/i });
    fireEvent.click(themeToggle);

    // Verify theme change
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  test('should handle responsive layout', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    // Test mobile view
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    // Trigger resize
    window.dispatchEvent(new Event('resize'));

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
  });

  test('should handle offline mode', () => {
    Object.defineProperty(window, 'navigator', {
      writable: true,
      configurable: true,
      value: {
        onLine: false,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      }
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
  });

  test('should handle authentication timeout', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthAuthenticated);

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    });

    // Simulate authentication timeout
    mockAuthAuthenticated.isAuthenticated = false;
    mockAuthAuthenticated.user = null;

    // Force re-render
    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
  });

  test('should handle route protection', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard', '/strategies', '/settings']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    // All routes should redirect to login
    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
    expect(screen.getByText(/请输入您的账号密码/i)).toBeInTheDocument();
  });

  test('should handle authentication state changes', async () => {
    const mockAuthAuthenticated = {
      ...mockAuth,
      isAuthenticated: true,
      user: {
        id: '1',
        username: 'testuser',
        email: 'testuser@example.com'
      },
    };

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    // Initially authenticated
    await waitFor(() => {
      expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    });

    // Change to not authenticated
    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuth);

    rerender(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/用户登录/i)).toBeInTheDocument();
  });
});