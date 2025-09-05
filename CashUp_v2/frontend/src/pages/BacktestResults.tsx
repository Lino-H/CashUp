/**
 * 回测结果可视化页面
 * Backtest Results Visualization Page
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
  DatePicker,
  Space,
  Tag,
  Progress,
  Tabs,
  Alert,
  Divider,
  Tooltip,
  Typography,
  Spin,
  message,
  Modal,
  Drawer
} from 'antd';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarCircle,
  Percentage,
  ClockCircle,
  BarChartOutlined,
  DownloadOutlined,
  EyeOutlined,
  FilterOutlined,
  ReloadOutlined,
  ShareAltOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

// 回测结果数据类型
interface BacktestResult {
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

// 性能指标卡片
const PerformanceMetricCard: React.FC<{
  title: string;
  value: number | string;
  prefix?: string;
  suffix?: string;
  precision?: number;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: number;
  color?: string;
}> = ({ title, value, prefix, suffix, precision = 2, trend, trendValue, color }) => {
  const formatValue = (val: number | string) => {
    if (typeof val === 'number') {
      return val.toFixed(precision);
    }
    return val;
  };

  return (
    <Card>
      <Statistic
        title={title}
        value={formatValue(value)}
        prefix={prefix}
        suffix={suffix}
        valueStyle={{ color: color || (trend === 'up' ? '#3f8600' : trend === 'down' ? '#cf1322' : '#000') }}
      />
      {trend && trendValue !== undefined && (
        <div style={{ marginTop: 8, fontSize: 12, color: trend === 'up' ? '#3f8600' : '#cf1322' }}>
          {trend === 'up' ? <TrendingUp /> : <TrendingDown />} {Math.abs(trendValue).toFixed(2)}%
        </div>
      )}
    </Card>
  );
};

const BacktestResults: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null);
  const [filters, setFilters] = useState({
    strategy: '',
    symbol: '',
    timeframe: '',
    dateRange: null as any,
    status: ''
  });
  const [detailVisible, setDetailVisible] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [compareResults, setCompareResults] = useState<BacktestResult[]>([]);

  // 模拟数据
  useEffect(() => {
    loadMockData();
  }, []);

  const loadMockData = () => {
    setLoading(true);
    
    // 模拟回测结果数据
    const mockResults: BacktestResult[] = [
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
        equityCurve: Array.from({ length: 365 }, (_, i) => ({
          date: new Date(2024, 0, 1 + i).toISOString().split('T')[0],
          equity: 10000 + Math.sin(i * 0.02) * 2000 + i * 15 + Math.random() * 500,
          drawdown: Math.random() * 15
        })),
        trades: Array.from({ length: 20 }, (_, i) => ({
          id: `trade_${i}`,
          symbol: 'BTCUSDT',
          side: Math.random() > 0.5 ? 'buy' : 'sell',
          entryTime: new Date(2024, 0, 1 + i * 10).toISOString(),
          exitTime: new Date(2024, 0, 1 + i * 10 + 4).toISOString(),
          entryPrice: 40000 + Math.random() * 5000,
          exitPrice: 40000 + Math.random() * 5000,
          quantity: 0.1,
          pnl: (Math.random() - 0.3) * 500,
          return: (Math.random() - 0.3) * 10,
          holdingPeriod: Math.floor(Math.random() * 10) + 1
        })),
        monthlyReturns: Array.from({ length: 12 }, (_, i) => ({
          month: `${i + 1}月`,
          return: (Math.random() - 0.2) * 15
        })),
        drawdownPeriods: [
          { startDate: '2024-03-01', endDate: '2024-03-15', depth: -8.5, duration: 14 },
          { startDate: '2024-07-10', endDate: '2024-07-25', depth: -12.3, duration: 15 }
        ]
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
        equityCurve: Array.from({ length: 365 }, (_, i) => ({
          date: new Date(2024, 0, 1 + i).toISOString().split('T')[0],
          equity: 10000 + Math.cos(i * 0.015) * 1500 + i * 8 + Math.random() * 400,
          drawdown: Math.random() * 20
        })),
        trades: Array.from({ length: 15 }, (_, i) => ({
          id: `trade_${i}`,
          symbol: 'ETHUSDT',
          side: Math.random() > 0.5 ? 'buy' : 'sell',
          entryTime: new Date(2024, 0, 1 + i * 15).toISOString(),
          exitTime: new Date(2024, 0, 1 + i * 15 + 6).toISOString(),
          entryPrice: 2200 + Math.random() * 300,
          exitPrice: 2200 + Math.random() * 300,
          quantity: 0.5,
          pnl: (Math.random() - 0.4) * 300,
          return: (Math.random() - 0.4) * 8,
          holdingPeriod: Math.floor(Math.random() * 12) + 1
        })),
        monthlyReturns: Array.from({ length: 12 }, (_, i) => ({
          month: `${i + 1}月`,
          return: (Math.random() - 0.3) * 12
        })),
        drawdownPeriods: [
          { startDate: '2024-05-01', endDate: '2024-05-20', depth: -15.2, duration: 19 },
          { startDate: '2024-09-05', endDate: '2024-09-18', depth: -18.7, duration: 13 }
        ]
      }
    ];

    setResults(mockResults);
    setLoading(false);
  };

  const filteredResults = results.filter(result => {
    return (
      (!filters.strategy || result.strategyName.toLowerCase().includes(filters.strategy.toLowerCase())) &&
      (!filters.symbol || result.symbol.includes(filters.symbol)) &&
      (!filters.timeframe || result.timeframe === filters.timeframe) &&
      (!filters.status || result.status === filters.status)
    );
  });

  const handleViewDetail = (result: BacktestResult) => {
    setSelectedResult(result);
    setDetailVisible(true);
  };

  const handleCompare = (result: BacktestResult) => {
    if (!compareResults.find(r => r.id === result.id)) {
      setCompareResults([...compareResults, result]);
    } else {
      message.warning('该回测结果已在对比列表中');
    }
  };

  const removeFromCompare = (resultId: string) => {
    setCompareResults(compareResults.filter(r => r.id !== resultId));
  };

  const exportResults = (result: BacktestResult) => {
    message.success('导出功能开发中...');
  };

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'strategyName',
      key: 'strategyName',
      render: (text: string, record: BacktestResult) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {record.symbol} | {record.timeframe}
          </div>
        </div>
      )
    },
    {
      title: '回测期间',
      dataIndex: 'startDate',
      key: 'period',
      render: (text: string, record: BacktestResult) => (
        <span>{text} 至 {record.endDate}</span>
      )
    },
    {
      title: '总收益',
      dataIndex: 'totalReturn',
      key: 'totalReturn',
      render: (value: number) => (
        <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      ),
      sorter: (a: BacktestResult, b: BacktestResult) => a.totalReturn - b.totalReturn
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      render: (value: number) => (
        <span style={{ color: value >= 1.5 ? '#3f8600' : value >= 1 ? '#faad14' : '#cf1322' }}>
          {value.toFixed(2)}
        </span>
      ),
      sorter: (a: BacktestResult, b: BacktestResult) => a.sharpeRatio - b.sharpeRatio
    },
    {
      title: '最大回撤',
      dataIndex: 'maxDrawdown',
      key: 'maxDrawdown',
      render: (value: number) => (
        <span style={{ color: '#cf1322' }}>
          {value.toFixed(2)}%
        </span>
      ),
      sorter: (a: BacktestResult, b: BacktestResult) => a.maxDrawdown - b.maxDrawdown
    },
    {
      title: '胜率',
      dataIndex: 'winRate',
      key: 'winRate',
      render: (value: number) => `${value.toFixed(1)}%`,
      sorter: (a: BacktestResult, b: BacktestResult) => a.winRate - b.winRate
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          completed: { color: 'green', text: '已完成' },
          running: { color: 'blue', text: '运行中' },
          failed: { color: 'red', text: '失败' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: BacktestResult) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="加入对比">
            <Button
              type="link"
              icon={<BarChartOutlined />}
              onClick={() => handleCompare(record)}
            />
          </Tooltip>
          <Tooltip title="导出结果">
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => exportResults(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>回测结果分析</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Button
              type={compareMode ? 'primary' : 'default'}
              icon={<BarChartOutlined />}
              onClick={() => setCompareMode(!compareMode)}
            >
              对比模式 {compareResults.length > 0 && `(${compareResults.length})`}
            </Button>
            <Button icon={<ReloadOutlined />} onClick={loadMockData}>
              刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 对比模式 */}
      {compareMode && compareResults.length > 0 && (
        <Card title="回测结果对比" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            {compareResults.map(result => (
              <Col span={8} key={result.id}>
                <Card
                  size="small"
                  title={result.strategyName}
                  extra={
                    <Button
                      type="text"
                      size="small"
                      onClick={() => removeFromCompare(result.id)}
                    >
                      移除
                    </Button>
                  }
                >
                  <Statistic
                    title="总收益"
                    value={result.totalReturn}
                    suffix="%"
                    precision={2}
                    valueStyle={{ color: result.totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
                  />
                  <Statistic
                    title="夏普比率"
                    value={result.sharpeRatio}
                    precision={2}
                    style={{ marginTop: 8 }}
                  />
                  <Statistic
                    title="最大回撤"
                    value={result.maxDrawdown}
                    suffix="%"
                    precision={2}
                    valueStyle={{ color: '#cf1322' }}
                    style={{ marginTop: 8 }}
                  />
                </Card>
              </Col>
            ))}
          </Row>
          
          {/* 对比图表 */}
          <div style={{ marginTop: 16, height: 300 }}>
            <Title level={4}>净值曲线对比</Title>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={compareResults[0]?.equityCurve || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                {compareResults.map((result, index) => (
                  <Line
                    key={result.id}
                    type="monotone"
                    dataKey="equity"
                    stroke={['#8884d8', '#82ca9d', '#ffc658'][index]}
                    name={result.strategyName}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {/* 筛选器 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={4}>
            <Select
              placeholder="选择策略"
              style={{ width: '100%' }}
              allowClear
              value={filters.strategy}
              onChange={(value) => setFilters({ ...filters, strategy: value })}
            >
              <Option value="MA Cross Strategy">MA Cross Strategy</Option>
              <Option value="RSI Mean Reversion">RSI Mean Reversion</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="选择交易对"
              style={{ width: '100%' }}
              allowClear
              value={filters.symbol}
              onChange={(value) => setFilters({ ...filters, symbol: value })}
            >
              <Option value="BTCUSDT">BTCUSDT</Option>
              <Option value="ETHUSDT">ETHUSDT</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="选择时间周期"
              style={{ width: '100%' }}
              allowClear
              value={filters.timeframe}
              onChange={(value) => setFilters({ ...filters, timeframe: value })}
            >
              <Option value="1h">1小时</Option>
              <Option value="4h">4小时</Option>
              <Option value="1d">1天</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="选择状态"
              style={{ width: '100%' }}
              allowClear
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
            >
              <Option value="completed">已完成</Option>
              <Option value="running">运行中</Option>
              <Option value="failed">失败</Option>
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['开始日期', '结束日期']}
            />
          </Col>
          <Col span={4}>
            <Button type="primary" icon={<FilterOutlined />} block>
              应用筛选
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 回测结果列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredResults}
          rowKey="id"
          loading={loading}
          pagination={{
            total: filteredResults.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
        />
      </Card>

      {/* 详情抽屉 */}
      <Drawer
        title={selectedResult?.strategyName}
        placement="right"
        width={1200}
        onClose={() => setDetailVisible(false)}
        open={detailVisible}
      >
        {selectedResult && (
          <div>
            {/* 基本信息 */}
            <Card title="基本信息" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="策略名称" value={selectedResult.strategyName} />
                </Col>
                <Col span={8}>
                  <Statistic title="交易对" value={selectedResult.symbol} />
                </Col>
                <Col span={8}>
                  <Statistic title="时间周期" value={selectedResult.timeframe} />
                </Col>
                <Col span={8}>
                  <Statistic title="回测期间" value={`${selectedResult.startDate} 至 ${selectedResult.endDate}`} />
                </Col>
                <Col span={8}>
                  <Statistic title="初始资金" value={selectedResult.initialCapital} prefix="$" />
                </Col>
                <Col span={8}>
                  <Statistic title="最终资金" value={selectedResult.finalCapital} prefix="$" />
                </Col>
              </Row>
            </Card>

            {/* 性能指标 */}
            <Card title="性能指标" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="总收益"
                    value={selectedResult.totalReturn}
                    suffix="%"
                    trend={selectedResult.totalReturn >= 0 ? 'up' : 'down'}
                    trendValue={selectedResult.totalReturn}
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="夏普比率"
                    value={selectedResult.sharpeRatio}
                    color={selectedResult.sharpeRatio >= 1.5 ? '#3f8600' : selectedResult.sharpeRatio >= 1 ? '#faad14' : '#cf1322'}
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="最大回撤"
                    value={selectedResult.maxDrawdown}
                    suffix="%"
                    color="#cf1322"
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="胜率"
                    value={selectedResult.winRate}
                    suffix="%"
                    color={selectedResult.winRate >= 60 ? '#3f8600' : '#faad14'}
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="盈利因子"
                    value={selectedResult.profitFactor}
                    color={selectedResult.profitFactor >= 2 ? '#3f8600' : '#faad14'}
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="总交易次数"
                    value={selectedResult.totalTrades}
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="平均盈利"
                    value={selectedResult.avgWin}
                    prefix="$"
                    color="#3f8600"
                  />
                </Col>
                <Col span={6}>
                  <PerformanceMetricCard
                    title="平均亏损"
                    value={selectedResult.avgLoss}
                    prefix="$"
                    color="#cf1322"
                  />
                </Col>
              </Row>
            </Card>

            {/* 图表分析 */}
            <Card title="图表分析" style={{ marginBottom: 16 }}>
              <Tabs defaultActiveKey="equity">
                <TabPane tab="净值曲线" key="equity">
                  <div style={{ height: 400 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={selectedResult.equityCurve}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <RechartsTooltip />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="equity"
                          stroke="#8884d8"
                          fill="#8884d8"
                          fillOpacity={0.3}
                          name="净值"
                        />
                        <Line
                          type="monotone"
                          dataKey="drawdown"
                          stroke="#ff7300"
                          name="回撤"
                          yAxisId="right"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </TabPane>
                <TabPane tab="月度收益" key="monthly">
                  <div style={{ height: 400 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={selectedResult.monthlyReturns}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <RechartsTooltip />
                        <Bar dataKey="return" fill="#8884d8" name="收益率" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </TabPane>
                <TabPane tab="交易分布" key="trades">
                  <div style={{ height: 400 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart data={selectedResult.trades}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="holdingPeriod" name="持仓时间" />
                        <YAxis dataKey="return" name="收益率" />
                        <RechartsTooltip />
                        <Scatter dataKey="return" fill="#8884d8" />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </TabPane>
              </Tabs>
            </Card>

            {/* 交易记录 */}
            <Card title="交易记录">
              <Table
                columns={[
                  { title: '交易ID', dataIndex: 'id', key: 'id' },
                  { title: '交易对', dataIndex: 'symbol', key: 'symbol' },
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
                  { title: '入场价格', dataIndex: 'entryPrice', key: 'entryPrice', render: (v: number) => `$${v.toFixed(2)}` },
                  { title: '出场价格', dataIndex: 'exitPrice', key: 'exitPrice', render: (v: number) => `$${v.toFixed(2)}` },
                  { title: '数量', dataIndex: 'quantity', key: 'quantity' },
                  {
                    title: '盈亏',
                    dataIndex: 'pnl',
                    key: 'pnl',
                    render: (v: number) => (
                      <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>
                        ${v.toFixed(2)}
                      </span>
                    )
                  },
                  {
                    title: '收益率',
                    dataIndex: 'return',
                    key: 'return',
                    render: (v: number) => (
                      <span style={{ color: v >= 0 ? '#3f8600' : '#cf1322' }}>
                        {v >= 0 ? '+' : ''}{v.toFixed(2)}%
                      </span>
                    )
                  },
                  { title: '持仓时间', dataIndex: 'holdingPeriod', key: 'holdingPeriod', render: (v: number) => `${v}天` }
                ]}
                dataSource={selectedResult.trades}
                rowKey="id"
                pagination={{ pageSize: 10 }}
              />
            </Card>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default BacktestResults;