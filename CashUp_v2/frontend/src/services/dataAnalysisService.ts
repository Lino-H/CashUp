/**
 * 数据分析API服务
 * Data Analysis API Service
 */

import { message } from 'antd';

// 性能指标类型
export interface PerformanceMetric {
  strategy: string;
  symbol: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  tradesCount: number;
  avgHoldingPeriod: number;
  calmarRatio: number;
  sortinoRatio: number;
  informationRatio: number;
  beta: number;
  alpha: number;
  treynorRatio: number;
}

// 相关性数据类型
export interface CorrelationData {
  symbol1: string;
  symbol2: string;
  correlation: number;
  pValue: number;
  covariance: number;
  period: string;
}

// 风险指标类型
export interface RiskMetric {
  metric: string;
  value: number;
  threshold: number;
  status: 'normal' | 'warning' | 'danger';
  trend: 'up' | 'down' | 'stable';
  unit: string;
  description: string;
}

// 市场情绪类型
export interface MarketSentiment {
  date: string;
  fearGreedIndex: number;
  volumeProfile: number;
  volatilityIndex: number;
  marketMomentum: number;
  putCallRatio: number;
  insiderTrading: number;
  marketSentiment: 'extreme_fear' | 'fear' | 'neutral' | 'greed' | 'extreme_greed';
}

// 资产配置类型
export interface AssetAllocation {
  asset: string;
  symbol: string;
  allocation: number;
  value: number;
  percentage: number;
  color: string;
  type: 'crypto' | 'stock' | 'bond' | 'commodity' | 'forex';
}

// 技术指标类型
export interface TechnicalIndicator {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma20: number;
  sma50: number;
  sma200: number;
  ema12: number;
  ema26: number;
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger: {
    upper: number;
    middle: number;
    lower: number;
  };
  stochastic: {
    k: number;
    d: number;
  };
  atr: number;
  adx: number;
}

// 统计分析类型
export interface StatisticalAnalysis {
  symbol: string;
  period: string;
  mean: number;
  median: number;
  stdDev: number;
  variance: number;
  skewness: number;
  kurtosis: number;
  min: number;
  max: number;
  range: number;
  percentiles: {
    p25: number;
    p50: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
  };
  normalityTest: {
    statistic: number;
    pValue: number;
    isNormal: boolean;
  };
}

// 回归分析类型
export interface RegressionAnalysis {
  dependent: string;
  independent: string;
  period: string;
  model: 'linear' | 'polynomial' | 'exponential' | 'logarithmic';
  coefficients: number[];
  rSquared: number;
  adjustedRSquared: number;
  fStatistic: number;
  pValue: number;
  standardError: number;
  residuals: {
    mean: number;
    stdDev: number;
    jarqueBera: number;
    ljungBox: number;
  };
}

// 时间序列分析类型
export interface TimeSeriesAnalysis {
  symbol: string;
  period: string;
  trend: 'up' | 'down' | 'sideways';
  seasonality: {
    detected: boolean;
    period: number;
    strength: number;
  };
  autocorrelation: {
    lag1: number;
    lag5: number;
    lag10: number;
    lag20: number;
  };
  stationarity: {
    adfTest: number;
    kpssTest: number;
    isStationary: boolean;
  };
  volatility: {
    historical: number;
    garch: number;
    ewma: number;
  };
  forecasts: {
    method: string;
    horizon: number;
    predictions: Array<{
      date: string;
      predicted: number;
      lower: number;
      upper: number;
    }>;
  };
}

// 分析参数类型
export interface AnalysisParams {
  symbols?: string[];
  strategies?: string[];
  startDate?: string;
  endDate?: string;
  timeframe?: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w' | '1M';
  metrics?: string[];
  includeBenchmark?: boolean;
  riskFreeRate?: number;
  confidenceLevel?: number;
}

// 图表配置类型
export interface ChartConfig {
  type: 'line' | 'bar' | 'scatter' | 'pie' | 'area' | 'candlestick' | 'heatmap';
  title: string;
  xAxis: {
    label: string;
    type: 'category' | 'number' | 'time';
  };
  yAxis: {
    label: string;
    type: 'number';
    min?: number;
    max?: number;
  };
  series: Array<{
    name: string;
    data: any[];
    type: string;
    color?: string;
    yAxisIndex?: number;
  }>;
  options: {
    showLegend?: boolean;
    showTooltip?: boolean;
    responsive?: boolean;
    animation?: boolean;
  };
}

// 报告生成类型
export interface ReportConfig {
  title: string;
  type: 'performance' | 'risk' | 'correlation' | 'market' | 'custom';
  format: 'pdf' | 'excel' | 'html' | 'json';
  includeCharts: boolean;
  includeTables: boolean;
  includeMetrics: boolean;
  dateRange: {
    start: string;
    end: string;
  };
  filters: Record<string, any>;
}

