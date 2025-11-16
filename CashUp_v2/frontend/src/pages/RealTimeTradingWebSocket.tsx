/**
 * 实时交易WebSocket页面
 * Real-time Trading WebSocket Page
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card,
  Row,
  Col,
  Table,
  Tag,
  Button,
  Space,
  Statistic,
  Alert,
  Typography,
  Spin,
  Badge,
  Drawer,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Divider,
  Tooltip,
  Progress,
  Timeline,
  List,
  Avatar,
} from 'antd';
import {
  LineChartOutlined,
  BarChartOutlined,
  AreaChartOutlined,
  PieChartOutlined,
  RiseOutlined,
  FallOutlined,
  DollarCircleOutlined,
  PercentageOutlined,
  ClockCircleOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  FilterOutlined,
  TableOutlined,
  SettingOutlined,
  ReloadOutlined,
  EyeOutlined,
  StopOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloudDownloadOutlined,
  LineChartOutlined as LineChartOutlined2,
  AreaChartOutlined as AreaChartOutlined2,
  WifiOutlined,
  DisconnectOutlined,
  SyncOutlined,
  HeartOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  RocketOutlined,
} from '@ant-design/icons';

import { 
  TradingWebSocketClient,
  MarketData,
  TradeData,
  OrderBookData,
  PositionUpdate,
  OrderUpdate,
  createTradingWebSocketClient,
} from '../utils/tradingWebSocket';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const RealTimeTradingWebSocket: React.FC = () => {
  // WebSocket连接状态
  const [wsClient, setWsClient] = useState<TradingWebSocketClient | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'reconnecting'>('disconnected');
  const [metrics, setMetrics] = useState<any>(null);
  const [lastMessageTime, setLastMessageTime] = useState<number>(0);
  const [errorCount, setErrorCount] = useState<number>(0);

  // 市场数据
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [trades, setTrades] = useState<TradeData[]>([]);
  const [orderBook, setOrderBook] = useState<OrderBookData | null>(null);
  const [positions, setPositions] = useState<PositionUpdate[]>([]);
  const [orders, setOrders] = useState<OrderUpdate[]>([]);

  // 交易表单
  const [tradeForm] = Form.useForm();
  const [isTradeModalVisible, setIsTradeModalVisible] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTC/USDT');

  // 图表数据
  const [priceData, setPriceData] = useState<any[]>([]);
  const [volumeData, setVolumeData] = useState<any[]>([]);

  // 配置
  const [symbols, setSymbols] = useState<string[]>(['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT']);
  const [autoReconnect, setAutoReconnect] = useState<boolean>(true);
  const [enableLogging, setEnableLogging] = useState<boolean>(false);

  // 使用ref来存储最新的数据
  const marketDataRef = useRef<MarketData[]>([]);
  const tradesRef = useRef<TradeData[]>([]);
  const priceDataRef = useRef<any[]>([]);

  // 初始化WebSocket
  useEffect(() => {
    initializeWebSocket();
    return () => {
      if (wsClient) {
        wsClient.disconnect();
      }
    };
  }, []);

  // 初始化WebSocket连接
  const initializeWebSocket = useCallback(() => {
    try {
      // 动态生成WebSocket URL，根据当前协议和环境
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/trading`;
      
      const client = createTradingWebSocketClient(
        {
          url: wsUrl,
          enableReconnect: autoReconnect,
          reconnectInterval: 5000,
          maxReconnectAttempts: 10,
          enableHeartbeat: true,
          heartbeatInterval: 30000,
          enableLogging: enableLogging,
          symbols: symbols,
        },
        {
          onMarketData: handleMarketData,
          onTrade: handleTrade,
          onOrderBook: handleOrderBook,
          onPositionUpdate: handlePositionUpdate,
          onOrderUpdate: handleOrderUpdate,
          onConnectionStatus: handleConnectionStatus,
          onError: handleError,
        }
      );

      setWsClient(client);
      client.initialize();
      client.connect();
    } catch (error) {
      message.error('WebSocket初始化失败');
    }
  }, [autoReconnect, enableLogging, symbols]);

  // 处理市场数据
  const handleMarketData = useCallback((data: MarketData) => {
    setLastMessageTime(Date.now());
    setErrorCount(0);

    // 更新市场数据
    setMarketData(prev => {
      const existingIndex = prev.findIndex(item => item.symbol === data.symbol);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = data;
        return updated;
      }
      return [...prev, data];
    });

    // 更新价格历史数据
    setPriceData(prev => {
      const newData = [...prev, {
        time: new Date(data.timestamp).toLocaleTimeString(),
        price: data.price,
        symbol: data.symbol,
      }];
      
      // 保持最近100个数据点
      if (newData.length > 100) {
        return newData.slice(-100);
      }
      return newData;
    });

    // 更新ref
    marketDataRef.current = marketDataRef.current.map(item => 
      item.symbol === data.symbol ? data : item
    );
    
    priceDataRef.current = [...priceDataRef.current, {
      time: new Date(data.timestamp).toLocaleTimeString(),
      price: data.price,
      symbol: data.symbol,
    }].slice(-100);
  }, []);

  // 处理交易数据
  const handleTrade = useCallback((data: TradeData) => {
    setLastMessageTime(Date.now());
    setErrorCount(0);

    setTrades(prev => {
      const newTrades = [data, ...prev].slice(0, 50); // 保持最近50笔交易
      return newTrades;
    });

    tradesRef.current = [data, ...tradesRef.current].slice(0, 50);
  }, []);

  // 处理订单簿数据
  const handleOrderBook = useCallback((data: OrderBookData) => {
    setLastMessageTime(Date.now());
    setOrderBook(data);
  }, []);

  // 处理持仓更新
  const handlePositionUpdate = useCallback((data: PositionUpdate) => {
    setLastMessageTime(Date.now());
    
    setPositions(prev => {
      const existingIndex = prev.findIndex(item => item.symbol === data.symbol);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = data;
        return updated;
      }
      return [...prev, data];
    });
  }, []);

  // 处理订单更新
  const handleOrderUpdate = useCallback((data: OrderUpdate) => {
    setLastMessageTime(Date.now());
    
    setOrders(prev => {
      const existingIndex = prev.findIndex(item => item.id === data.id);
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = data;
        return updated;
      }
      return [...prev, data];
    });
  }, []);

  // 处理连接状态
  const handleConnectionStatus = useCallback((status: 'connected' | 'disconnected' | 'reconnecting') => {
    setConnectionStatus(status as any);
  }, []);

  // 处理错误
  const handleError = useCallback((error: Error) => {
    setErrorCount(prev => prev + 1);
    message.error(`WebSocket错误: ${error.message}`);
  }, []);

  // 订阅数据
  const subscribeToData = useCallback(() => {
    if (!wsClient) return;

    try {
      wsClient.subscribeMarketData(symbols);
      wsClient.subscribeTrades(symbols);
      wsClient.subscribeOrderBook(symbols);
      wsClient.subscribePositions();
      wsClient.subscribeOrders();
      
      message.success('成功订阅所有数据');
    } catch (error) {
      message.error('订阅数据失败');
    }
  }, [wsClient, symbols]);

  // 取消订阅
  const unsubscribeFromData = useCallback(() => {
    if (!wsClient) return;

    try {
      wsClient.unsubscribeAll();
      message.success('成功取消所有订阅');
    } catch (error) {
      message.error('取消订阅失败');
    }
  }, [wsClient]);

  // 发送订单
  const handleSendOrder = async (values: any) => {
    if (!wsClient || !wsClient.isConnected()) {
      message.error('WebSocket未连接');
      return;
    }

    try {
      const order = {
        symbol: values.symbol,
        side: values.side,
        type: values.type,
        quantity: values.quantity,
        price: values.price,
        stopPrice: values.stopPrice,
      };

      const result = await wsClient.sendOrder(order);
      message.success(`订单创建成功: ${result.orderId}`);
      setIsTradeModalVisible(false);
      tradeForm.resetFields();
    } catch (error) {
      const msg = (error as any)?.message || '订单创建失败';
      message.error(`订单创建失败: ${msg}`);
    }
  };

  // 取消订单
  const handleCancelOrder = async (orderId: string) => {
    if (!wsClient || !wsClient.isConnected()) {
      message.error('WebSocket未连接');
      return;
    }

    try {
      await wsClient.cancelOrder(orderId);
      message.success('订单取消成功');
    } catch (error) {
      const msg2 = (error as any)?.message || '订单取消失败';
      message.error(`订单取消失败: ${msg2}`);
    }
  };

  // 重新连接
  const handleReconnect = () => {
    if (wsClient) {
      wsClient.disconnect();
      initializeWebSocket();
    }
  };

  // 更新指标
  useEffect(() => {
    if (wsClient) {
      const newMetrics = wsClient.getMetrics();
      setMetrics(newMetrics);
    }
  }, [wsClient]);

  // 市场数据表格列
  const marketColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Tag color="blue">{symbol}</Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => (
        <Text strong style={{ color: price > 0 ? '#52c41a' : '#f5222d' }}>
          ${price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '24h变化',
      dataIndex: 'change24h',
      key: 'change24h',
      render: (change: number) => (
        <Text style={{ color: change > 0 ? '#52c41a' : '#f5222d' }}>
          {change > 0 ? '+' : ''}{change.toFixed(2)}%
        </Text>
      ),
    },
    {
      title: '24h成交量',
      dataIndex: 'volume24h',
      key: 'volume24h',
      render: (volume: number) => (
        <Text>${volume.toLocaleString()}</Text>
      ),
    },
    {
      title: '最高价',
      dataIndex: 'high24h',
      key: 'high24h',
      render: (high: number) => (
        <Text>${high.toFixed(2)}</Text>
      ),
    },
    {
      title: '最低价',
      dataIndex: 'low24h',
      key: 'low24h',
      render: (low: number) => (
        <Text>${low.toFixed(2)}</Text>
      ),
    },
  ];

  // 交易数据表格列
  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: number) => (
        <Text>{new Date(timestamp).toLocaleTimeString()}</Text>
      ),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Tag color="blue">{symbol}</Tag>
      ),
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
      render: (price: number) => (
        <Text>${price.toFixed(2)}</Text>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => (
        <Text>{quantity.toFixed(4)}</Text>
      ),
    },
    {
      title: '手续费',
      dataIndex: 'fee',
      key: 'fee',
      render: (fee: number) => (
        <Text>${fee.toFixed(4)}</Text>
      ),
    },
  ];

  // 订单更新表格列
  const orderColumns = [
    {
      title: '订单ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Text code>{id}</Text>
      ),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Tag color="blue">{symbol}</Tag>
      ),
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
      title: '类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'default';
        if (status === 'filled') color = 'green';
        else if (status === 'rejected') color = 'red';
        else if (status === 'canceled') color = 'orange';
        else if (status === 'pending') color = 'blue';
        
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number, record: OrderUpdate) => (
        <Text>
          {record.filledQuantity}/{record.quantity}
        </Text>
      ),
    },
  ];

  // 连接状态指示器
  const renderConnectionStatus = () => {
    let status = connectionStatus;
    let color: 'success' | 'error' | 'warning' | 'processing' | 'default' = 'default';
    let icon = <DisconnectOutlined />;
    
    if (status === 'connected') {
      color = 'success';
      icon = <WifiOutlined />;
    } else if (status === 'connecting') {
      color = 'processing';
      icon = <SyncOutlined spin />;
    } else if (status === 'reconnecting') {
      color = 'warning';
      icon = <SyncOutlined spin />;
    }
    
    return (
      <Badge status={color} text={<span>{icon} 连接状态: {status}</span>} />
    );
  };

  // 获取连接状态描述
  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return '已连接';
      case 'connecting':
        return '连接中...';
      case 'reconnecting':
        return '重连中...';
      default:
        return '已断开';
    }
  };

  // 获取连接状态颜色
  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'processing';
      case 'reconnecting':
        return 'warning';
      default:
        return 'error';
    }
  };

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和连接状态 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={2}>实时交易WebSocket</Title>
          <Paragraph type="secondary">
            实时市场数据、交易数据和订单管理
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          {renderConnectionStatus()}
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">
              最后消息: {lastMessageTime ? new Date(lastMessageTime).toLocaleTimeString() : '无'}
            </Text>
          </div>
        </Col>
      </Row>

      {/* 连接状态和指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="连接状态"
              value={getConnectionStatusText()}
              valueStyle={{ color: getConnectionStatusColor() === 'success' ? '#52c41a' : '#f5222d' }}
              prefix={connectionStatus === 'connected' ? <WifiOutlined /> : <DisconnectOutlined />}
            />
          </Card>
        </Col>
        
        {metrics && (
          <>
            <Col span={6}>
              <Card>
                <Statistic
                  title="接收消息"
                  value={metrics.receivedMessages}
                  suffix="条"
                />
              </Card>
            </Col>
            
            <Col span={6}>
              <Card>
                <Statistic
                  title="发送消息"
                  value={metrics.sentMessages}
                  suffix="条"
                />
              </Card>
            </Col>
            
            <Col span={6}>
              <Card>
                <Statistic
                  title="错误次数"
                  value={errorCount}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Card>
            </Col>
          </>
        )}
      </Row>

      {/* 控制按钮 */}
      <Card title="控制面板" style={{ marginBottom: 24 }}>
        <Space>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={subscribeToData}
            disabled={connectionStatus !== 'connected'}
          >
            订阅数据
          </Button>
          
          <Button
            icon={<StopOutlined />}
            onClick={unsubscribeFromData}
            disabled={connectionStatus !== 'connected'}
          >
            取消订阅
          </Button>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={handleReconnect}
            loading={connectionStatus === 'connecting' || connectionStatus === 'reconnecting'}
          >
            重新连接
          </Button>
          
          <Button
            icon={<SettingOutlined />}
            onClick={() => {
              setAutoReconnect(!autoReconnect);
              setEnableLogging(!enableLogging);
            }}
          >
            配置
          </Button>
        </Space>
      </Card>

      {/* 市场数据 */}
      <Card title="市场数据" style={{ marginBottom: 24 }}>
        <Table
          columns={marketColumns}
          dataSource={marketData}
          pagination={{ pageSize: 5 }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* 实时价格图表 */}
      <Card title="实时价格图表" style={{ marginBottom: 24 }}>
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Spin size="large">
            <div>
              <LineChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Text type="secondary">实时价格图表</Text>
              </div>
            </div>
          </Spin>
        </div>
      </Card>

      {/* 交易数据 */}
      <Card title="最新交易" style={{ marginBottom: 24 }}>
        <Table
          columns={tradeColumns}
          dataSource={trades}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 800 }}
          rowKey="id"
        />
      </Card>

      {/* 订单更新 */}
      <Card title="订单更新" style={{ marginBottom: 24 }}>
        <Table
          columns={orderColumns}
          dataSource={orders}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 800 }}
          rowKey="id"
        />
      </Card>

      {/* 交易模态框 */}
      <Drawer
        title="快速交易"
        width={500}
        onClose={() => setIsTradeModalVisible(false)}
        visible={isTradeModalVisible}
      >
        <Form
          form={tradeForm}
          layout="vertical"
          onFinish={handleSendOrder}
        >
          <Form.Item
            name="symbol"
            label="交易对"
            initialValue={selectedSymbol}
          >
            <Select>
              {symbols.map(symbol => (
                <Option key={symbol} value={symbol}>{symbol}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="side"
            label="方向"
            rules={[{ required: true, message: '请选择方向' }]}
          >
            <Select>
              <Option value="buy">买入</Option>
              <Option value="sell">卖出</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select>
              <Option value="market">市价单</Option>
              <Option value="limit">限价单</Option>
              <Option value="stop">止损单</Option>
              <Option value="stop_limit">止损限价单</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="quantity"
            label="数量"
            rules={[{ required: true, message: '请输入数量' }]}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>

          {tradeForm.getFieldValue('type') === 'limit' && (
            <Form.Item
              name="price"
              label="价格"
              rules={[{ required: true, message: '请输入价格' }]}
            >
              <InputNumber style={{ width: '100%' }} />
            </Form.Item>
          )}

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsTradeModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                发送订单
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
};

export default RealTimeTradingWebSocket;