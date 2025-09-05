/**
 * 实时交易监控测试
 * Real-time Trading Monitoring Test
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RealTimeTrading from '../pages/RealTimeTrading';
import { realTimeTradingService } from '../services/realTimeTradingService';

// Mock the real-time trading service
jest.mock('../services/realTimeTradingService');

const mockRealTimeTrades = [
  {
    id: '1',
    strategyName: 'MA Cross Strategy',
    symbol: 'BTCUSDT',
    side: 'buy' as const,
    price: 43250.50,
    quantity: 0.1,
    amount: 4325.05,
    timestamp: new Date().toISOString(),
    exchange: 'Binance',
    status: 'filled' as const,
    orderId: '123456789',
    fee: 4.32,
    pnl: 25.50
  },
  {
    id: '2',
    strategyName: 'RSI Mean Reversion',
    symbol: 'ETHUSDT',
    side: 'sell' as const,
    price: 2250.30,
    quantity: 0.5,
    amount: 1125.15,
    timestamp: new Date(Date.now() - 60000).toISOString(),
    exchange: 'Gate.io',
    status: 'filled' as const,
    orderId: '987654321',
    fee: 1.12,
    pnl: -15.20
  }
];

const mockRealTimePrices = [
  {
    symbol: 'BTCUSDT',
    price: 43250.50,
    change24h: 1250.50,
    changePercent24h: 2.98,
    volume24h: 28500000000,
    high24h: 43800.00,
    low24h: 41800.00,
    timestamp: new Date().toISOString()
  },
  {
    symbol: 'ETHUSDT',
    price: 2250.30,
    change24h: -85.70,
    changePercent24h: -3.67,
    volume24h: 15600000000,
    high24h: 2350.00,
    low24h: 2200.00,
    timestamp: new Date().toISOString()
  }
];

const mockStrategyStatus = [
  {
    id: '1',
    name: 'MA Cross Strategy',
    status: 'running' as const,
    startTime: '2024-01-15T10:30:00Z',
    uptime: '2d 5h 30m',
    tradesCount: 156,
    totalPnl: 2540.50,
    winRate: 65.4,
    currentPositions: 2,
    maxDrawdown: -8.5,
    cpuUsage: 25.3,
    memoryUsage: 512,
    lastSignal: 'Buy signal triggered for BTCUSDT'
  },
  {
    id: '2',
    name: 'RSI Mean Reversion',
    status: 'running' as const,
    startTime: '2024-01-20T14:20:00Z',
    uptime: '1d 15h 40m',
    tradesCount: 89,
    totalPnl: 1285.30,
    winRate: 58.9,
    currentPositions: 1,
    maxDrawdown: -12.3,
    cpuUsage: 18.7,
    memoryUsage: 384,
    lastSignal: 'Sell signal triggered for ETHUSDT'
  }
];

describe('RealTimeTrading Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Mock the service methods
    (realTimeTradingService.getRecentTrades as jest.Mock).mockResolvedValue(mockRealTimeTrades);
    (realTimeTradingService.getRealTimePrices as jest.Mock).mockResolvedValue(mockRealTimePrices);
    (realTimeTradingService.getStrategyStatus as jest.Mock).mockResolvedValue(mockStrategyStatus);
    (realTimeTradingService.getAccountBalances as jest.Mock).mockResolvedValue([
      {
        exchange: 'Binance',
        totalBalance: 15420.50,
        availableBalance: 12420.50,
        usedBalance: 3000.00,
        btcValue: 0.356,
        change24h: 254.30,
        currencies: [
          { currency: 'USDT', balance: 12420.50, available: 12420.50, locked: 0, btcValue: 0.287 },
          { currency: 'BTC', balance: 0.069, available: 0.069, locked: 0, btcValue: 0.069 }
        ]
      }
    ]);
    (realTimeTradingService.getCurrentPositions as jest.Mock).mockResolvedValue([
      {
        id: '1',
        strategyName: 'MA Cross Strategy',
        symbol: 'BTCUSDT',
        side: 'long' as const,
        quantity: 0.1,
        entryPrice: 41800.00,
        currentPrice: 43250.50,
        pnl: 145.05,
        pnlPercent: 3.47,
        margin: 4180.00,
        leverage: 1,
        liquidationPrice: 0,
        openTime: '2024-01-18T09:30:00Z',
        duration: '2d 3h',
        exchange: 'Binance'
      }
    ]);
    (realTimeTradingService.getRiskMetrics as jest.Mock).mockResolvedValue({
      totalExposure: 5347.50,
      marginUsage: 45.2,
      maxDrawdown: -8.5,
      var95: -1250.30,
      sharpeRatio: 1.85,
      beta: 0.85,
      correlation: 0.72,
      riskLevel: 'medium' as const
    });
  });

  test('renders real-time trading page correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    // Check if the title is rendered
    expect(screen.getByText('实时交易监控')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
      expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
    });
  });

  test('displays overview statistics correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if overview statistics are displayed
      expect(screen.getByText('总余额')).toBeInTheDocument();
      expect(screen.getByText('今日盈亏')).toBeInTheDocument();
      expect(screen.getByText('运行策略')).toBeInTheDocument();
      expect(screen.getByText('风险等级')).toBeInTheDocument();
    });
  });

  test('displays strategy status correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if strategy status is displayed
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
      expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
      expect(screen.getByText('运行中')).toBeInTheDocument();
    });
  });

  test('displays real-time prices correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if real-time prices are displayed
      expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
      expect(screen.getByText('ETHUSDT')).toBeInTheDocument();
      expect(screen.getByText('$43,250.50')).toBeInTheDocument();
      expect(screen.getByText('$2,250.30')).toBeInTheDocument();
    });
  });

  test('handles auto refresh toggle', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('自动刷新:')).toBeInTheDocument();
    });

    // Toggle auto refresh
    const autoRefreshSwitch = screen.getByRole('switch');
    fireEvent.click(autoRefreshSwitch);

    // Check if auto refresh is toggled
    expect(autoRefreshSwitch).not.toBeChecked();
  });

  test('handles refresh interval change', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('5秒')).toBeInTheDocument();
    });

    // Change refresh interval
    const intervalSelect = screen.getByDisplayValue('5秒');
    fireEvent.change(intervalSelect, { target: { value: '10' } });

    // Check if interval is changed
    expect(screen.getByDisplayValue('10秒')).toBeInTheDocument();
  });

  test('displays recent trades in table', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Switch to trades tab
      fireEvent.click(screen.getByText('实时交易'));
    });

    // Check if trades table is displayed
    await waitFor(() => {
      expect(screen.getByText('时间')).toBeInTheDocument();
      expect(screen.getByText('策略')).toBeInTheDocument();
      expect(screen.getByText('交易对')).toBeInTheDocument();
      expect(screen.getByText('方向')).toBeInTheDocument();
      expect(screen.getByText('价格')).toBeInTheDocument();
      expect(screen.getByText('数量')).toBeInTheDocument();
      expect(screen.getByText('金额')).toBeInTheDocument();
      expect(screen.getByText('盈亏')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
      expect(screen.getByText('操作')).toBeInTheDocument();
    });
  });

  test('displays current positions correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Switch to positions tab
      fireEvent.click(screen.getByText('当前持仓'));
    });

    // Check if positions table is displayed
    await waitFor(() => {
      expect(screen.getByText('策略')).toBeInTheDocument();
      expect(screen.getByText('交易对')).toBeInTheDocument();
      expect(screen.getByText('方向')).toBeInTheDocument();
      expect(screen.getByText('数量')).toBeInTheDocument();
      expect(screen.getByText('入场价格')).toBeInTheDocument();
      expect(screen.getByText('当前价格')).toBeInTheDocument();
      expect(screen.getByText('盈亏')).toBeInTheDocument();
      expect(screen.getByText('盈亏比例')).toBeInTheDocument();
      expect(screen.getByText('持仓时间')).toBeInTheDocument();
      expect(screen.getByText('交易所')).toBeInTheDocument();
    });
  });

  test('displays account balances correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Switch to balances tab
      fireEvent.click(screen.getByText('账户余额'));
    });

    // Check if account balances are displayed
    await waitFor(() => {
      expect(screen.getByText('Binance')).toBeInTheDocument();
      expect(screen.getByText('总余额')).toBeInTheDocument();
      expect(screen.getByText('可用余额')).toBeInTheDocument();
      expect(screen.getByText('使用余额')).toBeInTheDocument();
      expect(screen.getByText('资产分布')).toBeInTheDocument();
    });
  });

  test('displays risk metrics correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Switch to risk tab
      fireEvent.click(screen.getByText('风险监控'));
    });

    // Check if risk metrics are displayed
    await waitFor(() => {
      expect(screen.getByText('风险指标')).toBeInTheDocument();
      expect(screen.getByText('总敞口')).toBeInTheDocument();
      expect(screen.getByText('保证金使用率')).toBeInTheDocument();
      expect(screen.getByText('最大回撤')).toBeInTheDocument();
      expect(screen.getByText('VaR (95%)')).toBeInTheDocument();
      expect(screen.getByText('风险分析')).toBeInTheDocument();
      expect(screen.getByText('夏普比率')).toBeInTheDocument();
      expect(screen.getByText('Beta系数')).toBeInTheDocument();
      expect(screen.getByText('相关系数')).toBeInTheDocument();
      expect(screen.getByText('风险提示')).toBeInTheDocument();
    });
  });

  test('handles strategy control', async () => {
    (realTimeTradingService.controlStrategy as jest.Mock).mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Find and click pause button
    const pauseButtons = screen.getAllByRole('button');
    const pauseButton = pauseButtons.find(button => 
      button.getAttribute('aria-label') === 'pause-circle'
    );
    
    if (pauseButton) {
      fireEvent.click(pauseButton);
    }

    // Check if control service was called
    await waitFor(() => {
      expect(realTimeTradingService.controlStrategy).toHaveBeenCalled();
    });
  });

  test('opens trade detail drawer', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Switch to trades tab
      fireEvent.click(screen.getByText('实时交易'));
    });

    await waitFor(() => {
      // Click view detail button
      const viewButtons = screen.getAllByRole('button');
      const viewButton = viewButtons.find(button => 
        button.getAttribute('aria-label') === 'eye'
      );
      
      if (viewButton) {
        fireEvent.click(viewButton);
      }
    });

    // Check if drawer opens
    await waitFor(() => {
      expect(screen.getByText('交易详情')).toBeInTheDocument();
    });
  });

  test('opens settings modal', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Click settings button
      const settingsButton = screen.getByRole('button', { name: /设置/i });
      fireEvent.click(settingsButton);
    });

    // Check if settings modal opens
    await waitFor(() => {
      expect(screen.getByText('监控设置')).toBeInTheDocument();
    });
  });

  test('handles manual refresh', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Click refresh button
      const refreshButton = screen.getByRole('button', { name: /刷新/i });
      fireEvent.click(refreshButton);
    });

    // Check if service methods were called again
    await waitFor(() => {
      expect(realTimeTradingService.getRecentTrades).toHaveBeenCalled();
      expect(realTimeTradingService.getRealTimePrices).toHaveBeenCalled();
      expect(realTimeTradingService.getStrategyStatus).toHaveBeenCalled();
    });
  });

  test('displays charts correctly', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('价格走势')).toBeInTheDocument();
      expect(screen.getByText('盈亏曲线')).toBeInTheDocument();
    });
  });

  test('handles WebSocket connection simulation', async () => {
    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // The component should load data and simulate real-time updates
      expect(screen.getByText('实时交易监控')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    // Mock services to return promises that don't resolve immediately
    (realTimeTradingService.getRecentTrades as jest.Mock).mockReturnValue(new Promise(() => {}));
    (realTimeTradingService.getRealTimePrices as jest.Mock).mockReturnValue(new Promise(() => {}));
    (realTimeTradingService.getStrategyStatus as jest.Mock).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    // Check if loading state is handled
    expect(screen.getByText('实时交易监控')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    (realTimeTradingService.getRecentTrades as jest.Mock).mockRejectedValue(new Error('API Error'));
    (realTimeTradingService.getRealTimePrices as jest.Mock).mockRejectedValue(new Error('API Error'));
    (realTimeTradingService.getStrategyStatus as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(
      <MemoryRouter>
        <RealTimeTrading />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if error is handled gracefully
      expect(screen.getByText('实时交易监控')).toBeInTheDocument();
    });
  });
});

export default RealTimeTrading;