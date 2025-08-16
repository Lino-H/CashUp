import React, { useState } from 'react'
import {
  Card, Table, Button, Space, Tag, Modal, Form, Input, Select, InputNumber,
  Typography, Row, Col, Statistic, Tabs, Tooltip, Drawer
} from 'antd'
import {
  PlusOutlined, PlayCircleOutlined, PauseCircleOutlined, EditOutlined,
  DeleteOutlined, CopyOutlined, BarChartOutlined,
  RocketOutlined, TrophyOutlined, EyeOutlined
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input
const { TabPane } = Tabs

interface Strategy {
  id: string
  name: string
  type: string
  status: 'running' | 'stopped' | 'error' | 'backtesting'
  description: string
  createdAt: string
  updatedAt: string
  performance: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    maxDrawdown: number
    winRate: number
    totalTrades: number
  }
  config: {
    symbols: string[]
    timeframe: string
    capital: number
    riskLevel: 'low' | 'medium' | 'high'
  }
}

interface BacktestResult {
  id: string
  strategyId: string
  startDate: string
  endDate: string
  initialCapital: number
  finalCapital: number
  totalReturn: number
  sharpeRatio: number
  maxDrawdown: number
  status: 'running' | 'completed' | 'failed'
  createdAt: string
}

const StrategyManagement: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([
    {
      id: '1',
      name: '趋势跟踪策略A',
      type: 'trend_following',
      status: 'running',
      description: '基于移动平均线的趋势跟踪策略，适用于中长期趋势交易',
      createdAt: '2024-01-15',
      updatedAt: '2024-12-19',
      performance: {
        totalReturn: 25.68,
        annualizedReturn: 28.5,
        sharpeRatio: 1.85,
        maxDrawdown: -8.2,
        winRate: 68.5,
        totalTrades: 156
      },
      config: {
        symbols: ['BTC/USDT', 'ETH/USDT'],
        timeframe: '1h',
        capital: 50000,
        riskLevel: 'medium'
      }
    },
    {
      id: '2',
      name: '均值回归策略B',
      type: 'mean_reversion',
      status: 'running',
      description: '基于统计套利的均值回归策略，捕捉价格偏离均值的机会',
      createdAt: '2024-02-20',
      updatedAt: '2024-12-18',
      performance: {
        totalReturn: 18.9,
        annualizedReturn: 22.3,
        sharpeRatio: 2.12,
        maxDrawdown: -5.8,
        winRate: 72.3,
        totalTrades: 289
      },
      config: {
        symbols: ['BNB/USDT', 'SOL/USDT', 'ADA/USDT'],
        timeframe: '15m',
        capital: 30000,
        riskLevel: 'low'
      }
    },
    {
      id: '3',
      name: '套利策略C',
      type: 'arbitrage',
      status: 'stopped',
      description: '跨交易所套利策略，利用价格差异获取无风险收益',
      createdAt: '2024-03-10',
      updatedAt: '2024-12-15',
      performance: {
        totalReturn: 12.4,
        annualizedReturn: 15.8,
        sharpeRatio: 1.67,
        maxDrawdown: -2.1,
        winRate: 85.2,
        totalTrades: 423
      },
      config: {
        symbols: ['BTC/USDT'],
        timeframe: '5m',
        capital: 20000,
        riskLevel: 'low'
      }
    }
  ])

  const [backtests, setBacktests] = useState<BacktestResult[]>([
    {
      id: '1',
      strategyId: '1',
      startDate: '2024-01-01',
      endDate: '2024-12-01',
      initialCapital: 100000,
      finalCapital: 125680,
      totalReturn: 25.68,
      sharpeRatio: 1.85,
      maxDrawdown: -8.2,
      status: 'completed',
      createdAt: '2024-12-19'
    }
  ])

  const [isModalVisible, setIsModalVisible] = useState(false)
  const [isBacktestModalVisible, setIsBacktestModalVisible] = useState(false)
  const [isDetailDrawerVisible, setIsDetailDrawerVisible] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [form] = Form.useForm()
  const [backtestForm] = Form.useForm()

  // 策略类型选项
  const strategyTypes = [
    { value: 'trend_following', label: '趋势跟踪' },
    { value: 'mean_reversion', label: '均值回归' },
    { value: 'momentum', label: '动量策略' },
    { value: 'arbitrage', label: '套利策略' },
    { value: 'market_making', label: '做市策略' }
  ]

  // 时间框架选项
  const timeframes = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '1h', label: '1小时' },
    { value: '4h', label: '4小时' },
    { value: '1d', label: '1天' }
  ]

  // 风险等级选项
  const riskLevels = [
    { value: 'low', label: '低风险', color: 'green' },
    { value: 'medium', label: '中风险', color: 'orange' },
    { value: 'high', label: '高风险', color: 'red' }
  ]

  // 策略表格列配置
  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Strategy) => (
        <Space>
          <div className={`status-indicator status-${record.status}`}></div>
          <div>
            <Text strong>{text}</Text>
            <br />
            <Text className="text-xs text-gray-500">{record.type}</Text>
          </div>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          running: { color: 'green', text: '运行中' },
          stopped: { color: 'red', text: '已停止' },
          error: { color: 'orange', text: '异常' },
          backtesting: { color: 'blue', text: '回测中' }
        }
        const config = statusMap[status as keyof typeof statusMap]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '总收益率',
      key: 'totalReturn',
      render: (_: any, record: Strategy) => (
        <Text className={record.performance.totalReturn >= 0 ? 'text-green-600' : 'text-red-600'}>
          {record.performance.totalReturn >= 0 ? '+' : ''}{record.performance.totalReturn.toFixed(2)}%
        </Text>
      )
    },
    {
      title: '夏普比率',
      key: 'sharpeRatio',
      render: (_: any, record: Strategy) => record.performance.sharpeRatio.toFixed(2)
    },
    {
      title: '最大回撤',
      key: 'maxDrawdown',
      render: (_: any, record: Strategy) => (
        <Text className="text-red-600">
          {record.performance.maxDrawdown.toFixed(2)}%
        </Text>
      )
    },
    {
      title: '胜率',
      key: 'winRate',
      render: (_: any, record: Strategy) => `${record.performance.winRate}%`
    },
    {
      title: '风险等级',
      key: 'riskLevel',
      render: (_: any, record: Strategy) => {
        const risk = riskLevels.find(r => r.value === record.config.riskLevel)
        return <Tag color={risk?.color}>{risk?.label}</Tag>
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Strategy) => (
        <Space>
          <Tooltip title="查看详情">
            <Button 
              type="link" 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => {
                setSelectedStrategy(record)
                setIsDetailDrawerVisible(true)
              }}
            />
          </Tooltip>
          <Tooltip title={record.status === 'running' ? '停止策略' : '启动策略'}>
            <Button
              type="link"
              size="small"
              icon={record.status === 'running' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleStrategy(record.id)}
            />
          </Tooltip>
          <Tooltip title="编辑策略">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditStrategy(record)}
            />
          </Tooltip>
          <Tooltip title="克隆策略">
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCloneStrategy(record)}
            />
          </Tooltip>
          <Tooltip title="删除策略">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteStrategy(record.id)}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  // 回测结果表格列配置
  const backtestColumns = [
    {
      title: '回测ID',
      dataIndex: 'id',
      key: 'id'
    },
    {
      title: '时间范围',
      key: 'dateRange',
      render: (_: any, record: BacktestResult) => `${record.startDate} ~ ${record.endDate}`
    },
    {
      title: '初始资金',
      dataIndex: 'initialCapital',
      key: 'initialCapital',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '最终资金',
      dataIndex: 'finalCapital',
      key: 'finalCapital',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: '总收益率',
      dataIndex: 'totalReturn',
      key: 'totalReturn',
      render: (value: number) => (
        <Text className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </Text>
      )
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpeRatio',
      key: 'sharpeRatio',
      render: (value: number) => value.toFixed(2)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          running: { color: 'blue', text: '运行中' },
          completed: { color: 'green', text: '已完成' },
          failed: { color: 'red', text: '失败' }
        }
        const config = statusMap[status as keyof typeof statusMap]
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt'
    }
  ]

  // 处理策略启停
  const handleToggleStrategy = (id: string) => {
    setStrategies(prev => prev.map(strategy => {
      if (strategy.id === id) {
        return {
          ...strategy,
          status: strategy.status === 'running' ? 'stopped' : 'running'
        }
      }
      return strategy
    }))
  }

  // 处理编辑策略
  const handleEditStrategy = (strategy: Strategy) => {
    form.setFieldsValue({
      name: strategy.name,
      type: strategy.type,
      description: strategy.description,
      symbols: strategy.config.symbols,
      timeframe: strategy.config.timeframe,
      capital: strategy.config.capital,
      riskLevel: strategy.config.riskLevel
    })
    setSelectedStrategy(strategy)
    setIsModalVisible(true)
  }

  // 处理克隆策略
  const handleCloneStrategy = (strategy: Strategy) => {
    form.setFieldsValue({
      name: `${strategy.name} (副本)`,
      type: strategy.type,
      description: strategy.description,
      symbols: strategy.config.symbols,
      timeframe: strategy.config.timeframe,
      capital: strategy.config.capital,
      riskLevel: strategy.config.riskLevel
    })
    setSelectedStrategy(null)
    setIsModalVisible(true)
  }

  // 处理删除策略
  const handleDeleteStrategy = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个策略吗？此操作不可撤销。',
      onOk: () => {
        setStrategies(prev => prev.filter(strategy => strategy.id !== id))
      }
    })
  }

  // 处理保存策略
  const handleSaveStrategy = (values: any) => {
    if (selectedStrategy) {
      // 编辑现有策略
      setStrategies(prev => prev.map(strategy => {
        if (strategy.id === selectedStrategy.id) {
          return {
            ...strategy,
            ...values,
            config: {
              symbols: values.symbols,
              timeframe: values.timeframe,
              capital: values.capital,
              riskLevel: values.riskLevel
            },
            updatedAt: new Date().toISOString().split('T')[0]
          }
        }
        return strategy
      }))
    } else {
      // 创建新策略
      const newStrategy: Strategy = {
        id: Date.now().toString(),
        ...values,
        status: 'stopped',
        createdAt: new Date().toISOString().split('T')[0],
        updatedAt: new Date().toISOString().split('T')[0],
        performance: {
          totalReturn: 0,
          annualizedReturn: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          winRate: 0,
          totalTrades: 0
        },
        config: {
          symbols: values.symbols,
          timeframe: values.timeframe,
          capital: values.capital,
          riskLevel: values.riskLevel
        }
      }
      setStrategies(prev => [...prev, newStrategy])
    }
    setIsModalVisible(false)
    form.resetFields()
    setSelectedStrategy(null)
  }

  // 处理回测
  const handleBacktest = (values: any) => {
    const newBacktest: BacktestResult = {
      id: Date.now().toString(),
      strategyId: selectedStrategy?.id || '',
      startDate: values.startDate,
      endDate: values.endDate,
      initialCapital: values.initialCapital,
      finalCapital: 0,
      totalReturn: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      status: 'running',
      createdAt: new Date().toISOString().split('T')[0]
    }
    setBacktests(prev => [...prev, newBacktest])
    setIsBacktestModalVisible(false)
    backtestForm.resetFields()
  }

  // 策略性能图表配置
  const performanceChartOption = {
    title: {
      text: '策略收益对比',
      left: 'left'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: strategies.map(s => s.name),
      top: 30
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: strategies.map((strategy) => ({
      name: strategy.name,
      type: 'line',
      data: Array.from({ length: 12 }, (_, i) => 
        Math.random() * strategy.performance.totalReturn * (i + 1) / 12
      ),
      smooth: true
    }))
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center">
        <div>
          <Title level={2} className="!mb-2">策略管理</Title>
          <Text className="text-gray-500">管理和监控您的量化交易策略</Text>
        </div>
        <Space>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => {
              setSelectedStrategy(null)
              form.resetFields()
              setIsModalVisible(true)
            }}
          >
            创建策略
          </Button>
          <Button 
            icon={<BarChartOutlined />}
            onClick={() => setIsBacktestModalVisible(true)}
          >
            新建回测
          </Button>
        </Space>
      </div>

      {/* 策略概览统计 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card className="dashboard-card">
            <Statistic
              title="总策略数"
              value={strategies.length}
              prefix={<RocketOutlined className="text-blue-600" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="dashboard-card">
            <Statistic
              title="运行中策略"
              value={strategies.filter(s => s.status === 'running').length}
              prefix={<PlayCircleOutlined className="text-green-600" />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card className="dashboard-card">
            <Statistic
              title="平均收益率"
              value={(strategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / strategies.length).toFixed(2)}
              suffix="%"
              prefix={<TrophyOutlined className="text-orange-500" />}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区域 */}
      <Card>
        <Tabs defaultActiveKey="strategies">
          <TabPane tab="策略列表" key="strategies">
            <Table
              columns={strategyColumns}
              dataSource={strategies}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className="data-table"
            />
          </TabPane>
          
          <TabPane tab="回测结果" key="backtests">
            <Table
              columns={backtestColumns}
              dataSource={backtests}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              className="data-table"
            />
          </TabPane>
          
          <TabPane tab="性能分析" key="performance">
            <ReactECharts option={performanceChartOption} style={{ height: '400px' }} />
          </TabPane>
        </Tabs>
      </Card>

      {/* 创建/编辑策略模态框 */}
      <Modal
        title={selectedStrategy ? '编辑策略' : '创建策略'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false)
          form.resetFields()
          setSelectedStrategy(null)
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveStrategy}
        >
          <Form.Item
            name="name"
            label="策略名称"
            rules={[{ required: true, message: '请输入策略名称' }]}
          >
            <Input placeholder="请输入策略名称" />
          </Form.Item>
          
          <Form.Item
            name="type"
            label="策略类型"
            rules={[{ required: true, message: '请选择策略类型' }]}
          >
            <Select placeholder="请选择策略类型">
              {strategyTypes.map(type => (
                <Option key={type.value} value={type.value}>{type.label}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="description"
            label="策略描述"
            rules={[{ required: true, message: '请输入策略描述' }]}
          >
            <TextArea rows={3} placeholder="请输入策略描述" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="symbols"
                label="交易品种"
                rules={[{ required: true, message: '请选择交易品种' }]}
              >
                <Select mode="multiple" placeholder="请选择交易品种">
                  <Option value="BTC/USDT">BTC/USDT</Option>
                  <Option value="ETH/USDT">ETH/USDT</Option>
                  <Option value="BNB/USDT">BNB/USDT</Option>
                  <Option value="SOL/USDT">SOL/USDT</Option>
                  <Option value="ADA/USDT">ADA/USDT</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="timeframe"
                label="时间框架"
                rules={[{ required: true, message: '请选择时间框架' }]}
              >
                <Select placeholder="请选择时间框架">
                  {timeframes.map(tf => (
                    <Option key={tf.value} value={tf.value}>{tf.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="capital"
                label="初始资金"
                rules={[{ required: true, message: '请输入初始资金' }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  placeholder="请输入初始资金"
                  min={1000}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value: string | undefined) => value ? parseInt(value.replace(/\$\s?|(,*)/g, '')) || 0 : 0}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="riskLevel"
                label="风险等级"
                rules={[{ required: true, message: '请选择风险等级' }]}
              >
                <Select placeholder="请选择风险等级">
                  {riskLevels.map(risk => (
                    <Option key={risk.value} value={risk.value}>{risk.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsModalVisible(false)
                form.resetFields()
                setSelectedStrategy(null)
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {selectedStrategy ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 回测模态框 */}
      <Modal
        title="创建回测"
        open={isBacktestModalVisible}
        onCancel={() => {
          setIsBacktestModalVisible(false)
          backtestForm.resetFields()
        }}
        footer={null}
        width={500}
      >
        <Form
          form={backtestForm}
          layout="vertical"
          onFinish={handleBacktest}
        >
          <Form.Item
            name="strategyId"
            label="选择策略"
            rules={[{ required: true, message: '请选择策略' }]}
          >
            <Select placeholder="请选择要回测的策略">
              {strategies.map(strategy => (
                <Option key={strategy.id} value={strategy.id}>{strategy.name}</Option>
              ))}
            </Select>
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="startDate"
                label="开始日期"
                rules={[{ required: true, message: '请选择开始日期' }]}
              >
                <Input type="date" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="endDate"
                label="结束日期"
                rules={[{ required: true, message: '请选择结束日期' }]}
              >
                <Input type="date" />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="initialCapital"
            label="初始资金"
            rules={[{ required: true, message: '请输入初始资金' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              placeholder="请输入初始资金"
              min={1000}
              formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={(value: string | undefined) => value ? parseInt(value.replace(/\$\s?|(,*)/g, '')) || 0 : 0}
            />
          </Form.Item>
          
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => {
                setIsBacktestModalVisible(false)
                backtestForm.resetFields()
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                开始回测
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 策略详情抽屉 */}
      <Drawer
        title="策略详情"
        placement="right"
        width={600}
        open={isDetailDrawerVisible}
        onClose={() => setIsDetailDrawerVisible(false)}
      >
        {selectedStrategy && (
          <div className="space-y-6">
            {/* 基本信息 */}
            <Card title="基本信息" size="small">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>策略名称：</Text>
                  <br />
                  <Text>{selectedStrategy.name}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>策略类型：</Text>
                  <br />
                  <Text>{strategyTypes.find(t => t.value === selectedStrategy.type)?.label}</Text>
                </Col>
                <Col span={24}>
                  <Text strong>策略描述：</Text>
                  <br />
                  <Text>{selectedStrategy.description}</Text>
                </Col>
              </Row>
            </Card>

            {/* 配置信息 */}
            <Card title="配置信息" size="small">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>交易品种：</Text>
                  <br />
                  <Space wrap>
                    {selectedStrategy.config.symbols.map(symbol => (
                      <Tag key={symbol}>{symbol}</Tag>
                    ))}
                  </Space>
                </Col>
                <Col span={12}>
                  <Text strong>时间框架：</Text>
                  <br />
                  <Text>{timeframes.find(t => t.value === selectedStrategy.config.timeframe)?.label}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>初始资金：</Text>
                  <br />
                  <Text>${selectedStrategy.config.capital.toLocaleString()}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>风险等级：</Text>
                  <br />
                  <Tag color={riskLevels.find(r => r.value === selectedStrategy.config.riskLevel)?.color}>
                    {riskLevels.find(r => r.value === selectedStrategy.config.riskLevel)?.label}
                  </Tag>
                </Col>
              </Row>
            </Card>

            {/* 性能指标 */}
            <Card title="性能指标" size="small">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title="总收益率"
                    value={selectedStrategy.performance.totalReturn}
                    precision={2}
                    suffix="%"
                    valueStyle={{ color: selectedStrategy.performance.totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="年化收益率"
                    value={selectedStrategy.performance.annualizedReturn}
                    precision={2}
                    suffix="%"
                    valueStyle={{ color: selectedStrategy.performance.annualizedReturn >= 0 ? '#3f8600' : '#cf1322' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="夏普比率"
                    value={selectedStrategy.performance.sharpeRatio}
                    precision={2}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="最大回撤"
                    value={selectedStrategy.performance.maxDrawdown}
                    precision={2}
                    suffix="%"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="胜率"
                    value={selectedStrategy.performance.winRate}
                    precision={1}
                    suffix="%"
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="总交易次数"
                    value={selectedStrategy.performance.totalTrades}
                  />
                </Col>
              </Row>
            </Card>

            {/* 操作按钮 */}
            <div className="text-center">
              <Space>
                <Button 
                  type="primary" 
                  icon={selectedStrategy.status === 'running' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  onClick={() => handleToggleStrategy(selectedStrategy.id)}
                >
                  {selectedStrategy.status === 'running' ? '停止策略' : '启动策略'}
                </Button>
                <Button 
                  icon={<EditOutlined />}
                  onClick={() => {
                    setIsDetailDrawerVisible(false)
                    handleEditStrategy(selectedStrategy)
                  }}
                >
                  编辑策略
                </Button>
                <Button 
                  icon={<BarChartOutlined />}
                  onClick={() => {
                    setIsDetailDrawerVisible(false)
                    setIsBacktestModalVisible(true)
                  }}
                >
                  创建回测
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default StrategyManagement