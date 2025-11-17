/**
 * 实时交易监控页面 - 连接真实API
 * Real-time Trading Monitoring Page - Connected to Real APIs
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
  
  Typography,
  Spin,
  message,
  Modal,
  Switch,
  InputNumber,
  Form,
  Badge,
  
  Popconfirm,
} from 'antd';
import { handleApiResponse, handleApiError, MarketDataResponse } from '../services/api';
import { dataCache } from '../utils/cache';
import { ReloadOutlined, StopOutlined, EyeOutlined, PauseCircleOutlined, PlayCircleOutlined } from '@ant-design/icons';
import moment from 'moment';
import {
  strategyAPI,
  tradingAPI,
  Strategy,
  Order,
  Position,
} from '../services/api';

const { Title } = Typography;
const { Option } = Select;

// 函数集注释：
// 1) fetchStrategies：获取策略列表
// 2) fetchMarketData：按选中交易对获取市场数据
// 3) fetchRecentOrders / fetchPositions / fetchAccountInfo：获取订单、持仓、账户
// 4) loadAllData：并行加载页面所需的全部数据
// 5) handleCreateOrder / handleCancelOrder / handleControlStrategy：交易与策略操作

// 实时交易监控组件
const RealTimeTrading: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  
  // 数据状态
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [marketData, setMarketData] = useState<MarketDataResponse[]>([]);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  
  
  // 详情显示
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  
  
  // 选中的交易对
  const [selectedSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT']);
  
  // 交易控制
  const [tradeModalVisible, setTradeModalVisible] = useState(false);
  const [tradeForm] = Form.useForm();
  
  // 账户信息
  const [accountInfo, setAccountInfo] = useState<any>(null);
  
  // 获取账户信息
  const fetchAccountInfo = React.useCallback(async () => {
    try {
      const response = await tradingAPI.getAccountInfo();
      setAccountInfo(response);
    } catch (error) {
      console.error('获取账户信息失败:', error);
      const errorMessage = handleApiError(error as any);
      message.error(errorMessage);
    }
  }, []);
  
  // 创建订单
  const handleCreateOrder = async (values: any) => {
    try {
      await tradingAPI.createOrder(values);
      message.success('订单创建成功');
      setTradeModalVisible(false);
      tradeForm.resetFields();
      await fetchRecentOrdersCb();
    } catch (error) {
      console.error('创建订单失败:', error);
      message.error('创建订单失败');
    }
  };
  
  // 取消订单
  const handleCancelOrder = async (orderId: string) => {
    try {
      await tradingAPI.cancelOrder(orderId);
      message.success('订单取消成功');
      await fetchRecentOrdersCb();
    } catch (error) {
      console.error('取消订单失败:', error);
      message.error('取消订单失败');
    }
  };
  
  // 平仓
  const handleClosePosition = async (positionId: string) => {
    try {
      await tradingAPI.closePosition(positionId);
      message.success('平仓成功');
      await fetchPositionsCb();
    } catch (error) {
      console.error('平仓失败:', error);
      message.error('平仓失败');
    }
  };
  
  // 获取策略列表
  const fetchStrategiesCb = React.useCallback(async () => {
    try {
      const response = await dataCache.fetchWithCache(
        'strategies',
        async () => {
          const apiResponse = await strategyAPI.getStrategies();
          return handleApiResponse(apiResponse) as Strategy[];
        },
        { ttl: 2 * 60 * 1000 } // 2分钟缓存
      );
      
      if (response && Array.isArray(response)) {
        setStrategies(response);
      } else if (response && (response as any).strategies) {
        setStrategies((response as any).strategies);
      }
    } catch (error) {
      const errorMessage = handleApiError(error);
      console.error('获取策略列表失败:', error);
      message.error(errorMessage);
    }
  }, []);
  
  // 获取市场数据
  const fetchMarketDataCb = React.useCallback(async () => {
    try {
      const promises = selectedSymbols.map(symbol => 
        strategyAPI.getRealTimeData(symbol)
      );
      const responses: any = await Promise.all(promises);
      const data = responses.map((response: any) => response);
      setMarketData(data);
    } catch (error) {
      console.error('获取市场数据失败:', error);
      const errorMessage = handleApiError(error as any);
      message.error(errorMessage);
    }
  }, [selectedSymbols]);
  
  
  
  // 获取最近订单
  const fetchRecentOrdersCb = React.useCallback(async () => {
    try {
      const response: any = await tradingAPI.getOrders({ 
        limit: 50, 
        sort_by: 'timestamp', 
        sort_order: 'desc' 
      });
      setRecentOrders(response || []);
    } catch (error) {
      console.error('获取最近订单失败:', error);
      const errorMessage = handleApiError(error as any);
      message.error(errorMessage);
    }
  }, []);
  
  // 获取持仓数据
  const fetchPositionsCb = React.useCallback(async () => {
    try {
      const response: any = await tradingAPI.getPositions();
      setPositions(response || []);
    } catch (error) {
      console.error('获取持仓数据失败:', error);
      const errorMessage = handleApiError(error as any);
      message.error(errorMessage);
    }
  }, []);
  
  // 加载所有数据
  const loadAllDataCb = React.useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchStrategiesCb(),
        fetchMarketDataCb(),
        fetchRecentOrdersCb(),
        fetchPositionsCb(),
        fetchAccountInfo()
      ]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchStrategiesCb, fetchMarketDataCb, fetchRecentOrdersCb, fetchPositionsCb, fetchAccountInfo]);
  
  // 策略控制
  const handleControlStrategy = async (strategyId: string, action: 'start' | 'stop' | 'reload') => {
    try {
      if (action === 'start') {
        await strategyAPI.startStrategy(strategyId);
        message.success('策略启动成功');
      } else if (action === 'stop') {
        await strategyAPI.stopStrategy(strategyId);
        message.success('策略停止成功');
      } else if (action === 'reload') {
        await strategyAPI.reloadStrategy(strategyId);
        message.success('策略重载成功');
      }
      await fetchStrategiesCb();
    } catch (error) {
      console.error('策略控制失败:', error);
      message.error('策略控制失败');
    }
  };
  
  // 查看订单详情
  const handleViewOrderDetail = (order: Order) => {
    setSelectedOrder(order);
    setDetailVisible(true);
  };
  
  // 自动刷新
  useEffect(() => {
    loadAllDataCb();
    if (autoRefresh) {
      const interval = setInterval(async () => {
        const promises = [
          fetchMarketDataCb(),
          fetchRecentOrdersCb(),
          fetchPositionsCb(),
          fetchAccountInfo()
        ];
        await Promise.all(promises);
      }, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, loadAllDataCb, fetchMarketDataCb, fetchRecentOrdersCb, fetchPositionsCb, fetchAccountInfo]);
  
  // 订单表格列
  const orderColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => (
        <span>{moment(timestamp).format('HH:mm:ss')}</span>
      ),
      sorter: (a: Order, b: Order) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    },
    {
      title: '策略ID',
      dataIndex: 'strategyId',
      key: 'strategyId',
      render: (strategyId: string) => (
        <Tag color="blue">{strategyId}</Tag>
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Tag color="green">{symbol}</Tag>
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
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'market' ? 'blue' : 'orange'}>
          {type === 'market' ? '市价' : '限价'}
        </Tag>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`,
      sorter: (a: Order, b: Order) => a.price - b.price
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4)
    },
    {
      title: '成交数量',
      dataIndex: 'filledQuantity',
      key: 'filledQuantity',
      render: (filledQuantity: number) => filledQuantity.toFixed(4)
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
      title: '操作',
      key: 'actions',
      render: (text: string, record: Order) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewOrderDetail(record)}
          >
            详情
          </Button>
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要取消这个订单吗？"
              onConfirm={() => handleCancelOrder(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                danger
                icon={<StopOutlined />}
              >
                取消
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];
  
  // 持仓表格列
  const positionColumns = [
    {
      title: '策略ID',
      dataIndex: 'strategyId',
      key: 'strategyId',
      render: (strategyId: string) => (
        <Tag color="blue">{strategyId}</Tag>
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="green">{symbol}</Tag>
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
      title: '操作',
      key: 'actions',
      render: (text: string, record: Position) => (
        <Popconfirm
          title="确定要平仓吗？"
          onConfirm={() => handleClosePosition(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button
            type="link"
            danger
            icon={<StopOutlined />}
          >
            平仓
          </Button>
        </Popconfirm>
      )
    }
  ];
  
  // 策略状态颜色
  const strategyStatusColor = {
    running: '#52c41a',
    stopped: '#8c8c8c',
    error: '#ff4d4f',
    paused: '#faad14'
  };
  
  // 策略状态文本
  const strategyStatusText = {
    running: '运行中',
    stopped: '已停止',
    error: '错误',
    paused: '暂停'
  };
  
  // 计算统计数据
  const totalPnl = recentOrders.reduce((sum, order) => sum + (order.pnl || 0), 0);
  const runningStrategies = strategies.filter(s => s.status === 'running').length;
  const totalPositions = positions.length;
  const totalExposure = positions.reduce((sum, pos) => sum + pos.margin, 0);
  const accountBalance = accountInfo?.total_balance || 0;
  const availableBalance = accountInfo?.available_balance || 0;
  
  return (
    <div style={{ padding: 24 }}>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Title level={2}>实时交易监控</Title>
          </Col>
          <Col span={12} style={{ textAlign: 'right' }}>
            <Space>
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => setTradeModalVisible(true)}>
                手动交易
              </Button>
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
              <Button icon={<ReloadOutlined />} onClick={loadAllDataCb}>
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
                title="今日盈亏"
                value={totalPnl}
                prefix="$"
                precision={2}
                valueStyle={{ color: totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                交易次数: {recentOrders.length}
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="运行策略"
                value={runningStrategies}
                suffix={`/ ${strategies.length}`}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                总持仓: {totalPositions}
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="账户余额"
                value={accountBalance}
                prefix="$"
                precision={2}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                可用余额: ${availableBalance.toFixed(2)}
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总敞口"
                value={totalExposure}
                prefix="$"
                precision={2}
              />
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                杠杆使用: {accountBalance > 0 ? ((totalExposure / accountBalance) * 100).toFixed(1) : '0'}%
              </div>
            </Card>
          </Col>
        </Row>
        
        {/* 策略状态 */}
        <Card title="策略状态" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            {strategies.map(strategy => (
              <Col span={12} key={strategy.id}>
                <Card size="small">
                  <Row gutter={16}>
                    <Col span={8}>
                      <div style={{ fontWeight: 'bold' }}>{strategy.name}</div>
                      <Badge 
                        color={strategyStatusColor[strategy.status]} 
                        text={strategyStatusText[strategy.status]}
                      />
                    </Col>
                    <Col span={8}>
                      <div style={{ fontSize: 12, color: '#666' }}>类型</div>
                      <div>{strategy.type}</div>
                    </Col>
                    <Col span={8}>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {strategy.performance ? '总盈亏' : '状态'}
                      </div>
                      <div style={{ color: strategy.performance?.totalPnl >= 0 ? '#3f8600' : '#cf1322' }}>
                        {strategy.performance ? `$${strategy.performance.totalPnl.toFixed(2)}` : '-'}
                      </div>
                    </Col>
                  </Row>
                  {strategy.performance && (
                    <Row gutter={16} style={{ marginTop: 8 }}>
                      <Col span={6}>
                        <div style={{ fontSize: 12, color: '#666' }}>胜率</div>
                        <div>{strategy.performance.winRate.toFixed(1)}%</div>
                      </Col>
                      <Col span={6}>
                        <div style={{ fontSize: 12, color: '#666' }}>交易次数</div>
                        <div>{strategy.performance.tradesCount}</div>
                      </Col>
                      <Col span={6}>
                        <div style={{ fontSize: 12, color: '#666' }}>最大回撤</div>
                        <div>{strategy.performance.maxDrawdown.toFixed(2)}%</div>
                      </Col>
                      <Col span={6}>
                        <Space>
                          <Button
                            type="link"
                            size="small"
                            icon={strategy.status === 'running' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                            onClick={() => handleControlStrategy(strategy.id, strategy.status === 'running' ? 'stop' : 'start')}
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
                  )}
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
        
        {/* 实时价格 */}
        <Card title="实时价格" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            {marketData.map(data => (
              <Col span={8} key={data.symbol}>
                <Card size="small">
                  <Row gutter={16}>
                    <Col span={12}>
                      <div style={{ fontWeight: 'bold' }}>{data.symbol}</div>
                      <div style={{ fontSize: 18, color: data.changePercent24h >= 0 ? '#3f8600' : '#cf1322' }}>
  ${Number(data.price || 0).toFixed(2)}
                      </div>
                    </Col>
                    <Col span={12}>
                      <div style={{ fontSize: 12, color: '#666' }}>24h变化</div>
                      <div style={{ color: data.changePercent24h >= 0 ? '#3f8600' : '#cf1322' }}>
                        {data.changePercent24h >= 0 ? '+' : ''}{data.changePercent24h.toFixed(2)}%
                      </div>
                      <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
                        成交量: ${(data.volume24h / 1000000).toFixed(1)}M
                      </div>
                    </Col>
                  </Row>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
        
        {/* 最近订单 */}
        <Card title="最近订单" style={{ marginBottom: 24 }}>
          <Table
            columns={orderColumns}
            dataSource={recentOrders}
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
            columns={positionColumns}
            dataSource={positions}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true
            }}
          />
        </Card>
        
        {/* 交易模态框 */}
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
                  label="策略ID"
                  name="strategyId"
                >
                  <Select placeholder="选择策略（可选）">
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
        
        {/* 订单详情模态框 */}
        <Modal
          title="订单详情"
          open={detailVisible}
          onCancel={() => setDetailVisible(false)}
          footer={null}
          width={600}
        >
          {selectedOrder && (
            <div>
              <Card title="基本信息" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic title="订单ID" value={selectedOrder.id} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="策略ID" value={selectedOrder.strategyId} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="交易对" value={selectedOrder.symbol} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="状态" value={selectedOrder.status} />
                  </Col>
                </Row>
              </Card>
              
              <Card title="交易信息">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic title="方向" value={selectedOrder.side === 'buy' ? '买入' : '卖出'} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="类型" value={selectedOrder.type === 'market' ? '市价' : '限价'} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="价格" value={`$${selectedOrder.price.toFixed(2)}`} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="数量" value={selectedOrder.quantity.toFixed(4)} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="成交数量" value={selectedOrder.filledQuantity.toFixed(4)} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="成交均价" value={`$${selectedOrder.averagePrice.toFixed(2)}`} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="手续费" value={`$${selectedOrder.fee.toFixed(2)}`} />
                  </Col>
                  <Col span={12}>
                    <Statistic 
                      title="盈亏" 
                      value={`$${selectedOrder.pnl?.toFixed(2) || '0.00'}`}
                      valueStyle={{ color: (selectedOrder.pnl || 0) >= 0 ? '#3f8600' : '#cf1322' }}
                    />
                  </Col>
                </Row>
              </Card>
            </div>
          )}
        </Modal>
      </Spin>
    </div>
  );
};

export default RealTimeTrading;