/**
 * 数据分析和图表页面
 * Data Analysis and Charts Page
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Button,
  Tabs,
  Statistic,
  Table,
  Tag,
  Space,
  Tooltip,
  Modal,
  Form,
  Input,
  Radio,
  Switch,
  Slider,
  Alert,
  Spin,
  Divider,
  Progress,
  Typography
} from 'antd';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  CandlestickChart,
  Candlestick
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  DollarOutlined,
  PercentageOutlined,
  AlertOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ScatterChartOutlined,
  DownloadOutlined,
  FilterOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

// 数据分析接口定义
interface AnalysisData {
  date: string;
  value: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  close?: number;
}

interface CorrelationData {
  symbol1: string;
  symbol2: string;
  correlation: number;
  pValue: number;
}

interface PerformanceMetric {
  strategy: string;
  symbol: string;
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  tradesCount: number;
  avgHoldingPeriod: number;
}

interface MarketSentiment {
  date: string;
  fearGreedIndex: number;
  volumeProfile: number;
  volatilityIndex: number;
  marketMomentum: number;
}

interface RiskAnalysis {
  metric: string;
  value: number;
  threshold: number;
  status: 'normal' | 'warning' | 'danger';
  trend: 'up' | 'down' | 'stable';
}

const DataAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d');
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('performance');
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);
  const [chartSettings, setChartSettings] = useState({
    showVolume: true,
    showMovingAverages: true,
    showBollingerBands: false,
    showRSI: false,
    showMACD: false,
    maPeriod: 20,
    bollingerPeriod: 20,
    bollingerStdDev: 2
  });
  const [settingsVisible, setSettingsVisible] = useState(false);

  // 模拟数据
  const performanceData: AnalysisData[] = [
    { date: '2024-01-01', value: 100000, volume: 1000000 },
    { date: '2024-01-02', value: 101500, volume: 1200000 },
    { date: '2024-01-03', value: 102800, volume: 980000 },
    { date: '2024-01-04', value: 101200, volume: 1500000 },
    { date: '2024-01-05', value: 103500, volume: 1100000 },
    { date: '2024-01-06', value: 104200, volume: 1300000 },
    { date: '2024-01-07', value: 105800, volume: 1400000 },
  ];

  const correlationData: CorrelationData[] = [
    { symbol1: 'BTCUSDT', symbol2: 'ETHUSDT', correlation: 0.85, pValue: 0.001 },
    { symbol1: 'BTCUSDT', symbol2: 'BNBUSDT', correlation: 0.72, pValue: 0.005 },
    { symbol1: 'ETHUSDT', symbol2: 'BNBUSDT', correlation: 0.68, pValue: 0.008 },
    { symbol1: 'BTCUSDT', symbol2: 'ADAUSDT', correlation: 0.45, pValue: 0.05 },
    { symbol1: 'ETHUSDT', symbol2: 'ADAUSDT', correlation: 0.52, pValue: 0.03 },
  ];

  const performanceMetrics: PerformanceMetric[] = [
    {
      strategy: 'MA Cross Strategy',
      symbol: 'BTCUSDT',
      totalReturn: 15.8,
      sharpeRatio: 1.85,
      maxDrawdown: -8.5,
      winRate: 65.4,
      profitFactor: 2.1,
      tradesCount: 156,
      avgHoldingPeriod: 2.5
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
      avgHoldingPeriod: 1.8
    },
    {
      strategy: 'Breakout Strategy',
      symbol: 'BNBUSDT',
      totalReturn: 22.1,
      sharpeRatio: 2.15,
      maxDrawdown: -6.8,
      winRate: 71.2,
      profitFactor: 2.8,
      tradesCount: 234,
      avgHoldingPeriod: 3.2
    }
  ];

  const marketSentimentData: MarketSentiment[] = [
    { date: '2024-01-01', fearGreedIndex: 65, volumeProfile: 120, volatilityIndex: 18, marketMomentum: 75 },
    { date: '2024-01-02', fearGreedIndex: 58, volumeProfile: 135, volatilityIndex: 22, marketMomentum: 68 },
    { date: '2024-01-03', fearGreedIndex: 72, volumeProfile: 110, volatilityIndex: 15, marketMomentum: 82 },
    { date: '2024-01-04', fearGreedIndex: 48, volumeProfile: 145, volatilityIndex: 28, marketMomentum: 55 },
    { date: '2024-01-05', fearGreedIndex: 68, volumeProfile: 125, volatilityIndex: 20, marketMomentum: 78 },
  ];

  const riskAnalysis: RiskAnalysis[] = [
    { metric: 'VaR (95%)', value: 1250, threshold: 1500, status: 'normal', trend: 'stable' },
    { metric: '最大回撤', value: 8.5, threshold: 10, status: 'normal', trend: 'down' },
    { metric: '夏普比率', value: 1.85, threshold: 1.5, status: 'normal', trend: 'up' },
    { metric: '信息比率', value: 0.85, threshold: 0.8, status: 'normal', trend: 'up' },
    { metric: '索提诺比率', value: 1.25, threshold: 1.2, status: 'normal', trend: 'stable' },
    { metric: '卡玛比率', value: 1.15, threshold: 1.0, status: 'normal', trend: 'up' },
  ];

  const strategyPerformance = [
    { strategy: 'MA Cross', return: 15.8, risk: 8.5, sharpe: 1.85 },
    { strategy: 'RSI Mean Reversion', return: 12.3, risk: 12.3, sharpe: 1.42 },
    { strategy: 'Breakout', return: 22.1, risk: 6.8, sharpe: 2.15 },
    { strategy: 'Momentum', return: 18.5, risk: 10.2, sharpe: 1.78 },
    { strategy: 'Arbitrage', return: 8.9, risk: 3.2, sharpe: 2.45 },
  ];

  const assetAllocation = [
    { name: 'BTC', value: 45, color: '#FF6B6B' },
    { name: 'ETH', value: 30, color: '#4ECDC4' },
    { name: 'BNB', value: 15, color: '#45B7D1' },
    { name: '其他', value: 10, color: '#96CEB4' },
  ];

  const columns: ColumnsType<PerformanceMetric> = [
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '总收益率',
      dataIndex: 'totalReturn',
      key: 'totalReturn',
      render: (value) => (
        <Statistic
          value={value}
          suffix="%"
          valueStyle={{ color: value >= 0 ? '#3f8600' : '#cf1322' }}
          prefix={value >= 0 ? <TrendingUp /> : <TrendingDown />}
        />
      )
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      render: (value) => (
        <Statistic
          value={value}
          precision={2}
          valueStyle={{ color: value >= 1.5 ? '#3f8600' : '#d48806' }}
        />
      )
    },
    {
      title: '最大回撤',
      dataIndex: 'maxDrawdown',
      key: 'maxDrawdown',
      render: (value) => (
        <Statistic
          value={value}
          suffix="%"
          valueStyle={{ color: '#cf1322' }}
        />
      )
    },
    {
      title: '胜率',
      dataIndex: 'winRate',
      key: 'winRate',
      render: (value) => (
        <Progress
          percent={value}
          size="small"
          strokeColor={value >= 60 ? '#3f8600' : '#d48806'}
        />
      )
    },
    {
      title: '盈亏比',
      dataIndex: 'profitFactor',
      key: 'profitFactor',
      render: (value) => (
        <Statistic
          value={value}
          precision={2}
          valueStyle={{ color: value >= 2 ? '#3f8600' : '#d48806' }}
        />
      )
    },
    {
      title: '交易次数',
      dataIndex: 'tradesCount',
      key: 'tradesCount',
      render: (value) => <Text>{value}</Text>
    },
    {
      title: '平均持仓时间',
      dataIndex: 'avgHoldingPeriod',
      key: 'avgHoldingPeriod',
      render: (value) => <Text>{value}天</Text>
    }
  ];

  const correlationColumns: ColumnsType<CorrelationData> = [
    {
      title: '交易对1',
      dataIndex: 'symbol1',
      key: 'symbol1',
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '交易对2',
      dataIndex: 'symbol2',
      key: 'symbol2',
      render: (text) => <Tag color="green">{text}</Tag>
    },
    {
      title: '相关系数',
      dataIndex: 'correlation',
      key: 'correlation',
      render: (value) => (
        <Progress
          percent={Math.abs(value) * 100}
          size="small"
          strokeColor={Math.abs(value) >= 0.7 ? '#3f8600' : Math.abs(value) >= 0.5 ? '#d48806' : '#cf1322'}
          format={() => value.toFixed(3)}
        />
      )
    },
    {
      title: 'P值',
      dataIndex: 'pValue',
      key: 'pValue',
      render: (value) => (
        <Text type={value <= 0.05 ? 'success' : 'warning'}>
          {value.toFixed(3)}
        </Text>
      )
    },
    {
      title: '相关性强度',
      key: 'strength',
      render: (_, record) => {
        const abs = Math.abs(record.correlation);
        let strength, color;
        if (abs >= 0.7) {
          strength = '强相关';
          color = 'green';
        } else if (abs >= 0.5) {
          strength = '中等相关';
          color = 'orange';
        } else if (abs >= 0.3) {
          strength = '弱相关';
          color = 'blue';
        } else {
          strength = '无相关';
          color = 'gray';
        }
        return <Tag color={color}>{strength}</Tag>;
      }
    }
  ];

  const exportData = () => {
    // 实现数据导出功能
    console.log('导出数据');
  };

  const renderPerformanceChart = () => (
    <Card title="策略表现分析" extra={
      <Space>
        <Select
          value={selectedTimeRange}
          onChange={setSelectedTimeRange}
          style={{ width: 120 }}
        >
          <Option value="1d">1天</Option>
          <Option value="7d">7天</Option>
          <Option value="30d">30天</Option>
          <Option value="90d">90天</Option>
          <Option value="1y">1年</Option>
        </Select>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <RechartsTooltip />
              <Legend />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="value"
                fill="#8884d8"
                fillOpacity={0.3}
                stroke="#8884d8"
                name="组合价值"
              />
              {chartSettings.showVolume && (
                <Bar
                  yAxisId="right"
                  dataKey="volume"
                  fill="#82ca9d"
                  name="成交量"
                />
              )}
              {chartSettings.showMovingAverages && (
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="value"
                  stroke="#ff7300"
                  name="移动平均"
                  strokeDasharray="5 5"
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </Col>
      </Row>
    </Card>
  );

  const renderCorrelationMatrix = () => (
    <Card title="相关性分析" extra={
      <Space>
        <Button icon={<FilterOutlined />}>筛选</Button>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Row gutter={[16, 16]}>
        <Col span={16}>
          <Table
            columns={correlationColumns}
            dataSource={correlationData}
            pagination={false}
            size="small"
          />
        </Col>
        <Col span={8}>
          <Card size="small" title="相关性分布">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: '强相关', value: correlationData.filter(d => Math.abs(d.correlation) >= 0.7).length },
                    { name: '中等相关', value: correlationData.filter(d => Math.abs(d.correlation) >= 0.5 && Math.abs(d.correlation) < 0.7).length },
                    { name: '弱相关', value: correlationData.filter(d => Math.abs(d.correlation) >= 0.3 && Math.abs(d.correlation) < 0.5).length },
                    { name: '无相关', value: correlationData.filter(d => Math.abs(d.correlation) < 0.3).length }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {[
                    { name: '强相关', color: '#3f8600' },
                    { name: '中等相关', color: '#d48806' },
                    { name: '弱相关', color: '#1890ff' },
                    { name: '无相关', color: '#8c8c8c' }
                  ].map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>
    </Card>
  );

  const renderRiskAnalysis = () => (
    <Card title="风险分析" extra={
      <Space>
        <Button icon={<SettingOutlined />} onClick={() => setSettingsVisible(true)}>
          设置
        </Button>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskAnalysis}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis />
              <RechartsTooltip />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </Col>
        <Col span={12}>
          <Table
            columns={[
              {
                title: '风险指标',
                dataIndex: 'metric',
                key: 'metric',
                render: (text) => <Text strong>{text}</Text>
              },
              {
                title: '当前值',
                dataIndex: 'value',
                key: 'value',
                render: (value, record) => (
                  <Space>
                    <Text>{value}</Text>
                    {record.trend === 'up' && <TrendingUp style={{ color: '#3f8600' }} />}
                    {record.trend === 'down' && <TrendingDown style={{ color: '#cf1322' }} />}
                    {record.trend === 'stable' && <Text type="secondary">→</Text>}
                  </Space>
                )
              },
              {
                title: '阈值',
                dataIndex: 'threshold',
                key: 'threshold',
                render: (value) => <Text type="secondary">{value}</Text>
              },
              {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                render: (status) => {
                  const colors = {
                    normal: 'green',
                    warning: 'orange',
                    danger: 'red'
                  };
                  return <Tag color={colors[status]}>{status}</Tag>;
                }
              }
            ]}
            dataSource={riskAnalysis}
            pagination={false}
            size="small"
          />
        </Col>
      </Row>
    </Card>
  );

  const renderStrategyComparison = () => (
    <Card title="策略对比分析" extra={
      <Space>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Row gutter={[16, 16]}>
        <Col span={16}>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis dataKey="risk" name="风险" unit="%" />
              <YAxis dataKey="return" name="收益" unit="%" />
              <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="策略" data={strategyPerformance} fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </Col>
        <Col span={8}>
          <Card size="small" title="策略排名">
            <Table
              columns={[
                {
                  title: '策略',
                  dataIndex: 'strategy',
                  key: 'strategy',
                  render: (text) => <Text strong>{text}</Text>
                },
                {
                  title: '夏普比率',
                  dataIndex: 'sharpe',
                  key: 'sharpe',
                  render: (value) => (
                    <Statistic
                      value={value}
                      precision={2}
                      valueStyle={{ color: value >= 1.5 ? '#3f8600' : '#d48806' }}
                    />
                  )
                }
              ]}
              dataSource={strategyPerformance
                .sort((a, b) => b.sharpe - a.sharpe)
                .map((item, index) => ({ ...item, key: index }))}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );

  const renderMarketSentiment = () => (
    <Card title="市场情绪分析" extra={
      <Space>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={marketSentimentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Line type="monotone" dataKey="fearGreedIndex" stroke="#8884d8" name="恐惧贪婪指数" />
              <Line type="monotone" dataKey="volatilityIndex" stroke="#82ca9d" name="波动率指数" />
              <Line type="monotone" dataKey="marketMomentum" stroke="#ffc658" name="市场动量" />
            </LineChart>
          </ResponsiveContainer>
        </Col>
        <Col span={12}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card size="small">
                <Statistic
                  title="当前恐惧贪婪指数"
                  value={68}
                  suffix="/100"
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<TrendingUp />}
                />
                <Progress percent={68} strokeColor="#3f8600" />
                <Text type="secondary">市场情绪：贪婪</Text>
              </Card>
            </Col>
            <Col span={24}>
              <Card size="small">
                <Statistic
                  title="波动率指数"
                  value={20}
                  suffix="%"
                  valueStyle={{ color: '#d48806' }}
                  prefix={<AlertOutlined />}
                />
                <Text type="secondary">市场波动：中等</Text>
              </Card>
            </Col>
            <Col span={24}>
              <Card size="small">
                <Statistic
                  title="市场动量"
                  value={78}
                  suffix="/100"
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<TrendingUp />}
                />
                <Text type="secondary">市场趋势：上涨</Text>
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>
    </Card>
  );

  const renderAssetAllocation = () => (
    <Card title="资产配置分析" extra={
      <Space>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={assetAllocation}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {assetAllocation.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        </Col>
        <Col span={12}>
          <Table
            columns={[
              {
                title: '资产',
                dataIndex: 'name',
                key: 'name',
                render: (text, record) => (
                  <Space>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        backgroundColor: record.color,
                        borderRadius: '50%'
                      }}
                    />
                    <Text strong>{text}</Text>
                  </Space>
                )
              },
              {
                title: '占比',
                dataIndex: 'value',
                key: 'value',
                render: (value) => <Text>{value}%</Text>
              },
              {
                title: '价值',
                key: 'value',
                render: (_, record) => {
                  const total = 1000000; // 假设总价值
                  const assetValue = (total * record.value) / 100;
                  return <Text>${assetValue.toLocaleString()}</Text>;
                }
              }
            ]}
            dataSource={assetAllocation}
            pagination={false}
            size="small"
          />
        </Col>
      </Row>
    </Card>
  );

  const renderPerformanceMetrics = () => (
    <Card title="性能指标汇总" extra={
      <Space>
        <Button icon={<DownloadOutlined />} onClick={exportData}>
          导出
        </Button>
      </Space>
    }>
      <Table
        columns={columns}
        dataSource={performanceMetrics}
        pagination={{ pageSize: 10 }}
        scroll={{ x: 1200 }}
      />
    </Card>
  );

  const tabItems = [
    {
      key: 'performance',
      label: '策略表现',
      children: renderPerformanceChart()
    },
    {
      key: 'metrics',
      label: '性能指标',
      children: renderPerformanceMetrics()
    },
    {
      key: 'correlation',
      label: '相关性分析',
      children: renderCorrelationMatrix()
    },
    {
      key: 'risk',
      label: '风险分析',
      children: renderRiskAnalysis()
    },
    {
      key: 'strategy',
      label: '策略对比',
      children: renderStrategyComparison()
    },
    {
      key: 'sentiment',
      label: '市场情绪',
      children: renderMarketSentiment()
    },
    {
      key: 'allocation',
      label: '资产配置',
      children: renderAssetAllocation()
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Spin spinning={loading}>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2}>数据分析与图表</Title>
          <Text type="secondary">
            深度分析交易数据，洞察市场趋势，优化投资策略
          </Text>
        </div>

        <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总收益率"
                value={15.8}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
                prefix={<TrendingUp />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="夏普比率"
                value={1.85}
                precision={2}
                valueStyle={{ color: '#3f8600' }}
                prefix={<PercentageOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="最大回撤"
                value={-8.5}
                suffix="%"
                valueStyle={{ color: '#cf1322' }}
                prefix={<AlertOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="胜率"
                value={65.4}
                suffix="%"
                valueStyle={{ color: '#3f8600' }}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
        </Row>

        <Card>
          <Tabs
            activeKey={selectedAnalysisType}
            onChange={setSelectedAnalysisType}
            items={tabItems}
          />
        </Card>

        <Modal
          title="图表设置"
          open={settingsVisible}
          onCancel={() => setSettingsVisible(false)}
          footer={null}
          width={600}
        >
          <Form layout="vertical">
            <Form.Item label="显示选项">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Switch
                  checked={chartSettings.showVolume}
                  onChange={(checked) => 
                    setChartSettings(prev => ({ ...prev, showVolume: checked }))
                  }
                />
                <Text>显示成交量</Text>
                
                <Switch
                  checked={chartSettings.showMovingAverages}
                  onChange={(checked) => 
                    setChartSettings(prev => ({ ...prev, showMovingAverages: checked }))
                  }
                />
                <Text>显示移动平均线</Text>
                
                <Switch
                  checked={chartSettings.showBollingerBands}
                  onChange={(checked) => 
                    setChartSettings(prev => ({ ...prev, showBollingerBands: checked }))
                  }
                />
                <Text>显示布林带</Text>
                
                <Switch
                  checked={chartSettings.showRSI}
                  onChange={(checked) => 
                    setChartSettings(prev => ({ ...prev, showRSI: checked }))
                  }
                />
                <Text>显示RSI指标</Text>
                
                <Switch
                  checked={chartSettings.showMACD}
                  onChange={(checked) => 
                    setChartSettings(prev => ({ ...prev, showMACD: checked }))
                  }
                />
                <Text>显示MACD指标</Text>
              </Space>
            </Form.Item>
            
            <Form.Item label="移动平均线周期">
              <Slider
                min={5}
                max={50}
                value={chartSettings.maPeriod}
                onChange={(value) => 
                  setChartSettings(prev => ({ ...prev, maPeriod: value as number }))
                }
              />
              <Text>{chartSettings.maPeriod}天</Text>
            </Form.Item>
            
            <Form.Item label="布林带设置">
              <Space>
                <Text>周期:</Text>
                <Slider
                  min={10}
                  max={50}
                  value={chartSettings.bollingerPeriod}
                  onChange={(value) => 
                    setChartSettings(prev => ({ ...prev, bollingerPeriod: value as number }))
                  }
                  style={{ width: 200 }}
                />
                <Text>{chartSettings.bollingerPeriod}天</Text>
                
                <Text>标准差:</Text>
                <Slider
                  min={1}
                  max={3}
                  step={0.5}
                  value={chartSettings.bollingerStdDev}
                  onChange={(value) => 
                    setChartSettings(prev => ({ ...prev, bollingerStdDev: value as number }))
                  }
                  style={{ width: 200 }}
                />
                <Text>{chartSettings.bollingerStdDev}</Text>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </Spin>
    </div>
  );
};

export default DataAnalysis;