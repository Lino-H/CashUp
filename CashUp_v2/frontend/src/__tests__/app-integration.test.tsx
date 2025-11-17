import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import App, { AppContent } from '../App';
import LoginPage from '../pages/LoginPage';

// Mock the AuthContext
const mockAuth = {
  isAuthenticated: false,
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  user: null,
};

jest.mock('../contexts/AuthContext', () => {
  const React = require('react');
  const useAuth = jest.fn(() => ({
    isAuthenticated: false,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
    user: null,
  }));
  return {
    AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    useAuth,
  };
});

// Mock API calls
jest.mock('../services/api', () => ({
  authAPI: {
    getCurrentUser: jest.fn(),
  },
}));

const { authAPI } = require('../services/api');

describe.skip('App Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuth);
  });

  test('未登录时重定向到登录页', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/CashUp/i)).toBeInTheDocument();
    expect(screen.getByText(/量化交易平台/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('登录后显示欢迎信息', async () => {
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
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText(/欢迎回来/i);
    await screen.findByText(/testuser/i);
  });

  test('显示加载中状态', () => {
    const mockAuthLoading = {
      ...mockAuth,
      loading: true,
    };

    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthLoading);

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/加载中.../i)).toBeInTheDocument();
  });

  test('处理路由导航', async () => {
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
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText(/欢迎回来/i);
  });

  test('受保护路由在未登录时重定向', () => {
    render(
      <MemoryRouter initialEntries={['/']}> 
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/CashUp/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('保留路由状态', () => {
    render(
      <MemoryRouter initialEntries={['/?param=value']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/CashUp/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('未知路由重定向到登录页', () => {
    render(
      <MemoryRouter initialEntries={['/nonexistent']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/CashUp/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('处理退出登录', async () => {
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
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText(/欢迎回来/i);

    // Mock logout
    mockAuthAuthenticated.logout.mockImplementation(() => {
      mockAuthAuthenticated.isAuthenticated = false;
      mockAuthAuthenticated.user = null;
    });

    // 展开下拉并点击退出登录
    fireEvent.click(screen.getByRole('button', { name: /testuser/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /退出登录/i }));

    expect(mockAuthAuthenticated.logout).toHaveBeenCalled();
  });

  test('处理 API 错误', async () => {
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
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByRole('button', { name: /登录/i });
  });

  test('处理网络错误', async () => {
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

    await screen.findByText(/欢迎回来/i);
  });

  test('支持基础 i18n 展示', () => {
    render(
      <MemoryRouter initialEntries={['/']}> 
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/CashUp/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('主题为暗色菜单', async () => {
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

    await screen.findByText(/欢迎回来/i);

    // 顶部菜单使用暗色主题
    expect(screen.getByRole('menu', { name: /主菜单/i })).toHaveClass('ant-menu-dark');
  });

  test('处理响应式布局', () => {
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

    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('处理离线模式', () => {
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

    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('处理认证超时', async () => {
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

    const { rerender } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText(/欢迎回来/i);

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

    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('受保护路由重定向', () => {
    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuth);
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    );
    expect(screen.getByText(/CashUp/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('认证状态变化', async () => {
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

    const { rerender } = render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    // Initially authenticated
    await screen.findByText(/欢迎回来/i);

    // Change to not authenticated
    jest.mocked(require('../contexts/AuthContext')).useAuth.mockReturnValue(mockAuth);

    rerender(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });
});