/**
 * 交易管理页面 - 专业的订单、持仓和账户管理界面
 * Trading Management Page - Professional Order, Position and Account Management Interface
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Typography,
  message,
  Modal,
  Switch,
  InputNumber,
  Form,
  Popconfirm,
  Tabs,
  Tooltip,
  Drawer,
  DatePicker,
  Dropdown,
  Descriptions,
  Progress,
  List,
} from 'antd';
import {
  FundOutlined,
  PlusOutlined,
  ExportOutlined,
  MoreOutlined,
  FileTextOutlined,
  BarChartOutlined,
  RiseOutlined,
  FallOutlined,
  DollarCircleOutlined,
  ClockCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
  EyeOutlined,
  StopOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  BankOutlined,
  WalletOutlined,
  SecurityScanOutlined,
  CalculatorOutlined,
  ArrowUpOutlined, ArrowDownOutlined
} from '@ant-design/icons';
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

import { 
  tradingAPI, 
  strategyAPI, 
  Order, 
  Position, 
  handleApiError,
  Strategy,
  apiCallWithRetry
} from '../services/api';
import { useDataCache } from '../hooks/useDataCache';
import moment from 'moment';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;
const { Option } = Select;
// 函数集注释：
// 1) loadOrders：获取订单列表并应用筛选
// 2) loadPositions：获取持仓列表并应用筛选
// 3) generateChartData：基于当前持仓生成分析图表数据
// 4) loadAllData：并行加载页面所需的全部数据

const TradingManagement: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [orders, setOrders] = useState<Order[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [accountInfo, setAccountInfo] = useState<any | null>(null);
  const [tradingStats, setTradingStats] = useState<any | null>(null);
  const [recentTrades, setRecentTrades] = useState<any[]>([]);
  const [orderFilters, setOrderFilters] = useState({
    symbol: '',
    status: '',
    side: '',
    type: '',
    strategyId: '',
    dateRange: [] as any[],
  });
  
  const [positionFilters, setPositionFilters] = useState({
    symbol: '',
    side: '',
    strategyId: '',
  });
  
  // 详情显示
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [orderDrawerVisible, setOrderDrawerVisible] = useState(false);
  const [positionDrawerVisible, setPositionDrawerVisible] = useState(false);
  
  // 交易模态框
  const [tradeModalVisible, setTradeModalVisible] = useState(false);
  const [tradeForm] = Form.useForm();
  
  // 图表数据
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [positionDistribution, setPositionDistribution] = useState<any[]>([]);
  const [orderFlowData, setOrderFlowData] = useState<any[]>([]);
  
  // 使用数据缓存
  const { getData: fetchOrders } = useDataCache<Order[]>(
    'orders',
    { ttl: 1 * 60 * 1000 } // 1分钟缓存
  );
  
  const { getData: fetchPositions } = useDataCache<Position[]>(
    'positions',
    { ttl: 30 * 1000 } // 30秒缓存
  );
  
  // 获取订单数据
  const loadOrders = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        ...orderFilters,
        start_date: orderFilters.dateRange?.[0]?.format('YYYY-MM-DD'),
        end_date: orderFilters.dateRange?.[1]?.format('YYYY-MM-DD'),
      };
      
      const data = await fetchOrders(
        async () => {
          const resp: any = await apiCallWithRetry(() => tradingAPI.getOrders(params));
          return Array.isArray(resp) ? resp : ((resp as any)?.orders || []);
        },
        true
      );
      
      if (data) {
        setOrders(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchOrders, orderFilters]);
  
  // 获取持仓数据
  const loadPositions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchPositions(
        async () => {
          const resp: any = await apiCallWithRetry(() => tradingAPI.getPositions(positionFilters));
          return Array.isArray(resp) ? resp : ((resp as any)?.positions || []);
        },
        true
      );
      
      if (data) {
        setPositions(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchPositions, positionFilters]);
  
  // 导出数据
  const handleExportData = (type: 'orders' | 'positions' | 'trades') => {
    let data: any[] = [];
    let filename = '';
    
    switch (type) {
      case 'orders':
        data = orders;
        filename = 'orders_export.csv';
        break;
      case 'positions':
        data = positions;
        filename = 'positions_export.csv';
        break;
      case 'trades':
        data = recentTrades;
        filename = 'trades_export.csv';
        break;
    }
    
    if (data.length > 0) {
      const headers = Object.keys(data[0]);
      const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => row[header]).join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.click();
      message.success('数据导出成功！');
    } else {
      message.warning('没有可导出的数据');
    }
  };
  
  

  
  
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
  }, []);
  
  // 获取账户信息
  const loadAccountInfo = useCallback(async () => {
    try {
      const data = await apiCallWithRetry(() => tradingAPI.getAccountInfo());
      setAccountInfo(data);
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  }, []);
  
  // 获取交易统计
  const loadTradingStats = useCallback(async () => {
    try {
      const data = await apiCallWithRetry(() => tradingAPI.getTradesStatistics());
      setTradingStats(data);
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  }, []);
  
  // 获取最近交易
  const loadRecentTrades = useCallback(async () => {
    try {
      const data = await apiCallWithRetry(() => tradingAPI.getTrades({ limit: 20 }));
      setRecentTrades(Array.isArray(data) ? data : []);
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  }, []);

  // 生成图表数据
  const generateChartData = useCallback(() => {
    const perfData = Array.from({ length: 30 }, (_, i) => ({
      date: `Day ${i + 1}`,
      pnl: Math.random() * 2000 - 1000,
      trades: Math.floor(Math.random() * 20) + 1,
      winRate: Math.random() * 100,
    }));
    setPerformanceData(perfData);
    const posDist = positions.map(pos => ({
      name: pos.symbol,
      value: Math.abs(pos.pnl),
      color: pos.pnl >= 0 ? '#52c41a' : '#ff4d4f',
    }));
    setPositionDistribution(posDist);
    const orderFlow = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      buy: Math.floor(Math.random() * 50) + 10,
      sell: Math.floor(Math.random() * 50) + 10,
    }));
    setOrderFlowData(orderFlow);
  }, [positions]);
  
  // 初始化图表数据
  useEffect(() => {
    generateChartData();
  }, [generateChartData]);
  
  // 加载所有数据
  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadOrders(),
        loadPositions(),
        loadStrategies(),
        loadAccountInfo(),
        loadTradingStats(),
        loadRecentTrades(),
      ]);
      generateChartData();
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [loadOrders, loadPositions, loadStrategies, loadAccountInfo, loadTradingStats, loadRecentTrades, generateChartData]);
  
  // 创建订单
  const handleCreateOrder = async (values: any) => {
    try {
      setLoading(true);
      await apiCallWithRetry(() => tradingAPI.createOrder(values));
      message.success('订单创建成功');
      setTradeModalVisible(false);
      tradeForm.resetFields();
      await loadOrders();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // 取消订单
  const handleCancelOrder = async (orderId: string) => {
    try {
      setLoading(true);
      await apiCallWithRetry(() => tradingAPI.cancelOrder(orderId));
      message.success('订单取消成功');
      await loadOrders();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // 平仓
  const handleClosePosition = async (positionId: string) => {
    try {
      setLoading(true);
      await apiCallWithRetry(() => tradingAPI.closePosition(positionId));
      message.success('平仓成功');
      await loadPositions();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  
  // 查看订单详情
  const handleViewOrder = (order: Order) => {
    setSelectedOrder(order);
    setOrderDrawerVisible(true);
  };
  
  // 查看持仓详情
  const handleViewPosition = (position: Position) => {
    setSelectedPosition(position);
    setPositionDrawerVisible(true);
  };
  
    
  // 初始化加载
  useEffect(() => {
    if (isAuthenticated) {
      loadAllData();
    }
  }, [isAuthenticated, loadAllData]);
  
  // 自动刷新
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        const promises = [
          loadOrders(),
          loadPositions(),
          loadAccountInfo(),
          loadRecentTrades(),
        ];
        Promise.all(promises);
      }, refreshInterval);
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, loadOrders, loadPositions, loadAccountInfo, loadRecentTrades]);
  
  // 订单表格列
  const orderColumns: any = [
    {
      title: '订单ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Tooltip title={id}>
          <Text code>{id.substring(0, 8)}...</Text>
        </Tooltip>
      ),
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => (
        <span>{moment(timestamp).format('MM-DD HH:mm:ss')}</span>
      ),
      sorter: (a: Order, b: Order) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    },
    {
      title: '策略',
      dataIndex: 'strategyId',
      key: 'strategyId',
      render: (strategyId: string) => {
        const strategy = strategies.find(s => s.id === strategyId);
        return (
          <Tooltip title={strategy?.name || strategyId}>
            <Tag color="blue">{strategy?.name || strategyId.substring(0, 8)}</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="green">{symbol}</Tag>,
      filters: [
        { text: 'BTCUSDT', value: 'BTCUSDT' },
        { text: 'ETHUSDT', value: 'ETHUSDT' },
        { text: 'BNBUSDT', value: 'BNBUSDT' },
      ],
      onFilter: (value: string, record: Order) => record.symbol === value,
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'} icon={side === 'buy' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}>
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
      filters: [
        { text: '买入', value: 'buy' },
        { text: '卖出', value: 'sell' },
      ],
      onFilter: (value: string, record: Order) => record.side === value,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'market' ? 'blue' : 'orange'}>
          {type === 'market' ? '市价' : '限价'}
        </Tag>
      ),
      filters: [
        { text: '市价单', value: 'market' },
        { text: '限价单', value: 'limit' },
      ],
      onFilter: (value: string, record: Order) => record.type === value,
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`,
      sorter: (a: Order, b: Order) => a.price - b.price,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4),
    },
    {
      title: '成交数量',
      dataIndex: 'filledQuantity',
      key: 'filledQuantity',
      render: (filledQuantity: number, record: Order) => (
        <div>
          <div>{filledQuantity.toFixed(4)}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {((filledQuantity / record.quantity) * 100).toFixed(1)}%
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          pending: { color: 'orange', text: '待成交', icon: <ClockCircleOutlined /> },
          filled: { color: 'green', text: '已成交', icon: <CheckCircleOutlined /> },
          cancelled: { color: 'red', text: '已取消', icon: <StopOutlined /> },
          failed: { color: 'red', text: '失败', icon: <ExclamationCircleOutlined /> },
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color} icon={config.icon}>{config.text}</Tag>;
      },
      filters: [
        { text: '待成交', value: 'pending' },
        { text: '已成交', value: 'filled' },
        { text: '已取消', value: 'cancelled' },
        { text: '失败', value: 'failed' },
      ],
      onFilter: (value: string, record: Order) => record.status === value,
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Text style={{ color: pnl >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
          {pnl >= 0 ? '+' : ''}${pnl?.toFixed(2) || '0.00'}
        </Text>
      ),
      sorter: (a: Order, b: Order) => (a.pnl || 0) - (b.pnl || 0),
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: Order) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewOrder(record)}
              size="small"
            />
          </Tooltip>
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要取消这个订单吗？"
              onConfirm={() => handleCancelOrder(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Tooltip title="取消订单">
                <Button
                  type="link"
                  danger
                  icon={<StopOutlined />}
                  size="small"
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];
  
  // 持仓表格列
  const positionColumns: any = [
    {
      title: '持仓ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Tooltip title={id}>
          <Text code>{id.substring(0, 8)}...</Text>
        </Tooltip>
      ),
    },
    {
      title: '策略',
      dataIndex: 'strategyId',
      key: 'strategyId',
      render: (strategyId: string) => {
        const strategy = strategies.find(s => s.id === strategyId);
        return (
          <Tooltip title={strategy?.name || strategyId}>
            <Tag color="blue">{strategy?.name || strategyId.substring(0, 8)}</Tag>
          </Tooltip>
        );
      },
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="green">{symbol}</Tag>,
      filters: [
        { text: 'BTCUSDT', value: 'BTCUSDT' },
        { text: 'ETHUSDT', value: 'ETHUSDT' },
        { text: 'BNBUSDT', value: 'BNBUSDT' },
      ],
      onFilter: (value: string, record: Position) => record.symbol === value,
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'long' ? 'green' : 'red'} icon={side === 'long' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}>
          {side === 'long' ? '多头' : '空头'}
        </Tag>
      ),
      filters: [
        { text: '多头', value: 'long' },
        { text: '空头', value: 'short' },
      ],
      onFilter: (value: string, record: Position) => record.side === value,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4),
    },
    {
      title: '入场价格',
      dataIndex: 'entryPrice',
      key: 'entryPrice',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '当前价格',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <Text style={{ color: pnl >= 0 ? '#52c41a' : '#ff4d4f', fontWeight: 'bold' }}>
          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
        </Text>
      ),
      sorter: (a: Position, b: Position) => a.pnl - b.pnl,
    },
    {
      title: '盈亏比例',
      dataIndex: 'pnlPercent',
      key: 'pnlPercent',
      render: (percent: number) => (
        <Text style={{ color: percent >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {percent >= 0 ? '+' : ''}{percent.toFixed(2)}%
        </Text>
      ),
      sorter: (a: Position, b: Position) => a.pnlPercent - b.pnlPercent,
    },
    {
      title: '保证金',
      dataIndex: 'margin',
      key: 'margin',
      render: (margin: number) => `$${margin.toFixed(2)}`,
    },
    {
      title: '杠杆',
      dataIndex: 'leverage',
      key: 'leverage',
      render: (leverage: number) => `${leverage}x`,
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: Position) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewPosition(record)}
              size="small"
            />
          </Tooltip>
          <Popconfirm
            title="确定要平仓吗？"
            onConfirm={() => handleClosePosition(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="平仓">
              <Button
                type="link"
                danger
                icon={<StopOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];
  
  // 计算统计数据
  const stats = {
    totalOrders: orders.length,
    pendingOrders: orders.filter(o => o.status === 'pending').length,
    filledOrders: orders.filter(o => o.status === 'filled').length,
    totalPnl: orders.reduce((sum, order) => sum + (order.pnl || 0), 0),
    totalPositions: positions.length,
    longPositions: positions.filter(p => p.side === 'long').length,
    shortPositions: positions.filter(p => p.side === 'short').length,
    positionsPnl: positions.reduce((sum, pos) => sum + pos.pnl, 0),
    totalMargin: positions.reduce((sum, pos) => sum + pos.margin, 0),
    accountBalance: accountInfo?.total_balance || 0,
    availableBalance: accountInfo?.available_balance || 0,
    totalExposure: positions.reduce((sum, pos) => sum + pos.margin * pos.leverage, 0),
  };
  
  // 最近交易表格列
  const recentTradesColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => moment(timestamp).format('HH:mm:ss'),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="green">{symbol}</Tag>,
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4),
    },
    {
      title: '手续费',
      dataIndex: 'fee',
      key: 'fee',
      render: (fee: number) => `$${fee.toFixed(2)}`,
    },
  ];
  
  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题和操作栏 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={12}>
          <Title level={2} style={{ margin: 0 }}>
            <FundOutlined /> 交易管理
          </Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => setTradeModalVisible(true)}
            >
              手动交易
            </Button>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'export-orders',
                    icon: <ExportOutlined />,
                    label: '导出订单',
                    onClick: () => handleExportData('orders'),
                  },
                  {
                    key: 'export-positions',
                    icon: <ExportOutlined />,
                    label: '导出持仓',
                    onClick: () => handleExportData('positions'),
                  },
                  {
                    key: 'export-trades',
                    icon: <ExportOutlined />,
                    label: '导出交易记录',
                    onClick: () => handleExportData('trades'),
                  },
                ],
              }}
            >
              <Button icon={<ExportOutlined />}>
                导出数据 <MoreOutlined />
              </Button>
            </Dropdown>
            <span>自动刷新:</span>
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
            />
            <Select
              value={refreshInterval}
              onChange={setRefreshInterval}
              style={{ width: 100 }}
              size="small"
            >
              <Option value={1000}>1秒</Option>
              <Option value={5000}>5秒</Option>
              <Option value={10000}>10秒</Option>
              <Option value={30000}>30秒</Option>
            </Select>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadAllData}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        </Col>
      </Row>
      
      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="账户余额"
              value={stats.accountBalance}
              prefix={<DollarCircleOutlined />}
              precision={2}
              valueStyle={{ color: '#1890ff' }}
              suffix="USDT"
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              可用: ${stats.availableBalance.toFixed(2)}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={stats.totalPnl}
              prefix={stats.totalPnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
              precision={2}
              valueStyle={{ color: stats.totalPnl >= 0 ? '#52c41a' : '#ff4d4f' }}
              suffix="USDT"
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              订单数: {stats.totalOrders}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="持仓盈亏"
              value={stats.positionsPnl}
              prefix={stats.positionsPnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
              precision={2}
              valueStyle={{ color: stats.positionsPnl >= 0 ? '#52c41a' : '#ff4d4f' }}
              suffix="USDT"
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              持仓数: {stats.totalPositions}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总敞口"
              value={stats.totalExposure}
              prefix={<BarChartOutlined />}
              precision={2}
              valueStyle={{ color: '#722ed1' }}
              suffix="USDT"
            />
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              杠杆: {stats.accountBalance > 0 ? (stats.totalExposure / stats.accountBalance).toFixed(2) : '0'}x
            </div>
          </Card>
        </Col>
      </Row>
      
      {/* 主要内容区域 */}
      <Tabs 
        defaultActiveKey="orders" 
        type="card"
        items={[
          {
            key: 'orders',
            label: (
              <span>
                <FileTextOutlined />
                订单管理 ({stats.totalOrders})
              </span>
            ),
            children: (
              <Card>
                {/* 订单筛选 */}
                <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                  <Col xs={24} sm={12} md={6}>
                    <Select
                      placeholder="状态"
                      style={{ width: '100%' }}
                      value={orderFilters.status}
                      onChange={(value) => setOrderFilters({ ...orderFilters, status: value })}
                      allowClear
                    >
                      <Option value="pending">待成交</Option>
                      <Option value="filled">已成交</Option>
                      <Option value="cancelled">已取消</Option>
                      <Option value="failed">失败</Option>
                    </Select>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Select
                      placeholder="交易对"
                      style={{ width: '100%' }}
                      value={orderFilters.symbol}
                      onChange={(value) => setOrderFilters({ ...orderFilters, symbol: value })}
                      allowClear
                    >
                      <Option value="BTCUSDT">BTC/USDT</Option>
                      <Option value="ETHUSDT">ETH/USDT</Option>
                      <Option value="BNBUSDT">BNB/USDT</Option>
                    </Select>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <DatePicker.RangePicker
                      style={{ width: '100%' }}
                      value={orderFilters.dateRange as any}
                      onChange={(dates) => setOrderFilters({ ...orderFilters, dateRange: (dates as any) })}
                      placeholder={['开始日期', '结束日期']}
                    />
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Button 
                      icon={<FilterOutlined />} 
                      onClick={() => setOrderFilters({ status: '', symbol: '', side: '', type: '', strategyId: '', dateRange: [] })}
                      style={{ width: '100%' }}
                    >
                      清除筛选
                    </Button>
                  </Col>
                </Row>
                
                <Table
                  loading={loading}
                  columns={orderColumns}
                  dataSource={orders}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  }}
                  scroll={{ x: 1600 }}
                  size="middle"
                />
              </Card>
            ),
          },
          {
            key: 'positions',
            label: (
              <span>
                <WalletOutlined />
                持仓管理 ({stats.totalPositions})
              </span>
            ),
            children: (
              <Card>
                {/* 持仓筛选 */}
                <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                  <Col xs={24} sm={12} md={8}>
                    <Select
                      placeholder="交易对"
                      style={{ width: '100%' }}
                      value={positionFilters.symbol}
                      onChange={(value) => setPositionFilters({ ...positionFilters, symbol: value })}
                      allowClear
                    >
                      <Option value="BTCUSDT">BTC/USDT</Option>
                      <Option value="ETHUSDT">ETH/USDT</Option>
                      <Option value="BNBUSDT">BNB/USDT</Option>
                    </Select>
                  </Col>
                  <Col xs={24} sm={12} md={8}>
                    <Select
                      placeholder="方向"
                      style={{ width: '100%' }}
                      value={positionFilters.side}
                      onChange={(value) => setPositionFilters({ ...positionFilters, side: value })}
                      allowClear
                    >
                      <Option value="long">多头</Option>
                      <Option value="short">空头</Option>
                    </Select>
                  </Col>
                  <Col xs={24} sm={12} md={8}>
                    <Button 
                      icon={<FilterOutlined />} 
                      onClick={() => setPositionFilters({ symbol: '', side: '', strategyId: '' })}
                      style={{ width: '100%' }}
                    >
                      清除筛选
                    </Button>
                  </Col>
                </Row>
                
                <Table
                  loading={loading}
                  columns={positionColumns}
                  dataSource={positions}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  }}
                  scroll={{ x: 1400 }}
                  size="middle"
                />
              </Card>
            ),
          },
          {
            key: 'analytics',
            label: (
              <span>
                <BarChartOutlined />
                交易分析
              </span>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {/* 性能图表 */}
                <Col span={24}>
                  <Card title="盈亏趋势">
                    <div style={{ height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={performanceData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="date" />
                          <YAxis />
                          <RechartsTooltip />
                          <Area 
                            type="monotone" 
                            dataKey="pnl" 
                            stroke="#8884d8" 
                            fill="#8884d8" 
                            fillOpacity={0.3}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>
                </Col>
                
                {/* 持仓分布 */}
                <Col xs={24} md={12}>
                  <Card title="持仓分布">
                    <div style={{ height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={positionDistribution}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent = 0 }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {positionDistribution.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <RechartsTooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>
                </Col>
                
                {/* 订单流 */}
                <Col xs={24} md={12}>
                  <Card title="订单流（24小时）">
                    <div style={{ height: '300px' }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={orderFlowData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="hour" />
                          <YAxis />
                          <RechartsTooltip />
                          <Legend />
                          <Bar dataKey="buy" fill="#52c41a" name="买入" />
                          <Bar dataKey="sell" fill="#ff4d4f" name="卖出" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </Card>
                </Col>
                
                {/* 最近交易 */}
                <Col span={24}>
                  <Card title="最近交易记录">
                    <Table
                      columns={recentTradesColumns}
                      dataSource={recentTrades}
                      rowKey="id"
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                      }}
                      size="small"
                    />
                  </Card>
                </Col>
              </Row>
            ),
          },
          {
            key: 'account',
            label: (
              <span>
                <BankOutlined />
                账户信息
              </span>
            ),
            children: (
              <Row gutter={[16, 16]}>
                {/* 账户概览 */}
                <Col span={24}>
                  <Card title="账户概览">
                    <Row gutter={[16, 16]}>
                      <Col xs={24} sm={12} md={8}>
                        <Statistic
                          title="总余额"
                          value={accountInfo?.total_balance || 0}
                          prefix={<DollarCircleOutlined />}
                          precision={2}
                          suffix="USDT"
                        />
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <Statistic
                          title="可用余额"
                          value={accountInfo?.available_balance || 0}
                          prefix={<WalletOutlined />}
                          precision={2}
                          suffix="USDT"
                        />
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <Statistic
                          title="冻结余额"
                          value={accountInfo?.frozen_balance || 0}
                          prefix={<SecurityScanOutlined />}
                          precision={2}
                          suffix="USDT"
                        />
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <Statistic
                          title="总盈亏"
                          value={accountInfo?.total_pnl || 0}
                          prefix={accountInfo?.total_pnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
                          precision={2}
                          valueStyle={{ color: (accountInfo?.total_pnl || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
                          suffix="USDT"
                        />
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <Statistic
                          title="今日盈亏"
                          value={accountInfo?.today_pnl || 0}
                          prefix={accountInfo?.today_pnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
                          precision={2}
                          valueStyle={{ color: (accountInfo?.today_pnl || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
                          suffix="USDT"
                        />
                      </Col>
                      <Col xs={24} sm={12} md={8}>
                        <Statistic
                          title="手续费"
                          value={accountInfo?.total_fee || 0}
                          prefix={<CalculatorOutlined />}
                          precision={2}
                          suffix="USDT"
                        />
                      </Col>
                    </Row>
                  </Card>
                </Col>
                
                {/* 风险指标 */}
                <Col xs={24} md={12}>
                  <Card title="风险指标">
                    <List size="small">
                      <List.Item>
                        <List.Item.Meta
                          title="保证金率"
                          description={`${((accountInfo?.margin_ratio || 0) * 100).toFixed(2)}%`}
                        />
                        <Progress 
                          percent={Math.min((accountInfo?.margin_ratio || 0) * 100, 100)}
                          status={accountInfo?.margin_ratio > 0.8 ? 'exception' : 'success'}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="维持保证金"
                          description={`$${(accountInfo?.maintenance_margin || 0).toFixed(2)}`}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="最大杠杆"
                          description={`${accountInfo?.max_leverage || 1}x`}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="风险等级"
                          description={
                            <Tag color={
                              accountInfo?.risk_level === 'low' ? 'green' :
                              accountInfo?.risk_level === 'medium' ? 'orange' : 'red'
                            }>
                              {accountInfo?.risk_level === 'low' ? '低' :
                               accountInfo?.risk_level === 'medium' ? '中' : '高'}
                            </Tag>
                          }
                        />
                      </List.Item>
                    </List>
                  </Card>
                </Col>
                
                {/* 交易统计 */}
                <Col xs={24} md={12}>
                  <Card title="交易统计">
                    <List size="small">
                      <List.Item>
                        <List.Item.Meta
                          title="总交易次数"
                          description={tradingStats?.total_trades || 0}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="胜率"
                          description={`${((tradingStats?.win_rate || 0) * 100).toFixed(2)}%`}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="平均持仓时间"
                          description={tradingStats?.avg_holding_time || '0h'}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="最大回撤"
                          description={`${((tradingStats?.max_drawdown || 0) * 100).toFixed(2)}%`}
                        />
                      </List.Item>
                      <List.Item>
                        <List.Item.Meta
                          title="夏普比率"
                          description={tradingStats?.sharpe_ratio?.toFixed(2) || '0.00'}
                        />
                      </List.Item>
                    </List>
                  </Card>
                </Col>
              </Row>
            ),
          },
        ]}
      />
      
      {/* 手动交易模态框 */}
      <Modal
        title="手动交易"
        open={tradeModalVisible}
        onCancel={() => {
          setTradeModalVisible(false);
          tradeForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={tradeForm}
          layout="vertical"
          onFinish={handleCreateOrder}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="交易对"
                name="symbol"
                rules={[{ required: true, message: '请选择交易对' }]}
              >
                <Select placeholder="选择交易对">
                  <Option value="BTCUSDT">BTC/USDT</Option>
                  <Option value="ETHUSDT">ETH/USDT</Option>
                  <Option value="BNBUSDT">BNB/USDT</Option>
                  <Option value="ADAUSDT">ADA/USDT</Option>
                  <Option value="DOTUSDT">DOT/USDT</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="方向"
                name="side"
                rules={[{ required: true, message: '请选择交易方向' }]}
              >
                <Select placeholder="选择方向">
                  <Option value="buy">买入</Option>
                  <Option value="sell">卖出</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="类型"
                name="type"
                rules={[{ required: true, message: '请选择订单类型' }]}
              >
                <Select placeholder="选择类型">
                  <Option value="market">市价单</Option>
                  <Option value="limit">限价单</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="策略"
                name="strategyId"
              >
                <Select placeholder="选择策略（可选）" allowClear>
                  {strategies.map(strategy => (
                    <Option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="价格"
                name="price"
                rules={[
                  { required: true, message: '请输入价格' },
                  { type: 'number', min: 0, message: '价格必须大于0' }
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="输入价格"
                  precision={2}
                  addonBefore="$"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="数量"
                name="quantity"
                rules={[
                  { required: true, message: '请输入数量' },
                  { type: 'number', min: 0, message: '数量必须大于0' }
                ]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="输入数量"
                  precision={4}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                提交订单
              </Button>
              <Button onClick={() => {
                setTradeModalVisible(false);
                tradeForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
      
      {/* 订单详情抽屉 */}
      <Drawer
        title="订单详情"
        placement="right"
        onClose={() => setOrderDrawerVisible(false)}
        open={orderDrawerVisible}
        width={600}
      >
        {selectedOrder && (
          <div>
            <Card title="基本信息" style={{ marginBottom: '16px' }}>
              <Descriptions column={2}>
                <Descriptions.Item label="订单ID">{selectedOrder.id}</Descriptions.Item>
                <Descriptions.Item label="策略ID">{selectedOrder.strategyId}</Descriptions.Item>
                <Descriptions.Item label="交易对">{selectedOrder.symbol}</Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={
                    selectedOrder.status === 'pending' ? 'orange' :
                    selectedOrder.status === 'filled' ? 'green' : 'red'
                  }>
                    {selectedOrder.status === 'pending' ? '待成交' :
                     selectedOrder.status === 'filled' ? '已成交' :
                     selectedOrder.status === 'cancelled' ? '已取消' : '失败'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {moment(selectedOrder.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
                <Descriptions.Item label="更新时间">
                  {selectedOrder && moment((selectedOrder as any).timestamp || (selectedOrder as any).updatedAt).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
              </Descriptions>
            </Card>
            
            <Card title="交易信息">
              <Descriptions column={2}>
                <Descriptions.Item label="方向">
                  <Tag color={selectedOrder.side === 'buy' ? 'green' : 'red'}>
                    {selectedOrder.side === 'buy' ? '买入' : '卖出'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="类型">
                  <Tag color={selectedOrder.type === 'market' ? 'blue' : 'orange'}>
                    {selectedOrder.type === 'market' ? '市价' : '限价'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="价格">${selectedOrder.price.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="数量">{selectedOrder.quantity.toFixed(4)}</Descriptions.Item>
                <Descriptions.Item label="成交数量">{selectedOrder.filledQuantity.toFixed(4)}</Descriptions.Item>
                <Descriptions.Item label="成交率">
                  {((selectedOrder.filledQuantity / selectedOrder.quantity) * 100).toFixed(2)}%
                </Descriptions.Item>
                <Descriptions.Item label="成交均价">${selectedOrder.averagePrice.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="手续费">${selectedOrder.fee.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="盈亏">
                  <Text style={{ 
                    color: (selectedOrder.pnl || 0) >= 0 ? '#52c41a' : '#ff4d4f',
                    fontWeight: 'bold'
                  }}>
                    {(selectedOrder.pnl || 0) >= 0 ? '+' : ''}${(selectedOrder.pnl || 0).toFixed(2)}
                  </Text>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </div>
        )}
      </Drawer>
      
      {/* 持仓详情抽屉 */}
      <Drawer
        title="持仓详情"
        placement="right"
        onClose={() => setPositionDrawerVisible(false)}
        open={positionDrawerVisible}
        width={600}
      >
        {selectedPosition && (
          <div>
            <Card title="基本信息" style={{ marginBottom: '16px' }}>
              <Descriptions column={2}>
                <Descriptions.Item label="持仓ID">{selectedPosition.id}</Descriptions.Item>
                <Descriptions.Item label="策略ID">{selectedPosition.strategyId}</Descriptions.Item>
                <Descriptions.Item label="交易对">{selectedPosition.symbol}</Descriptions.Item>
                <Descriptions.Item label="方向">
                  <Tag color={selectedPosition.side === 'long' ? 'green' : 'red'}>
                    {selectedPosition.side === 'long' ? '多头' : '空头'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="开仓时间">
                  {moment(selectedPosition.timestamp).format('YYYY-MM-DD HH:mm:ss')}
                </Descriptions.Item>
                <Descriptions.Item label="持仓时长">
                  {moment().diff(moment(selectedPosition.timestamp), 'hours')}小时
                </Descriptions.Item>
              </Descriptions>
            </Card>
            
            <Card title="价格信息" style={{ marginBottom: '16px' }}>
              <Descriptions column={2}>
                <Descriptions.Item label="入场价格">${selectedPosition.entryPrice.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="当前价格">${selectedPosition.currentPrice.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="价格差">
                  <Text style={{ 
                    color: (selectedPosition.currentPrice - selectedPosition.entryPrice) >= 0 ? '#52c41a' : '#ff4d4f'
                  }}>
                    {selectedPosition.currentPrice >= selectedPosition.entryPrice ? '+' : ''}
                    ${(selectedPosition.currentPrice - selectedPosition.entryPrice).toFixed(2)}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="价格变化">
                  <Text style={{ 
                    color: ((selectedPosition.currentPrice - selectedPosition.entryPrice) / selectedPosition.entryPrice * 100) >= 0 ? '#52c41a' : '#ff4d4f'
                  }}>
                    {((selectedPosition.currentPrice - selectedPosition.entryPrice) / selectedPosition.entryPrice * 100) >= 0 ? '+' : ''}
                    {((selectedPosition.currentPrice - selectedPosition.entryPrice) / selectedPosition.entryPrice * 100).toFixed(2)}%
                  </Text>
                </Descriptions.Item>
              </Descriptions>
            </Card>
            
            <Card title="盈亏分析">
              <Descriptions column={2}>
                <Descriptions.Item label="数量">{selectedPosition.quantity.toFixed(4)}</Descriptions.Item>
                <Descriptions.Item label="保证金">${selectedPosition.margin.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="杠杆">{selectedPosition.leverage}x</Descriptions.Item>
                <Descriptions.Item label="盈亏">
                  <Text style={{ 
                    color: selectedPosition.pnl >= 0 ? '#52c41a' : '#ff4d4f',
                    fontWeight: 'bold'
                  }}>
                    {selectedPosition.pnl >= 0 ? '+' : ''}${selectedPosition.pnl.toFixed(2)}
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="盈亏比例">
                  <Text style={{ 
                    color: selectedPosition.pnlPercent >= 0 ? '#52c41a' : '#ff4d4f'
                  }}>
                    {selectedPosition.pnlPercent >= 0 ? '+' : ''}{selectedPosition.pnlPercent.toFixed(2)}%
                  </Text>
                </Descriptions.Item>
                <Descriptions.Item label="收益率">
                  <Text style={{ 
                    color: (selectedPosition.pnl / selectedPosition.margin * 100) >= 0 ? '#52c41a' : '#ff4d4f'
                  }}>
                    {(selectedPosition.pnl / selectedPosition.margin * 100) >= 0 ? '+' : ''}
                    {(selectedPosition.pnl / selectedPosition.margin * 100).toFixed(2)}%
                  </Text>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default TradingManagement;