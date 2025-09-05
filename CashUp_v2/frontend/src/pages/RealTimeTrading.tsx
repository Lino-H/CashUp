/**
 * 实时交易监控页面 - 简化版本
 * Real-time Trading Monitoring Page - Simplified Version
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Select,
  Space,
  Tag,
  Progress,
  Alert,
  Divider,
  Typography,
  Spin,
  message,
  Modal,
  Badge,
  Switch,
  InputNumber,
  Form,
  Input,
} from 'antd';
import {
  RiseOutlined as TrendingUp,
  FallOutlined as TrendingDown,
  DollarCircleOutlined as DollarCircle,
  PercentageOutlined as Percentage,
  ClockCircleOutlined as ClockCircle,
  BarChartOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  EyeOutlined,
  SettingOutlined,
  BellOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  OrderedListOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;

// 实时交易数据类型
interface RealTimeTrade {
  id: string;
  strategyName: string;
  symbol: string;
  side: 'buy' | 'sell';
  price: number;
  quantity: number;
  amount: number;
  timestamp: string;
  exchange: string;
  status: 'pending' | 'filled' | 'cancelled' | 'failed';
  orderId: string;
  fee: number;
  pnl?: number;
}

// 实时价格数据类型
interface RealTimePrice {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

// 策略状态类型
interface StrategyStatus {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'error' | 'paused';
  startTime?: string;
  uptime: string;
  tradesCount: number;
  totalPnl: number;
  winRate: number;
  currentPositions: number;
  maxDrawdown: number;
  cpuUsage: number;
  memoryUsage: number;
  lastSignal?: string;
  lastError?: string;
}

// 账户余额类型
interface AccountBalance {
  exchange: string;
  totalBalance: number;
  availableBalance: number;
  usedBalance: number;
  btcValue: number;
  change24h: number;
  currencies: Array<{
    currency: string;
    balance: number;
    available: number;
    locked: number;
    btcValue: number;
  }>;
}

// 当前持仓类型
interface CurrentPosition {
  id: string;
  strategyName: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  margin: number;
  leverage: number;
  liquidationPrice: number;
  openTime: string;
  duration: string;
  exchange: string;
}

// 风险指标类型
interface RiskMetrics {
  totalExposure: number;
  marginUsage: number;
  maxDrawdown: number;
  var95: number;
  sharpeRatio: number;
  beta: number;
  correlation: number;
  riskLevel: 'low' | 'medium' | 'high';
}

// 实时交易监控组件
const RealTimeTrading: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('all');
  const [selectedExchange, setSelectedExchange] = useState<string>('all');
  
  // 实时数据状态
  const [recentTrades, setRecentTrades] = useState<RealTimeTrade[]>([]);
  const [realTimePrices, setRealTimePrices] = useState<RealTimePrice[]>([]);
  const [strategyStatus, setStrategyStatus] = useState<StrategyStatus[]>([]);
  const [accountBalances, setAccountBalances] = useState<AccountBalance[]>([]);
  const [currentPositions, setCurrentPositions] = useState<CurrentPosition[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  
  // 详情显示
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<RealTimeTrade | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  
  // 模拟数据加载
  useEffect(() => {
    loadMockData();
    if (autoRefresh) {
      const interval = setInterval(loadMockData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadMockData = () => {
    // 模拟实时交易数据
    const mockTrades: RealTimeTrade[] = [
      {
        id: '1',
        strategyName: 'MA Cross Strategy',
        symbol: 'BTCUSDT',
        side: 'buy',
        price: 43250.50,
        quantity: 0.1,
        amount: 4325.05,
        timestamp: new Date().toISOString(),
        exchange: 'Binance',
        status: 'filled',
        orderId: '123456789',
        fee: 4.32,
        pnl: 25.50
      },
      {
        id: '2',
        strategyName: 'RSI Mean Reversion',
        symbol: 'ETHUSDT',
        side: 'sell',
        price: 2250.30,
        quantity: 0.5,
        amount: 1125.15,
        timestamp: new Date(Date.now() - 60000).toISOString(),
        exchange: 'Gate.io',
        status: 'filled',
        orderId: '987654321',
        fee: 1.12,
        pnl: -15.20
      }
    ];

    // 模拟实时价格数据
    const mockPrices: RealTimePrice[] = [
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

    // 模拟策略状态
    const mockStrategyStatus: StrategyStatus[] = [
      {
        id: '1',
        name: 'MA Cross Strategy',
        status: 'running',
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
        status: 'running',
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

    // 模拟账户余额
    const mockBalances: AccountBalance[] = [
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
      },
      {
        exchange: 'Gate.io',
        totalBalance: 8750.30,
        availableBalance: 6250.30,
        usedBalance: 2500.00,
        btcValue: 0.202,
        change24h: -125.60,
        currencies: [
          { currency: 'USDT', balance: 6250.30, available: 6250.30, locked: 0, btcValue: 0.144 },
          { currency: 'ETH', balance: 1.2, available: 1.2, locked: 0, btcValue: 0.058 }
        ]
      }
    ];

    // 模拟当前持仓
    const mockPositions: CurrentPosition[] = [
      {
        id: '1',
        strategyName: 'MA Cross Strategy',
        symbol: 'BTCUSDT',
        side: 'long',
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
      },
      {
        id: '2',
        strategyName: 'RSI Mean Reversion',
        symbol: 'ETHUSDT',
        side: 'short',
        quantity: 0.5,
        entryPrice: 2335.00,
        currentPrice: 2250.30,
        pnl: 42.35,
        pnlPercent: 3.63,
        margin: 1167.50,
        leverage: 1,
        liquidationPrice: 0,
        openTime: '2024-01-19T14:15:00Z',
        duration: '1d 2h',
        exchange: 'Gate.io'
      }
    ];

    // 模拟风险指标
    const mockRiskMetrics: RiskMetrics = {
      totalExposure: 5347.50,
      marginUsage: 45.2,
      maxDrawdown: -8.5,
      var95: -1250.30,
      sharpeRatio: 1.85,
      beta: 0.85,
      correlation: 0.72,
      riskLevel: 'medium'
    };

    setRecentTrades(mockTrades);
    setRealTimePrices(mockPrices);
    setStrategyStatus(mockStrategyStatus);
    setAccountBalances(mockBalances);
    setCurrentPositions(mockPositions);
    setRiskMetrics(mockRiskMetrics);
  };

  const handleViewTradeDetail = (trade: RealTimeTrade) => {
    setSelectedTrade(trade);
    setDetailVisible(true);
  };

  const handleControlStrategy = (strategyId: string, action: 'start' | 'stop' | 'pause') => {
    message.success(`策略 ${action} 操作已执行`);
    loadMockData();
  };

  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => (
        <span>{moment(timestamp).format('HH:mm:ss')}</span>
      ),
      sorter: (a: RealTimeTrade, b: RealTimeTrade) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    },
    {
      title: '策略',
      dataIndex: 'strategyName',
      key: 'strategyName',
      render: (text: string, record: RealTimeTrade) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>{record.exchange}</div>
        </div>
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Tag color="blue">{symbol}</Tag>
      )
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
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`,
      sorter: (a: RealTimeTrade, b: RealTimeTrade) => a.price - b.price
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4)
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => `$${amount.toFixed(2)}`
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span style={{ color: pnl >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          {pnl >= 0 ? '+' : ''}${pnl?.toFixed(2) || '0.00'}
        </span>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          pending: { color: 'orange', text: '待成交' },
          filled: { color: 'green', text: '已成交' },
          cancelled: { color: 'red', text: '已取消' },
          failed: { color: 'red', text: '失败' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: RealTimeTrade) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewTradeDetail(record)}
        >
          详情
        </Button>
      )
    }
  ];

  const statusColor = {
    running: '#52c41a',
    stopped: '#8c8c8c',
    error: '#ff4d4f',
    paused: '#faad14'
  };

  const statusText = {
    running: '运行中',
    stopped: '已停止',
    error: '错误',
    paused: '暂停'
  };

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>实时交易监控</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <span>自动刷新:</span>
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
            />
            <Select
              value={refreshInterval}
              onChange={setRefreshInterval}
              style={{ width: 120 }}
            >
              <Option value={1000}>1秒</Option>
              <Option value={5000}>5秒</Option>
              <Option value={10000}>10秒</Option>
              <Option value={30000}>30秒</Option>
            </Select>
            <Button icon={<SettingOutlined />} onClick={() => setSettingsVisible(true)}>
              设置
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadMockData}>
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 实时状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总余额"
              value={accountBalances.reduce((sum, balance) => sum + balance.totalBalance, 0)}
              prefix="$"
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              24h变化: +${accountBalances.reduce((sum, balance) => sum + balance.change24h, 0).toFixed(2)}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={recentTrades.reduce((sum, trade) => sum + (trade.pnl || 0), 0)}
              prefix="$"
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              交易次数: {recentTrades.length}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行策略"
              value={strategyStatus.filter(s => s.status === 'running').length}
              suffix={`/ ${strategyStatus.length}`}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              总持仓: {currentPositions.length}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="风险等级"
              value={riskMetrics?.riskLevel === 'low' ? '低' : riskMetrics?.riskLevel === 'medium' ? '中' : '高'}
              valueStyle={{ 
                color: riskMetrics?.riskLevel === 'low' ? '#52c41a' : 
                       riskMetrics?.riskLevel === 'medium' ? '#faad14' : '#ff4d4f' 
              }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              杠杆使用: {riskMetrics?.marginUsage.toFixed(1)}%
            </div>
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* 策略状态 */}
        <Col span={12}>
          <Card title="策略状态">
            {strategyStatus.map(strategy => (
              <div key={strategy.id} style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={8}>
                    <div style={{ fontWeight: 'bold' }}>{strategy.name}</div>
                    <Tag color={statusColor[strategy.status]} style={{ marginTop: 4 }}>
                      {statusText[strategy.status]}
                    </Tag>
                  </Col>
                  <Col span={8}>
                    <div style={{ fontSize: 12, color: '#666' }}>运行时间</div>
                    <div>{strategy.uptime}</div>
                  </Col>
                  <Col span={8}>
                    <div style={{ fontSize: 12, color: '#666' }}>今日盈亏</div>
                    <div style={{ color: strategy.totalPnl >= 0 ? '#3f8600' : '#cf1322' }}>
                      ${strategy.totalPnl.toFixed(2)}
                    </div>
                  </Col>
                </Row>
                <Row gutter={16} style={{ marginTop: 8 }}>
                  <Col span={6}>
                    <div style={{ fontSize: 12, color: '#666' }}>交易次数</div>
                    <div>{strategy.tradesCount}</div>
                  </Col>
                  <Col span={6}>
                    <div style={{ fontSize: 12, color: '#666' }}>胜率</div>
                    <div>{strategy.winRate.toFixed(1)}%</div>
                  </Col>
                  <Col span={6}>
                    <div style={{ fontSize: 12, color: '#666' }}>持仓数</div>
                    <div>{strategy.currentPositions}</div>
                  </Col>
                  <Col span={6}>
                    <Space>
                      <Button
                        type="link"
                        size="small"
                        icon={strategy.status === 'running' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                        onClick={() => handleControlStrategy(strategy.id, strategy.status === 'running' ? 'pause' : 'start')}
                      />
                      <Button
                        type="link"
                        size="small"
                        icon={<StopOutlined />}
                        onClick={() => handleControlStrategy(strategy.id, 'stop')}
                      />
                    </Space>
                  </Col>
                </Row>
                <Divider style={{ margin: '8px 0' }} />
              </div>
            ))}
          </Card>
        </Col>

        {/* 实时价格 */}
        <Col span={12}>
          <Card title="实时价格">
            {realTimePrices.map(price => (
              <div key={price.symbol} style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={8}>
                    <div style={{ fontWeight: 'bold' }}>{price.symbol}</div>
                    <div style={{ fontSize: 18, color: price.changePercent24h >= 0 ? '#3f8600' : '#cf1322' }}>
                      ${price.price.toFixed(2)}
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ fontSize: 12, color: '#666' }}>24h变化</div>
                    <div style={{ color: price.changePercent24h >= 0 ? '#3f8600' : '#cf1322' }}>
                      {price.changePercent24h >= 0 ? '+' : ''}{price.changePercent24h.toFixed(2)}%
                    </div>
                  </Col>
                  <Col span={8}>
                    <div style={{ fontSize: 12, color: '#666' }}>24h成交量</div>
                    <div>${(price.volume24h / 1000000).toFixed(1)}M</div>
                  </Col>
                </Row>
                <Divider style={{ margin: '8px 0' }} />
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      {/* 实时交易表格 */}
      <Card title="实时交易" style={{ marginBottom: 24 }}>
        <Table
          columns={tradeColumns}
          dataSource={recentTrades}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 当前持仓 */}
      <Card title="当前持仓">
        <Table
          columns={[
            {
              title: '策略',
              dataIndex: 'strategyName',
              key: 'strategyName'
            },
            {
              title: '交易对',
              dataIndex: 'symbol',
              key: 'symbol',
              render: (symbol: string) => <Tag color="blue">{symbol}</Tag>
            },
            {
              title: '方向',
              dataIndex: 'side',
              key: 'side',
              render: (side: string) => (
                <Tag color={side === 'long' ? 'green' : 'red'}>
                  {side === 'long' ? '多头' : '空头'}
                </Tag>
              )
            },
            {
              title: '数量',
              dataIndex: 'quantity',
              key: 'quantity',
              render: (quantity: number) => quantity.toFixed(4)
            },
            {
              title: '入场价格',
              dataIndex: 'entryPrice',
              key: 'entryPrice',
              render: (price: number) => `$${price.toFixed(2)}`
            },
            {
              title: '当前价格',
              dataIndex: 'currentPrice',
              key: 'currentPrice',
              render: (price: number) => `$${price.toFixed(2)}`
            },
            {
              title: '盈亏',
              dataIndex: 'pnl',
              key: 'pnl',
              render: (pnl: number) => (
                <span style={{ color: pnl >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
                  {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
                </span>
              )
            },
            {
              title: '盈亏比例',
              dataIndex: 'pnlPercent',
              key: 'pnlPercent',
              render: (percent: number) => (
                <span style={{ color: percent >= 0 ? '#3f8600' : '#cf1322' }}>
                  {percent >= 0 ? '+' : ''}{percent.toFixed(2)}%
                </span>
              )
            },
            {
              title: '持仓时间',
              dataIndex: 'duration',
              key: 'duration'
            },
            {
              title: '交易所',
              dataIndex: 'exchange',
              key: 'exchange'
            }
          ]}
          dataSource={currentPositions}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true
          }}
        />
      </Card>

      {/* 交易详情模态框 */}
      <Modal
        title="交易详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={600}
      >
        {selectedTrade && (
          <div>
            <Card title="基本信息" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="交易ID" value={selectedTrade.id} />
                </Col>
                <Col span={12}>
                  <Statistic title="策略名称" value={selectedTrade.strategyName} />
                </Col>
                <Col span={12}>
                  <Statistic title="交易对" value={selectedTrade.symbol} />
                </Col>
                <Col span={12}>
                  <Statistic title="交易所" value={selectedTrade.exchange} />
                </Col>
                <Col span={12}>
                  <Statistic title="订单ID" value={selectedTrade.orderId} />
                </Col>
                <Col span={12}>
                  <Statistic title="状态" value={selectedTrade.status} />
                </Col>
              </Row>
            </Card>

            <Card title="交易信息">
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="方向" value={selectedTrade.side === 'buy' ? '买入' : '卖出'} />
                </Col>
                <Col span={12}>
                  <Statistic title="价格" value={`$${selectedTrade.price.toFixed(2)}`} />
                </Col>
                <Col span={12}>
                  <Statistic title="数量" value={selectedTrade.quantity.toFixed(4)} />
                </Col>
                <Col span={12}>
                  <Statistic title="金额" value={`$${selectedTrade.amount.toFixed(2)}`} />
                </Col>
                <Col span={12}>
                  <Statistic title="手续费" value={`$${selectedTrade.fee.toFixed(2)}`} />
                </Col>
                <Col span={12}>
                  <Statistic 
                    title="盈亏" 
                    value={`$${selectedTrade.pnl?.toFixed(2) || '0.00'}`}
                    valueStyle={{ color: (selectedTrade.pnl || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                  />
                </Col>
              </Row>
            </Card>
          </div>
        )}
      </Modal>

      {/* 设置模态框 */}
      <Modal
        title="监控设置"
        open={settingsVisible}
        onCancel={() => setSettingsVisible(false)}
        footer={null}
        width={600}
      >
        <Form layout="vertical">
          <Form.Item label="自动刷新">
            <Switch checked={autoRefresh} onChange={setAutoRefresh} />
          </Form.Item>
          <Form.Item label="刷新间隔">
            <Select value={refreshInterval} onChange={setRefreshInterval}>
              <Option value={1000}>1秒</Option>
              <Option value={5000}>5秒</Option>
              <Option value={10000}>10秒</Option>
              <Option value={30000}>30秒</Option>
            </Select>
          </Form.Item>
          <Form.Item label="告警设置">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <span>盈亏告警阈值: </span>
                <InputNumber min={0} max={10000} defaultValue={1000} style={{ width: 120 }} />
                <span style={{ marginLeft: 8 }}>美元</span>
              </div>
              <div>
                <span>风险告警阈值: </span>
                <InputNumber min={0} max={100} defaultValue={80} style={{ width: 120 }} />
                <span style={{ marginLeft: 8 }}>%</span>
              </div>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RealTimeTrading;