import React, { useState } from 'react'
import {
  Card, Table, Button, Space, Tag, Typography, Row, Col, Statistic,
  Select, DatePicker, Input, Modal, Form, InputNumber, Alert, Tabs,
  Progress, Tooltip, Badge
} from 'antd'
import {
  PlayCircleOutlined, StopOutlined, ReloadOutlined,
  SearchOutlined, FilterOutlined, ExportOutlined, EyeOutlined,
  DollarOutlined, TrophyOutlined, ClockCircleOutlined,

} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'


const { Title, Text } = Typography
const { Option } = Select
const { RangePicker } = DatePicker
const { TabPane } = Tabs

interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  size: number
  entryPrice: number
  currentPrice: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  margin: number
  strategy: string
  openTime: string
}

interface Order {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  type: 'market' | 'limit' | 'stop'
  amount: number
  price?: number
  filled: number
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  strategy: string
  createdAt: string
  updatedAt: string
}

interface Trade {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  amount: number
  price: number
  fee: number
  realizedPnL: number
  strategy: string
  executedAt: string
}

interface TradingStats {
  totalPnL: number
  todayPnL: number
  totalVolume: number
  todayVolume: number
  totalTrades: number
  todayTrades: number
  winRate: number
  activePositions: number
  pendingOrders: number
}

