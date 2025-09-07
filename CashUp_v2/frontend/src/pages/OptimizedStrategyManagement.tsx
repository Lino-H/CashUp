/**
 * 优化后的策略管理页面 - useCallback优化版本
 * Optimized Strategy Management Page - useCallback Optimized Version
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  InputNumber,
  Switch,
  Divider,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Progress,
  Badge,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { 
  strategyAPI, 
  Strategy, 
  StrategyPerformance 
} from '../services/api';
import { dataCache } from '../utils/cache';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// 策略性能卡片组件
const StrategyPerformanceCard: React.FC<{ performance: StrategyPerformance }> = React.memo(({ performance }) => {
  const winRate = performance.winRate.toFixed(1);
  const maxDrawdown = Math.abs(performance.maxDrawdown).toFixed(2);

  return (
    <Row gutter={16}>
      <Col span={6}>
        <div style={{ fontSize: 12, color: '#666' }}>胜率</div>
        <div style={{ color: parseFloat(winRate) >= 50 ? '#3f8600' : '#cf1322' }}>
          {winRate}%
        </div>
      </Col>
      <Col span={6}>
        <div style={{ fontSize: 12, color: '#666' }}>交易次数</div>
        <div>{performance.tradesCount}</div>
      </Col>
      <Col span={6}>
        <div style={{ fontSize: 12, color: '#666' }}>最大回撤</div>
        <div style={{ color: parseFloat(maxDrawdown) > 5 ? '#cf1322' : '#3f8600' }}>
          {maxDrawdown}%
        </div>
      </Col>
      <Col span={6}>
        <div style={{ fontSize: 12, color: '#666' }}>夏普比率</div>
        <div>{performance.sharpeRatio.toFixed(2)}</div>
      </Col>
    </Row>
  );
});

StrategyPerformanceCard.displayName = 'StrategyPerformanceCard';

// 策略状态标签组件
const StrategyStatusTag: React.FC<{ status: string }> = React.memo(({ status }) => {
  const statusConfig = {
    running: { color: 'green', text: '运行中' },
    stopped: { color: 'red', text: '已停止' },
    error: { color: 'orange', text: '错误' },
    paused: { color: 'orange', text: '暂停' },
    created: { color: 'blue', text: '已创建' },
    backtesting: { color: 'purple', text: '回测中' },
  };

  const config = statusConfig[status as keyof typeof statusConfig];
  return <Tag color={config.color}>{config.text}</Tag>;
});

StrategyStatusTag.displayName = 'StrategyStatusTag';

// 策略操作按钮组件
const StrategyActionButtons: React.FC<{
  strategy: Strategy;
  onEdit: (strategy: Strategy) => void;
  onDelete: (id: string) => void;
  onStart: (id: string) => void;
  onStop: (id: string) => void;
  onReload: (id: string) => void;
}> = React.memo(({ strategy, onEdit, onDelete, onStart, onStop, onReload }) => {
  const getActionButtons = () => {
    switch (strategy.status) {
      case 'running':
        return (
          <Space>
            <Button
              icon={<PauseCircleOutlined />}
              onClick={() => onStop(strategy.id)}
              size="small"
            >
              停止
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => onReload(strategy.id)}
              size="small"
            >
              重载
            </Button>
            <Button
              icon={<EditOutlined />}
              onClick={() => onEdit(strategy)}
              size="small"
            >
              编辑
            </Button>
            <Popconfirm
              title="确定要删除这个策略吗？"
              onConfirm={() => onDelete(strategy.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                icon={<DeleteOutlined />}
                danger
                size="small"
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
      case 'stopped':
        return (
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => onStart(strategy.id)}
              size="small"
            >
              启动
            </Button>
            <Button
              icon={<EditOutlined />}
              onClick={() => onEdit(strategy)}
              size="small"
            >
              编辑
            </Button>
            <Popconfirm
              title="确定要删除这个策略吗？"
              onConfirm={() => onDelete(strategy.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                icon={<DeleteOutlined />}
                danger
                size="small"
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
      case 'error':
        return (
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => onReload(strategy.id)}
              size="small"
            >
              重载
            </Button>
            <Button
              icon={<DeleteOutlined />}
              danger
              onClick={() => onDelete(strategy.id)}
              size="small"
            >
              删除
            </Button>
          </Space>
        );
      default:
        return (
          <Space>
            <Button
              icon={<EditOutlined />}
              onClick={() => onEdit(strategy)}
              size="small"
            >
              编辑
            </Button>
            <Popconfirm
              title="确定要删除这个策略吗？"
              onConfirm={() => onDelete(strategy.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                icon={<DeleteOutlined />}
                danger
                size="small"
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
    }
  };

  return <Space size="small">{getActionButtons()}</Space>;
});

StrategyActionButtons.displayName = 'StrategyActionButtons';

// 优化后的策略管理组件
const OptimizedStrategyManagement: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  // 使用 useMemo 缓存计算数据
  const statistics = useMemo(() => ({
    totalStrategies: strategies.length,
    runningStrategies: strategies.filter(s => s.status === 'running').length,
    stoppedStrategies: strategies.filter(s => s.status === 'stopped').length,
    errorStrategies: strategies.filter(s => s.status === 'error').length,
    totalPnl: strategies.reduce((sum, s) => sum + (s.performance?.totalPnl || 0), 0),
    averageWinRate: strategies.length > 0 
      ? strategies.reduce((sum, s) => sum + (s.performance?.winRate || 0), 0) / strategies.length 
      : 0,
  }), [strategies]);

  // 使用 useMemo 缓存表格列定义
  const columns = useMemo(() => [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Strategy) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name}</div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {record.symbol} | {record.timeframe}
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <StrategyStatusTag status={status} />,
    },
    {
      title: '盈亏',
      dataIndex: 'performance',
      key: 'performance',
      render: (performance: StrategyPerformance) => (
        <div>
          <div style={{ 
            color: performance?.totalPnl >= 0 ? '#3f8600' : '#cf1322',
            fontWeight: 'bold'
          }}>
            {performance?.totalPnl ? `$${performance.totalPnl.toFixed(2)}` : '$0.00'}
          </div>
          <div style={{ fontSize: 12, color: '#666' }}>
            {performance?.winRate ? `${performance.winRate.toFixed(1)}%` : '0%'}
          </div>
        </div>
      ),
      sorter: (a, b) => (a.performance?.totalPnl || 0) - (b.performance?.totalPnl || 0),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: Strategy) => (
        <StrategyActionButtons
          strategy={record}
          onEdit={handleEditStrategy}
          onDelete={handleDeleteStrategy}
          onStart={handleStartStrategy}
          onStop={handleStopStrategy}
          onReload={handleReloadStrategy}
        />
      ),
    },
  ], []);

  // 使用 useCallback 缓存 API 调用函数
  const fetchStrategies = useCallback(async () => {
    setLoading(true);
    try {
      const response = await dataCache.fetchWithCache(
        'strategies',
        async () => {
          const apiResponse = await strategyAPI.getStrategies();
          return apiResponse.strategies || [];
        },
        { ttl: 2 * 60 * 1000 } // 2分钟缓存
      );
      
      setStrategies(response);
    } catch (error) {
      message.error('获取策略列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleCreateStrategy = useCallback(async (values: any) => {
    try {
      await strategyAPI.createStrategy(values);
      message.success('策略创建成功');
      setCreateModalVisible(false);
      createForm.resetFields();
      await fetchStrategies();
    } catch (error) {
      message.error('策略创建失败');
    }
  }, [createForm, fetchStrategies]);

  const handleEditStrategy = useCallback((strategy: Strategy) => {
    setEditingStrategy(strategy);
    editForm.setFieldsValue(strategy);
    setEditModalVisible(true);
  }, [editForm]);

  const handleUpdateStrategy = useCallback(async (values: any) => {
    if (!editingStrategy) return;

    try {
      await strategyAPI.updateStrategy(editingStrategy.id, values);
      message.success('策略更新成功');
      setEditModalVisible(false);
      setEditingStrategy(null);
      editForm.resetFields();
      await fetchStrategies();
    } catch (error) {
      message.error('策略更新失败');
    }
  }, [editingStrategy, editForm, fetchStrategies]);

  const handleDeleteStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.deleteStrategy(id);
      message.success('策略删除成功');
      await fetchStrategies();
    } catch (error) {
      message.error('策略删除失败');
    }
  }, [fetchStrategies]);

  const handleStartStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.startStrategy(id);
      message.success('策略启动成功');
      await fetchStrategies();
    } catch (error) {
      message.error('策略启动失败');
    }
  }, [fetchStrategies]);

  const handleStopStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.stopStrategy(id);
      message.success('策略停止成功');
      await fetchStrategies();
    } catch (error) {
      message.error('策略停止失败');
    }
  }, [fetchStrategies]);

  const handleReloadStrategy = useCallback(async (id: string) => {
    try {
      await strategyAPI.reloadStrategy(id);
      message.success('策略重载成功');
      await fetchStrategies();
    } catch (error) {
      message.error('策略重载失败');
    }
  }, [fetchStrategies]);

  // 初始化加载
  useEffect(() => {
    fetchStrategies();
  }, [fetchStrategies]);

  return (
    <div style={{ padding: 24 }}>
      {/* 统计概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总策略数" value={statistics.totalStrategies} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="运行中" 
              value={statistics.runningStrategies}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="已停止" 
              value={statistics.stoppedStrategies}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="总盈亏" 
              value={statistics.totalPnl}
              precision={2}
              prefix="$"
              valueStyle={{ 
                color: statistics.totalPnl >= 0 ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作区域 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Title level={2}>策略管理</Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            创建策略
          </Button>
        </Col>
      </Row>

      {/* 策略列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={strategies}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
          scroll={{ x: 1200 }}
          bordered
        />
      </Card>

      {/* 创建策略模态框 */}
      <Modal
        title="创建策略"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateStrategy}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="策略名称"
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input placeholder="输入策略名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="symbol"
                label="交易对"
                rules={[{ required: true, message: '请选择交易对' }]}
              >
                <Select placeholder="选择交易对">
                  <Option value="BTCUSDT">BTC/USDT</Option>
                  <Option value="ETHUSDT">ETH/USDT</Option>
                  <Option value="BNBUSDT">BNB/USDT</Option>
                  <Option value="ADAUSDT">ADA/USDT</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="timeframe"
                label="时间周期"
                rules={[{ required: true, message: '请选择时间周期' }]}
              >
                <Select placeholder="选择时间周期">
                  <Option value="1m">1分钟</Option>
                  <Option value="5m">5分钟</Option>
                  <Option value="15m">15分钟</Option>
                  <Option value="1h">1小时</Option>
                  <Option value="4h">4小时</Option>
                  <Option value="1d">1天</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="type"
                label="策略类型"
                rules={[{ required: true, message: '请选择策略类型' }]}
              >
                <Select placeholder="选择策略类型">
                  <Option value="trend">趋势跟踪</Option>
                  <Option value="mean_reversion">均值回归</Option>
                  <Option value="breakout">突破策略</Option>
                  <Option value="arbitrage">套利策略</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="config"
            label="策略配置"
            rules={[{ required: true, message: '请输入策略配置' }]}
          >
            <TextArea 
              rows={4} 
              placeholder="输入JSON格式的策略配置"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建策略
              </Button>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑策略模态框 */}
      <Modal
        title="编辑策略"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingStrategy(null);
          editForm.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleUpdateStrategy}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="策略名称"
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input placeholder="输入策略名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="symbol"
                label="交易对"
                rules={[{ required: true, message: '请选择交易对' }]}
              >
                <Select placeholder="选择交易对">
                  <Option value="BTCUSDT">BTC/USDT</Option>
                  <Option value="ETHUSDT">ETH/USDT</Option>
                  <Option value="BNBUSDT">BNB/USDT</Option>
                  <Option value="ADAUSDT">ADA/USDT</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="timeframe"
                label="时间周期"
                rules={[{ required: true, message: '请选择时间周期' }]}
              >
                <Select placeholder="选择时间周期">
                  <Option value="1m">1分钟</Option>
                  <Option value="5m">5分钟</Option>
                  <Option value="15m">15分钟</Option>
                  <Option value="1h">1小时</Option>
                  <Option value="4h">4小时</Option>
                  <Option value="1d">1天</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="type"
                label="策略类型"
                rules={[{ required: true, message: '请选择策略类型' }]}
              >
                <Select placeholder="选择策略类型">
                  <Option value="trend">趋势跟踪</Option>
                  <Option value="mean_reversion">均值回归</Option>
                  <Option value="breakout">突破策略</Option>
                  <Option value="arbitrage">套利策略</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="config"
            label="策略配置"
            rules={[{ required: true, message: '请输入策略配置' }]}
          >
            <TextArea 
              rows={4} 
              placeholder="输入JSON格式的策略配置"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                更新策略
              </Button>
              <Button onClick={() => {
                setEditModalVisible(false);
                setEditingStrategy(null);
                editForm.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OptimizedStrategyManagement;