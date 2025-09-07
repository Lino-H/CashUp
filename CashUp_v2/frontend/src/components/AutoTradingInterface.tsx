/**
 * 自动交易界面组件
 * Auto Trading Interface Component
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Alert,
  Progress,
  Tag,
  Badge,
  Button,
  Select,
  Radio,
  Switch,
  Input,
  Slider,
  Divider,
  List,
  Table,
  Modal,
  Form,
  Tooltip,
  Avatar,
  Rate,
  Calendar,
  Tabs,
  Spin,
  message,
  InputNumber,
  Checkbox,
  TimePicker,
  DatePicker,
  notification,
  Popconfirm,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  SafetyOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  EyeOutlined,
  EditOutlined,
  PlusOutlined,
  DeleteOutlined,
  SyncOutlined,
  RobotOutlined,
  DollarOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  StockOutlined,
  GlobalOutlined,
  BankOutlined,
  FundOutlined,
  ApiOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  ExclamationTriangleOutlined,
  CrownOutlined,
  HeartOutlined,
  ShareAltOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TeamOutlined,
  FireOutlined,
  RocketLaunchOutlined,
  AntDesignOutlined,
  BanknoteOutlined,
  SafetyCertificateOutlined,
  RocketOutlined as RocketOutlined2,
  DashboardOutlined,
  AlertOutlined,
  BellOutlined,
  TrophyOutlined,
  BulbOutlined as BulbOutlined2,
  EditOutlined as EditOutlined2,
  EyeOutlined as EyeOutlined2,
  PlusOutlined as PlusOutlined2,
  DeleteOutlined as DeleteOutlined2,
  SyncOutlined as SyncOutlined2,
  RobotOutlined as RobotOutlined2,
  DollarOutlined as DollarOutlined2,
  TrendingUpOutlined as TrendingUpOutlined2,
  TrendingDownOutlined as TrendingDownOutlined2,
  StockOutlined as StockOutlined2,
  GlobalOutlined as GlobalOutlined2,
  BankOutlined as BankOutlined2,
  FundOutlined as FundOutlined2,
  ApiOutlined as ApiOutlined2,
  BarChartOutlined as BarChartOutlined2,
  LineChartOutlined as LineChartOutlined2,
  PieChartOutlined as PieChartOutlined2,
  ExclamationTriangleOutlined as ExclamationTriangleOutlined2,
  CrownOutlined as CrownOutlined2,
  HeartOutlined as HeartOutlined2,
  ShareAltOutlined as ShareAltOutlined2,
  ClockCircleOutlined as ClockCircleOutlined2,
  UserOutlined as UserOutlined2,
  TeamOutlined as TeamOutlined2,
  FireOutlined as FireOutlined2,
  RocketLaunchOutlined as RocketLaunchOutlined2,
  AntDesignOutlined as AntDesignOutlined2,
  BanknoteOutlined as BanknoteOutlined2,
  SafetyCertificateOutlined as SafetyCertificateOutlined2,
  RocketOutlined as RocketOutlined3,
  DashboardOutlined as DashboardOutlined2,
  AlertOutlined as AlertOutlined2,
  BellOutlined as BellOutlined2,
  TrophyOutlined as TrophyOutlined2,
  BulbOutlined as BulbOutlined3,
  EditOutlined as EditOutlined3,
  EyeOutlined as EyeOutlined3,
  PlusOutlined as PlusOutlined3,
  DeleteOutlined as DeleteOutlined3,
  SyncOutlined as SyncOutlined3,
  RobotOutlined as RobotOutlined3,
  DollarOutlined as DollarOutlined3,
  TrendingUpOutlined as TrendingUpOutlined3,
  TrendingDownOutlined as TrendingDownOutlined3,
  StockOutlined as StockOutlined3,
  GlobalOutlined as GlobalOutlined3,
  BankOutlined as BankOutlined3,
  FundOutlined as FundOutlined3,
  ApiOutlined as ApiOutlined3,
  BarChartOutlined as BarChartOutlined3,
  LineChartOutlined as LineChartOutlined3,
  PieChartOutlined as PieChartOutlined3,
  ExclamationTriangleOutlined as ExclamationTriangleOutlined3,
  CrownOutlined as CrownOutlined3,
  HeartOutlined as HeartOutlined3,
  ShareAltOutlined as ShareAltOutlined3,
  ClockCircleOutlined as ClockCircleOutlined3,
  UserOutlined as UserOutlined3,
  TeamOutlined as TeamOutlined3,
  FireOutlined as FireOutlined3,
  RocketLaunchOutlined as RocketLaunchOutlined3,
  AntDesignOutlined as AntDesignOutlined3,
  BanknoteOutlined as BanknoteOutlined3,
  SafetyCertificateOutlined as SafetyCertificateOutlined3,
  RocketOutlined as RocketOutlined4,
  DashboardOutlined as DashboardOutlined3,
  AlertOutlined as AlertOutlined3,
  BellOutlined as BellOutlined3,
  TrophyOutlined as TrophyOutlined3,
  BulbOutlined as BulbOutlined4,
  EditOutlined as EditOutlined4,
  EyeOutlined as EyeOutlined4,
  PlusOutlined as PlusOutlined4,
  DeleteOutlined as DeleteOutlined4,
  SyncOutlined as SyncOutlined4,
  RobotOutlined as RobotOutlined4,
  DollarOutlined as DollarOutlined4,
  TrendingUpOutlined as TrendingUpOutlined4,
  TrendingDownOutlined as TrendingDownOutlined4,
  StockOutlined as StockOutlined4,
  GlobalOutlined as GlobalOutlined4,
  BankOutlined as BankOutlined4,
  FundOutlined as FundOutlined4,
  ApiOutlined as ApiOutlined4,
  BarChartOutlined as BarChartOutlined4,
  LineChartOutlined as LineChartOutlined4,
  PieChartOutlined as PieChartOutlined4,
  ExclamationTriangleOutlined as ExclamationTriangleOutlined4,
  CrownOutlined as CrownOutlined4,
  HeartOutlined as HeartOutlined4,
  ShareAltOutlined as ShareAltOutlined4,
  ClockCircleOutlined as ClockCircleOutlined4,
  UserOutlined as UserOutlined4,
  TeamOutlined as TeamOutlined4,
  FireOutlined as FireOutlined4,
  RocketLaunchOutlined as RocketLaunchOutlined4,
  AntDesignOutlined as AntDesignOutlined4,
  BanknoteOutlined as BanknoteOutlined4,
  SafetyCertificateOutlined as SafetyCertificateOutlined4,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RadioGroup } = Radio;
const { TabPane } = Tabs;
const { TextArea } = Input;

// 交易策略类型定义
export interface TradingStrategy {
  id: string;
  name: string;
  description: string;
  type: 'trend' | 'momentum' | 'mean_reversion' | 'arbitrage' | 'scalping';
  status: 'active' | 'paused' | 'stopped' | 'error';
  symbol: string;
  timeframe: string;
  parameters: {
    stopLoss: number;
    takeProfit: number;
    positionSize: number;
    maxPosition: number;
    riskPerTrade: number;
  };
  performance: {
    totalTrades: number;
    winRate: number;
    profitFactor: number;
    totalPnL: number;
    maxDrawdown: number;
    sharpeRatio: number;
  };
  createdAt: number;
  lastUpdate: number;
  running: boolean;
}

// 自动交易订单类型定义
export interface AutoOrder {
  id: string;
  strategyId: string;
  strategyName: string;
  type: 'buy' | 'sell' | 'stop_loss' | 'take_profit';
  symbol: string;
  price: number;
  quantity: number;
  status: 'pending' | 'executed' | 'cancelled' | 'failed';
  timestamp: number;
  executedAt?: number;
  reason: string;
  pnl?: number;
  fees?: number;
}

// 风险控制类型定义
export interface RiskControl {
  id: string;
  name: string;
  enabled: boolean;
  type: 'stop_loss' | 'position_limit' | 'daily_loss' | 'max_drawdown' | 'concurrent_trades';
  value: number;
  action: 'pause' | 'stop' | 'alert';
  description: string;
}

// 生成模拟交易策略数据
const generateMockTradingStrategies = (): TradingStrategy[] => {
  const strategies: TradingStrategy[] = [];
  const strategyNames = ['趋势跟踪策略', '动量突破策略', '均值回归策略', '套利策略', '高频交易策略'];
  const strategyTypes = ['trend', 'momentum', 'mean_reversion', 'arbitrage', 'scalping'] as const;
  const statuses = ['active', 'paused', 'stopped', 'error'] as const;
  const symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'];
  
  for (let i = 0; i < 5; i++) {
    strategies.push({
      id: `strategy_${i}`,
      name: strategyNames[i],
      description: `这是一个专业的${strategyNames[i]}，采用先进的算法模型进行交易决策。`,
      type: strategyTypes[i],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      symbol: symbols[Math.floor(Math.random() * symbols.length)],
      timeframe: '1h',
      parameters: {
        stopLoss: 0.02 + Math.random() * 0.08,
        takeProfit: 0.03 + Math.random() * 0.12,
        positionSize: 0.1 + Math.random() * 0.9,
        maxPosition: 1 + Math.random() * 4,
        riskPerTrade: 0.01 + Math.random() * 0.04,
      },
      performance: {
        totalTrades: Math.floor(Math.random() * 1000),
        winRate: 0.4 + Math.random() * 0.4,
        profitFactor: 0.8 + Math.random() * 1.4,
        totalPnL: (Math.random() - 0.5) * 10000,
        maxDrawdown: Math.random() * 0.3,
        sharpeRatio: Math.random() * 2,
      },
      createdAt: Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000,
      lastUpdate: Date.now() - Math.random() * 24 * 60 * 60 * 1000,
      running: Math.random() > 0.3,
    });
  }
  
  return strategies;
};

// 生成模拟自动交易订单数据
const generateMockAutoOrders = (): AutoOrder[] => {
  const orders: AutoOrder[] = [];
  const strategies = generateMockTradingStrategies();
  const types = ['buy', 'sell', 'stop_loss', 'take_profit'] as const;
  const statuses = ['pending', 'executed', 'cancelled', 'failed'] as const;
  
  for (let i = 0; i < 20; i++) {
    const strategy = strategies[Math.floor(Math.random() * strategies.length)];
    orders.push({
      id: `order_${i}`,
      strategyId: strategy.id,
      strategyName: strategy.name,
      type: types[Math.floor(Math.random() * types.length)],
      symbol: strategy.symbol,
      price: 1000 + Math.random() * 50000,
      quantity: 0.01 + Math.random() * 2,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      timestamp: Date.now() - Math.random() * 24 * 60 * 60 * 1000,
      executedAt: Math.random() > 0.3 ? Date.now() - Math.random() * 24 * 60 * 60 * 1000 : undefined,
      reason: `自动交易订单 ${i + 1}`,
      pnl: (Math.random() - 0.5) * 1000,
      fees: Math.random() * 10,
    });
  }
  
  return orders.sort((a, b) => b.timestamp - a.timestamp);
};

// 生成模拟风险控制数据
const generateMockRiskControls = (): RiskControl[] => {
  const controls: RiskControl[] = [
    {
      id: 'rc1',
      name: '单笔止损',
      enabled: true,
      type: 'stop_loss',
      value: 0.02,
      action: 'pause',
      description: '单笔交易最大亏损2%',
    },
    {
      id: 'rc2',
      name: '持仓限制',
      enabled: true,
      type: 'position_limit',
      value: 5,
      action: 'stop',
      description: '最大同时持仓5个品种',
    },
    {
      id: 'rc3',
      name: '日亏损限制',
      enabled: true,
      type: 'daily_loss',
      value: 0.05,
      action: 'stop',
      description: '单日最大亏损5%',
    },
    {
      id: 'rc4',
      name: '最大回撤',
      enabled: true,
      type: 'max_drawdown',
      value: 0.1,
      action: 'stop',
      description: '最大回撤10%时停止交易',
    },
    {
      id: 'rc5',
      name: '并发交易',
      enabled: true,
      type: 'concurrent_trades',
      value: 10,
      action: 'pause',
      description: '最大并发交易10笔',
    },
  ];
  
  return controls;
};

// 策略状态颜色
const getStrategyStatusColor = (status: string): string => {
  switch (status) {
    case 'active': return '#52c41a';
    case 'paused': return '#faad14';
    case 'stopped': return '#f5222d';
    case 'error': return '#ff4d4f';
    default: return '#d9d9d9';
  }
};

// 策略运行状态图标
const getStrategyStatusIcon = (running: boolean): React.ReactNode => {
  return running ? <PlayCircleOutlined style={{ color: '#52c41a' }} /> : <PauseCircleOutlined style={{ color: '#faad14' }} />;
};

// 订单状态颜色
const getOrderStatusColor = (status: string): string => {
  switch (status) {
    case 'pending': return '#1890ff';
    case 'executed': return '#52c41a';
    case 'cancelled': return '#faad14';
    case 'failed': return '#f5222d';
    default: return '#d9d9d9';
  }
};

// 订单类型颜色
const getOrderTypeColor = (type: string): string => {
  switch (type) {
    case 'buy': return '#52c41a';
    case 'sell': return '#f5222d';
    case 'stop_loss': return '#ff4d4f';
    case 'take_profit': return '#52c41a';
    default: return '#d9d9d9';
  }
};

interface AutoTradingInterfaceProps {
  portfolioId?: string;
  autoRefresh?: boolean;
  onStrategyChange?: (strategies: TradingStrategy[]) => void;
  onOrderChange?: (orders: AutoOrder[]) => void;
}

const AutoTradingInterface: React.FC<AutoTradingInterfaceProps> = ({
  portfolioId = 'default',
  autoRefresh = true,
  onStrategyChange,
  onOrderChange,
}) => {
  const [strategies, setStrategies] = useState<TradingStrategy[]>([]);
  const [orders, setOrders] = useState<AutoOrder[]>([]);
  const [riskControls, setRiskControls] = useState<RiskControl[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [strategyModalVisible, setStrategyModalVisible] = useState(false);
  const [orderModalVisible, setOrderModalVisible] = useState(false);
  const [riskModalVisible, setRiskModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('strategies');
  const [isSystemRunning, setIsSystemRunning] = useState(false);

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        const mockStrategies = generateMockTradingStrategies();
        const mockOrders = generateMockAutoOrders();
        const mockRiskControls = generateMockRiskControls();
        
        setStrategies(mockStrategies);
        setOrders(mockOrders);
        setRiskControls(mockRiskControls);
        
        onStrategyChange?.(mockStrategies);
        onOrderChange?.(mockOrders);
      } catch (error) {
        console.error('Failed to initialize auto trading data:', error);
        message.error('初始化数据失败');
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, []);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      const mockOrders = generateMockAutoOrders();
      setOrders(mockOrders);
      onOrderChange?.(mockOrders);
    }, 5000); // 每5秒刷新一次订单数据

    return () => clearInterval(interval);
  }, [autoRefresh, onOrderChange]);

  // 处理策略运行状态切换
  const handleStrategyToggle = useCallback((strategyId: string) => {
    setStrategies(prev => prev.map(strategy => 
      strategy.id === strategyId 
        ? { ...strategy, running: !strategy.running, status: !strategy.running ? 'active' : 'paused' }
        : strategy
    ));
    onStrategyChange?.(strategies.map(strategy => 
      strategy.id === strategyId 
        ? { ...strategy, running: !strategy.running, status: !strategy.running ? 'active' : 'paused' }
        : strategy
    ));
    message.success('策略状态已更新');
  }, [strategies, onStrategyChange]);

  // 处理系统运行状态切换
  const handleSystemToggle = useCallback(() => {
    setIsSystemRunning(!isSystemRunning);
    message.info(isSystemRunning ? '自动交易系统已停止' : '自动交易系统已启动');
  }, [isSystemRunning]);

  // 处理策略创建
  const handleCreateStrategy = useCallback((values: any) => {
    const newStrategy: TradingStrategy = {
      id: `strategy_${Date.now()}`,
      name: values.name,
      description: values.description,
      type: values.type,
      status: 'active',
      symbol: values.symbol,
      timeframe: values.timeframe,
      parameters: {
        stopLoss: values.stopLoss,
        takeProfit: values.takeProfit,
        positionSize: values.positionSize,
        maxPosition: values.maxPosition,
        riskPerTrade: values.riskPerTrade,
      },
      performance: {
        totalTrades: 0,
        winRate: 0,
        profitFactor: 0,
        totalPnL: 0,
        maxDrawdown: 0,
        sharpeRatio: 0,
      },
      createdAt: Date.now(),
      lastUpdate: Date.now(),
      running: false,
    };
    
    setStrategies(prev => [...prev, newStrategy]);
    onStrategyChange?.([...strategies, newStrategy]);
    setStrategyModalVisible(false);
    message.success('策略创建成功');
  }, [strategies, onStrategyChange]);

  // 处理策略删除
  const handleDeleteStrategy = useCallback((strategyId: string) => {
    setStrategies(prev => prev.filter(strategy => strategy.id !== strategyId));
    onStrategyChange?.(strategies.filter(strategy => strategy.id !== strategyId));
    message.success('策略删除成功');
  }, [strategies, onStrategyChange]);

  // 处理风险控制更新
  const handleRiskControlUpdate = useCallback((riskControl: RiskControl) => {
    setRiskControls(prev => prev.map(rc => 
      rc.id === riskControl.id ? riskControl : rc
    ));
    message.success('风险控制已更新');
  }, []);

  // 策略表格列
  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: TradingStrategy) => (
        <Space>
          {getStrategyStatusIcon(record.running)}
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap = {
          trend: '趋势跟踪',
          momentum: '动量',
          mean_reversion: '均值回归',
          arbitrage: '套利',
          scalping: '高频',
        };
        return <Tag>{typeMap[type as keyof typeof typeMap]}</Tag>;
      },
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStrategyStatusColor(status)}>
          {status === 'active' ? '运行中' :
           status === 'paused' ? '已暂停' :
           status === 'stopped' ? '已停止' : '错误'}
        </Tag>
      ),
    },
    {
      title: '盈亏',
      dataIndex: 'performance',
      key: 'pnl',
      render: (performance: TradingStrategy['performance']) => (
        <span style={{ color: performance.totalPnL >= 0 ? '#52c41a' : '#f5222d' }}>
          {performance.totalPnL >= 0 ? '+' : ''}{performance.totalPnL.toFixed(2)}
        </span>
      ),
    },
    {
      title: '胜率',
      dataIndex: 'performance',
      key: 'winRate',
      render: (performance: TradingStrategy['performance']) => (
        <span style={{ color: performance.winRate >= 0.5 ? '#52c41a' : '#faad14' }}>
          {(performance.winRate * 100).toFixed(1)}%
        </span>
      ),
    },
    {
      title: '夏普比率',
      dataIndex: 'performance',
      key: 'sharpeRatio',
      render: (performance: TradingStrategy['performance']) => (
        <span style={{ color: performance.sharpeRatio >= 1 ? '#52c41a' : '#faad14' }}>
          {performance.sharpeRatio.toFixed(2)}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: TradingStrategy) => (
        <Space>
          <Button 
            type="link" 
            size="small" 
            onClick={() => handleStrategyToggle(record.id)}
            icon={record.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          >
            {record.running ? '暂停' : '启动'}
          </Button>
          <Button 
            type="link" 
            size="small" 
            onClick={() => setSelectedStrategy(record.id)}
          >
            详情
          </Button>
          <Popconfirm
            title="确定删除此策略吗？"
            onConfirm={() => handleDeleteStrategy(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 订单表格列
  const orderColumns = [
    {
      title: '策略',
      dataIndex: 'strategyName',
      key: 'strategyName',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getOrderTypeColor(type)}>
          {type === 'buy' ? '买入' :
           type === 'sell' ? '卖出' :
           type === 'stop_loss' ? '止损' : '止盈'}
        </Tag>
      ),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (text: number) => `$${text.toFixed(2)}`,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (text: number) => text.toFixed(4),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getOrderStatusColor(status)}>
          {status === 'pending' ? '待执行' :
           status === 'executed' ? '已执行' :
           status === 'cancelled' ? '已取消' : '失败'}
        </Tag>
      ),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl?: number) => pnl ? (
        <span style={{ color: pnl >= 0 ? '#52c41a' : '#f5222d' }}>
          {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}
        </span>
      ) : '-',
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: number) => new Date(timestamp).toLocaleString(),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>自动交易系统 - {portfolioId}</Title>
          <Paragraph type="secondary">
            智能化自动交易，多策略并行执行，风险控制完备
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          <Space>
            <Switch
              checkedChildren="运行中"
              unCheckedChildren="已停止"
              checked={isSystemRunning}
              onChange={handleSystemToggle}
              loading={loading}
            />
            <Button 
              type={isSystemRunning ? 'default' : 'primary'}
              icon={isSystemRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={handleSystemToggle}
              loading={loading}
            >
              {isSystemRunning ? '停止系统' : '启动系统'}
            </Button>
            <Button icon={<SettingOutlined />} onClick={() => setRiskModalVisible(true)}>
              风险控制
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 系统状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行策略"
              value={strategies.filter(s => s.running).length}
              suffix={`/ ${strategies.length}`}
              valueStyle={{ color: '#52c41a' }}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日交易"
              value={orders.filter(o => 
                new Date(o.timestamp).toDateString() === new Date().toDateString()
              ).length}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={isSystemRunning ? '运行中' : '已停止'}
              valueStyle={{ color: isSystemRunning ? '#52c41a' : '#faad14' }}
              prefix={isSystemRunning ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={orders
                .filter(o => 
                  new Date(o.timestamp).toDateString() === new Date().toDateString() && 
                  o.pnl !== undefined
                )
                .reduce((sum, o) => sum + (o.pnl || 0), 0)}
              valueStyle={{ color: '#1890ff' }}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="策略管理" key="strategies">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setStrategyModalVisible(true)}
                  >
                    创建策略
                  </Button>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={strategies}
              columns={strategyColumns}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              loading={loading}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="交易订单" key="orders">
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space>
                  <Button icon={<SyncOutlined />} onClick={() => window.location.reload()}>
                    刷新
                  </Button>
                  <Button icon={<EyeOutlined />} onClick={() => setOrderModalVisible(true)}>
                    查看详情
                  </Button>
                </Space>
              </Col>
            </Row>
            
            <Table
              dataSource={orders}
              columns={orderColumns}
              rowKey="id"
              pagination={{ pageSize: 20 }}
              loading={loading}
              size="small"
              scroll={{ x: 1000 }}
            />
          </TabPane>
          
          <TabPane tab="风险控制" key="risk">
            <Row gutter={[16, 16]}>
              {riskControls.map((control) => (
                <Col span={8} key={control.id}>
                  <Card size="small">
                    <Row gutter={16}>
                      <Col span={16}>
                        <Text strong>{control.name}</Text>
                        <br />
                        <Text type="secondary">{control.description}</Text>
                      </Col>
                      <Col span={8}>
                        <Switch
                          checked={control.enabled}
                          onChange={(checked) => handleRiskControlUpdate({ ...control, enabled: checked })}
                        />
                      </Col>
                    </Row>
                    <Progress
                      percent={(control.value / 100) * 100}
                      strokeColor={control.enabled ? '#52c41a' : '#d9d9d9'}
                      trailColor="#f0f0f0"
                      showInfo={false}
                    />
                    <Text type="secondary">{control.value}</Text>
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建策略模态框 */}
      <Modal
        title="创建交易策略"
        open={strategyModalVisible}
        onCancel={() => setStrategyModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          layout="vertical"
          onFinish={handleCreateStrategy}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="策略名称"
                name="name"
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input placeholder="输入策略名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="策略类型"
                name="type"
                rules={[{ required: true, message: '请选择策略类型' }]}
              >
                <Select>
                  <Option value="trend">趋势跟踪</Option>
                  <Option value="momentum">动量</Option>
                  <Option value="mean_reversion">均值回归</Option>
                  <Option value="arbitrage">套利</Option>
                  <Option value="scalping">高频</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            label="策略描述"
            name="description"
            rules={[{ required: true, message: '请输入策略描述' }]}
          >
            <TextArea rows={3} placeholder="输入策略描述" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="交易对"
                name="symbol"
                rules={[{ required: true, message: '请选择交易对' }]}
              >
                <Select>
                  <Option value="BTC/USDT">BTC/USDT</Option>
                  <Option value="ETH/USDT">ETH/USDT</Option>
                  <Option value="BNB/USDT">BNB/USDT</Option>
                  <Option value="ADA/USDT">ADA/USDT</Option>
                  <Option value="SOL/USDT">SOL/USDT</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="时间周期"
                name="timeframe"
                rules={[{ required: true, message: '请选择时间周期' }]}
              >
                <Select>
                  <Option value="1m">1分钟</Option>
                  <Option value="5m">5分钟</Option>
                  <Option value="15m">15分钟</Option>
                  <Option value="1h">1小时</Option>
                  <Option value="4h">4小时</Option>
                  <Option value="1d">1天</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="止损比例"
                name="stopLoss"
                rules={[{ required: true, message: '请输入止损比例' }]}
              >
                <InputNumber min="0" max="1" step="0.01" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="止盈比例"
                name="takeProfit"
                rules={[{ required: true, message: '请输入止盈比例' }]}
              >
                <InputNumber min="0" max="1" step="0.01" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="每笔风险"
                name="riskPerTrade"
                rules={[{ required: true, message: '请输入每笔风险' }]}
              >
                <InputNumber min="0" max="1" step="0.01" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="持仓大小"
                name="positionSize"
                rules={[{ required: true, message: '请输入持仓大小' }]}
              >
                <InputNumber min="0" max="1" step="0.01" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="最大持仓"
                name="maxPosition"
                rules={[{ required: true, message: '请输入最大持仓' }]}
              >
                <InputNumber min="1" max="10" step="1" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建策略
              </Button>
              <Button onClick={() => setStrategyModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 策略详情模态框 */}
      <Modal
        title="策略详情"
        open={!!selectedStrategy}
        onCancel={() => setSelectedStrategy(null)}
        footer={null}
        width={800}
      >
        {selectedStrategy && strategies.find(s => s.id === selectedStrategy) && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>策略名称：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>策略类型：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.type}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>交易对：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.symbol}</Text>
              </Col>
              <Col span={12}>
                <Text strong>时间周期：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.timeframe}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>创建时间：</Text>
                <Text>{new Date(strategies.find(s => s.id === selectedStrategy)?.createdAt || 0).toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>最后更新：</Text>
                <Text>{new Date(strategies.find(s => s.id === selectedStrategy)?.lastUpdate || 0).toLocaleString()}</Text>
              </Col>
            </Row>
            <Divider />
            <Row gutter={16}>
              <Col span={8}>
                <Text strong>总交易次数：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.performance.totalTrades}</Text>
              </Col>
              <Col span={8}>
                <Text strong>胜率：</Text>
                <Text>{(strategies.find(s => s.id === selectedStrategy)?.performance.winRate || 0 * 100).toFixed(1)}%</Text>
              </Col>
              <Col span={8}>
                <Text strong>夏普比率：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.performance.sharpeRatio.toFixed(2)}</Text>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={8}>
                <Text strong>总盈亏：</Text>
                <Text style={{ color: (strategies.find(s => s.id === selectedStrategy)?.performance.totalPnL || 0) >= 0 ? '#52c41a' : '#f5222d' }}>
                  {(strategies.find(s => s.id === selectedStrategy)?.performance.totalPnL || 0).toFixed(2)}
                </Text>
              </Col>
              <Col span={8}>
                <Text strong>最大回撤：</Text>
                <Text>{(strategies.find(s => s.id === selectedStrategy)?.performance.maxDrawdown || 0 * 100).toFixed(2)}%</Text>
              </Col>
              <Col span={8}>
                <Text strong>盈利因子：</Text>
                <Text>{strategies.find(s => s.id === selectedStrategy)?.performance.profitFactor.toFixed(2)}</Text>
              </Col>
            </Row>
          </Space>
        )}
      </Modal>
    </div>
  );
};

export default AutoTradingInterface;