const TradingMonitor: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('positions')
  const [isOrderModalVisible, setIsOrderModalVisible] = useState(false)
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null)
  const [form] = Form.useForm()

  // 模拟数据
  const [tradingStats] = useState<TradingStats>({
    totalPnL: 12580.50,
    todayPnL: 1250.30,
    totalVolume: 2580000,
    todayVolume: 125000,
    totalTrades: 1256,
    todayTrades: 45,
    winRate: 68.5,
    activePositions: 8,
    pendingOrders: 12
  })

  const [positions] = useState<Position[]>([
    {
      id: '1',
      symbol: 'BTC/USDT',
      side: 'long',
      size: 0.5,
      entryPrice: 42800,
      currentPrice: 43250,
      unrealizedPnL: 225,
      unrealizedPnLPercent: 1.05,
      margin: 8560,
      strategy: '趋势跟踪策略A',
      openTime: '2024-12-19 10:30:00'
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      side: 'short',
      size: 2.0,
      entryPrice: 2720,
      currentPrice: 2680,
      unrealizedPnL: 80,
      unrealizedPnLPercent: 1.47,
      margin: 2720,
      strategy: '均值回归策略B',
      openTime: '2024-12-19 11:15:00'
    },
    {
      id: '3',
      symbol: 'BNB/USDT',
      side: 'long',
      size: 10,
      entryPrice: 310,
      currentPrice: 315.60,
      unrealizedPnL: 56,
      unrealizedPnLPercent: 1.81,
      margin: 1550,
      strategy: '套利策略C',
      openTime: '2024-12-19 09:45:00'
    }
  ])

  const [orders] = useState<Order[]>([
    {
      id: '1',
      symbol: 'BTC/USDT',
      side: 'buy',
      type: 'limit',
      amount: 0.2,
      price: 42500,
      filled: 0,
      status: 'pending',
      strategy: '趋势跟踪策略A',
      createdAt: '2024-12-19 14:20:00',
      updatedAt: '2024-12-19 14:20:00'
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      side: 'sell',
      type: 'stop',
      amount: 1.0,
      price: 2650,
      filled: 0,
      status: 'pending',
      strategy: '均值回归策略B',
      createdAt: '2024-12-19 13:45:00',
      updatedAt: '2024-12-19 13:45:00'
    },
    {
      id: '3',
      symbol: 'SOL/USDT',
      side: 'buy',
      type: 'market',
      amount: 5,
      filled: 5,
      status: 'filled',
      strategy: '动量策略D',
      createdAt: '2024-12-19 12:30:00',
      updatedAt: '2024-12-19 12:30:15'
    }
  ])

  const [trades] = useState<Trade[]>([
    {
      id: '1',
      symbol: 'BTC/USDT',
      side: 'buy',
      amount: 0.5,
      price: 42800,
      fee: 10.7,
      realizedPnL: 0,
      strategy: '趋势跟踪策略A',
      executedAt: '2024-12-19 10:30:00'
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      side: 'sell',
      amount: 2.0,
      price: 2720,
      fee: 5.44,
      realizedPnL: 0,
      strategy: '均值回归策略B',
      executedAt: '2024-12-19 11:15:00'
    },
    {
      id: '3',
      symbol: 'SOL/USDT',
      side: 'buy',
      amount: 5,
      price: 98.75,
      fee: 2.47,
      realizedPnL: 15.6,
      strategy: '动量策略D',
      executedAt: '2024-12-19 12:30:15'
    }
  ])

  // 持仓表格列配置
  const positionColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '做多' : '做空'}
        </Tag>
      )
    },
    {
      title: '数量',
      dataIndex: 'size',
      key: 'size',
      render: (value: number) => value.toFixed(4)
    },
    {
      title: '开仓价格',
      dataIndex: 'entryPrice',
      key: 'entryPrice',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '当前价格',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '未实现盈亏',
      key: 'unrealizedPnL',
      render: (_: any, record: Position) => (
        <div>
          <Text className={record.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'}>
            ${record.unrealizedPnL.toFixed(2)}
          </Text>
          <br />
          <Text className={`text-xs ${record.unrealizedPnLPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ({record.unrealizedPnLPercent >= 0 ? '+' : ''}{record.unrealizedPnLPercent.toFixed(2)}%)
          </Text>
        </div>
      )
    },
    {
      title: '保证金',
      dataIndex: 'margin',
      key: 'margin',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy'
    },
    {
      title: '开仓时间',
      dataIndex: 'openTime',
      key: 'openTime'
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Position) => (
        <Space>
          <Tooltip title="查看详情">
            <Button 
              type="link" 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => setSelectedPosition(record)}
            />
          </Tooltip>
          <Tooltip title="平仓">
            <Button
              type="link"
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleClosePosition(record.id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  // 订单表格列配置
  const orderColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>
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
      render: (type: string) => {
        const typeMap = {
          market: { color: 'blue', text: '市价' },
          limit: { color: 'orange', text: '限价' },
          stop: { color: 'purple', text: '止损' }
        }
        const config = typeMap[type as keyof typeof typeMap]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '数量',
      dataIndex: 'amount',
      key: 'amount',
      render: (value: number) => value.toFixed(4)
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (value: number) => value ? `$${value.toLocaleString()}` : '-'
    },
    {
      title: '已成交',
      dataIndex: 'filled',
      key: 'filled',
      render: (value: number, record: Order) => (
        <div>
          <Text>{value.toFixed(4)}</Text>
          <br />
          <Progress 
            percent={(value / record.amount) * 100} 
            size="small" 
            showInfo={false}
          />
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          pending: { color: 'blue', text: '待成交' },
          filled: { color: 'green', text: '已成交' },
          cancelled: { color: 'red', text: '已取消' },
          rejected: { color: 'orange', text: '已拒绝' }
        }
        const config = statusMap[status as keyof typeof statusMap]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy'
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Order) => (
        <Space>
          {record.status === 'pending' && (
            <Button
              type="link"
              size="small"
              danger
              onClick={() => handleCancelOrder(record.id)}
            >
              取消
            </Button>
          )}
        </Space>
      )
    }
  ]

  // 交易历史表格列配置
  const tradeColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (text: string) => <Text strong>{text}</Text>
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
      title: '数量',
      dataIndex: 'amount',
      key: 'amount',
      render: (value: number) => value.toFixed(4)
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '手续费',
      dataIndex: 'fee',
      key: 'fee',
      render: (value: number) => `$${value.toFixed(2)}`
    },
    {
      title: '已实现盈亏',
      dataIndex: 'realizedPnL',
      key: 'realizedPnL',
      render: (value: number) => (
        <Text className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {value >= 0 ? '+' : ''}${value.toFixed(2)}
        </Text>
      )
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy'
    },
    {
      title: '执行时间',
      dataIndex: 'executedAt',
      key: 'executedAt'
    }
  ]

  // 盈亏图表配置
  const pnlChartOption = {
    title: {
      text: '实时盈亏曲线',
      left: 'left'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>盈亏: $${data.value.toFixed(2)}`
      }
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 24 }, (_, i) => `${i}:00`)
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '${value}'
      }
    },
    series: [{
      data: Array.from({ length: 24 }, () => Math.random() * 2000 - 1000),
      type: 'line',
      smooth: true,
      lineStyle: { color: '#1890ff', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
            { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
          ]
        }
      }
    }]
  }

  // 处理平仓
  const handleClosePosition = (positionId: string) => {
    Modal.confirm({
      title: '确认平仓',
      content: '确定要平仓这个持仓吗？',
      onOk: () => {
        console.log('平仓持仓:', positionId)
      }
    })
  }

  // 处理取消订单
  const handleCancelOrder = (orderId: string) => {
    Modal.confirm({
      title: '确认取消',
      content: '确定要取消这个订单吗？',
      onOk: () => {
        console.log('取消订单:', orderId)
      }
    })
  }

  // 处理手动下单
  const handleManualOrder = (values: any) => {
    console.log('手动下单:', values)
    setIsOrderModalVisible(false)
    form.resetFields()
  }

  // 刷新数据
  const handleRefresh = () => {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">交易监控</Title>
          <Text className="text-gray-500">实时监控交易活动和持仓状态</Text>
        </div>
        <Space>
          <Button 
            type="primary" 
            icon={<PlayCircleOutlined />}
            onClick={() => setIsOrderModalVisible(true)}
          >
            手动下单
          </Button>
          <Button 
            icon={<ReloadOutlined />} 
            loading={loading}
            onClick={handleRefresh}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 交易统计 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="总盈亏"
              value={tradingStats.totalPnL}
              precision={2}
              prefix={<TrophyOutlined className="text-orange-500" />}
              suffix="USD"
              valueStyle={{ color: tradingStats.totalPnL >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="今日盈亏"
              value={tradingStats.todayPnL}
              precision={2}
              prefix={<DollarOutlined className="text-blue-600" />}
              suffix="USD"
              valueStyle={{ color: tradingStats.todayPnL >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="活跃持仓"
              value={tradingStats.activePositions}
              prefix={<TrophyOutlined className="text-purple-600" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="待成交订单"
              value={tradingStats.pendingOrders}
              prefix={<ClockCircleOutlined className="text-green-600" />}
            />
          </Card>
        </Col>
      </Row>

      {/* 实时盈亏图表 */}
      <Card title="实时盈亏曲线" className="dashboard-card">
        <ReactECharts option={pnlChartOption} style={{ height: '300px' }} />
      </Card>

      {/* 主要内容区域 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={(
              <Badge count={positions.length} size="small">
                <span>持仓管理</span>
              </Badge>
            )} 
            key="positions"
          >
            <div className="mb-4">
              <Alert
                message="持仓风险提醒"
                description="当前持仓总保证金使用率为 32.5%，请注意风险控制。"
                type="info"
                showIcon
                closable
              />
            </div>
            <Table
              columns={positionColumns}
              dataSource={positions}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className="data-table"
              scroll={{ x: 1200 }}
            />
          </TabPane>
          
          <TabPane 
            tab={(
              <Badge count={orders.filter(o => o.status === 'pending').length} size="small">
                <span>订单管理</span>
              </Badge>
            )} 
            key="orders"
          >
            <div className="mb-4 flex justify-between items-center">
              <Space>
                <Select defaultValue="all" style={{ width: 120 }}>
                  <Option value="all">全部状态</Option>
                  <Option value="pending">待成交</Option>
                  <Option value="filled">已成交</Option>
                  <Option value="cancelled">已取消</Option>
                </Select>
                <Select defaultValue="all" style={{ width: 120 }}>
                  <Option value="all">全部类型</Option>
                  <Option value="market">市价</Option>
                  <Option value="limit">限价</Option>
                  <Option value="stop">止损</Option>
                </Select>
                <RangePicker />
              </Space>
              <Button icon={<FilterOutlined />}>筛选</Button>
            </div>
            <Table
              columns={orderColumns}
              dataSource={orders}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className="data-table"
              scroll={{ x: 1200 }}
            />
          </TabPane>
          
          <TabPane tab="交易历史" key="trades">
            <div className="mb-4 flex justify-between items-center">
              <Space>
                <Input.Search
                  placeholder="搜索交易对"
                  style={{ width: 200 }}
                  prefix={<SearchOutlined />}
                />
                <RangePicker />
              </Space>
              <Button icon={<ExportOutlined />}>导出</Button>
            </div>
            <Table
              columns={tradeColumns}
              dataSource={trades}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className="data-table"
              scroll={{ x: 1000 }}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 手动下单模态框 */}
      <Modal
        title="手动下单"
        open={isOrderModalVisible}
        onCancel={() => {
          setIsOrderModalVisible(false)
          form.resetFields()
        }}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleManualOrder}
        >
          <Form.Item
            name="symbol"
            label="交易对"
            rules={[{ required: true, message: '请选择交易对' }]}
          >
            <Select placeholder="请选择交易对">
              <Option value="BTC/USDT">BTC/USDT</Option>
              <Option value="ETH/USDT">ETH/USDT</Option>
              <Option value="BNB/USDT">BNB/USDT</Option>
              <Option value="SOL/USDT">SOL/USDT</Option>
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="side"
                label="方向"
                rules={[{ required: true, message: '请选择方向' }]}
              >
                <Select placeholder="请选择方向">
                  <Option value="buy">买入</Option>
                  <Option value="sell">卖出</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="type"
                label="类型"
                rules={[{ required: true, message: '请选择类型' }]}
              >
                <Select placeholder="请选择类型">
                  <Option value="market">市价</Option>
                  <Option value="limit">限价</Option>
                  <Option value="stop">止损</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="amount"
            label="数量"
            rules={[{ required: true, message: '请输入数量' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入数量"
              min={0.0001}
              step={0.0001}
            />
          </Form.Item>
          
          <Form.Item
            name="price"
            label="价格"
            tooltip="市价单无需填写价格"
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入价格"
              min={0.01}
              step={0.01}
            />
          </Form.Item>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsOrderModalVisible(false)
                form.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                下单
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 持仓详情模态框 */}
      {selectedPosition && (
        <Modal
          title="持仓详情"
          open={!!selectedPosition}
          onCancel={() => setSelectedPosition(null)}
          footer={[
            <Button key="close" onClick={() => setSelectedPosition(null)}>
              关闭
            </Button>,
            <Button key="closePosition" type="primary" danger onClick={() => {
              handleClosePosition(selectedPosition.id)
              setSelectedPosition(null)
            }}>
              平仓
            </Button>
          ]}
        >
          <div className="space-y-4">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Text strong>交易对：</Text>
                <br />
                <Text>{selectedPosition.symbol}</Text>
              </Col>
              <Col span={12}>
                <Text strong>方向：</Text>
                <br />
                <Tag color={selectedPosition.side === 'long' ? 'green' : 'red'}>
                  {selectedPosition.side === 'long' ? '做多' : '做空'}
                </Tag>
              </Col>
              <Col span={12}>
                <Text strong>数量：</Text>
                <br />
                <Text>{selectedPosition.size}</Text>
              </Col>
              <Col span={12}>
                <Text strong>开仓价格：</Text>
                <br />
                <Text>${selectedPosition.entryPrice.toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>当前价格：</Text>
                <br />
                <Text>${selectedPosition.currentPrice.toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>未实现盈亏：</Text>
                <br />
                <Text className={selectedPosition.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'}>
                  ${selectedPosition.unrealizedPnL.toFixed(2)} ({selectedPosition.unrealizedPnLPercent >= 0 ? '+' : ''}{selectedPosition.unrealizedPnLPercent.toFixed(2)}%)
                </Text>
              </Col>
              <Col span={12}>
                <Text strong>保证金：</Text>
                <br />
                <Text>${selectedPosition.margin.toLocaleString()}</Text>
              </Col>
              <Col span={12}>
                <Text strong>策略：</Text>
                <br />
                <Text>{selectedPosition.strategy}</Text>
              </Col>
              <Col span={24}>
                <Text strong>开仓时间：</Text>
                <br />
                <Text>{selectedPosition.openTime}</Text>
              </Col>
            </Row>
          </div>
        </Modal>
      )}
    </div>
  )
}

export default TradingMonitor