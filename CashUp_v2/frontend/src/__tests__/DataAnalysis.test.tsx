/**
 * 数据分析和图表测试
 * Data Analysis and Charts Test
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DataAnalysis from '../pages/DataAnalysis';
import { dataAnalysisService } from '../services/dataAnalysisService';

// Mock the data analysis service
jest.mock('../services/dataAnalysisService');

const mockPerformanceMetrics = [
  {
    strategy: 'MA Cross Strategy',
    symbol: 'BTCUSDT',
    totalReturn: 15.8,
    sharpeRatio: 1.85,
    maxDrawdown: -8.5,
    winRate: 65.4,
    profitFactor: 2.1,
    tradesCount: 156,
    avgHoldingPeriod: 2.5,
    calmarRatio: 1.86,
    sortinoRatio: 2.15,
    informationRatio: 0.85,
    beta: 0.85,
    alpha: 2.3,
    treynorRatio: 1.92
  },
  {
    strategy: 'RSI Mean Reversion',
    symbol: 'ETHUSDT',
    totalReturn: 12.3,
    sharpeRatio: 1.42,
    maxDrawdown: -12.3,
    winRate: 58.9,
    profitFactor: 1.8,
    tradesCount: 89,
    avgHoldingPeriod: 1.8,
    calmarRatio: 1.0,
    sortinoRatio: 1.65,
    informationRatio: 0.65,
    beta: 1.15,
    alpha: 1.2,
    treynorRatio: 1.25
  }
];

const mockCorrelationData = [
  {
    symbol1: 'BTCUSDT',
    symbol2: 'ETHUSDT',
    correlation: 0.85,
    pValue: 0.001,
    covariance: 0.000234,
    period: '30d'
  },
  {
    symbol1: 'BTCUSDT',
    symbol2: 'BNBUSDT',
    correlation: 0.72,
    pValue: 0.005,
    covariance: 0.000189,
    period: '30d'
  },
  {
    symbol1: 'ETHUSDT',
    symbol2: 'BNBUSDT',
    correlation: 0.68,
    pValue: 0.008,
    covariance: 0.000156,
    period: '30d'
  }
];

const mockRiskMetrics = [
  {
    metric: 'VaR (95%)',
    value: 1250,
    threshold: 1500,
    status: 'normal' as const,
    trend: 'stable' as const,
    unit: 'USD',
    description: '95%置信度下的风险价值'
  },
  {
    metric: '最大回撤',
    value: 8.5,
    threshold: 10,
    status: 'normal' as const,
    trend: 'down' as const,
    unit: '%',
    description: '最大回撤率'
  },
  {
    metric: '夏普比率',
    value: 1.85,
    threshold: 1.5,
    status: 'normal' as const,
    trend: 'up' as const,
    unit: '',
    description: '风险调整后收益'
  }
];

const mockMarketSentiment = [
  {
    date: '2024-01-01',
    fearGreedIndex: 65,
    volumeProfile: 120,
    volatilityIndex: 18,
    marketMomentum: 75,
    putCallRatio: 0.8,
    insiderTrading: 0.3,
    marketSentiment: 'greed' as const
  },
  {
    date: '2024-01-02',
    fearGreedIndex: 58,
    volumeProfile: 135,
    volatilityIndex: 22,
    marketMomentum: 68,
    putCallRatio: 1.2,
    insiderTrading: 0.5,
    marketSentiment: 'neutral' as const
  },
  {
    date: '2024-01-03',
    fearGreedIndex: 72,
    volumeProfile: 110,
    volatilityIndex: 15,
    marketMomentum: 82,
    putCallRatio: 0.6,
    insiderTrading: 0.2,
    marketSentiment: 'greed' as const
  }
];

const mockAssetAllocation = [
  {
    asset: 'Bitcoin',
    symbol: 'BTC',
    allocation: 45,
    value: 450000,
    percentage: 45,
    color: '#FF6B6B',
    type: 'crypto' as const
  },
  {
    asset: 'Ethereum',
    symbol: 'ETH',
    allocation: 30,
    value: 300000,
    percentage: 30,
    color: '#4ECDC4',
    type: 'crypto' as const
  },
  {
    asset: 'Binance Coin',
    symbol: 'BNB',
    allocation: 15,
    value: 150000,
    percentage: 15,
    color: '#45B7D1',
    type: 'crypto' as const
  },
  {
    asset: 'Others',
    symbol: 'OTHERS',
    allocation: 10,
    value: 100000,
    percentage: 10,
    color: '#96CEB4',
    type: 'crypto' as const
  }
];

describe('DataAnalysis Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Mock the service methods
    (dataAnalysisService.getPerformanceMetrics as jest.Mock).mockResolvedValue(mockPerformanceMetrics);
    (dataAnalysisService.getCorrelationAnalysis as jest.Mock).mockResolvedValue(mockCorrelationData);
    (dataAnalysisService.getRiskMetrics as jest.Mock).mockResolvedValue(mockRiskMetrics);
    (dataAnalysisService.getMarketSentiment as jest.Mock).mockResolvedValue(mockMarketSentiment);
    (dataAnalysisService.getAssetAllocation as jest.Mock).mockResolvedValue(mockAssetAllocation);
    (dataAnalysisService.generateReport as jest.Mock).mockResolvedValue({
      reportId: 'test-report-123',
      downloadUrl: '/api/reports/test-report-123.pdf',
      generatedAt: new Date().toISOString()
    });
    (dataAnalysisService.exportData as jest.Mock).mockResolvedValue({
      downloadUrl: '/api/exports/test-data.csv',
      filename: 'analysis-data.csv'
    });
  });

  test('renders data analysis page correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Check if the title is rendered
    expect(screen.getByText('数据分析与图表')).toBeInTheDocument();
    expect(screen.getByText('深度分析交易数据，洞察市场趋势，优化投资策略')).toBeInTheDocument();

    // Check if overview statistics are displayed
    expect(screen.getByText('总收益率')).toBeInTheDocument();
    expect(screen.getByText('夏普比率')).toBeInTheDocument();
    expect(screen.getByText('最大回撤')).toBeInTheDocument();
    expect(screen.getByText('胜率')).toBeInTheDocument();
  });

  test('displays strategy performance chart correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('策略表现分析')).toBeInTheDocument();
    });

    // Switch to performance tab
    fireEvent.click(screen.getByText('策略表现'));

    // Check if chart elements are present
    await waitFor(() => {
      expect(screen.getByText('组合价值')).toBeInTheDocument();
      expect(screen.getByText('成交量')).toBeInTheDocument();
      expect(screen.getByText('移动平均')).toBeInTheDocument();
    });
  });

  test('displays performance metrics table correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to metrics tab
    fireEvent.click(screen.getByText('性能指标'));

    // Check if table headers are displayed
    await waitFor(() => {
      expect(screen.getByText('策略')).toBeInTheDocument();
      expect(screen.getByText('交易对')).toBeInTheDocument();
      expect(screen.getByText('总收益率')).toBeInTheDocument();
      expect(screen.getByText('夏普比率')).toBeInTheDocument();
      expect(screen.getByText('最大回撤')).toBeInTheDocument();
      expect(screen.getByText('胜率')).toBeInTheDocument();
      expect(screen.getByText('盈亏比')).toBeInTheDocument();
      expect(screen.getByText('交易次数')).toBeInTheDocument();
      expect(screen.getByText('平均持仓时间')).toBeInTheDocument();
    });

    // Check if data rows are displayed
    await waitFor(() => {
      expect(screen.getByText('MA Cross Strategy')).toBeInTheDocument();
      expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
      expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
      expect(screen.getByText('ETHUSDT')).toBeInTheDocument();
    });
  });

  test('displays correlation analysis correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to correlation tab
    fireEvent.click(screen.getByText('相关性分析'));

    // Check if correlation table is displayed
    await waitFor(() => {
      expect(screen.getByText('交易对1')).toBeInTheDocument();
      expect(screen.getByText('交易对2')).toBeInTheDocument();
      expect(screen.getByText('相关系数')).toBeInTheDocument();
      expect(screen.getByText('P值')).toBeInTheDocument();
      expect(screen.getByText('相关性强度')).toBeInTheDocument();
    });

    // Check if correlation data is displayed
    await waitFor(() => {
      expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
      expect(screen.getByText('ETHUSDT')).toBeInTheDocument();
      expect(screen.getByText('强相关')).toBeInTheDocument();
      expect(screen.getByText('中等相关')).toBeInTheDocument();
    });
  });

  test('displays risk analysis correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to risk tab
    fireEvent.click(screen.getByText('风险分析'));

    // Check if risk metrics are displayed
    await waitFor(() => {
      expect(screen.getByText('风险指标')).toBeInTheDocument();
      expect(screen.getByText('当前值')).toBeInTheDocument();
      expect(screen.getByText('阈值')).toBeInTheDocument();
      expect(screen.getByText('状态')).toBeInTheDocument();
    });

    // Check if risk data is displayed
    await waitFor(() => {
      expect(screen.getByText('VaR (95%)')).toBeInTheDocument();
      expect(screen.getByText('最大回撤')).toBeInTheDocument();
      expect(screen.getByText('夏普比率')).toBeInTheDocument();
    });
  });

  test('displays strategy comparison correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to strategy comparison tab
    fireEvent.click(screen.getByText('策略对比'));

    // Check if comparison elements are displayed
    await waitFor(() => {
      expect(screen.getByText('策略对比分析')).toBeInTheDocument();
      expect(screen.getByText('策略排名')).toBeInTheDocument();
    });
  });

  test('displays market sentiment correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to market sentiment tab
    fireEvent.click(screen.getByText('市场情绪'));

    // Check if sentiment elements are displayed
    await waitFor(() => {
      expect(screen.getByText('市场情绪分析')).toBeInTheDocument();
      expect(screen.getByText('当前恐惧贪婪指数')).toBeInTheDocument();
      expect(screen.getByText('波动率指数')).toBeInTheDocument();
      expect(screen.getByText('市场动量')).toBeInTheDocument();
    });
  });

  test('displays asset allocation correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to asset allocation tab
    fireEvent.click(screen.getByText('资产配置'));

    // Check if allocation elements are displayed
    await waitFor(() => {
      expect(screen.getByText('资产配置分析')).toBeInTheDocument();
      expect(screen.getByText('资产')).toBeInTheDocument();
      expect(screen.getByText('占比')).toBeInTheDocument();
      expect(screen.getByText('价值')).toBeInTheDocument();
    });

    // Check if asset data is displayed
    await waitFor(() => {
      expect(screen.getByText('Bitcoin')).toBeInTheDocument();
      expect(screen.getByText('Ethereum')).toBeInTheDocument();
      expect(screen.getByText('Binance Coin')).toBeInTheDocument();
    });
  });

  test('handles time range selection', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to performance tab
    fireEvent.click(screen.getByText('策略表现'));

    await waitFor(() => {
      expect(screen.getByText('7天')).toBeInTheDocument();
    });

    // Change time range
    const timeRangeSelect = screen.getByDisplayValue('7d');
    fireEvent.change(timeRangeSelect, { target: { value: '30d' } });

    // Check if time range is changed
    expect(screen.getByDisplayValue('30d')).toBeInTheDocument();
  });

  test('opens chart settings modal', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to risk tab
    fireEvent.click(screen.getByText('风险分析'));

    await waitFor(() => {
      expect(screen.getByText('设置')).toBeInTheDocument();
    });

    // Click settings button
    fireEvent.click(screen.getByText('设置'));

    // Check if settings modal opens
    await waitFor(() => {
      expect(screen.getByText('图表设置')).toBeInTheDocument();
      expect(screen.getByText('显示选项')).toBeInTheDocument();
      expect(screen.getByText('显示成交量')).toBeInTheDocument();
      expect(screen.getByText('显示移动平均线')).toBeInTheDocument();
    });
  });

  test('handles chart settings changes', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Open settings modal
    fireEvent.click(screen.getByText('风险分析'));
    await waitFor(() => {
      fireEvent.click(screen.getByText('设置'));
    });

    // Toggle volume display
    const volumeSwitch = screen.getAllByRole('switch')[0];
    fireEvent.click(volumeSwitch);

    // Toggle moving averages
    const maSwitch = screen.getAllByRole('switch')[1];
    fireEvent.click(maSwitch);

    // Check if settings are applied
    expect(volumeSwitch).not.toBeChecked();
    expect(maSwitch).not.toBeChecked();
  });

  test('handles export functionality', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Switch to performance tab
    fireEvent.click(screen.getByText('策略表现'));

    await waitFor(() => {
      expect(screen.getByText('导出')).toBeInTheDocument();
    });

    // Click export button
    fireEvent.click(screen.getByText('导出'));

    // Check if export service was called
    await waitFor(() => {
      expect(dataAnalysisService.exportData).toHaveBeenCalled();
    });
  });

  test('handles report generation', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // This would test report generation functionality
    // In a real scenario, you would click a generate report button
    expect(screen.getByText('数据分析与图表')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    // Mock services to return promises that don't resolve immediately
    (dataAnalysisService.getPerformanceMetrics as jest.Mock).mockReturnValue(new Promise(() => {}));
    (dataAnalysisService.getCorrelationAnalysis as jest.Mock).mockReturnValue(new Promise(() => {}));
    (dataAnalysisService.getRiskMetrics as jest.Mock).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Check if loading state is handled
    expect(screen.getByText('数据分析与图表')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    (dataAnalysisService.getPerformanceMetrics as jest.Mock).mockRejectedValue(new Error('API Error'));
    (dataAnalysisService.getCorrelationAnalysis as jest.Mock).mockRejectedValue(new Error('API Error'));
    (dataAnalysisService.getRiskMetrics as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Check if error is handled gracefully
    await waitFor(() => {
      expect(screen.getByText('数据分析与图表')).toBeInTheDocument();
    });
  });

  test('handles responsive layout', () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Check if responsive layout elements are present
    expect(screen.getByText('数据分析与图表')).toBeInTheDocument();
    
    // In a real test, you would test different screen sizes
    // and verify the layout adapts correctly
  });

  test('displays correct statistics overview', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Check if overview statistics are displayed with correct values
    await waitFor(() => {
      expect(screen.getByText('15.8%')).toBeInTheDocument();
      expect(screen.getByText('1.85')).toBeInTheDocument();
      expect(screen.getByText('-8.5%')).toBeInTheDocument();
      expect(screen.getByText('65.4%')).toBeInTheDocument();
    });
  });

  test('handles tab navigation correctly', async () => {
    render(
      <MemoryRouter>
        <DataAnalysis />
      </MemoryRouter>
    );

    // Test navigating through all tabs
    const tabs = [
      '策略表现',
      '性能指标',
      '相关性分析',
      '风险分析',
      '策略对比',
      '市场情绪',
      '资产配置'
    ];

    for (const tab of tabs) {
      fireEvent.click(screen.getByText(tab));
      await waitFor(() => {
        expect(screen.getByText(tab)).toBeInTheDocument();
      });
    }
  });
});

export default DataAnalysis;