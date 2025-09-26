/**
 * 回测功能页面 - 策略回测和性能分析
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Table,
  Space,
  Tag,
  Progress,
  Statistic,
  Row,
  Col,
  Tabs,
  Alert,
  Modal,
  Result,
  Typography,
  Divider,
  Tooltip,
  Badge,
  Switch,
  InputNumber,
  message
} from 'antd';
import {
  PlayCircleOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DownloadOutlined,
  SettingOutlined,
  ReloadOutlined,
  EyeOutlined,
  StopOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  RiseOutlined,
  DollarCircleOutlined,
  FilterOutlined,
  TableOutlined,
  LineChartOutlined as LineChartOutlined2,
  AreaChartOutlined,
  ShareAltOutlined,
  CloudDownloadOutlined
} from '@ant-design/icons';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  ComposedChart,
  Scatter
} from 'recharts';
import moment from 'moment';
import { useAuth } from '../contexts/AuthContext';
import { strategyAPI, handleApiError } from '../services/api';
import { useDataCache } from '../hooks/useDataCache';
import { SmartLoading } from '../components/SmartLoading';
import { PageSkeleton } from '../components/PageSkeleton';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

interface BacktestConfig {
  strategyId: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  positionSize: number;
  maxPositions: number;
  stopLoss: number;
  takeProfit: number;
  commission: number;
  slippage: number;
}

interface BacktestResult {
  id: string;
  strategyName: string;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
  totalReturn: number;
  annualizedReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  totalTrades: number;
  profitFactor: number;
  calmarRatio: number;
  sortinoRatio: number;
  beta: number;
  alpha: number;
  status: 'running' | 'completed' | 'failed';
  progress: number;
  createdAt: string;
  completedAt?: string;
  equityCurve: Array<{ date: string; value: number }>;
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
    commission: number;
    slippage: number;
    status: 'win' | 'loss';
  }>;
  metrics: {
    avgTrade: number;
    avgWinTrade: number;
    avgLossTrade: number;
    maxConsecutiveWins: number;
    maxConsecutiveLosses: number;
    recoveryFactor: number;
    profitFactor: number;
  };
}

const BacktestPage: React.FC = () => {
  const { isAuthenticated, apiCallWithRetry } = useAuth();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [backtestHistory, setBacktestHistory] = useState<BacktestResult[]>([]);
  const [currentBacktest, setCurrentBacktest] = useState<BacktestResult | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [resultModalVisible, setResultModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('config');
  const [chartType, setChartType] = useState('line');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(10);
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null);
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [tradeAnalysis, setTradeAnalysis] = useState<any[]>([]);

  // 策略选项
  const [strategies, setStrategies] = useState<any[]>([]);
  
  // 交易对选项
  const symbols = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT',
    'SOL/USDT', 'MATIC/USDT', 'AVAX/USDT', 'LINK/USDT', 'UNI/USDT'
  ];

  // 时间周期选项
  const timeframes = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '1h', label: '1小时' },
    { value: '4h', label: '4小时' },
    { value: '1d', label: '1天' }
  ];

  // 获取策略列表
  const loadStrategies = useCallback(async () => {
    try {
      const data = await apiCallWithRetry(() => strategyAPI.getStrategies());
      if (data) {
        setStrategies(Array.isArray(data) ? data : (data as any).strategies || []);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  }, [apiCallWithRetry]);

  // 获取回测历史
  const loadBacktestHistory = useCallback(async () => {
    try {
      const data = await apiCallWithRetry(() => strategyAPI.getBacktests());
      if (data) {
        setBacktestHistory(Array.isArray(data) ? data : (data as any).backtests || []);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  }, [apiCallWithRetry]);

  // 获取性能数据
  const fetchPerformanceData = useCallback(async (backtestId: string) => {
    const response = await fetch(`/api/backtest/${backtestId}/performance`);
    if (!response.ok) {
      throw new Error(`性能数据API错误: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }, []);

  // 获取交易分析数据
  const fetchTradeAnalysis = useCallback(async (backtestId: string) => {
    const response = await fetch(`/api/backtest/${backtestId}/trades`);
    if (!response.ok) {
      throw new Error(`交易分析API错误: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }, []);

  // 数据导出功能
  const exportBacktestData = (type: 'csv' | 'json' | 'pdf') => {
    const dataToExport = backtestHistory.map(result => ({
      '回测ID': result.id,
      '策略名称': result.strategyName,
      '交易对': result.symbol,
      '时间周期': result.timeframe,
      '开始日期': result.startDate,
      '结束日期': result.endDate,
      '总收益率': `${result.totalReturn.toFixed(2)}%`,
      '年化收益率': `${result.annualizedReturn.toFixed(2)}%`,
      '最大回撤': `${result.maxDrawdown.toFixed(2)}%`,
      '夏普比率': result.sharpeRatio.toFixed(2),
      '胜率': `${result.winRate.toFixed(2)}%`,
      '交易次数': result.totalTrades,
      '盈利因子': result.profitFactor.toFixed(2),
      '状态': result.status,
      '创建时间': result.createdAt
    }));

    if (type === 'csv') {
      const csvContent = [
        Object.keys(dataToExport[0]).join(','),
        ...dataToExport.map(row => Object.values(row).join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `backtest_results_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
    } else if (type === 'json') {
      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `backtest_results_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
    } else {
      message.info('PDF导出功能开发中...');
    }
    message.success(`数据导出成功！`);
  };

  // 图表渲染函数
  const renderChart = (type: string) => {
    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Line type="monotone" dataKey="equity" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Area type="monotone" dataKey="equity" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        );
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="trades" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        );
      case 'drawdown':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Area type="monotone" dataKey="drawdown" stroke="#ff7300" fill="#ff7300" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        );
      case 'sharpe':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Line type="monotone" dataKey="sharpe" stroke="#ff0000" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );
      default:
        return null;
    }
  };

  // 自动刷新功能
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh && currentBacktest?.status === 'running') {
      interval = setInterval(() => {
        loadBacktestHistory();
      }, refreshInterval * 1000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, currentBacktest?.status, loadBacktestHistory]);

  // 初始化加载
  useEffect(() => {
    if (isAuthenticated) {
      loadStrategies();
      loadBacktestHistory();
    }
  }, [isAuthenticated, loadStrategies, loadBacktestHistory]);

  // 启动回测
  const handleStartBacktest = async (values: BacktestConfig) => {
    try {
      setLoading(true);
      const backtestData = {
        ...values,
        startDate: values.startDate,
        endDate: values.endDate
      };

      const result = await apiCallWithRetry(() => strategyAPI.createBacktest(backtestData));
      
      if (result) {
        message.success('回测任务已启动');
        setModalVisible(false);
        form.resetFields();
        
        // 开始轮询回测状态
        pollBacktestStatus(result.id);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 轮询回测状态
  const pollBacktestStatus = (backtestId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/backtest/${backtestId}/status`);
        if (!response.ok) {
          throw new Error(`回测状态API错误: ${response.status} ${response.statusText}`);
        }
        const result = await response.json();
        
        setCurrentBacktest(result);
        
        if (result.status === 'completed' || result.status === 'failed') {
          clearInterval(interval);
          if (result.status === 'completed') {
            message.success('回测完成！');
          } else {
            message.error('回测失败！');
          }
          loadBacktestHistory();
        }
      } catch (error) {
        console.error('Failed to poll backtest status:', error);
        clearInterval(interval);
        message.error('轮询回测状态失败');
      }
    }, 2000);
  };







  // 查看回测结果
  const handleViewResult = (result: BacktestResult) => {
    setCurrentBacktest(result);
    setResultModalVisible(true);
  };

  // 回测历史表格列
  const historyColumns = [
    {
      title: '策略名称',
      dataIndex: 'strategyName',
      key: 'strategyName',
      render: (text: string, record: BacktestResult) => (
        <Space>
          <Text strong>{text}</Text>
          <Badge 
            status={record.status === 'completed' ? 'success' : record.status === 'running' ? 'processing' : 'error'}
            text={record.status === 'completed' ? '已完成' : record.status === 'running' ? '运行中' : '失败'}
          />
        </Space>
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="green">{symbol}</Tag>
    },
    {
      title: '时间周期',
      dataIndex: 'timeframe',
      key: 'timeframe',
      render: (timeframe: string) => <Tag color="blue">{timeframe}</Tag>
    },
    {
      title: '总收益率',
      dataIndex: 'totalReturn',
      key: 'totalReturn',
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#f5222d', fontWeight: 'bold' }}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </Text>
      )
    },
    {
      title: '最大回撤',
      dataIndex: 'maxDrawdown',
      key: 'maxDrawdown',
      render: (value: number) => (
        <Text style={{ color: '#f5222d', fontWeight: 'bold' }}>
          {value.toFixed(2)}%
        </Text>
      )
    },
    {
      title: '胜率',
      dataIndex: 'winRate',
      key: 'winRate',
      render: (value: number) => (
        <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>
          {value.toFixed(1)}%
        </Text>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (text: any, record: BacktestResult) => (
        <Space size="small">
          <Tooltip title="查看结果">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              onClick={() => handleViewResult(record)}
              disabled={record.status !== 'completed'}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 交易记录表格列
  const tradeColumns = [
    {
      title: '交易ID',
      dataIndex: 'id',
      key: 'id',
      width: 100
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      )
    },
    {
      title: '入场时间',
      dataIndex: 'entryTime',
      key: 'entryTime',
      width: 150
    },
    {
      title: '出场时间',
      dataIndex: 'exitTime',
      key: 'exitTime',
      width: 150
    },
    {
      title: '入场价格',
      dataIndex: 'entryPrice',
      key: 'entryPrice',
      render: (price: number) => price.toFixed(2)
    },
    {
      title: '出场价格',
      dataIndex: 'exitPrice',
      key: 'exitPrice',
      render: (price: number) => price.toFixed(2)
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4)
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Text style={{ color: pnl >= 0 ? '#52c41a' : '#f5222d', fontWeight: 'bold' }}>
          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
        </Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge 
          status={status === 'win' ? 'success' : 'error'}
          text={status === 'win' ? '盈利' : '亏损'}
        />
      )
    }
  ];

  // 图表颜色
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card 
            title="回测管理"
            extra={
              <Space>
                <Button 
                  icon={<FilterOutlined />}
                  onClick={() => message.info('筛选功能开发中')}
                >
                  筛选
                </Button>
                <Button 
                  icon={<TableOutlined />}
                  onClick={() => message.info('表格视图开发中')}
                >
                  表格视图
                </Button>
                <Button 
                  icon={<CloudDownloadOutlined />}
                  onClick={() => exportBacktestData('csv')}
                >
                  导出CSV
                </Button>
                <Button 
                  icon={<CloudDownloadOutlined />}
                  onClick={() => exportBacktestData('json')}
                >
                  导出JSON
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    loadStrategies();
                    loadBacktestHistory();
                  }}
                >
                  刷新
                </Button>
              </Space>
            }
          >
            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <Tabs.TabPane 
                tab={
                  <span>
                    <SettingOutlined />
                    回测配置
                  </span>
                } 
                key="config"
              >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleStartBacktest}
              initialValues={{
                initialCapital: 100000,
                positionSize: 10,
                maxPositions: 5,
                stopLoss: 2,
                takeProfit: 3,
                commission: 0.1,
                slippage: 0.05
              }}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="选择策略"
                    name="strategyId"
                    rules={[{ required: true, message: '请选择策略' }]}
                  >
                    <Select placeholder="选择要回测的策略">
                      {strategies.map(strategy => (
                        <Option key={strategy.id} value={strategy.id}>
                          {strategy.name}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="交易对"
                    name="symbol"
                    rules={[{ required: true, message: '请选择交易对' }]}
                  >
                    <Select placeholder="选择交易对">
                      {symbols.map(symbol => (
                        <Option key={symbol} value={symbol}>
                          {symbol}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="时间周期"
                    name="timeframe"
                    rules={[{ required: true, message: '请选择时间周期' }]}
                  >
                    <Select placeholder="选择时间周期">
                      {timeframes.map(timeframe => (
                        <Option key={timeframe.value} value={timeframe.value}>
                          {timeframe.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="回测时间范围"
                    rules={[{ required: true, message: '请选择回测时间范围' }]}
                  >
                    <RangePicker 
                      style={{ width: '100%' }}
                      disabledDate={(current) => current && current > moment().endOf('day')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    label="初始资金 (USDT)"
                    name="initialCapital"
                    rules={[{ required: true, message: '请输入初始资金' }]}
                  >
                    <InputNumber 
                      min={1000} 
                      max={10000000} 
                      style={{ width: '100%' }}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="仓位大小 (%)"
                    name="positionSize"
                    rules={[{ required: true, message: '请输入仓位大小' }]}
                  >
                    <InputNumber 
                      min={1} 
                      max={100} 
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                                          />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="最大持仓数"
                    name="maxPositions"
                    rules={[{ required: true, message: '请输入最大持仓数' }]}
                  >
                    <InputNumber min={1} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    label="止损 (%)"
                    name="stopLoss"
                    rules={[{ required: true, message: '请输入止损比例' }]}
                  >
                    <InputNumber 
                      min={0.1} 
                      max={50} 
                      step={0.1}
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                                          />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="止盈 (%)"
                    name="takeProfit"
                    rules={[{ required: true, message: '请输入止盈比例' }]}
                  >
                    <InputNumber 
                      min={0.1} 
                      max={100} 
                      step={0.1}
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                                          />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label="手续费 (%)"
                    name="commission"
                    rules={[{ required: true, message: '请输入手续费' }]}
                  >
                    <InputNumber 
                      min={0} 
                      max={1} 
                      step={0.01}
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                                          />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={loading}
                    icon={<PlayCircleOutlined />}
                  >
                    开始回测
                  </Button>
                  <Button onClick={() => form.resetFields()}>
                    重置配置
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Tabs.TabPane>

          <Tabs.TabPane 
            tab={
              <span>
                <BarChartOutlined />
                回测历史
              </span>
            } 
            key="history"
          >
            <SmartLoading
              loading={loading}
              error={null}
              data={backtestHistory}
              skeletonVariant="table"
              skeletonLines={8}
            >
              <Table
                columns={historyColumns}
                dataSource={backtestHistory}
                rowKey="id"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                }}
              />
            </SmartLoading>
          </Tabs.TabPane>

          {currentBacktest && (
            <Tabs.TabPane 
              tab={
                <span>
                  <LineChartOutlined />
                  当前回测
                </span>
              } 
              key="current"
            >
              <Card
                extra={
                  <Space>
                    <Switch 
                      checkedChildren="自动刷新" 
                      unCheckedChildren="手动刷新" 
                      checked={autoRefresh}
                      onChange={setAutoRefresh}
                    />
                    {autoRefresh && (
                      <InputNumber
                        min={5}
                        max={300}
                        value={refreshInterval}
                        onChange={setRefreshInterval}
                        addonAfter="秒"
                        style={{ width: 100 }}
                      />
                    )}
                    <Button 
                      icon={<EyeOutlined />}
                      onClick={async () => {
                        setSelectedResult(currentBacktest);
                        if (currentBacktest) {
                          try {
                            const [performanceData, tradeData] = await Promise.allSettled([
                              fetchPerformanceData(currentBacktest.id),
                              fetchTradeAnalysis(currentBacktest.id)
                            ]);
                            
                            if (performanceData.status === 'fulfilled') {
                              setPerformanceData(performanceData.value);
                            } else {
                              message.error(`性能数据加载失败: ${performanceData.reason.message}`);
                              setPerformanceData([]);
                            }
                            
                            if (tradeData.status === 'fulfilled') {
                              setTradeAnalysis(tradeData.value);
                            } else {
                              message.error(`交易数据加载失败: ${tradeData.reason.message}`);
                              setTradeAnalysis([]);
                            }
                          } catch (error) {
                            console.error('Failed to load backtest details:', error);
                            message.error('加载回测详情失败');
                            setPerformanceData([]);
                            setTradeAnalysis([]);
                          }
                        }
                        setResultModalVisible(true);
                      }}
                    >
                      查看详情
                    </Button>
                    <Button 
                      icon={<StopOutlined />}
                      danger
                      onClick={() => message.info('停止回测功能开发中')}
                    >
                      停止回测
                    </Button>
                  </Space>
                }
              >
                <Space style={{ marginBottom: 16 }}>
                  <Text strong>策略: {currentBacktest.strategyName}</Text>
                  <Tag color="green">{currentBacktest.symbol}</Tag>
                  <Tag color="blue">{currentBacktest.timeframe}</Tag>
                  <Badge 
                    status={currentBacktest.status === 'completed' ? 'success' : 'processing'}
                    text={currentBacktest.status === 'completed' ? '已完成' : '运行中'}
                  />
                </Space>

                {currentBacktest.status === 'running' && (
                  <div style={{ marginBottom: 24 }}>
                    <Text>回测进度: </Text>
                    <Progress 
                      percent={currentBacktest.progress} 
                      status="active"
                      style={{ marginLeft: 16, width: 300 }}
                    />
                  </div>
                )}

                {currentBacktest.status === 'completed' && (
                  <>
                    <Row gutter={16} style={{ marginBottom: 24 }}>
                      <Col span={6}>
                        <Statistic
                          title="总收益率"
                          value={currentBacktest.totalReturn}
                          precision={2}
                          valueStyle={{ 
                            color: currentBacktest.totalReturn >= 0 ? '#3f8600' : '#cf1322' 
                          }}
                          suffix="%"
                          prefix={<RiseOutlined />}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="年化收益率"
                          value={currentBacktest.annualizedReturn}
                          precision={2}
                          valueStyle={{ 
                            color: currentBacktest.annualizedReturn >= 0 ? '#3f8600' : '#cf1322' 
                          }}
                          suffix="%"
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="最大回撤"
                          value={currentBacktest.maxDrawdown}
                          precision={2}
                          valueStyle={{ color: '#cf1322' }}
                          suffix="%"
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="夏普比率"
                          value={currentBacktest.sharpeRatio}
                          precision={2}
                          valueStyle={{ color: '#3f8600' }}
                        />
                      </Col>
                    </Row>

                    <Row gutter={16} style={{ marginBottom: 24 }}>
                      <Col span={6}>
                        <Statistic
                          title="胜率"
                          value={currentBacktest.winRate}
                          precision={1}
                          suffix="%"
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="总交易次数"
                          value={currentBacktest.totalTrades}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="盈亏比"
                          value={currentBacktest.profitFactor}
                          precision={2}
                        />
                      </Col>
                      <Col span={6}>
                        <Statistic
                          title="卡尔玛比率"
                          value={currentBacktest.calmarRatio}
                          precision={2}
                        />
                      </Col>
                    </Row>

                    <Divider />

                    <Title level={4}>权益曲线</Title>
                    <div style={{ height: 400, marginBottom: 24 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={currentBacktest.equityCurve}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <RechartsTooltip />
                          <Area 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#8884d8" 
                            fill="#8884d8" 
                            fillOpacity={0.3}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>

                    <Button 
                      type="primary" 
                      icon={<EyeOutlined />}
                      onClick={() => setResultModalVisible(true)}
                    >
                      查看详细结果
                    </Button>
                  </>
                )}
              </Card>
            </Tabs.TabPane>
          )}
        </Tabs>
      </Card>

      {/* 回测结果详情弹窗 */}
      <Modal
        title="回测结果详情"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={null}
        width={1200}
        style={{ top: 20 }}
      >
        {currentBacktest && currentBacktest.status === 'completed' && (
          <div>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Statistic
                  title="总收益率"
                  value={currentBacktest.totalReturn}
                  precision={2}
                  valueStyle={{ 
                    color: currentBacktest.totalReturn >= 0 ? '#3f8600' : '#cf1322' 
                  }}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="年化收益率"
                  value={currentBacktest.annualizedReturn}
                  precision={2}
                  valueStyle={{ 
                    color: currentBacktest.annualizedReturn >= 0 ? '#3f8600' : '#cf1322' 
                  }}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="最大回撤"
                  value={currentBacktest.maxDrawdown}
                  precision={2}
                  valueStyle={{ color: '#cf1322' }}
                  suffix="%"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="夏普比率"
                  value={currentBacktest.sharpeRatio}
                  precision={2}
                />
              </Col>
            </Row>

            <Tabs defaultActiveKey="equity">
              <Tabs.TabPane tab="权益曲线" key="equity">
                <div style={{ height: 400 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={currentBacktest.equityCurve}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Area 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#8884d8" 
                        fill="#8884d8" 
                        fillOpacity={0.3}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Tabs.TabPane>

              <Tabs.TabPane tab="交易记录" key="trades">
                <Table
                  columns={tradeColumns}
                  dataSource={currentBacktest.trades}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true
                  }}
                  scroll={{ x: 1200 }}
                />
              </Tabs.TabPane>

              <Tabs.TabPane tab="性能指标" key="metrics">
                <Row gutter={16}>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="平均交易盈亏"
                        value={currentBacktest.metrics.avgTrade}
                        precision={2}
                        valueStyle={{ 
                          color: currentBacktest.metrics.avgTrade >= 0 ? '#3f8600' : '#cf1322' 
                        }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="平均盈利交易"
                        value={currentBacktest.metrics.avgWinTrade}
                        precision={2}
                        valueStyle={{ color: '#3f8600' }}
                      />
                    </Card>
                  </Col>
                  <Col span={8}>
                    <Card>
                      <Statistic
                        title="平均亏损交易"
                        value={currentBacktest.metrics.avgLossTrade}
                        precision={2}
                        valueStyle={{ color: '#cf1322' }}
                      />
                    </Card>
                  </Col>
                </Row>

                <Row gutter={16} style={{ marginTop: 16 }}>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="最大连续盈利"
                        value={currentBacktest.metrics.maxConsecutiveWins}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="最大连续亏损"
                        value={currentBacktest.metrics.maxConsecutiveLosses}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="恢复因子"
                        value={currentBacktest.metrics.recoveryFactor}
                        precision={2}
                      />
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card>
                      <Statistic
                        title="盈亏比"
                        value={currentBacktest.metrics.profitFactor}
                        precision={2}
                      />
                    </Card>
                  </Col>
                </Row>
              </Tabs.TabPane>
            </Tabs>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default BacktestPage;