/**
 * 回测结果API服务
 * Backtest Results API Service
 */

import { message } from 'antd';

// 回测结果数据类型
export interface BacktestResult {
  id: string;
  strategyName: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  avgWin: number;
  avgLoss: number;
  largestWin: number;
  largestLoss: number;
  avgHoldingPeriod: number;
  status: 'completed' | 'running' | 'failed';
  createdAt: string;
  equityCurve: Array<{
    date: string;
    equity: number;
    drawdown: number;
  }>;
  trades: Array<{
    id: string;
    symbol: string;
    side: 'buy' | 'sell';
    entryTime: string;
    exitTime: string;
    entryPrice: number;
    exitPrice: number;
    quantity: number;
    pnl: number;
    return: number;
    holdingPeriod: number;
  }>;
  monthlyReturns: Array<{
    month: string;
    return: number;
  }>;
  drawdownPeriods: Array<{
    startDate: string;
    endDate: string;
    depth: number;
    duration: number;
  }>;
}

// 回测请求参数
export interface BacktestRequest {
  strategyId: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  params?: Record<string, any>;
}

// 回测配置
export interface BacktestConfig {
  strategyId: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  commission: number;
  slippage: number;
  params: Record<string, any>;
}

class BacktestService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8003';
  }

  // 获取所有回测结果
  async getBacktestResults(params?: {
    strategy?: string;
    symbol?: string;
    timeframe?: string;
    status?: string;
    startDate?: string;
    endDate?: string;
    page?: number;
    limit?: number;
  }): Promise<{ results: BacktestResult[]; total: number }> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/backtest/results${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回测结果失败:', error);
      throw error;
    }
  }

  // 获取单个回测结果
  async getBacktestResult(id: string): Promise<BacktestResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/results/${id}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回测结果详情失败:', error);
      throw error;
    }
  }

  // 创建回测任务
  async createBacktest(request: BacktestRequest): Promise<{ id: string; status: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      message.success('回测任务创建成功');
      return result;
    } catch (error) {
      console.error('创建回测任务失败:', error);
      message.error('创建回测任务失败');
      throw error;
    }
  }

  // 启动回测
  async startBacktest(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/${id}/start`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success('回测任务启动成功');
    } catch (error) {
      console.error('启动回测任务失败:', error);
      message.error('启动回测任务失败');
      throw error;
    }
  }

  // 停止回测
  async stopBacktest(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/${id}/stop`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success('回测任务停止成功');
    } catch (error) {
      console.error('停止回测任务失败:', error);
      message.error('停止回测任务失败');
      throw error;
    }
  }

  // 删除回测结果
  async deleteBacktest(id: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/results/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success('回测结果删除成功');
    } catch (error) {
      console.error('删除回测结果失败:', error);
      message.error('删除回测结果失败');
      throw error;
    }
  }

  // 获取回测配置
  async getBacktestConfig(strategyId: string): Promise<BacktestConfig> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/config/${strategyId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回测配置失败:', error);
      throw error;
    }
  }

  // 保存回测配置
  async saveBacktestConfig(config: BacktestConfig): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success('回测配置保存成功');
    } catch (error) {
      console.error('保存回测配置失败:', error);
      message.error('保存回测配置失败');
      throw error;
    }
  }

  // 导出回测结果
  async exportBacktestResult(id: string, format: 'csv' | 'excel' | 'pdf' = 'csv'): Promise<Blob> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/results/${id}/export/${format}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.blob();
    } catch (error) {
      console.error('导出回测结果失败:', error);
      message.error('导出回测结果失败');
      throw error;
    }
  }

  // 获取回测进度
  async getBacktestProgress(id: string): Promise<{
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    currentStep: string;
    estimatedTime: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/${id}/progress`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回测进度失败:', error);
      throw error;
    }
  }

  // 获取回测统计
  async getBacktestStats(params?: {
    strategy?: string;
    symbol?: string;
    timeframe?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<{
    totalBacktests: number;
    completedBacktests: number;
    averageReturn: number;
    bestReturn: number;
    worstReturn: number;
    averageSharpeRatio: number;
    averageMaxDrawdown: number;
    averageWinRate: number;
  }> {
    try {
      const queryString = params ? `?${new URLSearchParams(params as any).toString()}` : '';
      const response = await fetch(`${this.baseUrl}/api/backtest/stats${queryString}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回测统计失败:', error);
      throw error;
    }
  }

  // 对比回测结果
  async compareBacktestResults(ids: string[]): Promise<{
    comparison: Array<{
      id: string;
      strategyName: string;
      metrics: Record<string, number>;
      equityCurve: Array<{ date: string; equity: number }>;
    }>;
    analysis: {
      bestPerforming: string;
      mostConsistent: string;
      lowestRisk: string;
      highestReturn: string;
    };
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/compare`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ids }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('对比回测结果失败:', error);
      throw error;
    }
  }

  // 获取回测日志
  async getBacktestLogs(id: string): Promise<Array<{
    timestamp: string;
    level: 'info' | 'warning' | 'error';
    message: string;
  }>> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/${id}/logs`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取回测日志失败:', error);
      throw error;
    }
  }

  // 获取推荐的回测参数
  async getRecommendedParams(strategyId: string, symbol: string, timeframe: string): Promise<{
    params: Record<string, any>;
    reasoning: string;
    confidence: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/backtest/recommend-params`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ strategyId, symbol, timeframe }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('获取推荐参数失败:', error);
      throw error;
    }
  }
}

// 创建单例实例
export const backtestService = new BacktestService();

// 导出类型
export type { BacktestRequest, BacktestConfig };