class DataAnalysisService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8002';
  }

  // 获取性能指标
  async getPerformanceMetrics(params?: AnalysisParams): Promise<PerformanceMetric[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/performance${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取性能指标失败:', error);
      throw error;
    }
  }

  // 获取相关性分析
  async getCorrelationAnalysis(params?: {
    symbols?: string[];
    period?: string;
    method?: 'pearson' | 'spearman' | 'kendall';
  }): Promise<CorrelationData[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/correlation${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取相关性分析失败:', error);
      throw error;
    }
  }

  // 获取风险指标
  async getRiskMetrics(params?: AnalysisParams): Promise<RiskMetric[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/risk${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取风险指标失败:', error);
      throw error;
    }
  }

  // 获取市场情绪
  async getMarketSentiment(params?: {
    startDate?: string;
    endDate?: string;
    indicators?: string[];
  }): Promise<MarketSentiment[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/sentiment${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取市场情绪失败:', error);
      throw error;
    }
  }

  // 获取资产配置
  async getAssetAllocation(params?: {
    portfolioId?: string;
    includeHistory?: boolean;
  }): Promise<AssetAllocation[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/allocation${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取资产配置失败:', error);
      throw error;
    }
  }

  // 获取技术指标
  async getTechnicalIndicators(params?: {
    symbol: string;
    timeframe: string;
    indicators?: string[];
    period?: number;
  }): Promise<TechnicalIndicator[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/technical${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取技术指标失败:', error);
      throw error;
    }
  }

  // 获取统计分析
  async getStatisticalAnalysis(params?: {
    symbol: string;
    period: string;
    tests?: string[];
  }): Promise<StatisticalAnalysis> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/statistical${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取统计分析失败:', error);
      throw error;
    }
  }

  // 获取回归分析
  async getRegressionAnalysis(params?: {
    dependent: string;
    independent: string;
    period: string;
    model?: string;
  }): Promise<RegressionAnalysis> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/regression${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回归分析失败:', error);
      throw error;
    }
  }

  // 获取时间序列分析
  async getTimeSeriesAnalysis(params?: {
    symbol: string;
    period: string;
    methods?: string[];
  }): Promise<TimeSeriesAnalysis> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/analysis/timeseries${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取时间序列分析失败:', error);
      throw error;
    }
  }

  // 生成图表配置
  async generateChart(config: ChartConfig): Promise<{
    chartId: string;
    imageUrl: string;
    config: ChartConfig;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/chart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('生成图表失败:', error);
      throw error;
    }
  }

  // 生成分析报告
  async generateReport(config: ReportConfig): Promise<{
    reportId: string;
    downloadUrl: string;
    generatedAt: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      message.success('报告生成成功');
      return result;
    } catch (error) {
      console.error('生成报告失败:', error);
      message.error('生成报告失败');
      throw error;
    }
  }

  // 获取市场数据
  async getMarketData(params?: {
    symbols?: string[];
    timeframe?: string;
    startDate?: string;
    endDate?: string;
    limit?: number;
  }): Promise<any[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/market/data${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取市场数据失败:', error);
      throw error;
    }
  }

  // 获取历史数据
  async getHistoricalData(params?: {
    symbol: string;
    timeframe: string;
    startDate?: string;
    endDate?: string;
  }): Promise<any[]> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/market/historical${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取历史数据失败:', error);
      throw error;
    }
  }

  // 导出数据
  async exportData(params?: {
    format: 'csv' | 'excel' | 'json' | 'parquet';
    data: any[];
    filename?: string;
  }): Promise<{ downloadUrl: string; filename: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('导出数据失败:', error);
      throw error;
    }
  }

  // 获取分析任务状态
  async getAnalysisTaskStatus(taskId: string): Promise<{
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    message?: string;
    result?: any;
    error?: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/tasks/${taskId}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取任务状态失败:', error);
      throw error;
    }
  }

  // 取消分析任务
  async cancelAnalysisTask(taskId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/analysis/tasks/${taskId}/cancel`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      message.success('任务已取消');
    } catch (error) {
      console.error('取消任务失败:', error);
      message.error('取消任务失败');
      throw error;
    }
  }
}

// 创建单例实例
export const dataAnalysisService = new DataAnalysisService();

// 导出类型
export type {
  PerformanceMetric,
  CorrelationData,
  RiskMetric,
  MarketSentiment,
  AssetAllocation,
  TechnicalIndicator,
  StatisticalAnalysis,
  RegressionAnalysis,
  TimeSeriesAnalysis,
  AnalysisParams,
  ChartConfig,
  ReportConfig
};