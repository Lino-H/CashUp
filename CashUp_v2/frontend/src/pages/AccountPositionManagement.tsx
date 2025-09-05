/**
 * 账户和仓位管理页面
 * Account and Position Management Page
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
  Tabs,
  Alert,
  Divider,
  Tooltip,
  Typography,
  Spin,
  message,
  Modal,
  Drawer,
  Form,
  Input,
  InputNumber,
  DatePicker,
  Switch,
  Radio,
  Slider,
  Badge,
  Avatar,
  List,
  Descriptions,
  Timeline,
  Progress,
  Rate
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
  Scatter,
  ComposedChart,
  CandlestickChart,
  Candlestick,
  FunnelChart,
  Funnel,
  Treemap
} from 'recharts';
import {
  DollarCircle,
  TrendingUp,
  TrendingDown,
  Percentage,
  AccountBookOutlined,
  PieChartOutlined,
  BarChartOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ExportOutlined,
  ImportOutlined,
  SyncOutlined,
  WarningOutlined,
  SafetyOutlined,
  BankOutlined,
  CreditCardOutlined,
  WalletOutlined,
  LineChartOutlined,
  DashboardOutlined,
  SettingOutlined,
  BellOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  ShieldOutlined,
  GlobalOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import moment from 'moment';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Meta } = Card;

// 账户信息类型
interface AccountInfo {
  id: string;
  name: string;
  type: 'exchange' | 'bank' | 'wallet';
  exchange?: string;
  totalBalance: number;
  availableBalance: number;
  usedBalance: number;
  currency: string;
  btcValue: number;
  change24h: number;
  changePercent24h: number;
  status: 'active' | 'inactive' | 'frozen' | 'maintenance';
  lastUpdated: string;
  riskLevel: 'low' | 'medium' | 'high';
  leverage: number;
  marginRatio: number;
  maintenanceMargin: number;
  unrealizedPnl: number;
  realizedPnl: number;
  totalDeposit: number;
  totalWithdraw: number;
  fees24h: number;
  tradingVolume24h: number;
  assets: Array<{
    currency: string;
    balance: number;
    available: number;
    locked: number;
    btcValue: number;
    usdValue: number;
    change24h: number;
    changePercent24h: number;
  }>;
}

// 仓位信息类型
interface PositionInfo {
  id: string;
  strategyName: string;
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  markPrice: number;
  pnl: number;
  pnlPercent: number;
  unrealizedPnl: number;
  realizedPnl: number;
  margin: number;
  leverage: number;
  liquidationPrice: number;
  bankruptcyPrice: number;
  takeProfit?: number;
  stopLoss?: number;
  openTime: string;
  duration: string;
  exchange: string;
  status: 'open' | 'closed' | 'liquidated' | 'adl';
  riskLevel: 'low' | 'medium' | 'high';
  fundingRate?: number;
  nextFundingTime?: string;
}

// 资金流水类型
interface TransactionRecord {
  id: string;
  type: 'deposit' | 'withdraw' | 'transfer' | 'fee' | 'pnl' | 'funding';
  amount: number;
  currency: string;
  fromAccount?: string;
  toAccount?: string;
  timestamp: string;
  status: 'completed' | 'pending' | 'failed';
  description: string;
  txHash?: string;
  fee?: number;
}

// 风险限额类型
interface RiskLimit {
  id: string;
  type: 'position_size' | 'leverage' | 'margin' | 'drawdown' | 'exposure';
  symbol?: string;
  currentValue: number;
  limitValue: number;
  usagePercent: number;
  status: 'normal' | 'warning' | 'critical';
  lastUpdated: string;
}

// 账户和仓位管理组件
const AccountPositionManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<string>('all');
  const [selectedExchange, setSelectedExchange] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<string>('24h');
  
  // 数据状态
  const [accounts, setAccounts] = useState<AccountInfo[]>([]);
  const [positions, setPositions] = useState<PositionInfo[]>([]);
  const [transactions, setTransactions] = useState<TransactionRecord[]>([]);
  const [riskLimits, setRiskLimits] = useState<RiskLimit[]>([]);
  
  // 图表数据
  const [balanceHistory, setBalanceHistory] = useState<any[]>([]);
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const [assetDistribution, setAssetDistribution] = useState<any[]>([]);
  
  // 详情显示
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedAccountDetail, setSelectedAccountDetail] = useState<AccountInfo | null>(null);
  const [positionDetailVisible, setPositionDetailVisible] = useState(false);
  const [selectedPositionDetail, setSelectedPositionDetail] = useState<PositionInfo | null>(null);
  const [settingsVisible, setSettingsVisible] = useState(false);
  
  // 模拟数据加载
  useEffect(() => {
    loadMockData();
  }, []);

  const loadMockData = () => {
    // 模拟账户数据
    const mockAccounts: AccountInfo[] = [
      {
        id: '1',
        name: 'Binance 主账户',
        type: 'exchange',
        exchange: 'Binance',
        totalBalance: 15420.50,
        availableBalance: 12420.50,
        usedBalance: 3000.00,
        currency: 'USDT',
        btcValue: 0.356,
        change24h: 254.30,
        changePercent24h: 1.68,
        status: 'active',
        lastUpdated: new Date().toISOString(),
        riskLevel: 'medium',
        leverage: 3,
        marginRatio: 0.25,
        maintenanceMargin: 750.00,
        unrealizedPnl: 145.50,
        realizedPnl: 2540.30,
        totalDeposit: 50000,
        totalWithdraw: 34579.50,
        fees24h: 12.50,
        tradingVolume24h: 125000,
        assets: [
          { currency: 'USDT', balance: 12420.50, available: 12420.50, locked: 0, btcValue: 0.287, usdValue: 12420.50, change24h: 0, changePercent24h: 0 },
          { currency: 'BTC', balance: 0.069, available: 0.069, locked: 0, btcValue: 0.069, usdValue: 2980.50, change24h: 1250.50, changePercent24h: 2.98 },
          { currency: 'ETH', balance: 1.2, available: 1.2, locked: 0, btcValue: 0.058, usdValue: 2700.00, change24h: -85.70, changePercent24h: -3.67 }
        ]
      },
      {
        id: '2',
        name: 'Gate.io 交易账户',
        type: 'exchange',
        exchange: 'Gate.io',
        totalBalance: 8750.30,
        availableBalance: 6250.30,
        usedBalance: 2500.00,
        currency: 'USDT',
        btcValue: 0.202,
        change24h: -125.60,
        changePercent24h: -1.42,
        status: 'active',
        lastUpdated: new Date().toISOString(),
        riskLevel: 'low',
        leverage: 2,
        marginRatio: 0.2,
        maintenanceMargin: 500.00,
        unrealizedPnl: 42.35,
        realizedPnl: 1285.30,
        totalDeposit: 20000,
        totalWithdraw: 11235.00,
        fees24h: 8.30,
        tradingVolume24h: 85000,
        assets: [
          { currency: 'USDT', balance: 6250.30, available: 6250.30, locked: 0, btcValue: 0.144, usdValue: 6250.30, change24h: 0, changePercent24h: 0 },
          { currency: 'ETH', balance: 2.5, available: 2.5, locked: 0, btcValue: 0.121, usdValue: 5625.00, change24h: -213.50, changePercent24h: -3.67 }
        ]
      }
    ];

    // 模拟仓位数据
    const mockPositions: PositionInfo[] = [
      {
        id: '1',
        strategyName: 'MA Cross Strategy',
        symbol: 'BTCUSDT',
        side: 'long',
        quantity: 0.1,
        entryPrice: 41800.00,
        currentPrice: 43250.50,
        markPrice: 43248.30,
        pnl: 145.05,
        pnlPercent: 3.47,
        unrealizedPnl: 145.05,
        realizedPnl: 0,
        margin: 4180.00,
        leverage: 1,
        liquidationPrice: 0,
        bankruptcyPrice: 0,
        takeProfit: 45000,
        stopLoss: 40000,
        openTime: '2024-01-18T09:30:00Z',
        duration: '2d 3h',
        exchange: 'Binance',
        status: 'open',
        riskLevel: 'low',
        fundingRate: 0.0001,
        nextFundingTime: '2024-01-20T16:00:00Z'
      },
      {
        id: '2',
        strategyName: 'RSI Mean Reversion',
        symbol: 'ETHUSDT',
        side: 'short',
        quantity: 0.5,
        entryPrice: 2335.00,
        currentPrice: 2250.30,
        markPrice: 2251.20,
        pnl: 42.35,
        pnlPercent: 3.63,
        unrealizedPnl: 42.35,
        realizedPnl: 0,
        margin: 1167.50,
        leverage: 1,
        liquidationPrice: 0,
        bankruptcyPrice: 0,
        takeProfit: 2200,
        stopLoss: 2400,
        openTime: '2024-01-19T14:15:00Z',
        duration: '1d 2h',
        exchange: 'Gate.io',
        status: 'open',
        riskLevel: 'medium',
        fundingRate: 0.0002,
        nextFundingTime: '2024-01-20T16:00:00Z'
      }
    ];

    // 模拟交易记录
    const mockTransactions: TransactionRecord[] = [
      {
        id: '1',
        type: 'deposit',
        amount: 10000,
        currency: 'USDT',
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        status: 'completed',
        description: '银行转账充值',
        txHash: '0x1234567890abcdef'
      },
      {
        id: '2',
        type: 'withdraw',
        amount: 5000,
        currency: 'USDT',
        timestamp: new Date(Date.now() - 172800000).toISOString(),
        status: 'completed',
        description: '提现到银行账户',
        txHash: '0xabcdef1234567890'
      },
      {
        id: '3',
        type: 'pnl',
        amount: 254.30,
        currency: 'USDT',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        status: 'completed',
        description: 'BTCUSDT 平仓盈利'
      }
    ];

    // 模拟风险限额
    const mockRiskLimits: RiskLimit[] = [
      {
        id: '1',
        type: 'position_size',
        symbol: 'BTCUSDT',
        currentValue: 0.1,
        limitValue: 1.0,
        usagePercent: 10,
        status: 'normal',
        lastUpdated: new Date().toISOString()
      },
      {
        id: '2',
        type: 'leverage',
        currentValue: 3,
        limitValue: 5,
        usagePercent: 60,
        status: 'warning',
        lastUpdated: new Date().toISOString()
      },
      {
        id: '3',
        type: 'margin',
        currentValue: 0.25,
        limitValue: 0.5,
        usagePercent: 50,
        status: 'normal',
        lastUpdated: new Date().toISOString()
      }
    ];

    // 模拟图表数据
    const mockBalanceHistory = Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split('T')[0],
      totalBalance: 24000 + Math.sin(i * 0.1) * 2000 + i * 50 + Math.random() * 1000,
      realizedPnl: Math.random() * 1000 - 500,
      unrealizedPnl: Math.random() * 500 - 250
    }));

    const mockPnlHistory = Array.from({ length: 24 }, (_, i) => ({
      time: `${i}:00`,
      pnl: Math.random() * 1000 - 500,
      cumulative: Math.random() * 5000 + 2000
    }));

    const mockAssetDistribution = [
      { name: 'BTC', value: 35.6, color: '#F7931A' },
      { name: 'ETH', value: 28.3, color: '#627EEA' },
      { name: 'USDT', value: 25.1, color: '#26A17B' },
      { name: '其他', value: 11.0, color: '#76838F' }
    ];

    setAccounts(mockAccounts);
    setPositions(mockPositions);
    setTransactions(mockTransactions);
    setRiskLimits(mockRiskLimits);
    setBalanceHistory(mockBalanceHistory);
    setPnlHistory(mockPnlHistory);
    setAssetDistribution(mockAssetDistribution);
  };

  const handleViewAccountDetail = (account: AccountInfo) => {
    setSelectedAccountDetail(account);
    setDetailVisible(true);
  };

  const handleViewPositionDetail = (position: PositionInfo) => {
    setSelectedPositionDetail(position);
    setPositionDetailVisible(true);
  };

  const handleClosePosition = (positionId: string) => {
    message.success('平仓指令已发送');
    loadMockData();
  };

  const accountColumns = [
    {
      title: '账户名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: AccountInfo) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {record.exchange} | {record.type === 'exchange' ? '交易所' : record.type === 'bank' ? '银行' : '钱包'}
          </div>
        </div>
      )
    },
    {
      title: '总余额',
      dataIndex: 'totalBalance',
      key: 'totalBalance',
      render: (value: number, record: AccountInfo) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>${value.toFixed(2)}</div>
          <div style={{ fontSize: 12, color: record.change24h >= 0 ? '#3f8600' : '#cf1322' }}>
            {record.change24h >= 0 ? '+' : ''}${record.change24h.toFixed(2)} ({record.changePercent24h >= 0 ? '+' : ''}{record.changePercent24h.toFixed(2)}%)
          </div>
        </div>
      ),
      sorter: (a: AccountInfo, b: AccountInfo) => a.totalBalance - b.totalBalance
    },
    {
      title: '可用余额',
      dataIndex: 'availableBalance',
      key: 'availableBalance',
      render: (value: number) => `$${value.toFixed(2)}`,
      sorter: (a: AccountInfo, b: AccountInfo) => a.availableBalance - b.availableBalance
    },
    {
      title: '使用余额',
      dataIndex: 'usedBalance',
      key: 'usedBalance',
      render: (value: number, record: AccountInfo) => (
        <div>
          <div>${value.toFixed(2)}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {((value / record.totalBalance) * 100).toFixed(1)}%
          </div>
        </div>
      )
    },
    {
      title: 'BTC价值',
      dataIndex: 'btcValue',
      key: 'btcValue',
      render: (value: number) => `${value.toFixed(6)} BTC`
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          active: { color: 'green', text: '正常' },
          inactive: { color: 'gray', text: '未激活' },
          frozen: { color: 'red', text: '冻结' },
          maintenance: { color: 'orange', text: '维护中' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '风险等级',
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      render: (level: string) => {
        const levelConfig = {
          low: { color: 'green', text: '低' },
          medium: { color: 'orange', text: '中' },
          high: { color: 'red', text: '高' }
        };
        const config = levelConfig[level as keyof typeof levelConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: AccountInfo) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewAccountDetail(record)}
          >
            详情
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
          >
            编辑
          </Button>
        </Space>
      )
    }
  ];

  const positionColumns = [
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
      title: '保证金',
      dataIndex: 'margin',
      key: 'margin',
      render: (margin: number) => `$${margin.toFixed(2)}`
    },
    {
      title: '杠杆',
      dataIndex: 'leverage',
      key: 'leverage',
      render: (leverage: number) => `${leverage}x`
    },
    {
      title: '强平价格',
      dataIndex: 'liquidationPrice',
      key: 'liquidationPrice',
      render: (price: number) => price ? `$${price.toFixed(2)}` : '-'
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
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          open: { color: 'green', text: '持仓中' },
          closed: { color: 'gray', text: '已平仓' },
          liquidated: { color: 'red', text: '已强平' },
          adl: { color: 'orange', text: 'ADL' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: PositionInfo) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewPositionDetail(record)}
          >
            详情
          </Button>
          {record.status === 'open' && (
            <Button
              type="link"
              danger
              onClick={() => handleClosePosition(record.id)}
            >
              平仓
            </Button>
          )}
        </Space>
      )
    }
  ];

  const totalBalance = accounts.reduce((sum, account) => sum + account.totalBalance, 0);
  const totalPnl = accounts.reduce((sum, account) => sum + account.unrealizedPnl + account.realizedPnl, 0);
  const totalMargin = accounts.reduce((sum, account) => sum + account.usedBalance, 0);

  return (
    <div style={{ padding: 24 }}>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>账户和仓位管理</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Button icon={<SyncOutlined />} onClick={loadMockData}>
              刷新
            </Button>
            <Button icon={<ExportOutlined />}>
              导出
            </Button>
            <Button icon={<PlusOutlined />} type="primary">
              添加账户
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 账户概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总余额"
              value={totalBalance}
              prefix="$"
              precision={2}
              valueStyle={{ color: '#3f8600' }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              24h变化: +${accounts.reduce((sum, account) => sum + account.change24h, 0).toFixed(2)}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总盈亏"
              value={totalPnl}
              prefix="$"
              precision={2}
              valueStyle={{ color: totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              实现盈亏: ${accounts.reduce((sum, account) => sum + account.realizedPnl, 0).toFixed(2)}
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总保证金"
              value={totalMargin}
              prefix="$"
              precision={2}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              使用率: {((totalMargin / totalBalance) * 100).toFixed(1)}%
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃仓位"
              value={positions.filter(p => p.status === 'open').length}
              suffix={`/ ${positions.length}`}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              总盈亏: ${positions.reduce((sum, position) => sum + position.pnl, 0).toFixed(2)}
            </div>
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="accounts">
        <TabPane tab="账户管理" key="accounts">
          <Card>
            <Table
              columns={accountColumns}
              dataSource={accounts}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="仓位管理" key="positions">
          <Card>
            <Table
              columns={positionColumns}
              dataSource={positions}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true
              }}
              scroll={{ x: 1600 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="资金流水" key="transactions">
          <Card>
            <Table
              columns={[
                {
                  title: '时间',
                  dataIndex: 'timestamp',
                  key: 'timestamp',
                  render: (timestamp: string) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
                },
                {
                  title: '类型',
                  dataIndex: 'type',
                  key: 'type',
                  render: (type: string) => {
                    const typeConfig = {
                      deposit: { color: 'green', text: '充值' },
                      withdraw: { color: 'red', text: '提现' },
                      transfer: { color: 'blue', text: '转账' },
                      fee: { color: 'orange', text: '手续费' },
                      pnl: { color: 'purple', text: '盈亏' },
                      funding: { color: 'cyan', text: '资金费用' }
                    };
                    const config = typeConfig[type as keyof typeof typeConfig];
                    return <Tag color={config.color}>{config.text}</Tag>;
                  }
                },
                {
                  title: '金额',
                  dataIndex: 'amount',
                  key: 'amount',
                  render: (amount: number, record: TransactionRecord) => (
                    <span style={{ 
                      color: record.type === 'deposit' || record.type === 'pnl' ? '#3f8600' : '#cf1322',
                      fontWeight: 'bold'
                    }}>
                      {record.type === 'deposit' || record.type === 'pnl' ? '+' : '-'}${amount.toFixed(2)}
                    </span>
                  )
                },
                {
                  title: '币种',
                  dataIndex: 'currency',
                  key: 'currency'
                },
                {
                  title: '描述',
                  dataIndex: 'description',
                  key: 'description'
                },
                {
                  title: '状态',
                  dataIndex: 'status',
                  key: 'status',
                  render: (status: string) => {
                    const statusConfig = {
                      completed: { color: 'green', text: '已完成' },
                      pending: { color: 'orange', text: '处理中' },
                      failed: { color: 'red', text: '失败' }
                    };
                    const config = statusConfig[status as keyof typeof statusConfig];
                    return <Tag color={config.color}>{config.text}</Tag>;
                  }
                },
                {
                  title: '交易哈希',
                  dataIndex: 'txHash',
                  key: 'txHash',
                  render: (hash: string) => hash ? (
                    <a href={`https://etherscan.io/tx/${hash}`} target="_blank" rel="noopener noreferrer">
                      {hash.substring(0, 10)}...
                    </a>
                  ) : '-'
                }
              ]}
              dataSource={transactions}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="风险控制" key="risk">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="风险限额">
                {riskLimits.map(limit => (
                  <div key={limit.id} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>{limit.type === 'position_size' ? '持仓大小' : 
                              limit.type === 'leverage' ? '杠杆倍数' : 
                              limit.type === 'margin' ? '保证金率' : 
                              limit.type === 'drawdown' ? '最大回撤' : '总敞口'}</span>
                      <Tag color={limit.status === 'normal' ? 'green' : limit.status === 'warning' ? 'orange' : 'red'}>
                        {limit.status === 'normal' ? '正常' : limit.status === 'warning' ? '警告' : '危险'}
                      </Tag>
                    </div>
                    <Progress 
                      percent={limit.usagePercent} 
                      status={limit.status === 'normal' ? 'normal' : limit.status === 'warning' ? 'exception' : 'exception'}
                      showInfo
                    />
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                      <span style={{ fontSize: 12, color: '#666' }}>
                        当前: {limit.currentValue} / 限额: {limit.limitValue}
                      </span>
                      <span style={{ fontSize: 12, color: '#666' }}>
                        {limit.usagePercent.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </Card>
            </Col>
            <Col span={12}>
              <Card title="资产分布">
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={assetDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {assetDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="数据分析" key="analytics">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="余额历史">
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={balanceHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Area type="monotone" dataKey="totalBalance" stackId="1" stroke="#8884d8" fill="#8884d8" name="总余额" />
                      <Area type="monotone" dataKey="realizedPnl" stackId="2" stroke="#82ca9d" fill="#82ca9d" name="已实现盈亏" />
                      <Area type="monotone" dataKey="unrealizedPnl" stackId="3" stroke="#ffc658" fill="#ffc658" name="未实现盈亏" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="盈亏趋势">
                <div style={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={pnlHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="pnl" fill="#8884d8" name="小时盈亏" />
                      <Line type="monotone" dataKey="cumulative" stroke="#82ca9d" name="累计盈亏" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 账户详情抽屉 */}
      <Drawer
        title="账户详情"
        placement="right"
        width={800}
        onClose={() => setDetailVisible(false)}
        open={detailVisible}
      >
        {selectedAccountDetail && (
          <div>
            <Card title="基本信息" style={{ marginBottom: 16 }}>
              <Descriptions column={2}>
                <Descriptions.Item label="账户名称">{selectedAccountDetail.name}</Descriptions.Item>
                <Descriptions.Item label="账户类型">{selectedAccountDetail.type === 'exchange' ? '交易所' : selectedAccountDetail.type === 'bank' ? '银行' : '钱包'}</Descriptions.Item>
                <Descriptions.Item label="交易所">{selectedAccountDetail.exchange}</Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={selectedAccountDetail.status === 'active' ? 'green' : 'red'}>
                    {selectedAccountDetail.status === 'active' ? '正常' : '异常'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="风险等级">
                  <Tag color={selectedAccountDetail.riskLevel === 'low' ? 'green' : selectedAccountDetail.riskLevel === 'medium' ? 'orange' : 'red'}>
                    {selectedAccountDetail.riskLevel === 'low' ? '低' : selectedAccountDetail.riskLevel === 'medium' ? '中' : '高'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="最后更新">{moment(selectedAccountDetail.lastUpdated).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="余额信息" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="总余额" value={selectedAccountDetail.totalBalance} prefix="$" precision={2} />
                </Col>
                <Col span={8}>
                  <Statistic title="可用余额" value={selectedAccountDetail.availableBalance} prefix="$" precision={2} />
                </Col>
                <Col span={8}>
                  <Statistic title="使用余额" value={selectedAccountDetail.usedBalance} prefix="$" precision={2} />
                </Col>
                <Col span={8}>
                  <Statistic title="BTC价值" value={selectedAccountDetail.btcValue} precision={6} suffix="BTC" />
                </Col>
                <Col span={8}>
                  <Statistic title="24h变化" value={selectedAccountDetail.change24h} prefix="$" precision={2} 
                    valueStyle={{ color: selectedAccountDetail.change24h >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
                <Col span={8}>
                  <Statistic title="24h变化%" value={selectedAccountDetail.changePercent24h} suffix="%" precision={2}
                    valueStyle={{ color: selectedAccountDetail.changePercent24h >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
              </Row>
            </Card>

            <Card title="交易信息" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="杠杆倍数" value={selectedAccountDetail.leverage} suffix="x" />
                </Col>
                <Col span={8}>
                  <Statistic title="保证金率" value={selectedAccountDetail.marginRatio} precision={2} suffix="%" />
                </Col>
                <Col span={8}>
                  <Statistic title="维持保证金" value={selectedAccountDetail.maintenanceMargin} prefix="$" precision={2} />
                </Col>
                <Col span={8}>
                  <Statistic title="未实现盈亏" value={selectedAccountDetail.unrealizedPnl} prefix="$" precision={2"
                    valueStyle={{ color: selectedAccountDetail.unrealizedPnl >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
                <Col span={8}>
                  <Statistic title="已实现盈亏" value={selectedAccountDetail.realizedPnl} prefix="$" precision={2"
                    valueStyle={{ color: selectedAccountDetail.realizedPnl >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
                <Col span={8}>
                  <Statistic title="总充值" value={selectedAccountDetail.totalDeposit} prefix="$" precision={2} />
                </Col>
              </Row>
            </Card>

            <Card title="资产分布">
              <Table
                columns={[
                  { title: '币种', dataIndex: 'currency', key: 'currency' },
                  { 
                    title: '余额', 
                    dataIndex: 'balance', 
                    key: 'balance',
                    render: (value: number, record: any) => `${value.toFixed(4)} ${record.currency}`
                  },
                  { 
                    title: '可用', 
                    dataIndex: 'available', 
                    key: 'available',
                    render: (value: number, record: any) => `${value.toFixed(4)} ${record.currency}`
                  },
                  { 
                    title: '冻结', 
                    dataIndex: 'locked', 
                    key: 'locked',
                    render: (value: number, record: any) => `${value.toFixed(4)} ${record.currency}`
                  },
                  { 
                    title: 'BTC价值', 
                    dataIndex: 'btcValue', 
                    key: 'btcValue',
                    render: (value: number) => `${value.toFixed(6)} BTC`
                  },
                  { 
                    title: 'USD价值', 
                    dataIndex: 'usdValue', 
                    key: 'usdValue',
                    render: (value: number) => `$${value.toFixed(2)}`
                  },
                  { 
                    title: '24h变化', 
                    dataIndex: 'changePercent24h', 
                    key: 'changePercent24h',
                    render: (value: number) => (
                      <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322' }}>
                        {value >= 0 ? '+' : ''}{value.toFixed(2)}%
                      </span>
                    )
                  }
                ]}
                dataSource={selectedAccountDetail.assets}
                rowKey="currency"
                pagination={false}
              />
            </Card>
          </div>
        )}
      </Drawer>

      {/* 仓位详情抽屉 */}
      <Drawer
        title="仓位详情"
        placement="right"
        width={600}
        onClose={() => setPositionDetailVisible(false)}
        open={positionDetailVisible}
      >
        {selectedPositionDetail && (
          <div>
            <Card title="基本信息" style={{ marginBottom: 16 }}>
              <Descriptions column={2}>
                <Descriptions.Item label="策略名称">{selectedPositionDetail.strategyName}</Descriptions.Item>
                <Descriptions.Item label="交易对">{selectedPositionDetail.symbol}</Descriptions.Item>
                <Descriptions.Item label="方向">
                  <Tag color={selectedPositionDetail.side === 'long' ? 'green' : 'red'}>
                    {selectedPositionDetail.side === 'long' ? '多头' : '空头'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={selectedPositionDetail.status === 'open' ? 'green' : 'red'}>
                    {selectedPositionDetail.status === 'open' ? '持仓中' : '已平仓'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="开仓时间">{moment(selectedPositionDetail.openTime).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
                <Descriptions.Item label="持仓时间">{selectedPositionDetail.duration}</Descriptions.Item>
                <Descriptions.Item label="交易所">{selectedPositionDetail.exchange}</Descriptions.Item>
                <Descriptions.Item label="风险等级">
                  <Tag color={selectedPositionDetail.riskLevel === 'low' ? 'green' : selectedPositionDetail.riskLevel === 'medium' ? 'orange' : 'red'}>
                    {selectedPositionDetail.riskLevel === 'low' ? '低' : selectedPositionDetail.riskLevel === 'medium' ? '中' : '高'}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card title="价格信息" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="入场价格" value={selectedPositionDetail.entryPrice} prefix="$" precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="当前价格" value={selectedPositionDetail.currentPrice} prefix="$" precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="标记价格" value={selectedPositionDetail.markPrice} prefix="$" precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="强平价格" value={selectedPositionDetail.liquidationPrice || 0} prefix="$" precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="止盈价格" value={selectedPositionDetail.takeProfit || 0} prefix="$" precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="止损价格" value={selectedPositionDetail.stopLoss || 0} prefix="$" precision={2} />
                </Col>
              </Row>
            </Card>

            <Card title="盈亏信息" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="数量" value={selectedPositionDetail.quantity} precision={4} />
                </Col>
                <Col span={12}>
                  <Statistic title="杠杆" value={selectedPositionDetail.leverage} suffix="x" />
                </Col>
                <Col span={12}>
                  <Statistic title="保证金" value={selectedPositionDetail.margin} prefix="$" precision={2} />
                </Col>
                <Col span={12}>
                  <Statistic title="盈亏" value={selectedPositionDetail.pnl} prefix="$" precision={2}
                    valueStyle={{ color: selectedPositionDetail.pnl >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
                <Col span={12}>
                  <Statistic title="盈亏比例" value={selectedPositionDetail.pnlPercent} suffix="%" precision={2}
                    valueStyle={{ color: selectedPositionDetail.pnlPercent >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
                <Col span={12}>
                  <Statistic title="未实现盈亏" value={selectedPositionDetail.unrealizedPnl} prefix="$" precision={2}
                    valueStyle={{ color: selectedPositionDetail.unrealizedPnl >= 0 ? '#3f8600' : '#cf1322' }} />
                </Col>
              </Row>
            </Card>

            {selectedPositionDetail.fundingRate && (
              <Card title="资金费用">
                <Descriptions column={2}>
                  <Descriptions.Item label="资金费率">{selectedPositionDetail.fundingRate * 100}%</Descriptions.Item>
                  <Descriptions.Item label="下次结算时间">
                    {selectedPositionDetail.nextFundingTime ? moment(selectedPositionDetail.nextFundingTime).format('YYYY-MM-DD HH:mm:ss') : '-'}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default AccountPositionManagement;