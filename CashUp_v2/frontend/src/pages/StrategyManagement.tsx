/**
 * 策略管理界面组件
 */

import React, { useState, useEffect } from 'react';
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
  message,
  Popconfirm,
  Tabs,
  Row,
  Col,
  Statistic,
  Progress,
  Badge,
  Tooltip,
  Typography,
  Drawer
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  EyeOutlined,
  UploadOutlined,
  DownloadOutlined,
  LineChartOutlined,
  DollarOutlined,
  TrophyOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import ReactMarkdown from 'react-markdown';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface Strategy {
  id: number;
  name: string;
  description: string;
  type: string;
  code: string;
  status: 'draft' | 'running' | 'stopped' | 'error';
  createdAt: string;
  updatedAt: string;
  performance?: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
  };
  config?: Record<string, any>;
}

interface StrategyFormData {
  name: string;
  description: string;
  type: string;
  code: string;
  config?: Record<string, any>;
}

const StrategyManagement: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | null>(null);
  const [viewingStrategy, setViewingStrategy] = useState<Strategy | null>(null);
  const [form] = Form.useForm<StrategyFormData>();
  const [activeTab, setActiveTab] = useState('list');

  // 模拟数据
  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockStrategies: Strategy[] = [
        {
          id: 1,
          name: '均线交叉策略',
          description: '基于短期和长期均线交叉的交易策略',
          type: 'trend',
          code: `def strategy(data):
    short_ma = data['close'].rolling(window=20).mean()
    long_ma = data['close'].rolling(window=60).mean()
    
    signals = []
    for i in range(1, len(data)):
        if short_ma[i] > long_ma[i] and short_ma[i-1] <= long_ma[i-1]:
            signals.append({'action': 'buy', 'price': data['close'][i]})
        elif short_ma[i] < long_ma[i] and short_ma[i-1] >= long_ma[i-1]:
            signals.append({'action': 'sell', 'price': data['close'][i]})
    
    return signals`,
          status: 'running',
          createdAt: '2024-01-15',
          updatedAt: '2024-01-20',
          performance: {
            totalReturn: 15.3,
            sharpeRatio: 1.8,
            maxDrawdown: -8.2,
            winRate: 62.5,
            profitFactor: 2.1
          },
          config: {
            short_window: 20,
            long_window: 60,
            stop_loss: 0.05,
            take_profit: 0.1
          }
        },
        {
          id: 2,
          name: 'RSI超卖策略',
          description: '基于RSI指标的超卖反转策略',
          type: 'mean_reversion',
          code: `def strategy(data):
    rsi = calculate_rsi(data['close'], period=14)
    
    signals = []
    for i in range(1, len(data)):
        if rsi[i] < 30 and rsi[i-1] >= 30:
            signals.append({'action': 'buy', 'price': data['close'][i]})
        elif rsi[i] > 70 and rsi[i-1] <= 70:
            signals.append({'action': 'sell', 'price': data['close'][i]})
    
    return signals`,
          status: 'draft',
          createdAt: '2024-01-18',
          updatedAt: '2024-01-18'
        },
        {
          id: 3,
          name: '网格交易策略',
          description: '在价格区间内进行网格交易的策略',
          type: 'grid',
          code: `def strategy(data):
    price = data['close'][-1]
    grid_spacing = 0.01  # 1% grid spacing
    grid_levels = []
    
    # 生成网格价位
    for i in range(-10, 11):
        grid_levels.append(price * (1 + i * grid_spacing))
    
    signals = []
    for level in grid_levels:
        if price <= level * (1 - grid_spacing/2):
            signals.append({'action': 'buy', 'price': level})
        elif price >= level * (1 + grid_spacing/2):
            signals.append({'action': 'sell', 'price': level})
    
    return signals`,
          status: 'stopped',
          createdAt: '2024-01-10',
          updatedAt: '2024-01-12',
          performance: {
            totalReturn: 8.7,
            sharpeRatio: 1.2,
            maxDrawdown: -5.1,
            winRate: 58.3,
            profitFactor: 1.5
          }
        }
      ];
      
      setStrategies(mockStrategies);
    } catch (error) {
      message.error('加载策略失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingStrategy(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    form.setFieldsValue({
      name: strategy.name,
      description: strategy.description,
      type: strategy.type,
      code: strategy.code,
      config: strategy.config
    });
    setModalVisible(true);
  };

  const handleView = (strategy: Strategy) => {
    setViewingStrategy(strategy);
    setDrawerVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setStrategies(strategies.filter(s => s.id !== id));
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleStartStop = async (id: number, action: 'start' | 'stop') => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setStrategies(strategies.map(s => 
        s.id === id 
          ? { ...s, status: action === 'start' ? 'running' : 'stopped' }
          : s
      ));
      message.success(action === 'start' ? '策略已启动' : '策略已停止');
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleSubmit = async (values: StrategyFormData) => {
    try {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const newStrategy: Strategy = {
        id: editingStrategy ? editingStrategy.id : Date.now(),
        ...values,
        status: 'draft',
        createdAt: editingStrategy ? editingStrategy.createdAt : new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      if (editingStrategy) {
        setStrategies(strategies.map(s => s.id === editingStrategy.id ? newStrategy : s));
        message.success('更新成功');
      } else {
        setStrategies([...strategies, newStrategy]);
        message.success('创建成功');
      }
      
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: Strategy['status']) => {
    const statusConfig = {
      draft: { color: 'default', text: '草稿' },
      running: { color: 'processing', text: '运行中' },
      stopped: { color: 'warning', text: '已停止' },
      error: { color: 'error', text: '错误' }
    };
    
    const config = statusConfig[status];
    return <Badge status={config.color as any} text={config.text} />;
  };

  const getTypeTag = (type: string) => {
    const typeConfig: Record<string, { color: string; label: string }> = {
      trend: { color: 'blue', label: '趋势' },
      mean_reversion: { color: 'green', label: '均值回归' },
      grid: { color: 'orange', label: '网格' },
      arbitrage: { color: 'purple', label: '套利' },
      momentum: { color: 'red', label: '动量' }
    };
    
    const config = typeConfig[type] || { color: 'default', label: type };
    return <Tag color={config.color as any}>{config.label}</Tag>;
  };

  const columns: ColumnsType<Strategy> = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Strategy) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.description}
          </Text>
        </Space>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => getTypeTag(type),
      width: 100
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: Strategy['status']) => getStatusBadge(status),
      width: 100
    },
    {
      title: '性能指标',
      key: 'performance',
      render: (_, record: Strategy) => {
        if (!record.performance) return <Text type="secondary">暂无数据</Text>;
        
        const { totalReturn, sharpeRatio, maxDrawdown, winRate } = record.performance;
        
        return (
          <Space direction="vertical" size="small">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="收益率"
                  value={totalReturn}
                  suffix="%"
                  valueStyle={{ fontSize: '12px' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="夏普比率"
                  value={sharpeRatio}
                  precision={2}
                  valueStyle={{ fontSize: '12px' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="最大回撤"
                  value={maxDrawdown}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: '12px', color: maxDrawdown < -10 ? '#ff4d4f' : '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="胜率"
                  value={winRate}
                  suffix="%"
                  precision={1}
                  valueStyle={{ fontSize: '12px' }}
                />
              </Col>
            </Row>
          </Space>
        );
      },
      width: 300
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      render: (text: string) => new Date(text).toLocaleDateString(),
      width: 120
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Strategy) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          
          {record.status === 'running' ? (
            <Tooltip title="停止">
              <Popconfirm
                title="确定要停止这个策略吗？"
                onConfirm={() => handleStartStop(record.id, 'stop')}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="text"
                  icon={<PauseCircleOutlined />}
                  danger
                />
              </Popconfirm>
            </Tooltip>
          ) : (
            <Tooltip title="启动">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => handleStartStop(record.id, 'start')}
              />
            </Tooltip>
          )}
          
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个策略吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                icon={<DeleteOutlined />}
                danger
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
      width: 200,
      fixed: 'right' as const
    }
  ];

  const strategyTypes = [
    { value: 'trend', label: '趋势策略' },
    { value: 'mean_reversion', label: '均值回归' },
    { value: 'grid', label: '网格策略' },
    { value: 'arbitrage', label: '套利策略' },
    { value: 'momentum', label: '动量策略' }
  ];

  const renderOverview = () => {
    const totalStrategies = strategies.length;
    const runningStrategies = strategies.filter(s => s.status === 'running').length;
    const totalReturn = strategies.reduce((sum, s) => sum + (s.performance?.totalReturn || 0), 0);
    const avgSharpeRatio = strategies.length > 0 
      ? strategies.reduce((sum, s) => sum + (s.performance?.sharpeRatio || 0), 0) / strategies.length 
      : 0;

    return (
      <div style={{ padding: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <Card>
              <Statistic
                title="总策略数"
                value={totalStrategies}
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行中"
                value={runningStrategies}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总收益率"
                value={totalReturn}
                suffix="%"
                precision={1}
                prefix={<DollarOutlined />}
                valueStyle={{ color: totalReturn > 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均夏普比率"
                value={avgSharpeRatio}
                precision={2}
                prefix={<LineChartOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
          <Col span={12}>
            <Card title="策略类型分布">
              <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Text type="secondary">策略类型图表占位</Text>
              </div>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="性能排行">
              <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Text type="secondary">性能排行图表占位</Text>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="策略概览" key="overview">
            {renderOverview()}
          </TabPane>
          <TabPane tab="策略列表" key="list">
            <div style={{ marginBottom: '16px' }}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreate}
                >
                  新建策略
                </Button>
                <Button icon={<UploadOutlined />}>
                  导入策略
                </Button>
                <Button icon={<DownloadOutlined />}>
                  导出策略
                </Button>
              </Space>
            </div>
            
            <Table
              columns={columns}
              dataSource={strategies}
              rowKey="id"
              loading={loading}
              scroll={{ x: 1200 }}
              pagination={{
                total: strategies.length,
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
            />
          </TabPane>
        </Tabs>
      </Card>

      <Modal
        title={editingStrategy ? '编辑策略' : '新建策略'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
        >
          <Form.Item
            name="name"
            label="策略名称"
            rules={[{ required: true, message: '请输入策略名称' }]}
          >
            <Input placeholder="请输入策略名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="策略描述"
            rules={[{ required: true, message: '请输入策略描述' }]}
          >
            <Input.TextArea rows={3} placeholder="请输入策略描述" />
          </Form.Item>

          <Form.Item
            name="type"
            label="策略类型"
            rules={[{ required: true, message: '请选择策略类型' }]}
          >
            <Select placeholder="请选择策略类型">
              {strategyTypes.map(type => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="code"
            label="策略代码"
            rules={[{ required: true, message: '请输入策略代码' }]}
          >
            <Input.TextArea
              rows={10}
              placeholder="请输入策略代码（Python）"
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                {editingStrategy ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title="策略详情"
        placement="right"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={600}
      >
        {viewingStrategy && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Title level={4}>{viewingStrategy.name}</Title>
              <Text type="secondary">{viewingStrategy.description}</Text>
              <div style={{ marginTop: '8px' }}>
                {getTypeTag(viewingStrategy.type)}
                {getStatusBadge(viewingStrategy.status)}
              </div>
            </div>

            {viewingStrategy.performance && (
              <Card title="性能指标" size="small">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="总收益率"
                      value={viewingStrategy.performance.totalReturn}
                      suffix="%"
                      precision={2}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="夏普比率"
                      value={viewingStrategy.performance.sharpeRatio}
                      precision={2}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="最大回撤"
                      value={viewingStrategy.performance.maxDrawdown}
                      suffix="%"
                      precision={2}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="胜率"
                      value={viewingStrategy.performance.winRate}
                      suffix="%"
                      precision={2}
                    />
                  </Col>
                </Row>
              </Card>
            )}

            {viewingStrategy.config && (
              <Card title="策略配置" size="small">
                <pre style={{ fontSize: '12px' }}>
                  {JSON.stringify(viewingStrategy.config, null, 2)}
                </pre>
              </Card>
            )}

            <Card title="策略代码" size="small">
              <div style={{ 
                backgroundColor: '#f5f5f5', 
                padding: '16px', 
                borderRadius: '4px',
                overflow: 'auto',
                maxHeight: '400px'
              }}>
                <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '12px' }}>
                  <code>{viewingStrategy.code}</code>
                </pre>
              </div>
            </Card>
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default StrategyManagement;