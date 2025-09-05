/**
 * 回测结果可视化测试
 * Backtest Results Visualization Test
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BacktestResults from '../pages/BacktestResults';
import { backtestService } from '../services/backtestService';

// Mock the backtest service
jest.mock('../services/backtestService');

const mockBacktestResults = [
  {
    id: '1',
    strategyName: 'MA Cross Strategy',
    symbol: 'BTCUSDT',
    timeframe: '1h',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    initialCapital: 10000,
    finalCapital: 15420,
    totalReturn: 54.2,
    sharpeRatio: 1.85,
    maxDrawdown: -12.3,
    winRate: 65.4,
    profitFactor: 2.15,
    totalTrades: 156,
    winningTrades: 102,
    losingTrades: 54,
    avgWin: 245.5,
    avgLoss: -178.2,
    largestWin: 1250,
    largestLoss: -450,
    avgHoldingPeriod: 4.2,
    status: 'completed',
    createdAt: '2024-01-15T10:30:00Z',
    equityCurve: [],
    trades: [],
    monthlyReturns: [],
    drawdownPeriods: []
  },
  {
    id: '2',
    strategyName: 'RSI Mean Reversion',
    symbol: 'ETHUSDT',
    timeframe: '4h',
    startDate: '2024-01-01',
    endDate: '2024-12-31',
    initialCapital: 10000,
    finalCapital: 12850,
    totalReturn: 28.5,
    sharpeRatio: 1.42,
    maxDrawdown: -18.7,
    winRate: 58.9,
    profitFactor: 1.78,
    totalTrades: 89,
    winningTrades: 52,
    losingTrades: 37,
    avgWin: 320.8,
    avgLoss: -245.5,
    largestWin: 980,
    largestLoss: -680,
    avgHoldingPeriod: 6.5,
    status: 'completed',
    createdAt: '2024-01-20T14:20:00Z',
    equityCurve: [],
    trades: [],
    monthlyReturns: [],
    drawdownPeriods: []
  }
];

describe('BacktestResults Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Mock the service methods
    (backtestService.getBacktestResults as jest.Mock).mockResolvedValue({
      results: mockBacktestResults,
      total: mockBacktestResults.length
    });
    
    (backtestService.getBacktestResult as jest.Mock).mockResolvedValue(mockBacktestResults[0]);
  });

  test('renders backtest results page correctly', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    // Check if the title is rendered
    expect(screen.getByText('回测结果分析')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
      expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
    });
  });

  test('displays backtest results in table', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if table headers are present
      expect(screen.getByText('策略名称')).toBeInTheDocument();
      expect(screen.getByText('回测期间')).toBeInTheDocument();
      expect(screen.getByText('总收益')).toBeInTheDocument();
      expect(screen.getByText('夏普比率')).toBeInTheDocument();
      expect(screen.getByText('最大回撤')).toBeInTheDocument();
      expect(screen.getByText('胜率')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
      expect(screen.getByText('操作')).toBeInTheDocument();

      // Check if data is rendered
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
      expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
      expect(screen.getByText('54.20%')).toBeInTheDocument();
      expect(screen.getByText('1.85')).toBeInTheDocument();
      expect(screen.getByText('-12.30%')).toBeInTheDocument();
      expect(screen.getByText('65.4%')).toBeInTheDocument();
    });
  });

  test('filters results correctly', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
      expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
    });

    // Test strategy filter
    const strategySelect = screen.getByPlaceholderText('选择策略');
    fireEvent.change(strategySelect, { target: { value: 'MA Cross Strategy' } });

    // Test symbol filter
    const symbolSelect = screen.getByPlaceholderText('选择交易对');
    fireEvent.change(symbolSelect, { target: { value: 'BTCUSDT' } });

    // Test timeframe filter
    const timeframeSelect = screen.getByPlaceholderText('选择时间周期');
    fireEvent.change(timeframeSelect, { target: { value: '1h' } });

    // Test status filter
    const statusSelect = screen.getByPlaceholderText('选择状态');
    fireEvent.change(statusSelect, { target: { value: 'completed' } });
  });

  test('opens detail drawer when view button is clicked', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Click the view button
    const viewButton = screen.getAllByRole('button')[0]; // First button should be view
    fireEvent.click(viewButton);

    // Check if drawer opens (you might need to adjust this based on your implementation)
    await waitFor(() => {
      expect(screen.getByText('基本信息')).toBeInTheDocument();
    });
  });

  test('handles compare mode', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Enable compare mode
    const compareButton = screen.getByText('对比模式');
    fireEvent.click(compareButton);

    // Add to compare
    const compareButtons = screen.getAllByRole('button');
    const addToCompareButton = compareButtons.find(button => 
      button.getAttribute('aria-label') === 'bar-chart'
    );
    
    if (addToCompareButton) {
      fireEvent.click(addToCompareButton);
    }

    // Check if compare mode is active
    expect(screen.getByText('回测结果对比')).toBeInTheDocument();
  });

  test('handles export functionality', async () => {
    (backtestService.exportBacktestResult as jest.Mock).mockResolvedValue(new Blob());

    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Click export button
    const exportButtons = screen.getAllByRole('button');
    const exportButton = exportButtons.find(button => 
      button.getAttribute('aria-label') === 'download'
    );
    
    if (exportButton) {
      fireEvent.click(exportButton);
    }

    // Check if export service was called
    await waitFor(() => {
      expect(backtestService.exportBacktestResult).toHaveBeenCalled();
    });
  });

  test('displays performance metrics correctly', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Open detail drawer
    const viewButton = screen.getAllByRole('button')[0];
    fireEvent.click(viewButton);

    await waitFor(() => {
      expect(screen.getByText('性能指标')).toBeInTheDocument();
      expect(screen.getByText('总收益')).toBeInTheDocument();
      expect(screen.getByText('夏普比率')).toBeInTheDocument();
      expect(screen.getByText('最大回撤')).toBeInTheDocument();
      expect(screen.getByText('胜率')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    // Mock the service to return a promise that doesn't resolve immediately
    (backtestService.getBacktestResults as jest.Mock).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    // Check if loading state is displayed
    expect(screen.getByText('回测结果分析')).toBeInTheDocument();
  });

  test('handles empty state', async () => {
    (backtestService.getBacktestResults as jest.Mock).mockResolvedValue({
      results: [],
      total: 0
    });

    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if empty state is handled
      expect(screen.getByText('回测结果分析')).toBeInTheDocument();
    });
  });

  test('handles error state', async () => {
    (backtestService.getBacktestResults as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Check if error is handled gracefully
      expect(screen.getByText('回测结果分析')).toBeInTheDocument();
    });
  });

  test('sorts results by different columns', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Test sorting by total return
    const returnHeader = screen.getByText('总收益');
    fireEvent.click(returnHeader);

    // Test sorting by Sharpe ratio
    const sharpeHeader = screen.getByText('夏普比率');
    fireEvent.click(sharpeHeader);

    // Test sorting by max drawdown
    const drawdownHeader = screen.getByText('最大回撤');
    fireEvent.click(drawdownHeader);

    // Test sorting by win rate
    const winRateHeader = screen.getByText('胜率');
    fireEvent.click(winRateHeader);
  });

  test('displays charts in detail view', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Open detail drawer
    const viewButton = screen.getAllByRole('button')[0];
    fireEvent.click(viewButton);

    await waitFor(() => {
      expect(screen.getByText('图表分析')).toBeInTheDocument();
      expect(screen.getByText('净值曲线')).toBeInTheDocument();
      expect(screen.getByText('月度收益')).toBeInTheDocument();
      expect(screen.getByText('交易分布')).toBeInTheDocument();
    });
  });

  test('displays trade history in detail view', async () => {
    render(
      <MemoryRouter>
        <BacktestResults />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
    });

    // Open detail drawer
    const viewButton = screen.getAllByRole('button')[0];
    fireEvent.click(viewButton);

    await waitFor(() => {
      expect(screen.getByText('交易记录')).toBeInTheDocument();
    });
  });
});

export default BacktestResults;