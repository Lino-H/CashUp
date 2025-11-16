/**
 * 策略管理页面 - 策略的创建、编辑、监控和管理
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress,
  Alert,
  Drawer,
  Typography,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  EyeOutlined,
  LineChartOutlined,
  BarChartOutlined,
  DollarCircleOutlined,
  RiseOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  FilterOutlined,
  TableOutlined,
  PieChartOutlined,
  BarChartOutlined as BarChartOutlined2,
  AreaChartOutlined as AreaChartOutlined2
} from '@ant-design/icons';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Scatter,
  ZAxis
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import { coreStrategyAPI, strategyAPI, handleApiError, Strategy } from '../services/api';
import { useDataCache } from '../hooks/useDataCache';
import { SmartLoading } from '../components/SmartLoading';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface StrategyFormData {
  name: string;
  description: string;
  type: string;
  symbol: string;
  timeframe: string;
  config: any;
  status: 'running' | 'stopped' | 'paused';
}

const StrategyManagement: React.FC = () => {
  const { isAuthenticated, apiCallWithRetry } = useAuth();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [performanceData, setPerformanceData] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [chartType, setChartType] = useState('line');
  const [realTimeData, setRealTimeData] = useState<any[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<number>(30);
  const [form] = Form.useForm();

  // 使用数据缓存
  const { data: cachedStrategies, getData: fetchStrategies } = useDataCache<Strategy[]>(
    'strategies',
    { ttl: 2 * 60 * 1000 } // 2分钟缓存
  );

  // 策略类型选项
  const strategyTypes = [
    { value: 'trend', label: '趋势策略' },
    { value: 'momentum', label: '动量策略' },
    { value: 'mean_reversion', label: '均值回归' },
    { value: 'breakout', label: '突破策略' },
    { value: 'arbitrage', label: '套利策略' },
    { value: 'grid', label: '网格策略' }
  ];

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
      setLoading(true);
      const resp = await coreStrategyAPI.listInstances('running', 1, 50);
      const items = (resp?.data?.items) || [];
      const mapped = items.map((it: any) => ({
        id: String(it.id),
        name: it.name,
        description: '',
        type: 'composite',
        symbol: it.symbol,
        timeframe: it.timeframe,
        status: it.status,
        config: it.config || {},
        performance: { totalPnl: 0, winRate: 0, tradesCount: 0, maxDrawdown: 0, sharpeRatio: 0 },
        createdAt: it.created_at || '',
        updatedAt: it.created_at || ''
      }));
      setStrategies(mapped);
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [fetchStrategies, apiCallWithRetry]);

  // 获取策略性能数据
  const loadPerformanceData = useCallback(async (strategyId: string) => {
    try {
      const data = await apiCallWithRetry(() => coreStrategyAPI.performance(Number(strategyId)));
      if (data) {
        // 生成模拟性能数据
        const mockData = Array.from({ length: 30 }, (_, i) => ({
          date: `Day ${i + 1}`,
          pnl: Math.random() * 1000 - 200,
          drawdown: Math.random() * 20,
          trades: Math.floor(Math.random() * 10) + 1,
          winRate: Math.random() * 100,
          volume: Math.random() * 100000,
          sharpe: Math.random() * 3
        }));
        setPerformanceData(mockData);
        
        // 生成实时数据
        const realTimeMockData = Array.from({ length: 20 }, (_, i) => ({
          time: `${new Date().getHours()}:${String(new Date().getMinutes() + i).padStart(2, '0')}`,
          price: 50000 + Math.random() * 2000,
          volume: Math.random() * 1000,
          orders: Math.random() > 0.5 ? 1 : 0
        }));
        setRealTimeData(realTimeMockData);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  }, [apiCallWithRetry]);

  // 实时数据更新
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        loadPerformanceData(selectedStrategy?.id || '');
      }, refreshInterval * 1000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, selectedStrategy?.id, loadPerformanceData]);

  // 数据导出功能
  const exportData = (type: 'csv' | 'json') => {
    const dataToExport = strategies.map(strategy => ({
      '策略名称': strategy.name,
      '类型': strategy.type,
      '交易对': strategy.symbol,
      '时间周期': strategy.timeframe,
      '状态': strategy.status,
      '收益率': strategy.performance?.totalPnl || 0,
      '胜率': strategy.performance?.winRate || 0,
      '交易次数': strategy.performance?.tradesCount || 0,
      '最大回撤': strategy.performance?.maxDrawdown || 0,
      '创建时间': strategy.createdAt,
      '更新时间': strategy.updatedAt
    }));

    if (type === 'csv') {
      const csvContent = [
        Object.keys(dataToExport[0]).join(','),
        ...dataToExport.map(row => Object.values(row).join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `strategies_${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
    } else {
      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `strategies_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
    }
    message.success(`数据导出成功！`);
  };

  // 初始化加载
  useEffect(() => {
    if (isAuthenticated) {
      loadStrategies();
    }
  }, [isAuthenticated, loadStrategies]);

  // 创建策略
  const handleCreate = async (values: StrategyFormData) => {
    try {
      const factors = Object.entries(factorConfig)
        .filter(([, cfg]: any) => cfg.enabled)
        .map(([name, cfg]: any) => ({ name, params: cfg.params }));
      const weights: any = {};
      Object.entries(factorConfig).forEach(([name, cfg]: any) => { if (cfg.enabled) weights[name] = cfg.weight; });
      const payload = {
        name: values.name,
        description: values.description,
        template_id: null,
        exchange: 'gateio',
        symbol: values.symbol.replace('/', '_'),
        timeframe: values.timeframe,
        config: {
          factors,
          combination: { mode: combinationMode, weights },
          risk_management: { max_position_size: 1, stop_loss: 0.02, take_profit: 0.03 }
        }
      };

      await apiCallWithRetry(() => coreStrategyAPI.createInstance(payload));
      message.success('策略创建成功');
      setModalVisible(false);
      form.resetFields();
      loadStrategies();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  };

  // 更新策略
  const handleUpdate = async (values: StrategyFormData) => {
    if (!editingStrategy) return;

    try {
      const strategyData = {
        ...values,
        config: JSON.stringify(values.config || {})
      };
      
      await apiCallWithRetry(() => strategyAPI.updateStrategy(editingStrategy.id, strategyData));
      message.success('策略更新成功');
      setModalVisible(false);
      form.resetFields();
      setEditingStrategy(null);
      loadStrategies();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  };

  // 删除策略
  const handleDelete = async (strategyId: string) => {
    try {
      await apiCallWithRetry(() => strategyAPI.deleteStrategy(strategyId));
      message.success('策略删除成功');
      loadStrategies();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  };

  // 启动策略
  const handleStart = async (strategyId: string) => {
    try {
      await apiCallWithRetry(() => coreStrategyAPI.startInstance(Number(strategyId)));
      message.success('策略启动成功');
      loadStrategies();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  };

  // 停止策略
  const handleStop = async (strategyId: string) => {
    try {
      await apiCallWithRetry(() => coreStrategyAPI.stopInstance(Number(strategyId)));
      message.success('策略停止成功');
      loadStrategies();
    } catch (error) {
      const errorMessage = handleApiError(error);
      message.error(errorMessage);
    }
  };

  // 查看策略详情
  const handleView = async (strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setDrawerVisible(true);
    setActiveTab('overview');
    await loadPerformanceData(strategy.id);
  };

  // 图表类型切换
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
              <Line type="monotone" dataKey="pnl" stroke="#8884d8" strokeWidth={2} />
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
              <Area type="monotone" dataKey="pnl" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.3} />
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
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={performanceData.slice(0, 5)}
                dataKey="trades"
                nameKey="date"
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                label
              />
              <RechartsTooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      case 'composed':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Area type="monotone" dataKey="pnl" fill="#8884d8" fillOpacity={0.3} />
              <Line type="monotone" dataKey="winRate" stroke="#ff7300" />
            </ComposedChart>
          </ResponsiveContainer>
        );
      default:
        return null;
    }
  };

  // 胜率趋势数据
  const winrateData = performanceData.map((d: any) => ({ date: d.date, winRate: d.winRate }));

  // 编辑策略
  const handleEdit = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    form.setFieldsValue({
      ...strategy,
      config: strategy.config || {}
    });
    setModalVisible(true);
  };

  // 表格列定义
  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Strategy) => (
        <Space>
          <Text strong>{text}</Text>
          <Badge 
            status={record.status === 'running' ? 'success' : record.status === 'stopped' ? 'error' : 'warning'}
            text={record.status === 'running' ? '运行中' : record.status === 'stopped' ? '已停止' : '暂停'}
          />
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap: { [key: string]: string } = {
          'trend': '趋势策略',
          'momentum': '动量策略',
          'mean_reversion': '均值回归',
          'breakout': '突破策略',
          'arbitrage': '套利策略',
          'grid': '网格策略'
        };
        return <Tag color="blue">{typeMap[type] || type}</Tag>;
      }
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
      render: (timeframe: string) => <Tag color="orange">{timeframe}</Tag>
    },
    {
      title: '收益率',
      dataIndex: 'performance',
      key: 'pnl',
      render: (performance: any) => {
        const pnl = performance?.totalPnl || 0;
        const winRate = performance?.winRate || 0;
        return (
          <div>
            <Text style={{ color: pnl >= 0 ? '#52c41a' : '#f5222d', fontWeight: 'bold' }}>
              {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}%
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              胜率: {winRate.toFixed(1)}%
            </Text>
          </div>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (text: any, record: Strategy) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="link" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {record.status === 'running' ? (
            <Tooltip title="停止">
              <Button 
                type="link" 
                danger 
                icon={<PauseCircleOutlined />} 
                onClick={() => handleStop(record.id)}
              />
            </Tooltip>
          ) : (
            <Tooltip title="启动">
              <Button 
                type="link" 
                icon={<PlayCircleOutlined />} 
                onClick={() => handleStart(record.id)}
              />
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Popconfirm
              title="确定删除此策略？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />} 
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  // 策略统计信息
  const stats = {
    total: strategies.length,
    running: strategies.filter(s => s.status === 'running').length,
    stopped: strategies.filter(s => s.status === 'stopped').length,
    paused: strategies.filter(s => s.status === 'paused').length,
    totalPnl: strategies.reduce((sum, s) => sum + (s.performance?.totalPnl || 0), 0),
    avgWinRate: strategies.length > 0 
      ? strategies.reduce((sum, s) => sum + (s.performance?.winRate || 0), 0) / strategies.length 
      : 0
  };

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总策略数"
              value={stats.total}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="运行中"
              value={stats.running}
              valueStyle={{ color: '#3f8600' }}
              prefix={<PlayCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总收益率"
              value={stats.totalPnl}
              precision={2}
              valueStyle={{ color: stats.totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
              prefix={<RiseOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均胜率"
              value={stats.avgWinRate}
              precision={1}
              valueStyle={{ color: '#3f8600' }}
              prefix={<LineChartOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="策略管理"
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
              icon={<DownloadOutlined />}
              onClick={() => exportData('csv')}
            >
              导出CSV
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={() => exportData('json')}
            >
              导出JSON
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => {
                setEditingStrategy(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              创建策略
            </Button>
          </Space>
        }
      >
        <SmartLoading
          loading={loading}
          error={null}
          data={strategies}
          skeletonVariant="table"
          skeletonLines={8}
        >
          <Table
            columns={columns}
            dataSource={strategies}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }}
          />
        </SmartLoading>
      </Card>

      {/* 创建/编辑策略弹窗 */}
      <Modal
        title={editingStrategy ? '编辑策略' : '创建策略'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingStrategy(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
      <Form
        form={form}
        layout="vertical"
        onFinish={editingStrategy ? handleUpdate : handleCreate}
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
                <Select placeholder="选择策略类型">
                  {strategyTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
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
          </Row>

          <Form.Item
            label="策略描述"
            name="description"
            rules={[{ required: true, message: '请输入策略描述' }]}
          >
            <TextArea rows={3} placeholder="输入策略描述" />
          </Form.Item>

          <Form.Item
            label="初始状态"
            name="status"
            initialValue="stopped"
          >
            <Select>
              <Option value="stopped">已停止</Option>
              <Option value="running">运行中</Option>
              <Option value="paused">暂停</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingStrategy ? '更新策略' : '创建策略'}
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingStrategy(null);
                form.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 策略详情抽屉 */}
      <Drawer
        title="策略详情"
        placement="right"
        onClose={() => {
          setDrawerVisible(false);
          setSelectedStrategy(null);
        }}
        open={drawerVisible}
        width={1000}
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
                onChange={(v) => setRefreshInterval(v ?? refreshInterval)}
                addonAfter="秒"
                style={{ width: 100 }}
              />
            )}
            <Button 
              icon={<DownloadOutlined />}
              onClick={() => exportData('csv')}
            >
              导出数据
            </Button>
          </Space>
        }
      >
        {selectedStrategy && (
          <div>
            <Tabs 
              activeKey={activeTab} 
              onChange={setActiveTab}
              items={[
                {
                  key: 'overview',
                  label: '概览',
                  children: (
                    <div>
                      <Row gutter={16} style={{ marginBottom: '24px' }}>
                        <Col span={12}>
                          <Statistic
                            title="总收益率"
                            value={selectedStrategy.performance?.totalPnl || 0}
                            precision={2}
                            valueStyle={{ 
                              color: (selectedStrategy.performance?.totalPnl || 0) >= 0 ? '#3f8600' : '#cf1322' 
                            }}
                            suffix="%"
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic
                            title="胜率"
                            value={selectedStrategy.performance?.winRate || 0}
                            precision={1}
                            valueStyle={{ color: '#3f8600' }}
                            suffix="%"
                          />
                        </Col>
                      </Row>

                      <Row gutter={16} style={{ marginBottom: '24px' }}>
                        <Col span={12}>
                          <Statistic
                            title="交易次数"
                            value={selectedStrategy.performance?.tradesCount || 0}
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic
                            title="最大回撤"
                            value={selectedStrategy.performance?.maxDrawdown || 0}
                            precision={2}
                            valueStyle={{ color: '#cf1322' }}
                            suffix="%"
                          />
                        </Col>
                      </Row>

                      <Row gutter={16} style={{ marginBottom: '24px' }}>
                        <Col span={12}>
                          <Statistic
                            title="夏普比率"
                            value={selectedStrategy.performance?.sharpeRatio || 0}
                            precision={2}
                            valueStyle={{ color: '#3f8600' }}
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic
                            title="平均交易量"
                            value={realTimeData.length > 0 ? Number((realTimeData.reduce((sum, d) => sum + (d.volume || 0), 0) / realTimeData.length).toFixed(0)) : 0}
                            precision={0}
                            valueStyle={{ color: '#3f8600' }}
                          />
                        </Col>
                      </Row>
                    </div>
                  )
                },
                {
                  key: 'charts',
                  label: '图表分析',
                  children: (
                    <div>
                      <Row gutter={16} style={{ marginBottom: '16px' }}>
                        <Col span={24}>
                          <Space>
                            <Button 
                              type={chartType === 'line' ? 'primary' : 'default'}
                              icon={<LineChartOutlined />}
                              onClick={() => setChartType('line')}
                            >
                              折线图
                            </Button>
                            <Button 
                              type={chartType === 'area' ? 'primary' : 'default'}
                              icon={<AreaChartOutlined2 />}
                              onClick={() => setChartType('area')}
                            >
                              面积图
                            </Button>
                            <Button 
                              type={chartType === 'bar' ? 'primary' : 'default'}
                              icon={<BarChartOutlined2 />}
                              onClick={() => setChartType('bar')}
                            >
                              柱状图
                            </Button>
                            <Button 
                              type={chartType === 'composed' ? 'primary' : 'default'}
                              icon={<BarChartOutlined />}
                              onClick={() => setChartType('composed')}
                            >
                              胜率趋势
                            </Button>
                          </Space>
                        </Col>
                      </Row>
                      <div style={{ height: 400, marginBottom: '24px' }}>
                        {chartType === 'composed' ? (
                          <ResponsiveContainer width="100%" height={300}>
                            <ComposedChart data={winrateData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="date" />
                              <YAxis />
                              <RechartsTooltip />
                              <Line type="monotone" dataKey="winRate" stroke="#ff7300" />
                            </ComposedChart>
                          </ResponsiveContainer>
                        ) : renderChart(chartType)}
                      </div>
                    </div>
                  )
                },
                {
                  key: 'realtime',
                  label: '实时数据',
                  children: (
                    <div>
                      <Row gutter={16} style={{ marginBottom: '24px' }}>
                        <Col span={24}>
                          <Card title="实时价格走势">
                            <ResponsiveContainer width="100%" height={200}>
                              <AreaChart data={realTimeData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="time" />
                                <YAxis />
                                <RechartsTooltip />
                                <Area 
                                  type="monotone" 
                                  dataKey="price" 
                                  stroke="#8884d8" 
                                  fill="#8884d8" 
                                  fillOpacity={0.3}
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </Card>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={12}>
                          <Card title="实时交易量">
                            <Statistic
                              value={realTimeData[realTimeData.length - 1]?.volume || 0}
                              precision={0}
                            />
                          </Card>
                        </Col>
                        <Col span={12}>
                          <Card title="当前订单">
                            <Statistic
                              value={realTimeData[realTimeData.length - 1]?.orders || 0}
                              suffix="个"
                            />
                          </Card>
                        </Col>
                      </Row>
                    </div>
                  )
                },
                {
                  key: 'info',
                  label: '策略信息',
                  children: (
                    <div>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text><strong>策略名称:</strong> {selectedStrategy.name}</Text>
                        <Text><strong>策略类型:</strong> {selectedStrategy.type}</Text>
                        <Text><strong>交易对:</strong> {selectedStrategy.symbol}</Text>
                        <Text><strong>时间周期:</strong> {selectedStrategy.timeframe}</Text>
                        <Text><strong>状态:</strong> 
                          <Badge 
                            status={selectedStrategy.status === 'running' ? 'success' : selectedStrategy.status === 'stopped' ? 'error' : 'warning'}
                            text={selectedStrategy.status === 'running' ? '运行中' : selectedStrategy.status === 'stopped' ? '已停止' : '暂停'}
                            style={{ marginLeft: 8 }}
                          />
                        </Text>
                        <Text><strong>创建时间:</strong> {selectedStrategy.createdAt}</Text>
                        <Text><strong>更新时间:</strong> {selectedStrategy.updatedAt}</Text>
                        <Text><strong>策略描述:</strong> {selectedStrategy.description}</Text>
                      </Space>
                    </div>
                  )
                }
              ]}
            />
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default StrategyManagement;
  const [factorConfig, setFactorConfig] = useState({
    rsi: { enabled: true, weight: 1.0, params: { period: 14, overbought: 70, oversold: 30 } },
    ma: { enabled: true, weight: 1.0, params: { period: 20 } },
    macd: { enabled: false, weight: 1.0, params: { fast: 12, slow: 26, signal: 9 } },
    ema: { enabled: false, weight: 1.0, params: { period: 20 } },
    boll: { enabled: false, weight: 1.0, params: { period: 20, mult: 2.0 } },
  });
  const [combinationMode, setCombinationMode] = useState<'weighted' | 'vote'>('weighted');
          <Row gutter={16}>
            <Col span={24}>
              <Card title="因子与组合配置" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Space>
                    <Switch checked={factorConfig.rsi.enabled} onChange={(v) => setFactorConfig({ ...factorConfig, rsi: { ...factorConfig.rsi, enabled: v } })} />
                    <Text>RSI 权重</Text>
                    <InputNumber min={0} max={2} step={0.1} value={factorConfig.rsi.weight} onChange={(v) => setFactorConfig({ ...factorConfig, rsi: { ...factorConfig.rsi, weight: Number(v) } })} />
                  </Space>
                  <Space>
                    <Switch checked={factorConfig.ma.enabled} onChange={(v) => setFactorConfig({ ...factorConfig, ma: { ...factorConfig.ma, enabled: v } })} />
                    <Text>MA 权重</Text>
                    <InputNumber min={0} max={2} step={0.1} value={factorConfig.ma.weight} onChange={(v) => setFactorConfig({ ...factorConfig, ma: { ...factorConfig.ma, weight: Number(v) } })} />
                  </Space>
                  <Space>
                    <Switch checked={factorConfig.macd.enabled} onChange={(v) => setFactorConfig({ ...factorConfig, macd: { ...factorConfig.macd, enabled: v } })} />
                    <Text>MACD 权重</Text>
                    <InputNumber min={0} max={2} step={0.1} value={factorConfig.macd.weight} onChange={(v) => setFactorConfig({ ...factorConfig, macd: { ...factorConfig.macd, weight: Number(v) } })} />
                  </Space>
                  <Space>
                    <Switch checked={factorConfig.ema.enabled} onChange={(v) => setFactorConfig({ ...factorConfig, ema: { ...factorConfig.ema, enabled: v } })} />
                    <Text>EMA 权重</Text>
                    <InputNumber min={0} max={2} step={0.1} value={factorConfig.ema.weight} onChange={(v) => setFactorConfig({ ...factorConfig, ema: { ...factorConfig.ema, weight: Number(v) } })} />
                  </Space>
                  <Space>
                    <Switch checked={factorConfig.boll.enabled} onChange={(v) => setFactorConfig({ ...factorConfig, boll: { ...factorConfig.boll, enabled: v } })} />
                    <Text>BOLL 权重</Text>
                    <InputNumber min={0} max={2} step={0.1} value={factorConfig.boll.weight} onChange={(v) => setFactorConfig({ ...factorConfig, boll: { ...factorConfig.boll, weight: Number(v) } })} />
                  </Space>
                  <Space>
                    <Text>组合模式</Text>
                    <Select value={combinationMode} onChange={(v) => setCombinationMode(v)} style={{ width: 200 }}>
                      <Option value="weighted">加权</Option>
                      <Option value="vote">投票</Option>
                    </Select>
                  </Space>
                </Space>
              </Card>
            </Col>
          </Row>