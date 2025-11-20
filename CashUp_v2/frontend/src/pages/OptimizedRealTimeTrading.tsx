/**
 * 优化后的实时交易监控页面 - React.memo优化版本
 * Optimized Real-time Trading Monitoring Page - React.memo Optimized Version
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Select,
  Space,
  Typography,
  Spin,
  message,
  Modal,
  Switch,
  InputNumber,
  Form,
} from 'antd';
import { handleApiResponse, handleApiError, MarketDataResponse } from '../services/api';
import { dataCache } from '../utils/cache';
import {
  ReloadOutlined,
} from '@ant-design/icons';
import {
  strategyAPI,
  tradingAPI,
  Strategy,
  Order,
  Position,
} from '../services/api';
import OptimizedOrderTable from '../components/RealTimeTrading/OptimizedOrderTable';
import OptimizedPositionTable from '../components/RealTimeTrading/OptimizedPositionTable';
import OptimizedStrategyCard from '../components/RealTimeTrading/OptimizedStrategyCard';

const { Title } = Typography;
const { Option } = Select;

// 函数集注释：
// 1) fetchStrategies / fetchMarketData / fetchRecentOrders / fetchPositions / fetchAccountInfo
// 2) loadAllData：并行加载页面所需数据
// 3) handleCreateOrder / handleCancelOrder / handleClosePosition / handleControlStrategy

// 优化后的实时交易监控组件
const OptimizedRealTimeTrading: React.FC = () => {
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

  // 使用useCallback优化事件处理函数，避免不必要的重新创建
  const fetchAccountInfo = useCallback(async () => {
    try {
      const response = await tradingAPI.getAccountInfo();
      setAccountInfo(response);
    } catch (error) {
      console.error('获取账户信息失败:', error);
    }
  }, []);

  // 获取最近订单（提前声明以避免 no-use-before-define）
  const fetchRecentOrders = useCallback(async () => {
    try {
      const response: any = await tradingAPI.getOrders({ 
        limit: 50, 
        sort_by: 'timestamp', 
        sort_order: 'desc' 
      });
      setRecentOrders(response || []);
    } catch (error) {
      console.error('获取最近订单失败:', error);
      message.error('获取最近订单失败');
    }
  }, []);

  // 获取持仓数据（提前声明以避免 no-use-before-define）
  const fetchPositions = useCallback(async () => {
    try {
      const response: any = await tradingAPI.getPositions();
      setPositions(response || []);
    } catch (error) {
      console.error('获取持仓数据失败:', error);
      message.error('获取持仓数据失败');
    }
  }, []);

  const handleCreateOrder = useCallback(async (values: any) => {
    try {
      await tradingAPI.createOrder(values);
      message.success('订单创建成功');
      setTradeModalVisible(false);
      tradeForm.resetFields();
      await fetchRecentOrders();
    } catch (error) {
      console.error('创建订单失败:', error);
      message.error('创建订单失败');
    }
  }, [tradeForm, fetchRecentOrders]);

  const handleCancelOrder = useCallback(async (orderId: string) => {
    try {
      await tradingAPI.cancelOrder(orderId);
      message.success('订单取消成功');
      await fetchRecentOrders();
    } catch (error) {
      console.error('取消订单失败:', error);
      message.error('取消订单失败');
    }
  }, [fetchRecentOrders]);

  const handleClosePosition = useCallback(async (positionId: string) => {
    try {
      await tradingAPI.closePosition(positionId);
      message.success('平仓成功');
      await fetchPositions();
    } catch (error) {
      console.error('平仓失败:', error);
      message.error('平仓失败');
    }
  }, [fetchPositions]);

  const fetchStrategies = useCallback(async () => {
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

  const fetchMarketData = useCallback(async () => {
    try {
      const promises = selectedSymbols.map(symbol => 
        strategyAPI.getRealTimeData(symbol)
      );
      const responses: any = await Promise.all(promises);
      const data = responses.map((response: any) => response);
      setMarketData(data);
    } catch (error) {
      console.error('获取市场数据失败:', error);
      message.error('获取市场数据失败');
    }
  }, [selectedSymbols]);


  

  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchStrategies(),
        fetchMarketData(),
        fetchRecentOrders(),
        fetchPositions(),
        fetchAccountInfo()
      ]);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchStrategies, fetchMarketData, fetchRecentOrders, fetchPositions, fetchAccountInfo]);

  const handleControlStrategy = useCallback(async (strategyId: string, action: 'start' | 'stop' | 'reload') => {
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
      await fetchStrategies();
    } catch (error) {
      console.error('策略控制失败:', error);
      message.error('策略控制失败');
    }
  }, [fetchStrategies]);

  const handleViewOrderDetail = useCallback((order: Order) => {
    setSelectedOrder(order);
    setDetailVisible(true);
  }, []);

  // 使用useMemo优化统计数据计算
  const statistics = useMemo(() => ({
    totalPnl: recentOrders.reduce((sum, order) => sum + (order.pnl || 0), 0),
    runningStrategies: strategies.filter(s => s.status === 'running').length,
    totalPositions: positions.length,
    totalExposure: positions.reduce((sum, pos) => sum + pos.margin, 0),
    accountBalance: accountInfo?.total_balance || 0,
    availableBalance: accountInfo?.available_balance || 0,
  }), [recentOrders, strategies, positions, accountInfo]);

  // 自动刷新
  useEffect(() => {
    loadAllData();
    if (autoRefresh) {
      const interval = setInterval(async () => {
        const promises = [
          fetchMarketData(),
          fetchRecentOrders(),
          fetchPositions(),
          fetchAccountInfo()
        ];
        await Promise.all(promises);
      }, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, loadAllData, fetchMarketData, fetchRecentOrders, fetchPositions, fetchAccountInfo]);

  // 使用useMemo优化渲染的UI元素
  const controlSection = useMemo(() => (
    <Col span={12} style={{ textAlign: 'right' }}>
      <Space>
        <Button type="primary" icon={<ReloadOutlined />} onClick={() => setTradeModalVisible(true)}>
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
        <Button icon={<ReloadOutlined />} onClick={loadAllData}>
          刷新
        </Button>
      </Space>
    </Col>
  ), [autoRefresh, refreshInterval, loadAllData]);

  const overviewCards = useMemo(() => (
    <>
      <Col span={6}>
        <Card>
          <Statistic
            title="今日盈亏"
            value={statistics.totalPnl}
            prefix="$"
            precision={2}
            valueStyle={{ color: statistics.totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
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
            value={statistics.runningStrategies}
            suffix={`/ ${strategies.length}`}
          />
          <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            总持仓: {statistics.totalPositions}
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="账户余额"
            value={statistics.accountBalance}
            prefix="$"
            precision={2}
          />
          <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            可用余额: ${statistics.availableBalance.toFixed(2)}
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="总敞口"
            value={statistics.totalExposure}
            prefix="$"
            precision={2}
          />
          <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
            杠杆使用: {statistics.accountBalance > 0 ? ((statistics.totalExposure / statistics.accountBalance) * 100).toFixed(1) : '0'}%
          </div>
        </Card>
      </Col>
    </>
  ), [statistics, recentOrders.length, strategies.length]);

  const strategyCards = useMemo(() => (
    <Row gutter={[16, 16]}>
      {strategies.map(strategy => (
        <Col span={12} key={strategy.id}>
          <OptimizedStrategyCard
            strategy={strategy}
            onControlStrategy={handleControlStrategy}
          />
        </Col>
      ))}
    </Row>
  ), [strategies, handleControlStrategy]);

  const marketCards = useMemo(() => (
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
  ), [marketData]);

  return (
    <div style={{ padding: 24 }}>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Title level={2}>实时交易监控</Title>
          </Col>
          {controlSection}
        </Row>
        
        {/* 实时状态概览 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          {overviewCards}
        </Row>
        
        {/* 策略状态 */}
        <Card title="策略状态" style={{ marginBottom: 24 }}>
          {strategyCards}
        </Card>
        
        {/* 实时价格 */}
        <Card title="实时价格" style={{ marginBottom: 24 }}>
          {marketCards}
        </Card>
        
        {/* 最近订单 */}
        <Card title="最近订单" style={{ marginBottom: 24 }}>
          <OptimizedOrderTable
            orders={recentOrders}
            onViewDetail={handleViewOrderDetail}
            onCancelOrder={handleCancelOrder}
            loading={loading}
          />
        </Card>
        
        {/* 当前持仓 */}
        <Card title="当前持仓">
          <OptimizedPositionTable
            positions={positions}
            onClosePosition={handleClosePosition}
            loading={loading}
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

export default OptimizedRealTimeTrading;
