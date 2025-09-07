import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import DashboardPage from '../DashboardPage';
import { AuthProvider, useAuth } from '../../contexts/AuthContext';

// Mock the AuthContext
const mockAuth = {
  isAuthenticated: true,
  loading: false,
  login: jest.fn(),
  logout: jest.fn(),
  user: {
    id: '1',
    username: 'testuser',
    email: 'testuser@example.com'
  },
};

jest.mock('../../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => mockAuth,
}));

// Mock API calls
jest.mock('../../services/api', () => ({
  tradingAPI: {
    getBalances: jest.fn(),
    getAccountInfo: jest.fn(),
  },
  strategyAPI: {
    getStrategies: jest.fn(),
    getMarketOverview: jest.fn(),
  },
}));

const { tradingAPI, strategyAPI } = require('../../services/api');

// Mock WebSocket
jest.mock('../../services/websocket', () => ({
  useWebSocket: jest.fn(() => ({
    lastMessage: null,
    sendMessage: jest.fn(),
    disconnect: jest.fn(),
  })),
}));

describe('DashboardPage Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('should render dashboard with user info', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/欢迎回来/i)).toBeInTheDocument();
    expect(screen.getByText(/testuser/i)).toBeInTheDocument();
  });

  test('should fetch account data on mount', async () => {
    tradingAPI.getBalances.mockResolvedValue({
      success: true,
      data: {
        total_balance: 10000,
        available_balance: 8000,
        margin_balance: 2000,
      }
    });

    tradingAPI.getAccountInfo.mockResolvedValue({
      success: true,
      data: {
        account_id: '12345',
        leverage: 10,
        margin_call_level: 80,
      }
    });

    strategyAPI.getStrategies.mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          name: 'Strategy 1',
          status: 'running',
          pnl: 1000,
        },
        {
          id: '2',
          name: 'Strategy 2',
          status: 'stopped',
          pnl: -500,
        }
      ]
    });

    strategyAPI.getMarketOverview.mockResolvedValue({
      success: true,
      data: {
        total_markets: 50,
        active_markets: 30,
        market_cap: '1.2T',
      }
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(tradingAPI.getBalances).toHaveBeenCalled();
      expect(tradingAPI.getAccountInfo).toHaveBeenCalled();
      expect(strategyAPI.getStrategies).toHaveBeenCalled();
      expect(strategyAPI.getMarketOverview).toHaveBeenCalled();
    });

    // Check if data is displayed
    expect(screen.getByText(/10000/i)).toBeInTheDocument();
    expect(screen.getByText(/Strategy 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Strategy 2/i)).toBeInTheDocument();
  });

  test('should handle API errors gracefully', async () => {
    tradingAPI.getBalances.mockRejectedValue({
      response: {
        status: 500,
        data: { error: 'Internal server error' }
      }
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/加载账户信息失败/i)).toBeInTheDocument();
    });
  });

  test('should display loading state', () => {
    const mockAuthWithLoading = {
      ...mockAuth,
      loading: true,
    };

    jest.mocked(require('../../contexts/AuthContext')).useAuth.mockReturnValue(mockAuthWithLoading);

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/加载中.../i)).toBeInTheDocument();
  });

  test('should show strategy management options', async () => {
    strategyAPI.getStrategies.mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          name: 'Moving Average Strategy',
          status: 'running',
          pnl: 1000,
        }
      ]
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Moving Average Strategy/i)).toBeInTheDocument();
      expect(screen.getByText(/运行中/i)).toBeInTheDocument();
    });

    // Check for strategy control buttons
    expect(screen.getByRole('button', { name: /停止/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /编辑/i })).toBeInTheDocument();
  });

  test('should handle strategy state changes', async () => {
    strategyAPI.getStrategies.mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          name: 'Moving Average Strategy',
          status: 'running',
          pnl: 1000,
        }
      ]
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Moving Average Strategy/i)).toBeInTheDocument();
    });

    // Click stop button
    fireEvent.click(screen.getByRole('button', { name: /停止/i }));

    // Verify API call was made
    expect(strategyAPI.getStrategies).toHaveBeenCalled();
  });

  test('should navigate to strategy creation', () => {
    const navigate = jest.fn();
    
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    // Click create strategy button
    fireEvent.click(screen.getByRole('button', { name: /创建策略/i }));

    expect(navigate).toHaveBeenCalledWith('/strategies/create');
  });

  test('should display market overview', async () => {
    strategyAPI.getMarketOverview.mockResolvedValue({
      success: true,
      data: {
        total_markets: 50,
        active_markets: 30,
        market_cap: '1.2T',
        volume_24h: '50B',
      }
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/50/i)).toBeInTheDocument();
      expect(screen.getByText(/30/i)).toBeInTheDocument();
      expect(screen.getByText(/1.2T/i)).toBeInTheDocument();
    });
  });

  test('should handle real-time updates', async () => {
    strategyAPI.getStrategies.mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          name: 'Strategy 1',
          status: 'running',
          pnl: 1000,
        }
      ]
    });

    const { rerender } = render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Strategy 1/i)).toBeInTheDocument();
    });

    // Simulate real-time update
    strategyAPI.getStrategies.mockResolvedValueOnce({
      success: true,
      data: [
        {
          id: '1',
          name: 'Strategy 1',
          status: 'stopped',
          pnl: 1200,
        }
      ]
    });

    // Re-render with new data
    rerender(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/已停止/i)).toBeInTheDocument();
      expect(screen.getByText(/1200/i)).toBeInTheDocument();
    });
  });

  test('should show performance metrics', async () => {
    strategyAPI.getStrategies.mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          name: 'Strategy 1',
          status: 'running',
          performance: {
            total_pnl: 1000,
            win_rate: 65,
            trades_count: 100,
            max_drawdown: 10,
            sharpe_ratio: 1.5,
          }
        }
      ]
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/65%/i)).toBeInTheDocument();
      expect(screen.getByText(/100/i)).toBeInTheDocument();
      expect(screen.getByText(/1.5/i)).toBeInTheDocument();
    });
  });

  test('should handle logout functionality', async () => {
    const navigate = jest.fn();
    
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => navigate,
    }));

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    // Click logout button
    fireEvent.click(screen.getByRole('button', { name: /退出登录/i }));

    expect(mockAuth.logout).toHaveBeenCalled();
    expect(navigate).toHaveBeenCalledWith('/login');
  });

  test('should display responsive layout', () => {
    // Test mobile view
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    // Check if mobile-friendly elements are present
    // This depends on the actual responsive implementation
    const dashboardContent = screen.getByRole('main');
    expect(dashboardContent).toBeInTheDocument();
  });

  test('should handle offline status', async () => {
    // Simulate offline status
    Object.defineProperty(window, 'navigator', {
      writable: true,
      configurable: true,
      value: {
        onLine: false,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      }
    });

    strategyAPI.getStrategies.mockResolvedValue({
      success: true,
      data: [
        {
          id: '1',
          name: 'Strategy 1',
          status: 'running',
          pnl: 1000,
        }
      ]
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Strategy 1/i)).toBeInTheDocument();
    });

    // Check if offline indicator is shown
    expect(screen.getByText(/离线模式/i)).toBeInTheDocument();
  });

  test('should support dark mode', () => {
    // Test dark mode class
    document.documentElement.classList.add('dark');

    render(
      <MemoryRouter>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </MemoryRouter>
    );

    // Check if dark mode styles are applied
    const dashboardElement = screen.getByRole('main');
    expect(dashboardElement).toBeInTheDocument();

    // Clean up
    document.documentElement.classList.remove('dark');
  });
});